"""Briefing packages (PG-DIRECTION DIR1, DIRECTION-2026-10-31.md §3, §6, §8, §11).

A **briefing package** is one held item of a Program, frozen when it is made
(the words he read are the words in the record), with a page token:

- 32 random bytes, base64url (43 characters); the hub stores only its SHA-256;
- 24 hours for one item (a digest, later, 12 hours);
- revocable; a revoked, an expired and an unknown token read the same: nothing;
- read many, decide once: each item is decided once, through the item's own
  verb (``program.decide`` with ``via="page"``), and then shows its outcome.

The page's principal is ``BRIEFING`` on that one package
(``holdspeak/principals.py``); the answer runs the owner's verb, because the
token proves him, and the record says the page. The token is never logged,
never in a frame and never in a URL query.

Not here yet (later slices of §12): a digest (DIR7), Later's return and the
Later group on the desk (DIR4, ``held_later``), Telegram (DIR5), a waive with
its typed reason on the page.
"""
from __future__ import annotations

import base64
import hashlib
import re
import secrets
import socket
import threading
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from ..db.briefing import BriefingStore
from ..logging_config import get_logger
from ..principals import Principal, PrincipalKind
from ..timestamps import utc_now_iso
from .errors import ServiceError

log = get_logger("services.briefing")

#: IMP5 (BROCREW-IMPORT "Knowledge escalates, authority never does"): the
#: kinds that never travel: a permission is always his, on his desk.
AUTHORITY_KINDS = frozenset({"gate", "gate_approval", "permission", "helper_allow"})
AUTHORITY_REF_PREFIXES = ("gate:",)
#: Why a held item may travel to a page, Telegram or a call (its ``because``).
QUESTION_KINDS = frozenset({"core", "answer", "requirement_word", "requirement_left", "limited"})
#: IMP5: the channel words of a late answer ("Answered at 21:46 from the desk").
VIA_FROM = {"desk": "from the desk", "page": "from the briefing page", "telegram": "from Telegram",
            "call": "on the call", "phone": "from your phone"}
NOT_OFFERED = "That choice was not on offer"
NOT_USABLE = "Choose one"
NOT_KEPT = "Could not keep that for later; it still waits"


#: DIRECTION §3: the words when a page-only item is answered elsewhere.
PAGE_ONLY = "This is decided on its page, where it shows what it sends. Open the page."


def because_of(kind: Any, *, rule: str = "kind", **more: Any) -> dict[str, Any]:
    """IMP5: why a held item travels: a question, a choice among offered
    presses, or a to-do; never a permission (those never become packages)."""
    kind = str(kind or "")
    words = ("a question" if kind in QUESTION_KINDS else "a to-do" if kind in ("door", "line")
             else "a choice among offered presses")
    return {"rule": rule, "kind": kind, "words": words, **{key: value for key, value in more.items() if value is not None}}


def not_pending(at: Any, via: Any) -> "BriefingRefused":
    """IMP5: "Answered at 21:46 from the desk": when and where."""
    clock = clock_words(at) if at else ""
    words = f"Answered at {clock} {VIA_FROM.get(str(via or 'desk'), 'from the desk')}" if clock else \
        f"Answered already {VIA_FROM.get(str(via or 'desk'), 'from the desk')}"
    return BriefingRefused("answered_already", words, refusal="not_pending", words=words,
                           outcome={"words": words, "at": at, "via": via})


#: DIR9: one page carries up to this many held items, in order, each decided alone.
DIGEST_MAX = 12
#: §3: a digest's page lives 12 hours.
DIGEST_HOURS = 12
#: §8: 256 random bits; the page path carries the base64url form.
TOKEN_BYTES = 32
TOKEN_PATTERN = r"[A-Za-z0-9_-]{43}"
_TOKEN = re.compile(f"^{TOKEN_PATTERN}$")
#: §6 "Expiring" (decision 6): one item 24 hours.
ITEM_HOURS = 24
#: §8 "Someone guesses a token": ten wrong tokens a minute from one address
#: are refused for a minute.
MISSES_PER_MINUTE = 10
#: The page's own path; the link is ``<hub>/b/<token>``.
PAGE_PREFIX = "/b/"
#: Program refs: the Needs you row's id (``program:<program id>:<item id>``).
PROGRAM_REF = "program:"

#: The held items a page answers (§3 "The held item"); an agent's question
#: (``answer``), a review ask (it prepares a send) and Close stay on the desk.
BRIEFABLE = frozenset({"core", "commit", "merge", "finding", "parked", "limited", "race", "add_step", "requirement_word", "todo",
                       "requirement_left", "requirement_proposed", "step_change", "step_amend", "delivery",
                       # DIR10: the step's agent asks; his answer is text (the page's one field).
                       "answer",
                       # PG-LANG JRN9 to JRN11: an audit's findings to file, its fix program, a lesson.
                       "audit_file", "fix_program", "lesson"})
#: The held items about the whole program (the desk's "The program").
PROGRAM_LEVEL = frozenset({"audit_file", "fix_program", "lesson"})
#: The kinds whose answer is his text, not a choice.
TEXT_KINDS = frozenset({"answer"})
#: The longest answer the page takes.
ANSWER_MAX_CHARS = 2000
#: A choice the page does not offer yet: a waive needs his typed reason.
_DESK_ONLY_CHOICES = frozenset({"waive"})

KIND_WORDS = {
    "core": "Core question", "commit": "Held commit", "merge": "Merge ask", "finding": "Finding", "parked": "Parked step",
    "limited": "Agent at its limit", "race": "Race winner", "add_step": "Added step",
    "requirement_word": "Your word", "requirement_left": "Requirement left", "todo": "To do",
    "requirement_proposed": "Proposed requirement", "step_change": "Proposed change",
    "step_amend": "Proposed amendment", "delivery": "Delivery", "answer": "The agent asks",
    "audit_file": "Audit findings", "fix_program": "Fix program", "lesson": "Lesson",
}

#: Each choice's label and what it does (§3 "The choices", ASD-STE100).
CHOICE_WORDS: dict[str, dict[str, tuple[str, str]]] = {
    "core": {"go_on": ("Go on", "The step goes on with this change."),
             "park": ("Park", "The step stops. The other steps go on.")},
    "commit": {"allow": ("Allow the commit", "The agent's change is committed. The check runs."),
               "not_now": ("Not now", "The step stops. The change stays in the worktree.")},
    "merge": {"merge": ("Merge", "HoldSpeak merges the PR."), "not_yet": ("Not yet", "The PR stays open.")},
    "finding": {"fix_now": ("Fix now", "The agent fixes it in this step."),
                "later": ("Make a task", "It becomes a task for later."),
                "skip": ("Skip", "The step goes on without the fix.")},
    "parked": {"resume": ("Resume", "The step starts again."), "skip": ("Skip", "The step stays stopped.")},
    "limited": {"continue": ("Continue", "Another agent takes the step now."),
                "wait": ("Wait", "The step waits for the reset.")},
    "race": {"pick": ("Pick", "This agent's work wins the race.")},
    "add_step": {"add": ("Add", "The step is added to the plan."), "skip": ("Skip", "No step is added.")},
    "requirement_word": {"met": ("Met", "The requirement is met."),
                         "unmet": ("Unmet", "The requirement is not met.")},
    "requirement_left": {"send_back": ("Send back", "The agent gets one more round.")},
    # PG-IMPORT IMP2: BroCrew's to-do presses.
    "todo": {"done": ("Done", "The requirement is met. The agent is told."),
             "cant": ("Can't do it", "The requirement is not met. The agent is told.")},
    "requirement_proposed": {"add": ("Add", "The requirement is added."), "skip": ("Skip", "Nothing is added.")},
    "step_change": {"apply": ("Apply", "The step changes."), "skip": ("Skip", "The step stays as it is.")},
    "step_amend": {"send": ("Send", "The agent gets the line."), "skip": ("Skip", "Nothing is sent.")},
    # LANG13: the delivery at Done (Merge at Secure; Retry after a failure).
    "delivery": {"merge": ("Merge", "The delivery PR merges."), "retry": ("Retry", "The delivery runs again."),
                 "skip": ("Skip", "The program stays Done, not delivered.")},
    # PG-LANG JRN9 to JRN11 (the consequence lines are brief_words').
    "audit_file": {"file": ("File", "Each finding becomes a Door task."),
                   "skip": ("Skip", "No task is made.")},
    "fix_program": {"make": ("Make", "HoldSpeak makes the fix program. It waits for your Start."),
                    "skip": ("Skip", "No fix program is made.")},
    "lesson": {"keep_program": ("Keep for this program", "Every step of this program gets it as a requirement."),
               "keep_repo": ("Keep for HoldSpeak", "A small step adds it to the repository's program file."),
               "skip": ("Skip", "Nothing changes.")},
}

#: Later's next touches the page offers (§7 "The words"); "At a time…" is DIR4.
LATER_CHOICES = ("in_1h", "at_13", "tonight", "tomorrow")

_LOCK = threading.RLock()


class BriefingRefused(ServiceError):
    """A named refusal; ``status`` rides on the answer."""

    def __init__(self, code: str, detail: str, *, status: int = 409, **more: Any) -> None:
        super().__init__(code, detail, context={"status": status, **more})


#: Unknown, expired and revoked read the same (§6 "Revocable"): no data.
def _gone() -> BriefingRefused:
    return BriefingRefused("page_expired", "This page has expired.", status=404)


def mint_token() -> str:
    """A new page token: 32 random bytes, base64url, no padding."""
    return base64.urlsafe_b64encode(secrets.token_bytes(TOKEN_BYTES)).rstrip(b"=").decode("ascii")


def token_hash(token: str) -> str:
    return hashlib.sha256(str(token).encode("utf-8")).hexdigest()


def is_token(value: Any) -> bool:
    return isinstance(value, str) and bool(_TOKEN.match(value))


def _parse(stamp: Any) -> Optional[datetime]:
    try:
        value = datetime.fromisoformat(str(stamp))
    except (TypeError, ValueError):
        return None
    return value if value.tzinfo else value.astimezone()


def clock_words(stamp: Any) -> str:
    """``06:31`` on the hub's wall clock."""
    value = _parse(stamp)
    return value.astimezone().strftime("%H:%M") if value else ""


def _left_words(seconds: float) -> str:
    if seconds >= 3600:
        return f"{int(seconds // 3600)} h"
    return f"{max(1, int(seconds // 60))} min"


def desk_in_reach() -> bool:
    """The hub that serves the page serves the desk too (its built bundle is
    there): the settled page offers Open on the desk."""
    return (Path(__file__).resolve().parents[1] / "static" / "_built" / "index.html").is_file()


def hub_name() -> str:
    """The hub's device name (no address, UX-CANON A.9)."""
    name = socket.gethostname().split(".")[0].strip()
    return name or "this hub"


def parse_program_ref(ref: Any) -> tuple[str, str]:
    """``program:<program id>:<item id>`` → ``(program id, item id)``."""
    text = str(ref or "")
    if not text.startswith(PROGRAM_REF):
        raise BriefingRefused("ref_unknown", "This item cannot be sent to a page yet.", status=400)
    rest = text[len(PROGRAM_REF):]
    program_id, _, item_id = rest.partition(":")
    if not program_id or not item_id:
        raise BriefingRefused("ref_unknown", "Name the item as program:<program>:<item>.", status=400)
    return program_id, item_id


def later_until(choice: str, now: datetime) -> datetime:
    """The next touch of one of ``LATER_CHOICES`` from ``now`` (aware, local)."""
    local = now.astimezone()
    if choice == "in_1h":
        return local + timedelta(hours=1)
    # The wall time on its own date, with that date's offset (wall_clock;
    # the DST day turned "At 13:00" into 12:00).
    from .wall_clock import at_local, next_local

    if choice == "at_13":
        return next_local(local, 13)
    if choice == "tonight":
        return next_local(local, 19)
    if choice == "tomorrow":
        return at_local(local, 7, days=1)
    raise BriefingRefused("later_invalid", "Choose In 1 hour, At 13:00, Tonight or Tomorrow.", status=400)


def later_options(now: datetime) -> list[dict[str, str]]:
    labels = {"in_1h": "In 1 hour", "at_13": "At 13:00", "tonight": "Tonight", "tomorrow": "Tomorrow at 07:00"}
    out = []
    for choice in LATER_CHOICES:
        until = later_until(choice, now)
        out.append({"id": choice, "label": labels[choice], "at": until.strftime("%H:%M")})
    return out


class _Misses:
    """Wrong tokens per address in the last minute."""

    def __init__(self) -> None:
        self._seen: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def blocked(self, address: str) -> bool:
        with self._lock:
            now = time.monotonic()
            recent = [at for at in self._seen.get(address, []) if now - at < 60]
            self._seen[address] = recent
            return len(recent) >= MISSES_PER_MINUTE

    def miss(self, address: str) -> None:
        with self._lock:
            self._seen.setdefault(address, []).append(time.monotonic())


MISSES = _Misses()

#: The owner, as the page's answer runs his verb (§6 "What the page writes").
PAGE_OWNER = Principal(PrincipalKind.OWNER, "briefing-page")


def report_rows(service: Any, step: Optional[Mapping[str, Any]]) -> list[dict[str, str]]:
    """PG-IMPORT IMP1: the step report as the page's rows, register by
    register (the label on the first line of each)."""
    from . import brief_words as words

    if not step:
        return []
    program_id = str(step.get("program_id") or "")
    report = words.step_report(step, service.store.list_checkpoints(program_id), service.requirements(program_id))
    if not report:
        return []
    rows: list[dict[str, str]] = []
    for key in ("observed", "claimed", "not_checked"):
        for index, row in enumerate(report[key]):
            rows.append({"label": report["words"][key] if index == 0 else "", "value": str(row["line"])})
    names = list(report["files"]) + ([f"and {report['files_more']} more"] if report["files_more"] else [])
    for index, name in enumerate(names):
        rows.append({"label": report["words"]["files"] if index == 0 else "", "value": name})
    return rows


class BriefingService:
    def __init__(self, db: Any, *, programs: Optional[Callable[[], Any]] = None,
                 clock: Callable[[], str] = utc_now_iso, reach: Any = None,
                 settle: Optional[Callable[[Mapping[str, Any], str], None]] = None,
                 telegram: Optional[Callable[[], Any]] = None) -> None:
        self.db = db
        self.store = BriefingStore(db)
        self._programs = programs
        self._clock = clock
        self._reach = reach
        #: DIR5: the package's Telegram message settles when it is answered
        #: here (``TelegramReach.settle``); the default reads the live bot.
        self.settle = settle
        self._telegram = telegram

    # ── seams ────────────────────────────────────────────────────────

    def programs(self) -> Any:
        if self._programs is not None:
            return self._programs()
        from .program_service import default_program_service

        return default_program_service(self.db)

    def _now(self) -> datetime:
        return _parse(self._clock()) or datetime.now().astimezone()

    def reach(self) -> Any:
        """DIR4: Later goes through the one reach service (``held_later``,
        the ledger line, YOLO's provisional park)."""
        if self._reach is None:
            from .reach_service import ReachService

            self._reach = ReachService(self.db, programs=self._programs, briefing=self, clock=self._clock)
        return self._reach

    def _settle(self, package: Mapping[str, Any], words: str) -> None:
        if not any(isinstance(row, dict) and row.get("via") == "telegram" for row in package.get("sent") or []):
            return
        try:
            if self.settle is not None:
                self.settle(package, words)
                return
            from .telegram_reach import default_telegram_reach, telegram_on

            if telegram_on():
                default_telegram_reach(self.db).settle(package, words)
        except Exception as exc:
            log.info(f"briefing: the Telegram message was not settled ({type(exc).__name__})")

    @staticmethod
    def _require_owner(principal: Any) -> None:
        if getattr(principal, "kind", None) is not PrincipalKind.OWNER:
            raise BriefingRefused("owner_only", "Only you can make or revoke a briefing page.", status=403)

    def _changed(self, package_id: str, verb: str) -> None:
        """``desk_changed("reach", package id, verb)``: never the token."""
        try:
            from ..runtime import composition

            composition.notify_desk_changed("reach", package_id, verb)
        except Exception:
            pass

    # ── the held item ────────────────────────────────────────────────

    def _held(self, ref: str) -> tuple[dict[str, Any], Optional[dict[str, Any]], Optional[dict[str, Any]]]:
        """``(program, step, item)`` for a Program ref; ``item`` is ``None``
        when nothing waits on him there now."""
        program_id, item_id = parse_program_ref(ref)
        service = self.programs()
        program = service.store.get_program(program_id)
        if program is None:
            raise BriefingRefused("ref_unknown", "There is no such program.", status=404)
        steps = service.store.list_steps(program_id)
        item = next((row for row in service._turn(program, steps) if str(row.get("id")) == item_id), None)
        step_id = str((item or {}).get("step_id") or item_id.split(":", 1)[0])
        step = next((row for row in steps if row["id"] == step_id), None)
        return program, step, item

    def _compose(self, ref: str, program: Mapping[str, Any], step: Optional[Mapping[str, Any]],
                 item: Mapping[str, Any]) -> dict[str, Any]:
        """The frozen package body for one held item (§3 "The briefing
        package"), in his terms (``brief_words``, the owner's BRIEF RULE of
        2026-10-31): ``note`` is the goal, the step and what happened, one
        short line each; then the one-sentence ``question``; then each choice
        with its consequence. The page, Telegram and the call read these
        lines in this order. The raw reason rides as ``error`` (the page's
        "The error" fold; never in a line)."""
        from . import brief_words as words
        from .program_rules import level_word

        kind = str(item.get("kind") or "")
        labels = CHOICE_WORDS.get(kind, {})
        steps = [row for row in self.programs().store.list_steps(program["id"]) if not row.get("race_of")]
        blocked = words.blocked_steps(steps, step)
        freed = words.freed_steps(steps, step)
        others_open = any(row.get("state") not in ("merged", "done", "parked") for row in steps
                          if step is None or row["id"] != step["id"])
        rest = words.rest_words(blocked, others_open)
        choices = []
        for index, choice in enumerate(item.get("choices") or []):
            if choice in _DESK_ONLY_CHOICES or choice not in labels:
                continue
            label, plain = labels[choice]
            said = words.consequence(kind, choice, item, step, rest, len(freed)) or plain
            choices.append({"id": choice, "label": label, "consequence": said, "primary": index == 0})
        if not choices and kind not in TEXT_KINDS:
            raise BriefingRefused("not_briefable", "This item has no choice the page can take. Answer it on your desk.",
                                  status=409)
        ordinal = (step or {}).get("ordinal") or item.get("ordinal")
        if kind in PROGRAM_LEVEL:  # about the whole program: its place is the program, not its last step
            ordinal = None
        head = f"{program['title']} · step {ordinal}" if ordinal else str(program["title"])
        goal = words.goal_line(program)
        status = ""
        if kind in PROGRAM_LEVEL:  # the program's own status line, as the window's status bar says it
            service = self.programs()
            status = service._status_line(program, service._summary(program, service.store.list_steps(program["id"])))
        doing = words.doing_words(kind, program, step, status)
        happened = words.happened_line(kind, item, step)
        if kind == "answer" and step is not None:
            # The agent's own last words on the step (its checkpoint line).
            said = next((row for row in self.programs().store.list_checkpoints(program["id"])
                         if row.get("step_id") == step["id"] and row.get("by") == "agent"), None)
            happened = words.sentence(f"The agent asks: {words.scrub(said['line'])}") if said else \
                "The step's agent asks you a question."
        question = words.question_line(kind, item)
        changed = []
        if step is not None:
            rows = [row for row in self.programs().store.list_checkpoints(program["id"])
                    if row.get("step_id") == step["id"] and not row.get("kind")]
            seen: list[str] = []
            for row in rows:
                line = words.changed_line(row.get("line"))
                if not line or line in seen:
                    continue
                seen.append(line)
                changed.append({"at": row["at"], "clock": clock_words(row["at"]), "line": line})
                if len(changed) >= 3:
                    break
        raw = ""
        if kind == "parked":
            raw = str((step or {}).get("parked_reason") or "")
        evidence = []
        if raw:
            evidence.append({"pane": "error", "label": "The error", "token": ""})
        if step is not None and step.get("pr_url"):
            evidence.append({"pane": "pr", "label": f"PR #{step.get('pr_number')}" if step.get("pr_number") else "PR",
                             "token": str(step.get("check_verdict") or "").replace("_", " ")})
        if step is not None and step.get("check_log"):
            evidence.append({"pane": "log", "label": "Check log",
                             "token": str(step.get("check_verdict") or "").replace("_", " ")})
        if step is not None and str(step.get("brief_markdown") or "").strip():
            evidence.append({"pane": "brief", "label": "Brief", "token": ""})
        if step is not None and step.get("state") in words.REPORT_STATES:
            # PG-IMPORT IMP1: the step's report in registers, read only.
            evidence.append({"pane": "report", "label": "Report", "token": ""})
        evidence.append({"pane": "text", "label": "Program text", "token": "read only"})
        now = self._now()
        since = _parse(item.get("since"))
        started = _parse((step or {}).get("started_at"))
        from .program_service import duration_words

        place = [f"Step {ordinal} of {len(steps)}" if ordinal else "The program"]
        if started:
            place.append(f"started {clock_words(started.isoformat())}")
        if since:
            place.append(f"waited {duration_words(max(0, int((now - since).total_seconds())))}")
        blocked_ids = {row["id"] for row in blocked}
        track = []
        for row in steps:
            state = str(row.get("state") or "")
            # An item about the whole program lights no step (the walk: a lesson lit step 2).
            if step is not None and kind not in PROGRAM_LEVEL and row["id"] == step["id"]:
                mark = "here"
            elif row["id"] in blocked_ids:
                mark = "blocked"
            elif state in ("merged", "done"):
                mark = "done"
            elif state == "parked":
                mark = "parked"
            elif state in ("planned", "ready"):
                mark = "planned"
            else:
                mark = "running"
            track.append({"ordinal": row["ordinal"], "title": row.get("title") or "", "mark": mark})
        return {
            "ref": ref, "kind": kind, "kind_words": KIND_WORDS.get(kind, "Waits on you"),
            "program_id": program["id"], "program_title": program["title"],
            "step_id": (step or {}).get("id") or "", "step_ordinal": ordinal or None,
            "step_title": (step or {}).get("title") or "", "head": head,
            "goal": goal, "doing": doing, "happened": happened, "note": [goal, doing, happened],
            "question": question, "place": " · ".join(place), "track": track,
            "blocked": [{"ordinal": row["ordinal"], "title": row.get("title") or ""} for row in blocked],
            "blocked_words": words.blocked_words(blocked),
            "level": level_word(program.get("control")), "since": item.get("since") or "",
            "changed": changed, "choices": choices, "evidence": evidence, "error": raw,
            **({"text": {"id": "answer", "label": "Your answer", "max": ANSWER_MAX_CHARS,
                         "consequence": "HoldSpeak types your answer to the agent. The step goes on."}}
               if kind in TEXT_KINDS else {}),
        }

    # ── DIR10: a held item outside Programs ───────────────────────────

    def _source(self, ref: Any) -> Any:
        from .briefing_sources import source_for

        return source_for(self.db, ref)

    def body_for(self, ref: str) -> dict[str, Any]:
        """The package body of one held item now (a Program's, or another
        source's, DIR10). Refused by name when nothing waits there or the
        item is answered on the desk only."""
        if str(ref).startswith(AUTHORITY_REF_PREFIXES):
            raise BriefingRefused("authority_stays", "A permission stays on your desk.", status=409)
        source = self._source(ref)
        if source is not None:
            item = source.held(ref)
            if item is None:
                raise BriefingRefused("not_waiting", "Nothing waits on you there now.", status=409)
            body = source.body(ref, item)
        else:
            program, step, item = self._held(ref)
            if item is None:
                raise BriefingRefused("not_waiting", "Nothing waits on you there now.", status=409)
            if str(item.get("kind") or "") in AUTHORITY_KINDS:
                raise BriefingRefused("authority_stays", "A permission stays on your desk.", status=409)
            if str(item.get("kind") or "") not in BRIEFABLE:
                raise BriefingRefused("not_briefable", "This item is answered on your desk.", status=409)
            body = self._compose(ref, program, step, item)
        if str(body.get("kind") or "") in AUTHORITY_KINDS:
            raise BriefingRefused("authority_stays", "A permission stays on your desk.", status=409)
        body["because"] = because_of(body.get("kind"))
        return body

    def _decided_where(self, ref: str, package: Optional[Mapping[str, Any]] = None) -> tuple[Any, Any]:
        """IMP5: when and where an item was answered: this package's answer,
        else the Program's own last owner line on the step (its channel)."""
        answers = (package or {}).get("answers") or {}
        answer = answers.get(ref) if isinstance(answers, dict) else None
        if isinstance(answer, dict) and answer.get("choice") and answer.get("choice") != "later":
            return answer.get("at"), answer.get("via")
        if not str(ref).startswith(PROGRAM_REF):
            return None, "desk"
        try:
            program_id, item_id = parse_program_ref(ref)
            step_id = item_id.split(":", 1)[0]
            row = next((row for row in self.programs().store.list_checkpoints(program_id)
                        if row.get("step_id") == step_id and row.get("by") == "owner"), None)
        except Exception:
            row = None
        return ((row or {}).get("at"), (row or {}).get("via") or "desk") if row else (None, "desk")

    @staticmethod
    def bodies(package: Mapping[str, Any]) -> list[dict[str, Any]]:
        """The items of a package, in order (DIR9: a digest holds several)."""
        body = dict(package.get("body") or {})
        if body.get("kind") == "digest":
            return [dict(item) for item in body.get("items") or []]
        return [body]

    # ── the owner's verbs ────────────────────────────────────────────

    def make(self, principal: Any, refs: Any, *, kind: Any = "item", send: Any = None,
             head: Any = None, lines: Any = None) -> dict[str, Any]:
        """One package and its page token: one held item (``item``), or up to
        twelve in order on one page (``digest``, DIR9: each decided alone).
        The token is in this answer only (the link); the hub keeps its hash."""
        self._require_owner(principal)
        kind = str(kind or "item")
        if kind not in ("item", "digest"):
            raise BriefingRefused("kind_invalid", "A page is one item or a digest.", status=400)
        if kind == "digest":
            return self._make_digest(refs, send=send, head=head, lines=lines)
        sends = [send] if isinstance(send, str) else list(send or [])
        sends = [str(row) for row in sends if row not in (None, "", "none")]
        if any(row != "telegram" for row in sends):
            raise BriefingRefused("send_unavailable", "Send takes telegram or none. Your phone's push is not "
                                  "built yet.", status=400)
        telegram = None
        if "telegram" in sends:
            if self._telegram is not None:
                telegram = self._telegram()
            else:
                from .telegram_reach import default_telegram_reach

                telegram = default_telegram_reach(self.db)
            if not telegram.live():
                raise BriefingRefused("telegram_not_paired", "Pair Telegram first, in Settings ▸ Reach.")
        refs = [str(ref) for ref in (refs if isinstance(refs, (list, tuple)) else [refs]) if ref]
        if len(refs) != 1:
            raise BriefingRefused("refs_invalid", "Name one item (refs: [ref]).", status=400)
        ref = refs[0]
        body = self.body_for(ref)
        now = self._now()
        expires = now + timedelta(hours=ITEM_HOURS)
        token = mint_token()
        package_id = f"pkg-{uuid.uuid4().hex[:12]}"
        self.store.add(package_id=package_id, kind="item", refs=[ref], body=body, token_hash=token_hash(token),
                       created_at=_utc(now), expires_at=_utc(expires))
        self._changed(package_id, "sent")
        made = {"id": package_id, "token": token, "path": f"{PAGE_PREFIX}{token}", "expires_at": _utc(expires),
                "expires_clock": expires.astimezone().strftime("%H:%M"), "refs": [ref]}
        if telegram is not None:
            made["telegram"] = telegram.send_package(package_id, made["path"])
            made["telegram"].pop("text", None)  # it holds the link, and the link holds the token
        return made

    def digest_lines(self, given: Any = None) -> list[dict[str, str]]:
        """DIR10: the digest's plain lines, no buttons: the Door tasks due
        today or late (read here), then the caller's lines (a blocker's words
        from Needs you), each in his words; a raw line is left out."""
        from . import brief_words as words

        out: list[dict[str, str]] = []
        today = self._now().astimezone().date().isoformat()
        try:
            rows = self.db.meetings.list_action_items(include_completed=False)
            due = [row for row in rows if str(getattr(row, "due", "") or "")[:10] and
                   str(getattr(row, "due", ""))[:10] <= today]
        except Exception as exc:
            log.debug(f"briefing: the Door's tasks were not read: {exc}")
            due = []
        if due:
            out.append({"kind": "door", "line": "1 task is due today." if len(due) == 1 else
                        f"{len(due)} tasks are due today."})
        for raw in given if isinstance(given, (list, tuple)) else []:
            text = words.sentence(" ".join(str(raw or "").split())[:160])
            if text and not words.fence_hits(text):
                out.append({"kind": "line", "line": text})
        return out[:6]

    def _make_digest(self, refs: Any, *, send: Any = None, head: Any = None, lines: Any = None) -> dict[str, Any]:
        """DIR9: one page for several held items, in the order given (Needs
        you's order), each composed and decided alone. An item that does not
        wait any more is left out; none left: refused."""
        if send not in (None, "", "none", [], ()):
            raise BriefingRefused("send_unavailable", "A digest goes as its link (the morning message).", status=400)
        refs = [str(ref) for ref in (refs if isinstance(refs, (list, tuple)) else [refs]) if ref]
        refs = list(dict.fromkeys(refs))[:DIGEST_MAX]
        items: list[dict[str, Any]] = []
        for ref in refs:
            try:
                items.append(self.body_for(ref))
            except BriefingRefused as exc:
                if exc.code not in ("not_waiting", "not_briefable", "ref_unknown"):
                    raise
        if not items:
            raise BriefingRefused("not_waiting", "Nothing waits on you there now.", status=409)
        words = "1 waits on you" if len(items) == 1 else f"{len(items)} wait on you"
        body = {"kind": "digest", "ref": None, "head": " ".join(str(head or "").split())[:200] or words,
                "count_words": words, "items": items, "lines": self.digest_lines(lines)}
        now = self._now()
        expires = now + timedelta(hours=DIGEST_HOURS)
        token = mint_token()
        package_id = f"pkg-{uuid.uuid4().hex[:12]}"
        kept = [item["ref"] for item in items]
        self.store.add(package_id=package_id, kind="digest", refs=kept, body=body, token_hash=token_hash(token),
                       created_at=_utc(now), expires_at=_utc(expires))
        self._changed(package_id, "sent")
        return {"id": package_id, "token": token, "path": f"{PAGE_PREFIX}{token}", "expires_at": _utc(expires),
                "expires_clock": expires.astimezone().strftime("%H:%M"), "refs": kept}

    def revoke(self, principal: Any, package_id: str) -> dict[str, Any]:
        self._require_owner(principal)
        package = self.store.get(str(package_id))
        if package is None:
            raise BriefingRefused("package_unknown", "There is no such page.", status=404)
        self.store.revoke(package["id"], _utc(self._now()))
        self._changed(package["id"], "revoked")
        return {"id": package["id"], "revoked": True}

    def packages(self, principal: Any, program_id: str) -> list[dict[str, Any]]:
        """The open pages of one Program (never a token: it is not stored)."""
        self._require_owner(principal)
        now = _utc(self._now())
        return [{"id": row["id"], "kind": row["kind"], "refs": row["refs"], "created_at": row["created_at"],
                 "expires_at": row["expires_at"], "answers": row["answers"]}
                for row in self.store.open_like(f"{PROGRAM_REF}{program_id}:", now)]

    # ── a call (DIR8): the package read aloud, no page ───────────────

    def compose(self, ref: str) -> Optional[dict[str, Any]]:
        """The package body of one held item for a channel that needs no page
        (a call reads it): composed now, never stored, no token. ``None`` when
        nothing waits on him there or the item is answered on the desk only."""
        try:
            return self.body_for(str(ref))
        except BriefingRefused:
            return None

    def decide_item(self, principal: Any, ref: str, choice: str, *, via: str) -> dict[str, Any]:
        """His choice on one held item from a channel (``via``), through the
        item's own verb. Refused by name when nothing waits there now or the
        choice is not one the package offers (a waive stays on the desk)."""
        self._require_owner(principal)
        source = self._source(ref)
        if source is not None:
            item = source.held(str(ref))
            if item is None:
                raise not_pending(*self._decided_where(str(ref)))
            if not str(choice or "").strip():
                raise BriefingRefused("not_usable", NOT_USABLE, status=400, refusal="not_usable", words=NOT_USABLE)
            if getattr(source, "page_only", False) and via != "page":
                raise BriefingRefused("page_only", PAGE_ONLY, status=409, refusal="not_offered", words=PAGE_ONLY)
            if str(choice) not in {row["id"] for row in source.body(str(ref), item)["choices"]}:
                raise BriefingRefused("not_offered", NOT_OFFERED, status=400, refusal="not_offered", words=NOT_OFFERED)
            return self._decide_source(source, str(ref), item, str(choice), via)
        program, step, item = self._held(str(ref))
        if item is None:
            raise not_pending(*self._decided_where(str(ref)))
        body = self._compose(str(ref), program, step, item)
        if not str(choice or "").strip():
            raise BriefingRefused("not_usable", NOT_USABLE, status=400, refusal="not_usable", words=NOT_USABLE)
        if str(choice) not in {row["id"] for row in body["choices"]}:
            raise BriefingRefused("not_offered", NOT_OFFERED, status=400, refusal="not_offered", words=NOT_OFFERED)
        return self.programs().decide(principal, str(program["id"]), str(item.get("step_id") or ""), via=via,
                                      choice=str(choice), **_decide_args(item))

    @staticmethod
    def _decide_source(source: Any, ref: str, item: Mapping[str, Any], choice: str, via: str) -> dict[str, Any]:
        """The item's own verb; a refusal of the verb reads as the page's."""
        try:
            return source.decide(ref, item, choice, via=via)
        except ServiceError as exc:
            raise BriefingRefused(exc.code, exc.detail, status=int((exc.context or {}).get("status", 409))) from exc

    # ── the page's verbs (the token is the authority) ────────────────

    def _package(self, token: Any) -> dict[str, Any]:
        if not is_token(token):
            raise _gone()
        package = self.store.by_hash(token_hash(str(token)))
        if package is None or package.get("revoked_at"):
            raise _gone()
        expires = _parse(package["expires_at"])
        if expires is None or expires <= self._now():
            raise _gone()
        return package

    def _others_on_page(self, package: Mapping[str, Any], ref: str) -> int:
        """How many other items on THIS page still wait on him: not decided
        on the page and still held (an item answered on the desk is gone).
        The desk-wide count is Needs you's, not the page's."""
        answers = package.get("answers") or {}
        count = 0
        for row in self.bodies(package):
            other = str(row.get("ref") or "")
            if not other or other == ref:
                continue
            answer = answers.get(other) if isinstance(answers, dict) else None
            if isinstance(answer, dict) and answer.get("choice") and answer.get("choice") != "later":
                continue
            try:
                source = self._source(other)
                held = source.held(other) if source is not None else self._held(other)[2]
            except Exception:
                held = None
            if held is not None:
                count += 1
        return count

    def _item_state(self, package: Mapping[str, Any], body: Mapping[str, Any]) -> dict[str, Any]:
        """The item's state now. A decided item settles to one line (the
        owner's rule 3): "Resume · 18:18. The step starts again. Nothing else
        waits on you."; Later: "Later · back at 13:00."."""
        from .brief_words import settle_words

        ref = str(body.get("ref") or "")
        answers = package.get("answers") or {}
        answer = answers.get(ref) if isinstance(answers, dict) else None
        labels = {choice["id"]: choice["label"] for choice in body.get("choices") or []}
        labels.setdefault("answer", "Answered")  # DIR10: his text answer
        if isinstance(answer, dict) and answer.get("choice") and answer.get("choice") != "later":
            label = labels.get(answer["choice"], str(answer["choice"]))
            via = answer.get("via")
            words = settle_words(str(body.get("kind") or ""), str(answer["choice"]), label,
                                 clock_words(answer.get("at")), self._others_on_page(package, ref),
                                 "" if via == "page" else _VIA_SETTLE.get(str(via), ""))
            return {"state": "decided", "outcome": {
                "choice": answer["choice"], "label": label, "via": via, "at": answer.get("at"), "words": words}}
        source = self._source(ref)
        if source is not None:
            step, item = None, source.held(ref)
        else:
            try:
                _program, step, item = self._held(ref)
            except BriefingRefused:
                step, item = None, None
        if item is None:
            merged = step is not None and step.get("state") in ("merged", "done")
            words = "This step is merged." if merged else "Answered already on your desk."
            return {"state": "gone", "outcome": {"words": words}}
        later_at = _parse((answer or {}).get("later_until")) if isinstance(answer, dict) else None
        if isinstance(answer, dict) and answer.get("choice") == "later" and later_at and later_at > self._now():
            return {"state": "later", "outcome": {
                "choice": "later", "label": "Later", "via": answer.get("via"), "at": answer.get("at"),
                "later_until": answer.get("later_until"),
                "words": f"Later · back at {clock_words(answer.get('later_until'))}."}}
        return {"state": "open"}

    def read(self, token: Any) -> dict[str, Any]:
        """The page's answer: the frozen package, each item's state now, the
        Later times. Read many."""
        package = self._package(token)
        now = self._now()
        body = dict(package.get("body") or {})
        items = []
        for row in self.bodies(package):
            row.pop("error", None)  # the raw reason opens as its fold only
            items.append({**row, **self._item_state(package, row)})
        first = items[0] if items else {}
        expires = _parse(package["expires_at"]) or now
        out = {
            "package": {"id": package["id"], "kind": package["kind"], "head": body.get("head") or "",
                        "expires_at": package["expires_at"],
                        "expires_words": f"Expires in {_left_words((expires - now).total_seconds())}",
                        "hub": hub_name(),
                        "desk": (f"/?open=program:{first.get('program_id')}" if first.get("program_id") else "/")
                        if desk_in_reach() else None},
            "items": items,
            "later": later_options(now),
        }
        if package["kind"] == "digest":
            # DIR9: the page's count says what still waits on this page.
            open_now = sum(1 for item in items if item.get("state") == "open")
            out["package"]["lines"] = list(body.get("lines") or [])  # DIR10: no buttons
            out["package"]["open"] = open_now
            out["package"]["open_words"] = ("Nothing on this page waits on you." if not open_now else
                                            "1 waits on you." if open_now == 1 else f"{open_now} wait on you.")
        return out

    def evidence(self, token: Any, ref: str, pane: str) -> dict[str, Any]:
        """One evidence pane, read only, loaded when it opens."""
        package = self._package(token)
        body = next((row for row in self.bodies(package) if str(row.get("ref")) == str(ref)), {})
        if not body or pane not in {row["pane"] for row in body.get("evidence") or []}:
            raise BriefingRefused("pane_unknown", "This page has no such pane.", status=404)
        service = self.programs()
        step = service.store.get_step(str(body.get("step_id") or "")) if body.get("step_id") else None
        if pane == "error":
            return {"pane": pane, "kind": "code", "text": str(body.get("error") or "")}
        if pane == "pr":
            step = step or {}
            rows = [{"label": "PR", "value": f"#{step.get('pr_number')}" if step.get("pr_number") else "Open"},
                    {"label": "Check", "value": str(step.get("check_verdict") or "Not yet").replace("_", " ")},
                    {"label": "Review", "value": str(step.get("review_verdict") or "Not yet").replace("_", " ")}]
            return {"pane": pane, "kind": "rows", "rows": rows, "url": step.get("pr_url") or None}
        if pane == "log":
            return {"pane": pane, "kind": "code", "text": _tail((step or {}).get("check_log"), 40)}
        if pane == "report":
            return {"pane": pane, "kind": "rows", "rows": report_rows(service, step), "url": None}
        if pane == "brief":
            lines = str((step or {}).get("brief_markdown") or "").splitlines()[:40]
            return {"pane": pane, "kind": "code", "text": "\n".join(lines)}
        text = service.text_get(PAGE_OWNER, str(body.get("program_id")))
        return {"pane": "text", "kind": "code", "text": str(text.get("text") or "")}

    def answer(self, token: Any, ref: Any, choice: Any, *, reason: Any = None, later: Any = None) -> dict[str, Any]:
        """His answer from the page: once per item, through the item's own
        verb with ``via="page"``. Later records the next touch and decides
        nothing."""
        with _LOCK:
            package = self._package(token)
            return self._answer(package, ref, choice, via="page", reason=reason, later=later)

    def answer_package(self, package_id: str, ref: Any, choice: Any, *, via: str, reason: Any = None,
                       later: Any = None) -> dict[str, Any]:
        """DIR5: his answer on a channel that proves him another way (the
        paired Telegram chat). The page's token expiry and Revoke end the page,
        not the item, so a tap still decides while the item waits."""
        with _LOCK:
            package = self.store.get(str(package_id))
            if package is None:
                raise BriefingRefused("package_unknown", "This item is gone.", status=404)
            return self._answer(package, ref, choice, via=via, reason=reason, later=later)

    def _answer(self, package: dict[str, Any], ref: Any, choice: Any, *, via: str, reason: Any = None,
                later: Any = None) -> dict[str, Any]:
        rows = self.bodies(package)
        ref, choice = str(ref or (rows[0].get("ref") if len(rows) == 1 else "") or ""), str(choice or "")
        body = next((row for row in rows if str(row.get("ref")) == ref), None)
        if body is None:
            raise BriefingRefused("ref_unknown", "This page does not hold that item.", status=404)
        state = self._item_state(package, body)
        if state["state"] in ("decided", "gone"):
            raise not_pending(*self._decided_where(ref, package))
        if not choice.strip():
            raise BriefingRefused("not_usable", NOT_USABLE, status=400, refusal="not_usable", words=NOT_USABLE)
        if body.get("page_only") and via != "page" and choice != "later":
            # DIRECTION §3: a prepared send is decided on its page, where its
            # preview names the destination; never a Telegram tap.
            raise BriefingRefused("page_only", PAGE_ONLY, status=409, refusal="not_offered", words=PAGE_ONLY)
        answers = dict(package.get("answers") or {})
        now = self._now()
        if choice == "later":
            try:
                deferred = self.reach().later(PAGE_OWNER, ref, later, via=via, package_id=package["id"])
            except ServiceError as exc:
                if exc.code == "later_invalid":
                    raise BriefingRefused(exc.code, exc.detail, status=400) from exc
                raise BriefingRefused("not_kept", NOT_KEPT, status=409, refusal="not_kept", words=NOT_KEPT) from exc
            except Exception as exc:  # IMP5: a Later that was not kept says so; the item still waits
                raise BriefingRefused("not_kept", NOT_KEPT, status=409, refusal="not_kept", words=NOT_KEPT) from exc
            answers[ref] = {"choice": "later", "via": via, "at": _utc(now), "later_until": deferred["until"]}
            self.store.answer(package["id"], answers)
            self._changed(package["id"], "later")
        else:
            text_answer = choice == "answer" and isinstance(body.get("text"), Mapping)
            if not text_answer and choice not in {row["id"] for row in body.get("choices") or []}:
                raise BriefingRefused("not_offered", NOT_OFFERED, status=400, refusal="not_offered", words=NOT_OFFERED)
            if text_answer:
                said = " ".join(str(reason or "").split())
                if not said:
                    raise BriefingRefused("answer_required", "Write your answer.", status=400)
                if len(said) > ANSWER_MAX_CHARS:
                    raise BriefingRefused("answer_too_long", f"An answer is at most {ANSWER_MAX_CHARS} characters.",
                                          status=400)
                source = self._source(ref)
                if source is not None:
                    # DIR10: a desk agent's question outside a Program.
                    held = source.held(ref)
                    if held is None:
                        raise not_pending(*self._decided_where(ref, package))
                    try:
                        source.answer_text(ref, held, said, via=via)
                    except ServiceError as exc:
                        raise BriefingRefused(exc.code, exc.detail, status=int((exc.context or {}).get("status", 409)),
                                              refusal="not_kept", words=exc.detail) from exc
                else:
                    _program, step, item = self._held(ref)
                    if item is None:
                        raise not_pending(*self._decided_where(ref, package))
                    self.programs().answer_agent(PAGE_OWNER, str(body["program_id"]),
                                                 str(item.get("step_id") or ""), said, via=via)
                answers[ref] = {"choice": "answer", "via": via, "at": _utc(now), "text": said[:200]}
                self.store.answer(package["id"], answers)
                self._changed(package["id"], "answered")
                fresh = self.store.get(package["id"]) or package
                state = {**body, **self._item_state(fresh, body)}
                state.pop("error", None)
                if via != "telegram":
                    self._settle(fresh, f"Answered · {clock_words(now)} · {_VIA_SETTLE.get(via, '')}".rstrip(" ·"))
                return {"item": state}
            source = self._source(ref)
            if source is not None:
                held = source.held(ref)
                if held is None:
                    raise not_pending(*self._decided_where(ref, package))
                self._decide_source(source, ref, held, choice, via)
            else:
                _program, _step, item = self._held(ref)
                if item is None:
                    raise not_pending(*self._decided_where(ref, package))
                self.programs().decide(PAGE_OWNER, str(body["program_id"]), str(item.get("step_id") or ""),
                                       via=via, choice=choice, reason=reason, **_decide_args(item))
            answers[ref] = {"choice": choice, "via": via, "at": _utc(now)}
            self.store.answer(package["id"], answers)
            self._changed(package["id"], "answered")
        fresh = self.store.get(package["id"]) or package
        state = {**body, **self._item_state(fresh, body)}
        state.pop("error", None)
        if via != "telegram":
            words = (state.get("outcome") or {}).get("words") or ""
            if state.get("state") == "decided":
                words = f"Decided: {state['outcome'].get('label')} · {clock_words(now)} · {_VIA_SETTLE.get(via, '')}".rstrip(" ·")
            self._settle(fresh, words)
        return {"item": state}


_VIA_SETTLE = {"page": "from the briefing page", "call": "on a call", "phone": "on your phone", "desk": "on your desk",
               "telegram": "from Telegram"}


def _decide_args(item: Mapping[str, Any]) -> dict[str, Any]:
    """``program.decide``'s kind and ids for one your-turn item."""
    kind = str(item.get("kind") or "")
    if kind in ("requirement_word", "requirement_left", "todo"):
        return {"kind": "requirement", "requirement_id": item.get("requirement_id")}
    if kind in ("requirement_proposed", "step_change", "step_amend"):
        return {"kind": kind, "proposal_id": item.get("proposal_id")}
    if kind == "add_step":
        return {"kind": kind, "finding_id": item.get("proposal")}
    if kind == "lesson":  # JRN11: the row names its lesson
        return {"kind": kind, "proposal_id": item.get("lesson_id")}
    return {"kind": kind, "finding_id": item.get("finding_id")}


def _utc(value: datetime) -> str:
    from datetime import timezone

    return value.astimezone(timezone.utc).isoformat()


def _tail(path: Any, lines: int) -> str:
    if not path:
        return ""
    try:
        file = Path(str(path))
        if not file.is_file():
            return ""
        with file.open("rb") as handle:
            handle.seek(0, 2)
            size = handle.tell()
            handle.seek(max(0, size - 65536))
            data = handle.read().decode("utf-8", errors="replace")
    except OSError:
        return ""
    return "\n".join(data.splitlines()[-lines:])


_DEFAULT: Optional[BriefingService] = None
_DEFAULT_DB: Any = None


def default_briefing_service(db: Any = None) -> BriefingService:
    global _DEFAULT, _DEFAULT_DB
    if db is None:
        from ..runtime import composition
        from ..db import get_database

        db = composition.db_or(get_database)
    if _DEFAULT is None or _DEFAULT_DB is not db:
        _DEFAULT = BriefingService(db)
        _DEFAULT_DB = db
    return _DEFAULT


__all__ = ["BRIEFABLE", "BriefingRefused", "BriefingService", "MISSES", "PAGE_OWNER", "TOKEN_PATTERN",
           "default_briefing_service", "is_token", "later_until", "mint_token", "parse_program_ref", "token_hash"]
