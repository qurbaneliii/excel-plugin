import { useEffect, useState } from "react";

import {
  analyzeRange,
  createActionPlan,
  explainFormula,
  fixFormula,
  generateFormula,
  generateReport,
  getLLMStatus,
  healthCheck,
  testLocalLLM,
} from "./api";
import { applySafeCleaning } from "./cleaning";
import {
  createBasicSummarySheet,
  insertFormulaIntoSelectedCell,
  writeCleanedDataToNewSheet,
  writeReportToNewSheet,
} from "./excelActions";
import { getFullSelectedRangeValuesForApply, getSelectedFormulaContext, getSelectedRangeContext } from "./excelContext";
import { ActionPlanPreview } from "./components/ActionPlanPreview";
import { AnalysisPanel } from "./components/AnalysisPanel";
import { FormulaAssistant } from "./components/FormulaAssistant";
import { PromptBox } from "./components/PromptBox";
import { RangeSummary } from "./components/RangeSummary";
import { ReportPanel } from "./components/ReportPanel";
import { StatusBar } from "./components/StatusBar";
import type {
  ActionPlanResponse,
  AnalyzeRangeResponse,
  FormulaExplainResponse,
  FormulaFixResponse,
  FormulaGenerateResponse,
  LLMStatusResponse,
  ProviderMetadata,
  ProviderMode,
  RangeContext,
  ReportResponse,
} from "./types";

const EMPTY_LLM_STATUS: LLMStatusResponse = {
  provider_mode: "auto",
  openai_available: false,
  local_enabled: false,
  local_available: false,
  local_provider: "ollama",
  local_base_url: "http://localhost:11434/v1",
  local_model: "qwen3:4b",
  fallback_available: true,
  warnings: [],
};

export default function App() {
  const [backendOk, setBackendOk] = useState(false);
  const [statusMessage, setStatusMessage] = useState("Checking backend...");
  const [providerMode, setProviderMode] = useState<ProviderMode>("auto");
  const [llmStatus, setLlmStatus] = useState<LLMStatusResponse>(EMPTY_LLM_STATUS);
  const [lastProviderMetadata, setLastProviderMetadata] = useState<ProviderMetadata | null>(null);
  const [prompt, setPrompt] = useState("Analyze this table and show problems.");
  const [rangeContext, setRangeContext] = useState<RangeContext | null>(null);
  const [analysis, setAnalysis] = useState<AnalyzeRangeResponse | null>(null);
  const [generatedFormula, setGeneratedFormula] = useState<FormulaGenerateResponse | null>(null);
  const [explainedFormula, setExplainedFormula] = useState<FormulaExplainResponse | null>(null);
  const [fixedFormula, setFixedFormula] = useState<FormulaFixResponse | null>(null);
  const [actionPlan, setActionPlan] = useState<ActionPlanResponse | null>(null);
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    void refreshBackend();
  }, []);

  async function refreshBackend() {
    try {
      const [health, status] = await Promise.all([healthCheck(), getLLMStatus()]);
      setBackendOk(health.status === "ok");
      setStatusMessage(`Backend running. Default mode: ${health.llm_provider_mode}.`);
      setLlmStatus(status);
    } catch (error) {
      setBackendOk(false);
      setStatusMessage(error instanceof Error ? error.message : "Backend not reachable.");
    }
  }

  function pushLog(message: string) {
    setLogs((current) => [message, ...current].slice(0, 12));
  }

  function rememberProvider(metadata?: ProviderMetadata) {
    if (!metadata) {
      return;
    }
    setLastProviderMetadata(metadata);
    if (metadata.fallback_used) {
      pushLog(`Fallback used for the last response via ${metadata.selected_provider}.`);
    }
  }

  async function loadRangeContext() {
    const context = await getSelectedRangeContext();
    setRangeContext(context);
    return context;
  }

  async function handleAnalyze() {
    try {
      const context = await loadRangeContext();
      const result = await analyzeRange({ userPrompt: prompt, rangeContext: context, providerMode });
      setAnalysis(result);
      rememberProvider(result.provider_metadata);
      pushLog("Analysis completed.");
    } catch (error) {
      pushLog(error instanceof Error ? error.message : "Analysis failed.");
    }
  }

  async function handleGenerateFormula() {
    try {
      const context = rangeContext ?? (await loadRangeContext());
      const result = await generateFormula({ userPrompt: prompt, headers: context.headers, sampleRows: context.sampleRows, providerMode });
      setGeneratedFormula(result);
      rememberProvider(result.provider_metadata);
      pushLog("Formula generated.");
    } catch (error) {
      pushLog(error instanceof Error ? error.message : "Formula generation failed.");
    }
  }

  async function handleExplainFormula() {
    try {
      const formulaContext = await getSelectedFormulaContext();
      const context = rangeContext ?? (await loadRangeContext());
      const result = await explainFormula({
        formula: formulaContext.formula,
        headers: context.headers,
        sampleRows: context.sampleRows,
        providerMode,
      });
      setExplainedFormula(result);
      rememberProvider(result.provider_metadata);
      pushLog("Formula explained.");
    } catch (error) {
      pushLog(error instanceof Error ? error.message : "Formula explanation failed.");
    }
  }

  async function handleFixFormula() {
    try {
      const formulaContext = await getSelectedFormulaContext();
      const context = rangeContext ?? (await loadRangeContext());
      const result = await fixFormula({
        formula: formulaContext.formula,
        error: prompt,
        headers: context.headers,
        sampleRows: context.sampleRows,
        providerMode,
      });
      setFixedFormula(result);
      rememberProvider(result.provider_metadata);
      pushLog("Formula fix generated.");
    } catch (error) {
      pushLog(error instanceof Error ? error.message : "Formula fix failed.");
    }
  }

  async function handleInsertFormula() {
    try {
      const formula = fixedFormula?.fixed_formula ?? generatedFormula?.formula;
      if (!formula) {
        throw new Error("Generate or fix a formula first.");
      }
      await insertFormulaIntoSelectedCell(formula);
      pushLog("Formula inserted into selected cell.");
    } catch (error) {
      pushLog(error instanceof Error ? error.message : "Formula insert failed.");
    }
  }

  async function handlePlanCleaning() {
    try {
      const context = await loadRangeContext();
      const result = await createActionPlan({ userPrompt: prompt, rangeContext: context, providerMode });
      setActionPlan(result);
      rememberProvider(result.provider_metadata);
      pushLog("Cleaning plan created.");
    } catch (error) {
      pushLog(error instanceof Error ? error.message : "Cleaning plan failed.");
    }
  }

  async function handleApplyCleaning() {
    try {
      const selection = await getFullSelectedRangeValuesForApply();
      const { cleanedValues, issues } = applySafeCleaning(selection.values);
      await writeCleanedDataToNewSheet(selection.worksheetName, cleanedValues, issues);
      pushLog("Cleaned data written to new sheet.");
    } catch (error) {
      pushLog(error instanceof Error ? error.message : "Apply cleaning failed.");
    }
  }

  async function handleGenerateReport() {
    try {
      const context = await loadRangeContext();
      const result = await generateReport({ userPrompt: prompt, rangeContext: context, providerMode });
      setReport(result);
      rememberProvider(result.provider_metadata);
      pushLog("Report generated.");
    } catch (error) {
      pushLog(error instanceof Error ? error.message : "Report generation failed.");
    }
  }

  async function handleWriteReport() {
    try {
      if (!report || !rangeContext) {
        throw new Error("Generate a report first.");
      }
      await writeReportToNewSheet(rangeContext.worksheetName, report);
      pushLog("Report written to new sheet.");
    } catch (error) {
      pushLog(error instanceof Error ? error.message : "Writing report failed.");
    }
  }

  async function handleCreateSummary() {
    try {
      const selection = await getFullSelectedRangeValuesForApply();
      await createBasicSummarySheet(selection.worksheetName, selection.values);
      pushLog("Summary sheet created.");
    } catch (error) {
      pushLog(error instanceof Error ? error.message : "Summary sheet creation failed.");
    }
  }

  async function handleTestLocalModel() {
    try {
      const result = await testLocalLLM('Say hello in JSON as {"message":"hello"}');
      pushLog(result.ok ? `Local LLM test succeeded with ${result.model}.` : result.error || "Local LLM test failed.");
    } catch (error) {
      pushLog(error instanceof Error ? error.message : "Local LLM test failed.");
    }
  }

  return (
    <div className="app-shell">
      <h1>Excel AI Assistant</h1>
      <StatusBar backendOk={backendOk} message={statusMessage} />
      <div className="panel">
        <h3>AI Provider</h3>
        <label className="provider-picker">
          Provider Mode
          <select value={providerMode} onChange={(event) => setProviderMode(event.target.value as ProviderMode)}>
            <option value="auto">Auto</option>
            <option value="openai">OpenAI</option>
            <option value="local">Local</option>
            <option value="fallback">Fallback</option>
          </select>
        </label>
        <p>OpenAI available: {llmStatus.openai_available ? "Yes" : "No"}</p>
        <p>Local LLM available: {llmStatus.local_available ? "Yes" : "No"}</p>
        <p>Local model: {llmStatus.local_model}</p>
        <p>
          Last provider:{" "}
          {lastProviderMetadata ? `${lastProviderMetadata.selected_provider}${lastProviderMetadata.model ? ` (${lastProviderMetadata.model})` : ""}` : "No request yet"}
        </p>
        {lastProviderMetadata?.fallback_used && <p className="warning">Fallback was used for the last response.</p>}
        {llmStatus.warnings.map((warning) => (
          <p key={warning} className="warning">{warning}</p>
        ))}
        <div className="actions compact-actions">
          <button onClick={() => void refreshBackend()}>Refresh Backend Status</button>
          <button onClick={() => void handleTestLocalModel()}>Test Local LLM</button>
          <button onClick={() => void loadRangeContext()}>Refresh Selected Range</button>
        </div>
      </div>
      <RangeSummary context={rangeContext} />
      <PromptBox value={prompt} onChange={setPrompt} />
      <div className="actions">
        <button onClick={() => void handleAnalyze()}>Analyze Selected Range</button>
        <button onClick={() => void handleGenerateFormula()}>Generate Formula</button>
        <button onClick={() => void handleExplainFormula()}>Explain Formula</button>
        <button onClick={() => void handleFixFormula()}>Fix Formula</button>
        <button onClick={() => void handleInsertFormula()}>Insert Generated Formula</button>
        <button onClick={() => void handlePlanCleaning()}>Plan Cleaning Actions</button>
        <button onClick={() => void handleApplyCleaning()}>Apply Safe Cleaning to New Sheet</button>
        <button onClick={() => void handleGenerateReport()}>Generate Report</button>
        <button onClick={() => void handleWriteReport()}>Write Report to New Sheet</button>
        <button onClick={() => void handleCreateSummary()}>Create Basic Summary Sheet</button>
      </div>
      <AnalysisPanel result={analysis} />
      <FormulaAssistant generated={generatedFormula} explained={explainedFormula} fixed={fixedFormula} />
      <ActionPlanPreview result={actionPlan} />
      <ReportPanel report={report} />
      <div className="panel">
        <h3>Logs / Errors</h3>
        <ul>
          {logs.map((entry, index) => (
            <li key={`${entry}-${index}`}>{entry}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
