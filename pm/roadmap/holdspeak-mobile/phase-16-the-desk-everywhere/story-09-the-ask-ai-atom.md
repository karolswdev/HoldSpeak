# HSM-16-09 — The Ask AI atom: lasso → ask → speak → print → keep or bin

- **Project:** holdspeak-mobile
- **Phase:** 16
- **Status:** todo — **the highest-value atom; a strong candidate to lead the capability work** (it runs
  on-device today and needs none of the mesh).
- **Depends on:** the lasso/selection (HSM-14-19), the on-device/endpoint provider
  (`InferenceConfigStore` / `generate`), Whisper dictation (Phase 3 / the wake-word stack), the egress
  badge. [[story-20-the-desk-object-model]] for the kind + grammar.
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
