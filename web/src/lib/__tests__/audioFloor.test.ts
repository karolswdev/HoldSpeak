// HS-112-06 — the browser's seat at the one audio floor.
//
// The open mic claims the SAME arbiter the hotkey, the meeting recorder
// and the wake listener claim, on a lease it heartbeats. A refusal names
// its owner so the room can render WHAT ("FLOOR HELD MEETING"); a lost
// heartbeat answers false rather than pretending the floor is still ours.
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));

vi.mock("../api", () => {
  class ApiError extends Error {
    constructor(
      public status: number,
      message: string,
      public payload: unknown = {},
    ) {
      super(message);
      this.name = "ApiError";
    }
  }
  return { ApiError, apiFetch: mocks.apiFetch };
});

import { ApiError } from "../api";
import {
  FLOOR_LEASE_SECONDS,
  FloorHeldError,
  claimAudioFloor,
  releaseAudioFloor,
  renewAudioFloor,
} from "../audioFloor";

beforeEach(() => {
  vi.clearAllMocks();
  mocks.apiFetch.mockResolvedValue({});
});

describe("the audio floor from the browser (HS-112-06)", () => {
  it("claims on a lease", async () => {
    await claimAudioFloor();
    expect(mocks.apiFetch).toHaveBeenCalledWith("/api/dictation/floor/claim", {
      method: "POST",
      json: { lease_seconds: FLOOR_LEASE_SECONDS },
    });
  });

  it("names the owner when the floor is held", async () => {
    mocks.apiFetch.mockRejectedValueOnce(
      new ApiError(409, "conflict", { owner: "meeting" }),
    );
    const refused = await claimAudioFloor().catch((error) => error);
    expect(refused).toBeInstanceOf(FloorHeldError);
    expect(refused.owner).toBe("meeting");
    // the room renders this verbatim: FLOOR HELD MEETING
    expect(refused.refusal).toBe("floor_held_meeting");
  });

  it("passes a non-floor failure through untouched", async () => {
    mocks.apiFetch.mockRejectedValueOnce(new Error("Failed to fetch"));
    await expect(claimAudioFloor()).rejects.toThrow(/Failed to fetch/);
  });

  it("heartbeats, and answers false the moment the floor is gone", async () => {
    expect(await renewAudioFloor()).toBe(true);
    mocks.apiFetch.mockRejectedValueOnce(
      new ApiError(409, "conflict", { owner: "meeting" }),
    );
    expect(await renewAudioFloor()).toBe(false);
  });

  it("releases, and a failed release is never fatal", async () => {
    await releaseAudioFloor();
    expect(mocks.apiFetch).toHaveBeenCalledWith("/api/dictation/floor/release", {
      method: "POST",
    });
    mocks.apiFetch.mockRejectedValueOnce(new Error("offline"));
    await expect(releaseAudioFloor()).resolves.toBeUndefined();
  });
});
