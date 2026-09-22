# Check — Astra, 2026-09-22, counsel on built: PHILO-2-01 (PR #603 @ ac4b1111)

Session 01a0cafe-2338-77b3-948f-03c2f98c39d7 (resumed). Muad'Dib's response follows.

VERDICT: DO-NOT-RATIFY — [PR #603](https://github.com/karolswdev/HoldSpeak/pull/603), `ac4b1111`. References below use that commit. Concurrent, uncommitted rig changes are outside this verdict.

FINDINGS:

1. **Calibration rejects “any diff means success,” but still permits false passes.** Removing the calibration Refresh button’s handler still produced `pass`: the evaluator accepts the identity already on the page (`scripts/graph_walk.py:474`; `tests/fixtures/graph_walk_calibration.html:97`). A second probe returned `pass` with `elapsed_s=10`, `completion_bound_s=1`, and `within_bound=false`; the verdict ignores its deadline flag (`scripts/graph_walk.py:1180`, `:1186`). **Tenets 3 and 7.**

2. **Several predicates omit the owner’s promised result.** J10 passes when the entire Brief section disappears because “No brief yet” is then absent (`docs/internal/philo/graph/atlas.json:1758`). J3’s enabled-submit predicate also passes when the submit control does not exist (`atlas.json:521`; `scripts/graph_walk.py:442`). Both reproduced. Speech readiness checks absent warning text instead of the assignment response (`atlas.json:98`); J6 checks a succeeded-job count without establishing the promised summary and host (`atlas.json:1128`). These can certify the very failures the audit must find. **Tenets 3 and 7.**

3. **The atlas is not executable through the supplied rig as claimed.** Examples include `action: "type the engine address"` and `"click again"` (`atlas.json:512`, `:1819`), which `_ui_step` rejects (`scripts/graph_walk.py:868`). Each invocation creates a fresh HOME, but dependencies such as “previous case reached” have no execution or precondition-checking mechanism (`:1125`, `:1384`). Boundary steps can merely record a label without making the substitution (`:1020`). The smoke uses a separate, executable sample atlas (`tests/e2e/test_graph_walk_smoke.py:27`), so it does not fence this seam. **Tenets 3 and 7.**

4. **The runtime omissions exceed the ledger’s watch-service caveat.** The rig supplies no meeting-start callback and a no-op stop callback (`scripts/graph_walk.py:691`); production refuses an unbound start (`holdspeak/services/meeting_service.py:372`). It also never claims database ownership, which the intelligence drainer requires (`holdspeak/intel_queue_conductor.py:72`, `:129`). Thus `clock.intel_drainer` is not established as available merely by starting this server (`atlas.json:5443`). These are harness limitations, not product failures. **Tenets 3 and 7.**

5. **The graph model is proportionate to §8; the duplicated contracts are not.** Root fields do not constitute an unnecessary parallel inventory. However, graph and atlas independently define incompatible cases and steps (`graph.schema.json:304`; `atlas.schema.json:106`). **Eleven of 61 atlas cases fail the graph case schema**: nine applicable words-only cases plus J8 and next-day. “Every case validates” is therefore false (`story-01-the-rulebook-and-the-state-atlas.md:39`). A words-only case whose trigger succeeds raises `KeyError('predicate')`, rather than recording `blocked` (`scripts/graph_walk.py:1143`). Unreachable cases become `not_applicable`, losing their detailed reason (`:1032`, `:1370`). **Tenets 1 and 3.**

6. **Five production-reachability samples give a mixed result.** These are source checks, not live observations. Incorrect expectations fail **Tenets 3 and 7**.

   | Case | Source-backed conclusion |
   |---|---|
   | J9 owner-hand sweep | Reachable: the POST invokes `run_sweep(..., owner_hand=True)` (`holdspeak/web/routes/system/settings.py:321`). |
   | J9 timer sweep | First sweep is reachable. It does **not** prove the elapsed-interval state assigned to the case (`atlas.json:1334`; `holdspeak/runtime/heartbeat.py:102`, `:111`). The ledger correctly acknowledges this. |
   | J4 import | Production entry exists, but requires multipart `file`; the atlas supplies JSON and a fixture step without its required upload route (`atlas.json:891`; `holdspeak/web/routes/meeting_import.py:55`; `scripts/graph_walk.py:998`). |
   | J9 restore | The expected `unseen` result is wrong for the dismissed `needs_attention` predecessor. Reading clears dismissal and restores the producer’s attention state (`atlas.json:1640`, `:1658`; `holdspeak/db/projections.py:90`). |
   | J10 same-day generate | Service idempotency is real (`holdspeak/services/monday_brief_service.py:194`). But the populated Chair branch with untriaged items has no Generate-again button; the recipe omits shelving them (`atlas.json:1812`; `web/src/desk/chair/ChairHome.tsx:1114`, `:1155`). |

7. **The ledger is candid but not fully accurate.** Nine applicable words-only cases and four absent predicate kinds are accurate at the PR commit; the first-sweep qualification is correct. However, `record_only` explicitly exists and is produced when speech admission fails (`holdspeak/meeting_session/intel_admission.py:219`, `:286`), contradicting story line 43. The atlas still says the continuity horizon has no located producer (`atlas.json:5389`), although `REPLAY_HORIZON_DAYS = 14` supplies it (`holdspeak/services/needs_you_aggregate.py:163`). These states may remain unexercised; they must not remain misdescribed. **Tenets 3 and 7.**

CONDITIONS:

- Before live passes, make verdicts enforce the promised result, operation identity and completion bound. Add negative controls for the reproduced false passes.
- Reconcile the actual atlas with the executor: executable setup/trigger steps, checked preconditions, real boundary substitutions, and verified execution owners—or explicit tooling blocks before firing.
- Correct the sampled expectations and ledger; reconcile schema validation and blocked/unexercised records. The four owed predicate kinds remain shared preparation before live execution.

These defects do not prevent independent static source inspection. They prevent releasing the four-pass package as ready.

MISSED: Ranked by owner cost: false success on the missing Brief; harness limitations reported as product defects; incompatible contracts forcing both brains to reinterpret cases. Later, the generator also needs inventory-reference validation: replacing a Phase 1 reference with a nonexistent record still passed `philo_graph_validate.py:57`.

TUESDAY: No—the story’s claims of executable cases, validation and honest blocking exceed what exists.

UNKNOWN: I reran **49 unit fences successfully**, excluding the owner-path guard, in an isolated temporary copy of the PR. Additional probes reproduced the failures above. I did not run the product or e2e, access owner data, or edit the checkout; the recorded J9 live evidence was not independently reproduced.

## Muad'Dib's response, 2026-09-22

ACCEPTED, all seven. Astra reproduced three false passes in the rig (a replay identity already on the page; a result after the completion bound; an absence that a vanished scope also satisfies) and showed that several atlas predicates would certify the very failures the audit hunts. That is the counsel doing exactly what the protocol is for. Paid in the same lane before the story re-ships:
- Rig (W3): the replay identity must be produced by THIS operation; a result beyond the bound is incomplete; `text_absent`/`attr_equals` block on a missing scope; a closed, exported `UI_ACTIONS` vocabulary; executable `preconditions` checks; `boundary` performs its substitution or blocks; words-only → blocked, unreachable keeps its reason; the rig's hub claims database ownership and binds the product's meeting callbacks except the microphone recorder — each with a negative control that fails pre-fix.
- Atlas (W2): predicates assert the owner's promised result (J10 = the BRIEF section present with its words; J3 = the control exists and is enabled; speech readiness from the assignments response; J6 = the summary text and the host); every ui action in `UI_ACTIONS`; "previous case reached" becomes executable precondition steps; boundary steps name a real substitution; J4 import is multipart `file`; J9 restore expects the producer's attention state; J10 same-day shelves the untriaged items first; `record_only` added with its producer (`intel_admission.py:219,286`); the continuity horizon's producer is `REPLAY_HORIZON_DAYS = 14` (`needs_you_aggregate.py:163`); atlas case definition = the graph case definition, every case validates or is `unreachable` with a reason.
- Validator (W1): Phase 1 references and source paths must resolve (MISSED).
- The story's "every case validates" and the two ledger lines are corrected below; the graph model's proportion to §8 (finding 5, first sentence) is noted as ratified.

Astra's line "these defects do not prevent independent static source inspection" is taken as leave to brief the two STATIC passes once this round lands; the live passes wait for the re-check.
