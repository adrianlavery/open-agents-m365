# API Contract: Auth Stub Service

**Feature**: `001-stub-agent-platform`
**Version**: `1.0.0`
**Service**: Auth Stub (`http://localhost:8000`)

---

## Purpose

The auth stub is a local stand-in for a production OIDC-compliant Identity Provider (IdP)
such as Okta, Microsoft Entra ID, or Auth0. It issues RS256-signed JWTs and exposes standard
OIDC discovery endpoints. When this stub is replaced with a real IdP in later features,
**only configuration changes are required in the agent services** — no code changes.

---

## Endpoints

### POST /token — Issue JWT Token

Issues a signed JWT. Supports `client_credentials` and `authorization_code` grant types.

**Request** (`application/x-www-form-urlencoded`):

| Parameter       | Required | Description                                               |
|----------------|----------|-----------------------------------------------------------|
| `grant_type`    | Yes      | `client_credentials` or `authorization_code`              |
| `client_id`     | Yes      | Registered client identifier                              |
| `client_secret` | Yes      | Client secret                                             |
| `scope`         | No       | Space-separated scopes. Default: `agents.invoke`          |
| `code`          | Conditional | Required for `authorization_code` grant                |
| `redirect_uri`  | Conditional | Required for `authorization_code` grant                |

**Pre-registered dev clients**:

| `client_id`    | `client_secret`   | Allowed scopes                              |
|---------------|-------------------|---------------------------------------------|
| `demo-client`  | `demo-secret`     | `agents.invoke`                             |
| `m365-plugin`  | `plugin-secret`   | `agents.invoke openid profile`              |

**Response (200 OK)**:
```json
{
  "access_token": "<RS256-signed JWT>",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "agents.invoke"
}
```

**Error responses**:

| Status | Condition                      | Body                                              |
|--------|-------------------------------|---------------------------------------------------|
| 400    | Missing required parameter     | `{"error": "invalid_request", "error_description": "..."}` |
| 401    | Unknown client or bad secret   | `{"error": "invalid_client", "error_description": "..."}` |
| 400    | Unsupported grant type         | `{"error": "unsupported_grant_type", "error_description": "..."}` |
| 400    | Invalid/expired auth code      | `{"error": "invalid_grant", "error_description": "..."}` |

---

### GET /authorize — Authorization Code Flow Initiation

Simulates the OAuth2 authorization endpoint. For workshop demo purposes, this endpoint
auto-approves the request and returns a short-lived auth code without requiring a user
login UI.

**Query parameters**:

| Parameter       | Required | Description                                    |
|----------------|----------|------------------------------------------------|
| `response_type` | Yes      | Must be `code`                                 |
| `client_id`     | Yes      | Registered client identifier                   |
| `redirect_uri`  | Yes      | Redirect destination                           |
| `scope`         | No       | Requested scopes                               |
| `state`         | No       | CSRF protection value (echoed back)            |

**Response**: HTTP 302 redirect to `redirect_uri?code=<auth_code>&state=<state>`

Auth codes are valid for 60 seconds and single-use.

---

### GET /.well-known/openid-configuration — OIDC Discovery

Returns the OIDC metadata document. This is the primary mechanism enabling IdP swappability:
agents are configured with only `OIDC_ISSUER`, and they fetch this document to discover
the token endpoint, JWKS URI, and supported algorithms.

**Response (200 OK)**:
```json
{
  "issuer": "http://localhost:8000",
  "authorization_endpoint": "http://localhost:8000/authorize",
  "token_endpoint": "http://localhost:8000/token",
  "jwks_uri": "http://localhost:8000/.well-known/jwks.json",
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code", "client_credentials"],
  "subject_types_supported": ["public"],
  "id_token_signing_alg_values_supported": ["RS256"],
  "scopes_supported": ["openid", "profile", "agents.invoke"]
}
```

---

### GET /.well-known/jwks.json — JSON Web Key Set

Returns the public key(s) used to sign JWTs. Agents use this endpoint (or a static public
key file) to validate incoming token signatures locally — no per-request network call needed.

**Response (200 OK)**:
```json
{
  "keys": [
    {
      "kty": "RSA",
      "use": "sig",
      "kid": "stub-dev-key-1",
      "alg": "RS256",
      "n": "<Base64url-encoded modulus>",
      "e": "AQAB"
    }
  ]
}
```

---

### GET /health — Health Check

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "service": "auth-stub"
}
```

---

## JWT Structure

All tokens issued by the auth stub have the following structure:

**Header**:
```json
{
  "alg": "RS256",
  "typ": "JWT",
  "kid": "stub-dev-key-1"
}
```

**Payload (client_credentials example)**:
```json
{
  "sub": "demo-client",
  "iss": "http://localhost:8000",
  "aud": "agents",
  "iat": 1711361538,
  "exp": 1711365138,
  "scope": "agents.invoke"
}
```

---

## IdP Swappability: How to Replace the Auth Stub

When moving from the local auth stub to a real IdP (Entra ID, Okta), update these
environment variables on each agent service — **no code changes**:

| Env Var               | Local Dev Value              | Real IdP Value (example)                               |
|-----------------------|-----------------------------|---------------------------------------------------------|
| `OIDC_ISSUER`         | `http://localhost:8000`     | `https://login.microsoftonline.com/{tenant-id}/v2.0`   |
| `AGENT_JWKS_URI`      | *(unset — uses static key)* | `https://login.microsoftonline.com/{tenant-id}/discovery/v2.0/keys` |
| `AGENT_PUBLIC_KEY_PATH` | `/keys/public.pem`        | *(unset — use JWKS URI instead)*                       |
| `JWT_AUDIENCE`        | `agents`                   | `api://{app-registration-client-id}`                   |

---

## Example curl: Full Client Credentials Flow

```bash
# Get a token
curl -s -X POST http://localhost:8000/token \
  -d "grant_type=client_credentials" \
  -d "client_id=demo-client" \
  -d "client_secret=demo-secret" \
  -d "scope=agents.invoke"

# Inspect the OIDC discovery document
curl -s http://localhost:8000/.well-known/openid-configuration | jq .

# Fetch the public key set
curl -s http://localhost:8000/.well-known/jwks.json | jq .
```
