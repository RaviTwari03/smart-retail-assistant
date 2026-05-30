"""
Tests for Forecast Service
===========================
Verifies Prophet-based forecasting returns correct structure and values.
"""

import pytest
from unittest.mock import patch, MagicMock


# =========================
# UNIT TESTS - forecast_service
# =========================

class TestPredictFutureSales:

    def test_returns_list(self):
        """predict_future_sales() must return a list."""
        from services.forecast_service import predict_future_sales

        with patch("services.forecast_service._load_or_train_model") as mock_model:
            mock_prophet = MagicMock()
            mock_prophet.make_future_dataframe.return_value = MagicMock()

            import pandas as pd
            from datetime import date, timedelta

            future_dates = pd.date_range(start="2026-06-01", periods=7, freq="W")
            mock_forecast = pd.DataFrame({
                "ds": future_dates,
                "yhat": [100000.0, 102000.0, 98000.0, 105000.0, 103000.0, 107000.0, 110000.0],
                "yhat_lower": [90000.0] * 7,
                "yhat_upper": [120000.0] * 7
            })

            mock_prophet.predict.return_value = mock_forecast
            mock_model.return_value = mock_prophet

            result = predict_future_sales(periods=7)

        assert isinstance(result, list)

    def test_returns_correct_number_of_periods(self):
        """predict_future_sales(periods=7) must return exactly 7 items."""
        from services.forecast_service import predict_future_sales

        with patch("services.forecast_service._load_or_train_model") as mock_model:
            mock_prophet = MagicMock()

            import pandas as pd
            future_dates = pd.date_range(start="2026-06-01", periods=7, freq="W")
            mock_forecast = pd.DataFrame({
                "ds": future_dates,
                "yhat": [100000.0] * 7,
                "yhat_lower": [90000.0] * 7,
                "yhat_upper": [110000.0] * 7
            })

            mock_prophet.predict.return_value = mock_forecast
            mock_model.return_value = mock_prophet

            result = predict_future_sales(periods=7)

        assert len(result) == 7

    def test_each_item_has_required_keys(self):
        """Each forecast item must have ds, yhat, yhat_lower, yhat_upper."""
        from services.forecast_service import predict_future_sales

        with patch("services.forecast_service._load_or_train_model") as mock_model:
            mock_prophet = MagicMock()

            import pandas as pd
            future_dates = pd.date_range(start="2026-06-01", periods=7, freq="W")
            mock_forecast = pd.DataFrame({
                "ds": future_dates,
                "yhat": [100000.0] * 7,
                "yhat_lower": [90000.0] * 7,
                "yhat_upper": [110000.0] * 7
            })

            mock_prophet.predict.return_value = mock_forecast
            mock_model.return_value = mock_prophet

            result = predict_future_sales(periods=7)

        for item in result:
            assert "ds" in item
            assert "yhat" in item
            assert "yhat_lower" in item
            assert "yhat_upper" in item

    def test_yhat_is_numeric(self):
        """yhat values must be floats."""
        from services.forecast_service import predict_future_sales

        with patch("services.forecast_service._load_or_train_model") as mock_model:
            mock_prophet = MagicMock()

            import pandas as pd
            future_dates = pd.date_range(start="2026-06-01", periods=7, freq="W")
            mock_forecast = pd.DataFrame({
                "ds": future_dates,
                "yhat": [100000.0] * 7,
                "yhat_lower": [90000.0] * 7,
                "yhat_upper": [110000.0] * 7
            })

            mock_prophet.predict.return_value = mock_forecast
            mock_model.return_value = mock_prophet

            result = predict_future_sales(periods=7)

        for item in result:
            assert isinstance(item["yhat"], float)

    def test_ds_is_string_date(self):
        """ds values must be string dates in YYYY-MM-DD format."""
        from services.forecast_service import predict_future_sales

        with patch("services.forecast_service._load_or_train_model") as mock_model:
            mock_prophet = MagicMock()

            import pandas as pd
            future_dates = pd.date_range(start="2026-06-01", periods=7, freq="W")
            mock_forecast = pd.DataFrame({
                "ds": future_dates,
                "yhat": [100000.0] * 7,
                "yhat_lower": [90000.0] * 7,
                "yhat_upper": [110000.0] * 7
            })

            mock_prophet.predict.return_value = mock_forecast
            mock_model.return_value = mock_prophet

            result = predict_future_sales(periods=7)

        for item in result:
            assert isinstance(item["ds"], str)
            # Must be parseable as a date
            from datetime import date
            parts = item["ds"].split("-")
            assert len(parts) == 3
