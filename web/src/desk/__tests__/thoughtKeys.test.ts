/* The keys typed between `Write a thought` and the Thought window are kept
 * (inventory 2026-10-03, A-apps row 31: "keys typed in the gap are lost").
 * The glass fence is tests/e2e/test_thought_opens_at_once_glass.py; this
 * holds the rule's edges. */
import { afterEach, describe, expect, it, vi } from "vitest";
import { claimThoughtKeys, sendThoughtKeysTo, startThoughtKeys, stopThoughtKeys } from "../thoughtKeys";

const key = (k: string, init: KeyboardEventInit = {}) => {
  const event = new KeyboardEvent("keydown", { key: k, bubbles: true, cancelable: true, ...init });
  document.body.dispatchEvent(event);
  return event;
};

describe("the keys of the gap", () => {
  afterEach(() => { stopThoughtKeys(); document.body.innerHTML = ""; });

  it("gives the field every key, in order, when the window loads after the keys", () => {
    startThoughtKeys();
    for (const k of ["A", "s", "k", "x", "Backspace", " ", "P", "Enter"]) expect(key(k).defaultPrevented).toBe(true);
    sendThoughtKeysTo("note_1");
    const take = vi.fn();
    claimThoughtKeys("note_1", take);
    expect(take).toHaveBeenCalledWith("Ask P\n");
    // The field has the cursor now: the next key is its own.
    expect(key("z").defaultPrevented).toBe(false);
  });

  it("gives an open window's field the keys at once", () => {
    const take = vi.fn();
    const release = claimThoughtKeys("note_2", take);
    startThoughtKeys();
    key("h"); key("i");
    sendThoughtKeysTo("note_2");
    expect(take).toHaveBeenCalledWith("hi");
    release();
  });

  it("leaves a key with ⌘, ⌃ or ⌥ to the desk", () => {
    startThoughtKeys();
    expect(key("k", { metaKey: true }).defaultPrevented).toBe(false);
    expect(key("t", { ctrlKey: true }).defaultPrevented).toBe(false);
    sendThoughtKeysTo("note_3");
    const take = vi.fn();
    claimThoughtKeys("note_3", take);
    expect(take).toHaveBeenCalledWith("");
  });

  it("stops when the owner types in another field", () => {
    const input = document.createElement("input");
    document.body.append(input);
    startThoughtKeys();
    key("a");
    const typed = new KeyboardEvent("keydown", { key: "b", bubbles: true, cancelable: true });
    input.dispatchEvent(typed);
    expect(typed.defaultPrevented).toBe(false);
    const take = vi.fn();
    claimThoughtKeys("note_4", take);
    sendThoughtKeysTo("note_4");
    expect(take).not.toHaveBeenCalled();
  });
});
