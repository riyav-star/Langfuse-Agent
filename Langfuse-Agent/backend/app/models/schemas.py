from pydantic import BaseModel, Field


class SupportRequest(BaseModel):
    message: str = Field(..., min_length=1)
    user_id: str = "test-user"


class Classification(BaseModel):
    category: str
    priority: str


class SupportResponse(BaseModel):
    category: str
    priority: str
    response: str
    source: str