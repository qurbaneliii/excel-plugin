from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .llm.router import LLMRouter
from .prompts import (
    ACTION_PLAN_PROMPT,
    ANALYZE_RANGE_PROMPT,
    FORMULA_EXPLAIN_PROMPT,
    FORMULA_FIX_PROMPT,
    FORMULA_GENERATE_PROMPT,
    REPORT_PROMPT,
)
from .schemas import (
    ActionPlanResponse,
    AnalyzeRangeResponse,
    FormulaExplainRequest,
    FormulaExplainResponse,
    FormulaFixRequest,
    FormulaFixResponse,
    FormulaGenerateRequest,
    FormulaGenerateResponse,
    HealthResponse,
    LLMStatusResponse,
    LLMTestLocalRequest,
    LLMTestLocalResponse,
    PromptedRangeRequest,
    ProviderMetadata,
    ReportResponse,
)
from .services.profiler import profile_range
from .settings import get_settings

settings = get_settings()
router = LLMRouter(settings)

app = FastAPI(title="Excel AI Assistant Backend", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _attach_metadata(result, warnings: list[str]) -> object:
    merged_warnings = [*result.response.warnings, *warnings, *result.warnings]
    deduped_warnings = list(dict.fromkeys([warning for warning in merged_warnings if warning]))
    payload = result.response.model_dump()
    payload["warnings"] = deduped_warnings
    payload["provider_metadata"] = ProviderMetadata(
        provider_mode=result.provider_mode,
        selected_provider=result.selected_provider,
        model=result.model,
        fallback_used=result.fallback_used,
        warnings=result.warnings,
    ).model_dump()
    return payload


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", backend="running", llm_provider_mode=settings.llm_provider)


@app.get("/api/llm/status", response_model=LLMStatusResponse)
def llm_status() -> LLMStatusResponse:
    return LLMStatusResponse(**router.get_status())


@app.post("/api/llm/test-local", response_model=LLMTestLocalResponse)
def llm_test_local(request: LLMTestLocalRequest) -> LLMTestLocalResponse:
    return LLMTestLocalResponse(**router.test_local(request.prompt))


@app.post("/api/analyze-range", response_model=AnalyzeRangeResponse)
def analyze_range(request: PromptedRangeRequest) -> AnalyzeRangeResponse:
    profile = profile_range(request.rangeContext.headers, request.rangeContext.sampleRows)
    result = router.generate_json(
        system_prompt=ANALYZE_RANGE_PROMPT,
        user_payload={
            "userPrompt": request.userPrompt,
            "rangeContext": request.rangeContext.model_dump(mode="json"),
            "profiler": profile,
        },
        response_model=AnalyzeRangeResponse,
        task_type="range_analysis",
        provider_mode_override=request.providerMode,
    )
    return AnalyzeRangeResponse(**_attach_metadata(result, request.rangeContext.warnings))


@app.post("/api/formula/generate", response_model=FormulaGenerateResponse)
def generate_formula(request: FormulaGenerateRequest) -> FormulaGenerateResponse:
    result = router.generate_json(
        system_prompt=FORMULA_GENERATE_PROMPT,
        user_payload=request.model_dump(mode="json", exclude_none=True),
        response_model=FormulaGenerateResponse,
        task_type="formula_generate",
        provider_mode_override=request.providerMode,
    )
    return FormulaGenerateResponse(**_attach_metadata(result, []))


@app.post("/api/formula/explain", response_model=FormulaExplainResponse)
def explain_formula(request: FormulaExplainRequest) -> FormulaExplainResponse:
    result = router.generate_json(
        system_prompt=FORMULA_EXPLAIN_PROMPT,
        user_payload=request.model_dump(mode="json", exclude_none=True),
        response_model=FormulaExplainResponse,
        task_type="formula_explain",
        provider_mode_override=request.providerMode,
    )
    return FormulaExplainResponse(**_attach_metadata(result, []))


@app.post("/api/formula/fix", response_model=FormulaFixResponse)
def fix_formula(request: FormulaFixRequest) -> FormulaFixResponse:
    result = router.generate_json(
        system_prompt=FORMULA_FIX_PROMPT,
        user_payload=request.model_dump(mode="json", exclude_none=True),
        response_model=FormulaFixResponse,
        task_type="formula_fix",
        provider_mode_override=request.providerMode,
    )
    return FormulaFixResponse(**_attach_metadata(result, []))


@app.post("/api/action-plan", response_model=ActionPlanResponse)
def action_plan(request: PromptedRangeRequest) -> ActionPlanResponse:
    profile = profile_range(request.rangeContext.headers, request.rangeContext.sampleRows)
    result = router.generate_json(
        system_prompt=ACTION_PLAN_PROMPT,
        user_payload={
            "userPrompt": request.userPrompt,
            "rangeContext": request.rangeContext.model_dump(mode="json"),
            "profiler": profile,
        },
        response_model=ActionPlanResponse,
        task_type="action_plan",
        provider_mode_override=request.providerMode,
    )
    return ActionPlanResponse(**_attach_metadata(result, request.rangeContext.warnings))


@app.post("/api/report", response_model=ReportResponse)
def report(request: PromptedRangeRequest) -> ReportResponse:
    profile = profile_range(request.rangeContext.headers, request.rangeContext.sampleRows)
    result = router.generate_json(
        system_prompt=REPORT_PROMPT,
        user_payload={
            "userPrompt": request.userPrompt,
            "rangeContext": request.rangeContext.model_dump(mode="json"),
            "profiler": profile,
        },
        response_model=ReportResponse,
        task_type="report",
        provider_mode_override=request.providerMode,
    )
    return ReportResponse(**_attach_metadata(result, request.rangeContext.warnings))
