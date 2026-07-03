# HSM-21-03 — GitHub-repo honesty on the desk

- **Project:** holdspeak-mobile
- **Phase:** 21
- **Status:** todo — the audited web+backend halves shipped pre-open (web settings binds
  `companion_github_repo`, `system/settings.py:429` persists it, the propose route falls
  back to it, `desk_actuators.py:236`).
- **Depends on:** the hub's desk-actuator status surface (whatever feeds the tile's
  `configured` state today).
- **Unblocks:** no dead-on-arrival GitHub sends from the desk.
- **Owner:** unassigned

## Problem

The iPad's `DeskHostLink.propose` sends no repo (`DeskDioramaStage.swift:2699`), so a
GitHub send works only through the host's `companion_github_repo` fallback — yet the
GitHub tile presents ready regardless. With no repo configured on the host, the send is a
guaranteed 400 discovered at approve time. The audit's literal fix ("iPad sends a repo")
is one option; the honest minimum is that **readiness tells the truth**.

## The design

1. **Ratify the host-config path** (this story's design decision): the repo is desktop
   configuration, like every credential — the iPad does not grow a repo field. Recorded
   here; the propose body stays `{text, title}`.
2. **The tile tells the truth:** the GitHub connector's ready state derives from the
   hub's real posture (repo configured or not); unconfigured renders the same
   not-configured treatment the other connectors use, and the act sheet routes to "set it
   on your desktop" instead of a doomed send.
3. **Hub side if needed:** if no existing status surface carries `github repo
   configured`, extend the desk-actuator status payload minimally (a boolean, no
   credential material — the repo name itself stays server-side unless already exposed).

## Scope

- **In:** the honest ready state + its data path; the ratified design note; proof (a
  hub with and without `companion_github_repo`).
- **Out:** an iPad repo input; web/settings changes (shipped); the actuator flow itself
  (HS-38/49, unchanged).

## Test plan

- Hub-side: route/unit tests for the status boolean (if added).
- Live-hub proof: tile state with and without the repo configured; `swift test` +
  meeting-capture sim build green.
