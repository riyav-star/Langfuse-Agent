from langfuse import observe

from app.agent.nodes import (
    classify_ticket,
    retrieve_information,
    generate_response,
)


@observe(as_type="agent")
def run_support_agent(message: str, user_id: str) -> dict:
    classification = classify_ticket(message)

    knowledge = retrieve_information(
        classification["category"]
    )

    response = generate_response(
        message=message,
        knowledge=knowledge["content"],
    )

    return {
        "category": classification["category"],
        "priority": classification["priority"],
        "response": response,
        "source": knowledge["source"],
    }