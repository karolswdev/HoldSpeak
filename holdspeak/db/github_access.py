"""Durable GitHub removal claim and its atomic connection settlement."""
from __future__ import annotations

from typing import Any

from holdspeak.timestamps import utc_now_iso
from holdspeak.services.errors import ConflictError

CONNECTION = "wpc_github"


def removal(db: Any) -> dict[str, Any] | None:
    with db._connection() as conn:
        row = conn.execute("SELECT * FROM github_connection_removals WHERE connection_id=?", (CONNECTION,)).fetchone()
    return dict(row) if row else None


def begin(db: Any, operation_id: str, account: str, checked_at: str) -> None:
    with db._connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        present = conn.execute("SELECT 1 FROM github_connection_removals WHERE connection_id=?", (CONNECTION,)).fetchone()
        if present:
            raise ConflictError("Check the GitHub sign-in before removing it.", code="github_sign_in_required")
        moved = conn.execute(
            "UPDATE watch_provider_connections SET state='owner_action_required', last_error_code='github_sign_in_required',"
            " last_error_detail='Sign in again', last_checked_at=? WHERE id=? AND state='connected'"
            " AND external_connection_ref=? AND last_checked_at=?",
            (utc_now_iso(), CONNECTION, account, checked_at),
        ).rowcount
        if moved != 1:
            raise ConflictError("GitHub connection changed. Check it before removing it.", code="github_connection_changed")
        conn.execute(
            "INSERT INTO github_connection_removals(connection_id,operation_id,account_ref,checked_at,state,updated_at)"
            " VALUES (?,?,?,?,'pending',?)", (CONNECTION, operation_id, account, checked_at, utc_now_iso()),
        )


def settle_in(conn: Any, operation_id: str, state: str) -> None:
    changed = conn.execute(
        "UPDATE github_connection_removals SET state=?,updated_at=? WHERE connection_id=? AND operation_id=?",
        (state, utc_now_iso(), CONNECTION, operation_id),
    ).rowcount
    if changed:
        conn.execute(
            "UPDATE watch_provider_connections SET state='owner_action_required', external_connection_ref='',"
            " last_error_code='github_sign_in_required',last_error_detail='Sign in again',last_checked_at=? WHERE id=?",
            (utc_now_iso(), CONNECTION),
        )


def ended_effect(operation: Any) -> Any:
    if operation.get("name") != "provider.github_remove":
        return None
    return lambda conn: settle_in(conn, str(operation["operation_id"]), "uncertain")


def save_check(db: Any, result: Any, manifest: Any, *, account: str | None, owner_check: bool,
               observed_removal: Any) -> None:
    import json
    with db._connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        current = conn.execute("SELECT * FROM github_connection_removals WHERE connection_id=?", (CONNECTION,)).fetchone()
        current_id = current["operation_id"] if current else None
        observed_id = observed_removal["operation_id"] if observed_removal else None
        if owner_check and current_id != observed_id:
            raise ConflictError("GitHub connection changed. Check sign-in again.", code="github_connection_changed")
        old = conn.execute("SELECT * FROM watch_provider_connections WHERE id=?", (CONNECTION,)).fetchone()
        held = current is not None or (old and old["state"] == "owner_action_required" and not old["external_connection_ref"])
        success = owner_check and result["state"] == "connected" and account
        if held and not success:
            return  # a failed/passive check never releases the removal refusal
        stamp = utc_now_iso()
        conn.execute(
            "INSERT INTO watch_provider_connections(id,provider_id,transport,state,capability_manifest_json,"
            "capability_revision,discovery_state,last_checked_at,last_connected_at,last_error_code,last_error_detail,"
            "external_connection_ref) VALUES (?,'github','connector_pack',?,?,?,'unknown',?,?,?,?,?)"
            " ON CONFLICT(id) DO UPDATE SET state=excluded.state,capability_manifest_json=excluded.capability_manifest_json,"
            "capability_revision=excluded.capability_revision,last_checked_at=excluded.last_checked_at,"
            "last_connected_at=COALESCE(excluded.last_connected_at,watch_provider_connections.last_connected_at),"
            "last_error_code=excluded.last_error_code,last_error_detail=excluded.last_error_detail,"
            "external_connection_ref=excluded.external_connection_ref",
            (CONNECTION, result["state"], json.dumps(manifest["capabilities"]), manifest["revision"], stamp,
             stamp if result["state"] == "connected" else None, result.get("error_code") or "",
             result.get("error_detail") or "", account or (result.get("display") or {}).get("account") or ""),
        )
        if success:
            conn.execute("DELETE FROM github_connection_removals WHERE connection_id=?", (CONNECTION,))
