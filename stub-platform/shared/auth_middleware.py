"""
JWT validation dependency for stub agents.

Configuration (all via environment variables):
  AGENT_PUBLIC_KEY_PATH  Path to RSA public key PEM file (used when AGENT_JWKS_URI is not set).
                         Default: /keys/public.pem
  AGENT_JWKS_URI         If set, fetch JWKS from this URL and use for validation instead of
                         a static PEM file. Enables IdP swap without code changes.
  OIDC_ISSUER            Expected JWT 'iss' claim. Default: http://localhost:8000
  JWT_AUDIENCE           Expected JWT 'aud' claim. Default: agents
  JWT_ALGORITHM          JWT signing algorithm. Default: RS256

To swap to a real IdP (Entra ID, Okta), update OIDC_ISSUER, JWT_AUDIENCE, and either
AGENT_JWKS_URI (preferred) or AGENT_PUBLIC_KEY_PATH — no code changes required.
"""

import os
from functools import lru_cache

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwk, jwt
from jose.exceptions import JWKError

_bearer_scheme = HTTPBearer(auto_error=False)

# Environment variable defaults
_DEFAULT_PUBLIC_KEY_PATH = "/keys/public.pem"
_DEFAULT_ISSUER = "http://localhost:8000"
_DEFAULT_AUDIENCE = "agents"
_DEFAULT_ALGORITHM = "RS256"


@lru_cache(maxsize=1)
def _load_public_key() -> str:
    """Load RSA public key from PEM file (cached after first load)."""
    key_path = os.environ.get("AGENT_PUBLIC_KEY_PATH", _DEFAULT_PUBLIC_KEY_PATH)
    try:
        with open(key_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        raise RuntimeError(
            f"Public key file not found at '{key_path}'. "
            "Set AGENT_PUBLIC_KEY_PATH or generate keys per stub-platform/keys/README.md."
        )


@lru_cache(maxsize=1)
def _fetch_jwks_keys() -> list[dict]:
    """Fetch JWKS keys from the configured URI (cached after first fetch)."""
    jwks_uri = os.environ.get("AGENT_JWKS_URI")
    if not jwks_uri:
        return []
    try:
        response = httpx.get(jwks_uri, timeout=5.0)
        response.raise_for_status()
        return response.json().get("keys", [])
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch JWKS from '{jwks_uri}': {exc}")


def _get_verification_key(token: str) -> object:
    """
    Return the key to use for verifying this token.
    Uses JWKS URI if configured, otherwise falls back to static PEM file.
    """
    jwks_uri = os.environ.get("AGENT_JWKS_URI")
    if jwks_uri:
        keys = _fetch_jwks_keys()
        # Try to match by kid header if present
        try:
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
        except JWTError:
            kid = None

        for key_data in keys:
            if kid is None or key_data.get("kid") == kid:
                try:
                    return jwk.construct(key_data)
                except JWKError:
                    continue
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No matching key found in JWKS",
        )
    return _load_public_key()


async def verify_jwt_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict:
    """
    FastAPI dependency that validates a Bearer JWT on every request.

    Returns the decoded token payload on success.
    Raises HTTP 401 for all auth failures — missing, expired, invalid, or wrong-key tokens.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    issuer = os.environ.get("OIDC_ISSUER", _DEFAULT_ISSUER)
    audience = os.environ.get("JWT_AUDIENCE", _DEFAULT_AUDIENCE)
    algorithm = os.environ.get("JWT_ALGORITHM", _DEFAULT_ALGORITHM)

    try:
        key = _get_verification_key(token)
        payload = jwt.decode(
            token,
            key,
            algorithms=[algorithm],
            audience=audience,
            issuer=issuer,
        )
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as exc:
        # Distinguish signature failures from other decode errors
        msg = str(exc).lower()
        if "signature" in msg or "verify" in msg:
            detail = "Token signature verification failed"
        else:
            detail = "Invalid token"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
