"""PR receipts (HS-104-04) — paying the Phase-94 candidate-Y deferral.

Read-only GitHub PR rows for REGISTERED delivery sources only, in the
Phase-86 `gh` mold: one batched `gh pr list` call per source, never a
subprocess per PR, never a forge abstraction. Every row carries its
`observed_at` (a receipt says when it observed; a dashboard implies
now) and a typed freshness — a failing poll degrades to `stale` with
the last-known-good rows retained, never a silent freeze.

Attribution wears its epistemics (the council's riskiest-assumption
warning): `exact` only when the PR's head SHA or exact branch matches
a registered worktree; `heuristic` when a Work attempt's story id
merely appears in the branch name (the row must never claim more than
the match proves); otherwise unattributed.

Egress: the batched `gh` call here and the EXPLICIT `git fetch` verb
are the only network touches; the grep census pins both
(tests/unit/test_pr_receipts.py). Refresh is manual (the surface
verb) or by a per-source `pr_refresh_seconds` cadence explicitly set
in the registry entry — never ambient.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

GH_TIMEOUT_SECONDS = 30
GIT_TIMEOUT_SECONDS = 30
MAX_PRS_PER_SOURCE = 50
MAX_DIFF_BYTES = 512 * 1024

#: The one batched query's fields — the row schema is exactly this.
GH_FIELDS = "number,title,url,headRefName,baseRefName,headRefOid,baseRefOid,state,isDraft,statusCheckRollup,author"

Runner = Callable[..., "subprocess.CompletedProcess[str]"]


def _default_runner(argv: list[str], cwd: Optional[str] = None):
    return subprocess.run(
        argv,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=GH_TIMEOUT_SECONDS,
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def rollup_conclusion(status_check_rollup: Any) -> str:
    """The conclusion, not the logs: failing > pending > passing >
    none. One word a station light can wear."""
    if not isinstance(status_check_rollup, list) or not status_check_rollup:
        return "none"
    states = set()
    for check in status_check_rollup:
        if not isinstance(check, dict):
            continue
        conclusion = str(
            check.get("conclusion") or check.get("state") or ""
        ).upper()
        states.add(conclusion)
    if {"FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED"} & states:
        return "failing"
    if {"", "PENDING", "IN_PROGRESS", "QUEUED", "EXPECTED"} & states:
        return "pending"
    if {"SUCCESS", "NEUTRAL", "SKIPPED", "COMPLETED"} & states:
        return "passing"
    return "none"


def pr_state(raw_state: Any, is_draft: Any) -> str:
    state = str(raw_state or "").lower()
    if state == "open" and bool(is_draft):
        return "draft"
    if state in ("open", "merged", "closed"):
        return state
    return "closed"


_STORY_ID = re.compile(r"[a-z]+-\d+-\d+")


def attribute(
    head_ref: str,
    head_sha: str,
    *,
    worktree_branches: list[str],
    worktree_heads: list[str],
    attempt_story_ids: list[str],
) -> dict[str, Any]:
    """`{"attribution": exact|heuristic|none, "basis": <one line>}`.

    Exact demands identity: the PR's head SHA is a registered
    worktree's HEAD, or its branch name is exactly a registered
    worktree's branch. Heuristic is a NAME resemblance only — a Work
    attempt's story id appearing inside the branch — and says so.
    """
    if head_sha and head_sha in worktree_heads:
        return {"attribution": "exact", "basis": "head SHA matches a registered worktree"}
    if head_ref and head_ref in worktree_branches:
        return {"attribution": "exact", "basis": "branch matches a registered worktree"}
    branch_lower = (head_ref or "").lower()
    for story_id in attempt_story_ids:
        needle = story_id.strip().lower()
        if needle and needle in branch_lower:
            return {
                "attribution": "heuristic",
                "basis": f"branch name resembles {story_id} (name match only)",
            }
    return {"attribution": "none", "basis": "no worktree or attempt match"}


def order_key(row: dict[str, Any]) -> tuple[int, int]:
    """Needs-you-first: open failing CI, then open pending, then open
    green, then draft, then merged/closed (quiet). Number descending
    inside a band."""
    state = row.get("state")
    ci = row.get("ci")
    if state == "open":
        band = {"failing": 0, "pending": 1}.get(str(ci), 2)
    elif state == "draft":
        band = 3
    else:
        band = 4
    return (band, -int(row.get("number") or 0))


@dataclass
class _SourcestatePr:
    rows: Optional[list[dict[str, Any]]] = None  # None = never observed
    status: str = "unavailable"
    detail: str = "not yet collected"
    observed_at: str = ""
    refreshed_monotonic: float = float("-inf")


class PrReceiptsService:
    """Cached PR rows per registered source. Reads never shell out;
    only `refresh()` (the surface verb) or an explicitly configured
    per-source cadence runs `gh`."""

    def __init__(
        self,
        registry: Any,
        *,
        runner: Optional[Runner] = None,
        clock: Callable[[], float] = time.monotonic,
        gh_available: Optional[Callable[[], bool]] = None,
    ) -> None:
        self._registry = registry
        self._runner = runner or _default_runner
        self._clock = clock
        self._gh_available = gh_available or (lambda: shutil.which("gh") is not None)
        self._lock = threading.Lock()
        self._states: dict[str, _SourcestatePr] = {}

    # ── reads (never shell) ─────────────────────────────────────────

    def rows_view(
        self, attempt_story_ids: Optional[list[str]] = None
    ) -> dict[str, Any]:
        with self._lock:
            sources = []
            for source in self._registry.sources():
                state = self._states.get(source.source_id, _SourcestatePr())
                sources.append(
                    {
                        "source_id": source.source_id,
                        "label": source.label,
                        "status": state.status,
                        "detail": state.detail,
                        "observed_at": state.observed_at,
                        # None only when never observed (the §13 rule).
                        "prs": None if state.rows is None else sorted(state.rows, key=order_key),
                    }
                )
        return {"pr_receipts_schema": 1, "sources": sources}

    # ── the explicit verb / the explicit cadence ────────────────────

    def refresh(
        self,
        source_id: Optional[str] = None,
        *,
        attempt_story_ids: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """One batched `gh` call per (selected) source — the one
        ambient-forbidden egress, run only from here."""
        for source in self._registry.sources():
            if source_id is not None and source.source_id != source_id:
                continue
            self._refresh_source(source, attempt_story_ids or [])
        return self.rows_view()

    def maybe_cadence_refresh(
        self, attempt_story_ids: Optional[list[str]] = None
    ) -> None:
        """Only sources whose registry entry explicitly set
        `pr_refresh_seconds` refresh here; everyone else waits for the
        verb. Never ambient by default."""
        now = self._clock()
        for source in self._registry.sources():
            cadence = getattr(source, "pr_refresh_seconds", None)
            if not cadence:
                continue
            with self._lock:
                state = self._states.setdefault(source.source_id, _SourcestatePr())
                due = (now - state.refreshed_monotonic) >= float(cadence)
            if due:
                self._refresh_source(source, attempt_story_ids or [])

    def _refresh_source(self, source: Any, attempt_story_ids: list[str]) -> None:
        with self._lock:
            state = self._states.setdefault(source.source_id, _SourcestatePr())
            state.refreshed_monotonic = self._clock()
        root = source.primary_path
        if not root:
            self._degrade(source.source_id, "source has no local worktree")
            return
        if not self._gh_available():
            self._degrade(source.source_id, "gh CLI is not installed")
            return
        argv = [
            "gh", "pr", "list", "--state", "all",
            "--limit", str(MAX_PRS_PER_SOURCE),
            "--json", GH_FIELDS,
        ]
        try:
            proc = self._runner(argv, str(root))
        except subprocess.TimeoutExpired:
            self._degrade(source.source_id, "gh timed out")
            return
        except OSError:
            self._degrade(source.source_id, "gh failed to start")
            return
        if proc.returncode != 0:
            self._degrade(source.source_id, f"gh exited {proc.returncode}")
            return
        try:
            raw = json.loads(proc.stdout)
        except (json.JSONDecodeError, ValueError):
            self._degrade(source.source_id, "gh did not return JSON")
            return
        if not isinstance(raw, list):
            self._degrade(source.source_id, "gh returned an unexpected shape")
            return

        worktree_branches = [wt.branch for wt in source.worktrees if wt.branch]
        worktree_heads = self._worktree_heads(source)
        observed = _utc_now()
        rows = []
        for pr in raw:
            if not isinstance(pr, dict):
                continue
            head_ref = str(pr.get("headRefName") or "")
            head_sha = str(pr.get("headRefOid") or "")
            rows.append(
                {
                    "source_id": source.source_id,
                    "number": int(pr.get("number") or 0),
                    "title": str(pr.get("title") or ""),
                    "url": str(pr.get("url") or ""),
                    "head_ref": head_ref,
                    "base_ref": str(pr.get("baseRefName") or ""),
                    "head_sha": head_sha,
                    "base_sha": str(pr.get("baseRefOid") or ""),
                    "state": pr_state(pr.get("state"), pr.get("isDraft")),
                    "ci": rollup_conclusion(pr.get("statusCheckRollup")),
                    "author": str((pr.get("author") or {}).get("login") or ""),
                    "observed_at": observed,
                    **attribute(
                        head_ref,
                        head_sha,
                        worktree_branches=worktree_branches,
                        worktree_heads=worktree_heads,
                        attempt_story_ids=attempt_story_ids,
                    ),
                }
            )
        with self._lock:
            state = self._states[source.source_id]
            state.rows = rows
            state.status = "live"
            state.detail = ""
            state.observed_at = observed

    def _degrade(self, source_id: str, detail: str) -> None:
        """Last-known-good retained; the status names the failure."""
        with self._lock:
            state = self._states.setdefault(source_id, _SourcestatePr())
            state.status = "stale" if state.rows is not None else "unavailable"
            state.detail = detail

    def _worktree_heads(self, source: Any) -> list[str]:
        heads = []
        for wt in source.worktrees:
            sha = self._git(["rev-parse", "HEAD"], wt.path)
            if sha:
                heads.append(sha)
        return heads

    # ── the diff verb (local, read-only) ────────────────────────────

    def diff(self, source_id: str, number: int) -> dict[str, Any]:
        """`base...head` from the mapped worktree, LOCAL only. Missing
        SHAs are an honest absence plus the explicit-fetch offer —
        never an implicit fetch (fetch is egress)."""
        source, row = self._find(source_id, number)
        if row is None:
            return {"status": "unknown_pr"}
        root = source.primary_path
        if not root:
            return {"status": "absent", "detail": "source has no local worktree"}
        head, base = row.get("head_sha") or "", row.get("base_sha") or ""
        if not head:
            return {"status": "absent", "detail": "no head SHA on the receipt"}
        missing = [
            sha for sha in (base, head)
            if sha and (self._git(["cat-file", "-t", sha], root) or "").strip() != "commit"
        ]
        if missing:
            return {
                "status": "absent",
                "detail": "commits are not in the local checkout",
                "offer_fetch": True,  # fetch is egress; it stays an explicit act
            }
        spec = f"{base}...{head}" if base else head
        diff_text = self._git(["diff", spec], root, max_bytes=MAX_DIFF_BYTES)
        if diff_text is None:
            return {"status": "absent", "detail": "git diff failed"}
        return {"status": "ok", "spec": spec, "diff": diff_text}

    def fetch(self, source_id: str, number: int) -> dict[str, Any]:
        """The explicit egress act the absence offers."""
        source, row = self._find(source_id, number)
        if row is None:
            return {"status": "unknown_pr"}
        root = source.primary_path
        if not root:
            return {"status": "absent", "detail": "source has no local worktree"}
        result = self._git(
            ["fetch", "origin", row.get("head_sha") or "", row.get("base_sha") or ""],
            root,
        )
        if result is None:
            return {"status": "failed", "detail": "git fetch failed"}
        return {"status": "ok"}

    def _find(self, source_id: str, number: int):
        for source in self._registry.sources():
            if source.source_id != source_id:
                continue
            with self._lock:
                state = self._states.get(source_id)
                rows = state.rows if state else None
            for row in rows or []:
                if row.get("number") == number:
                    return source, row
            return source, None
        return None, None

    def _git(
        self, args: list[str], cwd: str, *, max_bytes: int = 65536
    ) -> Optional[str]:
        try:
            proc = self._runner(["git", *[a for a in args if a]], str(cwd))
        except (subprocess.TimeoutExpired, OSError):
            return None
        if proc.returncode != 0:
            return None
        return (proc.stdout or "")[:max_bytes]
