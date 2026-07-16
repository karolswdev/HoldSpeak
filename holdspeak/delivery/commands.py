"""The typed command envelope and its idempotent receipts (HS-94-06).

PLATFORM-CONTRACT §8: every remote-capable command is one envelope —
``command_schema: 1``, a UUID ``command_id``, issued/expiry instants,
an IMMUTABLE target (node/target/generation), a typed operation, a
server-derived authority block, the payload with its sha256 binding,
and an ``expected_sequence`` that serializes writes per target.

The node processing order is implemented EXACTLY (§8, numbered in
:meth:`NodeCommandProcessor.process`); execution happens only through
the existing chokepoints — ``coder_steering.deliver`` /
``deliver_keys`` for text and keys, ``coder_factory`` for lifecycle —
so every grant/posture invariant stays where it always lived. The
authority block is resolved ONCE through ``operation_policy`` at the
hub; no client controls actor, policy version, or authority reason
(a client-supplied authority block is refused by name).

Receipts (§8.1) are persisted in the node's durable dedup ledger
before they are final: a duplicate envelope returns the SAME receipt
without re-execution, a lost response reconciles by ``command_id``,
and a node that lost its ledger across an unclean reset answers
``indeterminate_after_node_reset`` — it never executes the old
envelope again (§8.2).
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Optional

from ..operation_policy import POLICY_VERSION, describe_operation, resolve_policy

COMMAND_SCHEMA = 1
RECEIPT_SCHEMA = 1
PAYLOAD_HEAD_CHARS = 120  # the steering-audit privacy ceiling, mirrored
DEFAULT_COMMAND_TTL_SECONDS = 30
MAX_COMMAND_TTL_SECONDS = 300

NODE_TARGET_ID = "node"  # the node-scoped pseudo-target (spawn/rename)

STEERING_VERBS = frozenset({"terminal.text", "terminal.keys"})
PANE_VERBS = frozenset({"terminal.text", "terminal.keys", "factory.kill"})
NODE_SCOPED_VERBS = frozenset({"factory.spawn", "factory.rename"})
KNOWN_OPERATIONS = frozenset(
    {
        ("coder_steering", "terminal.text"),
        ("coder_steering", "terminal.keys"),
        ("coder_steering", "terminal.disarm"),
        ("coder_factory", "factory.spawn"),
        ("coder_factory", "factory.rename"),
        ("coder_factory", "factory.kill"),
    }
)

_ENVELOPE_FIELDS = frozenset(
    {
        "command_schema",
        "command_id",
        "issued_at",
        "expires_at",
        "target",
        "operation",
        "authority",
        "payload",
        "payload_sha256",
        "payload_head",
        "expected_sequence",
    }
)
_AUTHORITY_FIELDS = ("actor", "control_posture", "decision", "policy_version")

# The ONE policy decision, encoded onto the wire and decoded back into
# the exact snapshot the chokepoint's invariant check consumes.
_DECISION_BY_OUTCOME = {
    ("allowed", "scoped_grant"): "allowed_by_active_grant",
    ("allowed", "control_posture"): "allowed_by_control_posture",
    ("grant_required", "none"): "grant_required",
}
_SNAPSHOT_BY_DECISION = {
    "allowed_by_active_grant": {
        "outcome": "allowed",
        "authority_basis": "scoped_grant",
        "reason_code": "steering_grant_active",
    },
    "allowed_by_control_posture": {
        "outcome": "allowed",
        "authority_basis": "control_posture",
        "reason_code": "registered_steering_posture_allowed",
    },
    "grant_required": {
        "outcome": "grant_required",
        "authority_basis": "none",
        "reason_code": "steering_grant_required",
    },
    "refused_registered_destination_required": {
        "outcome": "refused",
        "authority_basis": "none",
        "reason_code": "registered_steering_destination_required",
    },
    "refused_by_policy": {
        "outcome": "refused",
        "authority_basis": "none",
        "reason_code": "steering_policy_refused",
    },
}
_SUCCEEDED = frozenset({"delivered", "disarmed", "spawned", "renamed", "killed"})
_FAILED = frozenset({"transport_error", "error"})


class CommandRefused(ValueError):
    """A typed envelope refusal: ``reason`` is machine-readable and the
    message never echoes payload content or secrets."""

    def __init__(self, reason: str, message: Optional[str] = None) -> None:
        super().__init__(message or reason)
        self.reason = reason


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_z(instant: datetime) -> str:
    return instant.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso(value: Any) -> Optional[datetime]:
    try:
        parsed = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def payload_digest(payload: Mapping[str, Any]) -> str:
    """The payload-binding hash: sha256 over canonical JSON."""
    canonical = json.dumps(dict(payload), separators=(",", ":"), sort_keys=True)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def payload_head(verb: str, payload: Mapping[str, Any]) -> str:
    """The bounded, privacy-ceiling receipt head (§8.1)."""
    if verb == "terminal.text":
        head = str(payload.get("text") or "")
    elif verb == "terminal.keys":
        head = json.dumps(payload.get("keys") or [], separators=(",", ":"))
    elif verb == "factory.spawn":
        head = f"spawn {payload.get('name') or ''}"
    elif verb == "factory.rename":
        head = f"rename {payload.get('target_session') or ''} -> {payload.get('new_name') or ''}"
    elif verb == "factory.kill":
        head = f"kill ({payload.get('scope') or 'pane'})"
    else:
        head = verb
    return head[:PAYLOAD_HEAD_CHARS]


def encode_decision(decision: Mapping[str, Any]) -> str:
    outcome = str(decision.get("outcome") or "")
    basis = str(decision.get("authority_basis") or "none")
    encoded = _DECISION_BY_OUTCOME.get((outcome, basis))
    if encoded:
        return encoded
    if str(decision.get("reason_code")) == "registered_steering_destination_required":
        return "refused_registered_destination_required"
    return "refused_by_policy"


def decode_decision(authority: Mapping[str, Any]) -> dict[str, Any]:
    """Rebuild the exact policy snapshot the chokepoint consumes from
    the envelope's authority block — the decision itself is never
    re-resolved node-side (one decision per command)."""
    snapshot = dict(
        _SNAPSHOT_BY_DECISION.get(
            str(authority.get("decision") or ""),
            _SNAPSHOT_BY_DECISION["refused_by_policy"],
        )
    )
    snapshot["policy_version"] = str(authority.get("policy_version") or "")
    snapshot["mode"] = str(authority.get("control_posture") or "")
    return snapshot


def validate_envelope(raw: Any) -> dict[str, Any]:
    """Normalize one wire envelope; refusals are typed by name."""
    if not isinstance(raw, Mapping):
        raise CommandRefused("envelope_malformed", "a command envelope must be an object")
    unknown = set(raw) - _ENVELOPE_FIELDS
    if unknown:
        raise CommandRefused(
            "envelope_field_not_allowed",
            f"field '{sorted(unknown)[0]}' is not in the command protocol",
        )
    if raw.get("command_schema") != COMMAND_SCHEMA:
        raise CommandRefused(
            "command_schema_unsupported",
            f"command_schema must be {COMMAND_SCHEMA}",
        )
    try:
        command_id = str(uuid.UUID(str(raw.get("command_id"))))
    except (ValueError, TypeError):
        raise CommandRefused("command_id_invalid", "command_id must be a UUID")
    issued_at = _parse_iso(raw.get("issued_at"))
    expires_at = _parse_iso(raw.get("expires_at"))
    if issued_at is None or expires_at is None:
        raise CommandRefused("timestamps_invalid", "issued_at/expires_at must be ISO instants")
    target = raw.get("target")
    if not isinstance(target, Mapping) or not all(
        str(target.get(k) or "").strip()
        for k in ("node_id", "target_id", "target_generation")
    ):
        raise CommandRefused(
            "target_incomplete",
            "target requires node_id, target_id, and target_generation",
        )
    operation = raw.get("operation")
    if not isinstance(operation, Mapping):
        raise CommandRefused("operation_unknown", "operation must be an object")
    family = str(operation.get("family") or "")
    verb = str(operation.get("verb") or "")
    if (family, verb) not in KNOWN_OPERATIONS:
        raise CommandRefused("operation_unknown", f"unknown operation {family}/{verb}")
    authority = raw.get("authority")
    if not isinstance(authority, Mapping) or not all(
        str(authority.get(k) or "").strip() for k in _AUTHORITY_FIELDS
    ):
        raise CommandRefused(
            "authority_incomplete",
            "authority requires actor, control_posture, decision, policy_version",
        )
    payload = raw.get("payload")
    if not isinstance(payload, Mapping):
        raise CommandRefused("payload_malformed", "payload must be an object")
    if str(raw.get("payload_sha256") or "") != payload_digest(payload):
        raise CommandRefused(
            "payload_hash_mismatch", "payload_sha256 does not bind the payload"
        )
    sequence = raw.get("expected_sequence")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
        raise CommandRefused(
            "expected_sequence_invalid", "expected_sequence must be a positive integer"
        )
    return {
        "command_schema": COMMAND_SCHEMA,
        "command_id": command_id,
        "issued_at": _iso_z(issued_at),
        "expires_at": _iso_z(expires_at),
        "target": {
            "node_id": str(target["node_id"]),
            "target_id": str(target["target_id"]),
            "target_generation": str(target["target_generation"]),
        },
        "operation": {"family": family, "verb": verb},
        "authority": {
            "actor": str(authority["actor"]),
            "control_posture": str(authority["control_posture"]),
            "decision": str(authority["decision"]),
            "policy_version": str(authority["policy_version"]),
            "grant_id": authority.get("grant_id"),
        },
        "payload": dict(payload),
        "payload_sha256": str(raw["payload_sha256"]),
        "payload_head": payload_head(verb, payload),
        "expected_sequence": sequence,
    }


def build_envelope(
    *,
    node_id: str,
    target_id: str,
    target_generation: str,
    family: str,
    verb: str,
    payload: Mapping[str, Any],
    expected_sequence: int,
    authority: Mapping[str, Any],
    command_id: Optional[str] = None,
    ttl_seconds: int = DEFAULT_COMMAND_TTL_SECONDS,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Hub-side stamping of one complete envelope (identity, instants,
    payload binding). ``authority`` is the server-derived block."""
    issued = now or _utc_now()
    ttl = max(1, min(int(ttl_seconds), MAX_COMMAND_TTL_SECONDS))
    raw = {
        "command_schema": COMMAND_SCHEMA,
        "command_id": command_id or str(uuid.uuid4()),
        "issued_at": _iso_z(issued),
        "expires_at": _iso_z(
            datetime.fromtimestamp(issued.timestamp() + ttl, tz=timezone.utc)
        ),
        "target": {
            "node_id": node_id,
            "target_id": target_id,
            "target_generation": target_generation,
        },
        "operation": {"family": family, "verb": verb},
        "authority": dict(authority),
        "payload": dict(payload),
        "payload_sha256": payload_digest(payload),
        "expected_sequence": int(expected_sequence),
    }
    return validate_envelope(raw)


# ── the node processor (§8, in order) ────────────────────────────────


class NodeCommandProcessor:
    """Executes envelopes on the node, §8 processing order EXACTLY.

    Every injectable exists so tests can prove the order without tmux;
    production defaults reach the real chokepoints and the real audit.
    """

    def __init__(
        self,
        *,
        node_id: str,
        targets: Any,
        ledger: Any,
        runner: Optional[Callable[..., Any]] = None,
        audit: Optional[Callable[..., int]] = None,
        text_transport: Optional[Callable[..., Any]] = None,
        keys_transport: Optional[Callable[..., Any]] = None,
        wall_now: Callable[[], datetime] = _utc_now,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.node_id = str(node_id)
        self.targets = targets
        self.ledger = ledger
        self._runner = runner
        self._audit = audit
        self._text_transport = text_transport
        self._keys_transport = keys_transport
        self._wall_now = wall_now
        self._clock = clock
        self._sequence_locks: dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()
        self.executions = 0  # test/metric seam: real chokepoint entries

    def _sequence_lock(self, key: str) -> threading.Lock:
        with self._locks_guard:
            lock = self._sequence_locks.get(key)
            if lock is None:
                lock = self._sequence_locks[key] = threading.Lock()
            return lock

    # receipt craft ------------------------------------------------------

    def _receipt(
        self,
        env: Mapping[str, Any],
        *,
        state: str,
        outcome: str,
        applied_sequence: Optional[int] = None,
        authority_basis: str = "none",
        node_audit_id: Optional[int] = None,
        error: Optional[str] = None,
        revoked: bool = False,
    ) -> dict[str, Any]:
        return {
            "receipt_schema": RECEIPT_SCHEMA,
            "receipt_id": "receipt_" + uuid.uuid4().hex[:16],
            "command_id": env["command_id"],
            "node_id": self.node_id,
            "target_id": env["target"]["target_id"],
            "target_generation": env["target"]["target_generation"],
            "state": state,
            "outcome": outcome,
            "applied_sequence": applied_sequence,
            "executed_at": _iso_z(self._wall_now()),
            "payload_sha256": env["payload_sha256"],
            "payload_head": env["payload_head"],
            "policy_version": env["authority"]["policy_version"],
            "authority_basis": authority_basis,
            "node_audit_id": node_audit_id,
            "error": error,
            "revoked": revoked,
            "ledger_epoch": self.ledger.epoch,
        }

    def _persist(
        self,
        env: Mapping[str, Any],
        receipt: dict[str, Any],
        *,
        seq_key: str = "",
        advance: bool = False,
    ) -> dict[str, Any]:
        self.ledger.commit(
            env["command_id"], receipt, target_id=seq_key, advance_sequence=advance
        )
        return receipt

    # the order ----------------------------------------------------------

    def process(self, envelope: Any) -> dict[str, Any]:
        from .. import coder_steering

        # 1. authenticated upstream (node link / hub session); validate
        #    protocol + policy versions here.
        env = validate_envelope(envelope)
        if env["authority"]["policy_version"] != POLICY_VERSION:
            return self._persist(
                env,
                self._receipt(
                    env,
                    state="refused",
                    outcome="policy_version_mismatch",
                    error=(
                        f"node speaks {POLICY_VERSION}, envelope carries "
                        f"{env['authority']['policy_version']}"
                    ),
                ),
            )

        # 2. a known command_id returns its existing receipt, verbatim.
        existing = self.ledger.get(env["command_id"])
        if existing is not None:
            return existing

        # 3. reject expired commands before touching anything.
        expires = _parse_iso(env["expires_at"])
        if expires is None or self._wall_now() > expires:
            return self._persist(
                env,
                self._receipt(
                    env,
                    state="refused",
                    outcome="command_expired",
                    error="the command expired before execution",
                ),
            )

        verb = env["operation"]["verb"]
        payload = env["payload"]
        session_key = str(payload.get("session_key") or "")
        if verb in PANE_VERBS or verb == "terminal.disarm":
            if not session_key:
                return self._persist(
                    env,
                    self._receipt(
                        env,
                        state="refused",
                        outcome="session_key_required",
                        error="steering verbs require payload.session_key",
                    ),
                )

        # terminal.disarm revokes authority: it must never be blocked by
        # a recycled/gone pane, so it resolves no target.
        if verb == "terminal.disarm":
            return self._execute_and_persist(env, pane_id=None)

        # 4. resolve the immutable target and verify its generation.
        pane_id: Optional[str] = None
        seq_key = env["target"]["target_id"]
        if verb in PANE_VERBS:
            verified = self.targets.verify(
                env["target"]["target_id"], env["target"]["target_generation"]
            )
            if verified["status"] in ("tmux_absent", "error"):
                # Transient, pre-execution: refuse WITHOUT persisting so a
                # retry of the same command may still execute once.
                return self._receipt(
                    env,
                    state="refused",
                    outcome=verified["status"],
                    error=str(verified.get("detail") or verified["status"]),
                )
            if verified["status"] == "target_gone":
                return self._persist(
                    env,
                    self._receipt(
                        env,
                        state="refused",
                        outcome="target_gone",
                        error=str(verified.get("detail") or "target gone"),
                    ),
                )
            if verified["status"] == "generation_mismatch":
                # The recycled-pane crown case: refuse, type nothing, and
                # revoke the applicable grant so nothing else types either.
                revoked = coder_steering.disarm(session_key) if session_key else False
                return self._persist(
                    env,
                    self._receipt(
                        env,
                        state="refused",
                        outcome="generation_mismatch",
                        error=str(verified.get("detail") or "generation mismatch"),
                        revoked=revoked,
                    ),
                )
            pane_id = verified["pane_id"]
        else:
            seq_key = f"{NODE_TARGET_ID}:{self.node_id}"

        # 5. node-side hard prerequisites held above; the shared policy
        #    decision rides the envelope and is consumed (not re-resolved)
        #    inside the chokepoint via decode_decision.
        # 6. serialize against the target's expected sequence.
        with self._sequence_lock(seq_key):
            expected = int(self.ledger.next_sequence(seq_key))
            if env["expected_sequence"] != expected:
                return self._persist(
                    env,
                    self._receipt(
                        env,
                        state="refused",
                        outcome="sequence_conflict",
                        error=(
                            f"expected_sequence {env['expected_sequence']} is not the "
                            f"target's next sequence {expected} — nothing was typed"
                        ),
                    ),
                    seq_key=seq_key,
                )
            # 7–9 under the same serialization window.
            return self._execute_and_persist(env, pane_id=pane_id, seq_key=seq_key)

    # step 7 (execute through the chokepoints) + 8 (persist) + 9 (return)
    def _execute_and_persist(
        self,
        env: dict[str, Any],
        *,
        pane_id: Optional[str],
        seq_key: str = "",
    ) -> dict[str, Any]:
        from .. import coder_factory, coder_steering

        verb = env["operation"]["verb"]
        payload = env["payload"]
        session_key = str(payload.get("session_key") or "")
        policy_snapshot = decode_decision(env["authority"])
        operation = describe_operation(
            operation_id=f"command:{env['command_id']}",
            family=env["operation"]["family"],
            effect_class="terminal/type_text_and_keys",
            actor="owner",
            destination=pane_id or env["target"]["target_id"],
            data_classes=("typed_text",) if verb == "terminal.text" else ("key_events",),
            resource_scope=session_key or None,
            fixed_destination=bool(pane_id),
            consequence="execute_now",
        ).to_dict()

        self.executions += 1
        kwargs: dict[str, Any] = {"runner": self._runner}
        if self._audit is not None:
            kwargs["audit"] = self._audit
        if verb == "terminal.text":
            if self._text_transport is not None:
                kwargs["transport"] = self._text_transport
            result = coder_steering.deliver(
                session_key,
                str(payload.get("text") or ""),
                current_target=pane_id,
                agent=str(payload.get("agent") or ""),
                submit=bool(payload.get("submit", True)),
                expected_pane_id=pane_id,
                operation=operation,
                policy_snapshot=policy_snapshot,
                **kwargs,
            )
            basis = policy_snapshot["authority_basis"]
        elif verb == "terminal.keys":
            if self._keys_transport is not None:
                kwargs["transport"] = self._keys_transport
            result = coder_steering.deliver_keys(
                session_key,
                payload.get("keys"),
                current_target=pane_id,
                agent=str(payload.get("agent") or ""),
                expected_pane_id=pane_id,
                operation=operation,
                policy_snapshot=policy_snapshot,
                **kwargs,
            )
            basis = policy_snapshot["authority_basis"]
        elif verb == "terminal.disarm":
            released = coder_steering.disarm(session_key)
            result = {"status": "disarmed", "released": released}
            basis = "authenticated_owner"
        elif verb == "factory.kill":
            result = coder_factory.kill(
                session_key,
                current_target=pane_id,
                scope=str(payload.get("scope") or "pane"),
                agent=str(payload.get("agent") or ""),
                **kwargs,
            )
            basis = "armed_pane_grant"
        elif verb == "factory.spawn":
            result = coder_factory.spawn(
                str(payload.get("name") or ""),
                command=payload.get("command"),
                **kwargs,
            )
            basis = "authenticated_owner"
        else:  # factory.rename
            result = coder_factory.rename(
                str(payload.get("target_session") or ""),
                str(payload.get("new_name") or ""),
                **kwargs,
            )
            basis = "authenticated_owner"

        status = str(result.get("status") or "error")
        if status in _SUCCEEDED:
            state = "succeeded"
        elif status in _FAILED:
            state = "failed"
        else:
            state = "refused"
        # Succeeded/failed consume the sequence slot (keystrokes may have
        # landed); pre-typing refusals leave it for a corrected resend.
        advance = bool(seq_key) and state in ("succeeded", "failed")
        receipt = self._receipt(
            env,
            state=state,
            outcome=status,
            applied_sequence=env["expected_sequence"] if advance else None,
            authority_basis=basis,
            node_audit_id=result.get("audit_id"),
            error=str(result.get("detail")) if result.get("detail") else None,
            revoked=bool(result.get("revoked")),
        )
        return self._persist(env, receipt, seq_key=seq_key, advance=advance)

    def reconcile(self, command_id: str) -> dict[str, Any]:
        """§8.2: the stored receipt if this node executed the command;
        otherwise a typed unknown carrying the ledger epoch so the hub
        can tell "never executed" from "ledger lost in a reset"."""
        stored = self.ledger.get(str(command_id))
        if stored is not None:
            return stored
        return {
            "command_id": str(command_id),
            "reconcile": "unknown_command",
            "ledger_epoch": self.ledger.epoch,
        }


# ── the hub service ──────────────────────────────────────────────────


class HubCommandService:
    """Hub side: stamp authority ONCE, dispatch (inline to the local
    node, queued for a remote claim), and keep the aggregate Receipt.

    The remote queue is memory-only on purpose: the hub database never
    retains a full payload (§8.1). A queue lost to a hub restart
    reconciles honestly as ``not_executed``.
    """

    def __init__(
        self,
        *,
        repo: Any,
        processor: NodeCommandProcessor,
        local_node_id: str = "local",
        mode_loader: Optional[Callable[[], str]] = None,
        grant_lookup: Optional[Callable[[str], Optional[dict[str, Any]]]] = None,
        wall_now: Callable[[], datetime] = _utc_now,
        default_ttl_seconds: int = DEFAULT_COMMAND_TTL_SECONDS,
    ) -> None:
        self.repo = repo
        self.processor = processor
        self.local_node_id = str(local_node_id)
        self._mode_loader = mode_loader
        self._grant_lookup = grant_lookup
        self._wall_now = wall_now
        self._default_ttl = int(default_ttl_seconds)
        self._queues: dict[str, list[dict[str, Any]]] = {}
        self._queue_lock = threading.Lock()

    # policy -------------------------------------------------------------

    def _mode(self) -> str:
        if self._mode_loader is not None:
            return str(self._mode_loader())
        from ..config import Config

        return str(Config.load().control_mode)

    def _grant(self, session_key: str) -> Optional[dict[str, Any]]:
        if self._grant_lookup is not None:
            return self._grant_lookup(session_key)
        from .. import coder_steering

        return coder_steering.policy_grant(session_key)

    def _authority_for(
        self,
        *,
        verb: str,
        session_key: str,
        destination: str,
        registered: bool,
    ) -> dict[str, Any]:
        """Resolve the shared policy ONCE and encode it onto the wire.
        Factory create/label acts and disarm are audited owner acts —
        exactly the local surface's posture — not policy families."""
        mode = self._mode()
        if verb in STEERING_VERBS:
            operation = describe_operation(
                operation_id=f"command:{verb}:{session_key}",
                family="coder_steering",
                effect_class="terminal/type_text_and_keys",
                actor="owner",
                destination=destination,
                data_classes=("typed_text",)
                if verb == "terminal.text"
                else ("key_events",),
                resource_scope=session_key or None,
                fixed_destination=registered,
                consequence="execute_now",
            )
            decision = resolve_policy(
                operation, mode=mode, source="config", grant=self._grant(session_key)
            )
            snapshot = decision.to_dict()
            return {
                "actor": "owner",
                "control_posture": mode,
                "decision": encode_decision(snapshot),
                "policy_version": POLICY_VERSION,
                "grant_id": session_key
                if snapshot["authority_basis"] == "scoped_grant"
                else None,
            }
        if verb == "factory.kill":
            return {
                "actor": "owner",
                "control_posture": mode,
                "decision": "grant_gate",  # enforced inside coder_factory.kill
                "policy_version": POLICY_VERSION,
                "grant_id": session_key or None,
            }
        return {
            "actor": "owner",
            "control_posture": mode,
            "decision": "allowed_audited_act",
            "policy_version": POLICY_VERSION,
            "grant_id": None,
        }

    # dispatch -----------------------------------------------------------

    def submit(self, request: Any) -> dict[str, Any]:
        """One client command intent → one dispatched envelope.

        The client names WHAT (target, operation, payload, sequence);
        the hub derives every authority fact. A client-supplied
        authority block is refused by name (§8)."""
        if not isinstance(request, Mapping):
            raise CommandRefused("request_malformed", "a command request must be an object")
        if "authority" in request:
            raise CommandRefused(
                "authority_not_client_settable",
                "authority is derived from the authenticated session and "
                "operation policy — remove the authority block",
            )
        operation = request.get("operation")
        if not isinstance(operation, Mapping):
            raise CommandRefused("operation_unknown", "operation must be an object")
        family = str(operation.get("family") or "")
        verb = str(operation.get("verb") or "")
        if (family, verb) not in KNOWN_OPERATIONS:
            raise CommandRefused("operation_unknown", f"unknown operation {family}/{verb}")
        payload = request.get("payload")
        if not isinstance(payload, Mapping):
            raise CommandRefused("payload_malformed", "payload must be an object")
        node_id = str(request.get("node_id") or self.local_node_id)
        local = node_id == self.local_node_id

        if verb in NODE_SCOPED_VERBS:
            target_id = NODE_TARGET_ID
            target_generation = NODE_TARGET_ID
        else:
            target_id = str(request.get("target_id") or "")
            target_generation = str(request.get("target_generation") or "")
            if not target_id or not target_generation:
                raise CommandRefused(
                    "target_incomplete",
                    "target_id and target_generation are required — a mutable "
                    "pane selector cannot address a command",
                )

        command_id = request.get("command_id")
        if command_id is not None:
            try:
                command_id = str(uuid.UUID(str(command_id)))
            except (ValueError, TypeError):
                raise CommandRefused("command_id_invalid", "command_id must be a UUID")
            known = self.repo.get(command_id)
            if known is not None and known.get("receipt"):
                return {
                    "command_id": command_id,
                    "state": "complete",
                    "duplicate": True,
                    "receipt": known["receipt"],
                }

        session_key = str(payload.get("session_key") or "")
        destination = target_id
        registered = False
        if local and verb in PANE_VERBS:
            verified = self.processor.targets.verify(target_id, target_generation)
            if verified["status"] == "ok":
                destination = verified["pane_id"]
                registered = True

        seq_key = (
            f"{NODE_TARGET_ID}:{node_id}" if verb in NODE_SCOPED_VERBS else target_id
        )
        expected_sequence = request.get("expected_sequence")
        if expected_sequence is None:
            if not local:
                raise CommandRefused(
                    "expected_sequence_required",
                    "remote commands must carry expected_sequence",
                )
            expected_sequence = int(self.processor.ledger.next_sequence(seq_key))

        envelope = build_envelope(
            node_id=node_id,
            target_id=target_id,
            target_generation=target_generation,
            family=family,
            verb=verb,
            payload=payload,
            expected_sequence=int(expected_sequence),
            authority=self._authority_for(
                verb=verb,
                session_key=session_key,
                destination=destination,
                registered=registered,
            ),
            command_id=command_id,
            ttl_seconds=int(request.get("expires_in_seconds") or self._default_ttl),
            now=self._wall_now(),
        )
        self.repo.record_sent(
            envelope,
            dispatch_epoch=self.processor.ledger.epoch if local else None,
        )
        if local:
            receipt = self.processor.process(envelope)
            self.repo.attach_receipt(receipt)
            return {
                "command_id": envelope["command_id"],
                "state": "complete",
                "receipt": receipt,
            }
        with self._queue_lock:
            self._queues.setdefault(node_id, []).append(envelope)
        return {"command_id": envelope["command_id"], "state": "sent"}

    # the node-link command leg -------------------------------------------

    def claim_for_node(self, node_id: str) -> list[dict[str, Any]]:
        """Drain this node's queued envelopes/probes (the ``command_source``
        hook the node link consults). Claiming marks the hub half."""
        with self._queue_lock:
            claimed = self._queues.pop(str(node_id), [])
        for item in claimed:
            if item.get("command_id") and item.get("command_schema"):
                self.repo.set_state(item["command_id"], "claimed")
        return claimed

    def record_results(self, node_id: str, results: Any) -> dict[str, Any]:
        """The node's results leg: receipts and reconcile answers,
        joined into the hub half by command_id. Idempotent."""
        processed = 0
        for item in results or []:
            if not isinstance(item, Mapping):
                continue
            command_id = str(item.get("command_id") or "")
            if not command_id:
                continue
            row = self.repo.get(command_id)
            if row is None or str(row.get("node_id")) != str(node_id):
                continue
            if item.get("receipt_schema") == RECEIPT_SCHEMA:
                self.repo.attach_receipt(dict(item))
                processed += 1
                continue
            if item.get("reconcile") == "unknown_command" and not row.get("receipt"):
                self.repo.set_state(
                    command_id,
                    self._absence_state(row, str(item.get("ledger_epoch") or "")),
                )
                processed += 1
        return {"ok": True, "processed": processed}

    @staticmethod
    def _absence_state(row: Mapping[str, Any], ledger_epoch: str) -> str:
        if str(row.get("hub_state")) == "sent":
            return "not_executed"  # never claimed: it cannot have run
        dispatch_epoch = str(row.get("dispatch_epoch") or "")
        if dispatch_epoch and ledger_epoch == dispatch_epoch:
            return "not_executed"  # same ledger, no row: never persisted
        return "indeterminate_after_node_reset"

    # the aggregate Receipt -------------------------------------------------

    def receipt(self, command_id: str) -> Optional[dict[str, Any]]:
        """The joined Receipt, reconciling by command_id when the node
        half is missing (§8.2). Never a blind retry."""
        row = self.repo.get(str(command_id))
        if row is None:
            return None
        if row.get("receipt"):
            return row
        if str(row.get("node_id")) == self.local_node_id:
            answer = self.processor.reconcile(str(command_id))
            if answer.get("receipt_schema") == RECEIPT_SCHEMA:
                self.repo.attach_receipt(answer)
            else:
                self.repo.set_state(
                    str(command_id),
                    self._absence_state(row, str(answer.get("ledger_epoch") or "")),
                )
            return self.repo.get(str(command_id))
        with self._queue_lock:
            queued = any(
                item.get("command_id") == str(command_id)
                for item in self._queues.get(str(row.get("node_id")), [])
            )
        if not queued and str(row.get("hub_state")) == "sent":
            # Never claimed and no longer queued (a hub restart dropped the
            # memory queue): it cannot have executed.
            self.repo.set_state(str(command_id), "not_executed")
            return self.repo.get(str(command_id))
        if not queued and str(row.get("hub_state")) == "claimed":
            # Lost after send: recorded unknown until the node answers the
            # reconcile probe on its next claim.
            self.repo.set_state(str(command_id), "unknown")
            with self._queue_lock:
                self._queues.setdefault(str(row.get("node_id")), []).append(
                    {"kind": "reconcile", "command_id": str(command_id)}
                )
            return self.repo.get(str(command_id))
        return row


__all__ = [
    "COMMAND_SCHEMA",
    "CommandRefused",
    "DEFAULT_COMMAND_TTL_SECONDS",
    "HubCommandService",
    "KNOWN_OPERATIONS",
    "NODE_TARGET_ID",
    "NodeCommandProcessor",
    "PAYLOAD_HEAD_CHARS",
    "RECEIPT_SCHEMA",
    "build_envelope",
    "decode_decision",
    "encode_decision",
    "payload_digest",
    "payload_head",
    "validate_envelope",
]
