from app.services.profiler import profile_range


def test_profiler_detects_currency_duplicates_and_summary_signals() -> None:
    headers = ["Customer ID", "Region", "Amount"]
    rows = [
        ["C001", " North ", "AZN 1200"],
        ["C002", "North", "1,200 AZN"],
        ["C001", " North ", "AZN 1200"],
    ]

    profile = profile_range(headers, rows)

    assert profile["table_type_guess"] in {"business_metrics_table", "summary_ready_table", "general_table"}
    assert any(column["type"] == "currency-like" for column in profile["detected_columns"])
    assert profile["duplicate_row_count"] >= 1
    assert "Customer ID" in profile["summary_signals"]["possible_id_columns"]
    assert "Region" in profile["summary_signals"]["possible_category_columns"]
    assert "Amount" in profile["summary_signals"]["possible_measure_columns"]
