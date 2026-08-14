# Langfuse-Agent

An AI customer support agent proof of concept built to evaluate **Langfuse observability and telemetry** on an LLM-powered workflow.

The project demonstrates how to instrument an AI agent to capture:

- **Traces** across the full agent workflow
- **Latency** for individual pipeline stages and LLM calls
- **Token usage** from OpenAI generations
- **Errors** and failed requests
- **Nested spans and observations** for debugging and performance analysis

The goal is to validate Langfuse telemetry on a small, isolated application before applying the same observability patterns to larger production workflows.

---

## Overview

The agent accepts a customer support request and processes it through three stages:

1. **Classify the request** — determines the category and priority.
2. **Retrieve information** — selects the relevant knowledge base article.
3. **Generate a response** — uses the classification and retrieved information to produce a customer-facing response.

Each stage is instrumented with Langfuse's `@observe` decorator, allowing the entire workflow to appear as a trace with nested observations.

### Agent Workflow

```text
POST /support
      │
      ▼
run_support_agent
   [Agent Span]
      │
      ├──► classify_ticket
      │       [Chain Span]
      │           │
      │           └──► call_llm
      │                [Generation]
      │                → category + priority
      │
      ├──► retrieve_information
      │       [Tool Span]
      │           │
      │           └──► knowledge_base/{category}.md
      │
      └──► generate_response
              [Chain Span]
                  │
                  └──► call_llm
                       [Generation]
                       → final response
Each support request produces a Langfuse trace containing the agent workflow, nested pipeline stages, and LLM generations.

---
## Telemetry Goals

The primary purpose of this project is to verify that **Langfuse** can provide useful observability data for an LLM application before expanding telemetry to additional application workflows.

| Metric | Purpose |
|---|---|
| **Traces** | Track the complete execution of each support request |
| **Latency** | Measure execution time for pipeline stages and LLM calls |
| **Token Usage** | Track input and output tokens consumed by LLM calls |
| **Errors** | Capture exceptions and failed agent executions |
| **Observations** | Inspect individual operations within the agent workflow |
| **LLM Generations** | Monitor model calls, inputs, outputs, and token usage |

### Why This Matters

The collected telemetry can be used to:

- Identify slow pipeline stages and LLM calls
- Monitor and analyze LLM token usage
- Debug failed agent executions
- Inspect individual steps within the workflow
- Evaluate the performance and reliability of the agent
- Determine whether Langfuse should be expanded to additional application workflows

The goal is not just to add tracing, but to **verify that the telemetry provides actionable information** that can be used to understand, debug, and improve an LLM-powered application.

## Tech Stack

| Technology | Purpose |
|---|---|
| **Python 3.9+** | Core programming language |
| **FastAPI** | REST API and backend application |
| **OpenAI API** | LLM inference and response generation |
| **Langfuse** | LLM observability, tracing, and telemetry |
| **Pydantic** | Request and response validation |
| **Pytest** | Automated testing |
| **Markdown** | Local knowledge base storage |

## Project Structure

```text
Langfuse-Agent/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   │   └── FastAPI application and API endpoints
│   │   │
│   │   ├── agent/
│   │   │   ├── graph.py
│   │   │   │   └── Agent workflow
│   │   │   ├── nodes.py
│   │   │   │   └── Classification, retrieval, and response generation
│   │   │   └── prompts.py
│   │   │       └── LLM prompts
│   │   │
│   │   ├── models/
│   │   │   └── schemas.py
│   │   │       └── Pydantic request/response models
│   │   │
│   │   ├── services/
│   │   │   ├── llm.py
│   │   │   │   └── OpenAI LLM wrapper
│   │   │   └── knowledge_base.py
│   │   │       └── Knowledge base lookup
│   │   │
│   │   └── telemetry/
│   │       └── langfuse.py
│   │           └── Langfuse client and trace utilities
│   │
│   ├── scripts/
│   │   └── run_experiments.py
│   │       └── End-to-end telemetry experiments
│   │
│   ├── tests/
│   │   ├── test_agent.py
│   │   │   └── Agent logic tests
│   │   └── test_telemetry.py
│   │       └── Langfuse instrumentation tests
│   │
│   ├── requirements.txt
│   ├── .env.example
│   └── .env
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

## Installation

### 1. Clone the Repository

```
git clone https://github.com/riyav-star/Langfuse-Agent.git
```

cd Langfuse-Agent

### 2. Create a Virtual Environment

```
cd backend
```

python -m venv venv

Activate the virtual environment.

#### macOS / Linux

```
source venv/bin/activate
```

#### Windows

```
venv\Scripts\activate
```

### 3. Install Dependencies

```
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file inside the `backend` directory.

```
OPENAI_API_KEY=your_openai_api_key
```




LANGFUSE\_PUBLIC\_KEY=your\_langfuse\_public\_key

LANGFUSE\_SECRET\_KEY=your\_langfuse\_secret\_key

LANGFUSE\_BASE\_URL=[https://cloud.langfuse.com](https://cloud.langfuse.com)




LANGFUSE\_TRACING\_ENVIRONMENT=development

Never commit real API keys to GitHub.

The repository includes `.env.example` as a template.

---

## Running the API

From the `backend` directory:

```
uvicorn app.main:app --reload
```

The API will run at:

```
http://127.0.0.1:8000
```

### Available Endpoints

| MethodEndpointDescription |            |                         |
| ------------------------- | ---------- | ----------------------- |
| `GET`                     | `/`        | Basic application check |
| `GET`                     | `/health`  | Health check            |
| `POST`                    | `/support` | Run the support agent   |

---

## Health Check

With the API running, open another terminal and run:

```
curl http://localhost:8000/health
```

Expected response:

```
{
```

  "status": "healthy"

}

---

## Running the Support Agent

Send a customer support request:

```
curl -X POST http://localhost:8000/support \
```

-H "Content-Type: application/json" \\

-d '{

    "message": "I was charged twice for my subscription.",

    "user\_id": "user-1"

  }'

The agent will:

1.  Classify the request. 
2.  Determine its priority. 
3.  Retrieve the relevant knowledge base information. 
4.  Generate a customer-facing response. 
5.  Record telemetry through Langfuse. 

---

## Langfuse Instrumentation

Langfuse is integrated throughout the agent pipeline using the `@observe` decorator.

Example:

```
from langfuse import observe
```




@observe()

def classify\_ticket(message):

    ...

The LLM service is also instrumented so that model calls can be monitored separately from the rest of the agent workflow.

This creates a hierarchy similar to:

```
Support Request
```

│

├── run\_support\_agent

│   │

│   ├── classify\_ticket

│   │   └── call\_llm

│   │

│   ├── retrieve\_information

│   │

│   └── generate\_response

│       └── call\_llm

This structure allows individual operations to be inspected inside the overall request trace.

## What Langfuse Captures

### Traces

Each support request creates a trace representing the complete execution of the agent.

This makes it possible to follow a request from the initial user message through classification, retrieval, and response generation.

### Latency

The telemetry allows individual operations to be inspected for execution time.

For example:

```
Total Request
```

│

├── Classification       850 ms

├── Knowledge Retrieval    5 ms

└── Response Generation  1.2 s

This can help identify slow LLM calls and other performance bottlenecks.

### Token Usage

LLM generations expose token usage information, allowing the application to track input and output tokens.

This can be used to evaluate:

-  LLM usage 
-  API costs 
-  Prompt efficiency 
-  Changes in token consumption 
-  Model usage patterns 

### Error Tracking

The project includes an intentional error path for testing telemetry.

Send:

```
{
```

  "message": "TEST\_ERROR",

  "user\_id": "test-user"

}

This deliberately triggers an exception so that failed requests can be verified in Langfuse.

The goal is to confirm that both successful and failed executions are observable.

---

## Running Tests

The project includes automated tests for the agent logic and telemetry instrumentation.

Run:

```
cd backend
```

pytest tests/ -v

The tests mock external OpenAI and Langfuse calls, so they do not require network access or consume API credits.

The test suite covers:

-  Classification parsing 
-  Knowledge base routing 
-  Knowledge base fallbacks 
-  Full agent pipeline execution 
- `/support` endpoint behavior 
-  Error handling 
- `@observe` instrumentation 
-  Trace URL generation 

These tests validate the application's implementation.

They do not replace live verification in the Langfuse dashboard.

---

## Running Telemetry Experiments

The project includes an experiment script for validating telemetry against the live application.

Run:

```
cd backend
```

python scripts/run\_experiments.py

The experiment suite includes scenarios such as:

-  Billing requests 
-  Account requests 
-  Technical issues 
-  Multi-issue requests 
-  Simulated errors 
-  Repeated requests 

The script sends requests through the live agent and retrieves the resulting Langfuse telemetry.

Results are written to:

```
experiments/results.md
```

The results can include:

-  Trace information 
-  Trace URLs 
-  Total latency 
-  LLM latency 
-  Token usage 
-  Observation timings 
-  Error information 

> **Note:** Running the experiments uses real OpenAI and Langfuse services and may incur API usage costs.

## Verifying Langfuse Telemetry

After running the application or experiment script:

1.  Open your Langfuse project. 
2.  Navigate to the traces/observability section. 
3.  Find the trace generated by the support request. 
4.  Open the trace. 
5.  Inspect the nested observations. 
6.  Verify the LLM generations. 
7.  Check latency information. 
8.  Check token usage. 
9.  Send the `TEST_ERROR` request. 
10.  Verify that the failed request appears in Langfuse. 

The purpose is not simply to confirm that Langfuse is installed.

The purpose is to determine whether the collected telemetry is actually useful for understanding the behavior and performance of the LLM workflow.

---

## Example Telemetry

A successful request should produce a trace similar to:

```
Trace: support-request
```

│

├── run\_support\_agent

│   │

│   ├── classify\_ticket

│   │   └── call\_llm

│   │       ├── Input tokens

│   │       ├── Output tokens

│   │       └── Latency

│   │

│   ├── retrieve\_information

│   │   └── Knowledge base lookup

│   │

│   └── generate\_response

│       └── call\_llm

│           ├── Input tokens

│           ├── Output tokens

│           └── Latency

│

└── Total trace latency

An unsuccessful request should allow the error to be associated with the relevant trace and operation.

---

## Knowledge Base

The project uses a simple local Markdown knowledge base rather than a vector database.

```
knowledge_base/
```

├── account.md

├── billing.md

├── refunds.md

└── technical.md

The agent maps the classified category to the corresponding Markdown file.

For example:

```
billing   → knowledge_base/billing.md
```

account   → knowledge\_base/account.md

refund    → knowledge\_base/refunds.md

technical → knowledge\_base/technical.md

The simple retrieval system keeps the proof of concept focused on telemetry rather than retrieval infrastructure. Key Takeaway

This project demonstrates a practical approach to introducing **LLM observability with Langfuse**.

Rather than simply adding logging, the project instruments an end-to-end AI workflow and evaluates whether the resulting telemetry can answer practical engineering questions:

```
What happened?
```

      ↓

How long did it take?

      ↓

How many tokens were used?

      ↓

Where did it fail?

The proof of concept provides a foundation for determining how Langfuse telemetry can be expanded across larger AI-powered application workflows.

---

## License

This project is licensed under the **MIT License**.
