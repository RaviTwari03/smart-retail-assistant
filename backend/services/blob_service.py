"""
Azure Blob Storage Service
==========================
Provides a centralized interface for all Azure Blob Storage operations
used by the Smart Retail Assistant knowledge base.

Environment Variables:
    AZURE_STORAGE_CONNECTION_STRING  - Azure Storage account connection string (required)
    AZURE_BLOB_CONTAINER             - Container name (default: "knowledge-base")
"""

import logging
import os
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

from azure.core.exceptions import ResourceNotFoundError, ServiceRequestError
from azure.storage.blob import BlobServiceClient, ContainerClient

# Load .env for local development
load_dotenv()

# =========================
# LOGGING
# =========================

logger = logging.getLogger(__name__)


# =========================
# CUSTOM EXCEPTIONS
# =========================

class AzureStorageError(Exception):
    """Raised when an Azure Blob Storage operation fails."""
    pass


class BlobNotFoundError(Exception):
    """Raised when a requested blob does not exist in the container."""
    pass


# =========================
# CONFIGURATION
# =========================

def _get_connection_string() -> str:
    """
    Retrieve and validate the Azure Storage connection string.

    Returns:
        str: The connection string from environment variables.

    Raises:
        ValueError: If the environment variable is not set.
    """
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

    if not conn_str:
        raise ValueError(
            "AZURE_STORAGE_CONNECTION_STRING environment variable is not set. "
            "Please configure it in your Azure App Service environment variables."
        )

    return conn_str


def _get_container_name() -> str:
    """
    Retrieve the Azure Blob Storage container name.

    Returns:
        str: Container name from environment variable, defaulting to 'knowledge-base'.
    """
    return os.getenv("AZURE_BLOB_CONTAINER", "knowledge-base")


# =========================
# CLIENT INITIALIZATION
# =========================

def _init_clients() -> tuple[BlobServiceClient, ContainerClient]:
    """
    Initialize and validate Azure Blob Storage clients.

    Returns:
        tuple: (BlobServiceClient, ContainerClient)

    Raises:
        ValueError: If connection string or container is missing/invalid.
        AzureStorageError: If the container cannot be accessed.
    """
    connection_string = _get_connection_string()
    container_name = _get_container_name()

    logger.info("Initializing Azure Blob Storage connection")

    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    except Exception as e:
        raise AzureStorageError(
            f"Failed to initialize BlobServiceClient: {str(e)}"
        ) from e

    logger.info(f"Initializing Azure Blob Storage container: {container_name}")

    container_client = blob_service_client.get_container_client(container_name)

    # Validate container exists
    try:
        container_client.get_container_properties()
    except ResourceNotFoundError:
        raise ValueError(
            f"Azure Blob Storage container '{container_name}' does not exist or is not accessible. "
            "Please verify the container name and connection string."
        )
    except Exception as e:
        raise AzureStorageError(
            f"Failed to access container '{container_name}': {str(e)}"
        ) from e

    return blob_service_client, container_client


# Initialize clients at module level (lazy — only when first used)
_blob_service_client: BlobServiceClient | None = None
_container_client: ContainerClient | None = None


def get_container_client() -> ContainerClient:
    """
    Get the initialized ContainerClient, creating it if necessary.

    Returns:
        ContainerClient: Initialized and validated container client.
    """
    global _blob_service_client, _container_client

    if _container_client is None:
        _blob_service_client, _container_client = _init_clients()

    return _container_client


# =========================
# HELPER FUNCTIONS
# =========================

def list_documents() -> List[str]:
    """
    List all documents stored in the Azure Blob Storage container.

    Filters out system files (blobs starting with '.').

    Returns:
        List[str]: List of blob names in the container.

    Raises:
        AzureStorageError: If the Azure SDK raises an exception during retrieval.
    """
    client = get_container_client()

    try:
        blobs = client.list_blobs()

        blob_names = [
            blob.name
            for blob in blobs
            if not blob.name.startswith(".")
        ]

        logger.info(f"Retrieved {len(blob_names)} blobs from container")

        return blob_names

    except AzureStorageError:
        raise

    except Exception as e:
        logger.error(f"Failed to list blobs: {str(e)}", exc_info=True)
        raise AzureStorageError(f"Failed to list documents from Azure Blob Storage: {str(e)}") from e


def upload_document(file_path: str, blob_name: str | None = None) -> Dict[str, str]:
    """
    Upload a local file to Azure Blob Storage.

    Overwrites the blob if it already exists.

    Args:
        file_path (str): Absolute or relative path to the local file.
        blob_name (str, optional): Name to use for the blob. Defaults to the file's basename.

    Returns:
        Dict[str, str]: {"blob_name": str, "status": "uploaded"}

    Raises:
        FileNotFoundError: If the local file does not exist.
        AzureStorageError: If the Azure SDK raises an exception during upload.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if blob_name is None:
        blob_name = path.name

    client = get_container_client()

    logger.info(f"Uploading blob: {blob_name}")

    try:
        with open(file_path, "rb") as data:
            client.upload_blob(
                name=blob_name,
                data=data,
                overwrite=True
            )

        logger.info(f"Successfully uploaded blob: {blob_name}")

        return {
            "blob_name": blob_name,
            "status": "uploaded"
        }

    except FileNotFoundError:
        raise

    except Exception as e:
        logger.error(f"Failed to upload blob '{blob_name}': {str(e)}", exc_info=True)
        raise AzureStorageError(f"Failed to upload document '{blob_name}': {str(e)}") from e


def download_document(blob_name: str, local_path: str) -> str:
    """
    Download a blob from Azure Blob Storage to a local path.

    Creates parent directories if they do not exist.

    Args:
        blob_name (str): Name of the blob to download.
        local_path (str): Local file path to save the downloaded blob.

    Returns:
        str: The local file path where the blob was saved.

    Raises:
        BlobNotFoundError: If the blob does not exist in the container.
        AzureStorageError: If the Azure SDK raises an exception during download.
    """
    container_name = _get_container_name()

    logger.info(f"Downloading blob: {blob_name} to {local_path}")

    # Ensure parent directory exists
    Path(local_path).parent.mkdir(parents=True, exist_ok=True)

    client = get_container_client()

    try:
        blob_client = client.get_blob_client(blob_name)
        download_stream = blob_client.download_blob()

        with open(local_path, "wb") as f:
            f.write(download_stream.readall())

        logger.info(f"Successfully downloaded blob: {blob_name}")

        return local_path

    except ResourceNotFoundError:
        raise BlobNotFoundError(
            f"Blob '{blob_name}' not found in container '{container_name}'"
        )

    except BlobNotFoundError:
        raise

    except Exception as e:
        logger.error(f"Failed to download blob '{blob_name}': {str(e)}", exc_info=True)
        raise AzureStorageError(f"Failed to download document '{blob_name}': {str(e)}") from e


def delete_document(blob_name: str) -> Dict[str, str]:
    """
    Delete a blob from Azure Blob Storage.

    Args:
        blob_name (str): Name of the blob to delete.

    Returns:
        Dict[str, str]: {"status": "deleted", "blob_name": str}

    Raises:
        BlobNotFoundError: If the blob does not exist in the container.
        AzureStorageError: If the Azure SDK raises an exception during deletion.
    """
    container_name = _get_container_name()

    logger.info(f"Deleting blob: {blob_name}")

    client = get_container_client()

    try:
        blob_client = client.get_blob_client(blob_name)
        blob_client.delete_blob()

        logger.info(f"Successfully deleted blob: {blob_name}")

        return {
            "status": "deleted",
            "blob_name": blob_name
        }

    except ResourceNotFoundError:
        raise BlobNotFoundError(
            f"Blob '{blob_name}' not found in container '{container_name}'"
        )

    except BlobNotFoundError:
        raise

    except Exception as e:
        logger.error(f"Failed to delete blob '{blob_name}': {str(e)}", exc_info=True)
        raise AzureStorageError(f"Failed to delete document '{blob_name}': {str(e)}") from e
