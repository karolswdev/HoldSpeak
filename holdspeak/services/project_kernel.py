"""The complete kernel path for the Room's admitted operations (PHILO-9-02).

Article XI as the owner ruled it for the Room (Q1 by effect, Q2 bounded
delegation): one ADMITTED logical operation is one kernel operation with one
terminal receipt. The path is the desk's (``services/desk_kernel.py``), with
three additions the Room needs:

1. **Replay by command key.** A call that carries ``command_id`` is keyed from
   it (``<name>:cmd:<command_id>`` and a native id derived from the principal,
   the name and the key), so a retry reaches the SAME kernel operation through
   the kernel's own replay (``kernel/journal.py``, by principal and key): the
   same key and payload answer the original operation and receipt; a changed
   payload is refused ``idempotency_conflict``. A call without a key is a new
   operation every time.
2. **A handle for the service.** While the bound method runs, :func:`current`
   answers the operation's :class:`KernelHandle`. A method whose domain write
   must commit WITH its receipt (the delivery record, the stop request, the
   policy's owner operation) ends the operation itself through
   :meth:`KernelHandle.terminal` with an ``effect`` (one transaction,
   ``journal_atomic.transition_and_receipt``); a method that starts
   asynchronous work (the steward's run) :meth:`KernelHandle.detach` es it, and
   its daemon writes the one terminal receipt later.
3. **One answer per command** (round three, Muad'Dib's ruling A). A write
   that carries ``command_id`` records its whole answer in story 01's
   ``project_commands.result_json`` and ends its operation (terminal state and
   receipt) in the SAME transaction as its domain write (:func:`answered`); a
   replay of the key answers that record. A failure anywhere in that
   transaction rolls back all three.
4. **Take-over of an abandoned operation.** A replay that finds its operation
   non-terminal while no call in this process is executing it (the terminal
   transaction failed and rolled back) executes it again and closes it ONCE
   (the strict revision check picks one winner).

Nothing here decides what is admitted: the descriptor does.
"""
from __future__ import annotations
from holdspeak.timestamps import utc_now_iso

import json
import threading
import time
import uuid
from contextvars import ContextVar
from typing import Any, Callable, Mapping

from ..kernel import project as rooms
from ..kernel.desk_broker import STRICT_CONFLICTS, journal_receipt
from ..kernel.model import FINAL_STATES, KernelRefused
from ..principals import Principal, PrincipalKind
from .desk_kernel import DeskKernelRefused, _attach, _outcome, target_ref
from .errors import ServiceError

_NODE = Principal(PrincipalKind.NODE, rooms.PROJECT_EXECUTOR)
#: The namespace the command-keyed native ids are derived in.
_NAMESPACE = uuid.UUID("4f8a3d2e-9c61-4b7e-a0d5-2c1f9e7b6a43")
_FORBIDDEN_STATUS = ("project_delegation", "principal", "owner_principal", "declared_capability", rooms.RUN_OWNER_REQUIRED)

_CURRENT: ContextVar["KernelHandle | None"] = ContextVar("project_kernel_current", default=None)
_IN_FLIGHT: set[str] = set()
_IN_FLIGHT_LOCK = threading.Lock()


class ProjectKernelRefused(DeskKernelRefused):
    """The kernel refused (or ended unsuccessfully) an admitted Room operation.

    The code is the kernel's rule (``project_delegation_required``,
    ``steward_run_owner_required``, ``idempotency_conflict`` ...); the context
    carries ``operation_id`` and the terminal ``receipt``. MCP answers
    ``{error, code, operation_id, receipt}``; HTTP answers the code with its
    status (403 for authority, 400 for arguments, 404 for a missing target,
    409 otherwise).
    """

    def __init__(self, code: str, operation: str, *, operation_id: str, receipt: Any,
                 status: int | None = None) -> None:
        if status is None:
            status = (400 if code == "invalid_arguments"
                      else 404 if code == "not_found"
                      else 403 if code.startswith(_FORBIDDEN_STATUS)
                      else 409)
        super().__init__(code, operation, operation_id=operation_id, receipt=receipt, status=status)


class KernelHandle:
    """One admitted Room operation, claimed, while its bound method runs."""

    def __init__(self, broker: Any, name: str, operation_id: str, revision: int, target: str,
                 principal: Any) -> None:
        self.broker = broker
        self.name = name
        self.operation_id = operation_id
        self.revision = revision
        self.target = target
        self.principal = principal
        self.closed = False
        self.detached = False
        self.receipt: Any = None
        #: A replay of an operation already admitted under this key: the
        #: method answers from what it recorded and writes nothing.
        self.replay = False
        self.write_failed = False
        #: Set while :func:`answered` ends the operation inside the service's
        #: own transaction; the receipt's journal entry follows the commit.
        self.terminal_in_txn = False
        self._journal: tuple[Any, str, str] | None = None

    @property
    def store(self) -> Any:
        return self.broker.store

    def operation(self) -> dict[str, Any]:
        return self.broker.store.operation(self.operation_id) or {}

    def detach(self) -> None:
        """The terminal receipt belongs to asynchronous work now (the steward's run)."""
        self.detached = True

    def terminal(self, state: str, outcome: str, result_ref: str = "", *,
                 effect: Callable[[Any], None] | None = None) -> Any:
        """The terminal state and its receipt, with ``effect`` in the SAME transaction.

        A lost race (another winner already ended it) re-reads the winner's
        receipt and changes nothing; an exception inside ``effect`` rolls all
        of it back and propagates.
        """
        try:
            operation, receipt = self.broker.store.transition_and_receipt(
                self.operation_id, self.revision, state, outcome, result_ref, strict=True, effect=effect,
            )
        except KernelRefused as exc:
            if exc.reason not in STRICT_CONFLICTS:
                raise
            self.closed = True
            self.receipt = self.broker.store.receipt(self.operation_id)
            raise
        except ServiceError:
            raise  # a domain refusal inside the effect: rolled back; the caller closes it refused
        except Exception:
            # The terminal transaction itself failed and rolled back: nothing
            # was written. The operation stays non-terminal (no invented
            # outcome); a replay of its key takes it over and closes it once.
            self.write_failed = True
            raise
        journal_receipt(self.broker.store, operation, outcome, result_ref)
        self.closed = True
        self.receipt = dict(receipt) if receipt is not None else None
        return self.receipt

    def close_in(self, conn: Any) -> None:
        """Succeeded, with its receipt, inside the caller's write transaction (ruling A)."""
        from ..kernel.journal_atomic import transition_and_receipt_in

        result_ref = _result_ref(self.target)
        operation, receipt = transition_and_receipt_in(
            conn, self.broker.store, self.operation_id, self.revision, "succeeded", "succeeded", result_ref,
            strict=True,
        )
        self.closed = True
        self.receipt = dict(receipt)
        self._journal = (operation, "succeeded", result_ref)

    def committed(self) -> None:
        """After the service's commit: the receipt's journal entry (as :meth:`terminal` writes it)."""
        self.terminal_in_txn = False
        if self._journal is not None:
            operation, outcome, result_ref = self._journal
            self._journal = None
            journal_receipt(self.broker.store, operation, outcome, result_ref)

    def kernel(self) -> dict[str, Any]:
        return {"operation_id": self.operation_id, "receipt": self.receipt}


def current() -> KernelHandle | None:
    """The operation the bound method is running under (``None`` off the kernel path)."""
    return _CURRENT.get()


def _broker(database: Any) -> Any:
    from ..kernel.runtime import _configure

    return _configure(database)


def target_for(name: str, args: Mapping[str, Any]) -> str:
    """The operation's journal-safe target: what it acts on."""
    for key, kind in (("send_id", "channel_send"), ("document_ref", "document"), ("run_id", "steward_run"), ("update_id", "project_update"),
                      ("destination_id", "channel_destination"), ("watch_id", "watch"),
                      ("step_id", "steward_step"), ("project_id", "project")):
        if args.get(key):
            return target_ref(kind, args.get(key))
    if name in {"connection.recheck", "project.door.count"}:
        return target_ref("connection", args.get("provider_id") or args.get("provider") or "unknown")
    if name == "project.door.create":
        return target_ref("project", "door")
    return target_ref("desk", name)


def _keys(principal: Any, name: str, payload: Mapping[str, Any]) -> tuple[str, str]:
    """The native id and the idempotency key: derived from ``command_id`` when there is one."""
    command_id = payload.get("command_id")
    if command_id:
        material = f"{getattr(principal, 'name', '')}:{getattr(principal, 'identity', '')}:{name}:{command_id}"
        return str(uuid.uuid5(_NAMESPACE, material)), f"{name}:cmd:{command_id}"
    native_id = str(uuid.uuid4())
    return native_id, f"{name}:{native_id}"


def _raw(name: str, native_id: str, key: str, target: str, payload: Mapping[str, Any],
         parent_operation_id: str) -> dict[str, Any]:
    raw = {
        "request_schema": 1, "request_id": native_id, "idempotency_key": key,
        "operation": {"name": name, "version": 1}, "target": {"ref": target},
        "arguments": {"native_id": native_id, "payload": json.loads(json.dumps(dict(payload), default=str))},
        "placement": rooms.PROJECT_PLACEMENT,
    }
    if parent_operation_id:
        raw["parent_operation_id"] = parent_operation_id
    return raw


def _refused(name: str, broker: Any, operation_id: str, receipt: Any = None) -> ProjectKernelRefused:
    receipt = receipt or broker.store.receipt(operation_id) or {}
    code = str(receipt.get("outcome") or "refused")
    if code == "idempotency_payload_mismatch":
        code = "idempotency_conflict"
    return ProjectKernelRefused(code, name, operation_id=operation_id, receipt=receipt)


def _in_flight(operation_id: str, on: bool) -> None:
    with _IN_FLIGHT_LOCK:
        (_IN_FLIGHT.add if on else _IN_FLIGHT.discard)(operation_id)


def _busy(flight: str) -> bool:
    with _IN_FLIGHT_LOCK:
        return flight in _IN_FLIGHT


def _claim_flight(flight: str) -> bool:
    """True when this caller now owns the key's flight (no other caller in this process has it)."""
    with _IN_FLIGHT_LOCK:
        if flight in _IN_FLIGHT:
            return False
        _IN_FLIGHT.add(flight)
        return True


def run(
    database: Any, principal: Any, name: str, args: Mapping[str, Any],
    call: Callable[[dict[str, Any]], Any], *,
    parent_operation_id: str = "",
) -> tuple[Any, dict[str, Any]]:
    """Submit, approve, claim, execute once, receipt -- inside this call.

    *call* receives the payload and performs the work (it may end the
    operation itself, or detach it). A replay calls it again under a
    handle marked ``replay``: the method answers from what it recorded
    (a ProjectService write, from its command record).
    """
    broker = _broker(database)
    payload = dict(args)
    native_id, key = _keys(principal, name, payload)
    target = target_for(name, payload)
    # The key is in flight from BEFORE its submission: a concurrent caller
    # with the same key waits for this one instead of taking it over.
    flight = f"{getattr(principal, 'identity', '')}\x00{key}"
    owner = _claim_flight(flight)
    try:
        with rooms.project_path():
            handle = broker.submit(_raw(name, native_id, key, target, payload, parent_operation_id), principal)
        operation_id = str(handle.get("operation_id") or "")
        state = str(handle.get("state") or "")
        if state == "refused" and handle.get("receipt") is not None:
            raise _refused(name, broker, operation_id, handle.get("receipt"))
        if state != "awaiting_decision" or not owner:
            return _replayed(broker, principal, name, operation_id, payload, target, call, flight, owner)
        return _execute(broker, principal, name, operation_id, int(handle["revision"]), native_id,
                        target, payload, call)
    finally:
        if owner:
            _in_flight(flight, False)


def _execute(broker: Any, principal: Any, name: str, operation_id: str, revision: int, native_id: str,
             target: str, payload: dict[str, Any], call: Callable[[dict[str, Any]], Any]) -> tuple[Any, dict[str, Any]]:
    with rooms.project_path():
        try:
            broker.decide(operation_id, "approve", revision, principal)
        except KernelRefused as exc:
            raise _refused(name, broker, operation_id, exc.receipt) from exc
        claimed = broker.claim(_NODE, native_id)
    if not claimed.get("operations"):
        raise _refused(name, broker, operation_id, claimed.get("refusal"))
    handle = KernelHandle(broker, name, operation_id, int(claimed["operations"][0]["revision"]), target, principal)
    return _call(broker, name, handle, payload, call)


def _call(broker: Any, name: str, handle: KernelHandle, payload: dict[str, Any],
          call: Callable[[dict[str, Any]], Any]) -> tuple[Any, dict[str, Any]]:
    token = _CURRENT.set(handle)
    try:
        # Ruling D: the Room's trusted path lasts while the service executes,
        # so a child it submits (a scheduled model draft's inference.invoke)
        # is admitted under the same rules as the operation itself.
        with rooms.project_path():
            result = call(payload)
    except KernelRefused as lost:
        _CURRENT.reset(token)
        token = None
        _unwind(handle)
        if lost.reason not in STRICT_CONFLICTS:
            raise
        # Another caller of this key closed it first: its outcome answers.
        operation = broker.store.operation(handle.operation_id) or {}
        receipt = broker.store.receipt(handle.operation_id)
        if str(operation.get("state")) != "succeeded":
            raise _refused(name, broker, handle.operation_id, receipt) from lost
        return _answer(broker, handle.principal, name, operation, handle.target, payload, call, receipt)
    except Exception as exc:
        _unwind(handle, exc)
        if not handle.closed and not handle.detached and not handle.write_failed:
            state, outcome = _room_outcome(exc)
            try:
                handle.terminal(state, outcome)
            except KernelRefused:
                pass
        receipt = handle.receipt if handle.receipt is not None else broker.store.receipt(handle.operation_id)
        _attach(exc, {"operation_id": handle.operation_id, "receipt": receipt})
        raise
    finally:
        if token is not None:
            _CURRENT.reset(token)
    handle.committed()
    if handle.detached and not handle.closed:
        return result, {"operation_id": handle.operation_id, "receipt": None, "state": "claimed"}
    if not handle.closed:
        try:
            handle.terminal("succeeded", "succeeded", _result_ref(handle.target))
        except KernelRefused as lost:
            if lost.reason not in STRICT_CONFLICTS:
                raise
            # Another caller of this key closed it first: its outcome stands.
            if str((broker.store.operation(handle.operation_id) or {}).get("state")) != "succeeded":
                raise _refused(name, broker, handle.operation_id, handle.receipt) from lost
    return result, handle.kernel()


def _unwind(handle: KernelHandle, exc: BaseException | None = None) -> None:
    """The service's transaction rolled back after :func:`answered` began: nothing was written.

    A domain refusal (a ServiceError) is closed refused as usual; any other
    failure inside the terminal transaction leaves the operation non-terminal
    (no invented outcome) for a replay of its key to take over and close once.
    """
    if not handle.terminal_in_txn:
        return
    handle.terminal_in_txn = False
    handle._journal = None
    if handle.broker.store.receipt(handle.operation_id) is not None:
        return
    handle.closed = False
    handle.receipt = None
    if exc is not None and not isinstance(exc, (ServiceError, KernelRefused)):
        handle.write_failed = True


def _room_outcome(exc: BaseException) -> tuple[str, str]:
    """The desk's mapping, plus the Room's own named domain refusals (never "failed")."""
    named = {"PublishedUpdateError": "published_update", "UpdateNotPublishedError": "update_not_published",
             "ActiveRunExistsError": "active_run_exists", "StewardDisabledError": "steward_disabled",
             "CooldownActiveError": "cooldown_active"}
    code = named.get(type(exc).__name__)
    if code is not None:
        return "refused", code
    return _outcome(exc)


def _result_ref(target: str) -> str:
    return target if target and not target.startswith("desk:") else ""


def _replayed(broker: Any, principal: Any, name: str, operation_id: str, payload: dict[str, Any], target: str,
              call: Callable[[dict[str, Any]], Any], flight: str, owner: bool) -> tuple[Any, dict[str, Any]]:
    """The same principal, key and payload: the original operation answers."""
    deadline = time.monotonic() + 30.0
    while True:
        operation = broker.store.operation(operation_id) or {}
        state = str(operation.get("state") or "")
        if state in FINAL_STATES:
            receipt = broker.store.receipt(operation_id)
            if state != "succeeded":
                if (name in rooms.SETTLED_ROW_REPLAY and state in {"indeterminate", "failed"}
                        and _settled_row(broker, operation_id)):
                    # PHILO-10-01 (design section 4a, seam 3): a send that ended
                    # UNKNOWN or FAILED answers its settled row, not a refusal.
                    return _answer(broker, principal, name, operation, target, payload, call, receipt)
                raise _refused(name, broker, operation_id, receipt)
            return _answer(broker, principal, name, operation, target, payload, call, receipt)
        if name in rooms.ASYNC_OPERATIONS and state == "claimed" and _durable(broker, name, operation_id):
            # The steward's work is running AND its durable row exists: its
            # pending handle answers (Codex Astra r1 finding 4: never a
            # handle without its run).
            return _answer(broker, principal, name, operation, target, payload, call, None)
        if state in {"awaiting_decision", "awaiting_execution", "claimed"} and (owner or _claim_flight(flight)):
            # No caller in this process is executing it (its terminal write
            # rolled back, or its caller is gone): take it over, close it once.
            try:
                return _take_over(broker, principal, name, operation, payload, target, call)
            finally:
                if not owner:
                    _in_flight(flight, False)
        if time.monotonic() > deadline:
            raise ProjectKernelRefused("operation_in_progress", name, operation_id=operation_id, receipt=None, status=409)
        time.sleep(0.02)


_NO_RESULT = object()

#: The command kind each admitted Room write records its answer under
#: (story 01's ``project_commands.command_kind``).
COMMAND_KINDS: dict[str, str] = {
    "project.archive": "archive_project",
    "project.link": "associate_meeting",
    "project.unlink": "disassociate_meeting",
    "project.resource.add": "add_resource",
    "project.resource.remove": "remove_resource",
    "project.add_suggested_source": "add_source_watch",
    "project.publish_update": "publish_update",
    "project.decide_proposal": "decide_proposal",
    "project.accept_review": "accept_review",
    "project.configure_steward": "configure_steward",
}


#: The writes whose method has no replay of its own: the kernel's replay
#: answers their record directly. Every other kind's method answers a replay
#: from the same record itself (story 01's ``_check_idempotency``).
RECORD_ANSWERS = frozenset({"project.publish_update", "project.configure_steward"})


def answered(conn: Any, *, command_id: str | None, project_id: str, command_kind: str, request_hash: str,
             answer: Any, close: bool = True) -> None:
    """THE one answer per command, and the running operation's end, in the caller's transaction.

    Records *answer* (the whole response) in ``project_commands.result_json``
    under *command_id*; when the admitted operation of this command kind is
    running this call, ends it (succeeded, with its receipt) in the SAME
    transaction (ruling A). A failure anywhere rolls back the domain write, the
    answer and the receipt together.
    """
    handle = current()
    closing = (close and handle is not None and not handle.replay and not handle.closed
               and not handle.detached and COMMAND_KINDS.get(handle.name) == command_kind)
    if closing:
        handle.terminal_in_txn = True
    if command_id:
        _record_answer(conn, command_id, project_id, command_kind, request_hash, answer)
    if closing:
        handle.close_in(conn)


def request_hash(payload: Mapping[str, Any]) -> str:
    """The request's hash, as story 01 records it (``project_commands.request_hash``)."""
    import hashlib

    material = json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]


def _record_answer(conn: Any, command_id: str, project_id: str, command_kind: str, request_hash: str,
                   answer: Any) -> None:

    existing = conn.execute("SELECT command_kind, status FROM project_commands WHERE id=?", (command_id,)).fetchone()
    if existing is not None and existing["status"] == "completed" and existing["command_kind"] != command_kind:
        from .errors import ConflictError

        raise ConflictError("idempotency conflict: this command_id answered another command",
                            code="idempotency_conflict", context={"command_id": command_id})
    now_iso = utc_now_iso()
    conn.execute(
        """INSERT INTO project_commands (
               id, project_id, command_kind, request_hash, status, result_json, completed_at, created_at
           ) VALUES (?, ?, ?, ?, 'completed', ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET
               status = 'completed', result_json = excluded.result_json, completed_at = excluded.completed_at""",
        (command_id, project_id, command_kind, request_hash, json.dumps(answer, ensure_ascii=False, default=str),
         now_iso, now_iso),
    )


def _recorded_answer(broker: Any, name: str, payload: Mapping[str, Any]) -> Any:
    command_id, kind = payload.get("command_id"), COMMAND_KINDS.get(name)
    if not command_id or kind is None or name not in RECORD_ANSWERS:
        return _NO_RESULT
    with broker.store._connection() as conn:
        row = conn.execute("SELECT result_json FROM project_commands WHERE id=? AND command_kind=? AND status='completed'",
                           (str(command_id), kind)).fetchone()
    return json.loads(row[0]) if row is not None and row[0] else _NO_RESULT


def _settled_row(broker: Any, operation_id: str) -> bool:
    """A ``channel_sends`` row of this send operation that settled (sent, failed, unknown)."""
    with broker.store._connection() as conn:
        return conn.execute("SELECT 1 FROM channel_sends WHERE send_operation_id=? AND state IN "
                            "('sent','failed','unknown')", (operation_id,)).fetchone() is not None


def _durable(broker: Any, name: str, operation_id: str) -> bool:
    """Whether an asynchronous operation's pending handle is backed by its durable row."""
    if name != "project.run_steward":
        return True
    with broker.store._connection() as conn:
        return conn.execute("SELECT 1 FROM steward_runs WHERE operation_id=?", (operation_id,)).fetchone() is not None


def _answer(broker: Any, principal: Any, name: str, operation: Mapping[str, Any], target: str,
            payload: dict[str, Any], call: Callable[[dict[str, Any]], Any], receipt: Any) -> tuple[Any, dict[str, Any]]:
    """A replay: the method answers from what it recorded, under a handle that writes nothing."""
    if receipt is not None:
        stored = _recorded_answer(broker, name, payload)
        if stored is not _NO_RESULT:
            # The original answer, recorded with the receipt: nothing runs again.
            return stored, {"operation_id": str(operation["operation_id"]), "receipt": dict(receipt)}
    handle = KernelHandle(broker, name, str(operation["operation_id"]), int(operation["revision"]), target, principal)
    handle.replay = True
    handle.receipt = dict(receipt) if receipt is not None else None
    handle.closed = receipt is not None
    token = _CURRENT.set(handle)
    try:
        with rooms.project_path():
            result = call(payload)
    finally:
        _CURRENT.reset(token)
    kernel = handle.kernel()
    if receipt is None:
        kernel["state"] = str(operation.get("state") or "")
    return result, kernel


def _take_over(broker: Any, principal: Any, name: str, operation: Mapping[str, Any], payload: dict[str, Any],
               target: str, call: Callable[[dict[str, Any]], Any]) -> tuple[Any, dict[str, Any]]:
    """An abandoned operation of this key (its terminal write rolled back): execute it again, close it once."""
    operation_id = str(operation["operation_id"])
    state = str(operation["state"])
    if state == "awaiting_decision":
        return _execute(broker, principal, name, operation_id, int(operation["revision"]),
                        str(operation["native_id"]), target, payload, call)
    if state == "awaiting_execution":
        return _claim_and_call(broker, principal, name, operation, target, payload, call)
    handle = KernelHandle(broker, name, operation_id, int(operation["revision"]), target, principal)
    return _call(broker, name, handle, payload, call)


def _claim_and_call(broker: Any, principal: Any, name: str, operation: Mapping[str, Any], target: str,
                    payload: dict[str, Any], call: Callable[[dict[str, Any]], Any]) -> tuple[Any, dict[str, Any]]:
    with rooms.project_path():
        claimed = broker.claim(_NODE, str(operation["native_id"]))
    if not claimed.get("operations"):
        raise _refused(name, broker, str(operation["operation_id"]), claimed.get("refusal"))
    handle = KernelHandle(broker, name, str(operation["operation_id"]),
                          int(claimed["operations"][0]["revision"]), target, principal)
    return _call(broker, name, handle, payload, call)


def refuse(database: Any, principal: Any, name: str, code: str, args: Any = None) -> dict[str, Any] | None:
    """A refusal receipt for an identifiable consequential attempt refused before the service (R2)."""
    kind = getattr(principal, "kind", None)
    if not isinstance(kind, PrincipalKind) or kind is PrincipalKind.NONE:
        return None
    broker = _broker(database)
    operation_id = "op_" + uuid.uuid4().hex
    raw = {"request_schema": 1, "request_id": operation_id, "idempotency_key": operation_id,
           "operation": {"name": name, "version": 1}, "target": {}, "arguments": {}}
    target = target_for(name, args) if isinstance(args, Mapping) else ""
    handle = broker._refuse_attempt(raw, principal, operation_id, code, unique=True,
                                    provenance={"target_ref": target} if target else None)
    return {"operation_id": handle.get("operation_id"), "receipt": handle.get("receipt")}


def service_error(exc: ServiceError) -> tuple[int, dict[str, Any]]:
    """An HTTP route's status and body fields for a refusal of an admitted Room operation."""
    context = dict(exc.context)
    status = int(context.pop("status", 409))
    return status, {"code": exc.code, "error": exc.detail, **context}
