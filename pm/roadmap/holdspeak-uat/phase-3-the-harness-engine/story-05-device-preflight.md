# HSU-3-05 — Device pre-flight block (answer the iPhone/iPad columns)

- **Project:** holdspeak-uat
- **Phase:** 3
- **Status:** backlog
- **Depends on:** none
- **Owner:** unassigned (device legs owner-gated)

## Problem

The three-surface parity claim is the rig's reason to exist, yet the iPhone/iPad
columns are almost all `n/a` — the re-eval's sharpest finding
(`PROTOCOL-COVERAGE.md` §3.2 / the re-eval §5). Some of that is a false `n/a`
(fixable in authorship), but the genuinely device-local preconditions — a paired
device, a model installed on it, the hub reachable on the LAN — cannot be induced
from the LAN and stay hand-staged. This story builds what the harness *can*: the
LAN-bind + pairing-facts + a `device_paired` liveness probe, so a device sitting
has a real pre-flight and the device *verdict* is the only manual part.

## Scope

- In:
  - A recipe `hub-reachable-on-lan`: boot LAN-bound (the conductor already mints
    the run's token + reports pairing facts), probe `hub_lists_models` reachable
    from the LAN address.
  - A verb `pair_device` where the product exposes a pairing/PSK route
    (`device psk` / `/api/devices/*`), and a probe `device_paired` reading the
    device registry (`/api/devices/health`) — green when a real device has paired.
  - A documented **press-play pre-flight runbook** (the HSM-16-06 shape) for the
    truly device-local states (`model-installed-on-device`, `airplane-mode-on`,
    `mic-permission-granted`) the harness checks-but-cannot-induce.
  - Wire the pre-flight into pack-b (mobile.steering.*) and pack-e (phone-served
    edge, iPad-relay) so the device columns become *walkable* — the verdict cast
    from the device's own browser over LAN (HSU-1-04's shared-run path).
- Out: faking any device-local state or device verdict; the App build/signing
  (that's the HSM track); anything that needs a device the owner doesn't have in
  hand.

## Acceptance criteria

- [ ] `hub-reachable-on-lan` boots LAN-bound and a device browser can reach the
      run + list its models (pairing facts correct).
- [ ] `device_paired` reads green only when a real device has paired — never
      faked; honestly red/pending otherwise.
- [ ] The pre-flight runbook names every device-local precondition the harness
      checks-but-can't-induce, and the packs' device legs point at it.
- [ ] The device *verdicts* remain owner-gated (cast from the device), and the
      record says so.

## Test plan

- Integration: LAN bind + pairing facts + `hub_lists_models` from the LAN
  address (a second loopback client stands in for a device in CI).
- Manual/device: the real pairing + the device verdicts — **owner-gated**, on
  real glass.

## Notes / open questions

- Read `web_auth.py` (per-HOME token), the `device psk` CLI + `/api/devices/*`
  routes, and the HSM-16-06 press-play runbook shape; this is the honest edge of
  what a LAN-bound harness can reach.
