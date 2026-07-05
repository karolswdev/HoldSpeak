# HSM-16-09 — The Ask AI atom: lasso → ask → speak → print → keep or bin

- **Project:** holdspeak-mobile
- **Phase:** 16
- **Status:** done (2026-07-04 — sim-proven end to end; the on-device real-metal walk is a 16-06
  beat by this story's own acceptance. **TRUTH-UP of the resume survey:** "zero Ask-AI code exists"
  was WRONG — the atom's skeleton (`askBundle` → `DioRouteSheet` → theater → `DioPrintedCard`,
  keep/bin, mic, profile picker) had already shipped under other names. What this story actually
  built was the part the skeleton faked: (1) **the full Ask lineage** — `RunProvenance` grew
  `contextIds`/`contextTitles`/`prompt` (decode-tolerant; recipe/chain wire shape byte-stable,
  test-locked) so a kept Ask persists as an `Artifact` naming every card it read + the exact
  instruction, one canonical `sources` row per context; (2) **two egress-honesty bugs fixed** —
  the printed card and the routing theater read the app-wide `isLocal` instead of the run's
  resolved profile, so a per-run cloud override printed a card claiming local (both now resolve
  the per-run profile; a cloud run names its real host, the 21-01 grammar); (3) **off the scrim**
  — the Ask composer joins the atelier posture and the result card PRINTS from the AI core it ran
  through onto a soft backdrop ([[feedback_no_modals_in_world]]); (4) the ask lineage glyph. Suite
  467/9/0; sim build green; three committed screenshots.)
- **Depends on:** the lasso/selection (HSM-14-19), **runtime profiles** (Phase 24 —
  `resolveProfile`/`makeProvider(profile:)`, not the old raw `InferenceConfigStore` mode), the
  speak-to-fill mic (`VoiceCaptureState`, [[feedback_voice_mic_every_input]]), the **`EgressScope`
  grammar** (21-01 — the chip states where the ask RUNS), the materialize treatment (14-03).
  [[story-20-the-desk-object-model]] for the kind + grammar.

## Build plan (2026-07-04 resume — every seam already shipped)

The atom is a composition, not a construction. Map each beat to its proven seam:

1. **Context assembly** — the lasso'd primitives' `routableText`, cited per-source, is exactly the
   17-04 dropped-context grounding block (`CoderAnswer`'s `[CONTEXT]` assembly). Reuse the grammar,
   don't reinvent it.
2. **The one model call** — the 17-05 pattern verbatim: one `ILLMProvider.complete` on a FRESH
   resolved provider (the Mode-A KV rule), profile-resolved per Phase 24 so "where this ask runs" is
   the user's named profile, key custody intact.
3. **The print** — the 14-03 materialize treatment; the card slides from the shelf, in-world, no
   modal ([[feedback_no_modals_in_world]]), wearing its `EgressScope` chip.
4. **Keep** — persist as a real `Artifact` (`SyncKind.artifact`) with provenance = the context ids +
   the prompt; it is instantly file-able (zones/KBs) and syncs to the hub + web with no new wire work
   (the 23-04 matrix already carries artifacts). **Bin** — nothing is saved, honestly.
5. **Voice** — the speak-to-fill mic on the prompt field; label microcopy only
   ([[feedback_no_prose_in_ui]]).

Pure flow logic lands host-tested in RuntimeCore (the house pattern); the device walk proves the
felt moment ([[feedback_verify_on_device_not_seeded]]).
- **Unblocks:** HSM-16-08 (a saved/chained sequence of Asks *is* a workflow — this is its atom).
- **Owner:** unassigned

## Problem

The full Workbench graph is powerful but heavy: you author a program before you get value. The most
valuable thing on the desk is far simpler and needs no authoring — **point the AI at a pile of context
and a spoken instruction, and judge what it hands back.** That atom is missing.

## The interaction (owner, verbatim-distilled)

> Lasso a bunch of stuff, pull an **Ask AI** mode out of a drawer, speak your prompt on top of all the
> context, and it spits out an output — like a **printer card coming out of the shelf** — you watch it,
> and you decide to **bin it or keep it**. This is the gamification of the DeskOS.

1. **Lasso** any objects — meetings, spilled outputs, KB entries, transcript slips. That is the
   **context**, mixed kinds welcome.
2. **Pull "Ask AI" from the Tools drawer** (or the selection bar's Ask action) and drop it on the
   selection — the atomic **combine** ([[story-20-the-desk-object-model]] grammar).
3. **Speak your prompt** (Whisper → text, editable) — your instruction *on top of* that context.
4. The model runs (on-device or endpoint, resolved by the inference setting / Phase-15 fluid compute);
   the **egress badge** says where it ran.
5. The output **prints** — a card slides out of the shelf with a real materialize animation; you watch
   it form.
6. **Keep or bin** — a decisive gesture (swipe up to keep / down to bin, or two buttons). **Keep**
   persists it as a real `Artifact` (Content — now file-able, classifiable, syncable, provenance =
   the lassoed context + the prompt). **Bin** discards it; nothing is saved.

## Scope

- **In:** the atom end-to-end on the iPad — lasso → Ask AI → spoken/typed prompt → context assembly
  from the selected objects → a single model call → the printed result card → keep (persist as an
  Artifact with provenance) / bin (discard). Egress-honest. On-device first; endpoint if configured.
- **Out:** chaining/saving Asks into a reusable Workflow (that promotion is HSM-16-08); the web build of
  the atom (parity, folds into HSM-16-04); multi-card batch asks.

## Acceptance criteria

- [ ] Lassoing objects + invoking Ask AI assembles their content as context for one model call.
- [ ] The prompt can be **spoken** (Whisper) or typed; the run shows the egress badge (where it ran).
- [ ] The output materializes as a **printed result card** you watch form; **Keep** persists it as an
      `Artifact` carrying its provenance (the context ids + the prompt); **Bin** discards it cleanly.
- [ ] Runs on-device with no network when inference is local (air-gap honest).
- [ ] Proven on the iPad Air M4 (real metal, not seeded — [[feedback_verify_on_device_not_seeded]]),
      ideally on the `.43`/Mac endpoint AND on-device.

## Test plan

- On device: lasso two meetings + an output, Ask AI, speak "what decisions are common across these",
  watch the card print, keep it → it appears as a filable artifact; bin a second one → gone.
- Host/unit: context assembly from a mixed selection; a kept Ask becomes an `Artifact` with provenance;
  egress scope resolves correctly for local vs endpoint.
