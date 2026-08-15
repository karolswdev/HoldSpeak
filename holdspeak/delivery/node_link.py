"""The authenticated node link — hub side (HS-94-03).

PLATFORM-CONTRACT §6: a node initiates an outbound authenticated
link to the hub, introduces itself with ``hello`` (protocol, node
identity, instance identity, capabilities, resume cursor), then
heartbeats every 5 seconds. The hub derives liveness from MONOTONIC
receipt times — ``live`` → ``stale`` after 15 s → ``offline`` after
30 s (or explicit disconnect) — and retains last-seen wall time
forever, even offline (§13: the terminal freezes with last-seen,
truth is never erased).

Transport decision: the contract sketches a WebSocket; this
implementation carries the SAME behavioral contract over outbound
HTTP hello/heartbeat/long-poll (the proven ``mesh serve`` pattern —
holdspeak/commands/mesh_serve.py). What the acceptance binds is
behavior, not framing: the node initiates, no inbound server runs on
the node, liveness states derive hub-side, cursors resume across
kill/restart, capabilities scope commands, and the node credential
is distinct from the browser token. A streaming upgrade can replace
the poll leg later without touching this state model.

Token custody (§6.1, §12.1): node tokens live in
``~/.holdspeak/node_auth_tokens.json`` (0600), per node, creatable /
rotatable / revocable via CLI — never repository content, never the
browser token, never printed to logs. A presented credential equal
to the hub's web token is refused BY NAME before any store lookup:
the browser token can never authenticate as a node.

The legacy env-table steering relay
(:mod:`holdspeak.coder_steering_relay`, ``HOLDSPEAK_STEER_NODES``)
stays fully working as the ``legacy-direct`` path (§14 rule 6); this
module supersedes it for discovery/liveness but does not remove it.
The nodes wire projection labels those rows honestly.
"""

from __future__ import annotations

import hmac
import secrets
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterator, Optional

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .node_credentials import NodeCredentialSnapshot

NODE_PROTOCOL = 1
#: v2 adds the credential generation and the per-node hub offer keypair
#: (HS-131-16). A v1 document is MIGRATED, losslessly: every existing pairing
#: keeps its node id, token, and revocation state and gains generation 1 with no
#: offer key, so those nodes still authenticate while a signed dispatch offer
#: refuses BY NAME until they are re-paired (pairing mints the keypair; rotation
#: deliberately does not, because the hub's signing key is the hub's). A
#: document of any other schema refuses rather than being read as empty — the one
#: thing custody may never do is silently become `{}` and erase the pairings a
#: subsequent write would then drop (repair R4).
NODE_TOKENS_SCHEMA = 2
NODE_TOKENS_SCHEMA_V1 = 1
DEFAULT_TOKEN_STORE_PATH = Path.home() / ".holdspeak" / "node_auth_tokens.json"

HEARTBEAT_SECONDS = 5.0
STALE_AFTER_SECONDS = 15.0
OFFLINE_AFTER_SECONDS = 30.0

# The capability that unlocks the command leg (later stories relay
# steering commands through it). Observation never requires it.
COMMAND_CAPABILITY = "coder.steering"

# §6.4 node events carry metadata only. The wire allow-list is the
# whole protocol: a field not named here refuses the event (§12.3 —
# no body-content smuggling), it is never silently dropped.
NODE_EVENT_FIELDS = (
    "seq",
    "event_id",
    "occurred_at",
    "kind",
    "project",
    "story_id",
    "worktree_hint",
    "detail",
)
NODE_EVENT_KINDS = frozenset(
    {
        "source.changed",
        "rail.cursor",
        "session.lifecycle",
        "target.changed",
        "receipt.changed",
        "evidence.invalidated",
        "capability.changed",
    }
)
MAX_DETAIL_KEYS = 16
MAX_DETAIL_CHARS = 500
MAX_RETAINED_EVENTS = 500

DEFAULT_LOCAL_CAPABILITIES = ("delivery.source", COMMAND_CAPABILITY)

# Refusal reasons that mean "the credential itself failed".
AUTH_REASONS = frozenset(
    {"unknown_node", "node_revoked", "token_rejected", "node_token_required"}
)


class NodeLinkError(ValueError):
    """A typed, client-safe refusal: ``reason`` is machine-readable,
    the message carries no secret, token, or filesystem path."""

    def __init__(self, reason: str, message: Optional[str] = None) -> None:
        super().__init__(message or reason)
        self.reason = reason


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── token custody ────────────────────────────────────────────────────


class NodeTokenStore:
    """Per-node pairing tokens and hub offer keys, outside repository content (§12.1).

    ``node_id`` is stable across restarts AND across rotation; it
    changes only on re-pair (revoke + create) — §3's identity table.

    HS-131-16 makes this custody process-coherent and asymmetric (design §1,
    Sol Amendments 1 and 3):

    * Every authentication, lookup, and lifecycle verb performs a FRESH read.
      Nothing is cached in the instance, so a rotate or revoke performed by the
      CLI is visible to a running hub immediately, without a restart.
    * Writers hold an exclusive cross-process lock across read-modify-write and
      replace the document atomically, so two concurrent verbs cannot lose one
      another's edit and a reader never observes a torn file.
    * A pairing carries a monotonic ``generation`` (bumped by create AND rotate)
      and a per-node Ed25519 offer keypair. The queue binds the generation at
      enqueue, so a rotated or re-paired credential cannot inherit old work.
      Only the PUBLIC half of the offer key ever leaves this file; the private
      half signs dispatch offers inside the hub's own claim transaction and
      never crosses a process boundary.
    """

    def __init__(self, path: Optional[Path] = None) -> None:
        self._path = Path(path) if path else DEFAULT_TOKEN_STORE_PATH

    # persistence ------------------------------------------------------

    def _refuse_custody(self) -> "NodeLinkError":
        """The ONE fixed custody refusal (repair R2.6).

        Unknown schema, a schema this build knows whose ``nodes`` is not an
        object, and a malformed node entry are the same failure with three
        surfaces: this document is not something this build can interpret. Every
        one of them raises — none of them returns ``{}`` — because ``{}`` is what
        the next ``create``, ``rotate``, or ``pair`` would WRITE, silently
        erasing every unrelated pairing on this machine.
        """
        return NodeLinkError(
            "node_custody_schema_unknown",
            "this machine's node pairing custody is a shape this build cannot read",
        )

    def _read(self) -> dict[str, dict[str, Any]]:
        """The fresh, metadata-checked read every verb starts from.

        Order is the repair (R2.6): the SCHEMA decides whether this document may
        be interpreted at all, and it is checked BEFORE ``nodes`` is looked at.
        The old order let an unknown schema whose ``nodes`` was not an object
        fall out as an empty store — the exact silent-erasure path the schema
        check existed to prevent.
        """
        from .node_credentials import read_private_document

        document = read_private_document(self._path)
        if document is None:
            # No custody document at all: this machine has simply never paired.
            return {}
        if not isinstance(document, dict) or not document:
            raise self._refuse_custody()
        schema = document.get("node_tokens_schema")
        if schema not in (NODE_TOKENS_SCHEMA, NODE_TOKENS_SCHEMA_V1):
            raise self._refuse_custody()
        nodes = document.get("nodes")
        if not isinstance(nodes, dict):
            raise self._refuse_custody()
        entries: dict[str, dict[str, Any]] = {}
        for name, entry in nodes.items():
            if not isinstance(name, str) or not name.strip() or not isinstance(entry, dict):
                # A non-dictionary node was silently DROPPED before, which the
                # next write then made permanent. It refuses instead.
                raise self._refuse_custody()
            entries[str(name)] = self._validated_entry(entry)
        if schema == NODE_TOKENS_SCHEMA_V1:
            return {name: self._migrated_v1(entry) for name, entry in entries.items()}
        return entries

    def _validated_entry(self, entry: dict[str, Any]) -> dict[str, Any]:
        """One pairing record, whole and well-typed, or the fixed refusal.

        Lossless is the contract: what comes back is the entry as written, plus
        nothing and minus nothing. Only the shape is judged.
        """
        checked = dict(entry)
        if not isinstance(checked.get("node_id", ""), str):
            raise self._refuse_custody()
        if not isinstance(checked.get("token", ""), str):
            raise self._refuse_custody()
        if "revoked" in checked and not isinstance(checked["revoked"], bool):
            raise self._refuse_custody()
        generation = checked.get("generation")
        if generation is not None and (
            not isinstance(generation, int)
            or isinstance(generation, bool)
            or generation < 1
        ):
            raise self._refuse_custody()
        for name in ("key_id", "offer_public_key", "offer_private_key"):
            if name in checked and not isinstance(checked[name], str):
                raise self._refuse_custody()
        return checked

    @staticmethod
    def _migrated_v1(entry: dict[str, Any]) -> dict[str, Any]:
        """One v1 pairing, carried forward whole.

        Identity, token, and revocation survive exactly. What v1 could not have —
        a credential generation and a hub offer keypair — is filled with
        generation 1 and no key material, so the node still authenticates and a
        dispatch offer for it refuses by name until it is rotated. Migration is
        lossless for EVERY node or it does not happen: a malformed entry has
        already refused above, without a write.
        """
        migrated = dict(entry)
        migrated.setdefault("generation", 1)
        migrated.setdefault("key_id", "")
        migrated.setdefault("offer_public_key", "")
        migrated.setdefault("offer_private_key", "")
        return migrated

    @contextmanager
    def custody_lock(self) -> Iterator[None]:
        """Hold this store's exclusive cross-process lock.

        The claim and first-settlement transactions take it so that revalidating
        a credential snapshot and committing against it are ONE decision: a
        rotate, revoke, or re-pair either lands before the transaction opens or
        waits for it to finish, and the loser refuses by name (repair R4).
        """
        from .node_credentials import exclusive_custody_lock

        with exclusive_custody_lock(self._path):
            yield

    def _write(self, nodes: dict[str, dict[str, Any]]) -> None:
        from .node_credentials import write_private_document

        write_private_document(
            self._path, {"node_tokens_schema": NODE_TOKENS_SCHEMA, "nodes": nodes}
        )

    @contextmanager
    def _mutate(self) -> Iterator[dict[str, dict[str, Any]]]:
        """Exclusive read-modify-write. The lock spans the whole edit."""
        from .node_credentials import exclusive_custody_lock

        with exclusive_custody_lock(self._path):
            nodes = self._read()
            yield nodes
            self._write(nodes)

    # lifecycle --------------------------------------------------------

    def create(self, name: str) -> tuple[str, str]:
        """Pair a node: returns ``(node_id, token)``. Re-pairing a
        revoked name mints a NEW node_id (§3); an active name refuses
        (rotate instead — pairing is deliberate)."""
        return self.pair(name)[0:2]

    def pair(self, name: str) -> tuple[str, str, "NodeCredentialSnapshot"]:
        """``create`` with the worker's pin: ``(node_id, token, snapshot)``.

        The snapshot is the PUBLIC view — node id, generation, key id, and the
        offer public key — which is exactly what a worker pins and nothing more.
        """
        from .node_credentials import NodeCredentialSnapshot, mint_offer_keypair

        name = self._clean_name(name)
        with self._mutate() as nodes:
            entry = nodes.get(name)
            if entry is not None and not entry.get("revoked"):
                raise NodeLinkError(
                    "already_paired", f"node '{name}' is already paired; rotate instead"
                )
            key_id, private_key, public_key = mint_offer_keypair()
            token = secrets.token_urlsafe(24)
            node_id = "node_" + uuid.uuid4().hex[:16]
            generation = int(entry.get("generation") or 0) + 1 if entry else 1
            nodes[name] = {
                "node_id": node_id,
                "token": token,
                "generation": generation,
                "key_id": key_id,
                "offer_private_key": private_key,
                "offer_public_key": public_key,
                "revoked": False,
                "created_at": _utc_now_iso(),
            }
        return node_id, token, NodeCredentialSnapshot(
            name=name,
            node_id=node_id,
            generation=generation,
            key_id=key_id,
            offer_public_key=public_key,
        )

    def rotate(self, name: str) -> str:
        """New token and a new generation, same node identity and offer key.

        The old token is dead the moment this returns — no repository edit
        involved. The generation moves so queued work addressed to the previous
        credential cannot be claimed under the replacement (Sol Amendment 3);
        the hub's signing key is the HUB's, not the node's, so it is unchanged
        and a worker's pin stays valid.
        """
        name = self._clean_name(name)
        with self._mutate() as nodes:
            entry = nodes.get(name)
            if entry is None or entry.get("revoked"):
                raise NodeLinkError("unknown_node", f"no active pairing for '{name}'")
            entry["token"] = secrets.token_urlsafe(24)
            entry["generation"] = int(entry.get("generation") or 1) + 1
            entry["rotated_at"] = _utc_now_iso()
            token = str(entry["token"])
        return token

    def revoke(self, name: str) -> None:
        """Kill the pairing by name. The record stays (revoked) so a
        revoked node's hello/heartbeat refuses BY NAME, not as an
        anonymous unknown. The private offer key goes with it."""
        name = self._clean_name(name)
        with self._mutate() as nodes:
            entry = nodes.get(name)
            if entry is None:
                raise NodeLinkError("unknown_node", f"no pairing for '{name}'")
            entry["revoked"] = True
            entry["token"] = ""
            entry["offer_private_key"] = ""
            entry["revoked_at"] = _utc_now_iso()

    def ensure(self, name: str) -> tuple[str, str]:
        """(node_id, token) — creating the pairing on first use. A
        revoked name is NOT resurrected: revocation holds until an
        explicit re-pair."""
        name = self._clean_name(name)
        entry = self._read().get(name)
        if entry is None:
            return self.create(name)
        if entry.get("revoked"):
            raise NodeLinkError("node_revoked", f"node '{name}' is revoked")
        return str(entry["node_id"]), str(entry["token"])

    def verify(
        self, name: str, token: Optional[str], *, web_token: Optional[str] = None
    ) -> str:
        """Authenticate one node request; returns the ``node_id``."""
        return self.authenticate(name, token, web_token=web_token).node_id

    def authenticate(
        self, name: str, token: Optional[str], *, web_token: Optional[str] = None
    ) -> "NodeCredentialSnapshot":
        """Authenticate one node request into ONE fresh credential snapshot.

        Order matters: the web-token equality check runs FIRST so a
        browser credential can never authenticate as a node even if
        someone copied it into the store (§12.1 distinctness).

        The returned snapshot carries the node id, the exact credential
        generation, and the offer key id — the same values the claim
        transaction revalidates at its commit boundary — and never the private
        signing key.
        """
        from .node_credentials import NodeCredentialSnapshot

        name = self._clean_name(name)
        provided = str(token or "")
        if not provided:
            raise NodeLinkError("token_rejected", "a node token is required")
        if web_token and hmac.compare_digest(
            provided.encode("utf-8"), web_token.encode("utf-8")
        ):
            raise NodeLinkError(
                "node_token_required",
                "the browser token cannot authenticate as a node",
            )
        entry = self._read().get(name)
        if entry is None:
            raise NodeLinkError("unknown_node", f"no pairing for '{name}'")
        if entry.get("revoked"):
            raise NodeLinkError("node_revoked", f"node '{name}' is revoked")
        expected = str(entry.get("token") or "")
        if not expected or not hmac.compare_digest(
            provided.encode("utf-8"), expected.encode("utf-8")
        ):
            raise NodeLinkError("token_rejected", f"token rejected for '{name}'")
        return NodeCredentialSnapshot(
            name=name,
            node_id=str(entry.get("node_id") or ""),
            generation=int(entry.get("generation") or 1),
            key_id=str(entry.get("key_id") or ""),
            offer_public_key=str(entry.get("offer_public_key") or ""),
            token=expected,
        )

    def pairing(self, name: str) -> Optional["NodeCredentialSnapshot"]:
        """The PUBLIC view of one active pairing, or ``None`` when there is none.

        What the relay enqueue needs to bind a job to a stable destination: the
        node id and the credential generation that is live right now. Carries no
        token and no key material.
        """
        from .node_credentials import NodeCredentialSnapshot

        entry = self._read().get(str(name or "").strip())
        if entry is None or entry.get("revoked"):
            return None
        return NodeCredentialSnapshot(
            name=str(name).strip(),
            node_id=str(entry.get("node_id") or ""),
            generation=int(entry.get("generation") or 1),
            key_id=str(entry.get("key_id") or ""),
            offer_public_key=str(entry.get("offer_public_key") or ""),
        )

    def bearer_token(self, name: str) -> str:
        """One active pairing's bearer token, for the deliberate export only.

        Distribution is an ACT: `holdspeak node token export` is the single
        caller, it writes owner-only custody, and it carries no key material.
        Nothing in the request path uses this — authentication compares tokens,
        it never fetches one.
        """
        name = self._clean_name(name)
        entry = self._read().get(name)
        if entry is None or entry.get("revoked"):
            raise NodeLinkError("unknown_node", f"no active pairing for '{name}'")
        token = str(entry.get("token") or "")
        if not token:
            raise NodeLinkError("unknown_node", f"node '{name}' has no token")
        return token

    def export_pairing(self, name: str) -> tuple["NodeCredentialSnapshot", str]:
        """The public snapshot AND its bearer token, from ONE locked document.

        Repair R2.9. Building an export out of :meth:`pairing` followed by
        :meth:`bearer_token` is two independent locked reads, and a rotate or
        re-pair that lands between them produces a transfer file that pairs
        generation 1's identity and pin with generation 2's token — a document
        that authenticates as nothing and refuses at the first claim. One read
        under one lock cannot straddle the change: the export is either entirely
        before it or entirely after it.
        """
        from .node_credentials import NodeCredentialSnapshot, exclusive_custody_lock

        name = self._clean_name(name)
        with exclusive_custody_lock(self._path):
            entry = self._read().get(name)
            if entry is None or entry.get("revoked"):
                raise NodeLinkError("unknown_node", f"no active pairing for '{name}'")
            token = str(entry.get("token") or "")
            if not token:
                raise NodeLinkError("unknown_node", f"node '{name}' has no token")
            snapshot = NodeCredentialSnapshot(
                name=name,
                node_id=str(entry.get("node_id") or ""),
                generation=int(entry.get("generation") or 1),
                key_id=str(entry.get("key_id") or ""),
                offer_public_key=str(entry.get("offer_public_key") or ""),
            )
        return snapshot, token

    def signing_snapshot(self, name: str) -> "NodeCredentialSnapshot":
        """The hub-only view that includes the offer PRIVATE key.

        Read fresh inside the claim transaction and never handed to a caller
        that is merely authenticating a request.
        """
        from .node_credentials import NodeCredentialSnapshot

        name = self._clean_name(name)
        entry = self._read().get(name)
        if entry is None or entry.get("revoked"):
            raise NodeLinkError("unknown_node", f"no active pairing for '{name}'")
        private_key = str(entry.get("offer_private_key") or "")
        if not private_key:
            raise NodeLinkError("unknown_node", f"node '{name}' has no offer key")
        return NodeCredentialSnapshot(
            name=name,
            node_id=str(entry.get("node_id") or ""),
            generation=int(entry.get("generation") or 1),
            key_id=str(entry.get("key_id") or ""),
            offer_public_key=str(entry.get("offer_public_key") or ""),
            token=str(entry.get("token") or ""),
            offer_private_key=private_key,
        )

    def principal_identity(self, token: Optional[str]) -> Optional[str]:
        """Derive a node identity from a credential without caller labels."""
        snapshot = self.identify(token)
        return snapshot.node_id if snapshot is not None else None

    def identify(self, token: Optional[str]) -> Optional["NodeCredentialSnapshot"]:
        """The whole authenticated identity behind one credential, or ``None``.

        The edge needs the NAME and GENERATION, not only the opaque id: a mesh
        claim is authorized against the queue row's destination node id AND its
        enqueue-time generation, and neither may come from the request body.
        """
        from .node_credentials import NodeCredentialSnapshot

        provided = str(token or "")
        if not provided:
            return None
        for name, entry in self._read().items():
            if entry.get("revoked"):
                continue
            expected = str(entry.get("token") or "")
            if expected and hmac.compare_digest(provided.encode(), expected.encode()):
                return NodeCredentialSnapshot(
                    name=str(name),
                    node_id=str(entry.get("node_id") or ""),
                    generation=int(entry.get("generation") or 1),
                    key_id=str(entry.get("key_id") or ""),
                    offer_public_key=str(entry.get("offer_public_key") or ""),
                    token=expected,
                )
        return None

    def status_rows(self) -> list[dict[str, Any]]:
        """Pairing inventory for the CLI: names and states, NEVER
        token or key material."""
        nodes = self._read()
        rows = []
        for name in sorted(nodes):
            entry = nodes[name]
            rows.append(
                {
                    "name": name,
                    "node_id": str(entry.get("node_id") or ""),
                    "generation": int(entry.get("generation") or 1),
                    "key_id": str(entry.get("key_id") or ""),
                    "revoked": bool(entry.get("revoked")),
                    "created_at": str(entry.get("created_at") or ""),
                }
            )
        return rows

    @staticmethod
    def _clean_name(name: str) -> str:
        clean = str(name or "").strip()
        if not clean:
            raise NodeLinkError("unknown_node", "a node name is required")
        return clean


# ── node events ──────────────────────────────────────────────────────


def validate_node_event(event: Any) -> dict[str, Any]:
    """One metadata-only node event, allow-listed field by field.

    Refusals are typed and name the offending field/kind — a refused
    event is never partially accepted or silently trimmed."""
    if not isinstance(event, dict):
        raise NodeLinkError("event_malformed", "a node event must be an object")
    for key in event:
        if key not in NODE_EVENT_FIELDS:
            raise NodeLinkError(
                "event_field_not_allowed",
                f"field '{key}' is not in the node event protocol",
            )
    kind = str(event.get("kind") or "")
    if kind not in NODE_EVENT_KINDS:
        raise NodeLinkError("event_kind_unknown", f"unknown event kind '{kind}'")
    seq = event.get("seq")
    if not isinstance(seq, int) or isinstance(seq, bool) or seq < 1:
        raise NodeLinkError("event_seq_invalid", "seq must be a positive integer")
    detail = event.get("detail")
    if detail is not None:
        if not isinstance(detail, dict) or len(detail) > MAX_DETAIL_KEYS:
            raise NodeLinkError(
                "event_detail_invalid", "detail must be a small flat object"
            )
        for key, value in detail.items():
            if not isinstance(key, str):
                raise NodeLinkError("event_detail_invalid", "detail keys must be strings")
            if isinstance(value, (dict, list, tuple)):
                raise NodeLinkError(
                    "event_detail_invalid",
                    f"detail '{key}' must be scalar metadata, not nested content",
                )
            if isinstance(value, str) and len(value) > MAX_DETAIL_CHARS:
                raise NodeLinkError(
                    "event_detail_invalid",
                    f"detail '{key}' exceeds the metadata ceiling",
                )
    return dict(event)


# ── link state ───────────────────────────────────────────────────────


@dataclass
class _LinkedNode:
    node_id: str
    name: str
    instance_id: str = ""
    protocol: int = 0
    capabilities: tuple[str, ...] = ()
    last_seen_mono: float = 0.0
    last_seen_wall: str = ""
    clock_skew_seconds: Optional[float] = None
    last_seq: int = 0
    explicit_offline: bool = False
    events: list[dict[str, Any]] = field(default_factory=list)


class NodeLinkState:
    """Hub-side truth for every linked node: identity, capabilities,
    liveness (monotonic), event cursor, and the retained metadata
    events. One instance per hub; the embedded local node and remote
    nodes share this exact code path (§2 rule 14)."""

    def __init__(
        self,
        token_store: Optional[NodeTokenStore] = None,
        *,
        web_token: Optional[str] = None,
        clock: Callable[[], float] = time.monotonic,
        wall_clock: Callable[[], str] = _utc_now_iso,
        stale_after_seconds: float = STALE_AFTER_SECONDS,
        offline_after_seconds: float = OFFLINE_AFTER_SECONDS,
        heartbeat_seconds: float = HEARTBEAT_SECONDS,
        command_source: Optional[Callable[[str], list[dict[str, Any]]]] = None,
    ) -> None:
        self.token_store = token_store or NodeTokenStore()
        self._web_token = web_token
        self._clock = clock
        self._wall_clock = wall_clock
        self.stale_after = float(stale_after_seconds)
        self.offline_after = float(offline_after_seconds)
        self.heartbeat_seconds = float(heartbeat_seconds)
        # HS-94-06: the command claim leg's supplier. The hub's command
        # service hands envelopes/probes per node_id; absent, the claim
        # stays the HS-94-03 empty envelope. Auth/capability gating is
        # unchanged — the source is consulted only after the gate.
        self.command_source = command_source
        self._nodes: dict[str, _LinkedNode] = {}

    # auth --------------------------------------------------------------

    def _verify(self, name: str, token: Optional[str]) -> str:
        return self.token_store.verify(name, token, web_token=self._web_token)

    # the wire verbs -----------------------------------------------------

    def hello(
        self,
        name: str,
        token: Optional[str],
        *,
        node_protocol: int,
        instance_id: str,
        capabilities: Optional[list[str]] = None,
        resume_cursor: Optional[int] = None,
        node_wall_time: Optional[str] = None,
    ) -> dict[str, Any]:
        """Register/refresh one node. Returns the link parameters and
        the hub's acked cursor — the node resumes from THAT, so a
        node that lost its own cursor cannot duplicate, and a hub
        that restarted adopts the node's persisted cursor."""
        node_id = self._verify(name, token)
        node = self._nodes.get(name)
        if node is None or node.node_id != node_id:
            node = _LinkedNode(node_id=node_id, name=name)
            if resume_cursor is not None and int(resume_cursor) >= 0:
                node.last_seq = int(resume_cursor)
            self._nodes[name] = node
        node.instance_id = str(instance_id or "")
        node.protocol = int(node_protocol)
        node.capabilities = tuple(str(c) for c in (capabilities or []))
        node.explicit_offline = False
        self._touch(node, node_wall_time)
        enabled, compat = self._command_gate(node)
        return {
            "ok": True,
            "node_protocol": NODE_PROTOCOL,
            "node_id": node.node_id,
            "cursor": node.last_seq,
            "commands_enabled": enabled,
            "compat": compat,
            "heartbeat_seconds": self.heartbeat_seconds,
            "stale_after_seconds": self.stale_after,
            "offline_after_seconds": self.offline_after,
            "clock_skew_seconds": node.clock_skew_seconds,
        }

    def heartbeat(
        self,
        name: str,
        token: Optional[str],
        *,
        instance_id: Optional[str] = None,
        events: Optional[list[Any]] = None,
        node_wall_time: Optional[str] = None,
    ) -> dict[str, Any]:
        """One heartbeat, optionally carrying a metadata event batch.

        Cursor discipline: duplicates (seq ≤ acked) are skipped —
        replay after an unacked send is free; the next expected seq
        is accepted in order; a gap accepts nothing further and
        answers ``resync: true`` (§ acceptance: an unreplayable gap
        requests a resync, never invents continuity)."""
        node_id = self._verify(name, token)
        node = self._nodes.get(name)
        if node is None or node.node_id != node_id:
            raise NodeLinkError("hello_required", f"node '{name}' must hello first")
        if instance_id:
            node.instance_id = str(instance_id)
        node.explicit_offline = False
        self._touch(node, node_wall_time)

        accepted = 0
        resync = False
        for raw in events or []:
            event = validate_node_event(raw)  # refusal aborts the batch
            seq = int(event["seq"])
            if seq <= node.last_seq:
                continue  # duplicate — already acked
            if seq != node.last_seq + 1:
                resync = True  # gap — never paper over missing truth
                break
            node.last_seq = seq
            event["node_id"] = node.node_id
            node.events = (node.events + [event])[-MAX_RETAINED_EVENTS:]
            accepted += 1
        return {
            "ok": True,
            "cursor": node.last_seq,
            "accepted": accepted,
            "resync": resync,
            "commands_enabled": self._command_gate(node)[0],
        }

    def disconnect(self, name: str, token: Optional[str]) -> dict[str, Any]:
        """Explicit disconnect → offline immediately (§6.3), with
        last-seen retained."""
        node_id = self._verify(name, token)
        node = self._nodes.get(name)
        if node is None or node.node_id != node_id:
            raise NodeLinkError("hello_required", f"node '{name}' must hello first")
        node.explicit_offline = True
        return {"ok": True}

    def poll_commands(self, name: str, token: Optional[str]) -> dict[str, Any]:
        """The command leg (long-poll claim). HS-94-03 carries the
        envelope only — no commands exist yet — but the capability /
        protocol gate is already real: a mismatched node gets a typed
        refusal here while observation keeps working."""
        node_id = self._verify(name, token)
        node = self._nodes.get(name)
        if node is None or node.node_id != node_id:
            raise NodeLinkError("hello_required", f"node '{name}' must hello first")
        enabled, compat = self._command_gate(node)
        if not enabled:
            raise NodeLinkError("commands_disabled", compat or "commands_disabled")
        commands: list[dict[str, Any]] = []
        if self.command_source is not None:
            commands = list(self.command_source(node.node_id))
        return {
            "commands_schema": 1,
            "node_id": node.node_id,
            "cursor": node.last_seq,
            "commands": commands,
        }

    # liveness ------------------------------------------------------------

    def _touch(self, node: _LinkedNode, node_wall_time: Optional[str]) -> None:
        node.last_seen_mono = self._clock()
        node.last_seen_wall = self._wall_clock()
        if node_wall_time:
            try:
                theirs = datetime.fromisoformat(
                    str(node_wall_time).replace("Z", "+00:00")
                )
                ours = datetime.fromisoformat(
                    node.last_seen_wall.replace("Z", "+00:00")
                )
                node.clock_skew_seconds = round(
                    (ours - theirs).total_seconds(), 3
                )
            except ValueError:
                node.clock_skew_seconds = None

    def status_of(self, name: str) -> Optional[str]:
        node = self._nodes.get(str(name or "").strip())
        if node is None:
            return None
        return self._status(node)

    def _status(self, node: _LinkedNode) -> str:
        if node.explicit_offline:
            return "offline"
        age = self._clock() - node.last_seen_mono
        if age < self.stale_after:
            return "live"
        if age < self.offline_after:
            return "stale"
        return "offline"

    def _command_gate(self, node: _LinkedNode) -> tuple[bool, Optional[str]]:
        if node.protocol != NODE_PROTOCOL:
            return False, "protocol_mismatch"
        if COMMAND_CAPABILITY not in node.capabilities:
            return False, "capability_missing"
        return True, None

    # projections ---------------------------------------------------------

    def events_of(self, name: str) -> list[dict[str, Any]]:
        node = self._nodes.get(str(name or "").strip())
        return list(node.events) if node else []

    def nodes_view(self, *, legacy_env: Optional[dict] = None) -> dict[str, Any]:
        """The nodes wire projection (§13): labels, opaque IDs, typed
        liveness, last-seen — no tokens, no URLs, no paths. Legacy
        env-table steering nodes appear labeled ``legacy-direct``
        with honest ``unknown`` liveness (§14 rule 6)."""
        rows: list[dict[str, Any]] = []
        for name in sorted(self._nodes):
            node = self._nodes[name]
            enabled, compat = self._command_gate(node)
            rows.append(
                {
                    "name": node.name,
                    "node_id": node.node_id,
                    "kind": "node-link",
                    "status": self._status(node),
                    "last_seen": node.last_seen_wall,
                    "instance_id": node.instance_id,
                    "capabilities": list(node.capabilities),
                    "commands_enabled": enabled,
                    "compat": compat,
                    "cursor": node.last_seq,
                    "clock_skew_seconds": node.clock_skew_seconds,
                }
            )
        from ..coder_steering_relay import load_nodes as load_legacy_nodes

        linked = {row["name"] for row in rows}
        for name in sorted(load_legacy_nodes(legacy_env)):
            if name in linked:
                continue
            rows.append(
                {
                    "name": name,
                    "node_id": None,
                    "kind": "legacy-direct",
                    "status": "unknown",
                    "last_seen": "",
                    "instance_id": "",
                    "capabilities": [COMMAND_CAPABILITY],
                    "commands_enabled": True,
                    "compat": "legacy-direct",
                    "cursor": 0,
                    "clock_skew_seconds": None,
                }
            )
        return {"nodes_schema": 1, "nodes": rows}


# ── the embedded local node ──────────────────────────────────────────


class LocalNodeAdapter:
    """The hub's own machine registered as a node — through the SAME
    hello/heartbeat/token code path as a remote (§2 rule 14: local is
    a node, not a special product). The hub process pumps
    ``heartbeat()``; tests drive it with injected clocks and prove
    the one behavior suite on both providers."""

    def __init__(
        self,
        state: NodeLinkState,
        *,
        name: str = "local",
        capabilities: Optional[list[str]] = None,
    ) -> None:
        self._state = state
        self.name = name
        self.capabilities = list(capabilities or DEFAULT_LOCAL_CAPABILITIES)
        self.instance_id = uuid.uuid4().hex
        self.node_id: Optional[str] = None
        self._token: Optional[str] = None
        self._cursor = 0

    def start(self, *, resume_cursor: Optional[int] = None) -> dict[str, Any]:
        _node_id, token = self._state.token_store.ensure(self.name)
        self._token = token
        response = self._state.hello(
            self.name,
            token,
            node_protocol=NODE_PROTOCOL,
            instance_id=self.instance_id,
            capabilities=self.capabilities,
            resume_cursor=resume_cursor if resume_cursor is not None else self._cursor,
        )
        self.node_id = str(response["node_id"])
        self._cursor = int(response["cursor"])
        return response

    def heartbeat(self, events: Optional[list[dict[str, Any]]] = None) -> dict[str, Any]:
        if self._token is None:
            raise NodeLinkError("hello_required", "local adapter not started")
        response = self._state.heartbeat(self.name, self._token, events=events or [])
        self._cursor = int(response["cursor"])
        return response

    def stop(self) -> None:
        if self._token is not None:
            self._state.disconnect(self.name, self._token)

    @property
    def cursor(self) -> int:
        return self._cursor
