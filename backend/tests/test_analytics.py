"""
test_analytics.py
=================
Tests for the Power BI analytics endpoints and analytics_service.py

Covers:
  - GET /analytics/revenue
  - GET /analytics/inventory
  - GET /analytics/forecast
  - GET /analytics/agent-insights
  - analytics_service unit tests (KPI shapes, field types, series structure)
"""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from tests.conftest import make_forecast_df


# ---------------------------------------------------------------------------
# Shared mock Walmart DataFrame
# ---------------------------------------------------------------------------

def _mock_walmart_df():
    """Minimal Walmart-shaped DataFrame for unit tests."""
    return pd.DataFrame({
        "Store":        [1, 1, 2, 2, 3, 3],
        "Date":         pd.to_datetime([
                            "2010-02-05", "2010-02-12",
                            "2010-02-05", "2010-02-12",
                            "2010-02-05", "2010-02-12"
                        ]),
        "Weekly_Sales": [1_643_690.90, 1_641_957.44,
                         1_200_000.00, 1_350_000.00,
                         900_000.00,   950_000.00],
        "Holiday_Flag": [0, 1, 0, 1, 0, 0],
        "Temperature":  [42.31, 38.51, 45.0, 40.0, 50.0, 48.0],
        "Fuel_Price":   [2.572, 2.548, 2.6, 2.55, 2.7, 2.65],
        "CPI":          [211.09, 211.24, 212.0, 212.5, 213.0, 213.5],
        "Unemployment": [8.106, 8.106, 7.8, 7.8, 8.0, 8.0],
    })


# ---------------------------------------------------------------------------
# analytics_service unit tests
# ---------------------------------------------------------------------------

class TestRevenueAnalyticsService:

    def test_kpis_present(self):
        """get_revenue_analytics() must return a kpis dict with required keys."""
        with patch("services.analytics_service._load_walmart", return_value=_mock_walmart_df()):
            from services.analytics_service import get_revenue_analytics
            result = get_revenue_analytics()

        kpis = result["kpis"]
        required = {
            "total_revenue", "avg_weekly_revenue", "peak_weekly_revenue",
            "peak_week_date", "total_stores", "total_weeks",
            "holiday_revenue", "non_holiday_revenue", "holiday_lift_pct"
        }
        assert required.issubset(kpis.keys())

    def test_total_revenue_is_positive(self):
        """total_revenue must be a positive float."""
        with patch("services.analytics_service._load_walmart", return_value=_mock_walmart_df()):
            from services.analytics_service import get_revenue_analytics
            result = get_revenue_analytics()

        assert result["kpis"]["total_revenue"] > 0

    def test_weekly_trend_is_list(self):
        """weekly_trend must be a non-empty list."""
        with patch("services.analytics_service._load_walmart", return_value=_mock_walmart_df()):
            from services.analytics_service import get_revenue_analytics
            result = get_revenue_analytics()

        assert isinstance(result["weekly_trend"], list)
        assert len(result["weekly_trend"]) > 0

    def test_weekly_trend_record_shape(self):
        """Each weekly_trend record must have date, total_sales, is_holiday."""
        with patch("services.analytics_service._load_walmart", return_value=_mock_walmart_df()):
            from services.analytics_service import get_revenue_analytics
            result = get_revenue_analytics()

        for record in result["weekly_trend"]:
            assert "date" in record
            assert "total_sales" in record
            assert "is_holiday" in record
            assert isinstance(record["total_sales"], float)
            assert isinstance(record["is_holiday"], bool)

    def test_top_stores_has_rank(self):
        """Each top_stores entry must have store_id, total_sales, rank."""
        with patch("services.analytics_service._load_walmart", return_value=_mock_walmart_df()):
            from services.analytics_service import get_revenue_analytics
            result = get_revenue_analytics()

        for store in result["top_stores"]:
            assert "store_id" in store
            assert "total_sales" in store
            assert "rank" in store

    def test_monthly_summary_is_list(self):
        """monthly_summary must be a list."""
        with patch("services.analytics_service._load_walmart", return_value=_mock_walmart_df()):
            from services.analytics_service import get_revenue_analytics
            result = get_revenue_analytics()

        assert isinstance(result["monthly_summary"], list)

    def test_generated_at_is_string(self):
        """generated_at must be an ISO timestamp string."""
        with patch("services.analytics_service._load_walmart", return_value=_mock_walmart_df()):
            from services.analytics_service import get_revenue_analytics
            result = get_revenue_analytics()

        assert isinstance(result["generated_at"], str)
        assert "T" in result["generated_at"]  # ISO format


class TestInventoryAnalyticsService:

    def test_kpis_present(self):
        """get_inventory_analytics() must return required KPI keys."""
        with patch("services.analytics_service._load_walmart", return_value=_mock_walmart_df()), \
             patch("services.analytics_service.detect_anomalies", return_value=[
                 {"sales": 1_000_000.0, "is_anomaly": False},
                 {"sales": 500.0, "is_anomaly": True},
             ]):
            from services.analytics_service import get_inventory_analytics
            result = get_inventory_analytics()

        kpis = result["kpis"]
        required = {
            "total_stores", "critical_stock_stores", "warning_stock_stores",
            "stable_stock_stores", "avg_unemployment", "avg_fuel_price", "avg_cpi"
        }
        assert required.issubset(kpis.keys())

    def test_store_inventory_status_is_list(self):
        """store_inventory_status must be a list with one entry per store."""
        with patch("services.analytics_service._load_walmart", return_value=_mock_walmart_df()), \
             patch("services.analytics_service.detect_anomalies", return_value=[]):
            from services.analytics_service import get_inventory_analytics
            result = get_inventory_analytics()

        assert isinstance(result["store_inventory_status"], list)
        assert len(result["store_inventory_status"]) == 3  # 3 stores in mock

    def test_store_status_values_are_valid(self):
        """stock_status must be one of Critical / Warning / Stable."""
        with patch("services.analytics_service._load_walmart", return_value=_mock_walmart_df()), \
             patch("services.analytics_service.detect_anomalies", return_value=[]):
            from services.analytics_service import get_inventory_analytics
            result = get_inventory_analytics()

        valid_statuses = {"Critical", "Warning", "Stable"}
        for store in result["store_inventory_status"]:
            assert store["stock_status"] in valid_statuses

    def test_anomaly_summary_present(self):
        """anomaly_summary must contain total_weeks_analysed and anomaly_rate_pct."""
        with patch("services.analytics_service._load_walmart", return_value=_mock_walmart_df()), \
             patch("services.analytics_service.detect_anomalies", return_value=[
                 {"is_anomaly": False}, {"is_anomaly": True}
             ]):
            from services.analytics_service import get_inventory_analytics
            result = get_inventory_analytics()

        summary = result["anomaly_summary"]
        assert "total_weeks_analysed" in summary
        assert "anomaly_weeks" in summary
        assert "anomaly_rate_pct" in summary

    def test_economic_indicators_is_list(self):
        """economic_indicators must be a list of dicts with date, fuel_price, cpi, unemployment."""
        with patch("services.analytics_service._load_walmart", return_value=_mock_walmart_df()), \
             patch("services.analytics_service.detect_anomalies", return_value=[]):
            from services.analytics_service import get_inventory_analytics
            result = get_inventory_analytics()

        assert isinstance(result["economic_indicators"], list)
        for record in result["economic_indicators"]:
            assert "date" in record
            assert "fuel_price" in record
            assert "cpi" in record
            assert "unemployment" in record


class TestForecastAnalyticsService:

    def _mock_predictions(self):
        return [
            {"ds": f"2026-06-0{i+1}", "yhat": 100_000.0 + i * 1_000,
             "yhat_lower": 90_000.0, "yhat_upper": 110_000.0}
            for i in range(7)
        ]

    def test_kpis_present(self):
        """get_forecast_analytics() must return required KPI keys."""
        with patch("services.analytics_service.predict_future_sales",
                   return_value=self._mock_predictions()), \
             patch("services.analytics_service._load_walmart", return_value=_mock_walmart_df()):
            from services.analytics_service import get_forecast_analytics
            result = get_forecast_analytics()

        kpis = result["kpis"]
        required = {
            "forecast_periods", "next_week_forecast", "peak_forecast_value",
            "peak_forecast_date", "min_forecast_value", "min_forecast_date",
            "avg_forecast_value", "trend_direction", "trend_change_pct"
        }
        assert required.issubset(kpis.keys())

    def test_trend_direction_is_valid(self):
        """trend_direction must be Upward, Downward, or Stable."""
        with patch("services.analytics_service.predict_future_sales",
                   return_value=self._mock_predictions()), \
             patch("services.analytics_service._load_walmart", return_value=_mock_walmart_df()):
            from services.analytics_service import get_forecast_analytics
            result = get_forecast_analytics()

        assert result["kpis"]["trend_direction"] in {"Upward", "Downward", "Stable"}

    def test_forecast_series_has_confidence_width(self):
        """Each forecast_series record must include confidence_width."""
        with patch("services.analytics_service.predict_future_sales",
                   return_value=self._mock_predictions()), \
             patch("services.analytics_service._load_walmart", return_value=_mock_walmart_df()):
            from services.analytics_service import get_forecast_analytics
            result = get_forecast_analytics()

        for record in result["forecast_series"]:
            assert "confidence_width" in record
            assert record["confidence_width"] >= 0

    def test_historical_vs_forecast_has_type_field(self):
        """historical_vs_forecast records must have a type field = historical or forecast."""
        with patch("services.analytics_service.predict_future_sales",
                   return_value=self._mock_predictions()), \
             patch("services.analytics_service._load_walmart", return_value=_mock_walmart_df()):
            from services.analytics_service import get_forecast_analytics
            result = get_forecast_analytics()

        types = {r["type"] for r in result["historical_vs_forecast"]}
        assert "historical" in types
        assert "forecast" in types


class TestAgentInsightsService:

    def test_kpis_present(self):
        """get_agent_insights() must return required KPI keys."""
        with patch("services.analytics_service.SessionLocal") as mock_session, \
             patch("services.analytics_service.list_documents", return_value=["faq.pdf"]), \
             patch("services.analytics_service.os.path.exists", return_value=True):

            mock_db = MagicMock()
            mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
            mock_db.query.return_value.count.return_value = 5
            mock_session.return_value = mock_db

            from services.analytics_service import get_agent_insights
            result = get_agent_insights()

        kpis = result["kpis"]
        required = {
            "total_chats", "knowledge_base_documents",
            "vector_db_exists", "agents_available", "rag_enabled"
        }
        assert required.issubset(kpis.keys())

    def test_agent_registry_has_5_agents(self):
        """agent_registry must list all 5 agents."""
        with patch("services.analytics_service.SessionLocal") as mock_session, \
             patch("services.analytics_service.list_documents", return_value=[]), \
             patch("services.analytics_service.os.path.exists", return_value=False):

            mock_db = MagicMock()
            mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
            mock_db.query.return_value.count.return_value = 0
            mock_session.return_value = mock_db

            from services.analytics_service import get_agent_insights
            result = get_agent_insights()

        assert len(result["agent_registry"]) == 5

    def test_rag_pipeline_status_present(self):
        """rag_pipeline_status must include embedding_model and chunk_size."""
        with patch("services.analytics_service.SessionLocal") as mock_session, \
             patch("services.analytics_service.list_documents", return_value=[]), \
             patch("services.analytics_service.os.path.exists", return_value=True):

            mock_db = MagicMock()
            mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
            mock_db.query.return_value.count.return_value = 0
            mock_session.return_value = mock_db

            from services.analytics_service import get_agent_insights
            result = get_agent_insights()

        rag = result["rag_pipeline_status"]
        assert rag["embedding_model"] == "sentence-transformers/all-MiniLM-L6-v2"
        assert rag["chunk_size"] == 300
        assert rag["similarity_k"] == 3


# ---------------------------------------------------------------------------
# API endpoint tests (via TestClient)
# ---------------------------------------------------------------------------

class TestAnalyticsEndpoints:

    def test_revenue_endpoint_returns_200(self, client):
        with patch("services.analytics_service._load_walmart", return_value=_mock_walmart_df()):
            response = client.get("/analytics/revenue")
        assert response.status_code == 200

    def test_revenue_endpoint_has_kpis(self, client):
        with patch("services.analytics_service._load_walmart", return_value=_mock_walmart_df()):
            data = client.get("/analytics/revenue").json()
        assert "kpis" in data
        assert "weekly_trend" in data
        assert "top_stores" in data

    def test_inventory_endpoint_returns_200(self, client):
        with patch("services.analytics_service._load_walmart", return_value=_mock_walmart_df()), \
             patch("services.analytics_service.detect_anomalies", return_value=[]):
            response = client.get("/analytics/inventory")
        assert response.status_code == 200

    def test_inventory_endpoint_has_store_status(self, client):
        with patch("services.analytics_service._load_walmart", return_value=_mock_walmart_df()), \
             patch("services.analytics_service.detect_anomalies", return_value=[]):
            data = client.get("/analytics/inventory").json()
        assert "store_inventory_status" in data
        assert "kpis" in data

    def test_forecast_endpoint_returns_200(self, client):
        mock_preds = [
            {"ds": f"2026-06-0{i+1}", "yhat": 100_000.0 + i * 500,
             "yhat_lower": 90_000.0, "yhat_upper": 110_000.0}
            for i in range(7)
        ]
        with patch("services.analytics_service.predict_future_sales", return_value=mock_preds), \
             patch("services.analytics_service._load_walmart", return_value=_mock_walmart_df()):
            response = client.get("/analytics/forecast")
        assert response.status_code == 200

    def test_forecast_endpoint_has_series(self, client):
        mock_preds = [
            {"ds": f"2026-06-0{i+1}", "yhat": 100_000.0,
             "yhat_lower": 90_000.0, "yhat_upper": 110_000.0}
            for i in range(7)
        ]
        with patch("services.analytics_service.predict_future_sales", return_value=mock_preds), \
             patch("services.analytics_service._load_walmart", return_value=_mock_walmart_df()):
            data = client.get("/analytics/forecast").json()
        assert "forecast_series" in data
        assert "historical_vs_forecast" in data

    def test_agent_insights_endpoint_returns_200(self, client):
        with patch("services.analytics_service.SessionLocal") as mock_session, \
             patch("services.analytics_service.list_documents", return_value=["faq.pdf"]), \
             patch("services.analytics_service.os.path.exists", return_value=True):

            mock_db = MagicMock()
            mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
            mock_db.query.return_value.count.return_value = 0
            mock_session.return_value = mock_db

            response = client.get("/analytics/agent-insights")
        assert response.status_code == 200

    def test_agent_insights_endpoint_has_registry(self, client):
        with patch("services.analytics_service.SessionLocal") as mock_session, \
             patch("services.analytics_service.list_documents", return_value=[]), \
             patch("services.analytics_service.os.path.exists", return_value=False):

            mock_db = MagicMock()
            mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
            mock_db.query.return_value.count.return_value = 0
            mock_session.return_value = mock_db

            data = client.get("/analytics/agent-insights").json()
        assert "agent_registry" in data
        assert "kpis" in data
        assert "rag_pipeline_status" in data

    def test_revenue_endpoint_returns_500_on_error(self, client):
        with patch("services.analytics_service._load_walmart",
                   side_effect=FileNotFoundError("CSV not found")):
            response = client.get("/analytics/revenue")
        assert response.status_code == 500
        assert response.json()["status"] == "error"

    def test_forecast_endpoint_returns_500_on_error(self, client):
        with patch("services.analytics_service.predict_future_sales",
                   side_effect=RuntimeError("model failed")):
            response = client.get("/analytics/forecast")
        assert response.status_code == 500
