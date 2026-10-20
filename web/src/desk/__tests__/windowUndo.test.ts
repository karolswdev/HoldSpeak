import { afterEach, describe, expect, it, vi } from "vitest";
import { restoreWindowUndo, WindowUndoStale } from "../windowUndo";
import type { WindowUndo } from "../used";

const apiFetch = vi.hoisted(() => vi.fn());
vi.mock("../../lib/api", () => ({ apiFetch }));

afterEach(() => {
  apiFetch.mockReset();
});

const row = (id: string, revision: number, geometry: Record<string, string>) => ({
  id,
  revision,
  ...geometry,
});

describe("S9 window Wrote Undo", () => {
  it("closes model-opened registry windows at their captured revisions", async () => {
    const undo: WindowUndo = {
      group: "ask:s9",
      windows: [
        {
          id: "surface-people",
          before: null,
          after: { id: "surface-people", object_ref: "people:rel-mira:prep", revision: 7 },
        },
        {
          id: "surface-meetings",
          before: null,
          after: { id: "surface-meetings", object_ref: "meeting:platform-sync?view=review", revision: 8 },
        },
      ],
    };
    apiFetch.mockImplementation(async (input: string, init: RequestInit = {}) => {
      if (input === "/api/desk/windows") {
        return { windows: [
          row("surface-people", 7, { x: "-1/2", y: "-1/2", w: "1/2", h: "100%" }),
          row("surface-meetings", 8, { x: "0%", y: "-1/2", w: "1/2", h: "100%" }),
        ] };
      }
      expect(init.method).toBe("POST");
      expect((init as RequestInit & { json?: unknown }).json).toMatchObject({
        expected_revision: input.includes("surface-people") ? 7 : 8,
      });
      return { id: input.includes("surface-people") ? "surface-people" : "surface-meetings", closed: true, revision: 9 };
    });

    await restoreWindowUndo(undo);

    expect(apiFetch).toHaveBeenCalledTimes(3);
    expect(apiFetch.mock.calls[1][0]).toContain("surface-people/close");
    expect(apiFetch.mock.calls[2][0]).toContain("surface-meetings/close");
  });

  it("keeps a newer owner move and sends no stale restore write", async () => {
    const undo: WindowUndo = {
      group: "ask:s9",
      windows: [{
        id: "surface-people",
        before: {
          id: "surface-people",
          geometry: { x: "10%", y: "10%", w: "40%", h: "80%" },
          revision: 2,
        },
        after: {
          id: "surface-people",
          geometry: { x: "-1/2", y: "-1/2", w: "1/2", h: "100%" },
          revision: 7,
        },
      }],
    };
    apiFetch.mockResolvedValue({ windows: [row("surface-people", 9, {
      x: "25%", y: "20%", w: "50%", h: "70%",
    })] });

    await expect(restoreWindowUndo(undo)).rejects.toBeInstanceOf(WindowUndoStale);
    expect(apiFetch).toHaveBeenCalledTimes(1);
    expect(apiFetch.mock.calls[0][0]).toBe("/api/desk/windows");
  });
});
