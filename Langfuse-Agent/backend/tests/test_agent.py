"""
Unit tests for the support agent pipeline.

These tests mock `call_llm` so they run offline, deterministically,
and without spending real OpenAI/Langfuse credits. They check the
agent's own logic (classification parsing, knowledge base routing,
node wiring) rather than the quality of any real model output.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.agent.nodes import classify_ticket, generate_response
from app.agent.graph import run_support_agent
from app.services.knowledge_base import search_knowledge_base
from app.main import app


client = TestClient(app)


# ---------------------------------------------------------------------
# classify_ticket
# ---------------------------------------------------------------------

class TestClassifyTicket:
    def test_parses_category_and_priority(self):
        with patch(
            "app.agent.nodes.call_llm",
            return_value="Category: billing\nPriority: high",
        ):
            result = classify_ticket("I was charged twice")

        assert result == {"category": "billing", "priority": "high"}

    def test_is_case_insensitive_on_labels(self):
        with patch(
            "app.agent.nodes.call_llm",
            return_value="CATEGORY: Account\nPRIORITY: Low",
        ):
            result = classify_ticket("locked out of my account")

        assert result == {"category": "account", "priority": "low"}

    def test_falls_back_to_defaults_when_unparseable(self):
        with patch(
            "app.agent.nodes.call_llm",
            return_value="the model said something unstructured",
        ):
            result = classify_ticket("some message")

        assert result == {"category": "technical", "priority": "medium"}

    def test_handles_partial_output(self):
        # Only category present, no priority line
        with patch(
            "app.agent.nodes.call_llm",
            return_value="Category: refund",
        ):
            result = classify_ticket("please refund my order")

        assert result["category"] == "refund"
        assert result["priority"] == "medium"  # default


# ---------------------------------------------------------------------
# search_knowledge_base
# ---------------------------------------------------------------------

class TestSearchKnowledgeBase:
    @pytest.mark.parametrize(
        "category,expected_file",
        [
            ("billing", "billing.md"),
            ("account", "account.md"),
            ("technical", "technical.md"),
            ("refund", "refunds.md"),
        ],
    )
    def test_known_categories_map_to_expected_file(self, category, expected_file):
        result = search_knowledge_base(category)
        assert result["source"] == expected_file
        assert result["content"]  # non-empty

    def test_unknown_category_falls_back_to_technical(self):
        result = search_knowledge_base("some-unrecognized-category")
        assert result["source"] == "technical.md"

    def test_missing_file_reports_no_documentation(self, tmp_path, monkeypatch):
        # Point KNOWLEDGE_BASE_DIR at an empty temp dir to force a miss
        import app.services.knowledge_base as kb_module

        monkeypatch.setattr(kb_module, "KNOWLEDGE_BASE_DIR", tmp_path)
        result = kb_module.search_knowledge_base("billing")

        assert result["source"] == "none"
        assert "No relevant documentation" in result["content"]


# ---------------------------------------------------------------------
# generate_response
# ---------------------------------------------------------------------

class TestGenerateResponse:
    def test_passes_message_and_knowledge_into_prompt(self):
        with patch("app.agent.nodes.call_llm") as mock_llm:
            mock_llm.return_value = "Here's how to fix that."
            result = generate_response(
                message="my app crashes on upload",
                knowledge="Technical doc content here.",
            )

        assert result == "Here's how to fix that."
        # confirm both message and knowledge were forwarded to the LLM call
        _, kwargs = mock_llm.call_args
        assert "my app crashes on upload" in kwargs["user_prompt"]
        assert "Technical doc content here." in kwargs["user_prompt"]


# ---------------------------------------------------------------------
# run_support_agent (full pipeline, LLM mocked)
# ---------------------------------------------------------------------

class TestRunSupportAgent:
    def test_full_flow_billing_request(self):
        with patch("app.agent.nodes.call_llm") as mock_llm:
            mock_llm.side_effect = [
                "Category: billing\nPriority: high",  # classify_ticket
                "Here is your refund information.",  # generate_response
            ]
            result = run_support_agent(
                message="I was charged twice", user_id="user-1"
            )

        assert result == {
            "category": "billing",
            "priority": "high",
            "response": "Here is your refund information.",
            "source": "billing.md",
        }

    def test_full_flow_falls_back_to_technical_kb(self):
        with patch("app.agent.nodes.call_llm") as mock_llm:
            mock_llm.side_effect = [
                "Category: something-unrecognized\nPriority: low",
                "General troubleshooting response.",
            ]
            result = run_support_agent(message="weird issue", user_id="user-2")

        assert result["source"] == "technical.md"
        assert result["response"] == "General troubleshooting response."


# ---------------------------------------------------------------------
# /support endpoint (via FastAPI TestClient)
# ---------------------------------------------------------------------

class TestSupportEndpoint:
    def test_root_and_health(self):
        assert client.get("/").status_code == 200
        assert client.get("/health").json() == {"status": "healthy"}

    def test_support_happy_path(self):
        with patch("app.agent.nodes.call_llm") as mock_llm:
            mock_llm.side_effect = [
                "Category: account\nPriority: medium",
                "Try resetting your password from the login screen.",
            ]
            response = client.post(
                "/support",
                json={"message": "I can't log in", "user_id": "user-3"},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["category"] == "account"
        assert body["source"] == "account.md"

    def test_support_test_error_returns_500(self):
        response = client.post(
            "/support",
            json={"message": "TEST_ERROR", "user_id": "user-4"},
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "The support agent encountered an error."
