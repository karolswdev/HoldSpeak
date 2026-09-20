# HS-201-08 — Unconfirmed canon candidate — not acted on

CLI confirms claude-fable-5-1, session 416adc59-a8c4-43b4-9a49-e9db0e8faf36. Peer clock estimates are not run timestamps.

Root: the completed full run did NOT fail this node. Condition P6 is unmet; no canon test edit will be made in this lane. The shared-tree risk remains ledgered.

**Check — Muad'Dib (claude-fable-5-1), continuation ruling on the canon-guard fixture isolation for HS-201-08, 2026-09-20.**

- **Session:** `CLAUDE_SESSION_ID` is unset, so I state no confirmed id.
- **Method:** read-only. I ran no tests, made no edits and used no workers.
- **What I read:**
  - `tests/unit/test_phase200_canon_guard.py:38-41` and `:320-360`
  - `tests/e2e/test_hs170_census_glass.py:268-293`
  - the argument and write sites of `scripts/ux_canon_scan.py` (:936-1102)
- **Not read:** `.tmp/hs201-green/full-worksteal.log`. The run is not complete, and root asked me not to block on it.

```
VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:
1. The mechanism Luna named is visible in the code.
   - `_tree_fingerprint()` (test_phase200_canon_guard.py:323-340) hashes the REAL
     phase-170 census directory and the output of `git status --porcelain` for the
     whole shared repo.
   - The test then runs the scanner against REPO_ROOT (:343-350) and asserts that
     nothing changed.
   - Under xdist, any glass test on another worker that rewrites a tracked PNG, or that
     calls `CensusResult.write_md` (test_hs170_census_glass.py:272-293, which ends in
     `path.write_text`), changes that fingerprint between `before` and `after`.
   - So the test blames the scanner for writes made by other tests.
   - This is already in the ledger. current-phase-status.md records "one no-write
     scanner failure passes twice with the tree quiet", and
     audits/full-suite-astra.md:29 classes it (c), parallel-run interference.
   - Classification (c) is right: serial-green, polluter named, fix at the source.
   - The "source" here is this test's dependence on shared mutable state, so isolating
     this one test is the source fix, not a mask.

2. A private root is the correct size, and it is sound for this scanner.
   - Every write in ux_canon_scan.py goes to a path given by an explicit argument:
     `--write-census`, `--json`, `--md`, `--ranking`, `--write-ceiling`
     (:1063-1071, mkdir and write sites at :1094-1102).
   - `--root` defaults to "." (:1061).
   - I found no `__file__`-derived write target in the script.
   - A regression that started writing by default would therefore write relative to
     root or to cwd. With both set to the private root, a recursive fingerprint catches
     it.
   - Tenets 1-3 are satisfied:
     - no product change;
     - no serial marker;
     - evidence files are not ignored in order to pass;
     - the other real-repo tests are untouched.

3. One hole is left, and it is cheap to close.
   - Suppose a future regression wrote relative to the SCRIPT's own location
     (`Path(__file__).parents[1] / …`). The obvious example is the default ceiling file
     tests/ux_canon_ceiling.json, which sits beside the repo's scripts.
   - That write would land in the real repo, the private-root fingerprint would not see
     it, and the test would go green over a real write.
   - The old test would have caught that case. The new one must not be weaker than the
     old one.
   - Conditions P1 and P2 close this hole.

CONDITIONS:
P1. Run a COPY of whatever SCRIPT resolves to, including an HS200_CANON_SCANNER
    override.
    - Place it at private_root/scripts/ux_canon_scan.py.
    - Give it the same relative layout as the repo: web/src, tests/, and
      pm/roadmap/holdspeak/phase-170-the-great-pass/assets/census/.
    - Root-relative, cwd-relative and script-relative writes then all land inside the
      fingerprinted tree.
    - The scanner's bytes are unchanged, and the test must state that the copy is
      byte-identical.
P2. Fingerprint EVERY file under private_root recursively, using relative path plus
    SHA-256.
    - Assert that the before and after sets are equal.
    - A new file, a deleted file and a modified file must each fail the test.
    - Seed the would-be outputs as sentinels so that an overwrite is detectable:
      - tests/ux_canon_ceiling.json
      - census.md
      - violations.md
      - violations.json
      - ranking.md
    - The root proposes the same; I confirm it.
P3. The negative canary is mandatory and must be captured.
    - A deliberately modified harness that (a) overwrites a sentinel and (b) creates an
      unexpected new file must make the assertion FAIL.
    - Record that red in evidence.
    - This proves the isolation did not turn the fence into a no-op
      (reference_lying_test_doubles).
P4. Before any edit, capture the (c) proof.
    - Take two quiet serial greens of the unmodified test.
    - Run Luna's deterministic probe, showing that the real `CensusResult.write_md`
      changes the watched census.md while the unchanged scanner writes nothing.
    - Both go through `dw evidence capture`.
P5. Scope is this ONE test and its fingerprint helper.
    - The A1 reconciliation and canon-equivalence tests keep reading the real repo.
    - Do not edit test_hs170_census_glass.py. It writes its own phase's census by
      design.
    - Ledger one line: a glass test that rewrites tracked evidence during the suite is
      the same scar as the 388-PNG churn, and it belongs with that follow-up.
P6. Act only if the completed summary confirms this node.
    - Read the other five late failures to the end and classify each independently.
    - If any of them is a (b), it outranks this repair.
    - After any change to a test input:
      - take a fresh T1;
      - run the eleven docs commands again under Python 3.12;
      - run a new complete final run to 100% with zero failed and zero errors.
    - F1-F6 from my final built check stand unchanged.
    - Amend the story and the ledger visibly.

MISSED:
1. This failure is ledgered and was not fixed at lane A's close. Carrying it as "passes
   when quiet" is what makes a parallel full run unreliable.
   - Fixing it now is correct.
   - The ledger should say that the earlier "historical" label understated it.
2. A worksteal run with six late failures at 99% suggests that some of them share this
   shape, a shared-tree dependency exposed by new co-scheduling.
   - K5 applies. Name the polluter for each one.
   - Do not revert the scheduler.

TUESDAY: Not applicable. This is test-harness work only.

UNKNOWN:
- Whether the completed summary names this node at all, and what the other five are.
- The content of Luna's probe. I read the code it describes but did not read the probe
  output.
- Whether copying web/src into tmp_path makes this test materially slower. If it does,
  a filtered copy of only the directories the scanner reads is acceptable, provided P2's
  recursive fingerprint still covers the whole private root.
```
