# Implementation Plan: Local Stub Agent Platform

**Branch**: `001-stub-agent-platform` | **Date**: 2026-03-25 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-stub-agent-platform/spec.md`

## Summary

Build a local Python-based stub platform that simulates the client's AWS/GCP agent
infrastructure for local development and workshop demos. Four FastAPI services (three
domain stub agents + one auth stub) run together via Docker Compose, expose a consistent
`POST /invoke` REST API with OpenAPI 3.0 specs, and enforce OAuth2/OIDC JWT authentication.
The auth layer is designed to be swappable via configuration only — replacing the local
auth stub with Entra ID or Okta in later features requires no agent code changes.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, uvicorn[standard], python-jose[cryptography], pydantic v2, httpx, pytest, pytest-asyncio
**Storage**: N/A (fully stateless)
**Testing**: pytest + pytest-asyncio + httpx (FastAPI test client)
**Target Platform**: Linux (Docker containers), local developer machine (macOS/Windows/Linux)
**Project Type**: Multi-service web APIs (4 independent FastAPI services)
**Performance Goals**: <500ms response on `/invoke` on a standard developer laptop (SC-003)
**Constraints**: Swappable auth via env vars only; no agent code changes for IdP swap (FR-011)
**Scale/Scope**: Local dev/demo only; 4 services; no production deployment

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. API-First Integration** | ✅ PASS | Each agent exposes OpenAPI 3.0 spec at `/openapi.json` (FR-003). FastAPI auto-generates from code. |
| **II. Zero Re-Platforming** | ✅ PASS | This feature *is* the stub platform that simulates what real client agents look like. The auth middleware design (env-var-only config swap) ensures that when real agents are targeted in later features, no agent code changes are needed. |
| **III. Progressive Integration Depth** | ✅ PASS | This feature is the pre-Phase 1 foundation. It enables Pattern A (next feature). Delivers standalone value as a local sandbox. |
| **IV. Auth as First-Class Concern** | ✅ PASS | OAuth2/OIDC auth stub with RS256 JWT signing. JWT validated at every `/invoke` call. Auth design documented in `contracts/auth-stub.md` with IdP swappability explicitly designed. |
| **V. M365-Native UX** | N/A | This feature has no M365 surface — it is the backend stub platform. M365 integration begins in Pattern A. |
| **VI. Documentation-Driven Development** | ✅ PASS | Spec, research, data-model, contracts, and quickstart complete before implementation. |

**Gate result**: ✅ All applicable principles pass. Proceed to implementation.

## Project Structure

### Documentation (this feature)

```text
specs/001-stub-agent-platform/
├── plan.md              ← This file
├── spec.md              ← Feature specification
├── research.md          ← Technical decisions and rationale
├── data-model.md        ← Entity definitions, config model, state transitions
├── quickstart.md        ← Setup and usage instructions
├── checklists/
│   └── requirements.md  ← Spec quality checklist
└── contracts/
    ├── agent-invoke.md  ← POST /invoke OpenAPI contract (all agents)
    └── auth-stub.md     ← Auth stub endpoints and JWT structure
```

### Source Code (repository root)

```text
stub-platform/
├── shared/                        # Shared Python package (imported by all agents)
│   ├── __init__.py
│   ├── models.py                  # InvokeRequest, InvokeResponse, HealthResponse Pydantic models
│   └── auth_middleware.py         # JWT validation dependency (env-var-configurable)
│
├── auth/                          # Auth stub service
│   ├── main.py                    # FastAPI app: /token, /authorize, /health, OIDC endpoints
│   ├── clients.py                 # Pre-registered dev clients (demo-client, m365-plugin)
│   ├── requirements.txt
│   └── Dockerfile
│
├── agents/
│   ├── creative/
│   │   ├── main.py                # FastAPI app: /invoke (creative mock), /health
│   │   ├── responses.py           # Mock creative campaign response templates
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── media/
│   │   ├── main.py                # FastAPI app: /invoke (media plan mock), /health
│   │   ├── responses.py           # Mock media plan response templates
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── analytics/
│       ├── main.py                # FastAPI app: /invoke (analytics mock), /health
│       ├── responses.py           # Mock analytics insights response templates
│       ├── requirements.txt
│       └── Dockerfile
│
├── keys/                          # Dev RSA key pair (gitignored, generated once)
│   ├── private.pem
│   └── public.pem
│
├── docker-compose.yml             # Orchestrates all 4 services with health checks
├── requirements.txt               # Shared/top-level deps for non-Docker path
└── README.md                      # Setup instructions, port map, curl examples
```

**Structure Decision**: Multi-service monorepo under `stub-platform/`. A `shared/` package
avoids duplicating JWT validation and Pydantic models across three identical agent services.
Each agent and the auth stub are independently runnable. This directly matches the
requirement for four separately containerised services (FR-012) while eliminating
maintenance duplication.

## Complexity Tracking

No constitution violations to justify. All complexity is necessary and bounded:

| Decision | Why Needed |
|----------|------------|
| 4 separate services | Required by spec (FR-001, FR-012) — must be independently runnable |
| RSA key pair | Required by auth design (RS256 for IdP-swappability, Decision 2 in research.md) |
| `shared/` package | Avoids 3× duplicate auth middleware; justified by DRY principle |
