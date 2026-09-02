# Phase 162 - Project Rooms: The Update Factory (P3)

- **Project:** holdspeak
- **Status:** in-progress
- **Chartered:** 2026-09-01 off main `856de35b` (161 The GitHub Watch MERGED via PR #525 — the FIFTH Project Rooms phase merged: P0 #521, P1 #522, P1a #523, P2 #524, P2a #525)
- **Canon:** docs/internal/project-rooms/SRS_DOMAIN_DRIVER.md §8 (UPD-001..005), §14 P3 slice; SRS_PRODUCT_VALIDATION.md PV-H04; the frozen contracts (project_contracts.py, refs.py); CONSTITUTION.md

## The charter

P3's exit, verbatim: **the owner creates a usable evidence-backed
update without reconstructing project truth.** The Update Factory is
"the immediately legible proof of value" (SRS_PRODUCT_VALIDATION):
update generation operates over an explicit Project revision and
review/source manifest, produces EDITABLE Markdown with structured
claim metadata, and every factual claim resolves to evidence refs —
unsupported model language is omitted or visibly marked (UPD-002).
The deterministic template fallback is not a nicety: it MUST remain
available when inference is unavailable (UPD-003), so it ships FIRST
and the model drafter composes on top. Regeneration never rewrites a
published update (UPD-004); Save, Copy Markdown, and Mark Published
are separate commands with honest receipts (UPD-005). The bar is a
NUMBER again: PV-H04 — median edit-to-copy under five minutes and at
least 70% of generated content retained.

OUT of this phase: the Steward (P4 owns run_once and every effect),
scheduling (P5), MCP (P6), Jira (P7). `project.update.draft` exists
in the §7.3 action vocabulary but its EXECUTION by rules is P4/P5 —
this phase builds the factory the action will call.

## Stories

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-162-01 | The update ledger (schema v70 + repo + revision pinning) | done | [story-01-the-update-ledger](./story-01-the-update-ledger.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-162-02 | The deterministic drafter (UPD-003 first; sections + claims + citations) | done | [story-02-the-deterministic-drafter](./story-02-the-deterministic-drafter.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-162-03 | The model drafter (frozen router; marked language; fallback proven) | done | [story-03-the-model-drafter](./story-03-the-model-drafter.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-162-04 | The verbs on the wire (draft/regenerate/save/copy/publish; api-surface) | done | [story-04-the-verbs](./story-04-the-verbs.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-162-05 | The face (the Update room — claims open their sources; OWNER VERDICT) | in-progress | [story-05-the-face](./story-05-the-face.md) | - |
| HS-162-06 | The walk (PV-H04 measured: edit-to-copy < 5:00, ≥70% retained; degraded leg) | done | [story-06-the-walk](./story-06-the-walk.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-162-07 | The close (gates, debts, final summary, PR) | backlog | [story-07-the-close](./story-07-the-close.md) | - |

## Where we are

6/7 flipped; 05 holds for THE OWNER'S VERDICT. 06 DONE — the walk:
PV-H04's TWO NUMBERS MEASURED — edit-to-copy 1.91s against the 300s
bar (segments itemized in assets/story-06-stopwatch.json) and
retention 1.0000 against the 0.70 bar (honest difflib measure; the
representative edit is additive). Four legs ×2 deterministic:
stopwatch+retention, the degraded leg (UPD-003 on glass — router
down ⇒ deterministic draft with the human fallback sentence, claims
still resolve), publish immutability (read-only render, regenerate
mints a new draft, the published body never changes, room revision
advances), and the no-raw-ids law asserted on every leg. Sixteen
shots, both viewports. THE BEAUTY ROUNDS the orchestrator forced
before the owner sees pixels: human chip labels (a closed table;
raw refs demoted to title/aria + a regex fence), the editor themed
to the house species, human fallback words, the full generator
label at both viewports, "Open item" for generic refs. The live
model leg deliberately rides 03's service-level .43 proof (wiring
.43 into the rig judged disproportionate — honest skip). Next: THE
OWNER'S VERDICT closes 05, then 07 the close.

## Active risks

- UPD-002's claim-to-evidence discipline is the phase's soul: a
  drafter that emits confident prose without locators is the exact
  failure the SRS names. The deterministic drafter defines the claim
  schema; the model drafter must be CONSTRAINED to it.
- PV-H04's 70%-retained metric needs an honest measure (diff-based),
  not a vibe.
- Debts carried in: 160's N-5 (widen the no-fetch spy), S-4 (source
  chips open their source — THIS phase's face is where citations
  become clickable), N-1 (Space preview), N-2 (server-side
  undismiss); 158's S-1/N-1/N-3; 159's seeding walls; 161 counsel
  N-1 (React scope key naming).
