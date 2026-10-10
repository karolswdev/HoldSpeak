import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  authToken,
  authenticatedHeaders,
  bootstrapAuth,
  websocketProtocols,
  websocketUrl,
} from "./auth";
import { ApiError, apiFetch, SIGN_IN_SENTENCE } from "./api";

describe("auth bootstrap", () => {
  beforeEach(() => {
    sessionStorage.clear();
    localStorage.clear();
    window.history.replaceState({}, "", "/dictation");
    bootstrapAuth();
  });
  afterEach(() => vi.unstubAllGlobals());

  it("captures a query token for the hub and scrubs it from the visible URL", () => {
    window.history.replaceState(
      {},
      "",
      "/dictation?token=secret-value&tab=ready",
    );
    expect(bootstrapAuth()).toBe("secret-value");
    expect(window.location.search).toBe("?tab=ready");
    expect(localStorage.getItem("hs.web.token")).toBe("secret-value");
    expect(authenticatedHeaders().get("X-HoldSpeak-Token")).toBe(
      "secret-value",
    );
  });

  it("keeps the token for a later page load with no token in the URL", () => {
    window.history.replaceState({}, "", "/?token=kept-token");
    bootstrapAuth();
    // A new tab, a bookmark, a browser restart: no query, new page state.
    window.history.replaceState({}, "", "/welcome");
    expect(bootstrapAuth()).toBe("kept-token");
    expect(authenticatedHeaders().get("X-HoldSpeak-Token")).toBe("kept-token");
  });

  it("moves an older tab-scoped token into the hub store once", () => {
    sessionStorage.setItem("hs.web.token", "old-tab-token");
    expect(bootstrapAuth()).toBe("old-tab-token");
    expect(localStorage.getItem("hs.web.token")).toBe("old-tab-token");
    expect(sessionStorage.getItem("hs.web.token")).toBeNull();
  });

  it("forwards the stored token in a protocol header, never the URL", () => {
    localStorage.setItem("hs.web.token", "tab-token");
    bootstrapAuth();
    expect(websocketUrl()).not.toContain("tab-token");
    expect(websocketProtocols()).toEqual([
      "holdspeak.v1",
      "holdspeak.auth.v1.dGFiLXRva2Vu",
    ]);
  });

  it("forgets a refused token and says the one sign-in sentence", async () => {
    window.history.replaceState({}, "", "/?token=rotated-token");
    bootstrapAuth();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ error: "principal_right_required" }), {
          status: 401,
          headers: { "content-type": "application/json" },
        }),
      ),
    );
    const error = await apiFetch("/api/meetings").catch((reason) => reason);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 401, message: SIGN_IN_SENTENCE });
    expect(authToken()).toBe("");
    expect(localStorage.getItem("hs.web.token")).toBeNull();
  });

  it("keeps the token on a refusal that is not a sign-in failure", async () => {
    window.history.replaceState({}, "", "/?token=good-token");
    bootstrapAuth();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ error: "principal_right_required" }), {
          status: 403,
          headers: { "content-type": "application/json" },
        }),
      ),
    );
    await apiFetch("/api/meetings").catch(() => undefined);
    expect(authToken()).toBe("good-token");
  });
});
