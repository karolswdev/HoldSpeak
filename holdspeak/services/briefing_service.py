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
BRIEFABLE = frozenset({"core", "merge", "finding", "parked", "limited", "race", "add_step", "requirement_word",
                       "requirement_left", "requirement_proposed", "step_change", "step_amend"})
#: A choice the page does not offer yet: a waive needs his typed reason.
_DESK_ONLY_CHOICES = frozenset({"waive"})

KIND_WORDS = {
    "core": "Core question", "merge": "Merge ask", "finding": "Finding", "parked": "Parked step",
    "limited": "Agent at its limit", "race": "Race winner", "add_step": "Added step",
    "requirement_word": "Your word", "requirement_left": "Requirement left",
    "requirement_proposed": "Proposed requirement", "step_change": "Proposed change",
    "step_amend": "Proposed amendment",
}

#: Each choice's label and what it does (§3 "The choices", ASD-STE100).
CHOICE_WORDS: dict[str, dict[str, tuple[str, str]]] = {
    "core": {"go_on": ("Go on", "The step goes on with this change."),
             "park": ("Park", "The step stops. The other steps go on.")},
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
    "requirement_proposed": {"add": ("Add", "The requirement is added."), "skip": ("Skip", "Nothing is added.")},
    "step_change": {"apply": ("Apply", "The step changes."), "skip": ("Skip", "The step stays as it is.")},
    "step_amend": {"send": ("Send", "The agent gets the line."), "skip": ("Skip", "Nothing is sent.")},
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
    if choice == "at_13":
        at = local.replace(hour=13, minute=0, second=0, microsecond=0)
        return at if at > local else at + timedelta(days=1)
    if choice == "tonight":
        at = local.replace(hour=19, minute=0, second=0, microsecond=0)
        return at if at > local else at + timedelta(days=1)
    if choice == "tomorrow":
        return (local + timedelta(days=1)).replace(hour=7, minute=0, second=0, microsecond=0)
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


class BriefingService:
    def __init__(self, db: Any, *, programs: Optional[Callable[[], Any]] = None,
                 clock: Callable[[], str] = utc_now_iso) -> None:
        self.db = db
        self.store = BriefingStore(db)
        self._programs = programs
        self._clock = clock

    # ── seams ────────────────────────────────────────────────────────

    def programs(self) -> Any:
        if self._programs is not None:
            return self._programs()
        from .program_service import default_program_service

        return default_program_service(self.db)

    def _now(self) -> datetime:
        return _parse(self._clock()) or datetime.now().astimezone()

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
        """The frozen package body for one held item (§3 "The briefing package")."""
        from .program_rules import level_word

        kind = str(item.get("kind") or "")
        words = CHOICE_WORDS.get(kind, {})
        choices = []
        for index, choice in enumerate(item.get("choices") or []):
            if choice in _DESK_ONLY_CHOICES or choice not in words:
                continue
            label, consequence = words[choice]
            choices.append({"id": choice, "label": label, "consequence": consequence, "primary": index == 0})
        if not choices:
            raise BriefingRefused("not_briefable", "This item has no choice the page can take. Answer it on your desk.",
                                  status=409)
        ordinal = (step or {}).get("ordinal") or item.get("ordinal")
        head = f"{program['title']} · step {ordinal}" if ordinal else str(program["title"])
        question = str(item.get("reason") or item.get("title") or "")
        if kind == "core" and item.get("reason"):
            question = f"Step {ordinal} asks you: {item['reason']}" if ordinal else str(item["reason"])
        else:
            question = str(item.get("title") or question)
        changed = []
        if step is not None:
            reason = str(item.get("reason") or "")
            rows = [row for row in self.programs().store.list_checkpoints(program["id"])
                    if row.get("step_id") == step["id"] and not row.get("kind")
                    and not (reason and reason in str(row.get("line") or ""))]
            changed = [{"at": row["at"], "clock": clock_words(row["at"]), "line": row["line"]} for row in rows[:3]]
        evidence = []
        if step is not None and step.get("pr_url"):
            evidence.append({"pane": "pr", "label": f"PR #{step.get('pr_number')}" if step.get("pr_number") else "PR",
                             "token": str(step.get("check_verdict") or "").replace("_", " ")})
        if step is not None and step.get("check_log"):
            evidence.append({"pane": "log", "label": "Check log",
                             "token": str(step.get("check_verdict") or "").replace("_", " ")})
        if step is not None and str(step.get("brief_markdown") or "").strip():
            evidence.append({"pane": "brief", "label": "Brief", "token": ""})
        evidence.append({"pane": "text", "label": "Program text", "token": "read only"})
        return {
            "ref": ref, "kind": kind, "kind_words": KIND_WORDS.get(kind, "Waits on you"),
            "program_id": program["id"], "program_title": program["title"],
            "step_id": (step or {}).get("id") or "", "step_ordinal": ordinal or None,
            "step_title": (step or {}).get("title") or "", "head": head, "question": question,
            "level": level_word(program.get("control")), "since": item.get("since") or "",
            "changed": changed, "choices": choices, "evidence": evidence,
        }

    # ── the owner's verbs ────────────────────────────────────────────

    def make(self, principal: Any, refs: Any, *, kind: Any = "item", send: Any = None) -> dict[str, Any]:
        """One package and its page token for one held item. The token is in
        this answer only (the link); the hub keeps its hash."""
        self._require_owner(principal)
        if str(kind or "item") != "item":
            raise BriefingRefused("digest_later", "A digest is not built yet. Make a page for one item.", status=400)
        if send not in (None, "", "none", []):
            raise BriefingRefused("send_unavailable", "Sending to Telegram or your phone is not built yet. "
                                  "Copy the page link.", status=400)
        refs = [str(ref) for ref in (refs if isinstance(refs, (list, tuple)) else [refs]) if ref]
        if len(refs) != 1:
            raise BriefingRefused("refs_invalid", "Name one item (refs: [ref]).", status=400)
        ref = refs[0]
        program, step, item = self._held(ref)
        if item is None:
            raise BriefingRefused("not_waiting", "Nothing waits on you there now.", status=409)
        if str(item.get("kind") or "") not in BRIEFABLE:
            raise BriefingRefused("not_briefable", "This item is answered on your desk.", status=409)
        body = self._compose(ref, program, step, item)
        now = self._now()
        expires = now + timedelta(hours=ITEM_HOURS)
        token = mint_token()
        package_id = f"pkg-{uuid.uuid4().hex[:12]}"
        self.store.add(package_id=package_id, kind="item", refs=[ref], body=body, token_hash=token_hash(token),
                       created_at=_utc(now), expires_at=_utc(expires))
        self._changed(package_id, "sent")
        return {"id": package_id, "token": token, "path": f"{PAGE_PREFIX}{token}", "expires_at": _utc(expires),
                "expires_clock": expires.astimezone().strftime("%H:%M"), "refs": [ref]}

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
            program, step, item = self._held(str(ref))
        except BriefingRefused:
            return None
        if item is None or str(item.get("kind") or "") not in BRIEFABLE:
            return None
        try:
            return self._compose(str(ref), program, step, item)
        except BriefingRefused:
            return None

    def decide_item(self, principal: Any, ref: str, choice: str, *, via: str) -> dict[str, Any]:
        """His choice on one held item from a channel (``via``), through the
        item's own verb. Refused by name when nothing waits there now or the
        choice is not one the package offers (a waive stays on the desk)."""
        self._require_owner(principal)
        program, step, item = self._held(str(ref))
        if item is None:
            raise BriefingRefused("answered_already", "Answered already.")
        body = self._compose(str(ref), program, step, item)
        if str(choice) not in {row["id"] for row in body["choices"]}:
            raise BriefingRefused("choice_invalid", "This choice waits for you on the desk.", status=400)
        return self.programs().decide(principal, str(program["id"]), str(item.get("step_id") or ""), via=via,
                                      choice=str(choice), **_decide_args(item))

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

    def _item_state(self, package: Mapping[str, Any], body: Mapping[str, Any]) -> dict[str, Any]:
        ref = str(body.get("ref") or "")
        answers = package.get("answers") or {}
        answer = answers.get(ref) if isinstance(answers, dict) else None
        labels = {choice["id"]: choice["label"] for choice in body.get("choices") or []}
        if isinstance(answer, dict) and answer.get("choice") and answer.get("choice") != "later":
            label = labels.get(answer["choice"], str(answer["choice"]))
            here = "decided here" if answer.get("via") == "page" else "decided"
            return {"state": "decided", "outcome": {
                "choice": answer["choice"], "label": label, "via": answer.get("via"), "at": answer.get("at"),
                "words": f"{label} · {here} · {clock_words(answer.get('at'))}"}}
        try:
            _program, step, item = self._held(ref)
        except BriefingRefused:
            step, item = None, None
        if item is None:
            merged = step is not None and step.get("state") in ("merged", "done")
            words = "This step is merged." if merged else "Answered already on your desk."
            return {"state": "gone", "outcome": {"words": words}}
        if isinstance(answer, dict) and answer.get("choice") == "later":
            return {"state": "later", "outcome": {
                "choice": "later", "label": "Later", "via": answer.get("via"), "at": answer.get("at"),
                "later_until": answer.get("later_until"),
                "words": f"Later · back at {clock_words(answer.get('later_until'))}"}}
        return {"state": "open"}

    def read(self, token: Any) -> dict[str, Any]:
        """The page's answer: the frozen package, each item's state now, the
        Later times. Read many."""
        package = self._package(token)
        now = self._now()
        body = dict(package.get("body") or {})
        item = {**body, **self._item_state(package, body)}
        expires = _parse(package["expires_at"]) or now
        return {
            "package": {"id": package["id"], "kind": package["kind"], "head": body.get("head") or "",
                        "expires_at": package["expires_at"],
                        "expires_words": f"Expires in {_left_words((expires - now).total_seconds())}",
                        "hub": hub_name()},
            "items": [item],
            "later": later_options(now),
        }

    def evidence(self, token: Any, ref: str, pane: str) -> dict[str, Any]:
        """One evidence pane, read only, loaded when it opens."""
        package = self._package(token)
        body = dict(package.get("body") or {})
        if str(ref) != str(body.get("ref")) or pane not in {row["pane"] for row in body.get("evidence") or []}:
            raise BriefingRefused("pane_unknown", "This page has no such pane.", status=404)
        service = self.programs()
        step = service.store.get_step(str(body.get("step_id") or "")) if body.get("step_id") else None
        if pane == "pr":
            step = step or {}
            rows = [{"label": "PR", "value": f"#{step.get('pr_number')}" if step.get("pr_number") else "Open"},
                    {"label": "Check", "value": str(step.get("check_verdict") or "Not yet").replace("_", " ")},
                    {"label": "Review", "value": str(step.get("review_verdict") or "Not yet").replace("_", " ")}]
            return {"pane": pane, "kind": "rows", "rows": rows, "url": step.get("pr_url") or None}
        if pane == "log":
            return {"pane": pane, "kind": "code", "text": _tail((step or {}).get("check_log"), 40)}
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
            body = dict(package.get("body") or {})
            ref, choice = str(ref or body.get("ref") or ""), str(choice or "")
            if ref != str(body.get("ref")):
                raise BriefingRefused("ref_unknown", "This page does not hold that item.", status=404)
            state = self._item_state(package, body)
            if state["state"] in ("decided", "gone"):
                raise BriefingRefused("answered_already", f"Answered already: {state['outcome']['words']}",
                                      outcome=state.get("outcome"))
            answers = dict(package.get("answers") or {})
            now = self._now()
            if choice == "later":
                until = later_until(str(later or ""), now)
                answers[ref] = {"choice": "later", "via": "page", "at": _utc(now), "later_until": _utc(until)}
                self.store.answer(package["id"], answers)
                self._changed(package["id"], "later")
            else:
                if choice not in {row["id"] for row in body.get("choices") or []}:
                    raise BriefingRefused("choice_invalid", "This choice is not on the page.", status=400)
                _program, _step, item = self._held(ref)
                if item is None:
                    raise BriefingRefused("answered_already", "Answered already on your desk.")
                self.programs().decide(PAGE_OWNER, str(body["program_id"]), str(item.get("step_id") or ""),
                                       via="page", choice=choice, reason=reason, **_decide_args(item))
                answers[ref] = {"choice": choice, "via": "page", "at": _utc(now)}
                self.store.answer(package["id"], answers)
                self._changed(package["id"], "answered")
            fresh = self.store.get(package["id"]) or package
            return {"item": {**body, **self._item_state(fresh, body)}}


def _decide_args(item: Mapping[str, Any]) -> dict[str, Any]:
    """``program.decide``'s kind and ids for one your-turn item."""
    kind = str(item.get("kind") or "")
    if kind in ("requirement_word", "requirement_left"):
        return {"kind": "requirement", "requirement_id": item.get("requirement_id")}
    if kind in ("requirement_proposed", "step_change", "step_amend"):
        return {"kind": kind, "proposal_id": item.get("proposal_id")}
    if kind == "add_step":
        return {"kind": kind, "finding_id": item.get("proposal")}
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
