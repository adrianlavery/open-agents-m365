from pydantic import BaseModel, Field


class InvokeRequest(BaseModel):
    prompt: str
    session_id: str | None = None


class InvokeResponse(BaseModel):
    agent_name: str
    response: str
    session_id: str


class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    scope: str
