"""HS-109-04 — the live proof: real archive, real metal, cited answers.

1. Rebuilds the memory index over the REAL archive and searches it for a
   REAL decision (the BLUE LANTERN codename recorded by the HS-109-01
   live proof) — ranked hit with its `decision:<id>` ref and snippet.
2. Control vs treatment on the REAL `.43` llama.cpp endpoint: the same
   question asked bare, then grounded with the memory hits as per-source
   blocks. The treatment must answer from the archive and the control
   must not know — selection demonstrably changes the model's output.

Usage:
  uv run python scripts/hs109_04_live_proof.py
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request

from holdspeak.db import Database

ENDPOINT = "http://192.168.1.43:8080/v1/chat/completions"
QUESTION = "What is the secret launch codename for the mesh milestone?"


def chat(messages: list[dict[str, str]]) -> str:
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(
            {"messages": messages, "temperature": 0.0, "max_tokens": 200}
        ).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode())["choices"][0]["message"]["content"]


def main() -> int:
    ok = True
    db = Database()

    counts = db.memory.rebuild()
    print(f"REAL ARCHIVE index rebuild: {json.dumps(counts)}")
    again = db.memory.rebuild()
    print(f"rebuild again (idempotent): {json.dumps(again)}")
    ok &= counts == again

    t0 = time.perf_counter()
    result = db.memory.search("BLUE LANTERN")
    hits = result.hits
    dt = (time.perf_counter() - t0) * 1000
    print(f"\nmemory.search('BLUE LANTERN') → {result.total} hit(s) in {dt:.1f} ms")
    for h in hits[:5]:
        print(f"  [{h.source_ref}] rank={h.rank} '{h.snippet[:90]}'")
    decision_hits = [h for h in hits if h.source_ref.startswith("decision:")]
    print(f"{'PASS' if decision_hits else 'FAIL'}  a real decision record is a ranked, "
          f"cited hit")
    ok &= bool(decision_hits)

    control = chat([{"role": "user", "content": QUESTION}])
    print(f"\nCONTROL (ungrounded .43): {control[:220]!r}")

    blocks = "\n\n".join(
        f"[REF: {h.source_ref}]\n{h.snippet}" for h in hits[:4]
    )
    treatment = chat([
        {"role": "system",
         "content": "Answer ONLY from the provided sources. Cite the [REF: …] "
                    "you used. If the sources do not answer, say so."},
        {"role": "user", "content": f"Sources:\n{blocks}\n\nQuestion: {QUESTION}"},
    ])
    print(f"TREATMENT (grounded on memory hits): {treatment[:300]!r}")

    t_knows = "BLUE LANTERN" in treatment.upper()
    c_knows = "BLUE LANTERN" in control.upper()
    cites = "decision:" in treatment
    print(f"{'PASS' if t_knows else 'FAIL'}  treatment answers from the archive")
    print(f"{'PASS' if not c_knows else 'FAIL'}  control does not know the codename")
    print(f"{'PASS' if cites else 'FAIL'}  treatment cites its decision ref")
    ok &= t_knows and not c_knows and cites

    print(f"\n{'ALL PASS' if ok else 'FAILURES ABOVE'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
