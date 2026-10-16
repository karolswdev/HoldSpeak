import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch } from "../../lib/api";
import { useGate } from "../gate";

vi.mock("../../lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../lib/api")>()),
  apiFetch: vi.fn(),
}));

const api = vi.mocked(apiFetch);
beforeEach(() => {
  api.mockReset();
  useGate.setState({ held: [], loaded: false, error: null });
});

describe("gate decision outcomes", () => {
  it("reads authoritative held proposals after an accepted decision", async () => {
    api.mockResolvedValueOnce({ state: "approved" }).mockResolvedValueOnce({ proposals: [] });
    await expect(useGate.getState().decide("call/1", "approved")).resolves.toBeUndefined();
    expect(api).toHaveBeenNthCalledWith(1, "/api/gate/proposals/call%2F1/decide", {
      method: "POST", json: { decision: "approved", reason: undefined, actor: "owner" },
    });
    expect(api).toHaveBeenNthCalledWith(2, "/api/gate/proposals?state=held");
    expect(useGate.getState()).toMatchObject({ held: [], loaded: true, error: null });
  });

  it("treats only the named already-decided 409 as a race and rereads truth", async () => {
    api.mockRejectedValueOnce(new ApiError(409, "already_decided", { error: "already_decided", state: "denied" }))
      .mockResolvedValueOnce({ proposals: [] });
    await expect(useGate.getState().decide("call1", "approved")).resolves.toBeUndefined();
    expect(api).toHaveBeenCalledTimes(2);
    expect(useGate.getState().held).toEqual([]);
  });

  it.each([
    new ApiError(409, "proposal_not_kernel_admitted", { error: "proposal_not_kernel_admitted" }),
    new ApiError(503, "Unavailable", { error: "Unavailable" }),
    new TypeError("Failed to fetch"),
  ])("rejects the actual refusal %s after an authoritative read", async (failure) => {
    api.mockRejectedValueOnce(failure).mockResolvedValueOnce({ proposals: [{ id: "call1", state: "held" }] });
    await expect(useGate.getState().decide("call1", "denied", "  Outside the worktree  ")).rejects.toBe(failure);
    expect(useGate.getState().held[0]).toMatchObject({ id: "call1", state: "held" });
    expect(api.mock.calls[0][1]?.json).toMatchObject({ reason: "Outside the worktree" });
  });

  it.each([false, true])("keeps a failed read separate from the settled decision, race=%s", async (race) => {
    if (race) api.mockRejectedValueOnce(new ApiError(409, "already_decided", { error: "already_decided" }));
    else api.mockResolvedValueOnce({ state: "approved" });
    api.mockRejectedValueOnce(new Error("Read unavailable"));
    await expect(useGate.getState().decide("call1", "approved")).resolves.toBeUndefined();
    expect(useGate.getState().error).toBe("Read unavailable");
    api.mockResolvedValueOnce({ proposals: [] });
    await useGate.getState().refresh();
    expect(api.mock.calls.filter(([, opts]) => opts?.method === "POST")).toHaveLength(1);
    expect(useGate.getState().error).toBeNull();
  });
});
