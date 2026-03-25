# API Contract: Agent Invoke Endpoint

**Feature**: `001-stub-agent-platform`
**Version**: `1.0.0`
**Applies to**: Creative Agent, Media Agent, Analytics Agent

---

## OpenAPI 3.0 Specification (shared across all three agents)

```yaml
openapi: "3.0.3"
info:
  title: "{Agent Name} Stub"
  description: >
    Local stub service simulating a client AI agent. Accepts a prompt and
    returns a mock domain-specific response. Requires Bearer token (JWT)
    issued by the local auth stub or a compatible OIDC-compliant IdP.
  version: "1.0.0"

servers:
  - url: "http://localhost:{port}"
    description: "Local development"
    variables:
      port:
        default: "8001"
        description: "Per-agent port: 8001 (creative), 8002 (media), 8003 (analytics)"

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: >
        RS256-signed JWT issued by the auth stub (or any compatible OIDC IdP).
        Must include claims: sub, iss, aud, exp, scope.
        Required scope: agents.invoke

  schemas:
    InvokeRequest:
      type: object
      required:
        - prompt
      properties:
        prompt:
          type: string
          description: "The instruction or question to send to the agent."
          example: "Create a summer campaign for a beverage brand targeting Gen Z."
        session_id:
          type: string
          description: >
            Optional session identifier. If omitted, the agent generates a new UUID v4.
            Echoed back in the response.
          example: "550e8400-e29b-41d4-a716-446655440000"

    InvokeResponse:
      type: object
      required:
        - agent_name
        - response
        - session_id
      properties:
        agent_name:
          type: string
          description: "Identifies which agent handled the request."
          enum:
            - creative-agent
            - media-agent
            - analytics-agent
          example: "creative-agent"
        response:
          type: string
          description: "Mock domain-specific text response from the agent."
          example: "Campaign concept: 'Refresh Your World' — a summer campaign..."
        session_id:
          type: string
          description: "Session identifier (echoed from request or newly generated)."
          example: "550e8400-e29b-41d4-a716-446655440000"

    HealthResponse:
      type: object
      required:
        - status
        - service
      properties:
        status:
          type: string
          enum: [healthy]
        service:
          type: string
          example: "creative-agent"

    ErrorResponse:
      type: object
      properties:
        detail:
          type: string
          description: "Human-readable error description."

security:
  - BearerAuth: []

paths:
  /invoke:
    post:
      summary: "Invoke the agent with a prompt"
      operationId: "invokeAgent"
      description: >
        Submit a prompt to the agent and receive a mock response. Requires a valid
        Bearer JWT in the Authorization header. The JWT must not be expired and must
        have been signed by the configured issuer.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/InvokeRequest"
            example:
              prompt: "Create a summer campaign for a beverage brand."
              session_id: "550e8400-e29b-41d4-a716-446655440000"
      responses:
        "200":
          description: "Successful invocation."
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/InvokeResponse"
              example:
                agent_name: "creative-agent"
                response: "Campaign concept: 'Refresh Your World'..."
                session_id: "550e8400-e29b-41d4-a716-446655440000"
        "401":
          description: "Missing, expired, or invalid JWT."
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ErrorResponse"
              examples:
                missing:
                  value: { "detail": "Missing bearer token" }
                expired:
                  value: { "detail": "Token has expired" }
                invalid:
                  value: { "detail": "Token signature verification failed" }
        "422":
          description: "Request body validation error (e.g., missing prompt field)."
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ErrorResponse"

  /health:
    get:
      summary: "Health check"
      operationId: "healthCheck"
      description: "Returns HTTP 200 when the service is healthy. No auth required."
      security: []
      responses:
        "200":
          description: "Service is healthy."
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/HealthResponse"
              example:
                status: "healthy"
                service: "creative-agent"
```

---

## Per-Agent Differentiation

The spec above is identical across all three agents except:

| Field                    | Creative Agent     | Media Agent     | Analytics Agent     |
|--------------------------|-------------------|-----------------|---------------------|
| `info.title`             | Creative Agent Stub | Media Agent Stub | Analytics Agent Stub |
| `servers[0].variables.port.default` | `8001` | `8002` | `8003` |
| `InvokeResponse.agent_name` enum | `creative-agent` | `media-agent` | `analytics-agent` |

---

## Example curl: Invoke Creative Agent

```bash
# 1. Obtain a token from the auth stub
TOKEN=$(curl -s -X POST http://localhost:8000/token \
  -d "grant_type=client_credentials" \
  -d "client_id=demo-client" \
  -d "client_secret=demo-secret" \
  -d "scope=agents.invoke" \
  | jq -r '.access_token')

# 2. Invoke the creative agent
curl -s -X POST http://localhost:8001/invoke \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a summer campaign for a beverage brand targeting Gen Z."}'
```

**Expected response**:
```json
{
  "agent_name": "creative-agent",
  "response": "Campaign Concept: 'Refresh Your World'\n\nTarget Audience: Gen Z (18–26)...",
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```
