import { afterEach, describe, expect, it, vi } from "vitest";
import { restoreWindowUndo, WindowUndoStale } from "../windowUndo";
import { ApiError } from "../../lib/api";
import recorded from "../compositor/__fixtures__/say_undo.json";

const apiFetch = vi.hoisted(() => vi.fn());
vi.mock("../../lib/api", async (original) => ({ ...await original<typeof import("../../lib/api")>(), apiFetch }));
afterEach(() => apiFetch.mockReset());

describe("window Undo uses the hub's atomic restore", () => {
  const undo = { group: "desk", ...recorded.undo.data.args };
  it("sends the captured state once", async () => {
    apiFetch.mockResolvedValue(recorded.restored);
    await restoreWindowUndo(undo);
    expect(apiFetch).toHaveBeenCalledExactlyOnceWith("/api/desk/windows/restore", { method: "POST", json: undo });
  });
  it("keeps the hub's stale refusal", async () => {
    apiFetch.mockRejectedValue(new ApiError(409, "window_stale", {}));
    await expect(restoreWindowUndo(undo)).rejects.toBeInstanceOf(WindowUndoStale);
    expect(apiFetch).toHaveBeenCalledTimes(1);
  });
});
