from __future__ import annotations

from typing import Any, Type

from pydantic import BaseModel

from ..schemas import (
    ActionPlanResponse,
    AnalyzeRangeResponse,
    DataQualityIssue,
    DetectedColumn,
    FormulaExplainResponse,
    FormulaFixResponse,
    FormulaGenerateResponse,
    RecommendedAction,
    ReportResponse,
)
from ..services.action_planner import create_deterministic_action_plan
from ..services.profiler import profile_range
from .base import LLMProvider, ProviderError


class FallbackProvider(LLMProvider):
    name = "fallback"
    model_name = "deterministic"

    def is_available(self) -> bool:
        return True

    def generate_json(
        self,
        system_prompt: str,
        user_payload: dict[str, Any],
        response_model: Type[BaseModel],
        task_type: str,
    ) -> BaseModel:
        if task_type == "range_analysis":
            context = user_payload["rangeContext"]
            profile = user_payload.get("profiler") or profile_range(context["headers"], context["sampleRows"])
            return AnalyzeRangeResponse(
                summary=f"Analyzed {context['rowCount']} rows x {context['columnCount']} columns from {context['worksheetName']}.",
                table_type_guess=profile["table_type_guess"],
                detected_columns=[DetectedColumn(**column) for column in profile["detected_columns"]],
                data_quality_issues=[DataQualityIssue(**issue) for issue in profile["issues"]],
                recommended_actions=[RecommendedAction(**action) for action in profile["recommended_actions"]],
                next_steps=[
                    "Review columns flagged as mixed or mostly blank first.",
                    "Use the cleaning plan preview before writing any cleaned data.",
                    "Generate a report after validating the sample rows.",
                ],
                warnings=["Deterministic fallback response was used."],
            )
        if task_type == "formula_generate":
            headers = user_payload.get("headers") or []
            first_column = headers[0] if headers else "ColumnA"
            return FormulaGenerateResponse(
                formula="=SUM(A:A)",
                explanation=f"Fallback formula sums the first column because no LLM response was available. Adapt it if '{first_column}' is not the target numeric field.",
                assumptions=["The target values are numeric and live in the first selected column."],
                warnings=["Deterministic fallback response was used.", "Review references before inserting the formula."],
            )
        if task_type == "formula_explain":
            formula = user_payload["formula"]
            return FormulaExplainResponse(
                plain_english_explanation="Fallback mode cannot deeply parse the formula, so this is a safe generic explanation.",
                step_by_step=[
                    "Read the formula from left to right.",
                    "Check function names, separators, and referenced cells or ranges.",
                    "Use Excel's Evaluate Formula tool for step-by-step execution.",
                ],
                possible_issues=["Deterministic fallback response was used.", "Nested functions may need manual review."],
                simplified_formula=formula,
            )
        if task_type == "formula_fix":
            return FormulaFixResponse(
                fixed_formula=user_payload["formula"],
                what_was_wrong=f"Fallback mode could not safely rewrite the formula. Reported error: {user_payload.get('error', 'unknown')}.",
                warnings=[
                    "Deterministic fallback response was used.",
                    "Check separators, balanced parentheses, and referenced column names or cells.",
                ],
            )
        if task_type == "action_plan":
            context = user_payload["rangeContext"]
            plan = create_deterministic_action_plan(context["headers"], context["sampleRows"])
            return ActionPlanResponse(**plan, warnings=["Deterministic fallback response was used."])
        if task_type == "report":
            context = user_payload["rangeContext"]
            profile = user_payload.get("profiler") or profile_range(context["headers"], context["sampleRows"])
            return ReportResponse(
                title=f"AI Report - {context['worksheetName']}",
                executive_summary=(
                    f"The selected range contains {context['rowCount']} rows and {context['columnCount']} columns. "
                    "This report was generated from sampled rows and deterministic profiling."
                ),
                key_findings=[
                    f"Table type guess: {profile['table_type_guess']}.",
                    f"Sampled issue count: {len(profile['issues'])}.",
                    f"Duplicate-looking sampled rows: {profile['duplicate_row_count']}.",
                ],
                data_quality_notes=[issue["issue"] for issue in profile["issues"]] or ["No major sampled issues detected."],
                suggested_charts=["Use a pivot or grouped totals chart when you have one category column and one numeric measure column."],
                recommended_next_actions=[
                    "Validate the sampled anomalies in the original sheet.",
                    "Write cleaned output to a new sheet only.",
                ],
                warnings=["Deterministic fallback response was used."],
            )
        raise ProviderError(f"Fallback provider does not support task type '{task_type}'.")

    def generate_text(self, system_prompt: str, user_prompt: str, task_type: str) -> str:
        return "Deterministic fallback mode does not generate free-form text."
