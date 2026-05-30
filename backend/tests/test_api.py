"""
Tests for FastAPI Endpoints
============================
Verifies all API endpoints return correct status codes and response shapes.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# =========================
# FIXTURES
# =========================

@pytest.fixture
def client():
    """Create a FastAPI test client with DB mocked out."""
    with patch("database.create_engine"), \
         patch("database.sessionmaker"), \
         patch("sqlalchemy.orm.declarative_base"):

        from main import app
        return TestClient(app)


# =========================
# HEALTH & ROOT
# =========================

class TestHealthEndpoints:

    def test_root_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()

    def test_health_returns_healthy(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


# =========================
# BLOB DOCUMENT ENDPOINTS
# =========================

class TestBlobDocumentEndpoints:

    def test_list_blob_documents_success(self, client):
        """GET /blob-documents returns status=success and documents list."""
        with patch("services.blob_service.get_container_client") as mock_client:
            mock_blob = MagicMock()
            mock_blob.name = "store_policy.pdf"
            mock_client.return_value.list_blobs.return_value = [mock_blob]

            response = client.get("/blob-documents")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert isinstance(data["documents"], list)

    def test_delete_document_not_found(self, client):
        """DELETE /delete-document/{name} returns 404 for missing blob."""
        from azure.core.exceptions import ResourceNotFoundError
        from services.blob_service import BlobNotFoundError

        with patch("services.blob_service.get_container_client") as mock_client:
            mock_blob_client = MagicMock()
            mock_blob_client.delete_blob.side_effect = ResourceNotFoundError("not found")
            mock_client.return_value.get_blob_client.return_value = mock_blob_client

            response = client.delete("/delete-document/nonexistent.pdf")

        assert response.status_code == 404
        assert response.json()["status"] == "error"


# =========================
# FORECAST ENDPOINT
# =========================

class TestForecastEndpoint:

    def test_forecast_returns_success(self, client):
        """GET /forecast returns status=success with forecast list."""
        mock_predictions = [
            {"ds": "2026-06-01", "yhat": 100000.0, "yhat_lower": 90000.0, "yhat_upper": 110000.0}
        ]

        with patch("services.forecast_service.predict_future_sales", return_value=mock_predictions):
            response = client.get("/forecast")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "forecast" in data


# =========================
# SEARCH DOCUMENTS ENDPOINT
# =========================

class TestSearchDocumentsEndpoint:

    def test_search_returns_results(self, client):
        """POST /search-documents returns status=success with results."""
        with patch("services.rag_service.os.path.exists", return_value=True), \
             patch("services.rag_service.Chroma") as mock_chroma:

            mock_doc = MagicMock()
            mock_doc.page_content = "30-day return policy applies."
            mock_chroma.return_value.similarity_search.return_value = [mock_doc]

            response = client.post(
                "/search-documents",
                json={"query": "return policy"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "results" in data

    def test_search_missing_query_returns_error(self, client):
        """POST /search-documents with empty body returns 422."""
        response = client.post("/search-documents", json={})
        assert response.status_code == 422


# =========================
# ANOMALY DETECTION ENDPOINT
# =========================

class TestAnomalyEndpoint:

    def test_anomaly_detection_returns_results(self, client):
        """POST /detect-anomaly returns status=success."""
        mock_results = [
            {"sales": 50000.0, "is_anomaly": False},
            {"sales": 5000.0, "is_anomaly": True}
        ]

        with patch("services.anomaly_service.detect_anomalies", return_value=mock_results):
            response = client.post(
                "/detect-anomaly",
                json={"sales": [50000.0, 5000.0]}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
