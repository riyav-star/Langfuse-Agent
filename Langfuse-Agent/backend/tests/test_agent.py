"""
Tests for the agent pipeline (classification, retrieval, response
generation) and the /support FastAPI endpoint.

All OpenAI and Langfuse calls are mocked, so these tests do not
require network access or consume API credits.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.agent.nodes import (
    classify_ticket,
    retrieve_information,
    generate_response,
)
from app.agent.graph import run_support_agent
from app.main import app
from app.services.knowledge_base import search_knowledge_base


# ---------------------------------------------------------------------------
# Classification parsing
# ---------------------------------------------------------------------------

class TestClassifyTicket:
    def test_parses_category_and_priority(self):
        fake_llm_output = "Category: billing\nPriority: high"

        with patch(
            "app.agent.nodes.call_llm", return_value=fake_llm_output
        ) as mock_call_llm:
            result = classify_ticket("I was charged twice.")

        assert result == {"category": "billing", "priority": "high"}
        mock_call_llm.assert_called_once()

    def test_is_case_insensitive_and_trims_whitespace(self):
        fake_llm_output = "  CATEGORY:  Technical  \n  PRIORITY:   Low  "

        with patch("app.agent.nodes.call_llm", return_value=fake_llm_output):
            result = classify_ticket("My app keeps crashing.")

        assert result == {"category": "technical", "priority": "low"}

    def test_defaults_when_fields_are_missing(self):
        # LLM didn't follow the expected format.
        fake_llm_output = "I'm not sure how to categorize this."

        with patch("app.agent.nodes.call_llm", return_value=fake_llm_output):
            result = classify_ticket("???")

        assert result == {"category": "technical", "priority": "medium"}

    def test_ignores_unrelated_lines(self):
        fake_llm_output = (
            "Here is my answer:\n"
            "Category: refund\n"
            "Some extra commentary\n"
            "Priority: high\n"
        )

        with patch("app.agent.nodes.call_llm", return_value=fake_llm_output):
            result = classify_ticket("I want my money back.")

        assert result == {"category": "refund", "priority": "high"}


# ---------------------------------------------------------------------------
# Knowledge base routing / fallbacks
# ---------------------------------------------------------------------------

class TestKnowledgeBaseRouting:
    @pytest.mark.parametrize(
        "category,expected_file",
        [
            ("billing", "billing.md"),
            ("account", "account.md"),
            ("technical", "technical.md"),
            ("refund", "refunds.md"),
        ],
    )
    def test_known_category_maps_to_expected_file(self, category, expected_file):
        result = search_knowledge_base(category)

        assert result["source"] == expected_file
        assert len(result["content"]) > 0

    def test_unknown_category_falls_back_to_technical(self):
        result = search_knowledge_base("some-made-up-category")

        assert result["source"] == "technical.md"

    def test_missing_file_returns_no_documentation_found(self):
        from pathlib import Path

        with patch(
            "app.services.knowledge_base.KNOWLEDGE_BASE_DIR",
            Path("/nonexistent/path"),
        ):
            result = search_knowledge_base("billing")

        assert result["source"] == "none"
        assert "No relevant documentation" in result["content"]

    def test_retrieve_information_delegates_to_knowledge_base(self):
        with patch(
            "app.agent.nodes.search_knowledge_base",
            return_value={"source": "billing.md", "content": "billing info"},
        ) as mock_search:
            result = retrieve_information("billing")

        mock_search.assert_called_once_with("billing")
        assert result == {"source": "billing.md", "content": "billing info"}


# ---------------------------------------------------------------------------
# Response generation
# ---------------------------------------------------------------------------

class TestGenerateResponse:
    def test_calls_llm_with_message_and_knowledge(self):
        with patch(
            "app.agent.nodes.call_llm", return_value="Here is your answer."
        ) as mock_call_llm:
            result = generate_response(
                message="I was charged twice.",
                knowledge="Refund policy details.",
            )

        assert result == "Here is your answer."

        _, kwargs = mock_call_llm.call_args
        assert "I was charged twice." in kwargs["user_prompt"]
        assert "Refund policy details." in kwargs["user_prompt"]


# ---------------------------------------------------------------------------
# Full agent pipeline execution
# ---------------------------------------------------------------------------

class TestRunSupportAgent:
    def test_full_pipeline_wires_stages_together(self):
        with patch(
            "app.agent.graph.classify_ticket",
            return_value={"category": "billing", "priority": "high"},
        ) as mock_classify, patch(
            "app.agent.graph.retrieve_information",
            return_value={"source": "billing.md", "content": "billing info"},
        ) as mock_retrieve, patch(
            "app.agent.graph.generate_response",
            return_value="Here is your answer.",
        ) as mock_generate:
            result = run_support_agent(
                message="I was charged twice.",
                user_id="user-1",
            )

        mock_classify.assert_called_once_with("I was charged twice.")
        mock_retrieve.assert_called_once_with("billing")
        mock_generate.assert_called_once_with(
            message="I was charged twice.",
            knowledge="billing info",
        )

        assert result == {
            "category": "billing",
            "priority": "high",
            "response": "Here is your answer.",
            "source": "billing.md",
        }

    def test_test_error_short_circuits_before_any_stage_runs(self):
        # Regression test: TEST_ERROR must raise from *inside*
        # run_support_agent (the @observe-decorated function) so the
        # failure is captured as part of a Langfuse trace, rather than
        # being raised by the caller before any trace exists.
        with patch("app.agent.graph.classify_ticket") as mock_classify, patch(
            "app.agent.graph.retrieve_information"
        ) as mock_retrieve, patch(
            "app.agent.graph.generate_response"
        ) as mock_generate:
            with pytest.raises(RuntimeError, match="Simulated agent failure"):
                run_support_agent(message="TEST_ERROR", user_id="test-user")

        mock_classify.assert_not_called()
        mock_retrieve.assert_not_called()
        mock_generate.assert_not_called()


# ---------------------------------------------------------------------------
# /support endpoint behavior
# ---------------------------------------------------------------------------

client = TestClient(app)


class TestSupportEndpoint:
    def test_success_returns_agent_result(self):
        fake_result = {
            "category": "billing",
            "priority": "high",
            "response": "Here is your answer.",
            "source": "billing.md",
        }

        with patch("app.main.run_support_agent", return_value=fake_result):
            response = client.post(
                "/support",
                json={"message": "I was charged twice.", "user_id": "user-1"},
            )

        assert response.status_code == 200
        assert response.json() == fake_result

    def test_agent_exception_returns_500(self):
        with patch(
            "app.main.run_support_agent",
            side_effect=RuntimeError("boom"),
        ):
            response = client.post(
                "/support",
                json={"message": "hello", "user_id": "user-1"},
            )

        assert response.status_code == 500
        assert (
            response.json()["detail"]
            == "The support agent encountered an error."
        )

    def test_test_error_message_returns_500(self):
        # End-to-end through the real (unmocked) run_support_agent:
        # confirms the TEST_ERROR path is reachable via the API and
        # surfaces as a 500, matching the documented telemetry
        # error-testing flow.
        response = client.post(
            "/support",
            json={"message": "TEST_ERROR", "user_id": "test-user"},
        )

        assert response.status_code == 500

    def test_missing_message_is_rejected(self):
        response = client.post("/support", json={"user_id": "user-1"})

        assert response.status_code == 422

    def test_root_and_health_endpoints(self):
        assert client.get("/").json() == {
            "message": "Langfuse Agent API is running"
        }
        assert client.get("/health").json() == {"status": "healthy"}
