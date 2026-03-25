<!--
SYNC IMPACT REPORT
==================
Version change: (new) → 1.0.0
New constitution — all sections created from scratch.

Modified principles: N/A (initial ratification)
Added sections:
  - Core Principles (6 principles)
  - Technology Constraints
  - Workshop Workflow
  - Governance

Removed sections: N/A

Templates checked:
  ✅ .specify/templates/plan-template.md — Constitution Check section is placeholder-driven; no update required.
  ✅ .specify/templates/spec-template.md — Requirements section uses MUST language consistent with principles; no update required.
  ✅ .specify/templates/tasks-template.md — Task structure is generic and compatible; no update required.

Deferred TODOs: None
-->

# Open Agents M365 Constitution

## Core Principles

### I. API-First Integration

All agent capabilities MUST be exposed as REST APIs with complete OpenAPI 3.0 specifications.
Proprietary protocols, binary RPC, or undocumented endpoints are prohibited.

- Every agent capability MUST have a corresponding OpenAPI 3.0 spec before it can be surfaced in M365.
- API contracts MUST be versioned and backward-compatible within a major version.
- OpenAPI specs MUST be hosted and machine-readable (e.g., via Azure APIM or a public endpoint).

**Rationale**: M365 Copilot invokes external capabilities exclusively as API Plugins, which require
OpenAPI 3.0 specs. Proprietary interfaces create lock-in and block the no-re-platforming goal.

### II. Zero Re-Platforming

Existing agent workloads running on AWS and GCP MUST remain untouched by integration work.
Integration layers (Azure APIM, M365 Agents SDK gateway) MUST bridge into M365 without
requiring any changes to client agent code, infrastructure, or deployment pipelines.

- PRs that modify client-side agent code solely to satisfy M365 requirements MUST be rejected.
- All translation, auth bridging, and protocol adaptation MUST occur on the Microsoft/Azure side.

**Rationale**: The client's agents represent significant existing investment. Requiring code changes
creates risk, delays, and undermines the core value proposition of the integration.

### III. Progressive Integration Depth

Integration MUST follow a phased approach, advancing only when the current phase delivers
standalone, demonstrable value:

- **Phase 1 — Pattern A (API Plugin)**: One or more agents callable from M365 Copilot via API Plugin.
  Target: working proof-of-concept within weeks. Near-zero Azure spend.
- **Phase 2 — Pattern B (Azure Gateway)**: Richer UX via Azure-hosted gateway — Adaptive Cards,
  streaming, Microsoft Graph context blending, multi-agent routing.
- **Phase 3 — Pattern C (Full Re-platform)**: Selective migration of agents to Azure AI Foundry
  where strategic fit and funding justify it.

Each phase MUST be independently deployable and demonstrable before Phase N+1 begins.

**Rationale**: Phased delivery reduces risk, enables early stakeholder validation, and provides clear
decision points for resource allocation and funding conversations.

### IV. Auth as First-Class Concern

OAuth2/OIDC MUST be the authentication mechanism at every integration boundary.
No API keys in production environments.

- JWT tokens MUST be validated at every service boundary (APIM, gateway, client agents).
- SSO bridging between M365 identity (Entra ID) and client identity (Okta) MUST be explicitly
  designed and documented before any integration pattern is implemented.
- Per-user identity propagation vs. service-to-service auth MUST be decided and documented per
  integration pattern.
- Auth flows MUST be included in every integration pattern spec (diagrams required).

**Rationale**: Auth is consistently the longest-lead item in cross-platform integrations. Treating it
as an afterthought causes rework. Clear decisions early prevent security gaps and deployment blockers.

### V. M365-Native UX

All user-facing integration surfaces MUST be delivered through M365 Copilot, Microsoft Teams, and
Office applications (Word, PowerPoint, Excel, Outlook). Standalone UIs that bypass M365 are out
of scope for this project.

- Integration MUST use M365-native constructs: Declarative Agents, API Plugins, Adaptive Cards,
  and/or the M365 Agents SDK.
- Response formats MUST be appropriate to the M365 surface (e.g., Adaptive Cards in Teams,
  text responses in Copilot Chat where cards are not supported).
- No new standalone web or desktop UIs MUST be created as deliverables of this project.

**Rationale**: The goal is to bring agents *into* M365 — not to build adjacent experiences. M365-native
delivery maximises reach across all surfaces (Teams, Word, PPT, Excel, Outlook, M365 Copilot Chat) with a
single integration.

### VI. Documentation-Driven Development

Every integration pattern, auth flow, and architecture decision MUST be fully documented as
workshop-ready content before implementation begins.

- A spec (including auth flow diagram and API contract example) MUST exist and be reviewed by
  both Microsoft and client stakeholders before implementation of any pattern starts.
- Architecture Decision Records (ADRs) MUST be written for any non-obvious technology choice.
- Workshop materials (diagrams, talking points, pattern comparisons) MUST be kept current with
  the implementation state.

**Rationale**: This project is simultaneously a reference implementation and workshop content.
Documentation that lags implementation cannot be used to guide client workshops. Writing docs first
also surfaces design issues before code is written.

## Technology Constraints

The following technology choices are fixed for this project and MUST NOT be substituted without a
formal constitution amendment.

### Microsoft / Azure Side

- **Azure API Management (APIM)** — API gateway, auth bridging, OpenAPI spec hosting, rate limiting.
- **M365 Agents SDK** — Code-based agent framework for Pattern B gateway implementation.
- **Teams Toolkit** — Dev tooling for building, debugging, and deploying M365 integrations.
- **Azure AI Foundry** — Agent development platform for Pattern C re-platform scenarios.
- **Entra ID** — Microsoft identity platform; source of M365 user identity tokens.

### Client / Multi-Cloud Side

- **Python orchestration** — LangChain, LangGraph, or CrewAI (existing client framework).
- **React frontend** — Existing client UI (not a deliverable of this project).
- **GCP**: Vertex AI for model serving; Cloud Run / GKE for agent hosting.
- **AWS**: Amazon Bedrock for model serving; Lambda / ECS / EKS for agent hosting.

### Shared / Cross-Cutting

- **OpenAPI 3.0** — Mandatory API specification format.
- **OAuth2 / OIDC** — Mandatory authentication protocol.
- **REST / HTTPS** — Mandatory transport and API style.
- **Adaptive Cards** — Mandatory rich UX format for Teams surfaces.

## Workshop Workflow

All feature and integration work in this project MUST follow this workflow before implementation:

1. **Discovery** — Begin with a client architecture review session. Capture current API contracts,
   auth model, agent orchestration framework, and cloud topology.
2. **Spec per Pattern** — Each integration pattern (A, B, C) MUST have its own spec before
   implementation begins. Specs MUST include:
   - Auth flow diagrams (sequence diagrams at minimum).
   - API contract examples (request/response with headers).
   - Pattern comparison rationale (why this pattern for this client context).
3. **Stakeholder Review** — Specs MUST be reviewed and approved by both Microsoft and client
   stakeholders before implementation begins. No exceptions.
4. **Implementation** — Follow the tasks defined in the feature's `tasks.md`.
5. **Workshop Validation** — Implementation artifacts MUST be validated as workshop-ready
   (reproducible, documented, demonstrable) before the pattern is considered complete.

## Governance

This constitution supersedes all other development practices and guidelines for the
Open Agents M365 project.

- All specs, plans, and tasks MUST be checked for compliance with the Core Principles before
  work begins (Constitution Check gate in plan.md).
- Amendments require: written rationale, version increment per semantic versioning rules
  (MAJOR for principle removals/redefinitions, MINOR for additions, PATCH for clarifications),
  and stakeholder acknowledgement.
- Compliance review MUST occur at the start of each integration pattern (Phase gate).
- This file is the authoritative source of truth. In case of conflict with any other document,
  this constitution takes precedence.

**Version**: 1.0.0 | **Ratified**: 2025-03-25 | **Last Amended**: 2026-03-25
