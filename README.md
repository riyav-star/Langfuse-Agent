# Langfuse-Agent

An AI customer-support agent proof of concept built to evaluate **Langfuse observability and telemetry** across an LLM-powered workflow.

The project instruments an end-to-end support workflow to capture:

*  End-to-end traces
*  Pipeline and LLM latency
*  Input/output token usage
*  Errors and failed executions
*  Nested observations and LLM generations

The goal is to determine whether Langfuse provides actionable telemetry that can be used to **debug, monitor, and improve AI application performance** before expanding observability to larger workflows.

---

## Overview

The agent processes a customer-support request through three stages:

```text
Customer Request
       │
       ▼
┌─────────────────────┐
│  Classify Request   │
│  Category + Priority│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Retrieve Information│
│   Knowledge Base    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Generate Response   │
│   Customer Reply    │
└─────────────────────┘
```

Each stage is instrumented with Langfuse so a single request can be inspected as a hierarchical trace.

### Example Trace

```text
run_support_agent
│
├── classify_ticket
│   └── call_llm
│       ├── Input tokens
│       ├── Output tokens
│       └── Latency
│
├── retrieve_information
│   └── Knowledge base lookup
│
└── generate_response
    └── call_llm
        ├── Input tokens
        ├── Output tokens
        └── Latency
```

---

## Key Features

### LLM Observability

Langfuse instrumentation provides visibility into:

| Metric              | Purpose                                         |
| ------------------- | ----------------------------------------------- |
| **Traces**          | Follow each support request end-to-end          |
| **Latency**         | Identify slow pipeline stages and LLM calls     |
| **Token Usage**     | Monitor input/output tokens and API usage       |
| **Errors**          | Investigate failed agent executions             |
| **Observations**    | Inspect individual workflow operations          |
| **LLM Generations** | Monitor model calls, inputs, outputs, and usage |

### Automated Telemetry Experiments

The project includes an experiment runner that sends multiple support scenarios through the live application and retrieves the resulting Langfuse telemetry.

Experiments include:

* Billing requests
* Account requests
* Technical issues
* Multi-issue requests
* Simulated failures
* Repeated requests

Collected results can include:

* Trace information
* Trace URLs
* Total latency
* LLM latency
* Token usage
* Observation timings
* Error information

Results are written to:

```text
experiments/results.md
```

### Error Monitoring

The project includes an intentional `TEST_ERROR` scenario to verify that failed executions can be observed in Langfuse.

Example:

```json
{
  "message": "TEST_ERROR",
  "user_id": "test-user"
}
```

This allows successful and unsuccessful executions to be tested separately.

---

## Tech Stack

* **Python 3.9+**
* **FastAPI** — REST API and backend
* **OpenAI API** — LLM inference
* **Langfuse** — LLM observability and tracing
* **Pydantic** — Request/response validation
* **Pytest** — Automated testing
* **Markdown** — Local knowledge base

---

## Project Structure

```text
Langfuse-Agent/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   │
│   │   ├── agent/
│   │   │   ├── graph.py
│   │   │   ├── nodes.py
│   │   │   └── prompts.py
│   │   │
│   │   ├── models/
│   │   │   └── schemas.py
│   │   │
│   │   ├── services/
│   │   │   ├── llm.py
│   │   │   └── knowledge_base.py
│   │   │
│   │   └── telemetry/
│   │       └── langfuse.py
│   │
│   ├── scripts/
│   │   └── run_experiments.py
│   │
│   ├── tests/
│   │   ├── test_agent.py
│   │   └── test_telemetry.py
│   │
│   ├── requirements.txt
│   └── .env.example
│
├── knowledge_base/
│   ├── account.md
│   ├── billing.md
│   ├── refunds.md
│   └── technical.md
│
├── experiments/
│   ├── test_cases.md
│   └── results.md
│
└── README.md
```

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/riyav-star/Langfuse-Agent.git
cd Langfuse-Agent
```

### 2. Create a Virtual Environment

```bash
cd backend
python -m venv venv
```

**macOS / Linux**

```bash
source venv/bin/activate
```

**Windows**

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file inside `backend/` using `.env.example` as a template:

```env
OPENAI_API_KEY=your_openai_api_key

LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_BASE_URL=https://cloud.langfuse.com

LANGFUSE_TRACING_ENVIRONMENT=development
```

**Never commit API keys or other secrets to GitHub.**

---

## Running the API

From the `backend/` directory:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

### Endpoints

| Method | Endpoint   | Description             |
| ------ | ---------- | ----------------------- |
| `GET`  | `/`        | Basic application check |
| `GET`  | `/health`  | Health check            |
| `POST` | `/support` | Run the support agent   |

---

## Example Request

```bash
curl -X POST http://localhost:8000/support \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I was charged twice for my subscription.",
    "user_id": "user-1"
  }'
```

The agent:

1. Classifies the request
2. Determines its priority
3. Retrieves relevant knowledge
4. Generates a customer-facing response
5. Records telemetry in Langfuse

---

## Running Tests

The project includes automated tests for agent logic and telemetry instrumentation.

```bash
cd backend
pytest tests/ -v
```

Tests cover:

* Classification parsing
* Knowledge-base routing
* Knowledge-base fallbacks
* Full agent pipeline
* `/support` endpoint behavior
* Error handling
* Langfuse instrumentation
* Trace URL generation

External OpenAI and Langfuse calls are mocked during testing, so the test suite does not require network access or consume API credits.

> Automated tests validate the implementation. Live Langfuse experiments are used to verify the resulting telemetry.

---

## Running Telemetry Experiments

To run the live telemetry experiments:

```bash
cd backend
python scripts/run_experiments.py
```

The script sends test cases through the application and retrieves the resulting Langfuse telemetry.

Results are saved to:

```text
experiments/results.md
```

> **Note:** Live experiments use OpenAI and Langfuse services and may incur API usage costs.

---

## Verifying Langfuse Telemetry

After running the application:

1. Open your Langfuse project.
2. Navigate to the traces/observability view.
3. Find the trace generated by a support request.
4. Open the trace.
5. Inspect the nested observations.
6. Verify the LLM generations.
7. Check latency measurements.
8. Check token usage.
9. Trigger the `TEST_ERROR` scenario.
10. Verify that the failed execution is observable.

The goal is not simply to verify that Langfuse is installed.

The goal is to determine whether the collected telemetry can answer practical engineering questions:

```text
What happened?
      ↓
How long did it take?
      ↓
How many tokens were used?
      ↓
Where did it fail?
      ↓
What can be improved?
```

---

## Knowledge Base

The proof of concept uses a simple local Markdown knowledge base:

```text
knowledge_base/
├── account.md
├── billing.md
├── refunds.md
└── technical.md
```

The classified category determines which document is retrieved.

For example:

```text
billing   → billing.md
account   → account.md
refund    → refunds.md
technical → technical.md
```

A simple file-based approach was intentionally used so the project could focus on **LLM observability rather than retrieval infrastructure**.

---

## Engineering Takeaways

This project demonstrates how observability can be integrated into an LLM-powered application to make its behavior measurable and debuggable.

The telemetry provides visibility into:

* End-to-end agent execution
* Individual workflow stages
* LLM performance
* Token consumption
* Application errors
* Execution latency

The proof of concept provides a foundation for evaluating how similar telemetry patterns could be expanded to larger AI application workflows.

---

## License

This project is licensed under the **MIT License**.
