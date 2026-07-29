"""HS-104-04 — PR receipts: mapping, attribution epistemics, ordering,
the honest-stale path, poll economy, the local diff, and the egress
census."""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pytest

from holdspeak.delivery.pr_receipts import (
    PrReceiptsService,
    attribute,
    order_key,
    pr_state,
    rollup_conclusion,
)

REPO = Path(__file__).resolve().parents[2]


@dataclass
class FakeWorktree:
    path: str
    branch: str
    worktree_id: str = "wt_1"


@dataclass
class FakeSource:
    source_id: str = "src_1"
    label: str = "holdspeak"
    worktrees: list = field(default_factory=list)
    pr_refresh_seconds: Optional[float] = None

    @property
    def primary_path(self) -> Optional[str]:
        return self.worktrees[0].path if self.worktrees else None


class FakeRegistry:
    def __init__(self, *sources):
        self._sources = list(sources)

    def sources(self):
        return list(self._sources)


GH_FIXTURE = [
    {
        "number": 42,
        "title": "HS-104-02: the tool-call gate",
        "url": "https://github.com/o/r/pull/42",
        "headRefName": "agent/hs-104-02-tool-call-gate",
        "baseRefName": "main",
        "headRefOid": "a" * 40,
        "baseRefOid": "b" * 40,
        "state": "OPEN",
        "isDraft": False,
        "statusCheckRollup": [{"conclusion": "FAILURE"}, {"conclusion": "SUCCESS"}],
        "author": {"login": "karolswdev"},
    },
    {
        "number": 41,
        "title": "green one",
        "url": "https://github.com/o/r/pull/41",
        "headRefName": "feature/nice",
        "baseRefName": "main",
        "headRefOid": "c" * 40,
        "baseRefOid": "b" * 40,
        "state": "OPEN",
        "isDraft": False,
        "statusCheckRollup": [{"conclusion": "SUCCESS"}],
        "author": {"login": "someone"},
    },
    {
        "number": 40,
        "title": "drafty",
        "url": "https://github.com/o/r/pull/40",
        "headRefName": "wip",
        "baseRefName": "main",
        "headRefOid": "d" * 40,
        "state": "OPEN",
        "isDraft": True,
        "statusCheckRollup": [],
        "author": {"login": "someone"},
    },
    {
        "number": 39,
        "title": "shipped",
        "url": "https://github.com/o/r/pull/39",
        "headRefName": "old",
        "baseRefName": "main",
        "headRefOid": "e" * 40,
        "state": "MERGED",
        "isDraft": False,
        "statusCheckRollup": [{"conclusion": "SUCCESS"}],
        "author": {"login": "someone"},
    },
]


def make_runner(git_head: str = "f" * 40, gh_rc: int = 0, gh_out: str | None = None):
    calls: list[list[str]] = []

    def runner(argv, cwd=None):
        calls.append(list(argv))
        if argv[0] == "gh":
            out = gh_out if gh_out is not None else json.dumps(GH_FIXTURE)
            return subprocess.CompletedProcess(argv, gh_rc, out, "")
        if argv[:2] == ["git", "rev-parse"]:
            return subprocess.CompletedProcess(argv, 0, git_head + "\n", "")
        if argv[:2] == ["git", "cat-file"]:
            return subprocess.CompletedProcess(argv, 0, "commit\n", "")
        if argv[:2] == ["git", "diff"]:
            return subprocess.CompletedProcess(argv, 0, "diff --git a/x b/x\n", "")
        if argv[:2] == ["git", "fetch"]:
            return subprocess.CompletedProcess(argv, 0, "", "")
        return subprocess.CompletedProcess(argv, 1, "", "unknown")

    runner.calls = calls
    return runner


def make_service(source=None, runner=None, clock=None):
    source = source or FakeSource(worktrees=[FakeWorktree(path="/tmp/repo", branch="main")])
    ticker = {"now": 0.0}
    service = PrReceiptsService(
        FakeRegistry(source),
        runner=runner or make_runner(),
        clock=(clock or (lambda: ticker["now"])),
        gh_available=lambda: True,
        gate_matcher=lambda _path: True,
    )
    return service, source, ticker


# ── pure helpers ─────────────────────────────────────────────────────


def test_rollup_conclusion_bands() -> None:
    assert rollup_conclusion([{"conclusion": "FAILURE"}, {"conclusion": "SUCCESS"}]) == "failing"
    assert rollup_conclusion([{"conclusion": ""}, {"conclusion": "SUCCESS"}]) == "pending"
    assert rollup_conclusion([{"conclusion": "SUCCESS"}]) == "passing"
    assert rollup_conclusion([]) == "none"
    assert rollup_conclusion(None) == "none"


def test_pr_state_mapping() -> None:
    assert pr_state("OPEN", True) == "draft"
    assert pr_state("OPEN", False) == "open"
    assert pr_state("MERGED", False) == "merged"
    assert pr_state("CLOSED", False) == "closed"


def test_attribution_matrix_never_claims_more_than_the_match() -> None:
    exact_sha = attribute("x", "s1", worktree_branches=[], worktree_heads=["s1"], attempt_story_ids=[])
    assert exact_sha["attribution"] == "exact"
    exact_branch = attribute("agent/x", "", worktree_branches=["agent/x"], worktree_heads=[], attempt_story_ids=[])
    assert exact_branch["attribution"] == "exact"
    heuristic = attribute(
        "agent/hs-104-02-gate", "zz",
        worktree_branches=["main"], worktree_heads=["s1"],
        attempt_story_ids=["HS-104-02"],
    )
    assert heuristic["attribution"] == "heuristic"
    assert "name match only" in heuristic["basis"]
    none = attribute("random", "zz", worktree_branches=["main"], worktree_heads=["s1"], attempt_story_ids=["HS-1-1"])
    assert none["attribution"] == "none"


def test_ordering_needs_you_first() -> None:
    rows = [
        {"state": "merged", "ci": "passing", "number": 39},
        {"state": "open", "ci": "passing", "number": 41},
        {"state": "draft", "ci": "none", "number": 40},
        {"state": "open", "ci": "failing", "number": 42},
    ]
    ordered = sorted(rows, key=order_key)
    assert [r["number"] for r in ordered] == [42, 41, 40, 39]


# ── the service ──────────────────────────────────────────────────────


def test_refresh_maps_the_batched_payload_with_observed_at() -> None:
    service, source, _ = make_service()
    view = service.refresh(attempt_story_ids=["HS-104-02"])
    src = view["sources"][0]
    assert src["status"] == "live"
    rows = src["prs"]
    assert [r["number"] for r in rows] == [42, 41, 40, 39]  # needs-you-first
    top = rows[0]
    assert top["state"] == "open" and top["ci"] == "failing"
    assert top["attribution"] == "heuristic"  # story id in the branch name
    assert top["observed_at"].endswith("Z")
    assert top["author"] == "karolswdev"


def test_one_gh_call_per_source_never_per_pr() -> None:
    runner = make_runner()
    service, _, _ = make_service(runner=runner)
    service.refresh()
    gh_calls = [c for c in runner.calls if c[0] == "gh"]
    assert len(gh_calls) == 1


def test_failing_gh_degrades_to_stale_and_recovers() -> None:
    good = make_runner()
    service, source, _ = make_service(runner=good)
    service.refresh()

    def bad_runner(argv, cwd=None):
        if argv[0] == "gh":
            raise subprocess.TimeoutExpired(argv, 1)
        return good(argv, cwd)

    service._runner = bad_runner
    view = service.refresh()
    src = view["sources"][0]
    assert src["status"] == "stale"  # never a silent freeze
    assert src["detail"] == "gh timed out"
    assert src["prs"] is not None  # last-known-good retained
    assert src["observed_at"]  # still the honest last observation

    service._runner = good
    recovered = service.refresh()
    assert recovered["sources"][0]["status"] == "live"


def test_action_verbs_name_availability_and_refusal() -> None:
    source = FakeSource(
        worktrees=[FakeWorktree(path="/tmp/repo", branch="agent/hs-104-02-tool-call-gate")]
    )
    service, _, _ = make_service(source=source, runner=make_runner(git_head="a" * 40))
    row = service.refresh()["sources"][0]["prs"][0]
    assert row["needs_you"] is True
    assert row["worktree_id"] == "wt_1"
    assert all(item["available"] for item in row["verbs"].values())

    calls = make_runner(git_head="a" * 40)

    def yanked(argv, cwd=None):
        if argv[0] == "gh":
            return subprocess.CompletedProcess(argv, 1, "", "authentication token missing; run gh auth login")
        return calls(argv, cwd)

    service._runner = yanked
    stale = service.refresh()["sources"][0]
    assert stale["status"] == "stale"
    assert stale["detail"] == "gh credentials unavailable"
    retained = stale["prs"][0]
    assert retained["verbs"]["send_agent"]["available"] is True
    assert retained["verbs"]["post_comment"] == {
        "available": False,
        "reason": "gh credentials unavailable",
    }


def test_matched_ungated_row_refuses_agent_and_names_truth() -> None:
    source = FakeSource(
        worktrees=[FakeWorktree(path="/tmp/repo", branch="agent/hs-104-02-tool-call-gate")]
    )
    service = PrReceiptsService(
        FakeRegistry(source),
        runner=make_runner(git_head="a" * 40),
        gh_available=lambda: True,
        gate_matcher=lambda _path: False,
    )
    row = service.refresh()["sources"][0]["prs"][0]
    assert row["agent_gate"] == "ungated"
    assert row["verbs"]["send_agent"] == {
        "available": False,
        "reason": "not gated",
    }
    assert row["verbs"]["draft_review"]["available"] is True


def test_unmatched_row_keeps_all_verbs_and_names_worktree_refusal() -> None:
    service, _, _ = make_service()
    row = service.refresh()["sources"][0]["prs"][0]
    assert row["verbs"]["send_agent"] == {
        "available": False,
        "reason": "no matching worktree",
    }
    assert row["verbs"]["draft_review"]["reason"] == "no matching worktree"
    assert row["verbs"]["post_comment"]["available"] is True


def test_never_observed_is_none_not_empty() -> None:
    service, _, _ = make_service()
    src = service.rows_view()["sources"][0]
    assert src["prs"] is None
    assert src["status"] == "unavailable"


def test_reads_never_shell_and_cadence_is_opt_in() -> None:
    runner = make_runner()
    service, source, ticker = make_service(runner=runner)
    service.rows_view()
    service.maybe_cadence_refresh()
    assert runner.calls == []  # no cadence configured: reads are silent

    source.pr_refresh_seconds = 30.0
    service.maybe_cadence_refresh()
    assert any(c[0] == "gh" for c in runner.calls)  # explicitly enabled
    count = len([c for c in runner.calls if c[0] == "gh"])
    ticker["now"] += 5.0
    service.maybe_cadence_refresh()
    assert len([c for c in runner.calls if c[0] == "gh"]) == count  # inside the window
    ticker["now"] += 31.0
    service.maybe_cadence_refresh()
    assert len([c for c in runner.calls if c[0] == "gh"]) == count + 1


def test_diff_local_and_honest_absence_with_fetch_offer() -> None:
    service, _, _ = make_service()
    service.refresh()
    ok = service.diff("src_1", 42)
    assert ok["status"] == "ok"
    assert ok["spec"] == "b" * 40 + "..." + "a" * 40
    assert ok["diff"].startswith("diff --git")

    def no_object_runner(argv, cwd=None):
        if argv[:2] == ["git", "cat-file"]:
            return subprocess.CompletedProcess(argv, 1, "", "missing")
        return make_runner()(argv, cwd)

    service._runner = no_object_runner
    absent = service.diff("src_1", 42)
    assert absent["status"] == "absent"
    assert absent["offer_fetch"] is True  # fetch stays an explicit act

    assert service.diff("src_1", 999)["status"] == "unknown_pr"


def test_egress_census_gh_and_fetch_only() -> None:
    """The grep census: `gh` is named only in pr_receipts (this
    delivery package's one collector egress) and the fetch verb is
    the one git-network call."""
    pkg = REPO / "holdspeak" / "delivery"
    gh_files = set()
    for path in pkg.glob("*.py"):
        code = "\n".join(
            line for line in path.read_text(encoding="utf-8").splitlines()
            if not line.lstrip().startswith("#")
        )
        if '"gh"' in code or "'gh'" in code:
            gh_files.add(path.name)
    assert gh_files == {"pr_receipts.py"}

    text = (pkg / "pr_receipts.py").read_text(encoding="utf-8")
    assert text.count('"fetch"') == 1  # one explicit egress verb
