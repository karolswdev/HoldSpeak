/** HS-105-05 — the ONE verb registry (the ARexx rule, scoped honestly):
 * a verb is a REGISTERED capability, and every face renders the same
 * registry. Faces today: the menu bar (this story) and the ⌘K shelf
 * (which already reaches DESK_TOOLS — re-exported here so the two faces
 * share one truth). The wire face deliberately WAITS for the kernel's
 * userland dispatch (invoking store verbs over HTTP without the broker's
 * consent model would widen authority — Article V).
 *
 * Ghosting over hiding: a verb that cannot run now stays visible with
 * its reason — the system admits what it can do. */
import { useDesk } from "./store";
import { openSurfaceOr } from "./shell";
import { objectByRef } from "./world";
import { DESK_TOOLS } from "./components/DeskToolShelf";

export type MenuId = "desk" | "object" | "go";

export interface VerbContext {
  /** The single selected object ref, when exactly one is selected. */
  selectedRef: string | null;
}

export interface Verb {
  id: string;
  label: string;
  menu: MenuId;
  /** Shown keyboard equivalent (display only; bindings live where they
   * already live — the registry never double-binds). */
  key?: string;
  /** null = runnable; a string = ghosted WITH that reason. */
  ghost(ctx: VerbContext): string | null;
  run(ctx: VerbContext): void;
}

const EDITABLE = new Set(["note", "kb", "recipe", "workflow"]);

function selected(ctx: VerbContext) {
  if (!ctx.selectedRef) return null;
  return objectByRef(useDesk.getState().items, ctx.selectedRef);
}

const needSelection = (ctx: VerbContext): string | null =>
  selected(ctx) ? null : "Select an object";

export const VERBS: Verb[] = [
  // ── Desk ────────────────────────────────────────────────────────────
  {
    id: "desk.new-note",
    label: "New Note",
    menu: "desk",
    ghost: () => null,
    run: () => void useDesk.getState().createPrimitive("note"),
  },
  {
    id: "desk.new-knowledge",
    label: "New Knowledge",
    menu: "desk",
    ghost: () => null,
    run: () => void useDesk.getState().createPrimitive("kb"),
  },
  {
    id: "desk.new-agent",
    label: "New Agent",
    menu: "desk",
    ghost: () => null,
    run: () => void useDesk.getState().createPrimitive("recipe"),
  },
  {
    id: "desk.new-zone",
    label: "New Zone",
    menu: "desk",
    ghost: () => null,
    run: () => void useDesk.getState().createPrimitive("zone"),
  },
  {
    id: "desk.toggle-view",
    label: "List view",
    menu: "desk",
    ghost: () => null,
    run: () => {
      const s = useDesk.getState();
      s.setViewMode(s.viewMode === "list" ? "spatial" : "list");
    },
  },
  // ── Object (selection-aware; ghosted with the reason) ───────────────
  {
    id: "object.open",
    label: "Open",
    menu: "object",
    ghost: needSelection,
    run: (ctx) => {
      const o = selected(ctx);
      if (o) useDesk.getState().openPullout(o.id);
    },
  },
  {
    id: "object.info",
    label: "Info",
    menu: "object",
    ghost: needSelection,
    run: (ctx) => {
      const o = selected(ctx);
      if (o) useDesk.getState().openInfoWindow(ctx.selectedRef as string);
    },
  },
  {
    id: "object.edit",
    label: "Edit",
    menu: "object",
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
  // ── Go (the four applications + tools — DESK_TOOLS is the truth) ────
  ...DESK_TOOLS.map(
    (tool): Verb => ({
      id: `go.${tool.action}`,
      label: tool.label,
      menu: "go",
      ghost: () => null,
      run: () => openSurfaceOr(tool.action, tool.href, tool.subjectRef),
    }),
  ),
];

export function menuVerbs(menu: MenuId): Verb[] {
  return VERBS.filter((v) => v.menu === menu);
}
