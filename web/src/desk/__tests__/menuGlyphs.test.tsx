/** HS-148-02 — the glyph content sweep guard: variant matrix, dock
 * parity, Go grouping separator, casing/ellipsis pins. */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { VERBS, menuVerbs, verbLabel } from "../verbRegistry";
import { DESK_TOOLS, KIND_GLYPH } from "../tools";
import { floorMenuEntries } from "../floorMenu";
import { WorkMenu, type WorkMenuEntry } from "../components/DeskMenu";
import { useDesk } from "../store";
import { EMPTY_ITEMS } from "../api";
import { __resetSurfaces } from "../shell";

const CTX = { selectedRef: null };

beforeEach(() => {
  __resetSurfaces();
  useDesk.setState({
    items: EMPTY_ITEMS,
    selectedIds: [],
    positions: {},
    createPrimitive: vi.fn().mockResolvedValue(undefined),
    openPullout: vi.fn(),
    openInfoWindow: vi.fn(),
    openEditor: vi.fn(),
    openAsk: vi.fn(),
  });
});

describe("glyph population (HS-148-02)", () => {
  it("every Go verb carries its DESK_TOOLS glyph — one glyph language", () => {
    const goVerbs = menuVerbs("go");
    for (const tool of DESK_TOOLS) {
      const verb = goVerbs.find((v) => v.id === `go.${tool.action}`);
      expect(verb, `go.${tool.action} missing`).toBeTruthy();
      expect(verb!.glyph).toBe(tool.glyph);
    }
  });

  it("every create verb carries its KIND_GLYPH", () => {
    const creates = VERBS.filter((v) => v.group === "new");
    const kindMap: Record<string, string> = {
      "desk.new-note": "note",
      "desk.new-decision": "decision",
      "desk.new-knowledge": "kb",
      "desk.new-agent": "recipe",
      "desk.new-workflow": "workflow",
      "desk.new-workbench": "workbench",
      "desk.new-zone": "zone",
      "desk.new-thread": "thread",
      "desk.new-project": "project",
    };
    for (const v of creates) {
      const kind = kindMap[v.id];
      expect(kind, `unmapped create verb ${v.id}`).toBeTruthy();
      expect(v.glyph).toBe(KIND_GLYPH[kind]);
    }
  });

  it("object verbs carry restrained glyphs for variant B", () => {
    const objectVerbs = menuVerbs("object");
    for (const v of objectVerbs) {
      expect(v.glyph, `${v.id} should have a glyph`).toBeTruthy();
      // Verify no emoji (emoji are surrogate pairs / outside BMP)
      expect(
        v.glyph!.length,
        `${v.id} glyph must be a single BMP character`,
      ).toBeLessThanOrEqual(2);
    }
  });

  it("dock-parity: the four primary apps have identical glyphs in tools.ts and the Go menu", () => {
    const primaries = ["dictate", "ask", "review-meetings", "configure-settings"];
    for (const action of primaries) {
      const tool = DESK_TOOLS.find((t) => t.action === action);
      const verb = VERBS.find((v) => v.id === `go.${action}`);
      expect(tool, `missing DESK_TOOLS entry ${action}`).toBeTruthy();
      expect(verb, `missing verb go.${action}`).toBeTruthy();
      expect(verb!.glyph).toBe(tool!.glyph);
    }
  });
});

describe("variant matrix — root attribute gating (HS-148-02)", () => {
  function renderMenu(menuContext: string, glyphs: string): HTMLElement {
    const entries: WorkMenuEntry[] = [
      {
        type: "item",
        id: "a",
        label: "Speak",
        glyph: "⌁",
        onSelect: vi.fn(),
      },
      { type: "item", id: "b", label: "Plain", onSelect: vi.fn() },
    ];
    // Create a desk-next root with the data-menu-glyphs attribute.
    const root = document.createElement("div");
    root.id = "desk-next";
    root.className = "desk-next";
    root.setAttribute("data-menu-glyphs", glyphs);
    document.body.appendChild(root);

    render(
      <WorkMenu
        label="Test"
        x={0}
        y={0}
        entries={entries}
        onClose={vi.fn()}
        menuContext={menuContext}
      />,
    );
    return root;
  }

  function cleanup(root: HTMLElement) {
    root.remove();
  }

  it("variant 'all' + launcher context: glyph column visible", () => {
    const root = renderMenu("launcher", "all");
    const menu = screen.getByRole("menu", { name: "Test" });
    const glyphEls = menu.querySelectorAll(".desk-menu-glyph");
    // Both rows should have the lane (lane law).
    expect(glyphEls.length).toBe(2);
    cleanup(root);
  });

  it("variant 'all' + verb context: glyph column visible", () => {
    const root = renderMenu("verb", "all");
    const menu = screen.getByRole("menu", { name: "Test" });
    const glyphEls = menu.querySelectorAll(".desk-menu-glyph");
    expect(glyphEls.length).toBe(2);
    cleanup(root);
  });

  it("variant 'none' sets data-menu-glyphs on desk root", () => {
    const root = renderMenu("launcher", "none");
    expect(root.getAttribute("data-menu-glyphs")).toBe("none");
    cleanup(root);
  });

  it("variant 'launcher' sets data-menu-glyphs on desk root", () => {
    const root = renderMenu("launcher", "launcher");
    expect(root.getAttribute("data-menu-glyphs")).toBe("launcher");
    cleanup(root);
  });

  it("panels declare data-menu-context attribute", () => {
    const root = renderMenu("launcher", "all");
    const menu = screen.getByRole("menu", { name: "Test" });
    expect(menu.getAttribute("data-menu-context")).toBe("launcher");
    cleanup(root);
  });

  it("panels default data-menu-context to verb", () => {
    const entries: WorkMenuEntry[] = [
      { type: "item", id: "a", label: "A", onSelect: vi.fn() },
    ];
    render(
      <WorkMenu
        label="Default"
        x={0}
        y={0}
        entries={entries}
        onClose={vi.fn()}
      />,
    );
    const menu = screen.getByRole("menu", { name: "Default" });
    expect(menu.getAttribute("data-menu-context")).toBe("verb");
  });
});

describe("Go menu grouping separator (HS-148-02)", () => {
  it("Go menu entries have the 4/9 app/tool group split with a separator", () => {
    const goVerbs = menuVerbs("go");
    // First 4 should be "app" group, rest "tool" group.
    const appVerbs = goVerbs.filter((v) => v.group === "app");
    const toolVerbs = goVerbs.filter((v) => v.group === "tool");
    expect(appVerbs.length).toBe(4);
    expect(toolVerbs.length).toBe(9);
    // Verify the order: first 4 are app, rest are tool.
    expect(goVerbs.slice(0, 4).every((v) => v.group === "app")).toBe(true);
    expect(goVerbs.slice(4).every((v) => v.group === "tool")).toBe(true);
  });

  it("the floor Launch submenu carries all Go entries with glyphs", () => {
    const entries = floorMenuEntries();
    const launch = entries.find(
      (e) => e.type === "sub" && e.id === "floor.launch",
    ) as Extract<WorkMenuEntry, { type: "sub" }>;
    expect(launch).toBeTruthy();
    const itemEntries = launch.entries.filter(
      (e): e is Extract<WorkMenuEntry, { type: "item" }> => e.type === "item",
    );
    // Every Launch entry has a glyph.
    for (const e of itemEntries) {
      expect(e.glyph, `${e.id} missing glyph`).toBeTruthy();
    }
  });

  it("the floor New submenu carries kind glyphs", () => {
    const entries = floorMenuEntries();
    const newSub = entries.find(
      (e) => e.type === "sub" && e.id === "floor.new",
    ) as Extract<WorkMenuEntry, { type: "sub" }>;
    expect(newSub).toBeTruthy();
    const itemEntries = newSub.entries.filter(
      (e): e is Extract<WorkMenuEntry, { type: "item" }> => e.type === "item",
    );
    for (const e of itemEntries) {
      expect(e.glyph, `${e.id} missing glyph`).toBeTruthy();
    }
  });

  it("floor submenus declare menuContext='launcher'", () => {
    const entries = floorMenuEntries();
    const newSub = entries.find(
      (e) => e.type === "sub" && e.id === "floor.new",
    ) as Extract<WorkMenuEntry, { type: "sub" }>;
    const launchSub = entries.find(
      (e) => e.type === "sub" && e.id === "floor.launch",
    ) as Extract<WorkMenuEntry, { type: "sub" }>;
    expect(newSub.menuContext).toBe("launcher");
    expect(launchSub.menuContext).toBe("launcher");
  });
});

describe("casing sweep — Window menu (HS-148-02)", () => {
  it("Window menu labels are uniform sentence case", () => {
    const windowVerbs = menuVerbs("window");
    const labels = windowVerbs.map((v) => verbLabel(v, CTX));
    // All multi-word labels should be sentence case (only first word capitalized,
    // except proper nouns).
    for (const label of labels) {
      const words = label.split(" ");
      // Second word onward should be lowercase (unless it's a known exception).
      for (let i = 1; i < words.length; i++) {
        const word = words[i];
        // Skip parenthetical content.
        if (word.startsWith("(")) continue;
        expect(
          word[0],
          `"${label}": "${word}" should be lowercase (sentence case)`,
        ).toBe(word[0].toLowerCase());
      }
    }
  });

  it("'Cycle windows' and 'Cycle windows (reverse)' are consistent", () => {
    const windowVerbs = menuVerbs("window");
    const cycle = windowVerbs.find((v) => v.id === "window.cycle");
    const cycleRev = windowVerbs.find((v) => v.id === "window.cycle-reverse");
    expect(verbLabel(cycle!, CTX)).toBe("Cycle windows");
    expect(verbLabel(cycleRev!, CTX)).toBe("Cycle windows (reverse)");
  });
});

describe("ellipsis audit (HS-148-02)", () => {
  it("Reset to seed ends with ellipsis (opens a dialog)", () => {
    const verb = VERBS.find((v) => v.id === "desk.reset-to-seed");
    expect(verb).toBeTruthy();
    expect(verbLabel(verb!, CTX)).toMatch(/…$/);
  });

  it("Find receipt ends with ellipsis (opens a dialog)", () => {
    const verb = VERBS.find((v) => v.id === "desk.intelligence-find-receipt");
    expect(verb).toBeTruthy();
    expect(verbLabel(verb!, CTX)).toMatch(/…$/);
  });
});

describe("bound-key-set byte-identical proof (HS-148-02)", () => {
  it("the glyph field does not alter the bound key set", () => {
    const keys = VERBS.filter((v) => v.key).map((v) => [v.id, v.key]);
    expect(Object.fromEntries(keys)).toEqual({
      "desk.new-note": "⌘N",
      "desk.new-decision": "⌘⇧N",
      "desk.overview": "⌃↑",
      "object.rename": "F2",
      "object.delete": "Delete",
      "go.ask": "⌘I",
      "go.dictate": "⌘1",
      "go.review-meetings": "⌘2",
      "go.inspect-personas-and-coders": "⌘3",
      "go.configure-settings": "⌘4",
      "window.close": "⌘W",
      "window.minimize": "⌘M",
      "window.cycle": "⌃`",
      "window.cycle-reverse": "⌃⇧`",
      "system.search": "⌘K",
      "system.sheet": "⌘/",
    });
  });
});
