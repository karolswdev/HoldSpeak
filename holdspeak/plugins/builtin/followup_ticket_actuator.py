"""Reference actuator: draft a follow-up ticket for an unowned action item.

Phase 37, HS-37-05. The first concrete **actuator** — the plugin kind that
proposes an external side effect rather than emitting a read-only artifact. It
exists to prove the whole loop end-to-end: propose → approve → execute → audit,
with nothing running without approval.

Two halves, deliberately separate (the safety split):

  - `FollowupTicketActuator` (the plugin) — `run(context)` reads the meeting's
    action items and, for the first one **without an owner**, returns an
    `ActuatorProposal` describing the follow-up ticket it *would* write. It does
    NOT reach out — building a proposal is all an actuator's `run()` ever does.

  - `build_outbox_connector(...)` (the connector) — performs the side effect:
    writes the ticket as a Markdown file into a local **outbox** directory. The
    guarded executor (HS-37-04) calls this only after the approval + policy +
    parity guards pass. A local-file write is a real, observable, reversible
    external artifact that is safe to exercise in CI (no network, no creds).

Why a local outbox and not `gh issue create`? The existing `github_cli`
connector pack is **read-only** by policy (`gh pr view` / `issue view`) — the
Phase-25 egress posture forbids unattended writes — and a real `gh`/`jira` call
needs credentials + creates real tickets (not reproducible). The outbox writer is
the honest, CI-safe reference; a gh/jira/webhook connector is a future actuator on
this same `ActuatorExecutor` contract.

The actuator is registered **behind the gate** via `register_followup_actuator`
(NOT in `register_builtin_plugins`), so the default plugin set + routing are
unchanged; it also declares `required_capabilities=["actuator"]`, so even when
registered it is capability-blocked until an operator enables actuators.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable, Optional

from ...logging_config import get_logger

log = get_logger("plugins.followup_ticket_actuator")

# Owner strings that actually mean "no owner" (mirrors action_owner_enforcer).
_UNASSIGNED = {"", "null", "none", "n/a", "na", "unassigned", "unknown", "tbd", "?"}

# A connector performs a proposal's side effect and returns a result dict.
OutboxWriter = Callable[[Path, str], int]


def _is_unowned(owner: Any) -> bool:
    return str(owner or "").strip().lower() in _UNASSIGNED


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(text).strip().lower()).strip("-")
    return (slug or "followup")[:48]


class FollowupTicketActuator:
    """Proposes a follow-up ticket for the first unowned action item."""

    id: str = "followup_ticket_actuator"
    version: str = "0.1.0"
    kind: str = "actuator"
    execution_mode: str = "inline"
    required_capabilities: list[str] = ["actuator"]

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        items = context.get("action_items") or []
        if not isinstance(items, list):
            items = []
        unowned = next(
            (it for it in items if isinstance(it, dict) and _is_unowned(it.get("owner"))),
            None,
        )
        if unowned is None:
            # Nothing to propose — raise so the host records a plain `error`
            # (no proposal, no side effect), never a half-formed proposal.
            raise ValueError("no unowned action item to follow up on")

        task = str(unowned.get("task") or "").strip() or "Unspecified action item"
        meeting_title = str(context.get("meeting_title") or context.get("title") or "meeting").strip()
        due = str(unowned.get("due") or "").strip()

        title = f"Follow up: {task}"
        body_lines = [
            f"# {title}",
            "",
            f"Raised in **{meeting_title}** with no owner assigned.",
            "",
            f"- **Task:** {task}",
            "- **Owner:** _unassigned_",
            f"- **Due:** {due or '_not stated_'}",
        ]
        body = "\n".join(body_lines) + "\n"
        filename = f"followup-{_slugify(task)}.md"

        return {
            "target": "outbox",
            "action": "write_followup_ticket",
            "preview": (
                f"Draft a follow-up ticket for the unowned action item "
                f"“{task}” → {filename}"
            ),
            "payload": {"filename": filename, "title": title, "body": body},
            "reversible": True,
            "required_capabilities": ["actuator"],
        }


def _default_writer(path: Path, content: str) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return len(content.encode("utf-8"))


def build_outbox_connector(
    outbox_dir: Path | str,
    *,
    dry_run: bool = False,
    writer: Optional[OutboxWriter] = None,
) -> Callable[[Any], dict[str, Any]]:
    """A connector that writes a proposal's ticket to a local outbox file.

    Returns a `connector(proposal) -> result` callable for `ActuatorExecutor`.
    The executor calls it only after approval + policy + parity pass; this is
    the egress point (a local filesystem write — no network). `dry_run` returns
    the path + content it *would* write without writing.
    """
    out = Path(outbox_dir)
    write = writer or _default_writer

    def _connector(proposal: Any) -> dict[str, Any]:
        payload = getattr(proposal, "payload", None) or {}
        filename = str(payload.get("filename") or "followup.md")
        # Defensive: never let a payload escape the outbox directory.
        safe_name = Path(filename).name
        target_path = out / safe_name
        content = str(payload.get("body") or "")
        if dry_run:
            return {"path": str(target_path), "bytes": len(content.encode("utf-8")), "dry_run": True}
        written = write(target_path, content)
        log.info("actuator wrote follow-up ticket to %s (%d bytes)", target_path, written)
        return {"path": str(target_path), "bytes": written, "dry_run": False}

    return _connector


def register_followup_actuator(host: Any) -> str:
    """Register the reference actuator on a host (behind the actuator gate).

    Explicit + opt-in: NOT part of `register_builtin_plugins`, so the default
    plugin set + routing chains are unchanged. The host still capability-blocks
    it unless `actuator` is in `enabled_capabilities`.
    """
    host.register(FollowupTicketActuator())
    return FollowupTicketActuator.id


__all__ = [
    "FollowupTicketActuator",
    "build_outbox_connector",
    "register_followup_actuator",
]
