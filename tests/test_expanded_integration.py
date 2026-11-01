from datetime import date

from openpyxl import load_workbook

from packages.core.io import ROOT, read_json
from packages.forecast.expanded import daily, monthly
from scripts.build_expanded import run


def test_full_pipeline_smoke_conserves_money_and_exports_formulas(tmp_path):
    result = run(3, tmp_path / "data", tmp_path / "exports")
    assert result["mode"] == "development_smoke"
    assert len(result["allocation"]) == 7
    assert (
        sum(row["methods"]["usage"] for row in result["allocation"])
        == result["generation"]["total_micro"]
    )
    assert (
        sum(row["fully_loaded_micro"] for row in result["units"])
        == result["generation"]["total_micro"]
    )
    assert len(result["recommendations"]["actions"]) == 7
    assert result["recommendations"]["joint_recovered_micro"] > 0
    book = load_workbook(tmp_path / "exports/allocation.xlsx")
    sheet = book["Allocation"]
    assert sheet["B2"].value == "usage"
    assert sheet["I6"].value == "=C6+H6"
    assert "SUMIF" in sheet["H6"].value
    assert result["exports"]["focus_rows"]["AllocatedCostAndUsage"] >= result["generation"]["rows"]


def test_rolling_forecast_and_monthly_cutoffs():
    config = read_json(ROOT / "evaluation/v2/plan.json")["forecast"]
    values = [100.0 + (i % 7) * 2 for i in range(151)]
    result = daily(values, values, date(2025, 1, 1), 90, config)
    assert result["rows"][0]["date"] == "2025-04-01"
    assert len(result["development_mae"]) == 3
    forecasts = monthly(values, values, date(2025, 1, 1), 90, result["method"], config)
    assert forecasts[0]["data_cutoff"] == "2025-03-31"
    assert forecasts[0]["lower"] <= forecasts[0]["point"] <= forecasts[0]["upper"]
    changed = values[:90] + [10000.0] * 61
    first = daily(changed, changed, date(2025, 1, 1), 90, config)
    assert first["method"] == result["method"]
    assert first["rows"][0]["point"] == result["rows"][0]["point"]
