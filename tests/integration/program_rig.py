"""The Programs rig: the engine over real git, a real database and fakes at
the process edge only.

- git is real: a repository with a bare ``origin`` (the engine's push is a
  real push), one real worktree per step (``git worktree add -b <branch>
  <path> <base>``), the fake agent's commits are real commits;
- the hand is AG12's ``HubProducer`` double grown a worktree (each launch is
  a launch record in AG12's ``Ledger`` double; a reviewer is a helper launch);
- the agent is :class:`FakeAgent`: it writes files, commits, and ends its
  turn (a new turn id, flight state ``done``);
- the gate is ``tests/fixtures/fake_program_check.sh`` (a quick-check-shaped
  log), run by the engine's own ``run_check`` through a real ``sh``;
- ``gh`` is :class:`FakeGitHub`: ``pr create`` answers a PR URL, ``pr merge``
  marks the PR merged, and :meth:`FakeGitHub.sweep` writes what the
  Heartbeat's follow-through writes on the launch (``follow_through.pr``);
- AG12's review loop is the real ``AgentReviewLoop`` with its reader seams;
  the fake reviewer's words are ``Rig.words`` (a test types them). PG-REQ:
  when a test's words name no ``REQ`` line, the fake reviewer answers
  ``REQ Rn: MET`` for each owner's requirement its brief lists (a reviewer
  that finds every requirement holds); a test that drives an UNMET or a
  missing answer writes its own ``REQ`` lines. The fake reviewer puts its
  words in the REVIEW RESULT block the brief asks for (``NO_BLOCK`` first:
  none).

The rig is cheap (pipe/programs-rig, 2026-11-09): the seeded repository and
its ``origin`` are built once per process and copied per test
(:func:`make_repo`); the rig reads a HEAD from the files, not through a git
process (:func:`head_of`). By default the engine's two git-heavy units are
in memory: a checkpoint pin (seven git calls each, real in
``ProgramRunner.pin_checkpoint``) and the checkpoint reach read
(``ProgramService.checkpoint_reach``); the engine's ``git rev-parse HEAD``
through its run port is answered from the files. ``Rig(..., real_git=True)``
keeps every git call real: the tests that read a pin with git use it, and
one smoke in ``test_program_run``. Everything else the engine does with git
(worktrees, add, commit, diff, push, fetch, rebase, the delivery) stays
real.
"""
from __future__ import annotations

import atexit
import hashlib
import re
import shutil
import tempfile

#: A test's reviewer words that start with this get no REVIEW RESULT block.
NO_BLOCK = "\x00no-block\x00"
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Optional

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.agent_hand_service import _STOPPED_LAUNCH_STATES, AgentHandRefused, program_step_spec
from holdspeak.services.agent_review import AgentReviewLoop
from holdspeak.services.program_runner import ProgramRunner, _default_runner
from holdspeak.services.program_service import ProgramService
from tests.unit.test_agent_review import Ledger

OWNER = Principal(PrincipalKind.OWNER, "owner-session")


def owner_app() -> Any:
    """A bare FastAPI app whose every request carries the owner principal, as
    the hub's edge sets it. A produced route reads no default owner (Codex on
    #2051): a request with no principal is unauthenticated."""
    from fastapi import FastAPI

    app = FastAPI()

    @app.middleware("http")
    async def _owner(request, call_next):  # type: ignore[no-untyped-def]
        request.state.principal = OWNER
        return await call_next(request)

    return app
FAKE_CHECK = Path(__file__).resolve().parents[1] / "fixtures" / "fake_program_check.sh"


def git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
    assert proc.returncode == 0, (args, proc.stderr)
    return proc.stdout.strip()


#: The rig's ``origin`` as written in the repository: a GitHub URL that git
#: rewrites to the bare repository (``url.<bare>.insteadOf``), so pushes are
#: real and ``gh`` (FakeGitHub) owns the PRs. ``github=False``: the bare path
#: itself (a remote with no PRs: HoldSpeak merges into the base itself).
RIG_GITHUB_URL = "https://github.com/acme/app.git"


_TEMPLATES: dict[tuple[bool, str], Path] = {}


def _seed(root: Path, *, github: bool) -> Path:
    """The seeded repository and its bare ``origin`` under ``root``, by git."""
    origin = root / "origin.git"
    subprocess.run(["git", "init", "-q", "--template=", "--bare", "-b", "main", str(origin)],
                   capture_output=True, check=True)
    repo = root / "app"
    repo.mkdir(parents=True)
    git(repo, "init", "-q", "--template=", "-b", "main")
    # One identity for the seed and every step worktree (worktrees share the
    # repository's config; FakeHand once wrote "Agent" into it per launch).
    git(repo, "config", "user.email", "agent@example.test")
    git(repo, "config", "user.name", "Agent")
    (repo / "README.md").write_text("# app\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "seed")
    if github:
        git(repo, "config", f"url.{origin}.insteadOf", RIG_GITHUB_URL)
        git(repo, "remote", "add", "origin", RIG_GITHUB_URL)
    else:
        git(repo, "remote", "add", "origin", str(origin))
    git(repo, "push", "-q", "-u", "origin", "main")
    return repo


def make_repo(root: Path, *, github: bool = True, seed: Optional[Callable[[Path], None]] = None) -> Path:
    """A repository with one seed commit pushed to a bare ``origin``, both
    under ``root``. Built by git once per process, then copied: the copy's
    only absolute path (the ``origin`` in ``.git/config``) is rewritten.
    ``seed``: a function that grows the template once (it commits and pushes
    what it writes); each copy starts from its result."""
    key = (github, f"{seed.__module__}.{seed.__qualname__}" if seed else "")
    template = _TEMPLATES.get(key)
    if template is None:
        scratch = tempfile.mkdtemp(prefix="holdspeak-rig-")
        atexit.register(shutil.rmtree, scratch, True)
        template = Path(scratch) / "seed"
        made = _seed(template, github=github)
        if seed is not None:
            seed(made)
        _TEMPLATES[key] = template
    root.mkdir(parents=True, exist_ok=True)
    for name in ("origin.git", "app"):
        shutil.copytree(template / name, root / name, symlinks=True)
    config = root / "app" / ".git" / "config"
    config.write_text(config.read_text(encoding="utf-8").replace(str(template), str(root)), encoding="utf-8")
    return root / "app"


def _git_dir(path: Path) -> Path:
    dot = path / ".git"
    if dot.is_dir():
        return dot
    found = dot.read_text(encoding="utf-8").strip()
    assert found.startswith("gitdir: "), found
    gitdir = Path(found[len("gitdir: "):])
    return gitdir if gitdir.is_absolute() else (path / gitdir).resolve()


def head_of(path: Path) -> Optional[str]:
    """``git rev-parse HEAD`` of a repository or worktree, read from its
    files (a loose ref or ``packed-refs``); ``None`` when it cannot say."""
    try:
        gitdir = _git_dir(Path(path))
        head = (gitdir / "HEAD").read_text(encoding="utf-8").strip()
        if not head.startswith("ref: "):
            return head or None
        ref = head[len("ref: "):]
        common = gitdir / "commondir"
        common_dir = (gitdir / common.read_text(encoding="utf-8").strip()).resolve() if common.is_file() else gitdir
        for base in (gitdir, common_dir):
            loose = base / ref
            if loose.is_file():
                sha = loose.read_text(encoding="utf-8").strip()
                return sha if re.fullmatch(r"[0-9a-f]{40}", sha) else None
        packed = common_dir / "packed-refs"
        if packed.is_file():
            for line in packed.read_text(encoding="utf-8").splitlines():
                sha, _, name = line.partition(" ")
                if name == ref:
                    return sha
    except (OSError, AssertionError):
        return None
    return None


def rev_parse_head(path: Path) -> str:
    return head_of(path) or git(path, "rev-parse", "HEAD")


def give_quick_check(repo: Path) -> None:
    """The repository's ``scripts/quick_check.sh`` (a recorded plan names it;
    Start's precheck refuses a check that is not there)."""
    script = repo / "scripts" / "quick_check.sh"
    if script.exists():
        return
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(f"#!/bin/sh\nexec sh {FAKE_CHECK}\n", encoding="utf-8")
    git(repo, "add", "scripts/quick_check.sh")
    git(repo, "commit", "-m", "quick check")
    git(repo, "push", "origin", "main")


class FakeHand:
    """AG12's ``HubProducer``, grown a real worktree per launch."""

    def __init__(self, db: Any, ledger: Ledger, states: dict[str, dict[str, Any]], repo: Path,
                 working_at_once: int = 6) -> None:
        self.db, self.ledger, self.states, self.repo = db, ledger, states, repo
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self.working_at_once = working_at_once
        self._control_mode = lambda: "yolo"

    def working_count(self) -> int:
        return sum(1 for state in self.states.values() if state.get("state") in ("starting", "working", "waiting"))

    def hand(self, principal: Any, kind: str, item_id: str, **kwargs: Any) -> dict[str, Any]:
        number = len(self.calls) + 1
        self.calls.append((kind, item_id, kwargs))
        launch_id = f"L{number}"
        helper_of = kwargs.get("helper_of")
        if helper_of:
            parent = self.ledger.get(helper_of) or {}
            name = f"{Path(parent['worktree_path']).name}-{number}-helper"
            branch = f"{parent['branch']}-{number}-helper"
            start = str(kwargs.get("start_point") or parent["branch"])
        else:
            spec = program_step_spec(self.db, item_id)
            assert spec is not None
            name, branch, start = spec["name"], spec["branch"], spec.get("start_point") or "main"
        path = self.repo.parent / name
        if not path.exists():
            git(self.repo, "worktree", "add", "-q", "-b", branch, str(path), start)
        elif not kwargs.get("handoff_brief") and not helper_of:
            # The real hand (``AgentHandService``): the item's worktree exists;
            # its earlier agent stopped → Hand again in the same worktree, on
            # its branch; still running → ``worktree_duplicate``.
            earlier = next((row for row in reversed(self.ledger.list())
                            if (row.get("origin_ref") or {}).get("id") == item_id), None)
            if earlier is None or earlier.get("state") not in _STOPPED_LAUNCH_STATES:
                raise AgentHandRefused("worktree_duplicate", f"worktree {name!r} already exists")
        # else PG19: a handoff continues in the same worktree, on its branch
        # (the real hand's Hand again path).
        self.ledger.record({
            "launch_id": launch_id, "state": "registered", "profile_id": kwargs.get("profile") or "claude-default",
            "origin_ref": {"kind": kind, "id": item_id}, "branch": branch, "worktree_path": str(path),
            "helper_of": helper_of, "engine_id": kwargs.get("engine"),
            **({"first_message": kwargs["handoff_brief"]} if kwargs.get("handoff_brief") else {}),
            **({"review": dict(kwargs["review"]), "role": "reviewer"} if helper_of and kwargs.get("review") else {}),
        })
        self.states[launch_id] = {"state": "working", "turn_id": None}
        return {"status": "launched", "launch_id": launch_id, "worktree": {"name": name, "branch": branch}}


class FakeAgent:
    """The step's agent: work, commit, end the turn."""

    def __init__(self, rig: "Rig") -> None:
        self.rig = rig
        self.turns = 0

    def finish(self, launch_id: str, files: dict[str, str], *, message: str = "work") -> str:
        record = self.rig.ledger.get(launch_id)
        path = Path(record["worktree_path"])
        for name, text in files.items():
            target = path / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        git(path, "add", "-A")
        git(path, "commit", "-m", message)
        self.end_turn(launch_id)
        return rev_parse_head(path)

    def end_turn(self, launch_id: str) -> None:
        self.turns += 1
        self.rig.states[launch_id] = {"state": "done", "turn_id": f"turn-{self.turns}"}

    def start_turn(self, launch_id: str) -> None:
        self.rig.states[launch_id] = {"state": "working", "turn_id": None}


class FakeGitHub:
    """``gh`` at the process edge; the follow-through's writes on the launch."""

    def __init__(self, rig: "Rig") -> None:
        self.rig = rig
        self.prs: dict[int, dict[str, Any]] = {}
        self.calls: list[list[str]] = []
        self.ci = "passing"
        #: A PR's own CI rollup (by number), over ``ci``.
        self.ci_by_number: dict[int, str] = {}
        #: The base branch's runs, newest first (``gh run list``; JRN3), as
        #: GitHub answers them: ``{status, conclusion, name, headSha}``.
        self.runs: list[dict[str, Any]] = []
        #: HS-S32: what ``gh pr merge`` of a Program's delivery PR does
        #: (``merged``; ``queued``: it answers yes and the PR stays open;
        #: ``fail``: it answers no; ``raise``: the transport throws) and what
        #: ``gh pr view`` answers (``live``; ``fail``; ``garbage``: not JSON).
        self.merge_mode = "merged"
        self.view_mode = "live"

    def __call__(self, argv: list[str], cwd: Optional[str] = None, **kwargs: Any) -> Any:
        if argv[:1] != ["gh"]:
            if not self.rig.real_git and len(argv) == 5 and argv[1] == "-C" and argv[3:] == ["rev-parse", "HEAD"]:
                head = head_of(Path(argv[2]))
                if head:
                    return SimpleNamespace(returncode=0, stdout=head + "\n", stderr="")
            return _default_runner(argv, cwd=cwd, **kwargs)
        self.calls.append(list(argv))
        if argv[1:3] == ["pr", "create"]:
            number = 100 + len(self.prs) + 1
            branch = argv[argv.index("--head") + 1]
            url = f"https://github.com/acme/app/pull/{number}"
            self.prs[number] = {"number": number, "url": url, "branch": branch, "state": "open", "approved_by": []}
            if "--base" in argv:
                self.prs[number]["base"] = argv[argv.index("--base") + 1]
            if cwd:
                # HS-S32: the PR's head as pushed (the delivery's prepared commit).
                self.prs[number]["head_sha"] = rev_parse_head(Path(cwd))
            return SimpleNamespace(returncode=0, stdout=url + "\n", stderr="")
        if argv[1:3] == ["pr", "view"]:
            return self._view(argv)
        if argv[1:3] == ["pr", "merge"]:
            # HS-S25: a person-gated merge names the PR by its URL.
            target = argv[3]
            number = next(n for n, row in self.prs.items() if row["url"] == target) if target.startswith("https://") \
                else int(target)
            mode = self.merge_mode if str(self.prs[number]["branch"]).endswith("/delivery") else "merged"
            if mode == "raise":
                raise OSError("gh: connection reset")
            if mode == "fail":
                return SimpleNamespace(returncode=1, stdout="", stderr="GraphQL: Base branch was modified")
            if "--match-head-commit" in argv and argv[argv.index("--match-head-commit") + 1] != \
                    self.prs[number].get("head_sha"):
                return SimpleNamespace(returncode=1, stdout="", stderr="Head branch was modified")
            if mode == "merged":
                self.prs[number]["state"] = "merged"
            self.sweep()
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if argv[1:3] == ["run", "list"]:
            import json

            return SimpleNamespace(returncode=0, stdout=json.dumps(self.runs), stderr="")
        return SimpleNamespace(returncode=1, stdout="", stderr="unknown gh call")

    def _view(self, argv: list[str]) -> Any:
        """HS-S32: ``gh pr view <url> --json …`` as GitHub answers it."""
        import json

        if self.view_mode == "fail":
            return SimpleNamespace(returncode=1, stdout="", stderr="HTTP 401: Bad credentials")
        if self.view_mode == "garbage":
            return SimpleNamespace(returncode=0, stdout="<html>rate limited</html>", stderr="")
        pr = next((row for row in self.prs.values() if row["url"] == argv[3]), None)
        if pr is None:
            return SimpleNamespace(returncode=1, stdout="", stderr="no pull requests found")
        return SimpleNamespace(returncode=0, stderr="", stdout=json.dumps({
            "url": pr["url"], "number": pr["number"], "state": str(pr["state"]).upper(),
            "headRefOid": pr.get("head_sha") or "", "baseRefName": pr.get("base") or "main",
            "headRefName": pr["branch"], "isCrossRepository": bool(pr.get("fork"))}))

    #: HS-S25: the gh state of the next review reads ("live" reads them).
    read_state = "live"

    def sweep(self) -> None:
        """What the Heartbeat's follow-through writes: the launch's PR, its
        state, its CI rollup and who approved it. HS-S25: a PR's raw
        ``latest_reviews`` (gh's ``latestReviews``), when a test sets it, goes
        through the real receipt normalization and the real observation;
        otherwise ``approved_by``/``changes_requested`` stand for it."""
        from holdspeak.delivery.follow_through import observe_review
        from holdspeak.delivery.pr_receipts import _approved_by, _changes_requested, read_token, review_quality

        for record in self.rig.ledger.list():
            pr = next((row for row in self.prs.values() if row["branch"] == record.get("branch")), None)
            if pr is None:
                continue
            follow = dict(record.get("follow_through") or {})
            ci = self.ci_by_number.get(pr["number"], self.ci)
            if "latest_reviews" in pr:
                raw = pr["latest_reviews"]
                approved, changes = _approved_by(raw), _changes_requested(raw)
            else:
                approved, changes = list(pr["approved_by"]), list(pr.get("changes_requested") or [])
                raw = ([{"author": {"login": login}, "state": "APPROVED"} for login in approved]
                       + [{"author": {"login": row["login"]}, "state": "CHANGES_REQUESTED"} for row in changes])
            follow["pr"] = {"url": pr["url"], "number": pr["number"], "state": pr["state"], "ci": ci,
                            "approved_by": approved,
                            # JRN14: a review that asks for changes, with its words.
                            **({"changes_requested": changes} if changes else {})}
            follow["pr_state"] = f"pr_{pr['state']}"
            token = read_token()
            head = pr.get("head") or rev_parse_head(Path(record["worktree_path"]))
            row = {"url": pr["url"], "number": pr["number"], "head_sha": head, "approved_by": approved,
                   "changes_requested": changes, "review_read": {"quality": review_quality(raw), "token": token}}
            follow = observe_review(follow, row, {"path": "sweep", "gh_state": self.read_state, "token": token},
                                    at="2026-11-08T00:00:00+00:00")
            self.rig.ledger.update(record["launch_id"], follow_through=follow)


class FakeGate:
    """The gate at the hub edge (``program_runner.HubGate``'s shape): the
    held calls of a launch, and the decisions the engine or his press made."""

    def __init__(self) -> None:
        self.holds: dict[str, list[dict[str, Any]]] = {}
        self.decisions: list[tuple[str, bool, str]] = []

    def hold_commit(self, launch_id: str, proposal_id: str = "gate-1", *, scope: str = "inside",
                    cwd: str = "", head: str = 'git add README.md && git commit -m "Add one line to the README"') -> None:
        self.holds.setdefault(launch_id, []).append({
            "proposal_id": proposal_id, "tool": "Bash", "scope": scope, "commit": True, "cwd": cwd, "head": head})

    def held(self, launch_id: str) -> list[dict[str, Any]]:
        return list(self.holds.get(launch_id, []))

    def propose(self, launch_id: str, command: str, *, worktree: Path, mode: str = "yolo") -> str:
        """One Bash call of a step's agent through the REAL hook verdict
        (``classify_tool_call``) and the REAL tool-gate policy
        (``resolve_policy``) as the hub runs them for a Program step: it is
        held here only when the policy answers ``authorization_required``.
        Returns the policy's outcome."""
        from holdspeak.operation_policy import describe_operation, resolve_policy
        from holdspeak.tool_gate_rules import UNPARSED, classify_tool_call

        verdict = classify_tool_call("Bash", {"command": command}, cwd=str(worktree), root=str(worktree)).to_dict()
        tool_call = {"launch_id": launch_id, "scope": verdict["scope"], "rule": verdict["rule"],
                     "read_rule": verdict["read_rule"], "destructive": verdict.get("destructive", ""),
                     "cwd_inside": "1" if verdict["scope"] == UNPARSED else "", "program_step": "1"}
        operation = describe_operation(
            operation_id=f"op-{len(self.decisions)}", family="tool_gate", effect_class="agent/tool_call_hold",
            actor="agent", destination=str(worktree), data_classes=("tool_arguments_redacted",),
            resource_scope="Bash", fixed_destination=True, consequence="execute_on_approval")
        outcome = resolve_policy(operation, mode=mode, source="config", tool_call=tool_call).outcome
        if outcome == "authorization_required":
            self.holds.setdefault(launch_id, []).append({
                "proposal_id": f"gate-call-{len(self.holds)}", "tool": "Bash", "scope": verdict["scope"],
                "commit": False, "cwd": str(worktree), "head": command})
        return outcome

    def decide(self, proposal_id: str, *, approve: bool, reason: str, principal: Any = None) -> None:
        self.decisions.append((proposal_id, approve, reason))
        for rows in self.holds.values():
            rows[:] = [row for row in rows if row["proposal_id"] != proposal_id]

    def expire(self, launch_id: str) -> None:
        self.holds.pop(launch_id, None)


def local_noon() -> Any:
    """Today 12:00 on the hub's wall clock: outside every default quiet
    hours, so a reach or a recorded answer never depends on the hour the
    test runs (a night run wrote "held for the morning")."""
    from datetime import datetime

    # Naive first, then the zone: on a DST change day (2026-11-01) the offset
    # at 12:00 is not the offset of the hour the test runs.
    return datetime.now().replace(hour=12, minute=0, second=0, microsecond=0).astimezone()


def frozen_quiet_phone(db: Any) -> Any:
    """The hub's Phone service over ``db`` whose quiet hours are read at
    :func:`local_noon` (an explicit instant still reads as given)."""
    from holdspeak.phone.service import default_phone_service

    phone = default_phone_service(db)
    if not getattr(phone, "_quiet_frozen", False):
        read = phone._quiet
        noon = local_noon()
        phone._quiet = lambda at=None: read(at if at is not None else noon)
        phone._quiet_frozen = True
    return phone


class Rig:
    def __init__(self, tmp_path: Path, *, kernel: bool = False, people: Any = None,
                 engines: Any = None, idle: Any = None, working_at_once: int = 6, clock: Any = None,
                 github: bool = True, real_git: bool = False, seed: Optional[Callable[[Path], None]] = None) -> None:
        self.real_git = real_git
        self.db = Database(tmp_path / "hub.db")
        self.repo = make_repo(tmp_path, github=github, seed=seed)
        self.ledger = Ledger()
        self.states: dict[str, dict[str, Any]] = {}
        self.words: dict[str, str] = {}
        self.prompts: list[tuple[str, str]] = []
        self.hand = FakeHand(self.db, self.ledger, self.states, self.repo, working_at_once)
        self.gh = FakeGitHub(self)
        self.agent = FakeAgent(self)
        self.gate = FakeGate()
        self.service = ProgramService(
            self.db, broadcast=self._frame, people=people, engines=engines,
            kernel=None if kernel else (lambda **_kw: None),
            runner=lambda: self.runner, **({"clock": clock} if clock is not None else {}),
            phone=lambda: frozen_quiet_phone(self.db),
        )
        self.frames: list[tuple[str, dict[str, Any]]] = []
        self.review = AgentReviewLoop(
            self.db, self.hand, ledger=self.ledger,
            state_reader=lambda launch_id: str((self.states.get(launch_id) or {}).get("state") or ""),
            commit_reader=lambda record: rev_parse_head(Path(record["worktree_path"])),
            result_reader=self.reviewer_words,
            prompt=lambda launch_id, text: self.prompts.append((launch_id, text)),
        )
        self.runner = ProgramRunner(
            self.service, hand=lambda: self.hand, ledger=lambda: self.ledger,
            launch_state=lambda launch_id: self.states.get(launch_id) or {},
            run=self.gh, prompt=lambda launch_id, text: self.prompts.append((launch_id, text)),
            review_tick=self.review.tick, idle=idle, async_checks=False, review_words=self.reviewer_words,
            gate=self.gate,
        )
        #: The in-memory checkpoint refs (``real_git=False``): ``{ref: commit}``.
        self.pins: dict[str, str] = {}
        if not real_git:
            self.runner.pin_checkpoint = self._pin  # type: ignore[method-assign]
            self.service.checkpoint_reach = self._reach  # type: ignore[method-assign]

    def _pin(self, step: Any, line: str) -> dict[str, Any]:
        """``ProgramRunner.pin_checkpoint`` in memory: the same answers (a
        numbered ref under the step, its commit, tree and parent head, or a
        note), no git."""
        from holdspeak.services.program_runner import CHECKPOINT_REFS

        worktree = str(step.get("worktree") or "")
        step_id = str(step.get("id") or "")
        if not step_id or not worktree or not Path(worktree).is_dir():
            return {"note": "No worktree to pin yet"}
        head = head_of(Path(worktree))
        if not head:
            return {"note": "Not pinned: the worktree has no commit git can read"}
        prefix = f"{CHECKPOINT_REFS}/{step_id}/"
        n = max((int(ref[len(prefix):]) for ref in self.pins if ref.startswith(prefix)), default=0) + 1
        ref = f"{prefix}{n}"
        commit = hashlib.sha1(f"commit {ref} {head} {line}".encode()).hexdigest()
        tree = hashlib.sha1(f"tree {ref} {head}".encode()).hexdigest()
        self.pins[ref] = commit
        return {"ref": ref, "n": n, "commit": commit, "tree": tree, "head": head}

    def _reach(self, rows: list[dict[str, Any]], repo_root: Optional[str]) -> list[dict[str, Any]]:
        """``ProgramService.checkpoint_reach`` over the in-memory refs (the
        product's projection; only the ``for-each-ref`` read is in memory)."""
        from holdspeak.services.program_checkpoint_reach import project

        def run(_argv: list[str], **_kwargs: Any) -> Any:
            return SimpleNamespace(returncode=0, stderr="",
                                   stdout="".join(f"{ref} {commit}\n" for ref, commit in self.pins.items()))

        return project(rows, repo_root, run)

    def reviewer_words(self, launch_id: str) -> str:
        """The fake reviewer's words (see the module note on REQ lines)."""
        words = self.words.get(launch_id, "")
        if not words:
            return words
        if "REQ" not in words:
            acceptance = ((self.ledger.get(launch_id) or {}).get("review") or {}).get("acceptance") or []
            asked = [found.group(1) for line in acceptance for found in [re.match(r"^R(\d+) · ", str(line))] if found]
            words = words + "".join(f"\nREQ R{n}: MET · the fake reviewer finds it holds" for n in asked)
        # The review brief asks for the REVIEW RESULT block (Astra post-merge
        # 2026-11-01); the fake reviewer writes it as told, unless a test
        # types its own block (or none, by ``NO_BLOCK``).
        if "REVIEW RESULT" in words or words.startswith(NO_BLOCK):
            return words.removeprefix(NO_BLOCK)
        return f"REVIEW RESULT\n{words}\nEND REVIEW RESULT"

    def _frame(self, frame: str, payload: Any) -> None:
        self.frames.append((frame, dict(payload)))

    def tick(self, n: int = 1) -> None:
        for _ in range(n):
            self.gh.sweep()
            self.runner.tick()

    def program(self, program_id: str) -> dict[str, Any]:
        return self.service.get(OWNER, program_id)

    def step(self, program_id: str, ordinal: int, *, contender: int = 0) -> dict[str, Any]:
        steps = self.program(program_id)["steps"]
        row = next(step for step in steps if step["ordinal"] == ordinal)
        return row["contenders"][contender - 1] if contender else row

    def note(self, program_id: str) -> str:
        note = self.db.notes.get(f"program-{program_id}")
        return note.body_markdown if note is not None else ""


class QuestionClient:
    """A face producer reads question custody before its real HTTP press.

    Security tests use the raw TestClient to exercise omission. No answer body
    is fabricated here: bindings and proposal IDs come from the real service.
    """
    def __init__(self, client, rig):
        self.client, self.rig = client, rig

    def request(self, method, path, **kw):
        import re
        from holdspeak.program_operations import PROGRAM_OPERATIONS
        for op in PROGRAM_OPERATIONS:
            if not op.question_binding or not op.http or op.http[0] != method.upper():
                continue
            pattern = re.sub(r"\{([^}]+)\}", r"(?P<\1>[^/]+)", op.http[1])
            match = re.fullmatch(pattern, str(path))
            if not match:
                continue
            params = match.groupdict()
            pid, sid = params["program_id"], params.get("step_id", "")
            if sid == "program": sid = ""
            if "requirement_id" in params:
                row = self.rig.service._requirement(self.rig.service._program(pid), params["requirement_id"])
                sid = str(row.get("step_id") or "")
            body = dict(kw.pop("json", None) or {})
            body.setdefault("binding", self.rig.service._answer_binding(self.rig.service._program(pid), self.rig.service.store.get_step(sid) if sid else None))
            if op.name == "program.text_apply" and body.get("allow_lower") and "proposal_id" not in body:
                preview = self.rig.service.text_apply(OWNER,pid,body.get("text"),base=body.get("base"))
                body["proposal_id"] = preview["proposal_id"]
            kw["json"] = body
            break
        return self.client.request(method,path,**kw)

    def post(self,path,**kw): return self.request("POST",path,**kw)
    def delete(self,path,**kw): return self.request("DELETE",path,**kw)
    def __getattr__(self,name): return getattr(self.client,name)
