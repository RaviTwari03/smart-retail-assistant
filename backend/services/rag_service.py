"""
RAG Service
===========
Retrieval-Augmented Generation pipeline for the Smart Retail Assistant.

Architecture:
    Azure Blob Storage
        ↓ Download PDFs
        ↓ Extract text
        ↓ Generate embeddings (sentence-transformers/all-MiniLM-L6-v2)
        ↓ Store in ChromaDB
        ↓ Similarity search
        ↓ Return results to FastAPI
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

# =========================
# LOGGING
# =========================

logger = logging.getLogger(__name__)


# =========================
# CONFIG
# =========================

DB_PATH = "./vector_db"


# =========================
# EMBEDDING MODEL
# =========================

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# =========================
# CREATE VECTOR DATABASE
# =========================

def create_vector_db() -> None:
    """
    Build the ChromaDB vector database from documents stored in Azure Blob Storage.

    Workflow:
        1. List all blobs in the Azure Blob Storage container
        2. Download each blob to a secure temporary directory
        3. Extract text from PDF and TXT files
        4. Split documents into chunks (size=300, overlap=50)
        5. Generate embeddings using sentence-transformers
        6. Persist embeddings in ChromaDB
        7. Clean up all temporary files

    Raises:
        AzureStorageError: If blob listing or download fails critically.
    """
    from services.blob_service import AzureStorageError, list_documents, download_document

    logger.info("Starting vector database creation from Azure Blobs")

    # List all blobs
    try:
        blob_names = list_documents()
    except AzureStorageError as e:
        logger.error(f"Failed to list blobs from Azure Blob Storage: {str(e)}")
        raise

    if not blob_names:
        logger.warning("No blobs found in Azure Blob Storage container. Vector DB not created.")
        return

    logger.info(f"Retrieved {len(blob_names)} blobs from container")

    documents = []
    temp_dir = tempfile.mkdtemp(prefix="rag_kb_")

    logger.info(f"Created temporary directory: {temp_dir}")

    try:
        for blob_name in blob_names:
            local_path = os.path.join(temp_dir, blob_name)

            # Download blob
            try:
                download_document(blob_name, local_path)
            except Exception as e:
                logger.error(f"Failed to download blob '{blob_name}': {str(e)}")
                continue

            # Extract text based on file type
            try:
                if blob_name.lower().endswith(".pdf"):
                    logger.info(f"Loading PDF: {blob_name}")
                    loader = PyPDFLoader(local_path)
                    documents.extend(loader.load())

                elif blob_name.lower().endswith(".txt"):
                    logger.info(f"Loading TXT: {blob_name}")
                    loader = TextLoader(local_path, encoding="utf-8")
                    documents.extend(loader.load())

                else:
                    logger.warning(f"Unsupported file type, skipping: {blob_name}")

            except Exception as e:
                logger.error(f"Error processing blob '{blob_name}': {str(e)}", exc_info=True)
                continue

        logger.info(f"Loaded {len(documents)} documents from {len(blob_names)} blobs")

        if not documents:
            logger.warning("No documents were successfully loaded. Vector DB not created.")
            return

        # Split into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=50
        )

        chunks = splitter.split_documents(documents)

        logger.info(f"Created {len(chunks)} document chunks")

        # Generate embeddings and store in ChromaDB
        Chroma.from_documents(
            documents=chunks,
            embedding=embedding_model,
            persist_directory=DB_PATH
        )

        logger.info(f"Vector database created successfully at {DB_PATH}")

    finally:
        # Always clean up temporary files
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temporary files from {temp_dir}")
        except Exception as e:
            logger.warning(
                f"Failed to clean up temporary directory '{temp_dir}': {str(e)}",
                exc_info=True
            )


# =========================
# SEARCH DOCUMENTS
# =========================

def search_documents(query: str) -> List[str]:
    """
    Perform a similarity search against the ChromaDB vector database.

    Args:
        query (str): The search query string.

    Returns:
        List[str]: List of matching document page contents (up to 3 results).
                   Returns an empty list if an error occurs.

    Raises:
        FileNotFoundError: If the vector database has not been created yet.
    """
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            f"Vector database not found at '{DB_PATH}'. "
            "Please run create_vector_db() first to build the knowledge base."
        )

    try:
        vector_db = Chroma(
            persist_directory=DB_PATH,
            embedding_function=embedding_model
        )

        results = vector_db.similarity_search(query, k=3)

        return [doc.page_content for doc in results]

    except FileNotFoundError:
        raise

    except Exception as e:
        logger.error(f"Search error for query '{query}': {str(e)}", exc_info=True)
        return []
