"""Authenticated runtime principals and edge authorization (HS-106-02).

Network location is deliberately absent from this module.  A principal comes
from a credential issued by the hub; callers may supply operation payloads,
but never their identity or rights.
"""
from __future__ import annotations

import hmac
import secrets
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional


class PrincipalKind(str, Enum):
    OWNER = "owner"
    AGENT = "agent"
    NODE = "node"
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
    PrincipalKind.NONE: frozenset(),
}


@dataclass(frozen=True)
class Principal:
    kind: PrincipalKind
    identity: str

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


class AgentCredentialStore:
    """In-memory, revocable credentials minted once per supervised process."""

    def __init__(self, *, clock=time.monotonic) -> None:
        self._lock = threading.RLock()
        self._clock = clock
        self._by_token: dict[str, AgentCredential] = {}
        self._by_identity: dict[str, str] = {}
        self._target_to_identity: dict[str, str] = {}
        self._hub_url = "http://127.0.0.1:8765"

    @property
    def hub_url(self) -> str:
        with self._lock:
            return self._hub_url

    def set_hub_url(self, url: str) -> None:
        with self._lock:
            self._hub_url = str(url or self._hub_url).rstrip("/")

    def issue(self, identity: str, *, ttl_seconds: float = 43_200.0) -> AgentCredential:
        clean = str(identity or "").strip()
        if not clean:
            raise ValueError("agent identity is required")
        with self._lock:
            self.revoke(clean)
            ttl = max(1.0, float(ttl_seconds))
            credential = AgentCredential(
                token=secrets.token_urlsafe(32),
                principal=Principal(PrincipalKind.AGENT, clean),
                expires_at=self._clock() + ttl,
            )
            self._by_token[credential.token] = credential
            self._by_identity[clean] = credential.token
            return credential

    def derive(self, token: Optional[str]) -> Optional[Principal]:
        provided = str(token or "")
        if not provided:
            return None
        with self._lock:
            # Do not expose dict lookup timing as a credential oracle.
            for expected, credential in list(self._by_token.items()):
                if credential.expires_at <= self._clock():
                    self.revoke(credential.principal.identity)
                    continue
                if hmac.compare_digest(provided.encode(), expected.encode()):
                    return credential.principal
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
            token = self._by_identity.pop(clean, None)
            if token is None:
                return False
            self._by_token.pop(token, None)
            stale = [target for target, owner in self._target_to_identity.items() if owner == clean]
            for target in stale:
                self._target_to_identity.pop(target, None)
            return True

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
