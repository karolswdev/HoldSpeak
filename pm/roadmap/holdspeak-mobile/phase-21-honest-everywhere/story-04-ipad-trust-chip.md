# HSM-21-04 — The ambient trust chip on the iPad

- **Project:** holdspeak-mobile
- **Phase:** 21
- **Status:** todo
- **Depends on:** the web `TrustChip.astro` (HS-42-05) + `/api/setup/status`
  (`holdspeak/web/routes/setup.py:23`, `build_setup_status()`); 21-01's `EgressScope`
  grammar.
- **Unblocks:** the iPad states its posture ambiently, like the web has since Phase 42.
- **Owner:** unassigned

## Problem

The web shell header carries an ambient posture chip ("Local only · Configured endpoint ·
Writes need approval · Needs attention") driven by `/api/setup/status`. The iPad — the
surface most likely to be trusted implicitly — has none; its only posture signals are
per-card badges.

## The design

1. **A setup-status client** on `HTTPDesktopClient` (own extension file, the equilibrium
   conflict rule): `setupStatus()` decoding the posture facts the chip needs.
2. **The chip in the Companion shell's top bar**, beside the connection chip: one compact
   posture line in the same grammar as the web chip; a degraded hub ("needs attention")
   renders honestly; unreachable renders nothing new (the connection chip already owns
   that state). Labels, never sentences.
3. **The web-chip audit** (the story's second half): verify `TrustChip` renders from the
   live `/api/setup/status` posture and never a hardcoded default once loaded — recorded
   in evidence with the posture flipped for real (e.g. actuators enabled vs not).

## Scope

- **In:** the client + decode test; the shell chip; the web audit; live-hub proof with
  two different postures.
- **Out:** the desk app's diorama (its trust surface is the per-primitive badge from
  21-01); any new hub route (the adapter exists).

## Test plan

- `swift test` (new `SetupStatusClientTests` decode + URL).
- Live-hub proof: two scratch-hub postures → two shell screenshots; the web chip
  audited against the same hubs.
