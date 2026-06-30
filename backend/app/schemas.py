from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ProviderMode = Literal["auto", "openai", "local", "fallback"]
Severity = Literal["low", "medium", "high"]
ColumnType = Literal["text", "number", "date-like", "formula-like", "currency-like", "mixed", "empty"]
ActionType = Literal[
    "trim_text",
    "normalize_blanks",
    "convert_currency_to_number",
    "convert_numeric_text_to_number",
    "standardize_date_text",
    "remove_duplicate_rows",
    "create_issues_sheet",
    "create_summary_sheet",
    "unknown",
]


class ProviderMetadata(BaseModel):
    provider_mode: ProviderMode
    selected_provider: Literal["openai", "local", "fallback"]
    model: str | None = None
    fallback_used: bool = False
    warnings: list[str] = Field(default_factory=list)


class ColumnMetadata(BaseModel):
    emptyCount: int = 0
    typeHint: ColumnType = "mixed"
    distinctSampleValues: list[str] = Field(default_factory=list)
    likelyId: bool = False
    likelyCategory: bool = False
    likelyMeasure: bool = False
    numericTextCount: int = 0
    blankLikeCount: int = 0
    whitespaceIssueCount: int = 0


class RangeContext(BaseModel):
    worksheetName: str
    rangeAddress: str
    rowCount: int
    columnCount: int
    headers: list[str]
    sampleRows: list[list[Any]]
    valuesPreview: list[list[Any]]
    metadata: dict[str, ColumnMetadata]
    warnings: list[str] = Field(default_factory=list)


class RequestBase(BaseModel):
    providerMode: ProviderMode | None = None


class PromptedRangeRequest(RequestBase):
    userPrompt: str
    rangeContext: RangeContext


class DetectedColumn(BaseModel):
    name: str
    type: str
    confidence: float
    issues: list[str]
    emptyCount: int = 0
    distinctSampleValues: list[str] = Field(default_factory=list)
    likelyId: bool = False
    likelyCategory: bool = False
    likelyMeasure: bool = False


class DataQualityIssue(BaseModel):
    severity: Severity
    issue: str
    target_column: str
    recommended_action: str


class RecommendedAction(BaseModel):
    action_type: str
    target_column: str
    description: str
    safe_to_apply: bool


class ResponseBase(BaseModel):
    warnings: list[str] = Field(default_factory=list)
    provider_metadata: ProviderMetadata | None = None


class AnalyzeRangeResponse(ResponseBase):
    summary: str
    table_type_guess: str
    detected_columns: list[DetectedColumn]
    data_quality_issues: list[DataQualityIssue]
    recommended_actions: list[RecommendedAction]
    next_steps: list[str]


class FormulaGenerateRequest(RequestBase):
    userPrompt: str
    headers: list[str]
    sampleRows: list[list[Any]]


class FormulaGenerateResponse(ResponseBase):
    formula: str
    explanation: str
    assumptions: list[str]


class FormulaExplainRequest(RequestBase):
    formula: str
    headers: list[str]
    sampleRows: list[list[Any]]


class FormulaExplainResponse(ResponseBase):
    plain_english_explanation: str
    step_by_step: list[str]
    possible_issues: list[str]
    simplified_formula: str


class FormulaFixRequest(RequestBase):
    formula: str
    error: str
    headers: list[str]
    sampleRows: list[list[Any]]


class FormulaFixResponse(ResponseBase):
    fixed_formula: str
    what_was_wrong: str


class ActionPlan(BaseModel):
    id: str
    type: ActionType
    target_column: str
    description: str
    risk_level: Severity
    requires_confirmation: bool


class ActionPlanResponse(ResponseBase):
    plan_summary: str
    actions: list[ActionPlan]
    will_write_to_new_sheet: bool
    blocked_actions: list[str]


class ReportResponse(ResponseBase):
    title: str
    executive_summary: str
    key_findings: list[str]
    data_quality_notes: list[str]
    suggested_charts: list[str]
    recommended_next_actions: list[str]


class LLMStatusResponse(BaseModel):
    provider_mode: ProviderMode
    openai_available: bool
    local_enabled: bool
    local_available: bool
    local_provider: str
    local_base_url: str
    local_model: str
    fallback_available: bool
    warnings: list[str] = Field(default_factory=list)


class LLMTestLocalRequest(BaseModel):
    prompt: str


class LLMTestLocalResponse(BaseModel):
    ok: bool
    provider: str
    model: str
    response: str | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    status: str
    backend: str
    llm_provider_mode: ProviderMode
