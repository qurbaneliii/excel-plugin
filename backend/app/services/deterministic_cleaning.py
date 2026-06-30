from __future__ import annotations

import re
from typing import Any

BLANK_LIKE_VALUES = {"", "na", "n/a", "null", "none", "-"}
CURRENCY_CLEAN_RE = re.compile(r"[^\d\.\-,]")


def normalize_blank(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, str) and value.strip().lower() in BLANK_LIKE_VALUES:
        return ""
    return value


def trim_text(value: Any) -> Any:
    return value.strip() if isinstance(value, str) else value


def convert_currency_string(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    cleaned = CURRENCY_CLEAN_RE.sub("", value).replace(" ", "").replace(",", "")
    if not cleaned or cleaned in {"-", ".", "-."}:
        return value
    try:
        return float(cleaned)
    except ValueError:
        return value


def convert_numeric_text(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    stripped = value.strip().replace(",", "").replace(" ", "")
    if not stripped:
        return value
    try:
        return int(stripped) if stripped.isdigit() or (stripped.startswith("-") and stripped[1:].isdigit()) else float(stripped)
    except ValueError:
        return value

