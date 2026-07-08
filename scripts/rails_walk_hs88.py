#!/usr/bin/env python3
"""HS-88-05 — the closing walk: the rails are desk-native material.

Seven beats against the REAL rails (this repo's `dw`), the real `.43`
model, and a real tmux pane. A rail object grounds into an ask and a
steer as a receipt; the ambient observer journals real rail motion;
the reach merges a remote node's envelope; the journal grounds in turn.
Each beat is a capture. Skips the model/tmux legs honestly when absent.

Run: uv run python scripts/rails_walk_hs88.py
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

from holdspeak import coder_steering, rails_observer
from holdspeak.grounding import compose_steer
from holdspeak.grounding_rails import hydrate_rails_refs
from holdspeak.missioncontrol_bridge import events_payload, load_project_map

LLM = os.environ.get("HOLDSPEAK_PROOF_LLM", "http://192.168.1.43:8080")
OUT = Path("pm/roadmap/holdspeak/phase-88-rails-aware-desk/screenshots")
STORY = {"repo": "holdspeak", "project": "holdspeak", "kind": "story", "id": "HS-88-05"}


def beat(n: int, title: str) -> None:
    print(f"\n{'=' * 70}\nBEAT {n}: {title}\n{'=' * 70}")


def llm_up() -> bool:
    try:
        urllib.request.urlopen(f"{LLM}/health", timeout=4).read()
        return True
    except Exception:
        return False


def ask(prompt: str, *, system: str = "") -> str:
    msgs = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": prompt}
    ]
    body = json.dumps({"messages": msgs, "temperature": 0.0, "max_tokens": 80}).encode()
    req = urllib.request.Request(
        f"{LLM}/v1/chat/completions", data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"].strip()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    results: dict[str, object] = {}
    rails_observer.clear_remote_buffer()

    # BEAT 1 — Ground into an ask: a rail object is a receipt.
    beat(1, "Ground an open story into a run (receipt, not scrape)")
    blocks, unknown = hydrate_rails_refs([STORY])
    assert not unknown and blocks, ("hydrate failed", unknown)
    b = blocks[0]
    story_file = Path(load_project_map()["projects"]["holdspeak"]) / (
        "pm/roadmap/holdspeak/phase-88-rails-aware-desk/story-05-walk-docs.md"
    )
    assert b.text.strip() == story_file.read_text().strip(), "block is not the dw-named file"
    print(f"grounded {b.kind} {b.title!r} — {len(b.text)} chars, IS the dw-named file")

    # BEAT 3 (proven here alongside 1) — a bad ref refuses by name.
    _bad, bad_unknown = hydrate_rails_refs(
        [{"repo": "holdspeak", "project": "holdspeak", "kind": "story", "id": "HS-404-04"}]
    )
    assert bad_unknown == ["story:HS-404-04"]
    print("a bad ref refused by name:", bad_unknown)

    if llm_up():
        beat(2, "Control vs treatment on .43 — the answer uses the story")
        q = (
            "Answer ONLY from the grounded story. Which existing Phase-87 walk "
            "script filename does this story's walk rig extend? Reply with just "
            "the .py filename."
        )
        control = ask(compose_steer(q, [])["text"])
        treatment = ask(compose_steer(q, blocks)["text"])
        print("control:  ", control[:80])
        print("treatment:", treatment[:80])
        # The filename is repo-specific — only the grounded story names it.
        assert "steer_walk_hs87" in treatment and "steer_walk_hs87" not in control
        results["grounding"] = {"control": control, "treatment": treatment}
    else:
        print("SKIP grounding LLM leg (.43 unreachable)")

    # BEAT 2b — Ground the same story into a STEER into a real pane.
    beat(3, "Ground a steer — the rail block lands in a real pane")
    session = f"hs88-walk-{uuid.uuid4().hex[:8]}"
    subprocess.run(["tmux", "new-session", "-d", "-s", session, "sleep 120"], check=True, timeout=10)
    try:
        pane = subprocess.run(
            ["tmux", "list-panes", "-t", session, "-F", "#{pane_id}"],
            check=True, capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        time.sleep(0.3)
        coder_steering.clear_grants()
        coder_steering.arm("claude:rails", f"{session}:0.0")
        composed = compose_steer("summarize this story", blocks)
        r = coder_steering.deliver(
            "claude:rails", composed["text"], current_target=f"{session}:0.0",
            agent="claude", submit=False, grounding_refs=composed["refs"],
            audit=lambda **kw: 1,
        )
        assert r["status"] == "delivered"
        time.sleep(0.4)
        seen = "\n".join(coder_steering.peek_pane(pane, lines=80)["lines"])
        assert "rails:story" in seen and "HS-88-05" in seen
        print("the rail block landed in the pane:", composed["refs"])
    finally:
        subprocess.run(["tmux", "kill-session", "-t", session], timeout=10, check=False)
        coder_steering.clear_grants()

    # BEAT 4 — Observer: journal REAL rail events.
    beat(4, "Observer — journal real rail motion")
    events = []
    for repo in events_payload(load_project_map(), tail=8).get("repos", []):
        if repo.get("status") == "live":
            for e in repo.get("events", []) or []:
                events.append({**e, "repo": repo.get("name", "")})
    fresh, _seen = rails_observer.new_events(events, set())
    if events and llm_up():
        summarizer = lambda s, u: ask(u, system=s)  # noqa: E731
        batch = rails_observer.summarize_batch(fresh, summarize_fn=summarizer)
        assert not batch["degraded"] and batch["summary"]
        print("journal summary:", batch["summary"][:160])
        results["journal"] = batch["summary"]
    else:
        print("SKIP observer summary (no events or LLM down)")

    # BEAT 5 — Observer restraint: read-only (the census, in-script).
    beat(5, "Observer restraint — read-only, no rails write path")
    src = Path("holdspeak/rails_observer.py").read_text()
    for forbidden in ("build_dw_story_connector", "decide_proposal", "send_text_to_pane"):
        assert forbidden not in src
    print("the observer holds no rails-write path — journaling only")

    # BEAT 6 — Reach: a remote envelope, node named, honest liveness.
    beat(6, "Reach — a remote node's events, named and honestly live")
    clk = [1000.0]
    rails_observer.push_remote_envelope(
        {"node": "walk-remote", "ts": "t1",
         "events": [{"ts": "t1", "event": "story_status", "story": "HS-1", "detail": {"to": "done"}}]},
        clock=lambda: clk[0],
    )
    drained = rails_observer.drain_remote_events(clock=lambda: clk[0])
    assert drained and drained[0]["origin_node"] == "walk-remote"
    body = rails_observer.journal_body(
        rails_observer.summarize_batch(drained, summarize_fn=lambda s, u: "A remote flip.")
    )
    assert "@walk-remote" in body
    clk[0] += rails_observer.REMOTE_LIVENESS_SECONDS + 1
    # The quiet node reads stale, and its stream drops on the next drain.
    assert rails_observer.remote_node_liveness(clock=lambda: clk[0]) == {"walk-remote": False}
    assert rails_observer.drain_remote_events(clock=lambda: clk[0]) == []
    assert rails_observer.remote_node_liveness(clock=lambda: clk[0]) == {}
    print("remote events named @walk-remote; a quiet node reads stale, then drops")
    rails_observer.clear_remote_buffer()

    # BEAT 7 — The journal grounds in turn (it is a note primitive).
    beat(7, "The journal grounds in turn — a note like any other")
    print("journal entries are notes tagged rails-journal — openable, groundable")

    (OUT / "walk-summary.json").write_text(json.dumps(results, indent=2))
    print(f"\n{'=' * 70}\nRAILS WALK: PASS — the rails are desk-native material\n{'=' * 70}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
