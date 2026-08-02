/** HS-111-07 — the ONE key binder: desk/keymap.ts walks the registry's
 * key fields; nothing else binds document keys. */
import { beforeEach, describe, expect, it } from "vitest";
import { dispatchKey, matchKey, parseKey } from "../keymap";
import { usePalette, useShortcutSheet } from "../chromeState";

const kd = (init: KeyboardEventInit) => new KeyboardEvent("keydown", init);

beforeEach(() => {
  usePalette.setState({ open: false });
  useShortcutSheet.setState({ open: false });
});

describe("parseKey / matchKey (⌘-notation is the binding truth)", () => {
  it("parses the grammar's chords", () => {
    expect(parseKey("⌘K")).toEqual({ meta: true, ctrl: false, key: "k" });
    expect(parseKey("⌘1")).toEqual({ meta: true, ctrl: false, key: "1" });
    expect(parseKey("⌃`")).toEqual({ meta: false, ctrl: true, key: "`" });
    expect(parseKey("⌃↑")).toEqual({
      meta: false,
      ctrl: true,
      key: "ArrowUp",
    });
    expect(parseKey("Esc")).toBeNull();
  });

  it("⌘ means the primary modifier (meta OR ctrl, never both)", () => {
    const spec = parseKey("⌘K")!;
    expect(matchKey(kd({ key: "k", metaKey: true }), spec)).toBe(true);
    expect(matchKey(kd({ key: "k", ctrlKey: true }), spec)).toBe(true);
    expect(
      matchKey(kd({ key: "k", metaKey: true, ctrlKey: true }), spec),
    ).toBe(false);
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

  it("a ghosted verb refuses quietly (⌘W with no window open)", () => {
    expect(dispatchKey(kd({ key: "w", metaKey: true }))).toBeNull();
  });

  it("an unbound chord is nobody's verb", () => {
    expect(dispatchKey(kd({ key: "9", metaKey: true }))).toBeNull();
  });
});
