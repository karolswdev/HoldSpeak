/* HS-202-02 job 3 — `Write a thought` opens a note, and keeping one is
 * confirmed.
 *
 * 04-sober-eye.md Job 3 (PARTLY) and ranks 3 and 5:
 *  - "There is a button on the Desk labelled **Write a thought**. I clicked
 *    it. It does not open a place to write a thought. It opens the **Speak**
 *    window, which is a dictation-routing console"; the real door was
 *    `Desk → New Note`, nine moves away.
 *  - "**And nothing happened on screen.** No toast, no note object on the
 *    Desk … I only know it worked because I asked the API."
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { keptReceipt } from "../keptReceipt";

const apiFetch = vi.fn();
const adoptThought = vi.fn();
const thoughtForNote = vi.fn();
const openPullout = vi.fn();
const refresh = vi.fn(async () => undefined);

vi.mock("../../lib/api", () => ({
  apiFetch: (...args: unknown[]) => apiFetch(...args),
  readableError: (e: unknown) => String(e),
}));
vi.mock("../thoughts", () => ({
  adoptThought: (...args: unknown[]) => adoptThought(...args),
  thoughtForNote: (...args: unknown[]) => thoughtForNote(...args),
}));
vi.mock("../store", () => ({
  useDesk: Object.assign(() => undefined, {
    getState: () => ({ openPullout, refresh }),
  }),
}));

describe("Write a thought opens a note in the Thought window", () => {
  beforeEach(() => {
    apiFetch.mockReset();
    adoptThought.mockReset();
    thoughtForNote.mockReset();
    openPullout.mockReset();
  });

  it("mints a note, adopts it as a Thought, and opens it", async () => {
    apiFetch.mockResolvedValue({ note: { id: "note_1" } });
    thoughtForNote.mockResolvedValue({
      ownership: "ordinary",
      note: { id: "note_1" },
      source_precondition: { content_sha256: "abc", last_modified: "t0" },
    });
    adoptThought.mockResolvedValue({ thought: { id: "th_1" }, default_context_receipt: {} });
    const { openNewThought } = await import("../newThought");

    await openNewThought();

    expect(apiFetch).toHaveBeenCalledWith(
      "/api/notes",
      expect.objectContaining({ method: "POST" }),
    );
    expect(adoptThought).toHaveBeenCalledWith(
      expect.objectContaining({ note_id: "note_1" }),
    );
    expect(openPullout).toHaveBeenCalledWith("note:note_1");
  });

  it("never opens the dictation router", async () => {
    const source = await import("../chair/ChairHome.tsx?raw");
    const chair = source.default as string;
    const verb = chair.slice(
      chair.indexOf('data-testid="arrival-develop-thought"') - 400,
      chair.indexOf('data-testid="arrival-develop-thought"') + 80,
    );
    expect(verb).not.toMatch(/openSurfaceOr\("dictate"/);
    expect(verb).toMatch(/openNewThought/);
  });

  it("still opens the note when the adoption is refused", async () => {
    apiFetch.mockResolvedValue({ note: { id: "note_2" } });
    thoughtForNote.mockRejectedValue(new Error("offline"));
    const { openNewThought } = await import("../newThought");

    await openNewThought();

    expect(openPullout).toHaveBeenCalledWith("note:note_2");
  });
});

describe("keeping a note is confirmed (HS-202-02)", () => {
  it("states the time it was kept", () => {
    const at = new Date("2026-09-20T15:41:00").getTime();
    expect(keptReceipt(at)).toMatch(/^Kept · /);
    expect(keptReceipt(at)).toMatch(/\d/);
  });

  it("says nothing before the first keep", () => {
    expect(keptReceipt(undefined)).toBeNull();
    expect(keptReceipt(0)).toBeNull();
  });
});
