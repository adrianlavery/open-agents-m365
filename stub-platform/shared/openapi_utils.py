"""
OpenAPI enrichment helper shared by all stub agents.

Adds BearerAuth security scheme and request/response examples to the
auto-generated OpenAPI spec, per contracts/agent-invoke.md.
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def enrich_openapi(app: FastAPI, agent_name: str, port: int) -> None:
    """
    Attach a custom openapi() method to the FastAPI app that enriches the
    auto-generated schema with:
      - BearerAuth (JWT) security scheme
      - Security requirement on /invoke
      - Request and response examples matching contracts/agent-invoke.md
    """

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
            servers=[
                {
                    "url": f"http://localhost:{port}",
                    "description": "Local development",
                }
            ],
        )

        # Add BearerAuth security scheme
        schema.setdefault("components", {})
        schema["components"].setdefault("securitySchemes", {})
        schema["components"]["securitySchemes"]["BearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": (
                "RS256-signed JWT issued by the auth stub (or any OIDC-compliant IdP). "
                "Required scope: agents.invoke"
            ),
        }

        # Apply security + examples to /invoke POST
        invoke_op = (
            schema.get("paths", {})
            .get("/invoke", {})
            .get("post", {})
        )
        if invoke_op:
            invoke_op["security"] = [{"BearerAuth": ["agents.invoke"]}]

            # Request body example
            req_content = invoke_op.get("requestBody", {}).get("content", {})
            if "application/json" in req_content:
                req_content["application/json"]["example"] = {
                    "prompt": f"Create a summer campaign for a beverage brand targeting Gen Z.",
                    "session_id": "550e8400-e29b-41d4-a716-446655440000",
                }

            # Response examples
            resp_200 = invoke_op.get("responses", {}).get("200", {})
            resp_content = resp_200.get("content", {})
            if "application/json" in resp_content:
                resp_content["application/json"]["example"] = {
                    "agent_name": agent_name,
                    "response": "Campaign Concept: 'Refresh Your World'\n\nTarget Audience: Gen Z (18–26)...",
                    "session_id": "550e8400-e29b-41d4-a716-446655440000",
                }

            # Add 401 response documentation
            invoke_op.setdefault("responses", {})["401"] = {
                "description": "Missing, expired, or invalid JWT.",
                "content": {
                    "application/json": {
                        "examples": {
                            "missing": {"value": {"detail": "Missing bearer token"}},
                            "expired": {"value": {"detail": "Token has expired"}},
                            "invalid": {"value": {"detail": "Token signature verification failed"}},
                        }
                    }
                },
            }

        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi
