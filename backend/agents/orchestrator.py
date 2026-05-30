"""
Multi-Agent Orchestrator
========================
Coordinates all agents in the Smart Retail Assistant platform.

Agents:
    - Customer Support Agent  → RAG + LLM answer from knowledge base
    - Inventory Agent         → Stock level classification
    - Forecast Agent          → Prophet-based sales forecast + insights
    - Data Analyst Agent      → Walmart dataset analytics
    - Document Search Agent   → Raw RAG chunk retrieval

The orchestrator routes queries to the appropriate agent(s)
based on the request context and returns a unified response.
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


def orchestrator(query: str, stock: int) -> Dict:
    """
    Run all relevant agents and return a unified multi-agent response.

    Args:
        query (str): The user's natural language query.
        stock (int): Current stock level for inventory assessment.

    Returns:
        Dict with responses from all agents.
    """
    logger.info(f"Orchestrator received query: '{query}', stock: {stock}")

    from agents.customer_support.support_agent import customer_support_agent
    from agents.inventory_agent.inventory_agent import inventory_agent
    from agents.forecast_agent.forecast_agent import forecast_agent
    from agents.data_analyst.data_analyst_agent import data_analyst_agent
    from agents.document_search.document_search_agent import document_search_agent

    # Run all agents
    support_response = customer_support_agent(query)
    inventory_response = inventory_agent(stock)
    forecast_response = forecast_agent()
    analyst_response = data_analyst_agent(query)
    doc_search_response = document_search_agent(query)

    return {
        "support_agent": support_response,
        "inventory_agent": inventory_response,
        "forecast_agent": forecast_response,
        "data_analyst_agent": analyst_response,
        "document_search_agent": doc_search_response
    }
