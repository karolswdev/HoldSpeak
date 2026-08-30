// HS-151-07 — one-time chat import: imports once, removes key, leaves key on failure.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const store = new Map<string, string>();
const mockAttempt = vi.fn();
const mockReceipt = "";

// Mock useWriteReceipt
vi.mock("../hooks/useWriteReceipt", () => ({
  useWriteReceipt: () => ({ attempt: mockAttempt, receipt: mockReceipt }),
}));

// Mock importThreads
const mockImportThreads = vi.fn();
vi.mock("../threads", () => ({
  importThreads: (...args: unknown[]) => mockImportThreads(...args),
}));

// We test the hook logic directly by importing after mocks are set up.
import { renderHook } from "@testing-library/react";
import { useChatImport } from "../hooks/useChatImport";

beforeEach(() => {
  store.clear();
  mockImportThreads.mockReset();
  mockAttempt.mockReset();
  vi.stubGlobal("localStorage", {
    getItem: (k: string) => store.get(k) ?? null,
    setItem: (k: string, v: string) => void store.set(k, v),
    removeItem: (k: string) => void store.delete(k),
    clear: () => store.clear(),
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("useChatImport", () => {
  it("does nothing when the key does not exist", () => {
    renderHook(() => useChatImport());
    expect(mockAttempt).not.toHaveBeenCalled();
  });

  it("calls attempt with import chats when the key exists", () => {
    store.set(
      "hs.desk.chats",
      JSON.stringify({
        scout: [{ id: "t1", role: "you", text: "hi" }],
      }),
    );

    // Mock attempt to capture the callback
    mockAttempt.mockImplementation(async (_label: string, fn: () => Promise<void>) => {
      await fn();
      return { ok: true };
    });
    mockImportThreads.mockResolvedValue({ imported: ["thread_1"] });

    renderHook(() => useChatImport());

    expect(mockAttempt).toHaveBeenCalledWith("import chats", expect.any(Function));
  });

  it("removes the localStorage key on success", async () => {
    store.set(
      "hs.desk.chats",
      JSON.stringify({
        scout: [{ id: "t1", role: "you", text: "hi" }],
      }),
    );

    mockImportThreads.mockResolvedValue({ imported: ["thread_1"] });
    mockAttempt.mockImplementation(async (_label: string, fn: () => Promise<void>) => {
      await fn();
      return { ok: true };
    });

    renderHook(() => useChatImport());

    // Wait for the async attempt to complete
    await vi.waitFor(() => {
      expect(store.has("hs.desk.chats")).toBe(false);
    });
  });

  it("leaves the key in place when import fails", async () => {
    store.set(
      "hs.desk.chats",
      JSON.stringify({
        scout: [{ id: "t1", role: "you", text: "hi" }],
      }),
    );

    mockImportThreads.mockRejectedValue(new Error("server error"));
    mockAttempt.mockImplementation(async (_label: string, fn: () => Promise<void>) => {
      await fn();
      return { ok: false };
    });

    renderHook(() => useChatImport());

    // The key should remain since importThreads threw
    await vi.waitFor(() => {
      expect(mockImportThreads).toHaveBeenCalled();
    });
    // The key stays because importThreads rejected before removeItem
    expect(store.has("hs.desk.chats")).toBe(true);
  });

  it("removes the key for an empty chat map", () => {
    store.set("hs.desk.chats", JSON.stringify({}));

    renderHook(() => useChatImport());

    // Empty map: no attempt needed, key cleaned up
    expect(mockAttempt).not.toHaveBeenCalled();
    expect(store.has("hs.desk.chats")).toBe(false);
  });

  it("does not run twice on rerender", () => {
    store.set(
      "hs.desk.chats",
      JSON.stringify({
        scout: [{ id: "t1", role: "you", text: "hi" }],
      }),
    );

    mockAttempt.mockResolvedValue({ ok: true });
    mockImportThreads.mockResolvedValue({ imported: ["thread_1"] });

    const { rerender } = renderHook(() => useChatImport());
    rerender();

    // attempt should be called only once despite the rerender
    expect(mockAttempt).toHaveBeenCalledTimes(1);
  });
});
