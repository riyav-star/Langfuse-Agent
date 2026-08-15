from langfuse import observe

from app.agent.nodes import (
    classify_ticket,
    retrieve_information,
    generate_response,
)


@observe(as_type="agent")
def run_support_agent(message: str, user_id: str) -> dict:
    # Special test case for telemetry experiments.
    # Kept inside the traced function so the failure is captured
    # as part of a Langfuse trace, instead of raising before any
    # trace is created.
    if message == "TEST_ERROR":
        raise RuntimeError(
            "Simulated agent failure for telemetry testing"
        )

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
