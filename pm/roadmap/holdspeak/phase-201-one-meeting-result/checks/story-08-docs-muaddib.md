# HS-201-08 — story-08-docs-muaddib

Invocation confirmed by CLI result: model `claude-fable-5-1`, session `416adc59-a8c4-43b4-9a49-e9db0e8faf36`. Peer clock estimates below are unverified; capture timestamps are UTC. Read-only check.

**Check — Muad'Dib (claude-fable-5-1), scope-extension design check #2 for HS-201-08 (documentation CI), 2026-09-20 ~06:10Z.**

- **Artifact:** the proposed amendment to make documentation CI green.
- **Session:** `CLAUDE_SESSION_ID` is unset, so I state no confirmed id.
- **Method:** read-only. I ran no tests, made no edits and used no workers.
- **What I read:**
  - `.tmp/hs201-green/docs-check.log`, in full (30 lines)
  - the docs job at `.github/workflows/test.yml:13-37`
  - the anchor check in `scripts/validate_architecture.py`
  - the provenance strings in the three generators
  - `docs/internal/philo/snapshot.json`
  - the doctor anchors in `runtime.json`
- **One script of my own:** I ran one AST comparison of the metadata's line anchors against current `def` lines. It writes nothing, and it is the basis for finding 2.

```
VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:
1. The diagnosis is correct, and classification (a) is right.
   - docs-check.log:21 reports `runtime.json.capabilities[7].sources[1].line: source line
     1454 is outside holdspeak/commands/doctor.py`.
   - doctor.py is now 1267 lines. `collect_doctor_checks` is at :1049 and
     `run_doctor_command` is at :1236.
   - The checks themselves are valid. The authored anchors and three generated outputs
     went stale when Phase 201 shortened doctor.py under metadata written at 675401a8.
   - One validator error cascades into two more failures. generate_capability_docs and
     check_doc_coverage refuse to run on invalid metadata (log :24-29).
   - The honest failure count is three drifted outputs plus ONE metadata error, not six
     independent failures. Evidence should say so.

2. "Two doctor source anchors" undercounts.
   - There are three doctor entries: runtime.json:1032 and :1038, and a second
     `collect_doctor_checks: 1267` at runtime.json:1558 (`operations.doctor`).
   - The anchor at 1267 passes the validator only by coincidence, because 1267 is the
     file's last line.
   - The validator checks `line <= file length` and that the symbol exists somewhere in
     the file (validate_architecture.py:250-255). It never checks that the symbol is AT
     that line.
   - My AST comparison found 57 of 190 Python anchors more than 3 lines away from their
     symbol's `def`. Of those, 19 are in holdspeak/inference_capabilities.py.
     - Caveat: some anchors may deliberately point inside a function body. Treat 57 as an
       upper bound, not a defect count.
   - One stale anchor comes from this lane. integrations.json has
     `thread_service.py::_m1_redactor` at 1850, and the symbol is now at :1855. The
     +5 is exactly the net lines of the guardrail-persistence edit.

3. The narrow repair is the right size.
   - Correct the doctor anchors.
   - Regenerate the four outputs with their existing generators.
   - Leave the CI checks unchanged.
   - Do NOT fix the other ~50 silent anchors in this story. They are not red, and
     fixing them is a Philo audit, not a main-green repair.
   - Tenets 1 and 3 are satisfied. Add a ledger line.

4. The provenance concern is real, and the proposed fix is sufficient.
   - All three generators stamp `snapshot: 675401a8…` from snapshot.json
     (philo_api_reference.py:56, philo_doctor_reference.py:24,
     philo_boundary_census.py:38) while reading the CURRENT working tree.
     - Example: boundary census line 34 calls `p.read_text()` over files listed in
       repository-tree.json.
   - The boundary `scope` string says "tracked implementation files at snapshot, read
     from current unchanged product tree". After any product commit, "unchanged" is
     false.
   - After regeneration the outputs would carry 675's hash on content derived from
     321 plus this lane. That is a provenance claim the evidence cannot support.
   - Editing the label strings and adding a short README note is the minimal honest
     correction. I would not ratify the regeneration WITHOUT it.
   - I agree with leaving these untouched: snapshot.json, the audit report, the
     repository census, and the schema.

CONDITIONS:
C1. Fix all THREE doctor entries (runtime.json:1032, :1038, :1558) and the lane-induced
    `_m1_redactor` anchor in integrations.json.
    - Add no other anchors.
    - Put the silent-anchor finding in the ledger with a home: the validator does not
      check symbol-at-line, and up to 57 of 190 anchors are off.
C2. Order matters. Regenerate LAST, after every product edit in this story has landed,
    and that includes the roadmaps.py fix.
    - Any later edit that moves lines makes the docs red again.
    - The final docs-check run must be captured on the same index tree as the commit.
C3. Each label edit must say two things:
    - the snapshot hash is the census BASELINE, meaning file membership and audit scope;
    - the handlers, checks and anchors were read from the working tree at generation.
    - Remove "unchanged".
    - Make no schema or key changes. The `snapshot` key stays, so existing consumers and
      `--check` keep working.
    - The three generator edits are string-only. The diff must show nothing else in
      those scripts.
C4. Capture red first, per check, through `dw evidence capture`, before any edit.
    - After regeneration, review the DIFF of each regenerated output and summarize it in
      evidence.
    - A regeneration must not quietly drop routes, checks or capability claims.
    - If a row disappears, stop. That would be a product finding, not drift.
C5. The amendment is written into story-08 visibly (scope In, the test plan's docs
    commands, classification (a)).
    - AC6's "green" now names both full pytest -n 4 and the eleven docs-job commands
      at test.yml:27-37.
    - Counsel-on-built is owed again, as root says.
C6. Standing conditions are unchanged.
    - The full quiet-tree run must be read to the end.
    - Every failure must be named.
    - Nothing may be relabelled.

MISSED (ranked by cost to the owner):
1. Docs CI is structurally fragile.
   - The generated references carry line-level evidence, and CI runs `--check` on them.
   - So any product commit that shifts lines in a referenced file makes main red until
     someone regenerates.
   - This lane will pay that cost once. The next lane will pay it again.
   - The owner's ruling "regenerate docs/generated/* when routes/schema change" does not
     cover line drift.
   - Do not redesign it here. Put it on the ledger as the first Philo follow-up. The
     smallest step is a note in AGENTS.md and CLAUDE.md telling authors to run the four
     generators before every product commit.
2. The validator's line check gives false assurance (finding 2). It reported one of the
   stale anchors and let the rest through.
3. Story 08 now has three scope extensions: the six reds plus notifications, then
   roadmaps, then docs.
   - Each extension is justified.
   - The PR body should list the three families separately, so the owner can see what
     "green" cost.
4. snapshot.json names `python: 3.14.6`, and CI runs the generators on 3.12.
   - If any generator output depends on AST or formatting, a local regeneration could
     still drift on CI.
   - Only the PR's docs job settles this. See UNKNOWN.

TUESDAY: Not applicable to a face. This is CI and documentation honesty. The owner's
gain is a green badge that is true, and references whose provenance line does not
overstate what they are.

UNKNOWN:
- Whether API-reference drift also predates this lane on bare 321247d2.
  - Root says yes for doctor.
  - I did not check out main to confirm, and it is forbidden here.
- What the three regenerated diffs contain. They do not exist yet (C4).
- Whether regeneration under local Python matches CI's 3.12 byte for byte.
- How many of the 57 off-anchor entries are intentional body anchors.
- The full pytest run was still in progress.
```
