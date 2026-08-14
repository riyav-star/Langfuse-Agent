from pathlib import Path


KNOWLEDGE_BASE_DIR = Path(__file__).resolve().parents[3] / "knowledge_base"


def search_knowledge_base(category: str) -> dict:
    """
    Simple keyword-based knowledge-base lookup.

    This is intentionally simple for the telemetry proof of concept.
    We can replace this with vector search later.
    """

    file_mapping = {
        "billing": "billing.md",
        "account": "account.md",
        "technical": "technical.md",
        "refund": "refunds.md",
    }

    filename = file_mapping.get(category, "technical.md")

    file_path = KNOWLEDGE_BASE_DIR / filename

    if not file_path.exists():
        return {
            "source": "none",
            "content": "No relevant documentation was found.",
        }

    content = file_path.read_text(encoding="utf-8")

    return {
        "source": filename,
        "content": content,
    }