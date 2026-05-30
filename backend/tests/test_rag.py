"""
Tests for RAG Service and Blob Service
=======================================
Verifies the RAG pipeline: blob listing, download, vector DB creation,
and similarity search.
"""

import os
import pytest
from unittest.mock import patch, MagicMock, mock_open


# =========================
# UNIT TESTS - blob_service
# =========================

class TestListDocuments:

    def test_returns_list_of_blob_names(self):
        """list_documents() must return a list of strings."""
        with patch("services.blob_service.get_container_client") as mock_client:
            mock_blob_1 = MagicMock()
            mock_blob_1.name = "customer_support_faq.pdf"
            mock_blob_2 = MagicMock()
            mock_blob_2.name = "store_policy.pdf"

            mock_client.return_value.list_blobs.return_value = [mock_blob_1, mock_blob_2]

            from services.blob_service import list_documents
            result = list_documents()

        assert isinstance(result, list)
        assert "customer_support_faq.pdf" in result
        assert "store_policy.pdf" in result

    def test_filters_system_files(self):
        """list_documents() must exclude blobs starting with '.'."""
        with patch("services.blob_service.get_container_client") as mock_client:
            mock_blob_1 = MagicMock()
            mock_blob_1.name = ".hidden_file"
            mock_blob_2 = MagicMock()
            mock_blob_2.name = "visible.pdf"

            mock_client.return_value.list_blobs.return_value = [mock_blob_1, mock_blob_2]

            from services.blob_service import list_documents
            result = list_documents()

        assert ".hidden_file" not in result
        assert "visible.pdf" in result

    def test_returns_empty_list_for_empty_container(self):
        """list_documents() must return [] when container is empty."""
        with patch("services.blob_service.get_container_client") as mock_client:
            mock_client.return_value.list_blobs.return_value = []

            from services.blob_service import list_documents
            result = list_documents()

        assert result == []


class TestDeleteDocument:

    def test_raises_blob_not_found_error(self):
        """delete_document() must raise BlobNotFoundError for missing blobs."""
        from azure.core.exceptions import ResourceNotFoundError
        from services.blob_service import BlobNotFoundError

        with patch("services.blob_service.get_container_client") as mock_client:
            mock_blob_client = MagicMock()
            mock_blob_client.delete_blob.side_effect = ResourceNotFoundError("not found")
            mock_client.return_value.get_blob_client.return_value = mock_blob_client

            from services.blob_service import delete_document

            with pytest.raises(BlobNotFoundError):
                delete_document("nonexistent.pdf")

    def test_returns_success_dict(self):
        """delete_document() must return status=deleted on success."""
        with patch("services.blob_service.get_container_client") as mock_client:
            mock_blob_client = MagicMock()
            mock_client.return_value.get_blob_client.return_value = mock_blob_client

            from services.blob_service import delete_document
            result = delete_document("store_policy.pdf")

        assert result["status"] == "deleted"
        assert result["blob_name"] == "store_policy.pdf"


# =========================
# UNIT TESTS - rag_service
# =========================

class TestSearchDocuments:

    def test_returns_list_of_strings(self):
        """search_documents() must return a list of strings."""
        with patch("services.rag_service.os.path.exists", return_value=True), \
             patch("services.rag_service.Chroma") as mock_chroma:

            mock_doc = MagicMock()
            mock_doc.page_content = "Return policy: 30 days."
            mock_chroma.return_value.similarity_search.return_value = [mock_doc]

            from services.rag_service import search_documents
            result = search_documents("What is the return policy?")

        assert isinstance(result, list)
        assert all(isinstance(r, str) for r in result)

    def test_raises_when_db_missing(self):
        """search_documents() must raise FileNotFoundError if vector DB doesn't exist."""
        with patch("services.rag_service.os.path.exists", return_value=False):
            from services.rag_service import search_documents

            with pytest.raises(FileNotFoundError):
                search_documents("test query")

    def test_returns_empty_list_on_search_error(self):
        """search_documents() must return [] on unexpected search errors."""
        with patch("services.rag_service.os.path.exists", return_value=True), \
             patch("services.rag_service.Chroma") as mock_chroma:

            mock_chroma.return_value.similarity_search.side_effect = RuntimeError("DB error")

            from services.rag_service import search_documents
            result = search_documents("test query")

        assert result == []

    def test_returns_up_to_3_results(self):
        """search_documents() must return at most k=3 results."""
        with patch("services.rag_service.os.path.exists", return_value=True), \
             patch("services.rag_service.Chroma") as mock_chroma:

            mock_docs = [MagicMock(page_content=f"chunk {i}") for i in range(3)]
            mock_chroma.return_value.similarity_search.return_value = mock_docs

            from services.rag_service import search_documents
            result = search_documents("discount policy")

        assert len(result) <= 3
