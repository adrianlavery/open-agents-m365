# Research: Local Stub Agent Platform

**Feature**: `001-stub-agent-platform`
**Date**: 2026-03-25

---

## Decision 1: Python Web Framework for Stub Services

**Decision**: FastAPI (Python 3.11+)

**Rationale**: FastAPI natively generates OpenAPI 3.0 specs from code (served at `/openapi.json`
by default), which directly satisfies FR-003. It also provides async support, built-in
request validation via Pydantic, and extremely low setup overhead — ideal for lightweight stubs.
Uvicorn is the production-grade ASGI server used with FastAPI.

**Alternatives considered**:
- Flask/Quart: Does not generate OpenAPI specs natively; would require a separate library
  (flasgger/apispec) adding complexity.
- Django REST Framework: Heavy — far more than needed for four stub services with 2-3 endpoints each.
- aiohttp: Lower-level; no automatic OpenAPI generation.

---

## Decision 2: JWT Signing Algorithm — RS256 (Asymmetric)

**Decision**: RS256 (RSA with SHA-256), asymmetric key pair.

**Rationale**: Asymmetric signing means agents only need the **public key** to validate tokens;
the private key stays in the auth stub. This matches real-world IdP behavior (Entra ID, Okta, Auth0
all use RS256 or ES256). Agents receive the public key (or JWKS URI) via configuration — when the
auth stub is swapped for a real IdP, only the `JWKS_URI` or `OIDC_ISSUER` environment variable
changes. No agent code changes required. This directly satisfies FR-011.

**Alternatives considered**:
- HS256 (symmetric/shared secret): Simpler to implement but agents would need the secret,
  making secret rotation harder and IdP-swap more intrusive (agents would need to unlearn the
  shared-secret pattern). Not representative of real production IdP behavior.
- ES256 (ECDSA): Also valid and used in production, but RS256 has broader library support in
  Python (python-jose, PyJWT) and is more familiar in Microsoft/Okta contexts.

---

## Decision 3: Key Material Strategy for Auth Stub

**Decision**: Generate a fixed RSA key pair at project setup time; store public key as a
static file (PEM) accessible to agents. Auth stub loads the private key; agents load the
public key via file mount or environment variable.

**Rationale**: Generating a key pair at container startup (ephemeral) would require agents to
re-fetch the public key on every restart, adding complexity. A committed dev key pair (clearly
marked as non-production) is simpler and mirrors how real teams use dev certificates. The public
key is shared via Docker Compose volume or `AGENT_PUBLIC_KEY_PATH` env var.

**Alternatives considered**:
- JWKS endpoint (agents fetch keys dynamically): More realistic for production swapping, but
  adds a network dependency per agent startup. Can be added as an enhancement for Pattern A.
- Symmetric key: Rejected (see Decision 2).

---

## Decision 4: Multi-Service Project Layout

**Decision**: Monorepo under `stub-platform/` with a `shared/` library for common auth
middleware and Pydantic models, and per-service subdirectories for each agent and the auth stub.

```
stub-platform/
├── shared/               # Common Python package (auth middleware, models)
├── auth/                 # Auth stub service
├── agents/
│   ├── creative/
│   ├── media/
│   └── analytics/
├── keys/                 # Dev RSA key pair (non-production)
├── docker-compose.yml
└── README.md
```

**Rationale**: The three agents are structurally identical (same endpoints, same auth validation,
same response schema). Sharing auth middleware and Pydantic models from a `shared/` package
avoids three copies of the same JWT validation logic — a maintenance hazard. FastAPI makes
sharing Pydantic models trivial.

**Alternatives considered**:
- Fully independent services with no shared code: Each agent would re-implement JWT validation
  independently. Any auth change (e.g., swapping JWKS URI) would require updating three files.
- Single monolithic FastAPI app with routing: Would not satisfy the "independently runnable
  services" requirement (FR-001) or the separate Docker containers in Compose (FR-012).

---

## Decision 5: Mock Response Strategy

**Decision**: Template-based mock responses using Python f-strings, with prompt keyword
detection for minor variation. No randomness by default; deterministic output.

**Rationale**: Workshop demos benefit from predictable, reviewable outputs. Deterministic
responses mean presenters know exactly what will appear. Prompt keyword detection (e.g.,
"summer" → summer-themed campaign) adds enough realism without LLM complexity. Static
templates are easy to update for different client contexts.

**Alternatives considered**:
- Fully random responses: Unpredictable in live demos.
- Pre-canned JSON fixture files: Less flexible; harder to incorporate prompt content.
- Real LLM calls: Explicitly out of scope (spec).

---

## Decision 6: OAuth2 Flows to Support

**Decision**: Implement client credentials (`grant_type=client_credentials`) as the primary
flow; add a minimal authorization code flow stub (`grant_type=authorization_code`) for
completeness. Client credentials is used for service-to-service; auth code simulates
user-delegated access (needed for Pattern A in M365 context).

**Rationale**: Pattern A (API Plugin in M365 Copilot) uses OAuth2 authorization code flow with
PKCE for user-delegated access. Having both flows in the stub lets workshop attendees see
both patterns. Client credentials is simpler to demo in curl examples.

**Pre-configured test clients** (hardcoded in dev config):
- `client_id: demo-client`, `client_secret: demo-secret`, scope: `agents.invoke`
- `client_id: m365-plugin`, `client_secret: plugin-secret`, scope: `agents.invoke openid profile`

---

## Decision 7: Port Assignments

| Service         | Port |
|----------------|------|
| Auth Stub       | 8000 |
| Creative Agent  | 8001 |
| Media Agent     | 8002 |
| Analytics Agent | 8003 |

All ports configurable via environment variables (`PORT`, defaulting to above values).

---

## Decision 8: Python Library Choices

| Purpose              | Library              | Reason |
|---------------------|----------------------|--------|
| Web framework        | `fastapi`            | OpenAPI auto-gen, async, Pydantic |
| ASGI server          | `uvicorn[standard]`  | Production-grade, FastAPI default |
| JWT encode/decode    | `python-jose[cryptography]` | RS256 support, JWKS-ready |
| RSA key generation   | `cryptography`       | Industry standard, used by python-jose |
| Data validation      | `pydantic` (v2)      | Bundled with FastAPI |
| HTTP client (tests)  | `httpx`              | FastAPI's recommended async test client |
| Testing              | `pytest` + `pytest-asyncio` | Standard Python test stack |

---

## Decision 9: OIDC Discovery Document

The auth stub's `/.well-known/openid-configuration` will return a standard OIDC metadata
document pointing to the local auth stub endpoints. This is the mechanism that makes the
auth stub swappable — when agents need to validate tokens from Entra ID instead, they only
change the `OIDC_ISSUER_URL` environment variable, and the OIDC discovery document at
`{OIDC_ISSUER_URL}/.well-known/openid-configuration` provides the JWKS URI automatically.

Agents will support two validation modes (configured via env var):
1. **Static public key** (`AGENT_PUBLIC_KEY_PATH`): Loads PEM file at startup.
2. **JWKS URI** (`AGENT_JWKS_URI`): Fetches keys from a JWKS endpoint (used with real IdPs).

For local dev, static public key mode is default. JWKS URI mode is used when connecting
to a real IdP in later features.
