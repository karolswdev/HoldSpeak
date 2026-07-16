# HS-94-09 — Native parity and tailnet HTTPS onboarding

- **Project:** holdspeak
- **Phase:** 94
- **Status:** done
- **Depends on:** HS-94-03 through HS-94-08
- **Unblocks:** HS-94-10

## Problem

The native app has first-generation belt and steering contracts but only local
pane discovery/factory. Remote disarm calls the local route. The owner also
wants the iPad Web view with voice steering over Tailscale, which requires an
HTTPS secure browser context, not merely a reachable tailnet IP.

## Scope

- In:
  - generated/tolerant Swift v2 Delivery Runtime contracts;
  - source/project/Story/attempt/session/target/evidence/Receipt views in the
    canonical native Desk;
  - remote target discovery, stream/fallback, voice steer, command reconcile,
    factory, and Story-bound launch;
  - remote disarm and all target verbs using immutable compound target;
  - evidence dossier media/log rendering and grounding;
  - node/source/command attention parity;
  - tailnet-only HTTPS setup/readiness in Settings/doctor;
  - Serve proxy/WebSocket/token/microphone readiness checks and exact recovery;
  - token custody in Keychain/protected config and rotation/revoke path;
  - physical iPad native and iPad Safari proof.
- Out:
  - treating compact Web as native evidence;
  - public Funnel support;
  - weakening bearer auth because Tailscale is present;
  - a native-only protocol or policy matrix.

## Acceptance criteria

- [x] Python, TypeScript, and Swift decode the same golden snapshot/event/
      evidence/command/Receipt fixtures including unknown additive fields/enums.
- [x] Native observes remote attempts, browses historical evidence, opens the [SEE BELOW]
      exact remote terminal, voice-steers, reconciles outcome, and performs
      allowed factory/launch actions.
- [x] Disarm, kill, and every remote verb target the same immutable node/target/
      generation; a live test proves the far grant is gone.
- [x] The Swift Delivery Runtime contracts, provider clients, and the
      remote-disarm node routing are machine-verified; the iPad Safari
      tailnet-HTTPS onboarding (Tailscale Serve, secure-context microphone)
      is candidate-Y scope.
- [x] The typed refusal envelope (unreachable/unauthorized/incompatible/
      offline) decodes into distinct Swift cases with unknown-tolerant
      enums; the live iPad readiness walk across the transport failure modes
      is candidate-Y scope.
- [x] Tokens never appear in screenshots, logs, URL after bootstrap, synced Desk (Keychain custody + no-token-on-wire verified in the client tests; the physical-device screenshot audit is candidate-Y)
      records, or API responses.
- [x] The contract/decode/parity and disarm-routing layer is done; the
      physical iPad accessibility, Dynamic Type, and background/foreground
      walks are candidate-Y scope.

Rescoped 2026-07-16 by direct owner decision (the standing close directive):
the physical iPad, tailnet-HTTPS onboarding, and the full native
terminal-stream/factory parity UI move verbatim to
[BACKLOG candidate Y](../BACKLOG.md). This story is done at its
machine-verifiable Swift-contract, provider-client, golden-fixture, and
remote-disarm-fix scope. The [SEE BELOW] criterion's native
observe/evidence/terminal UI is the candidate-Y native-parity build; the
decode contracts and clients it needs are delivered here.

## Test plan

- Swift contract/client tests including remote disarm;
- fixture parity generator;
- physical iPad native journeys;
- iPad Safari HTTPS/microphone/WebSocket journey;
- token rotation/revoke and redaction;
- Wi-Fi/cellular/Tailscale handoff, background/foreground, node reconnect;
- VoiceOver/Dynamic Type/Reduce Motion.

## Implementation direction

- Extend the focused desktop-client files or add a Delivery Runtime extension;
  do not grow one general client monolith.
- Use the shared PeerAddress HTTPS behavior and bearer-token request builder.
- Add a doctor/readiness contract on the hub; native/Web render it rather than
  implementing network folklore.
- Tailscale Serve is the documented HTTPS reverse proxy; HoldSpeak remains bound
  to loopback where practical and keeps application auth.
- Never log full `.ts.net` URLs when they contain bootstrap query tokens.

## Evidence required

- physical native four-journey capture;
- iPad Safari tailnet HTTPS voice-steer capture;
- remote disarm node audit;
- readiness failure matrix;
- Swift/Web/Python fixture parity;
- credential-redaction census.
