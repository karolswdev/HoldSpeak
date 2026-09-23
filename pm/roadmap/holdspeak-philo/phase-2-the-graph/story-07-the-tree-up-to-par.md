# PHILO-2-07 - The tree up to par

- **Project:** holdspeak-philo
- **Phase:** 2
- **Status:** done
- **Depends on:** PHILO-2-06
- **Unblocks:** see the phase status doc
- **Owner:** Muad'Dib (Opus workers); Astra checks

## Problem

The sweep informs us or it was theatre. The Philo inventories gain the two missing layers as generated files; every load-bearing sentence about an edge or an action becomes a doc-claims row with a predicate over the graph; the forty walk scripts are parked behind the one rig; a walk skill and refreshed briefs carry this week's scars.

## Scope

- **In:** what the acceptance criteria name, and only that; the one brief (`docs/internal/philo/briefs/graph-audit-brief.md`) is the contract.
- **Out:** fixing the product (Phase 3), correcting docs before the council (story 07), anything on the owner's desk.

## Acceptance criteria

- [x] `scripts/philo_graph_reference.py` (+ `--check`) generates `docs/generated/graph.json` as the join of both static graphs, both sealed live observation sets, the existing Phase 1 inventories and the council's explicit resolutions, never silently unioning contradictory claims; `--check` proves generated consistency, and a SEPARATE current-source census comparison detects new, removed or changed entry points (brief §8); saved observations keep their original revision. CI drift-checks it like the other Philo inventories.
- [x] `tests/unit/doc_claims/registry.py` gains `holds` rows for the claims the council marked drift AFTER the prose is corrected to the current truth in the same commit; missing product behaviour stays in the findings and its Phase 3 story, never in the prose; the known-false ceiling is ZERO and this story does not raise it.
- [x] A phase walk script is moved to `scripts/_parked/` (never deleted) ONLY after its callers and assertions are mapped to verified replacements in `scripts/graph_walk.py` or to an explicit council disposition, recorded per script; the rest stay.
- [x] The portable Phase 1 skills and maintenance index (`agent/skills/`, `docs/internal/philo/data/README.md`) are EXTENDED with the walk procedure (mint a case, run the rig, read an observation, run-specific output directories, never a blanket restore loop); `.claude/skills/graph-walk/SKILL.md` and the AGENTS.md mirror LINK to that shared procedure; `.claude/agents/opus-worker.md` and `scripts/astra` preambles carry the scars: fences naming old words, lying doubles, receipts under one branch, the restore loop.
- [x] `docs/internal/philo/README.md`, the Philo project README and the HoldSpeak README index point at the graph.

## Test plan

- **Unit:** `test_phase200_doc_claims` green with the new rows; `philo_graph_reference.py --check` green; the skill validates like the Phase 1 skills.
- **Integration:** the Philo drift job in CI.
- **Manual / device:** none.

## Notes / open questions

**Astra's counsel on built (RATIFY-WITH-CONDITIONS, `checks/story-07-built-astra.md`): three code conditions paid in the counsel round (the census reads current source routes; subtype disagreements disclosed via an explicit normalization table; the council citation names the revision holding the corrected ruling); ledger corrections: paired execution covers 59 of 73 cases (12 Astra preflight blocks + 2 unreachable), the timer exposure disagreement is REVERSED (astra=conditional / muaddib=active) and does not follow the other 52, the three `holds` rows are documentation-drift checks not outcome proof, the walk ledger holds 34 files plus `desk_walk/` (five walkers); the four miscited handler names are Astra's static-pass errors (sealed, not rewritten).**

**Counsel round PAID:** the census builds the app from source (`gen_api_surface.build_reference_app`) and compares method+path+handler against the graph, reports `stale:` when committed OpenAPI differs from source (fails), and tells `miscited` from `changed` by git history; a regression test changes routes in memory with OpenAPI untouched and sees new/removed/changed. Subtypes: 144 disagreements = 130 normalized by an explicit table (refinement, bucket, vocabulary — RULED accepted by the lane owner; both positions stay in every label) + 14 CONFLICTS carried as notes, never decided (8 route edges `ui` vs `http` incl. `edge.route.model_profile_delete`; the heartbeat timer `ui` vs `timer`; the restart cli; two face edges; two interfaces). `COUNCIL_REVISION` = 54cf71a7 with a test that the cited file hashes equal the input read. The census now reports 5 miscitations (a fifth: `edge.route.meeting_stop` cites only `api_meeting_stop` while `/api/stop` had `api_stop` at c42963bc) — sealed-pass citation errors, reported, not rewritten. Route-change sequence in the script docstring and the walk procedure (step 7).

**Built 2026-09-23 (Opus 5.5 worker).** `scripts/philo_graph_reference.py` (+`--check`, `--census`; stdlib only; registered in `.github/workflows/test.yml`) joins both static graphs, both live observation sets, the Phase 1 inventories and `council-resolutions.json` into `docs/generated/graph.json` (6,472 nodes, 808 links, 73 cases, 216 observations, 112 claim reviews, 47 findings, 47 resolutions; validator OK). Contradictions in TYPED fields error (kind, verified-vs-contradicted, one id two contents, a finding without a resolution, a case not in the atlas); the 53 EXPOSURE disagreements between the two static passes (Muad'Dib "conditional" vs Astra "active/internal" on 52 desk verbs and one timer) are recorded as both positions in the node label — RULED by the lane owner: exposure is not a typed schema field and the two passes use "conditional" in different senses; a council reading, not an error. Census: 0 new/removed/changed against source, 4 miscited handler names in static-astra (line numbers right, names wrong; reported, not failed). Three doc-drift lines corrected with `holds` rows (known-false ceiling stays 0). One stale council resolution row (§4.6) corrected to tooling-debt and the graph regenerated. WALK SCRIPTS: NONE PARKED — the council gave no disposition and no script has a verified replacement (the atlas covers J1–J11 only); all 36 kept, each with its reason and law warnings in `scripts/_parked/README.md` (four read the owner's real archive; four drive :8765; one deletes his DB). Skills: the walk procedure lives ONCE in `agent/skills/holdspeak-capability-verifier/SKILL.md`; the doc-maintainer skill, `docs/internal/philo/data/README.md`, `AGENTS.md` link to it; the five scars are in ORCHESTRATION §3 and in `scripts/astra`'s preamble. `.claude/` is gitignored, so `.claude/skills/graph-walk/SKILL.md` and the opus-worker edits exist only on this machine (re-apply on a fresh clone, as the agent file already says). Also regenerated on this branch: `api-reference.json` and `boundary-candidates.json`, which were drifting on main. UNKNOWN: README's "222 tools" vs 225 names in the catalogue (not touched); the sealed `live-muaddib.json` records the OLD lane-brief sha256 (historical by design).

The roots lens applies to every criterion: the owner works ninety percent of his day on the desk; the interfaces guide him; Workbench 2.0+ on steroids (Tenet 6). A finding that does not cost him on a Tuesday ranks last.
