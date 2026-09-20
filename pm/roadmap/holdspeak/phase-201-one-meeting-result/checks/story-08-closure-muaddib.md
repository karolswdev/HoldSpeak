# HS-201-08 — Closure ratified

**Check — Muad'Dib (claude-fable-5-1), final closure counsel for HS-201-08, 2026-09-20.**

- **Artifact:** the closure records and the staged index on `feat/hs-201-green` in `/Users/karol/dev/tools/wt-201-a`.
- **Session:** `416adc59-a8c4-43b4-9a49-e9db0e8faf36`. The CLI confirmed this id to root; the environment variable is unset here.
- **Method:** read-only. I ran no tests, made no edits and used no workers.

What I read:
- the tail of `.tmp/hs201-green/full-verified.log`, plus a grep of the log for failure and error markers
- the staged counts, and the staged delta from T1
- the header and AC boxes of story 08, and its delivery section
- the evidence top (`evidence-story-08.md`), and the `07:18:40Z` capture header
- the phase status lines that name HS-201-08
- `.tmp/hs201-green/pr-body-draft.md`

What I did not read again:
- the code
- the shots
- the record of my late check, `checks/story-08-late-built-muaddib.md`

```
VERDICT: RATIFY

FINDINGS:
1. The final full-suite run is complete and green. I read the log myself.
   - Tail of full-verified.log:
     `11264 passed, 116 skipped, 4 xfailed in 1508.86s (0:25:08)`.
   - A grep for `FAILED` or `ERROR ` finds two lines. Both are the PASSED parametrized
     node `test_a_listener_failure_becomes_one_token_not_a_stack[…LISTENER FAILED]`
     (:15927-15928). Neither is a failure.
   - The four xfails are the existing strict proposal-chain nodes. Their reason strings
     are unchanged.
   - Z1 is paid.
   - I did not re-derive two of root's claims: the skip-summary comparison, and "all 12
     historic audit nodes passed". Those stand as root's.

2. The index invariant holds (Z2).
   - 83 paths are staged.
   - 18 of them are PNGs, and all 18 sit under story-08-shots.
   - The staged delta from T1 `6c8c47bd…` is 12 paths. ALL 12 are under `pm/roadmap/`.
   - The capture's own index tree is `315f0ef2…`. It differs from T1 by exactly one
     path, `evidence-story-08.md`.
   - So the full run executed on the same inputs as the docs capture.
   - The only unstaged change is the evidence append (`AM`), as root says.

3. The AC7 rewording is honest. It does not waive delivery.
   - A pre-commit record cannot truthfully tick "commit, push, PR" as done.
   - The old bundled box could only be flipped by claiming future acts.
   - The new box covers what exists: the peer checks, and the verified closing
     conditions.
   - story-08:78-82 keeps the delivery protocol explicit and unchanged:
     - one gated commit
     - push to `feat/hs-201-green`
     - the exact PR title
     - no merge
   - Delivery stays required. The commit trailers and the PR will be its proof.
   - I ratify this as a visible amendment under TWO-BRAINS §3. It is recorded in the
     story, which is where it belongs.

4. The records are coherent.
   - Story 08 has Status done and all seven boxes checked.
   - AC6 names worksteal and the eleven docs commands.
   - The status row reads done, and "Last updated" says gated delivery is awaited and
     no merge.
   - The `--tests-capture` anchor `#2026-09-20T07:18:40Z` exists in evidence (:2522),
     with Exit code 0 and the exact command.
   - The PR draft carries:
     - the seven repair groups with their classes
     - the fact that the first complete run still found six failures
     - the final counts
     - the three D5 sentences
     - the envelope limit
     - the CI-only unknowns
     - the local-only status of the high-fd proof
     - "a failed branch check reopens verification"
     - "do not merge"
   - That satisfies Z3 through Z5.

5. No material defect found in the final record.

CONDITIONS:
None blocking. The remaining delivery mechanics are already root's plan:
- Restage the roadmap records only. Then confirm once more that the T1 delta is still
  entirely under pm/roadmap/ BEFORE `dw contract new`. The contract stamps the index,
  so the order matters.
- Run `.githooks/dw contract new --story HS-201-08 --tests-capture
  pm/roadmap/…/evidence-story-08.md#2026-09-20T07:18:40Z`.
- Flip each box only after verifying it. Commit without --no-verify.
- One story flips done, and its evidence file ships in the same commit.
- Push. Open the PR titled exactly "HS-201-08 main is green". No merge.
- Record this counsel at checks/story-08-closure-muaddib.md before staging, so it ships
  in the same commit.

MISSED:
1. The status line says "seven of eight stories verified done in this lane".
   - When the PR opens, the owner-facing report should lead with two facts:
     - Story 07, the sitting, is the phase's real close.
     - This PR makes no first-use claim.
   - The draft says "do not merge". It does not mention story 07.
   - Adding one sentence is optional and not blocking.
2. The title is a promise about MAIN, and only the PR's CI can keep it.
   - Until those jobs report, say "green locally, CI pending" to the owner.
   - Do not say "main is green".

TUESDAY:
- Yes for what this story touches:
  - Roadmaps list
  - SAVED HERE after a restart
  - Deny held through a reload
  - targeted credential revoke
- Not yet for creating the carried decision. The record says so.

UNKNOWN:
- The PR's CI result on Ubuntu and macOS.
- Byte-equality of the regenerated references under CI's Python 3.12.
- Whether the gate accepts the contract. That is a delivery fact, not yet made.
- Root's claims that I did not re-derive in this round:
  - the skip-summary identity
  - the 12 historic nodes
  - the shot re-viewing
  - the late-check wrapper
```
