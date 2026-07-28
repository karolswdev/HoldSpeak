"""The tool-call gate — a held hand, not a watched one (HS-104-02).

A steered agent's risky tool call stops and asks the desk. This
module is the agent-side half plus the shared vocabulary:

- **Config** (``~/.holdspeak/gate.json``, ``gate_schema: 1``): the
  master switch AND a per-repo matcher — the double opt-in. Both off
  by default. Arming is a decision; the file is edited only by
  ``holdspeak gate arm|disarm|allow|revoke`` (or by hand).
- **The hook runner** (:func:`run_hook`): what
  ``holdspeak gate hook`` executes on Claude Code's PreToolUse. Fast
  path first: when the gate is not armed for (cwd, tool), it exits
  inert — no proposal row, no audit row, no hub contact, bounded
  latency. When armed it POSTs the REDACTED proposal (sha256 + first
  120 chars, computed here so the full arguments never leave the
  agent process) to the hub over loopback and blocks the agent's
  loop, polling until a decision or expiry. **Fail-closed**: armed +
  hub unreachable / 500 / timeout ⇒ deny with the named reason.
  There is no code path that allows on error, and no
  timeout-auto-allow anywhere.
- **Install** (:func:`install_block`): prints the hook block for the
  user to add to ``~/.claude/settings.json`` themselves. Touching
  another app's settings is a decision, so this module NEVER edits
  ``~/.claude``.

The hub-side half (receive, decide from the shade, restart
invalidation, audit) lives in
:mod:`holdspeak.web.routes.system.gate_routes` over
:mod:`holdspeak.db.gate`.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional
from urllib import error as urlerror
from urllib import request as urlrequest

GATE_CONFIG_SCHEMA = 1
GATE_CONFIG_FILE = Path.home() / ".holdspeak" / "gate.json"

#: The one tool family held this phase (the story's decision: start
#: with Bash only; a wider matcher is a reviewed edit).
DEFAULT_TOOLS = ("Bash",)

#: How long a proposal stays decidable. Expiry is a DENY. The Claude
#: Code hook block carries a longer timeout so the deny reason lands
#: before the agent kills the hook.
DEFAULT_TTL_SECONDS = 240.0
HOOK_TIMEOUT_SECONDS = 300

DEFAULT_HUB_URL = "http://127.0.0.1:8765"
POLL_INTERVAL_SECONDS = 1.0

ARGS_HEAD_CHARS = 120


# -- config ----------------------------------------------------------------


@dataclass
class GateConfig:
    armed: bool = False
    #: repo path (resolved, absolute) → held tool names.
    repos: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_schema": GATE_CONFIG_SCHEMA,
            "armed": self.armed,
            "repos": {path: list(tools) for path, tools in sorted(self.repos.items())},
        }


def load_gate_config(path: Path | None = None) -> GateConfig:
    """A missing or unreadable file is the OFF state — the gate never
    arms itself by accident."""
    target = path or GATE_CONFIG_FILE
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return GateConfig()
    if not isinstance(raw, dict):
        return GateConfig()
    repos: dict[str, list[str]] = {}
    raw_repos = raw.get("repos")
    if isinstance(raw_repos, dict):
        for repo_path, tools in raw_repos.items():
            if isinstance(tools, list):
                cleaned = [str(t).strip() for t in tools if str(t).strip()]
                if cleaned:
                    repos[str(repo_path)] = cleaned
    return GateConfig(armed=bool(raw.get("armed")), repos=repos)


def save_gate_config(config: GateConfig, path: Path | None = None) -> Path:
    target = path or GATE_CONFIG_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(config.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return target


def gate_matches(config: GateConfig, *, cwd: str, tool: str) -> bool:
    """The double opt-in, resolved: master switch AND a configured
    repo whose path contains ``cwd`` AND the tool in that repo's
    list."""
    if not config.armed or not tool:
        return False
    try:
        cwd_path = Path(cwd).resolve()
    except OSError:
        return False
    for repo_path, tools in config.repos.items():
        if tool not in tools:
            continue
        try:
            repo_resolved = Path(repo_path).expanduser().resolve()
        except OSError:
            continue
        if cwd_path == repo_resolved or repo_resolved in cwd_path.parents:
            return True
    return False


# -- redaction -------------------------------------------------------------


def redact_args(tool_input: Mapping[str, Any] | None) -> tuple[str, str]:
    """(sha256, first-120-chars) over the canonical JSON of the tool
    input — computed agent-side so the full payload never crosses the
    wire, let alone lands in a row or a log."""
    canonical = json.dumps(
        dict(tool_input or {}), separators=(",", ":"), sort_keys=True, ensure_ascii=False
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return digest, canonical[:ARGS_HEAD_CHARS]


# -- supervised principal lifecycle ----------------------------------------


def _credential_path(hub_url: str, session_id: str) -> Path:
    hub_key = hashlib.sha256(hub_url.rstrip("/").encode()).hexdigest()[:16]
    session_key = hashlib.sha256(session_id.encode()).hexdigest()
    return Path.home() / ".holdspeak" / "agent_credentials" / hub_key / session_key


def _owner_token() -> str:
    from .config import Config

    return str(Config.load().meeting.web_auth_token or "").strip()


def issue_agent_credential(
    session_id: str, hub_url: str, *, force: bool = False
) -> str:
    """Mint or recover the hub-issued credential for one Claude session."""
    inherited = str(os.environ.get("HOLDSPEAK_AGENT_CREDENTIAL") or "").strip()
    if inherited:
        return inherited
    identity = f"claude:{str(session_id).strip()}"
    path = _credential_path(hub_url, identity)
    try:
        cached = path.read_text(encoding="utf-8").strip()
    except OSError:
        cached = ""
    if cached and not force:
        return cached
    owner = _owner_token()
    if not owner:
        raise RuntimeError("owner credential unavailable")
    data = json.dumps({"identity": identity}).encode("utf-8")
    request = urlrequest.Request(
        f"{hub_url.rstrip('/')}/api/principals/agents",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {owner}",
        },
        method="POST",
    )
    status, payload = _send(request, 5.0)
    credential = str(payload.get("credential") or "").strip()
    if status != 201 or not credential:
        raise RuntimeError(f"agent credential issuance refused (HTTP {status})")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(credential, encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return credential


def revoke_agent_credential(session_id: str, hub_url: str) -> bool:
    """Revoke one session credential and remove its process-local cache."""
    identity = f"claude:{str(session_id).strip()}"
    path = _credential_path(hub_url, identity)
    token = str(os.environ.get("HOLDSPEAK_AGENT_CREDENTIAL") or "").strip()
    if not token:
        try:
            token = path.read_text(encoding="utf-8").strip()
        except OSError:
            token = ""
    if not token:
        return False
    request = urlrequest.Request(
        f"{hub_url.rstrip('/')}/api/principals/self",
        headers={"Authorization": f"Bearer {token}"},
        method="DELETE",
    )
    try:
        status, payload = _send(request, 5.0)
    except Exception:
        return False
    try:
        path.unlink()
    except OSError:
        pass
    return status == 200 and bool(payload.get("revoked"))


def run_session_start(payload: Mapping[str, Any], *, hub_url: str | None = None) -> bool:
    session_id = str(payload.get("session_id") or "").strip()
    if not session_id:
        return False
    base = (hub_url or os.environ.get("HOLDSPEAK_HUB_URL") or DEFAULT_HUB_URL).rstrip("/")
    try:
        return bool(issue_agent_credential(session_id, base, force=True))
    except Exception:
        return False


def run_session_end(payload: Mapping[str, Any], *, hub_url: str | None = None) -> bool:
    session_id = str(payload.get("session_id") or "").strip()
    if not session_id:
        return False
    base = (hub_url or os.environ.get("HOLDSPEAK_HUB_URL") or DEFAULT_HUB_URL).rstrip("/")
    return revoke_agent_credential(session_id, base)


# -- the hook runner -------------------------------------------------------


@dataclass(frozen=True)
class HookDecision:
    """What the hook tells Claude Code. ``deny=None`` means inert /
    no opinion (exit 0, no output): the call proceeds through the
    agent's own permission flow."""

    deny: Optional[str]  # the reason, ridden back to the agent verbatim

    def to_hook_output(self) -> Optional[dict[str, Any]]:
        if self.deny is None:
            return None
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": self.deny,
            }
        }


def run_hook(
    payload: Mapping[str, Any],
    *,
    config: GateConfig | None = None,
    hub_url: str | None = None,
    http_post: Callable[[str, dict[str, Any], float], tuple[int, dict[str, Any]]] | None = None,
    http_get: Callable[[str, float], tuple[int, dict[str, Any]]] | None = None,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], float] = time.monotonic,
    ttl_seconds: float = DEFAULT_TTL_SECONDS,
    agent_credential: str | None = None,
) -> HookDecision:
    """One PreToolUse arrival, start to verdict.

    The idempotency key is minted HERE, once per hook invocation
    (``tool_use_id`` when Claude Code provides one, else a UUID), so a
    network-blip retry re-lands on the same proposal instead of
    minting a twin card — HS-104-03 attacks exactly this seam.
    """
    cfg = config if config is not None else load_gate_config()
    if ttl_seconds == DEFAULT_TTL_SECONDS:
        try:
            ttl_seconds = float(os.environ.get("HOLDSPEAK_GATE_TTL", "") or ttl_seconds)
        except ValueError:
            pass
    tool = str(payload.get("tool_name") or "").strip()
    cwd = str(payload.get("cwd") or "").strip()

    # The inert fast path: not armed for this (cwd, tool) — no
    # proposal, no audit, no hub contact.
    if not gate_matches(cfg, cwd=cwd, tool=tool):
        return HookDecision(deny=None)

    session_id = str(payload.get("session_id") or "").strip() or "unknown-session"
    proposal_id = str(payload.get("tool_use_id") or "").strip() or f"gate-{uuid.uuid4()}"
    args_sha256, args_head = redact_args(payload.get("tool_input"))

    base = (hub_url or os.environ.get("HOLDSPEAK_HUB_URL") or DEFAULT_HUB_URL).rstrip("/")
    if http_post is None or http_get is None:
        try:
            credential = str(agent_credential or issue_agent_credential(session_id, base))
        except Exception:
            return HookDecision(
                deny="gate armed but the agent principal could not authenticate; the call was not run"
            )
    else:
        credential = str(agent_credential or "")
    post = http_post or (
        lambda url, body, timeout: _default_post(
            url, body, timeout, credential=credential
        )
    )
    get = http_get or (
        lambda url, timeout: _default_get(url, timeout, credential=credential)
    )

    body = {
        "id": proposal_id,
        "tool": tool,
        "args_sha256": args_sha256,
        "args_head": args_head,
        "cwd": cwd,
        "ttl_seconds": ttl_seconds,
    }
    parent_operation_id = str(
        os.environ.get("HOLDSPEAK_PARENT_OPERATION_ID") or ""
    ).strip()
    if parent_operation_id:
        body["parent_operation_id"] = parent_operation_id

    # Fail-closed from here down: the gate is armed and matched, so
    # every error path is a deny with its name — never an allow.
    try:
        status, response = post(f"{base}/api/gate/proposals", body, 5.0)
    except Exception:
        return HookDecision(deny="gate armed but hub unreachable; the call was not run")
    if status != 200:
        return HookDecision(
            deny=f"gate armed but the hub refused the proposal (HTTP {status}); the call was not run"
        )
    state = str(response.get("state") or "")
    if state in ("approved",):
        return HookDecision(deny=None)
    if state in ("denied", "expired", "invalidated"):
        return HookDecision(deny=_deny_reason(response))

    deadline = now() + ttl_seconds
    while now() < deadline:
        sleep(POLL_INTERVAL_SECONDS)
        try:
            status, response = get(f"{base}/api/gate/proposals/{proposal_id}", 5.0)
        except Exception:
            return HookDecision(deny="gate armed but the hub stopped answering mid-hold; the call was not run")
        if status != 200:
            return HookDecision(
                deny=f"gate armed but the decision read failed (HTTP {status}); the call was not run"
            )
        state = str(response.get("state") or "")
        if state == "approved":
            return HookDecision(deny=None)
        if state in ("denied", "expired", "invalidated"):
            return HookDecision(deny=_deny_reason(response))
    return HookDecision(
        deny="gate hold expired with no decision; the call was not run"
    )


def _deny_reason(response: Mapping[str, Any]) -> str:
    state = str(response.get("state") or "denied")
    reason = str(response.get("reason") or "").strip()
    if state == "denied":
        base_text = "denied from the desk"
    elif state == "expired":
        base_text = "the hold expired with no decision"
    else:
        base_text = "the hold was invalidated (hub restart); propose again by retrying"
    if reason:
        return f"{base_text}: {reason}"
    return base_text


def _default_post(
    url: str,
    body: dict[str, Any],
    timeout: float,
    *,
    credential: str = "",
) -> tuple[int, dict[str, Any]]:
    data = json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if credential:
        headers["Authorization"] = f"Bearer {credential}"
    req = urlrequest.Request(url, data=data, headers=headers)
    return _send(req, timeout)


def _default_get(
    url: str, timeout: float, *, credential: str = ""
) -> tuple[int, dict[str, Any]]:
    headers = {"Authorization": f"Bearer {credential}"} if credential else {}
    return _send(urlrequest.Request(url, headers=headers), timeout)


def _send(req: "urlrequest.Request", timeout: float) -> tuple[int, dict[str, Any]]:
    try:
        with urlrequest.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8") or "{}")
            return resp.status, payload if isinstance(payload, dict) else {}
    except urlerror.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8") or "{}")
        except Exception:
            payload = {}
        return exc.code, payload if isinstance(payload, dict) else {}


# -- the usage report leg (HS-104-05) --------------------------------------


def summarize_transcript_usage(transcript_path: Path) -> Optional[dict[str, Any]]:
    """Session token totals from the agent's OWN transcript (the
    file Claude Code hands the Stop hook). Only NUMBERS and the model
    name are extracted — no message text ever leaves this function.
    Each cache figure stays its own total, never summed."""
    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_creation_tokens": 0,
    }
    model = ""
    saw_usage = False
    try:
        with transcript_path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                message = entry.get("message") if isinstance(entry, dict) else None
                if not isinstance(message, dict):
                    continue
                usage = message.get("usage")
                if not isinstance(usage, dict):
                    continue
                saw_usage = True
                model = str(message.get("model") or model)
                totals["input_tokens"] += int(usage.get("input_tokens") or 0)
                totals["output_tokens"] += int(usage.get("output_tokens") or 0)
                totals["cache_read_tokens"] += int(usage.get("cache_read_input_tokens") or 0)
                totals["cache_creation_tokens"] += int(
                    usage.get("cache_creation_input_tokens") or 0
                )
    except OSError:
        return None
    if not saw_usage:
        return None
    return {"model": model, **totals}


def run_stop_hook(
    payload: Mapping[str, Any],
    *,
    config: GateConfig | None = None,
    hub_url: str | None = None,
    http_post: Callable[[str, dict[str, Any], float], tuple[int, dict[str, Any]]] | None = None,
) -> bool:
    """The Stop-event leg: report the session's usage totals to the
    hub, for sessions in a gate-held repo only (the same double
    opt-in). Telemetry, not consent — every failure is silent and
    the agent's stop is never blocked. Returns whether a report was
    sent."""
    cfg = config if config is not None else load_gate_config()
    cwd = str(payload.get("cwd") or "").strip()
    # The matcher's repo opt-in, tool-independent: usage reports ride
    # for any repo the gate holds at all.
    held_repo = any(
        gate_matches(cfg, cwd=cwd, tool=tool)
        for tools in cfg.repos.values()
        for tool in tools
    )
    if not cfg.armed or not held_repo:
        return False
    session_id = str(payload.get("session_id") or "").strip()
    transcript = str(payload.get("transcript_path") or "").strip()
    if not session_id or not transcript:
        return False
    usage = summarize_transcript_usage(Path(transcript).expanduser())
    if usage is None:
        return False
    base = (hub_url or os.environ.get("HOLDSPEAK_HUB_URL") or DEFAULT_HUB_URL).rstrip("/")
    if http_post is None:
        try:
            credential = issue_agent_credential(session_id, base)
        except Exception:
            return False
        post = lambda url, body, timeout: _default_post(
            url, body, timeout, credential=credential
        )
    else:
        post = http_post
    try:
        status, _ = post(
            f"{base}/api/gate/usage",
            usage,
            5.0,
        )
    except Exception:
        return False
    return status == 200


def run_post_tool_hook(
    payload: Mapping[str, Any],
    *,
    config: GateConfig | None = None,
    hub_url: str | None = None,
) -> bool:
    """Report that an approved, claimed tool call actually completed."""
    cfg = config if config is not None else load_gate_config()
    tool = str(payload.get("tool_name") or "").strip()
    cwd = str(payload.get("cwd") or "").strip()
    proposal_id = str(payload.get("tool_use_id") or "").strip()
    session_id = str(payload.get("session_id") or "").strip()
    if not proposal_id or not session_id or not gate_matches(cfg, cwd=cwd, tool=tool):
        return False
    base = (hub_url or os.environ.get("HOLDSPEAK_HUB_URL") or DEFAULT_HUB_URL).rstrip("/")
    try:
        credential = issue_agent_credential(session_id, base)
        status, _ = _default_post(
            f"{base}/api/gate/proposals/{proposal_id}/receipt",
            {"outcome": "succeeded"},
            5.0,
            credential=credential,
        )
    except Exception:
        return False
    return status in (200, 202)


# -- install ---------------------------------------------------------------


def install_block(executable: str = "holdspeak") -> str:
    """The hook block the USER adds to ``~/.claude/settings.json``.
    Printed, never written: this module does not edit another app's
    config."""
    block = {
        "hooks": {
            "SessionStart": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"{executable} gate hook",
                            "timeout": 15,
                        }
                    ]
                }
            ],
            "PreToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"{executable} gate hook",
                            "timeout": HOOK_TIMEOUT_SECONDS,
                        }
                    ],
                }
            ],
            "PostToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"{executable} gate hook",
                            "timeout": 15,
                        }
                    ],
                }
            ],
            # HS-104-05: the session-receipt usage report. Same
            # command; the hook dispatches on hook_event_name.
            "Stop": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"{executable} gate hook",
                            "timeout": 15,
                        }
                    ]
                }
            ],
            "SessionEnd": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"{executable} gate hook",
                            "timeout": 15,
                        }
                    ]
                }
            ],
        }
    }
    return json.dumps(block, indent=2)
