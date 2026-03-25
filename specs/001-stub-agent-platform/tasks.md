---

description: "Task list for Local Stub Agent Platform implementation"
---

# Tasks: Local Stub Agent Platform

**Input**: Design documents from `/specs/001-stub-agent-platform/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Create the `stub-platform/` directory structure and shared tooling configuration.

- [x] T001 Create top-level directory structure: `stub-platform/shared/`, `stub-platform/auth/`, `stub-platform/agents/creative/`, `stub-platform/agents/media/`, `stub-platform/agents/analytics/`, `stub-platform/keys/`
- [x] T002 [P] Create `stub-platform/requirements.txt` with shared deps: `fastapi`, `uvicorn[standard]`, `python-jose[cryptography]`, `cryptography`, `pydantic>=2.0`, `httpx`, `pytest`, `pytest-asyncio`
- [x] T003 [P] Create `stub-platform/shared/__init__.py` as an empty package initializer
- [x] T004 [P] Create `stub-platform/.gitignore` ignoring `keys/*.pem`, `__pycache__/`, `.venv/`, `*.pyc`
- [x] T005 [P] Create `stub-platform/keys/README.md` documenting how to generate the RSA key pair with the `openssl` commands from `specs/001-stub-agent-platform/quickstart.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared models and auth middleware that ALL agents depend on. Must be complete before any agent implementation.

⚠️ **CRITICAL**: No agent work can begin until this phase is complete.

- [ ] T006 Create `stub-platform/shared/models.py` with Pydantic v2 models: `InvokeRequest` (fields: `prompt: str`, `session_id: str | None = None`), `InvokeResponse` (fields: `agent_name: str`, `response: str`, `session_id: str`), `HealthResponse` (fields: `status: str = "healthy"`, `service: str`) — per `specs/001-stub-agent-platform/data-model.md`
- [ ] T007 Create `stub-platform/shared/auth_middleware.py` implementing a FastAPI dependency `verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()))` that: (1) loads the public key from `AGENT_PUBLIC_KEY_PATH` env var (PEM file) OR fetches from `AGENT_JWKS_URI` if set, (2) decodes and verifies RS256 JWT using `python-jose`, (3) validates `iss` matches `OIDC_ISSUER` env var and `aud` matches `JWT_AUDIENCE` env var, (4) raises `HTTPException(status_code=401)` with detail message for missing/expired/invalid tokens — per `specs/001-stub-agent-platform/data-model.md` state transitions and `contracts/agent-invoke.md`
- [ ] T008 [P] Create per-service `requirements.txt` files for each service directory: `stub-platform/auth/requirements.txt`, `stub-platform/agents/creative/requirements.txt`, `stub-platform/agents/media/requirements.txt`, `stub-platform/agents/analytics/requirements.txt` — all referencing same deps as `stub-platform/requirements.txt` plus `../shared` local package

**Checkpoint**: `shared/models.py` and `shared/auth_middleware.py` complete — agent implementation can begin.

---

## Phase 3: User Story 1 — Invoke a Stub Agent via Authenticated REST Call (Priority: P1) 🎯 MVP

**Goal**: Auth stub issues JWTs; stub agents validate them and return mock responses on `POST /invoke`.

**Independent Test**: Start auth stub and one agent (e.g., creative). Obtain a token via `POST /token`, call `POST /invoke` with valid JWT → receive `InvokeResponse`. Call without token → receive 401.

### Auth Stub Implementation

- [ ] T009 Create `stub-platform/auth/clients.py` defining a `REGISTERED_CLIENTS` dict with two pre-configured dev clients: `{"demo-client": {"secret": "demo-secret", "scopes": ["agents.invoke"]}, "m365-plugin": {"secret": "plugin-secret", "scopes": ["agents.invoke", "openid", "profile"]}}` — per `specs/001-stub-agent-platform/contracts/auth-stub.md`
- [ ] T010 Create `stub-platform/auth/main.py` as a FastAPI app with: (1) `POST /token` endpoint supporting `grant_type=client_credentials` (form-encoded) — validates `client_id`/`client_secret` against `clients.py`, issues RS256 JWT with claims `sub`, `iss`, `aud`, `exp`, `iat`, `scope` using private key at `PRIVATE_KEY_PATH` env var; (2) returns `TokenResponse` with `access_token`, `token_type="Bearer"`, `expires_in`, `scope`; (3) returns OAuth2-compliant error responses (400/401) for invalid client or bad grant type — per `specs/001-stub-agent-platform/contracts/auth-stub.md`
- [ ] T011 Add `GET /health` endpoint to `stub-platform/auth/main.py` returning `HealthResponse(status="healthy", service="auth-stub")` with no auth required — per `specs/001-stub-agent-platform/data-model.md`

### Creative Agent Implementation

- [ ] T012 [P] Create `stub-platform/agents/creative/responses.py` with a `build_response(prompt: str) -> str` function returning a templated mock creative campaign response. If prompt contains keywords like "summer", "brand", or "campaign", incorporate them into the response text. Default response: a multi-line campaign brief. Keep responses realistic and workshop-presentable — per research.md Decision 5
- [ ] T013 [P] Create `stub-platform/agents/creative/main.py` as a FastAPI app with: (1) `POST /invoke` endpoint using `verify_jwt_token` dependency from `shared/auth_middleware.py`, accepting `InvokeRequest`, generating a UUID v4 `session_id` if not provided, calling `responses.build_response(prompt)`, returning `InvokeResponse(agent_name="creative-agent", response=..., session_id=...)`; (2) `GET /health` returning `HealthResponse(status="healthy", service="creative-agent")` with no auth; (3) FastAPI `title="Creative Agent Stub"`, `description` matching contracts/agent-invoke.md — per `specs/001-stub-agent-platform/contracts/agent-invoke.md`

### Media Agent Implementation

- [ ] T014 [P] Create `stub-platform/agents/media/responses.py` with a `build_response(prompt: str) -> str` function returning a templated mock media plan response. Include channel mix (TV, digital, social), budget allocation, and timeline. Incorporate prompt keywords where natural. Default: a structured media plan with channel recommendations — per research.md Decision 5
- [ ] T015 [P] Create `stub-platform/agents/media/main.py` as a FastAPI app identical in structure to `agents/creative/main.py` but with `agent_name="media-agent"`, `title="Media Agent Stub"`, and importing from `agents/media/responses.py` — per `specs/001-stub-agent-platform/contracts/agent-invoke.md`

### Analytics Agent Implementation

- [ ] T016 [P] Create `stub-platform/agents/analytics/responses.py` with a `build_response(prompt: str) -> str` function returning a templated mock analytics insight response. Include metrics (impressions, CTR, conversions), trend commentary, and recommendations. Incorporate prompt keywords where natural — per research.md Decision 5
- [ ] T017 [P] Create `stub-platform/agents/analytics/main.py` as a FastAPI app identical in structure to `agents/creative/main.py` but with `agent_name="analytics-agent"`, `title="Analytics Agent Stub"`, and importing from `agents/analytics/responses.py` — per `specs/001-stub-agent-platform/contracts/agent-invoke.md`

**Checkpoint**: Auth stub + all three agents runnable via `uvicorn`. Token → invoke flow works end-to-end. HTTP 401 on missing/invalid JWT verified manually. User Story 1 independently complete.

---

## Phase 4: User Story 2 — Docker Compose One-Command Startup (Priority: P2)

**Goal**: All four services containerised and orchestratable with `docker compose up`.

**Independent Test**: `docker compose up --build` starts all four services. All four `/health` endpoints return 200 within 30 seconds. Key generation documented and works.

- [ ] T018 Create `stub-platform/auth/Dockerfile`: Python 3.11-slim base image, `COPY` auth and shared directories, `pip install -r requirements.txt`, `CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]` — per plan.md project structure
- [ ] T019 [P] Create `stub-platform/agents/creative/Dockerfile`: Python 3.11-slim base image, `COPY` agents/creative and shared directories, `pip install`, `CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]` — per plan.md project structure
- [ ] T020 [P] Create `stub-platform/agents/media/Dockerfile`: identical structure to creative Dockerfile but port 8002 — per plan.md project structure
- [ ] T021 [P] Create `stub-platform/agents/analytics/Dockerfile`: identical structure to creative Dockerfile but port 8003 — per plan.md project structure
- [ ] T022 Create `stub-platform/docker-compose.yml` defining four services: `auth-stub` (build: `./auth`, ports: `8000:8000`, volumes: `./keys:/keys:ro`, env: `PRIVATE_KEY_PATH=/keys/private.pem`, `PUBLIC_KEY_PATH=/keys/public.pem`, `ISSUER=http://localhost:8000`, `AUDIENCE=agents`, healthcheck: `GET /health`), `creative-agent` (build: `./agents/creative`, ports: `8001:8001`, volumes: `./keys:/keys:ro`, env: `AGENT_NAME=creative-agent`, `AGENT_PUBLIC_KEY_PATH=/keys/public.pem`, `OIDC_ISSUER=http://localhost:8000`, `JWT_AUDIENCE=agents`, healthcheck), `media-agent` (same pattern, port 8002), `analytics-agent` (same pattern, port 8003) — per `specs/001-stub-agent-platform/data-model.md` config model and research.md Decision 7

**Checkpoint**: `docker compose up` brings all services up. Health checks green. User Story 2 independently testable.

---

## Phase 5: User Story 3 — Discover Agent Contracts via OpenAPI Spec (Priority: P3)

**Goal**: Each agent's auto-generated OpenAPI spec is enriched with correct metadata, security scheme, and examples matching `contracts/agent-invoke.md`. Auth stub exposes OIDC discovery and JWKS endpoints.

**Independent Test**: `GET /openapi.json` on each agent returns a valid OpenAPI 3.0 document. `GET /.well-known/openid-configuration` on auth stub returns valid OIDC metadata. `GET /.well-known/jwks.json` returns valid JWKS.

- [ ] T023 Enrich `stub-platform/agents/creative/main.py` FastAPI app metadata: set `openapi_url="/openapi.json"`, add `BearerAuth` security scheme to the OpenAPI spec via `app.openapi()` override, add request/response examples on the `/invoke` endpoint matching `specs/001-stub-agent-platform/contracts/agent-invoke.md` — ensures SC-005 (valid OpenAPI 3.0 spec)
- [ ] T024 [P] Apply same OpenAPI enrichment to `stub-platform/agents/media/main.py` — matching `specs/001-stub-agent-platform/contracts/agent-invoke.md`
- [ ] T025 [P] Apply same OpenAPI enrichment to `stub-platform/agents/analytics/main.py` — matching `specs/001-stub-agent-platform/contracts/agent-invoke.md`
- [ ] T026 Add `GET /.well-known/openid-configuration` endpoint to `stub-platform/auth/main.py` returning an `OIDCConfiguration`-shaped JSON response with all fields from `specs/001-stub-agent-platform/data-model.md` (issuer, authorization_endpoint, token_endpoint, jwks_uri, supported grant types, algorithms, scopes) — per `specs/001-stub-agent-platform/contracts/auth-stub.md`
- [ ] T027 Add `GET /.well-known/jwks.json` endpoint to `stub-platform/auth/main.py` that reads the public key from `PUBLIC_KEY_PATH`, converts the RSA public key to JWKS format (extracting `n` and `e` as Base64url), and returns a `{"keys": [...]}` document with `kty="RSA"`, `use="sig"`, `kid="stub-dev-key-1"`, `alg="RS256"` — per `specs/001-stub-agent-platform/contracts/auth-stub.md`
- [ ] T028 [P] Add `GET /authorize` stub endpoint to `stub-platform/auth/main.py` supporting OAuth2 authorization code flow: accepts `response_type`, `client_id`, `redirect_uri`, `scope`, `state` query params; validates client_id against `clients.py`; generates a short-lived (60s) single-use auth code; redirects to `redirect_uri?code=<code>&state=<state>` — per `specs/001-stub-agent-platform/contracts/auth-stub.md`
- [ ] T029 Extend `stub-platform/auth/main.py` `POST /token` to also handle `grant_type=authorization_code`: validate `code`, `client_id`, `client_secret`, `redirect_uri`; consume the single-use code; issue JWT same as client credentials flow — per `specs/001-stub-agent-platform/contracts/auth-stub.md`

**Checkpoint**: OpenAPI specs validated. OIDC discovery and JWKS accessible. Auth code flow testable via curl. User Story 3 independently complete.

---

## Phase 6: User Story 4 — Run Services Without Docker (Priority: P4)

**Goal**: Non-Docker setup is fully documented and works with standard Python tooling.

**Independent Test**: Fresh venv, `pip install -r requirements.txt`, start each service with `uvicorn` per README instructions — all four services healthy.

- [ ] T030 Create `stub-platform/README.md` with: (1) project overview and port map table, (2) RSA key generation commands, (3) Docker Compose quickstart (all steps from `specs/001-stub-agent-platform/quickstart.md` Docker path), (4) Python/uvicorn non-Docker path (all steps from quickstart.md Option B), (5) curl examples: obtain token, invoke all three agents, test auth rejection, inspect OpenAPI spec and OIDC discovery — SC-001 compliance gate

**Checkpoint**: Any developer can follow README start-to-finish and have a working platform. User Story 4 complete.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Auth code flow edge cases, error handling hardening, and end-to-end validation.

- [ ] T031 [P] Add `GET /authorize` OAuth2 authorization code flow endpoint to `stub-platform/auth/main.py` — add in-memory (dict) short-lived code store with expiry checking to support T029; ensure codes are single-use and expire after 60 seconds
- [ ] T032 [P] Harden error handling in `stub-platform/shared/auth_middleware.py`: ensure wrong-key-signature errors (JWTError with signature mismatch) return 401 not 500; ensure all `python-jose` exceptions are caught and mapped to appropriate 401 responses with detail messages matching `specs/001-stub-agent-platform/data-model.md` state transitions
- [ ] T033 [P] Add `AGENT_JWKS_URI` support to `stub-platform/shared/auth_middleware.py`: if `AGENT_JWKS_URI` env var is set, fetch JWKS from that URL on startup (cache the keys), use fetched keys for validation instead of local PEM file — this is the IdP-swap mechanism (SC-006, FR-011)
- [ ] T034 Run `docker compose up --build` end-to-end and validate: (1) all health checks green, (2) token issuance works, (3) all three agents respond to `/invoke`, (4) 401s returned for missing/bad tokens, (5) `/openapi.json` accessible on each agent, (6) OIDC discovery and JWKS accessible — verify against all SC-001 through SC-006

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all agent work
- **US1 — Auth+Invoke (Phase 3)**: Depends on Phase 2 — auth stub (T009–T011) must complete before agents (T012–T017); agents T012–T017 can all run in parallel after T011
- **US2 — Docker (Phase 4)**: Depends on Phase 3 complete — Dockerfiles require working services
- **US3 — OpenAPI/OIDC (Phase 5)**: Depends on Phase 3 — enriches existing services; T023–T025 parallel; OIDC endpoints T026–T029 parallel where noted
- **US4 — Non-Docker docs (Phase 6)**: Can start after Phase 3; depends on all services being finalized
- **Polish (Phase 7)**: Depends on Phase 5 complete

### Within Phase 3 (Critical Path)

```
T006 (models) → T007 (auth_middleware) → T010 (auth main) → T012..T017 (agents, all parallel)
T008 (req files, parallel with T006/T007)
T009 (clients.py, parallel with T006/T007) → T010
T011 (auth /health, same file as T010 — sequential after T010)
```

### Parallel Opportunities by Phase

**Phase 2**: T006, T007, T008 can all start simultaneously (different files).

**Phase 3 — after T010/T011 complete**:
```bash
# Launch all six agent files simultaneously:
Task: "stub-platform/agents/creative/responses.py"   [T012]
Task: "stub-platform/agents/creative/main.py"        [T013]
Task: "stub-platform/agents/media/responses.py"      [T014]
Task: "stub-platform/agents/media/main.py"           [T015]
Task: "stub-platform/agents/analytics/responses.py"  [T016]
Task: "stub-platform/agents/analytics/main.py"       [T017]
```

**Phase 4 — Dockerfiles (after Phase 3)**:
```bash
Task: "stub-platform/auth/Dockerfile"              [T018]
Task: "stub-platform/agents/creative/Dockerfile"   [T019]
Task: "stub-platform/agents/media/Dockerfile"      [T020]
Task: "stub-platform/agents/analytics/Dockerfile"  [T021]
# Then T022 (docker-compose.yml) after all Dockerfiles
```

**Phase 5 — OpenAPI enrichment**:
```bash
Task: "Enrich creative main.py openapi"   [T023]
Task: "Enrich media main.py openapi"      [T024]
Task: "Enrich analytics main.py openapi"  [T025]
Task: "OIDC discovery endpoint"           [T026]
Task: "JWKS endpoint"                     [T027]
Task: "/authorize endpoint"               [T028]
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (shared models + auth middleware)
3. Complete Phase 3: Auth stub + three agents with invoke+auth
4. **STOP AND VALIDATE**: Get a token, call all three `/invoke` endpoints, confirm 401 rejections
5. This is a fully usable local agent sandbox — demonstrate Pattern A integration readiness

### Incremental Delivery

1. Phase 1 + 2 → Foundation ready
2. Phase 3 → **MVP**: Token issuance + agent invocation with auth ✅
3. Phase 4 → Add Docker Compose → One-command startup ✅
4. Phase 5 → Add OpenAPI/OIDC specs → Pattern A integration ready ✅
5. Phase 6 → Add README → Workshop-ready onboarding ✅
6. Phase 7 → Hardening → Production-quality demo platform ✅

### Parallel Team Strategy

With two developers:
- **Developer A**: T006 (models) → T007 (auth_middleware) → T009+T010+T011 (auth stub) → T018 (auth Dockerfile)
- **Developer B**: T008 (req files) → T012+T014+T016 (response templates) → T013+T015+T017 (agent mains) → T019+T020+T021 (agent Dockerfiles)
- Both converge on T022 (docker-compose.yml) → Phase 5 → Phase 6

---

## Notes

- T031 and T028 both touch `/authorize` in `auth/main.py` — implement together or ensure T028 scaffolds the endpoint that T031 completes
- The `shared/` package must be importable from each agent's working directory — test this in Phase 2 before proceeding
- RSA key pair generation (T005 documents it) must be done by the developer before any service starts; the `keys/` directory is gitignored
- Do NOT hardcode keys or secrets in source files; all sensitive values via env vars only
- Commit after each phase checkpoint to enable incremental review
