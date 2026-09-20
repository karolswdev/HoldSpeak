import { describe, expect, it } from "vitest";
import { egressBadge, inboundBadge } from "./setup";

describe("egressBadge", () => {
  it("names the latest journal-backed actuator destination", () => {
    expect(
      egressBadge({
        trust: {
          last_egress: {
            id: "companion_webhook",
            name: "Custom webhook",
            receipt: "1785180327.4260201",
          },
        },
      }),
    ).toEqual({
      scope: "mixed",
      text: "→ Custom webhook",
      title: "Last receipted egress: 1785180327.4260201",
    });
  });
});

// HS-201-01 — the chrome chip and the Trust window state the same thing.
// The Trust window's lede is `All data stays on this device` while zero
// destinations are enabled (`components/TrustWindow.tsx:79-81`); the chip
// must not contradict it.
describe("egressBadge agrees with the Trust window", () => {
  it("stays on this device when no destination is enabled", () => {
    expect(
      egressBadge({
        trust: {
          web_bind: "127.0.0.1",
          auth_token_set: false,
          actuators_enabled: true,
          transcript_egress: "none",
          destinations: [
            { id: "companion_webhook", name: "Custom webhook", operation: "webhook",
              enabled: false, destination: "none", boundary: "device",
              data_class: "meeting", authority_basis: "owner",
              background_ability: "none", revoke_action: "disable" },
          ],
        },
      }).text,
    ).toBe("⌂ This device");
  });

  it("names external reach when a destination is enabled", () => {
    expect(
      egressBadge({
        trust: {
          web_bind: "127.0.0.1",
          auth_token_set: false,
          actuators_enabled: true,
          transcript_egress: "none",
          destinations: [
            { id: "companion_webhook", name: "Custom webhook", operation: "webhook",
              enabled: true, destination: "https://example.test", boundary: "network",
              data_class: "meeting", authority_basis: "owner",
              background_ability: "none", revoke_action: "disable" },
          ],
        },
      }).text,
    ).toBe("→ External reach enabled");
  });
});

// HS-201-01 (counsel fix round) — Astra finding 4: the inbound fact is
// its OWN token. Who may REACH this hub is not where data GOES, so the
// destination count never decides it and the egress chip never carries
// it.
describe("inboundBadge — the hub is open to the network", () => {
  const trust = (over: Record<string, unknown>) => ({
    trust: { transcript_egress: "none", destinations: [], ...over },
  });

  it("names the exposure when the hub binds off the loopback with no token", () => {
    expect(inboundBadge(trust({ web_bind: "0.0.0.0", auth_token_set: false }))?.text)
      .toBe("OPEN TO NETWORK");
  });

  it("stays silent on the loopback", () => {
    expect(inboundBadge(trust({ web_bind: "127.0.0.1", auth_token_set: false }))).toBeNull();
    expect(inboundBadge(trust({ web_bind: "localhost", auth_token_set: false }))).toBeNull();
    expect(inboundBadge(trust({ web_bind: "::1", auth_token_set: false }))).toBeNull();
  });

  it("stays silent when a token guards the off-loopback bind", () => {
    expect(inboundBadge(trust({ web_bind: "0.0.0.0", auth_token_set: true }))).toBeNull();
  });

  it("does not depend on the destinations, and the egress chip keeps its own answer", () => {
    const open = trust({
      web_bind: "192.168.1.43",
      auth_token_set: false,
      destinations: [
        { id: "companion_webhook", name: "Custom webhook", operation: "webhook",
          enabled: false, destination: "none", boundary: "device",
          data_class: "meeting", authority_basis: "owner",
          background_ability: "none", revoke_action: "disable" },
      ],
    });
    expect(inboundBadge(open)?.text).toBe("OPEN TO NETWORK");
    // the egress chip still states egress, and nothing leaves this device
    expect(egressBadge(open).text).toBe("\u2302 This device");
  });

  it("says nothing without a setup snapshot", () => {
    expect(inboundBadge(null)).toBeNull();
  });
});
