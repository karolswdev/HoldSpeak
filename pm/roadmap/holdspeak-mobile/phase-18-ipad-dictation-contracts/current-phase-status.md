# Phase 18 — The iPad joins the dictation contracts

**Status:** planned — **leads The Equilibrium program** ([`EQUILIBRIUM.md`](../EQUILIBRIUM.md)).
Ready to open; stories authored.

**Last updated:** 2026-06-27 (**authored** from the parity audit. The biggest single
imbalance the flotilla found: the iPad authors desk primitives but is a *tourist* for the
dictation contracts. The hub already serves every route; the iPad has no Swift client. This
phase builds the clients.)

## Why this phase exists

Audit theme 2: *the iPad is an authoring port for the desk primitives but a tourist for the
dictation and meeting contracts.* `HTTPDesktopClient` implements only a narrow slice
(`sendRemoteDictation`, summaries, companion, agent/chain run) and never touches the rich
read routes the hub already exposes. The dictation half of that gap is six concrete,
verified holes — five of them high-severity:

- **The dictation pipeline has no iPad surface.** `HTTPDesktopClient.swift` does only
  `sendRemoteDictation`; `CompanionShellApp.swift:228` `dictateScreen` is a static
  placeholder. The hub serves `/api/dictation/readiness`, `/blocks` (+CRUD),
  `/block-templates`, `/dry-run`, `/project-context` — none are called.
- **Voice command macros silently never fire** on the iPad→desktop relay.
  `api_dictation_remote` (`holdspeak/.../pipeline.py:299-369`) goes straight to
  `_run_dictation_dry_run_text` and never calls `dispatch_voice_command`. The iPad has no
  authoring board either.
- **Spoken language is ignored.** All three WhisperKit call sites (`Stores.swift:42`,
  `CompanionAnswerApp.swift:44`, `SpeakHarnessApp.swift:108`) omit
  `DecodingOptions(language:)` and always auto-detect, though the language knob is canonical
  on the hub.
- **The spoken-symbol dictionary is entirely absent in Swift.** No `TextProcessor` port
  after `WhisperText.clean`.
- **Activity pre-briefing has no client.** The iPad never calls any `/api/activity/*` route.

A route existing on the hub is not the contract being honored. This phase makes the iPad a
real client of the dictation contracts, end to end, proven on metal.

## The load-bearing design call

**One client seam, many routes.** The work is overwhelmingly *plumbing the hub routes the
iPad already has the right to call* into `HTTPDesktopClient` + a thin SwiftUI surface, plus
two genuine on-device ports (language at the WhisperKit sites; the symbol dictionary). It
reuses three proven seams:

1. **The desktop client** (`HTTPDesktopClient` / `DeskHostLink`) — already authed with the
   Bearer token (fixed this session). New routes hang off it.
2. **The remote dictation relay** (`/api/dictation/remote`, the Phase-13 proven inject
   path) — the macro fix lives on the *hub* end of this exact relay.
3. **The on-device WhisperKit transcriber** + `InferenceConfigStore` — the language code and
   the symbol pass slot into the existing transcribe path, no new engine.

**Honesty + voice rules carry in:** every new text field gets a speak-to-fill mic
([[feedback_voice_mic_every_input]]); new screens edit in-world, not in dim-scrim modals
([[feedback_no_modals_in_world]]); any new send shows the egress badge.

## Stories

| ID | Title | Status |
|----|-------|--------|
| HSM-18-01 | The dictation pipeline client + authoring/preview screen — **leads** | todo |
| HSM-18-02 | Voice command macros fire on the remote relay + the iPad CommandsBoard | todo |
| HSM-18-03 | Spoken language at every WhisperKit call site | todo |
| HSM-18-04 | The spoken-symbol dictionary, ported to Swift | todo |
| HSM-18-05 | Activity pre-briefing — the source-cited nudge client | todo |
| HSM-18-06 | The real-metal proof + entry-point docs | todo |

## Where we are

Not started. The audit supplies every story's starting `file:symbol` evidence. **18-01
leads** (it stands up the client surface the dictation features hang off); **18-02 is the
highest-value single fix** (a one-function hub gap that makes the entire macro feature work
from the iPad). 18-03 and 18-04 are independent on-device ports and can run in parallel.
18-06 is the gate.

## Carried context

- 18-02's hub fix (`pipeline.py`) is the only *desktop-side* change in this phase; it is a
  real contract hole, not iPad-only plumbing, so it carries a hub-path test.
- The learning loop's iPad client is **Phase 19**, not here (it is meeting-adjacent and
  read-first); do not fold it in.
