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
from typing import Any, Callable, Mapping, NamedTuple, Optional
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
    #: Paths armed on their own, by a launch the owner pressed (Hand to
    #: agent). Held whatever the master switch says; the switch still
    #: decides every other listed repo, so arming one worktree never holds
    #: another.
    armed_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        doc: dict[str, Any] = {
            "gate_schema": GATE_CONFIG_SCHEMA,
            "armed": self.armed,
            "repos": {path: list(tools) for path, tools in sorted(self.repos.items())},
        }
        if self.armed_paths:
            doc["armed_paths"] = sorted(set(self.armed_paths))
        return doc


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
    raw_paths = raw.get("armed_paths")
    armed_paths = [
        str(path) for path in (raw_paths if isinstance(raw_paths, list) else [])
        if str(path).strip() and str(path) in repos
    ]
    return GateConfig(armed=bool(raw.get("armed")), repos=repos, armed_paths=armed_paths)


def save_gate_config(config: GateConfig, path: Path | None = None) -> Path:
    """Write the gate file whole: a temp file in the same folder, then an
    atomic replace, so a reader never sees half a file."""
    target = path or GATE_CONFIG_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(f".{target.name}.{os.getpid()}.{uuid.uuid4().hex[:8]}.tmp")
    tmp.write_text(
        json.dumps(config.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(tmp, target)
    return target


def update_gate_config(
    mutate: Callable[[GateConfig], Any], path: Path | None = None
) -> Any:
    """Read, change and write the gate file under one exclusive lock, so two
    writers (two launches arming at once) never lose each other's change.
    Returns what ``mutate`` returns."""
    import fcntl

    target = path or GATE_CONFIG_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    lock_path = target.with_name(target.name + ".lock")
    with open(lock_path, "a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            config = load_gate_config(target)
            result = mutate(config)
            save_gate_config(config, target)
            return result
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def gate_matches(config: GateConfig, *, cwd: str, tool: str) -> bool:
    """The double opt-in, resolved: master switch AND a configured
    repo whose path contains ``cwd`` AND the tool in that repo's
    list."""
    return gate_match_root(config, cwd=cwd, tool=tool) is not None


def gate_match_root(config: GateConfig, *, cwd: str, tool: str) -> Optional[str]:
    """The held repo path that contains ``cwd`` for ``tool`` (the nearest
    one when held paths nest), or ``None``: the matcher of
    :func:`gate_matches`, naming its match. Conductor K5 reads a held
    call against this root."""
    if not tool:
        return None
    try:
        cwd_path = Path(cwd).resolve()
    except OSError:
        return None
    own = set(config.armed_paths)
    best: Optional[tuple[int, str]] = None
    for repo_path, tools in config.repos.items():
        if tool not in tools:
            continue
        if not config.armed and repo_path not in own:
            continue
        try:
            repo_resolved = Path(repo_path).expanduser().resolve()
        except OSError:
            continue
        if cwd_path == repo_resolved or repo_resolved in cwd_path.parents:
            depth = len(repo_resolved.parts)
            if best is None or depth > best[0]:
                best = (depth, str(repo_resolved))
    return best[1] if best else None


# -- redaction -------------------------------------------------------------


class RedactedCall(NamedTuple):
    """One tool call as the hook may send it: the hash of the real call, the
    first :data:`ARGS_HEAD_CHARS` of its REDACTED canonical text, and the
    length of that whole redacted text (PHILO-14 A5).

    The length is the redacted text's, never the raw call's: the raw length
    would be a side channel for the size of a redacted secret. The desk says
    ``+N CHARS`` with ``N = length - len(head)`` and never offers Approve on
    a call longer than its head."""

    sha256: str
    head: str
    length: int


def redact_call(tool_input: Mapping[str, Any] | None) -> RedactedCall:
    """The hash, the head and the redacted length of one call, computed
    agent-side so the full payload never crosses the wire, let alone lands
    in a row or a log."""
    canonical = json.dumps(
        dict(tool_input or {}), separators=(",", ":"), sort_keys=True, ensure_ascii=False
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    # PHILO-14 C0: the hash is over the real call; the stored head is
    # secret-redacted on the WHOLE text before it is cut.
    from .memory.defense import redact

    redacted = redact(canonical)
    return RedactedCall(digest, redacted[:ARGS_HEAD_CHARS], len(redacted))


def redact_args(tool_input: Mapping[str, Any] | None) -> tuple[str, str]:
    """(sha256, first-120-chars) over the canonical JSON of the tool
    input (:func:`redact_call` without the length)."""
    call = redact_call(tool_input)
    return call.sha256, call.head


# -- supervised principal lifecycle ----------------------------------------


def _credential_path(hub_url: str, session_id: str) -> Path:
    hub_key = hashlib.sha256(hub_url.rstrip("/").encode()).hexdigest()[:16]
    session_key = hashlib.sha256(session_id.encode()).hexdigest()
    return Path.home() / ".holdspeak" / "agent_credentials" / hub_key / session_key


def _owner_token() -> str:
    from .config import Config

    return str(Config.load().meeting.web_auth_token or "").strip()


#: The coding agents whose hooks reach the gate; a session's identity is
#: ``<agent>:<session_id>`` (the agent registry's session key).
GATE_AGENTS = ("claude", "codex")


def agent_identity(session_id: str, agent: str = "claude") -> str:
    """The principal identity of one agent session: ``claude:<id>`` or ``codex:<id>``."""
    name = str(agent or "claude").strip().lower()
    if name not in GATE_AGENTS:
        raise ValueError(f"agent must be one of: {', '.join(GATE_AGENTS)}")
    return f"{name}:{str(session_id).strip()}"


def issue_agent_credential(
    session_id: str, hub_url: str, *, force: bool = False, agent: str = "claude",
) -> str:
    """Mint or recover the hub-issued credential for one agent session."""
    inherited = str(os.environ.get("HOLDSPEAK_AGENT_CREDENTIAL") or "").strip()
    if inherited:
        return inherited
    identity = agent_identity(session_id, agent)
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


def revoke_agent_credential(session_id: str, hub_url: str, *, agent: str = "claude") -> bool:
    """Revoke one session credential and remove its process-local cache."""
    identity = agent_identity(session_id, agent)
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


def run_session_start(
    payload: Mapping[str, Any], *, hub_url: str | None = None, agent: str = "claude",
) -> bool:
    session_id = str(payload.get("session_id") or "").strip()
    if not session_id:
        return False
    base = (hub_url or os.environ.get("HOLDSPEAK_HUB_URL") or DEFAULT_HUB_URL).rstrip("/")
    try:
        return bool(issue_agent_credential(session_id, base, force=True, agent=agent))
    except Exception:
        return False


#: SessionEnd reasons after which the process keeps running: ``/clear`` and
#: ``/resume`` end the conversation, not the agent, so the process credential
#: (the one the spawn put in the environment) stays. Claude Code 2.1.288 sends
#: one of clear, resume, logout, prompt_input_exit, other; the last three end
#: the process and revoke.
SESSION_END_KEEPS_CREDENTIAL = frozenset({"clear", "resume"})


def run_session_end(
    payload: Mapping[str, Any], *, hub_url: str | None = None, agent: str = "claude",
) -> bool:
    session_id = str(payload.get("session_id") or "").strip()
    if not session_id:
        return False
    inherited = bool(str(os.environ.get("HOLDSPEAK_AGENT_CREDENTIAL") or "").strip())
    if inherited and str(payload.get("reason") or "").strip().lower() in SESSION_END_KEEPS_CREDENTIAL:
        # Conductor K6: a /clear or /resume must not cut the agent off its MCP.
        return False
    # Conductor R2: a credential the hub minted for this one session
    # (``claude:<session_id>``) ends with the session on every reason: after
    # /clear or /resume the next session mints its own.
    base = (hub_url or os.environ.get("HOLDSPEAK_HUB_URL") or DEFAULT_HUB_URL).rstrip("/")
    return revoke_agent_credential(session_id, base, agent=agent)


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
    agent: str = "claude",
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
    parent_operation_id = str(
        os.environ.get("HOLDSPEAK_PARENT_OPERATION_ID") or ""
    ).strip()

    # The inert fast path: not armed for this (cwd, tool) — no
    # proposal, no audit, no hub contact. Conductor K5: an agent HoldSpeak
    # launched under the gate (its spawn sets the parent operation) is held
    # for the gate's tools wherever its working folder is, so a working
    # folder outside its worktree cannot make a call inert.
    from .tool_gate_rules import EDIT_TOOLS

    # Conductor R1: a launch's file writes are read against the worktree its
    # Bash is held for (the per-launch settings put them on the gate).
    root = gate_match_root(cfg, cwd=cwd, tool="Bash" if tool in EDIT_TOOLS else tool)
    if root is None and not (parent_operation_id and (tool in DEFAULT_TOOLS or tool in EDIT_TOOLS)):
        return HookDecision(deny=None)

    session_id = str(payload.get("session_id") or "").strip() or "unknown-session"
    proposal_id = str(payload.get("tool_use_id") or "").strip() or f"gate-{uuid.uuid4()}"
    redacted = redact_call(payload.get("tool_input"))
    args_sha256, args_head, args_len = redacted.sha256, redacted.head, redacted.length
    # Conductor K5: the call is read HERE, against the held worktree, so the
    # full command never leaves the agent process; the hub gets the verdict
    # and applies the Control mode (``tool_gate_rules``).
    verdict = _classify(tool, payload, cwd=cwd, root=root)
    # Bound to this call: the hub takes the verdict only for this proposal
    # id and this args hash (a verdict copied from another call is unparsed).
    verdict["proposal_id"] = proposal_id
    verdict["args_sha256"] = args_sha256

    base = (hub_url or os.environ.get("HOLDSPEAK_HUB_URL") or DEFAULT_HUB_URL).rstrip("/")
    if http_post is None or http_get is None:
        try:
            credential = str(
                agent_credential or issue_agent_credential(session_id, base, agent=agent)
            )
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
        "args_len": args_len,
        "cwd": cwd,
        "ttl_seconds": ttl_seconds,
        "classification": verdict,
    }
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

    # Conductor R2: a hub restart mid-hold. While the hub is down the hook
    # keeps waiting, for at most HUB_RESTART_GRACE_SECONDS in a row (then it
    # denies, as before: a dead hub never allows). The restart invalidates the
    # held proposal (HS-104-02: never resume a pre-restart hold), so the
    # hook proposes the same call again under a new id, and the new hold is
    # decided afresh by the Control mode or the owner. Fail-closed at the
    # deadline, as before.
    deadline = now() + ttl_seconds
    current_id = proposal_id
    reproposals = 0
    unreachable = False
    down_since: Optional[float] = None
    stopped = HookDecision(deny="gate armed but the hub stopped answering mid-hold; the call was not run")

    def _down() -> bool:
        """Note one failed contact; True when the grace is spent."""
        nonlocal down_since, unreachable
        unreachable = True
        moment = now()
        down_since = moment if down_since is None else down_since
        return moment - down_since >= HUB_RESTART_GRACE_SECONDS

    while now() < deadline:
        sleep(POLL_INTERVAL_SECONDS)
        try:
            status, response = get(f"{base}/api/gate/proposals/{current_id}", 5.0)
        except Exception:
            if _down():
                return stopped
            continue
        if status >= 500 or status == 0:
            if _down():
                return stopped
            continue
        unreachable, down_since = False, None
        if status != 200:
            return HookDecision(
                deny=f"gate armed but the decision read failed (HTTP {status}); the call was not run"
            )
        state = str(response.get("state") or "")
        if state == "approved":
            return HookDecision(deny=None)
        if state == "invalidated" and _restart_invalidated(response) and reproposals < MAX_REPROPOSALS:
            reproposals += 1
            current_id = f"{proposal_id}~r{reproposals}"
            again = dict(body, id=current_id)
            again["classification"] = dict(verdict, proposal_id=current_id)
            while now() < deadline:
                try:
                    status, response = post(f"{base}/api/gate/proposals", again, 5.0)
                except Exception:
                    if _down():
                        return stopped
                    sleep(POLL_INTERVAL_SECONDS)
                    continue
                if status >= 500 or status == 0:
                    if _down():
                        return stopped
                    sleep(POLL_INTERVAL_SECONDS)
                    continue
                unreachable, down_since = False, None
                break
            else:
                break
            if status != 200:
                return HookDecision(
                    deny=f"gate armed but the hub refused the proposal (HTTP {status}); the call was not run"
                )
            state = str(response.get("state") or "")
            if state == "approved":
                return HookDecision(deny=None)
        if state in ("denied", "expired", "invalidated"):
            return HookDecision(deny=_deny_reason(response))
    if unreachable:
        return stopped
    return HookDecision(
        deny="gate hold expired with no decision; the call was not run"
    )


#: How long a held call waits for a hub that stopped answering (a restart)
#: before it denies.
HUB_RESTART_GRACE_SECONDS = 20.0

#: How many times one call is proposed again after hub restarts.
MAX_REPROPOSALS = 3

#: The reason a startup invalidation writes (``GateService.invalidate_held_on_startup``).
RESTART_INVALIDATION_REASON = "hub restarted while the proposal was held"


def _restart_invalidated(response: Mapping[str, Any]) -> bool:
    return RESTART_INVALIDATION_REASON in str(response.get("reason") or "")


def _classify(
    tool: str, payload: Mapping[str, Any], *, cwd: str, root: Optional[str],
) -> dict[str, str]:
    """The Conductor K5 verdict on one call; a reading error is ``unparsed``
    (the call waits), never an allow."""
    from .tool_gate_rules import classify_tool_call

    try:
        raw = payload.get("tool_input")
        verdict = classify_tool_call(
            tool, raw if isinstance(raw, Mapping) else None, cwd=cwd, root=root
        ).to_dict()
    except Exception:
        verdict = {"scope": "unparsed", "rule": "read_failed", "read_rule": "", "push_branch": ""}
    verdict["root"] = root or ""
    return verdict


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
    agent: str = "claude",
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
    if not held_repo:  # gate_matches already applies the switch and armed paths
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
            credential = issue_agent_credential(session_id, base, agent=agent)
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
    agent: str = "claude",
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
        credential = issue_agent_credential(session_id, base, agent=agent)
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


def _hook_settings(command: str) -> dict[str, Any]:
    """The complete gate lifecycle for one Claude Code settings source."""
    return {
        "hooks": {
            "SessionStart": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": command,
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
                            "command": command,
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
                            "command": command,
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
                            "command": command,
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
                            "command": command,
                            "timeout": 15,
                        }
                    ]
                }
            ],
        }
    }


def write_spawn_settings(
    path: Path | None = None, *, project_root: Path | None = None
) -> Path:
    """Write HoldSpeak-owned settings for a supervised ``process.spawn``.

    Unlike :func:`install_block`, this never edits Claude Code's user config.
    The launched process receives this file explicitly with ``--settings``.
    ``uv --project`` pins every lifecycle hook to the same HoldSpeak checkout
    that launched the agent, rather than whichever ``holdspeak`` is on PATH.
    """
    import shlex

    root = (project_root or Path(__file__).resolve().parents[1]).resolve()
    root_key = hashlib.sha256(str(root).encode("utf-8")).hexdigest()[:16]
    target = path or Path.home() / ".holdspeak" / "gate-spawn-settings" / f"{root_key}.json"
    prefix = f"uv run --project {shlex.quote(str(root))} holdspeak"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(spawn_settings(prefix), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


def spawn_settings(prefix: str) -> dict[str, Any]:
    """The gate hooks plus the rider hooks, in one settings document.

    The rider hooks (``agent-hook ingest --agent claude``) report the
    session, its Story claim and its state to the hub, so a launched agent
    registers with no manual ``holdspeak agent-hook install``. The gate
    hooks stay inert unless the gate holds the worktree. ``prefix`` is the
    command that runs this HoldSpeak checkout (``uv run --project ...
    holdspeak``)."""
    import copy

    from .agent_context.hooks import claude_hook_template

    merged = _hook_settings(f"{prefix} gate hook")
    # Conductor R1: in a launch, Claude's file writes go through the gate too:
    # ``acceptEdits`` (Normal and YOLO) also accepts edits in Claude's other
    # allowed folders; the gate passes writes inside the launch's worktree
    # and holds the rest in every mode.
    from .tool_gate_rules import EDIT_TOOLS

    merged["hooks"]["PreToolUse"].append({
        "matcher": "|".join(sorted(EDIT_TOOLS)),
        "hooks": [{"type": "command", "command": f"{prefix} gate hook", "timeout": HOOK_TIMEOUT_SECONDS}],
    })
    rider = copy.deepcopy(claude_hook_template())
    rider_command = f"{prefix} agent-hook ingest --agent claude"
    for event, entries in (rider.get("hooks") or {}).items():
        for entry in entries:
            for hook in entry.get("hooks") or []:
                hook["command"] = rider_command
        merged["hooks"].setdefault(event, []).extend(entries)
    return merged


def spawn_prefix(project_root: Path | None = None) -> str:
    """The command that runs this HoldSpeak checkout from a hook."""
    import shlex

    root = (project_root or Path(__file__).resolve().parents[1]).resolve()
    return f"uv run --project {shlex.quote(str(root))} holdspeak"


def codex_spawn_hooks(prefix: str) -> dict[str, Any]:
    """The hooks of one Codex launch: the gate (``gate hook --agent codex``,
    PreToolUse held up to 300 s) and the rider (``agent-hook ingest --agent
    codex``), both run by ``prefix`` (this HoldSpeak checkout)."""
    import copy

    from .agent_context.hooks import codex_hook_template

    template = copy.deepcopy(
        codex_hook_template(gate_command=f"{prefix} gate hook --agent codex")
    )
    rider_command = f"{prefix} agent-hook ingest --agent codex"
    for entries in template["hooks"].values():
        for entry in entries:
            for hook in entry.get("hooks") or []:
                if GATE_HOOK_MARKER not in hook["command"]:
                    hook["command"] = rider_command
    return template


#: Marker of a gate hook command (``... gate hook --agent codex``).
GATE_HOOK_MARKER = " gate hook"


def _toml_value(value: Any) -> str:
    """One TOML inline value (tables, arrays, strings, integers): what
    ``codex -c key=<value>`` parses. JSON string escapes are valid TOML."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, Mapping):
        return "{" + ",".join(f"{key}={_toml_value(item)}" for key, item in value.items()) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_toml_value(item) for item in value) + "]"
    raise TypeError(f"no TOML form for {type(value).__name__}")


def codex_hook_flags(prefix: str) -> list[str]:
    """``-c hooks.<Event>=[...]`` for each event of :func:`codex_spawn_hooks`.

    Codex runs a session-flag hook only when the user config trusts its hash
    (``hooks.state."/<session-flags>/config.toml:<event>:<group>:<handler>"
    .trusted_hash``): the owner-only ``agent_hooks.install`` writes that trust
    (``agent_context.codex_trust``) and every Codex launch checks it first."""
    flags: list[str] = []
    for event, entries in codex_spawn_hooks(prefix)["hooks"].items():
        flags += ["-c", f"hooks.{event}={_toml_value(entries)}"]
    return flags


def codex_spawn_args(prefix: str | None = None) -> list[str]:
    """The Codex arguments of every launch: its own process (``--no-daemon``)
    and its hooks.

    ``--no-daemon``: an interactive Codex 0.159 otherwise joins the shared
    app-server daemon of ``CODEX_HOME``, and its hooks then run in the
    daemon's environment, without this launch's story claim, parent operation,
    credential or tmux pane."""
    return ["--no-daemon", *codex_hook_flags(prefix or spawn_prefix())]


def install_block(executable: str = "holdspeak") -> str:
    """The hook block the USER adds to ``~/.claude/settings.json``.
    Printed, never written: this module does not edit another app's
    config."""
    return json.dumps(_hook_settings(f"{executable} gate hook"), indent=2)
