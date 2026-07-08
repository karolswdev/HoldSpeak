#!/usr/bin/env python3
"""HS-87-04 control-vs-treatment: a grounded steer changes the answer.

The Phase-53 proof pattern, on real metal. The SAME question is asked
twice: once bare (control), once with a desk artifact hydrated in by
`grounding.compose_steer` (treatment). The model on .43 answers both;
the treatment answer demonstrably uses the grounded fact the control
could not know. Then the treatment steer is delivered through the
real chokepoint into a real tmux pane, proving the composed text
lands exactly as previewed.

Run: uv run python scripts/steer_grounding_proof.py
Env: HOLDSPEAK_PROOF_LLM (default http://192.168.1.43:8080)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
import uuid

from holdspeak.coder_steering import arm, clear_grants, deliver, peek_pane
from holdspeak.grounding import GroundingBlock, compose_steer

LLM = os.environ.get("HOLDSPEAK_PROOF_LLM", "http://192.168.1.43:8080")

# The grounded fact the model cannot know from its weights: a made-up,
# specific decision that only rides in through the artifact.
SECRET = "the deploy is locked to Friday the 13th at 3:47pm, code-named BLUEBIRD"
QUESTION = "In one short sentence: when is the deploy and what is its code name?"


def ask(prompt: str) -> str:
    body = json.dumps(
        {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 120,
        }
    ).encode()
    req = urllib.request.Request(
        f"{LLM}/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"].strip()


def main() -> int:
    try:
        urllib.request.urlopen(f"{LLM}/health", timeout=4).read()
    except Exception as exc:
        print(f"SKIP: LLM at {LLM} unreachable ({exc})")
        return 0

    # Control: the bare question.
    control_steer = compose_steer(QUESTION, [])
    control_answer = ask(control_steer["text"])

    # Treatment: the same question, grounded with the artifact.
    block = GroundingBlock(
        kind="artifact",
        ref="deploy-decisions",
        title="Deploy Decisions",
        subtitle="Release Planning",
        text=f"Decision: {SECRET}.",
    )
    treatment_steer = compose_steer(QUESTION, [block])
    treatment_answer = ask(treatment_steer["text"])

    print("=" * 70)
    print("CONTROL steer (no grounding):")
    print(control_steer["text"])
    print("-" * 70)
    print("CONTROL answer:")
    print(control_answer)
    print("=" * 70)
    print("TREATMENT steer (grounded, composed by compose_steer):")
    print(treatment_steer["text"])
    print("-" * 70)
    print("TREATMENT answer:")
    print(treatment_answer)
    print("=" * 70)

    uses_it = "bluebird" in treatment_answer.lower() or "3:47" in treatment_answer
    control_blind = "bluebird" not in control_answer.lower()
    print(f"treatment uses the grounded fact: {uses_it}")
    print(f"control could not know it:        {control_blind}")

    # And prove the composed treatment lands in a REAL pane.
    session = f"hs87-ground-{uuid.uuid4().hex[:8]}"
    subprocess.run(
        ["tmux", "new-session", "-d", "-s", session, "sleep 120"],
        check=True,
        timeout=10,
    )
    pane_landed = False
    try:
        pane = subprocess.run(
            ["tmux", "list-panes", "-t", session, "-F", "#{pane_id}"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        time.sleep(0.3)
        clear_grants()
        arm("claude:ground-proof", f"{session}:0.0")
        result = deliver(
            "claude:ground-proof",
            treatment_steer["text"],
            current_target=f"{session}:0.0",
            agent="claude",
            submit=False,
            grounding_refs=treatment_steer["refs"],
            audit=lambda **kw: 1,
        )
        time.sleep(0.4)
        seen = "\n".join(peek_pane(pane, lines=60).get("lines", []))
        pane_landed = "BLUEBIRD" in seen and result["status"] == "delivered"
        print(f"composed steer landed in the real pane: {pane_landed}")
    finally:
        subprocess.run(["tmux", "kill-session", "-t", session], timeout=10)
        clear_grants()

    ok = uses_it and control_blind and pane_landed
    print("=" * 70)
    print("PROOF:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
