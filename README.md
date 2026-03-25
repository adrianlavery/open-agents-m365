# 🤖 Open Agents → M365 Integration

> Bring your existing AI agents into Microsoft 365 — without re-platforming.

This repository contains architecture patterns, reference designs, and workshop materials for integrating **open agent platforms** (Python, LangChain/LangGraph, hosted on GCP/AWS) with **Microsoft 365 Copilot**, Teams, Word, PowerPoint, and more.

---

## 🎯 The Core Idea

Your agents are already running. They're already smart. **You don't need to rebuild them to get them into M365.**

M365 Copilot can call your existing agents as API plugins — turning your GCP/AWS agent platform into a first-class M365 experience in days, not months.

---

## 🏗️ Three Integration Patterns

### ⚡ Pattern A — API Plugin *(Recommended Starting Point)*

The lightest-touch option. Your agents stay exactly where they are. M365 Copilot calls them over HTTPS via an OpenAPI spec.

```
M365 Copilot / Teams / Word / PPT
        │
        │  HTTPS (OpenAPI-defined)
        ▼
Azure API Management  ←  auth bridging, rate limiting
        │
        ▼
Your Agents on AWS + GCP  ←  nothing changes here
```

✅ Zero re-platforming  
✅ Works across all M365 surfaces  
✅ Prototype in 1–2 weeks  

---

### 🔀 Pattern B — Azure Agent Gateway *(Hybrid)*

Deploy a thin Python gateway on Azure that bridges M365 and your existing agents. Unlocks richer UX — Adaptive Cards, streaming, Microsoft Graph context.

```
M365 Copilot / Teams
        │  Bot Framework Protocol
        ▼
Azure Gateway (Python — App Service / ACA)
  • Routes to sub-agents
  • Returns Adaptive Cards
  • Blends Microsoft Graph data
        │
        ▼
Your Agents on AWS + GCP  ←  still unchanged
```

✅ Adaptive Cards (interactive UI in Teams)  
✅ Combine M365 user context with agent responses  
✅ Streaming support  

---

### 🏢 Pattern C — Full Azure AI Foundry Re-Platform *(Maximum Investment)*

Rebuild agents natively in Azure AI Foundry for the deepest M365 integration. A strategic, longer-term play.

✅ Deepest native M365 experience  
✅ Azure OpenAI, AI Search, Cosmos DB — fully integrated  
⚠️ Significant effort — this is a migration, not an integration  

---

## 📊 Pattern Comparison

| | ⚡ A: API Plugin | 🔀 B: Azure Gateway | 🏢 C: Full Re-platform |
|---|---|---|---|
| **Client effort** | Low | Low–Medium | High |
| **Time to prototype** | 1–2 weeks | 3–4 weeks | 3–6 months |
| **UX richness** | Text responses | Adaptive Cards + streaming | Full native |
| **Azure spend** | Minimal | Moderate | Significant |
| **Agents stay on GCP/AWS?** | ✅ Yes | ✅ Yes | ❌ Migrated |

---

## 🔐 Auth Architecture

Auth is usually the longest pole. The recommended flow:

```
User in Teams/Copilot
    │  1. SSO via Microsoft identity
    ▼
M365 Copilot
    │  2. Invokes plugin using OAuth against Okta
    ▼
Azure APIM / Gateway
    │  3. Validates Okta JWT
    ▼
Client Agents on AWS/GCP
    │  4. Authorize request and respond
    ▼
Response flows back to user
```

---

## 🦸 The "Super Agent" Pattern in M365

M365 Copilot *already is* a super agent. Map your existing orchestration directly:

```
M365 Copilot (BizChat / Teams / Word)
    │
    ▼
Declarative Agent: "Super Agent"
    ├── 🎨 creative-agent   (API Plugin → GCP)
    ├── 📺 media-agent      (API Plugin → GCP)
    ├── 📈 analytics-agent  (API Plugin → GCP)
    ├── 📚 Knowledge: SharePoint brand guidelines
    └── 🗂️  Knowledge: Microsoft Graph (files, email, calendar)
```

Copilot handles routing based on user intent — you don't need to rebuild your orchestration logic.

---

## 🛠️ Key Technologies

| Technology | Role |
|---|---|
| **M365 Copilot** | The super agent / orchestration surface |
| **Declarative Agents** | Config-driven agent definition (no code) |
| **API Plugins** | How Copilot calls external APIs (OpenAPI-based) |
| **Teams Toolkit** | Dev tooling for build / debug / deploy |
| **M365 Agents SDK** | Code-based agent framework (Bot Framework evolution) |
| **Azure API Management** | API gateway, auth bridging, rate limiting |
| **Azure AI Foundry** | Full agent dev platform (if re-platforming) |
| **Azure AI Search** | RAG over your content |
| **Microsoft Graph** | Access to user's M365 data |
| **Adaptive Cards** | Rich interactive UI in Teams / Copilot |

---

## 📋 Contents

| File | Description |
|---|---|
| [`workshop-prep-summary.md`](./workshop-prep-summary.md) | Full workshop prep: architecture patterns, auth design, talking points, and pattern comparison |

---

## 🚀 Recommended Phased Approach

1. **Phase 1** *(weeks)* — Pattern A: one agent callable from M365 Copilot via API Plugin. Proof of concept, near-zero Azure spend.
2. **Phase 2** *(month)* — Pattern B: Azure Gateway for richer UX, multi-agent routing, Adaptive Cards.
3. **Phase 3** *(quarter)* — Evaluate whether re-platforming specific agents to Azure AI Foundry makes sense based on usage and funding.

---

## 💡 The Bottom Line

> **The client doesn't need to re-platform to get into M365.**  
> API Plugins let their GCP/AWS agents be called from Copilot today.  
> The question is how deep and rich they want the integration to be.
