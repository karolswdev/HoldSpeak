"""HS-173-03 / HS-173-05 -- Room health signal derivations.

Pure functions that derive health signals from Watch snapshot entities
and CI history.  No `gh` calls, no writes, no side-effects.  Every
function returns a typed dict that the Room read and the face consume.

Vocabulary (design addendum C1): REVIEW WAIT (days from createdAt),
never REVIEW LATENCY.  Tones: green | amber | red.

A signal is ``present: True`` whenever its SOURCE has entities and
``present: False`` only when the source has none (design addendum C2).
"""
from __future__ import annotations

import statistics
from datetime import datetime, timezone
from typing import Any


# ── review_wait ──────────────────────────────────────────────────────

def review_wait(
    entities: list[dict[str, Any]],
    now: datetime | None = None,
) -> dict[str, Any]:
    """Derive review-wait signal from PR entities.

    An entity is "waiting" when it is OPEN, has non-empty reviewRequests,
    and reviewDecision is null or REVIEW_REQUIRED.  Wait = now - createdAt
    in fractional days.

    Returns::

        {
            "present": bool,       # source has waiting PRs
            "median_days": float,  # overall median wait (days)
            "waiting_count": int,  # number of PRs waiting
            "per_reviewer": [      # per-reviewer breakdown
                {"login": str, "median_days": float, "count": int},
                ...
            ],
        }
    """
    if now is None:
        now = datetime.now(timezone.utc)
    now_naive = now.replace(tzinfo=None)

    # Collect waits per reviewer
    reviewer_waits: dict[str, list[float]] = {}
    all_waits: list[float] = []

    for entity in entities:
        state = str(entity.get("state") or "").upper()
        if state != "OPEN":
            continue
        review_requests = (
            entity.get("review_requests")
            or entity.get("reviewRequests")
            or []
        )
        if not review_requests:
            continue
        review_decision = str(
            entity.get("review_decision")
            or entity.get("reviewDecision")
            or ""
        ).upper()
        if review_decision and review_decision not in ("", "REVIEW_REQUIRED"):
            continue

        created_at_str = entity.get("created_at") or entity.get("createdAt") or ""
        if not created_at_str:
            continue
        try:
            created_dt = datetime.fromisoformat(
                str(created_at_str).replace("Z", "+00:00")
            ).replace(tzinfo=None)
        except (ValueError, TypeError):
            continue

        wait_days = max(0.0, (now_naive - created_dt).total_seconds() / 86400)
        all_waits.append(wait_days)

        for login in review_requests:
            login_str = str(login).strip().lower()
            if not login_str:
                continue
            reviewer_waits.setdefault(login_str, []).append(wait_days)

    if not all_waits:
        return {
            "present": False,
            "tone": "green",
            "median_days": 0.0,
            "waiting_count": 0,
            "per_reviewer": [],
        }

    per_reviewer = sorted(
        [
            {
                "login": login,
                "median_days": round(statistics.median(waits), 1),
                "count": len(waits),
            }
            for login, waits in reviewer_waits.items()
        ],
        key=lambda r: -r["median_days"],
    )

    median = round(statistics.median(all_waits), 1)

    # Tone from the worst reviewer's median (D2e: <1 d green, 1-2 amber, >2 red)
    worst_days = max((r["median_days"] for r in per_reviewer), default=0.0)
    if worst_days > 2:
        tone = "red"
    elif worst_days > 1:
        tone = "amber"
    else:
        tone = "green"

    return {
        "present": True,
        "tone": tone,
        "median_days": median,
        "waiting_count": len(all_waits),
        "per_reviewer": per_reviewer,
    }


# ── issue_aging ──────────────────────────────────────────────────────

def issue_aging(
    entities: list[dict[str, Any]],
    now: datetime | None = None,
    threshold_days: int = 14,
) -> dict[str, Any]:
    """Derive issue-aging signal from Jira entities.

    An entity is "aged" when its created_at is older than threshold_days
    and its status is not Done/Closed.

    Returns::

        {
            "present": bool,       # Jira entities exist
            "aged_count": int,     # issues past the threshold
        }
    """
    if now is None:
        now = datetime.now(timezone.utc)
    now_naive = now.replace(tzinfo=None)

    if not entities:
        return {"present": False, "tone": "green", "aged_count": 0,
                "threshold_days": threshold_days}

    aged = 0
    for entity in entities:
        status = str(entity.get("status") or "").lower()
        if status in ("done", "closed"):
            continue
        created_at_str = entity.get("created_at") or entity.get("createdAt") or ""
        if not created_at_str:
            continue
        try:
            created_dt = datetime.fromisoformat(
                str(created_at_str).replace("Z", "+00:00").split("T")[0]
            ).replace(tzinfo=None)
        except (ValueError, TypeError):
            continue
        age_days = (now_naive - created_dt).days
        if age_days > threshold_days:
            aged += 1

    # Tone (D2e: 0 green, 1-2 amber, 3+ red)
    if aged >= 3:
        tone = "red"
    elif aged >= 1:
        tone = "amber"
    else:
        tone = "green"

    return {"present": True, "tone": tone, "aged_count": aged,
            "threshold_days": threshold_days}


# ── ci_health ────────────────────────────────────────────────────────

def ci_health(
    history: list[dict[str, Any]],
    *,
    queue: int = 0,
) -> dict[str, Any]:
    """Derive CI health signal from run history (latest first).

    ``history`` is a list of CI run dicts each with at least
    ``conclusion`` (success | failure | ...) and optionally ``branch``.

    ``queue`` is the merge-queue depth (open non-draft PRs with passing
    CI), computed by ``merge_queue_depth`` and passed in so the signal
    is self-contained.

    Tone:
      - green: last 3 runs all pass
      - amber: 1 failure in last 3
      - red: 2+ failures in last 3

    Flaky branch count: branches with alternating pass/fail pattern.

    Returns::

        {
            "present": bool,
            "tone": "green" | "amber" | "red",
            "failures_last_3": int,
            "flaky_branch_count": int,
            "queue": int,
        }
    """
    if not history:
        return {
            "present": False,
            "tone": "green",
            "failures_last_3": 0,
            "flaky_branch_count": 0,
            "queue": queue,
        }

    # Last 3 conclusions
    recent = history[:3]
    failures = sum(
        1 for run in recent
        if str(run.get("conclusion") or "").lower() in ("failure", "timed_out", "cancelled")
    )

    if failures >= 2:
        tone = "red"
    elif failures == 1:
        tone = "amber"
    else:
        tone = "green"

    # Flaky branches: group by branch, check for alternating pass/fail
    branch_runs: dict[str, list[str]] = {}
    for run in history:
        branch = str(run.get("branch") or run.get("headBranch") or "").strip()
        conclusion = str(run.get("conclusion") or "").lower()
        if branch and conclusion:
            branch_runs.setdefault(branch, []).append(conclusion)

    flaky_count = 0
    for _branch, conclusions in branch_runs.items():
        if len(conclusions) < 2:
            continue
        alternating = 0
        for i in range(1, len(conclusions)):
            prev_pass = conclusions[i - 1] == "success"
            curr_pass = conclusions[i] == "success"
            if prev_pass != curr_pass:
                alternating += 1
        # A branch is flaky if it alternates at least twice
        if alternating >= 2:
            flaky_count += 1

    return {
        "present": True,
        "tone": tone,
        "failures_last_3": failures,
        "flaky_branch_count": flaky_count,
        "queue": queue,
    }


# ── merge_queue_depth ────────────────────────────────────────────────

def merge_queue_depth(
    pr_entities: list[dict[str, Any]],
) -> int:
    """Count open non-draft PRs with passing CI (merge-ready queue).

    Returns the count (0 when no qualifying PRs).
    """
    count = 0
    for entity in pr_entities:
        state = str(entity.get("state") or "").upper()
        if state != "OPEN":
            continue
        if entity.get("isDraft") or entity.get("is_draft"):
            continue
        checks = str(entity.get("checks") or "").lower()
        if checks in ("success", "passing"):
            count += 1
    return count


# ── readiness (the composite scorecard, D2e) ─────────────────────────

_TONE_ORDER = {"green": 0, "amber": 1, "red": 2}


def _tone_from_count(count: int) -> str:
    """Tone from a count: 0 → green, 1 → amber, 2+ → red."""
    if count >= 2:
        return "red"
    if count == 1:
        return "amber"
    return "green"


def readiness(
    *,
    review_signal: dict[str, Any],
    ci_signal: dict[str, Any],
    blocker_count: int = 0,
    overdue_count: int = 0,
) -> dict[str, Any]:
    """Compute the composite release-readiness scorecard.

    Each sub-signal is independently graded green/amber/red.
    The composite: green when all green, amber when any amber and none
    red, red when any red.

    Thresholds for review latency (from D2e):
      - green: all reviewers < 1 day (24 h)
      - amber: any 1-2 days (24-48 h)
      - red: any > 2 days (48 h)

    Returns::

        {
            "present": bool,
            "composite": "green" | "amber" | "red",
            "signals": {
                "review_wait": "green" | "amber" | "red",
                "ci": "green" | "amber" | "red",
                "blockers": "green" | "amber" | "red",
                "overdue": "green" | "amber" | "red",
            },
            "blockers_count": int,
        }
    """
    # Review latency tone: from the worst reviewer's median_days
    review_tone = "green"
    if review_signal.get("present"):
        worst_days = 0.0
        for reviewer in review_signal.get("per_reviewer", []):
            worst_days = max(worst_days, reviewer.get("median_days", 0.0))
        if worst_days > 2:
            review_tone = "red"
        elif worst_days > 1:
            review_tone = "amber"

    # CI tone: from ci_health
    ci_tone = ci_signal.get("tone", "green") if ci_signal.get("present") else "green"

    # Blockers
    blocker_tone = _tone_from_count(blocker_count)

    # Overdue commitments
    overdue_tone = _tone_from_count(overdue_count)

    signals = {
        "review_wait": review_tone,
        "ci": ci_tone,
        "blockers": blocker_tone,
        "overdue": overdue_tone,
    }

    # Any signal with data?
    any_present = (
        review_signal.get("present", False)
        or ci_signal.get("present", False)
        or blocker_count > 0
        or overdue_count > 0
    )

    if not any_present:
        return {
            "present": False,
            "tone": "green",
            "composite": "green",
            "signals": signals,
            "blockers_count": 0,
            "blockers": [],
        }

    # Composite: worst of all signals
    tones = list(signals.values())
    if "red" in tones:
        composite = "red"
    elif "amber" in tones:
        composite = "amber"
    else:
        composite = "green"

    # Count red signals for the "N BLOCKERS" cell
    red_count = sum(1 for t in tones if t == "red")

    # Names of signals that are red or amber (for the face's blocker labels)
    blocker_names = [name for name, t in signals.items() if t in ("red", "amber")]

    return {
        "present": True,
        "tone": composite,
        "composite": composite,
        "signals": signals,
        "blockers_count": red_count,
        "blockers": blocker_names,
    }
