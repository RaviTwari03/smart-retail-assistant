from services.rag_service import search_documents


def customer_support_agent(query):

    documents = search_documents(query)

    # No results found
    if not documents:

        return (
            "Sorry, I could not find any information "
            "related to your query."
        )

    # Take only top result
    best_match = documents[0]

    # Clean formatting
    cleaned_response = best_match.replace("\n", " ")

    # Shorten overly long responses
    if len(cleaned_response) > 400:

        cleaned_response = cleaned_response[:400] + "..."

    # Final AI-style response
    response = (
        f"According to RetailMart policies:\n\n"
        f"{cleaned_response}"
    )

    return response