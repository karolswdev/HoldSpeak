"""The call that decides (PG-DIRECTION DIR8, DIRECTION-2026-10-31.md §4).

Owner ruling 2026-10-31: a call can decide, when it brings the context over
and he can defer with no pressure. This module is the hub's part of that
call, with no model in it:

- **The package, in his words.** For each held item of a Program
  (``briefing_service.BRIEFABLE``) the call says the head, the brief's lines
  (the goal, the step, what happened, the question, what the answer blocks:
  the same lines in the same order as the page and Telegram), each choice
  with its consequence, and ends with "or later".
- **A spoken choice is read back once, then decided.** His words are matched
  to a choice of the package (:func:`match_choice`, the labels of
  ``briefing_service.CHOICE_WORDS``); the read back names the title, the step
  and the consequence; on his yes the item's own verb runs as his press with
  ``via="call"`` ("… · decided on a call" in the ledger). On no nothing
  changes and the question is asked again once. A merge and a Skip that
  drops a proposal take the same read back and the same yes (ruled).
- **Later defers with no penalty.** "later", "not now", "wait", "ask me
  later", "put it on my desk", with a time or not (``reach_service.parse_later``). "next"
  (and "skip" where Skip is not a choice) is Later with the default touch.
  A waive never decides from a call: it waits for him on the desk.
- **Interruption-safe.** A call that ends before his yes decides nothing;
  the item stays held, and the ledger line says "no answer".
- **The ledger line.** When the call ends, each item it read gets one line
  ("Asked on a call 12:10 · Go on, decided · transcript: Call · 31 Oct
  12:10") with the call's Note in ``undo.note_ref``.

Later goes through the one Later verb, ``ReachService.later`` (DIR4,
``services/reach_service.py``) with ``via="call"``: its parser reads the
time, the item leaves the Needs you count and comes back at the next touch,
and at YOLO a core question's step is parked for now (Overturnable).
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Callable, Mapping, Optional

from ..logging_config import get_logger
from ..principals import Principal, PrincipalKind
from ..timestamps import local_now

log = get_logger("calls.decide")

OWNER = Principal(PrincipalKind.OWNER, "owner-calls")

NOTHING_WAITS = "Nothing waits on you."
DECIDED = "Decided."
NOTHING_CHANGED = "Nothing changed."
SAY_A_TIME = "Say a time, for example 14:30."
ON_THE_DESK = "A waive waits for you on the desk."
#: Unclear answers to one question before the call goes to the next item.
UNCLEAR_TRIES = 2

_COUNT = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight", 9: "Nine",
          10: "Ten", 11: "Eleven", 12: "Twelve"}
#: Words a choice is also heard by (``not met`` is Unmet).
_ALIASES = {"unmet": ("not met",), "not_yet": ("not yet",), "fix_now": ("fix it now", "fix it"),
            "send_back": ("send it back",)}


# ── his words ─────────────────────────────────────────────────────────

def _words(text: Any) -> str:
    """Lower case, ``13.30`` as ``13:30``, punctuation as spaces."""
    out = str(text or "").lower().replace("’", "'")
    out = re.sub(r"(\d)[:.](\d\d)\b", r"\1:\2", out)
    out = re.sub(r"[^a-z0-9:' ]+", " ", out)
    return " ".join(out.split())


_WHAT_WAITS = re.compile(r"\bwhat\b.*\b(waits?|waiting)\b|\bwhat (do|must|should) i decide\b|"
                         r"\banything (waiting|for me to decide)\b")
_LATER = re.compile(r"\b(later|not now|wait|on (my|the) desk|tonight|tomorrow)\b|^(in|at) \S+")
_NEXT = re.compile(r"^(next|skip)( (one|item|please|it))*$")
_WAIVE = re.compile(r"\bwaive\b")
_YES = re.compile(r"\b(yes|yeah|yep|yup|sure|ok(ay)?|do it|go ahead|correct|decide( it)?|confirmed?)\b")
_NO = re.compile(r"\b(no|nope|don'?t|do not|stop|cancel)\b")
_STOP = re.compile(r"^(ok(ay)? )?(thanks?( you)? )?(that'?s all|that is all|stop|enough|good ?bye|bye)\b")


def is_what_waits(text: Any) -> bool:
    """"What waits on me", "what is waiting for me", "what do I decide"."""
    return bool(_WHAT_WAITS.search(_words(text)))


def is_later(text: Any) -> bool:
    """Later on a decision hold: "later", "not now", "wait", "ask me later",
    "put it on my desk", "tonight", "tomorrow", "in two hours", "at one"."""
    return bool(_LATER.search(_words(text)))


def is_next(text: Any) -> bool:
    return bool(_NEXT.match(_words(text)))


def is_waive(text: Any) -> bool:
    """A waive (it lowers the bar): never from a call."""
    return bool(_WAIVE.search(_words(text)))


def is_stop(text: Any) -> bool:
    return bool(_STOP.match(_words(text)))


def yes_no(text: Any) -> str:
    """``yes``, ``no`` or ``""``. Later is read before this (a "wait" is
    Later on a decision hold, never No)."""
    words = _words(text)
    yes, no = bool(_YES.search(words)), bool(_NO.search(words))
    if yes and not no:
        return "yes"
    if no and not yes:
        return "no"
    return ""


def match_choice(body: Mapping[str, Any], text: Any) -> Optional[str]:
    """The package's choice his words name (the longest label heard wins),
    or None. Finding's ``later`` is "Make a task": the word later is Later."""
    words = f" {_words(text)} "
    best: tuple[int, Optional[str]] = (0, None)
    for choice in body.get("choices") or []:
        names = {_words(choice.get("label")), *(_ALIASES.get(str(choice.get("id")), ()))}
        if choice.get("id") != "later":
            names.add(_words(str(choice.get("id")).replace("_", " ")))
        for name in names:
            if name and f" {name} " in words and len(name) > best[0]:
                best = (len(name), str(choice["id"]))
    return best[1]


def later_words(text: Any) -> str:
    """His spoken Later as the words ``reach_service.parse_later`` reads:
    no punctuation, the fillers out ("not now", "wait", "ask me", "put it on
    my desk", "next"), "later" in front. "Later, at one." → "later at one";
    "Not now." → "later"."""
    words = _words(text)
    for strip in (r"\bask me\b", r"\blater\b", r"\bnot now\b", r"\bwait\b", r"\bplease\b", r"\bagain\b",
                  r"\bcall me\b", r"\bput it on (my|the) desk\b", r"\bon (my|the) desk\b", r"^(next|skip)\b",
                  r"^(ok(ay)?|yes|no)\b"):
        words = re.sub(strip, " ", words)
    words = " ".join(words.split())
    return f"later {words}".strip()


def clock(value: datetime) -> str:
    return value.astimezone().strftime("%H:%M")


# ── the package, spoken ───────────────────────────────────────────────

def _lower_first(text: str) -> str:
    """"The step stops." → "the step stops."; "HoldSpeak …" and "PR …" stay."""
    text = str(text or "").strip()
    first = text.split(" ", 1)[0] if text else ""
    if len(first) < 2 or any(char.isupper() for char in first[1:]):
        return text
    return text[:1].lower() + text[1:]


def _sentence(text: Any) -> str:
    text = " ".join(str(text or "").split()).strip()
    return text if not text or text[-1] in ".?!" else text + "."


def where_words(body: Mapping[str, Any]) -> str:
    """"step 7 of Overnight on the home box" (or the title alone)."""
    ordinal = body.get("step_ordinal")
    title = str(body.get("program_title") or "the program")
    return f"step {ordinal} of {title}" if ordinal else title


def choices_words(body: Mapping[str, Any]) -> str:
    """"Say Go on, Park, or later."."""
    labels = [str(choice["label"]) for choice in body.get("choices") or []]
    return f"Say {', '.join(labels)}, or later." if labels else "Say later."


def spoken_change(line: Any) -> str:
    """A ledger line as words for the ear: its parts joined by commas, a part
    that is only a path (a check log) left out."""
    parts = [part.strip() for part in str(line or "").split(" · ")]
    return ", ".join(part for part in parts if part and not (" " not in part and "/" in part))


def package_words(body: Mapping[str, Any]) -> str:
    """The package read aloud (§4.1, the owner's BRIEF RULE of 2026-10-31):
    the head, then the same lines the page and Telegram show, in the same
    order (``brief_words.brief_lines``: the goal, the step, what
    happened, the question, what the answer blocks), each choice with its
    consequence, "or later"."""
    from ..services.brief_words import brief_lines
    from .runner import speakable

    head = str(body.get("head") or "").replace(" · ", ", ")
    parts = [_sentence(head), *(_sentence(line) for line in brief_lines(body))]
    for choice in body.get("choices") or []:
        parts.append(_sentence(f"{choice['label']}: {_lower_first(choice.get('consequence') or '')}"))
    parts.append(choices_words(body))
    return speakable(" ".join(part for part in parts if part), 900)


def read_back_words(body: Mapping[str, Any], choice: str) -> str:
    """§4.2, verbatim: the full title, the step and the consequence."""
    row = next((c for c in body.get("choices") or [] if c["id"] == choice), {"label": choice, "consequence": ""})
    consequence = _lower_first(row.get("consequence") or "").rstrip(".")
    said = f"You said {row['label']} for {where_words(body)}"
    return f"{said}: {consequence}. Say yes to decide, or no." if consequence else f"{said}. Say yes to decide, or no."


def answered_words(body: Mapping[str, Any], how: str) -> str:
    """"Step 7 of Overnight on the home box is answered already: Go on: … ·
    decided from the briefing page." (§4.4: the first answer wins)."""
    where = where_words(body)
    return _sentence(f"{where[:1].upper()}{where[1:]}: {how}")


def count_words(n: int) -> str:
    return _COUNT.get(n, str(n))


def summary_words(outcomes: list[dict[str, Any]], desk_only: int = 0) -> str:
    """"That is all. Two decided, one later at 13:00." (§9 Delight 3)."""
    decided = [row for row in outcomes if row["outcome"] == "decided"]
    later = [row for row in outcomes if row["outcome"] == "later"]
    waiting = [row for row in outcomes if row["outcome"] in ("no_answer", "")]
    parts = []
    if decided:
        parts.append(f"{count_words(len(decided))} decided")
    if later:
        part = f"{count_words(len(later))} later"
        if len(later) == 1:
            part += f" at {later[0]['until_clock']}"
        parts.append(part)
    if waiting:
        parts.append(f"{count_words(len(waiting))} still waits" if len(waiting) == 1
                     else f"{count_words(len(waiting))} still wait")
    text = "That is all."
    if parts:
        first = ", ".join(parts)
        text += " " + first[0].upper() + first[1:].lower() + "."
    if desk_only:
        text += (" One more waits for you on the desk." if desk_only == 1
                 else f" {count_words(desk_only)} more wait for you on the desk.")
    return text


def ledger_words(row: Mapping[str, Any], note_title: str = "") -> str:
    """The call's line in the Program's ledger for one item it read."""
    asked = f"Asked on a call {row.get('asked_clock') or ''}".strip()
    outcome = {"decided": f"{row.get('label')}, decided",
               "later": f"later, back at {row.get('until_clock')}",
               "answered": "answered already"}.get(str(row.get("outcome")), "no answer")
    line = f"{asked} · {outcome}"
    return f"{line} · transcript: {note_title}" if note_title else line


# ── the hub's held items ──────────────────────────────────────────────

class DeskHeld:
    """What waits on him, for a call: the Program held items as packages,
    his choice through the item's own verb (``via="call"``), Later, and the
    ledger lines at the end. Every method is sync (the runner calls it off
    the event loop)."""

    def __init__(self, db: Any, *, briefing: Any = None, programs: Optional[Callable[[], Any]] = None,
                 reach: Optional[Callable[[], Any]] = None, now: Callable[[], datetime] = local_now) -> None:
        self._db = db
        self._briefing = briefing
        self._programs = programs
        self._reach = reach
        self._now = now

    def now(self) -> datetime:
        return self._now()

    def briefing(self) -> Any:
        if self._briefing is not None:
            return self._briefing
        from ..services.briefing_service import BriefingService

        self._briefing = BriefingService(self._db, programs=self._programs)
        return self._briefing

    def programs(self) -> Any:
        if self._programs is not None:
            return self._programs()
        from ..services.program_service import default_program_service

        return default_program_service(self._db)

    def items(self, about: str = "", because: Optional[Mapping[str, Any]] = None) -> tuple[list[dict[str, Any]], int]:
        """``(packages, desk_only)``: each Program held item a call can
        answer, the one the call is about first (``about``: a step id), as
        Needs you ranks them; ``desk_only`` counts the rest."""
        bodies: list[dict[str, Any]] = []
        desk_only = 0
        for item in self.programs().needs_you_items():
            if item.get("later"):
                continue  # deferred: it comes back at its next touch, not on this call
            body = self.briefing().compose(f"program:{item['program_id']}:{item['id']}")
            if body is None:
                desk_only += 1
                continue
            if about and body.get("step_id") == about and because:
                # DIR8a: the item the desk called about carries the reach's why.
                body["because"] = {**dict(body.get("because") or {}), **dict(because), "via": "call"}
            else:
                body["because"] = {**dict(body.get("because") or {}), "rule": "asked_on_call", "via": "call"}
            bodies.append(body)
        if about:
            bodies.sort(key=lambda body: 0 if body.get("step_id") == about else 1)
        return bodies, desk_only

    def answered(self, body: Mapping[str, Any]) -> str:
        """``""`` while the item waits on him; else how it was answered (the
        step's last owner line), for "Step 7 is answered already: …"."""
        from ..services.briefing_service import not_pending

        if self.briefing().compose(str(body["ref"])) is not None:
            return ""
        # IMP5: the same words as the page and Telegram ("Answered at 21:46 from the desk").
        return str(not_pending(*self.briefing()._decided_where(str(body["ref"]))).detail)

    def decide(self, body: Mapping[str, Any], choice: str) -> None:
        """His spoken yes: the item's own verb, as his press, ``via="call"``.
        Raises the verb's refusal (answered already, not mergeable, …)."""
        self.briefing().decide_item(OWNER, str(body["ref"]), choice, via="call")

    def reach(self) -> Any:
        if self._reach is not None:
            return self._reach()
        from ..services.reach_service import default_reach_service

        return default_reach_service(self._db)

    def later(self, body: Mapping[str, Any], words: str) -> datetime:
        """Later with the next touch his words name, through the one Later
        verb (``ReachService.later``, ``via="call"``): the item leaves the
        Needs you count, comes back at the next touch, and at YOLO a core
        question's step is parked for now. Decides nothing. Raises
        ``ValueError`` when his words name no time."""
        from ..services.reach_service import ReachRefused

        try:
            done = self.reach().later(OWNER, str(body["ref"]), later_words(words), via="call")
        except ReachRefused as exc:
            if exc.code == "later_invalid":
                raise ValueError(str(words)) from exc
            raise
        return datetime.fromisoformat(str(done["until"]).replace("Z", "+00:00")).astimezone()

    def ledger(self, rows: list[dict[str, Any]], *, note_ref: str = "", note_title: str = "") -> None:
        """One line per item the call read (§4.6), the transcript Note linked."""
        programs = self.programs()
        for row in rows:
            body = row["body"]
            try:
                programs.call_line(str(body["program_id"]), str(body.get("step_id") or "") or None,
                                   ledger_words(row, note_title), note_ref=note_ref or None,
                                   because=body.get("because"), refusal=row.get("refusal"))
            except Exception as exc:  # the ledger line is not a gate
                log.warning(f"the call's ledger line was not written: {exc}")


__all__ = [
    "DECIDED", "DeskHeld", "answered_words", "is_waive", "NOTHING_CHANGED", "NOTHING_WAITS", "ON_THE_DESK", "SAY_A_TIME", "choices_words",
    "is_later", "is_next", "is_stop", "is_what_waits", "later_words", "ledger_words", "match_choice", "package_words",
    "read_back_words", "summary_words", "where_words", "yes_no",
]
