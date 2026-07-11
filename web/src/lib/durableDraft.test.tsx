import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import {
  durableDraftKey,
  readDurableDraft,
  useDurableDraft,
} from "./durableDraft";

describe("durable drafts", () => {
  beforeEach(() => localStorage.clear());

  it("writes synchronously and restores after a remount", () => {
    const first = renderHook(() => useDurableDraft("desk-ask"));
    act(() => first.result.current.setDraft("Words that must survive."));
    expect(readDurableDraft("desk-ask")?.text).toBe("Words that must survive.");
    first.unmount();

    const restored = renderHook(() => useDurableDraft("desk-ask"));
    expect(restored.result.current.value).toBe("Words that must survive.");
    expect(restored.result.current.recovered).toBe(true);
  });

  it("clears only the persisted copy while retaining the live editor value", () => {
    const draft = renderHook(() => useDurableDraft("first-words"));
    act(() => draft.result.current.setDraft("Now retained as a Note."));
    act(() => draft.result.current.clearPersisted());

    expect(localStorage.getItem(durableDraftKey("first-words"))).toBeNull();
    expect(draft.result.current.value).toBe("Now retained as a Note.");
  });
});
