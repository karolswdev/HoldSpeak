# HSM-13-01 — Remote-dictation inject path (desktop + client)

- **Project:** holdspeak-mobile
- **Phase:** 13
- **Status:** done (2026-06-20 — desktop inject path + Swift seam shipped and
  LAN-proven; see [evidence-story-01](./evidence-story-01.md))
- **Depends on:** HSM-12-01 (the desktop client seam + token)
- **Unblocks:** HSM-13-02, HSM-13-04
- **Owner:** unassigned

## Problem

Today the desktop dictates locally (mic → the focused target / the AI PI delivery
path). For the iPad to answer a coder, the desktop needs to accept a dictated
payload **from the client** and route it through the same rich dictation runtime —
plugins, blocks, corrections — so an answer sent from the iPad is as smart as one
spoken at the desk. This is the one genuinely new desktop-side surface in the
track. (Precedent: the mobile program already added Python routes in Phase 10 —
`holdspeak/web/routes/sync.py`.)

## Scope

- **In (desktop, Python):** a new authenticated endpoint (e.g.
  `POST /api/dictation/remote`) in `holdspeak/web/routes/dictation` that accepts a
  dictated payload (text + optional target/session id) from the client and routes
  it through the dictation runtime's rich pipeline (the existing
  plugins/blocks/corrections path used by `dictation_runner`), delivering it to the
  selected destination (the AI PI delivery path / the focused dictation target).
  Tokened behind the Phase-12 client handshake; never autonomous (deliver-on-command
  only). **In (client, Swift):** the `IDesktopClient` method that posts to it.
- **Out:** capturing the voice note (HSM-13-02 produces the text). The Companion
  board / target selection UI (HSM-13-03). Any change to how the desktop dictates
  locally (this is additive — a remote entry point into the same pipeline).

## Acceptance criteria

- [x] `POST /api/dictation/remote` accepts a dictated payload and routes it through
      the dictation runtime's rich pipeline — a test asserts a known
      correction/block/plugin transform is applied (the delivered text is **not**
      raw input). *(`test_processes_through_pipeline_and_delivers`: the stubbed
      pipeline's `[corrected]` transform is what gets delivered, not the raw input.)*
- [x] The endpoint requires the Phase-12 client token; an untokened request is
      refused; the token is never echoed in a response/log. *(Auth is the runtime's
      existing off-loopback web-auth middleware — proven on real metal over the LAN:
      `/api/runtime/status` 401 without token → 200 with it; the Swift seam joins the
      token at call time and never echoes it.)*
- [x] Delivery is deliver-on-command (the payload carries an explicit intent to
      send); there is no autonomous/background injection path. *(The route fires only
      on the client's POST; a delivery-hook failure returns 502 with no retry —
      `test_delivery_failure_surfaces_502_not_autonomous_retry`.)*
- [x] The Swift `IDesktopClient` posts a payload through the seam and surfaces the
      desktop's accept/refuse result; a fake desktop drives the client test.
      *(`testSendRemoteDictationPostsAndDecodes` / `...HTTPErrorThrows` against
      `StubProtocol`; the Bearer token rides, the 401 path throws.)*

## Test plan

- Unit (Python): `uv run pytest` over the new route — pipeline transform applied,
  token required, malformed/untokened refused, target honored; add it to the route
  preflight sweep so it cannot ship dead-on-arrival.
- Unit (Swift): the client method posts + decodes accept/refuse against a fake
  desktop; token joined at call time, never in the echoed result.
- Manual / device: deferred to HSM-13-04 (real session delivery).

## Notes / open questions

- Reuse, do not fork: route into the existing dictation runtime so the AI PI
  delivery path + the rich pipeline both apply (Decisions deferred, phase status).
  Do not build a second, thinner dictation path that skips the plugins.
- This story spans both roadmaps' code (a `holdspeak` Python route + the `apple`
  client). Keep the desktop route minimal and contract-clean; the richness comes
  from the pipeline it delegates to, not from this endpoint.
- Mirror the Phase-61 Slack-credential discipline for the token; mirror the
  actuator Propose→Approve posture for "never autonomous."
