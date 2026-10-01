# PHILO-13-12 - C2 The gadgets that are missing

- **Project:** holdspeak-philo
- **Phase:** 13
- **Status:** backlog
- **Depends on:** PHILO-13-11 (C1 canvas ratified; the gadget set's place in the chrome)
- **Unblocks:** none
- **Owner:** Muad'Dib (Fedaykin, Opus 5.5); Astra checks
- **Lane:** Faces + frame (`../wt-philo-13-muaddib`, `feat/philo-13-muaddib`)
- **Proposal:** C2 (PROPOSAL §3, Wave C)
- **Closure finding:** `grounding/faces-jobs.md:146-148`; `grounding/structure.md:19`, `:131-132`
- **Canvas:** C1's (the gadget set); no separate canvas

`grounding/` = `docs/internal/philo/phase-13/grounding/`.

## Goal

The Workbench gadgets that are missing work: depth, zoom, right button = the active window's menu bar, Amiga-key shortcuts on every menu verb.

## Problem

Focus raises; there is no send-to-back (`web/src/desk/store/compositorSlice.ts:300`; `grounding/structure.md:131`). Maximize fills the work band with one retained rect (`compositorSlice.ts:331`; `web/src/desk/components/DeskWindow.tsx:737`); Intuition's zoom alternates two remembered size-and-position sets (`grounding/structure.md:19`, `:132`). The title-bar right-click builds Minimize / Maximize / Close only (`web/src/desk/components/window/windowMenuAdapter.tsx:16-56`; `DeskWindow.tsx:815-821`). Keyboard programs exist for ⌘1–⌘4 (`web/src/desk/applications.ts:84`, `:114`, `:135`, `:155`); menu verbs show no shortcuts. The Object menu stays all ghost after a list row is selected (`grounding/faces-surfaces.md:69`; `grounding/shots/surfaces/111-object-menu-decision-pop-1440.png`).

## Scope

- **In:**
  - **Depth:** send the front window to the back (a gadget and a menu verb).
  - **Zoom:** alternate two remembered rects per window, on top of maximize; both rects persist (B2's document).
  - **Right button = the active window's menu bar:** the Desk menus of the front window at the pointer.
  - **Amiga-key shortcuts** on every menu verb, shown in the menus (`verbRegistry.ts`, `windowMenuAdapter.tsx`).
  - Each gadget by mouse, by key and by touch.
- **Out:** screen depth (out of scope; `grounding/structure.md:19`); `Send to ▸` in the menus (C5); the gadget art (C1).

## Acceptance criteria

- [ ] Depth sends the front window behind its peers; the next window comes to the front. Mouse, key and touch at 393.
- [ ] Zoom toggles between two remembered rects; each survives a reload. Red on main (maximize only).
- [ ] Right button anywhere in a window opens that window's menu bar; at 393 a long-press does.
- [ ] Every menu verb shows its shortcut; each shortcut runs its verb (a fence over the verb registry: no verb without a shortcut is shown with one, no shown shortcut is dead).
- [ ] Every verb the library Button; shots at 1440 and 393.
- [ ] **Gate (review evidence):** this story's PR merge record cites the owner's ratification record of the C1 canvas it is built on (path + his quote); without it the checker refuses the merge.

## Test plan

- **Atlas file:** `docs/internal/philo/graph/atlas-phase13-muaddib.json` (this lane's only atlas file; `--atlas` per run, `scripts/graph_walk.py:6507`); its count fence in `tests/unit/test_philo13_muaddib_atlas.py`.
- **Focused:** web unit on the compositor (depth order; zoom's two rects); the shortcut fence over `verbRegistry.ts`; `uv run python scripts/check_web_baseline.py --run`.
- **Glass:** Playwright through the real hub: each gadget by mouse, key and touch.
- **Atlas:** one case per gadget, at 1440 and 393, one case per `scripts/graph_walk.py run` invocation.
- **Shots:** each gadget before and after, both widths.

## Worker-brief scars

- **Doubles that lie:** jsdom lies about focus (Phase 148); key and touch proof is on glass.
- **A verb that does nothing is a lie (A.11):** a gadget that cannot act on this window is withheld, not ghosted with no reason.

## Effort (not a promise)

Grounding size: not sized as one move. PROVISIONAL.

## Notes

- 2026-10-01 — r2: Astra charter check r1 (DO-NOT-RATIFY) paid; see the status file, "Round two".
- 2026-10-01 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
