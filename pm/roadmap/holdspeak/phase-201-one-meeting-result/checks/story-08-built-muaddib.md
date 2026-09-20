# HS-201-08 — story-08-built-muaddib

Invocation confirmed by CLI result: model `claude-fable-5-1`, session `416adc59-a8c4-43b4-9a49-e9db0e8faf36`. Peer clock estimates below are unverified; capture timestamps are UTC. Read-only check.

**Check — Muad'Dib (claude-fable-5-1), counsel on built, 2026-09-19 23:45 MDT / 2026-09-20 05:45Z.** Artifact: HS-201-08's working tree on `feat/hs-201-green` in `/Users/karol/dev/tools/wt-201-a` (uncommitted, base 321247d2).

- **Session:** `CLAUDE_SESSION_ID` is unset, so I do not state a confirmed id. The newest transcript in `~/.claude/projects/-Users-karol-dev-tools-wt-201-a/` was `416adc59-a8c4-43b4-9a49-e9db0e8faf36` at the design check. That is probable, not confirmed.
- **Method:** I did a read-only review. I ran no tests, made no edits and spawned no workers. I read:
  - the updated story and the top of `evidence-story-08.md`
  - the full diff of the four source files and the seven changed Python tests
  - the new `tests/unit/test_web_server_startup.py`
  - the names of the four new cases in `threads.test.ts`
  - the final focused logs in `.tmp/hs201-green/`
  - four of the eight shots: guardrail before at 1440, guardrail after reload at 1440 and 393, restart at 393
- **Not read:** the `ThreadPullout.test.tsx` and transcriber test diff bodies.

```
VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:
1. The full quiet-tree run is pending and already shows failures.
   - .tmp/hs201-green/full-final.log (1,183 bytes, 23:39 MDT) has four `F` between 4% and
     8% of the run.
   - The run is -q, so no node names are available until it finishes.
   - AC6 (story-08:25) is NOT met.
   - I did not wait for the run. Nothing in this verdict ratifies a green that does not
     exist yet.
   - Those four may be inherited. The status ledger already carries twelve inherited
     failures plus the daily-loop pair (current-phase-status.md, "Lane A debt ledger").
     If they are, a story titled "Main is green" is claiming more than the evidence
     shows. See C1.

2. The guardrail REASON disappears on reload. The repair restores the verdict only.
   - Shot before-guardrail-decision-box-1440.png shows the row
     "X GUARDRAIL VIOLATION / people.commitment.transition called without a named source"
     above the decision box.
   - Shots guardrail-decision-box-1440.png and -393.png, taken after reload, show Deny
     primary and focused. The violation row is gone.
   - The data for the row is on disk. thread_service.py:1248-1256 persists a
     kind="guardrail" part with the violations.
   - threads.ts keeps guardrailRows as live-frame state only (:609, applyGuardrail :1152).
     No hydration path reads the part.
   - The changed glass test asserts the row BEFORE reload and only the buttons AFTER it
     (tests/e2e/test_hs153_practice_glass.py, new reload block). The gap is unfenced.
   - AC2 as written is satisfied: Deny survives, primary and focused, at both widths.
   - This does not block the story. The guardrail window is about 30 s and this is a
     restoration story.
   - The ratified HS-153-03 face is "violation row + Deny". A Deny with no stated reason
     fails UX-CANON "build what was ratified" and tenet 3 (help, accelerate).
   - See C3.

3. A correction to my own design check.
   - The original shot shows Allow PRIMARY while Deny holds the focus ring
     (before-guardrail-decision-box-1440.png: "Allow once" filled, "Deny" outlined).
   - The mechanism I gave was therefore incomplete. On a row whose live frame said deny,
     autoFocus fired once at mount and stayed on Deny. Hydration then erased the field,
     so the primary fill moved to Allow.
   - "Enter approves" was an inference from ThreadPullout.tsx:647. Nobody observed it
     as a key gesture.
   - The observed defect is a split signal: the fill said Allow and the focus said Deny.
     Per the species law, a primary/focus split is a bug in its own right, and the
     built fix closes it.
   - The record in checks/story-08-design-muaddib.md should carry this correction. I
     cannot edit it because this check is read-only.

4. web_server.py readiness: sound, and the right size.
   - start() polls uvicorn's `started` flag under one 5 s monotonic deadline
     (diff hunk at :425-446).
   - It detects three exit conditions: should_exit, thread death and a captured
     exception.
   - `except BaseException` in _run_server is justified. uvicorn leaves through
     sys.exit(1) when bind fails. Before this change that killed the thread silently and
     start() returned a dead URL.
   - The one production caller already handles the raise:
     web_runtime.py:520-525 turns Exception into a printed message and SystemExit(1).
   - The permanent tests are real proof. The first gates an actual Uvicorn lifespan
     with an on_startup hold, asserts start() does not return for 1 s, releases, then
     opens a TCP connection (tests/unit/test_web_server_startup.py:42-88).
   - The second models a failed startup and asserts RuntimeError with no URL.
   - The second test uses a fake Server. That is fine for branch coverage, and the
     first test is the honest one.
   - Two small ledger notes, neither blocking:
     (a) If the thread outlives _fail_startup's 1 s join, _server and _thread stay set.
         The next start() then raises "already in progress" until the thread dies.
     (b) The timeout message names the phase ("listener" or "startup"). That is
         operator text, not face text, so it is fine.

5. Guardrail persistence and hydration match the accepted design.
   - The decision is computed before append_part. It is written to the meta only when
     it is non-None, and the same value is emitted (thread_service.py hunk at :1327-1351).
   - The unit fence reads the REAL part back from the REAL repository
     (tests/unit/test_thread_guardrail.py:498-504). It is not a double.
   - The live fallback in threads.ts is limited to state === "awaiting_decision" and to
     the one field. Terminal hydration therefore wins, and
     "does not carry a live decision onto a terminal hydrated row" fences it.
   - The persisted value is checked against the two legal strings before use.

6. Classification of CI HOME: I side with Astra's (b, harness), with one wording fix.
   - The assertion is valid and unchanged, so this is not (a).
   - The defect is the workflow running unit tests against a HOME that the suite's own
     guard forbids once anything has been written there.
   - The named writer is a real leak. observer_or()'s fallback opens the default
     database under test_124_verify_round3
     (::test_pipeline_events_without_filters_returns_recent_events).
   - Isolation CONTAINS that leak. It does not fix it.
   - The evidence says "contains", which is honest. Add the writer as its own ledger
     line, so the entry does not read as closed.

7. Remaining items are correct as built.
   - Custody: sibling copy then os.replace, which leaves the old inode live. Custody
     assertions are unchanged.
   - Attention: the helper clock is pinned to 12:00Z, and the two quiet-hours tests keep
     their own clocks.
   - The CI isolation docstring has been brought up to date.
   - The guardrail shots moved to the phase-201 SHOTS_08 directory, so phase 153's
     closed evidence is no longer rewritten. This is a quiet improvement and should be
     kept.
   - The restart test is now parametrized at both widths, with SAVED HERE asserted and
     SAVED ON ANOTHER DESK refused.
   - taskresume-after-restart-393.png reads "SAVED 23:35 · SAVED HERE · Resume", with
     no raw id.

CONDITIONS:
C1. Full-suite green is a hard condition of closure.
    - Read full-final.log to its end and name every failing node.
    - Each failure is one of two things: caused by this diff, in which case fix it; or
      inherited, in which case prove it red on 321247d2 and ledger it.
    - If any inherited red remains, AC6 cannot be boxed.
    - In that case the PR body and story must say "the six named reds and the
      notification family are green; N inherited reds remain, listed". They must not
      say "main is green".
    - That is a visible criterion amendment under TWO-BRAINS §3, and I would ratify it.
      I would not ratify a silent pass.
C2. The web check is recorded by its exit file, not by its tail.
    - web-check.log ends at "bundle gate passed".
    - Read .tmp/hs201-green/web-check.exit and the inherited-baseline verdict (zero
      BRANCH-NEW) into evidence before flipping the box.
C3. Ledger finding 2: the guardrail violation row is not hydrated although
    kind="guardrail" is persisted.
    - Give it a home in BACKLOG or a Phase 153 follow-up.
    - Do not fix it in this story. Doing so would design hydration for a second row
      species inside a restoration lane.
C4. Before staging:
    - Restore the 66 churned PNGs.
    - Stage by explicit path.
    - Exclude assets/story-08-probes/__pycache__. It is already ignored by
      .gitignore:2, so verify rather than assume.
    - Include the new tests/unit/test_web_server_startup.py. It is untracked and easy
      to miss.
C5. Put the finding-3 correction into the built-check record so that the two checks
    read consistently.

MISSED (ranked by cost to the owner):
1. After a reload the owner sees Deny with no reason (finding 2). For a tired owner,
   an unexplained Deny is the moment they press Allow.
2. The story title promises more than this lane can deliver if inherited reds remain
   (finding 1, C1). He will read "main is green" and then see a red badge.
3. The observer-fallback leak is contained on CI and still open everywhere else.
   - Any unisolated local run still writes into the real HOME. That is the v43
     pollution scar, reached by a different route.
   - The guard refuses such a run only when an installation already exists.
4. The node id test_the_custody_token_after_a_restart_at_1440[393] now contradicts its
   own name. This is cosmetic. Leave it until someone renames the node and updates the
   story table together.
5. The integration job stays unisolated by choice. The docstring says so, but the
   workflow carries no comment at test.yml:180. The next reader may "fix" it and lose
   the model cache.

TUESDAY:
- Yes for the restored Ask. He reopens the Room and reads SAVED HERE with Resume, at
  both widths.
- Yes, with a caveat, for the guardrail. Deny is filled and focused before and after a
  reload, but after the reload the glass no longer says why.

UNKNOWN:
- The outcome of the full quiet-tree run. It was pending and already showed four
  failures at 8%.
- The web check's exit code and baseline verdict.
- Whether any of the four early failures touch this diff.
- The ThreadPullout.test.tsx and transcriber test diff bodies.
  - I checked only the names of the threads.test.ts cases.
  - I accept root's captured "57 passed" and "3 passed, 13 deselected" as claims that
    the logs support, and I did not re-run them.
- The three Ubuntu reds are fixed by reasoning plus a Linux-resolver probe on this Mac.
  They have not yet been confirmed on a Linux runner. Only the PR's CI run confirms them.
- The key-gesture behaviour of the old face (finding 3) was never observed by anyone.
```
