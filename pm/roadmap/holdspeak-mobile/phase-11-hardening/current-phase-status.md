# Phase 11 — Hardening

**Status:** in-progress (scaffolded 2026-06-18; **HSM-11-06 done** — the first hardening
landed: on-device generation robustness, host-side). Track L of the Council Implementation
Charter — the final phase. It stresses the whole stack (audio + Whisper + local inference +
persistence + sync + UI) against the charter's five real-world scenarios and declares
production readiness. Closing this phase means the HoldSpeak Mobile Runtime ships.

**Last updated:** 2026-06-21 (**HSM-11-06 done — on-device generation robustness
(structured-output salvage).** A host-side hardening that flowed straight from the real-metal
finding that a 22-min meeting dropped 3 of 4 artifact types to `noJSON`. `StructuredOutput`
now does **balanced extraction** (first complete brace-balanced structure, string/escape
aware — not first-`{`-to-last-`}`), **truncation salvage** (close an open string + brackets so
a cut-off object still decodes), **conservative repair** (smart quotes, value-position Python
literals, string-aware trailing-comma removal — never corrupting body text), and **array
unwrap** (`[{…}]` → the inner object). The repair-retry loop stays the backstop. `swift test`
**197/6-skip/0-fail (+15)**; the existing `InferenceTests` stay green (no regressions). Pure +
model-free → no device needed; it **de-risks the pending HSM-8-06 device gate** (fewer
`noJSON` losses) without replacing it. See [`evidence-story-06`](./evidence-story-06.md).
Earlier: scaffolded — stories HSM-11-01..05 stubbed from charter Track L; no work started.)

## Goal

Prove the mobile runtime survives real-world abuse: a 4-hour meeting, airplane
mode, low battery, thermal stress, and app suspend/resume — each as a deliberate
scenario on real Tier-1/Tier-2 hardware, with graceful degradation (model
downgrade, queue-and-resume) rather than data loss or crashes. The phase passes on
production readiness — the Track L gate / program Gate 7 — which is the program's
final gate.

## Scope

- **In:** the five charter scenarios as dedicated stories — 4-hour meeting
  (HSM-11-01), airplane mode / offline (HSM-11-02), low battery + thermal stress
  (HSM-11-03), app suspend/resume + background audio (HSM-11-04) — and the
  production-readiness closeout that runs them all on hardware (HSM-11-05).
- **Out:** new features. The earlier gates (each phase owns its own). A public App
  Store submission / TestFlight logistics (that's a release step beyond this
  roadmap; this phase declares the runtime *ready*, the owner decides shipping).
  Encryption-at-rest beyond what HSM-11 surfaces as a gap.

## Exit criteria (evidence required)

- [ ] A 4-hour continuous meeting completes on real hardware without crash, data
      loss, or unbounded memory (HSM-11-01).
- [ ] Airplane mode / offline: Mode A (fully local) works end to end with no
      network; nothing degrades silently or fails opaquely (HSM-11-02).
- [ ] Low battery + thermal stress: the runtime degrades gracefully (model
      downgrade per the local-model strategy, throttle, warn) rather than crashing
      or corrupting (HSM-11-03).
- [ ] App suspend/resume + backgrounding during an active recording loses no
      audio and resumes cleanly (HSM-11-04).
- [ ] **Track L gate / Gate 7 — production readiness:** all five scenarios pass on
      real Tier-1/Tier-2 hardware, findings filed, and a readiness verdict recorded
      (HSM-11-05).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSM-11-01 | 4-hour meeting endurance | backlog | [story-01](./story-01-four-hour-meeting.md) | — |
| HSM-11-02 | Airplane mode / offline | backlog | [story-02](./story-02-airplane-mode.md) | — |
| HSM-11-03 | Low battery + thermal stress | backlog | [story-03](./story-03-low-battery-thermal.md) | — |
| HSM-11-04 | Suspend / resume + background audio | backlog | [story-04](./story-04-suspend-resume.md) | — |
| HSM-11-05 | Production-readiness closeout (Gate 7) | backlog | [story-05](./story-05-production-readiness-closeout.md) | — |
| HSM-11-06 | On-device generation robustness (structured-output salvage) | done | [story-06](./story-06-structured-output-robustness.md) | [evidence](./evidence-story-06.md) |

## Where we are

Just scaffolded. This is the program's last phase: it doesn't add features, it
proves the stack the prior phases built holds under the charter's five stress
scenarios. Each scenario is its own story so a failure is attributable, and the
closeout (HSM-11-05) is the production-readiness verdict on real hardware. Every
story here depends on the full stack (Phases 2–10) being in place. Next: pick up
the scenarios once the feature phases land; do not start hardening a stack that
isn't whole.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| A scenario exposes a deep architectural problem too late to fix cheaply (e.g. memory model can't hold 4 hours) | high | Run the endurance + thermal scenarios as early in this phase as possible (they're the riskiest), not last; feed findings back as new feature-phase stories, not Phase-11 hacks | A scenario fails for a reason rooted in an earlier phase's design — file it back to that phase; don't patch it in the hardening layer |
| Graceful degradation isn't actually graceful — thermal/battery stress crashes instead of downgrading | high | HSM-11-03 builds explicit downgrade paths (smaller model, throttle) and asserts the app survives, not just that it warns | The app crashes or corrupts under thermal/battery stress instead of degrading — halt; degradation is a charter requirement, not optional |
| Suspend/resume loses the tail of a recording (the classic mobile bug) | high | HSM-11-04 kills/backgrounds mid-recording and verifies the tail is intact, building on Phase-4 crash recovery | Backgrounding loses the last segments — fix the audio/persistence lifecycle before the gate |
| "Production readiness" has no definition, so the final gate is a feeling | medium | HSM-11-05 fixes the readiness checklist (the five scenarios pass + findings triaged) up front; readiness is the checklist, not a vibe | The closeout can't say what "ready" means — define the checklist first |
| No real hardware for the full matrix (Tier-1 iPad + Tier-2 iPhone) | medium | The whole phase is hardware-only by nature; secure the devices before starting; simulator results don't count | Any scenario closed on simulator-only evidence — reject; the gate is on metal |

## Decisions made (this phase)

- 2026-06-18 — Each of the five charter scenarios is a dedicated story (not one
  "hardening" blob) so a failure is attributable and findings route back to the
  owning phase; HSM-11-05 is the production-readiness verdict — roadmap-builder
  convention + charter Track L.

## Decisions deferred

- The production-readiness checklist's exact contents beyond the five scenarios
  (crash-free session rate? a battery-drain bar?) — trigger: HSM-11-05 — default:
  the five scenarios pass + all findings triaged (fixed or filed) as the readiness
  bar; extend only if the owner adds criteria.
- Whether encryption-at-rest is required for v1 (deferred from Phase 4) — trigger:
  HSM-11-03/05 — default: surface it as a finding for the owner; not a v1 blocker
  unless the owner makes it one.
- What "ship" means after readiness (TestFlight vs. App Store vs. internal) —
  trigger: HSM-11-05 verdict — default: out of this roadmap's scope; the owner
  decides once the runtime is declared ready.
