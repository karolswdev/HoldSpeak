# HS-201-08 design check

Claude session: 416adc59-a8c4-43b4-9a49-e9db0e8faf36 (from invocation result).

**Check — Muad'Dib (claude-fable-5-1), 2026-09-19 23:20 MDT / 2026-09-20 05:20Z.** Artifact: `pm/roadmap/holdspeak/phase-201-one-meeting-result/story-08-main-is-green.md` (untracked, on `feat/hs-201-green` at 321247d2).

- **Session:** `CLAUDE_SESSION_ID` is unset. The newest transcript in `~/.claude/projects/-Users-karol-dev-tools-wt-201-a/` is `416adc59-a8c4-43b4-9a49-e9db0e8faf36`. That is probably this session, but I have not confirmed it.
- **Method:** I did a read-only review. I ran no tests, made no edits and spawned no workers. The red evidence is the last completed main CI run, 35478778899 on 675401a8, read with `gh run view --log`. I reproduced nothing on this Mac. Every diagnosis below comes from reading the code and that CI log, and I say where a claim is only a hypothesis.

```
VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:
1. The brief's premise is half wrong: three of the six reds are macOS, not Linux.
   - CI run 35478778899, Unit Tests job (ubuntu-latest, .github/workflows/test.yml:95), 3 failed:
     - test_the_running_suite_is_itself_isolated
     - test_custody_survives_the_database_file_being_recreated
     - test_boot_warm_is_reused_by_a_legacy_dictation
   - Same run, E2E Tests job (macos-14, test.yml:194), 3 failed:
     - test_guardrail_row_renders_and_deny_focused
     - test_a_saved_ask_survives_a_hub_restart
     - test_the_custody_token_after_a_restart_at_1440
   - The story never lists the six by node id (story-08:11,15). AC1's "environment-specific
     red" cannot be written honestly without the job and OS for each failure.
   - The three macOS reds should be tried on this Mac before anyone calls them
     environment-specific.

2. Boundary 2 diagnoses the two glass restart failures in the wrong place.
   - Both die on the FIRST request to the FIRST hub, before any restart:
     tests/e2e/test_hs200_task_resume_glass.py:659 (POST /api/projects, Content-Length 87)
     and :743. Both return ConnectionRefused.
   - "Make restart rigs retain their isolated config" (story-08:37) does not address that.
     _boot already pins CONFIG_FILE for the whole test (tests/e2e/glass_infra.py:215), and
     the pin is resolved dynamically (holdspeak/config/core.py:47-48).
   - Probable cause from reading the code, not reproduced. MeetingWebServer.start() returns
     once _started is set (holdspeak/web_server.py:420). _started is set inside the FastAPI
     startup hook (:1326). uvicorn awaits lifespan.startup() BEFORE it binds the socket
     (uvicorn/server.py:97). So start() can hand back a URL nobody is listening on yet.
   - These two tests are the ones that hit urllib immediately. The other rigs launch
     Chromium first, which hides the race.
   - If confirmed, this is class (b) in product code. Every caller of start() shares it,
     including the owner's launch-URL path.
   - Status: CONDITIONAL DIAGNOSIS. Astra must reproduce it, or tighten the window with a
     sleep in the startup hook, before choosing a fix.
   - Tenet 3 (help, accelerate) applies: a rig-config fix would go green by luck and the
     flake would come back.

3. Boundary 4 assumes a persisted field that does not exist.
   - "Restore persisted default_decision when hydrating" (story-08:39) cannot work as
     written. The tool_call part's meta_json is written at
     holdspeak/services/thread_service.py:1328-1335 with id, name, arguments, class and state.
   - default_decision is computed AFTER that write (:1337-1345) and only ever broadcast (:1358).
   - hydrateToolRows rebuilds each row without it (web/src/desk/threads.ts:1083-1100).
     It then spreads the rebuilt rows OVER the live ones (:1106), which erases the
     defaultDecision the live frame delivered (:956).
   - AC2's "survives reload" therefore needs a small backend leg: compute the decision
     before append_part and include it in the meta. It also needs the merge-order fix in
     threads.ts.
   - That stays inside "no new interface". It is still a product write path, and the
     design should say so.
   - This is the owner-facing finding. ThreadPullout.tsx:640-664 treats an undefined
     decision as Allow: Allow becomes primary and takes autoFocus. After hydration, a tool
     call that violated a guardrail shows Allow focused, and Enter approves it. This fails
     the ratified HS-153-03 face and UX-CANON "build what was ratified".
   - The window is bounded by _TOOL_DEADLINE_S = 30s (thread_service.py:65), so there is
     no legacy backfill to do.

4. The guardrail 'allow' on CI has two possible producers, and the face cannot tell them apart.
   - data-default-decision renders `row.defaultDecision || "allow"` (ThreadPullout.tsx:640).
   - "No guardrail ran or hydration erased it" reads the same as "the server said allow".
   - The server says allow whenever control_mode is "yolo" (thread_service.py:1342-1345,
     default lambda :142). The fixture depends on Config.load() seeing
     home/.holdspeak/config.json (tests/e2e/test_hs153_practice_glass.py:486-489;
     holdspeak/web/routes/_thread_factory.py:32).
   - Hydration overwrite is the likelier cause, given finding 3, but it is not proven.
   - Condition: capture the thread_tool_pending frame in the red run before classifying.

5. AC5 presupposes an xdist polluter that probably does not exist.
   - This is a hypothesis with strong circumstantial support, and I did not run it.
   - _service() builds HeartbeatService with clock=None and quiet=(2,3) in UTC
     (tests/unit/test_phase200_attention.py:480-494). With no clock the service reads the
     wall clock (holdspeak/services/heartbeat_service.py:132-135). The quiet-hours verdict
     is taken from that instant (:382, :752).
   - Eleven of the class's 13 tests take this wall-clock path. Only the two quiet-hours
     tests inject a clock.
   - Any run between 02:00 and 02:59 UTC answers held_quiet_hours where the tests expect sent.
   - The recorded "eight failed under -n 4" sits in the capture gap between 02:41Z and
     03:43Z (evidence-story-04.md:744 to :846). The two "serial-green" reruns are stamped
     03:43:04Z and 03:43:06Z (:858, :870), after the window closed.
   - That (c) classification in evidence-story-04.md:913-928 is mine (lane B). On this
     reading it is wrong, and I withdraw it pending the falsifier below.
   - The class did NOT fail in CI run 35478778899, whose unit job ran about 00:30-01:30Z.
   - Falsifier: inject a _Clock at 02:30Z into _service and run the class serially. If
     that goes red, it is class (a), a test defect. The fix is a fixed default clock in
     _service.
   - In that case "xdist reproduction" and "name the polluter" (story-08:24,30,40) cannot
     be satisfied and must be amended visibly (TWO-BRAINS §3, "a brief that changes a
     chartered criterion").
   - If I am wrong and it stays green at 02:30Z, boundary 5 stands as written.

6. Boundary 1 is sound, with one stale anchor and one risk.
   - Cause on CI: the unit job runs with a bare HOME (test.yml:116). Some earlier unit test
     writes ~/.config/holdspeak or ~/.local/share/holdspeak. Then test_the_running_suite_is_
     itself_isolated (tests/unit/test_phase200_ci_isolation.py:79-95) sees an "installation"
     and fails.
   - HOME=$(mktemp -d) fixes it. The docstring at :55-59 then needs updating, because it
     says the jobs run unisolated.
   - Risk: isolating HOME on the macos-14 integration job (test.yml:180) hides
     ~/.cache/huggingface. The core-path smoke test then re-downloads whisper "tiny" or
     skips (test.yml:172-179). Integration was GREEN in that run. Either pass HF_HOME
     through the way the e2e job passes npm_config_cache (:257-271), or leave that job alone.
   - The honest ledger line: a unit test writes into the real HOME. Name that writer even
     if isolation makes it harmless.

7. Boundaries 2 (unit leg) and 3 are correct as class (a).
   - Custody: the red is `database_identity != before_file` with identical digests. Linux
     reused the inode after unlink + copy2 (tests/unit/test_phase200_task_resume.py:716,723,727).
     Custody itself, asserted at :728, never failed.
   - Custody fix: copy to a sibling path, then os.replace while the old inode is still alive.
   - Transcriber: on the Linux runner "mlx" raises and compares raw, and "auto" is
     unresolvable without faster-whisper (holdspeak/transcribe.py:64-67,122-146). Two builds
     is the CORRECT answer there.
   - Transcriber fix: pin _is_darwin_arm64 and _module_available in the test. No product change.

CONDITIONS:
C1. Name the six node ids in the story, each with its CI job and OS, before briefing
    (finding 1).
C2. Rewrite boundary 2's e2e leg as "diagnose first-boot readiness". A rig-config edit is
    not an acceptable fix for a ConnectionRefused at line 659. If the start()/bind race
    reproduces, fix it in web_server.py so readiness means the socket is listening, and
    fence it (finding 2).
C3. State in boundary 4 that default_decision gets persisted in the tool_call meta and
    that hydration merges under live rows. The Deny-focused fence must FAIL pre-fix through
    a forced hydrate or reload. A lucky ordering is not proof (finding 3;
    reference_lying_test_doubles).
C4. Run finding 5's falsifier first. If it goes red, amend AC5 and boundary 5 visibly to
    "fixed wall-clock defect in the rig, proven red at an injected 02:30Z". The
    two-serial-green doctrine cannot detect a time-of-day fault, so do not rely on it here.
C5. Integration-job HOME isolation happens only with a cache passthrough, or not at all
    (finding 6).
No tenet objects to the scope. It is small repair with no new face or interface
(tenets 1-3 satisfied).

MISSED (ranked by cost to the owner):
1. Fail-open Deny. After hydration the guardrail box puts Allow in focus, so Enter
   approves a violating tool call. The story frames this as a test going green. It is the
   one item here that touches the owner's hands (finding 3).
2. start() returns before bind. This is a product readiness race that affects every real
   launch. It is not a rig quirk (finding 2).
3. The "pollution family" is probably a clock fault, not pollution. Left as written,
   workers spend the lane hunting a polluter that does not exist (finding 5).
4. database_identity can miss a replaced file when Linux reuses the inode. That is HS-200-02's
   question, not custody's. It is out of scope here and belongs in the ledger
   (holdspeak/services/project_service.py:310-316).
5. Once CI isolates HOME, the docstring at test_phase200_ci_isolation.py:55-59 becomes false.
6. The "Tuesday" sentence (story-08:11) promises the owner outcomes. Most of this story
   is CI hygiene. Only the guardrail item and the bind race reach the owner.

TUESDAY: Mostly not applicable, since this story restores green rather than a face. The one
screen it touches, the guardrail decision box, is usable by a tired owner only if C3 lands:
Deny focused after reload, at 1440 and 393.

UNKNOWN:
- Nothing was reproduced on this Mac, by instruction. The macOS e2e reds may or may not
  reproduce here.
- Whether the bind race is the actual cause of the ConnectionRefused. The captured uvicorn
  CancelledError is consistent with teardown in mid-startup, and it does not prove the
  cause. Port reuse at _find_free_port is the alternative.
- Which producer emitted 'allow' on CI (finding 4).
- The exact start time of the -n 4 run behind finding 5. It is inferred from capture-stamp
  gaps, not from a log.
- The two main runs for 3a78bece and 321247d2 were still queued or in progress when I read
  them, so "six" may not be the current count.
- Which unit test writes the installation marker into a bare HOME.
```

## Astra response

Accepted C1–C5. CI job/OS and exact nodes are in the story. The guardrail needs persisted metadata plus hydration preservation; no face redesign. Restart failures concern first-boot listener readiness; an event-gated probe precedes the product repair. The ambient 02:30 UTC probe reproduced exactly eight attention failures, so AC5 is visibly amended to a deterministic test clock; no pollution reset or serial mark. Integration HOME isolation must retain HF_HOME. Full-suite pre-fix diagnostic run was interrupted once the clock falsifier resolved its purpose; it is not full-suite proof. Final full verification remains required.

## Correction from counsel on built

The before shot shows Allow primary and Deny focused. The observed defect was a split signal. No Enter key gesture was observed; the earlier “Enter approves” inference is withdrawn. See story-08-built-muaddib.md.
