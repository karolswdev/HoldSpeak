"""The Line's guards (LINE design §5), one table the hub and the Line both read.

- Emergency numbers are never dialled (exit 13).
- The daily limit of placed calls (``calls.daily_limit``, exit 14);
  incoming calls do not count.
- The AI disclosure: the first words of every call the Line places.
"""
from __future__ import annotations

import json
import os
import re
import threading
from datetime import date
from pathlib import Path
from typing import Optional

#: Never dialled: the emergency numbers of the places a carrier line can
#: reach (North America, the EU and most of the world, the UK, Australia,
#: and the other common short codes).
EMERGENCY_NUMBERS = frozenset({
    "911", "112", "999", "000", "110", "119", "118", "100", "101", "102", "103", "106", "108", "113", "117",
    "120", "122", "123", "190", "193", "197", "991", "995", "997", "998", "988",
})

DEFAULT_DAILY_LIMIT = 20

#: Said first on every call the Line places.
DISCLOSURE = "This is HoldSpeak, an AI assistant, calling for {name}."
DISCLOSURE_NO_NAME = "This is HoldSpeak, an AI assistant."


def disclosure(owner: str = "") -> str:
    owner = str(owner or "").strip()
    return DISCLOSURE.format(name=owner) if owner else DISCLOSURE_NO_NAME


def _user_digits(target: str) -> str:
    text = str(target or "").strip().lower()
    text = re.sub(r"^(sips?|tel):", "", text)
    user = text.split("@", 1)[0].split(";", 1)[0]
    return re.sub(r"[^0-9]", "", user) if re.fullmatch(r"[+0-9 ()./-]+", user or "x") else ""


def is_emergency(target: str) -> bool:
    """A number (or a SIP URI whose user is a number) on the table. ``+911``,
    ``tel:112`` and ``sip:999@carrier`` are all refused."""
    digits = _user_digits(target)
    return bool(digits) and digits in EMERGENCY_NUMBERS


class DailyCount:
    """Placed calls today, kept in a small file (one per keeper)."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()

    def _read(self) -> dict:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def today(self, *, on: Optional[date] = None) -> int:
        day = (on or date.today()).isoformat()
        data = self._read()
        return int(data.get("count", 0)) if data.get("day") == day else 0

    def allow(self, limit: int, *, on: Optional[date] = None) -> bool:
        return limit <= 0 or self.today(on=on) < limit

    def add(self, *, on: Optional[date] = None) -> int:
        day = (on or date.today()).isoformat()
        with self._lock:
            count = self.today(on=on) + 1
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps({"day": day, "count": count}), encoding="utf-8")
            os.replace(tmp, self.path)
            return count


__all__ = ["DEFAULT_DAILY_LIMIT", "DISCLOSURE", "DailyCount", "EMERGENCY_NUMBERS", "disclosure", "is_emergency"]
