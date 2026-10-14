/** The 393 dock glass on main (ab43627c6): with the hub gone, every Desk read
 * rejects at once, in no fixed order, and the receipt named whichever read
 * rejected FIRST (READ ARTIFACTS, READ NOTES, ...), so "READ MEETINGS FAILED
 * · HUB UNREACHABLE" showed on some runs only. The receipt names the first
 * read in the Desk's own order, every time. The real `loadAll`; the hub
 * transport is the double. */
import { describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
vi.mock("../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../lib/api")>("../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});

import { loadAll } from "../api";
import { ApiError, SIGN_IN_SENTENCE } from "../../lib/api";

describe("loadAll with the hub unreachable", () => {
  it("names Meetings whatever read rejects first", async () => {
    for (let run = 0; run < 5; run += 1) {
      apiFetch.mockReset();
      // Meetings rejects LAST; every other read rejects at once.
      apiFetch.mockImplementation((path: string) => new Promise((_, reject) => {
        const delay = path.startsWith("/api/meetings") ? 30 : run;
        setTimeout(() => reject(new TypeError("Failed to fetch")), delay);
      }));
      const result = await loadAll();
      expect(result.failed?.label).toBe("Meetings");
      expect(result.error.startsWith("Meetings:")).toBe(true);
      expect(result.transientFailures).toMatchObject({ meeting: true, note: true, workbench: true });
    }
  });

  it("classifies each failed read without letting an earlier 503 mask a later 403", async () => {
    apiFetch.mockReset();
    apiFetch.mockImplementation((path: string) => {
      if (path.startsWith("/api/meetings")) return Promise.reject(new ApiError(503, "meetings unavailable", {}));
      if (path === "/api/decisions") return Promise.reject(new ApiError(403, "access refused", {}));
      if (path === "/api/workbenches") return Promise.reject(new Error("unknown read failure"));
      return Promise.resolve({});
    });

    const result = await loadAll();

    expect(result.transientFailures).toEqual({ meeting: true, workbench: true });
    expect(result.status).toMatchObject({ meeting: "unreachable", decision: "unreachable", workbench: "unreachable" });
    expect(result.failed?.label).toBe("Meetings");
    expect(result.error).toBe("Meetings: meetings unavailable");
  });

  it("does not classify a 401 as transient and keeps the sign-in error", async () => {
    apiFetch.mockReset();
    apiFetch.mockImplementation((path: string) => {
      if (path === "/api/decisions") return Promise.reject(new ApiError(401, SIGN_IN_SENTENCE, {}));
      return Promise.resolve({});
    });

    const result = await loadAll();

    expect(result.transientFailures).toEqual({});
    expect(result.status.decision).toBe("unreachable");
    expect(result.failed?.label).toBe("Decisions");
    expect(result.error).toBe(SIGN_IN_SENTENCE);
  });
});
