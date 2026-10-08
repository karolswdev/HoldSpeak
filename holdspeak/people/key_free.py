"""PHILO-15-09: a read that never touches the People store.

The Brief is made by a scheduled job at 06:00 and is sent to other places. Its
reads must not ask for the People key (a Keychain prompt with nobody at the
desk) and must not carry People content. Inside ``no_people_reads()`` the
follow-through board leaves out the People commitment overlay, the Door does
not resolve owners to people, and the People readiness is not read. The
People rows are not hidden from the owner's own faces: those reads run outside
this block.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

_PEOPLE_FREE: ContextVar[bool] = ContextVar("holdspeak_people_free", default=False)


def people_reads_allowed() -> bool:
    """False inside ``no_people_reads()``."""
    return not _PEOPLE_FREE.get()


@contextmanager
def no_people_reads() -> Iterator[None]:
    token = _PEOPLE_FREE.set(True)
    try:
        yield
    finally:
        _PEOPLE_FREE.reset(token)
