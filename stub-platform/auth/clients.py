"""
Pre-registered OAuth2 clients for the local auth stub.

These are development-only credentials. They carry no production trust and
MUST NOT be used outside of local development and workshop demos.
"""

REGISTERED_CLIENTS: dict[str, dict] = {
    "demo-client": {
        "secret": "demo-secret",
        "scopes": ["agents.invoke"],
    },
    "m365-plugin": {
        "secret": "plugin-secret",
        "scopes": ["agents.invoke", "openid", "profile"],
    },
}
