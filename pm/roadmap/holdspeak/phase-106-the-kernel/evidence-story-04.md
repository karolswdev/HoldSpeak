# Evidence - HS-106-04

- **Story:** HS-106-04 - The broker and the journal — four calls
- **Status:** done
- **Date:** 2026-07-26

## Proof

### Captured run — 2026-07-27T02:26:49Z

- **Command:** `uv run pytest -q -s tests/unit/test_kernel_broker.py tests/unit/test_kernel_effect_fence.py tests/unit/test_coder_gate.py tests/integration/test_gate_threat_model.py tests/integration/test_kernel_real_hub.py tests/unit/test_api_surface.py tests/unit/test_db_schema_policy.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 05c8a4f52b91fe70133736fffbdd7b95118482bf

```text
...{"tamper":"journal_record_hash_mismatch","restored":"ok"}
..............................................{"agent_decide": "principal_right_required", "claim": "claimed", "cursor_replay_same": true, "immutable": "admitted_envelope_immutable", "receipt": "succeeded", "recovered": "hub_restart_during_decision", "refusal_receipt": "journal_content_forbidden", "sigkill": -9, "submit": "awaiting_decision"}
..............
63 passed in 14.04s
```

### Captured run — 2026-07-27T02:27:46Z

- **Command:** `bash /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/755cdf1e-8c7b-4e33-923d-a46dc3bb7d49/scratchpad/kernel_guard_mutations.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 05c8a4f52b91fe70133736fffbdd7b95118482bf

```text
CONDITIONAL MUTATION NAMED: E           driver-specific conditional in broker module: holdspeak/kernel/broker.py:297 (if dispatch)
LINE MUTATION NAMED: E           kernel broker module over 300-line budget: holdspeak/kernel/broker.py: 316 lines
..                                                                       [100%]
2 passed in 0.05s
```

### Captured run — 2026-07-27T02:28:08Z

- **Command:** `bash -c set -o pipefail; uv run pytest -q --ignore=tests/e2e/test_metal.py 2>&1 | tee /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/755cdf1e-8c7b-4e33-923d-a46dc3bb7d49/scratchpad/full-final.txt`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 05c8a4f52b91fe70133736fffbdd7b95118482bf

```text
ssssssssssssssssssssssssssssssss........................................ [  1%]
........................................................................ [  3%]
.s...................................................................... [  5%]
..............................................................ss........ [  6%]
........................................................................ [  8%]
........................................................................ [ 10%]
........................................................................ [ 11%]
........................................................................ [ 13%]
........................................................................ [ 15%]
........................................................................ [ 16%]
........................................................................ [ 18%]
........................................................F...F.......F... [ 20%]
........F............................................................... [ 21%]
............F........................................................... [ 23%]
........................................................................ [ 25%]
........................................................................ [ 26%]
........................................................................ [ 28%]
........................................................................ [ 30%]
........................................................................ [ 31%]
........................................................................ [ 33%]
........................................................................ [ 35%]
........................................................................ [ 36%]
........................................................................ [ 38%]
........................................................................ [ 40%]
.................................................................F...... [ 42%]
........................................................................ [ 43%]
........................................................................ [ 45%]
........................................................................ [ 47%]
........................................................................ [ 48%]
........................................................................ [ 50%]
........................................................................ [ 52%]
........................................................................ [ 53%]
........................................................................ [ 55%]
.................s...................................................... [ 57%]
........................................................................ [ 58%]
........................................................................ [ 60%]
........................................................................ [ 62%]
........................................................................ [ 63%]
........................................................................ [ 65%]
........................................................................ [ 67%]
........................................................................ [ 68%]
........................................................................ [ 70%]
........................................................................ [ 72%]
........................................................................ [ 73%]
........................................................................ [ 75%]
........................................................................ [ 77%]
........................................................................ [ 79%]
........................................................................ [ 80%]
........................................................................ [ 82%]
........................................................................ [ 84%]
........................................................................ [ 85%]
........................................................................ [ 87%]
........................................................................ [ 89%]
........................................................................ [ 90%]
........................................................................ [ 92%]
........................................................................ [ 94%]
........................................................................ [ 95%]
........................................................................ [ 97%]
........................................................................ [ 99%]
..................................                                       [100%]
=================================== FAILURES ===================================
________________ test_meeting_recipe_yields_a_real_open_action _________________

real_manager = <uat.conductor.runs.RunManager object at 0x1341f2df0>

    def test_meeting_recipe_yields_a_real_open_action(real_manager):
        run = _boot_or_skip(real_manager, "golden-43")
>       result = real_manager.apply_recipe(run.id, "meeting-just-ended-open-actions")
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/uat/test_induction_integration_43.py:52: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
uat/conductor/runs.py:387: in apply_recipe
    return self.recipes.apply(name, run_id, self, allow_intel=allow_intel)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <uat.conductor.induction.recipes.RecipeEngine object at 0x133cf5c10>
name = 'meeting-just-ended-open-actions', run_id = 'run-20260727T023218-48ccf2'
host = <uat.conductor.runs.RunManager object at 0x1341f2df0>

    def apply(
        self, name: str, run_id: str, host: "RecipeHost", *, allow_intel: bool = True
    ) -> ApplyResult:
        order = self.registry.resolve_order(name)
        target = self.registry.load(name)
    
        if target.requires_intel and not allow_intel:
            raise RecipeError(
                f"recipe {name!r} requires intel (the .43 LAN endpoint) but "
                "intel is disabled for this apply"
            )
    
        # 1. Ensure the run is booted on the recipe's deck + cache posture.
        restarted = host.ensure_deck(run_id, target.deck, link_caches=target.link_caches)
    
        client = host.product_client(run_id)
        home = host.run_home(run_id)
        evaluator = ProbeEvaluator(client, home=home, run_id=run_id)
    
        # The combined probe is the target's own probe (includes stage the world;
        # the target's probe is the authoritative claim). Included recipes still
        # contribute their seeds/actions below.
        probe_spec = target.probe
    
        # 2. Probe-first idempotency.
        pre = evaluator.evaluate(probe_spec)
        if pre.ok and probe_spec:
            return ApplyResult(
                recipe=name,
                deck=target.deck,
                already_satisfied=True,
                probe=pre.to_dict(),
                restarted=restarted,
            )
    
        # 3. Stage: seeds (deps first), then actions (deps first).
        seed_outcomes: list[dict] = []
        action_log: list[dict] = []
        for rn in order:
            r = self.registry.load(rn)
            for seed_name in r.seeds:
                manifest = self.seed_registry.load(seed_name)
                seed_outcomes.append(Seeder(client).apply(manifest).to_dict())
            for action in r.actions:
                action_log.append(self._run_action(action, run_id, host, client))
    
        # 4. Verify.
        post = evaluator.evaluate(probe_spec)
        result = ApplyResult(
            recipe=name,
            deck=target.deck,
            already_satisfied=False,
            probe=post.to_dict(),
            seeds=seed_outcomes,
            actions=action_log,
            restarted=restarted,
        )
        if probe_spec and not post.ok:
>           raise RecipeVerifyError(
                f"recipe {name!r} failed to verify: {post.summary()}", result
            )
E           uat.conductor.induction.recipes.RecipeVerifyError: recipe 'meeting-just-ended-open-actions' failed to verify: meeting_with_open_actions: timed out after 180s: meetings present but none with ≥1 open actions: Pylon incident war room (UAT seed)(0,queued)

uat/conductor/induction/recipes.py:240: RecipeVerifyError
__________________ test_intel_endpoint_dead_degrades_honestly __________________

real_manager = <uat.conductor.runs.RunManager object at 0x13306b2f0>

    def test_intel_endpoint_dead_degrades_honestly(real_manager):
        run = _boot_or_skip(real_manager)
>       result = real_manager.apply_recipe(run.id, "intel-endpoint-dead")
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/uat/test_induction_integration_local.py:73: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
uat/conductor/runs.py:387: in apply_recipe
    return self.recipes.apply(name, run_id, self, allow_intel=allow_intel)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <uat.conductor.induction.recipes.RecipeEngine object at 0x13478e7b0>
name = 'intel-endpoint-dead', run_id = 'run-20260727T024031-e076f8'
host = <uat.conductor.runs.RunManager object at 0x13306b2f0>

    def apply(
        self, name: str, run_id: str, host: "RecipeHost", *, allow_intel: bool = True
    ) -> ApplyResult:
        order = self.registry.resolve_order(name)
        target = self.registry.load(name)
    
        if target.requires_intel and not allow_intel:
            raise RecipeError(
                f"recipe {name!r} requires intel (the .43 LAN endpoint) but "
                "intel is disabled for this apply"
            )
    
        # 1. Ensure the run is booted on the recipe's deck + cache posture.
        restarted = host.ensure_deck(run_id, target.deck, link_caches=target.link_caches)
    
        client = host.product_client(run_id)
        home = host.run_home(run_id)
        evaluator = ProbeEvaluator(client, home=home, run_id=run_id)
    
        # The combined probe is the target's own probe (includes stage the world;
        # the target's probe is the authoritative claim). Included recipes still
        # contribute their seeds/actions below.
        probe_spec = target.probe
    
        # 2. Probe-first idempotency.
        pre = evaluator.evaluate(probe_spec)
        if pre.ok and probe_spec:
            return ApplyResult(
                recipe=name,
                deck=target.deck,
                already_satisfied=True,
                probe=pre.to_dict(),
                restarted=restarted,
            )
    
        # 3. Stage: seeds (deps first), then actions (deps first).
        seed_outcomes: list[dict] = []
        action_log: list[dict] = []
        for rn in order:
            r = self.registry.load(rn)
            for seed_name in r.seeds:
                manifest = self.seed_registry.load(seed_name)
                seed_outcomes.append(Seeder(client).apply(manifest).to_dict())
            for action in r.actions:
                action_log.append(self._run_action(action, run_id, host, client))
    
        # 4. Verify.
        post = evaluator.evaluate(probe_spec)
        result = ApplyResult(
            recipe=name,
            deck=target.deck,
            already_satisfied=False,
            probe=post.to_dict(),
            seeds=seed_outcomes,
            actions=action_log,
            restarted=restarted,
        )
        if probe_spec and not post.ok:
>           raise RecipeVerifyError(
                f"recipe {name!r} failed to verify: {post.summary()}", result
            )
E           uat.conductor.induction.recipes.RecipeVerifyError: recipe 'intel-endpoint-dead' failed to verify: runtime_endpoint_unreachable: runtime-test ok=False status='unavailable' in 0.0s: Backend 'openai_compatible' requires the 'openai' package. Install with: uv pip install holdspeak[dictation-openai]

uat/conductor/induction/recipes.py:240: RecipeVerifyError
______________ test_run_dispatched_onto_the_worker_returns_badged ______________

real_manager = <uat.conductor.runs.RunManager object at 0x133113070>

    def test_run_dispatched_onto_the_worker_returns_badged(real_manager):
        run = _boot_or_skip(real_manager, "mesh-node")
    
>       result = real_manager.apply_recipe(run.id, "mesh-run-on-worker")
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/uat/test_mesh_dispatch.py:55: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
uat/conductor/runs.py:387: in apply_recipe
    return self.recipes.apply(name, run_id, self, allow_intel=allow_intel)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <uat.conductor.induction.recipes.RecipeEngine object at 0x10fc87d70>
name = 'mesh-run-on-worker', run_id = 'run-20260727T024036-0b8947'
host = <uat.conductor.runs.RunManager object at 0x133113070>

    def apply(
        self, name: str, run_id: str, host: "RecipeHost", *, allow_intel: bool = True
    ) -> ApplyResult:
        order = self.registry.resolve_order(name)
        target = self.registry.load(name)
    
        if target.requires_intel and not allow_intel:
            raise RecipeError(
                f"recipe {name!r} requires intel (the .43 LAN endpoint) but "
                "intel is disabled for this apply"
            )
    
        # 1. Ensure the run is booted on the recipe's deck + cache posture.
        restarted = host.ensure_deck(run_id, target.deck, link_caches=target.link_caches)
    
        client = host.product_client(run_id)
        home = host.run_home(run_id)
        evaluator = ProbeEvaluator(client, home=home, run_id=run_id)
    
        # The combined probe is the target's own probe (includes stage the world;
        # the target's probe is the authoritative claim). Included recipes still
        # contribute their seeds/actions below.
        probe_spec = target.probe
    
        # 2. Probe-first idempotency.
        pre = evaluator.evaluate(probe_spec)
        if pre.ok and probe_spec:
            return ApplyResult(
                recipe=name,
                deck=target.deck,
                already_satisfied=True,
                probe=pre.to_dict(),
                restarted=restarted,
            )
    
        # 3. Stage: seeds (deps first), then actions (deps first).
        seed_outcomes: list[dict] = []
        action_log: list[dict] = []
        for rn in order:
            r = self.registry.load(rn)
            for seed_name in r.seeds:
                manifest = self.seed_registry.load(seed_name)
                seed_outcomes.append(Seeder(client).apply(manifest).to_dict())
            for action in r.actions:
                action_log.append(self._run_action(action, run_id, host, client))
    
        # 4. Verify.
        post = evaluator.evaluate(probe_spec)
        result = ApplyResult(
            recipe=name,
            deck=target.deck,
            already_satisfied=False,
            probe=post.to_dict(),
            seeds=seed_outcomes,
            actions=action_log,
            restarted=restarted,
        )
        if probe_spec and not post.ok:
>           raise RecipeVerifyError(
                f"recipe {name!r} failed to verify: {post.summary()}", result
            )
E           uat.conductor.induction.recipes.RecipeVerifyError: recipe 'mesh-run-on-worker' failed to verify: run_returned_badged: dispatch failed HTTP 502: None; run_claimed_by_worker: worker claims 0→1 (moved=True); hub provider='' scope='' (no-local=False); run_output_contains: output MISSING 'PYLON-CANARY-7' (0 chars)

uat/conductor/induction/recipes.py:240: RecipeVerifyError
__________________________ test_pack_d_stages_locally __________________________

real_client = <starlette.testclient.TestClient object at 0x13402fe70>

    def test_pack_d_stages_locally(real_client):
        """Pack D demos without the LAN: its bad-endpoint scenario stages + verifies."""
        created = real_client.post("/api/sittings", json={"pack": "pack-d-honest-failure"}).json()
        if created["run"] is None or created["run"]["status"] != "up":
            pytest.skip("product did not boot")
        sid = created["id"]
        # Stage the dead-endpoint scenario (fully local — port 9 refused).
        staged = real_client.post(f"/api/sittings/{sid}/stage", json={"scenario_id": "d-dead-endpoint-doctor"}).json()
>       assert staged["ok"], staged
E       AssertionError: {'ok': False, 'scenario_id': 'd-dead-endpoint-doctor', 'staging': [{'error': "recipe 'intel-endpoint-dead' failed to v...--no-open`): browser auto-open disabled.
E         Press Ctrl+C to stop.'}, 'ok': False, 'recipe': 'intel-endpoint-dead', ...}]}
E       assert False

tests/uat/test_packs.py:180: AssertionError
_________________ test_transcribe_up_but_unreachable_is_honest _________________

client = <starlette.testclient.TestClient object at 0x133f8e7b0>

    def test_transcribe_up_but_unreachable_is_honest(client):
        # Fake product reports 'up' but nothing actually serves the transcribe route,
        # so the proxy honestly reports it could not reach the product — never fakes.
        sid = client.post("/api/sittings", json={"pack": "smoke"}).json()["id"]
        r = client.post(f"/api/sittings/{sid}/transcribe", content=_silence_wav())
        body = r.json()
        assert body["ok"] is False
>       assert "reach" in body["error"].lower() or "not up" in body["error"].lower()
E       AssertionError: assert ('reach' in 'transcribe failed (http 502).' or 'not up' in 'transcribe failed (http 502).')
E        +  where 'transcribe failed (http 502).' = <built-in method lower of str object at 0x133c393e0>()
E        +    where <built-in method lower of str object at 0x133c393e0> = 'Transcribe failed (HTTP 502).'.lower
E        +  and   'transcribe failed (http 502).' = <built-in method lower of str object at 0x133c393e0>()
E        +    where <built-in method lower of str object at 0x133c393e0> = 'Transcribe failed (HTTP 502).'.lower

tests/uat/test_voice_notes.py:52: AssertionError
________ TestDatabaseShape.test_fresh_schema_matches_canonical_snapshot ________

self = <tests.unit.test_db.TestDatabaseShape object at 0x10dbc4410>
tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-449/test_fresh_schema_matches_cano0')
project_root = PosixPath('/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a2198eebd38f826cc')

    def test_fresh_schema_matches_canonical_snapshot(self, tmp_path, project_root: Path):
        """HS-31-04: the migration ladder was squashed to one canonical schema.
        A fresh build must match the committed snapshot exactly — any intended
        schema change must update tests/fixtures/db_schema_canonical.txt in the
        same commit, keeping the schema honest without a version ladder."""
        import re
        import sqlite3
        from holdspeak.db import Database
    
        Database(tmp_path / "schema_check.db")
        conn = sqlite3.connect(str(tmp_path / "schema_check.db"))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT type, name, sql FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
        ).fetchall()
        actual = "\n".join(
            f"{r['type']} {r['name']}: {re.sub(r'\\s+', ' ', (r['sql'] or '').strip())}"
            for r in rows
 
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-07-27T03:18:09Z

- **Command:** `bash -c set -o pipefail; uv run pytest -q --ignore=tests/e2e/test_metal.py 2>&1 | tee /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/755cdf1e-8c7b-4e33-923d-a46dc3bb7d49/scratchpad/full-final-executor-split.txt`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 05c8a4f52b91fe70133736fffbdd7b95118482bf

```text
ssssssssssssssssssssssssssssssss........................................ [  1%]
........................................................................ [  3%]
.s...................................................................... [  5%]
..............................................................ss........ [  6%]
........................................................................ [  8%]
........................................................................ [ 10%]
........................................................................ [ 11%]
........................................................................ [ 13%]
........................................................................ [ 15%]
........................................................................ [ 16%]
........................................................................ [ 18%]
........................................................................ [ 20%]
........................................................................ [ 21%]
............F........................................................... [ 23%]
........................................................................ [ 25%]
........................................................................ [ 26%]
........................................................................ [ 28%]
........................................................................ [ 30%]
........................................................................ [ 31%]
........................................................................ [ 33%]
........................................................................ [ 35%]
........................................................................ [ 36%]
........................................................................ [ 38%]
........................................................................ [ 40%]
........................................................................ [ 42%]
........................................................................ [ 43%]
........................................................................ [ 45%]
........................................................................ [ 47%]
........................................................................ [ 48%]
........................................................................ [ 50%]
........................................................................ [ 52%]
........................................................................ [ 53%]
........................................................................ [ 55%]
.................s...................................................... [ 57%]
........................................................................ [ 58%]
........................................................................ [ 60%]
........................................................................ [ 62%]
........................................................................ [ 63%]
........................................................................ [ 65%]
........................................................................ [ 67%]
........................................................................ [ 68%]
........................................................................ [ 70%]
........................................................................ [ 72%]
........................................................................ [ 73%]
........................................................................ [ 75%]
........................................................................ [ 77%]
........................................................................ [ 79%]
........................................................................ [ 80%]
........................................................................ [ 82%]
........................................................................ [ 84%]
........................................................................ [ 85%]
........................................................................ [ 87%]
........................................................................ [ 89%]
........................................................................ [ 90%]
........................................................................ [ 92%]
........................................................................ [ 94%]
........................................................................ [ 95%]
........................................................................ [ 97%]
........................................................................ [ 99%]
..................................                                       [100%]
=================================== FAILURES ===================================
_________________ test_transcribe_up_but_unreachable_is_honest _________________

client = <starlette.testclient.TestClient object at 0x1375b1550>

    def test_transcribe_up_but_unreachable_is_honest(client):
        # Fake product reports 'up' but nothing actually serves the transcribe route,
        # so the proxy honestly reports it could not reach the product — never fakes.
        sid = client.post("/api/sittings", json={"pack": "smoke"}).json()["id"]
        r = client.post(f"/api/sittings/{sid}/transcribe", content=_silence_wav())
        body = r.json()
        assert body["ok"] is False
>       assert "reach" in body["error"].lower() or "not up" in body["error"].lower()
E       AssertionError: assert ('reach' in 'transcribe failed (http 502).' or 'not up' in 'transcribe failed (http 502).')
E        +  where 'transcribe failed (http 502).' = <built-in method lower of str object at 0x137b9f3c0>()
E        +    where <built-in method lower of str object at 0x137b9f3c0> = 'Transcribe failed (HTTP 502).'.lower
E        +  and   'transcribe failed (http 502).' = <built-in method lower of str object at 0x137b9f3c0>()
E        +    where <built-in method lower of str object at 0x137b9f3c0> = 'Transcribe failed (HTTP 502).'.lower

tests/uat/test_voice_notes.py:52: AssertionError
=============================== warnings summary ===============================
tests/integration/test_web_transcript_import_api.py::test_txt_upload_uses_the_transcript_fallback_speaker
  /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a2198eebd38f826cc/.venv/lib/python3.13/site-packages/_pytest/threadexception.py:58: PytestUnhandledThreadExceptionWarning: Exception in thread meeting-import-5adad37a
  
  Traceback (most recent call last):
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a2198eebd38f826cc/holdspeak/web/routes/meeting_import.py", line 95, in _run_import_job
      import_transcript(
      ~~~~~~~~~~~~~~~~~^
          tmp_path,
          ^^^^^^^^^
      ...<6 lines>...
          started_at=started_at,
          ^^^^^^^^^^^^^^^^^^^^^^
      )
      ^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a2198eebd38f826cc/holdspeak/meeting_import.py", line 395, in import_transcript
      return _persist_import(
          db=db,
      ...<8 lines>...
          speakers_found=parsed.speakers_found,
      )
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a2198eebd38f826cc/holdspeak/meeting_import.py", line 325, in _persist_import
      db.intel.enqueue_intel_job(
      ~~~~~~~~~~~~~~~~~~~~~~~~~~^
          state.id,
          ^^^^^^^^^
          transcript_hash=state.transcript_hash(),
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
          reason=state.intel_status_detail,
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      )
      ^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a2198eebd38f826cc/holdspeak/db/intel.py", line 35, in enqueue_intel_job
      with self._connection() as conn:
           ~~~~~~~~~~~~~~~~^^
    File "/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/contextlib.py", line 148, in __exit__
      next(self.gen)
      ~~~~^^^^^^^^^^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a2198eebd38f826cc/holdspeak/db/core.py", line 1447, in _connection
      conn.commit()
      ~~~~~~~~~~~^^
  sqlite3.OperationalError: disk I/O error
  
  During handling of the above exception, another exception occurred:
  
  Traceback (most recent call last):
    File "/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/threading.py", line 1044, in _bootstrap_inner
      self.run()
      ~~~~~~~~^^
    File "/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/threading.py", line 995, in run
      self._target(*self._args, **self._kwargs)
      ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a2198eebd38f826cc/holdspeak/web/routes/meeting_import.py", line 136, in _run_import_job
      _set_import_status(
      ~~~~~~~~~~~~~~~~~~^
          db, meeting_id, "import_failed", f"{type(exc).__name__}: {exc}"
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      )
      ^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a2198eebd38f826cc/holdspeak/web/routes/meeting_import.py", line 72, in _set_import_status
      state = db.meetings.get_meeting(meeting_id)
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a2198eebd38f826cc/holdspeak/db/meetings.py", line 440, in get_meeting
      row = conn.execute(
            ~~~~~~~~~~~~^
          "SELECT * FROM meetings WHERE id = ?", (meeting_id,)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      ).fetchone()
      ^
  sqlite3.OperationalError: no such table: meetings
  
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.
    warnings.warn(pytest.PytestUnhandledThreadExceptionWarning(msg))

tests/integration/test_web_transcript_import_api.py::test_garbage_transcript_marks_the_row_honestly_and_is_removable
  /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a2198eebd38f826cc/.venv/lib/python3.13/site-packages/_pytest/threadexception.py:58: PytestUnhandledThreadExceptionWarning: Exception in thread meeting-import-7b32b5cb
  
  Traceback (most recent call last):
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a2198eebd38f826cc/holdspeak/web/routes/meeting_import.py", line 95, in _run_import_job
      import_transcript(
      ~~~~~~~~~~~~~~~~~^
          tmp_path,
          ^^^^^^^^^
      ...<6 lines>...
          started_at=started_at,
          ^^^^^^^^^^^^^^^^^^^^^^
      )
      ^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a2198eebd38f826cc/holdspeak/meeting_import.py", line 395, in import_transcript
      return _persist_import(
          db=db,
      ...<8 lines>...
          speakers_found=parsed.speakers_found,
      )
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a2198eebd38f826cc/holdspeak/meeting_import.py", line 325, in _persist_import
      db.intel.enqueue_intel_job(
      ~~~~~~~~~~~~~~~~~~~~~~~~~~^
          state.id,
          ^^^^^^^^^
          transcript_hash=state.transcript_hash(),
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
          reason=state.intel_status_detail,
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      )
      ^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a2198eebd38f826cc/holdspeak/db/intel.py", line 35, in enqueue_intel_job
      with self._connection() as conn:
           ~~~~~~~~~~~~~~~~^^
    File "/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/contextlib.py", line 148, in __exit__
      next(self.gen)
      ~~~~^^^^^^^^^^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a2198eebd38f826cc/holdspeak/db/core.py", line 1447, in _connection
      conn.commit()
      ~~~~~~~~~~~^^
  sqlite3.OperationalError: disk I/O error
  
  During handling of the above exception, another exception occurred:
  
  Traceback (most recent call last):
    File "/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/threading.py", line 1044, in _bootstrap_inner
      self.run()
      ~~~~~~~~^^
    File "/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/threading.py", line 995, in run
      self._target(*self._args, **self._kwargs)
      ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a2198eebd38f826cc/holdspeak/web/routes/meeting_import.py", line 136, in _run_import_job
      _set_import_status(
      ~~~~~~~~~~~~~~~~~~^
          db, meeting_id, "import_failed", f"{type(exc).__name__}: {exc}"
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      )
      ^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a2198eebd38f826cc/holdspeak/web/routes/meeting_import.py", line 72, in _set_import_status
      state = db.meetings.get_meeting(meeting_id)
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a2198eebd38f826cc/holdspeak/db/meetings.py", line 440, in get_meeting
      row = conn.execute(
            ~~~~~~~~~~~~^
          "SELECT * FROM meetings WHERE id = ?", (meeting_id,)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      ).fetchone()
      ^
  sqlite3.OperationalError: no such table: meetings
  
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.
    warnings.warn(pytest.PytestUnhandledThreadExceptionWarning(msg))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
SKIPPED [1] tests/e2e/test_dictation_learning_digest_spoken_e2e.py:33: opt-in: set HOLDSPEAK_SPOKEN_DICTATION_E2E=1 to run the spoken-dictation learning-digest e2e (uses macOS `say` + the Whisper base model)
SKIPPED [1] tests/e2e/test_live_bus.py:24: needs Playwright + a browser
SKIPPED [1] tests/e2e/test_route_preflight.py:26: pre-flight needs Playwright + a browser
SKIPPED [1] tests/e2e/test_spoken_meeting_e2e.py:41: opt-in: set HOLDSPEAK_SPOKEN_E2E=1 to run the spoken-meeting e2e
SKIPPED [1] tests/unit/test_mesh_discovery.py:21: could not import 'zeroconf': No module named 'zeroconf'
SKIPPED [1] tests/e2e/test_dictation_enrichment_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation enrichment e2e
SKIPPED [1] tests/e2e/test_dictation_journal_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation journal e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:44: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:52: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [12] tests/e2e/test_dogfood_plumbing_e2e.py:66: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:85: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:95: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [10] tests/e2e/test_meeting_transcription.py: Mock meeting fixture not found: /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a2198eebd38f826cc/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/integration/test_dictation_llama_cpp_e2e.py:72: llama-cpp-python and /Users/karol/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_llama_cpp.py:38: llama-cpp-python and /Users/karol/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /Users/karol/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
SKIPPED [1] tests/unit/test_dictation_grammars.py:91: could not import 'llama_cpp': No module named 'llama_cpp'
FAILED tests/uat/test_voice_notes.py::test_transcribe_up_but_unreachable_is_honest
1 failed, 4245 passed, 41 skipped, 2 warnings in 885.73s (0:14:45)
```

### Captured run — 2026-07-27T03:33:14Z

- **Command:** `uv run pytest -q -s tests/unit/test_kernel_broker.py tests/unit/test_kernel_effect_fence.py tests/unit/test_coder_gate.py tests/integration/test_gate_threat_model.py tests/integration/test_kernel_real_hub.py tests/unit/test_api_surface.py tests/unit/test_db_schema_policy.py tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 05c8a4f52b91fe70133736fffbdd7b95118482bf

```text
...{"tamper":"journal_record_hash_mismatch","restored":"ok"}
..............................................{"agent_decide": "principal_right_required", "claim": "claimed", "cursor_replay_same": true, "immutable": "admitted_envelope_immutable", "receipt": "succeeded", "recovered": "hub_restart_during_decision", "refusal_receipt": "journal_content_forbidden", "sigkill": -9, "submit": "awaiting_decision"}
...............
64 passed in 14.01s
```

### Captured run — 2026-07-27T03:33:53Z

- **Command:** `bash /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/755cdf1e-8c7b-4e33-923d-a46dc3bb7d49/scratchpad/kernel_guard_mutations.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 05c8a4f52b91fe70133736fffbdd7b95118482bf

```text
CONDITIONAL MUTATION NAMED: E           driver-specific conditional in broker module: holdspeak/kernel/broker.py:226 (if dispatch)
LINE MUTATION NAMED: E           kernel broker module over 300-line budget: holdspeak/kernel/broker.py: 325 lines
..                                                                       [100%]
2 passed in 0.32s
```
