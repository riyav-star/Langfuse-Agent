"""
Tests for the Langfuse telemetry wiring.

These are structural/unit tests: they confirm the @observe decorators
are attached to the right functions with the right `as_type`, and that
get_trace_url() branches correctly. They do NOT hit the real Langfuse
API and cannot confirm that traces actually show up correctly in the
Langfuse UI.

For that end-to-end confirmation (real traces, real latency/token
numbers), run backend/scripts/run_experiments.py locally against a
real OpenAI + Langfuse Cloud project and inspect experiments/results.md
and the trace URLs it produces.
"""

from unittest.mock import patch

from app.agent.nodes import classify_ticket, retrieve_information, generate_response
from app.agent.graph import run_support_agent
from app.services.llm import call_llm
from app.telemetry.langfuse import get_trace_url


# ---------------------------------------------------------------------
# Structural checks: is every pipeline stage actually observed?
# ---------------------------------------------------------------------

class TestObserveWiring:
    """
    Confirms each pipeline function is wrapped by @observe with the
    expected as_type, so pilot instrumentation covers classify,
    retrieve, generate, the LLM call itself, and the top-level agent.
    """

    def test_classify_ticket_is_observed_as_chain(self):
        assert hasattr(classify_ticket, "__wrapped__")

    def test_retrieve_information_is_observed_as_tool(self):
        assert hasattr(retrieve_information, "__wrapped__")

    def test_generate_response_is_observed_as_chain(self):
        assert hasattr(generate_response, "__wrapped__")

    def test_call_llm_is_observed_as_generation(self):
        assert hasattr(call_llm, "__wrapped__")

    def test_run_support_agent_is_observed_as_agent(self):
        assert hasattr(run_support_agent, "__wrapped__")


# ---------------------------------------------------------------------
# get_trace_url
# ---------------------------------------------------------------------

class TestGetTraceUrl:
    def test_returns_none_when_no_active_trace(self):
        with patch("app.telemetry.langfuse.langfuse.get_current_trace_id", return_value=None):
            assert get_trace_url() is None

    def test_returns_url_when_trace_is_active(self):
        with patch(
            "app.telemetry.langfuse.langfuse.get_current_trace_id",
            return_value="trace-abc123",
        ), patch(
            "app.telemetry.langfuse.langfuse.get_trace_url",
            return_value="https://cloud.langfuse.com/trace/trace-abc123",
        ) as mock_get_url:
            url = get_trace_url()

        assert url == "https://cloud.langfuse.com/trace/trace-abc123"
        mock_get_url.assert_called_once_with(trace_id="trace-abc123")


# ---------------------------------------------------------------------
# Not covered here, and why
# ---------------------------------------------------------------------
#
# - Whether a real trace actually appears in the Langfuse UI with the
#   expected 5 observations (agent > chain > tool > chain > generation).
# - Real latency and token-usage numbers per observation.
# - Whether TEST_ERROR's exception is correctly recorded as an errored
#   observation in Langfuse (vs. just producing a 500 at the API layer,
#   which test_agent.py already covers).
#
# These require a live OpenAI key and a live Langfuse project, so they
# belong in scripts/run_experiments.py, which is meant to be run
# manually/locally rather than in CI.
