
## Workshop Prep: Open Agents → M365 Integration

### 1. Understanding the Client's Likely Current Architecture

Based on the agenda (Python, React, GCP, AWS), the client's agent stack likely looks like:

```
┌──────────────────────────────────────┐
│  Open / Super Agent Platform         │
│  (React Frontend)                    │
└──────────────┬───────────────────────┘
               │
┌──────────────▼───────────────────────┐
│  Agent Orchestration Layer           │
│  (Python — LangChain/LangGraph,     │
│   CrewAI, or custom framework)       │
│  • Routing / intent detection        │
│  • Tool calling / function execution │
│  • Memory / context management       │
└──────────────┬───────────────────────┘
               │
┌──────────────▼───────────────────────┐
│  Multi-Cloud Infrastructure          │
│  • GCP: Vertex AI, Cloud Run / GKE   │
│  • AWS: Bedrock, Lambda / ECS / EKS  │
│  • Shared data + state services      │
│  • Existing platform-specific tools  │
└──────────────────────────────────────┘
```

**Key questions to ask in the workshop:**

- What LLM orchestration framework? (LangChain, LangGraph, Semantic Kernel, custom?)
- What models? (Gemini, Bedrock-hosted models, Claude, GPT via API?)
- How do "Super Agents" compose sub-agents? (Sequential, parallel, router pattern?)
- What's the API contract? (REST, gRPC, streaming SSE?)
- How is auth handled? (OAuth2, API keys, service accounts?)
- What tools/plugins do agents call? (Internal APIs, databases, third-party SaaS?)
- How is conversation state managed? (Stateless per-request, or persistent sessions?)

---

### 2. Three Integration Patterns: GCP Agents → M365

There are three realistic architecture patterns, each with different trade-offs:

---

#### Pattern A: API Plugin (Lightest Touch — Recommended Starting Point)

The client keeps agents on AWS and GCP. M365 Copilot calls them as API plugins via OpenAPI specs.

```
┌─────────────────────────────────────────────────────┐
│  M365 Copilot / Teams / Word / PPT                  │
│                                                      │
│  Declarative Agent                                   │
│  ┌─────────────────────────────────────────┐        │
│  │ Instructions: "You are a creative    │        │
│  │ assistant that can call agents..."   │        │
│  │                                          │        │
│  │ Actions:                                 │        │
│  │  • open-agent (API Plugin)               │        │
│  │  • creative-agent (API Plugin)           │        │
│  │  • Microsoft Graph (built-in)            │        │
│  └──────────────┬──────────────────────────┘        │
└─────────────────┼───────────────────────────────────┘
                  │ HTTPS (OpenAPI-defined)
                  │
┌─────────────────▼───────────────────────────────────┐
│  Azure API Management (APIM)                         │
│  • Auth translation (M365 context → Okta-backed APIs)│
│  • Rate limiting, logging, CORS                      │
│  • OpenAPI spec hosting                              │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│  Client Agent Platform (AWS + GCP)                   │
│  AWS + GCP endpoints                                 │
│  Existing Python agent orchestration                 │
└─────────────────────────────────────────────────────┘
```

**Why this is the best starting point:**
- **Zero re-platforming** — client agents stay on AWS/GCP untouched
- **Copilot orchestrates** — M365 Copilot decides when to invoke client agents based on user intent
- **Works across all M365 surfaces** — Teams, Word, PPT, Excel, Outlook, M365 Copilot Chat
- **Fast to prototype** — days, not months

**What the client needs to provide:**
- REST API endpoints for each agent capability
- OpenAPI 3.0 specs describing those endpoints
- Auth mechanism (OAuth2 preferred for Copilot plugins)

**What Microsoft side needs:**
- Azure API Management (optional but recommended for auth bridging)
- Declarative Agent manifest (JSON config — no code)
- Teams App Package for sideloading/publishing

**Implementation detail — the API Plugin spec:**

```json
// agent-plugin.json
{
  "schema_version": "v2.1",
  "name_for_human": "Creative Agent",
  "name_for_model": "creative_agent",
  "description_for_human": "Access creative AI agents",
  "description_for_model": "Call this plugin when the user wants creative campaign ideas, brand analysis, media planning, or content generation using specialized AI agents.",
  "auth": {
    "type": "oauth",
    "authorization_url": "https://{yourOktaDomain}/oauth2/{authServerId}/v1/authorize",
    "token_url": "https://{yourOktaDomain}/oauth2/{authServerId}/v1/token",
    "scope": "openid profile email agents.invoke"
  },
  "api": {
    "type": "openapi",
    "url": "https://agents.azure-api.net/openapi.json"
  }
}
```

---

#### Pattern B: Azure-Hosted Agent Gateway (Hybrid)

Deploy a thin orchestration layer on Azure that bridges M365 and AWS/GCP agents.

```
┌──────────────────────────────────────────────────────┐
│  M365 Copilot / Teams / Word / PPT                   │
└──────────────┬───────────────────────────────────────┘
               │ Bot Framework Protocol
┌──────────────▼───────────────────────────────────────┐
│  Azure (Microsoft 365 Agents SDK)                     │
│                                                       │
│  Agent Gateway (Python — Azure App Service / ACA)     │
│  ┌─────────────────────────────────────────────┐     │
│  │  • Receives M365 messages via Bot Framework   │     │
│  │  • Routes to appropriate agent               │     │
│  │  • Translates response → Adaptive Cards       │     │
│  │  • Handles auth (M365 context ↔ Okta)        │     │
│  │  • Optionally adds Azure AI Search context    │     │
│  └──────────────┬──────────────────────────────┘     │
└─────────────────┼────────────────────────────────────┘
                  │ HTTPS
┌─────────────────▼────────────────────────────────────┐
│  Client Agent Platform (AWS + GCP)                    │
│  Existing agents unchanged                            │
└──────────────────────────────────────────────────────┘
```

**Advantages over Pattern A:**
- Richer UX — can return **Adaptive Cards** (interactive UI in Teams/Copilot)
- Can combine **Microsoft Graph data** (user context, documents, calendar) with client agent calls
- Can add **Azure AI Search** over the client's content for RAG
- Streaming support
- Can implement **Super Agent** pattern in Azure that orchestrates multiple client sub-agents

**Azure resources needed:**
- Azure App Service or Azure Container Apps (host the gateway)
- Azure Bot Service registration
- Azure AI Search (optional, for RAG over client content)
- Azure Key Vault (store GCP service account creds)

---

#### Pattern C: Full Re-Platform to Azure AI Foundry (Maximum Investment)

Rebuild agents natively in Azure AI Foundry (formerly Azure AI Studio).

```
┌──────────────────────────────────────────────────────┐
│  M365 Copilot / Teams / Word / PPT                   │
└──────────────┬───────────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────────┐
│  Azure AI Foundry                                     │
│  ┌────────────────────────────────────────────┐      │
│  │  Super Agent (Prompt Flow / Agent Svc)      │      │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐   │      │
│  │  │Creative  │ │Media     │ │Analytics │   │      │
│  │  │Sub-Agent │ │Sub-Agent │ │Sub-Agent │   │      │
│  │  └──────────┘ └──────────┘ └──────────┘   │      │
│  │                                             │      │
│  │  Azure OpenAI (GPT-4o / GPT-4.1)           │      │
│  │  Azure AI Search (RAG)                      │      │
│  │  Azure Cosmos DB (state)                    │      │
│  └────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────┘
```

**When this makes sense:**
- Microsoft is funding the Azure consumption
- Client wants deepest M365 integration (inline Copilot experiences, Office add-ins)
- Client wants to use Azure OpenAI models instead of Vertex AI
- Long-term strategic play

**Significant effort** — this is a migration project, not an integration.

---

### 3. Pattern Comparison Matrix

| Dimension | A: API Plugin | B: Azure Gateway | C: Full Re-platform |
|---|---|---|---|
| **Client effort** | Low (expose REST APIs + OpenAPI) | Low-Medium (no agent changes) | High (rebuild agents) |
| **Microsoft effort** | Low (declarative config) | Medium (build gateway) | High (infra + dev) |
| **Time to prototype** | 1-2 weeks | 3-4 weeks | 3-6 months |
| **M365 surface coverage** | All (Copilot, Teams, Word, PPT, Excel) | All | All |
| **UX richness** | Text responses only | Adaptive Cards, streaming | Full native |
| **Runs on Azure?** | APIM only (agents stay on AWS/GCP) | Gateway on Azure, agents on AWS/GCP | Fully Azure |
| **Funding implication** | Minimal Azure spend | Moderate Azure spend | Significant Azure spend |
| **GCP dependency** | Retained | Retained | Eliminated |

---

### 4. The "Super Agent" Architecture in M365

For the "Super Agent" concept (an orchestrator that routes to specialized sub-agents), there's a clean M365 mapping:

```
M365 Copilot (M365 Copilot Chat / Teams / Word / PPT)
    │
    ▼
Declarative Agent: "Super Agent"
    │
    ├── Action: creative-agent  (API Plugin → GCP)
    ├── Action: media-agent     (API Plugin → GCP)  
    ├── Action: analytics-agent (API Plugin → GCP)
    ├── Knowledge: SharePoint site with brand guidelines
    └── Knowledge: Microsoft Graph (user's files, emails, calendar)
```

M365 Copilot **already is** a super agent — it has built-in reasoning to decide which action/plugin to call based on user intent. The client doesn't need to rebuild their orchestration; Copilot handles it.

Alternatively, if the client's Super Agent has **custom routing logic** that Copilot can't replicate, use Pattern B and keep the orchestration in the gateway.

---

### 5. Auth Architecture (Critical Detail)

This is usually the hardest part. Here's the recommended flow:

```
User in Teams/Copilot
    │
    │ 1. User authenticates in M365 (SSO in Microsoft context)
    ▼
M365 Copilot
    │
    │ 2. Copilot invokes plugin using OAuth against Okta
    ▼
Azure APIM / Gateway (optional)
    │
    │ 3. Validates Okta JWT (or passes through to backend)
    ▼
Client Agents on AWS/GCP
    │
    │ 4. Validate Okta token and authorize request
    ▼
Response flows back up
```

**Key decisions to discuss:**
- Does the client want per-user auth (user identity to AWS/GCP) or service-to-service via Okta clients?
- Will AWS and GCP agent runtimes validate Okta JWTs directly, or via a central gateway?
- Are Okta app integrations/scopes already defined for each agent capability?

---

### 6. Specific Technical Skills Needed

| Role | Microsoft Side | Client Side |
|---|---|---|
| **M365 Platform** | Teams Toolkit, Declarative Agents, API Plugin spec | — |
| **Auth** | Plugin OAuth configuration, APIM policies | Okta app integration, JWT validation in AWS/GCP |
| **Agent Dev** | M365 Agents SDK (if Pattern B) | Python agent framework expertise |
| **Cloud Infra** | Azure APIM, App Service/ACA | GCP Cloud Run/GKE |
| **Frontend** | Adaptive Cards (if Pattern B) | React (existing UI) |
| **API Design** | OpenAPI spec review | OpenAPI spec authoring |

---

### 7. Recommended Workshop Talking Points

1. **Start with a demo ask**: "Can we see an agent invoked via REST API today?" — if yes, Pattern A is immediately viable.

2. **Define the MVP surface**: Recommend starting with **Teams + M365 Copilot Chat** — these have the richest plugin support. Word/PPT/Excel Copilot support for plugins is more constrained.

3. **Auth is the longest pole**: Get clarity on the client's current auth model early. Everything else is configuration.

4. **Propose a phased approach**:
   - **Phase 1** (weeks): Pattern A — API Plugin. One agent callable from M365 Copilot. Proof of concept.
   - **Phase 2** (month): Pattern B — Azure Gateway. Richer UX, multi-agent routing, Adaptive Cards.
   - **Phase 3** (quarter): Evaluate whether re-platforming specific agents to Azure AI Foundry makes sense based on usage patterns and funding.

5. **Funding hook**: Pattern A is nearly zero Azure spend. Pattern B is moderate (App Service + APIM). Pattern C is significant. This gives Microsoft clear decision points for resource allocation.

6. **Ask the client**: "What does the user journey look like today?" Get them to walk through a real user flow end-to-end — this reveals the API contracts you'll need to wrap.

---

### 8. Quick Reference: Key Microsoft Technologies

| Technology | Role in This Architecture |
|---|---|
| **M365 Copilot** | The "super agent" / orchestration surface |
| **Declarative Agents** | Config-driven agent definition (no code) |
| **API Plugins** | How Copilot calls external APIs (OpenAPI-based) |
| **Teams Toolkit** | Dev tooling for building/debugging/deploying |
| **M365 Agents SDK** | Code-based agent framework (Bot Framework evolution) |
| **Azure API Management** | API gateway, auth bridging, rate limiting |
| **Azure AI Foundry** | Full agent development platform (if re-platforming) |
| **Azure AI Search** | RAG over client content |
| **Entra ID** | Identity and auth |
| **Microsoft Graph** | Access to user's M365 data (files, email, calendar) |
| **Adaptive Cards** | Rich interactive UI in Teams/Copilot |

This should give you a strong technical foundation for the workshop. The key message: **the client doesn't need to re-platform to get into M365 — API Plugins let their GCP agents be called from Copilot today.** The question is how deep/rich they want the integration to be.
