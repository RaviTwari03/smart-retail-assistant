"""
Vector Database Builder
=======================
Entry point script to build the ChromaDB vector database
from documents stored in Azure Blob Storage.

Usage:
    python create_vector_db.py

Environment Variables Required:
    AZURE_STORAGE_CONNECTION_STRING  - Azure Storage account connection string
    AZURE_BLOB_CONTAINER             - Container name (default: "knowledge-base")
"""

import logging
import sys

# =========================
# LOGGING SETUP
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


# =========================
# MAIN
# =========================

if __name__ == "__main__":

    logger.info("=== Vector Database Builder ===")
    logger.info("Source: Azure Blob Storage → ChromaDB")

    try:
        from services.rag_service import create_vector_db

        create_vector_db()

        logger.info("=== Vector database build complete ===")

    except Exception as e:
        logger.error(f"Vector database build failed: {str(e)}", exc_info=True)
        sys.exit(1)
