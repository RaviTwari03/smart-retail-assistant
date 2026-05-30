"""
Customer Support Agent
======================
Multi-step RAG agent for the Smart Retail Assistant.

Pipeline:
    User Query
        ↓ RAG Search (ChromaDB similarity search)
        ↓ Retrieved context chunks from Azure Blob knowledge base
        ↓ LLM (OpenAI GPT) synthesizes a grounded answer
        ↓ Response returned to FastAPI

Environment Variables:
    OPENAI_API_KEY  - Required for LLM synthesis step
"""

import logging
import os
from typing import Optional

from openai import OpenAI

from services.rag_service import search_documents

# =========================
# LOGGING
# =========================

logger = logging.getLogger(__name__)


# =========================
# OPENAI CLIENT
# =========================

def _get_openai_client() -> Optional[OpenAI]:
    """
    Initialize the OpenAI client if an API key is available.

    Returns:
        OpenAI client instance, or None if no API key is configured.
    """
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        logger.warning(
            "OPENAI_API_KEY not set. "
            "Customer support agent will return raw RAG context without LLM synthesis."
        )
        return None

    return OpenAI(api_key=api_key)


# =========================
# PROMPT BUILDER
# =========================

def _build_prompt(query: str, context_chunks: list[str]) -> str:
    """
    Build the RAG prompt by combining retrieved context with the user query.

    Args:
        query (str): The user's question.
        context_chunks (list[str]): Retrieved document chunks from ChromaDB.

    Returns:
        str: Formatted prompt for the LLM.
    """
    context = "\n\n---\n\n".join(context_chunks)

    return f"""You are a helpful customer support assistant for RetailMart.
Use ONLY the information provided in the context below to answer the customer's question.
If the context does not contain enough information to answer, say so clearly.
Do not make up information that is not in the context.

CONTEXT FROM KNOWLEDGE BASE:
{context}

CUSTOMER QUESTION:
{query}

ANSWER:"""


# =========================
# CUSTOMER SUPPORT AGENT
# =========================

def customer_support_agent(query: str) -> str:
    """
    Answer a customer support query using RAG + LLM synthesis.

    Pipeline:
        1. Search ChromaDB for relevant document chunks (built from Azure Blob PDFs)
        2. Build a grounded prompt with retrieved context
        3. Call OpenAI GPT to synthesize a natural language answer
        4. Fall back to best raw chunk if LLM is unavailable

    Args:
        query (str): The customer's question.

    Returns:
        str: A grounded, natural language answer based on the knowledge base.
    """
    logger.info(f"Customer support query: {query}")

    # -------------------------
    # Step 1: RAG Search
    # -------------------------
    try:
        context_chunks = search_documents(query)
    except FileNotFoundError:
        logger.error("Vector database not found. Cannot perform RAG search.")
        return (
            "I'm sorry, the knowledge base is currently unavailable. "
            "Please try again later or contact support directly."
        )
    except Exception as e:
        logger.error(f"RAG search failed: {str(e)}", exc_info=True)
        return (
            "I'm sorry, I encountered an error while searching the knowledge base. "
            "Please try again later."
        )

    if not context_chunks:
        logger.warning(f"No relevant documents found for query: {query}")
        return (
            "I'm sorry, I couldn't find any information related to your question "
            "in our knowledge base. Please contact our support team directly for assistance."
        )

    logger.info(f"Retrieved {len(context_chunks)} context chunks from knowledge base")

    # -------------------------
    # Step 2: LLM Synthesis
    # -------------------------
    client = _get_openai_client()

    if client is None:
        # Fallback: return best raw chunk without LLM
        logger.info("Falling back to raw RAG context (no LLM available)")
        best_chunk = context_chunks[0].replace("\n", " ").strip()

        if len(best_chunk) > 500:
            best_chunk = best_chunk[:500] + "..."

        return (
            f"According to RetailMart policies:\n\n{best_chunk}"
        )

    # -------------------------
    # Step 3: Build prompt and call LLM
    # -------------------------
    try:
        prompt = _build_prompt(query, context_chunks)

        logger.info("Calling LLM for answer synthesis")

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a knowledgeable and friendly customer support assistant "
                        "for RetailMart. Always base your answers strictly on the provided "
                        "knowledge base context. Be concise, clear, and helpful."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=500,
            temperature=0.2
        )

        answer = response.choices[0].message.content.strip()

        logger.info("LLM synthesis complete")

        return answer

    except Exception as e:
        logger.error(f"LLM synthesis failed: {str(e)}", exc_info=True)

        # Fallback to raw chunk if LLM call fails
        logger.info("LLM failed — falling back to raw RAG context")
        best_chunk = context_chunks[0].replace("\n", " ").strip()

        if len(best_chunk) > 500:
            best_chunk = best_chunk[:500] + "..."

        return (
            f"According to RetailMart policies:\n\n{best_chunk}"
        )
