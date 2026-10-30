"""Agent Profiles, the git-worktree-create op, and Story-bound agent
launch (HS-94-07).

PLATFORM-CONTRACT §9: agent launch is a typed operation, never
arbitrary shell text. A client names ``agent_profile_id`` + ``source_id``
+ ``worktree{mode,...}`` + ``story_ref`` (+ ``session_label``) and NOTHING
else — profiles are node-configured argv templates with FIXED
executables (an allow-list of known launchers) and allow-listed option
slots; a client-supplied executable, argv, command, shell, or worktree
path refuses BY NAME before anything executes.

Launching into a new worktree is a DISTINCT typed operation
(``worktree.create``) riding the HS-94-06 command envelope with its own
receipt: if the subsequent launch fails, the worktree-create receipt
records what exists (the worktree is retained and named — never a
silent rollback delete). Its guards — injection in names, out-of-root
paths, duplicate worktrees, dirty-worktree reuse — all refuse
pre-execution, typed.

Launch success creates, in one logical transaction: the tmux session
(via the ``factory.spawn`` envelope, so it carries a node receipt), the
IMMUTABLE terminal target, ONE Work attempt (``kind='launch'``,
``exact=true``, session unbound), and the launch record. The rider
binds the real session identity when its hooks report the Story claim
(HS-94-04's rider path — the SAME attempt gains its ``session_id``, no
duplicate row is ever created). A launch whose rider never registers
moves ``starting`` → ``unknown`` with reason ``failed_to_register`` —
the terminal stays openable and nothing is silently orphaned.

Discovery lists panes/sessions with node + source/worktree + profile +
the immutable target — a client never needs a pre-known ``pane:%N``.
Every wire projection here is path-free (§13).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from ..redaction import redact_error
from .. import coder_factory, coder_steering
from ..coder_steering import Runner
from ..logging_config import get_logger
from .attempts import resolver_from_registry

log = get_logger("delivery.factory_launch")

AGENT_PROFILES_SCHEMA = 1
LAUNCHES_SCHEMA = 1
DISCOVER_SCHEMA = 1
DEFAULT_PROFILES_PATH = Path.home() / ".holdspeak" / "agent_profiles.json"
DEFAULT_LAUNCHES_PATH = Path.home() / ".holdspeak" / "agent_launches.json"

#: The FIXED launcher allow-list (§9): a profile's executable must be
#: one of these bare names — never a path, never a shell.
KNOWN_EXECUTABLES = ("claude", "codex", "pi")


def agent_of_profile(profile_id: Any) -> str:
    """The agent a launch profile runs, by its id: ``codex``, ``pi`` or
    ``claude`` (the default). The one mapping the lane, the flights, the
    Brief and the Hand read."""
    text = str(profile_id or "").strip().lower()
    if text.startswith("codex"):
        return "codex"
    if text.startswith("pi-") or text == "pi":
        return "pi"
    return "claude"

#: A rider that never registers within this window is honestly
#: ``unknown`` / ``failed_to_register`` — never a fake success.
DEFAULT_REGISTER_TIMEOUT_SECONDS = 120

#: How many launch records the ledger retains (newest kept).
LAUNCH_LEDGER_MAX_ROWS = 200

GIT_TIMEOUT_SECONDS = 60

# One argv token: no whitespace, no shell metacharacter, ever. Every
# profile arg and option value is held to this at definition AND use.
_SAFE_TOKEN_RE = re.compile(r"^[A-Za-z0-9@%+=:,./_-]+$")
# Opaque refs a client may send (profile ids, projects, story ids).
_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
# A branch name: strict allow-list, no traversal, its own argv slot.
_BRANCH_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9._/-]{0,99}$")
_FLAG_RE = re.compile(r"^--[A-Za-z0-9][A-Za-z0-9-]{0,63}$")


def _replace_option(argv: list[str], flag: str, value: str) -> list[str]:
    """Replace a profile option without allowing a reviewer override."""
    out: list[str] = []
    index = 0
    while index < len(argv):
        token = str(argv[index])
        if token == flag:
            index += 2
            continue
        if token.startswith(flag + "="):
            index += 1
            continue
        out.append(argv[index])
        index += 1
    return [*out, flag, value]


def _remove_variadic_option(argv: list[str], flag: str) -> list[str]:
    """Remove one CLI option whose value consumes tokens until the next flag."""
    out: list[str] = []
    index = 0
    while index < len(argv):
        token = str(argv[index])
        if token == flag:
            index += 1
            while index < len(argv) and not str(argv[index]).startswith("--"):
                index += 1
            continue
        if token.startswith(flag + "="):
            index += 1
            continue
        out.append(argv[index])
        index += 1
    return out


def _replace_tools_option(argv: list[str], value: str) -> list[str]:
    """Replace Claude's variadic ``--tools`` option with one safe list."""
    out = _remove_variadic_option(argv, "--tools")
    return [*out, "--tools", value]


def _claude_read_only_argv(argv: list[str]) -> list[str]:
    """Remove Claude permission escapes before adding its read-only tools."""
    out = _replace_option(argv, "--permission-mode", "plan")
    out = _remove_variadic_option(out, "--allowedTools")
    out = [
        token for token in out
        if str(token) not in {"--dangerously-skip-permissions", "--allow-dangerously-skip-permissions"}
    ]
    return _replace_tools_option(out, "Read,Grep,Glob")


def _codex_read_only_argv(argv: list[str]) -> list[str]:
    """Remove profile escape hatches before adding Codex's read-only sandbox."""
    out: list[str] = []
    index = 0
    boolean_flags = {
        "--yolo", "--full-auto", "--approve-for-me",
        "--dangerously-bypass-approvals-and-sandbox", "--no-sandbox",
    }
    pair_flags = {
        "--sandbox", "-s", "--ask-for-approval", "-a", "--add-dir",
    }
    while index < len(argv):
        token = str(argv[index])
        lower = token.lower()
        if lower in boolean_flags:
            index += 1
            continue
        if lower.startswith(("--sandbox=", "--ask-for-approval=")):
            index += 1
            continue
        if lower in pair_flags:
            index += 2
            continue
        if lower in {"--config", "-c"} and index + 1 < len(argv):
            config_value = str(argv[index + 1]).lower()
            if config_value.startswith("sandbox_mode=") or config_value.startswith("sandbox_permissions="):
                index += 2
                continue
        if lower.startswith(("--config=sandbox_mode=", "--config=sandbox_permissions=")):
            index += 1
            continue
        out.append(argv[index])
        index += 1
    return _replace_option(out, "--sandbox", "read-only")

#: The desk objects a launch may name as its origin (Hand to agent): the
#: item the agent works on. Optional; carried on the launch record and the
#: Work attempt so a later merge can close the item it came from.
ORIGIN_KINDS = (
    "action",
    "decision",
    "decision_record",
    "project_item",
    "note",
    "meeting",
    "artifact",
    "issue",  # Conductor R4: a Room issue, ``<watch_id>.<entity_id>``
    "program_step",  # Programs (2026-10-28): one step of a Program
)
_ORIGIN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")

#: Request fields a browser/native client must NEVER supply — each
#: refuses by its own name (§9: no executable, argv, or shell string).
_CLIENT_FORBIDDEN_FIELDS = ("executable", "argv", "command", "shell", "args", "env")

_DEFAULT_PROFILES: list[dict[str, Any]] = [
    {
        "profile_id": "claude-default",
        "label": "Claude Code",
        "executable": "claude",
        "args": [],
        "option_slots": {
            "permission_mode": {
                "flag": "--permission-mode",
                "choices": ["plan", "acceptEdits"],
            },
            "model": {"flag": "--model", "choices": ["sonnet", "opus", "haiku"]},
        },
    },
    {
        "profile_id": "codex-default",
        "label": "Codex CLI",
        "executable": "codex",
        "args": [],
        "option_slots": {
            "sandbox": {
                "flag": "--sandbox",
                "choices": ["read-only", "workspace-write"],
            },
        },
    },
    {
        # pi (pi spike #1020): its model is the hub's engine for coding work
        # (``pi_launch.coding_engine``), so it has no model slot.
        "profile_id": "pi-default",
        "label": "pi",
        "executable": "pi",
        "args": [],
        "option_slots": {},
    },
]


#: Seeded profiles added after the profile file existed: a file written
#: before them gets them at load (``AgentProfileStore``, ``LaunchReads``).
LATER_DEFAULT_PROFILES = ("pi-default",)


def later_default_profile(profile_id: str) -> Optional[dict[str, Any]]:
    """The seeded profile ``profile_id`` when it is a later default."""
    if profile_id not in LATER_DEFAULT_PROFILES:
        return None
    entry = next((e for e in _DEFAULT_PROFILES if e["profile_id"] == profile_id), None)
    return _valid_profile(entry) if entry is not None else None


class LaunchRefused(ValueError):
    """A typed launch refusal: ``reason`` is machine-readable and the
    message never echoes a filesystem path, an argv, or a secret."""

    def __init__(
        self, reason: str, message: Optional[str] = None, *,
        context: Optional[Mapping[str, Any]] = None,
    ) -> None:
        super().__init__(message or reason)
        self.reason = reason
        #: Machine-readable detail that rides the refusal (path-free).
        self.context = dict(context or {})


def _iso_now(now: Optional[datetime] = None) -> str:
    moment = now or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_ts(text: Any) -> Optional[datetime]:
    try:
        parsed = datetime.fromisoformat(str(text or "").replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def origin_ref_of(request: Mapping[str, Any]) -> Optional[dict[str, str]]:
    """The optional ``origin_ref`` of a launch request, validated.

    Absent is ``None``. Present, it must be ``{kind, id}`` with a known
    kind and an opaque id, else it refuses ``origin_ref_invalid``."""
    raw = request.get("origin_ref")
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise LaunchRefused("origin_ref_invalid", "origin_ref must be an object")
    kind = str(raw.get("kind") or "")
    item_id = str(raw.get("id") or "")
    if kind not in ORIGIN_KINDS or not _ORIGIN_ID_RE.match(item_id):
        raise LaunchRefused("origin_ref_invalid", "origin_ref carries invalid tokens")
    return {"kind": kind, "id": item_id}


def derived_story_ref(project: str, kind: str, item_id: str) -> dict[str, str]:
    """A story ref for work that has no dw story: ``<kind>-<id>`` under the
    item's Project. It must pass the same token rule as any story ref."""
    story_id = f"{kind}-{item_id}"
    project = str(project or "")
    if not _REF_RE.match(project) or not _REF_RE.match(story_id):
        raise LaunchRefused("story_ref_invalid", "the derived story ref is not a valid token")
    return {"project": project, "story_id": story_id}


def valid_branch(branch: str) -> bool:
    text = str(branch or "")
    return bool(_BRANCH_RE.match(text)) and ".." not in text and "//" not in text


def _default_git_runner(argv: list[str], cwd: Optional[str] = None):
    return subprocess.run(
        argv,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=GIT_TIMEOUT_SECONDS,
    )


def _scrub(detail: str, *roots: Any) -> str:
    """Client-safe error text: filesystem roots replaced, credentials
    redacted (PHILO-17 redact: git can echo a Basic header or a password in
    a remote URL), then bounded."""
    text = str(detail or "")
    for root in roots:
        if root:
            text = text.replace(str(root), "<root>")
    return redact_error(text, 300)


# ── Agent Profiles (§9: node-configured argv templates) ──────────────


def _valid_profile(entry: Any) -> Optional[dict[str, Any]]:
    """One stored profile, validated field by field. An invalid entry
    is dropped whole — a hand-edited file cannot smuggle a shell."""
    if not isinstance(entry, Mapping):
        return None
    profile_id = str(entry.get("profile_id") or "")
    label = str(entry.get("label") or profile_id)
    executable = str(entry.get("executable") or "")
    if not _REF_RE.match(profile_id):
        return None
    if executable not in KNOWN_EXECUTABLES:
        return None  # the executable is FIXED: a path or stranger refuses
    args_raw = entry.get("args")
    args: list[str] = []
    for token in args_raw if isinstance(args_raw, list) else []:
        if not isinstance(token, str) or not _SAFE_TOKEN_RE.match(token):
            return None
        args.append(token)
    slots_raw = entry.get("option_slots")
    slots: dict[str, dict[str, Any]] = {}
    for name, slot in (slots_raw or {}).items() if isinstance(slots_raw, Mapping) else []:
        if not isinstance(name, str) or not _REF_RE.match(name):
            return None
        if not isinstance(slot, Mapping):
            return None
        flag = str(slot.get("flag") or "")
        choices_raw = slot.get("choices")
        if not _FLAG_RE.match(flag) or not isinstance(choices_raw, list) or not choices_raw:
            return None
        choices: list[str] = []
        for choice in choices_raw:
            if not isinstance(choice, str) or not _SAFE_TOKEN_RE.match(choice):
                return None
            choices.append(choice)
        slots[name] = {"flag": flag, "choices": choices}
    return {
        "profile_id": profile_id,
        "label": label,
        "executable": executable,
        "args": args,
        "option_slots": slots,
    }


def _write_document(path: Path, document: Mapping[str, Any]) -> None:
    """Publish a whole document; concurrent readers keep the previous one."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


class AgentProfileStore:
    """Node-configured Agent Profiles at
    ``~/.holdspeak/agent_profiles.json`` (``agent_profiles_schema: 1``).

    Each profile is an argv TEMPLATE: a fixed executable from
    :data:`KNOWN_EXECUTABLES`, fixed safe-token args, and allow-listed
    option slots (flag + closed choice list). A client selects a
    ``profile_id`` and slot choices; it can never supply an executable,
    an argv token, or a shell fragment.
    """

    def __init__(self, path: Optional[Path] = None) -> None:
        self._path = Path(path) if path else DEFAULT_PROFILES_PATH
        self._profiles: dict[str, dict[str, Any]] = {}
        self._load_or_seed()

    def _load_or_seed(self) -> None:
        raw: Any = None
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raw = None
        if isinstance(raw, dict) and raw.get("agent_profiles_schema") == AGENT_PROFILES_SCHEMA:
            for entry in raw.get("profiles") or []:
                profile = _valid_profile(entry)
                if profile is not None:
                    self._profiles[profile["profile_id"]] = profile
            # A seeded default added later (pi-default, pi spike #1020) joins a
            # file written before it; a profile the file already names stays.
            added = False
            for entry in _DEFAULT_PROFILES:
                if entry["profile_id"] in LATER_DEFAULT_PROFILES and entry["profile_id"] not in self._profiles:
                    profile = _valid_profile(entry)
                    if profile is not None:
                        self._profiles[profile["profile_id"]] = profile
                        added = True
            if added:
                self._save()
            return
        for entry in _DEFAULT_PROFILES:
            profile = _valid_profile(entry)
            assert profile is not None
            self._profiles[profile["profile_id"]] = profile
        self._save()

    def _save(self) -> None:
        doc = {
            "agent_profiles_schema": AGENT_PROFILES_SCHEMA,
            "profiles": [self._profiles[k] for k in sorted(self._profiles)],
        }
        _write_document(self._path, doc)

    def get(self, profile_id: str) -> Optional[dict[str, Any]]:
        return self._profiles.get(str(profile_id or ""))

    def to_wire(self) -> dict[str, Any]:
        """Profiles as a client sees them: the template is node config
        (executable NAMES and option choices), never a path."""
        return {
            "agent_profiles_schema": AGENT_PROFILES_SCHEMA,
            "known_executables": list(KNOWN_EXECUTABLES),
            "profiles": [self._profiles[k] for k in sorted(self._profiles)],
        }

    def resolve_argv(
        self, profile_id: str, options: Any = None
    ) -> list[str]:
        """The launch argv from a profile + client slot choices.

        Refusals are typed: unknown profile, an option slot the profile
        does not declare, a value outside the slot's closed choices."""
        profile = self.get(profile_id)
        if profile is None:
            raise LaunchRefused("profile_unknown", f"unknown agent profile {profile_id!r}")
        argv = [profile["executable"], *profile["args"]]
        chosen = options if isinstance(options, Mapping) else {}
        for name, value in chosen.items():
            slot = profile["option_slots"].get(str(name))
            if slot is None:
                raise LaunchRefused(
                    "option_not_allowed",
                    f"option {name!r} is not a slot of profile {profile_id!r}",
                )
            if not isinstance(value, str) or value not in slot["choices"]:
                raise LaunchRefused(
                    "option_value_not_allowed",
                    f"option {name!r} only accepts its declared choices",
                )
            argv.extend([slot["flag"], value])
        return argv


def _resume_words(profile_id: Any, session_key: str) -> Optional[str]:
    """``claude --resume <id>`` for a bound session (shown, never run)."""
    _agent, _, session_id = str(session_key or "").partition(":")
    try:
        return " ".join(resume_argv(agent_of_profile(profile_id), [agent_of_profile(profile_id)], session_id))
    except LaunchRefused:
        return None


def resume_argv(executable: str, argv: list[str], session_id: str) -> list[str]:
    """The agent's own resume (Betterment AG6; herdr's resume table, checked
    against each CLI's ``--help`` on 2026-10-18): Claude Code
    ``claude [flags] --resume <id>``; Codex ``codex resume [flags] <id>`` (the
    subcommand takes the same flags); pi ``pi [flags] --session <id>`` (a
    session file or a partial id, looked up in the launch's ``--session-dir``)."""
    if not _SAFE_TOKEN_RE.match(str(session_id or "")):
        raise LaunchRefused("no_session_to_resume", "the session id is not a safe token")
    if executable == "claude":
        return [*argv, "--resume", session_id]
    if executable == "codex":
        return [argv[0], "resume", *argv[1:], session_id]
    if executable == "pi":
        return [*argv, "--session", session_id]
    raise LaunchRefused("resume_unsupported", f"{executable!r} has no resume")


# ── the worktree-create op (node-side executor) ──────────────────────


def derive_worktree_path(primary_path: str, name: str) -> Path:
    """The server-derived new-worktree path: a SIBLING of the source's
    primary worktree, named by the validated ``name``. The containment
    root is the primary's parent directory — nothing a client sends can
    widen it (the client cannot send a path at all)."""
    if not coder_factory.valid_name(name):
        raise LaunchRefused("worktree_name_invalid", f"invalid worktree name: {name!r}")
    root = Path(primary_path).expanduser().resolve().parent
    candidate = (root / name).resolve()
    if candidate.parent != root or candidate.name != name:
        raise LaunchRefused(
            "worktree_out_of_root", "the derived worktree path escapes the source root"
        )
    return candidate


def execute_worktree_create(
    payload: Mapping[str, Any],
    *,
    runner: Optional[Runner] = None,
    audit: Optional[Callable[..., int]] = None,
) -> dict[str, Any]:
    """The ``worktree.create`` executor the command envelope dispatches
    to (its dispatch branch in :mod:`.commands` is HS-94-07's one
    additive hook). Statuses: ``worktree_created``, ``bad_name``,
    ``branch_invalid``, ``out_of_root``, ``worktree_duplicate``,
    ``error``. Guards re-prove here even though the hub pre-checked —
    the node never trusts the wire. Audited like every factory act."""
    record = audit or coder_steering._default_audit
    name = str(payload.get("name") or "")
    branch = str(payload.get("branch") or "")
    repo_path = str(payload.get("repo_path") or "")
    path = str(payload.get("path") or "")

    def _audited(result: dict[str, Any]) -> dict[str, Any]:
        try:
            result["audit_id"] = record(
                session_key=f"factory:worktree:{name}", agent="factory", pane_id=None,
                text=f"worktree {name} -b {branch}", grounding=[], submit=False,
                outcome=result["status"], detail=result.get("detail"),
            )
        except Exception:
            result["audit_id"] = None
        return result

    if not coder_factory.valid_name(name):
        return _audited({"status": "bad_name", "detail": f"invalid worktree name: {name!r}"})
    if not valid_branch(branch):
        return _audited({"status": "branch_invalid", "detail": f"invalid branch: {branch!r}"})
    if not repo_path or not path:
        return _audited({"status": "error", "detail": "repo_path and path are required"})
    repo = Path(repo_path).expanduser()
    candidate = Path(path).expanduser()
    try:
        resolved = candidate.resolve()
        root = repo.resolve().parent
    except OSError as exc:
        return _audited({"status": "error", "detail": _scrub(str(exc), repo_path, path)})
    if resolved.parent != root or resolved.name != name:
        return _audited(
            {"status": "out_of_root", "detail": "worktree path escapes the source root"}
        )
    if resolved.exists():
        return _audited(
            {"status": "worktree_duplicate", "detail": f"worktree {name!r} already exists"}
        )
    run = runner or _default_git_runner
    argv = ["git", "-C", str(repo), "worktree", "add", str(resolved), "-b", branch]
    # Betterment AG11: a helper's worktree starts at its parent's branch.
    start_point = str(payload.get("start_point") or "")
    if start_point:
        if not valid_branch(start_point):
            return _audited({"status": "branch_invalid", "detail": f"invalid start point: {start_point!r}"})
        argv.append(start_point)
    try:
        completed = run(argv)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return _audited({"status": "error", "detail": _scrub(str(exc), repo_path, path)})
    if completed.returncode != 0:
        detail = _scrub((completed.stderr or "").strip() or "git refused", repo_path, path)
        status = "worktree_duplicate" if "already exists" in detail.lower() else "error"
        return _audited({"status": status, "detail": detail})
    return _audited({"status": "worktree_created", "name": name, "branch": branch})


def execute_worktree_remove(
    payload: Mapping[str, Any],
    *,
    runner: Optional[Runner] = None,
    audit: Optional[Callable[..., int]] = None,
) -> dict[str, Any]:
    """The ``factory.worktree_remove`` executor (Conductor K4): remove a
    launch's worktree after its PR merged. It removes a CLEAN, MERGED
    worktree only, and refuses everything else by name before git runs:

    ``worktree_removed``, ``bad_name``, ``out_of_root``, ``worktree_absent``,
    ``worktree_dirty`` (uncommitted or untracked changes),
    ``worktree_unmerged`` (HEAD is not the merged head or an ancestor of
    it: a commit made after the merge stays), ``error``.

    ``merged_head`` is the head SHA the forge reports merged. The branch is
    kept (only the checkout goes). Audited like every factory act."""
    record = audit or coder_steering._default_audit
    name = str(payload.get("name") or "")
    repo_path = str(payload.get("repo_path") or "")
    path = str(payload.get("path") or "")
    merged_head = str(payload.get("merged_head") or "").strip()

    def _audited(result: dict[str, Any]) -> dict[str, Any]:
        try:
            result["audit_id"] = record(
                session_key=f"factory:worktree:{name}", agent="factory", pane_id=None,
                text=f"worktree remove {name}", grounding=[], submit=False,
                outcome=result["status"], detail=result.get("detail"),
            )
        except Exception:
            result["audit_id"] = None
        return result

    if not coder_factory.valid_name(name):
        return _audited({"status": "bad_name", "detail": f"invalid worktree name: {name!r}"})
    if not repo_path or not path:
        return _audited({"status": "error", "detail": "repo_path and path are required"})
    try:
        resolved = Path(path).expanduser().resolve()
        root = Path(repo_path).expanduser().resolve().parent
    except OSError as exc:
        return _audited({"status": "error", "detail": _scrub(str(exc), repo_path, path)})
    if resolved.parent != root or resolved.name != name:
        return _audited({"status": "out_of_root", "detail": "worktree path escapes the source root"})
    if not resolved.exists():
        return _audited({"status": "worktree_absent", "detail": f"worktree {name!r} is not there"})
    run = runner or _default_git_runner

    def git(*args: str) -> Any:
        return run(["git", "-C", str(resolved), *args])

    try:
        status = git("status", "--porcelain")
        if status.returncode != 0:
            return _audited({"status": "error", "detail": "git status failed"})
        if (status.stdout or "").strip():
            return _audited({"status": "worktree_dirty", "detail": f"worktree {name!r} has changes"})
        if not merged_head or not _SAFE_TOKEN_RE.match(merged_head):
            return _audited({"status": "worktree_unmerged", "detail": "no merged head to compare"})
        ancestor = git("merge-base", "--is-ancestor", "HEAD", merged_head)
        if ancestor.returncode != 0:
            return _audited(
                {"status": "worktree_unmerged", "detail": f"worktree {name!r} has commits the merge does not hold"}
            )
        removed = run(["git", "-C", str(Path(repo_path).expanduser()), "worktree", "remove", str(resolved)])
    except (OSError, subprocess.TimeoutExpired) as exc:
        return _audited({"status": "error", "detail": _scrub(str(exc), repo_path, path)})
    if removed.returncode != 0:
        detail = _scrub((removed.stderr or "").strip() or "git refused", repo_path, path)
        return _audited({"status": "error", "detail": detail})
    return _audited({"status": "worktree_removed", "name": name})


# ── the launch ledger (durable launch records) ───────────────────────


class LaunchLedgerNotRead(RuntimeError):
    """The launch file exists and could not be read (its reason)."""


class LaunchLedger:
    """Launch records at ``~/.holdspeak/agent_launches.json``
    (``launches_schema: 1``, newest :data:`LAUNCH_LEDGER_MAX_ROWS`
    kept). Records are path-free by construction — every field is an
    opaque ID, a label, or a receipt reference."""

    #: One lock per ledger file, shared by every instance in the process:
    #: the rider binding, the first-message waiter, the session watcher and
    #: a restart stop each read-modify-write the same file from their own
    #: thread. Without it a reader's reload replaced ``_records`` under a
    #: writer, and the writer saved the stale list (a lost "registered").
    _LOCKS: dict[str, threading.RLock] = {}
    _LOCKS_GUARD = threading.Lock()

    def __init__(self, path: Optional[Path] = None) -> None:
        self._path = Path(path) if path else DEFAULT_LAUNCHES_PATH
        with LaunchLedger._LOCKS_GUARD:
            self._lock = LaunchLedger._LOCKS.setdefault(
                str(self._path.expanduser().absolute()), threading.RLock()
            )
        self._records: list[dict[str, Any]] = []
        #: PHILO-15 lane 19 (Astra r1): why the last read of a file that
        #: EXISTS could not be used; None when it was read (or is absent).
        self.not_read: Optional[str] = None
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            # Astra r2 (2): a removed file holds no launches; the cache goes.
            self.not_read = None
            self._records = []
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except OSError as exc:
            self.not_read = f"the launch file cannot be read ({exc.strerror or type(exc).__name__})"
            return
        except ValueError:
            self.not_read = "the launch file is not valid JSON"
            return
        rows = raw.get("launches") if isinstance(raw, dict) else None
        if not (isinstance(raw, dict) and raw.get("launches_schema") == LAUNCHES_SCHEMA
                and isinstance(rows, list)):
            self.not_read = "the launch file has an unknown format"
            return
        self.not_read = None
        self._records = [dict(row) for row in rows if isinstance(row, dict)]

    def read_all(self) -> list[dict[str, Any]]:
        """Every launch record, read now; a file that exists and cannot be
        read raises :class:`LaunchLedgerNotRead` (never an empty list)."""
        with self._lock:
            self._load()
            if self.not_read:
                raise LaunchLedgerNotRead(self.not_read)
            return [dict(row) for row in self._records]

    def _park_unread(self) -> None:
        """Astra r2 (1), the never-delete law: before a save replaces a file
        that could not be read, its exact bytes are parked beside it as
        ``<name>.not-read-<stamp>``. A park that fails stops the save."""
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        parked = self._path.with_name(f"{self._path.name}.not-read-{stamp}")
        try:
            original = self._path.read_bytes()
            with open(parked, "xb") as handle:
                handle.write(original)
        except OSError as exc:
            raise LaunchLedgerNotRead(
                f"{self.not_read}; it was not replaced: the copy could not be parked "
                f"({exc.strerror or type(exc).__name__})"
            ) from exc
        log.warning("launch ledger: %s; parked the original at %s", self.not_read, parked.name)
        self.not_read = None

    def _save(self) -> None:
        if self.not_read and self._path.exists():
            self._park_unread()
        doc = {
            "launches_schema": LAUNCHES_SCHEMA,
            "launches": self._records[-LAUNCH_LEDGER_MAX_ROWS:],
        }
        _write_document(self._path, doc)

    def record(self, launch: dict[str, Any]) -> None:
        with self._lock:
            # The kernel codec and the launch executor may hold separate ledger
            # instances over the same durable file. Reload before each mutation and
            # upsert by launch id so admission becomes execution without a twin row.
            self._load()
            launch_id = str(launch.get("launch_id") or "")
            self._records = [row for row in self._records if row.get("launch_id") != launch_id]
            self._records.append(dict(launch))
            self._records = self._records[-LAUNCH_LEDGER_MAX_ROWS:]
            self._save()

    def update(self, launch_id: str, **fields: Any) -> Optional[dict[str, Any]]:
        with self._lock:
            self._load()
            for row in self._records:
                if row.get("launch_id") == launch_id:
                    row.update(fields)
                    self._save()
                    return dict(row)
            return None

    def get(self, launch_id: str) -> Optional[dict[str, Any]]:
        with self._lock:
            self._load()
            for row in self._records:
                if row.get("launch_id") == launch_id:
                    return dict(row)
            return None

    def by_session(self, session: str) -> Optional[dict[str, Any]]:
        with self._lock:
            for row in reversed(self._records):
                if row.get("session") == str(session or ""):
                    return dict(row)
            return None

    def by_attempt(self, attempt_id: str) -> Optional[dict[str, Any]]:
        with self._lock:
            for row in reversed(self._records):
                if row.get("attempt_id") == str(attempt_id or ""):
                    return dict(row)
            return None

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            self._load()
            return [dict(row) for row in self._records]


# ── the launch service (hub-side agent.launch executor) ──────────────


class LaunchService:
    """Story-bound agent launch + remote discovery over the existing
    seams: profiles (this module), the Delivery Source registry, the
    immutable target registry, the HS-94-06 command envelope, and the
    HS-94-04 Work-attempt repository."""

    def __init__(
        self,
        *,
        profiles: AgentProfileStore,
        registry: Any,
        targets: Any,
        commands: Any,
        attempts: Any,
        ledger: Optional[LaunchLedger] = None,
        runner: Optional[Runner] = None,
        git_runner: Optional[Callable[..., Any]] = None,
        local_node_id: str = "local",
        wall_now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        which: Optional[Callable[[str], Optional[str]]] = None,
        control_mode: Optional[Callable[[], str]] = None,
        mcp_config_dir: Optional[Path] = None,
        codex_trust: Optional[Callable[[list[str]], list[str]]] = None,
        pi_engine: Optional[Callable[[], Any]] = None,
        db: Any = None,
    ) -> None:
        self._profiles = profiles
        # Programs PG13b: the database a launch's Program is read from (its
        # control level picks the launch flags); None: the hub's own.
        self._db = db
        # pi (pi spike #1020): the hub's engine for coding work, resolved at
        # launch (``pi_launch.coding_engine``); None: no engine is known.
        self._pi_engine = pi_engine
        # Conductor K6: the Control mode read at launch decides whether the
        # agent's ``holdspeak`` MCP tools are pre-approved in its pane.
        from . import agent_mcp

        self._control_mode = control_mode or agent_mcp.config_control_mode
        self._mcp_config_dir = mcp_config_dir
        # The executable preflight. Production asks the real PATH; a test
        # that injects a tmux runner has no real binaries, so the preflight
        # runs there only when the test passes its own ``which``.
        self._which = which if which is not None else (
            shutil.which if runner is None else None
        )
        # Conductor R3: Codex runs a launch's hooks only when its config trusts
        # them. Production asks Codex (``codex app-server``); a test with an
        # injected runner checks only when it passes its own reader.
        if codex_trust is None and self._which is not None and runner is None:
            from ..agent_context.codex_trust import untrusted_launch_hooks

            codex_trust = untrusted_launch_hooks
        self._codex_trust = codex_trust
        self._registry = registry
        self._targets = targets
        self._commands = commands
        self._attempts = attempts
        self._ledger = ledger or LaunchLedger()
        self._runner = runner
        self._git = git_runner or _default_git_runner
        self._local_node_id = str(local_node_id)
        self._wall_now = wall_now
        self._kernel: Any = None
        from .first_message import FirstMessage

        self._first = FirstMessage(self)
        self._reconciled = False

    def _launch_mode(self, request: Mapping[str, Any]) -> str:
        """The Control mode word one launch runs at (Programs PG13b): a
        Program step's launch at its Program's control, a helper at its
        parent's level, every other launch at the desk's Control mode. It
        picks Claude Code's permission mode and Codex's approvals and
        sandbox below."""
        from ..services.control_level import mode_for_request

        return mode_for_request(request, db=self._db, desk=self._control_mode)

    def bind_kernel(self, broker: Any) -> None:
        """Bind the existing launch driver to the kernel executor plane."""
        self._kernel = broker
        self._commands._kernel = broker
        if not self._reconciled:
            # A pending first message survives a restart: resume or name it.
            self._reconciled = True
            try:
                self._first.reconcile()
            except Exception:
                pass

    def launch_record(self, launch_id: str) -> Optional[dict[str, Any]]:
        return self._ledger.get(launch_id)

    def record_admitted(
        self, launch_id: str, request: Mapping[str, Any], *, operation_id: str,
    ) -> None:
        review = request.get("review") if isinstance(request.get("review"), Mapping) else {}
        role = "reviewer" if str(review.get("role") or "").strip().lower() == "reviewer" else "builder"
        if role == "reviewer" and review.get("read_only") is False:
            raise LaunchRefused("reviewer_read_only_required", "reviewer launches are always read-only")
        read_only = role == "reviewer"
        self._ledger.record(
            {
                "launch_schema": LAUNCHES_SCHEMA,
                "launch_id": launch_id,
                "state": "admitted",
                "operation_id": operation_id,
                "request": dict(request),
                # AG12: this is durable before the factory issues a credential
                # or creates a process. It is immutable launch posture.
                "role": role,
                "read_only": read_only,
                **({"review": dict(review)} if role == "reviewer" else {}),
                "commands": {"worktree_create": None, "spawn": None, "instruction": None},
            }
        )

    def record_decision(self, launch_id: str, decision: str, *, reason: str = "") -> None:
        self._ledger.update(
            launch_id,
            state="approved" if decision == "approve" else "rejected",
            decision=decision,
            decision_reason=str(reason or ""),
        )

    def validate_request(self, request: Any) -> None:
        """Run every launch hard prerequisite without performing an effect."""
        if not isinstance(request, Mapping):
            raise LaunchRefused("request_malformed", "a launch request must be an object")
        self._refuse_client_execution_fields(request)
        profile_id = str(request.get("agent_profile_id") or request.get("profile_id") or "")
        self._profiles.resolve_argv(profile_id, request.get("options"))
        origin_ref_of(request)
        self._preflight(self._profiles.get(profile_id) or {})
        _, story_id = self._story_ref(request)
        source_id = str(request.get("source_id") or "")
        source = self._registry.get(source_id)
        if source is None:
            raise LaunchRefused("source_unknown", f"unknown source {source_id!r}")
        self._resolve_worktree(request, source)
        self._session_name(request, story_id)

    def validate_process_spawn(self, request: Any) -> None:
        """A kernel-spawned agent must be brokered before it can launch.

        Manual ``agent.launch`` and ``coder_factory.spawn`` remain unchanged;
        this extra prerequisite belongs only to ``process.spawn``.  The
        supervised tool contract is the Bash hook of Claude Code or Codex, so
        any other profile or an unarmed destination refuses before a worktree, process,
        or launch record exists.
        """
        self.validate_request(request)
        assert isinstance(request, Mapping)
        profile_id = str(request.get("agent_profile_id") or request.get("profile_id") or "")
        profile = self._profiles.get(profile_id) or {}
        source = self._registry.get(str(request.get("source_id") or ""))
        assert source is not None
        _, worktree_path, _ = self._resolve_worktree(request, source)
        self._require_process_gate(profile, worktree_path)

    def _preflight(self, profile: Mapping[str, Any], engine_id: str = "") -> None:
        """Refuse before any envelope when the agent or tmux is not on
        this machine: ``executable_absent`` / ``tmux_absent``; a Codex whose
        config does not trust the launch hooks: ``codex_hooks_untrusted``; a
        pi with no OpenAI-compatible engine for coding work:
        ``no_assignment`` / ``no_compatible_assignment``."""
        which = self._which
        if which is None:
            self._require_codex_trust(profile)
            self._require_pi_engine(profile, engine_id)
            return
        if which("tmux") is None:
            raise LaunchRefused("tmux_absent", "tmux is not installed on this machine")
        executable = str(profile.get("executable") or "")
        if executable and which(executable) is None:
            raise LaunchRefused(
                "executable_absent", f"{executable} is not installed on this machine"
            )
        self._require_codex_trust(profile)
        self._require_pi_engine(profile, engine_id)

    def pi_engine(self, engine_id: str = "") -> Any:
        """The engine a pi launch runs on now, or the route's refusal.

        Programs (2026-10-28): ``engine_id`` names an engine profile of the
        model library (a step's Runs on); empty is the desk's ``agent.code``
        assignment."""
        if self._pi_engine is None:
            raise LaunchRefused("no_assignment", "pi has no engine for coding work")
        if engine_id:
            return self._pi_engine(engine_id)
        return self._pi_engine()

    def _require_pi_engine(self, profile: Mapping[str, Any], engine_id: str = "") -> None:
        if str(profile.get("executable") or "") == "pi":
            self.pi_engine(engine_id)

    def _require_codex_trust(self, profile: Mapping[str, Any]) -> None:
        """Refuse a Codex launch whose hooks Codex would not run (untrusted:
        no story claim, no gate, and a "Hooks need review" screen in the pane)."""
        if str(profile.get("executable") or "") != "codex" or self._codex_trust is None:
            return
        from .. import coder_gate
        from ..agent_context.codex_trust import CodexTrustError

        try:
            untrusted = self._codex_trust(coder_gate.codex_hook_flags(coder_gate.spawn_prefix()))
        except CodexTrustError as exc:
            raise LaunchRefused(
                "codex_hooks_unchecked", f"Codex did not say whether it trusts the hooks ({exc.reason})"
            ) from exc
        if untrusted:
            # Each entry names what keeps one launch hook from running
            # (missing:/disabled:/untrusted:<key>); a launch hook's key is a
            # session-flag position, never a path of the owner's.
            raise LaunchRefused(
                "codex_hooks_untrusted",
                "Codex will not run the HoldSpeak hooks. Press Install hooks on the Agents card.",
                context={"hooks": list(untrusted)},
            )

    @staticmethod
    def _require_process_gate(profile: Mapping[str, Any], worktree_path: str) -> None:
        from .. import coder_gate

        # Claude Code (``--settings``), Codex (``-c hooks.*``, R3) and pi (its
        # extension, pi spike #1020) carry the gate on their Bash calls.
        if str(profile.get("executable") or "") not in ("claude", "codex", "pi"):
            raise LaunchRefused("process_spawn_not_gated", "not gated")
        if not coder_gate.gate_matches(
            coder_gate.load_gate_config(), cwd=worktree_path, tool="Bash"
        ):
            raise LaunchRefused("process_spawn_not_gated", "not gated")

    def _codex_mode_args(
        self, argv: list[str], mode: Any, worktree_path: str, *, read_only: bool = False,
    ) -> list[str]:
        """Codex's approval and sandbox by the Control mode at launch (R3,
        coordinator ruling 2026-10-06).

        YOLO: no approval prompts (``-a never``); HoldSpeak's gate holds a
        Bash call outside the worktree, and Codex's ``workspace-write``
        sandbox keeps writes in the worktree plus the git folders a commit
        writes. Codex 0.159 keeps a writable root's git folder read-only (for
        a worktree, the ``.git/worktrees/<name>`` its ``.git`` file names) and
        a parent ``--add-dir`` does not lift it; the exact folders do
        (observed): the worktree's own git folder and, when shared, the
        repository's ``objects``, ``refs`` and ``logs``.
        Secure and Normal: Codex's own approvals (``on-request``); its
        prompts reach Needs you as TO APPROVE. A profile ``--sandbox`` choice
        is kept."""
        from . import agent_mcp

        if read_only:
            # Reviewer posture wins over the hub's Normal/YOLO setting. The
            # installed ``codex exec`` exposes the native read-only sandbox;
            # it has no ``--ask-for-approval`` option, so do not invent one.
            # The profile already carries ``--sandbox read-only``.
            return []
        if agent_mcp.normalized_mode(mode) != "yolo":
            return ["--ask-for-approval", "on-request"]
        args = ["--ask-for-approval", "never"]
        if "--sandbox" not in argv:
            args += ["--sandbox", "workspace-write"]
        # Ruling 2026-10-06: the sandbox has no network by default; YOLO lets
        # the agent `git push origin <launch branch>` and `gh pr create` (the
        # gate still holds URLs and other pushes, K5).
        args += ["-c", "sandbox_workspace_write.network_access=true"]
        git_dir = self._git_path(worktree_path, "--absolute-git-dir")
        common = self._git_path(worktree_path, "--git-common-dir")
        if git_dir:
            args += ["--add-dir", git_dir]
        if common and common != git_dir:
            for part in ("objects", "refs", "logs"):
                args += ["--add-dir", os.path.join(common, part)]
        return args

    def _git_path(self, worktree: str, flag: str) -> str:
        """One git folder of ``worktree`` (absolute, real), or ``""``."""
        try:
            completed = self._git(
                ["git", "-C", str(worktree), "rev-parse", "--path-format=absolute", flag]
            )
        except (OSError, subprocess.TimeoutExpired):
            return ""
        if completed.returncode != 0:
            return ""
        path = (completed.stdout or "").strip()
        return os.path.realpath(path) if path else ""

    # request validation ---------------------------------------------------

    def _refuse_client_execution_fields(self, request: Mapping[str, Any]) -> None:
        for field in _CLIENT_FORBIDDEN_FIELDS:
            if field in request:
                raise LaunchRefused(
                    f"{field}_not_client_settable",
                    f"a client can never supply {field!r} — select an agent "
                    "profile by id; the node owns the argv template",
                )

    @staticmethod
    def _story_ref(request: Mapping[str, Any]) -> tuple[str, str]:
        story = request.get("story_ref")
        if not isinstance(story, Mapping):
            raise LaunchRefused("story_ref_required", "story_ref must be an object")
        project = str(story.get("project") or "")
        story_id = str(story.get("story_id") or "")
        if not _REF_RE.match(project) or not _REF_RE.match(story_id):
            raise LaunchRefused("story_ref_invalid", "story_ref carries invalid tokens")
        return project, story_id

    def _session_name(self, request: Mapping[str, Any], story_id: str) -> str:
        label = str(request.get("session_label") or "")
        if label:
            if not coder_factory.valid_name(label):
                raise LaunchRefused(
                    "session_label_invalid", f"invalid session label: {label!r}"
                )
            return label
        # PHILO-14 A2b (Astra r1 on #945): tmux names hold 64 characters
        # (coder_factory.NAME_RE). A long story id (`decision_record-record-
        # <32 hex>`) is cut to a bounded prefix plus a digest of the WHOLE
        # id, so two ids that share the prefix never share a name; the full
        # id stays on the launch record (story_ref). 3+40+1+8+1+6 = 59.
        slug = re.sub(r"[^A-Za-z0-9_.-]", "-", story_id.lower())
        if len(slug) > 40:
            digest = hashlib.sha1(story_id.encode("utf-8")).hexdigest()[:8]
            slug = f"{slug[:40].rstrip('-.')}-{digest}"
        return f"hs-{slug}-{uuid.uuid4().hex[:6]}"

    def _worktree_dirty(self, path: str) -> bool:
        try:
            completed = self._git(["git", "-C", str(path), "status", "--porcelain"])
        except (OSError, subprocess.TimeoutExpired):
            return True  # unprovable cleanliness is treated as dirty
        if completed.returncode != 0:
            return True
        return bool((completed.stdout or "").strip())

    def _again_branch(self, request: Mapping[str, Any]) -> str:
        """Hand again keeps the earlier launch's branch (the tool gate lets
        the agent push that branch only)."""
        spec = request.get("worktree") or {}
        again = str(spec.get("again_of") or "") if isinstance(spec, Mapping) else ""
        return str((self._ledger.get(again) or {}).get("branch") or "") if again else ""

    def _resolve_worktree(
        self, request: Mapping[str, Any], source: Any
    ) -> tuple[str, str, Optional[dict[str, Any]]]:
        """(worktree_id, path, pending_create) — every guard here is
        pre-execution: nothing has run when a refusal raises."""
        spec = request.get("worktree")
        if not isinstance(spec, Mapping):
            raise LaunchRefused("worktree_required", "worktree must be an object")
        if "path" in spec:
            raise LaunchRefused(
                "worktree_path_not_client_settable",
                "a client selects worktrees by id or name; paths are server truth",
            )
        mode = str(spec.get("mode") or "")
        if mode == "existing":
            worktree_id = str(spec.get("worktree_id") or "")
            record = next(
                (wt for wt in source.worktrees if wt.worktree_id == worktree_id), None
            )
            if record is None:
                raise LaunchRefused("worktree_unknown", f"unknown worktree {worktree_id!r}")
            again = str(spec.get("again_of") or "")
            if again:
                # Betterment AG7 gaps, Hand again: the item's OWN worktree, made
                # by an earlier launch of the same item whose agent no longer
                # runs. Its uncommitted work is the work to continue.
                prior = self._ledger.get(again) or {}
                if (
                    prior.get("origin_ref") != request.get("origin_ref")
                    or str(prior.get("worktree_id") or "") != worktree_id
                    or str(prior.get("state") or "") in ("starting", "launched", "registered")
                ):
                    raise LaunchRefused(
                        "hand_again_refused",
                        "only the item's own worktree, after its agent stopped, takes Hand again",
                    )
                return record.worktree_id, record.path, None
            if self._worktree_dirty(record.path):
                raise LaunchRefused(
                    "worktree_dirty",
                    "the worktree has uncommitted changes — commit, stash, or "
                    "launch into a new worktree",
                )
            return record.worktree_id, record.path, None
        if mode == "new":
            primary = source.primary_path
            if not primary:
                raise LaunchRefused("source_has_no_worktree", "source has no worktree")
            name = str(spec.get("name") or "")
            candidate = derive_worktree_path(primary, name)  # name + root guards
            branch = str(spec.get("branch") or name)
            if not valid_branch(branch):
                raise LaunchRefused("branch_invalid", f"invalid branch: {branch!r}")
            if candidate.exists():
                raise LaunchRefused(
                    "worktree_duplicate", f"worktree {name!r} already exists"
                )
            if any(
                Path(wt.path).name == name and Path(wt.path).parent == candidate.parent
                for wt in source.worktrees
            ):
                raise LaunchRefused(
                    "worktree_duplicate", f"worktree {name!r} is already registered"
                )
            return "", str(candidate), {
                "name": name,
                "branch": branch,
                "repo_path": str(primary),
                "path": str(candidate),
                **({"start_point": str(spec["start_point"])} if spec.get("start_point") else {}),
            }
        raise LaunchRefused("worktree_mode_invalid", "worktree.mode must be existing|new")

    # command composition ---------------------------------------------------

    def _agent_argv(
        self, executable: str, argv: list[str], launch_id: str, mode: Any, parent_operation_id: str,
        *, read_only: bool = False, engine_id: str = "",
    ) -> dict[str, Any]:
        """The agent's own flags on top of the profile argv: the rider and
        gate hooks, the HoldSpeak MCP, the Control mode's permission flags,
        pi's folder and engine. One composition for a launch and for its
        Resume after a restart (Betterment AG6). ``codex_tail`` goes after
        Codex's mode flags (they need the worktree, added at the spawn)."""
        from . import agent_mcp

        env: dict[str, str] = {}
        model_key_slot = ""
        codex_tail: list[str] = []
        gated = False
        if executable == "claude":
            # Every Claude launch carries HoldSpeak's spawn settings: the
            # rider hooks (so the launch registers with no manual
            # ``agent-hook install``) and the gate hooks (inert unless the
            # gate holds this worktree).
            from .. import coder_gate

            if read_only:
                argv = _claude_read_only_argv(argv)
            settings_path = coder_gate.write_spawn_settings()
            # Claude's documented ``--add-dir`` discovery loads skills from
            # the private launch directory. ``--settings`` remains the hook
            # document; neither flag edits the user's Claude config.
            argv = [*argv, "--settings", str(settings_path), "--add-dir", str(settings_path.parent)]
            # Conductor K6: the HoldSpeak MCP, from the launch's credential.
            mcp_config = agent_mcp.write_mcp_config(launch_id, self._mcp_config_dir)
            allowed: tuple[str, ...] = () if read_only else (("Bash",) if parent_operation_id else ())
            # Conductor R1: Normal and YOLO accept edits in the worktree.
            argv = [*argv, *agent_mcp.claude_permission_args(mode, argv, read_only=read_only)]
            argv = [*argv, *agent_mcp.claude_args(mcp_config, mode, allowed=allowed, read_only=read_only)]
            if read_only:
                # Verified against the installed Claude Code help: --tools is
                # an explicit built-in allow-list; these tools cannot edit or
                # execute shell commands.
                argv = _replace_tools_option(argv, "Read,Grep,Glob")
            gated = bool(parent_operation_id)
        elif executable == "codex":
            from .. import coder_gate
            from ..principals import agent_credentials

            if read_only:
                argv = _codex_read_only_argv(argv)

            # Conductor R3: every Codex launch runs in its own process with the
            # rider and gate hooks (inert unless the gate holds this worktree).
            from .. import agent_skill

            launch_settings_dir = coder_gate.spawn_settings_path().parent
            agent_skill.install_launch_skills(launch_settings_dir)
            argv = [*argv, *coder_gate.codex_spawn_args()]
            # The approval and sandbox flags need the worktree's git folder:
            # added once the worktree exists (before the spawn).
            codex_tail = agent_mcp.codex_args(agent_credentials.hub_url, mode, read_only=read_only)
            gated = bool(parent_operation_id)
        elif executable == "pi":
            from .. import coder_gate
            from ..principals import agent_credentials
            from . import pi_launch

            # pi spike #1020: the launch's own pi folder (the engine, the
            # HoldSpeak MCP, the gate and rider commands), the transcript
            # folder and the extension. The engine's key rides the spawn's
            # one-shot file (by its slot), never argv.
            engine = self.pi_engine(engine_id)
            pi_folder = pi_launch.write_pi_dir(
                launch_id, engine, hub_url=agent_credentials.hub_url,
                hooks=coder_gate.pi_spawn_hooks(coder_gate.spawn_prefix()),
                keyed=bool(engine.key_slot), directory=self._mcp_config_dir,
            )
            argv = [*argv, *pi_launch.launch_args(engine, pi_folder, read_only=read_only)]
            if read_only:
                argv = _replace_tools_option(argv, "read,grep,find,ls")
            env = pi_launch.launch_env(pi_folder, mcp_hold=not agent_mcp.pre_approved(mode))
            model_key_slot = engine.key_slot
            gated = bool(parent_operation_id)
        return {"argv": argv, "codex_tail": codex_tail, "env": env,
                "model_key_slot": model_key_slot, "gated": gated}

    @staticmethod
    def compose_command(
        argv: list[str], worktree_path: str, story_env: str,
        *, parent_operation_id: str = "", env: Optional[Mapping[str, str]] = None,
        shell_after_failure: bool = False,
    ) -> str:
        """The ONE shell string tmux receives. Every substitution is a
        pre-validated safe token or a server-side path, individually
        quoted — a client never contributes a byte of it directly.
        ``env``: server-side variables of the launch (pi's folder and its
        offline switches); never a secret. ``shell_after_failure`` (a
        Resume, Betterment AG6): when the agent exits with an error (an old
        session id), the pane keeps a login shell in the worktree."""
        quoted = " ".join(shlex.quote(token) for token in argv)
        parent = (
            f"HOLDSPEAK_PARENT_OPERATION_ID={shlex.quote(parent_operation_id)} "
            if parent_operation_id
            else ""
        )
        extra = "".join(
            f"{name}={shlex.quote(str(value))} " for name, value in sorted((env or {}).items())
            if re.match(r"^[A-Z][A-Z0-9_]{0,63}$", str(name))
        )
        if shell_after_failure:
            return (
                f"cd {shlex.quote(str(worktree_path))} && "
                f"HOLDSPEAK_STORY_REF={shlex.quote(story_env)} {parent}{extra}{quoted} "
                '|| exec "${SHELL:-/bin/sh}" -l'
            )
        return (
            f"cd {shlex.quote(str(worktree_path))} && "
            f"HOLDSPEAK_STORY_REF={shlex.quote(story_env)} {parent}{extra}exec {quoted}"
        )

    # the launch -------------------------------------------------------------

    def launch(
        self, request: Any, *, launch_id: str = "", parent_operation_id: str = "",
        principal: Any = None,
    ) -> dict[str, Any]:
        """§9 agent.launch. All refusals are typed and pre-execution;
        the execution order (and what each failure leaves behind) is:

        1. worktree.create envelope (mode=new only) → its OWN receipt;
           a later failure retains the worktree and names it.
        2. factory.spawn envelope → the node launch receipt.
        3. immutable terminal target issued from the spawned pane.
        4. ONE Work attempt (kind=launch, exact, session unbound).
        5. the launch record persisted. A failure after step 2 retains
           the spawned session and NAMES it in the record — ending an
           attempt and killing a process are separate consequences
           (the kill stays coder_factory's gated act), so nothing is
           ever killed implicitly and nothing is silently orphaned.
        """
        if not isinstance(request, Mapping):
            raise LaunchRefused("request_malformed", "a launch request must be an object")
        self._refuse_client_execution_fields(request)
        profile_id = str(
            request.get("agent_profile_id") or request.get("profile_id") or ""
        )
        argv = self._profiles.resolve_argv(profile_id, request.get("options"))
        origin_ref = origin_ref_of(request)
        profile = self._profiles.get(profile_id) or {}
        engine_id = str(request.get("engine_id") or "").strip()
        self._preflight(profile, engine_id)
        project, story_id = self._story_ref(request)
        source_id = str(request.get("source_id") or "")
        source = self._registry.get(source_id)
        if source is None:
            raise LaunchRefused("source_unknown", f"unknown source {source_id!r}")
        worktree_id, worktree_path, pending_create = self._resolve_worktree(
            request, source
        )
        session_name = self._session_name(request, story_id)
        gate_state = "not gated"
        if parent_operation_id:
            self._require_process_gate(profile, worktree_path)
        launch_id = launch_id or "launch_" + uuid.uuid4().hex[:16]
        from . import agent_mcp

        mode = self._launch_mode(request)
        review = request.get("review") if isinstance(request.get("review"), Mapping) else {}
        role = "reviewer" if str(review.get("role") or "").strip().lower() == "reviewer" else "builder"
        if role == "reviewer" and review.get("read_only") is False:
            raise LaunchRefused("reviewer_read_only_required", "reviewer launches are always read-only")
        read_only = role == "reviewer"
        executable = str(profile.get("executable") or "")
        agent_argv = self._agent_argv(
            executable, argv, launch_id, mode, parent_operation_id, read_only=read_only, engine_id=engine_id,
        )
        argv, codex_tail = agent_argv["argv"], agent_argv["codex_tail"]
        launch_env, model_key_slot = agent_argv["env"], agent_argv["model_key_slot"]
        if agent_argv["gated"]:
            gate_state = "gated"
        record: dict[str, Any] = {
            "launch_schema": LAUNCHES_SCHEMA,
            "launch_id": launch_id,
            "state": "starting",
            "node_id": self._local_node_id,
            "profile_id": profile_id,
            "gate": gate_state,
            "source_id": source_id,
            "worktree_id": worktree_id,
            # Conductor K5: the branch this launch made; the tool gate lets a
            # YOLO agent push this branch only. Empty for an existing worktree.
            "branch": str((pending_create or {}).get("branch") or "") or self._again_branch(request),
            "story_ref": {"project": project, "story_id": story_id},
            "origin_ref": origin_ref,
            # Betterment AG11: a helper names the launch that started it.
            "helper_of": str(request.get("helper_of") or "") or None,
            "session": session_name,
            "target": None,
            "attempt_id": None,
            "commands": {"worktree_create": None, "spawn": None, "instruction": None},
            "operation_id": parent_operation_id or None,
            "rollback": None,
            "launched_at": _iso_now(self._wall_now()),
            # PHILO-14 C0: the control mode the launch ran under (the lane shows it).
            "control_mode": mode,
            "role": role,
            "read_only": read_only,
            **({"review": dict(review)} if role == "reviewer" else {}),
            "mcp": {
                "server": agent_mcp.SERVER_NAME,
                "palette": "CONDUCTOR",
                "pre_approved": agent_mcp.pre_approved(mode),
            },
        }

        # Publish the immutable reviewer posture before any credential, grant,
        # worktree or process side effect. Subsequent updates retain this row.
        self._ledger.record(record)

        # 1. the DISTINCT worktree-create op, through the envelope.
        if pending_create is not None:
            created = self._commands.submit(
                {
                    "node_id": self._local_node_id,
                    "operation": {"family": "delivery_factory", "verb": "worktree.create"},
                    "payload": pending_create,
                }
            )
            record["commands"]["worktree_create"] = created.get("command_id")
            receipt = created.get("receipt") or {}
            if receipt.get("outcome") != "worktree_created":
                record["state"] = "failed"
                record["failure"] = {
                    "stage": "worktree_create",
                    "outcome": str(receipt.get("outcome") or created.get("state")),
                }
                self._release_mcp(launch_id)
                self._ledger.record(record)
                return record
            registered_source, registered = self._registry.register(worktree_path)
            assert registered_source.source_id == source_id
            worktree_id = record["worktree_id"] = registered.worktree_id

        # 2. spawn through the envelope: the node launch receipt.
        if executable == "codex":
            from .. import agent_skill

            # Codex discovers repository skills from ``.agents/skills`` below
            # its CWD/repository root. The private settings folder above
            # carries the launch artifact, while this repo-native copy makes
            # the skill visible to the actual Codex process without changing
            # the user's CODEX_HOME or auth configuration.
            agent_skill.install_codex_repo_skill(Path(worktree_path))
            argv = [*argv, *self._codex_mode_args(argv, mode, worktree_path, read_only=read_only), *codex_tail]
        command = self.compose_command(
            argv, worktree_path, f"{project}/{story_id}",
            parent_operation_id=parent_operation_id, env=launch_env,
        )
        spawned = self._commands.submit(
            {
                "node_id": self._local_node_id,
                "operation": {"family": "coder_factory", "verb": "factory.spawn"},
                # launch_id: the spawn issues the launch-bound credential.
                "payload": {
                    "name": session_name, "command": command, "launch_id": launch_id,
                    # K6 item scope: the agent may change its origin item.
                    "scope_items": [f"{origin_ref['kind']}:{origin_ref['id']}"] if origin_ref else [],
                    # K6: the Project the agent may add to (a hand-off's own).
                    "project_id": project if origin_ref and project != "desk" else None,
                    "role": role,
                    "read_only": read_only,
                    # pi: the engine key's SLOT (the value is read at spawn).
                    **({"model_key_slot": model_key_slot} if model_key_slot else {}),
                },
            }
        )
        record["commands"]["spawn"] = spawned.get("command_id")
        spawn_receipt = spawned.get("receipt") or {}
        if spawn_receipt.get("outcome") != "spawned":
            record["state"] = "failed"
            record["failure"] = {
                "stage": "spawn",
                "outcome": str(spawn_receipt.get("outcome") or spawned.get("state")),
            }
            if pending_create is not None:
                # The worktree-create receipt records what exists: the
                # worktree is retained and named, never silently deleted.
                record["rollback"] = {
                    "worktree": "retained",
                    "worktree_command_id": record["commands"]["worktree_create"],
                }
            self._release_mcp(launch_id)
            self._ledger.record(record)
            return record

        # 3. the immutable target from the pane the spawn created.
        pane_id = self._first_pane(session_name)
        issued = (
            self._targets.issue(f"pane:{pane_id}")
            if pane_id
            else {"status": "pane_gone"}
        )
        if issued.get("status") != "issued":
            record["state"] = "failed"
            record["failure"] = {"stage": "target", "outcome": str(issued.get("status"))}
            record["rollback"] = {
                **(record.get("rollback") or {}),
                "session": "retained",  # named here; ending it is a gated act
            }
            self._release_mcp(launch_id)
            self._ledger.record(record)
            return record
        record["target"] = {
            "target_id": issued["target_id"],
            "target_generation": issued["target_generation"],
            "pane_id": issued["pane_id"],
        }
        # PR #1022 r1: the launch's process group, read while its first
        # process lives, so Stop ends its children after that process exits.
        record["process_group"] = coder_factory.pane_process_group(
            str(issued["pane_id"]), runner=self._runner
        )

        # 4. ONE Work attempt: kind=launch, exact, session unbound until
        #    the rider reports.
        try:
            attempt = self._attempts.create(
                source_id=source_id,
                worktree_id=worktree_id,
                project=project,
                story_id=story_id,
                node_id=self._local_node_id,
                session_id=None,
                target_id=issued["target_id"],
                kind="launch",
                exact=True,
                claimed_by=f"launch:{profile_id}",
                state="starting",
                now=self._wall_now(),
                origin_ref=(
                    f"{origin_ref['kind']}:{origin_ref['id']}" if origin_ref else None
                ),
            )
        except Exception as exc:
            # The failed logical transaction leaves NO unaccounted
            # process: the spawned session is retained and NAMED here
            # (terminal openable via the issued target); ending it is
            # coder_factory.kill's gated, deliberate act — never an
            # implicit rollback side effect.
            record["state"] = "failed"
            record["failure"] = {"stage": "attempt", "outcome": _scrub(str(exc))}
            record["rollback"] = {
                **(record.get("rollback") or {}),
                "session": "retained",
            }
            self._release_mcp(launch_id)
            self._ledger.record(record)
            return record

        record["attempt_id"] = attempt.attempt_id
        record["state"] = "launched"
        # K6: the owner's press on the launch grants the launch identity
        # decision PROPOSALS (decision.create, status proposed) for its life.
        record["mcp"]["decision_proposals"] = "not_granted" if read_only else self._grant(principal, launch_id, None)
        # ... and additions (links, resources) to its own Project.
        launch_project = project if origin_ref and project != "desk" else None
        record["mcp"]["project_additions"] = (
            "not_granted" if read_only else (self._grant(principal, launch_id, launch_project) if launch_project else "no_project")
        )
        self._ledger.record(record)
        return record

    @staticmethod
    def _grant(principal: Any, launch_id: str, project_id: Optional[str]) -> str:
        from .. import coder_factory
        from ..services import conductor_launch

        identity = coder_factory.launch_identity(launch_id)
        try:
            granted = (
                conductor_launch.grant_project_additions(principal, identity, project_id, ttl_seconds=43_200.0)
                if project_id
                else conductor_launch.grant_decision_proposals(principal, identity, ttl_seconds=43_200.0)
            )
        except Exception as exc:  # a grant never fails the launch
            log.warning("launch grant not made for %s (%s)", launch_id, exc)
            return "not_granted"
        return "granted" if granted else "not_granted"

    def _release_mcp(self, launch_id: str) -> None:
        """A failed launch: its MCP credential and config go (K6). The
        session, when one was spawned, is retained and named as before."""
        from .. import coder_factory
        from . import agent_mcp

        coder_factory.revoke_launch(launch_id)
        agent_mcp.remove_mcp_config(launch_id, self._mcp_config_dir)

    def submit_process_spawn(
        self, request: Mapping[str, Any], instruction: str, principal: Any,
        *,
        after_registration: bool = False,
        parent_operation_id: str = "",
    ) -> dict[str, Any]:
        """Admit, approve and execute one ``process.spawn`` owner gesture.

        The existing launch service remains the driver. The bounded first
        instruction is a child ``process.input`` operation while the spawn/run
        operation is claimed. Agent hook tool calls inherit the same parent id
        from the launched process environment.
        """
        if self._kernel is None:
            raise LaunchRefused("kernel_unavailable")
        text = str(instruction or "").strip()
        if not text or len(text.encode("utf-8")) > 32768:
            raise LaunchRefused("instruction_invalid")
        self.validate_process_spawn(request)
        from ..kernel.process_spawn import new_launch_id
        from ..principals import Principal, PrincipalKind

        launch_id = new_launch_id()
        subject_refs = [
            f"delivery-source:{request.get('source_id')}",
            f"story:{(request.get('story_ref') or {}).get('story_id')}",
        ]
        origin = origin_ref_of(request)
        if origin is not None:
            subject_refs.append(f"{origin['kind']}:{origin['id']}")
        raw = {
            "request_schema": 1,
            "request_id": str(uuid.uuid4()),
            "idempotency_key": f"process.spawn:{launch_id}",
            "operation": {"name": "process.spawn", "version": 1},
            "subject_refs": subject_refs,
            "target": {"ref": f"launch:{launch_id}"},
            "arguments": {"launch_id": launch_id, **dict(request)},
            "placement": f"node:{self._local_node_id}",
        }
        if parent_operation_id:
            raw["parent_operation_id"] = str(parent_operation_id)
        handle = self._kernel.submit(raw, principal)
        if handle.get("state") == "refused":
            raise LaunchRefused(str((handle.get("receipt") or {}).get("outcome") or "kernel_refused"))
        handle = self._kernel.decide(
            handle["operation_id"], "approve", int(handle["revision"]), principal
        )
        node = Principal(PrincipalKind.NODE, self._local_node_id)
        claimed = self._kernel.claim(node, launch_id)
        if not claimed.get("operations"):
            reason = str((claimed.get("refusal") or {}).get("outcome") or "kernel_claim_refused")
            raise LaunchRefused(reason)
        operation_id = str(handle["operation_id"])
        try:
            record = self.launch(
                request, launch_id=launch_id, parent_operation_id=operation_id,
                principal=principal,
            )
            if record.get("state") != "launched":
                self._kernel.receipt(operation_id, "failed", f"launch:{launch_id}", node)
                return {"operation_id": operation_id, "launch": record}
            if after_registration:
                # The agent reads its first message only once it is up: a
                # dialog (folder trust) or a slow start would eat text typed
                # now. The brief is HELD on the launch record and typed when
                # the rider registers the session (first_message.py).
                profile = self._profiles.get(
                    str(request.get("agent_profile_id") or request.get("profile_id") or "")
                ) or {}
                record = self._first.hold(
                    launch_id, text, principal, operation_id=operation_id,
                    agent=str(request.get("agent_profile_id") or "agent"),
                    trust=profile.get("executable") == "claude",
                    codex=profile.get("executable") == "codex",
                ) or record
                self._first.start(launch_id)
                self._first.watch(launch_id)
                return {
                    "operation_id": operation_id,
                    "correlation_id": operation_id,
                    "launch": record,
                    "instruction_operation_id": None,
                    "instruction_receipt": None,
                }
            sent = self._send_instruction(record, text, principal, request, operation_id)
            commands = dict(record.get("commands") or {})
            commands["instruction"] = sent.get("command_id")
            outcome = str((sent.get("receipt") or {}).get("outcome") or "")
            record = self._ledger.update(
                launch_id, commands=commands,
                instruction_state="sent" if outcome == "delivered" else (outcome or "not_delivered"),
                **({"brief_sent_at": str((sent.get("receipt") or {}).get("executed_at") or "") or _brief_clock()}
                   if outcome == "delivered" else {}),
            ) or record
            self._first.watch(launch_id)
            return {
                "operation_id": operation_id,
                "correlation_id": operation_id,
                "launch": record,
                "instruction_operation_id": sent.get("operation_id"),
                "instruction_receipt": sent.get("receipt"),
            }
        except Exception:
            if self._kernel.store.receipt(operation_id) is None:
                self._kernel.receipt(operation_id, "failed", f"launch:{launch_id}", node)
            self._release_mcp(launch_id)
            raise

    def _send_instruction(
        self, record: Mapping[str, Any], text: str, principal: Any,
        request: Mapping[str, Any], operation_id: str,
    ) -> dict[str, Any]:
        """Arm the spawned pane and type ``text`` as a child ``process.input``."""
        from .. import coder_steering

        target = record.get("target") or {}
        armed = coder_steering.arm(
            str(record.get("session") or ""),
            str(target.get("pane_id") or ""),
            runner=self._runner,
        )
        if armed.get("status") != "armed":
            raise LaunchRefused(
                str(armed.get("status") or "arm_refused"),
                str(armed.get("detail") or "spawned pane could not be armed"),
            )
        return self._commands.submit_process_input(
            {
                "node_id": self._local_node_id,
                "target_id": target.get("target_id"),
                "target_generation": target.get("target_generation"),
                "operation": {"family": "coder_steering", "verb": "terminal.text"},
                "payload": {
                    "text": text,
                    "submit": True,
                    "session_key": record.get("session"),
                    "agent": str(request.get("agent_profile_id") or request.get("profile_id") or "agent"),
                },
                "parent_operation_id": operation_id,
            },
            principal,
        )

    def _worktree_path(self, record: Mapping[str, Any]) -> str:
        """The server-side path of the launch's worktree (never on the wire)."""
        source = self._registry.get(str(record.get("source_id") or ""))
        if source is None:
            return ""
        worktree = next(
            (wt for wt in source.worktrees if wt.worktree_id == record.get("worktree_id")), None
        )
        if worktree is None:
            return ""
        try:
            return str(Path(worktree.path).resolve())
        except OSError:
            return str(worktree.path)

    @property
    def first_message(self) -> Any:
        """The pending first message of this service's launches."""
        return self._first

    def resume_delivery(self, launch_id: str) -> dict[str, Any]:
        """Deliver the held brief of an existing launch (no relaunch)."""
        return self._first.resume(launch_id)

    def resume_session(self, launch_id: str) -> dict[str, Any]:
        """Betterment AG6: bring an agent a restart stopped back to its
        conversation. A new tmux session (the launch's own name) in the
        launch's worktree, through the same start-up as the launch
        (``factory.spawn``: a fresh launch credential, the rider and gate
        hooks, the HoldSpeak MCP), runs the agent's own resume
        (:func:`resume_argv`). The launch keeps its id, its Work attempt and
        its bound session; it reads ``registered`` again with ``resume =
        {state: resuming, at, session_id, command}``. When the resume fails
        (an old id), a login shell stays in the worktree; the flight reads
        ``resume_failed`` once the agent has not reported in the usual
        window. Refusals are typed and leave the launch as it was."""
        from ..services.agent_flights import STOPPED_BY_RESTART

        record = self._ledger.get(launch_id)
        if not record:
            raise LaunchRefused("launch_unknown", f"unknown launch {launch_id!r}")
        if str(record.get("state") or "") != STOPPED_BY_RESTART:
            raise LaunchRefused("launch_not_stopped", "only an agent a restart stopped resumes")
        key = str(record.get("session_key") or "")
        if not key and record.get("attempt_id"):
            try:
                key = str(getattr(self._attempts.get(str(record["attempt_id"])), "session_id", "") or "")
            except Exception:
                key = ""
        _agent, _, session_id = key.partition(":")
        if not session_id or not _SAFE_TOKEN_RE.match(session_id):
            raise LaunchRefused("no_session_to_resume", "the agent never reported its session")
        profile_id = str(record.get("profile_id") or "")
        profile = self._profiles.get(profile_id)
        if profile is None:
            raise LaunchRefused("profile_unknown", f"unknown agent profile {profile_id!r}")
        worktree_path = self._worktree_path(record)
        if not worktree_path or not Path(worktree_path).is_dir():
            raise LaunchRefused("worktree_gone", "the agent's worktree is gone")
        self._preflight(profile, str(record.get("engine_id") or ""))
        parent = str(record.get("operation_id") or "")
        if parent:
            self._require_process_gate(profile, worktree_path)
        executable = str(profile.get("executable") or "")
        mode = self._launch_mode(record)
        role = str(record.get("role") or "builder")
        read_only = role == "reviewer"
        composed = self._agent_argv(
            executable, [executable, *profile["args"]], launch_id, mode, parent,
            read_only=read_only, engine_id=str(record.get("engine_id") or ""),
        )
        argv = composed["argv"]
        if executable == "codex":
            from .. import agent_skill

            agent_skill.install_codex_repo_skill(Path(worktree_path))
            argv = [*argv, *self._codex_mode_args(argv, mode, worktree_path, read_only=read_only), *composed["codex_tail"]]
        argv = resume_argv(executable, argv, session_id)
        story = record.get("story_ref") or {}
        command = self.compose_command(
            argv, worktree_path, f"{story.get('project')}/{story.get('story_id')}",
            parent_operation_id=parent, env=composed["env"], shell_after_failure=True,
        )
        origin = record.get("origin_ref") or {}
        project = str(story.get("project") or "")
        session_name = str(record.get("session") or "")
        spawned = self._commands.submit({
            "node_id": self._local_node_id,
            "operation": {"family": "coder_factory", "verb": "factory.spawn"},
            "payload": {
                "name": session_name, "command": command, "launch_id": launch_id,
                "scope_items": [f"{origin['kind']}:{origin['id']}"] if origin.get("kind") else [],
                "project_id": project if origin.get("kind") and project != "desk" else None,
                "role": role,
                "read_only": read_only,
                **({"model_key_slot": composed["model_key_slot"]} if composed["model_key_slot"] else {}),
            },
        })
        stamp = _iso_now(self._wall_now())
        resume = {
            "at": stamp, "session_id": session_id, "command_id": spawned.get("command_id"),
            "command": " ".join(resume_argv(executable, [executable], session_id)),
        }
        outcome = str((spawned.get("receipt") or {}).get("outcome") or spawned.get("state") or "")
        if outcome != "spawned":
            return self._ledger.update(launch_id, resume={**resume, "state": "failed", "outcome": outcome}) or record
        pane_id = self._first_pane(session_name)
        issued = self._targets.issue(f"pane:{pane_id}") if pane_id else {"status": "pane_gone"}
        fields: dict[str, Any] = {
            "state": "registered", "stopped": None, "control_mode": mode,
            "resume": {**resume, "state": "resuming"},
        }
        if issued.get("status") == "issued":
            fields["target"] = {
                "target_id": issued["target_id"],
                "target_generation": issued["target_generation"],
                "pane_id": issued["pane_id"],
            }
            fields["process_group"] = coder_factory.pane_process_group(str(issued["pane_id"]), runner=self._runner)
        return self._ledger.update(launch_id, **fields) or record

    def _session_alive(self, session_name: str) -> bool:
        run = self._runner or coder_steering._default_runner
        try:
            completed = run(["tmux", "has-session", "-t", session_name])
        except (OSError, subprocess.TimeoutExpired):
            return False
        return completed.returncode == 0

    def _first_pane(self, session_name: str) -> Optional[str]:
        run = self._runner or coder_steering._default_runner
        try:
            completed = run(
                ["tmux", "list-panes", "-t", session_name, "-F", "#{pane_id}"]
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if completed.returncode != 0:
            return None
        lines = (completed.stdout or "").strip().splitlines()
        return lines[0] if lines else None

    # rider binding (HS-94-04's claim path onto the SAME attempt) ------------

    def bind_rider_claims(
        self,
        claims: Optional[list[Mapping[str, Any]]] = None,
        *,
        state_path: Optional[Path] = None,
        now: Optional[datetime] = None,
    ) -> dict[str, int]:
        """Bind emitted rider claims onto their launch attempts.

        A claim whose (source, worktree, project, story) matches a live
        launch attempt with no session binds THAT attempt — the same
        ``attempt_id``, never a duplicate row. A session that already
        holds a live exact attempt is skipped (the DB's partial unique
        index is the final guard). Run this BEFORE the generic
        ``sync_rider_claims`` sweep; once bound, that sweep sees the
        launch attempt as the session's current exact attempt and only
        heartbeats it.
        """
        if claims is None:
            from ..agent_context.sessions import list_agent_story_claims

            claims = list_agent_story_claims(state_path=state_path, now=now)
        resolve = resolver_from_registry(self._registry)
        summary = {"bound": 0, "skipped": 0}
        for row in claims:
            claim = row.get("story_claim")
            if not isinstance(claim, Mapping):
                summary["skipped"] += 1
                continue
            project = str(claim.get("project") or "")
            story_id = str(claim.get("story_id") or "")
            session_key = str(row.get("session_key") or "")
            identity = resolve(row.get("repo_root")) or resolve(row.get("cwd"))
            if not project or not story_id or not session_key or identity is None:
                summary["skipped"] += 1
                continue
            candidates = [
                attempt
                for attempt in self._attempts.find_active(
                    source_id=identity["source_id"],
                    worktree_id=identity["worktree_id"],
                    project=project,
                    story_id=story_id,
                )
                if attempt.kind == "launch" and not attempt.session_id
            ]
            if not candidates:
                summary["skipped"] += 1
                continue
            if self._attempts.find_active(session_id=session_key, exact=True):
                summary["skipped"] += 1  # already exactly bound: no double-pin
                continue
            attempt = candidates[-1]  # oldest unbound launch first
            if not self._bind_session(
                attempt.attempt_id,
                session_key,
                claimed_by=str(claim.get("claimed_by") or f"rider:{row.get('agent')}"),
                claimed_at=claim.get("claimed_at"),
                now=now,
            ):
                summary["skipped"] += 1
                continue
            lifecycle = str(row.get("lifecycle") or "working")
            if lifecycle in ("working", "waiting", "idle", "ended"):
                try:
                    self._attempts.transition(
                        attempt.attempt_id,
                        lifecycle,
                        reason="rider_registered",
                        now=now,
                    )
                except Exception:
                    pass  # binding held; the state heartbeat can retry
            launch = self._ledger.by_attempt(attempt.attempt_id)
            if launch:
                self._ledger.update(
                    launch["launch_id"], state="registered", session_key=session_key,
                    # Betterment AG6: what Resume runs after a restart.
                    resume_command=_resume_words(launch.get("profile_id"), session_key),
                )
            summary["bound"] += 1
        return summary

    def _bind_session(
        self,
        attempt_id: str,
        session_key: str,
        *,
        claimed_by: str,
        claimed_at: Any,
        now: Optional[datetime],
    ) -> bool:
        """Set the launch attempt's session identity, once.

        The attempt repository's public API is deliberately read/
        transition-only; session binding is HS-94-07's one launch-
        specific mutation, performed through the repository's own
        connection factory and guarded by the SAME partial unique index
        (one live exact attempt per session) — an IntegrityError means
        the session is already pinned, and the bind is refused, not
        forced."""
        import sqlite3

        timestamp = _iso_now(now or self._wall_now())
        try:
            with self._attempts._connection() as conn:
                updated = conn.execute(
                    "UPDATE work_attempts SET session_id = ?, claimed_by = ?, "
                    "claimed_at = COALESCE(?, claimed_at), updated_at = ? "
                    "WHERE attempt_id = ? AND session_id IS NULL",
                    (
                        session_key,
                        claimed_by,
                        str(claimed_at) if claimed_at else None,
                        timestamp,
                        attempt_id,
                    ),
                ).rowcount
                if not updated:
                    return False
                conn.execute(
                    "INSERT INTO work_attempt_events "
                    "(attempt_id, from_state, to_state, reason, occurred_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (attempt_id, "starting", "starting", "rider_registered", timestamp),
                )
        except sqlite3.IntegrityError:
            return False
        return True

    # failed-to-register (launch without a rider) -----------------------------

    def expire_unregistered(
        self,
        *,
        timeout_seconds: int = DEFAULT_REGISTER_TIMEOUT_SECONDS,
        now: Optional[datetime] = None,
    ) -> int:
        """Launch attempts still ``starting`` with no session past the
        registration window move to ``unknown`` with reason
        ``failed_to_register`` — a retained partial state. The terminal
        target stays valid and openable; nothing is deleted."""
        moment = now or self._wall_now()
        moved = 0
        for attempt in self._attempts.find_active():
            if attempt.kind != "launch" or attempt.session_id:
                continue
            if attempt.state != "starting":
                continue
            started = _parse_ts(attempt.started_at)
            if started is None:
                continue
            if (moment - started).total_seconds() < timeout_seconds:
                continue
            self._attempts.transition(
                attempt.attempt_id, "unknown", reason="failed_to_register", now=now
            )
            launch = self._ledger.by_attempt(attempt.attempt_id)
            if launch:
                self._ledger.update(launch["launch_id"], state="failed_to_register")
            moved += 1
        return moved

    # discovery ---------------------------------------------------------------

    def discover(self) -> dict[str, Any]:
        """Panes/sessions as launchable/steerable TARGETS: node +
        source/worktree + profile + the immutable target handle. No
        client ever needs a pre-known ``pane:%N`` — this listing IS how
        targets are learned. Wire rows are path-free (§13)."""
        if self._runner is None and shutil.which("tmux") is None:
            return {
                "discover_schema": DISCOVER_SCHEMA,
                "node_id": self._local_node_id,
                "status": "tmux_absent",
                "targets": [],
            }
        run = self._runner or coder_steering._default_runner
        try:
            completed = run(
                [
                    "tmux",
                    "list-panes",
                    "-a",
                    "-F",
                    "#{session_name}\t#{pane_id}\t#{pane_current_path}",
                ]
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {
                "discover_schema": DISCOVER_SCHEMA,
                "node_id": self._local_node_id,
                "status": "error",
                "detail": _scrub(str(exc)),
                "targets": [],
            }
        if completed.returncode != 0:
            return {
                "discover_schema": DISCOVER_SCHEMA,
                "node_id": self._local_node_id,
                "status": "tmux_absent",
                "targets": [],
            }
        resolve = resolver_from_registry(self._registry)
        rows: list[dict[str, Any]] = []
        for line in (completed.stdout or "").splitlines():
            parts = line.split("\t")
            if len(parts) != 3:
                continue
            session, pane_id, pane_path = parts
            issued = self._targets.issue(f"pane:{pane_id}")
            if issued.get("status") != "issued":
                continue  # an unprovable pane gets no target (typed absence)
            identity = resolve(pane_path) or {}
            launch = self._ledger.by_session(session)
            attempt = None
            if launch and launch.get("attempt_id"):
                attempt = self._attempts.get(launch["attempt_id"])
            rows.append(
                {
                    "node_id": self._local_node_id,
                    "session": session,
                    "pane_id": issued["pane_id"],
                    "target_id": issued["target_id"],
                    "target_generation": issued["target_generation"],
                    "source_id": identity.get("source_id"),
                    "worktree_id": identity.get("worktree_id"),
                    "profile_id": launch.get("profile_id") if launch else None,
                    "gate": launch.get("gate") if launch else "not gated",
                    "launch_id": launch.get("launch_id") if launch else None,
                    "story_ref": launch.get("story_ref") if launch else None,
                    "attempt_id": launch.get("attempt_id") if launch else None,
                    "attempt_state": attempt.state if attempt else None,
                    "session_bound": bool(attempt.session_id) if attempt else False,
                }
            )
        return {
            "discover_schema": DISCOVER_SCHEMA,
            "node_id": self._local_node_id,
            "status": "ok",
            "targets": rows,
        }


_DEFAULT_SERVICES: dict[int, LaunchService] = {}


def default_launch_service(database: Any) -> LaunchService:
    """One production launch driver shared by the codec and web façade."""
    key = id(database)
    service = _DEFAULT_SERVICES.get(key)
    if service is not None:
        return service
    from ..db.delivery_receipts import NodeReceiptLedger
    from . import DeliveryRegistry
    from .commands import HubCommandService, NodeCommandProcessor
    from .terminal import TerminalTargetRegistry

    targets = TerminalTargetRegistry()
    processor = NodeCommandProcessor(
        node_id="local", targets=targets, ledger=NodeReceiptLedger()
    )
    commands = HubCommandService(
        repo=database.delivery_receipts,
        processor=processor,
        local_node_id="local",
    )
    from .pi_launch import coding_engine, engine_for_profile

    service = LaunchService(
        profiles=AgentProfileStore(),
        registry=DeliveryRegistry(),
        targets=targets,
        commands=commands,
        attempts=database.work_attempts,
        ledger=LaunchLedger(),
        local_node_id="local",
        pi_engine=lambda engine_id="": (
            engine_for_profile(database, engine_id) if engine_id else coding_engine(database)
        ),
        db=database,
    )
    _DEFAULT_SERVICES[key] = service
    return service


__all__ = [
    "AGENT_PROFILES_SCHEMA",
    "AgentProfileStore",
    "DEFAULT_REGISTER_TIMEOUT_SECONDS",
    "DISCOVER_SCHEMA",
    "KNOWN_EXECUTABLES",
    "LAUNCHES_SCHEMA",
    "LaunchLedger",
    "LaunchRefused",
    "LaunchService",
    "ORIGIN_KINDS",
    "agent_of_profile",
    "default_launch_service",
    "derive_worktree_path",
    "derived_story_ref",
    "origin_ref_of",
    "execute_worktree_create",
    "execute_worktree_remove",
    "valid_branch",
]


def _brief_clock() -> str:
    """PHILO-15 B42: the brief's delivery time (UTC, ``Z``)."""
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
