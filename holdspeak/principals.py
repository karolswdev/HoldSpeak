"""Authenticated runtime principals and edge authorization (HS-106-02).

Network location is deliberately absent from this module.  A principal comes
from a credential issued by the hub; callers may supply operation payloads,
but never their identity or rights.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import re
import secrets
import threading
import time
import uuid
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Iterable, Optional


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
    #: PHILO-9-07 (the DESK = ALL repair): the palette NAME the owner issued,
    #: stored at issue. Never reverse-mapped from the resolved tool set.
    palette_name: Optional[str] = None
    #: Conductor K6: the agent launch this credential is bound to (None for a
    #: credential the owner issued by hand). A launch-bound credential reaches
    #: POST /api/mcp from loopback with the Reach switch off.
    launch_id: Optional[str] = None
    #: Conductor K6: the launch's own Project (None: the desk). The agent may
    #: ADD to it (links, resources); it writes no other Project.
    project_id: Optional[str] = None


# HS-174 max TTL cap (counsel H2: 30 days).
_MAX_TTL_SECONDS: float = 30 * 24 * 3600.0


def _hash_token(plaintext: str) -> str:
    """SHA-256 hash for credential-at-rest (C4: plaintext only at issue)."""
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


_log = logging.getLogger(__name__)


class AgentCredentialStore:
    """Revocable credentials minted once per supervised process.

    HS-174: credentials store ``sha256(token)`` at rest and compare hashes
    constant-time.  The plaintext token is returned ONLY from ``issue()`` and
    is never stored.

    Conductor R2: once the hub ``attach``es its database, every issue,
    revoke, target and launch ownership is written through to the
    ``agent_credentials`` and ``agent_launch_ownership`` tables (the hash
    only), and ``attach`` reloads the live ones, so a hub restart keeps a
    running agent's access, palette and ownership. Expired and revoked rows
    are not loaded. A store with no database is memory only, as before.
    """

    def __init__(self, *, clock=time.monotonic, wall_clock=time.time) -> None:
        self._lock = threading.RLock()
        self._clock = clock
        self._wall = wall_clock
        self._db: Any = None
        # Keyed by sha256(token) -- the plaintext is never stored.
        self._by_hash: dict[str, AgentCredential] = {}
        self._by_identity: dict[str, str] = {}  # identity -> hash
        self._by_id: dict[str, str] = {}  # credential id -> hash
        self._target_to_identity: dict[str, str] = {}
        self._hub_url = "http://127.0.0.1:8765"
        # Conductor K6: per launch, the item ids the agent may change (its
        # origin item, and the items it created during the launch).
        self._launch_scope: dict[str, set[str]] = {}
        # ... and, of those, the desk objects the agent created itself (the
        # only owner-desk records it may edit or delete).
        self._launch_created: dict[str, set[str]] = {}
        # Launch-bound credentials revoked under the lock; their hooks run
        # after it is released (never hold the store lock into the kernel).
        self._pending_launch_revokes: list[tuple[str, str]] = []
        self.launch_revoked_hooks: list[Any] = []

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

    # -- Conductor R2: write-through persistence ------------------------

    def attach(self, database: Any) -> int:
        """Write through to *database* from now on, and load its live
        credentials (with their targets and launch ownership). Returns the
        number loaded. Expired rows are marked revoked ``expired``; revoked
        and expired rows are never loaded."""
        with self._lock:
            self._db = database
            now_wall = float(self._wall())
            loaded = 0
            try:
                with database._connection() as conn:
                    conn.execute(
                        "UPDATE agent_credentials SET revoked_at = ?, revocation_reason = 'expired' "
                        "WHERE revoked_at IS NULL AND expires_at <= ?",
                        (now_wall, now_wall),
                    )
                    rows = conn.execute(
                        "SELECT id, token_sha256, identity, palette_json, palette_name, launch_id, "
                        "project_id, targets_json, expires_at FROM agent_credentials "
                        "WHERE revoked_at IS NULL AND expires_at > ? ORDER BY created_at",
                        (now_wall,),
                    ).fetchall()
                    owned = conn.execute(
                        "SELECT o.credential_id, o.ref, o.created FROM agent_launch_ownership o "
                        "JOIN agent_credentials c ON c.id = o.credential_id "
                        "WHERE c.revoked_at IS NULL AND c.expires_at > ?",
                        (now_wall,),
                    ).fetchall()
            except Exception:
                _log.warning("agent credential reload failed", exc_info=True)
                return 0
            by_cred: dict[str, list[tuple[str, bool]]] = {}
            for row in owned:
                by_cred.setdefault(str(row["credential_id"]), []).append((str(row["ref"]), bool(row["created"])))
            for row in rows:
                token_hash = str(row["token_sha256"])
                identity = str(row["identity"])
                if token_hash in self._by_hash:
                    continue
                stale = self._by_identity.get(identity)
                if stale is not None:  # a newer in-memory issue wins
                    continue
                palette = None
                if row["palette_json"] is not None:
                    palette = frozenset(str(n) for n in json.loads(row["palette_json"]))
                credential = AgentCredential(
                    token=token_hash,
                    principal=Principal(PrincipalKind.AGENT, identity),
                    expires_at=self._clock() + (float(row["expires_at"]) - now_wall),
                    palette=palette,
                    id=str(row["id"]),
                    palette_name=row["palette_name"],
                    launch_id=row["launch_id"],
                    project_id=row["project_id"],
                )
                self._by_hash[token_hash] = credential
                self._by_identity[identity] = token_hash
                self._by_id[credential.id] = token_hash
                for target in json.loads(row["targets_json"] or "[]"):
                    self._target_to_identity[str(target)] = identity
                if credential.launch_id:
                    refs = by_cred.get(credential.id, [])
                    self._launch_scope[credential.launch_id] = {ref for ref, _c in refs}
                    self._launch_created[credential.launch_id] = {ref for ref, c in refs if c}
                loaded += 1
            return loaded

    def detach(self) -> None:
        """Stop writing through (memory stays)."""
        with self._lock:
            self._db = None

    def _forget_memory(self) -> None:
        """Drop every in-memory credential WITHOUT revoking it: what a
        process exit does. Tests use it to stand in for a hub restart."""
        with self._lock:
            self._db = None
            self._by_hash.clear()
            self._by_identity.clear()
            self._by_id.clear()
            self._target_to_identity.clear()
            self._launch_scope.clear()
            self._launch_created.clear()
            self._pending_launch_revokes.clear()

    def _write(self, sql: str, params: tuple[Any, ...]) -> None:
        database = self._db
        if database is None:
            return
        try:
            with database._connection() as conn:
                conn.execute(sql, params)
        except Exception:  # persistence never blocks an issue or a revoke
            _log.warning("agent credential write failed", exc_info=True)

    def _persist_issue(self, credential: AgentCredential, scope: Iterable[str]) -> None:
        if self._db is None:
            return
        now_wall = float(self._wall())
        wall_expires = now_wall + (credential.expires_at - self._clock())
        palette_json = (
            json.dumps(sorted(credential.palette)) if credential.palette is not None else None
        )
        self._write(
            "INSERT INTO agent_credentials (id, token_sha256, identity, palette_json, palette_name, "
            "launch_id, project_id, targets_json, expires_at, revoked_at, revocation_reason, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, '[]', ?, NULL, '', ?)",
            (credential.id, credential.token, credential.principal.identity, palette_json,
             credential.palette_name, credential.launch_id, credential.project_id,
             wall_expires, now_wall),
        )
        for ref in sorted(scope):
            self._write(
                "INSERT OR IGNORE INTO agent_launch_ownership (credential_id, ref, created, recorded_at) "
                "VALUES (?, ?, 0, ?)",
                (credential.id, ref, now_wall),
            )

    def _persist_ownership(self, launch_id: str, ref: str, *, created: bool) -> None:
        if self._db is None:
            return
        cred = next((c for c in self._by_hash.values() if c.launch_id == launch_id), None)
        if cred is None:
            return
        self._write(
            "INSERT INTO agent_launch_ownership (credential_id, ref, created, recorded_at) "
            "VALUES (?, ?, ?, ?) ON CONFLICT(credential_id, ref) DO UPDATE SET created = MAX(created, excluded.created)",
            (cred.id, ref, 1 if created else 0, float(self._wall())),
        )

    def issue(
        self,
        identity: str,
        *,
        ttl_seconds: float = 43_200.0,
        palette: Optional[frozenset[str]] = None,
        palette_name: Optional[str] = None,
        launch_id: Optional[str] = None,
        scope_items: Iterable[str] = (),
        project_id: Optional[str] = None,
    ) -> AgentCredential:
        """Mint a new credential.  Returns the credential with the plaintext
        token; the store keeps only the hash (C4)."""
        clean = str(identity or "").strip()
        if not clean:
            raise ValueError("agent identity is required")
        self.revoke(clean)
        with self._lock:
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
                palette_name=palette_name,
                launch_id=(str(launch_id).strip() or None) if launch_id else None,
                project_id=(str(project_id).strip() or None) if project_id and launch_id else None,
            )
            self._by_hash[token_hash] = credential
            self._by_identity[clean] = token_hash
            self._by_id[cred_id] = token_hash
            if credential.launch_id:
                self._launch_scope[credential.launch_id] = {
                    str(item).strip() for item in scope_items if str(item or "").strip()
                }
                self._launch_created[credential.launch_id] = set()
            self._persist_issue(credential, self._launch_scope.get(credential.launch_id or "", set()))
            # Return a copy with the plaintext so the caller can show it once.
            return AgentCredential(
                token=plaintext,
                principal=credential.principal,
                expires_at=credential.expires_at,
                palette=credential.palette,
                id=credential.id,
                last_used_at=credential.last_used_at,
                palette_name=credential.palette_name,
                launch_id=credential.launch_id,
                project_id=credential.project_id,
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
        found: Optional[AgentCredential] = None
        with self._lock:
            # Do not expose dict lookup timing as a credential oracle.
            for stored_hash, credential in list(self._by_hash.items()):
                if credential.expires_at <= self._clock():
                    self._revoke_locked(credential.principal.identity, "expired")
                    continue
                if found is None and hmac.compare_digest(provided_hash.encode(), stored_hash.encode()):
                    # Touch last_used_at (frozen dataclass -> replace).
                    found = replace(credential, last_used_at=self._clock())
                    self._by_hash[stored_hash] = found
        self._flush_launch_revokes()
        return found

    # -- Conductor K6: the launch-bound credential's scope ---------------

    def launch_credential(self, identity: str) -> Optional[AgentCredential]:
        """The live launch-bound credential of *identity*, else None."""
        clean = str(identity or "").strip()
        with self._lock:
            token_hash = self._by_identity.get(clean)
            cred = self._by_hash.get(token_hash) if token_hash else None
            if cred is None or not cred.launch_id or cred.expires_at <= self._clock():
                return None
            return cred

    def scope_add(self, launch_id: str, item_id: str) -> None:
        """An object the agent created: in its item scope, and its own."""
        with self._lock:
            scope = self._launch_scope.get(str(launch_id))
            created = self._launch_created.get(str(launch_id))
            if scope is not None and created is not None and str(item_id or "").strip():
                scope.add(str(item_id).strip())
                created.add(str(item_id).strip())
                self._persist_ownership(str(launch_id), str(item_id).strip(), created=True)

    def created_by(self, launch_id: str, object_id: str) -> bool:
        """Whether the launch's agent created *object_id* during the launch."""
        with self._lock:
            return str(object_id or "").strip() in self._launch_created.get(str(launch_id), set())

    def in_scope(self, launch_id: str, item_id: str) -> bool:
        with self._lock:
            return str(item_id or "").strip() in self._launch_scope.get(str(launch_id), set())

    def _flush_launch_revokes(self) -> None:
        with self._lock:
            pending, self._pending_launch_revokes = self._pending_launch_revokes, []
            hooks = list(self.launch_revoked_hooks)
        for launch_id, identity in pending:
            for hook in hooks:
                try:
                    hook(launch_id, identity)
                except Exception:  # a hook never blocks a revoke
                    import logging

                    logging.getLogger(__name__).warning("launch revoke hook failed", exc_info=True)

    def bind_target(self, identity: str, *targets: Optional[str]) -> None:
        with self._lock:
            for target in targets:
                clean = str(target or "").strip()
                if clean:
                    self._target_to_identity[clean] = identity
            token_hash = self._by_identity.get(str(identity or "").strip())
            cred = self._by_hash.get(token_hash) if token_hash else None
            if cred is not None:
                bound = sorted(t for t, owner in self._target_to_identity.items() if owner == identity)
                self._write("UPDATE agent_credentials SET targets_json = ? WHERE id = ?",
                            (json.dumps(bound), cred.id))

    def revoke(self, identity: str, reason: str = "revoked") -> bool:
        with self._lock:
            revoked = self._revoke_locked(identity, reason)
        self._flush_launch_revokes()
        return revoked

    def _revoke_locked(self, identity: str, reason: str = "revoked") -> bool:
        clean = str(identity or "").strip()
        with self._lock:
            token_hash = self._by_identity.pop(clean, None)
            if token_hash is None:
                return False
            cred = self._by_hash.pop(token_hash, None)
            if cred:
                self._write(
                    "UPDATE agent_credentials SET revoked_at = ?, revocation_reason = ? "
                    "WHERE id = ? AND revoked_at IS NULL",
                    (float(self._wall()), str(reason), cred.id),
                )
                self._by_id.pop(cred.id, None)
                if cred.launch_id:
                    self._launch_scope.pop(cred.launch_id, None)
                    self._launch_created.pop(cred.launch_id, None)
                    self._pending_launch_revokes.append((cred.launch_id, clean))
            stale = [target for target, owner in self._target_to_identity.items() if owner == clean]
            for target in stale:
                self._target_to_identity.pop(target, None)
            return True

    def revoke_by_id(self, credential_id: str) -> bool:
        """Revoke a credential by its id (for the settings face)."""
        clean = str(credential_id or "").strip()
        with self._lock:
            token_hash = self._by_id.get(clean)
            cred = self._by_hash.get(token_hash) if token_hash is not None else None
            identity = cred.principal.identity if cred else None
        return self.revoke(identity) if identity else False

    def identity_for_id(self, credential_id: str) -> Optional[str]:
        """The principal identity of a credential id, removing nothing (PHILO-7-02).

        A short locked read that returns BEFORE the kernel is entered (the
        lifecycle beat's callback contract: the store lock is never held
        across a kernel transaction).
        """
        clean = str(credential_id or "").strip()
        with self._lock:
            token_hash = self._by_id.get(clean)
            cred = self._by_hash.get(token_hash) if token_hash is not None else None
            return cred.principal.identity if cred is not None else None

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


def launch_reader(principal: Any) -> bool:
    """Conductor K6: an AGENT whose launch-bound credential is live reads
    memory for the life of its launch (the People cut applies to what it
    reads). Revoked with the credential."""
    if getattr(principal, "kind", None) is not PrincipalKind.AGENT:
        return False
    return agent_credentials.launch_credential(principal.identity) is not None


def derive_owner(token: Optional[str], expected: Optional[str]) -> Optional[Principal]:
    if not token or not expected:
        return None
    if hmac.compare_digest(str(token).encode(), str(expected).encode()):
        return Principal(PrincipalKind.OWNER, "owner-session")
    return None


# PHILO-9-02 (B2; the steward beat, section 6): the exact method and route
# patterns of the Room's ADMITTED and CONDITIONAL operations. An authenticated
# agent reaches the declared operation, whose kernel path refuses it
# ``project_delegation_required`` WITH a receipt (or, after story 07, executes
# under a LIVE project grant) -- never the edge's receipt-less 403. Exact
# patterns, no prefix: every other Room route keeps its OWNER edge right, and a
# conditional route's adapter re-applies OWNER to its exempt form.
_SEGMENT = r"[^/]+"
_ROOM_AGENT_SUBMIT: tuple[tuple[str, Any], ...] = tuple(
    (verb, re.compile("^" + pattern.replace("{id}", _SEGMENT).replace("{path}", ".+") + "$"))
    for verb, pattern in (
        ("DELETE", "/api/projects/{id}"),
        ("POST", "/api/projects/{id}/meetings/{id}"),
        ("DELETE", "/api/projects/{id}/meetings/{id}"),
        ("PUT", "/api/projects/{id}/resources/{path}"),
        ("DELETE", "/api/projects/{id}/resources/{path}"),
        ("POST", "/api/projects/{id}/reviews/{id}/proposals/{id}/decide"),
        ("POST", "/api/projects/{id}/reviews/{id}/accept"),
        ("POST", "/api/updates/{id}/publish"),
        ("POST", "/api/updates/{id}/delivered"),
        # PHILO-10-01: the Send's admitted routes (an agent prepares; its send,
        # discard and destination writes are refused with a receipt).
        ("POST", "/api/channels/destinations"),
        ("DELETE", "/api/channels/destinations/{id}"),
        ("POST", "/api/channels/sends"),
        ("POST", "/api/channels/sends/{id}/discard"),
        ("POST", "/api/channels/send"),
        ("POST", "/api/projects/door/count"),
        ("PUT", "/api/projects/{id}/steward/policy"),
        ("POST", "/api/projects/{id}/steward/runs"),
        ("POST", "/api/steward/runs/{id}/stop"),
        ("POST", "/api/steward/trigger"),
        ("POST", "/api/nudges/{id}/send"),
        ("POST", "/api/watches/{id}/test"),
        ("POST", "/api/watches/{id}/evaluate"),
        ("PUT", "/api/watches/{id}/rules"),
        ("POST", "/api/watches/{id}/pause"),
        ("POST", "/api/watches/{id}/resume"),
        ("POST", "/api/watches/{id}/retire"),
        ("PATCH", "/api/watches/{id}"),
        ("POST", "/api/watches/{id}/baseline"),
        ("POST", "/api/projects/{id}/suggested-sources/{path}/add"),
        # conditional (the adapter re-applies OWNER to the exempt form)
        ("POST", "/api/projects/door"),
        ("POST", "/api/connections/{id}/recheck"),
    )
)


def room_agent_submit(method: str, path: str) -> bool:
    """True for exactly the Room's admitted and conditional HTTP routes (B2)."""
    verb = str(method or "").upper()
    return any(verb == want and pattern.match(path) for want, pattern in _ROOM_AGENT_SUBMIT)


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
    # PHILO-7-02: the desk delegation grant routes reach the kernel for an
    # agent too, so an agent's attempt is refused BY THE KERNEL with a receipt
    # (owner_principal_required), never by the edge with none.
    if path.startswith("/api/settings/remote/delegations/") and verb in {"PUT", "DELETE"}:
        return PrincipalRight.AGENT_SUBMIT
    if room_agent_submit(verb, path):
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
