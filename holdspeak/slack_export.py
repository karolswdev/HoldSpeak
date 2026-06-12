"""Send to Slack — the export message builder + connector (Phase 61, HS-61-01).

The meeting loop closes locally (the aftercare digest, the follow-up draft);
this module gives those results one outbound door: a Slack *incoming webhook*
(one POST of ``{"text": ...}``, no OAuth, no rich blocks — the Phase-38
posture). Three pieces, all pure except the connector's eventual POST:

  - ``slack_message_for(digest, what)`` — the exact message text for one
    export kind (``digest`` | ``followup``), in Slack mrkdwn conventions,
    capped honestly (a visible truncation notice, never a silent cut). This
    text IS the proposal preview AND the body Slack receives: executed ==
    previewed, byte for byte.

  - ``slack_webhook_host(url)`` — validates the configured webhook URL
    (https with a host, or it raises) and returns the lowercased host.

  - ``build_slack_connector(webhook_url)`` — wraps the Phase-38 host-gated
    webhook connector with a manifest allow-listing EXACTLY the configured
    URL's host (setting the URL is the consent for that host; there is no
    second list to maintain).

The credential rule (Slack treats webhook URLs as secrets): the URL never
enters a proposal payload, a broadcast, or an API response. The stored
payload carries only ``{"body": {"text": ...}}``; this connector injects the
configured URL in memory at execution time, so the credential never rests in
the DB and can never ride ``GET /api/meetings/{id}/proposals``.
"""
from __future__ import annotations

from typing import Any, Callable, Optional
from urllib.parse import urlparse

from .plugins.actuators import ActuatorProposal
from .plugins.builtin.webhook_post_actuator import build_webhook_connector

# Slack renders long messages poorly and truncates around 4k characters; cap
# below that with a visible notice so nothing is ever cut silently.
SLACK_TEXT_LIMIT: int = 3800
TRUNCATION_NOTICE: str = "\n…(truncated to fit Slack; the full version lives in HoldSpeak)"

EXPORT_KINDS: tuple[str, ...] = ("digest", "followup")


# Plain http is honest only where the wire never leaves the machine — it
# lets the closeout (and a curious user) point at a local receiver.
_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


def slack_webhook_host(url: str) -> str:
    """Validate a Slack incoming-webhook URL and return its lowercased host.

    THE rule, shared by the config layer and the settings boundary: https
    with a host (plain http is allowed for loopback hosts only). Raises
    ``ValueError`` otherwise; an empty URL is also an error here — callers
    gate on "configured" before reaching this.
    """
    text = str(url or "").strip()
    if not text:
        raise ValueError("no Slack webhook URL is configured")
    parsed = urlparse(text)
    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError("the Slack webhook URL must have a host")
    if parsed.scheme != "https" and not (
        parsed.scheme == "http" and host in _LOOPBACK_HOSTS
    ):
        raise ValueError(
            "the Slack webhook URL must be https (plain http is allowed for loopback only)"
        )
    return host


def _cap(text: str) -> str:
    """Apply the honest length cap: truncate WITH a visible notice."""
    if len(text) <= SLACK_TEXT_LIMIT:
        return text
    keep = SLACK_TEXT_LIMIT - len(TRUNCATION_NOTICE)
    return text[:keep].rstrip() + TRUNCATION_NOTICE


def _markdown_to_mrkdwn(markdown: str) -> str:
    """Convert the follow-up draft's markdown to Slack mrkdwn conventions.

    Deliberately minimal: it handles exactly what ``build_followup_draft``
    emits (``#``/``##`` headers and ``- `` bullets). Slack has no headers, so
    they become bold lines; bullets become the dot Slack renders natively.
    """
    lines: list[str] = []
    for line in markdown.splitlines():
        if line.startswith("## "):
            lines.append(f"*{line[3:].strip()}*")
        elif line.startswith("# "):
            lines.append(f"*{line[2:].strip()}*")
        elif line.startswith("- "):
            lines.append(f"• {line[2:]}")
        else:
            lines.append(line)
    return "\n".join(lines)


def _digest_message(digest: dict[str, Any]) -> str:
    """The aftercare digest as one Slack message: decided, open, changed."""
    title = str(digest.get("meeting_title") or "").strip() or "Meeting"
    date = str(digest.get("meeting_date") or "")[:10]
    header = f"*{title}*" + (f" ({date})" if date else "")

    sections: list[str] = [header]

    decisions = digest.get("decisions") or []
    decision_lines = ["*What we decided*"]
    for d in decisions:
        decision = str(d.get("decision") or "").strip()
        if not decision:
            continue
        rationale = str(d.get("rationale") or "").strip()
        decision_lines.append(
            f"• {decision}" + (f". Why: {rationale}" if rationale else "")
        )
    if len(decision_lines) > 1:
        sections.append("\n".join(decision_lines))

    by_owner = (digest.get("open_items") or {}).get("by_owner") or []
    open_lines = ["*Still open*"]
    for group in by_owner:
        owner = group.get("owner") or "Unassigned"
        for item in group.get("items") or []:
            task = str(item.get("task") or "").strip()
            if not task:
                continue
            due = str(item.get("due") or "").strip()
            open_lines.append(f"• {owner}: {task}" + (f" (due {due})" if due else ""))
    if len(open_lines) > 1:
        sections.append("\n".join(open_lines))

    since = digest.get("since_last_meeting")
    if since and since.get("changed"):
        prev = (since.get("previous_meeting") or {}).get("title") or "the last meeting"
        counts = []
        if since.get("new_decisions"):
            counts.append(f"{len(since['new_decisions'])} new decision(s)")
        if since.get("new_actions"):
            counts.append(f"{len(since['new_actions'])} new action item(s)")
        if since.get("closed_actions"):
            counts.append(f"{len(since['closed_actions'])} closed since last time")
        sections.append(f"*Since {prev}:* " + ", ".join(counts))

    return "\n\n".join(sections)


def slack_message_for(digest: dict[str, Any], what: str) -> str:
    """The exact Slack message text for one export kind.

    ``what`` is ``"digest"`` (the aftercare rollup) or ``"followup"`` (the
    HS-49-04 draft, converted to mrkdwn). Anything else raises ``ValueError``.
    The result is both the proposal preview and the body Slack receives.
    """
    if what == "digest":
        return _cap(_digest_message(digest))
    if what == "followup":
        from .meeting_aftercare import build_followup_draft

        return _cap(_markdown_to_mrkdwn(build_followup_draft(digest)))
    raise ValueError(f"unknown export kind: {what!r} (expected 'digest' or 'followup')")


def build_slack_connector(
    webhook_url: str,
    *,
    client: Optional[Callable[..., Any]] = None,
) -> Callable[[Any], dict[str, Any]]:
    """A connector POSTing an approved Slack-export proposal's text.

    Wraps the Phase-38 ``build_webhook_connector`` with a manifest
    allow-listing exactly the configured URL's host, and injects the URL into
    the payload **in memory only** — the stored proposal never carries the
    credential. ``client`` is the test seam (no real HTTP in the suite).
    """
    host = slack_webhook_host(webhook_url)
    inner = build_webhook_connector(allowed_hosts=[host], client=client)

    def connector(proposal: Any) -> dict[str, Any]:
        merged = dict(getattr(proposal, "payload", None) or {})
        merged["url"] = str(webhook_url).strip()
        view = ActuatorProposal(
            target=str(getattr(proposal, "target", "slack")),
            action=str(getattr(proposal, "action", "post_message")),
            preview=str(getattr(proposal, "preview", "")),
            payload=merged,
            reversible=bool(getattr(proposal, "reversible", False)),
            required_capabilities=tuple(
                getattr(proposal, "required_capabilities", ()) or ()
            ),
        )
        return inner(view)

    return connector


__all__ = [
    "EXPORT_KINDS",
    "SLACK_TEXT_LIMIT",
    "TRUNCATION_NOTICE",
    "build_slack_connector",
    "slack_message_for",
    "slack_webhook_host",
]
