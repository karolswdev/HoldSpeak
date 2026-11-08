"""PARKED 20261108 (subtraction day, Lane R): tests of parked routes.

Moved from ``tests/integration/test_working_context_promotion.py``: test_the_browser_route_admits_promotion_and_lists_it_back. Not collected.
"""
from __future__ import annotations
"""HS-200-10 Lane B: the promotion VERB, through the real service.

Lane A built the BOUNDARY -- the three tables, the guarded FTS triggers, the
graph-route fence and the two relevance call-site belts -- and proved it by
writing `context_promotions` rows directly, in the order the verb must use.
This file drives the verb itself: `InterviewService.command()` with the two new
event kinds, on the transaction `command()` already opens.

The lesson this phase paid for twice: **a test that cannot fail on the real
path is not proof.**  So every fence here is exercised through
`InterviewService.command()` with a real Thread, a real user message and a real
part -- never by calling a private helper -- and every assertion is paired with
the case that must still SUCCEED, so a fence that over-reaches fails as loudly
as one that is missing.

Ordering (ruling C1): the boundary landed before the verb it bounds.
"""


import json
import uuid
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ServiceError
from holdspeak.services.interview_contracts import INTERVIEW_MODE_ID
from holdspeak.services.interview_service import InterviewService
from holdspeak.services.thread_modes import seed_modes
from holdspeak.services.thread_service import ThreadService

OWNER = Principal(PrincipalKind.OWNER, "hs-200-10-owner")
AGENT = Principal(PrincipalKind.AGENT, "hs-200-10-agent")

# D0's Tuesday sentence, carrying a token that appears in nothing else so an
# assertion can look at the actual bytes rather than at a ref list.
RARE = "kestrelmark"
CONSTRAINT = (
    f"We cannot take another {RARE} cutover without a rollback rehearsal. "
    "That is not negotiable."
)
TITLE = f"We cannot take another {RARE} cutover without a rollback rehearsal"


class Rig:
    """One Interview Thread, and the smallest honest way to drive it."""

    def __init__(self, db: Database, thread_id: str) -> None:
        self.db = db
        self.tid = thread_id
        self.svc = InterviewService(db)

    def say(self, text: str, *, sensitive: bool = False, draft: bool = False) -> str:
        message = self.db.threads.append_message(self.tid, role="user")
        self.db.threads.append_part(
            message.id, kind="text", text=text, sensitive=sensitive, draft=draft
        )
        return message.id

    def command(self, event: dict[str, Any], *, command_id: str | None = None,
                expected_revision: int | None = None) -> dict[str, Any]:
        revision = self.svc.get(self.tid)["revision"] if expected_revision is None else expected_revision
        return self.svc.command(
            OWNER, self.tid, command_id=command_id or uuid.uuid4().hex,
            expected_revision=revision, event=event,
        )

    def record(self, *, fact_id: str = "goal", quote: str = CONSTRAINT,
               text: str = "Rollback rehearsal before every cutover",
               basis: str = "stated", message_id: str | None = None) -> str:
        source = message_id or self.say(quote)
        self.command({"kind": "fact", "fact_id": fact_id, "text": text, "basis": basis,
                      "source_message_id": source, "quote": quote})
        return source

    def promote(self, *, fact_id: str = "goal", **extra: Any) -> dict[str, Any]:
        return self.command({"kind": "promote", "fact_id": fact_id, **extra})

    def rows(self, sql: str, params: tuple[Any, ...] = ()) -> list[Any]:
        with self.db._connection() as conn:
            return conn.execute(sql, params).fetchall()

    def note_for(self, result: dict[str, Any]) -> Any:
        return self.db.notes.get(result["promotion"]["target_ref"].split(":", 1)[1])

    def promotion_row(self, promotion_id: str) -> Any:
        return self.rows("SELECT * FROM context_promotions WHERE promotion_id=?", (promotion_id,))[0]

    def dependent(self, canonical_ref: str, consumer_id: str = "thought-1") -> Any:
        """Register one consumer of a record, the shape `_persist_manifest` writes.

        The reconcile point that writes these for real lives in
        `refinement_context_service._persist_manifest`, which this lane does not
        own; the revoke rule under test reads the row, it does not write it.
        """
        with self.db._connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO context_dependents(canonical_ref,consumer_kind,consumer_id,"
                "consumer_revision,bound_manifest_sha256,bound_at,stale_since,stale_reason) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (canonical_ref, "thought", consumer_id, 1, "sha256:manifest",
                 "2026-09-07T09:00:00Z", None, ""),
            )
        return consumer_id

    def dependent_state(self, canonical_ref: str, consumer_id: str = "thought-1") -> str:
        row = self.rows(
            "SELECT stale_reason FROM context_dependents WHERE canonical_ref=? AND consumer_id=?",
            (canonical_ref, consumer_id),
        )
        return str(row[0]["stale_reason"]) if row else "<missing>"

    def fts_ids(self) -> set[str]:
        return {str(row[0]) for row in self.rows("SELECT source_id FROM notes_memory_fts")}

    def fts_matches(self, term: str) -> set[str]:
        return {
            str(row[0])
            for row in self.rows("SELECT source_id FROM notes_memory_fts WHERE notes_memory_fts MATCH ?", (term,))
        }


@pytest.fixture
def rig(tmp_path: Path):
    db = Database(tmp_path / "promotion.db")
    seed_modes(db)
    thread = ThreadService(db, broadcast=lambda *_: None).create(recipe_id=INTERVIEW_MODE_ID)
    yield Rig(db, thread["id"])
    db.close()


# ── The verb: what a promotion writes, and what it refuses to write ──────


# ── F0 through the REAL verb: the body never reaches the corpus ──────────


# ── Revocation: the claim, not the record ───────────────────────────────


# ── Transport ───────────────────────────────────────────────────────────

# The two verbs that mint or unmake a canonical record.  They belong to the
# owner's browser and to nothing else.
PROMOTION_KINDS = frozenset({"promote", "revoke_promotion"})


def _mcp_source_strings() -> tuple[set[str], int]:
    """Every string CONSTANT in the MCP package, and how many files were read.

    Equality, not substring: a docstring that says the word `promote` is not a
    finding, an event kind that IS `"promote"` is.  Read by AST over the whole
    package rather than off one family's ``TOOLS``, because a dispatcher in any
    family could name the kind.
    """
    import ast

    import holdspeak

    root = Path(holdspeak.__file__).parent / "mcp"
    files = sorted(root.rglob("*.py"))
    constants: set[str] = set()
    for path in files:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                constants.add(node.value)
    return constants, len(files)


def _mcp_interview_kind_map() -> tuple[set[str], set[str]]:
    """The SHIPPING tool-name -> event-kind map, read out of `dispatch` by AST.

    Not a private constant the test could drift from: the literal the dispatcher
    actually indexes.  Returns (tool names it maps, event kinds it can produce).
    """
    import ast
    import inspect

    from holdspeak.mcp.families import interview as interview_family

    names: set[str] = set()
    kinds: set[str] = set()
    for node in ast.walk(ast.parse(inspect.getsource(interview_family))):
        if not isinstance(node, ast.Dict) or not node.keys:
            continue
        pairs = [
            (key.value, value.value)
            for key, value in zip(node.keys, node.values)
            if isinstance(key, ast.Constant) and isinstance(key.value, str)
            and isinstance(value, ast.Constant) and isinstance(value.value, str)
        ]
        if len(pairs) != len(node.keys) or not pairs:
            continue
        if all(name.startswith("interview.") for name, _ in pairs):
            names |= {name for name, _ in pairs}
            kinds |= {kind for _, kind in pairs}
    return names, kinds


@pytest.mark.requires_meeting
def test_the_browser_route_admits_promotion_and_lists_it_back(tmp_path: Path) -> None:
    """AC4 needs a `promotion_id` the owner can reach, so a READ route ships.

    Without it `revoke_promotion` is unreachable: `promotion_id` existed only
    inside the single `promote` response, and `interview.get` does not carry
    promotions.  The route is owner-only in the same shape as the verbs -- the
    check lives in the SERVICE, proved here against an agent principal, not
    only in the handler.
    """
    from fastapi.testclient import TestClient

    from holdspeak.db import get_database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    reset_database()
    try:
        db = get_database(tmp_path / "transport.db")
        seed_modes(db)
        server = MeetingWebServer(WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None, on_stop=lambda *_a, **_k: None,
            get_state=lambda: None), host="127.0.0.1")
        client = TestClient(server.app)
        tid = client.post("/api/threads", json={"recipe_id": INTERVIEW_MODE_ID}).json()["id"]
        rig = Rig(db, tid)
        rig.record()

        empty = client.get(f"/api/threads/{tid}/interview/promotions")
        assert empty.status_code == 200, empty.text
        assert empty.json() == {"promotions": []}

        promote = client.post(f"/api/threads/{tid}/interview", json={
            "command_id": "route-promote", "expected_revision": rig.svc.get(tid)["revision"],
            "event": {"kind": "promote", "fact_id": "goal"}})
        assert promote.status_code == 200, promote.text
        promotion = promote.json()["promotion"]
        assert promotion["minted"] is True

        # The whole point of the route: the id the owner needs to revoke.
        listed = client.get(f"/api/threads/{tid}/interview/promotions")
        assert listed.status_code == 200, listed.text
        assert [row["promotion_id"] for row in listed.json()["promotions"]] == [promotion["promotion_id"]]
        assert listed.json()["promotions"][0]["disclosure_state"] == "active"

        revoke = client.post(f"/api/threads/{tid}/interview", json={
            "command_id": "route-revoke", "expected_revision": rig.svc.get(tid)["revision"],
            "event": {"kind": "revoke_promotion",
                      "promotion_id": listed.json()["promotions"][0]["promotion_id"]}})
        assert revoke.status_code == 200, revoke.text
        assert revoke.json()["promotion"]["revoked"] == "source_claim"
        after = client.get(f"/api/threads/{tid}/interview/promotions")
        assert after.json()["promotions"][0]["disclosure_state"] == "revoked"

        # A kind the MCP map HAS and the browser allowlist does not: the
        # allowlist is a real gate, not a comment.
        refused = client.post(f"/api/threads/{tid}/interview", json={
            "command_id": "route-fact", "expected_revision": rig.svc.get(tid)["revision"],
            "event": {"kind": "fact", "fact_id": "sneak", "text": "x", "basis": "stated",
                      "source_message_id": "m", "quote": "y"}})
        # The body matters, not just the code: admitting `fact` would ALSO
        # answer 400 (its own validation refuses the forged source message), so
        # a status-only assertion cannot tell the gate from the fallout.
        assert refused.status_code == 400, refused.text
        assert refused.json() == {"error": "Unsupported interview control"}

        # Owner-only, enforced where the verbs enforce it.
        with pytest.raises(ServiceError) as denied:
            InterviewService(db).promotions(AGENT, tid)
        assert denied.value.code == "owner_required"
    finally:
        reset_database()


