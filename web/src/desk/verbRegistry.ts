/** HS-105-05 - the ONE verb registry (the ARexx rule, scoped honestly):
 * a verb is a REGISTERED capability, and every face renders the same
 * registry. HS-111-07 (v2): the five parallel verb lists are gone -
 * the menubar, the mark menu, the Create menu, the floor and object
 * context menus, and the ⌘K command deck ALL derive from here, and
 * `desk/keymap.ts` is the ONLY key binder, driven by the `key` fields
 * below. The wire face deliberately WAITS for the kernel's userland
 * dispatch (invoking store verbs over HTTP without the broker's
 * consent model would widen authority - Article V).
 *
 * Ghosting over hiding: a verb that cannot run now stays visible with
 * its reason - the system admits what it can do. */
import { defaultViewFor, useDesk } from "./store";
import { openSurfaceOr } from "./shell";
import { objectByRef } from "./world";
import { DESK_TOOLS } from "./tools";
import { usePalette, useShortcutSheet } from "./chromeState";
import {
  closeFrontWindow,
  cycleWindows,
  focusOrRestoreApp,
  minimizeFrontWindow,
  openWindowCount,
  toggleExpose,
} from "./components/DeskWindow";

export type MenuId = "desk" | "object" | "go";
export type VerbScope = "floor" | "object" | "go" | "window" | "system";

export interface VerbContext {
  /** The single selected object ref, when exactly one is selected. */
  selectedRef: string | null;
}

export interface Verb {
  id: string;
  /** A function label names the verb honestly for the CURRENT state
   * (the view toggle names the OTHER view). */
  label: string | ((ctx: VerbContext) => string);
  /** Menubar placement; a verb without one has no menubar face. */
  menu?: MenuId;
  scope: VerbScope;
  /** Separator grouping inside a menu face. */
  group?: string;
  /** ⌘-notation shortcut - BOUND by desk/keymap.ts (the one binder). */
  key?: string;
  /** false hides the verb from the ⌘K deck (default: shown). */
  palette?: boolean;
  /** Extra ⌘K match terms. */
  keywords?: string[];
  /** null = runnable; a string = ghosted WITH that reason. */
  ghost(ctx: VerbContext): string | null;
  run(ctx: VerbContext): void;
}

export function verbLabel(v: Verb, ctx: VerbContext): string {
  return typeof v.label === "function" ? v.label(ctx) : v.label;
}

const EDITABLE = new Set(["note", "kb", "recipe", "workflow"]);

function selected(ctx: VerbContext) {
  if (!ctx.selectedRef) return null;
  return objectByRef(useDesk.getState().items, ctx.selectedRef);
}

const needSelection = (ctx: VerbContext): string | null =>
  selected(ctx) ? null : "Select an object";

const never = () => null;

/** The view the toggle verb would LEAVE (HS-105-01 density default). */
function currentView(): "list" | "spatial" {
  const s = useDesk.getState();
  return defaultViewFor(
    s.viewMode,
    Object.values(s.items).reduce((n, l) => n + l.length, 0),
    typeof window !== "undefined" && window.innerWidth <= 720,
  );
}

/** The four applications carry ⌘1-⌘4 and a window id the keymap can
 * focus/restore instead of re-opening (the HS-101 B8 behavior). */
const APP_BINDINGS: Record<
  string,
  { key: string; windowId: string } | undefined
> = {
  dictate: { key: "⌘1", windowId: "surface-dictation" },
  "review-meetings": { key: "⌘2", windowId: "surface-meetings" },
  "inspect-personas-and-coders": { key: "⌘3", windowId: "surface-companion" },
  "configure-settings": { key: "⌘4", windowId: "surface-settings" },
};

const needWindow = (): string | null =>
  openWindowCount() > 0 ? null : "No window open";

export const VERBS: Verb[] = [
  // ── Desk: NEW (the one create path - createPrimitive) ──────────────
  {
    id: "desk.new-note",
    label: "New Note",
    menu: "desk",
    scope: "floor",
    group: "new",
    keywords: ["create", "write"],
    ghost: never,
    run: () => void useDesk.getState().createPrimitive("note"),
  },
  {
    id: "desk.new-knowledge",
    label: "New Knowledge",
    menu: "desk",
    scope: "floor",
    group: "new",
    keywords: ["create", "kb"],
    ghost: never,
    run: () => void useDesk.getState().createPrimitive("kb"),
  },
  {
    id: "desk.new-agent",
    label: "New Agent",
    menu: "desk",
    scope: "floor",
    group: "new",
    keywords: ["create", "recipe"],
    ghost: never,
    run: () => void useDesk.getState().createPrimitive("recipe"),
  },
  {
    id: "desk.new-workflow",
    label: "New Workflow",
    menu: "desk",
    scope: "floor",
    group: "new",
    keywords: ["create", "steps"],
    ghost: never,
    run: () => void useDesk.getState().createPrimitive("workflow"),
  },
  {
    id: "desk.new-zone",
    label: "New Zone",
    menu: "desk",
    scope: "floor",
    group: "new",
    keywords: ["create", "place"],
    ghost: never,
    run: () => void useDesk.getState().createPrimitive("zone"),
  },
  // ── Desk: the floor verbs ───────────────────────────────────────────
  {
    id: "desk.toggle-view",
    label: () => (currentView() === "list" ? "Spatial view" : "List view"),
    menu: "desk",
    scope: "floor",
    group: "view",
    keywords: ["list", "spatial", "view"],
    ghost: never,
    run: () => {
      useDesk
        .getState()
        .setViewMode(currentView() === "list" ? "spatial" : "list");
    },
  },
  {
    id: "desk.arrange",
    label: "Arrange desk",
    scope: "floor",
    group: "floor",
    keywords: ["tidy", "clean"],
    ghost: () =>
      Object.keys(useDesk.getState().positions).length > 0
        ? null
        : "Nothing moved",
    run: () => useDesk.getState().tidyDesk(),
  },
  {
    id: "desk.overview",
    label: "Overview",
    scope: "floor",
    group: "floor",
    key: "⌃↑",
    keywords: ["expose", "windows"],
    ghost: needWindow,
    run: () => toggleExpose(),
  },
  {
    id: "desk.reset-layout",
    label: "Reset layout",
    scope: "floor",
    group: "floor",
    keywords: ["windows", "cascade"],
    ghost: needWindow,
    run: () => useDesk.getState().resetLayout(),
  },
  {
    // HS-112-03 — the desk's first destructive verb NEVER fires from a
    // menu tap: it opens the Prefs Desk module, where the armed confirm
    // (RESET DESK?) states what resets and what survives.
    id: "desk.reset-to-seed",
    label: "Reset to seed…",
    scope: "floor",
    group: "floor",
    keywords: ["fresh", "seed", "wipe", "architect"],
    ghost: never,
    run: () => openSurfaceOr("configure-settings", "/settings", "desk"),
  },
  {
    id: "desk.refresh",
    label: "Refresh from hub",
    scope: "floor",
    group: "floor",
    keywords: ["reload", "sync"],
    ghost: never,
    run: () => void useDesk.getState().refresh(),
  },
  // ── Object (selection-aware; ghosted with the reason) ───────────────
  {
    id: "object.open",
    label: "Open",
    menu: "object",
    scope: "object",
    ghost: needSelection,
    run: (ctx) => {
      const o = selected(ctx);
      if (o) useDesk.getState().openPullout(o.id);
    },
  },
  {
    id: "object.info",
    label: "Get Info",
    menu: "object",
    scope: "object",
    ghost: needSelection,
    run: (ctx) => {
      const o = selected(ctx);
      if (o) useDesk.getState().openInfoWindow(ctx.selectedRef as string);
    },
  },
  {
    id: "object.ask-project",
    label: "Ask this project",
    menu: "object",
    scope: "object",
    ghost: (ctx) => {
      const o = selected(ctx);
      if (!o) return "Select a Project";
      return o.kind === "project" ? null : "Select a Project";
    },
    run: (ctx) => {
      const o = selected(ctx);
      if (o?.kind !== "project") return;
      const desk = useDesk.getState();
      desk.setSelected([`project:${o.id}`]);
      desk.openAsk();
    },
  },
  {
    id: "object.edit",
    label: "Edit",
    menu: "object",
    scope: "object",
    ghost: (ctx) => {
      const o = selected(ctx);
      if (!o) return "Select an object";
      return EDITABLE.has(o.kind) ? null : "Not editable";
    },
    run: (ctx) => {
      const o = selected(ctx);
      if (o) useDesk.getState().openEditor(o.id);
    },
  },
  // ── Go (the applications - DESK_TOOLS is the data truth) ────────────
  ...DESK_TOOLS.map((tool): Verb => {
    const binding = APP_BINDINGS[tool.action];
    return {
      id: `go.${tool.action}`,
      label: tool.label,
      menu: "go",
      scope: "go",
      group: "launch",
      key: binding?.key,
      keywords: tool.description.toLocaleLowerCase().split(/\W+/).slice(0, 6),
      ghost: never,
      run: () => {
        if (binding && focusOrRestoreApp(binding.windowId)) return;
        openSurfaceOr(tool.action, tool.href, tool.subjectRef);
      },
    };
  }),
  // ── Window ──────────────────────────────────────────────────────────
  {
    id: "window.close",
    label: "Close window",
    scope: "window",
    key: "⌘W",
    ghost: needWindow,
    run: () => closeFrontWindow(),
  },
  {
    id: "window.minimize",
    label: "Minimize window",
    scope: "window",
    key: "⌘M",
    ghost: needWindow,
    run: () => minimizeFrontWindow(),
  },
  {
    id: "window.cycle",
    label: "Cycle windows",
    scope: "window",
    key: "⌃`",
    palette: false,
    ghost: needWindow,
    run: () => cycleWindows(),
  },
  // ── System ──────────────────────────────────────────────────────────
  {
    id: "system.search",
    label: "Search",
    scope: "system",
    key: "⌘K",
    palette: false,
    ghost: never,
    run: () => usePalette.getState().toggle(),
  },
  {
    id: "system.sheet",
    label: "Keyboard shortcuts",
    scope: "system",
    key: "⌘/",
    keywords: ["keys", "help"],
    ghost: never,
    run: () => useShortcutSheet.getState().toggle(),
  },
];

export function menuVerbs(menu: MenuId): Verb[] {
  return VERBS.filter((v) => v.menu === menu);
}

export function verbsFor(scope: VerbScope): Verb[] {
  return VERBS.filter((v) => v.scope === scope);
}

export function verbById(id: string): Verb | undefined {
  return VERBS.find((v) => v.id === id);
}
