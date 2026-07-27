import { describe, expect, it } from "vitest";
import { egressBadge } from "./setup";

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
