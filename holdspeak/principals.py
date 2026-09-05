"""Authenticated runtime principals and edge authorization (HS-106-02).

Network location is deliberately absent from this module.  A principal comes
from a credential issued by the hub; callers may supply operation payloads,
but never their identity or rights.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Optional


class PrincipalKind(str, Enum):
    OWNER = "owner"
    AGENT = "agent"
    NODE = "node"
    # Internal-only scheduler identity. It has no edge rights and is admitted
    # solely by ParentRunController.start_delegated_schedule.
    SCHEDULER = "scheduler"
    # Narrow runtime identity for an explicitly-issued ambient service.
    SERVICE = "service"
    NONE = "none"


class PrincipalRight(str, Enum):
    OWNER = "owner"
    DECIDE = "decide"
    DELEGATE = "delegate"
    POSTURE = "posture"
    READ = "read"
    AGENT_SUBMIT = "agent.submit"
    AGENT_READ = "agent.read"
    AGENT_USAGE = "agent.usage"
    SELF_REVOKE = "self.revoke"
    NODE_LINK = "node.link"


_RIGHTS: dict[PrincipalKind, frozenset[PrincipalRight]] = {
    PrincipalKind.OWNER: frozenset(PrincipalRight),
    PrincipalKind.AGENT: frozenset(
        {
            PrincipalRight.AGENT_SUBMIT,
            PrincipalRight.AGENT_READ,
            PrincipalRight.AGENT_USAGE,
            PrincipalRight.SELF_REVOKE,
        }
    ),
    PrincipalKind.NODE: frozenset({PrincipalRight.NODE_LINK}),
    PrincipalKind.SCHEDULER: frozenset(),
    PrincipalKind.SERVICE: frozenset(),
    PrincipalKind.NONE: frozenset(),
}


@dataclass(frozen=True)
class Principal:
    kind: PrincipalKind
    identity: str
    allowed_operations: frozenset[tuple[str, int]] = frozenset()
    authority_basis: str = ""

    @property
    def name(self) -> str:
        return self.kind.value

    @property
    def rights(self) -> frozenset[PrincipalRight]:
        return _RIGHTS[self.kind]

    def permits(self, right: PrincipalRight) -> bool:
        return right in self.rights


UNAUTHENTICATED = Principal(PrincipalKind.NONE, "unauthenticated")


@dataclass(frozen=True)
class AgentCredential:
    token: str
    principal: Principal
    expires_at: float
    palette: Optional[frozenset[str]] = None
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    last_used_at: Optional[float] = None


# HS-174 max TTL cap (counsel H2: 30 days).
_MAX_TTL_SECONDS: float = 30 * 24 * 3600.0


def _hash_token(plaintext: str) -> str:
    """SHA-256 hash for credential-at-rest (C4: plaintext only at issue)."""
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


class AgentCredentialStore:
    """In-memory, revocable credentials minted once per supervised process.

    HS-174: credentials store ``sha256(token)`` at rest and compare hashes
    constant-time.  The plaintext token is returned ONLY from ``issue()`` and
    is never stored.  The store is wiped on process restart (persistence
    deferred; see D4 H6).
    """

    def __init__(self, *, clock=time.monotonic) -> None:
        self._lock = threading.RLock()
        self._clock = clock
        # Keyed by sha256(token) -- the plaintext is never stored.
        self._by_hash: dict[str, AgentCredential] = {}
        self._by_identity: dict[str, str] = {}  # identity -> hash
        self._by_id: dict[str, str] = {}  # credential id -> hash
        self._target_to_identity: dict[str, str] = {}
        self._hub_url = "http://127.0.0.1:8765"

    # -- Legacy compat: _by_token property for old callers (read-only). --
    @property
    def _by_token(self) -> dict[str, AgentCredential]:
        return self._by_hash

    @property
    def hub_url(self) -> str:
        with self._lock:
            return self._hub_url

    def set_hub_url(self, url: str) -> None:
        with self._lock:
            self._hub_url = str(url or self._hub_url).rstrip("/")

    def issue(
        self,
        identity: str,
        *,
        ttl_seconds: float = 43_200.0,
        palette: Optional[frozenset[str]] = None,
    ) -> AgentCredential:
        """Mint a new credential.  Returns the credential with the plaintext
        token; the store keeps only the hash (C4)."""
        clean = str(identity or "").strip()
        if not clean:
            raise ValueError("agent identity is required")
        with self._lock:
            self.revoke(clean)
            ttl = min(max(1.0, float(ttl_seconds)), _MAX_TTL_SECONDS)
            plaintext = secrets.token_urlsafe(32)
            token_hash = _hash_token(plaintext)
            cred_id = uuid.uuid4().hex[:16]
            credential = AgentCredential(
                token=token_hash,  # stored form is the hash
                principal=Principal(PrincipalKind.AGENT, clean),
                expires_at=self._clock() + ttl,
                palette=palette,
                id=cred_id,
                last_used_at=None,
            )
            self._by_hash[token_hash] = credential
            self._by_identity[clean] = token_hash
            self._by_id[cred_id] = token_hash
            # Return a copy with the plaintext so the caller can show it once.
            return AgentCredential(
                token=plaintext,
                principal=credential.principal,
                expires_at=credential.expires_at,
                palette=credential.palette,
                id=credential.id,
                last_used_at=credential.last_used_at,
            )

    def derive(self, token: Optional[str]) -> Optional[Principal]:
        """Derive a principal from a bearer token (backward-compat signature)."""
        cred = self.derive_credential(token)
        return cred.principal if cred else None

    def derive_credential(self, token: Optional[str]) -> Optional[AgentCredential]:
        """Derive the full credential from a bearer token.

        Hashes the provided token and compares against stored hashes
        constant-time.  Updates ``last_used_at`` on match.  Returns
        ``None`` on miss or expiry.
        """
        provided = str(token or "")
        if not provided:
            return None
        provided_hash = _hash_token(provided)
        with self._lock:
            # Do not expose dict lookup timing as a credential oracle.
            for stored_hash, credential in list(self._by_hash.items()):
                if credential.expires_at <= self._clock():
                    self.revoke(credential.principal.identity)
                    continue
                if hmac.compare_digest(provided_hash.encode(), stored_hash.encode()):
                    # Touch last_used_at (frozen dataclass -> replace).
                    updated = AgentCredential(
                        token=credential.token,
                        principal=credential.principal,
                        expires_at=credential.expires_at,
                        palette=credential.palette,
                        id=credential.id,
                        last_used_at=self._clock(),
                    )
                    self._by_hash[stored_hash] = updated
                    return updated
        return None

    def bind_target(self, identity: str, *targets: Optional[str]) -> None:
        with self._lock:
            for target in targets:
                clean = str(target or "").strip()
                if clean:
                    self._target_to_identity[clean] = identity

    def revoke(self, identity: str) -> bool:
        clean = str(identity or "").strip()
        with self._lock:
            token_hash = self._by_identity.pop(clean, None)
            if token_hash is None:
                return False
            cred = self._by_hash.pop(token_hash, None)
            if cred:
                self._by_id.pop(cred.id, None)
            stale = [target for target, owner in self._target_to_identity.items() if owner == clean]
            for target in stale:
                self._target_to_identity.pop(target, None)
            return True

    def revoke_by_id(self, credential_id: str) -> bool:
        """Revoke a credential by its id (for the settings face)."""
        clean = str(credential_id or "").strip()
        with self._lock:
            token_hash = self._by_id.get(clean)
            if token_hash is None:
                return False
            cred = self._by_hash.get(token_hash)
            if cred:
                return self.revoke(cred.principal.identity)
        return False

    def list_credentials(self) -> list[AgentCredential]:
        """Return all credentials (including expired) for the settings face.

        ``N CREDENTIALS`` counts all; ``N ACTIVE`` counts non-expired (P2s).
        """
        with self._lock:
            return list(self._by_hash.values())

    def count_active(self) -> int:
        """Count non-expired credentials."""
        now = self._clock()
        with self._lock:
            return sum(1 for c in self._by_hash.values() if c.expires_at > now)

    def revoke_targets(self, targets: Iterable[Optional[str]]) -> bool:
        with self._lock:
            identities = {
                self._target_to_identity.get(str(target or "").strip())
                for target in targets
                if str(target or "").strip()
            }
        revoked = False
        for identity in identities:
            if identity:
                revoked = self.revoke(identity) or revoked
        return revoked


agent_credentials = AgentCredentialStore()


def derive_owner(token: Optional[str], expected: Optional[str]) -> Optional[Principal]:
    if not token or not expected:
        return None
    if hmac.compare_digest(str(token).encode(), str(expected).encode()):
        return Principal(PrincipalKind.OWNER, "owner-session")
    return None


def required_right(method: str, path: str) -> Optional[PrincipalRight]:
    """Return the centralized edge right for one HTTP route.

    Static shell files and explicitly public health/pairing entrances return
    ``None``.  API reads and mutations otherwise belong to the owner unless a
    narrower agent or node protocol right is named here.
    """
    verb = str(method or "GET").upper()
    if path in {"/health", "/api/devices/audio", "/api/mesh/info"}:
        return None
    # HS-174: the MCP HTTP transport accepts AGENT credentials; its own
    # route handler enforces the per-route loopback guard and palette.
    if path == "/api/mcp" and verb == "POST":
        return PrincipalRight.AGENT_SUBMIT
    if path.startswith("/_built") or not path.startswith("/api/"):
        return None
    if (
        path == "/api/decisions"
        or path.startswith("/api/decisions/")
        or path == "/api/memory/search"
    ) and verb == "GET":
        return PrincipalRight.READ
    if path.startswith("/api/delivery/node/") or path.startswith("/api/kernel/executor/"):
        return PrincipalRight.NODE_LINK
    # HS-131-16: the mesh relay legs are a NODE protocol, not an owner API. The
    # right is the narrow gate; `MeshService` additionally requires the principal
    # to BE a node, so an owner token cannot claim, complete, or fail relay work.
    if path.startswith("/api/mesh/relay/"):
        return PrincipalRight.NODE_LINK
    if path == "/api/kernel/submit" and verb == "POST":
        return PrincipalRight.AGENT_SUBMIT
    if path == "/api/kernel/read" or path == "/api/kernel/events":
        return PrincipalRight.AGENT_READ
    if path.startswith("/api/kernel/operations/") and path.endswith("/decide"):
        return PrincipalRight.DECIDE
    if path == "/api/gate/proposals" and verb == "POST":
        return PrincipalRight.AGENT_SUBMIT
    if path.startswith("/api/gate/proposals/") and path.endswith("/decide"):
        return PrincipalRight.DECIDE
    if path.startswith("/api/gate/proposals/") and path.endswith("/receipt"):
        return PrincipalRight.AGENT_USAGE
    if path.startswith("/api/gate/proposals/") and verb == "GET":
        return PrincipalRight.AGENT_READ
    if path == "/api/gate/usage" and verb == "POST":
        return PrincipalRight.AGENT_USAGE
    if path == "/api/principals/self":
        return PrincipalRight.SELF_REVOKE
    if path == "/api/principals/agents" or path.startswith("/api/principals/agents/"):
        return PrincipalRight.DELEGATE
    if path == "/api/authority/control-mode":
        return PrincipalRight.POSTURE
    if path.startswith("/api/authority/grants") and verb != "GET":
        return PrincipalRight.DELEGATE
    return PrincipalRight.OWNER


def refusal(principal: Principal, right: PrincipalRight) -> dict[str, object]:
    return {
        "success": False,
        "error": "principal_right_required",
        "principal": principal.name,
        "principal_identity": principal.identity,
        "missing_right": right.value,
    }
