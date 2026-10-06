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
principal, through its broker (``services/channel_cli.py``; PHILO-10-02);
the email channel sends its frozen request body as an ``external.egress`` CHILD
of the send, under the send's authenticated owner principal, through its
broker (``services/channel_email.py``; PHILO-10-03).
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Optional

from holdspeak.db.channels import BUILTIN_FOLDER_ID, is_builtin, now_iso, settle_in_transaction
from holdspeak.logging_config import get_logger

from . import channel_contract as contract
from . import channel_email  # noqa: F401 -- registers the email channel (PHILO-10-03)
from . import channel_slack  # noqa: F401 -- registers the Slack channel (PHILO-11-02)
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

    def __init__(self, db: Any, *, on_changed: Callable[[str, str, str], None] | None = None) -> None:
        self._db, self._on_changed = db, on_changed

    # ── views ──────────────────────────────────────────────────────────

    def _destination_view(self, row: Mapping[str, Any]) -> dict[str, Any]:
        target = contract.shown_target(json.loads(row["target_json"] or "{}"))
        account = json.loads(row["account_json"] or "{}")
        # The built-in folder's sync is read now (iCloud Drive can be switched on or off).
        synced = bool(target.get("cloud")) if is_builtin(row) else bool(row["synced"])
        return {
            "id": row["id"], "name": row["name"], "channel": row["channel"],
            "account": account, "target": target, "builtin": is_builtin(row),
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
        # Existing channels report frozen byte size. Slack reports the text
        # characters governed by its 39,000-character refusal.
        size = (contract.payload_size("slack", payload)[0]
                if str(row["channel"]) == "slack" else len(payload))
        return {
            "id": row["id"], "document_ref": row["document_ref"], "destination_id": row["destination_id"],
            "destination_name": destination.get("name"), "channel": row["channel"],
            "badge": contract.channel(row["channel"]).badge(self._synced(destination, row)),
            "account": json.loads(row["account_json"] or "{}"),
            "target": contract.shown_target(json.loads(row["target_json"] or "{}")),
            "target_digest": row["target_digest"], "payload_digest": row["payload_digest"],
            "document_json": json.loads(row["document_json"]) if row.get("document_json") else None,
            "size": size, "preview": contract.preview_for(row["channel"], payload, row["account_json"]),
            "prepared_by": {"kind": row["prepared_by_kind"], "identity": row["prepared_by_identity"]},
            "prepare_operation_id": row["prepare_operation_id"], "send_operation_id": row["send_operation_id"],
            "state": row["state"], "reason": row["reason"],
            "proof": json.loads(row["proof_json"]) if row["proof_json"] else None,
            "file_path": row["file_path"], "created_at": row["created_at"],
            "dispatch_started_at": row["dispatch_started_at"], "settled_at": row["settled_at"],
            "dispatch_seq": row["dispatch_seq"], "egress": row.get("egress"),
        }

    @staticmethod
    def _synced(destination: Mapping[str, Any], send: Optional[Mapping[str, Any]] = None) -> bool:
        """A destination's cloud sync: its saved flag; for the built-in folder, iCloud Drive.

        A settled send of the built-in answers from its own proof (what was true
        at send time); anything else reads the folder now.
        """
        if not destination or not is_builtin(destination):
            return bool((destination or {}).get("synced"))
        if send is not None and send.get("dispatch_seq") is not None:
            return bool(send.get("egress"))  # judged at its boundary: any sync provider
        return contract.builtin_egress() is not None

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

    def sends(self, principal: Any, document_ref: Optional[str] = None, send_id: Optional[str] = None) -> dict[str, Any]:
        if send_id:
            row = self._db.channel_sends.get(send_id)
            if row is None:
                raise NotFound("send", send_id)
            return {"sends": [self._send_view(row)]}
        if document_ref:
            rows = self._db.channel_sends.list_for_document(document_ref)
        else:
            rows = self._db.channel_sends.list_recent()
        return {"sends": [self._send_view(r) for r in rows]}

    def preview(self, principal: Any, document_ref: str, destination_id: str) -> dict[str, Any]:
        """What the destination's channel would get: the exact bytes' digest and their readable preview."""
        destination = self._destination(destination_id)
        if destination["state"] != "active":
            raise ChannelRefused("destination_parked", f"Destination {destination_id} is parked")
        document = contract.render_document(self._db, document_ref)
        chan = contract.channel(destination["channel"])
        payload = contract.serialize_for(destination, document)
        self._size(destination["channel"], payload)
        size = (contract.payload_size("slack", payload)[0]
                if destination["channel"] == "slack" else len(payload))
        return {"document_ref": document.ref, "title": document.title, "destination_id": destination["id"],
                "channel": destination["channel"], "badge": chan.badge(self._synced(destination)),
                "payload_digest": contract.sha256(payload), "size": size,
                "preview": contract.preview_for(destination["channel"], payload, destination["account_json"])}

    def check_destination(self, principal: Any, destination_id: str) -> dict[str, Any]:
        """A folder: a local check (it resolves to the saved folder, it is a folder, it is writable).

        A GitHub, Jira or Confluence destination: its stored Phase 9 connection
        state (no probe here; ``connection.recheck`` probes).
        """
        import os

        row = self._destination(destination_id)
        if row["channel"] == "email":
            state, answered_at = self._email_state(row)
            return {"destination": self._destination_view(row),
                    "check": {"state": state, "resolved": None, "answered_at": answered_at}}
        if row["channel"] == "slack":
            if row["state"] != "active":
                return {"destination": self._destination_view(row),
                        "check": {"state": "parked", "resolved": None}}
            chan = contract.channel("slack")
            check = chan.check_destination(json.loads(row["target_json"] or "{}"),
                                           account=json.loads(row["account_json"] or "{}"))
            return {"destination": self._destination_view(row),
                    "check": {"state": str(check), "resolved": None}}
        if row["channel"] != "file":
            view = self._destination_view(row)
            state = "parked" if row["state"] != "active" else str((view["connection"] or {}).get("state") or "")
            return {"destination": view, "check": {"state": state, "resolved": None}}
        target = json.loads(row["target_json"] or "{}")
        if contract.is_builtin_target(target):
            # The built-in folder is never "missing": the next send makes it.
            resolved = contract.builtin_folder()
            parent = resolved
            while not os.path.isdir(parent) and os.path.dirname(parent) != parent:
                parent = os.path.dirname(parent)
            state = ("parked" if row["state"] != "active"
                     else "ready" if os.access(parent, os.W_OK)
                     else "not_writable")
            return {"destination": self._destination_view(row), "check": {"state": state, "resolved": resolved}}
        folder = str(target.get("folder") or "")
        resolved = os.path.realpath(folder) if folder else ""
        state = ("parked" if row["state"] != "active"
                 else "changed" if resolved != folder
                 else "missing" if not os.path.isdir(resolved)
                 else "ready" if os.access(resolved, os.W_OK)
                 else "not_writable")
        return {"destination": self._destination_view(row), "check": {"state": state, "resolved": resolved}}

    def _email_state(self, row: Mapping[str, Any]) -> tuple[str, Optional[str]]:
        """An email destination, checked locally (no call to the provider): the key in a native keychain, then
        what the provider LAST answered for a send from this from address, and when (PHILO-10-04, B11; Codex
        Astra r2 on #697: say what is known, never a fresh verification).

        ``sender_accepted``: the provider accepted the latest answered send (at ``answered_at``);
        ``sender_not_verified``: its latest answer was the pinned 403; ``key_changed``: the key was saved
        again after that answer, so the answer no longer speaks for it; ``ready``: the key is there and no
        send from this sender has an answer yet."""
        if row["state"] != "active":
            return "parked", None
        account = json.loads(row["account_json"] or "{}")
        provider_name = str(account.get("provider") or "")
        try:
            key_ref = channel_email.valid_key_ref(account.get("key_ref"))
            channel_email.read_key(provider_name, key_ref)
        except channel_email.EmailKeyError as exc:
            return exc.code, None
        except ValidationError:
            return "email_key_ref_invalid", None
        with self._db._connection() as conn:
            # PHILO-10-07: the answer of THIS provider for this sender (a Resend answer never speaks for SendGrid).
            latest = conn.execute(
                "SELECT state, reason, dispatch_started_at FROM channel_sends WHERE channel='email'"
                " AND json_extract(account_json, '$.from_email')=? AND json_extract(account_json, '$.provider')=?"
                " AND dispatch_seq IS NOT NULL"
                " AND (state='sent' OR (state='failed' AND reason='sender_not_verified'))"
                " ORDER BY dispatch_seq DESC LIMIT 1",
                (str(account.get("from_email") or ""), provider_name)).fetchone()
            key_saved = conn.execute(
                "SELECT MAX(r.created_at) AS at FROM kernel_receipts r JOIN kernel_operations o"
                " ON o.operation_id=r.operation_id WHERE o.name='channel.save_email_key' AND r.state='succeeded'"
                " AND r.result_ref=?", (f"email_key:{channel_email.key_slot(provider_name, key_ref)}",)).fetchone()
        if latest is None:
            return "ready", None
        answered_at = str(latest["dispatch_started_at"] or "")
        try:
            answered = datetime.fromisoformat(answered_at).timestamp()
        except ValueError:
            answered = 0.0
        if key_saved is not None and key_saved["at"] is not None and float(key_saved["at"]) > answered:
            return "key_changed", answered_at
        return ("sender_accepted" if latest["state"] == "sent" else "sender_not_verified"), answered_at

    # ── destinations (admitted, the owner's) ───────────────────────────────

    def save_destination(self, principal: Any, name: str, channel: str, folder: Optional[str] = None,
                         synced: bool = False, replaces: Optional[str] = None, host: Optional[str] = None,
                         repo: Optional[str] = None, kind: Optional[str] = None, number: Optional[int] = None,
                         site: Optional[str] = None, email: Optional[str] = None, key: Optional[str] = None,
                         space_id: Optional[str] = None, provider: Optional[str] = None,
                         from_email: Optional[str] = None, from_name: Optional[str] = None,
                         key_ref: Optional[str] = None, to: Optional[list[str]] = None,
                         cc: Optional[list[str]] = None, channel_label: Optional[str] = None,
                         command_id: Optional[str] = None) -> dict[str, Any]:
        """Save one destination. ``replaces``: Edit -- the old row parks and this one is new.

        The account is CONCRETE (design section 1): GitHub freezes ``{host, login}``
        read now from ``gh api user --hostname``; Jira and Confluence ``{site, email}``.
        Email (PHILO-10-03): the account freezes ``{provider, from_email,
        from_name, key_ref}`` (the key's NAME, never the key); the target is
        ``{to, cc}``.
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
        elif channel == "email":
            account, target = chan.target_at_save({"provider": provider, "from_email": from_email,
                                                   "from_name": from_name, "key_ref": key_ref, "to": to, "cc": cc})
            synced = False
        elif channel == "slack":
            account, target = chan.target_at_save({"key_ref": key_ref, "channel_label": channel_label})
            # Saving the URL is a separate held operation.  A Slack
            # destination stores only the keychain item name, never the URL.
            try:
                chan.read_key(str(account.get("key_ref") or ""))
            except channel_slack.SlackKeyError as exc:
                raise ChannelRefused(exc.code, f"The Slack webhook cannot be read: {exc.code}", status=400) from None
            synced = False
        else:
            raise ValidationError(f"{channel} destinations arrive with their channel", code="channel_unknown")
        if replaces == BUILTIN_FOLDER_ID:
            raise ChannelRefused("destination_builtin", "The HoldSpeak folder stays", status=400)
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

    def save_slack_webhook(self, principal: Any, webhook_url: Any, command_id: Optional[str] = None) -> dict[str, Any]:
        """Save one Slack incoming-webhook URL in native key custody.

        The URL is transport-held and is passed directly to the native key
        store.  It never enters the operation arguments, destination account,
        receipt, or response.  The returned key reference is then used by the
        ordinary destination save operation.
        """
        handle = _handle()
        # The key reference is minted from the admitted save operation.  It is
        # only a keychain item name, never a credential fingerprint.
        key_ref = "slack_" + hashlib.sha256(str(handle.operation_id).encode()).hexdigest()[:24]
        chan = contract.channel("slack")
        if handle.replay:
            return {"key_ref": key_ref, "saved": True}
        key = webhook_url if isinstance(webhook_url, str) else ""
        try:
            chan.save_key(key_ref, key)
        except channel_slack.SlackKeyError as exc:
            raise ChannelRefused(exc.code, f"The Slack webhook could not be saved: {exc.code}", status=400) from None
        handle.terminal("succeeded", "succeeded", f"slack_webhook:{key_ref}")
        return {"key_ref": key_ref, "saved": True}

    def remove_destination(self, principal: Any, destination_id: str,
                           command_id: Optional[str] = None) -> dict[str, Any]:
        """Remove parks the row; history is kept (a prepared send to it is then refused)."""
        handle = _handle()
        row = self._destination(destination_id)
        if handle.replay:
            return {"destination": self._destination_view(row)}
        if is_builtin(row):
            raise ChannelRefused("destination_builtin", "The HoldSpeak folder stays", status=400)
        if row["state"] != "active":
            raise ChannelRefused("destination_parked", f"Destination {destination_id} is already parked")

        def effect(conn: Any) -> None:
            if not self._db.channel_destinations.park_in_transaction(conn, destination_id):
                raise ChannelRefused("destination_parked", f"Destination {destination_id} is already parked")

        handle.terminal("succeeded", "succeeded", f"channel_destination:{destination_id}", effect=effect)
        return {"destination": self._destination_view(self._stored(destination_id))}

    def save_email_key(self, principal: Any, key_ref: str, api_key: Any, provider: Optional[str] = None,
                       command_id: Optional[str] = None) -> dict[str, Any]:
        """Save the email provider's key in the OS keychain under *key_ref* (config, the owner's).

        ``api_key`` is HELD by the transport: never an argument, so it never
        reaches the kernel's request, its envelope digest, a receipt or a log.
        The answer and the receipt name the key's NAME only.
        """
        handle = _handle()
        ref = channel_email.valid_key_ref(key_ref)
        chosen = str(provider or "sendgrid")
        channel_email.provider(chosen)
        answer = {"key_ref": ref, "provider": chosen, "saved": True}
        if handle.replay:
            return answer
        key = api_key if isinstance(api_key, str) else ""
        if not key.strip() or len(key) > 512 or any(ch.isspace() for ch in key):
            raise ValidationError("The key is one line of 1-512 characters with no spaces", code="email_key_invalid")
        try:
            channel_email.save_key(chosen, ref, key)
        except channel_email.EmailKeyError as exc:
            raise ChannelRefused(exc.code, f"The key could not be saved: {exc.code}", status=400) from None
        handle.terminal("succeeded", "succeeded", f"email_key:{channel_email.key_slot(chosen, ref)}")
        return answer

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
                                 f"The payload is {size} {unit}; the {channel} channel takes {limit}", status=400,
                                 size=size, limit=limit, unit=unit)

    def prepare(self, principal: Any, document_ref: str, destination_id: str,
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
        document = contract.render_document(self._db, document_ref)
        payload = contract.serialize_for(destination, document)
        self._size(destination["channel"], payload)
        document_json = contract.frozen_document_json(document)
        send_id = _derived_id("chs_", handle.operation_id)
        operation = handle.operation()

        def effect(conn: Any) -> None:
            conn.execute(
                "INSERT INTO channel_sends (id, document_ref, destination_id, channel, account_json, target_json,"
                " target_digest, payload, payload_digest, document_json, prepared_by_kind, prepared_by_identity,"
                " prepare_operation_id, state, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'prepared', ?)",
                (send_id, document.ref, destination["id"], destination["channel"], destination["account_json"],
                 destination["target_json"], destination["target_digest"], payload, contract.sha256(payload), document_json,
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

    def send(self, principal: Any, send_id: Optional[str] = None, document_ref: Optional[str] = None,
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
        row = self._boundary(handle, send_id=send_id, document_ref=document_ref, destination_id=destination_id,
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

    def _boundary(self, handle: Any, *, send_id: Optional[str], document_ref: Optional[str],
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
            document = (contract.document_from_json(document_ref, row["document_json"])
                        if row.get("document_json") else None)
            document_json = row.get("document_json")
            # A prepared send leaves only when its frozen bytes are the bytes
            # its document renders NOW, for every document kind (inventory
            # gap 5, 2026-10-03; every kind 2026-10-05). A row frozen by an
            # older renderer (the Brief's People overlay) or before its source
            # changed never leaves: it refuses PREVIEW CHANGED and he takes a
            # fresh preview. A source deleted since prepare still sends its
            # frozen bytes (PHILO-11), except a Brief: it refuses as before.
            try:
                current = contract.render_document(self._db, document_ref)
            except ChannelRefused as exc:
                if exc.code != "document_not_found" or str(document_ref).startswith("monday_brief:"):
                    raise
                current = None
            if current is not None:
                fresh = contract.serialize_for(destination, current)
                if contract.sha256(fresh) != row["payload_digest"]:
                    raise ChannelRefused("preview_changed", "The document changed since this send was prepared")
        else:
            if not (document_ref and destination_id and preview_digest):
                raise ValidationError("A send names send_id, or document_ref + destination_id + preview_digest",
                                      code="invalid_arguments")
            destination = self._destination(destination_id)
            document = contract.render_document(self._db, document_ref)
            payload = contract.serialize_for(destination, document)
            if contract.sha256(payload) != str(preview_digest):
                raise ChannelRefused("preview_changed", "The document changed since the preview you saw")
            frozen_target, frozen_digest = json.loads(destination["target_json"]), destination["target_digest"]
            document_ref = document.ref
            document_json = contract.frozen_document_json(document)
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
        # login again (github_identity_changed / github_not_logged_in by name);
        # email's key store is native and holds the key (email_key_store_not_native / email_key_missing).
        folder = chan.check_before_dispatch(frozen_target, account=frozen_account, principal=handle.principal)
        if channel_name == "file":
            # A new row carries its complete naming provenance. A legacy row
            # has no document_json, so retain the Phase 10 lookup only for the
            # file channel that needs a path; other channels send their
            # frozen bytes (checked against a fresh render above).
            if document is None:
                document = contract.naming(self._db, document_ref)
            path = chan.choose_path(folder, document, send_id)
        else:
            path = None
        # The egress, judged once here; the settle copies it into the proof on every path.
        egress = contract.egress_at_boundary(frozen_target, folder if channel_name == "file" else None)
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
                    f" file_path=?, egress=?, dispatch_seq=({next_seq}) WHERE id=? AND state='prepared' AND {claimed}",
                    (operation_id, started, path, egress, send_id, operation_id)).rowcount
            else:
                moved = conn.execute(
                    "INSERT INTO channel_sends (id, document_ref, destination_id, channel, account_json, target_json,"
                    " target_digest, payload, payload_digest, document_json, prepared_by_kind, prepared_by_identity,"
                    " send_operation_id, state, file_path, created_at, dispatch_started_at, egress, dispatch_seq)"
                    f" SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'dispatching', ?, ?, ?, ?, ({next_seq}) WHERE {claimed}",
                    (send_id, document_ref, destination["id"], channel_name, destination["account_json"],
                     destination["target_json"], destination["target_digest"], payload, contract.sha256(payload), document_json,
                     "owner", str(getattr(handle.principal, "identity", "") or ""), operation_id, path, started,
                     started, egress, operation_id)).rowcount
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
        settled = self._db.channel_sends.get(row["id"])
        if settled is not None and str(settled.get("state") or "") in {"sent", "failed", "unknown"}:
            self._changed(str(row["id"]), str(settled["state"]))
        return self._answer(settled)

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

    def _changed(self, send_id: str, state: str) -> None:
        if self._on_changed is None:
            return
        try:
            self._on_changed("send", str(send_id), str(state))
        except Exception:  # pragma: no cover - a dead socket never undoes a send
            pass


__all__ = ["ChannelService"]


def _destination_still_frozen(conn: Any, destination_id: str, frozen_digest: str) -> None:
    """Inside the boundary transaction: the destination is active and its target is the frozen one."""
    current = conn.execute("SELECT state, target_digest FROM channel_destinations WHERE id=?",
                           (destination_id,)).fetchone()
    if current is None or current["state"] != "active":
        raise ChannelRefused("destination_parked", f"Destination {destination_id} is parked")
    if current["target_digest"] != frozen_digest:
        raise ChannelRefused("destination_changed", f"Destination {destination_id} changed since prepare")
