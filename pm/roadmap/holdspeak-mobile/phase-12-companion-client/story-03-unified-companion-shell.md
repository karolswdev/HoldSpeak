# HSM-12-03 — The unified Companion shell

- **Project:** holdspeak-mobile
- **Phase:** 12
- **Status:** done (2026-06-20 — the `CompanionShell` view-model + `CompanionShellApp`
  present both the on-device runtime and the server in one Signal-language shell;
  host-tested, screenshot-verified on the sim, and run live on a physical iPad. See
  [evidence-story-03](./evidence-story-03.md))
- **Depends on:** HSM-12-01, HSM-12-02
- **Unblocks:** HSM-12-04
- **Owner:** unassigned

## Problem

This is where the "not a dumb terminal" principle becomes visible or gets
violated. The iPad must present, in one native app, **both** its own on-device
runtime **and** the server it is pointed at — web-app-consistent so it feels like
the HoldSpeak you already know, and rich enough that the device clearly stands its
own ground. A shell that hides the local runtime when paired, or that looks
nothing like the portal, fails the owner's brief.

## Scope

- **In:** the SwiftUI Companion shell — navigation consistent with the web portal's
  surfaces (Meetings / Dictate / Companion), dressed in the Signal design language
  (reuse the harness palette: near-black surfaces, one orange signal for the
  live/primary moment, real depth, per-type cards); a connect-to-desktop onboarding
  (point at the server — host/port + token from HSM-12-01); the meetings
  remote-control screens over the HSM-12-02 view-models; and a clear, calm
  "server unreachable" state that never blocks the app. Crucially, the shell
  presents the iPad's **own on-device runtime as a first-class peer** of the server
  view (local meetings / local inference remain reachable and obviously alive when
  paired).
- **Out:** answering the coder / the companion board / voice-note dictation (Phase
  13 — the "Companion" tab's deep content lands there; this story stands up the
  navigation slot and the meetings/local surfaces). The PencilKit notebook (Phase
  8). Any business logic in the views (it stays in the Runtime-Core view-models).

## Acceptance criteria

- [ ] The shell is web-app-consistent: the portal's Meetings / Dictate / Companion
      navigation, rendered in the Signal language (not stock SwiftUI), to a high UI
      standard (real depth, affordances, no flat/basic placeholder cards).
- [ ] Connect-to-desktop onboarding points the iPad at a server (HSM-12-01) and the
      meetings remote-control surfaces (HSM-12-02) are reachable from the shell.
- [ ] The iPad's **on-device runtime is presented alongside** the server view — a
      paired iPad still shows its local meetings/inference as first-class; the device
      is not reduced to a remote (proven in the screenshot/walkthrough).
- [ ] A "server unreachable" state is clear and calm and never blocks on-device use;
      the views hold no business logic (Runtime-Core view-models only).

## Test plan

- Unit: the shell's view-models (composed from HSM-12-01/02) drive
  connected/unreachable/local-only states without UIKit.
- Screenshot / device: the shell on an iPad showing (a) the portal-consistent
  navigation in Signal, (b) the on-device runtime present while paired, (c) the
  unreachable state — screenshot-verified (a class in the bundle is not proof it
  renders; capture the actual screen).
- Manual / device: folded into HSM-12-04.

## Notes / open questions

- Reuse the `InferenceHarnessApp` Signal palette/components as the seed, but this is
  the real shell, not the demo harness — retire harness-only scaffolding.
- One app, not two: default to the companion living as a mode/tab alongside the
  on-device surfaces (Decisions deferred, phase status) so the device stays unified.
- High UI bar applies (repo standing rule): add affordances, check overflow on the
  iPad's large canvas, offer copy/preview where it helps; flat placeholder cards are
  rejected.
