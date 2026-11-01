"""AG12: the bounded builder/reviewer loop for an explicit hand-off.

The loop is hub-owned.  A builder's completed turn is eligible only when the
worktree has a new commit.  The reviewer is a normal AG11 helper launch, with
one fresh helper worktree per round and a read-only review brief.  Findings
are retained on the builder launch record so the pair survives a hub restart.
"""
from __future__ import annotations

import re
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Optional

from ..logging_config import get_logger
from .errors import ServiceError

log = get_logger("agent_review")

MAX_REVIEW_ROUNDS = 2
REVIEW_BY = ("none", "codex", "claude", "pi")
REVIEW_PROFILE = {
    "codex": "codex-default",
    "claude": "claude-default",
    "pi": "pi-default",
}
_ALIASES = {
    "": "none", "none": "none", "off": "none",
    "codex": "codex", "codex-default": "codex",
    "claude": "claude", "claude-code": "claude", "claude_code": "claude",
    "claude-default": "claude", "pi": "pi", "pi-default": "pi",
}
_FINDING = re.compile(r"^\s*(?:[-*]\s*)?(MUST|SHOULD)\b\s*[:\-]?\s*(.*?)\s*$", re.I)
_REQ_UNMET = re.compile(r"^\s*(?:[-*]\s*)?REQ\s+R(\d+)\s*[:\-]\s*UNMET\b\s*(?:[·:\-—]\s*)?(.*?)\s*$", re.I)
_CLEAR_FINDING = re.compile(
    r"^\s*(?:[-*]\s*)?MUST\s*[:\-]?\s*(?:none|no|zero)(?:\s+findings?)?\s*[.!]?\s*$",
    re.I,
)
_CLEAR_VERDICT = re.compile(
    r"^\s*(?:[-*]\s*)?(?:VERDICT|RESULT|STATUS)\s*[:\-]?\s*"
    r"(?:clear|clean|pass(?:ed)?|approved|no\s+findings?)\s*[.!]?\s*$",
    re.I,
)


class AgentReviewRefused(ServiceError):
    """A named refusal from the review loop, never a hidden retry."""

    def __init__(self, code: str, detail: str, *, status: int = 409) -> None:
        super().__init__(code, detail, context={"status": status})


def normalize_review_by(value: Any) -> str:
    key = str(value or "").strip().lower().replace(" ", "-")
    try:
        return _ALIASES[key]
    except KeyError as exc:
        raise AgentReviewRefused("reviewer_unknown", f"unknown reviewer {value!r}") from exc


def initial_review(value: Any) -> Optional[dict[str, Any]]:
    """The durable pair state attached to a builder launch."""
    reviewer = normalize_review_by(value)
    if reviewer == "none":
        return None
    return {
        "requested": reviewer,
        "status": "awaiting_builder_commit",
        "round": 0,
        "rounds": [],
        "findings_left": [],
        "reviewer_launch_id": None,
        "last_builder_commit": None,
        "result": None,
    }


#: Empty reads of a finished reviewer's words before its result is unclear
#: (one per review tick, about 30 s each).
EMPTY_READS_WAIT = 4


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _copy_review(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, Mapping) else {}


def parse_findings(words: Any) -> list[dict[str, str]]:
    """Read only explicit MUST/SHOULD lines from a reviewer's Done text.
    Programs PG-REQ: ``REQ R3: UNMET · <what is missing>`` (an owner's
    requirement the reviewer judged unmet) is a MUST, so the round that
    exists sends it back; it carries ``requirement`` ("R3")."""
    text = str(words or "")
    found: list[dict[str, str]] = []
    for line in text.splitlines():
        unmet = _REQ_UNMET.match(line)
        if unmet:
            detail = unmet.group(2).strip()
            found.append({"level": "MUST", "text": f"R{unmet.group(1)} is unmet" + (f": {detail}" if detail else ""),
                          "requirement": f"R{unmet.group(1)}"})
            continue
        match = _FINDING.match(line)
        if not match or not match.group(2):
            continue
        detail = match.group(2).strip()
        # "MUST: none." (a closing mark) is none; "MUST: 1 remains (…)" is the
        # reviewer's count of the findings above, never a finding (the first
        # real night, 2026-11-01: both went back to the builder as findings).
        # "SHOULD · docs/index.md:5 · None required." (the fourth real night):
        # a leading place is not the finding; "none required" is none.
        plain = re.sub(r"^[·\-:\s]*(?:[\w./-]+:\d+\s*[·\-:]\s*)?", "", detail).strip(" .!;,").strip()
        if re.fullmatch(r"(?:no|none|zero|nothing)(?:\s+(?:findings?|left|remain(?:s|ing)?|required|needed))?", plain, re.I) \
                or re.match(r"^(?:no|none|nothing)\s+(?:required|needed)\b", plain, re.I):
            continue
        if re.match(r"^\d+\s+(?:remains?|left|open|found|findings?)\b", plain, re.I):
            continue
        found.append({"level": match.group(1).upper(), "text": detail})
    if not found and re.search(r"\b(?:no|none|zero)\s+(?:MUST\s+)?findings?\b", text, re.I):
        return []
    return found


def _review_result(words: Any) -> tuple[list[dict[str, str]], bool]:
    """Return findings and whether the reviewer explicitly cleared MUSTs.

    A blank, prose-only, or malformed Done result is unknown.  It must never
    close a pair simply because the parser found no ``MUST`` line.
    """
    text = str(words or "")
    findings = parse_findings(text)
    explicit_clear = any(_CLEAR_FINDING.match(line) or _CLEAR_VERDICT.match(line) for line in text.splitlines())
    return findings, explicit_clear


def review_wire(value: Any) -> Optional[dict[str, Any]]:
    """Small, stable wire shape for the Conductor rows."""
    if not isinstance(value, Mapping):
        return None
    findings = [dict(item) for item in value.get("findings_left") or [] if isinstance(item, Mapping)]
    result = value.get("result") if isinstance(value.get("result"), Mapping) else None
    return {
        "requested": str(value.get("requested") or ""),
        "status": str(value.get("status") or ""),
        "role": str(value.get("role") or "builder"),
        "builder": str(value.get("builder") or ""),
        "round": int(value.get("round") or 0),
        "rounds": int((result or {}).get("rounds") or value.get("round") or 0),
        "findings_left": findings,
        "reviewer_launch_id": value.get("reviewer_launch_id"),
        "pair_result": dict(result) if result else None,
    }


def review_row_words(value: Mapping[str, Any]) -> str:
    """The compact row fact required by the settled face design."""
    role = str(value.get("role") or "builder")
    requested = str(value.get("requested") or "")
    reviewer = {"codex": "Codex", "claude": "Claude Code", "pi": "pi"}.get(requested, requested)
    round_ = int(value.get("round") or 0)
    if role == "reviewer":
        builder = str(value.get("builder") or "builder")
        return f"{reviewer} reviews · {builder} builds · round {round_}"
    return f"{str(value.get('builder') or 'Builder')} builds · {reviewer} reviews · round {round_}"


class AgentReviewLoop:
    """One bounded, idempotent pass over all explicit review pairs."""

    def __init__(
        self,
        db: Any,
        hand_service: Any,
        *,
        ledger: Any = None,
        state_reader: Optional[Callable[[str], str]] = None,
        commit_reader: Optional[Callable[[Mapping[str, Any]], Optional[str]]] = None,
        result_reader: Optional[Callable[[str], str]] = None,
        prompt: Optional[Callable[[str, str], Any]] = None,
        clock: Callable[[], str] = _now,
    ) -> None:
        self.db = db
        self.hand_service = hand_service
        if ledger is None:
            from ..delivery.factory_launch import LaunchLedger

            ledger = LaunchLedger()
        self.ledger = ledger
        self._state_reader = state_reader
        self._commit_reader = commit_reader
        self._result_reader = result_reader
        self._prompt = prompt
        self._clock = clock

    def _state(self, launch_id: str) -> str:
        if self._state_reader is not None:
            return str(self._state_reader(launch_id) or "")
        try:
            from .agent_flights import agent_flights

            for flight in agent_flights(self.db, ledger=self.ledger):
                if str(flight.get("launch_id") or "") == launch_id:
                    return str(flight.get("state") or "")
        except Exception as exc:
            log.debug("review state read failed: %s", exc)
        record = self.ledger.get(launch_id) or {}
        return str(record.get("state") or "")

    def _commit(self, record: Mapping[str, Any]) -> Optional[str]:
        if self._commit_reader is not None:
            return self._commit_reader(record)
        for key in ("head_commit", "commit", "builder_commit"):
            if record.get(key):
                return str(record[key])
        # The lane reader uses the launch's registered worktree and reads git
        # inside that worktree only. If the registry is unavailable, no review
        # starts: a Done turn without proof of a new commit is not eligible.
        try:
            from .agent_hand_preview import LaunchReads
            from .launch_lane import _worktree_path, worktree_facts

            launcher = self.hand_service._launch_service()
            reads = LaunchReads()
            reads.registry = lambda: launcher._registry
            path = _worktree_path(reads, record)
            facts = worktree_facts(str(record.get("launch_id") or ""), path)
            commits = facts.get("commits") if isinstance(facts, Mapping) else None
            if isinstance(commits, list) and commits:
                return str((commits[0] or {}).get("sha") or "") or None
        except Exception as exc:
            log.debug("review commit read failed: %s", exc)
        return None

    def _result(self, launch_id: str) -> str:
        if self._result_reader is not None:
            return str(self._result_reader(launch_id) or "")
        try:
            from .agent_helpers import last_words

            return str(last_words(self.db, launch_id, self.ledger) or "")
        except Exception as exc:
            log.debug("review result read failed: %s", exc)
            return ""

    def _prompt_builder(self, builder_id: str, text: str) -> Any:
        if self._prompt is not None:
            return self._prompt(builder_id, text)
        # The builder is the launch owner, so AG11's helper-only ``prompt``
        # verb cannot address it (that verb deliberately requires
        # ``helper_of``). Reuse its same pane/credential chokepoint directly
        # for the one explicit MUST hand-back.
        from .agent_helpers import _helper_send, helper_state

        record = self.ledger.get(builder_id) or {}
        state = helper_state(self.db, builder_id, ledger=self.ledger)
        session_key = str(state.get("session_key") or record.get("session_key") or "")
        if not session_key:
            raise AgentReviewRefused("builder_not_ready", "the builder has no registered session")
        return _helper_send(
            builder_id, builder_id, record, text, session_key=session_key,
        )

    def _active_helper(self, builder_id: str) -> Optional[dict[str, Any]]:
        for record in reversed(self.ledger.list()):
            if str(record.get("helper_of") or "") != builder_id:
                continue
            # LaunchLedger keeps a helper record for history.  Its durable
            # launch state is not the turn state, so use the hub read here;
            # otherwise round two would be blocked by the completed round-one
            # helper forever.
            launch_id = str(record.get("launch_id") or "")
            if launch_id and self._state(launch_id) in {"starting", "launched", "registered", "working", "waiting"}:
                return record
        return None

    def _review_brief(
        self, builder: Mapping[str, Any], pair: Mapping[str, Any], round_: int, commit: str,
    ) -> str:
        origin = builder.get("origin_ref") or {}
        item = pair.get("item") if isinstance(pair.get("item"), Mapping) else {}
        title = str(item.get("title") or origin.get("id") or "the handed item")
        acceptance = pair.get("acceptance") if isinstance(pair.get("acceptance"), list) else []
        checks = "\n".join(f"- {str(check)}" for check in acceptance) or "- Use the hand-off acceptance checks."
        return (
            f"Review item {origin.get('kind', '')}:{origin.get('id', '')} — {title}.\n"
            f"Round {round_}. The builder commit is {commit}. Review the diff of this branch against main.\n"
            f"Acceptance checks:\n{checks}\n\n"
            "Read the worktree only. Change nothing and do not commit.\n"
            "List findings one per line with MUST or SHOULD, file and line when known. "
            "End with MUST: none when no MUST finding remains."
        )

    def _start_reviewer(self, builder: Mapping[str, Any], pair: dict[str, Any], commit: str) -> dict[str, Any]:
        round_ = int(pair.get("round") or 0) + 1
        requested = str(pair.get("requested") or "")
        reviewer = REVIEW_PROFILE.get(requested)
        if not reviewer:
            raise AgentReviewRefused("reviewer_unknown", f"unknown reviewer {requested!r}")
        instruction = self._review_brief(builder, pair, round_, commit)
        item = pair.get("item") if isinstance(pair.get("item"), Mapping) else {}
        review_context = {
            "role": "reviewer", "requested": requested, "round": round_,
            "builder_launch_id": str(builder.get("launch_id") or ""),
            "builder_commit": commit, "read_only": True,
            "builder": str(builder.get("agent") or builder.get("profile_id") or "builder"),
            "item": dict(item), "acceptance": list(pair.get("acceptance") or []),
            # Programs: a pi reviewer's engine (the Program's reviewer Runs on).
            **({"engine": str(pair["engine"])} if pair.get("engine") else {}),
        }
        from .agent_helpers import start_helper

        answer = start_helper(
            str(builder.get("launch_id") or ""), instruction=instruction, profile=reviewer,
            hand_service=self.hand_service,
            control_mode=getattr(self.hand_service, "_control_mode", lambda: "yolo"),
            ledger=self.ledger, helper_round=round_, state_reader=self._state,
            start_point=commit,
            review=review_context,
        )
        pair["round"] = round_
        pair["last_builder_commit"] = commit
        pair["last_started_at"] = self._clock()
        if answer.get("status") == "awaiting_owner":
            pair["status"] = "awaiting_owner"
            pair["reviewer_launch_id"] = None
            pair["owner_request_id"] = ((answer.get("owner_action") or {}).get("request_id"))
        else:
            self._adopt_reviewer(builder, pair, answer)
        return answer

    def _adopt_reviewer(self, builder: Mapping[str, Any], pair: dict[str, Any], answer: Mapping[str, Any]) -> str:
        """Attach the helper launch to the pair, including Secure approval.

        ``agent.start_helper`` owns the authority and cap checks.  Its Secure
        path creates an owner request first; once that request is allowed, the
        next tick adopts the one active helper that belongs to this builder.
        """
        reviewer_id = str(answer.get("launch_id") or "")
        if not reviewer_id:
            raise AgentReviewRefused("reviewer_not_started", "the reviewer did not produce a launch")
        round_ = int(pair.get("round") or 0)
        builder_commit = str(pair.get("last_builder_commit") or "")
        item = pair.get("item") if isinstance(pair.get("item"), Mapping) else {}
        requested = str(pair.get("requested") or "")
        reviewer_meta = {
            "role": "reviewer", "requested": requested, "round": round_,
            "builder_launch_id": str(builder.get("launch_id") or ""),
            "builder_commit": builder_commit, "read_only": True,
            "builder": str(builder.get("agent") or builder.get("profile_id") or "builder"),
            "item": dict(item), "acceptance": list(pair.get("acceptance") or []),
        }
        self.ledger.update(reviewer_id, review=reviewer_meta)
        pair["status"] = "reviewing"
        pair["reviewer_launch_id"] = reviewer_id
        pair["last_builder_commit"] = builder_commit
        pair.setdefault("rounds", []).append({
            "round": round_, "builder_commit": builder_commit, "reviewer_launch_id": reviewer_id,
            "status": "reviewing", "worktree": answer.get("worktree"),
        })
        return reviewer_id

    def _finish_reviewer(self, builder: Mapping[str, Any], pair: dict[str, Any]) -> Optional[dict[str, Any]]:
        reviewer_id = str(pair.get("reviewer_launch_id") or "")
        words = self._result(reviewer_id)
        if not str(words or "").strip() and int(pair.get("empty_reads") or 0) < EMPTY_READS_WAIT:
            # The turn ended before its Stop words landed (the first real
            # night: an empty read became "Reviewer result is unclear" for
            # him). Read again on the next ticks before calling it unclear.
            pair["empty_reads"] = int(pair.get("empty_reads") or 0) + 1
            return None
        pair.pop("empty_reads", None)
        findings, explicit_clear = _review_result(words)
        must = [item for item in findings if item.get("level") == "MUST"]
        round_ = int(pair.get("round") or 0)
        rows = pair.get("rounds") if isinstance(pair.get("rounds"), list) else []
        current = next((row for row in reversed(rows) if isinstance(row, Mapping) and int(row.get("round") or 0) == round_), None)
        if isinstance(current, dict):
            current.update({"status": "done", "result": words, "findings": findings, "findings_left": must, "finished_at": self._clock()})
        # A concrete MUST finding is a known non-clear result.  Only a result
        # with no MUSTs needs the explicit ``MUST: none``/verdict fence.
        if not explicit_clear and not must:
            unknown = {
                "level": "MUST",
                "text": "Reviewer result is unclear; owner must inspect the review.",
            }
            pair["status"] = "needs_you"
            pair["findings_left"] = [*must, unknown] if must else [unknown]
            pair["reviewer_launch_id"] = None
            pair["result"] = {
                "rounds": round_, "findings_left": pair["findings_left"],
                "reason": "review_result_unclear", "raw": words,
            }
            if isinstance(current, dict):
                current["status"] = "needs_you"
            return pair["result"]
        pair["findings_left"] = must
        pair["reviewer_launch_id"] = None
        if not must:
            pair["status"] = "done"
            pair["result"] = {"rounds": round_, "findings_left": [], "wording": f"round {round_}, nothing left"}
            return pair["result"]
        if round_ >= MAX_REVIEW_ROUNDS:
            pair["status"] = "needs_you"
            pair["result"] = {"rounds": round_, "findings_left": must}
            return pair["result"]
        pair["status"] = "awaiting_builder_commit"
        # Keep the partial pair result visible while the builder works.  The
        # next round replaces it with the final result or a new partial one.
        pair["result"] = {"rounds": round_, "findings_left": must}
        prompt_words = "\n".join(f"MUST: {item['text']}" for item in must)
        try:
            self._prompt_builder(str(builder.get("launch_id") or ""), f"Review findings for round {round_}:\n{prompt_words}\nFix the MUST findings, then commit.")
        except Exception as exc:
            # No retry loop: the pair stays visible for the owner.
            pair["status"] = "needs_you"
            pair["result"] = {"rounds": round_, "findings_left": must, "prompt_error": str(exc)}
        return pair.get("result")

    def tick(self) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for raw in self.ledger.list():
            # Reviewer launches carry the same durable ``review`` metadata as
            # their builder, but they are leaves of the pair. Only a builder
            # can own a next review round; otherwise the reviewer would be
            # recursively reviewed as a second builder.
            if str(raw.get("role") or "builder") == "reviewer":
                continue
            pair = raw.get("review")
            if not isinstance(pair, Mapping) or not pair.get("requested") or pair.get("requested") == "none":
                continue
            pair = _copy_review(pair)
            builder_id = str(raw.get("launch_id") or "")
            if not builder_id or str(pair.get("status") or "") in {"done", "needs_you"}:
                continue
            if pair.get("status") == "awaiting_owner":
                # Secure Control mode creates the helper through the existing
                # owner approval path.  Adoption is one-shot when that press
                # has produced the builder's active helper launch.
                helper = self._active_helper(builder_id)
                if helper:
                    self._adopt_reviewer(raw, pair, helper)
                    self.ledger.update(builder_id, review=pair)
                    events.append({"builder_launch_id": builder_id, "status": pair.get("status"), "round": pair.get("round")})
                continue
            reviewer_id = str(pair.get("reviewer_launch_id") or "")
            if reviewer_id and self._state(reviewer_id) == "done":
                result = self._finish_reviewer(raw, pair)
                self.ledger.update(builder_id, review=pair)
                events.append({"builder_launch_id": builder_id, "status": pair.get("status"), "result": result})
                continue
            if reviewer_id and self._state(reviewer_id) in {"starting", "launched", "registered"}:
                continue
            if self._active_helper(builder_id):
                continue
            if self._state(builder_id) != "done":
                continue
            commit = self._commit(raw)
            if not commit or commit == pair.get("last_builder_commit"):
                # A Done turn without a new commit is deliberately inert.
                continue
            try:
                self._start_reviewer(raw, pair, commit)
            except Exception as exc:
                pair["status"] = "needs_you"
                pair["result"] = {"rounds": int(pair.get("round") or 0), "findings_left": [{"level": "MUST", "text": f"Reviewer could not start: {exc}"}]}
                self.ledger.update(builder_id, review=pair)
                events.append({"builder_launch_id": builder_id, "status": pair.get("status"), "result": pair.get("result")})
                continue
            self.ledger.update(builder_id, review=pair)
            events.append({"builder_launch_id": builder_id, "status": pair.get("status"), "round": pair.get("round")})
        return events


def review_tick(db: Any = None, *, hand_service: Any = None, ledger: Any = None) -> list[dict[str, Any]]:
    """Production seam used by the hub's existing coder watcher."""
    if db is None:
        from ..db import get_database

        db = get_database()
    if hand_service is None:
        from .agent_hand_service import default_agent_hand_service

        hand_service = default_agent_hand_service(db)
    return AgentReviewLoop(db, hand_service, ledger=ledger).tick()


__all__ = [
    "AgentReviewLoop", "AgentReviewRefused", "MAX_REVIEW_ROUNDS", "REVIEW_BY",
    "REVIEW_PROFILE", "initial_review", "normalize_review_by", "parse_findings",
    "review_tick", "review_wire", "review_row_words",
]
