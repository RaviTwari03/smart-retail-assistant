"""
Azure Blob Storage Service
==========================
Single source of truth for all knowledge-base document operations.

Environment Variables:
    AZURE_STORAGE_CONNECTION_STRING  - Required. Azure Storage connection string.
    AZURE_BLOB_CONTAINER             - Optional. Container name (default: knowledge-base).

Design principles:
    - Lazy client initialisation — never crashes on import
    - Every public function logs start, success, and failure
    - All Azure SDK exceptions are caught and re-raised as typed exceptions
    - Application never crashes due to Azure failures
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv

from azure.core.exceptions import (
    AzureError,
    ResourceNotFoundError,
    ServiceRequestError,
)
from azure.storage.blob import BlobServiceClient, ContainerClient

load_dotenv()

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Custom exceptions
# ─────────────────────────────────────────────────────────────

class AzureStorageError(Exception):
    """Raised when an Azure Blob Storage operation fails unexpectedly."""


class BlobNotFoundError(Exception):
    """Raised when a requested blob does not exist in the container."""


class AzureConfigError(Exception):
    """Raised when required Azure environment variables are missing."""


# ─────────────────────────────────────────────────────────────
# Environment validation
# ─────────────────────────────────────────────────────────────

def validate_azure_config() -> Tuple[str, str]:
    """
    Validate that required Azure environment variables are present.

    Returns:
        Tuple[str, str]: (connection_string, container_name)

    Raises:
        AzureConfigError: If AZURE_STORAGE_CONNECTION_STRING is not set.
    """
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "").strip()
    container = os.getenv("AZURE_BLOB_CONTAINER", "knowledge-base").strip()

    if not conn_str:
        raise AzureConfigError(
            "AZURE_STORAGE_CONNECTION_STRING is not set. "
            "Configure it in Azure App Service → Environment Variables."
        )

    if not container:
        container = "knowledge-base"
        logger.warning(
            "AZURE_BLOB_CONTAINER not set — using default: 'knowledge-base'"
        )

    return conn_str, container


# ─────────────────────────────────────────────────────────────
# Lazy client cache
# ─────────────────────────────────────────────────────────────

_blob_service_client: Optional[BlobServiceClient] = None
_container_client: Optional[ContainerClient] = None


def _reset_clients() -> None:
    """Reset cached clients (useful after config changes or in tests)."""
    global _blob_service_client, _container_client
    _blob_service_client = None
    _container_client = None


def get_container_client() -> ContainerClient:
    """
    Return a validated ContainerClient, initialising it on first call.

    Returns:
        ContainerClient: Ready-to-use Azure container client.

    Raises:
        AzureConfigError: If environment variables are missing.
        AzureStorageError: If the container cannot be reached.
    """
    global _blob_service_client, _container_client

    if _container_client is not None:
        return _container_client

    conn_str, container_name = validate_azure_config()

    logger.info("Initialising Azure Blob Storage connection")

    try:
        _blob_service_client = BlobServiceClient.from_connection_string(conn_str)
    except Exception as exc:
        raise AzureStorageError(
            f"Failed to create BlobServiceClient: {exc}"
        ) from exc

    logger.info(f"Connecting to container: '{container_name}'")

    _container_client = _blob_service_client.get_container_client(container_name)

    # Validate the container actually exists
    try:
        _container_client.get_container_properties()
        logger.info(f"Azure Blob Storage ready — container: '{container_name}'")
    except ResourceNotFoundError:
        _container_client = None
        raise AzureStorageError(
            f"Container '{container_name}' does not exist. "
            "Create it in the Azure Portal or check AZURE_BLOB_CONTAINER."
        )
    except Exception as exc:
        _container_client = None
        raise AzureStorageError(
            f"Cannot access container '{container_name}': {exc}"
        ) from exc

    return _container_client


# ─────────────────────────────────────────────────────────────
# Public helper functions
# ─────────────────────────────────────────────────────────────

def list_documents() -> List[str]:
    """
    List all user-visible blobs in the knowledge-base container.

    Filters out system/hidden blobs (names starting with '.').

    Returns:
        List[str]: Blob names, e.g. ["faq.pdf", "policy.txt"]

    Raises:
        AzureConfigError: If environment variables are missing.
        AzureStorageError: If the Azure SDK raises an unexpected error.
    """
    logger.info("Listing blobs in Azure Blob Storage container")

    client = get_container_client()

    try:
        blob_names = [
            b.name
            for b in client.list_blobs()
            if not b.name.startswith(".")
        ]
        logger.info(f"Found {len(blob_names)} blob(s) in container")
        return blob_names

    except (AzureConfigError, AzureStorageError):
        raise
    except Exception as exc:
        logger.error(f"list_documents failed: {exc}", exc_info=True)
        raise AzureStorageError(
            f"Failed to list documents from Azure Blob Storage: {exc}"
        ) from exc


def upload_document(
    file_path: str,
    blob_name: Optional[str] = None,
) -> Dict[str, str]:
    """
    Upload a local file to Azure Blob Storage (overwrites if exists).

    Args:
        file_path: Absolute or relative path to the local file.
        blob_name:  Blob name to use. Defaults to the file's basename.

    Returns:
        {"blob_name": str, "status": "uploaded"}

    Raises:
        FileNotFoundError: If the local file does not exist.
        AzureConfigError:  If environment variables are missing.
        AzureStorageError: If the upload fails.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Local file not found: {file_path}")

    if not blob_name:
        blob_name = path.name

    logger.info(f"Uploading '{blob_name}' to Azure Blob Storage")

    client = get_container_client()

    try:
        with open(file_path, "rb") as data:
            client.upload_blob(name=blob_name, data=data, overwrite=True)

        logger.info(f"Upload successful: '{blob_name}'")
        return {"blob_name": blob_name, "status": "uploaded"}

    except FileNotFoundError:
        raise
    except Exception as exc:
        logger.error(f"Upload failed for '{blob_name}': {exc}", exc_info=True)
        raise AzureStorageError(
            f"Failed to upload '{blob_name}': {exc}"
        ) from exc


def download_document(blob_name: str, local_path: str) -> str:
    """
    Download a blob to a local path, creating parent directories as needed.

    Args:
        blob_name:  Name of the blob to download.
        local_path: Destination file path on disk.

    Returns:
        str: The local_path where the file was saved.

    Raises:
        BlobNotFoundError: If the blob does not exist.
        AzureConfigError:  If environment variables are missing.
        AzureStorageError: If the download fails.
    """
    logger.info(f"Downloading blob '{blob_name}' → '{local_path}'")

    Path(local_path).parent.mkdir(parents=True, exist_ok=True)

    client = get_container_client()
    container_name = os.getenv("AZURE_BLOB_CONTAINER", "knowledge-base")

    try:
        blob_client = client.get_blob_client(blob_name)
        data = blob_client.download_blob().readall()

        with open(local_path, "wb") as f:
            f.write(data)

        logger.info(f"Download successful: '{blob_name}' ({len(data):,} bytes)")
        return local_path

    except ResourceNotFoundError:
        raise BlobNotFoundError(
            f"Blob '{blob_name}' not found in container '{container_name}'"
        )
    except BlobNotFoundError:
        raise
    except Exception as exc:
        logger.error(f"Download failed for '{blob_name}': {exc}", exc_info=True)
        raise AzureStorageError(
            f"Failed to download '{blob_name}': {exc}"
        ) from exc


def delete_document(blob_name: str) -> Dict[str, str]:
    """
    Delete a blob from Azure Blob Storage.

    Args:
        blob_name: Name of the blob to delete.

    Returns:
        {"blob_name": str, "status": "deleted"}

    Raises:
        BlobNotFoundError: If the blob does not exist.
        AzureConfigError:  If environment variables are missing.
        AzureStorageError: If the deletion fails.
    """
    logger.info(f"Deleting blob '{blob_name}' from Azure Blob Storage")

    client = get_container_client()
    container_name = os.getenv("AZURE_BLOB_CONTAINER", "knowledge-base")

    try:
        client.get_blob_client(blob_name).delete_blob()
        logger.info(f"Deleted blob: '{blob_name}'")
        return {"blob_name": blob_name, "status": "deleted"}

    except ResourceNotFoundError:
        raise BlobNotFoundError(
            f"Blob '{blob_name}' not found in container '{container_name}'"
        )
    except BlobNotFoundError:
        raise
    except Exception as exc:
        logger.error(f"Delete failed for '{blob_name}': {exc}", exc_info=True)
        raise AzureStorageError(
            f"Failed to delete '{blob_name}': {exc}"
        ) from exc
