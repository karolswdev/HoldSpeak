# Phase 18 — The iPad joins the dictation contracts

**Status:** in-progress (opened 2026-06-27) — **leads The Equilibrium program**
([`EQUILIBRIUM.md`](../EQUILIBRIUM.md)), built against the
[Experience Vision](../EXPERIENCE-VISION-2026-06-27.md) (the dictation teleprompter + the
"macro fires as an object" signature moment).

**Last updated:** 2026-07-03 (**RESUMED, owner-picked, + the Desk-Era rider added.** After
the web/hub Desk Era closed (Phases 72–78, PRs #207–#214), the owner chose iPad parity as
the next platform step and scoped it as *this phase as authored plus one rider*:
**HSM-18-07** — run-born artifacts (hub schema v6, `origin='run'`) join the cross-surface
artifact contract and materialize on the iPad desk, plus a guard locking
`HTTPDesktopClient` paths against `docs/api-surface.json` (the durable form of verifying
the Phase-72 route rename). Grounded findings: `artifact.schema.json` carries no `origin`
field; Swift already calls `/api/coders/*` with zero stale `api/companion` literals but
nothing locks it. Prior update, 2026-06-27: **OPENED + first fix landed.** HSM-18-02's hub half shipped:
`api_dictation_remote` now fires voice-command macros on the remote relay (it never did, so a
macro spoken from the iPad was silently dictated as prose). The macro fires through the same
bounded/guarded connector as the local path; a `type_text` macro free-types into the focused
Mac app via the proven focused relay; the response carries a `fired` object the companion
renders as the macro chip. Off by default (macros disabled → byte-identical plain dictation).
Proven: `tests/unit/test_web_routes_remote_dictation.py` 11/11 incl. the remote-path macro
test the audit demanded — the seam that shipped broken because only the local path was tested.)

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
| HSM-18-01 | The dictation pipeline client + authoring/preview screen — **leads** | in-progress (client spine + teleprompter screen landed, sim-proven; voice input + metal proof remain) |
| HSM-18-02 | Voice command macros fire on the remote relay + the iPad CommandsBoard | in-progress (hub half landed; iPad board todo) |
| HSM-18-03 | Spoken language at every WhisperKit call site | in-progress (main app done; harness apps + metal proof remain) |
| HSM-18-04 | The spoken-symbol dictionary, ported to Swift | in-progress (built-ins ported + tested + on the dictation path; user-symbol editor + metal proof remain) |
| HSM-18-05 | Activity pre-briefing — the source-cited nudge client | todo |
| HSM-18-06 | The real-metal proof + entry-point docs | todo |
| HSM-18-07 | The Desk-Era rider: run-born artifacts on the iPad desk + the route-surface lock | in-progress (contract half landed: `origin` on the wire + schema + Swift models; the route-surface lock verified already shipped as HS-72-02; desk materialization remains) |

## Where we are

**Resumed 2026-07-03 as the owner-picked next platform step**, scoped to the six authored
stories plus the Desk-Era rider (HSM-18-07). HSM-18-02's hub half is done + tested (the macro
relay; see Last updated). Remaining: 18-02's iPad CommandsBoard; 18-01 (the dictation pipeline
client + teleprompter preview screen, the phase's experience hero); 18-03/18-04 (the
independent on-device language + symbol ports, parallel-startable); 18-05 (activity nudges,
needs 18-01's dictate path); 18-07 (parallel-startable, contract-first); 18-06 (the
real-metal gate). The audit supplies every story's starting `file:symbol` evidence. The
owner's Phase-72 iPad device walk stays owner-gated and outside this phase (tracked in
`pm/roadmap/holdspeak/HANDOVER-2026-07-03-desk-era.md`).

## Carried context

- 18-02's hub fix (`pipeline.py`) is the only *desktop-side* change in this phase; it is a
  real contract hole, not iPad-only plumbing, so it carries a hub-path test.
- The learning loop's iPad client is **Phase 19**, not here (it is meeting-adjacent and
  read-first); do not fold it in.
