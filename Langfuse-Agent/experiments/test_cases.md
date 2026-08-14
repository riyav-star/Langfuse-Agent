# Langfuse Telemetry Test Cases

## Objective

Evaluate whether Langfuse successfully captures useful telemetry from the AI support agent.

The main metrics being evaluated are:

- Traces
- Latency
- Token usage
- Errors
- Agent workflow observations

---

## Test 1: Normal Support Request

### Input

"I was charged twice for my subscription."

### Expected Behavior

- Agent classifies the request as billing.
- Agent assigns an appropriate priority.
- Agent retrieves billing information.
- Agent generates a support response.
- Langfuse records a successful trace.

### Telemetry to Verify

- [ ] Trace created
- [ ] Agent observation recorded
- [ ] Classification LLM call recorded
- [ ] Knowledge-base operation recorded
- [ ] Response-generation LLM call recorded
- [ ] Input tokens recorded
- [ ] Output tokens recorded
- [ ] Latency recorded
- [ ] No errors recorded

---

## Test 2: Account Support Request

### Input

"I can't log into my account because I forgot my password."

### Expected Behavior

- Agent classifies the request as account.
- Agent retrieves account information.
- Agent generates a response.
- Langfuse records a successful trace.

### Telemetry to Verify

- [ ] Trace created
- [ ] Token usage recorded
- [ ] Latency recorded
- [ ] Model information recorded
- [ ] No errors recorded

---

## Test 3: Technical Support Request

### Input

"The application keeps showing an error when I try to upload a file."

### Expected Behavior

- Agent classifies the request as technical.
- Agent retrieves technical support information.
- Agent generates a response.

### Telemetry to Verify

- [ ] Trace created
- [ ] Token usage recorded
- [ ] Latency recorded
- [ ] Knowledge-base operation recorded
- [ ] Response-generation operation recorded

---

## Test 4: Complex Request

### Input

"I was charged twice for my subscription, I can't log into my account,
and I'm also getting an error when trying to reset my password."

### Expected Behavior

The agent should process a more complex request and generate a
useful response.

### Telemetry to Verify

- [ ] Trace created
- [ ] Latency recorded
- [ ] Token usage recorded
- [ ] Agent workflow recorded
- [ ] Response-generation latency recorded

### Comparison

Compare this request with Test 1 to determine whether more complex
requests result in:

- Higher latency
- Higher token usage
- Different agent behavior

---

## Test 5: Simulated Agent Error

### Input

"TEST_ERROR"

### Expected Behavior

The application intentionally raises an error.

### Telemetry to Verify

- [ ] Error occurs
- [ ] Failed request is visible
- [ ] Error information is captured
- [ ] Failed trace can be identified
- [ ] Error can be investigated from the trace

---

## Test 6: Repeated Requests

Run multiple support requests using different categories.

### Goal

Collect enough traces to identify patterns in:

- Average latency
- High-latency requests
- Token usage
- Error rate
- Frequently used operations

### Telemetry to Verify

- [ ] Multiple traces created
- [ ] Each trace is identifiable
- [ ] Token usage is available
- [ ] Latency is available
- [ ] Errors are distinguishable from successful requests