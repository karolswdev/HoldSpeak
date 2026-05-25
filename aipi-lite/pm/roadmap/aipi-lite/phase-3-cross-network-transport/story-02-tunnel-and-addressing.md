# AIPI-3-02 - Tunnel/VPN Choice + Cross-Network Addressing

- **Project:** aipi-lite
- **Phase:** 3
- **Status:** backlog
- **Depends on:** AIPI-3-01
- **Unblocks:** AIPI-3-05
- **Owner:** unassigned

## Problem

With TLS in place (story 01) the bridge can talk `wss://` to any
public-reachable HoldSpeak. But HoldSpeak is local-first and binds
to `127.0.0.1`; getting it reachable from the bridge running on a
different network needs a tunnel or VPN. Pick one to recommend,
document the alternatives.

## Scope

### In

- **Recommended path: Tailscale.** Both bridge host + HoldSpeak host
  on the user's tailnet; magic DNS gives stable hostnames
  (`holdspeak.<tailnet>.ts.net`); free for personal use; mesh
  topology has no single point of failure.
- **Documented alternatives:**
  - **Cloudflare Tunnel** — public hostname, real cert from Let's
    Encrypt, no port forwarding. Requires Cloudflare account; free
    tier covers personal use. Edge terminates TLS; the underlying
    HoldSpeak link can stay `ws://` on loopback.
  - **Self-hosted WireGuard** — for users who don't want a third
    party (Tailscale's coordination server, Cloudflare). More setup
    work; full control.
- **Per-network bridge.env profiles** — the user might run the
  bridge on a laptop that travels between networks. The bridge
  itself doesn't care (the URL is the URL), but the runbook should
  show how to keep one `bridge.env` for home and one for travel
  (e.g., `bridge.env.home` + `bridge.env.travel` symlinked at
  runtime, or a small wrapper script).
- **Document the addressing decision tree:**
  - On the same LAN as HoldSpeak → `127.0.0.1` or `holdspeak.local`.
  - On Tailscale → `<host>.<tailnet>.ts.net`.
  - On Cloudflare Tunnel → public hostname.
  - On a port-forwarded home network → public IP / dyndns name.

### Out

- Configuring HoldSpeak for cross-network listening (HoldSpeak
  HS-15's job — bind beyond loopback, handle forwarded headers).
- Setting up the tunnels themselves end-to-end — runbook links to
  Tailscale / Cloudflare / WireGuard install docs rather than
  re-deriving them.
- Multi-bridge orchestration (running bridges on multiple machines
  reaching one HoldSpeak).

## Acceptance Criteria

- [ ] Runbook section "Cross-network setup" exists in
  `docs/HOLDSPEAK_BRIDGE.md` (or a dedicated
  `docs/CROSS_NETWORK.md` if the content is large enough),
  covering Tailscale (recommended) + Cloudflare Tunnel + WireGuard
  (in that order of recommendation).
- [ ] End-to-end smoke test against at least one of the three
  paths: bridge on a different network, HoldSpeak at the user's
  home, voice typing works. Recorded as evidence (terminal output
  + a screenshot of the typed text).
- [ ] Addressing decision tree documented (which scheme to use for
  which setup).
- [ ] Per-network `bridge.env` profile workflow documented.
- [ ] No code change required in the bridge for this story (story
  01 already added TLS + URL handling). If verification surfaces a
  bridge-side bug, fix it in this story.

## Test Plan

- **Manual** — this story is mostly setup + verification:
  1. Install Tailscale on the bridge laptop + HoldSpeak host;
     verify both are on the tailnet.
  2. From the bridge laptop, while connected to a *different*
     physical network (e.g. phone hotspot), run
     `bridge.py --check` with `HOLDSPEAK_URL=ws://<holdspeak-host>.<tailnet>.ts.net:<port>/api/devices/audio`.
     Expect exit 0.
  3. Run `bridge.py` for real, focus a text editor on the
     HoldSpeak host (using the magic of "the host's display via
     screen-sharing or local presence"), press the device's right
     button, speak, release. Expect typed text within latency
     tolerances (story 03 measures).

## Notes

- Tailscale's free tier is up to 100 devices, which covers any
  realistic personal use of AIPI-Lite. If the user objects to the
  coordination server, point at WireGuard.
- Cloudflare Tunnel terminates TLS at the edge, which means the
  bridge sees `wss://` (matching story 01's TLS work) and HoldSpeak
  sees plain `ws://` on loopback (no HoldSpeak-side TLS work
  required). This is actually a clean way to "do TLS without HS-15
  shipping TLS termination" — note in the runbook.
- WireGuard requires server-side config + DNS. Not for the
  faint-of-heart but full control. Document at the level of "here
  are the steps; consult WireGuard's docs for deep detail."
- The "per-network profiles" story is mostly a shell-script question.
  A small `scripts/bridge-with.sh home` wrapper that picks the
  right env file is enough.
