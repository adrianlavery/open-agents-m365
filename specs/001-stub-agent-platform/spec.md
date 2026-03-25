# Feature Specification: Local Stub Agent Platform

**Feature Branch**: `001-stub-agent-platform`
**Created**: 2026-03-25
**Status**: Draft

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Invoke a Stub Agent via Authenticated REST Call (Priority: P1)

A developer or workshop presenter wants to demonstrate an agent invocation locally.
They obtain a JWT token from the local auth service, then call one of the three stub
agents (Creative, Media, or Analytics) with a prompt and receive a plausible mock response.
This is the core end-to-end flow that all later M365 integration patterns depend on.

**Why this priority**: Without a working invoke-with-auth flow, no subsequent integration
pattern (A, B, or C) can be built or demonstrated. This is the foundational capability.

**Independent Test**: Run `docker compose up`, obtain a token with a curl command, POST to
`/invoke` on any stub agent with a prompt — receive a structured JSON response. Demonstrates
value standalone as a local agent sandbox.

**Acceptance Scenarios**:

1. **Given** all services are running locally, **When** a developer sends a `POST /token`
   request to the auth stub with valid client credentials, **Then** they receive a JWT
   containing standard claims (`sub`, `iss`, `aud`, `exp`, `scope`).
2. **Given** a valid JWT, **When** a developer sends `POST /invoke` to the Creative Agent
   with `{"prompt": "Create a summer campaign"}`, **Then** they receive
   `{"agent_name": "creative-agent", "response": "<mock text>", "session_id": "<uuid>"}`.
3. **Given** no Authorization header, **When** a developer calls `POST /invoke`, **Then**
   the agent returns HTTP 401 Unauthorized.
4. **Given** an expired or malformed JWT, **When** a developer calls `POST /invoke`,
   **Then** the agent returns HTTP 401 Unauthorized.

---

### User Story 2 - Run All Services via Docker Compose (Priority: P2)

A developer who has just cloned the repo wants to get the full local platform running with
a single command (`docker compose up`) — all four services start, are healthy, and are
reachable on their designated ports.

**Why this priority**: This is the developer experience gate. Without a reliable one-command
startup, workshop setup and onboarding become fragile and time-consuming.

**Independent Test**: Run `docker compose up` from the repo root. Within 30 seconds, all
four health check endpoints (`GET /health`) return HTTP 200. No manual configuration steps
required beyond cloning the repo.

**Acceptance Scenarios**:

1. **Given** Docker and Docker Compose are installed, **When** `docker compose up` is run
   in the project root, **Then** all four services start without errors and their
   `/health` endpoints respond with HTTP 200 within 30 seconds.
2. **Given** all services are running, **When** a developer sends the example curl commands
   from the README, **Then** they successfully obtain a token and invoke each agent.
3. **Given** any single service is stopped, **When** its `/health` endpoint is called,
   **Then** it returns a non-200 status, confirming independent health reporting.

---

### User Story 3 - Discover Agent Contracts via OpenAPI Spec (Priority: P3)

A developer or integration engineer wants to inspect the exact API contract for a stub
agent so they can build the OpenAPI spec required for an M365 API Plugin (Pattern A).
They navigate to each agent's `/openapi.json` endpoint and retrieve a complete,
valid OpenAPI 3.0 document.

**Why this priority**: The OpenAPI spec is the bridge between the stub platform and M365
integration. Without it, Pattern A cannot be built. However, the invoke + auth flow
(P1/P2) must work first.

**Independent Test**: Call `GET /openapi.json` on each of the three agents. Each returns
a valid OpenAPI 3.0 JSON document that correctly describes the `POST /invoke` endpoint,
request body, and response schema — verified against an OpenAPI validator.

**Acceptance Scenarios**:

1. **Given** a stub agent is running, **When** `GET /openapi.json` is called, **Then**
   a valid OpenAPI 3.0 document is returned describing the `/invoke` and `/health` endpoints.
2. **Given** the three agent OpenAPI specs, **When** they are compared, **Then** the
   `/invoke` request and response schemas are identical across all three agents (only
   `agent_name` values differ).
3. **Given** the auth stub is running, **When** `GET /.well-known/openid-configuration`
   is called, **Then** a valid OIDC discovery document is returned listing the token
   endpoint and supported grant types.

---

### User Story 4 - Run Services Without Docker (Priority: P4)

A developer without Docker (or in a restricted environment) wants to run each service
directly using standard Python tooling. They install dependencies and launch each service
individually using documented commands.

**Why this priority**: Docker is the primary path, but workshop environments are varied.
Having a Docker-free path ensures no one is blocked by environment constraints.

**Independent Test**: In a Python virtual environment, run `pip install -r requirements.txt`
and start each service with `uvicorn`. All four services start and respond to health checks.

**Acceptance Scenarios**:

1. **Given** Python and pip are available, **When** a developer follows the non-Docker
   setup instructions in the README, **Then** all four services start successfully.
2. **Given** all services are running without Docker, **When** the example curl commands
   are executed, **Then** they produce the same results as the Docker Compose path.

---

### Edge Cases

- What happens when a JWT has valid format but is signed with the wrong key? The agent
  MUST return HTTP 401 (signature validation failure), not 500.
- What happens when `prompt` is an empty string in the invoke body? The agent MUST still
  return a mock response (empty prompts are valid for stub purposes).
- What happens when `session_id` is omitted from the invoke body? The agent MUST generate
  and return a new session ID in the response.
- What happens when the auth stub is unreachable and an agent tries to validate a token?
  Agents MUST perform local JWT validation (verify signature against a known public key)
  — they MUST NOT depend on a live auth service call per request.
- What happens when the client credentials grant uses unknown `client_id`? Auth stub MUST
  return HTTP 401 with an OAuth2-compliant error response body.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The platform MUST include three stub agent services: Creative Agent, Media
  Agent, and Analytics Agent — each as an independently runnable service.
- **FR-002**: Each stub agent MUST expose `POST /invoke` accepting
  `{"prompt": "string", "session_id": "string (optional)"}` and returning
  `{"agent_name": "string", "response": "string", "session_id": "string"}`.
- **FR-003**: Each stub agent MUST serve its OpenAPI 3.0 spec at `GET /openapi.json`.
- **FR-004**: Each stub agent MUST expose `GET /health` returning HTTP 200 when healthy.
- **FR-005**: All three stub agents MUST share an identical `/invoke` request and response
  schema; only the `agent_name` field value and mock response content differ.
- **FR-006**: The platform MUST include a local auth stub service that issues JWTs via
  OAuth2 client credentials flow (`POST /token`) and authorization code flow.
- **FR-007**: Issued JWTs MUST include standard claims: `sub`, `iss`, `aud`, `exp`, `scope`.
- **FR-008**: The auth stub MUST expose a OIDC discovery document at
  `GET /.well-known/openid-configuration`.
- **FR-009**: Each stub agent MUST validate the JWT on every request to `/invoke` and
  return HTTP 401 for missing, expired, or invalid tokens.
- **FR-010**: JWT validation in agents MUST be performed locally (signature verification
  against a known public key) — agents MUST NOT call the auth stub per request.
- **FR-011**: The auth integration in agents MUST be swappable via configuration only —
  swapping the issuer URL or public key MUST require no agent code changes.
- **FR-012**: A Docker Compose file MUST be provided that starts all four services, each
  on a distinct port, with health check configuration.
- **FR-013**: Mock responses MUST be realistic enough to represent each agent's domain
  (creative campaigns, media plans, analytics insights) without real LLM calls.
- **FR-014**: The platform MUST include a README with: setup instructions, port map,
  example curl commands to obtain a token and invoke each agent.
- **FR-015**: All services MUST be runnable without Docker via standard Python tooling.

### Key Entities

- **Stub Agent**: A lightweight service representing one agent capability. Has a name,
  a designated port, and produces domain-specific mock responses. Validates JWT auth.
- **JWT Token**: A signed token issued by the auth stub. Contains claims identifying the
  caller, intended audience, expiry, and granted scopes.
- **Auth Stub**: A local service that acts as a stand-in for a real IdP (Okta, Entra ID).
  Issues JWTs, exposes OIDC discovery. Configuration-only swap to real IdP.
- **Invoke Request**: The standard input to any agent — a prompt string and optional
  session identifier.
- **Invoke Response**: The standard output from any agent — agent name, mock response
  text, and session identifier (generated if not provided).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer with no prior project knowledge can clone the repo, run
  `docker compose up`, obtain a token, and invoke all three agents in under 5 minutes
  by following only the README instructions.
- **SC-002**: All four services pass their health checks within 30 seconds of
  `docker compose up`.
- **SC-003**: Calling `/invoke` with a valid JWT returns a response in under 500ms on a
  standard developer laptop.
- **SC-004**: Calling `/invoke` without a token, with an expired token, or with a
  malformed token returns HTTP 401 in 100% of test cases.
- **SC-005**: Each agent's `/openapi.json` passes validation as a valid OpenAPI 3.0
  document with no errors.
- **SC-006**: Swapping from the local auth stub to a different issuer (simulated by
  changing only configuration values) requires zero changes to agent source code.

## Assumptions

- Developers have Docker Desktop (or Docker Engine + Compose plugin) installed, or Python
  3.11+ with pip for the non-Docker path.
- Mock responses are static or lightly templated — no randomness beyond what aids
  demo realism. Response quality is not a success criterion.
- The auth stub uses asymmetric key signing (RS256) so that agents can validate tokens
  locally with a public key — matching realistic IdP behavior.
- Port assignments: auth stub on 8000, creative agent on 8001, media agent on 8002,
  analytics agent on 8003 (configurable via environment variables).
- Persistent session state across requests is out of scope — `session_id` is echoed
  back but not stored.
- No TLS/HTTPS required for the local stub environment; HTTP is sufficient.
- The feature is the integration target platform only; no M365 connection is made in
  this feature (that is Pattern A, a subsequent feature).
