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

import json
import re
import shlex
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from .. import coder_factory, coder_steering
from ..coder_steering import Runner
from .attempts import resolver_from_registry

AGENT_PROFILES_SCHEMA = 1
LAUNCHES_SCHEMA = 1
DISCOVER_SCHEMA = 1
DEFAULT_PROFILES_PATH = Path.home() / ".holdspeak" / "agent_profiles.json"
DEFAULT_LAUNCHES_PATH = Path.home() / ".holdspeak" / "agent_launches.json"

#: The FIXED launcher allow-list (§9): a profile's executable must be
#: one of these bare names — never a path, never a shell.
KNOWN_EXECUTABLES = ("claude", "codex")

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
]


class LaunchRefused(ValueError):
    """A typed launch refusal: ``reason`` is machine-readable and the
    message never echoes a filesystem path, an argv, or a secret."""

    def __init__(self, reason: str, message: Optional[str] = None) -> None:
        super().__init__(message or reason)
        self.reason = reason


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
    """Client-safe error text: filesystem roots replaced, bounded."""
    text = str(detail or "")
    for root in roots:
        if root:
            text = text.replace(str(root), "<root>")
    return text[:300]


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
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

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
    try:
        completed = run(argv)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return _audited({"status": "error", "detail": _scrub(str(exc), repo_path, path)})
    if completed.returncode != 0:
        detail = _scrub((completed.stderr or "").strip() or "git refused", repo_path, path)
        status = "worktree_duplicate" if "already exists" in detail.lower() else "error"
        return _audited({"status": status, "detail": detail})
    return _audited({"status": "worktree_created", "name": name, "branch": branch})


# ── the launch ledger (durable launch records) ───────────────────────


class LaunchLedger:
    """Launch records at ``~/.holdspeak/agent_launches.json``
    (``launches_schema: 1``, newest :data:`LAUNCH_LEDGER_MAX_ROWS`
    kept). Records are path-free by construction — every field is an
    opaque ID, a label, or a receipt reference."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self._path = Path(path) if path else DEFAULT_LAUNCHES_PATH
        self._records: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if isinstance(raw, dict) and raw.get("launches_schema") == LAUNCHES_SCHEMA:
            rows = raw.get("launches")
            if isinstance(rows, list):
                self._records = [dict(row) for row in rows if isinstance(row, dict)]

    def _save(self) -> None:
        doc = {
            "launches_schema": LAUNCHES_SCHEMA,
            "launches": self._records[-LAUNCH_LEDGER_MAX_ROWS:],
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def record(self, launch: dict[str, Any]) -> None:
        self._records.append(dict(launch))
        self._records = self._records[-LAUNCH_LEDGER_MAX_ROWS:]
        self._save()

    def update(self, launch_id: str, **fields: Any) -> Optional[dict[str, Any]]:
        for row in self._records:
            if row.get("launch_id") == launch_id:
                row.update(fields)
                self._save()
                return dict(row)
        return None

    def get(self, launch_id: str) -> Optional[dict[str, Any]]:
        for row in self._records:
            if row.get("launch_id") == launch_id:
                return dict(row)
        return None

    def by_session(self, session: str) -> Optional[dict[str, Any]]:
        for row in reversed(self._records):
            if row.get("session") == str(session or ""):
                return dict(row)
        return None

    def by_attempt(self, attempt_id: str) -> Optional[dict[str, Any]]:
        for row in reversed(self._records):
            if row.get("attempt_id") == str(attempt_id or ""):
                return dict(row)
        return None

    def list(self) -> list[dict[str, Any]]:
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
    ) -> None:
        self._profiles = profiles
        self._registry = registry
        self._targets = targets
        self._commands = commands
        self._attempts = attempts
        self._ledger = ledger or LaunchLedger()
        self._runner = runner
        self._git = git_runner or _default_git_runner
        self._local_node_id = str(local_node_id)
        self._wall_now = wall_now

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
        derived = "hs-" + re.sub(r"[^A-Za-z0-9_.-]", "-", story_id.lower())
        return f"{derived}-{uuid.uuid4().hex[:6]}"

    def _worktree_dirty(self, path: str) -> bool:
        try:
            completed = self._git(["git", "-C", str(path), "status", "--porcelain"])
        except (OSError, subprocess.TimeoutExpired):
            return True  # unprovable cleanliness is treated as dirty
        if completed.returncode != 0:
            return True
        return bool((completed.stdout or "").strip())

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
            }
        raise LaunchRefused("worktree_mode_invalid", "worktree.mode must be existing|new")

    # command composition ---------------------------------------------------

    @staticmethod
    def compose_command(argv: list[str], worktree_path: str, story_env: str) -> str:
        """The ONE shell string tmux receives. Every substitution is a
        pre-validated safe token or a server-side path, individually
        quoted — a client never contributes a byte of it directly."""
        quoted = " ".join(shlex.quote(token) for token in argv)
        return (
            f"cd {shlex.quote(str(worktree_path))} && "
            f"HOLDSPEAK_STORY_REF={shlex.quote(story_env)} exec {quoted}"
        )

    # the launch -------------------------------------------------------------

    def launch(self, request: Any) -> dict[str, Any]:
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
        project, story_id = self._story_ref(request)
        source_id = str(request.get("source_id") or "")
        source = self._registry.get(source_id)
        if source is None:
            raise LaunchRefused("source_unknown", f"unknown source {source_id!r}")
        worktree_id, worktree_path, pending_create = self._resolve_worktree(
            request, source
        )
        session_name = self._session_name(request, story_id)

        launch_id = "launch_" + uuid.uuid4().hex[:16]
        record: dict[str, Any] = {
            "launch_schema": LAUNCHES_SCHEMA,
            "launch_id": launch_id,
            "state": "starting",
            "node_id": self._local_node_id,
            "profile_id": profile_id,
            "source_id": source_id,
            "worktree_id": worktree_id,
            "story_ref": {"project": project, "story_id": story_id},
            "session": session_name,
            "target": None,
            "attempt_id": None,
            "commands": {"worktree_create": None, "spawn": None},
            "rollback": None,
            "launched_at": _iso_now(self._wall_now()),
        }

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
                self._ledger.record(record)
                return record
            registered_source, registered = self._registry.register(worktree_path)
            assert registered_source.source_id == source_id
            worktree_id = record["worktree_id"] = registered.worktree_id

        # 2. spawn through the envelope: the node launch receipt.
        command = self.compose_command(argv, worktree_path, f"{project}/{story_id}")
        spawned = self._commands.submit(
            {
                "node_id": self._local_node_id,
                "operation": {"family": "coder_factory", "verb": "factory.spawn"},
                "payload": {"name": session_name, "command": command},
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
            self._ledger.record(record)
            return record
        record["target"] = {
            "target_id": issued["target_id"],
            "target_generation": issued["target_generation"],
            "pane_id": issued["pane_id"],
        }

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
            self._ledger.record(record)
            return record

        record["attempt_id"] = attempt.attempt_id
        record["state"] = "launched"
        self._ledger.record(record)
        return record

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
                    launch["launch_id"], state="registered", session_key=session_key
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
    "derive_worktree_path",
    "execute_worktree_create",
    "valid_branch",
]
