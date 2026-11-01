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
  missing answer writes its own ``REQ`` lines.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Optional

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.agent_hand_service import _STOPPED_LAUNCH_STATES, AgentHandRefused, program_step_spec
from holdspeak.services.agent_review import AgentReviewLoop
from holdspeak.services.program_runner import ProgramRunner, _default_runner
from holdspeak.services.program_service import ProgramService
from tests.unit.test_agent_review import Ledger

OWNER = Principal(PrincipalKind.OWNER, "owner-session")
FAKE_CHECK = Path(__file__).resolve().parents[1] / "fixtures" / "fake_program_check.sh"


def git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
    assert proc.returncode == 0, (args, proc.stderr)
    return proc.stdout.strip()


def make_repo(root: Path) -> Path:
    origin = root / "origin.git"
    subprocess.run(["git", "init", "--bare", "-b", "main", str(origin)], capture_output=True, check=True)
    repo = root / "app"
    repo.mkdir(parents=True)
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "test@example.test")
    git(repo, "config", "user.name", "Test")
    (repo / "README.md").write_text("# app\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "seed")
    git(repo, "remote", "add", "origin", str(origin))
    git(repo, "push", "-u", "origin", "main")
    return repo


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
            git(self.repo, "worktree", "add", "-b", branch, str(path), start)
            git(path, "config", "user.email", "agent@example.test")
            git(path, "config", "user.name", "Agent")
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
        return git(path, "rev-parse", "HEAD")

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

    def __call__(self, argv: list[str], cwd: Optional[str] = None, **kwargs: Any) -> Any:
        if argv[:1] != ["gh"]:
            return _default_runner(argv, cwd=cwd, **kwargs)
        self.calls.append(list(argv))
        if argv[1:3] == ["pr", "create"]:
            number = 100 + len(self.prs) + 1
            branch = argv[argv.index("--head") + 1]
            url = f"https://github.com/acme/app/pull/{number}"
            self.prs[number] = {"number": number, "url": url, "branch": branch, "state": "open", "approved_by": []}
            return SimpleNamespace(returncode=0, stdout=url + "\n", stderr="")
        if argv[1:3] == ["pr", "merge"]:
            number = int(argv[3])
            self.prs[number]["state"] = "merged"
            self.sweep()
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=1, stdout="", stderr="unknown gh call")

    def sweep(self) -> None:
        """What the Heartbeat's follow-through writes: the launch's PR, its
        state, its CI rollup and who approved it."""
        for record in self.rig.ledger.list():
            pr = next((row for row in self.prs.values() if row["branch"] == record.get("branch")), None)
            if pr is None:
                continue
            follow = dict(record.get("follow_through") or {})
            ci = self.ci_by_number.get(pr["number"], self.ci)
            follow["pr"] = {"url": pr["url"], "number": pr["number"], "state": pr["state"], "ci": ci,
                            "approved_by": list(pr["approved_by"])}
            follow["pr_state"] = f"pr_{pr['state']}"
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
                 engines: Any = None, idle: Any = None, working_at_once: int = 6, clock: Any = None) -> None:
        self.db = Database(tmp_path / "hub.db")
        self.repo = make_repo(tmp_path)
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
            commit_reader=lambda record: git(Path(record["worktree_path"]), "rev-parse", "HEAD"),
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

    def reviewer_words(self, launch_id: str) -> str:
        """The fake reviewer's words (see the module note on REQ lines)."""
        words = self.words.get(launch_id, "")
        if not words or "REQ" in words:
            return words
        acceptance = ((self.ledger.get(launch_id) or {}).get("review") or {}).get("acceptance") or []
        asked = [found.group(1) for line in acceptance for found in [re.match(r"^R(\d+) · ", str(line))] if found]
        return words + "".join(f"\nREQ R{n}: MET · the fake reviewer finds it holds" for n in asked)

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
