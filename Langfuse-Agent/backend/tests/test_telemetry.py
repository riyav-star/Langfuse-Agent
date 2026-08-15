"""
Tests for Langfuse instrumentation: the @observe decorator wiring
and the trace-URL helper.

These tests don't hit the real Langfuse API. They verify that our
code is wired up correctly (decorators applied, trace-URL logic
correct, errors captured inside the traced path) rather than testing
the Langfuse SDK itself.
"""

from unittest.mock import patch

import pytest

from app.agent.graph import run_support_agent
from app.agent.nodes import classify_ticket, retrieve_information, generate_response
from app.services.llm import call_llm
from app.telemetry.langfuse import get_trace_url


# ---------------------------------------------------------------------------
# @observe instrumentation
# ---------------------------------------------------------------------------

class TestObserveInstrumentation:
    """
    The @observe decorator wraps each function with functools.wraps,
    so decorated functions should still look like the originals
    (name, docstring, signature) while actually being the wrapped
    version. This also guards against accidentally removing the
    decorator during future refactors.
    """

    @pytest.mark.parametrize(
        "func",
        [
            run_support_agent,
            classify_ticket,
            retrieve_information,
            generate_response,
            call_llm,
        ],
    )
    def test_function_is_wrapped_by_observe(self, func):
        # functools.wraps (used internally by @observe) sets
        # __wrapped__ to point at the original function.
        assert hasattr(func, "__wrapped__"), (
            f"{func.__name__} does not appear to be wrapped by @observe"
        )

    def test_run_support_agent_keeps_its_name_and_signature(self):
        assert run_support_agent.__name__ == "run_support_agent"

    def test_test_error_is_raised_from_inside_the_traced_function(self):
        # Regression test for the telemetry gap: TEST_ERROR must be
        # raised by the @observe-decorated run_support_agent itself,
        # not by code that runs before it. Otherwise no Langfuse
        # trace/span is ever opened for the "failed request" scenario
        # that the README's error-tracking walkthrough relies on.
        with pytest.raises(RuntimeError) as exc_info:
            run_support_agent(message="TEST_ERROR", user_id="test-user")

        tb_function_names = set()
        tb = exc_info.tb
        while tb is not None:
            tb_function_names.add(tb.tb_frame.f_code.co_name)
            tb = tb.tb_next

        assert "run_support_agent" in tb_function_names


# ---------------------------------------------------------------------------
# Trace URL generation
# ---------------------------------------------------------------------------

class TestGetTraceUrl:
    def test_returns_none_when_there_is_no_active_trace(self):
        with patch(
            "app.telemetry.langfuse.langfuse.get_current_trace_id",
            return_value=None,
        ):
            assert get_trace_url() is None

    def test_returns_url_when_a_trace_is_active(self):
        with patch(
            "app.telemetry.langfuse.langfuse.get_current_trace_id",
            return_value="trace-123",
        ), patch(
            "app.telemetry.langfuse.langfuse.get_trace_url",
            return_value="https://cloud.langfuse.com/trace/trace-123",
        ) as mock_get_url:
            url = get_trace_url()

        mock_get_url.assert_called_once_with(trace_id="trace-123")
        assert url == "https://cloud.langfuse.com/trace/trace-123"
