export type ProviderMode = "auto" | "openai" | "local" | "fallback";

export type ProviderMetadata = {
  provider_mode: ProviderMode;
  selected_provider: "openai" | "local" | "fallback";
  model: string | null;
  fallback_used: boolean;
  warnings: string[];
};

export type ColumnMetadata = {
  emptyCount: number;
  typeHint: "text" | "number" | "date-like" | "formula-like" | "currency-like" | "mixed" | "empty";
  distinctSampleValues: string[];
  likelyId?: boolean;
  likelyCategory?: boolean;
  likelyMeasure?: boolean;
  numericTextCount?: number;
  blankLikeCount?: number;
  whitespaceIssueCount?: number;
};

export type RangeContext = {
  worksheetName: string;
  rangeAddress: string;
  rowCount: number;
  columnCount: number;
  headers: string[];
  sampleRows: unknown[][];
  valuesPreview: unknown[][];
  metadata: Record<string, ColumnMetadata>;
  warnings: string[];
};

type ResponseBase = {
  warnings?: string[];
  provider_metadata?: ProviderMetadata;
};

export type AnalyzeRangeResponse = ResponseBase & {
  summary: string;
  table_type_guess: string;
  detected_columns: {
    name: string;
    type: string;
    confidence: number;
    issues: string[];
    emptyCount?: number;
    distinctSampleValues?: string[];
    likelyId?: boolean;
    likelyCategory?: boolean;
    likelyMeasure?: boolean;
  }[];
  data_quality_issues: {
    severity: "low" | "medium" | "high";
    issue: string;
    target_column: string;
    recommended_action: string;
  }[];
  recommended_actions: {
    action_type: string;
    target_column: string;
    description: string;
    safe_to_apply: boolean;
  }[];
  next_steps: string[];
};

export type FormulaGenerateResponse = ResponseBase & {
  formula: string;
  explanation: string;
  assumptions: string[];
};

export type FormulaExplainResponse = ResponseBase & {
  plain_english_explanation: string;
  step_by_step: string[];
  possible_issues: string[];
  simplified_formula: string;
};

export type FormulaFixResponse = ResponseBase & {
  fixed_formula: string;
  what_was_wrong: string;
};

export type ActionPlanResponse = ResponseBase & {
  plan_summary: string;
  actions: {
    id: string;
    type: string;
    target_column: string;
    description: string;
    risk_level: string;
    requires_confirmation: boolean;
  }[];
  will_write_to_new_sheet: boolean;
  blocked_actions: string[];
};

export type ReportResponse = ResponseBase & {
  title: string;
  executive_summary: string;
  key_findings: string[];
  data_quality_notes: string[];
  suggested_charts: string[];
  recommended_next_actions: string[];
};

export type HealthResponse = {
  status: string;
  backend: string;
  llm_provider_mode: ProviderMode;
};

export type LLMStatusResponse = {
  provider_mode: ProviderMode;
  openai_available: boolean;
  local_enabled: boolean;
  local_available: boolean;
  local_provider: string;
  local_base_url: string;
  local_model: string;
  fallback_available: boolean;
  warnings: string[];
};

export type LLMTestLocalResponse = {
  ok: boolean;
  provider: string;
  model: string;
  response: string | null;
  error: string | null;
};
