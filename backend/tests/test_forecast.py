"""
test_forecast.py
================
Unit tests for services/forecast_service.py

Covers:
  - Return type and shape of predict_future_sales()
  - Field names and value types in each forecast record
  - Custom period count
  - Error propagation when model loading fails
  - Forecast agent trend classification
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from tests.conftest import make_forecast_df


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_model(periods: int = 7):
    """Return a MagicMock Prophet model whose predict() returns a valid df."""
    model = MagicMock()
    model.make_future_dataframe.return_value = MagicMock()
    model.predict.return_value = make_forecast_df(periods)
    return model


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPredictFutureSales:

    def test_returns_list(self):
        """predict_future_sales() must return a list."""
        from services.forecast_service import predict_future_sales

        with patch("services.forecast_service._load_or_train_model", return_value=_mock_model()):
            result = predict_future_sales(periods=7)

        assert isinstance(result, list)

    def test_returns_correct_period_count(self):
        """predict_future_sales(periods=7) must return exactly 7 items."""
        from services.forecast_service import predict_future_sales

        with patch("services.forecast_service._load_or_train_model", return_value=_mock_model(7)):
            result = predict_future_sales(periods=7)

        assert len(result) == 7

    def test_custom_period_count(self):
        """predict_future_sales(periods=3) must return exactly 3 items."""
        from services.forecast_service import predict_future_sales

        with patch("services.forecast_service._load_or_train_model", return_value=_mock_model(3)):
            result = predict_future_sales(periods=3)

        assert len(result) == 3

    def test_each_record_has_required_keys(self):
        """Every forecast record must contain ds, yhat, yhat_lower, yhat_upper."""
        from services.forecast_service import predict_future_sales

        with patch("services.forecast_service._load_or_train_model", return_value=_mock_model()):
            result = predict_future_sales(periods=7)

        required_keys = {"ds", "yhat", "yhat_lower", "yhat_upper"}
        for record in result:
            assert required_keys.issubset(record.keys()), (
                f"Missing keys in record: {required_keys - record.keys()}"
            )

    def test_yhat_is_float(self):
        """yhat values must be Python floats (JSON-serialisable)."""
        from services.forecast_service import predict_future_sales

        with patch("services.forecast_service._load_or_train_model", return_value=_mock_model()):
            result = predict_future_sales(periods=7)

        for record in result:
            assert isinstance(record["yhat"], float), (
                f"Expected float, got {type(record['yhat'])}"
            )

    def test_ds_is_yyyy_mm_dd_string(self):
        """ds must be a string in YYYY-MM-DD format."""
        from services.forecast_service import predict_future_sales

        with patch("services.forecast_service._load_or_train_model", return_value=_mock_model()):
            result = predict_future_sales(periods=7)

        for record in result:
            ds = record["ds"]
            assert isinstance(ds, str)
            parts = ds.split("-")
            assert len(parts) == 3, f"Expected YYYY-MM-DD, got: {ds}"
            assert len(parts[0]) == 4  # year
            assert len(parts[1]) == 2  # month
            assert len(parts[2]) == 2  # day

    def test_yhat_lower_lte_yhat_upper(self):
        """Confidence interval must be valid: yhat_lower <= yhat_upper."""
        from services.forecast_service import predict_future_sales

        with patch("services.forecast_service._load_or_train_model", return_value=_mock_model()):
            result = predict_future_sales(periods=7)

        for record in result:
            assert record["yhat_lower"] <= record["yhat_upper"], (
                f"Invalid interval: lower={record['yhat_lower']} > upper={record['yhat_upper']}"
            )

    def test_raises_on_model_load_failure(self):
        """predict_future_sales() must propagate exceptions from _load_or_train_model."""
        from services.forecast_service import predict_future_sales

        with patch(
            "services.forecast_service._load_or_train_model",
            side_effect=FileNotFoundError("No model or dataset found")
        ):
            with pytest.raises(FileNotFoundError):
                predict_future_sales()


class TestForecastAgent:

    def test_forecast_agent_returns_success_status(self):
        """forecast_agent() must return status=success when forecast works."""
        from agents.forecast_agent.forecast_agent import forecast_agent

        mock_predictions = [
            {"ds": f"2026-06-0{i+1}", "yhat": 100_000.0 + i * 500,
             "yhat_lower": 90_000.0, "yhat_upper": 110_000.0}
            for i in range(7)
        ]

        # forecast_agent imports predict_future_sales inside the function body,
        # so we patch it at the source module level.
        with patch("services.forecast_service.predict_future_sales",
                   return_value=mock_predictions):
            result = forecast_agent()

        assert result["status"] == "success"

    def test_forecast_agent_includes_trend(self):
        """forecast_agent() must include a trend field."""
        from agents.forecast_agent.forecast_agent import forecast_agent

        mock_predictions = [
            {"ds": f"2026-06-0{i+1}", "yhat": 100_000.0 + i * 1_000,
             "yhat_lower": 90_000.0, "yhat_upper": 110_000.0}
            for i in range(7)
        ]

        with patch("services.forecast_service.predict_future_sales",
                   return_value=mock_predictions):
            result = forecast_agent()

        assert "trend" in result
        assert "Upward" in result["trend"]  # sales increase → upward trend
