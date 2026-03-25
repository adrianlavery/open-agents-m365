"""
Auth Stub — local OAuth2/OIDC identity provider for workshop demos.

Endpoints:
  POST /token                          OAuth2 token issuance (client_credentials + authorization_code)
  GET  /authorize                      OAuth2 authorization code flow initiation (stub — auto-approves)
  GET  /.well-known/openid-configuration  OIDC discovery document
  GET  /.well-known/jwks.json          JSON Web Key Set (public key)
  GET  /health                         Health check (no auth)

Environment variables:
  PRIVATE_KEY_PATH      Path to RSA private key PEM.  Default: /keys/private.pem
  PUBLIC_KEY_PATH       Path to RSA public key PEM.   Default: /keys/public.pem
  ISSUER                JWT iss claim base URL.        Default: http://localhost:8000
  AUDIENCE              JWT aud claim.                 Default: agents
  TOKEN_EXPIRY_SECONDS  Token validity in seconds.     Default: 3600
  PORT                  Port to bind.                  Default: 8000
"""

import os
import secrets
import time
from datetime import datetime, timezone

from fastapi import FastAPI, Form, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from jose import jwt
from jose.backends import RSAKey
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
import base64

from clients import REGISTERED_CLIENTS

# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def _get_private_key() -> str:
    path = os.environ.get("PRIVATE_KEY_PATH", "/keys/private.pem")
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        raise RuntimeError(
            f"Private key not found at '{path}'. "
            "Generate keys per stub-platform/keys/README.md."
        )


def _get_public_key_pem() -> str:
    path = os.environ.get("PUBLIC_KEY_PATH", "/keys/public.pem")
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        raise RuntimeError(
            f"Public key not found at '{path}'. "
            "Generate keys per stub-platform/keys/README.md."
        )


def _issuer() -> str:
    return os.environ.get("ISSUER", "http://localhost:8000")


def _audience() -> str:
    return os.environ.get("AUDIENCE", "agents")


def _expiry() -> int:
    return int(os.environ.get("TOKEN_EXPIRY_SECONDS", "3600"))


# ---------------------------------------------------------------------------
# In-memory auth code store  {code: {client_id, redirect_uri, scope, exp}}
# ---------------------------------------------------------------------------

_auth_codes: dict[str, dict] = {}

AUTH_CODE_TTL = 60  # seconds


def _issue_auth_code(client_id: str, redirect_uri: str, scope: str) -> str:
    code = secrets.token_urlsafe(32)
    _auth_codes[code] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "exp": time.time() + AUTH_CODE_TTL,
    }
    return code


def _consume_auth_code(code: str) -> dict | None:
    """Return and delete the auth code entry if valid, None if missing or expired."""
    entry = _auth_codes.pop(code, None)
    if entry is None:
        return None
    if time.time() > entry["exp"]:
        return None
    return entry


# ---------------------------------------------------------------------------
# JWT issuance
# ---------------------------------------------------------------------------

def _issue_token(sub: str, scope: str) -> dict:
    now = int(time.time())
    expiry = _expiry()
    payload = {
        "sub": sub,
        "iss": _issuer(),
        "aud": _audience(),
        "iat": now,
        "exp": now + expiry,
        "scope": scope,
    }
    private_key = _get_private_key()
    access_token = jwt.encode(payload, private_key, algorithm="RS256")
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": expiry,
        "scope": scope,
    }


# ---------------------------------------------------------------------------
# JWKS helper
# ---------------------------------------------------------------------------

def _public_key_to_jwks() -> dict:
    """Convert the RSA public key PEM to a JWKS key object."""
    from cryptography.hazmat.primitives.serialization import load_pem_public_key

    pem = _get_public_key_pem().encode()
    pub_key: RSAPublicKey = load_pem_public_key(pem)
    pub_numbers = pub_key.public_key().public_numbers() if hasattr(pub_key, "public_key") else pub_key.public_numbers()

    def _b64url(n: int, byte_length: int) -> str:
        b = n.to_bytes(byte_length, "big")
        return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

    key_size_bytes = (pub_numbers.n.bit_length() + 7) // 8
    return {
        "kty": "RSA",
        "use": "sig",
        "kid": "stub-dev-key-1",
        "alg": "RS256",
        "n": _b64url(pub_numbers.n, key_size_bytes),
        "e": _b64url(pub_numbers.e, 3),
    }


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Auth Stub",
    description=(
        "Local OAuth2/OIDC identity provider stub for workshop demos. "
        "Issues RS256-signed JWTs. Swappable with Entra ID or Okta via config only."
    ),
    version="1.0.0",
)


@app.get("/health", tags=["ops"])
def health():
    return {"status": "healthy", "service": "auth-stub"}


@app.post("/token", tags=["oauth2"])
def token(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    scope: str = Form(default="agents.invoke"),
    code: str = Form(default=None),
    redirect_uri: str = Form(default=None),
):
    """Issue a JWT access token via client_credentials or authorization_code grant."""
    client = REGISTERED_CLIENTS.get(client_id)
    if client is None or client["secret"] != client_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_client", "error_description": "Unknown client or bad credentials"},
        )

    if grant_type == "client_credentials":
        # Validate requested scopes against allowed scopes
        requested = set(scope.split())
        allowed = set(client["scopes"])
        granted = " ".join(requested & allowed) or "agents.invoke"
        return _issue_token(sub=client_id, scope=granted)

    elif grant_type == "authorization_code":
        if not code or not redirect_uri:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "invalid_request", "error_description": "code and redirect_uri required"},
            )
        entry = _consume_auth_code(code)
        if entry is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "invalid_grant", "error_description": "Authorization code invalid or expired"},
            )
        if entry["client_id"] != client_id or entry["redirect_uri"] != redirect_uri:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "invalid_grant", "error_description": "client_id or redirect_uri mismatch"},
            )
        return _issue_token(sub=client_id, scope=entry["scope"])

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "unsupported_grant_type", "error_description": f"Grant type '{grant_type}' is not supported"},
        )


@app.get("/authorize", tags=["oauth2"])
def authorize(
    response_type: str = Query(...),
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    scope: str = Query(default="agents.invoke"),
    state: str = Query(default=""),
):
    """
    OAuth2 authorization code flow initiation.
    Auto-approves for demo purposes — no login UI required.
    """
    if response_type != "code":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "unsupported_response_type"},
        )
    if client_id not in REGISTERED_CLIENTS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_client"},
        )
    code = _issue_auth_code(client_id=client_id, redirect_uri=redirect_uri, scope=scope)
    location = f"{redirect_uri}?code={code}"
    if state:
        location += f"&state={state}"
    return RedirectResponse(url=location, status_code=302)


@app.get("/.well-known/openid-configuration", tags=["oidc"])
def openid_configuration():
    """OIDC discovery document."""
    base = _issuer()
    return {
        "issuer": base,
        "authorization_endpoint": f"{base}/authorize",
        "token_endpoint": f"{base}/token",
        "jwks_uri": f"{base}/.well-known/jwks.json",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "client_credentials"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "scopes_supported": ["openid", "profile", "agents.invoke"],
    }


@app.get("/.well-known/jwks.json", tags=["oidc"])
def jwks():
    """JSON Web Key Set — public key for JWT signature verification."""
    return {"keys": [_public_key_to_jwks()]}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
