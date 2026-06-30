from __future__ import annotations

import re
from collections import Counter
from typing import Any

BLANK_LIKE_VALUES = {"", "na", "n/a", "null", "none", "-"}
CURRENCY_RE = re.compile(r"^\s*(?:[A-Z]{3}|\u20bc|\$|€|£)?\s*[-+]?\d[\d,\s]*(?:\.\d+)?\s*(?:[A-Z]{3}|\u20bc|\$|€|£)?\s*$")
DATE_RE = re.compile(r"^\s*\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}\s*$")
ID_HEADER_RE = re.compile(r"\b(id|code|sku|invoice|order|account|ref)\b", re.IGNORECASE)
CATEGORY_HEADER_RE = re.compile(r"\b(category|segment|region|status|type|team|department)\b", re.IGNORECASE)
MEASURE_HEADER_RE = re.compile(r"\b(amount|revenue|sales|total|count|price|cost|quantity|qty|score)\b", re.IGNORECASE)


def normalize_scalar(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def is_blank_like(value: Any) -> bool:
    return normalize_scalar(value).lower() in BLANK_LIKE_VALUES


def classify_value(value: Any) -> str:
    if value is None or is_blank_like(value):
        return "blank"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return "number"
    text = normalize_scalar(value)
    if text.startswith("="):
        return "formula-like"
    if CURRENCY_RE.match(text):
        return "currency-like"
    if DATE_RE.match(text):
        return "date-like"
    try:
        float(text.replace(",", "").replace(" ", ""))
        return "number-text"
    except ValueError:
        return "text"


def infer_column_type(values: list[Any]) -> str:
    non_blank_types = [classify_value(value) for value in values if not is_blank_like(value)]
    if not non_blank_types:
        return "empty"
    counts = Counter(non_blank_types)
    if counts["formula-like"] >= max(1, len(non_blank_types) * 0.7):
        return "formula-like"
    if counts["currency-like"] >= max(1, len(non_blank_types) * 0.5):
        return "currency-like"
    if counts["date-like"] >= max(1, len(non_blank_types) * 0.5):
        return "date-like"
    if counts["number"] + counts["number-text"] >= max(1, len(non_blank_types) * 0.7):
        return "number"
    if counts["text"] >= max(1, len(non_blank_types) * 0.7):
        return "text"
    return "mixed"


def _distinct_values(values: list[Any], limit: int = 5) -> list[str]:
    distinct: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = normalize_scalar(value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        distinct.append(normalized)
        if len(distinct) >= limit:
            break
    return distinct


def profile_range(headers: list[str], sample_rows: list[list[Any]]) -> dict[str, Any]:
    if not headers:
        return {
            "table_type_guess": "unknown",
            "detected_columns": [],
            "issues": [],
            "recommended_actions": [],
            "duplicate_row_count": 0,
            "summary_signals": {},
        }

    columns = list(zip(*sample_rows, strict=False)) if sample_rows else [[] for _ in headers]
    detected_columns: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    recommended_actions: list[dict[str, Any]] = []
    signals = {
        "possible_id_columns": [],
        "possible_category_columns": [],
        "possible_measure_columns": [],
        "blank_like_columns": [],
        "mixed_type_columns": [],
    }

    for index, header in enumerate(headers):
        column_values = list(columns[index]) if index < len(columns) else []
        inferred = infer_column_type(column_values)
        empty_count = sum(1 for value in column_values if is_blank_like(value))
        blank_like_count = empty_count
        numeric_text_count = sum(1 for value in column_values if classify_value(value) == "number-text")
        whitespace_issue_count = sum(
            1 for value in column_values if isinstance(value, str) and value != value.strip()
        )
        issues_for_column: list[str] = []
        distinct_values = _distinct_values(column_values)
        non_blank_values = [value for value in column_values if not is_blank_like(value)]
        unique_count = len({normalize_scalar(value) for value in non_blank_values})
        likely_id = bool(ID_HEADER_RE.search(header)) or (
            unique_count >= max(1, len(non_blank_values) * 0.8) and inferred in {"text", "number"}
        )
        likely_category = bool(CATEGORY_HEADER_RE.search(header)) or (
            1 < unique_count <= max(2, len(non_blank_values) * 0.5) and inferred == "text"
        )
        likely_measure = bool(MEASURE_HEADER_RE.search(header)) or inferred in {"number", "currency-like"}

        if inferred == "empty":
            issues_for_column.append("Column appears empty in sampled rows.")
            signals["blank_like_columns"].append(header)
            issues.append(
                {
                    "severity": "medium",
                    "issue": "Column is empty or blank-like in sampled rows.",
                    "target_column": header,
                    "recommended_action": "Review whether the column should be removed or backfilled.",
                }
            )
        if inferred == "mixed":
            issues_for_column.append("Mixed value types detected.")
            signals["mixed_type_columns"].append(header)
            issues.append(
                {
                    "severity": "high",
                    "issue": "Mixed data types detected.",
                    "target_column": header,
                    "recommended_action": "Standardize formats before downstream analysis.",
                }
            )
        if blank_like_count and len(column_values) and blank_like_count / max(1, len(column_values)) >= 0.3:
            issues_for_column.append("Many blank-like values.")
            if header not in signals["blank_like_columns"]:
                signals["blank_like_columns"].append(header)
            issues.append(
                {
                    "severity": "medium",
                    "issue": "High share of blank-like values.",
                    "target_column": header,
                    "recommended_action": "Normalize blanks and validate completeness.",
                }
            )
            recommended_actions.append(
                {
                    "action_type": "normalize_blanks",
                    "target_column": header,
                    "description": "Normalize blank-like values to empty cells.",
                    "safe_to_apply": True,
                }
            )
        if whitespace_issue_count:
            issues_for_column.append("Whitespace inconsistencies found.")
            issues.append(
                {
                    "severity": "low",
                    "issue": "Leading or trailing whitespace detected.",
                    "target_column": header,
                    "recommended_action": "Trim leading and trailing whitespace.",
                }
            )
            recommended_actions.append(
                {
                    "action_type": "trim_text",
                    "target_column": header,
                    "description": "Trim leading and trailing whitespace.",
                    "safe_to_apply": True,
                }
            )
        if inferred == "currency-like":
            recommended_actions.append(
                {
                    "action_type": "convert_currency_to_number",
                    "target_column": header,
                    "description": "Convert currency strings to numeric values.",
                    "safe_to_apply": True,
                }
            )
        if numeric_text_count:
            issues_for_column.append("Numeric-looking text values found.")
            recommended_actions.append(
                {
                    "action_type": "convert_numeric_text_to_number",
                    "target_column": header,
                    "description": "Convert numeric-looking text values to numbers when safe.",
                    "safe_to_apply": True,
                }
            )
        if inferred == "date-like":
            recommended_actions.append(
                {
                    "action_type": "standardize_date_text",
                    "target_column": header,
                    "description": "Standardize date text into a consistent format.",
                    "safe_to_apply": False,
                }
            )
        if likely_id:
            signals["possible_id_columns"].append(header)
        if likely_category:
            signals["possible_category_columns"].append(header)
        if likely_measure:
            signals["possible_measure_columns"].append(header)

        detected_columns.append(
            {
                "name": header,
                "type": inferred,
                "confidence": 0.9 if inferred not in {"mixed", "text"} else 0.7,
                "issues": issues_for_column,
                "emptyCount": empty_count,
                "distinctSampleValues": distinct_values,
                "likelyId": likely_id,
                "likelyCategory": likely_category,
                "likelyMeasure": likely_measure,
            }
        )

    normalized_rows = [tuple(normalize_scalar(cell) for cell in row) for row in sample_rows]
    duplicate_row_count = len(normalized_rows) - len(set(normalized_rows))
    if duplicate_row_count > 0:
        issues.append(
            {
                "severity": "medium",
                "issue": "Potential duplicate rows detected in sampled rows.",
                "target_column": "*row*",
                "recommended_action": "Review duplicate rows before reporting.",
            }
        )
        recommended_actions.append(
            {
                "action_type": "remove_duplicate_rows",
                "target_column": "*row*",
                "description": "Remove exact duplicate rows while preserving the first occurrence.",
                "safe_to_apply": True,
            }
        )

    if signals["possible_category_columns"] and signals["possible_measure_columns"]:
        recommended_actions.append(
            {
                "action_type": "create_summary_sheet",
                "target_column": "*table*",
                "description": "Create a grouped summary sheet for category and measure columns.",
                "safe_to_apply": True,
            }
        )

    if issues:
        recommended_actions.append(
            {
                "action_type": "create_issues_sheet",
                "target_column": "*table*",
                "description": "Write detected cleaning issues to a separate sheet during apply.",
                "safe_to_apply": True,
            }
        )

    table_type_guess = "general_table"
    lower_headers = " ".join(header.lower() for header in headers)
    if any(word in lower_headers for word in ("date", "sales", "amount", "revenue", "price")):
        table_type_guess = "business_metrics_table"
    elif any(word in lower_headers for word in ("email", "phone", "customer", "name")):
        table_type_guess = "customer_dataset"
    elif signals["possible_category_columns"] and signals["possible_measure_columns"]:
        table_type_guess = "summary_ready_table"

    return {
        "table_type_guess": table_type_guess,
        "detected_columns": detected_columns,
        "issues": issues,
        "recommended_actions": recommended_actions,
        "duplicate_row_count": duplicate_row_count,
        "summary_signals": signals,
    }
