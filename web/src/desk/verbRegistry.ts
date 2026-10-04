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
import { openPerson, openProjectUpdates } from "./openObject";
import { objectByRef } from "./world";
import { DESK_TOOLS, KIND_GLYPH } from "./tools";
import { applicationForAction } from "./applications";
import { primitiveCan } from "../lib/primitives";
import { usePalette, useShortcutSheet } from "./chromeState";
import { useSettleState } from "./settleState";
import { useChairState } from "./chairState";
import { deleteSeatShown } from "./deleteSeat";
import {
  closeFrontWindow,
  dockWindowCount,
  focusOrRestoreApp,
  minimizeFrontWindow,
  openWindowCount,
} from "./components/window/windowRegistry";
import {
  CHAIR_WINDOWS,
  isChairWindowOpen,
  openChairWindow,
} from "./chair/chairWindows";
import {
  cycleWindows,
  cycleWindowsReverse,
  sendFrontWindowToBack,
  snapFrontWindow, zoomFrontWindow,
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
  /** PHILO-13-14 (C4) — the program the verb opens, by its own name: the
   * query `People` finds the People app before a note that starts with the
   * word. */
  app?: string;
  /** PHILO-8-01 — the verb makes or edits a zone, so only a face that shows
   * zones (the Floor: spatial or list) offers it; the Chair withholds it
   * (the owner's Q2 (c), UX-CANON §A.11). */
  needsZones?: boolean;
  /** PHILO-13-11 (C1, slice two) — the menu face lists the verb inside a
   * submenu of this name (Window ▸ Chair). */
  submenu?: string;
  /** A checkable verb: true draws the check mark (an open Chair window). */
  checked?(ctx: VerbContext): boolean;
  /** Offered only at desktop width (Capture: at 393 Speak opens it). */
  wide?: boolean;
  /** null = runnable; a string = ghosted WITH that reason. */
  ghost(ctx: VerbContext): string | null;
  run(ctx: VerbContext): void;
}

/** PHILO-8-01 — true when the face the owner is on shows zones. */
export function zonesShown(): boolean {
  return useChairState.getState().surface === "floor";
}

/** PHILO-8-01 — false when this face withholds the verb (a zone verb on
 * the Chair). The palette and the menu bar ask this before they list it. */
export function offeredHere(v: Verb): boolean {
  if (v.wide && typeof window !== "undefined" && window.innerWidth <= 720) return false;
  return !v.needsZones || zonesShown();
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
/** Overview fans the windows with a Dock chip (not the Chair's). */
const needDockWindow = (): string | null =>
  dockWindowCount() > 0 ? null : "No window open";

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
  // PHILO-13-16 (C6) — the pop-key: a thought from any window in one key
  // press (⌃T). At 393 the same verb is in the Desk menu; no key is assumed.
  {
    id: "desk.new-thought",
    label: "Write a thought",
    menu: "desk",
    scope: "floor",
    group: "new",
    key: "⌃T",
    glyph: KIND_GLYPH.note,
    keywords: ["capture", "thought", "write", "idea"],
    ghost: never,
    run: async () => {
      const { openNewThought } = await import("./newThought");
      await openNewThought();
    },
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
    needsZones: true,
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
      const { openNewThread } = await import("./newThread");
      await openNewThread();
    },
  },
  // HS-159-05: Project creation joins the shared creation grammar (WEB-CR-001)
  {
    id: "desk.new-project",
    label: "New Project",
    menu: "desk",
    scope: "floor",
    group: "new",
    glyph: KIND_GLYPH.project,
    keywords: ["create", "project", "interview", "setup", "watch"],
    ghost: never,
    run: () => openSurfaceOr("project-setup", "/"),
  },
  // ── Desk: the floor verbs ───────────────────────────────────────────
  {
    id: "desk.settle",
    // HS-201-06 (Constitution tenet 4, ASD-STE100): "Settle in" is an
    // idiom. The verb hides the navigation chrome and shows it again.
    label: () => useSettleState.getState().settled ? "Back to Desk" : "Hide the menus",
    menu: "desk",
    scope: "floor",
    group: "view",
    key: "⌘⇧F",
    glyph: "◌",
    keywords: ["focus", "quiet", "zen", "chrome", "settle"],
    ghost: never,
    run: () => useSettleState.getState().toggle(),
  },
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
    ghost: needDockWindow,
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
    app: "Intelligence",
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
    app: "People",
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
      const { openNewThread } = await import("./newThread");
      await openNewThread({ seed_refs: [{ ref_kind: o.kind, ref_id: o.id }] });
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
      // PHILO-8-01 — a zone renames where zones are shown; the Chair
      // shows none, so it does not start a rename nothing can draw.
      if (o.kind === "directory" && !zonesShown()) return "Open the Floor";
      return primitiveCan(o.kind, "rename")
        ? null
        : "Not renameable";
    },
    run: (ctx) => {
      const o = selected(ctx);
      if (!o) return;
      if (o.kind === "directory") {
        if (zonesShown()) useDesk.getState().setRenamingZone(o.id);
      } else if (primitiveCan(o.kind, "rename")) useDesk.getState().openEditor(o.id, ctx.origin);
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
      if (!primitiveCan(o.kind, "delete")) return "Cannot delete";
      // PHILO-8-02 round two — a delete is offered only where its receipt
      // can be read; the Chair shows none (UX-CANON A.11).
      return deleteSeatShown() ? null : "Open the Floor or the list";
    },
    run: (ctx) => {
      const o = selected(ctx);
      if (!o || !primitiveCan(o.kind, "delete") || !deleteSeatShown() || typeof window === "undefined") return;
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
    // PHILO-13-12 (C2): the Workbench name of the gadget (design §3).
    label: "Iconify",
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
  // PHILO-13-12 (C2) — zoom and depth (design §3, board C1-2b). ⌘ stands
  // for the Amiga key; ⌃M and ⌃B are the canvas's proposals, bound here.
  {
    id: "window.maximize",
    label: "Zoom",
    menu: "window",
    scope: "window",
    group: "layout",
    key: "⌃M",
    keywords: ["maximize", "zoom", "size"],
    // At 393 a window fills the work area: zoom has nothing to change.
    ghost: () =>
      needWindow() ??
      (typeof window !== "undefined" && window.innerWidth <= 720 ? "Fills the screen" : null),
    run: () => zoomFrontWindow(),
  },
  {
    id: "window.depth",
    label: "To back",
    menu: "window",
    scope: "window",
    group: "layout",
    key: "⌃B",
    keywords: ["depth", "back", "behind", "lower"],
    ghost: needWindow,
    run: () => sendFrontWindowToBack(),
  },
  // ── Window ▸ Chair (PHILO-13-11 C1, R1): the Chair's four windows, a
  // check on each open one; picking one opens it in front. Only on the
  // Chair (its windows are not mounted on the Floor). ─────────────────────
  ...CHAIR_WINDOWS.map((w): Verb => ({
    id: `chair.window.${w.key}`,
    label: w.title,
    menu: "window",
    scope: "window",
    group: "chair",
    submenu: "Chair",
    wide: !w.phone,
    palette: false,
    keywords: ["chair", "window"],
    checked: () => isChairWindowOpen(w.id),
    ghost: () => (useChairState.getState().surface === "chair" ? null : "Not on the Chair"),
    run: () => openChairWindow(w.id),
  })),
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

/* ── PHILO-13-14 (C4): the week's verbs ─────────────────────────────────
 * A verb FAMILY is one registered verb with one row per thing of his week:
 * a report, a project, a destination of the front document. The palette
 * renders these rows; each runs through the one open grammar (openObject)
 * or C5's push seam (windowSend). A `Send …` row only opens the exact
 * preview in the document's SEND well: he presses Send (Article V). */

export interface WeekPerson { id: string; name: string; kind: string }
export interface WeekProject { id: string; name: string }
export interface WeekSend { title: string; choices: Array<{ id: string; name: string; channel: string; pick(): void }> }
export interface Week { people: WeekPerson[]; projects: WeekProject[]; send: WeekSend | null }

export interface WeekVerbRow { id: string; family: string; label: string; keywords: string; run(): void }

export interface VerbFamily {
  id: string;
  rows(week: Week): WeekVerbRow[];
}

export const VERB_FAMILIES: VerbFamily[] = [
  {
    id: "week.prep",
    // Every relationship has a Prep lens (a report, a peer): PeopleCore.
    rows: (week) => week.people
      .map((p) => ({
        id: `week.prep.${p.id}`, family: "week.prep",
        label: `Prep 1:1 with ${p.name}`, keywords: "prep 1:1 one on one agenda",
        run: () => openPerson(p.id, "prep"),
      })),
  },
  {
    id: "week.send",
    rows: (week) => (week.send?.choices ?? []).map((d) => ({
      id: `week.send.${d.id}`, family: "week.send",
      label: `Send ${week.send?.title} to ${d.name}`, keywords: `send ${d.channel.toLowerCase()}`,
      run: () => d.pick(),
    })),
  },
  {
    id: "week.draft-update",
    rows: (week) => week.projects.map((p) => ({
      id: `week.draft-update.${p.id}`, family: "week.draft-update",
      label: `Draft update for ${p.name}`, keywords: "draft update status weekly project",
      run: () => openProjectUpdates(p.id),
    })),
  },
];

/** Every week-verb row, in family order. */
export function weekVerbs(week: Week): WeekVerbRow[] {
  return VERB_FAMILIES.flatMap((f) => f.rows(week));
}
