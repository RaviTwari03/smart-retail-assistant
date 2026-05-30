"""
Document Search Agent
=====================
Searches the RAG knowledge base (Azure Blob → ChromaDB)
and returns relevant policy/FAQ context for a given query.
Distinct from the customer support agent — this agent
returns raw retrieved chunks for use by other agents
or direct API consumers.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def document_search_agent(query: str) -> Dict:
    """
    Search the ChromaDB knowledge base for relevant document chunks.

    Args:
        query (str): The search query.

    Returns:
        Dict with status, query, results list, and source count.
    """
    logger.info(f"Document search agent query: {query}")

    try:
        from services.rag_service import search_documents

        results = search_documents(query)

        if not results:
            return {
                "status": "success",
                "query": query,
                "results": [],
                "count": 0,
                "message": "No relevant documents found for this query."
            }

        return {
            "status": "success",
            "query": query,
            "results": results,
            "count": len(results)
        }

    except FileNotFoundError:
        logger.error("Vector database not found")
        return {
            "status": "error",
            "query": query,
            "results": [],
            "count": 0,
            "message": (
                "Knowledge base not initialized. "
                "Please run create_vector_db() to build the vector database."
            )
        }

    except Exception as e:
        logger.error(f"Document search agent error: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "query": query,
            "results": [],
            "count": 0,
            "message": str(e)
        }
