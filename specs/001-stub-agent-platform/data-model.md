# Data Model: Local Stub Agent Platform

**Feature**: `001-stub-agent-platform`
**Date**: 2026-03-25

---

## Entities

### InvokeRequest

The standard input payload accepted by every stub agent's `POST /invoke` endpoint.

| Field        | Type             | Required | Constraints                                     |
|-------------|-----------------|----------|-------------------------------------------------|
| `prompt`     | string           | Yes      | Non-null; empty string is valid (stub returns default response) |
| `session_id` | string (UUID)    | No       | If omitted, agent generates a new UUID v4       |

**Validation rules**:
- `prompt` MUST be present in the JSON body (missing key = HTTP 422 Unprocessable Entity).
- `session_id`, if provided, MUST be a non-empty string (format not enforced by stub).

---

### InvokeResponse

The standard output payload returned by every stub agent's `POST /invoke` endpoint.

| Field        | Type   | Always Present | Notes                                              |
|-------------|--------|----------------|----------------------------------------------------|
| `agent_name` | string | Yes            | Fixed per agent: `creative-agent`, `media-agent`, `analytics-agent` |
| `response`   | string | Yes            | Mock domain-specific text response                 |
| `session_id` | string | Yes            | Echoed from request, or newly generated UUID v4    |

---

### HealthResponse

Returned by `GET /health` on all four services (agents + auth stub).

| Field     | Type   | Value      |
|----------|--------|------------|
| `status`  | string | `"healthy"` |
| `service` | string | Service name (e.g., `"creative-agent"`, `"auth-stub"`) |

---

### TokenRequest

The OAuth2 token request payload for `POST /token` on the auth stub.

| Field          | Type   | Required for client_credentials | Required for auth_code |
|---------------|--------|--------------------------------|------------------------|
| `grant_type`   | string | Yes (`client_credentials`)     | Yes (`authorization_code`) |
| `client_id`    | string | Yes                            | Yes                    |
| `client_secret`| string | Yes                            | Yes                    |
| `scope`        | string | No (defaults to `agents.invoke`) | No                  |
| `code`         | string | No                             | Yes                    |
| `redirect_uri` | string | No                             | Yes                    |

Delivered as `application/x-www-form-urlencoded` per OAuth2 spec.

---

### TokenResponse

Returned by `POST /token` on a successful grant.

| Field          | Type    | Notes                                       |
|---------------|---------|---------------------------------------------|
| `access_token` | string  | RS256-signed JWT                            |
| `token_type`   | string  | Always `"Bearer"`                           |
| `expires_in`   | integer | Seconds until expiry (default: 3600)        |
| `scope`        | string  | Space-separated granted scopes              |

---

### JWT Claims (inside `access_token`)

| Claim   | Type    | Description                                        |
|--------|---------|----------------------------------------------------|
| `sub`   | string  | Subject — `client_id` for client credentials; user ID for auth code |
| `iss`   | string  | Issuer — auth stub base URL (e.g., `http://localhost:8000`) |
| `aud`   | string  | Audience — `agents` (configurable)                 |
| `exp`   | integer | Unix timestamp — issued time + `expires_in`        |
| `iat`   | integer | Unix timestamp — time of issuance                  |
| `scope` | string  | Space-separated granted scopes                     |

---

### OIDCConfiguration

Returned by `GET /.well-known/openid-configuration` on the auth stub.

| Field                    | Type     | Value (local dev)                             |
|--------------------------|----------|-----------------------------------------------|
| `issuer`                 | string   | `http://localhost:8000`                       |
| `authorization_endpoint` | string   | `http://localhost:8000/authorize`             |
| `token_endpoint`         | string   | `http://localhost:8000/token`                 |
| `jwks_uri`               | string   | `http://localhost:8000/.well-known/jwks.json` |
| `response_types_supported` | array  | `["code"]`                                    |
| `grant_types_supported`  | array    | `["authorization_code", "client_credentials"]` |
| `subject_types_supported`| array    | `["public"]`                                  |
| `id_token_signing_alg_values_supported` | array | `["RS256"]`                  |
| `scopes_supported`       | array    | `["openid", "profile", "agents.invoke"]`      |

---

### JWKS (JSON Web Key Set)

Returned by `GET /.well-known/jwks.json` on the auth stub.

Standard JWKS document containing the public RSA key used to sign tokens. Each key entry:

| Field | Description                                      |
|-------|--------------------------------------------------|
| `kty` | Key type: `"RSA"`                               |
| `use` | Key use: `"sig"`                                |
| `kid` | Key ID: `"stub-dev-key-1"` (fixed for dev)      |
| `alg` | Algorithm: `"RS256"`                            |
| `n`   | RSA public modulus (Base64url-encoded)           |
| `e`   | RSA public exponent (Base64url-encoded)          |

---

## State Transitions

The stub platform is **stateless** — no session state is persisted between requests.

```
Request arrives at agent
    │
    ├─ No Authorization header?  → HTTP 401 {"detail": "Missing bearer token"}
    ├─ Invalid JWT format?        → HTTP 401 {"detail": "Invalid token"}
    ├─ JWT signature invalid?     → HTTP 401 {"detail": "Token signature verification failed"}
    ├─ JWT expired?               → HTTP 401 {"detail": "Token has expired"}
    └─ JWT valid?
         │
         └─ POST /invoke
              ├─ `prompt` missing? → HTTP 422 (Pydantic validation error)
              └─ Valid request?    → HTTP 200 InvokeResponse
```

---

## Configuration Model

Each agent service is configured entirely via environment variables. No config files required
at runtime. All variables have defaults suitable for local development.

### Agent Services (Creative, Media, Analytics)

| Env Var                  | Default                            | Description                                  |
|--------------------------|-----------------------------------|----------------------------------------------|
| `PORT`                   | 8001 / 8002 / 8003                | Port to bind                                 |
| `AGENT_NAME`             | `creative-agent` etc.             | Value returned in `agent_name` response field |
| `JWT_ALGORITHM`          | `RS256`                           | JWT signing algorithm to expect              |
| `JWT_AUDIENCE`           | `agents`                          | Expected `aud` claim value                   |
| `OIDC_ISSUER`            | `http://localhost:8000`           | Expected `iss` claim value                   |
| `AGENT_PUBLIC_KEY_PATH`  | `/keys/public.pem`                | Path to RSA public key PEM (static mode)     |
| `AGENT_JWKS_URI`         | *(unset)*                         | If set, use JWKS URI instead of static key   |

### Auth Stub

| Env Var                  | Default                            | Description                                  |
|--------------------------|-----------------------------------|----------------------------------------------|
| `PORT`                   | `8000`                            | Port to bind                                 |
| `ISSUER`                 | `http://localhost:8000`           | JWT `iss` claim                              |
| `AUDIENCE`               | `agents`                          | JWT `aud` claim                              |
| `TOKEN_EXPIRY_SECONDS`   | `3600`                            | Token validity duration                      |
| `PRIVATE_KEY_PATH`       | `/keys/private.pem`               | Path to RSA private key PEM                  |
| `PUBLIC_KEY_PATH`        | `/keys/public.pem`                | Path to RSA public key PEM (for JWKS)        |
