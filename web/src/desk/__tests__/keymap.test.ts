/** HS-111-07 — the ONE key binder: desk/keymap.ts walks the registry's
 * key fields; nothing else binds document keys. */
import { beforeEach, describe, expect, it, vi } from "vitest";
import { dispatchKey, matchKey, parseKey } from "../keymap";
import { useDesk } from "../store";
import { usePalette, useShortcutSheet } from "../chromeState";

const kd = (init: KeyboardEventInit) => new KeyboardEvent("keydown", init);

beforeEach(() => {
  usePalette.setState({ open: false });
  useShortcutSheet.setState({ open: false });
  useDesk.setState({
    createPrimitive: vi.fn().mockResolvedValue(undefined),
    openAsk: vi.fn(),
  });
});

describe("parseKey / matchKey (⌘-notation is the binding truth)", () => {
  it("parses the grammar's chords", () => {
    expect(parseKey("⌘K")).toEqual({ meta: true, ctrl: false, plain: false, key: "k" });
    expect(parseKey("⌘I")).toEqual({ meta: true, ctrl: false, plain: false, key: "i" });
    expect(parseKey("⌘1")).toEqual({ meta: true, ctrl: false, plain: false, key: "1" });
    expect(parseKey("⌃`")).toEqual({ meta: false, ctrl: true, plain: false, key: "`" });
    expect(parseKey("⌃↑")).toEqual({
      meta: false,
      ctrl: true,
      plain: false,
      key: "ArrowUp",
    });
    expect(parseKey("Esc")).toBeNull();
  });

  it("⌘ means the primary modifier (meta OR ctrl, never both)", () => {
    const spec = parseKey("⌘K")!;
    expect(matchKey(kd({ key: "k", metaKey: true }), spec)).toBe(true);
    expect(matchKey(kd({ key: "k", ctrlKey: true }), spec)).toBe(true);
    expect(matchKey(kd({ key: "k", metaKey: true, ctrlKey: true }), spec)).toBe(
      false,
    );
    expect(matchKey(kd({ key: "k" }), spec)).toBe(false);
  });
});

describe("dispatchKey runs registry verbs", () => {
  it("⌘K toggles the command deck (system.search)", () => {
    const ran = dispatchKey(kd({ key: "k", metaKey: true }));
    expect(ran?.id).toBe("system.search");
    expect(usePalette.getState().open).toBe(true);
  });

  it("⌘/ toggles the shortcut sheet (system.sheet)", () => {
    const ran = dispatchKey(kd({ key: "/", metaKey: true }));
    expect(ran?.id).toBe("system.sheet");
    expect(useShortcutSheet.getState().open).toBe(true);
  });

  it("⌘I opens Ask AI without a selection", () => {
    const ran = dispatchKey(kd({ key: "i", metaKey: true }));
    expect(ran?.id).toBe("go.ask");
    expect(useDesk.getState().openAsk).toHaveBeenCalledOnce();
  });

  it("⌘N creates a note and ⌘⇧N creates a decision", () => {
    expect(dispatchKey(kd({ key: "n", metaKey: true }))?.id).toBe(
      "desk.new-note",
    );
    expect(useDesk.getState().createPrimitive).toHaveBeenCalledWith("note");
    expect(
      dispatchKey(kd({ key: "N", metaKey: true, shiftKey: true }))?.id,
    ).toBe("desk.new-decision");
    expect(useDesk.getState().createPrimitive).toHaveBeenCalledWith("decision");
  });

  it("a ghosted verb refuses quietly (⌘W with no window open)", () => {
    expect(dispatchKey(kd({ key: "w", metaKey: true }))).toBeNull();
  });

  it("an unbound chord is nobody's verb", () => {
    expect(dispatchKey(kd({ key: "9", metaKey: true }))).toBeNull();
  });
});
