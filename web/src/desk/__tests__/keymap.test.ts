/** HS-111-07 — the ONE key binder: desk/keymap.ts walks the registry's
 * key fields; nothing else binds document keys. */
import { beforeEach, describe, expect, it, vi } from "vitest";
import { dispatchKey, matchKey, parseKey } from "../keymap";
import { useDesk } from "../store";
import { VERBS } from "../verbRegistry";
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
    // PHILO-16: Esc is a plain key now (Window ▸ Back); ⌥ and the arrows parse.
    expect(parseKey("Esc")).toEqual({ meta: false, ctrl: false, plain: true, key: "escape" });
    expect(parseKey("⌘⌥←")).toEqual({ meta: true, ctrl: false, plain: false, alt: true, key: "ArrowLeft" });
    expect(parseKey("⌘⏎")).toEqual({ meta: true, ctrl: false, plain: false, key: "Enter" });
    expect(parseKey("⌘⇧`")).toEqual({ meta: true, ctrl: false, plain: false, shift: true, key: "`" });
  });

  it("⌃⇧` stays the reverse cycle; ⌘⇧` is To back (Astra M5)", () => {
    // Every verb runnable and silent: the test asks which verb the key reaches.
    const spies = VERBS.flatMap((v) => [
      vi.spyOn(v, "ghost").mockReturnValue(null),
      vi.spyOn(v, "run").mockImplementation(() => {}),
    ]);
    const run = (init: KeyboardEventInit) =>
      dispatchKey(new KeyboardEvent("keydown", { key: "`", code: "Backquote", cancelable: true, ...init }))?.id;
    expect(run({ ctrlKey: true, shiftKey: true })).toBe("window.cycle-reverse");
    expect(run({ metaKey: true, shiftKey: true })).toBe("window.depth");
    // "~" is what most layouts report for ⇧`: the key code binds it.
    expect(run({ ctrlKey: true, shiftKey: true, key: "~" })).toBe("window.cycle-reverse");
    expect(run({ ctrlKey: true })).toBe("window.cycle");
    expect(run({ metaKey: true })).toBe("window.cycle");
    for (const spy of spies) spy.mockRestore();
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

  it("PHILO-17 U27: the menus show ⌃ keys a browser tab receives; the ⌘ keys stay bound", () => {
    const shown = (id: string) => VERBS.find((v) => v.id === id)?.key;
    expect(shown("window.close")).toBe("⌃W");
    expect(shown("window.minimize")).toBe("⌃M");
    expect(shown("desk.new-note")).toBe("⌃N");
    expect(shown("desk.new-decision")).toBe("⌃⇧N");
    expect(shown("go.dictate")).toBe("⌃1");
    expect(shown("go.configure-settings")).toBe("⌃4");
    // No menu shows a key Chrome or Safari keeps for the tab.
    const kept = new Set(["⌘W", "⌘N", "⌘⇧N", "⌘M", "⌘1", "⌘2", "⌘3", "⌘4"]);
    expect(VERBS.filter((v) => v.key && kept.has(v.key)).map((v) => v.id)).toEqual([]);
    // The old ⌘ keys stay bound where a browser passes them (never shown).
    expect(VERBS.find((v) => v.id === "window.close")?.altKeys).toEqual(["⌘W"]);
    expect(VERBS.find((v) => v.id === "go.dictate")?.altKeys).toEqual(["⌘1"]);
    // ⌃N and ⌃⇧N run New Note and New Decision; ⌃M is Iconify, not Zoom.
    expect(dispatchKey(kd({ key: "n", ctrlKey: true }))?.id).toBe("desk.new-note");
    expect(dispatchKey(kd({ key: "N", ctrlKey: true, shiftKey: true }))?.id).toBe("desk.new-decision");
    const iconify = VERBS.find((v) => v.id === "window.minimize")!;
    expect(matchKey(kd({ key: "m", ctrlKey: true }), parseKey(iconify.key!)!)).toBe(true);
    expect(VERBS.find((v) => v.id === "window.maximize")?.altKeys ?? []).not.toContain("⌃M");
    // In a field ⌃N is the field's key (next line), never a new note.
    const field = document.createElement("textarea");
    document.body.append(field);
    const typed = new KeyboardEvent("keydown", { key: "n", ctrlKey: true, bubbles: true });
    Object.defineProperty(typed, "target", { value: field });
    expect(dispatchKey(typed)).toBeNull();
    field.remove();
  });

  it("a ghosted verb refuses quietly (⌘W with no window open)", () => {
    expect(dispatchKey(kd({ key: "w", metaKey: true }))).toBeNull();
  });

  it("an unbound chord is nobody's verb", () => {
    expect(dispatchKey(kd({ key: "9", metaKey: true }))).toBeNull();
  });
});
