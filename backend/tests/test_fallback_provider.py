from app.llm.fallback_provider import FallbackProvider
from app.schemas import AnalyzeRangeResponse, FormulaGenerateResponse, ReportResponse


def test_fallback_provider_returns_schema_safe_analysis() -> None:
    provider = FallbackProvider()
    payload = {
        "rangeContext": {
            "worksheetName": "Sheet1",
            "rowCount": 3,
            "columnCount": 2,
            "headers": ["Region", "Amount"],
            "sampleRows": [["North", "100"], ["South", "200"]],
        }
    }

    result = provider.generate_json("", payload, AnalyzeRangeResponse, "range_analysis")

    assert isinstance(result, AnalyzeRangeResponse)
    assert result.summary


def test_fallback_provider_returns_formula_and_report() -> None:
    provider = FallbackProvider()
    formula = provider.generate_json("", {"headers": ["Amount"]}, FormulaGenerateResponse, "formula_generate")
    report = provider.generate_json(
        "",
        {"rangeContext": {"worksheetName": "Sheet1", "rowCount": 3, "columnCount": 1, "headers": ["Amount"], "sampleRows": [["100"], ["200"]]}},
        ReportResponse,
        "report",
    )

    assert formula.formula.startswith("=")
    assert report.title.startswith("AI Report")
