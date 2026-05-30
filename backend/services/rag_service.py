"""
RAG Service
===========
Retrieval-Augmented Generation pipeline for the Smart Retail Assistant.

Architecture:
    Azure Blob Storage (single source of truth)
        ↓  list_documents()
        ↓  download_document() → secure temp directory
        ↓  PyPDFLoader / TextLoader
        ↓  RecursiveCharacterTextSplitter (chunk=300, overlap=50)
        ↓  HuggingFaceEmbeddings (all-MiniLM-L6-v2)
        ↓  ChromaDB (persisted at ./vector_db)
        ↓  similarity_search(k=3)
        ↓  FastAPI response

Design principles:
    - One corrupt blob never stops the whole pipeline
    - Temp files are always cleaned up (finally block)
    - search_documents() never crashes the API
    - Structured logging at every stage
"""

import logging
import os
import shutil
import tempfile
from typing import List

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

DB_PATH = "./vector_db"

CHUNK_SIZE    = 300
CHUNK_OVERLAP = 50
SEARCH_K      = 3
EMBED_MODEL   = "sentence-transformers/all-MiniLM-L6-v2"

# ─────────────────────────────────────────────────────────────
# Embedding model (module-level singleton)
# ─────────────────────────────────────────────────────────────

logger.info(f"Loading embedding model: {EMBED_MODEL}")

embedding_model = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

logger.info("Embedding model loaded successfully")


# ─────────────────────────────────────────────────────────────
# Vector DB status helpers
# ─────────────────────────────────────────────────────────────

def vector_db_exists() -> bool:
    """Return True if the ChromaDB directory exists and is non-empty."""
    return os.path.isdir(DB_PATH) and bool(os.listdir(DB_PATH))


# ─────────────────────────────────────────────────────────────
# Create / rebuild vector database
# ─────────────────────────────────────────────────────────────

def create_vector_db() -> dict:
    """
    Build (or rebuild) the ChromaDB vector database from Azure Blob Storage.

    Workflow:
        1. List all blobs in the Azure container
        2. Download each blob to a secure temp directory
        3. Load PDFs with PyPDFLoader, TXT files with TextLoader
        4. Skip (log + continue) any blob that fails to download or parse
        5. Split all loaded documents into chunks
        6. Generate embeddings and persist to ChromaDB
        7. Delete the temp directory (always, even on failure)

    Returns:
        dict: {
            "status": "success" | "partial" | "error",
            "blobs_found": int,
            "blobs_loaded": int,
            "chunks_created": int,
            "message": str
        }
    """
    from services.blob_service import (
        AzureStorageError,
        AzureConfigError,
        list_documents,
        download_document,
    )

    logger.info("=" * 60)
    logger.info("Starting vector database creation from Azure Blob Storage")
    logger.info("=" * 60)

    # ── Step 1: list blobs ────────────────────────────────────
    try:
        blob_names = list_documents()
    except (AzureStorageError, AzureConfigError) as exc:
        logger.error(f"Cannot list blobs — aborting vector DB creation: {exc}")
        return {
            "status": "error",
            "blobs_found": 0,
            "blobs_loaded": 0,
            "chunks_created": 0,
            "message": str(exc),
        }

    if not blob_names:
        logger.warning("No blobs found in Azure Blob Storage — vector DB not created")
        return {
            "status": "error",
            "blobs_found": 0,
            "blobs_loaded": 0,
            "chunks_created": 0,
            "message": "No documents found in Azure Blob Storage container",
        }

    logger.info(f"Found {len(blob_names)} blob(s): {blob_names}")

    # ── Step 2: download & parse ──────────────────────────────
    documents   = []
    failed      = []
    temp_dir    = tempfile.mkdtemp(prefix="rag_kb_")

    logger.info(f"Temp directory: {temp_dir}")

    try:
        for blob_name in blob_names:
            local_path = os.path.join(temp_dir, blob_name)

            # Download
            try:
                download_document(blob_name, local_path)
            except Exception as exc:
                logger.error(
                    f"[SKIP] Download failed for '{blob_name}': {exc}"
                )
                failed.append(blob_name)
                continue

            # Parse
            try:
                ext = blob_name.lower().rsplit(".", 1)[-1] if "." in blob_name else ""

                if ext == "pdf":
                    logger.info(f"Parsing PDF: '{blob_name}'")
                    docs = PyPDFLoader(local_path).load()
                    documents.extend(docs)
                    logger.info(
                        f"  → {len(docs)} page(s) loaded from '{blob_name}'"
                    )

                elif ext == "txt":
                    logger.info(f"Parsing TXT: '{blob_name}'")
                    docs = TextLoader(local_path, encoding="utf-8").load()
                    documents.extend(docs)
                    logger.info(
                        f"  → {len(docs)} document(s) loaded from '{blob_name}'"
                    )

                else:
                    logger.warning(
                        f"[SKIP] Unsupported file type '{ext}' for blob '{blob_name}'"
                    )

            except Exception as exc:
                logger.error(
                    f"[SKIP] Failed to parse '{blob_name}': {exc}",
                    exc_info=True,
                )
                failed.append(blob_name)
                continue

        blobs_loaded = len(blob_names) - len(failed)
        logger.info(
            f"Loaded {len(documents)} document page(s) from "
            f"{blobs_loaded}/{len(blob_names)} blob(s)"
        )

        if not documents:
            logger.warning(
                "No documents were successfully loaded — vector DB not created"
            )
            return {
                "status": "error",
                "blobs_found": len(blob_names),
                "blobs_loaded": 0,
                "chunks_created": 0,
                "message": "All blobs failed to load. Check logs for details.",
            }

        # ── Step 3: chunk ─────────────────────────────────────
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
        chunks = splitter.split_documents(documents)
        logger.info(f"Created {len(chunks)} chunk(s) from {len(documents)} page(s)")

        # ── Step 4: embed & persist ───────────────────────────
        logger.info(f"Generating embeddings and persisting to ChromaDB at '{DB_PATH}'")

        Chroma.from_documents(
            documents=chunks,
            embedding=embedding_model,
            persist_directory=DB_PATH,
        )

        logger.info(
            f"Vector database created successfully — "
            f"{len(chunks)} chunks at '{DB_PATH}'"
        )

        status = "success" if not failed else "partial"
        msg = (
            f"Vector DB built from {blobs_loaded}/{len(blob_names)} blobs, "
            f"{len(chunks)} chunks"
        )
        if failed:
            msg += f". Failed blobs: {failed}"

        return {
            "status": status,
            "blobs_found": len(blob_names),
            "blobs_loaded": blobs_loaded,
            "chunks_created": len(chunks),
            "message": msg,
        }

    finally:
        # ── Step 5: cleanup ───────────────────────────────────
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temp directory: '{temp_dir}'")
        except Exception as exc:
            logger.warning(
                f"Could not remove temp directory '{temp_dir}': {exc}"
            )


# ─────────────────────────────────────────────────────────────
# Search
# ─────────────────────────────────────────────────────────────

def search_documents(query: str) -> List[str]:
    """
    Perform a semantic similarity search against the ChromaDB vector database.

    Args:
        query: Natural language search query.

    Returns:
        List[str]: Up to SEARCH_K matching document chunks.
                   Returns [] on any error (never crashes the API).

    Raises:
        FileNotFoundError: If the vector database has not been built yet.
    """
    logger.info(f"RAG search — query: '{query}'")

    if not vector_db_exists():
        logger.warning(
            f"Vector database not found at '{DB_PATH}'. "
            "Upload documents and trigger a rebuild."
        )
        raise FileNotFoundError(
            f"Vector database not found at '{DB_PATH}'. "
            "Please upload documents to Azure Blob Storage and rebuild the index."
        )

    try:
        vector_db = Chroma(
            persist_directory=DB_PATH,
            embedding_function=embedding_model,
        )

        results = vector_db.similarity_search(query, k=SEARCH_K)
        chunks  = [doc.page_content for doc in results]

        logger.info(f"Search returned {len(chunks)} result(s) for query: '{query}'")
        return chunks

    except FileNotFoundError:
        raise

    except Exception as exc:
        logger.error(
            f"Search failed for query '{query}': {exc}",
            exc_info=True,
        )
        return []
