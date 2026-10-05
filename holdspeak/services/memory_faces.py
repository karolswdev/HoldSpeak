"""Memory on the Desk (canvas section 2, option B "Where the work lives").

The read shapes the three faces draw, made from the merged read APIs and
nothing else:

* **beliefs** -- one more kind of the Desk memory recall card.  Made from
  ``consolidate.read_observations`` (served text, live evidence, the
  history a reader may see).  Each evidence ref carries the short token the
  boards name (``MTG 10-01 · 14:20``, ``DEC 10-01``, ``CMT 10-01``) and
  ``against`` when it contradicts the belief.  A current belief that
  superseded an older one holds the old text in its history.
* **standing pages** -- the fixed page set of one scope (``pages.PAGE_SET``),
  each read by ``pages.read`` (no model call).  A page that serves no
  sentence is not in the list.  The withheld count is NOT in the shape: a
  withheld sentence is simply not drawn.  ``new_sources`` counts the
  sources in scope that changed after the page saw the scope.

Nothing here reads the People store: memory admits no People kind, and no
People field, alias or id steers a read here.  Every text was redacted by
the read API it came from.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Iterable, Optional

from ..memory.consolidate import ScopeReader, read_observations
from ..memory.pages import PAGE_SET, read as read_page

#: The token word for each ref kind the Desk opens (the boards' grammar).
_TOKEN_WORD = {
    "meeting": "MTG",
    "transcript": "MTG",
    "decision": "DEC",
    "desk_decision": "DEC",
    "decision_record": "DEC",
    "action_item": "CMT",
    "action": "CMT",
    "note": "NOTE",
    "thread": "THREAD",
    "artifact": "ARTIFACT",
}

#: A history row's reason as the consolidator writes it:
#: ``refines: <why>`` / ``superseded by <id>: <why>`` / ``disputed by <id>: <why>``.
_REASON = re.compile(r"^(refines|superseded by \S+|disputed by \S+):\s*(.*)$", re.DOTALL)
_REASON_WORD = {"refines": "REFINED", "superseded": "SUPERSEDED", "disputed": "DISPUTED"}

#: The wordless Desk memory read shows this many beliefs at most.
RECENT_BELIEFS = 10


def _parse(stamp: Any) -> Optional[datetime]:
    if not stamp or not isinstance(stamp, str):
        return None
    try:
        parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = datetime.fromisoformat(stamp[:10])
        except ValueError:
            return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed


def day(stamp: Any) -> str:
    """``10-01``: the day of a stamp, local; "" when there is none."""
    parsed = _parse(stamp)
    return parsed.strftime("%m-%d") if parsed else ""


#: The other names memory gives the record a Desk ref names (a Desk ref says
#: ``action_item:`` / ``decision:``; memory's ledger says ``action:`` /
#: ``decision_record:`` or ``desk_decision:``).
_ALIASES = {
    "action_item": ("action",),
    "decision": ("decision_record", "desk_decision"),
    "desk_decision": ("decision",),
    "meeting": ("transcript",),
}


def _names(ref: str) -> list[str]:
    base = str(ref).split("#", 1)[0]
    kind, _, rest = base.partition(":")
    return [base, *(f"{alias}:{rest}" for alias in _ALIASES.get(kind, ()))]


def ref_tokens(conn: Any, refs: Iterable[str]) -> dict[str, str]:
    """The short token of each ref, dated from memory's own source ledger
    (``memory_sources.occurred_at``): ``MTG 10-01 · 14:20``, ``DEC 10-01``.
    A ref memory holds no date for reads as its kind word alone."""
    out: dict[str, str] = {}
    for ref in dict.fromkeys(str(r) for r in refs):
        kind = ref.split(":", 1)[0]
        word = _TOKEN_WORD.get(kind, kind.replace("_", " ").upper())
        names = _names(ref)
        row = conn.execute(
            "SELECT occurred_at FROM memory_sources WHERE source_ref IN (SELECT value FROM json_each(?))"
            " AND occurred_at IS NOT NULL ORDER BY occurred_at DESC LIMIT 1",
            (json.dumps(names),),
        ).fetchone()
        parsed = _parse(row[0]) if row else None
        if parsed is None:
            out[ref] = word
        elif word == "MTG":
            out[ref] = f"MTG {parsed.strftime('%m-%d')} · {parsed.strftime('%H:%M')}"
        else:
            out[ref] = f"{word} {parsed.strftime('%m-%d')}"
    return out


def _reason(raw: str) -> tuple[str, str]:
    """(``SUPERSEDED``, ``freeze moved``) from a stored history reason."""
    match = _REASON.match(str(raw or "").strip())
    if not match:
        return "", str(raw or "").strip()
    return _REASON_WORD.get(match.group(1).split(" ", 1)[0], ""), match.group(2).strip()


def _project_names(conn: Any) -> dict[str, str]:
    try:
        return {str(r[0]): str(r[1] or r[0]) for r in conn.execute("SELECT id,name FROM projects")}
    except Exception:  # pragma: no cover - a desk with no projects table
        return {}


def belief_cards(db: Any, observations: list[dict[str, Any]], *, every: Optional[list[dict[str, Any]]] = None) -> list[dict[str, Any]]:
    """The belief cards of ``observations`` (``read_observations`` rows).

    ``every`` is the full served set the predecessors are found in (a
    current belief that superseded an older one holds the old text in its
    history); default ``observations``."""
    pool = every if every is not None else observations
    successors: dict[str, list[dict[str, Any]]] = {}
    for row in pool:
        if row.get("state") == "superseded" and row.get("superseded_by"):
            successors.setdefault(str(row["superseded_by"]), []).append(row)
    with db._connection() as conn:
        names = _project_names(conn)
        refs = [e["ref"] for row in observations for e in row.get("evidence", [])]
        tokens = ref_tokens(conn, refs)
    cards: list[dict[str, Any]] = []
    for row in observations:
        evidence: list[dict[str, Any]] = []
        seen: set[tuple[str, bool]] = set()
        ordered = sorted(row.get("evidence", []), key=lambda e: e.get("stance") == "contradicts")
        for item in ordered:
            against = item.get("stance") == "contradicts"
            key = (str(item["ref"]), against)
            if key in seen:
                continue
            seen.add(key)
            evidence.append({
                "ref": str(item["ref"]),
                "token": tokens.get(str(item["ref"]), ""),
                "opens": bool(item.get("opens")),
                "against": against,
            })
        history: list[dict[str, Any]] = []
        since = ""
        for item in row.get("history", []):
            word, why = _reason(item.get("reason", ""))
            if word == "SUPERSEDED" and row.get("state") == "superseded":
                since = since or day(item.get("at"))
            if word == "REFINED" and item.get("prior_text"):
                history.append({"at": day(item.get("at")), "text": str(item["prior_text"]),
                                "word": word, "reason": why})
        for old in successors.get(str(row["id"]), []):
            for item in old.get("history", []):
                word, why = _reason(item.get("reason", ""))
                if word == "SUPERSEDED":
                    history.append({"at": day(item.get("at")), "text": str(old["text"]),
                                    "word": word, "reason": why})
                    break
        history.sort(key=lambda h: h["at"], reverse=True)
        scope = row.get("scope") or {}
        project = None
        if scope.get("kind") == "project" and scope.get("id"):
            project = {"id": str(scope["id"]), "name": names.get(str(scope["id"]), str(scope["id"]))}
        cards.append({
            "id": str(row["id"]),
            "kind": "belief",
            "text": str(row["text"]),
            "state": str(row["state"]),
            # The facts that back it (``proof_count``) and the DISTINCT
            # sources they come from: the card says SOURCES, so it counts
            # sources (Astra, PR #877 P2: one note, two facts = 1 SOURCE).
            "proof_count": int(row.get("proof_count") or 0),
            "source_count": len({e["ref"].split("#", 1)[0] for e in evidence if not e["against"]}),
            "seen": day(row.get("last_seen")),
            "since": since,
            "project": project,
            "evidence": evidence,
            "history": history,
        })
    return cards


def recall_beliefs(db: Any, query: str, *, recent: bool = False, limit: int = 50) -> list[dict[str, Any]]:
    """The beliefs a Desk memory recall draws: every served belief whose
    text or evidence holds every word of ``query``; with no query (the
    recent read) the newest current and disputed ones."""
    every = read_observations(db, limit=200)
    terms = [t for t in str(query or "").casefold().split() if t]
    if terms:
        def holds(row: dict[str, Any]) -> bool:
            hay = " ".join([str(row["text"]), *(str(e.get("fact") or "") for e in row.get("evidence", []))]).casefold()
            return all(term in hay for term in terms)
        chosen = [row for row in every if holds(row)]
    elif recent:
        chosen = [row for row in every if row["state"] in ("current", "disputed")][:RECENT_BELIEFS]
    else:
        chosen = []
    order = {"current": 0, "disputed": 1, "superseded": 2}
    chosen.sort(key=lambda r: order.get(str(r["state"]), 3))
    return belief_cards(db, chosen[: max(1, int(limit))], every=every)


def _new_sources(db: Any, scope: tuple[str, str], slug: str) -> int:
    """The sources in ``scope`` stamped after the page saw the scope
    (``last_memory_seen_at``).  Called only for a page ``pages.read`` calls
    stale (the content digest, ``pages.is_stale``): this is the count the
    chip names, not the staleness rule.  A change the clock cannot place
    after the page (a refile, an edit in the same second) counts 0, and the
    chip then reads ``STALE`` alone.  Public names only: no private import
    of ``pages``."""
    with db._connection() as conn:
        row = conn.execute(
            "SELECT last_memory_seen_at FROM memory_pages WHERE scope_kind=? AND scope_id=? AND slug=?",
            (*scope, slug),
        ).fetchone()
        if row is None:
            return 0
        scopes = ScopeReader(conn)
        return sum(
            1 for (ref,) in conn.execute(
                "SELECT source_ref FROM memory_sources WHERE updated_at>?", (str(row[0]),)
            ) if scopes.in_scope(str(ref), scope)
        )


def standing_pages(db: Any, scope_kind: str, project_id: str = "") -> list[dict[str, Any]]:
    """The served pages of one scope, in the fixed order (``PAGE_SET``)."""
    scope = (scope_kind, project_id if scope_kind == "project" else "")
    out: list[dict[str, Any]] = []
    for spec in PAGE_SET[scope_kind]:
        page = read_page(db, scope[0], scope[1], spec.slug)
        if page is None:
            continue
        with db._connection() as conn:
            tokens = ref_tokens(conn, [r["ref"] for s in page["sentences"] for r in s["refs"]])
        out.append({
            "slug": spec.slug,
            "question": page["question"],
            "sentences": [
                {"text": s["text"],
                 "refs": [{"ref": r["ref"], "opens": bool(r["opens"]), "token": tokens.get(r["ref"], "")}
                          for r in s["refs"]]}
                for s in page["sentences"]
            ],
            "built_at": page["built_at"],
            "stale": bool(page["stale"]),
            "new_sources": _new_sources(db, scope, spec.slug) if page["stale"] else 0,
            "model": page["model"],
            "boundary": page["boundary"],
        })
    return out


__all__ = ["belief_cards", "day", "recall_beliefs", "ref_tokens", "standing_pages"]
