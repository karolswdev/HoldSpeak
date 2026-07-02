# Evidence — HS-73-04 — Open in-world: the pull-out

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-73-desk-inhabited`)
- **Owner:** agent (Fable), owner-directed phase

## What changed

- **The bounce-out is dead.** Tapping ANY object opens its pull-out ON the
  stage (`Pullout.tsx`, a `motion` spring slide from the right, kind-tinted
  edge) — the DioPullout port. The world stays alive behind it (no
  vignette, floats keep floating); Escape and click-elsewhere close;
  **"Open full" is the ONE navigation on the desk** (meetings →
  `/history?meeting=id`, in the header only).
- **The meeting drawer**: fetches the detail (the payload IS the bare
  `MeetingState.to_dict`, `intel_status` nested — the documented gotcha) +
  `/artifacts`; sections Summary / Actions / Artifacts. An artifact row
  opens **in place** (a one-deep stack; ← returns to the meeting).
- **Per-kind bodies**: artifact (markdown + the lineage chips — the
  faithful `resolveRef`/`lineage` port in `lineage.ts`, tolerating the
  same wire drift, `via` capability split from `from` sources; resolved
  refs open in place); note/kb (content; **Edit swaps in the HS-73-03
  inline editor**); agent (role + prompt, the profile egress badge in the
  header); chain/workflow (steps); coder (state + question, display-only).
- **Run, minimally wired** (the HS-73-07 stage adds the theater + result
  landing): agents/chains/workflows get an Ask input + Run through the
  real `/run` routes, output rendered inline.
- **Move to…** in every filable kind's pull-out — the no-drag/keyboard
  filing path (the iPhone-filing lesson): a zone chip row writing the real
  `PUT /api/directories/{id}/members/{pid}` and forgetting the free
  position (the object lives on the shelf now).

## Verification artifacts (Playwright, real hub, scratch DB)

- Tap the meeting → the drawer with the REAL persisted intel (summary +
  actions with the wire's `task` key — the first fixture used `text` and
  the renderer was corrected to the actual shape) + the artifact row —
  **`location` asserted unchanged**; `04-meeting-drawer.png`.
- The artifact row opened in place (body + lineage), still zero
  navigation; ← returned to the meeting; `04-artifact-stacked.png`.
- Escape closed. Note pull-out → Edit swapped in the inline editor
  (pull-out gone, editor present).
- Move to… → the membership row landed in the DB
  (`primitive_id=n-ed → Q3`).
- Zero page errors. Build 18 pages; the manifest regenerated proactively
  this time (api-surface + pre-flight **7 passed** first try); full suite
  **3066 passed, 37 skipped, 0 failures**.

## Acceptance criteria — re-checked

- [x] Tap opens in-world for every kind; zero route changes except the
      explicit "Open full".
- [x] The meeting drawer groups summary/actions/artifacts; the one-deep
      stack with back.
- [x] Lineage ported faithfully (drift-tolerant, via/from split, resolved
      refs clickable).
- [x] Edit swaps the inline editor; Move-to files via the real PUT.
- [x] Drag still arranges without opening (the HS-73-03 discrimination,
      unchanged).

## Deviations from plan

- "Open full" ships for meetings only: agents/chains/workflows have no
  single canonical full page today (`/workbench` edits workflows but not
  agents/chains) — per the story's own "where one exists".
- The artifact lineage grouping renders as chips on the artifact rather
  than pre-grouping the meeting's artifact list (every artifact of the
  drawer IS the meeting's by `meeting_id`; the `via` capability shows on
  the artifact itself) — the same information, one level truer to the
  wire.

## Follow-ups

- HS-73-07 upgrades Run (generation theater + the result landing as an
  object).
