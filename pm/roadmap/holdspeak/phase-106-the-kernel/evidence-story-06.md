# Evidence - HS-106-06

- **Story:** HS-106-06 - Thin slice II — actuator egress
- **Status:** done
- **Date:** 2026-07-27

## Outcome

`actuator.egress@1` is the third registered operation type and the second
heterogeneous effect driver. `submit` now creates and links the existing durable
actuator proposal by its native proposal ID; no second proposal or approval
record exists. The owner can read the exact native preview and payload through
`read` before deciding. `decide` advances the existing
`proposed -> approved | rejected` machine, then mints the existing generic
warrant. `ActuatorExecutor` remains the only egress driver: for kernel-linked
proposals it exact-claims the operation immediately before its existing parity
checks and connector call, then closes the generic receipt with the existing
audit-row ref.

The journal records `egress:<destination>` and the two declared data-class refs
at admission. The setup/trust projection reads the last terminal event for that
journaled egress ref, and the Desk's one badge names that destination. Existing
actuator audit rows project through `read(view=full)` as `native_receipts`; none
is copied into the kernel journal.

The real-hub proof submitted a webhook proposal, read its material, approved it,
terminated the hub, restarted on the same database, and only then executed it
through `ActuatorExecutor` against a real loopback HTTP destination. The exact
body arrived once and the terminal receipt was `succeeded`. A rejected proposal
produced a refusal receipt and no second outbound call. A stale expected
revision returned `operation_revision_conflict` before native approval. The
live Desk badge read `-> Custom webhook`; the inspected screenshot is
[`assets/hs-106-06-egress-badge.png`](./assets/hs-106-06-egress-badge.png).

## Where the spine resisted

The broker stayed driver-blind. All actuator behavior lives in the typed codec
or the actuator/web adapter; no actuator branch, dispatch table, or type test
entered admission, broker, journal, executor-plane, or runtime dispatch. The
final guard output is reproduced verbatim below: `2 passed in 0.05s`, followed
by every kernel module's line count (all below 300).

`native_id` is now earned generic shape rather than a provisional terminal-only
selector. Two durable actuator proposals can be approved for the same
`node:actuator-local` placement. `ActuatorExecutor.execute(proposal_id)` must
claim the operation linked to that exact proposal, not the older placement
candidate. The unit proof approved two proposals, executed the newer one, and
left the older operation in `awaiting_execution`. Terminal input and actuator
egress are now the two filtered callers.

The durable driver did **not** reproduce slice I's native-queue-loss boundary.
Both the existing proposal and the kernel operation survive a hub restart; the
proof observes `awaiting_execution` with no premature receipt after restart,
then exact-claims and closes it when `ActuatorExecutor` returns. No unclaimed
receipt was permitted and no executor-plane invariant was relaxed. The honest
remaining edge is generic liveness: if no executor ever returns, an approved
operation remains pending rather than fabricating a terminal outcome. This
slice needed no second adapter workaround for restart, but HS-106-07 should
carry that no-executor liveness question into the kill-criterion verdict.

No generic envelope field was added. Actuator-specific proposal material stays
inside the typed codec's arguments. The only shared codec surface added is
`project_receipts`, implemented by all three codecs; tool-call and terminal
return no native receipt projections.

## Full-suite adjudication

The final required command completed with **4,257 passed, 41 skipped, 5 failed,
1 warning in 953.66 seconds**. The five failures are exactly the user's
pre-adjudicated list and no others:

- `test_meeting_recipe_yields_a_real_open_action`: the known queued-intel
  180-second timeout.
- `test_intel_endpoint_dead_degrades_honestly`: the known missing `openai`
  optional dependency.
- `test_run_dispatched_onto_the_worker_returns_badged`: the known mesh 502 /
  absent canary result.
- `test_pack_d_stages_locally`: the same known missing-`openai` induction
  failure projected through Pack D.
- `test_transcribe_up_but_unreachable_is_honest`: the adjudicated wording drift
  (`Transcribe failed (HTTP 502).`).

The three `tests/e2e/test_live_bus.py` regressions from HS-106-02 are green after
the required main merge: **3 passed in 27.88 seconds**. The one warning is the
existing asynchronous meeting-import teardown race (`sqlite3.OperationalError`
after a test database is removed); it did not fail a test and is unrelated to
this slice.

## Proof

### Captured run — 2026-07-27T19:29:52Z

- **Command:** `bash -o pipefail -c uv run pytest -q tests/unit/test_actuator_kernel.py tests/integration/test_actuator_kernel_real_hub.py tests/unit/test_actuator_repository.py tests/unit/test_actuator_executor.py tests/unit/test_kernel_broker.py tests/unit/test_kernel_effect_fence.py tests/unit/test_trust_destinations.py tests/integration/test_web_setup_status_api.py tests/integration/test_web_trust_chip.py tests/integration/test_web_companion_slack.py && npm --prefix web run typecheck && npm --prefix web run test:desk`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** da2a5cbb61d83c66c9b9d4b9006bb0e83db873f2

```text
........................................................................ [ 83%]
..............                                                           [100%]
86 passed in 19.79s

> holdspeak-web@0.0.1 typecheck
> tsc --noEmit


> holdspeak-web@0.0.1 test:desk
> vitest run src/desk --maxWorkers=2


 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web

Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/axe-core/axe.js:16723:49
    at Object.get (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/axe-core/axe.js:11239:23)
    at _isIconLigature (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/axe-core/axe.js:16722:41)
    at /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/axe-core/axe.js:28288:54
    at Array.some (<anonymous>)
    at hasRealTextChildren (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/axe-core/axe.js:28287:35)
    at Rule.colorContrastMatches [as matches] (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/axe-core/axe.js:28249:12) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at createColoredCanvas (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canUseNewCanvasBlendModes.mjs:7:26)
    at canUseNewCanvasBlendModes (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canUseNewCanvasBlendModes.mjs:17:21)
    at file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canvasUtils.mjs:11:19
    at ModuleJob.run (node:internal/modules/esm/module_job:343:25)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at onImport.tracePromise.__proto__ (node:internal/modules/esm/loader:665:26)
    at VitestModuleEvaluator.runExternalModule (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/vitest/dist/module-evaluator.js:80:21) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at getTestContext (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/program/getTestContext.mjs:8:22)
    at getMaxFragmentPrecision (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/program/getMaxFragmentPrecision.mjs:8:16)
    at new _GlProgram (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/GlProgram.mjs:37:40)
    at Function.from (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/GlProgram.mjs:77:27)
    at new ParticleShader (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/scene/particle-container/shared/shader/ParticleShader.mjs:15:33)
    at new ParticleContainerPipe (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/scene/particle-container/shared/ParticleContainerPipe.mjs:29:26)
    at new CanvasParticleContainerPipe (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/scene/particle-container/canvas/CanvasParticleContainerPipe.mjs:8:5) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/src/desk/gl/engine.ts:205:7) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/src/desk/gl/engine.ts:205:7) undefined

 Test Files  40 passed (40)
      Tests  296 passed (296)
   Start at  13:30:17
   Duration  10.35s (transform 1.09s, setup 1.40s, import 3.93s, tests 2.98s, environment 8.77s)
```

### Captured run — 2026-07-27T19:30:38Z

- **Command:** `uv run pytest -q -s tests/integration/test_actuator_kernel_real_hub.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** da2a5cbb61d83c66c9b9d4b9006bb0e83db873f2

```text
{"badge_source": {"id": "companion_webhook", "name": "Custom webhook", "receipt": "1785180641.331476"}, "effect": {"text": "Kernel egress live"}, "historic_audit_projection": ["proposed", "approved", "executed"], "operation_id": "op_453868a6a74d4398be1f2ad03a6ea334", "real_destination": "http://127.0.0.1:50094/sink", "receipt": "succeeded", "rejected": "refused", "stale": "operation_revision_conflict"}
.
1 passed in 3.71s
```

### Captured run — 2026-07-27T19:30:49Z

- **Command:** `bash -euo pipefail -c uv run pytest -q tests/unit/test_kernel_effect_fence.py::test_kernel_broker_modules_stay_within_line_budget tests/unit/test_kernel_effect_fence.py::test_kernel_broker_has_zero_driver_specific_conditionals && wc -l holdspeak/kernel/*.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** da2a5cbb61d83c66c9b9d4b9006bb0e83db873f2

```text
..                                                                       [100%]
2 passed in 0.05s
       9 holdspeak/kernel/__init__.py
     231 holdspeak/kernel/actuator.py
      64 holdspeak/kernel/admission.py
     228 holdspeak/kernel/broker.py
     111 holdspeak/kernel/executor.py
     293 holdspeak/kernel/journal.py
      70 holdspeak/kernel/model.py
     136 holdspeak/kernel/process_input.py
      93 holdspeak/kernel/runtime.py
     147 holdspeak/kernel/tool_call.py
    1382 total
```

### Captured run — 2026-07-27T19:30:58Z

- **Command:** `node /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/755cdf1e-8c7b-4e33-923d-a46dc3bb7d49/scratchpad/shoot_egress.mjs`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** da2a5cbb61d83c66c9b9d4b9006bb0e83db873f2

```text
{"text":"→ Custom webhook","title":"Last receipted egress: 1785180327.4260201"}
```

### Captured run — 2026-07-27T19:39:46Z

- **Command:** `uv run pytest -q -s tests/integration/test_actuator_kernel_real_hub.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 525c1d14da0beae35c8f50dd31338d9dd74ea621

```text
{"badge_source": {"id": "companion_webhook", "name": "Custom webhook", "receipt": "1785181190.155036"}, "effect": {"text": "Kernel egress live"}, "historic_audit_projection": ["proposed", "approved", "executed"], "operation_id": "op_ae084834f002482fb664b14876d6bbac", "real_destination": "http://127.0.0.1:52316/sink", "receipt": "succeeded", "rejected": "refused", "reviewed_preview": "Kernel egress live", "stale": "operation_revision_conflict"}
.
1 passed in 3.82s
```

### Captured run — 2026-07-27T19:40:01Z

- **Command:** `bash -o pipefail -c uv run pytest -q --ignore=tests/e2e/test_metal.py 2>&1 | tee /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/755cdf1e-8c7b-4e33-923d-a46dc3bb7d49/scratchpad/full-suite-hs10606-final.txt`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 525c1d14da0beae35c8f50dd31338d9dd74ea621

```text
ssssssssssssssssssssssssssssssss........................................ [  1%]
........................................................................ [  3%]
..s..................................................................... [  5%]
.................................................................ss..... [  6%]
........................................................................ [  8%]
........................................................................ [ 10%]
........................................................................ [ 11%]
........................................................................ [ 13%]
........................................................................ [ 15%]
........................................................................ [ 16%]
........................................................................ [ 18%]
...........................................................F...F.......F [ 20%]
...........F............................................................ [ 21%]
...............F........................................................ [ 23%]
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
........................................................................ [ 41%]
........................................................................ [ 43%]
........................................................................ [ 45%]
........................................................................ [ 46%]
........................................................................ [ 48%]
........................................................................ [ 50%]
........................................................................ [ 51%]
........................................................................ [ 53%]
........................................................................ [ 55%]
..........................s............................................. [ 56%]
........................................................................ [ 58%]
........................................................................ [ 60%]
........................................................................ [ 61%]
........................................................................ [ 63%]
........................................................................ [ 65%]
........................................................................ [ 67%]
........................................................................ [ 68%]
........................................................................ [ 70%]
........................................................................ [ 72%]
........................................................................ [ 73%]
........................................................................ [ 75%]
........................................................................ [ 77%]
........................................................................ [ 78%]
........................................................................ [ 80%]
........................................................................ [ 82%]
........................................................................ [ 83%]
........................................................................ [ 85%]
........................................................................ [ 87%]
........................................................................ [ 88%]
........................................................................ [ 90%]
........................................................................ [ 92%]
........................................................................ [ 93%]
........................................................................ [ 95%]
........................................................................ [ 97%]
........................................................................ [ 98%]
..................................................                       [100%]
=================================== FAILURES ===================================
________________ test_meeting_recipe_yields_a_real_open_action _________________

real_manager = <uat.conductor.runs.RunManager object at 0x10f7f32f0>

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

self = <uat.conductor.induction.recipes.RecipeEngine object at 0x137c6fb30>
name = 'meeting-just-ended-open-actions', run_id = 'run-20260727T194402-7adf37'
host = <uat.conductor.runs.RunManager object at 0x10f7f32f0>

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

real_manager = <uat.conductor.runs.RunManager object at 0x1103cdef0>

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

self = <uat.conductor.induction.recipes.RecipeEngine object at 0x10f85d850>
name = 'intel-endpoint-dead', run_id = 'run-20260727T195217-1cec75'
host = <uat.conductor.runs.RunManager object at 0x1103cdef0>

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

real_manager = <uat.conductor.runs.RunManager object at 0x110b7c550>

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

self = <uat.conductor.induction.recipes.RecipeEngine object at 0x136e62f30>
name = 'mesh-run-on-worker', run_id = 'run-20260727T195224-976140'
host = <uat.conductor.runs.RunManager object at 0x110b7c550>

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

real_client = <starlette.testclient.TestClient object at 0x10fc6c490>

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

client = <starlette.testclient.TestClient object at 0x1358fff00>

    def test_transcribe_up_but_unreachable_is_honest(client):
        # Fake product reports 'up' but nothing actually serves the transcribe route,
        # so the proxy honestly reports it could not reach the product — never fakes.
        sid = client.post("/api/sittings", json={"pack": "smoke"}).json()["id"]
        r = client.post(f"/api/sittings/{sid}/transcribe", content=_silence_wav())
        body = r.json()
        assert body["ok"] is False
>       assert "reach" in body["error"].lower() or "not up" in body["error"].lower()
E       AssertionError: assert ('reach' in 'transcribe failed (http 502).' or 'not up' in 'transcribe failed (http 502).')
E        +  where 'transcribe failed (http 502).' = <built-in method lower of str object at 0x136aefbe0>()
E        +    where <built-in method lower of str object at 0x136aefbe0> = 'Transcribe failed (HTTP 502).'.lower
E        +  and   'transcribe failed (http 502).' = <built-in method lower of str object at 0x136aefbe0>()
E        +    where <built-in method lower of str object at 0x136aefbe0> = 'Transcribe failed (HTTP 502).'.lower

tests/uat/test_voice_notes.py:52: AssertionError
=============================== warnings summary ===============================
tests/integration/test_web_transcript_import_api.py::test_garbage_transcript_marks_the_row_honestly_and_is_removable
  /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/.venv/lib/python3.14/site-packages/_pytest/threadexception.py:58: PytestUnhandledThreadExceptionWarning: Exception in thread meeting-import-96382258
  
  Traceback (most recent call last):
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/holdspeak/web/routes/meeting_import.py", line 95, in _run_import_job
      import_transcript(
      ~~~~~~~~~~~~~~~~~^
          tmp_path,
          ^^^^^^^^^
      ...<6 lines>...
          started_at=started_at,
          ^^^^^^^^^^^^^^^^^^^^^^
      )
      ^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/holdspeak/meeting_import.py", line 395, in import_transcript
      return _persist_import(
          db=db,
      ...<8 lines>...
          speakers_found=parsed.speakers_found,
      )
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/holdspeak/meeting_import.py", line 325, in _persist_import
      db.intel.enqueue_intel_job(
      ~~~~~~~~~~~~~~~~~~~~~~~~~~^
          state.id,
          ^^^^^^^^^
          transcript_h
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-07-27T19:58:54Z

- **Command:** `uv run pytest -q tests/e2e/test_live_bus.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 525c1d14da0beae35c8f50dd31338d9dd74ea621

```text
...                                                                      [100%]
3 passed in 27.88s
```

### Captured run — 2026-07-27T20:00:34Z

- **Command:** `uv run python -c from pathlib import Path; p=Path("/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/755cdf1e-8c7b-4e33-923d-a46dc3bb7d49/scratchpad/full-suite-hs10606-final.txt"); lines=p.read_text().splitlines(); print("\n".join(line for line in lines if line.startswith("FAILED ") or " failed, " in line))`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 525c1d14da0beae35c8f50dd31338d9dd74ea621

```text
FAILED tests/uat/test_induction_integration_43.py::test_meeting_recipe_yields_a_real_open_action
FAILED tests/uat/test_induction_integration_local.py::test_intel_endpoint_dead_degrades_honestly
FAILED tests/uat/test_mesh_dispatch.py::test_run_dispatched_onto_the_worker_returns_badged
FAILED tests/uat/test_packs.py::test_pack_d_stages_locally - AssertionError: ...
FAILED tests/uat/test_voice_notes.py::test_transcribe_up_but_unreachable_is_honest
5 failed, 4257 passed, 41 skipped, 1 warning in 953.66s (0:15:53)
```

### Captured run — 2026-07-27T20:01:08Z

- **Command:** `bash -o pipefail -c uv run pytest -q tests/unit/test_actuator_kernel.py tests/integration/test_actuator_kernel_real_hub.py tests/unit/test_actuator_repository.py tests/unit/test_actuator_executor.py tests/unit/test_kernel_broker.py tests/unit/test_kernel_effect_fence.py tests/unit/test_trust_destinations.py tests/integration/test_web_setup_status_api.py tests/integration/test_web_trust_chip.py tests/integration/test_web_companion_slack.py && npm --prefix web run typecheck && npm --prefix web run test:desk`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 525c1d14da0beae35c8f50dd31338d9dd74ea621

```text
........................................................................ [ 83%]
..............                                                           [100%]
86 passed in 17.68s

> holdspeak-web@0.0.1 typecheck
> tsc --noEmit


> holdspeak-web@0.0.1 test:desk
> vitest run src/desk --maxWorkers=2


 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web

Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/axe-core/axe.js:16723:49
    at Object.get (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/axe-core/axe.js:11239:23)
    at _isIconLigature (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/axe-core/axe.js:16722:41)
    at /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/axe-core/axe.js:28288:54
    at Array.some (<anonymous>)
    at hasRealTextChildren (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/axe-core/axe.js:28287:35)
    at Rule.colorContrastMatches [as matches] (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/axe-core/axe.js:28249:12) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at createColoredCanvas (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canUseNewCanvasBlendModes.mjs:7:26)
    at canUseNewCanvasBlendModes (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canUseNewCanvasBlendModes.mjs:17:21)
    at file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/rendering/renderers/canvas/utils/canvasUtils.mjs:11:19
    at ModuleJob.run (node:internal/modules/esm/module_job:343:25)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at onImport.tracePromise.__proto__ (node:internal/modules/esm/loader:665:26)
    at VitestModuleEvaluator.runExternalModule (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/vitest/dist/module-evaluator.js:80:21) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at getTestContext (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/program/getTestContext.mjs:8:22)
    at getMaxFragmentPrecision (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/program/getMaxFragmentPrecision.mjs:8:16)
    at new _GlProgram (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/GlProgram.mjs:37:40)
    at Function.from (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/rendering/renderers/gl/shader/GlProgram.mjs:77:27)
    at new ParticleShader (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/scene/particle-container/shared/shader/ParticleShader.mjs:15:33)
    at new ParticleContainerPipe (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/scene/particle-container/shared/ParticleContainerPipe.mjs:29:26)
    at new CanvasParticleContainerPipe (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/scene/particle-container/canvas/CanvasParticleContainerPipe.mjs:8:5) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/src/desk/gl/engine.ts:205:7) undefined
Error: Not implemented: HTMLCanvasElement.prototype.getContext (without installing the canvas npm package)
    at module.exports (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/browser/not-implemented.js:9:17)
    at HTMLCanvasElementImpl.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/living/nodes/HTMLCanvasElement-impl.js:42:5)
    at HTMLCanvasElement.getContext (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/jsdom/lib/jsdom/living/generated/HTMLCanvasElement.js:131:58)
    at CanvasContextSystem.init (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/rendering/renderers/canvas/CanvasContextSystem.mjs:35:46)
    at CanvasRenderer.init (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/rendering/renderers/shared/system/AbstractRenderer.mjs:69:40)
    at processTicksAndRejections (node:internal/process/task_queues:105:5)
    at autoDetectRenderer (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/rendering/renderers/autoDetectRenderer.mjs:53:3)
    at _Application.init (file:///Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/node_modules/pixi.js/lib/app/Application.mjs:52:21)
    at WorldEngine.init (/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a60e76bf0c8e621e4/web/src/desk/gl/engine.ts:205:7) undefined

 Test Files  40 passed (40)
      Tests  296 passed (296)
   Start at  14:01:32
   Duration  9.29s (transform 919ms, setup 1.18s, import 3.58s, tests 2.91s, environment 7.78s)
```

### Captured run — 2026-07-27T20:01:48Z

- **Command:** `bash -euo pipefail -c uv run pytest -q tests/unit/test_kernel_effect_fence.py::test_kernel_broker_modules_stay_within_line_budget tests/unit/test_kernel_effect_fence.py::test_kernel_broker_has_zero_driver_specific_conditionals && wc -l holdspeak/kernel/*.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 525c1d14da0beae35c8f50dd31338d9dd74ea621

```text
..                                                                       [100%]
2 passed in 0.05s
       9 holdspeak/kernel/__init__.py
     231 holdspeak/kernel/actuator.py
      64 holdspeak/kernel/admission.py
     228 holdspeak/kernel/broker.py
     111 holdspeak/kernel/executor.py
     293 holdspeak/kernel/journal.py
      70 holdspeak/kernel/model.py
     136 holdspeak/kernel/process_input.py
      93 holdspeak/kernel/runtime.py
     147 holdspeak/kernel/tool_call.py
    1382 total
```
