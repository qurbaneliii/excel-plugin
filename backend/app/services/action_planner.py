from __future__ import annotations

from .profiler import profile_range


def create_deterministic_action_plan(headers: list[str], sample_rows: list[list[object]]) -> dict[str, object]:
    profile = profile_range(headers, sample_rows)
    actions = []
    seen_pairs: set[tuple[str, str]] = set()

    for index, action in enumerate(profile["recommended_actions"], start=1):
        pair = (action["action_type"], action["target_column"])
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        actions.append(
            {
                "id": f"action_{index}",
                "type": action["action_type"] if action["action_type"] in {
                    "trim_text",
                    "normalize_blanks",
                    "convert_currency_to_number",
                    "convert_numeric_text_to_number",
                    "standardize_date_text",
                    "remove_duplicate_rows",
                    "create_issues_sheet",
                    "create_summary_sheet",
                } else "unknown",
                "target_column": action["target_column"],
                "description": action["description"],
                "risk_level": "low" if action["safe_to_apply"] else "medium",
                "requires_confirmation": True,
            }
        )

    blocked_actions = []
    if not actions:
        blocked_actions.append("No deterministic cleaning actions were detected from the sampled rows.")

    return {
        "plan_summary": "Deterministic cleaning plan based on sampled rows and profiler signals.",
        "actions": actions,
        "will_write_to_new_sheet": True,
        "blocked_actions": blocked_actions,
    }
