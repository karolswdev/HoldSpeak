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
  cycleWindowsReverse,
  focusOrRestoreApp,
  maximizeFrontWindow,
  minimizeFrontWindow,
  openWindowCount,
  snapFrontWindow,
  toggleExpose,
} from "./components/DeskWindow";

export type MenuId = "desk" | "object" | "go" | "window";
export type VerbScope = "floor" | "object" | "go" | "window" | "system";

export interface VerbContext {
  /** The single selected object ref, when exactly one is selected. */
  selectedRef: string | null;
  /** The pointer origin for context-menu actions that open a window. */
  origin?: { x: number; y: number };
}

/** A registry verb requests deletion; the rendered desk owns its undo receipt. */
export const OBJECT_DELETE_REQUEST = "desk:request-object-delete";

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
const DELETABLE = new Set([
  "note",
  "decision",
  "kb",
  "recipe",
  "directory",
  "chain",
  "workflow",
]);
const DUPLICABLE = new Set([
  "note",
  "decision",
  "kb",
  "recipe",
  "workflow",
  "workbench",
]);
const ASKABLE = new Set([
  "note",
  "kb",
  "recipe",
  "meeting",
  "artifact",
  "workflow",
]);

function selected(ctx: VerbContext) {
  if (!ctx.selectedRef) return null;
  return objectByRef(useDesk.getState().items, ctx.selectedRef);
}

const needSelection = (ctx: VerbContext): string | null =>
  selected(ctx) ? null : "Select an object";

const never = () => null;

/** Preserve the editable payload while letting createPrimitive own IDs, routes,
 * placement, the NEW beat, and the destination editor. */
function duplicateOverrides(o: NonNullable<ReturnType<typeof selected>>) {
  const source = o.ref as unknown as Record<string, unknown>;
  const copyName = `Copy of ${o.title}`;
  switch (o.kind) {
    case "note":
      return {
        title: copyName,
        body_markdown: source.bodyMarkdown ?? "",
        tags: source.tags ?? [],
      };
    case "decision":
      return {
        title: copyName,
        status: source.status ?? "proposed",
        context_markdown: source.contextMarkdown ?? "",
        decision_markdown: source.decisionMarkdown ?? "",
        consequences_markdown: source.consequencesMarkdown ?? "",
        alternatives: source.alternatives ?? [],
      };
    case "kb":
      return { name: copyName };
    case "recipe":
      return { name: copyName, avatar: source.avatar ?? "" };
    case "workflow":
      return { name: copyName, graph_json: source.graphJson };
    case "workbench":
      return { name: copyName };
  }
}

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
    key: "⌘N",
    keywords: ["create", "write"],
    ghost: never,
    run: () => void useDesk.getState().createPrimitive("note"),
  },
  {
    id: "desk.new-decision",
    label: "New Decision",
    menu: "desk",
    scope: "floor",
    group: "new",
    key: "⌘⇧N",
    keywords: ["create", "adr", "architecture"],
    ghost: never,
    run: () => void useDesk.getState().createPrimitive("decision"),
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
    id: "desk.new-workbench",
    label: "New Workbench",
    menu: "desk",
    scope: "floor",
    group: "new",
    keywords: ["create", "agent", "todo", "backlog"],
    ghost: never,
    run: () => void useDesk.getState().createPrimitive("workbench"),
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
    menu: "window",
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
      if (!o) return;
      if (o.kind === "directory")
        useDesk.getState().openZoneWindow(o.id, ctx.origin);
      else useDesk.getState().openPullout(o.id, ctx.origin);
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
    id: "object.ask",
    label: "Ask AI",
    menu: "object",
    scope: "object",
    ghost: (ctx) => {
      const o = selected(ctx);
      if (!o) return "Select an object";
      return ASKABLE.has(o.kind) ? null : "Ask unavailable";
    },
    run: (ctx) => {
      const o = selected(ctx);
      if (!o || !ASKABLE.has(o.kind)) return;
      const desk = useDesk.getState();
      desk.setSelected([`${o.kind}:${o.id}`]);
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
  {
    id: "object.rename",
    label: "Rename",
    menu: "object",
    scope: "object",
    key: "F2",
    ghost: (ctx) => {
      const o = selected(ctx);
      if (!o) return "Select an object";
      return o.kind === "directory" || EDITABLE.has(o.kind)
        ? null
        : "Not renameable";
    },
    run: (ctx) => {
      const o = selected(ctx);
      if (!o) return;
      if (o.kind === "directory") useDesk.getState().setRenamingZone(o.id);
      else if (EDITABLE.has(o.kind)) useDesk.getState().openEditor(o.id);
    },
  },
  {
    id: "object.duplicate",
    label: "Duplicate",
    menu: "object",
    scope: "object",
    ghost: (ctx) => {
      const o = selected(ctx);
      if (!o) return "Select an object";
      return DUPLICABLE.has(o.kind) ? null : "Cannot duplicate";
    },
    run: (ctx) => {
      const o = selected(ctx);
      if (!o || !DUPLICABLE.has(o.kind)) return;
      const overrides = duplicateOverrides(o);
      if (!overrides) return;
      void useDesk.getState().createPrimitive(
        o.kind as "note" | "decision" | "kb" | "recipe" | "workflow" | "workbench",
        overrides,
      );
    },
  },
  {
    id: "object.file",
    label: "Move to Zone",
    menu: "object",
    scope: "object",
    ghost: (ctx) => {
      const o = selected(ctx);
      if (!o) return "Select an object";
      return o.kind === "directory" ? "A zone cannot file itself" : null;
    },
    run: (ctx) => {
      const o = selected(ctx);
      // The pullout's Filing disclosure is the one Zone picker; opening it
      // preserves a single membership path instead of inventing a second.
      if (o && o.kind !== "directory") useDesk.getState().openPullout(o.id, ctx.origin);
    },
  },
  {
    id: "object.delete",
    label: "Delete",
    menu: "object",
    scope: "object",
    group: "danger",
    key: "Delete",
    ghost: (ctx) => {
      const o = selected(ctx);
      if (!o) return "Select an object";
      return DELETABLE.has(o.kind) ? null : "Cannot delete";
    },
    run: (ctx) => {
      const o = selected(ctx);
      if (!o || !DELETABLE.has(o.kind) || typeof window === "undefined") return;
      window.dispatchEvent(
        new CustomEvent(OBJECT_DELETE_REQUEST, { detail: { ref: ctx.selectedRef } }),
      );
    },
  },
  {
    id: "zone.focus",
    label: "Focus",
    scope: "object",
    ghost: (ctx) => {
      const o = selected(ctx);
      if (!o) return "Select a Zone";
      return o.kind === "directory" ? null : "Select a Zone";
    },
    run: (ctx) => {
      const o = selected(ctx);
      if (o?.kind === "directory") useDesk.getState().diveInto(o.id);
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
      key: tool.action === "ask" ? "⌘I" : binding?.key,
      keywords: tool.description.toLocaleLowerCase().split(/\W+/).slice(0, 6),
      ghost: never,
      run: () => {
        if (tool.action === "ask") {
          useDesk.getState().openAsk();
          return;
        }
        if (binding && focusOrRestoreApp(binding.windowId)) return;
        openSurfaceOr(tool.action, tool.href, tool.subjectRef);
      },
    };
  }),
  // ── Window ──────────────────────────────────────────────────────────
  {
    id: "window.close",
    label: "Close window",
    menu: "window",
    scope: "window",
    key: "⌘W",
    ghost: needWindow,
    run: () => closeFrontWindow(),
  },
  {
    id: "window.minimize",
    label: "Minimize window",
    menu: "window",
    scope: "window",
    key: "⌘M",
    ghost: needWindow,
    run: () => minimizeFrontWindow(),
  },
  {
    id: "window.cycle",
    label: "Cycle windows",
    menu: "window",
    scope: "window",
    key: "⌃`",
    palette: false,
    ghost: needWindow,
    run: () => cycleWindows(),
  },
  {
    id: "window.cycle-reverse",
    label: "Cycle Windows (Reverse)",
    menu: "window",
    scope: "window",
    key: "⌃⇧`",
    palette: false,
    ghost: needWindow,
    run: () => cycleWindowsReverse(),
  },
  {
    id: "window.snap-left",
    label: "Snap Left",
    menu: "window",
    scope: "window",
    group: "layout",
    ghost: needWindow,
    run: () => snapFrontWindow("left"),
  },
  {
    id: "window.snap-right",
    label: "Snap Right",
    menu: "window",
    scope: "window",
    group: "layout",
    ghost: needWindow,
    run: () => snapFrontWindow("right"),
  },
  {
    id: "window.maximize",
    label: "Maximize",
    menu: "window",
    scope: "window",
    group: "layout",
    ghost: needWindow,
    run: () => maximizeFrontWindow(),
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
