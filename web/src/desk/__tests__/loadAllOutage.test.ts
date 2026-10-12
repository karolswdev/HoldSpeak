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
    }
  });
});
