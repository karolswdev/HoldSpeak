# PARKED 2026-11-12: persistence of unused next actions is retired.
from holdspeak.cadence.models import NextBestAction, Nudge
from holdspeak.db import Database

def test_next_action_and_nudge_persist(db: Database):
    loop = db.cadence.upsert_loop(_loop())
    aid = db.cadence.add_next_action(
        NextBestAction(loop_id=loop.id, kind="create_issue", title="Draft issue", confidence=0.9)
    )
    nid = db.cadence.record_nudge(
        Nudge(loop_id=loop.id, surface="cli", next_action_id=aid, title="File it")
    )
    assert aid and nid

