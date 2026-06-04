"""Webhook POST write connector + actuator (Phase 38, HS-38-03).

The second reference connector on the HS-38-01 framework — and the most reusable.
It exercises the *other* gate, `network:outbound`: an HTTP POST to an **allow-listed
host**, which covers Slack / Teams *incoming webhooks* and any generic endpoint. It
proves the framework gates network egress as tightly as it gates subprocess egress.

Two halves, the same safety split as the GitHub connector (HS-38-02):

  - `WebhookPostActuator` (the plugin) — `run(context)` returns an `ActuatorProposal`
    whose payload carries `{url, body}` (the target webhook + the JSON message it
    *would* post). It never reaches out — building the proposal is all it does.

  - `build_webhook_connector(...)` (the connector) — built with
    `build_gated_connector`: permission `network:outbound` via
    `PermissionGate.open_outbound_socket`, manifest declaring the **allow-listed
    host(s)**. The connector POSTs the payload's JSON to the target URL; a target
    host **not** on the allow-list is refused **before** egress. A non-2xx response
    (or a transport error) raises → the executor records `failed` + audit. The
    response status is returned as the result.

Decision (resolved here, deferred from HS-38-01): **host allow-listing granularity**
is a *config allow-list of hosts* — `MeetingConfig.webhook_allowed_hosts`. A
proposal's target host must be a member; the list is **default-empty**, so a
misconfigured webhook actuator posts nowhere. Slack/Teams are simply incoming-webhook
URLs whose host is on the allow-list — not bespoke API integrations (no OAuth, no
rich blocks; a plain incoming-webhook POST only).

Like the other connectors this is a **host-side gated connector** the executor
injects (not a discovered pack), opt-in (`register_webhook_post_actuator`, NOT in
`register_builtin_plugins`) and off by default — reached only after approval + the
policy/parity gates + `network:outbound`.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Optional
from urllib.parse import urlparse

from ...logging_config import get_logger
from ..actuator_executor import Connector
from ..gated_connector import (
    GatedOperation,
    WriteConnectorManifest,
    build_gated_connector,
)

log = get_logger("plugins.webhook_post_actuator")

# Per-request wall-clock timeout for the HTTP POST.
DEFAULT_TIMEOUT_SECONDS: float = 10.0

# The HTTP-POST primitive: (url, body) -> WebhookResponse. The default is a urllib
# POST; tests inject a fake so the default suite makes no real HTTP call.
WebhookClient = Callable[[str, Any], "WebhookResponse"]


@dataclass(frozen=True)
class WebhookResponse:
    """The minimal result of a webhook POST the connector cares about."""

    status: int
    body: str = ""


class WebhookPostActuator:
    """Proposes an HTTP POST of a meeting update to a configured webhook URL."""

    id: str = "webhook_post_actuator"
    version: str = "0.1.0"
    kind: str = "actuator"
    execution_mode: str = "inline"
    required_capabilities: list[str] = ["actuator"]

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        url = str(context.get("webhook_url") or "").strip()
        if not url:
            # No destination → cannot build a faithful proposal; an `error`, not a
            # half-formed proposal (no side effect).
            raise ValueError("no webhook_url in context to post to")

        host = urlparse(url).hostname or ""
        if not host:
            raise ValueError(f"webhook_url has no host: {url!r}")

        meeting_title = str(
            context.get("meeting_title") or context.get("title") or "meeting"
        ).strip()
        items = context.get("action_items") or []
        if not isinstance(items, list):
            items = []
        open_items = [it for it in items if isinstance(it, dict)]

        text = (
            f"*{meeting_title}* wrapped — {len(open_items)} action item(s) captured."
        )
        body = {"text": text}

        return {
            "target": "webhook",
            "action": "post_message",
            "preview": f"POST a meeting update to {host}: “{text}”",
            "payload": {"url": url, "body": body},
            "reversible": False,  # a posted message cannot be unsent
            "required_capabilities": ["actuator"],
        }


def _default_post(url: str, body: Any, *, timeout: float) -> WebhookResponse:
    """POST `body` as JSON to `url` via urllib, returning a `WebhookResponse`.

    A non-2xx response arrives as `urllib.error.HTTPError` (itself a response) —
    we convert it to a `WebhookResponse` carrying its code so the connector's
    `interpret` raises a uniform error (→ executor `failed`).
    """
    if isinstance(body, (bytes, bytearray)):
        data = bytes(body)
    elif isinstance(body, str):
        data = body.encode("utf-8")
    else:
        data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, method="POST", headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:  # noqa: S310 — host is allow-listed before this runs
            status = getattr(resp, "status", None) or resp.getcode()
            return WebhookResponse(status=int(status), body=resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as exc:
        return WebhookResponse(status=int(exc.code), body=str(exc.reason or ""))


def _plan(proposal: Any) -> GatedOperation:
    """Build the outbound op (host + the request the opener will POST)."""
    payload = getattr(proposal, "payload", None) or {}
    url = str(payload.get("url") or "").strip()
    body = payload.get("body")
    parsed = urlparse(url)
    host = parsed.hostname or ""
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return GatedOperation.outbound(host, port, request={"url": url, "body": body})


def _interpret(response: Any, op: GatedOperation) -> dict[str, Any]:
    """Map the webhook response into the executor's result dict (or raise → `failed`)."""
    status = getattr(response, "status", None)
    if status is None and isinstance(response, dict):
        status = response.get("status")
    if not isinstance(status, int) or not (200 <= status < 300):
        raise RuntimeError(f"webhook POST to {op.host} returned HTTP {status}")
    log.info("actuator posted webhook to %s (HTTP %s)", op.host, status)
    return {"status": status, "host": op.host}


def build_webhook_connector(
    *,
    allowed_hosts: Any,
    client: Optional[WebhookClient] = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> Connector:
    """A connector that POSTs a proposal's message to an allow-listed webhook host.

    `allowed_hosts` is the host allow-list (from `MeetingConfig.webhook_allowed_hosts`);
    a proposal whose target host is not a member is refused **before** egress. The
    POST routes through `PermissionGate.open_outbound_socket` (`network:outbound`).
    `client` defaults to a urllib POST; tests inject a fake (no real HTTP).
    """
    manifest = WriteConnectorManifest(
        connector_id="webhook_writer",
        permission="network:outbound",
        label="Webhook poster",
        description="HTTP POST to an allow-listed host only; URL + body from the approved proposal.",
        allowed_hosts=tuple(allowed_hosts),
    )
    post = client or (lambda url, body: _default_post(url, body, timeout=timeout_seconds))
    return build_gated_connector(
        manifest,
        plan=_plan,
        interpret=_interpret,
        opener=lambda op: post((op.request or {})["url"], (op.request or {}).get("body")),
    )


def register_webhook_post_actuator(host: Any) -> str:
    """Register the webhook actuator on a host (behind the actuator gate).

    Explicit + opt-in: NOT part of `register_builtin_plugins`, so the default
    plugin set + routing chains are unchanged. The host capability-blocks it
    unless `actuator` is in `enabled_capabilities`.
    """
    host.register(WebhookPostActuator())
    return WebhookPostActuator.id


__all__ = [
    "DEFAULT_TIMEOUT_SECONDS",
    "WebhookClient",
    "WebhookPostActuator",
    "WebhookResponse",
    "build_webhook_connector",
    "register_webhook_post_actuator",
]
