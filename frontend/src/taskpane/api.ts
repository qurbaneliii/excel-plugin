import type {
  ActionPlanResponse,
  AnalyzeRangeResponse,
  FormulaExplainResponse,
  FormulaFixResponse,
  FormulaGenerateResponse,
  HealthResponse,
  LLMStatusResponse,
  LLMTestLocalResponse,
  ProviderMode,
  RangeContext,
  ReportResponse,
} from "./types";

const BASE_URL = "http://localhost:8000";

function formatError(status: number, text: string): Error {
  if (status === 404) {
    return new Error("Backend endpoint was not found. Verify the FastAPI server is running the latest code.");
  }
  if (status >= 500) {
    return new Error(`Backend error (${status}). ${text || "Check backend logs for details."}`);
  }
  return new Error(`Request failed (${status}). ${text}`);
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const text = await response.text();
    throw formatError(response.status, text);
  }

  return response.json() as Promise<T>;
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`);
  if (!response.ok) {
    const text = await response.text();
    throw formatError(response.status, text);
  }
  return response.json() as Promise<T>;
}

export function healthCheck(): Promise<HealthResponse> {
  return getJson<HealthResponse>("/health");
}

export function getLLMStatus(): Promise<LLMStatusResponse> {
  return getJson<LLMStatusResponse>("/api/llm/status");
}

export function testLocalLLM(prompt: string): Promise<LLMTestLocalResponse> {
  return postJson<LLMTestLocalResponse>("/api/llm/test-local", { prompt });
}

export function analyzeRange(payload: { userPrompt: string; rangeContext: RangeContext; providerMode: ProviderMode }) {
  return postJson<AnalyzeRangeResponse>("/api/analyze-range", payload);
}

export function generateFormula(payload: {
  userPrompt: string;
  headers: string[];
  sampleRows: unknown[][];
  providerMode: ProviderMode;
}) {
  return postJson<FormulaGenerateResponse>("/api/formula/generate", payload);
}

export function explainFormula(payload: {
  formula: string;
  headers: string[];
  sampleRows: unknown[][];
  providerMode: ProviderMode;
}) {
  return postJson<FormulaExplainResponse>("/api/formula/explain", payload);
}

export function fixFormula(payload: {
  formula: string;
  error: string;
  headers: string[];
  sampleRows: unknown[][];
  providerMode: ProviderMode;
}) {
  return postJson<FormulaFixResponse>("/api/formula/fix", payload);
}

export function createActionPlan(payload: { userPrompt: string; rangeContext: RangeContext; providerMode: ProviderMode }) {
  return postJson<ActionPlanResponse>("/api/action-plan", payload);
}

export function generateReport(payload: { userPrompt: string; rangeContext: RangeContext; providerMode: ProviderMode }) {
  return postJson<ReportResponse>("/api/report", payload);
}
