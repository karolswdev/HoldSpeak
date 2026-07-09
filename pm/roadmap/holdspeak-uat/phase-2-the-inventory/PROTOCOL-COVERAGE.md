# UAT Protocol — Coverage & Authoring Round (2026-07-09)

> Authored by a 6-agent flotilla (one per domain), each self-validated against
> the contract. 53 scenarios across 7 packs load CLEAN. This doc records what
> the protocol now covers and the **harness backlog** (§3) — the engine verbs
> and probes needed to unlock the live-agent / on-device tier.

# UAT Protocol — Authoring Round

## 1. Packs authored

| Pack | Scenarios authored | Control-vs-treatment beats | Validated |
|---|---|---|---|
| `pack-a-aftercare` | 7 (`01-import-to-artifacts` → `07-followup-draft-export`) | 3 | clean |
| `pack-b-steering` | 4 (`01-relay-owns-grant` → `04-ground-a-steer`) | 1 | clean |
| `pack-c-dictation-grounding` | 8 (`01-grounded-rewrite` → `08-groundless-control`) | 5 | clean |
| `pack-d-honest-failure` | 8 (revised `04`/`05` + new `07`–`12`) | 2 | clean |
| `pack-desk` | 8 (`01-seeded-desk-reads-back` → `08-doctor-honest-close`) | 1 | clean |
| `pack-e-mesh-edge` | 7 (`01-node-serves-and-reads-live` → `07-offline-door-refuses-fast`) | 2 | clean |
| **Total** | **42 scenarios** | **14 beats** | **6/6 clean** |

## 2. Must-test ledger coverage

Deduplicated across all six `must_covered` lists: **46 unique ledger keys** now have an authored scenario (two keys — `trust.egress.cloud-meeting-intel` and `desk.sync.profile-shape-across-surfaces` — are legitimately shared across packs and counted once). Against the ~115-key must-test ledger, that is **≈40% (46/115) of must-tests covered** by an authored, validated scenario.

Domains landed: dictation/learning-loop (10 keys), meetings/aftercare (10), trust/egress/release (10 incl. the shared cloud-intel key), mesh/models/agents (8), desk (5 incl. shared sync key), and steering/factory (5).

## 3. Harness backlog (consolidated `blocked_on_engine`, ordered by capabilities unlocked)

The blockers cluster into shared missing primitives. Ordered by how many distinct capabilities/scenarios each unlocks:

1. **`spawn_pane` + `arm_grant` recipe verbs + steering probes** (`peek_shows_prompt`/`session_live`, `grant_live`, `key_landed`/`key_rejected`, `pane_listed`, `audit_row_written`) — unlocks the entire live-steering spine: `steering.peek`, `steering.arm_steer`, `steering.keys` (incl. the `trust.steering.named-key-allowlist` negative), `steering.attach_any_pane`, `steering.classify`/`audit`, and the `agents.answer_coder.ai_drafted` OFF/ON draft. This one primitive family is the single largest unlock (~6 capabilities across all four `pack-b-steering` scenarios).

2. **Device pre-flight recipe block** (`pair_device` + `model-installed-on-device` + `hub-reachable-on-lan`; probe `device_paired`) — unlocks every currently-honest-`n/a` iPhone/iPad leg: all of `mobile.steering.*` (pack-b), the from-iPad relay + phone-served-edge legs in `pack-e-mesh-edge/02`,`/03`,`/06`, and turns the mobile columns of the mesh/steering packs from unknown into walkable. Unblocks ~4 capabilities across two packs.

3. **`dispatch_run` / `ask_on_profile` verb + returned-card badge probe** (worker-log-claims-it / hub-shows-no-model-load) — unlocks `pack-e-mesh-edge/02`,`03`,`06` (drive a real desk-ask onto the mesh worker, read the ⇄ mesh badge + provenance). Core to Pack E's headline arc.

4. **Cloud-egress card recipe + per-card egress probe** (`egress-cloud-card` proposal with a real named cloud target; a probe reading its badge/target) — unlocks `pack-d-honest-failure/07` (egress badge cloud-flip) **and** `pack-d/11` / `pack-a-aftercare/04` (`trust.egress.cloud-meeting-intel` OFF/ON). Two packs.

5. **Dictation dry-run pipeline probes** — `dictation_dry_run` action + `typed_output` probe (spoken-symbol matcher, `pack-c/02`); `preview_field_byte_locked`/`typed_matches_preview_verbatim` (byte-lock, `pack-c/05`); `learned_correction_taught` + `learned_from_count` (honest-N chip, `pack-c/06`). Closes three human-eyeball beats in Pack C.

6. **Single-scenario probes** (one capability each): `nonloopback_request_rejected` (pack-d/05 loopback 401); `key_never_reappears` (pack-d/08); `no_network_beacon` (pack-d/09 idle telemetry); `newer_db_refused_untouched` + crafted-schema seeds (pack-d/10); `mesh_run_refuses_fast` (pack-e/07); `hub_observer_has_remote_events` (pack-e/05); `key_absent_in_sync` (pack-e/04); `meeting_artifact_typed`/`artifact_source_resolves` and a ≥2-chain lineage probe (pack-a/01,05); a delta-context toggle knob (pack-a/02); a non-English-speaker recipe world (pack-c/07).

`pack-desk` is the only pack with an **empty** `blocked_on_engine` list — it is fully machine-verifiable today.

## 4. How much of the supportable surface is authored

Honestly: the **breadth** is nearly complete but the **depth** is gated. Every domain the ecosystem exposes now has authored, CLEAN-validated scenarios — 42 across six packs — and the arcs that today's recipes/probes can actually stage are done end-to-end and machine-checkable. `pack-desk` (all 8 scenarios) and the bulk of `pack-a-aftercare`, `pack-c-dictation-grounding`, and `pack-d-honest-failure` are real do-then-assert protocols, not happy-path: they open on staging-verify beats, carry 14 ordered control-vs-treatment pairs (grounded-rewrite naming BLUEBIRD, mesh run surfacing `PYLON-CANARY-7`, mixed-topic routing naming QL-310/QL-301, the egress cloud-flip), and close on honest-failure legs.

Where it is still blocked is the **live-agent and on-device tier**. `pack-b-steering` is the sharpest example: only 4 of its ~10 capabilities are stageable today, and the crown MUSTs — `steering.arm_steer`, `steering.keys`, `agents.answer_coder.ai_drafted` — are all parked behind the single missing `spawn_pane`/`arm_grant` primitive; the pack currently proves the offline "refuse fast, by name" case (`01`/`02` riding mesh-node-just-died) but not a live steer. Similarly, Pack E authors the full mesh arc but leaves the actual dispatch-onto-worker and iPad-relay legs as `n/a`/human-eyeball pending `dispatch_run` and the device pre-flight block. So: roughly **40% of the must-ledger is covered by authored scenarios**, of which the desk/dictation/trust/aftercare majority is fully harness-verifiable now, while the steering, mesh-dispatch, and every iPhone/iPad column remain **authored-but-human-walked** until the ~15 deduplicated harness verbs and probes above — led by `spawn_pane`+`arm_grant` and the device pre-flight recipe — are built. The authoring is not the bottleneck anymore; the harness engine is.