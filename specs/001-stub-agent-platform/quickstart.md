# Quickstart: Local Stub Agent Platform

**Feature**: `001-stub-agent-platform`
**Date**: 2026-03-25

Get the full local agent platform running in under 5 minutes.

---

## Prerequisites

**Option A — Docker (recommended)**:
- Docker Desktop 4.x+ or Docker Engine 24.x+ with Compose plugin
- `curl` and `jq` (for the example commands)

**Option B — Python (no Docker)**:
- Python 3.11+
- `pip`
- `curl` and `jq`

---

## Option A: Docker Compose (Recommended)

### 1. Generate dev RSA key pair

```bash
cd stub-platform
mkdir -p keys
# Generate 2048-bit RSA private key
openssl genrsa -out keys/private.pem 2048
# Extract public key
openssl rsa -in keys/private.pem -pubout -out keys/public.pem
```

> Keys are `.gitignore`d. Generate once; they persist across restarts.

### 2. Start all services

```bash
docker compose up --build
```

All four services start in ~20–30 seconds. You'll see health checks pass in the logs.

**Services running**:

| Service         | Port | URL                      |
|----------------|------|--------------------------|
| Auth Stub       | 8000 | http://localhost:8000    |
| Creative Agent  | 8001 | http://localhost:8001    |
| Media Agent     | 8002 | http://localhost:8002    |
| Analytics Agent | 8003 | http://localhost:8003    |

### 3. Verify health checks

```bash
curl http://localhost:8000/health  # auth stub
curl http://localhost:8001/health  # creative agent
curl http://localhost:8002/health  # media agent
curl http://localhost:8003/health  # analytics agent
```

All should return:
```json
{"status": "healthy", "service": "<service-name>"}
```

---

## Option B: Python Without Docker

### 1. Set up virtual environment and install dependencies

```bash
cd stub-platform
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Generate dev RSA key pair

```bash
mkdir -p keys
openssl genrsa -out keys/private.pem 2048
openssl rsa -in keys/private.pem -pubout -out keys/public.pem
```

### 3. Start each service in a separate terminal

**Terminal 1 — Auth Stub**:
```bash
cd stub-platform
uvicorn auth.main:app --port 8000 --reload
```

**Terminal 2 — Creative Agent**:
```bash
cd stub-platform
AGENT_NAME=creative-agent uvicorn agents.creative.main:app --port 8001 --reload
```

**Terminal 3 — Media Agent**:
```bash
cd stub-platform
AGENT_NAME=media-agent uvicorn agents.media.main:app --port 8002 --reload
```

**Terminal 4 — Analytics Agent**:
```bash
cd stub-platform
AGENT_NAME=analytics-agent uvicorn agents.analytics.main:app --port 8003 --reload
```

---

## Core Workflow: Get a Token and Invoke an Agent

### Step 1: Obtain a JWT from the auth stub

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/token \
  -d "grant_type=client_credentials" \
  -d "client_id=demo-client" \
  -d "client_secret=demo-secret" \
  -d "scope=agents.invoke" \
  | jq -r '.access_token')

echo "Token obtained: ${TOKEN:0:50}..."
```

### Step 2: Invoke the Creative Agent

```bash
curl -s -X POST http://localhost:8001/invoke \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a summer campaign for a beverage brand targeting Gen Z."}' \
  | jq .
```

**Expected output**:
```json
{
  "agent_name": "creative-agent",
  "response": "Campaign Concept: 'Refresh Your World'\n\nTarget Audience: Gen Z (18–26)...",
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### Step 3: Invoke the Media Agent

```bash
curl -s -X POST http://localhost:8002/invoke \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Plan a media campaign for Q3 with a £500k budget."}' \
  | jq .
```

### Step 4: Invoke the Analytics Agent

```bash
curl -s -X POST http://localhost:8003/invoke \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What are the top performing channels this quarter?"}' \
  | jq .
```

---

## Inspect the OpenAPI Specs

Each agent serves its own OpenAPI 3.0 spec. These are the specs you'll use to create
M365 API Plugin manifests in Pattern A.

```bash
# Creative Agent OpenAPI spec
curl -s http://localhost:8001/openapi.json | jq .

# Interactive docs (Swagger UI) — open in browser
open http://localhost:8001/docs
```

---

## Inspect the Auth Stub

```bash
# OIDC discovery document
curl -s http://localhost:8000/.well-known/openid-configuration | jq .

# Public key set (JWKS)
curl -s http://localhost:8000/.well-known/jwks.json | jq .
```

---

## Test Auth Rejection

Verify agents correctly reject invalid tokens:

```bash
# No token — expect HTTP 401
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8001/invoke \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'
# Output: 401

# Invalid token — expect HTTP 401
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8001/invoke \
  -H "Authorization: Bearer not-a-real-token" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'
# Output: 401
```

---

## Session ID Continuity

Pass a `session_id` to maintain a consistent identifier across calls (stub echoes it back):

```bash
curl -s -X POST http://localhost:8001/invoke \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Continue the campaign brief.", "session_id": "my-session-123"}' \
  | jq .session_id
# Output: "my-session-123"
```

---

## Stopping the Platform

```bash
# Docker
docker compose down

# Python — Ctrl+C in each terminal
```

---

## Next Steps

Once the stub platform is running, the next feature is **Pattern A: API Plugin** — wrapping
these stub agents as M365 Copilot API Plugins using Azure APIM and a Declarative Agent manifest.
