# Langfuse-Agent

An AI customer support agent proof of concept built to evaluate **Langfuse observability and telemetry** across an LLM workflow.

The project instruments an end-to-end support pipeline to capture:

- **Traces** — complete agent execution and nested operations
- **Latency** — timing for the overall request and individual stages
- **Token usage** — input/output usage from LLM generations
- **Errors** — failed requests and exceptions
- **Observations** — individual agent, chain, tool, and LLM operations

The goal is to validate Langfuse on a small LLM workflow before expanding telemetry to larger production AI workflows.

---

## Overview

The agent takes a customer support message and processes it through three stages:

1. **Classify** the support request and determine its priority.
2. **Retrieve** relevant information from a small knowledge base.
3. **Generate** a customer-facing response using the classification and retrieved information.

Langfuse's `@observe` decorator instruments each stage so the complete request can be viewed as a single trace with nested observations.

### Agent Pipeline

```text
                    POST /support
                          │
                          ▼
                 ┌─────────────────┐
                 │ run_support_    │
                 │ agent           │
                 └────────┬────────┘
                          │
             ┌────────────┼────────────┐
             │            │            │
             ▼            ▼            ▼
       classify_ticket  retrieve    generate_response
             │          information        │
             ▼            │                ▼
          call_llm        │             call_llm
             │            │                │
             ▼            ▼                ▼
       category +      knowledge       final response
        priority        article

Each request creates a Langfuse trace containing the agent workflow and its nested observations.
Telemetry
The main purpose of this project is to verify that useful telemetry can be collected from an LLM-powered application.
Telemetry	Purpose
Traces	View the complete execution of a support request
Latency	Identify slow stages and LLM calls
Token Usage	Monitor LLM input/output consumption
Errors	Identify failed requests and exceptions
Observations	Inspect individual operations within a trace
Environment	Distinguish development/test telemetry
This makes it possible to answer questions such as:
How long did the request take?
Which stage was the slowest?
How many tokens did each LLM call use?
Where did an error occur?
What did the complete agent execution look like?
Tech Stack
Technology	Purpose
Python	Application logic
FastAPI	REST API
OpenAI API	LLM inference
Langfuse	LLM observability and telemetry
Pydantic	Request/response validation
Pytest	Automated testing
Uvicorn	ASGI server
Project Structure
Langfuse-Agent/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   │   └── FastAPI application and API endpoints
│   │   │
│   │   ├── agent/
│   │   │   ├── graph.py
│   │   │   │   └── Agent workflow orchestration
│   │   │   ├── nodes.py
│   │   │   │   └── Classification, retrieval, and response nodes
│   │   │   └── prompts.py
│   │   │       └── LLM prompts
│   │   │
│   │   ├── models/
│   │   │   └── schemas.py
│   │   │       └── Pydantic request/response models
│   │   │
│   │   ├── services/
│   │   │   ├── llm.py
│   │   │   │   └── OpenAI client and LLM generation
│   │   │   └── knowledge_base.py
│   │   │       └── Knowledge base lookup
│   │   │
│   │   └── telemetry/
│   │       └── langfuse.py
│   │           └── Langfuse configuration and tracing utilities
│   │
│   ├── scripts/
│   │   └── run_experiments.py
│   │       └── End-to-end telemetry experiments
│   │
│   ├── tests/
│   │   ├── test_agent.py
│   │   │   └── Agent logic tests
│   │   └── test_telemetry.py
│   │       └── Telemetry instrumentation tests
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
├── LICENSE
└── README.md
.env contains local credentials and should never be committed to version control.
Setup
Prerequisites
You will need:
Python 3.9+
An OpenAI API key
A Langfuse account/project
Git
1. Clone the repository
git clone https://github.com/riyav-star/Langfuse-Agent.git
cd Langfuse-Agent
2. Create a virtual environment
cd backend
python -m venv venv
source venv/bin/activate
For Windows:
venv\Scripts\activate
3. Install dependencies
pip install -r requirements.txt
4. Configure environment variables
Create a .env file in the backend/ directory based on .env.example:
OPENAI_API_KEY=your_openai_api_key

LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_BASE_URL=https://cloud.langfuse.com

LANGFUSE_TRACING_ENVIRONMENT=development
Never commit real API keys or secrets to GitHub.
Running the API
From the backend/ directory:
uvicorn app.main:app --port 8000
For development with automatic reload:
uvicorn app.main:app --reload
The API will run at:
http://localhost:8000
API Endpoints
GET /
Basic application check.
GET /health
Health check endpoint.
curl http://localhost:8000/health
Expected response:
{
  "status": "healthy"
}
POST /support
Runs the customer support agent.
Example:
curl -X POST http://localhost:8000/support \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I was charged twice for my subscription.",
    "user_id": "user-1"
  }'
The request is processed by the agent and the corresponding execution is recorded by Langfuse.
Testing Error Tracking
The application includes a deliberate error path for validating error telemetry.
Send:
curl -X POST http://localhost:8000/support \
  -H "Content-Type: application/json" \
  -d '{
    "message": "TEST_ERROR",
    "user_id": "test-user"
  }'
This intentionally triggers an exception.
The resulting failed request can be inspected in Langfuse to verify that errors are associated with the corresponding trace.
Testing
The project includes automated tests for both agent behavior and telemetry instrumentation.
Run the full test suite:
cd backend
pytest tests/ -v
The tests cover:
Classification behavior
Knowledge base routing
Knowledge base fallbacks
Agent pipeline execution
/support endpoint behavior
Error handling
Langfuse @observe instrumentation
Telemetry utility functions
LLM calls and Langfuse interactions are mocked during unit tests, so the test suite does not require live API requests or consume API credits.
Unit tests validate application behavior and instrumentation. They do not verify the complete end-to-end Langfuse Cloud integration.
Telemetry Experiments
The project includes an experiment script for validating telemetry using real OpenAI and Langfuse requests.
The experiment suite contains six scenarios:
Billing request
Account request
Technical support request
Multi-issue request
Simulated error
Repeated request
Run the experiments with:
cd backend
python scripts/run_experiments.py
The script sends requests through the live agent and records telemetry results in:
experiments/results.md
The experiment results include information such as:
Trace IDs
Trace URLs
Total request latency
Individual observation latency
Token usage
Successful requests
Failed requests
Error information
Warning: The experiment script uses real OpenAI and Langfuse services and may incur API usage costs.
Knowledge Base
The current implementation uses a simple file-based knowledge base.
Supported categories:
billing
account
technical
refund
The knowledge base is organized as:
knowledge_base/
├── account.md
├── billing.md
├── refunds.md
└── technical.md
The agent maps the predicted support category to the corresponding Markdown file.
This is intentionally a lightweight implementation because the primary focus of the project is LLM observability, not information retrieval.
Design Decisions
Why Langfuse?
LLM applications can be difficult to debug because a single user request may involve multiple model calls and application steps.
Langfuse provides visibility into those operations by connecting them into traces and observations.
This project uses Langfuse to investigate:
Request-level latency
Individual operation latency
LLM token usage
Agent execution flow
Failed requests
Errors within the pipeline
Why a Proof of Concept?
The purpose of this project is to test telemetry on a small and controlled workflow before applying the same approach to a larger application.
The support agent provides enough complexity to demonstrate:
API Request
     ↓
Agent
     ↓
LLM Call
     ↓
Knowledge Retrieval
     ↓
LLM Call
     ↓
Response
while remaining simple enough to inspect and debug.
Current Limitations
This project is intentionally a proof of concept and has several limitations:
Knowledge retrieval uses a category-to-file mapping rather than semantic search.
There is no vector database or RAG pipeline.
The application is not designed as a production customer support system.
Authentication and persistent user storage are not implemented.
Telemetry experiments use live API calls.
The current implementation focuses primarily on observability rather than deployment and scalability.
Future Improvements
Potential extensions include:
Replace file-based retrieval with vector search
Add a RAG pipeline
Track additional application metadata
Add user/session identifiers to traces
Add evaluation scores for generated responses
Compare model latency and token costs
Build telemetry dashboards
Add production error monitoring
Expand Langfuse instrumentation to additional workflows
Add automated evaluation of response quality
Key Takeaway
This project demonstrates a practical approach to adding LLM observability to an existing AI workflow.
The proof of concept validates that Langfuse can provide visibility into:
Traces
   ↓
Latency
   ↓
Token Usage
   ↓
Errors
across an end-to-end LLM pipeline.
The resulting telemetry can then be used to understand system performance, identify failures, monitor LLM usage, and determine where observability should be expanded in a larger production application.
License
This project is licensed under the MIT License.
See the LICENSE file for details.

