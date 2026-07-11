import { describe, expect, it } from "vitest";
import { matchingDeviceSession, slotLabel } from "./targets.js";

describe("execution slot identity", () => {
  it("labels a React tablet slot as web, not native", () => {
    expect(slotLabel({
      target: "web_react",
      form_factor: "ipad_browser",
      label: "iPad browser",
      native: false,
    })).toBe("WEB · React · iPad browser");
  });

  it("requires target, form factor, and verified pairing for a native match", () => {
    const slot = { target: "ios_flagship_swift", form_factor: "ipad", native: true };
    const sessions = [
      { id: "wrong-app", target: "ios_companion_swift", form_factor: "ipad", pairing_verified: true },
      { id: "wrong-device", target: "ios_flagship_swift", form_factor: "iphone", pairing_verified: true },
      { id: "not-paired", target: "ios_flagship_swift", form_factor: "ipad", pairing_verified: false },
      { id: "match", execution_target: "ios_flagship_swift", form_factor: "ipad", pairing_verified: 1 },
    ];
    expect(matchingDeviceSession(slot, sessions)?.id).toBe("match");
  });
});
