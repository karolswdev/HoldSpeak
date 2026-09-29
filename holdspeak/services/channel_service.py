"""PHILO-10-01: the Send -- saved destinations, prepare and press, the dispatch boundary.

Built to ``pm/roadmap/holdspeak-philo/phase-10-the-channels/design/send-lifecycle.md``:

* **Prepare** (``channel.prepare``) freezes the destination's target and the
  channel's exact transport bytes in a ``prepared`` row, under the preparer's
  own identity (the owner, or an agent he connected). Nothing leaves.
* **Send** (``channel.send``) is the owner's press. Before any effect it
  re-reads the destination (parked or changed: refused), re-checks the frozen
  digest, and commits the **dispatch boundary** in a transaction of its own
  (``prepared`` -> ``dispatching`` + ``send_operation_id``, or, for the inline
  form, the row inserted ``dispatching``), guarded by the kernel operation
  still being claimed. Only then the effect runs; one **settle** transaction
  moves the row to sent / failed / unknown, writes the history row and the
  kernel's terminal receipt together.
* **Recovery never dispatches again.** A call that finds its row
  ``dispatching`` (a take-over after a lost caller or a failed settle) reads
  the file back or answers UNKNOWN. The reaper and the startup recovery settle
  a silent send in their own terminal transaction
  (``kernel/project.channel_send_ended_effect``); a replay answers the settled
  row (``services/project_kernel._replayed``).
* **Discard** moves ``prepared`` -> ``discarded`` by one conditional write in
  its receipt's transaction; Send and Discard at once: one wins.

The file channel is the one direct writer (``services/channel_contract.py``);
the GitHub, Jira and Confluence channels dispatch each command as a
``subprocess.exec`` child of the send, under the send's authenticated owner
principal, through its broker (``services/channel_cli.py``; PHILO-10-02).
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping, Optional

from holdspeak.db.channels import now_iso, settle_in_transaction
from holdspeak.logging_config import get_logger

from . import channel_contract as contract
from .channel_contract import ChannelRefused, Outcome
from .errors import NotFound, ValidationError

log = get_logger("services.channel")


def _derived_id(prefix: str, operation_id: str) -> str:
    """An id derived from the admitted operation: a replay of the key finds the same row."""
    return prefix + hashlib.sha256(str(operation_id).encode()).hexdigest()[:24]


def _handle() -> Any:
    from . import project_kernel

    handle = project_kernel.current()
    if handle is None:
        raise RuntimeError("an admitted channel operation runs only through the Room's kernel path")
    return handle


class ChannelService:
    """The one service behind every ``channel.*`` operation (HTTP, MCP and the rig reach it)."""

    def __init__(self, db: Any) -> None:
        self._db = db

    # ── views ──────────────────────────────────────────────────────────

    def _destination_view(self, row: Mapping[str, Any]) -> dict[str, Any]:
        target = json.loads(row["target_json"] or "{}")
        account = json.loads(row["account_json"] or "{}")
        synced = bool(row["synced"])
        return {
            "id": row["id"], "name": row["name"], "channel": row["channel"],
            "account": account, "target": target,
            "target_digest": row["target_digest"], "synced": synced, "state": row["state"],
            "badge": contract.channel(row["channel"]).badge(synced), "created_at": row["created_at"],
            "parked_at": row["parked_at"], "connection": self._connection(str(row["channel"]), account),
        }

    def _connection(self, channel: str, account: Mapping[str, Any]) -> Optional[dict[str, Any]]:
        """The Phase 9 connection this destination's account uses, with its B1 state (shown, never the identity).

        A stored read of ``watch_provider_connections`` (no probe): ``connected``,
        ``never_checked``, or the state the last check stored.
        """
        if channel == "github":
            connection_id = "wpc_github"
        elif channel in {"jira", "confluence"}:
            connection_id = f"wpc_{channel}_{account.get('site')}|{account.get('email')}"
        else:
            return None
        row = self._db.automations.get_provider_connection(connection_id)
        if row is None or not row.get("last_checked_at"):
            return {"id": connection_id, "state": "never_checked", "last_checked_at": None}
        state = str(row.get("state") or "")
        display = {"connected": "connected", "disconnected": "owner_action_required",
                   "owner_action_required": "owner_action_required", "unavailable": "unavailable"}.get(state, "degraded")
        return {"id": connection_id, "state": display, "last_checked_at": row.get("last_checked_at")}

    def _send_view(self, row: Mapping[str, Any]) -> dict[str, Any]:
        destination = self._db.channel_destinations.get(row["destination_id"]) or {}
        payload = bytes(row["payload"] or b"")
        return {
            "id": row["id"], "document_ref": row["document_ref"], "destination_id": row["destination_id"],
            "destination_name": destination.get("name"), "channel": row["channel"],
            "badge": contract.channel(row["channel"]).badge(bool(destination.get("synced"))),
            "account": json.loads(row["account_json"] or "{}"), "target": json.loads(row["target_json"] or "{}"),
            "target_digest": row["target_digest"], "payload_digest": row["payload_digest"],
            "size": len(payload), "preview": contract.channel(row["channel"]).preview(payload),
            "prepared_by": {"kind": row["prepared_by_kind"], "identity": row["prepared_by_identity"]},
            "prepare_operation_id": row["prepare_operation_id"], "send_operation_id": row["send_operation_id"],
            "state": row["state"], "reason": row["reason"],
            "proof": json.loads(row["proof_json"]) if row["proof_json"] else None,
            "file_path": row["file_path"], "created_at": row["created_at"],
            "dispatch_started_at": row["dispatch_started_at"], "settled_at": row["settled_at"],
            "dispatch_seq": row["dispatch_seq"],
        }

    def _answer(self, row: Mapping[str, Any]) -> dict[str, Any]:
        view = self._send_view(row)
        return {"send": view, "outcome": view["state"]}

    def _destination(self, destination_id: str) -> dict[str, Any]:
        row = self._db.channel_destinations.get(str(destination_id or ""))
        if row is None:
            # A send to a destination that is not saved: refused before any effect.
            raise ChannelRefused("destination_not_saved", f"No saved destination {destination_id}", status=404)
        return row

    # ── reads (exempt) ───────────────────────────────────────────────────

    def destinations(self, principal: Any, include_parked: bool = False) -> dict[str, Any]:
        rows = self._db.channel_destinations.list(include_parked=bool(include_parked))
        return {"destinations": [self._destination_view(r) for r in rows]}

    def sends(self, principal: Any, update_id: Optional[str] = None, send_id: Optional[str] = None) -> dict[str, Any]:
        if send_id:
            row = self._db.channel_sends.get(send_id)
            if row is None:
                raise NotFound("send", send_id)
            return {"sends": [self._send_view(row)]}
        if update_id:
            rows = self._db.channel_sends.list_for_document(f"project_update:{update_id}")
        else:
            rows = self._db.channel_sends.list_recent()
        return {"sends": [self._send_view(r) for r in rows]}

    def preview(self, principal: Any, update_id: str, destination_id: str) -> dict[str, Any]:
        """What the destination's channel would get: the exact bytes' digest and their readable preview."""
        destination = self._destination(destination_id)
        if destination["state"] != "active":
            raise ChannelRefused("destination_parked", f"Destination {destination_id} is parked")
        document = contract.render_update(self._db, update_id)
        chan = contract.channel(destination["channel"])
        payload = chan.serialize(document)
        self._size(destination["channel"], payload)
        return {"document_ref": document.ref, "title": document.title, "destination_id": destination["id"],
                "channel": destination["channel"], "badge": chan.badge(bool(destination["synced"])),
                "payload_digest": contract.sha256(payload), "size": len(payload), "preview": chan.preview(payload)}

    def check_destination(self, principal: Any, destination_id: str) -> dict[str, Any]:
        """A folder: a local check (it resolves to the saved folder, it is a folder, it is writable).

        A GitHub, Jira or Confluence destination: its stored Phase 9 connection
        state (no probe here; ``connection.recheck`` probes).
        """
        import os

        row = self._destination(destination_id)
        if row["channel"] != "file":
            view = self._destination_view(row)
            state = "parked" if row["state"] != "active" else str((view["connection"] or {}).get("state") or "")
            return {"destination": view, "check": {"state": state, "resolved": None}}
        target = json.loads(row["target_json"] or "{}")
        folder = str(target.get("folder") or "")
        resolved = os.path.realpath(folder) if folder else ""
        state = ("parked" if row["state"] != "active"
                 else "changed" if resolved != folder
                 else "missing" if not os.path.isdir(resolved)
                 else "ready" if os.access(resolved, os.W_OK)
                 else "not_writable")
        return {"destination": self._destination_view(row), "check": {"state": state, "resolved": resolved}}

    # ── destinations (admitted, the owner's) ───────────────────────────────

    def save_destination(self, principal: Any, name: str, channel: str, folder: Optional[str] = None,
                         synced: bool = False, replaces: Optional[str] = None, host: Optional[str] = None,
                         repo: Optional[str] = None, kind: Optional[str] = None, number: Optional[int] = None,
                         site: Optional[str] = None, email: Optional[str] = None, key: Optional[str] = None,
                         space_id: Optional[str] = None, command_id: Optional[str] = None) -> dict[str, Any]:
        """Save one destination. ``replaces``: Edit -- the old row parks and this one is new.

        The account is CONCRETE (design section 1): GitHub freezes ``{host, login}``
        read now from ``gh api user --hostname``; Jira and Confluence ``{site, email}``.
        """
        handle = _handle()
        destination_id = _derived_id("chd_", handle.operation_id)
        if handle.replay:
            return {"destination": self._destination_view(self._stored(destination_id)),
                    "replaced": replaces or None}
        label = str(name or "").strip()
        if not label or len(label) > 120:
            raise ValidationError("A destination needs a name (120 characters at most)", code="destination_name_invalid")
        chan = contract.channel(channel)
        if channel == "file":
            account, target = {}, chan.target_at_save(folder)
        elif channel in {"github", "jira", "confluence"}:
            account, target = chan.target_at_save(
                {"host": host, "repo": repo, "kind": kind, "number": number, "site": site, "email": email,
                 "key": key, "space_id": space_id}, handle.principal)
            synced = False
        else:
            raise ValidationError(f"{channel} destinations arrive with their channel", code="channel_unknown")
        if replaces:
            old = self._destination(replaces)
            if old["state"] != "active":
                raise ChannelRefused("destination_parked", f"Destination {replaces} is already parked")

        def effect(conn: Any) -> None:
            if replaces and not self._db.channel_destinations.park_in_transaction(conn, replaces):
                raise ChannelRefused("destination_parked", f"Destination {replaces} is already parked")
            self._db.channel_destinations.insert_in_transaction(
                conn, destination_id=destination_id, name=label, channel=channel, account=account,
                target=target, synced=bool(synced))

        handle.terminal("succeeded", "succeeded", f"channel_destination:{destination_id}", effect=effect)
        return {"destination": self._destination_view(self._stored(destination_id)), "replaced": replaces or None}

    def remove_destination(self, principal: Any, destination_id: str,
                           command_id: Optional[str] = None) -> dict[str, Any]:
        """Remove parks the row; history is kept (a prepared send to it is then refused)."""
        handle = _handle()
        row = self._destination(destination_id)
        if handle.replay:
            return {"destination": self._destination_view(row)}
        if row["state"] != "active":
            raise ChannelRefused("destination_parked", f"Destination {destination_id} is already parked")

        def effect(conn: Any) -> None:
            if not self._db.channel_destinations.park_in_transaction(conn, destination_id):
                raise ChannelRefused("destination_parked", f"Destination {destination_id} is already parked")

        handle.terminal("succeeded", "succeeded", f"channel_destination:{destination_id}", effect=effect)
        return {"destination": self._destination_view(self._stored(destination_id))}

    def _stored(self, destination_id: str) -> dict[str, Any]:
        row = self._db.channel_destinations.get(destination_id)
        if row is None:
            raise NotFound("destination", destination_id)
        return row

    # ── prepare and discard ──────────────────────────────────────────────

    def _size(self, channel: str, payload: bytes) -> None:
        size, limit, unit = contract.payload_size(channel, payload)
        if limit and size > limit:
            raise ChannelRefused(f"payload_too_large:{channel}",
                                 f"The payload is {size} {unit}; the {channel} channel takes {limit}", status=400)

    def prepare(self, principal: Any, update_id: str, destination_id: str,
                command_id: Optional[str] = None) -> dict[str, Any]:
        """Freeze the target and the exact bytes in a ``prepared`` row, under the preparer's identity."""
        handle = _handle()
        if handle.replay:
            row = self._db.channel_sends.by_operation(prepare_operation_id=handle.operation_id)
            if row is None:
                raise NotFound("send", handle.operation_id)
            return self._answer(row)
        destination = self._destination(destination_id)
        if destination["state"] != "active":
            raise ChannelRefused("destination_parked", f"Destination {destination_id} is parked")
        document = contract.render_update(self._db, update_id)
        chan = contract.channel(destination["channel"])
        payload = chan.serialize(document)
        self._size(destination["channel"], payload)
        send_id = _derived_id("chs_", handle.operation_id)
        operation = handle.operation()

        def effect(conn: Any) -> None:
            conn.execute(
                "INSERT INTO channel_sends (id, document_ref, destination_id, channel, account_json, target_json,"
                " target_digest, payload, payload_digest, prepared_by_kind, prepared_by_identity,"
                " prepare_operation_id, state, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'prepared', ?)",
                (send_id, document.ref, destination["id"], destination["channel"], destination["account_json"],
                 destination["target_json"], destination["target_digest"], payload, contract.sha256(payload),
                 str(operation.get("principal_kind") or ""), str(operation.get("principal_identity") or ""),
                 handle.operation_id, now_iso()))

        handle.terminal("succeeded", "succeeded", f"channel_send:{send_id}", effect=effect)
        return self._answer(self._db.channel_sends.get(send_id))

    def discard(self, principal: Any, send_id: str, command_id: Optional[str] = None) -> dict[str, Any]:
        """``prepared`` -> ``discarded``, one conditional write; against Send, one wins."""
        handle = _handle()
        row = self._db.channel_sends.get(send_id)
        if row is None:
            raise NotFound("send", send_id)
        if handle.replay:
            return self._answer(row)

        def effect(conn: Any) -> None:
            moved = conn.execute("UPDATE channel_sends SET state='discarded', settled_at=? WHERE id=? AND state='prepared'",
                                 (now_iso(), send_id)).rowcount
            if moved != 1:
                raise ChannelRefused("send_already_settled", f"Send {send_id} is no longer prepared")

        handle.terminal("succeeded", "succeeded", f"channel_send:{send_id}", effect=effect)
        return self._answer(self._db.channel_sends.get(send_id))

    # ── the press ────────────────────────────────────────────────────────

    def send(self, principal: Any, send_id: Optional[str] = None, update_id: Optional[str] = None,
             destination_id: Optional[str] = None, preview_digest: Optional[str] = None,
             command_id: Optional[str] = None) -> dict[str, Any]:
        """The owner's press: a prepared row (``send_id``), or the document, the destination and
        the digest of the preview he saw (the inline form)."""
        handle = _handle()
        mine = self._db.channel_sends.by_operation(send_operation_id=handle.operation_id)
        if handle.replay:
            if mine is None:
                raise NotFound("send", handle.operation_id)
            return self._answer(mine)
        if mine is not None:
            # This operation already crossed its boundary: a take-over. NEVER dispatch again.
            if mine["state"] == "dispatching":
                outcome = self._recover(mine)
                return self._settle(handle, mine, outcome)
            return self._close_as_row(handle, mine)
        row = self._boundary(handle, send_id=send_id, update_id=update_id, destination_id=destination_id,
                             preview_digest=preview_digest)
        from .channel_cli import Seam

        # The send's authority for its CLI children (design section 6).
        seam = Seam(principal=handle.principal, parent_operation_id=handle.operation_id, broker=handle.broker)
        try:
            outcome = contract.channel(row["channel"]).dispatch(row, seam)
        except Exception as exc:  # the effect's own error after the boundary: never FAILED
            log.warning("channel send %s: dispatch raised %s", row["id"], type(exc).__name__)
            outcome = Outcome("unknown", f"dispatch_{type(exc).__name__.lower()}")
        return self._settle(handle, row, outcome)

    def _recover(self, row: Mapping[str, Any]) -> Outcome:
        try:
            return contract.channel(row["channel"]).recover(row)
        except Exception as exc:
            return Outcome("unknown", f"recover_{type(exc).__name__.lower()}")

    def _boundary(self, handle: Any, *, send_id: Optional[str], update_id: Optional[str],
                  destination_id: Optional[str], preview_digest: Optional[str]) -> dict[str, Any]:
        """Every check before the effect, then the durable dispatch boundary (its own commit)."""
        if send_id:
            row = self._db.channel_sends.get(send_id)
            if row is None:
                raise NotFound("send", send_id)
            if row["state"] != "prepared":
                raise ChannelRefused("send_already_settled", f"Send {send_id} is {row['state']}")
            destination = self._destination(row["destination_id"])
            payload = bytes(row["payload"])
            frozen_target, frozen_digest = json.loads(row["target_json"]), row["target_digest"]
            document_ref = row["document_ref"]
        else:
            if not (update_id and destination_id and preview_digest):
                raise ValidationError("A send names send_id, or update_id + destination_id + preview_digest",
                                      code="invalid_arguments")
            destination = self._destination(destination_id)
            document = contract.render_update(self._db, update_id)
            payload = contract.channel(destination["channel"]).serialize(document)
            if contract.sha256(payload) != str(preview_digest):
                raise ChannelRefused("preview_changed", "The document changed since the preview you saw")
            frozen_target, frozen_digest = json.loads(destination["target_json"]), destination["target_digest"]
            document_ref = document.ref
            send_id = _derived_id("chs_", handle.operation_id)
            row = None
        # The destination's state and digest are read again inside the boundary transaction (below).
        channel_name = destination["channel"]
        chan = contract.channel(channel_name)
        frozen_account = json.loads((row or destination)["account_json"] or "{}")
        if row is not None and contract.sha256(payload) != row["payload_digest"]:
            raise ChannelRefused("payload_changed", "The frozen payload does not match its digest")
        self._size(channel_name, payload)
        # Before the boundary: the file's folder resolves again; GitHub reads its
        # login again (github_identity_changed / github_not_logged_in by name).
        folder = chan.check_before_dispatch(frozen_target, account=frozen_account, principal=handle.principal)
        path = (chan.choose_path(folder, contract.naming(self._db, document_ref), send_id)
                if channel_name == "file" else None)
        # PHILO-10-04: the boundary time (display only; the order is dispatch_seq).
        started = datetime.now(timezone.utc).isoformat(timespec="microseconds")
        operation_id = handle.operation_id
        claimed = "EXISTS (SELECT 1 FROM kernel_operations WHERE operation_id=? AND state='claimed')"
        # PHILO-10-04: the order sends LEFT in, allocated inside the boundary
        # transaction (BEGIN IMMEDIATE holds the write lock): a total order for
        # "latest", whatever the clock says.
        next_seq = "SELECT COALESCE(MAX(dispatch_seq), 0) + 1 FROM channel_sends"
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            # The destination, read again INSIDE the boundary transaction: a Remove
            # or an Edit that committed after the read above wins, and nothing is
            # dispatched; one that comes after this commit parks it, and the send stands.
            _destination_still_frozen(conn, destination["id"], frozen_digest)
            if row is not None:
                moved = conn.execute(
                    "UPDATE channel_sends SET state='dispatching', send_operation_id=?, dispatch_started_at=?,"
                    f" file_path=?, dispatch_seq=({next_seq}) WHERE id=? AND state='prepared' AND {claimed}",
                    (operation_id, started, path, send_id, operation_id)).rowcount
            else:
                moved = conn.execute(
                    "INSERT INTO channel_sends (id, document_ref, destination_id, channel, account_json, target_json,"
                    " target_digest, payload, payload_digest, prepared_by_kind, prepared_by_identity,"
                    " send_operation_id, state, file_path, created_at, dispatch_started_at, dispatch_seq)"
                    f" SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'dispatching', ?, ?, ?, ({next_seq}) WHERE {claimed}",
                    (send_id, document_ref, destination["id"], channel_name, destination["account_json"],
                     destination["target_json"], destination["target_digest"], payload, contract.sha256(payload),
                     "owner", str(getattr(handle.principal, "identity", "") or ""), operation_id, path, started,
                     started, operation_id)).rowcount
        if moved != 1:
            state = str((handle.operation() or {}).get("state") or "")
            if state != "claimed":
                raise ChannelRefused("operation_ended_before_dispatch", "The send ended before its dispatch")
            raise ChannelRefused("send_already_settled", f"Send {send_id} is no longer prepared")
        return self._db.channel_sends.get(send_id)

    def _settle(self, handle: Any, row: Mapping[str, Any], outcome: Outcome) -> dict[str, Any]:
        """ONE transaction: the row's end, its history row and the kernel's terminal receipt."""
        from holdspeak.kernel.desk_broker import STRICT_CONFLICTS
        from holdspeak.kernel.model import KernelRefused

        state, receipt_outcome = outcome.kernel_end()
        destination = self._db.channel_destinations.get(row["destination_id"]) or {}

        def effect(conn: Any) -> None:
            settled = settle_in_transaction(conn, send_operation_id=handle.operation_id, state=outcome.state,
                                            reason=outcome.reason, proof=outcome.record(),
                                            delivered_to=str(destination.get("name") or ""))
            if settled is None:
                raise RuntimeError("the send row is no longer dispatching")

        try:
            handle.terminal(state, receipt_outcome, f"channel_send:{row['id']}", effect=effect)
        except KernelRefused as exc:
            if exc.reason not in STRICT_CONFLICTS:
                raise
            # The reaper (or a take-over) ended it first, with the row: its settle answers.
        return self._answer(self._db.channel_sends.get(row["id"]))

    def _close_as_row(self, handle: Any, row: Mapping[str, Any]) -> dict[str, Any]:
        """A take-over that finds its row already settled: the kernel state follows the row."""
        if not handle.closed and row["state"] in {"sent", "failed", "unknown"}:
            from holdspeak.kernel.desk_broker import STRICT_CONFLICTS
            from holdspeak.kernel.model import KernelRefused

            state, outcome = Outcome(row["state"], row["reason"]).kernel_end()
            try:
                handle.terminal(state, outcome, f"channel_send:{row['id']}")
            except KernelRefused as exc:
                if exc.reason not in STRICT_CONFLICTS:
                    raise
        return self._answer(row)


__all__ = ["ChannelService"]


def _destination_still_frozen(conn: Any, destination_id: str, frozen_digest: str) -> None:
    """Inside the boundary transaction: the destination is active and its target is the frozen one."""
    current = conn.execute("SELECT state, target_digest FROM channel_destinations WHERE id=?",
                           (destination_id,)).fetchone()
    if current is None or current["state"] != "active":
        raise ChannelRefused("destination_parked", f"Destination {destination_id} is parked")
    if current["target_digest"] != frozen_digest:
        raise ChannelRefused("destination_changed", f"Destination {destination_id} changed since prepare")
