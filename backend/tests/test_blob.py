"""
test_blob.py
============
Unit tests for services/blob_service.py

Covers:
  - list_documents(): success, empty container, system-file filtering, SDK error
  - upload_document(): success, file-not-found, overwrite behaviour
  - download_document(): success, blob-not-found, directory creation
  - delete_document(): success, blob-not-found
  - Connection string validation
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from azure.core.exceptions import ResourceNotFoundError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_blob(name: str) -> MagicMock:
    b = MagicMock()
    b.name = name
    return b


def _patched_client(blobs=None, blob_client=None):
    """
    Return a context-manager patch for get_container_client that yields
    a mock ContainerClient pre-configured with the given blobs / blob_client.
    """
    mock_container = MagicMock()
    if blobs is not None:
        mock_container.list_blobs.return_value = blobs
    if blob_client is not None:
        mock_container.get_blob_client.return_value = blob_client
    return patch("services.blob_service.get_container_client", return_value=mock_container)


# ---------------------------------------------------------------------------
# list_documents
# ---------------------------------------------------------------------------

class TestListDocuments:

    def test_returns_all_visible_blob_names(self):
        """list_documents() returns names of all non-hidden blobs."""
        blobs = [_make_blob("customer_support_faq.pdf"),
                 _make_blob("store_policy.pdf"),
                 _make_blob("inventory_rules.pdf")]

        with _patched_client(blobs=blobs):
            from services.blob_service import list_documents
            result = list_documents()

        assert set(result) == {
            "customer_support_faq.pdf",
            "store_policy.pdf",
            "inventory_rules.pdf",
        }

    def test_filters_out_dot_prefixed_blobs(self):
        """list_documents() must exclude blobs whose names start with '.'."""
        blobs = [_make_blob(".hidden"), _make_blob("visible.pdf")]

        with _patched_client(blobs=blobs):
            from services.blob_service import list_documents
            result = list_documents()

        assert ".hidden" not in result
        assert "visible.pdf" in result

    def test_returns_empty_list_for_empty_container(self):
        """list_documents() returns [] when the container has no blobs."""
        with _patched_client(blobs=[]):
            from services.blob_service import list_documents
            result = list_documents()

        assert result == []

    def test_raises_azure_storage_error_on_sdk_failure(self):
        """list_documents() wraps unexpected SDK errors in AzureStorageError."""
        from services.blob_service import AzureStorageError

        mock_container = MagicMock()
        mock_container.list_blobs.side_effect = RuntimeError("network timeout")

        with patch("services.blob_service.get_container_client",
                   return_value=mock_container):
            from services.blob_service import list_documents
            with pytest.raises(AzureStorageError):
                list_documents()


# ---------------------------------------------------------------------------
# upload_document
# ---------------------------------------------------------------------------

class TestUploadDocument:

    def test_upload_returns_blob_name_and_status(self, tmp_path):
        """upload_document() returns {blob_name, status='uploaded'} on success."""
        test_file = tmp_path / "policy.pdf"
        test_file.write_bytes(b"%PDF-1.4 fake content")

        mock_container = MagicMock()
        with patch("services.blob_service.get_container_client",
                   return_value=mock_container):
            from services.blob_service import upload_document
            result = upload_document(str(test_file), blob_name="policy.pdf")

        assert result["blob_name"] == "policy.pdf"
        assert result["status"] == "uploaded"
        mock_container.upload_blob.assert_called_once()

    def test_upload_uses_filename_as_default_blob_name(self, tmp_path):
        """upload_document() uses the file's basename when blob_name is omitted."""
        test_file = tmp_path / "discount_policy.pdf"
        test_file.write_bytes(b"content")

        mock_container = MagicMock()
        with patch("services.blob_service.get_container_client",
                   return_value=mock_container):
            from services.blob_service import upload_document
            result = upload_document(str(test_file))

        assert result["blob_name"] == "discount_policy.pdf"

    def test_upload_raises_file_not_found_for_missing_file(self):
        """upload_document() raises FileNotFoundError when the local file is absent."""
        from services.blob_service import upload_document

        with pytest.raises(FileNotFoundError):
            upload_document("/nonexistent/path/file.pdf")

    def test_upload_calls_overwrite_true(self, tmp_path):
        """upload_document() always passes overwrite=True to the SDK."""
        test_file = tmp_path / "file.pdf"
        test_file.write_bytes(b"data")

        mock_container = MagicMock()
        with patch("services.blob_service.get_container_client",
                   return_value=mock_container):
            from services.blob_service import upload_document
            upload_document(str(test_file), blob_name="file.pdf")

        _, kwargs = mock_container.upload_blob.call_args
        assert kwargs.get("overwrite") is True


# ---------------------------------------------------------------------------
# download_document
# ---------------------------------------------------------------------------

class TestDownloadDocument:

    def test_download_returns_local_path(self, tmp_path):
        """download_document() returns the local path it wrote to."""
        local_path = str(tmp_path / "downloaded.pdf")

        mock_blob_client = MagicMock()
        mock_blob_client.download_blob.return_value.readall.return_value = b"PDF content"

        with _patched_client(blob_client=mock_blob_client):
            from services.blob_service import download_document
            result = download_document("store_policy.pdf", local_path)

        assert result == local_path

    def test_download_creates_parent_directories(self, tmp_path):
        """download_document() creates missing parent directories."""
        nested_path = str(tmp_path / "subdir" / "deep" / "file.pdf")

        mock_blob_client = MagicMock()
        mock_blob_client.download_blob.return_value.readall.return_value = b"data"

        with _patched_client(blob_client=mock_blob_client):
            from services.blob_service import download_document
            download_document("file.pdf", nested_path)

        assert Path(nested_path).parent.exists()

    def test_download_raises_blob_not_found_error(self, tmp_path):
        """download_document() raises BlobNotFoundError when blob is absent."""
        from services.blob_service import BlobNotFoundError

        mock_blob_client = MagicMock()
        mock_blob_client.download_blob.side_effect = ResourceNotFoundError("not found")

        with _patched_client(blob_client=mock_blob_client):
            from services.blob_service import download_document
            with pytest.raises(BlobNotFoundError):
                download_document("missing.pdf", str(tmp_path / "out.pdf"))


# ---------------------------------------------------------------------------
# delete_document
# ---------------------------------------------------------------------------

class TestDeleteDocument:

    def test_delete_returns_success_dict(self):
        """delete_document() returns {status='deleted', blob_name} on success."""
        mock_blob_client = MagicMock()

        with _patched_client(blob_client=mock_blob_client):
            from services.blob_service import delete_document
            result = delete_document("old_policy.pdf")

        assert result["status"] == "deleted"
        assert result["blob_name"] == "old_policy.pdf"
        mock_blob_client.delete_blob.assert_called_once()

    def test_delete_raises_blob_not_found_error(self):
        """delete_document() raises BlobNotFoundError when blob doesn't exist."""
        from services.blob_service import BlobNotFoundError

        mock_blob_client = MagicMock()
        mock_blob_client.delete_blob.side_effect = ResourceNotFoundError("not found")

        with _patched_client(blob_client=mock_blob_client):
            from services.blob_service import delete_document
            with pytest.raises(BlobNotFoundError):
                delete_document("nonexistent.pdf")


# ---------------------------------------------------------------------------
# Connection string validation
# ---------------------------------------------------------------------------

class TestConnectionStringValidation:

    def test_raises_value_error_when_connection_string_missing(self):
        """validate_azure_config() raises AzureConfigError when env var is absent."""
        from services.blob_service import validate_azure_config, AzureConfigError

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("AZURE_STORAGE_CONNECTION_STRING", None)
            with pytest.raises(AzureConfigError):
                validate_azure_config()

    def test_returns_connection_string_when_set(self):
        """validate_azure_config() returns (conn_str, container) when set."""
        from services.blob_service import validate_azure_config

        with patch.dict(os.environ, {
            "AZURE_STORAGE_CONNECTION_STRING": "DefaultEndpoints...",
            "AZURE_BLOB_CONTAINER": "knowledge-base"
        }):
            conn_str, container = validate_azure_config()

        assert conn_str == "DefaultEndpoints..."
        assert container == "knowledge-base"
