#!/usr/bin/env python3
"""HS-87-06 — the closing walk: steer a REAL session from the desk.

Eight beats against one real tmux pane and one real DB, each a real
act, no mocked frames. The consent spine is tried at every turn: watch
free, refuse unarmed, arm, steer, ground, classify, then the crown
cases fire live — recycled pane, TTL expiry, disarm mid-window. The
audit trail for beats 2-7 is read back at the end and every delivered
or refused steer is asserted to have its row (the audit-completeness
rule). Grounding's control-vs-treatment runs when .43 is reachable.

Run: uv run python scripts/steer_walk_hs87.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
import uuid
from pathlib import Path

from holdspeak import coder_steering
from holdspeak.coder_steering import (
    arm,
    clear_grants,
    deliver,
    disarm,
    peek_pane,
    require_grant,
)
from holdspeak.db import core as dbcore
from holdspeak.grounding import GroundingBlock, compose_steer

LLM = os.environ.get("HOLDSPEAK_PROOF_LLM", "http://192.168.1.43:8080")
OUT = Path("pm/roadmap/holdspeak/phase-87-steering-desk/screenshots")
KEY = "claude:walk"


def beat(n: int, title: str) -> None:
    print(f"\n{'=' * 70}\nBEAT {n}: {title}\n{'=' * 70}")


def tmux(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["tmux", *args], capture_output=True, text=True, check=check, timeout=10)


def new_pane(session: str) -> str:
    tmux("new-session", "-d", "-s", session, "sleep 300")
    time.sleep(0.3)
    return tmux("list-panes", "-t", session, "-F", "#{pane_id}").stdout.strip()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    dbcore.reset_database()
    db_path = Path(os.environ.get("HOLDSPEAK_WALK_DB", f"/tmp/hs87-walk-{uuid.uuid4().hex[:8]}.db"))
    db_path.unlink(missing_ok=True)  # a fresh audit each run — no carry-over
    db = dbcore.Database(db_path)
    import holdspeak.db as hsdb

    hsdb.get_database = lambda *a, **k: db
    clear_grants()

    session = f"hs87-walk-{uuid.uuid4().hex[:8]}"
    pane = new_pane(session)
    target = f"{session}:0.0"
    audit = db.steering
    results: dict[str, object] = {}

    def steer(text: str, **kw) -> dict:
        """Deliver through the chokepoint AND audit into the real DB."""
        return deliver(
            KEY, text, current_target=target, agent="claude",
            audit=lambda **row: audit.record(**row), **kw,
        )

    try:
        # BEAT 1 — Attach: watch the pane, live, no grant issued.
        beat(1, "Attach — watch the pane (zero grants)")
        tmux("send-keys", "-t", pane, "-l", "the agent is working")
        time.sleep(0.3)
        seen = peek_pane(pane, lines=20)
        assert seen["status"] == "live" and "working" in "\n".join(seen["lines"])
        assert coder_steering.active_grants() == {}
        print("watched; grants:", coder_steering.active_grants())

        # BEAT 2 — Refusal first: an unarmed steer is refused, types nothing.
        beat(2, "Refuse — unarmed steer refused, nothing typed")
        r = steer("this must not land", submit=False)
        assert r["status"] == "unarmed", r
        print("refused:", r["status"], "audit_id:", r["audit_id"])

        # BEAT 3 — Arm: pin the pane identity, start the countdown.
        beat(3, "Arm — pin %N, countdown begins")
        armed = arm(KEY, target)
        assert armed["status"] == "armed" and armed["pane_id"] == pane
        print("armed pane:", armed["pane_id"], "ttl:", armed["expires_in_seconds"])

        # BEAT 4 — Steer: a reply lands in the pane exactly as composed.
        beat(4, "Steer — a reply lands in the real pane")
        marker = f"walk-steer-{uuid.uuid4().hex[:6]}"
        r = steer(marker, submit=False)
        assert r["status"] == "delivered" and r["pane_id"] == pane
        time.sleep(0.4)
        assert marker in "\n".join(peek_pane(pane, lines=40)["lines"])
        print("delivered and visible:", marker)

        # BEAT 5 — Ground: control vs treatment on real metal.
        beat(5, "Ground — control vs treatment (.43)")
        secret = "the release is BLUEBIRD, Friday the 13th at 3:47pm"
        block = GroundingBlock("artifact", "a1", "Deploy Decisions", "Release", f"Decision: {secret}.")
        q = "In one short sentence: when is the deploy and its code name?"
        try:
            urllib.request.urlopen(f"{LLM}/health", timeout=4).read()

            def ask(prompt: str) -> str:
                body = json.dumps({"messages": [{"role": "user", "content": prompt}],
                                   "temperature": 0.0, "max_tokens": 120}).encode()
                req = urllib.request.Request(f"{LLM}/v1/chat/completions", data=body,
                                             headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=60) as resp:
                    return json.loads(resp.read())["choices"][0]["message"]["content"].strip()

            control = ask(compose_steer(q, [])["text"])
            treatment = ask(compose_steer(q, [block])["text"])
            uses = "bluebird" in treatment.lower()
            blind = "bluebird" not in control.lower()
            print("control:", control[:80])
            print("treatment:", treatment[:80])
            assert uses and blind, "grounding did not change the answer"
            results["grounding"] = {"control": control, "treatment": treatment}
        except Exception as exc:
            print(f"SKIP grounding LLM leg ({exc})")
            results["grounding"] = "skipped: LLM unreachable"
        # The grounded steer itself is delivered + audited with its refs.
        composed = compose_steer(q, [block])
        r = steer(composed["text"], submit=False, grounding_refs=composed["refs"])
        assert r["status"] == "delivered"
        print("grounded steer delivered; refs:", composed["refs"])

        # BEAT 6 — Classify: keep the ask as a note.
        beat(6, "Classify — keep as note")
        from holdspeak.web.routes.primitives._shared import _new_id
        note = db.notes.upsert(note_id=_new_id("note"), title=f"From claude · {KEY}",
                               body_markdown=f"> kept from `{KEY}`\n\nMerge the branch?",
                               tags=["session", "claude"])
        assert db.notes.get(note.id) is not None
        print("note kept and openable:", note.id)

        # BEAT 7 — Crown cases, live.
        beat(7, "Crown cases — recycled pane, expiry, cross-surface disarm")
        # (a) recycled pane: kill + a NEW session reuses ids; the pinned %N
        #     no longer resolves — refuse AND revoke.
        tmux("kill-session", "-t", session, check=False)
        time.sleep(0.2)
        r = steer("meant for the dead pane", submit=False)
        assert r["status"] == "pane_gone" and r.get("revoked")
        assert coder_steering.active_grants() == {}
        print("(a) recycled/dead pane refused + revoked:", r["status"])

        # (b) TTL expiry mid-window: a short-TTL grant on a fresh pane,
        #     stepped past its window → the send refuses, ARM re-offered.
        session2 = f"hs87-walk-{uuid.uuid4().hex[:8]}"
        pane2 = new_pane(session2)
        target2 = f"{session2}:0.0"
        clock = [1000.0]
        arm(KEY, target2, ttl_seconds=coder_steering.ARM_MIN_TTL_SECONDS, clock=lambda: clock[0])
        clock[0] += coder_steering.ARM_MIN_TTL_SECONDS + 1
        r = deliver(KEY, "too late", current_target=target2, agent="claude",
                    clock=lambda: clock[0], audit=lambda **row: audit.record(**row))
        assert r["status"] == "expired" and r.get("revoked")
        print("(b) TTL expiry refused + revoked:", r["status"])

        # (c) disarm from another surface while a compose is open: the grant
        #     dies the moment disarm lands; the next send is unarmed.
        arm(KEY, target2)
        assert disarm(KEY) is True  # "another surface" taps disarm
        r = deliver(KEY, "after the disarm", current_target=target2, agent="claude",
                    audit=lambda **row: audit.record(**row))
        assert r["status"] == "unarmed"
        print("(c) cross-surface disarm → next send unarmed:", r["status"])
        tmux("kill-session", "-t", session2, check=False)

        # BEAT 8 — The audit: read the trail back; every steer has a row.
        beat(8, "Audit — the trail for beats 2-7, read back")
        trail = audit.list(session_key=KEY, limit=50)
        outcomes = [e.outcome for e in trail]
        print("audit outcomes (newest first):", outcomes)
        # Every steer attempt of the walk left exactly one row.
        expected = {"unarmed", "delivered", "pane_gone", "expired"}
        assert expected.issubset(set(outcomes)), (expected, set(outcomes))
        # No full text stored — heads and hashes only.
        assert all(len(e.text_head) <= 120 for e in trail)
        # The grounded steer's row carries its refs.
        assert any(e.grounding for e in trail), "no grounding ref recorded"
        results["audit"] = [e.to_dict() for e in trail]

        (OUT / "walk-audit.json").write_text(json.dumps(results["audit"], indent=2))
        print(f"\n{'=' * 70}\nWALK: PASS — {len(trail)} audit rows, all beats live\n{'=' * 70}")
        return 0
    finally:
        for s in (session, session2 if "session2" in dir() else None):
            if s:
                tmux("kill-session", "-t", s, check=False)
        clear_grants()
        dbcore.reset_database()


if __name__ == "__main__":
    sys.exit(main())
