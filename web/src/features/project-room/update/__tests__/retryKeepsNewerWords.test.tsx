/** PHILO-13-04 fix round (Astra counsel P1): the Room's Try again sends the
 * CURRENT editor text and never replaces newer words. Before the fix the
 * stored callback was the failed render's `save`: it resent the old text,
 * wrote it back over the editor and cleared `dirty`. */
import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../../../lib/api";

const saveUpdate = vi.fn();
vi.mock("../api", () => ({
  saveUpdate: (...args: unknown[]) => saveUpdate(...args),
  fetchUpdates: vi.fn().mockResolvedValue([]),
}));

import { useUpdateController } from "../useUpdateController";
import type { ProjectUpdate } from "../model";

const draft = { id: "u1", lifecycle: "draft", bodyMd: "start", deliveries: [] } as unknown as ProjectUpdate;
const saved = (body: string) => ({ ...draft, bodyMd: body }) as ProjectUpdate;

beforeEach(() => saveUpdate.mockReset());

describe("Room Try again keeps his newer words", () => {
  it("Save fails, he types more, Try again sends the newer text and keeps it", async () => {
    const { result } = renderHook(() => useUpdateController("p1", () => {}));
    act(() => result.current.openUpdate(draft));
    act(() => result.current.handleEditBody("first edit"));
    saveUpdate.mockRejectedValueOnce(new ApiError(500, "injected", {}));
    await act(async () => { await result.current.save(); });
    expect(result.current.error).toBe("NOT SAVED · HUB FAILED");

    act(() => result.current.handleEditBody("first edit and newer words"));
    saveUpdate.mockImplementationOnce(async (_id: string, body: string) => saved(body));
    await act(async () => { result.current.retryFailed?.(); await Promise.resolve(); });

    expect(saveUpdate).toHaveBeenLastCalledWith("u1", "first edit and newer words");
    expect(result.current.editBody).toBe("first edit and newer words");
    expect(result.current.error).toBe("");
  });

  it("words typed while a save is in flight are never replaced by its answer", async () => {
    const { result } = renderHook(() => useUpdateController("p1", () => {}));
    act(() => result.current.openUpdate(draft));
    act(() => result.current.handleEditBody("sent text"));
    let answer!: (u: ProjectUpdate) => void;
    saveUpdate.mockImplementationOnce(() => new Promise((r) => { answer = r; }));
    let pending!: Promise<void>;
    act(() => { pending = result.current.save(); });
    act(() => result.current.handleEditBody("sent text plus more"));
    await act(async () => { answer(saved("sent text")); await pending; });
    expect(result.current.editBody).toBe("sent text plus more");
    expect(result.current.dirty).toBe(true);
  });
});
