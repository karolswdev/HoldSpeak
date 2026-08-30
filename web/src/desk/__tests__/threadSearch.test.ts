// HS-151-07 — search result opening: thread hits open the pullout at
// the matched message (parse thread:<id>#<message_id>).
import { describe, expect, it, vi, beforeEach } from "vitest";

const mockOpenPrimitive = vi.fn();
const mockSetFocusMessage = vi.fn();

vi.mock("../shell", () => ({
  openPrimitive: (...args: unknown[]) => mockOpenPrimitive(...args),
  openSurfaceOr: vi.fn(),
}));

vi.mock("../threads", () => ({
  useThreadStore: {
    getState: () => ({
      setFocusMessage: mockSetFocusMessage,
    }),
  },
}));

import { openSourceRef } from "../surface/citations";

beforeEach(() => {
  mockOpenPrimitive.mockReset();
  mockSetFocusMessage.mockReset();
});

describe("thread search result opening", () => {
  it("opens a plain thread ref as a normal primitive", () => {
    openSourceRef("thread:abc123");
    expect(mockOpenPrimitive).toHaveBeenCalledWith("thread:abc123");
    expect(mockSetFocusMessage).not.toHaveBeenCalled();
  });

  it("parses thread:<id>#<message_id> and sets focus before opening", async () => {
    openSourceRef("thread:abc123#msg456");
    // setFocusMessage is called via dynamic import, so wait a tick
    await vi.waitFor(() => {
      expect(mockSetFocusMessage).toHaveBeenCalledWith("msg456");
    });
    expect(mockOpenPrimitive).toHaveBeenCalledWith("thread:abc123");
  });

  it("does not confuse a non-thread ref with a fragment", () => {
    openSourceRef("note:abc#123");
    expect(mockOpenPrimitive).toHaveBeenCalledWith("note:abc#123");
    expect(mockSetFocusMessage).not.toHaveBeenCalled();
  });
});
