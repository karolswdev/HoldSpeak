"""Entity resolution for memory facts (MEMORY-DESIGN.md §3.1 step 6).

Hindsight's score, without Postgres (``H/engine/memories/pg/entity_resolver.py``):

    score = 0.5 x name similarity + 0.3 x shared neighbours + 0.2 x closeness in time

A mention joins the best candidate of the same kind at ``MATCH_SCORE`` (0.6)
or more; below that it is a new entity.  Two rules are code, never a model
guess:

* **The per-token guard.**  Two names of two or more words that have a word
  each that the other does not have ("John Smith", "Jane Smith") are never
  one entity, however high the rest of the score is.  An initial is the same
  word as the name it starts ("J. Smith", "John Smith").
* **The initial rule.**  A name with a given name cut to its initial and
  the same surname ("T. Wierzbicki", "Tomasz Wierzbicki") joins at
  ``MATCH_SCORE`` whatever the rest of the score is, but only when the guard
  passes on every name the candidate is known by and no second candidate
  could take it.
* **No model merge.**  Nothing here calls a model.

Candidates come from SQL: the same kind, and a name that starts the same or
shares a word.  Everything runs inside the caller's transaction, so the
entities of a job commit with its facts or not at all.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import re
import sqlite3
import unicodedata
from datetime import datetime, timezone
from typing import Iterable, Optional, Sequence

#: The kinds of entity memory holds.  A kind the model gives that is not here
#: is stored as ``topic``.
ENTITY_KINDS = ("person", "project", "system", "org", "topic")
MATCH_SCORE = 0.6
NAME_WEIGHT = 0.5
NEIGHBOUR_WEIGHT = 0.3
TIME_WEIGHT = 0.2
TIME_WINDOW_DAYS = 7.0
NAME_MAX_CHARS = 120

#: Words that name no one: a pronoun or the speaker label of the owner.
_NOT_A_NAME = frozenset(
    "i me my mine we us our you your he him his she her they them their it its "
    "someone somebody everyone everybody nobody team the owner owner speaker "
    "remote user assistant unknown".split()
)
_WORD = re.compile(r"[\w][\w'.-]*", re.UNICODE)


def fold_words(text: str) -> list[str]:
    """Lower case, accents off, no punctuation at the ends of words."""
    value = unicodedata.normalize("NFKD", str(text or ""))
    value = "".join(char for char in value if not unicodedata.combining(char))
    words = [word.strip(".,;:'\"()[]{}!?-") for word in value.casefold().split()]
    words = [word[:-2] if word.endswith("'s") else word for word in words]
    return [word for word in words if word]


def fold(name: str) -> str:
    """The ``name_key``: lower case, accents off, one space between words,
    no leading "the", no punctuation at the ends of words."""
    words = fold_words(name)
    if len(words) > 1 and words[0] == "the":
        words = words[1:]
    return " ".join(words)[:NAME_MAX_CHARS]


def fold_question(text: str) -> str:
    """A whole question folded as names are, with no length cut."""
    return " ".join(fold_words(text))


def tokens(name_key: str) -> list[str]:
    return [token for token in name_key.split(" ") if token]


def is_name(name: str) -> bool:
    """False for a pronoun, the owner's speaker label, or an empty name."""
    key = fold(name)
    return bool(key) and key not in _NOT_A_NAME and any(char.isalnum() for char in key)


def entity_kind(kind: str) -> str:
    value = str(kind or "").strip().lower()
    return value if value in ENTITY_KINDS else "topic"


def entity_id(kind: str, name_key: str) -> str:
    """A stable id: the same name of the same kind is the same id on every
    build, so ``holdspeak memory rebuild`` gives the same rows."""
    digest = hashlib.sha256(f"{kind}\x1f{name_key}".encode("utf-8")).hexdigest()
    return f"ent_{digest[:20]}"


def _same_word(left: str, right: str) -> bool:
    """One word of a name against one word of the other: equal, or one is
    the initial of the other ("j" or "j." against "john")."""
    left, right = left.rstrip("."), right.rstrip(".")
    if left == right:
        return True
    if len(left) == 1 and right.startswith(left):
        return True
    return len(right) == 1 and left.startswith(right)


def token_guard(left_key: str, right_key: str) -> bool:
    """True when the two names MAY be one entity.

    Two names of two or more words where each has a word the other lacks are
    two entities: "John Smith" and "Jane Smith", "Dana Lee" and "Dana Kim".
    A one-word name against a longer one ("Dana", "Dana Lee") passes; the
    rest of the score decides.
    """
    left, right = tokens(left_key), tokens(right_key)
    if len(left) < 2 or len(right) < 2:
        return True
    left_only = [word for word in left if not any(_same_word(word, other) for other in right)]
    right_only = [word for word in right if not any(_same_word(word, other) for other in left)]
    return not (left_only and right_only)


def initial_form(left_key: str, right_key: str) -> bool:
    """True when one name is the other with a given name cut to its initial:
    "t wierzbicki" and "tomasz wierzbicki".

    The rule is narrow on purpose: the same number of words, the LAST word
    (the surname) equal and longer than one letter, every other word equal or
    the initial of the other, and at least one initial.  "J. Smith" against
    "John Smith" is True; against "Jane Smith" it is True too, so two full
    names of one surname make the mention ambiguous and ``resolve`` keeps it
    its own entity (one match only).
    """
    left, right = tokens(left_key), tokens(right_key)
    if len(left) < 2 or len(left) != len(right):
        return False
    if left[-1] != right[-1] or len(left[-1]) < 2:
        return False
    initials = 0
    for one, other in zip(left[:-1], right[:-1]):
        one, other = one.rstrip("."), other.rstrip(".")
        if one == other:
            continue
        if not _same_word(one, other):
            return False
        initials += 1
    return initials > 0


def name_similarity(left_key: str, right_key: str) -> float:
    if left_key == right_key:
        return 1.0
    return difflib.SequenceMatcher(None, left_key, right_key).ratio()


def _instant(value: Optional[str]) -> Optional[datetime]:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = datetime.fromisoformat(text[:10])
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def time_closeness(seen: Optional[str], first: Optional[str], last: Optional[str]) -> float:
    """1.0 inside the candidate's seen range, falling to 0 at seven days."""
    at = _instant(seen)
    low, high = _instant(first), _instant(last)
    if at is None or (low is None and high is None):
        return 0.0
    low = low or high
    high = high or low
    if low <= at <= high:
        return 1.0
    gap = min(abs((at - low).total_seconds()), abs((at - high).total_seconds())) / 86400.0
    return max(0.0, 1.0 - gap / TIME_WINDOW_DAYS)


def score(
    name_key: str,
    candidate_keys: Sequence[str],
    neighbours: set[str],
    candidate_neighbours: set[str],
    seen: Optional[str],
    first_seen: Optional[str],
    last_seen: Optional[str],
) -> float:
    """Hindsight's score for one candidate.  0.0 when the token guard says
    the new name and ANY name the candidate is known by (its name or one of
    its aliases) are two people (or two things).  A chain cannot walk round
    the guard: "J. Smith" may join "John Smith", and "Jane Smith" then still
    meets "John Smith"."""
    if not all(token_guard(name_key, key) for key in candidate_keys):
        return 0.0
    name = max(name_similarity(name_key, key) for key in candidate_keys)
    shared = (len(neighbours & candidate_neighbours) / len(neighbours)) if neighbours else 0.0
    closeness = time_closeness(seen, first_seen, last_seen)
    value = NAME_WEIGHT * name + NEIGHBOUR_WEIGHT * shared + TIME_WEIGHT * closeness
    if any(initial_form(name_key, key) for key in candidate_keys):
        # The initial rule: "T. Wierzbicki" is "Tomasz Wierzbicki" when the
        # guard passed on every known name.  Ambiguity (two full names of
        # one surname) is ``resolve``'s one-match rule.
        return max(value, MATCH_SCORE)
    return value


def _candidates(conn: sqlite3.Connection, kind: str, name_key: str) -> list[sqlite3.Row]:
    """Same kind; a name that starts the same, or shares a word (SQL)."""
    words = [word for word in tokens(name_key) if len(word) >= 2][:6]
    return conn.execute(
        """SELECT id,name,name_key,aliases_json,first_seen,last_seen FROM memory_entities
           WHERE kind=? AND (name_key LIKE ? OR EXISTS (
             SELECT 1 FROM json_each(?) w
              WHERE (' '||name_key||' ') LIKE '% '||w.value||' %'
                 OR aliases_json LIKE '%'||w.value||'%'))
           ORDER BY id""",
        (kind, name_key[:3] + "%", json.dumps(words)),
    ).fetchall()


def _neighbours_of(conn: sqlite3.Connection, entity: str) -> set[str]:
    """The name keys of the entities that share a live fact with ``entity``."""
    return {
        str(row[0])
        for row in conn.execute(
            """SELECT DISTINCT e.name_key FROM memory_fact_entities mine
               JOIN memory_facts f ON f.id=mine.fact_id AND f.state='live'
               JOIN memory_fact_entities other ON other.fact_id=mine.fact_id
                AND other.entity_id<>mine.entity_id
               JOIN memory_entities e ON e.id=other.entity_id
               WHERE mine.entity_id=?""",
            (entity,),
        )
    }


def _aliases(raw: str) -> list[str]:
    try:
        value = json.loads(raw or "[]")
    except ValueError:
        return []
    return [str(item) for item in value] if isinstance(value, list) else []


def resolve(
    conn: sqlite3.Connection,
    *,
    name: str,
    kind: str,
    neighbours: Iterable[str] = (),
    seen: Optional[str] = None,
) -> str:
    """The entity id for one mention; a new entity below ``MATCH_SCORE``.

    ``neighbours`` are the other names in the same fact.  Runs in the
    caller's transaction.  The matched entity takes the mention's name as an
    alias and widens its seen range.

    One match only: when two entities could take the mention ("Dana" next
    to "Dana Lee" and "Dana Kim"), it is its own entity, so a short name can
    never join two people.
    """
    kind = entity_kind(kind)
    display = " ".join(str(name or "").split())[:NAME_MAX_CHARS]
    key = fold(display)
    near = {fold(item) for item in neighbours if is_name(item)} - {key}
    own: Optional[sqlite3.Row] = None
    by_alias: list[sqlite3.Row] = []
    scored: list[tuple[float, sqlite3.Row]] = []
    for row in _candidates(conn, kind, key):
        keys = [str(row["name_key"])] + [fold(alias) for alias in _aliases(row["aliases_json"])]
        if key == str(row["name_key"]):
            own = row
            break
        if key in keys:
            by_alias.append(row)
            continue
        value = score(
            key, keys, near, _neighbours_of(conn, str(row["id"])), seen,
            row["first_seen"], row["last_seen"],
        )
        if value >= MATCH_SCORE:
            scored.append((value, row))
    best: Optional[sqlite3.Row] = None
    best_score = 0.0
    if own is not None:
        best, best_score = own, 1.0
    elif len(by_alias) == 1:
        best, best_score = by_alias[0], 1.0
    elif not by_alias and len(scored) == 1:
        best_score, best = scored[0]
    if best is None or best_score < MATCH_SCORE:
        new_id = entity_id(kind, key)
        conn.execute(
            "INSERT INTO memory_entities(id,kind,name,name_key,aliases_json,first_seen,last_seen,mention_count)"
            " VALUES (?,?,?,?,'[]',?,?,0)"
            " ON CONFLICT(id) DO UPDATE SET"
            " first_seen=CASE WHEN excluded.first_seen IS NOT NULL AND"
            "  (memory_entities.first_seen IS NULL OR excluded.first_seen<memory_entities.first_seen)"
            "  THEN excluded.first_seen ELSE memory_entities.first_seen END,"
            " last_seen=CASE WHEN excluded.last_seen IS NOT NULL AND"
            "  (memory_entities.last_seen IS NULL OR excluded.last_seen>memory_entities.last_seen)"
            "  THEN excluded.last_seen ELSE memory_entities.last_seen END",
            (new_id, kind, display, key, seen, seen),
        )
        return new_id
    entity = str(best["id"])
    aliases = _aliases(best["aliases_json"])
    if key != str(best["name_key"]) and display not in aliases:
        aliases.append(display)
    first = min((value for value in (best["first_seen"], seen) if value), default=None)
    last = max((value for value in (best["last_seen"], seen) if value), default=None)
    conn.execute(
        "UPDATE memory_entities SET aliases_json=?,first_seen=?,last_seen=? WHERE id=?",
        (json.dumps(sorted(aliases), ensure_ascii=False), first, last, entity),
    )
    return entity


def recount(conn: sqlite3.Connection, entity_ids: Iterable[str]) -> None:
    """Set ``mention_count`` from the live links, and remove an entity that no
    live or kept fact names any more (its name came only from facts that are
    gone)."""
    for entity in sorted(set(entity_ids)):
        count = int(conn.execute(
            """SELECT count(DISTINCT fe.fact_id) FROM memory_fact_entities fe
               JOIN memory_facts f ON f.id=fe.fact_id AND f.state='live'
               WHERE fe.entity_id=?""",
            (entity,),
        ).fetchone()[0])
        linked = conn.execute(
            "SELECT 1 FROM memory_fact_entities WHERE entity_id=? LIMIT 1", (entity,)
        ).fetchone()
        if linked is None:
            conn.execute("DELETE FROM memory_entities WHERE id=?", (entity,))
        else:
            conn.execute("UPDATE memory_entities SET mention_count=? WHERE id=?", (count, entity))


__all__ = [
    "ENTITY_KINDS",
    "MATCH_SCORE",
    "entity_id",
    "entity_kind",
    "fold",
    "fold_question",
    "fold_words",
    "initial_form",
    "is_name",
    "name_similarity",
    "recount",
    "resolve",
    "score",
    "token_guard",
    "tokens",
]
