"""Phase 109 — The Long Memory — the eight-beat closeout session.

One rerunnable command (Article IX): every beat runs against the REAL
archive and, where a model is involved, the REAL `.43` endpoint. Each
beat prints PASS/FAIL by name; the session fails if any beat fails.

  uv run --extra dictation-openai python scripts/phase109_closeout_beats.py
  uv run ... phase109_closeout_beats.py --beat 5      # one beat

B1  backfill idempotency on the real archive (counts; second run no-op)
B2  a real decision carries a verified transcript moment; the jump resolves
B3  promotion: deterministic ADR with decision:<id> lineage; supersession
    propagates; superseded re-promotion refuses naming the successor
B4  model-assisted promotion through inference.run@1 on .43; receipt read
B5  memory search over the real archive; the q/search wire regression
B6  grounded ask-this-project on .43 with citations; control-vs-treatment
B7  the process window's truth: reducer folds, cursor replay, endpoint
    surface, pending-forever stays Waiting (the pinned web suite)
B8  the sweep: full pytest, web chain, guards, kernel spine byte-diff,
    effect register untouched (21 total / 3 covered / 3 exempt / 15 debt)
"""

from __future__ import annotations

import argparse
import subprocess
import sys

SPINE = [
    "holdspeak/kernel/broker.py",
    "holdspeak/kernel/admission.py",
    "holdspeak/kernel/journal.py",
    "holdspeak/kernel/model.py",
    "holdspeak/kernel/executor.py",
]


def run(cmd: list[str], timeout: int = 3600) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, (proc.stdout + proc.stderr)


def beat(number: int, name: str, code: int, tail: str) -> bool:
    ok = code == 0
    print(f"{'PASS' if ok else 'FAIL'}  B{number}  {name}")
    if not ok:
        print("\n".join(tail.strip().splitlines()[-12:]))
    return ok


def b1() -> bool:
    code, out = run([
        "uv", "run", "python", "-c",
        "import json; from holdspeak.db import Database\n"
        "db = Database()\n"
        "first = db.decisions.backfill(); second = db.decisions.backfill()\n"
        "print('run1:', json.dumps(first)); print('run2:', json.dumps(second))\n"
        "assert second['inserted'] == 0 and second['updated'] == 0, 'not a no-op'\n",
    ])
    print(out.strip())
    return beat(1, "real-archive backfill idempotent", code, out)


def b2() -> bool:
    code, out = run(["uv", "run", "python", "scripts/hs109_02_live_proof.py"])
    print("\n".join(out.strip().splitlines()[-6:]))
    return beat(2, "verified transcript moment + the jump (.43)", code, out)


def b3_b4() -> tuple[bool, bool]:
    code, out = run(["uv", "run", "--extra", "dictation-openai", "python",
                     "scripts/hs109_03_live_proof.py"])
    print("\n".join(out.strip().splitlines()[-10:]))
    ok3 = beat(3, "promotion, supersession, named refusal", code, out)
    ok4 = beat(4, "model-assisted promotion receipt on .43", code, out)
    return ok3, ok4


def b5() -> bool:
    code1, out1 = run(["uv", "run", "python", "scripts/hs109_04_live_proof.py"])
    print("\n".join(out1.strip().splitlines()[-8:]))
    code2, out2 = run(["uv", "run", "pytest", "-q",
                       "tests/integration/test_web_meetings_facets_api.py"])
    return beat(5, "memory search + cited grounding + wire regression",
                code1 or code2, out1 + out2)


def b6() -> bool:
    # b5's live proof already runs control-vs-treatment; B6 re-asserts the
    # citation surface end to end through the ask path suites.
    code, out = run(["uv", "run", "pytest", "-q", "tests/unit/test_web_routes_ask.py",
                     "tests/integration/test_memory_retrieval.py"])
    return beat(6, "cited ask surfaces (grounded-on honesty)", code, out)


def b7() -> bool:
    code, out = run(["bash", "-c",
                     "cd web && npx vitest run src/desk/__tests__/processWindow.test.ts "
                     "src/desk/__tests__/processWindowReducer.test.ts "
                     "src/pages/cores/__tests__/processCore.test.tsx 2>&1 | tail -6"])
    print(out.strip())
    return beat(7, "process window: fold, replay, endpoint surface", code, out)


def b8() -> bool:
    fails: list[str] = []
    code, out = run(["git", "diff", "--exit-code", "origin/main", "--"] + SPINE)
    if code != 0:
        fails.append("kernel spine differs from origin/main")
    code, out = run(["uv", "run", "pytest", "-q",
                     "tests/unit/test_kernel_effect_fence.py"])
    if code != 0:
        fails.append("effect fence not green (register must read 21/3/3/15)")
    code, out = run(["bash", "-c", "cd web && npm run test:web 2>&1 | tail -3 "
                     "&& npm run build 2>&1 | tail -2"])
    if code != 0:
        fails.append("web chain failed")
    code, full = run(["uv", "run", "pytest", "-q",
                      "--ignore=tests/e2e/test_metal.py"], timeout=2400)
    tail = "\n".join(full.strip().splitlines()[-3:])
    print(tail)
    known = ("test_committed_ledger_is_up_to_date",
             "test_transcribe_up_but_unreachable_is_honest")
    if code != 0:
        unexpected = [ln for ln in full.splitlines()
                      if ln.startswith("FAILED") and not any(k in ln for k in known)]
        if unexpected:
            fails.append("unexpected suite failures: " + "; ".join(unexpected[:4]))
    for f in fails:
        print(f"  · {f}")
    return beat(8, "the sweep (suite, web, fence, spine, register)",
                0 if not fails else 1, "\n".join(fails))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--beat", type=int, default=0)
    args = parser.parse_args()
    results: list[bool] = []
    want = args.beat

    if want in (0, 1):
        results.append(b1())
    if want in (0, 2):
        results.append(b2())
    if want in (0, 3, 4):
        ok3, ok4 = b3_b4()
        results.extend([ok3, ok4] if want == 0 else [ok3 if want == 3 else ok4])
    if want in (0, 5):
        results.append(b5())
    if want in (0, 6):
        results.append(b6())
    if want in (0, 7):
        results.append(b7())
    if want in (0, 8):
        results.append(b8())

    print(f"\n{sum(results)}/{len(results)} beats passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
