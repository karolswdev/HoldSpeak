"""Render the legacy meeting documents used by the channel source registry.

Slack delivery belongs to the channel contract. This module keeps only the
deterministic Markdown projection needed by document sources and the URL
validator used by the generic companion webhook. The old aftercare Slack
proposal connector is intentionally gone.
"""
from __future__ import annotations

from typing import Any, Callable, Optional
from urllib.parse import urlparse

# Plain http is honest only where the wire never leaves the machine — it
# remains useful for the generic companion webhook's local test receiver.
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


def _digest_markdown(digest: dict[str, Any]) -> str:
    """Render the stored aftercare digest as complete Markdown.

    This is the document-source renderer used by the channels.  It deliberately
    has no Slack length cap: a channel decides whether a payload fits before the
    dispatch boundary, and a document must never be silently shortened.
    """
    title = str(digest.get("meeting_title") or "").strip() or "Meeting"
    date = str(digest.get("meeting_date") or "")[:10]
    header = f"# {title}" + (f"\n{date}" if date else "")
    sections: list[str] = [header]

    decisions = digest.get("decisions") or []
    decision_lines = ["## What we decided"]
    for item in decisions:
        decision = str(item.get("decision") or "").strip()
        if not decision:
            continue
        rationale = str(item.get("rationale") or "").strip()
        decision_lines.append(
            f"- {decision}" + (f". Why: {rationale}" if rationale else "")
        )
    if len(decision_lines) > 1:
        sections.append("\n".join(decision_lines))

    by_owner = (digest.get("open_items") or {}).get("by_owner") or []
    open_lines = ["## Still open"]
    for group in by_owner:
        owner = str(group.get("owner") or "Unassigned")
        for item in group.get("items") or []:
            task = str(item.get("task") or "").strip()
            if not task:
                continue
            due = str(item.get("due") or "").strip()
            open_lines.append(f"- {owner}: {task}" + (f" (due {due})" if due else ""))
    if len(open_lines) > 1:
        sections.append("\n".join(open_lines))

    since = digest.get("since_last_meeting")
    if since and since.get("changed"):
        previous = (since.get("previous_meeting") or {}).get("title") or "the last meeting"
        lines = [f"## Since {previous}"]
        new_decisions = since.get("new_decisions") or []
        if new_decisions:
            lines.append("New decisions:")
            lines.extend(f"- {str(item.get('decision') or '').strip()}" for item in new_decisions)
        new_actions = since.get("new_actions") or []
        if new_actions:
            lines.append("New action items:")
            lines.extend(f"- {str(item.get('task') or '').strip()}" for item in new_actions)
        closed = since.get("closed_actions") or []
        if closed:
            lines.append("Closed since last time:")
            lines.extend(f"- {str(item.get('task') or '').strip()}" for item in closed)
        if len(lines) > 1:
            sections.append("\n".join(lines))

    if len(sections) == 1:
        sections.append("Nothing was decided and nothing is open for this meeting.")
    return "\n\n".join(sections)


def document_markdown_for(digest: dict[str, Any], what: str) -> str:
    """Return the complete Markdown body for a channel document source.

    ``digest`` is already the persisted aftercare projection.  The function is
    deterministic and does not call a model or read a transcript.  ``what`` is
    ``digest`` or ``followup``; unknown values are refused by name.
    """
    if what == "digest":
        return _digest_markdown(digest)
    if what == "followup":
        from .meeting_aftercare import build_followup_draft

        return build_followup_draft(digest)
    raise ValueError(f"unknown export kind: {what!r} (expected 'digest' or 'followup')")


def build_url_webhook_connector(
    webhook_url: str,
    *,
    client: Optional[Callable[..., Any]] = None,
) -> Callable[[Any], dict[str, Any]]:
    """A generic webhook connector (HSM-14) — the Slack connector, minus the
    slack.com host check, for the iPad desk's Webhook connector.

    Same credential discipline: the manifest allow-lists exactly the configured
    URL's host, and the URL is injected into the payload **in memory only** —
    the stored proposal never carries it. ``client`` is the test seam.
    """
    from urllib.parse import urlparse
    from .plugins.actuators import ActuatorProposal
    from .plugins.builtin.webhook_post_actuator import build_webhook_connector

    parsed = urlparse(str(webhook_url).strip())
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError(f"invalid webhook URL: {webhook_url!r}")
    host = parsed.hostname.lower()
    inner = build_webhook_connector(allowed_hosts=[host], client=client)

    def connector(proposal: Any) -> dict[str, Any]:
        merged = dict(getattr(proposal, "payload", None) or {})
        merged["url"] = str(webhook_url).strip()
        view = ActuatorProposal(
            target=str(getattr(proposal, "target", "webhook")),
            action=str(getattr(proposal, "action", "post_message")),
            preview=str(getattr(proposal, "preview", "")),
            payload=merged,
            reversible=bool(getattr(proposal, "reversible", False)),
            required_capabilities=tuple(getattr(proposal, "required_capabilities", ()) or ()),
        )
        return inner(view)

    return connector


__all__ = [
    "build_url_webhook_connector",
    "document_markdown_for",
    "slack_webhook_host",
]
