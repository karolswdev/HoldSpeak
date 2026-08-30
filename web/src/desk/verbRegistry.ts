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
import { openIntelligence } from "./intelligenceNavigation";
import { openSurfaceOr } from "./shell";
import { objectByRef } from "./world";
import { DESK_TOOLS, KIND_GLYPH } from "./tools";
import { applicationForAction } from "./applications";
import { primitiveCan } from "../lib/primitives";
import { usePalette, useShortcutSheet } from "./chromeState";
import {
  closeFrontWindow,
  focusOrRestoreApp,
  minimizeFrontWindow,
  openWindowCount,
} from "./components/window/windowRegistry";
import {
  cycleWindows,
  cycleWindowsReverse,
  maximizeFrontWindow,
  snapFrontWindow,
} from "./components/window/windowCommands";
import { toggleExpose } from "./components/window/Expose";

export type MenuId = "desk" | "object" | "go" | "window";
export type VerbScope = "floor" | "object" | "go" | "window" | "system" | "thread";

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
  /** HS-148-02: unicode text-glyph for menus, deck, and palette. */
  glyph?: string;
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
    glyph: KIND_GLYPH.note,
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
    glyph: KIND_GLYPH.decision,
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
    glyph: KIND_GLYPH.kb,
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
    glyph: KIND_GLYPH.recipe,
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
    glyph: KIND_GLYPH.workflow,
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
    glyph: KIND_GLYPH.workbench,
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
    glyph: KIND_GLYPH.zone,
    keywords: ["create", "place"],
    ghost: never,
    run: () => void useDesk.getState().createPrimitive("zone"),
  },
  {
    id: "desk.new-thread",
    label: "New Thread",
    menu: "desk",
    scope: "floor",
    group: "new",
    glyph: KIND_GLYPH.thread,
    keywords: ["create", "chat", "conversation"],
    ghost: never,
    run: async () => {
      const { createThread } = await import("./threads");
      const t = await createThread({});
      useDesk.getState().openPullout(`thread:${t.id}`);
      void useDesk.getState().refresh();
    },
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
  {
    id: "desk.open-intelligence",
    label: "Open Intelligence",
    menu: "desk",
    scope: "floor",
    group: "view",
    glyph: "◆",
    keywords: ["brief", "follow-through", "receipts"],
    ghost: never,
    run: () => openIntelligence({ view: "brief" }),
  },
  {
    id: "desk.open-people",
    label: "Open People",
    menu: "desk",
    scope: "floor",
    group: "view",
    glyph: "⊕",
    keywords: ["relationships", "1:1", "one on one", "management"],
    ghost: never,
    run: () => openSurfaceOr("open-people", "/", undefined),
  },
  {
    id: "desk.intelligence-brief",
    label: "Show today's brief",
    scope: "floor",
    keywords: ["intelligence", "daily", "brief"],
    ghost: never,
    run: () => openIntelligence({ view: "brief" }),
  },
  {
    id: "desk.intelligence-overdue",
    label: "Show overdue follow-through",
    scope: "floor",
    keywords: ["intelligence", "follow-through", "overdue"],
    ghost: never,
    run: () => openIntelligence({ view: "follow-through", overdueOnly: true }),
  },
  {
    id: "desk.intelligence-find-receipt",
    label: "Find receipt…",
    scope: "floor",
    keywords: ["intelligence", "receipt", "decision", "why"],
    ghost: never,
    run: () => openIntelligence({ view: "receipts" }),
  },
  {
    id: "desk.intelligence-review-decisions",
    label: "Review decisions",
    scope: "floor",
    keywords: ["intelligence", "receipts", "governing", "why"],
    ghost: never,
    run: () => openIntelligence({ view: "receipts", receiptQuery: "", whyOnly: true }),
  },
  // ── Object (selection-aware; ghosted with the reason) ───────────────
  // HS-148-02: restrained verb glyphs so variant B is truthful.
  {
    id: "object.open",
    label: "Open",
    menu: "object",
    scope: "object",
    glyph: "▷",
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
    glyph: "⊙",
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
    glyph: "✦",
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
    glyph: "✦",
    ghost: (ctx) => {
      const o = selected(ctx);
      if (!o) return "Select an object";
      return primitiveCan(o.kind, "ask") ? null : "Ask unavailable";
    },
    run: (ctx) => {
      const o = selected(ctx);
      if (!o || !primitiveCan(o.kind, "ask")) return;
      const desk = useDesk.getState();
      desk.setSelected([`${o.kind}:${o.id}`]);
      desk.openAsk();
    },
  },
  {
    id: "object.continue-in-thread",
    label: "Continue in thread",
    menu: "object",
    scope: "object",
    glyph: KIND_GLYPH.thread,
    keywords: ["chat", "thread", "conversation"],
    ghost: (ctx) => {
      const o = selected(ctx);
      if (!o) return "Select an object";
      const threadable = new Set(["meeting", "note", "artifact", "decision", "recipe", "people"]);
      return threadable.has(o.kind) ? null : "Not threadable";
    },
    run: async (ctx) => {
      const o = selected(ctx);
      if (!o) return;
      const { createThread } = await import("./threads");
      const t = await createThread({
        seed_refs: [{ ref_kind: o.kind, ref_id: o.id }],
      });
      useDesk.getState().openPullout(`thread:${t.id}`);
      void useDesk.getState().refresh();
    },
  },
  {
    id: "object.edit",
    label: "Edit",
    menu: "object",
    scope: "object",
    glyph: "✎",
    ghost: (ctx) => {
      const o = selected(ctx);
      if (!o) return "Select an object";
      return primitiveCan(o.kind, "edit") ? null : "Not editable";
    },
    run: (ctx) => {
      const o = selected(ctx);
      if (o) useDesk.getState().openEditor(o.id, ctx.origin);
    },
  },
  {
    id: "object.rename",
    label: "Rename",
    menu: "object",
    scope: "object",
    key: "F2",
    glyph: "⌶",
    ghost: (ctx) => {
      const o = selected(ctx);
      if (!o) return "Select an object";
      return primitiveCan(o.kind, "rename")
        ? null
        : "Not renameable";
    },
    run: (ctx) => {
      const o = selected(ctx);
      if (!o) return;
      if (o.kind === "directory") useDesk.getState().setRenamingZone(o.id);
      else if (primitiveCan(o.kind, "rename")) useDesk.getState().openEditor(o.id, ctx.origin);
    },
  },
  {
    id: "object.duplicate",
    label: "Duplicate",
    menu: "object",
    scope: "object",
    glyph: "⧉",
    ghost: (ctx) => {
      const o = selected(ctx);
      if (!o) return "Select an object";
      return primitiveCan(o.kind, "duplicate") ? null : "Cannot duplicate";
    },
    run: (ctx) => {
      const o = selected(ctx);
      if (!o || !primitiveCan(o.kind, "duplicate")) return;
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
    glyph: "↦",
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
    glyph: "⌫",
    ghost: (ctx) => {
      const o = selected(ctx);
      if (!o) return "Select an object";
      return primitiveCan(o.kind, "delete") ? null : "Cannot delete";
    },
    run: (ctx) => {
      const o = selected(ctx);
      if (!o || !primitiveCan(o.kind, "delete") || typeof window === "undefined") return;
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
  // HS-148-02: glyph and group flow from DESK_TOOLS (dock-parity).
  ...DESK_TOOLS.map((tool): Verb => {
    const application = applicationForAction(tool.action);
    const binding =
      application?.shortcut && application.windowId
        ? { key: application.shortcut, windowId: application.windowId }
        : undefined;
    return {
      id: `go.${tool.action}`,
      label: tool.label,
      menu: "go",
      scope: "go",
      group: tool.group,
      glyph: tool.glyph,
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
    label: "Cycle windows (reverse)",
    menu: "window",
    scope: "window",
    key: "⌃⇧`",
    palette: false,
    ghost: needWindow,
    run: () => cycleWindowsReverse(),
  },
  {
    id: "window.snap-left",
    label: "Snap left",
    menu: "window",
    scope: "window",
    group: "layout",
    ghost: needWindow,
    run: () => snapFrontWindow("left"),
  },
  {
    id: "window.snap-right",
    label: "Snap right",
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
  // ── Thread slash verbs (HS-153-02) ─────────────────────────────────
  // These are the verb-ids for the ThreadComposer's / commands.
  // The composer owns the trigger; the pullout owns the handler.
  {
    id: "thread.keep",
    label: "Keep as note",
    scope: "thread",
    palette: false,
    ghost: never,
    run: () => {},
  },
  {
    id: "thread.fork",
    label: "Fork from here",
    scope: "thread",
    palette: false,
    ghost: never,
    run: () => {},
  },
  {
    id: "thread.stop",
    label: "Stop generation",
    scope: "thread",
    palette: false,
    ghost: never,
    run: () => {},
  },
  {
    id: "thread.new",
    label: "New thread",
    scope: "thread",
    palette: false,
    ghost: never,
    run: () => {},
  },
  {
    id: "thread.mode",
    label: "Switch mode",
    scope: "thread",
    palette: false,
    keywords: ["desk", "chase", "draft", "plan"],
    ghost: never,
    run: () => {},
  },
  {
    id: "thread.prompt",
    label: "Insert prompt",
    scope: "thread",
    palette: false,
    keywords: ["saved", "template"],
    ghost: never,
    run: () => {},
  },
  {
    id: "thread.tools",
    label: "Show tools",
    scope: "thread",
    palette: false,
    keywords: ["palette", "capabilities"],
    ghost: never,
    run: () => {},
  },
  {
    id: "thread.todo",
    label: "Add todo",
    scope: "thread",
    palette: false,
    keywords: ["task", "action"],
    ghost: never,
    run: () => {},
  },
  {
    id: "thread.compact",
    label: "Compact thread",
    scope: "thread",
    palette: false,
    keywords: ["summarize", "compress"],
    ghost: never,
    run: () => {},
  },
  {
    id: "thread.guardrail",
    label: "Toggle guardrail",
    scope: "thread",
    palette: false,
    keywords: ["guard", "safety"],
    ghost: never,
    run: () => {},
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
