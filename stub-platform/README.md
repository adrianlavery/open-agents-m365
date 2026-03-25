# Open Agents M365 — Local Stub Platform

A local Python-based stub platform that simulates the client's AWS/GCP agent infrastructure
for local development and workshop demos.

Four independent FastAPI services run together via Docker Compose, exposing a consistent
`POST /invoke` REST API with OpenAPI 3.0 specs and OAuth2/OIDC JWT authentication.

The auth layer is **IdP-swappable via configuration only** — when you're ready to connect
to a real identity provider (Entra ID, Okta), you change environment variables, not code.

---

## Services

| Service         | Port | URL                                          |
|----------------|------|----------------------------------------------|
| Auth Stub       | 8000 | http://localhost:8000                        |
| Creative Agent  | 8001 | http://localhost:8001                        |
| Media Agent     | 8002 | http://localhost:8002                        |
| Analytics Agent | 8003 | http://localhost:8003                        |

---

## Prerequisites

**Option A — Docker (recommended)**
- Docker Desktop 4.x+ or Docker Engine 24.x+ with Compose plugin
- `curl` and `jq` (for example commands)
- `openssl` (for key generation — one-time setup)

**Option B — Python (no Docker)**
- Python 3.11+, `pip`, `openssl`, `curl`, `jq`

---

## Setup: Generate RSA Key Pair (one-time)

Run from this directory (`stub-platform/`):

```bash
mkdir -p keys
openssl genrsa -out keys/private.pem 2048
openssl rsa -in keys/private.pem -pubout -out keys/public.pem
```

> Keys are gitignored. Generate once and they persist across restarts.

---

## Option A: Docker Compose (Recommended)

### Start all services

```bash
docker compose up --build
```

All four services start in ~20–30 seconds. Health checks pass when services are ready.

### Stop all services

```bash
docker compose down
```

---

## Option B: Python Without Docker

### Set up virtual environment

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Start each service in a separate terminal

```bash
# Terminal 1 — Auth Stub
uvicorn auth.main:app --port 8000

# Terminal 2 — Creative Agent
AGENT_PUBLIC_KEY_PATH=keys/public.pem \
OIDC_ISSUER=http://localhost:8000 \
uvicorn agents.creative.main:app --port 8001

# Terminal 3 — Media Agent
AGENT_PUBLIC_KEY_PATH=keys/public.pem \
OIDC_ISSUER=http://localhost:8000 \
uvicorn agents.media.main:app --port 8002

# Terminal 4 — Analytics Agent
AGENT_PUBLIC_KEY_PATH=keys/public.pem \
OIDC_ISSUER=http://localhost:8000 \
uvicorn agents.analytics.main:app --port 8003
```

> **Note**: For the auth stub, set `PRIVATE_KEY_PATH=keys/private.pem PUBLIC_KEY_PATH=keys/public.pem` if the defaults (`/keys/*.pem`) don't match your local path.

---

## Verify Health Checks

```bash
curl http://localhost:8000/health   # {"status":"healthy","service":"auth-stub"}
curl http://localhost:8001/health   # {"status":"healthy","service":"creative-agent"}
curl http://localhost:8002/health   # {"status":"healthy","service":"media-agent"}
curl http://localhost:8003/health   # {"status":"healthy","service":"analytics-agent"}
```

---

## Core Workflow: Get a Token and Invoke an Agent

### Step 1 — Obtain a JWT

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/token \
  -d "grant_type=client_credentials" \
  -d "client_id=demo-client" \
  -d "client_secret=demo-secret" \
  -d "scope=agents.invoke" \
  | jq -r '.access_token')

echo "Token: ${TOKEN:0:60}..."
```

### Step 2 — Invoke the Creative Agent

```bash
curl -s -X POST http://localhost:8001/invoke \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a summer campaign for a beverage brand targeting Gen Z."}' \
  | jq .
```

**Expected response:**
```json
{
  "agent_name": "creative-agent",
  "response": "Creative Campaign Brief — Summer Campaign\n\n...",
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### Step 3 — Invoke the Media Agent

```bash
curl -s -X POST http://localhost:8002/invoke \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Plan a media campaign for Q3 with a £500k budget."}' \
  | jq .
```

### Step 4 — Invoke the Analytics Agent

```bash
curl -s -X POST http://localhost:8003/invoke \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What are the top performing channels this quarter?"}' \
  | jq .
```

---

## Test Auth Rejection

```bash
# No token → expect HTTP 401
curl -s -o /dev/null -w "%{http_code}" \
  -X POST http://localhost:8001/invoke \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'
# Output: 401

# Malformed token → expect HTTP 401
curl -s -o /dev/null -w "%{http_code}" \
  -X POST http://localhost:8001/invoke \
  -H "Authorization: Bearer not-a-real-token" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'
# Output: 401
```

---

## Session ID Continuity

Pass a `session_id` to track a conversation across calls (echoed back in every response):

```bash
curl -s -X POST http://localhost:8001/invoke \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Continue the brief.", "session_id": "my-session-123"}' \
  | jq .session_id
# "my-session-123"
```

---

## Inspect OpenAPI Specs

Each agent serves a complete OpenAPI 3.0 spec with BearerAuth security scheme and examples:

```bash
# Get the spec as JSON
curl -s http://localhost:8001/openapi.json | jq .

# Open interactive Swagger UI in browser
open http://localhost:8001/docs

# Verify all three specs are accessible
curl -s http://localhost:8001/openapi.json | jq '.info.title'   # "Creative Agent Stub"
curl -s http://localhost:8002/openapi.json | jq '.info.title'   # "Media Agent Stub"
curl -s http://localhost:8003/openapi.json | jq '.info.title'   # "Analytics Agent Stub"
```

---

## Inspect Auth Stub (OIDC + JWKS)

```bash
# OIDC discovery document
curl -s http://localhost:8000/.well-known/openid-configuration | jq .

# JSON Web Key Set (public key used to verify tokens)
curl -s http://localhost:8000/.well-known/jwks.json | jq .
```

---

## Pre-registered Dev Clients

| `client_id`    | `client_secret` | Allowed scopes                          |
|---------------|-----------------|------------------------------------------|
| `demo-client`  | `demo-secret`   | `agents.invoke`                          |
| `m365-plugin`  | `plugin-secret` | `agents.invoke openid profile`           |

---

## Swapping to a Real Identity Provider

When you're ready to replace this auth stub with Entra ID, Okta, or another OIDC IdP,
**only change environment variables on the agent services** — no code changes required:

| Env Var               | Local Dev                    | Entra ID example                                                      |
|-----------------------|------------------------------|-----------------------------------------------------------------------|
| `OIDC_ISSUER`         | `http://localhost:8000`      | `https://login.microsoftonline.com/{tenant-id}/v2.0`                 |
| `AGENT_JWKS_URI`      | *(unset — uses PEM file)*    | `https://login.microsoftonline.com/{tenant-id}/discovery/v2.0/keys`  |
| `AGENT_PUBLIC_KEY_PATH` | `keys/public.pem`          | *(unset — use AGENT_JWKS_URI instead)*                               |
| `JWT_AUDIENCE`        | `agents`                     | `api://{your-app-registration-client-id}`                            |

---

## Environment Variables Reference

### Auth Stub

| Variable               | Default                    | Description                        |
|-----------------------|----------------------------|------------------------------------|
| `PRIVATE_KEY_PATH`    | `/keys/private.pem`        | RSA private key for signing JWTs   |
| `PUBLIC_KEY_PATH`     | `/keys/public.pem`         | RSA public key for JWKS endpoint   |
| `ISSUER`              | `http://localhost:8000`    | JWT `iss` claim                    |
| `AUDIENCE`            | `agents`                   | JWT `aud` claim                    |
| `TOKEN_EXPIRY_SECONDS`| `3600`                     | Token validity in seconds          |
| `PORT`                | `8000`                     | Port to bind                       |

### Agent Services

| Variable                | Default                    | Description                                     |
|------------------------|----------------------------|-------------------------------------------------|
| `AGENT_NAME`           | `creative-agent` etc.      | Returned in `agent_name` response field         |
| `AGENT_PUBLIC_KEY_PATH`| `/keys/public.pem`         | RSA public key PEM (static validation mode)     |
| `AGENT_JWKS_URI`       | *(unset)*                  | JWKS URI (dynamic key fetch — for real IdPs)    |
| `OIDC_ISSUER`          | `http://localhost:8000`    | Expected JWT `iss` claim                        |
| `JWT_AUDIENCE`         | `agents`                   | Expected JWT `aud` claim                        |
| `JWT_ALGORITHM`        | `RS256`                    | JWT signing algorithm                           |
| `PORT`                 | `8001` / `8002` / `8003`   | Port to bind                                    |

---

## Project Structure

```
stub-platform/
├── shared/                    # Shared package: Pydantic models, JWT auth middleware
│   ├── models.py
│   ├── auth_middleware.py
│   └── openapi_utils.py
├── auth/                      # Auth stub (port 8000)
│   ├── main.py
│   └── clients.py
├── agents/
│   ├── creative/              # Creative Agent (port 8001)
│   ├── media/                 # Media Agent (port 8002)
│   └── analytics/             # Analytics Agent (port 8003)
├── keys/                      # Dev RSA key pair (gitignored)
├── docker-compose.yml
└── requirements.txt
```

---

## Next Step

Once this stub platform is running, the next feature is **Pattern A: API Plugin** — wrapping
these agents as M365 Copilot API Plugins using Azure APIM and a Declarative Agent manifest.
