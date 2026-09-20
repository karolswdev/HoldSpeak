# HS-201-08 — Daily loop and remote isolation

CLI confirms claude-fable-5-1 session 416adc59-a8c4-43b4-9a49-e9db0e8faf36. Root accepts conditions; implementation pending.

**Check — Muad'Dib (claude-fable-5-1), continuation ruling on the DAILY LOOP and REMOTE SETTINGS families for HS-201-08, 2026-09-20.**

- **Session:** `CLAUDE_SESSION_ID` is unset, so I state no confirmed id.
- **Method:** read-only. I ran no tests, made no edits and used no workers.
- **What I read:**
  - `tests/e2e/test_phase200_daily_loop.py:1-40`, `:107-108`, `:160-200`, `:895-935`
  - `tests/unit/test_hs172_loop_wire.py:76-118` (root cited it under `tests/e2e/`, but it lives in `tests/unit/`)
  - `tests/e2e/test_hs174_remote_settings_glass.py:60-75`, `:236-275`
  - `holdspeak/principals.py:103,272`
  - every product consumer of `agent_credentials`
- **What I did not read:** Luna's red and green logs, and the traces in `full-worksteal.log`. Those stand as root's readings.

```
VERDICT: RATIFY-WITH-CONDITIONS
  Both repairs are ratified. The remote-settings repair is ratified as proposed. The
  daily-loop repair needs one change to its fixture proof (D2), and the owner must be
  told about it in the terms set out under D5.

FINDINGS:

DAILY LOOP
1. Classification (a) is correct, and it follows from a ratified decision.
   - :920 waits for two proposals produced by `Run intelligence` through "the real
     plugin host, the real bridge" (module contract, :14-16).
   - The lane-A amendment in current-phase-status.md ("Decisions made", 2026-09-19)
     removed that production entry on purpose. The job succeeds, the coverage is read,
     and `engine.plugin_calls == []`.
   - So the test asserts a posture that the phase retired.
   - The same amendment already carries four strict xfails in
     test_hs200_meeting_outcomes_glass.py.
   - Splitting this test instead of adding a fifth xfail is the better choice, because
     six of its eight stations do not depend on the retired entry.

2. The proposed split is the honest minimum, and its order is right.
   - FIRST it pins the current law on the real run:
     - the job succeeded;
     - scripted summary plus coverage 3;
     - `proposals == []`;
     - `plugin_calls == []`;
     - the Review face says PROPOSALS NOT RUN and shows no EXTRACTED.
   - That part is a fence that fails if someone quietly re-enables the pipeline.
   - THEN it seeds the historical proposals so that the remaining stations keep running:
     S3 confirm, S4 attention, the day boundary, S5 recall, S6 people, S7 completion
     and S8 carry.
   - Discarding day 2 would throw away the only end-to-end proof that a decision and a
     commitment survive a hub restart. That proof is first-use value (tenet 3).

3. One thing in the proposal I would not ratify as written: the seed shapes.
   - The cited source, test_hs172_loop_wire.py:79-118, writes artifacts with a raw
     `INSERT INTO artifacts` and a hand-typed `structured_json`.
   - That source is itself a fixture. The real plugins do not produce it. Copying its
     shapes into an e2e walk is the lying-double scar
     (reference_lying_test_doubles): the bridge would be proven against a shape nobody
     has checked against the producer.
   - The daily-loop file already holds the real thing. `DECISIONS_JSON` and
     `ACTIONS_JSON` (:107-108 region) are the scripted PROVIDER outputs that the real
     `decision_capture` and `action_owner_enforcer` plugins used to parse.
   - Condition D2 follows from this.

REMOTE SETTINGS
4. Classification (c) is correct, and it is properly earned.
   - Root reports two serial greens.
   - A NAMED producer reproduces the exact red in sequence.
   - The mechanism is visible in code:
     - `agent_credentials = AgentCredentialStore()` is a process-global singleton
       (principals.py:272).
     - `_boot` resets the database and never resets that store.
     - The glass test clicks `page.locator(".btn", has_text="Revoke").first` (:261).
       With a leftover `test-sweep-runner` row from test_hs174_runner_loopback.py, that
       is the WRONG row.
     - It then waits for `test-glass-runner` to detach, and that never happens.
   - Root is right to record the actual predecessor in the full run as unknown.

5. The monkeypatch is coherent. I checked this because a half-patched singleton would
   make things worse.
   - Every product consumer binds the store at CALL time or through `app.state`:
     - web_server.py:403 and :615-621, which are function-local imports;
     - gate_routes.py:53-63, via `request.app.state.agent_credentials`;
     - mcp_http.py:75, via app.state;
     - ws.py:28 and voice_stream.py:112, local imports;
     - coder_factory.py:73,196, local imports.
   - None of them holds a module-top reference.
   - So patching `holdspeak.principals.agent_credentials` BEFORE `_boot` gives the whole
     hub one fresh store.
   - Stopping the server before monkeypatch restores the attribute is the right
     teardown order.

6. The existing fixture never stops its hub. `setup` (:63-67) boots a server and returns
   None.
   - There is no yield and no `server.stop()`.
   - Four parametrized tests leave four live hubs in the worker.
   - The proposed `yield` plus `finally: server.stop()` fixes a real leak.
   - This is also a concrete candidate for the fd accumulation that I asked to have
     ledgered (S4 in the interrupted-send ruling). Name it there.

CONDITIONS:

DAILY LOOP
D1. One file: tests/e2e/test_phase200_daily_loop.py.
    - No product route changes.
    - No re-enabling of frozen plugins.
    - No skip and no xfail.
    - No assertion from S3 through S8 is removed or loosened.
D2. Mint the historical artifacts through the REAL producer where that is possible.
    - Run the real `decision_capture` and `action_owner_enforcer` plugin classes
      directly on the imported transcript, with the file's existing scripted engine.
    - Record their actual output through the real `db.plugins.record_artifact`.
    - Then run the real `ProposalBridgeService.bridge_meeting_artifacts`.
    - If the plugins cannot be invoked in isolation within this one file:
      - hand-built artifacts are acceptable ONLY if the test also asserts that their
        `structured_json` parses through the real plugin's own output validator or
        schema constant;
      - evidence must say which path was taken, and why.
    - Do not copy test_hs172_loop_wire.py's raw INSERT.
D3. The current-law block must be proven red in both directions.
    - Pre-edit, it captures the existing full-run failure.
    - A canary that forces one plugin call, or one proposal, must make the new
      `plugin_calls == []` and `proposals == []` assertions FAIL.
D4. Rewrite the module contract and the walk labels.
    - S2 no longer claims "the real plugin host, the real bridge" from
      `Run intelligence`.
    - The docstring and a `walk.fact` state three things:
      - the proposals are a HISTORICAL FIXTURE;
      - they were not produced by the summary;
      - they were not produced by any current owner gesture.
    - "NORMAL CONTROLS" at :4 must carve out that one seeded step by name.
D5. Evidence and the PR body say the following, in these terms:
    - "Day 2 continuity is proven from a seeded day-1 state."
    - "No current product path creates the decision or the commitment that day 2
      carries."
    - This sentence is the honest cost of the split. It belongs in front of the owner,
      with the BACKLOG return path next to it.
D6. Green at both widths, with shots, and root views them.
    - The Review face in the PROPOSALS NOT RUN state needs a shot at 1440 and at 393.
      It is a face state that no existing shot covers.

REMOTE SETTINGS
R1. One file: tests/e2e/test_hs174_remote_settings_glass.py.
    - No production store change.
    - No global or autouse fixture in conftest.
    - Do not edit test_hs174_runner_loopback.py.
R2. The fixture does these steps, in this order:
    - patch the fresh store;
    - `_boot`;
    - `yield`;
    - `server.stop()` in a `finally`.
    Monkeypatch then restores the module attribute after the hub has closed.
R3. Target the row.
    - Scope Revoke to the ledger row whose primary is `test-glass-runner`.
    - Wait for THAT row to detach.
    - Keep the second-credential leg: seed another credential through the real API.
    - After the targeted revoke, assert that the other row is still present AND its
      token still derives a principal.
    - That leg proves the row targeting did not hide a revoke-all bug. It also preserves
      the hard-revoke law.
R4. Capture the following through dw:
    - two quiet serial greens before the edit;
    - the real producer sequence red (loopback file, then glass file);
    - the identical sequence green afterwards;
    - the glass file under `-n 4`.
    - Do NOT reduce the (c) proof to the two serial greens alone. They did not find the
      cause last time.
R5. Ledger with a home: the credential store is process-global.
    - Any rig that boots more than one hub in a process shares it.
    - Other consumers still need isolation.
    - Make no claim that it is globally cleared.

BOTH
X1. The closing sequence restarts after all four repairs:
    - rerun the web check and record the exit file plus zero BRANCH-NEW;
    - take a fresh T1;
    - run the eleven docs commands under Python 3.12;
    - run one complete worksteal run to 100% with zero failed and zero errors.
    F1-F6 stand unchanged.
X2. The story and the PR body list SEVEN repair families.
    - They say that the first complete worksteal run was RED with 6 failed.
    - Visible amendments are made per TWO-BRAINS §3.

MISSED (ranked by cost to the owner):
1. After D5, nothing in this product's tests proves that a decision or a commitment can
   be CREATED by the owner today and then carried forward.
   - The first-use path ends at the summary.
   - This is the real content of the lane-A amendment.
   - A green suite must not blur it. It belongs at the top of the phase status doc's
     ledger, not only in BACKLOG.
2. The glass fixture that never stopped its hub has been leaking a server per test for
   as long as this file has existed.
   - Other glass classes that copy the same `setup` pattern probably do the same.
   - Add the grep result to the fd ledger as one line. Fix no others here.
3. A process-global credential store is a test-isolation problem today.
   - In an in-process hub restart it would also carry live agent tokens across the
     restart.
   - Nobody has asked whether that is the intended law.
   - One ledger line, with no ruling from me.

TUESDAY:
- No owner-facing face changes.
- Remote access: he issues and revokes a credential, and the row goes.
- Daily loop: what he can do on Tuesday is get the summary. The carried-forward
  decision is not something he can produce yet. The record must say so.

UNKNOWN:
- I did not read:
  - the trace lines in full-worksteal.log;
  - the two remote serial logs;
  - the producer-red log;
  - any daily-loop worker red.
- Whether the real plugins can be invoked standalone inside one test file (D2).
- Which test actually preceded the remote glass test in the full run.
- Whether removing the leaked hubs changes the fd pressure, and therefore whether any
  other test's behaviour shifts in the next complete run.
- The outcome of the next complete run and of the PR's CI.
```
