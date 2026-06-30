from __future__ import annotations

import json
from typing import Any, Type

from pydantic import BaseModel, ValidationError

from .base import ProviderError


def extract_json_object(text: str) -> str:
    stripped = (text or "").strip()
    if not stripped:
        raise ProviderError("Model returned an empty response.")
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped

    start = stripped.find("{")
    if start == -1:
        raise ProviderError("Model response did not contain a JSON object.")

    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(stripped)):
        char = stripped[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return stripped[start : index + 1]

    raise ProviderError("Model response contained incomplete JSON.")


def validate_response_model(content: str, response_model: Type[BaseModel]) -> BaseModel:
    try:
        return response_model.model_validate_json(content)
    except ValidationError as exc:
        raise ProviderError(f"Model JSON did not match schema: {exc}") from exc


def dump_payload(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=True)


def normalize_json_text(text: str) -> str:
    return extract_json_object(text)
