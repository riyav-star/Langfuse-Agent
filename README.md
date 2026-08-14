# Langfuse-Agent

An AI support agent proof of concept built to evaluate **Langfuse observability for LLM applications**.

The project instruments a small end-to-end AI workflow to determine whether Langfuse can reliably capture useful telemetry, including **traces, latency, token usage, and errors**. The collected telemetry is analyzed to identify observability gaps and determine how telemetry could be expanded across larger production workflows.

---

## Project Overview

This project simulates a customer support workflow powered by an LLM.

A user submits a support request. The agent:

1. Classifies the support request
2. Determines the category and priority
3. Retrieves a relevant knowledge-base article
4. Generates a support response
5. Records telemetry for the workflow using Langfuse

The purpose of the project is to evaluate the usefulness of LLM observability before applying similar telemetry instrumentation to production workflows.

### Evaluation Goals

The project evaluates four primary telemetry areas:

- **Traces** — Can the complete agent workflow be observed?
- **Latency** — Which parts of the workflow take the most time?
- **Token usage** — How many input and output tokens are consumed?
- **Errors** — Are application and LLM-related failures visible and traceable?

The experiment results are documented in `experiments/results.md`.

---

# Architecture

```text
                         POST /support
                              │
                              ▼
                    ┌───────────────────┐
                    │ run_support_agent │
                    └─────────┬─────────┘
                              │
              ┌───────────────┼────────────────┐
              │               │                │
              ▼               ▼                ▼
     ┌────────────────┐ ┌──────────────┐ ┌────────────────────┐
     │ classify_ticket│ │ retrieve_    │ │ generate_response  │
     │                │ │ information  │ │                    │
     └───────┬────────┘ └──────┬───────┘ └─────────┬──────────┘
             │                 │                   │
             ▼                 ▼                   ▼
        ┌─────────┐      ┌─────────────┐      ┌─────────┐
        │ call_llm│      │ Knowledge   │      │ call_llm│
        │         │      │ Base        │      │         │
        └─────────┘      └─────────────┘      └─────────┘
             │                                      │
             └────────────────┬─────────────────────┘
                              ▼
                         Langfuse
                       Observability
Each major stage is instrumented using Langfuse's @observe decorator.
A typical request produces a hierarchical trace:
run_support_agent
│
├── classify_ticket
│   └── call_llm
│
├── retrieve_information
│
└── generate_response
    └── call_llm
Each request produces one trace containing six observations:
Top-level agent span
Classification chain
Classification LLM generation
Knowledge-base tool span
Response-generation chain
Response-generation LLM generation
This structure makes it possible to inspect both the complete workflow and individual operations.
Telemetry
1. Traces
Each support request is represented as a Langfuse trace.
Traces provide visibility into:
Complete agent execution
Individual pipeline stages
LLM calls
Inputs and outputs
Execution timing
Errors
Metadata
This allows the workflow to be investigated as a single request rather than as isolated LLM calls.
2. Latency
The project measures latency at multiple levels.
Examples include:
Total request latency
Agent execution latency
Ticket classification latency
Knowledge-base retrieval latency
Response-generation latency
Individual LLM call latency
The goal is to determine which parts of the workflow contribute most to overall response time.
3. Token Usage
LLM generations are monitored for:
Input tokens
Output tokens
Total tokens
Token usage can be compared between different support scenarios to identify:
High-token operations
Large prompts
Large responses
Potential optimization opportunities
Potential cost considerations
4. Error Tracking
The project includes a deliberate error scenario using:
TEST_ERROR
This allows the experiment to determine whether failures are visible through Langfuse.
The error experiment evaluates:
Whether the failed request creates a trace
Whether the trace records an error
Where the failure occurs
Whether errors outside LLM calls are captured
Whether additional application-level instrumentation is needed

Project Structure
Langfuse-Agent/
│
├── backend/
│   │
│   ├── app/
│   │   │
│   │   ├── main.py
│   │   │   └── FastAPI application and API endpoints
│   │   │
│   │   ├── agent/
│   │   │   ├── graph.py
│   │   │   │   └── Agent workflow and pipeline orchestration
│   │   │   │
│   │   │   ├── nodes.py
│   │   │   │   └── Classification, retrieval, and response generation
│   │   │   │
│   │   │   └── prompts.py
│   │   │       └── LLM system prompts
│   │   │
│   │   ├── models/
│   │   │   └── schemas.py
│   │   │       └── Pydantic request and response models
│   │   │
│   │   ├── services/
│   │   │   ├── llm.py
│   │   │   │   └── OpenAI wrapper and Langfuse generation
│   │   │   │
│   │   │   └── knowledge_base.py
│   │   │       └── Knowledge-base retrieval
│   │   │
│   │   └── telemetry/
│   │       └── langfuse.py
│   │           └── Langfuse client and trace utilities
│   │
│   ├── scripts/
│   │   └── run_experiments.py
│   │       └── Runs telemetry experiments and collects results
│   │
│   ├── tests/
│   │   ├── test_agent.py
│   │   │   └── Agent logic tests
│   │   │
│   │   └── test_telemetry.py
│   │       └── Langfuse instrumentation tests
│   │
│   ├── requirements.txt
│   ├── .env
│   └── .env.example
│
├── knowledge_base/
│   ├── account.md
│   ├── billing.md
│   ├── refunds.md
│   └── technical.md
│
└── experiments/
    ├── test_cases.md
    └── results.md

Tech Stack
Technology	Purpose
Python	Backend and agent logic
FastAPI	REST API
OpenAI API	LLM inference
Langfuse	LLM observability and telemetry
Pydantic	Request and response validation
pytest	Automated testing
python-dotenv	Environment configuration

Setup
Prerequisites
Before running the project, install:
Python 3.9+
Git
OpenAI API key
Langfuse account
Langfuse project
1. Clone the Repository
git clone <your-repository-url>
cd Langfuse-Agent

2. Create a Virtual Environment
Navigate to the backend:
cd backend
Create the virtual environment:
python3 -m venv venv
Activate it:
macOS / Linux
source venv/bin/activate
Windows
venv\Scripts\activate
After activation, your terminal should look similar to:
(venv) user@computer backend %
3. Install Dependencies
pip install -r requirements.txt
4. Configure Environment Variables
Copy the example environment file:
cp .env.example .env
Open .env and add your API credentials:
OPENAI_API_KEY=sk-...

LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com

LANGFUSE_TRACING_ENVIRONMENT=development

Security
Never commit your .env file.
Your .gitignore should contain:
.env
venv/
__pycache__/
*.pyc
.pytest_cache/
API keys should only be stored in environment variables.
Running the API
From the backend directory with the virtual environment activated:
uvicorn app.main:app --port 8000
The API will start at:
http://localhost:8000
You should see:
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
Keep this terminal running while testing the application.

API Endpoints
Endpoint	Method	Description
/	GET	Application liveness check
/health	GET	Health check
/support	POST	Runs the AI support agent
Health Check
Open a second terminal and activate the virtual environment:
cd ~/Documents/GitHub/Langfuse-Agent/backend
source venv/bin/activate
Then run:
curl http://localhost:8000/health
Expected response:
{
  "status": "healthy"
}
Running the Support Agent
Send a support request:
curl -X POST http://localhost:8000/support \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I was charged twice for my subscription.",
    "user_id": "user-1"
  }'
The request passes through:
Request
   ↓
Classification
   ↓
Knowledge Base Retrieval
   ↓
Response Generation
   ↓
Final Response
At the same time, Langfuse records the telemetry associated with the workflow.
Testing Error Handling
The application contains a deliberate error scenario.
Send:
curl -X POST http://localhost:8000/support \
  -H "Content-Type: application/json" \
  -d '{
    "message": "TEST_ERROR",
    "user_id": "error-test-user"
  }'
The endpoint should return an error response.
This scenario is used to determine whether the error is visible in Langfuse and whether the trace provides enough context to identify where the failure occurred.
Running Automated Tests
The project includes automated tests for the agent and telemetry instrumentation.
From the backend directory:
pytest tests/ -v
The tests mock external services, including OpenAI and Langfuse, so they do not require:
OpenAI API credits
Langfuse API access
Network access
The test suite covers:
Ticket classification
Classification parsing
Knowledge-base routing
Knowledge-base fallback behavior
Full agent pipeline execution
/support endpoint behavior
Error handling
Langfuse @observe instrumentation
Trace URL generation
These tests validate the application's logic and instrumentation wiring.
They do not prove that telemetry is successfully appearing in the Langfuse dashboard.
For that, real telemetry experiments are required.
Running Telemetry Experiments
The project includes a controlled experiment suite in:
experiments/test_cases.md
The experiment contains six scenarios:
Test	Scenario	Purpose
1	Billing request	Baseline LLM workflow
2	Account request	Compare another category
3	Technical request	Compare technical workflow
4	Multi-issue request	Evaluate a more complex input
5	Simulated error	Evaluate error observability
6	Repeated requests	Build a larger telemetry sample
The experiment script sends real requests to the application and retrieves the resulting telemetry.
Run the Experiment
Make sure the API server is running in one terminal.
Open a second terminal:
cd ~/Documents/GitHub/Langfuse-Agent/backend
source venv/bin/activate
Then run:
python scripts/run_experiments.py
The script will:
Send the test cases to /support
Execute the agent using the real OpenAI API
Generate Langfuse traces
Retrieve the resulting traces
Measure request latency
Collect token usage
Inspect individual observations
Evaluate the error scenario
Write the results to experiments/results.md
Warning: This experiment uses real OpenAI and Langfuse endpoints and may incur API usage costs.
Viewing Telemetry in Langfuse
After running the experiments, open your Langfuse project and navigate to the Traces section.
For a successful request, inspect:
Trace
Trace ID
Trace name
Status
Total latency
Input
Output
Classification
Classification latency
Input tokens
Output tokens
Total tokens
Model information
Knowledge Base
Retrieval latency
Selected category
Retrieved document
Response Generation
Generation latency
Input tokens
Output tokens
Total tokens
Model information
Error Case
Inspect whether:
A trace was created
The trace contains an error
The error is associated with the correct operation
The failure occurred before or during an LLM call
Experiment Results
Results are stored in:
experiments/results.md
The results document records information such as:
Test Case
Trace ID
Trace URL
Request Latency
Classification Latency
Retrieval Latency
Response Generation Latency
Input Tokens
Output Tokens
Total Tokens
Error Status
The goal is to use these measurements to identify patterns rather than simply confirming that telemetry exists.

Analysis
The experiment is designed to answer several questions.
Trace Coverage
Does every successful request produce a trace?
Are all important pipeline stages visible?
Are nested LLM calls represented correctly?
Are failed requests represented?
Latency
Which operation is the slowest?
How much of the total latency comes from LLM calls?
Is retrieval contributing meaningful latency?
Are there unexpected performance bottlenecks?
Token Usage
Which LLM operation consumes the most tokens?
Do complex requests use more tokens?
Are prompts larger than necessary?
Are there opportunities to reduce token usage?
Error Observability
Are application errors captured?
Are LLM errors captured?
Are errors associated with the correct trace?
Are failures occurring inside or outside instrumented operations?
Telemetry Expansion Recommendations
The purpose of the experiment is to use actual telemetry results to determine how observability should be expanded.
The evaluation follows:
Implement
    ↓
Run controlled experiments
    ↓
Collect telemetry
    ↓
Analyze results
    ↓
Identify observability gaps
    ↓
Recommend expansion
Potential expansion areas include:
Current Proof of Concept
        │
        ▼
Additional LLM Workflows
        │
        ├── Agent workflows
        ├── API boundaries
        ├── Tool execution
        ├── Error handling
        ├── Token/cost monitoring
        └── Performance monitoring
Recommendations should be based on the experiment results.
For example:
If LLM calls dominate latency
Prioritize LLM generation instrumentation across additional workflows.
If token usage varies significantly
Expand token and cost monitoring to workflows with higher usage.
If application-level errors are missing
Add explicit error instrumentation around API and workflow boundaries.
If certain agent operations are difficult to debug
Add additional spans and metadata around those operations.
Knowledge Base
The project intentionally uses a simple file-based knowledge base rather than vector search.
Supported categories:
billing
account
technical
refund
Knowledge-base files:
knowledge_base/
├── account.md
├── billing.md
├── refunds.md
└── technical.md
The category returned by the classifier determines which document is retrieved.
Unsupported categories fall back to:
technical.md
This keeps the project focused on observability rather than retrieval infrastructure.
LLM Configuration
The agent currently uses:
Model: gpt-4o-mini
Temperature: 0.2
The OpenAI client and Langfuse generation instrumentation are implemented in:
backend/app/services/llm.py
The model can be changed there if needed.
Why This Project
Adding observability to an LLM application is not only about collecting data.
The telemetry needs to answer practical engineering questions:
What is slow?
What is expensive?
What is failing?
Where is the failure occurring?
Which workflows need additional instrumentation?
Is the telemetry detailed enough to debug production issues?
This project uses a small controlled AI workflow to answer those questions before applying similar instrumentation to larger application workflows.
Key Takeaway
This project demonstrates a practical approach to evaluating LLM observability:
                ┌──────────────────┐
                │  Instrument App  │
                └────────┬─────────┘
                         ↓
                ┌──────────────────┐
                │ Run Experiments  │
                └────────┬─────────┘
                         ↓
                ┌──────────────────┐
                │ Collect Telemetry│
                └────────┬─────────┘
                         ↓
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
       Traces         Latency        Tokens
          │              │              │
          └──────────────┼──────────────┘
                         ↓
                  Error Analysis
                         ↓
                Identify Gaps
                         ↓
             Recommend Expansion
The objective is to evaluate Langfuse using measurable results, identify observability gaps, and determine how telemetry can be expanded across additional LLM and application workflows.
Future Improvements
Potential future improvements include:
Add application-level error instrumentation
Add production environment tracing
Add user and session metadata
Add LLM cost tracking
Add evaluation scores
Add custom Langfuse dashboards
Add automated telemetry regression tests
Expand instrumentation to additional application workflows
Replace file-based retrieval with vector search
Add retrieval quality metrics
Compare latency and token usage across different models
Add alerting for latency and error thresholds
Security
Never commit secrets to the repository.
The following files and directories should remain ignored:
.env
venv/
__pycache__/
.pytest_cache/
*.pyc
Use .env.example to document required environment variables without exposing real credentials.
License
This project is a proof of concept for evaluating LLM observability and telemetry using Langfuse.
