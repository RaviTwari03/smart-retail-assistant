"""
test_api.py
===========
Integration tests for FastAPI endpoints using TestClient.

Covers:
  - GET  /                          root
  - GET  /health                    health check
  - GET  /dashboard-metrics         metrics
  - GET  /forecast                  Prophet forecast
  - POST /detect-anomaly            anomaly detection
  - POST /search-documents          RAG search
  - POST /customer-support          customer support agent
  - GET  /blob-documents            list blobs
  - POST /upload-document           upload blob
  - DELETE /delete-document/{name}  delete blob

All external dependencies (DB, Azure, OpenAI, ML models) are mocked.
The `client` fixture is provided by conftest.py.
"""

import io
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Root & Health
# ---------------------------------------------------------------------------

class TestRootAndHealth:

    def test_root_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_root_contains_message(self, client):
        data = client.get("/").json()
        assert "message" in data
        assert "Running" in data["message"]

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_status_is_healthy(self, client):
        data = client.get("/health").json()
        assert data["status"] == "healthy"


# ---------------------------------------------------------------------------
# Dashboard Metrics
# ---------------------------------------------------------------------------

class TestDashboardMetrics:

    def test_dashboard_metrics_returns_200(self, client):
        response = client.get("/dashboard-metrics")
        assert response.status_code == 200

    def test_dashboard_metrics_has_required_fields(self, client):
        data = client.get("/dashboard-metrics").json()
        assert "total_revenue" in data
        assert "inventory_alerts" in data
        assert "sales_trend" in data


# ---------------------------------------------------------------------------
# Forecast endpoint
# ---------------------------------------------------------------------------

class TestForecastEndpoint:

    def test_forecast_returns_200(self, client):
        mock_preds = [
            {"ds": "2026-06-01", "yhat": 100_000.0,
             "yhat_lower": 90_000.0, "yhat_upper": 110_000.0}
        ]
        with patch("services.forecast_service._load_or_train_model") as mock_model:
            import pandas as pd
            from tests.conftest import make_forecast_df
            m = MagicMock()
            m.make_future_dataframe.return_value = MagicMock()
            m.predict.return_value = make_forecast_df(7)
            mock_model.return_value = m

            response = client.get("/forecast")

        assert response.status_code == 200

    def test_forecast_response_has_status_success(self, client):
        with patch("services.forecast_service._load_or_train_model") as mock_model:
            from tests.conftest import make_forecast_df
            m = MagicMock()
            m.make_future_dataframe.return_value = MagicMock()
            m.predict.return_value = make_forecast_df(7)
            mock_model.return_value = m

            data = client.get("/forecast").json()

        assert data["status"] == "success"

    def test_forecast_response_contains_forecast_list(self, client):
        with patch("services.forecast_service._load_or_train_model") as mock_model:
            from tests.conftest import make_forecast_df
            m = MagicMock()
            m.make_future_dataframe.return_value = MagicMock()
            m.predict.return_value = make_forecast_df(7)
            mock_model.return_value = m

            data = client.get("/forecast").json()

        assert "forecast" in data
        assert isinstance(data["forecast"], list)

    def test_forecast_returns_error_on_failure(self, client):
        with patch("services.forecast_service._load_or_train_model",
                   side_effect=FileNotFoundError("no model")):
            data = client.get("/forecast").json()

        assert data["status"] == "error"
        assert "message" in data


# ---------------------------------------------------------------------------
# Anomaly Detection endpoint
# ---------------------------------------------------------------------------

class TestAnomalyEndpoint:

    def test_anomaly_returns_200(self, client):
        mock_results = [{"sales": 50_000.0, "is_anomaly": False}]
        with patch("services.anomaly_service._load_model") as mock_load:
            mock_model = MagicMock()
            mock_model.predict.return_value = [1]
            mock_load.return_value = mock_model

            response = client.post("/detect-anomaly", json={"sales": [50_000.0]})

        assert response.status_code == 200

    def test_anomaly_response_has_status_success(self, client):
        with patch("services.anomaly_service._load_model") as mock_load:
            mock_model = MagicMock()
            mock_model.predict.return_value = [1, -1]
            mock_load.return_value = mock_model

            data = client.post(
                "/detect-anomaly",
                json={"sales": [50_000.0, 500.0]}
            ).json()

        assert data["status"] == "success"

    def test_anomaly_missing_body_returns_422(self, client):
        response = client.post("/detect-anomaly", json={})
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Search Documents endpoint
# ---------------------------------------------------------------------------

class TestSearchDocumentsEndpoint:

    def test_search_returns_200(self, client):
        with patch("services.rag_service.vector_db_exists", return_value=True), \
             patch("services.rag_service.Chroma") as mock_chroma:

            mock_chroma.return_value.similarity_search.return_value = [
                MagicMock(page_content="Return policy: 30 days.")
            ]

            response = client.post("/search-documents", json={"query": "return policy"})

        assert response.status_code == 200

    def test_search_response_has_status_success(self, client):
        with patch("services.rag_service.vector_db_exists", return_value=True), \
             patch("services.rag_service.Chroma") as mock_chroma:

            mock_chroma.return_value.similarity_search.return_value = [
                MagicMock(page_content="Discount: 10% on Tuesdays.")
            ]

            data = client.post(
                "/search-documents",
                json={"query": "discount"}
            ).json()

        assert data["status"] == "success"
        assert "results" in data
        assert isinstance(data["results"], list)

    def test_search_missing_query_returns_422(self, client):
        response = client.post("/search-documents", json={})
        assert response.status_code == 422

    def test_search_returns_error_when_db_missing(self, client):
        with patch("services.rag_service.vector_db_exists", return_value=False):
            response = client.post(
                "/search-documents",
                json={"query": "anything"}
            )
        # Returns 503 Service Unavailable when vector DB is not ready
        assert response.status_code == 503
        assert response.json()["status"] == "error"


# ---------------------------------------------------------------------------
# Customer Support endpoint
# ---------------------------------------------------------------------------

class TestCustomerSupportEndpoint:

    def test_customer_support_returns_200(self, client):
        with patch("services.rag_service.os.path.exists", return_value=True), \
             patch("services.rag_service.Chroma") as mock_chroma, \
             patch("agents.customer_support.support_agent._get_openai_client",
                   return_value=None):

            mock_chroma.return_value.similarity_search.return_value = [
                MagicMock(page_content="Store policy text.")
            ]

            response = client.post(
                "/customer-support",
                json={"query": "What are your store hours?"}
            )

        assert response.status_code == 200

    def test_customer_support_response_has_status_success(self, client):
        with patch("services.rag_service.os.path.exists", return_value=True), \
             patch("services.rag_service.Chroma") as mock_chroma, \
             patch("agents.customer_support.support_agent._get_openai_client",
                   return_value=None):

            mock_chroma.return_value.similarity_search.return_value = [
                MagicMock(page_content="Store hours: 9am–9pm.")
            ]

            data = client.post(
                "/customer-support",
                json={"query": "store hours"}
            ).json()

        assert data["status"] == "success"
        assert "response" in data
        assert isinstance(data["response"], str)

    def test_customer_support_missing_query_returns_422(self, client):
        response = client.post("/customer-support", json={})
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Blob Storage endpoints
# ---------------------------------------------------------------------------

class TestBlobDocumentsEndpoint:

    def test_list_blob_documents_returns_200(self, client):
        with patch("services.blob_service.get_container_client") as mock_cc:
            blob = MagicMock()
            blob.name = "store_policy.pdf"
            mock_cc.return_value.list_blobs.return_value = [blob]

            response = client.get("/blob-documents")

        assert response.status_code == 200

    def test_list_blob_documents_status_success(self, client):
        with patch("services.blob_service.get_container_client") as mock_cc:
            blob = MagicMock()
            blob.name = "inventory_rules.pdf"
            mock_cc.return_value.list_blobs.return_value = [blob]

            data = client.get("/blob-documents").json()

        assert data["status"] == "success"
        assert "documents" in data
        assert "inventory_rules.pdf" in data["documents"]

    def test_list_blob_documents_returns_500_on_error(self, client):
        with patch("services.blob_service.get_container_client") as mock_cc:
            mock_cc.return_value.list_blobs.side_effect = RuntimeError("Azure down")

            response = client.get("/blob-documents")

        assert response.status_code == 500
        assert response.json()["status"] == "error"


class TestUploadDocumentEndpoint:

    def test_upload_document_returns_200(self, client):
        with patch("services.blob_service.get_container_client") as mock_cc:
            mock_cc.return_value.upload_blob.return_value = None

            file_content = b"%PDF-1.4 fake pdf content"
            response = client.post(
                "/upload-document",
                files={"file": ("test_policy.pdf", io.BytesIO(file_content), "application/pdf")}
            )

        assert response.status_code == 200

    def test_upload_document_response_has_blob_name(self, client):
        with patch("services.blob_service.get_container_client") as mock_cc:
            mock_cc.return_value.upload_blob.return_value = None

            data = client.post(
                "/upload-document",
                files={"file": ("my_doc.pdf", io.BytesIO(b"content"), "application/pdf")}
            ).json()

        assert data["status"] == "success"
        assert data["blob_name"] == "my_doc.pdf"


class TestDeleteDocumentEndpoint:

    def test_delete_document_returns_200(self, client):
        with patch("services.blob_service.get_container_client") as mock_cc:
            mock_cc.return_value.get_blob_client.return_value.delete_blob.return_value = None

            response = client.delete("/delete-document/store_policy.pdf")

        assert response.status_code == 200

    def test_delete_document_returns_404_for_missing_blob(self, client):
        from azure.core.exceptions import ResourceNotFoundError

        with patch("services.blob_service.get_container_client") as mock_cc:
            mock_cc.return_value.get_blob_client.return_value \
                .delete_blob.side_effect = ResourceNotFoundError("not found")

            response = client.delete("/delete-document/nonexistent.pdf")

        assert response.status_code == 404
        assert response.json()["status"] == "error"

    def test_delete_document_success_message(self, client):
        with patch("services.blob_service.get_container_client") as mock_cc:
            mock_cc.return_value.get_blob_client.return_value.delete_blob.return_value = None

            data = client.delete("/delete-document/old_policy.pdf").json()

        assert data["status"] == "success"
        assert "old_policy.pdf" in data["message"]
