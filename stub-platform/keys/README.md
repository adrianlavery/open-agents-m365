# Dev RSA Key Pair

This directory holds the RSA 2048-bit key pair used by the local auth stub to sign JWTs
and by agents to validate them. **These files are gitignored and must be generated locally.**

## Generate the key pair

Run these commands from the `stub-platform/` directory:

```bash
# Generate 2048-bit RSA private key
openssl genrsa -out keys/private.pem 2048

# Extract the public key
openssl rsa -in keys/private.pem -pubout -out keys/public.pem
```

## ⚠️ Important

- **Never commit** `private.pem` or `public.pem` to source control.
- These are **development-only** keys. They carry no production trust.
- Regenerate freely if lost — just restart services after regenerating.
- Both files are required before any service will start.

## Files expected

| File          | Used by             | Purpose                                 |
|--------------|---------------------|-----------------------------------------|
| `private.pem` | Auth stub           | Signs JWTs (RS256)                      |
| `public.pem`  | All three agents    | Validates JWT signatures locally        |
| `public.pem`  | Auth stub (JWKS)    | Served at `/.well-known/jwks.json`      |
