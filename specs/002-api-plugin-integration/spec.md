# Feature Specification: Pattern A — API Plugin Integration

**Feature Branch**: `002-api-plugin-integration`
**Created**: 2025-07-14
**Status**: Draft
**Phase**: Phase 1 of Progressive Integration Depth (Constitution Principle III)
**Depends on**: `001-stub-agent-platform`

## Overview

This feature establishes the first integration tier between M365 Copilot and the local
stub agent platform built in feature 001. A Declarative Agent called "Open Agents" is
registered into the user's M365 Copilot environment via a Teams App Package. The agent
exposes the three stub agents (Creative, Media, Analytics) as API Plugin actions. When a
user types a prompt in M365 Copilot Chat, Copilot routes the request through the
Declarative Agent, which selects the appropriate stub agent, calls it over HTTPS via a
local tunnel, and surfaces the response back in the Copilot chat interface.

No changes are made to the stub agent code (Zero Re-Platforming principle). The only new
artifacts are integration manifests, OpenAPI plugin specs, a Teams App Package, auth
configuration, and local development tooling.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — End-to-End Demo: Creative Agent via M365 Copilot Chat (Priority: P1)

A workshop presenter is showing an audience how M365 Copilot can route a user's natural
language prompt to a specialised external agent. The presenter opens M365 Copilot Chat,
types "Create a summer campaign", and within a few seconds the Copilot UI displays a
creative-campaign mock response that originated from the local Creative Agent stub running
on the presenter's laptop.

**Why this priority**: This is the single most visible deliverable of the entire feature.
Every other story supports it. If only one thing works, it must be this.

**Independent Test**: With the stub platform running and the dev tunnel active, sideload
the Teams App Package, open M365 Copilot Chat, invoke the "Open Agents" declarative agent, and type
the demo prompt. Observe a response containing creative-campaign content appear in Copilot.
Delivers standalone value as proof that the full API Plugin integration pattern functions.

**Acceptance Scenarios**:

1. **Given** the stub platform is running locally and a dev tunnel exposes it to the
   internet, **When** a user types "Create a summer campaign" into M365 Copilot Chat
   while the "Open Agents" declarative agent is active, **Then** Copilot routes the
   request to the Creative Agent API Plugin, the stub agent's mock response is returned,
   and the response text appears in the Copilot Chat conversation.
2. **Given** the declarative agent is active, **When** the user types a prompt with
   media-related intent (e.g., "Plan a media buy for Q3"), **Then** Copilot routes to
   the Media Agent API Plugin and the mock media-plan response appears in M365 Copilot Chat.
3. **Given** the declarative agent is active, **When** the user types a prompt with
   analytics intent (e.g., "Analyse our campaign performance"), **Then** Copilot routes
   to the Analytics Agent API Plugin and the mock analytics response appears in M365 Copilot Chat.
4. **Given** a request reaches any stub agent via the API Plugin, **When** the plugin
   calls the agent's `/invoke` endpoint, **Then** the HTTP request carries a valid JWT
   in the Authorization header (obtained via the `m365-plugin` client credentials grant).

---

### User Story 2 — Sideload the Teams App Package into M365 (Priority: P2)

An integration engineer wants to register the "Open Agents" Declarative Agent into
their M365 Copilot tenant so it appears as an available agent in M365 Copilot Chat. They upload
the Teams App Package to their tenant using Teams Toolkit or the Teams Developer Portal.

**Why this priority**: Without a working Teams App Package, the agent cannot be activated
in any M365 tenant. This is the deployment gate for the integration.

**Independent Test**: Zip the Teams App Package, upload it to the Teams Admin Centre or
Developer Portal, and confirm the "Open Agents" agent appears in the M365 Copilot Chat agent list
and can be invoked. Delivers standalone value: the agent is registered and can be selected
even before a live tunnel is active.

**Acceptance Scenarios**:

1. **Given** a valid Teams App Package (manifest.json + icons + plugin specs), **When**
   the package is uploaded via Teams Toolkit or the Developer Portal, **Then** the "Open
   Agents" agent appears in the user's M365 Copilot Chat without errors.
2. **Given** the app is sideloaded, **When** the user opens the "Open Agents" agent in
   M365 Copilot Chat, **Then** the agent's description and capabilities are presented correctly.
3. **Given** an invalid or schema-violating manifest.json, **When** it is submitted for
   sideloading, **Then** the upload fails with a clear validation error (not a silent
   failure).

---

### User Story 3 — OAuth2 Auth Bridge: Plugin Obtains Token from Stub Auth Service (Priority: P3)

A security-aware reviewer or workshop facilitator wants to confirm that the integration
uses real OAuth2 token acquisition — not hard-coded credentials or anonymous calls. Before
calling any stub agent, the API Plugin must authenticate against the stub auth service
using the `m365-plugin` client and include the resulting JWT in every agent request.

**Why this priority**: The auth bridging pattern is one of the declared learning goals of
the workshop. It must be demonstrably working so that the audience sees the same config
pattern that will be used when swapping to Entra ID. However, the happy-path demo (P1)
works regardless of whether the auth path is fully visible to the audience.

**Independent Test**: Inspect the HTTP traffic reaching the stub agent (via tunnel logs or
agent logs). Confirm every `/invoke` request carries an Authorization header with a JWT
issued by the local auth stub, audience `creative-agent` (or `media-agent` / `analytics-
agent`), and `client_id` claim matching `m365-plugin`. Delivers standalone value as an
auditable proof of the auth bridge.

**Acceptance Scenarios**:

1. **Given** the API Plugin auth config points at the stub auth service's OIDC discovery
   endpoint, **When** Copilot triggers any API Plugin action, **Then** the plugin first
   calls `POST /token` on the auth stub using the `m365-plugin` client credentials and
   receives a valid JWT.
2. **Given** a JWT obtained via the `m365-plugin` client, **When** the JWT is inspected,
   **Then** it contains `sub: m365-plugin`, the correct `aud` matching the target agent,
   `iss` matching the stub auth service, and has not expired.
3. **Given** the `m365-plugin` client credentials are changed to invalid values, **When**
   the plugin attempts to call an agent, **Then** the token acquisition fails and the
   agent call is not made (Copilot surfaces an error rather than making an unauthenticated
   request).

---

### User Story 4 — Local Developer Setup: Tunnel + Stub Platform Side-by-Side (Priority: P4)

A developer preparing the workshop wants to run the complete local development environment
in a single session: Docker Compose starts the stub platform, a dev tunnel (or ngrok)
exposes the local ports to the internet, and Teams Toolkit is configured with the tunnel
URLs so that M365 Copilot can reach the local agents.

**Why this priority**: A reproducible local setup is what makes the pattern teachable. If
the setup is undocumented or brittle, the workshop cannot be delivered confidently. It
comes after the core demo (P1–P3) because the setup is in service of those stories.

**Independent Test**: Follow the local development setup guide from a clean environment.
Confirm that after completing the steps, the dev tunnel is active, the stub agents are
reachable via their tunnel URLs, and a direct HTTP call to a tunnel URL returns a valid
agent response. Delivers standalone value as a reproducible workshop-prep checklist.

**Acceptance Scenarios**:

1. **Given** Docker and a tunnel tool (dev tunnel or ngrok) are installed, **When** a
   developer follows the local setup guide, **Then** the stub platform is reachable via
   a publicly accessible tunnel URL, confirmed by a direct HTTP call that returns HTTP 200.
2. **Given** the tunnel URL is known, **When** the developer updates the API Plugin spec
   server URL to the tunnel URL, **Then** M365 Copilot can reach the local stub agents
   without any change to the stub agent code.
3. **Given** the tunnel is stopped, **When** a user tries to invoke the "Open Agents"
   agent in M365 Copilot Chat, **Then** Copilot surfaces a connectivity error rather than hanging
   indefinitely.

---

### Edge Cases

- What happens when the tunnel is restarted and the URL changes? The API Plugin specs
  must be updated with the new tunnel URL and the Teams App Package re-uploaded (or the
  manifest updated in the Developer Portal). The setup guide MUST document this re-upload
  step.
- What happens when a user's intent does not clearly match any of the three agents? The
  Declarative Agent instructions MUST include fallback guidance so Copilot either asks a
  clarifying question or routes to the most plausible agent rather than returning an error.
- What happens when the stub agent is healthy but the tunnel is down? The API Plugin call
  will fail. Copilot MUST surface an error message to the user; the stub agent logs MUST
  NOT show any unauthenticated or malformed requests as a side effect.
- What happens when the JWT issued by the auth stub is refused by the stub agent (e.g.,
  audience mismatch)? The agent returns HTTP 401 and the plugin MUST propagate this as
  an error to Copilot rather than retrying silently.
- What happens when the Teams App Package manifest version is not incremented before
  re-uploading? The Developer Portal may reject the upload or cache the old version.
  The setup guide MUST document the versioning requirement.
- What happens when `m365-plugin` client secret is left at its default value in the
  plugin auth config? The system MUST still function (default creds work in local env),
  but the setup guide MUST note that the secret must be rotated before any non-local use.

## Requirements *(mandatory)*

### Functional Requirements

**Declarative Agent**

- **FR-001**: The feature MUST provide a Declarative Agent manifest named "Open Agents"
  that registers the three stub agent API Plugins as callable actions within M365 Copilot.
- **FR-002**: The Declarative Agent instructions MUST describe each of the three agents
  (Creative, Media, Analytics) with enough detail for Copilot's orchestrator to select
  the appropriate plugin based on the user's prompt intent.
- **FR-003**: The Declarative Agent MUST include a fallback instruction directing Copilot
  to ask a clarifying question when user intent does not match any registered agent.

**API Plugin Specs**

- **FR-004**: The feature MUST provide one API Plugin OpenAPI spec per stub agent (three
  total): `creative-agent-plugin.json`, `media-agent-plugin.json`,
  `analytics-agent-plugin.json`.
- **FR-005**: Each API Plugin spec MUST include `description_for_model` fields on the
  operation and response objects that describe, in plain language, what the action does
  and what the response contains — enabling Copilot to use the response in a grounded
  answer.
- **FR-006**: Each API Plugin spec MUST target the stub agent's `/invoke` endpoint
  (`POST /invoke`) with the standard request body (`prompt`, optional `session_id`) and
  response schema (`agent_name`, `response`, `session_id`).
- **FR-007**: Each API Plugin spec MUST declare the OAuth2 security scheme pointing at
  the stub auth service's token endpoint (discovered via the OIDC discovery document).
- **FR-008**: The server URL in each API Plugin spec MUST be configurable to point at
  the tunnel URL without modifying the stub agent source code.

**Teams App Package**

- **FR-009**: The feature MUST provide a Teams App Package containing: `manifest.json`,
  a color icon (192×192 px), and an outline icon (32×32 px).
- **FR-010**: The `manifest.json` MUST reference the Declarative Agent manifest and all
  three API Plugin specs.
- **FR-011**: The Teams App Package MUST be sideloadable via Teams Toolkit or the Teams
  Developer Portal into a standard M365 tenant that permits custom app uploads.
- **FR-012**: The `manifest.json` version field MUST be incremented on every material
  change to enable re-sideloading without tenant caching conflicts.

**Auth Configuration**

- **FR-013**: The API Plugin auth config MUST use OAuth2 client credentials grant with
  `client_id: m365-plugin` against the stub auth service's token endpoint.
- **FR-014**: The auth config MUST reference the stub auth service's OIDC discovery
  endpoint (`GET /.well-known/openid-configuration`) as the authority, so that swapping
  to a real IdP (Entra ID) requires only a URL change in the config — no code changes.
- **FR-015**: Every call from an API Plugin to a stub agent's `/invoke` endpoint MUST
  include the JWT obtained from the auth stub in the `Authorization: Bearer <token>` header.
- **FR-016**: The `m365-plugin` client MUST already be registered in the stub auth
  service (feature 001 deliverable); this feature MUST NOT require changes to the auth
  stub source code to add this client.

**Local Development Setup**

- **FR-017**: The feature MUST include a local development setup guide documenting the
  exact steps to: start the stub platform, start a tunnel, update plugin spec server
  URLs with the tunnel URL, and sideload the Teams App Package.
- **FR-018**: The setup guide MUST document how to restart the tunnel and re-register the
  new URL without restarting the stub platform.
- **FR-019**: The setup guide MUST include verification steps (specific URLs to check and
  expected responses) that confirm end-to-end connectivity before opening M365 Copilot Chat.

### Key Entities

- **Declarative Agent**: The M365 Copilot agent definition that binds a name ("Open
  Agents"), a system prompt / instructions, and a set of API Plugin actions. Described
  in a JSON manifest. Registered in M365 via the Teams App Package.
- **API Plugin Spec**: An OpenAPI 3.0 document augmented with M365 Copilot-specific
  fields (`description_for_model`, response semantics). One per stub agent. Describes
  how Copilot should call the agent and interpret its response.
- **Teams App Package**: A ZIP archive containing `manifest.json`, icons, and the
  Declarative Agent manifest + API Plugin specs. The unit of deployment into an M365 tenant.
- **Plugin Auth Config**: The OAuth2 configuration embedded in each API Plugin spec
  that tells Copilot how to obtain a token before calling the agent. Points at the
  stub auth service (or any OIDC-compatible IdP).
- **Dev Tunnel / ngrok**: A tunnelling tool that creates a publicly reachable HTTPS URL
  forwarding to a localhost port. Required because M365 Copilot (cloud) must reach the
  stub agents (local laptop).
- **m365-plugin client**: The OAuth2 client credential pre-registered in the stub auth
  service. Used by the API Plugin to obtain JWTs for agent calls.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A workshop presenter can deliver the end-to-end demo — open M365 Copilot Chat, type
  "Create a summer campaign", receive a Creative Agent response — in under 2 minutes from
  a prepared environment (stub platform running, tunnel active, app sideloaded).
- **SC-002**: All three stub agents are reachable and return valid responses via the
  API Plugin integration — confirmed by invoking each agent at least once through M365 Copilot Chat
  before the workshop.
- **SC-003**: Every API Plugin call carries a valid JWT in the Authorization header —
  confirmed by inspecting at least one request in tunnel or agent logs during a test run.
- **SC-004**: The Teams App Package sideloads successfully into a fresh M365 tenant
  (one with no prior version of the app) in under 5 minutes by following only the setup
  guide.
- **SC-005**: The local development setup guide enables a developer with no prior
  knowledge of this feature to reach the "tunnel active + app sideloaded + first M365 Copilot Chat
  response received" state in under 30 minutes.
- **SC-006**: Swapping from the stub auth service to a real IdP (Entra ID) requires
  changes to configuration only — zero changes to API Plugin spec logic, Declarative
  Agent manifest, or stub agent source code — verifiable by inspection.
- **SC-007**: The integration produces no changes to the stub agent source code
  (verifiable by `git diff` against the feature 001 baseline showing no modifications
  to files under `stub-platform/`).

## Assumptions

- The stub platform from feature 001 is fully operational: all four services start via
  `docker compose up`, health checks pass, and the `m365-plugin` client credential is
  pre-registered in the auth stub.
- The developer / workshop presenter has access to an M365 tenant where custom app
  sideloading is permitted (either via Teams Admin Centre policy or a developer tenant).
- A tunnel tool (Microsoft dev tunnel or ngrok) is available in the workshop environment.
  Tunnel stability during a live demo is the presenter's responsibility; the setup guide
  documents the re-registration steps for tunnel restarts.
- The stub auth service issues JWTs with audience values matching each agent's service
  name (`creative-agent`, `media-agent`, `analytics-agent`); the `m365-plugin` client
  is already registered with permission to request these audiences.
- Stub agents perform local JWT validation (RS256, against a known public key) as
  established in feature 001 — no per-request auth stub calls are required.
- The M365 tenant used for the workshop supports M365 Copilot with Declarative Agent
  capability (requires appropriate licencing; not validated by this feature).
- Teams Toolkit CLI or VS Code extension is available for packaging and sideloading;
  manual ZIP upload via the Developer Portal is the fallback.
- No Azure APIM or cloud gateway is required for this feature; the tunnel is the sole
  path from the M365 cloud to the local stub platform.
- Adaptive Cards, rich media responses, and multi-turn conversation state are out of
  scope (addressed in Pattern B).
- Icon assets (color and outline) will be created as simple placeholder images sufficient
  for sideloading; final branding is out of scope for this phase.
