from app.schemas import FormulaGenerateRequest, ProviderMetadata, RangeContext


def test_range_context_schema() -> None:
    payload = RangeContext(
        worksheetName="Sheet1",
        rangeAddress="A1:B3",
        rowCount=3,
        columnCount=2,
        headers=["A", "B"],
        sampleRows=[[1, 2]],
        valuesPreview=[[1, 2]],
        metadata={"A": {"emptyCount": 0, "typeHint": "number", "distinctSampleValues": ["1"]}},
        warnings=[],
    )
    request = FormulaGenerateRequest(userPrompt="sum it", headers=payload.headers, sampleRows=payload.sampleRows, providerMode="auto")
    metadata = ProviderMetadata(
        provider_mode="auto",
        selected_provider="fallback",
        model="deterministic",
        fallback_used=True,
        warnings=["fallback"],
    )
    assert request.headers == ["A", "B"]
    assert metadata.selected_provider == "fallback"
