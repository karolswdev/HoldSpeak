# Phase 162 — Project Rooms: The Update Factory (P3) — Final summary

**Verdict:** COMPLETE 7/7 · owner's shot verdict on the face: **PASS
(round 4)** · counsel: (recorded below at close).

## What this phase proved

P3's exit, verbatim from the driver: **the owner creates a usable
evidence-backed update without reconstructing project truth.** The
factory drafts over a pinned revision + source manifest, cannot emit
an unlocated claim, survives a dead router, and freezes what it
publishes.

- **The update ledger (01):** schema v70 `project_updates` — pinned
  to an explicit project_revision + manifest at draft time; lifecycle
  law as REPO law (PublishedUpdateError — published is immutable;
  supersede mints draft_revision+1 atomically); pupd_ correctly
  non-deterministic; reconcile proven on a COPY of the owner's real
  DB.
- **The deterministic drafter (02), shipped FIRST:** the frozen Claim
  schema {span_id, text, refs, section}; six UPD-001 sections; every
  factual sentence resolves to canonical refs — it does not know how
  to lie; honest minimal sections; caveats iff coverage is partial;
  BYTE-deterministic across a supersede boundary (goldens:
  rich/empty/degraded).
- **The model drafter (03):** constrained to 02's schema — cited or
  MARKED (**[UNVERIFIED]**), never bare fact; invented refs rejected
  against the manifest inventory; typed fallbacks (no_broker /
  no_assignment / runner_error / no_output / unparseable_output) with
  honest generator provenance; the 143 census-lawful routing
  entrance; **the live .43 leg passed on real LAN inference** (worker
  + orchestrator runs). Two pre-existing census drifts healed — two
  main-baseline names now green on this branch.
- **The five verbs (04):** UPD-005 as separate commands with honest
  receipts; ONE publish transaction (publish + project revision+1 +
  change row + ledger + command); the HTTP loop proven
  (draft→save→publish→list→regenerate→markdown); api-surface 606→612
  purely additive.
- **The face (05):** the Updates verb in the Room's chrome →
  UpdatePosture; the body edits in **DeskEditor** (the Notes
  CodeMirror species); published renders as a **document** (Material)
  with named, deduplicated source chips that OPEN their sources —
  **160's S-4 debt paid** where it matters; MARKED spans and a single
  unverified banner; egress badge at the model-draft decision.
  **CLOSED ON THE OWNER'S VERDICT (PASS, round 4)** — four rounds,
  each recorded verbatim (below).
- **The walk (06):** PV-H04's two numbers MEASURED and held through
  every round — **2.77s** edit-to-copy vs the 300s bar (real
  keystrokes through CodeMirror); **retention 1.0** vs 0.70 (honest
  difflib measure, the representative edit recorded as additive);
  four legs ×2 deterministic; the no-raw-ids law asserted on glass;
  the live model leg deliberately rides 03's service-level proof.

## The four owner rounds (the phase's lesson)

r1 BOUNCE — "why aren't we using the component that we use for
Notes"; the published view was a claims dump. → DeskEditor reused;
the rendered document with per-section deduplicated sources.
r2 BOUNCE — the list row clipped to fragments ("Model ("). → Three
attempts to the TRUE root cause: the house ledger's nowrap crushing
the two-liner; fixed with a targeted :has() override.
r3 QUESTIONS + FINDING — editability confirmed by canon (UPD-001/
UPD-005/PV-H04); "it's not obvious that it is an interactable
surface" → the row (already a button) gained a rest-visible chevron.
r4 **PASS — close it.**

The 161 lesson compounded: prove the MOUNT, prove the PIXELS — and
the orchestrator's own eyes on every shot before the owner's
(three defects caught pre-verdict: unmounted-adjacent claims dump
framing, raw ids, the clipped row) plus four rounds of the owner's
eyes after. Fixtures speak the wire; a fixture bypassing a
validating seam is a lie.

## Gates

- Web: npm check PASS; inherited baseline 2224/2225 passed with the
  ONE candidate being the KNOWN ThoughtDocumentPane suite-order flake
  family (isolation ×2 green; thought-workspace untouched since
  main). Zero unexplained branch-new.
- Python full suite + sweep vs main's 27-name baseline: (filled at
  close from the story-07 evidence capture).
- Counsel: (filled at close).

## Debts

- PAID: 160's S-4 (source chips open their source — on the face that
  makes it matter).
- Carried (named, for P4): 160's N-5 (widen the no-fetch spy), N-1
  (Space preview), N-2 (server-side undismiss); 158's S-1/N-1/N-3;
  159's seeding walls; 161 counsel N-1 (React scope key).

## The arc

P0 #521 → P1 #522 → P1a #523 → P2 #524 → P2a #525 → **P3 (this
phase)** → next: **P4 The Steward's Hand** (manual run_once, the
bounded V0 effect set) — and Gate A's dogfood clock keeps mattering.
