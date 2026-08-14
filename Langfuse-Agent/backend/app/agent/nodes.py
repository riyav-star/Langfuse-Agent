from langfuse import observe

from app.agent.prompts import (
    CLASSIFICATION_SYSTEM_PROMPT,
    RESPONSE_SYSTEM_PROMPT,
)

from app.services.llm import call_llm
from app.services.knowledge_base import search_knowledge_base


@observe(as_type="chain")
def classify_ticket(message: str) -> dict:
    result = call_llm(
        system_prompt=CLASSIFICATION_SYSTEM_PROMPT,
        user_prompt=message,
        operation_name="classify-ticket",
    )

    category = "technical"
    priority = "medium"

    for line in result.splitlines():
        line = line.strip()

        if line.lower().startswith("category:"):
            category = line.split(":", 1)[1].strip().lower()

        elif line.lower().startswith("priority:"):
            priority = line.split(":", 1)[1].strip().lower()

    return {
        "category": category,
        "priority": priority,
    }


@observe(as_type="tool")
def retrieve_information(category: str) -> dict:
    return search_knowledge_base(category)


@observe(as_type="chain")
def generate_response(
    message: str,
    knowledge: str,
) -> str:

    prompt = f"""
Customer message:

{message}

Knowledge base:

{knowledge}

Write the best possible support response.
"""

    return call_llm(
        system_prompt=RESPONSE_SYSTEM_PROMPT,
        user_prompt=prompt,
        operation_name="generate-support-response",
    )