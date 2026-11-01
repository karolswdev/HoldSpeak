"""Reach: Later as an answer, the ladder, his settings (PG-DIRECTION DIR4, DIR6 hub, DIR7 in part).

DIRECTION-2026-10-31.md §7 (Defer, ruled: all defaults approved 2026-10-31):

- **Later is one choice with a next touch.** The words are a rule, no model
  (:func:`parse_later`): "later" (his default, Settings ▸ Reach ▸ Later
  means), "in 1 hour", "later 2h", "later 30m", "at 13:00", "at one",
  "tonight" (19:00), "tomorrow" (the end of quiet hours tomorrow). Anything
  else is refused with "Say a time, for example 14:30."
- **The next touch.** A deferred item is kept in ``held_later``; it leaves
  the Needs you count and sits in the Later group with "back at 13:00" in its
  line. At the next touch it comes back to the count and the ladder sends it
  again on the channel he deferred it on (Telegram when he said it there or
  on the page; the desk's own rung otherwise).
- **The ladder.** Desk at once; the Phone app push as built
  (``phone_rules``); Telegram by his setting: At once · After 10 min · Only
  the digest · Off; a call by ``phone_rules`` as built. Never twice in five
  minutes for one item, at most three messages an hour for one step, quiet
  hours queue every message to their end (the digest then carries them), an
  answer anywhere stops the ladder.
- **YOLO's provisional move.** ``ProgramService.later``: a deferred core
  question parks its step for now (Overturnable); below YOLO the step waits.

His settings live in one cadence policy row (``reach``), next to the one
quiet-hours store (``heartbeat_service.read_quiet_hours``, shared with the
Phone). Nothing here reads the machine; Telegram's sends are
``services/telegram_reach.py`` (``HOLDSPEAK_TELEGRAM=off`` on every rig).
"""
from __future__ import annotations

import re
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Mapping, Optional

from ..db.briefing import BriefingStore, HeldLaterStore
from ..logging_config import get_logger
from ..principals import PrincipalKind
from ..timestamps import utc_now_iso
from .errors import ServiceError

log = get_logger("services.reach")

POLICY = "reach"
#: PG-LANG LANG12: the night digest lines (one per night per Program), kept the last 30.
NIGHT_POLICY = "reach_night_lines"
NIGHT_KEPT = 30
#: Settings ▸ Reach ▸ When to reach you ▸ Telegram.
TELEGRAM_MODES = ("at_once", "after_10", "digest", "off")
TELEGRAM_MODE_WORDS = {"at_once": "At once", "after_10": "After 10 min", "digest": "Only the digest", "off": "Off"}
#: Settings ▸ Reach ▸ Later means.
LATER_MEANS = ("in_2h", "end_of_quiet", "tomorrow")
LATER_MEANS_WORDS = {"in_2h": "In 2 hours", "end_of_quiet": "End of quiet hours", "tomorrow": "Tomorrow"}
#: Settings ▸ Reach ▸ Digest: the end of quiet hours, or an hour of the day.
DIGEST_END = "end_of_quiet"
DEFAULTS: dict[str, Any] = {"telegram": "at_once", "later_means": "in_2h", "digest": DIGEST_END, "phone_app": "on"}
#: The minutes Telegram waits for an answer on the desk at After 10 min.
TELEGRAM_AFTER_MINUTES = 10
#: Shared with the Phone (``phone_rules.REPEAT_MINUTES``, ``docs/phone.md``).
REPEAT_MINUTES = 5
STEP_MESSAGES_PER_HOUR = 3
#: Later's fixed next touches (the page's and Telegram's buttons).
LATER_CHOICES = ("in_1h", "at_13", "tonight", "tomorrow")
LATER_LABELS = {"in_1h": "1 h", "at_13": "13:00", "tonight": "Tonight", "tomorrow": "Tomorrow"}
_VIA = ("desk", "phone", "call", "telegram", "page")

_NUMBERS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
            "ten": 10, "eleven": 11, "twelve": 12, "a": 1, "an": 1, "half": 0}
_LOCK = threading.RLock()


class ReachRefused(ServiceError):
    def __init__(self, code: str, detail: str, *, status: int = 409, **more: Any) -> None:
        super().__init__(code, detail, context={"status": status, **more})


def _parse(stamp: Any) -> Optional[datetime]:
    try:
        value = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def clock_words(stamp: Any) -> str:
    value = _parse(stamp) if not isinstance(stamp, datetime) else stamp
    return value.astimezone().strftime("%H:%M") if value else ""


def in_quiet(moment: datetime, quiet: tuple[int, int]) -> bool:
    from ..cadence.scheduler import in_quiet_hours

    return in_quiet_hours(moment.astimezone(), int(quiet[0]), int(quiet[1]))


def quiet_end_after(moment: datetime, quiet: tuple[int, int]) -> datetime:
    """The next end of quiet hours after ``moment`` (local)."""
    local = moment.astimezone()
    at = local.replace(hour=int(quiet[1]) % 24, minute=0, second=0, microsecond=0)
    return at if at > local else at + timedelta(days=1)


def _at_hour(local: datetime, hour: int, minute: int = 0) -> datetime:
    at = local.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return at if at > local else at + timedelta(days=1)


def parse_later(text: Any, now: datetime, *, quiet: tuple[int, int] = (22, 8),
                means: str = "in_2h") -> datetime:
    """His Later words to the next touch (aware, local). §7 "The words"; no
    model. Raises :class:`ReachRefused` ``later_invalid`` on anything else."""
    local = now.astimezone()
    words = " ".join(str(text or "").lower().replace(",", " ").split())
    words = re.sub(r"^(ask me )?later\b", "", words).strip()
    words = re.sub(r"\bplease\b", "", words).strip()
    if words in LATER_CHOICES:
        choice = words
        if choice == "in_1h":
            return local + timedelta(hours=1)
        if choice == "at_13":
            return _at_hour(local, 13)
        words = choice
    if words in ("", "default", "not now", "wait"):
        if means == "end_of_quiet":
            return quiet_end_after(local, quiet)
        if means == "tomorrow":
            return (local + timedelta(days=1)).replace(hour=int(quiet[1]) % 24, minute=0, second=0, microsecond=0)
        until = local + timedelta(hours=2)
        return quiet_end_after(local, quiet) if in_quiet(until, quiet) else until
    if words in ("in_2h",):
        return local + timedelta(hours=2)
    if words == "tonight":
        return _at_hour(local, 19)
    if words in ("tomorrow", "tomorrow morning"):
        return (local + timedelta(days=1)).replace(hour=int(quiet[1]) % 24, minute=0, second=0, microsecond=0)
    if words == "end_of_quiet":
        return quiet_end_after(local, quiet)
    # "in 2 hours", "in two hours", "2h", "30m", "in 30 minutes", "in an hour", "in half an hour"
    span = re.fullmatch(r"(?:in )?(half an|an|a|\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
                        r" ?(h|hr|hrs|hour|hours|m|min|mins|minute|minutes)", words)
    if span:
        amount_word, unit = span.group(1), span.group(2)
        if amount_word == "half an":
            return local + timedelta(minutes=30)
        amount = int(amount_word) if amount_word.isdigit() else _NUMBERS[amount_word]
        if amount <= 0:
            raise _invalid()
        minutes = amount * 60 if unit.startswith("h") else amount
        if minutes > 7 * 24 * 60:
            raise _invalid()
        return local + timedelta(minutes=minutes)
    # "at 13:00", "13:00", "14:30", "at one", "at 5", "at 5pm"
    clock = re.fullmatch(r"(?:at )?(\d{1,2})[:.](\d{2})", words)
    if clock:
        hour, minute = int(clock.group(1)), int(clock.group(2))
        if hour > 23 or minute > 59:
            raise _invalid()
        return _at_hour(local, hour, minute)
    bare = re.fullmatch(r"(?:at )?(\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
                        r"(?: ?(am|pm|o'clock))?", words)
    if bare and (words.startswith("at ") or bare.group(2)):
        raw = bare.group(1)
        hour = int(raw) if raw.isdigit() else _NUMBERS[raw]
        mark = bare.group(2)
        if hour > 23:
            raise _invalid()
        if mark == "am":
            return _at_hour(local, hour % 12)
        if mark == "pm":
            return _at_hour(local, hour % 12 + 12)
        if hour > 12:
            return _at_hour(local, hour)
        # "at one" at 12:10 is 13:00, at 06:30 it is 13:00 too: the next of h and h+12.
        candidates = [_at_hour(local, hour % 12), _at_hour(local, hour % 12 + 12)]
        return min(candidates)
    raise _invalid()


def _invalid() -> ReachRefused:
    return ReachRefused("later_invalid", "Say a time, for example 14:30.", status=400)


def is_later_words(text: Any) -> bool:
    """A reply that is Later ("later", "later 2h", "tonight", "tomorrow", ...)."""
    words = " ".join(str(text or "").lower().replace(",", " ").split())
    return bool(re.match(r"^(ask me )?later\b", words)) or words in ("tonight", "tomorrow", "not now")


class ReachService:
    """His reach settings, Later on any channel, and the ladder's tick."""

    def __init__(self, db: Any, *, programs: Optional[Callable[[], Any]] = None, briefing: Any = None,
                 telegram: Optional[Callable[[], Any]] = None, clock: Callable[[], str] = utc_now_iso) -> None:
        self.db = db
        self.later_rows = HeldLaterStore(db)
        self.packages = BriefingStore(db)
        self._programs = programs
        self._briefing = briefing
        self._telegram = telegram
        self._clock = clock
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._digest_sent: Optional[str] = None

    # ── seams ────────────────────────────────────────────────────────

    def programs(self) -> Any:
        if self._programs is not None:
            return self._programs()
        from .program_service import default_program_service

        return default_program_service(self.db)

    def briefing(self) -> Any:
        if self._briefing is not None:
            return self._briefing
        from .briefing_service import default_briefing_service

        return default_briefing_service(self.db)

    def telegram(self) -> Any:
        if self._telegram is not None:
            return self._telegram()
        from .telegram_reach import default_telegram_reach

        return default_telegram_reach(self.db)

    def now(self) -> datetime:
        return _parse(self._clock()) or datetime.now(timezone.utc)

    def quiet(self) -> tuple[int, int]:
        from .heartbeat_service import read_quiet_hours

        return read_quiet_hours(self.db)

    @staticmethod
    def _require_owner(principal: Any) -> None:
        if getattr(principal, "kind", None) is not PrincipalKind.OWNER:
            raise ReachRefused("owner_only", "Only you can change how HoldSpeak reaches you.", status=403)

    def _changed(self, ident: str, verb: str) -> None:
        try:
            from ..runtime import composition

            composition.notify_desk_changed("reach", ident, verb)
        except Exception:
            pass

    # ── his settings ─────────────────────────────────────────────────

    def settings(self) -> dict[str, Any]:
        out = dict(DEFAULTS)
        try:
            policy = self.db.cadence.get_policy(POLICY)
            config = dict(getattr(policy, "config", None) or {}) if policy is not None else {}
        except Exception:
            config = {}
        for key in DEFAULTS:
            if key in config:
                out[key] = config[key]
        return out

    def save_settings(self, principal: Any, patch: Mapping[str, Any]) -> dict[str, Any]:
        """PUT /api/reach: Telegram's rung, Later means, the digest time, the
        Phone app channel. Quiet hours stay on the heartbeat writer."""
        self._require_owner(principal)
        current = self.settings()
        for key, value in dict(patch or {}).items():
            if key == "telegram":
                if value not in TELEGRAM_MODES:
                    raise ReachRefused("telegram_invalid", "Telegram takes At once, After 10 min, Only the digest "
                                       "or Off.", status=400)
            elif key == "later_means":
                if value not in LATER_MEANS:
                    raise ReachRefused("later_means_invalid", "Later means takes In 2 hours, End of quiet hours "
                                       "or Tomorrow.", status=400)
            elif key == "digest":
                if value != DIGEST_END and not (isinstance(value, int) and not isinstance(value, bool)
                                                and 0 <= value <= 23):
                    raise ReachRefused("digest_invalid", "The digest takes End of quiet hours or an hour, 0 to 23.",
                                       status=400)
            elif key == "phone_app":
                if value not in ("on", "off"):
                    raise ReachRefused("phone_app_invalid", "The Phone app takes On or Off.", status=400)
            elif key in ("quiet_hours", "reach"):
                continue  # their own writers (heartbeat; calls.phone_reach)
            else:
                raise ReachRefused("setting_unknown", f"Reach has no setting {key!r}.", status=400)
            current[key] = value
        from ..cadence.models import CadencePolicy

        self.db.cadence.upsert_policy(CadencePolicy(name=POLICY, config=current))
        self._changed("settings", "updated")
        return current

    def digest_hour(self) -> int:
        value = self.settings().get("digest")
        return int(value) if isinstance(value, int) else int(self.quiet()[1]) % 24

    # ── Later ────────────────────────────────────────────────────────

    def later_until(self, words: Any) -> datetime:
        return parse_later(words, self.now(), quiet=self.quiet(), means=str(self.settings().get("later_means")))

    def later(self, principal: Any, ref: Any, words: Any = None, *, via: Any = "desk",
              package_id: Optional[str] = None) -> dict[str, Any]:
        """His Later on one held item, from any channel (owner's verb; a page
        or Telegram answer runs it as the owner). Decides nothing."""
        self._require_owner(principal)
        from .briefing_service import parse_program_ref

        ref = str(ref or "")
        channel = str(via or "desk")
        if channel not in _VIA:
            raise ReachRefused("via_invalid", f"via takes {', '.join(_VIA)}.", status=400)
        from .briefing_sources import source_for

        source = source_for(self.db, ref)
        program_id, item_id = ("", "") if source is not None else parse_program_ref(ref)
        until = self.later_until(words)
        until_words = until.astimezone().strftime("%H:%M")
        with _LOCK:
            # DIR10: another source's item only gets its next touch (its row
            # stays on the desk); a Program's item also gets the engine's move.
            moved = {} if source is not None else self.programs().later(
                principal, program_id, item_id, until=_utc(until), until_words=until_words, via=channel)
            self.later_rows.put(ref=ref, until=_utc(until), via=channel, at=_utc(self.now()), package_id=package_id)
        self._changed(ref, "later")
        return {"ref": ref, "until": _utc(until), "until_clock": until_words, "via": channel,
                "words": f"Later · back at {until_words}", "parked": bool(moved.get("parked"))}

    # ── what he sees in Settings ▸ Reach ─────────────────────────────

    def status(self, principal: Any) -> dict[str, Any]:
        """GET /api/reach: the channels, the ladder, quiet hours, the digest,
        Later means and the open packages (never a token, never a secret)."""
        self._require_owner(principal)
        settings = self.settings()
        start, end = self.quiet()
        now = self.now()
        try:
            telegram = self.telegram().status()
        except Exception as exc:
            log.info(f"reach: telegram status not read: {exc}")
            telegram = {"on": False, "paired": None, "token": "missing", "pairing": None}
        phone = _phone_status()
        open_rows = []
        for package in self.packages.open_like("program:", _utc(now)):
            open_rows.append({"id": package["id"], "refs": package["refs"], "head": (package["body"] or {}).get("head"),
                              "expires_at": package["expires_at"], "sent": package["sent"]})
        later_rows = [row for row in self.later_rows.like("program:").values() if _utc_cmp(row["until"]) > _utc(now)]
        return {
            "channels": {
                "desk": {"words": "Always"},
                "phone_app": {"on": settings["phone_app"] == "on", "paired": phone.get("paired"),
                              "words": phone.get("words")},
                "telegram": telegram,
                "calls": {"ready": phone.get("calls_ready"), "words": phone.get("calls_words")},
            },
            "ladder": {"telegram": settings["telegram"], "telegram_words": TELEGRAM_MODE_WORDS[settings["telegram"]],
                       "order": ["desk", "phone_app", "telegram", "call"], "kinds": _reach_kinds()},
            "quiet_hours": {"start": start, "end": end, "now": in_quiet(now, (start, end))},
            "digest": {"at": settings["digest"], "hour": self.digest_hour()},
            "later_means": settings["later_means"],
            "later_means_words": LATER_MEANS_WORDS[settings["later_means"]],
            "open_packages": open_rows, "later": later_rows,
        }

    def summary(self) -> dict[str, Any]:
        """``phone.status``'s reach part (§11): Telegram's state, the ladder,
        the open packages (ids, refs and times only; no token, no text)."""
        settings = self.settings()
        try:
            telegram = self.telegram().status()
        except Exception:
            telegram = {"on": False, "paired": None, "token": "missing", "pairing": None}
        now = _utc(self.now())
        return {
            "telegram": telegram,
            "ladder": {"telegram": settings["telegram"], "order": ["desk", "phone_app", "telegram", "call"],
                       "later_means": settings["later_means"], "digest": settings["digest"]},
            "open_packages": [{"id": row["id"], "refs": row["refs"], "expires_at": row["expires_at"],
                               "sent": [{"via": s.get("via"), "at": s.get("at")} for s in row["sent"]
                                        if isinstance(s, dict)]}
                              for row in self.packages.open_like("program:", now)],
        }

    # ── the ladder (one tick: the reach thread, every 30 s) ──────────

    def tick(self) -> dict[str, Any]:
        """Later's returns, Telegram's rung, the digest at his time, and the
        sent messages settled when the item was answered elsewhere."""
        done: dict[str, Any] = {"returned": [], "sent": [], "settled": [], "digest": None}
        now = self.now()
        quiet = self.quiet()
        for row in self.later_rows.due(_utc(now)):
            self.later_rows.drop(row["ref"])
            done["returned"].append(row)
            self._changed(row["ref"], "returned")
        try:
            telegram = self.telegram()
        except Exception as exc:
            log.debug(f"reach: no telegram: {exc}")
            return done
        if not telegram.live():
            return done
        mode = self.settings()["telegram"]
        returned = {row["ref"]: row for row in done["returned"]}
        items = self._open_items()
        if mode in ("at_once", "after_10") and not in_quiet(now, quiet):
            for ref, item in items.items():
                if item.get("later"):
                    continue
                sent = self._telegram_sends(ref)
                back = returned.get(ref)
                if sent and not (back and back["via"] in ("telegram", "page")):
                    continue
                if not back and mode == "after_10" and _minutes(item.get("since"), now) < TELEGRAM_AFTER_MINUTES:
                    continue
                if not self.may_send(ref, item, now):
                    continue
                try:
                    done["sent"].append(telegram.brief(ref))
                except ServiceError as exc:
                    log.info(f"reach: {ref} not sent to Telegram: {exc.code}")
        done["settled"] = telegram.settle_gone(set(items))
        # JRN4: the night's line is the morning's one message at the digest
        # hour; when it goes, the plain digest of that day does not.
        done["night"] = self._send_night_lines(telegram, now, quiet)
        if done["night"]:
            self._set_digest_day(now.astimezone().strftime("%Y-%m-%d"))
        done["digest"] = self._maybe_digest(telegram, now, quiet, items)
        return done

    # ── PG-LANG LANG12: the night's digest line ──────────────────────

    def _night_rows(self) -> list[dict[str, Any]]:
        try:
            policy = self.db.cadence.get_policy(NIGHT_POLICY)
            rows = (getattr(policy, "config", None) or {}).get("lines") if policy else None
        except Exception:
            rows = None
        return [dict(row) for row in rows or [] if isinstance(row, dict)]

    def _save_night_rows(self, rows: list[dict[str, Any]]) -> None:
        from ..cadence.models import CadencePolicy

        self.db.cadence.upsert_policy(CadencePolicy(name=NIGHT_POLICY, config={"lines": rows[-NIGHT_KEPT:]}))

    def night_line(self, ref: str, text: str, *, items: Optional[list[str]] = None) -> dict[str, Any]:
        """One line set at a night's end ("Since last night: …"), once per
        ``ref``. It goes on the ladder's Telegram rung as the morning's one
        digest (JRN4): not when Telegram is Off, held to the end of quiet
        hours and to the digest hour; ``items`` are the night's held items
        (their count and a briefing page link for the first one still held)."""
        with _LOCK:
            rows = self._night_rows()
            if any(row.get("ref") == ref for row in rows):
                return {"ref": ref, "queued": False, "again": True}
            rows.append({"ref": str(ref), "text": str(text or "")[:1000], "at": _utc(self.now()), "sent_at": None,
                         "items": [str(item) for item in items or []][:20]})
            self._save_night_rows(rows)
        sent: list[str] = []
        try:
            telegram = self.telegram()
            if telegram.live():
                sent = self._send_night_lines(telegram, self.now(), self.quiet())
        except Exception as exc:
            log.info(f"reach: the night line waits: {exc}")
        return {"ref": ref, "queued": ref not in sent, "sent": ref in sent}

    def _night_due(self, row: Mapping[str, Any], now: datetime) -> bool:
        """At or after the digest hour of the day the line was set (a line set
        after that hour goes at once)."""
        at = _parse(row.get("at"))
        if at is None:
            return True
        local = at.astimezone()
        due = local.replace(hour=self.digest_hour() % 24, minute=0, second=0, microsecond=0)
        return now.astimezone() >= max(due, local)

    def _night_text(self, telegram: Any, row: Mapping[str, Any]) -> str:
        """The line, and what of the night still waits on him: the count and
        one briefing page link (one item's page, or DIR9's one page for all of
        them, in order)."""
        text = str(row.get("text") or "")
        held = [ref for ref in row.get("items") or [] if ref in self._open_items()]
        if not held:
            return text
        words = "1 waits on you." if len(held) == 1 else f"{len(held)} wait on you."
        try:
            from .telegram_reach import TELEGRAM_OWNER

            if len(held) == 1:
                made = telegram.briefing().make(TELEGRAM_OWNER, held)
            else:
                made = telegram.briefing().make(TELEGRAM_OWNER, held, kind="digest",
                                                head=str(row.get("text") or "").splitlines()[-1][:200])
            link = telegram.link_for(made["path"])
        except Exception as exc:
            log.info(f"reach: the night's page was not made: {exc}")
            link = None
        return f"{text}\n{words}" + (f"\nOpen the page: {link}" if link else "")

    def _send_night_lines(self, telegram: Any, now: datetime, quiet: tuple[int, int]) -> list[str]:
        if self.settings()["telegram"] == "off" or in_quiet(now, quiet):
            return []
        with _LOCK:
            rows = self._night_rows()
            sent: list[str] = []
            for row in rows:
                if row.get("sent_at") or not self._night_due(row, now):
                    continue
                try:
                    telegram.line(self._night_text(telegram, row))
                except ServiceError as exc:
                    log.info(f"reach: the night line was not sent: {exc.code}")
                    continue
                row["sent_at"] = _utc(now)
                sent.append(str(row.get("ref")))
            if sent:
                self._save_night_rows(rows)
        return sent

    def _open_items(self) -> dict[str, dict[str, Any]]:
        from .briefing_service import BRIEFABLE

        out: dict[str, dict[str, Any]] = {}
        try:
            rows = self.programs().needs_you_items()
        except Exception as exc:
            log.info(f"reach: program items not read: {exc}")
            return out
        for item in rows:
            if str(item.get("kind") or "") in BRIEFABLE:
                out[f"program:{item['program_id']}:{item['id']}"] = item
        return out

    def _telegram_sends(self, ref: str) -> list[dict[str, Any]]:
        since = _utc(self.now() - timedelta(days=2))
        return [row for package in self.packages.sent_since(since) if ref in package["refs"]
                for row in package["sent"] if isinstance(row, dict) and row.get("via") == "telegram"]

    def may_send(self, ref: str, item: Mapping[str, Any], now: datetime) -> bool:
        """The shared budget (§5 "Rate and quiet hours"): never twice in five
        minutes for one item, at most three an hour for one step."""
        sends = self._telegram_sends(ref)
        if any(_minutes(row.get("at"), now) < REPEAT_MINUTES for row in sends):
            return False
        step_prefix = f"program:{item.get('program_id')}:{item.get('step_id')}:"
        since = _utc(now - timedelta(hours=1))
        step_sends = [row for package in self.packages.sent_since(since)
                      if any(str(r).startswith(step_prefix) for r in package["refs"])
                      for row in package["sent"] if isinstance(row, dict) and row.get("via") == "telegram"
                      and str(row.get("at") or "") > since]
        return len(step_sends) < STEP_MESSAGES_PER_HOUR

    def _maybe_digest(self, telegram: Any, now: datetime, quiet: tuple[int, int],
                      items: Mapping[str, Mapping[str, Any]]) -> Optional[dict[str, Any]]:
        """One message a day at his digest time, only when something waits."""
        if self.settings()["telegram"] == "off" or in_quiet(now, quiet):
            return None
        local = now.astimezone()
        if local.hour != self.digest_hour():
            return None
        day = local.strftime("%Y-%m-%d")
        last = self._digest_day()
        if last == day:
            return None
        waiting = [item for item in items.values() if not item.get("later")]
        if not waiting:
            return None
        sent = telegram.digest(list(waiting))
        self._set_digest_day(day)
        return sent

    def _digest_day(self) -> Optional[str]:
        try:
            policy = self.db.cadence.get_policy("reach_digest")
            return (getattr(policy, "config", None) or {}).get("last_sent_date") if policy else None
        except Exception:
            return None

    def _set_digest_day(self, day: str) -> None:
        from ..cadence.models import CadencePolicy

        self.db.cadence.upsert_policy(CadencePolicy(name="reach_digest", config={"last_sent_date": day}))

    def send_digest_now(self, principal: Any) -> dict[str, Any]:
        """Send the digest now (his press: egress to his own chat)."""
        self._require_owner(principal)
        telegram = self.telegram()
        if not telegram.live():
            raise ReachRefused("telegram_not_paired", "Pair Telegram first.", status=409)
        waiting = [item for item in self._open_items().values() if not item.get("later")]
        if not waiting:
            raise ReachRefused("nothing_waits", "Nothing waits on you now. No digest was sent.", status=409)
        return telegram.digest(waiting)

    # ── the reach thread ─────────────────────────────────────────────

    def start(self) -> None:
        """One daemon thread: Telegram's long poll when it is live (paired, or
        a pairing code open), else a 30 s wait; the ladder's tick between."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()

        def loop() -> None:
            offset: Optional[int] = None
            last_tick = 0.0
            import time

            while not self._stop.is_set():
                polled = False
                try:
                    telegram = self.telegram()
                    if telegram.should_poll():
                        offset = telegram.poll_once(offset)
                        polled = True
                except Exception as exc:
                    log.error(f"reach: telegram poll failed: {type(exc).__name__}")
                if time.monotonic() - last_tick >= 30:
                    last_tick = time.monotonic()
                    try:
                        self.tick()
                    except Exception as exc:
                        log.error(f"reach: tick failed: {type(exc).__name__}: {exc}")
                if not polled:
                    self._wake.wait(30)
                    self._wake.clear()

        self._thread = threading.Thread(target=loop, name="holdspeak-reach", daemon=True)
        self._thread.start()

    def wake(self) -> None:
        self._wake.set()

    def stop(self) -> None:
        self._stop.set()
        self._wake.set()


def _utc_cmp(stamp: Any) -> str:
    value = _parse(stamp)
    return _utc(value) if value else str(stamp)


def _minutes(stamp: Any, now: datetime) -> float:
    value = _parse(stamp)
    return (now - value).total_seconds() / 60 if value else 1e9


def _phone_status() -> dict[str, Any]:
    """The paired phone and the Calls line, from the Phone as built (nothing
    when the phone is off on this hub)."""
    try:
        from ..phone import phone_on

        if not phone_on():
            return {"paired": None, "words": "Phone is off on this desk", "calls_ready": False,
                    "calls_words": "Not set in Settings ▸ Calls"}
        from ..phone.service import default_phone_service

        status = default_phone_service().status()
        devices = status.get("devices") or []
        line = status.get("line") or {}
        return {"paired": (devices[0].get("name") if devices else None),
                "words": (f"Paired · {devices[0].get('name')}" if devices else "No phone is paired"),
                "calls_ready": bool(line.get("ready")), "calls_words": "Ready for calls" if line.get("ready")
                else str(line.get("words") or "Not set in Settings ▸ Calls")}
    except Exception as exc:
        log.info(f"reach: phone status not read: {exc}")
        return {"paired": None, "words": "No phone is paired", "calls_ready": False,
                "calls_words": "Not set in Settings ▸ Calls"}


def _reach_kinds() -> dict[str, Any]:
    """The Reach you rows (moved from Settings ▸ Calls ▸ Phone): his own word
    per kind over the level's, as the Phone reads them (``phone_rules``)."""
    from ..phone.phone_rules import KINDS, table

    try:
        from ..config import Config

        config = Config.load()
        own_words = dict(getattr(getattr(config, "calls", None), "phone_reach", {}) or {})
        level = str(getattr(config, "control_mode", "") or "normal")
    except Exception:
        own_words, level = {}, "normal"
    from ..phone.phone_rules import level_of

    level = level_of(level)
    out: dict[str, Any] = {"level": level}
    for kind in KINDS:
        word, _rule = table(level, kind, {"may_call": True})
        level_word = "call" if word.startswith("call") else word
        own = own_words.get(kind)
        out[kind] = {"word": own or level_word, "own": bool(own), "level_word": level_word}
    return out


_DEFAULT: Optional[ReachService] = None
_DEFAULT_DB: Any = None
_DEFAULT_LOCK = threading.Lock()


def default_reach_service(db: Any = None) -> ReachService:
    global _DEFAULT, _DEFAULT_DB
    if db is None:
        from ..db import get_database
        from ..runtime import composition

        db = composition.db_or(get_database)
    with _DEFAULT_LOCK:
        if _DEFAULT is None or _DEFAULT_DB is not db:
            if _DEFAULT is not None:
                _DEFAULT.stop()
            _DEFAULT = ReachService(db)
            _DEFAULT_DB = db
        return _DEFAULT


__all__ = ["DEFAULTS", "LATER_CHOICES", "LATER_LABELS", "LATER_MEANS", "ReachRefused", "ReachService",
           "TELEGRAM_MODES", "clock_words", "default_reach_service", "in_quiet", "is_later_words", "parse_later"]
