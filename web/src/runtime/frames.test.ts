// The web mirror of the hub's frame vocabulary (holdspeak/realtime_frames.py).
// tests/unit/test_realtime_frame_registry.py diffs the two names lists; this
// pins what the web reads off it: the Programs frame (2026-10-28) is a frame
// type, and the list stays sorted with no name twice.
import { describe, expect, it } from "vitest";
import { RUNTIME_FRAME_TYPES, isRuntimeFrameType } from "./frames";

describe("the runtime frame mirror", () => {
  it("knows the Programs frame", () => {
    expect(isRuntimeFrameType("program_changed")).toBe(true);
    expect(isRuntimeFrameType("program_moved")).toBe(false);
  });

  it("names each frame once", () => {
    expect(new Set(RUNTIME_FRAME_TYPES).size).toBe(RUNTIME_FRAME_TYPES.length);
  });
});
