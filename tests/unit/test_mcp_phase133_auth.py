"""Phase 133 auth tests — HS-133-08: the honest handshake."""
import importlib.util
import os
import sys

# Load auth.py directly to avoid the mcp/__init__.py -> server -> tools
# -> families circular-import chain that exists while teammate family
# modules are being wired in parallel.
_AUTH_PATH = os.path.join(
    os.path.dirname(__file__),
    os.pardir,
    os.pardir,
    "holdspeak",
    "mcp",
    "auth.py",
)
_spec = importlib.util.spec_from_file_location("holdspeak.mcp.auth", _AUTH_PATH)
assert _spec and _spec.loader
_auth = importlib.util.module_from_spec(_spec)
sys.modules["holdspeak.mcp.auth"] = _auth
_spec.loader.exec_module(_auth)

MCPAuth = _auth.MCPAuth
resolve_auth = _auth.resolve_auth

from holdspeak.principals import PrincipalKind  # noqa: E402


def test_resolve_auth_no_token_yields_owner_local_mcp():
    """resolve_auth() without HOLDSPEAK_TOKEN yields OWNER / local-mcp."""
    auth = resolve_auth(environ={})
    assert auth.principal.kind is PrincipalKind.OWNER
    assert auth.principal.identity == "local-mcp"


def test_resolve_auth_with_token_yields_owner_mcp_token():
    """resolve_auth() with HOLDSPEAK_TOKEN yields OWNER / mcp-token."""
    auth = resolve_auth(environ={"HOLDSPEAK_TOKEN": "some-secret"})
    assert auth.principal.kind is PrincipalKind.OWNER
    assert auth.principal.identity == "mcp-token"


def test_mcpauth_has_no_url_attribute():
    """MCPAuth no longer carries a url field (removed in HS-133-08)."""
    assert not hasattr(MCPAuth, "url")
    auth = resolve_auth(environ={})
    assert not hasattr(auth, "url")
