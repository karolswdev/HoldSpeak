import { beforeEach, describe, expect, it } from "vitest";
import {
  authenticatedHeaders,
  bootstrapAuth,
  websocketProtocols,
  websocketUrl,
} from "./auth";

describe("auth bootstrap", () => {
  beforeEach(() => {
    sessionStorage.clear();
    window.history.replaceState({}, "", "/dictation");
  });

  it("captures a query token for the tab and scrubs it from the visible URL", () => {
    window.history.replaceState(
      {},
      "",
      "/dictation?token=secret-value&tab=ready",
    );
    expect(bootstrapAuth()).toBe("secret-value");
    expect(window.location.search).toBe("?tab=ready");
    expect(sessionStorage.getItem("hs.web.token")).toBe("secret-value");
    expect(authenticatedHeaders().get("X-HoldSpeak-Token")).toBe(
      "secret-value",
    );
  });

  it("forwards the session token in a protocol header, never the URL", () => {
    sessionStorage.setItem("hs.web.token", "tab-token");
    bootstrapAuth();
    expect(websocketUrl()).not.toContain("tab-token");
    expect(websocketProtocols()).toEqual([
      "holdspeak.v1",
      "holdspeak.auth.v1.dGFiLXRva2Vu",
    ]);
  });
});
