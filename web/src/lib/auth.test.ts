import { beforeEach, describe, expect, it } from "vitest";
import { authenticatedHeaders, bootstrapAuth, websocketUrl } from "./auth";

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

  it("forwards the session token to the WebSocket handshake", () => {
    sessionStorage.setItem("hs.web.token", "tab-token");
    bootstrapAuth();
    expect(websocketUrl()).toContain("token=tab-token");
  });
});
