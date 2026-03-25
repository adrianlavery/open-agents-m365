"""
Creative Agent Stub — simulates a client creative AI agent on AWS/GCP.

Endpoints:
  POST /invoke   Accept a prompt, return a mock creative campaign response (auth required)
  GET  /health   Health check (no auth)

Environment variables:
  AGENT_NAME             Value returned in agent_name field.   Default: creative-agent
  AGENT_PUBLIC_KEY_PATH  Path to RSA public key PEM.           Default: /keys/public.pem
  AGENT_JWKS_URI         If set, use JWKS URI for key lookup.
  OIDC_ISSUER            Expected JWT iss claim.               Default: http://localhost:8000
  JWT_AUDIENCE           Expected JWT aud claim.               Default: agents
  PORT                   Port to bind.                         Default: 8001
"""

import os
import sys
import uuid

from fastapi import Depends, FastAPI

# Allow importing shared package when running without Docker (python path)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from shared.auth_middleware import verify_jwt_token
from shared.models import HealthResponse, InvokeRequest, InvokeResponse
from shared.openapi_utils import enrich_openapi
from . import responses  # noqa: E402 — relative import for package mode


AGENT_NAME = os.environ.get("AGENT_NAME", "creative-agent")
_PORT = int(os.environ.get("PORT", "8001"))

app = FastAPI(
    title="Creative Agent Stub",
    description=(
        "Local stub simulating a client creative AI agent. "
        "Returns mock creative campaign responses. Requires Bearer JWT auth."
    ),
    version="1.0.0",
    openapi_url="/openapi.json",
)

enrich_openapi(app, agent_name=AGENT_NAME, port=_PORT)


@app.get("/health", tags=["ops"])
def health() -> HealthResponse:
    return HealthResponse(service=AGENT_NAME)


@app.post("/invoke", tags=["agent"])
def invoke(
    body: InvokeRequest,
    _token: dict = Depends(verify_jwt_token),
) -> InvokeResponse:
    session_id = body.session_id or str(uuid.uuid4())
    mock_response = responses.build_response(body.prompt)
    return InvokeResponse(
        agent_name=AGENT_NAME,
        response=mock_response,
        session_id=session_id,
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8001"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
