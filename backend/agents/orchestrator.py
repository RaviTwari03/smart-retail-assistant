from agents.customer_support.support_agent import customer_support_agent
from agents.inventory_agent.inventory_agent import inventory_agent


def orchestrator(query, stock):

    support_response = customer_support_agent(query)

    inventory_response = inventory_agent(stock)

    return {
        "support_agent": support_response,
        "inventory_agent": inventory_response
    }