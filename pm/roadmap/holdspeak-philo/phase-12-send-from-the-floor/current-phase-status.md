# Phase 12 - Send from the Floor

**Last updated:** 2026-09-30 (DRAFTED by the Fedaykin docs lane for Muad'Dib; unchecked.)

**Status:** DRAFT — UNCHECKED — awaiting Astra's check, then the owner's ratification. Nothing is built. The stories stay `backlog` until he ratifies.

## Goal

The owner sends a document from the Desk's Floor the way he sends it from its window today. His saved destinations sit on the Floor as icons. He drags a decision, a meeting, a project, the brief or an artifact onto one; the document's window opens with that destination picked and the exact preview shown; he presses Send. On the phone, and anywhere he prefers a menu, right-click (or long-press) → `Send to ▸` does the same. Artifacts become sendable documents.

## Authority

The owner, 2026-09-30, verbatim: **"How do we now take advantage of all of this not only on the 'wall' (or whatever that black interface is), but also through the native desk os thing, right? the icons and so on?"** His picks: surface **"The web Desk's Floor"**; kinds **"What's sendable today"** (decisions, the meeting summary, digest and follow-up, project updates, plus a brief icon) and **"Artifacts"**. Notes were not picked.

Carried, unchanged: the Seven Tenets (`docs/internal/CONSTITUTION.md:18-60`); Article III, honest egress; Article XI, the kernel (XI.5: preview is exempt computation); UX-CANON §A (every verb the library Button, the canvas before build, no prose, no modals, no counter of zero, egress where egress happens, a verb that does nothing is withheld), §B, §E (`docs/internal/UX-CANON.md`); the Phase 10 send lifecycle (`../phase-10-the-channels/design/send-lifecycle.md`); the Phase 11 document sources and the SEND well species (`../phase-11-more-documents-on-the-channels/design/document-sources.md`); his Phase 10 and 11 rulings: **"You, every time"**, **"Saved destinations"**, **"I'm the only user"**, **"Stop being so paranoid"**, **"if it changes, we re-send"**; his ruling on thread authority (2026-09-29: a thread stops for his press on EGRESS, AUTHORITY and CONFIG).

## The roots

- **Tenet 6 (Workbench 2.0+ on steroids):** his question is the Workbench one: documents and destinations are icons, and a drop does the work. Destination icons in a column at the right edge are Workbench's disk icons.
- **Tenet 7 (a Senior Architect with reports):** the decision, the meeting's outcome, the project update and the brief are what he tells his team and his boss. Artifacts (requirements, diagrams, kept answers) are the same kind of work product.
- **Tenet 3 (help and accelerate):** no new window, no new preview, no new Send. The drop and the menu open the window that already has the SEND well, with the pick made for him.
- **Tenet 1 (no over-engineering for safety):** no new operation, authority class, table or migration; preview on drop, not prepare; the artifact body as stored, refused by name when it cannot go.
- **Tenet 2 (not even pre-alpha):** no compatibility layer; the drop matrix and the menu grow by one rule and one entry.
- **Tenet 5 (component framework):** the menu species already nests; the SEND well is one species; the artifact window's raw buttons become library Buttons.
- **Tenet 4 (ASD-STE100):** the tag says what release does: `Preview for <destination>`, never `Send`.

## Status of this charter

DRAFT, 2026-09-30, written by the Fedaykin docs lane (Opus 5.5) for Muad'Dib. Inputs: the faces half (`docs/internal/philo/phase-12/grounding/faces.md`, Muad'Dib's lane, draft PR #713) and the backend half (`docs/internal/philo/phase-12/grounding/backend.md`, Astra's lane, draft PR #714), with Muad'Dib's check of the backend half (`docs/internal/philo/phase-12/grounding/checks/backend-muaddib.md`, RATIFY, no conditions). The settled design is `design/floor-send.md`. Owed: Astra's check, then the owner's one answer (below).

**Phase 11 is still closing** (story 06 part 2, story 07). Phase 12 builds start after Phase 11's merges. The canvases (story 02) may start before that: they draw on a harness shim of the wire in `design/floor-send.md`.

## The grounding (main `22c0acc4`)

- **The faces** (faces.md): what sits on the Floor and which document windows carry the SEND well (§1a); the menus, which already nest (§1b); the drop matrix and the `ground-into` precedent (§1c); the private pick (§1d); icons and states (§1e); the Dock (§1f); the phone opens the list (§1g); findings F1–F11; boards F–J; eight questions.
- **The backend** (backend.md): artifacts are stored text (§1); the brief as a projection, not a primitive (§2); the destinations read and per-browser positions (§3); the drop calls `channel.preview` with no new operation (§4); findings 1–4; forks 1–2.
- **What the check found** (backend-muaddib.md): the two halves agree finding for finding; the two forks equal the faces defaults. The Shade test date fault (`tests/e2e/test_hs171_shade_glass.py:912`) is outside this phase (Muad'Dib's test fix).

## Scope

- **In:**
  1. **The artifact source and the Floor binding (story 01),** design §§2, 4. `artifact:<id>` as the ninth document source: one renderer, one registry row, the producer footer left out, `artifact_body_missing` and `artifact_not_text`, the channel limits reused. The descriptor text and the registry fence move to nine. The Floor binding: one pure module that maps a Floor object (or projection) to its `document_ref` or a named refusal, and the projection variant for non-primitive icons (destinations, the brief), as data only. No face.
  2. **The canvases F–J (story 02),** faces.md §3, at 1440 and 393, on the real product with a harness shim. The owner ratifies them before stories 03 and 04 commit a face change.
  3. **The menu path, the artifact window and the decision sprite (story 03),** design §§3, 7, 8. `Send to ▸` on every sendable object in the spatial Floor, the list and the menu bar; withheld where it cannot run; `Add destination` when there are none. The SEND well in the artifact window; its three raw buttons become library Buttons. The decision's own sprite family. The pre-pick setters (faces F9). This story is the phone's whole path, so it merges before the drag (faces F1).
  4. **The Floor layer and the drop (story 04),** design §§1, 5, 6. Destination icons at the right edge (active only, draggable, per-browser positions, pixel art per channel, `Open` → Settings → Destinations at that row, withheld at compact widths). The brief icon. The send rule in the drop matrix: the `Preview for <destination>` tag, the refusals on the tag, release opens the dragged document's window with the destination picked; no auto-prepare. The Room deep link to the Update posture if it does not exist.
  5. **The atlas cases (story 05)** for the menu path and the drop, at both widths where the face exists.
  6. **The closing use (story 06):** real sends from the Floor on his session; a cold agent prepares an artifact send; he presses Send.
- **Out (with their homes):**
  - **Notes as documents:** not picked. BACKLOG if he asks.
  - **Floor icons for the decision record and the meeting decision** (faces F7): they keep their Phase 11 wells. BACKLOG if he asks.
  - **`Send to …` in the ⌘K palette:** not grounded. BACKLOG.
  - **Destination icons on the phone** (design §1, narrow widths). The menu is the phone's path.
  - **A brief per generated brief, a full Brief primitive, Generate from the Floor** (design §5).
  - **Binary artifacts, attachments, conversion, truncation** (design §4).
  - **Prepare on drop; any send that is not his press** ("You, every time").
  - **Cross-device icon positions** (positions are per browser, backend §3).

## Admission by effect

No change. `artifact:<id>` is a new `document_ref` value on the existing operations. The Phase 10 and Phase 11 tables stand (`../phase-10-the-channels/current-phase-status.md`, "Admission by effect"; `../phase-11-more-documents-on-the-channels/current-phase-status.md`, same section). Drawing icons is a read; preview is XI.5-exempt; Send stays EGRESS with the owner's press (design §9).

## Exit criteria (evidence required)

The proof is new capability through the real hub on an isolated HOME, never a test double that lies about the field a check reads. "At both widths" means 1440x900 and 393x852. "Red on main" applies where a defect exists (the decision's note sprite; the artifact window's raw buttons; `artifact:<id>` refused `document_kind_unknown`).

- [ ] 1. **The artifact is a document.** `artifact:<id>` renders the stored body by id, through each real producer the Floor shows (meeting synthesis, run output, Ask Keep), with no model run. Red on main (`document_kind_unknown`), green here. Refusals by name: `document_not_found`, `artifact_body_missing`, `artifact_not_text` (checked on the raw stored value), `payload_too_large:<channel>`. The synthesis source footer is not in the payload, and the Phase 11 no-internal-id fence passes over nine kinds. The Phase 10 lifecycle fences run over one artifact. Over MCP alone, a fence maps "send this artifact to <destination>" and "prepare it" to a tool and an argument path; an external agent's `channel.send` is refused `owner_principal_required`.
- [ ] 2. **Each icon binds its exact document.** The binding module answers the design §2 table, one case per row, and the named refusals (no summary, no published update, a parked destination). A glass fence per kind presses Send after a drop or a menu pick and reads the hub's send row: its `document_ref` is the expected one (a project sends its latest published update; a meeting sends Summary unless the picker changed it; the brief sends the id the view shows).
- [ ] 3. **`Send to ▸` works on every face that reads the object menu.** On the spatial Floor, the list and the menu bar Object menu, for each sendable kind, at both widths (the list at 393). Withheld on a kind that cannot send and on an object that cannot send now. With no destinations, one `Add destination` row opens Settings at the form. A pick opens the document's window with the destination picked and the preview loaded; zero `channel_sends` rows and zero kernel operations exist until Send.
- [ ] 4. **Destinations on the Floor.** One icon per active destination at the right edge; a parked one gone after the next read; a moved icon keeps its place after a reload; `Open` opens Settings → Destinations at that row; none drawn at compact width; nothing drawn with no destinations. Each channel's sprite and the decision's new sprite ship rest, `_sel` and `_stale`; the decision no longer wears the note sprite (red on main).
- [ ] 5. **The drop opens the preview; he sends.** At 1440, for each sendable kind: the tag reads `Preview for <destination>` and never contains `Send`; release opens the dragged document's window at the drop point with the destination picked and the preview loaded; the icon goes back to its place; no send row and no kernel operation until Send. Each refusal shows on the tag and release does nothing. After his press, the face's outcome equals the hub's send row and receipt in the same fence.
- [ ] 6. **The face, as ratified.** Canvases F–J ratified by the owner (his word recorded) before the first face commit. Each ratified board built and fenced through the real hub at both widths. The artifact window's three raw `<button>`s are library Buttons (red on main). Every verb the library Button; no modal; the egress chip in the well, not on the tag; no prose on the tag; no counter of zero. The web baseline has zero branch-new failures.
- [ ] 7. **The atlas** has face cases for `Send to ▸` per sendable kind at both widths, the drop per kind at 1440, the tag refusals, and the artifact send, with `.op` siblings where the outcome is durable. The Phase 7–11 atlas cases still pass.
- [ ] 8. **The closing use.** On his own session, to targets he names (the Phase 10 Q6 ruling carries): one real send from the Floor of each picked kind (decision, meeting summary, project update, brief, artifact) on the channels he has, by drag at 1440 and by `Send to ▸` at 393, each proof read back from the far side, or a named limit with its reason. A cold Codex session prepares one artifact send from the MCP catalogue alone; he presses Send on the face. Secrets and addresses redacted at capture. Rehearsed, owner-reviewed shots; never recorded as a sitting.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| PHILO-12-01 | The artifact source and the Floor binding | backlog | [story-01-the-artifact-source-and-the-floor-binding](./story-01-the-artifact-source-and-the-floor-binding.md) | — |
| PHILO-12-02 | The canvases F–J | backlog | [story-02-the-canvases](./story-02-the-canvases.md) | — |
| PHILO-12-03 | Send to, the artifact window and the decision sprite | backlog | [story-03-send-to-the-artifact-window-and-the-decision-sprite](./story-03-send-to-the-artifact-window-and-the-decision-sprite.md) | — |
| PHILO-12-04 | Destinations on the Floor and the drop | backlog | [story-04-destinations-on-the-floor-and-the-drop](./story-04-destinations-on-the-floor-and-the-drop.md) | — |
| PHILO-12-05 | The atlas cases | backlog | [story-05-the-atlas-cases](./story-05-the-atlas-cases.md) | — |
| PHILO-12-06 | The closing use | backlog | [story-06-the-closing-use](./story-06-the-closing-use.md) | — |

**Two changes from the brief's five-story proposal, with reasons:**

1. **The face build is two stories (03 and 04), not one.** Faces F1: the phone has no drag; `Send to ▸` is its whole path and must ship with or before the drag. A separate story lets the menu path merge first. It also keeps each PR one review: 03 touches the menu, the artifact window and one sprite; 04 touches the world, the scene, the engine and the drop matrix.
2. **Story 01 owns the Floor binding as data only.** The brief put "the Floor projection seam" in Astra's backend story. Its files are web: `world.ts`, `sceneModel.ts` and `engine.ts` are the files story 04 must change to draw and drop the icons. Two lanes in one file breaks TWO-BRAINS §4 (disjoint files). So story 01 delivers the binding and the projection as a **new, pure module** with its unit fences (Astra's strength: an exact algorithmic map with named refusals), and story 04 wires it into the world and the engine.

## Lanes (proposed)

| Lane | Stories | Owner | Checker | Worktree | Branch |
|---|---|---|---|---|---|
| The artifact source and the binding | 01 | Astra (Luna, xhigh) | Muad'Dib | ../wt-philo-12-01 | feat/philo-12-01 |
| The canvases | 02 | Muad'Dib (Fedaykin, Opus 5.5) | Astra | ../wt-philo-12-02 | feat/philo-12-02-canvases |
| The faces | 03 → 04 | Muad'Dib (Fedaykin, Opus 5.5) | Astra | ../wt-philo-12-03, ../wt-philo-12-04 | feat/philo-12-03-send-to, feat/philo-12-04-floor-drop |
| The atlas | 05 | Astra (Luna, xhigh) | Muad'Dib | ../wt-philo-12-05 | feat/philo-12-05-atlas |
| The closing use | 06 | Muad'Dib | Astra | ../wt-philo-12-06 | feat/philo-12-06-closing-use |

- **Why this split** (TWO-BRAINS §4): Astra takes the backend, the exact binding and the verification harness (01, 05); Muad'Dib takes the faces and the owner-facing close (02, 03, 04, 06).
- **What runs in parallel.** 02 may start now, before Phase 11 closes (a harness shim of the design's wire). 01 starts after Phase 11's merges; it touches `document_sources.py`, `channel_operations.py` and one new web module. 03 builds after 02 is ratified and 01 has merged. 04 follows 03 (the shared pre-pick setters land in 03). 05 follows 04. 06 is last.
- A lane runs its scoped fences and rig cases only. The orchestrator runs the full suite before the done call. CI does not gate a merge (the owner, 2026-09-28).

## Where we are

2026-09-30: DRAFTED (this branch, `docs/philo-12-charter`, carrying the two grounding halves, draft PRs #713 and #714, and Muad'Dib's backend check). Next: Astra's check of this charter; then the owner's one answer.

**Estimate (PROVISIONAL; calibrated on Phases 10 and 11):** effort **7.5–10 engineering days** — 01 1–1.5 (one renderer, two refusals, the footer rule, the binding module and its fences); 02 about 1 (five canvases, about 20 boards at two widths); 03 1.5–2 (the menu entry on three faces, the artifact well and Buttons, one sprite family, the setters); 04 2–3 (the layer, six channel sprites, the drop rule and the tag, five open paths, the brief icon, the Room deep link); 05 about 1; 06 about 1, plus the real-send legs. Calibration: Phase 11's 9–13 engineering days built in about two elapsed days, plus the check rounds. **Elapsed forecast: about 2 days after Phase 11 closes, gated by the canvas ratification and the check rounds.**

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The drop sends, or a tag says Send | medium | release calls preview only; a tag-text fence (design §6) | a `channel_sends` row or a kernel operation before his press; `Send` in a tag |
| The wrong document goes (project vs update, meeting form, brief id) | medium | one binding module, one case per row (design §2) | a send row whose `document_ref` differs from the design table |
| Destinations become a primitive, and the registry grows with it | medium | a world layer like zones; a projection variant (design §§1, 5) | a 21st `PrimitiveKind`, a pullout or descriptor row for a destination |
| The phone gets nothing | low | `Send to ▸` merges first (story 03) | story 04 merges before 03 |
| An internal id leaves the machine in an artifact | medium | the footer rule and the Phase 11 fence over nine kinds | `art-`, a window id or a run id in a payload |
| The menu fills with ghosts | low | withhold where it cannot run (design §3) | a ghosted `Send to ▸` row |
| A new artifact review gate or revision store grows | low | his preview and Send are the approval; R9 | a status gate or a version column for artifacts |

## The one question

**"Ratify Phase 12 with all the defaults below?"** **Recommended: yes.** Each default comes from the grounding; both halves and Muad'Dib's check agree on them. He may change any row by number; the rest stand.

| # | Choice | Default | From |
|---|---|---|---|
| 1 | Where destinations sit | a column at the right edge, like Workbench's disk icons; he can drag them; parked ones hidden | faces Q1 |
| 2 | Destination icons on the phone | none; the phone uses `Send to ▸` in the list | faces Q2 |
| 3 | `Send to ▸` where it cannot send | withheld (not a ghost row) | faces Q3 |
| 4 | The drop tag | `Preview for <destination>`; never `Send` | faces Q4 |
| 5 | A project dropped | its latest published update; none → refused on the tag | faces Q5 |
| 6 | The brief | one icon for the latest stored brief, beside the destinations; open → Intelligence → BRIEF; no brief → no icon; no Dock change | faces Q6, backend fork 1 |
| 7 | The icon art | one pixel-art silhouette per channel in the house palette; no brand logos; the destination's name is the label | faces Q7 |
| 8 | Opening a destination icon | Settings → Destinations at that row | faces Q8 |
| 9 | A meeting dropped | Summary first, the Summary / Digest / Follow-up picker in the preview | backend fork 2 |
| 10 | What a drop does | opens the preview only; no prepare; he presses Send | backend finding 4 |
| 11 | An artifact | its stored text; the internal source footer left out; refused by name when missing, not text or too large | backend §1 |

No other choice is open. The tag and refusal words and the icon art are drawn on canvases F–J; he ratifies those boards in story 02.

## Decisions made (this phase)

- 2026-09-30 — the owner picked the surface and the kinds (Authority, verbatim).
- 2026-09-30 — Muad'Dib checked the backend grounding: RATIFY, no conditions (`docs/internal/philo/phase-12/grounding/checks/backend-muaddib.md`).
- 2026-09-30 — DRAFTED: six stories; destinations a world layer; the drop opens the preview; `Send to ▸` first; the artifact as the ninth source; the eleven defaults as one question — Fedaykin docs lane for Muad'Dib.

## Decisions deferred

- The tag and refusal words, the icon art, the column's spacing: canvases F–J, ratified by the owner.
- The Room deep link's shape, if it must be built: story 04's first commit, checked by Astra.
