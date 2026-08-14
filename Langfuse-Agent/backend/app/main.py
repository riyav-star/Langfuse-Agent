from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.agent.graph import run_support_agent
from app.models.schemas import (
    SupportRequest,
    SupportResponse,
)
from app.telemetry.langfuse import langfuse, get_trace_url


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

    # Make sure pending Langfuse events are sent
    langfuse.flush()


app = FastAPI(
    title="Langfuse Agent",
    description="AI support agent with Langfuse observability",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
def root():
    return {
        "message": "Langfuse Agent API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post(
    "/support",
    response_model=SupportResponse,
)
def support(request: SupportRequest):

    try:

        # Special test case for telemetry experiments
        if request.message == "TEST_ERROR":
            raise RuntimeError(
                "Simulated agent failure for telemetry testing"
            )

        result = run_support_agent(
            message=request.message,
            user_id=request.user_id,
        )

        return result

    except Exception as error:

        print(f"Agent error: {error}")

        raise HTTPException(
            status_code=500,
            detail="The support agent encountered an error.",
        )