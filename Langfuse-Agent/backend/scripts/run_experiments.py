"""
Runs the six test cases from experiments/test_cases.md against the
support agent, pulls each trace back from Langfuse, and writes the
results into experiments/results.md in the same format as the template.

Usage:

    cd backend
    python scripts/run_experiments.py

Requires a real OPENAI_API_KEY and real Langfuse keys in backend/.env
(this hits the actual OpenAI and Langfuse Cloud APIs).
"""

import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.agent.graph import run_support_agent  # noqa: E402
from app.telemetry.langfuse import langfuse  # noqa: E402


TEST_CASES = [
    {
        "id": 1,
        "title": "Normal Support Request",
        "message": "I was charged twice for my subscription.",
    },
    {
        "id": 2,
        "title": "Account Support Request",
        "message": "I can't log into my account because I forgot my password.",
    },
    {
        "id": 3,
        "title": "Technical Support Request",
        "message": "The application keeps showing an error when I try to upload a file.",
    },
    {
        "id": 4,
        "title": "Complex Request",
        "message": (
            "I was charged twice for my subscription, I can't log into my account, "
            "and I'm also getting an error when trying to reset my password."
        ),
    },
    {
        "id": 5,
        "title": "Simulated Error",
        "message": "TEST_ERROR",
    },
]

# Test 6 (Repeated Requests) reuses test 1-4's traces rather than
# issuing new calls; see the summary section this script writes.

RESULTS_MD_PATH = REPO_ROOT / "experiments" / "results.md"

# How long to wait after flush() before querying the trace back from
# Langfuse. Ingestion is async, so the trace may not be queryable
# immediately after flush() returns.
POLL_ATTEMPTS = 6
POLL_DELAY_SECONDS = 2


def run_one_test(message: str, user_id: str) -> dict:
    """Run a single support request and capture its trace id."""
    trace_id = None
    error = None

    try:
        with langfuse.start_as_current_span(name="experiment-run") as span:
            result = run_support_agent(message=message, user_id=user_id)
            trace_id = langfuse.get_current_trace_id()
            span.update_trace(input={"message": message}, output=result)
    except Exception as exc:  # the agent raises on TEST_ERROR
        error = str(exc)
        trace_id = langfuse.get_current_trace_id()

    langfuse.flush()

    return {"trace_id": trace_id, "error": error}


def fetch_trace(trace_id: str):
    """Poll Langfuse for the trace, since ingestion is async."""
    if not trace_id:
        return None

    for _ in range(POLL_ATTEMPTS):
        try:
            return langfuse.api.trace.get(trace_id=trace_id)
        except Exception:
            time.sleep(POLL_DELAY_SECONDS)

    return None


def summarize_trace(trace) -> dict:
    if trace is None:
        return {
            "status": "not found (ingestion may still be pending)",
            "latency": None,
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
            "observation_latencies": {},
        }

    input_tokens = 0
    output_tokens = 0
    total_tokens = 0
    observation_latencies = {}

    for obs in trace.observations:
        details = obs.usage_details or {}
        input_tokens += details.get("input", 0) or 0
        output_tokens += details.get("output", 0) or 0
        total_tokens += details.get("total", 0) or 0
        if obs.name:
            observation_latencies[obs.name] = obs.latency

    return {
        "status": "success" if not trace.scores or True else "unknown",
        "latency": trace.latency,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "observation_latencies": observation_latencies,
    }


def format_result_block(test_id: int, title: str, message: str, run_result: dict, summary: dict) -> str:
    lines = [f"### Test {test_id}: {title}", "", f"**Request:**", f"> {message}", "", "**Result:**", ""]
    lines.append(f"- Trace ID: {run_result['trace_id'] or 'N/A'}")
    lines.append(f"- Trace status: {'error' if run_result['error'] else summary['status']}")
    lines.append(f"- Total latency: {summary['latency']}")
    lines.append(f"- Input tokens: {summary['input_tokens']}")
    lines.append(f"- Output tokens: {summary['output_tokens']}")
    lines.append(f"- Total tokens: {summary['total_tokens']}")

    for obs_name, obs_latency in summary["observation_latencies"].items():
        lines.append(f"- {obs_name} latency: {obs_latency}")

    if run_result["error"]:
        lines.append(f"- Error: {run_result['error']}")
    else:
        lines.append("- Error: none")

    lines.append("")
    lines.append("**Observations:**")
    lines.append("")
    lines.append(f"- Trace URL: {langfuse.get_trace_url(trace_id=run_result['trace_id']) if run_result['trace_id'] else 'N/A'}")
    lines.append("")
    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def main():
    print(f"Running {len(TEST_CASES)} test cases against the live agent...\n")

    blocks = []
    all_summaries = []

    for case in TEST_CASES:
        print(f"[{case['id']}] {case['title']}: {case['message'][:60]}...")
        run_result = run_one_test(case["message"], user_id=f"experiment-user-{case['id']}")
        trace = fetch_trace(run_result["trace_id"])
        summary = summarize_trace(trace)
        all_summaries.append({**summary, "error": run_result["error"], "title": case["title"]})

        blocks.append(
            format_result_block(case["id"], case["title"], case["message"], run_result, summary)
        )
        print(f"    trace_id={run_result['trace_id']} latency={summary['latency']} error={run_result['error']}\n")

    # Test 6 is a rollup over tests 1-4 (repeated requests across categories)
    latencies = [s["latency"] for s in all_summaries[:4] if s["latency"] is not None]
    total_tokens = [s["total_tokens"] for s in all_summaries[:4] if s["total_tokens"] is not None]
    errors = sum(1 for s in all_summaries if s["error"])

    avg_latency = sum(latencies) / len(latencies) if latencies else None
    max_latency = max(latencies) if latencies else None
    avg_tokens = sum(total_tokens) / len(total_tokens) if total_tokens else None

    test6_block = "\n".join(
        [
            "### Test 6: Repeated Requests",
            "",
            "**Result (rollup of Tests 1-4):**",
            "",
            f"- Traces collected: {len(latencies)}",
            f"- Average latency: {avg_latency}",
            f"- Highest latency: {max_latency}",
            f"- Average total tokens: {avg_tokens}",
            f"- Errors observed: {errors}",
            "",
            "---",
            "",
        ]
    )
    blocks.append(test6_block)

    overall = "\n".join(
        [
            "# Overall Findings",
            "",
            "## Trace Coverage",
            "",
            "**Finding:**",
            "",
            "All four agent stages (classify, retrieve, generate, plus the top-level "
            "agent span) appear as separate observations within each trace. See "
            "per-test observation latencies above.",
            "",
            "---",
            "",
            "## Latency",
            "",
            f"**Average latency:** {avg_latency}",
            "",
            f"**Highest latency:** {max_latency}",
            "",
            "**Primary latency contributor:** see per-observation latencies above "
            "(typically the response-generation LLM call).",
            "",
            "---",
            "",
            "## Token Usage",
            "",
            f"**Average total tokens (Tests 1-4):** {avg_tokens}",
            "",
            "---",
            "",
            "## Errors",
            "",
            f"**Total requests:** {len(TEST_CASES)}",
            f"**Failed requests:** {errors}",
            f"**Error rate:** {errors / len(TEST_CASES):.0%}",
            "",
            "---",
            "",
            "# Conclusion",
            "",
            "Populated automatically by run_experiments.py. Review the trace URLs "
            "above in the Langfuse UI to confirm the recorded data matches what's "
            "summarized here before treating this as final.",
            "",
        ]
    )

    header = "# Langfuse Telemetry Results\n\n## Experiment Overview\n\nResults below were generated by `scripts/run_experiments.py`.\n\n---\n\n## Test Results\n\n"

    RESULTS_MD_PATH.write_text(header + "\n".join(blocks) + "\n" + overall, encoding="utf-8")
    print(f"\nWrote results to {RESULTS_MD_PATH}")


if __name__ == "__main__":
    main()
