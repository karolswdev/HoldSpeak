// HS-105-05 — the menu bar: the browsable face of the ONE verb registry.
// Menus derive from verbRegistry (never hardcode a verb here — the guard
// census enforces it). Betterment shell S0 (UX-CANON A.11, "withhold, never
// ghost"): a verb that cannot run now is not drawn. The Object menu is the
// right-click menu of the thing in front (objectMenuEntries), titled by its
// kind, and is not drawn when nothing is in front.
// HS-111-07 — dropdowns render through the WorkMenu portal: inside the
// chrome cluster they inherited the z-30 stacking context and windows
// (z-42) covered open menus. The OS's own voice draws OVER the programs
// it hosts, always.
// HS-148-01 — the D3 repair: bar-path menus autoFocus their first item
// on intentional open (click/keyboard), NOT on hover-switch (which must
// never steal focus from wherever the user is typing).
import "./chrome-menus.css";
import { useEffect, useRef, useState } from "react";
import { useDesk } from "../store";
import { useSettleState } from "../settleState";
import {
  VERBS,
  menuVerbs,
  offeredHere,
  verbLabel,
  type MenuId,
  type VerbContext,
} from "../verbRegistry";
import { openProjectRoom } from "../shell";
import { KIND_GLYPH, KIND_LABEL } from "../tools";
import { objectMenuEntries, windowObjectRef } from "../objectMenu";
import { objectByRef } from "../world";
import { WorkMenu, withholdGhosts, type WorkMenuEntry } from "./DeskMenu";
import { useCompactViewport } from "../useCompactViewport";
import { CHAIR_WINDOW_IDS } from "../chair/chairWindows";
import {
  applicationVerbId,
  goRows,
  type GoGroup,
  type GoRow,
} from "../applications";
import { useBuilderTools } from "../builderTools";
import { useLaunchers } from "./window/launcherRegistry";
import { rootDirectories } from "../screen/compose";
import { openScreenRef } from "../screen/open";
import { qualifiedRef } from "../api";
import { Button } from "../../components/signal/Signal";
import { frontSendTo, primeSendTo, useSendToTick } from "../windowSend";
import {
  closeFrontWindow,
  focusOrRestoreApp,
  frontWindowId,
  openWindowCount,
  registrySnapshot,
  useAllOpenWindows,
} from "./window/windowRegistry";

const MENUS: { id: MenuId; label: string }[] = [
  { id: "desk", label: "Desk" },
  { id: "object", label: "Object" },
  { id: "go", label: "Go" },
  { id: "window", label: "Window" },
];

/** Betterment shell S0: the Object menu's title is the kind of the thing in
 * front, in words. */
const OBJECT_TITLE: Record<string, string> = {
  note: "Note",
  meeting: "Meeting",
  people: "Person",
  project: "Project",
  decision: "Decision",
  directory: "Drawer",
};
export function objectMenuTitle(kind: string): string {
  return OBJECT_TITLE[kind] ?? KIND_LABEL[kind] ?? kind.charAt(0).toUpperCase() + kind.slice(1);
}

/** Betterment shell S0: the Object menu's target. The front window's object
 * when the desk knows it, else the one selected icon, else none. `fromWindow`
 * says the target is a window's, so its Delete closes that window first (the
 * same rule as the window's own `Object ▸`). */
export function menuBarObjectTarget(
  frontId: string | null,
  selectedIds: readonly string[],
): { ref: string; kind: string; fromWindow: boolean } | null {
  const items = useDesk.getState().items;
  const fromWindow = windowObjectRef(frontId);
  const ref = fromWindow ?? (selectedIds.length === 1 ? selectedIds[0] : null);
  if (!ref) return null;
  const object = objectByRef(items, ref);
  if (!object) return null;
  return { ref, kind: object.kind, fromWindow: Boolean(fromWindow) };
}

/** PARKED (betterment shell S1): the phone's hand-written Go lists. Go on
 * the phone and the phone home now draw the manifest's Go groups
 * (`goRows`, applications.ts) like the desktop; nothing reads these two.
 * Brief and The week left the phone list (parked by ../daily/); Capture is
 * on the phone Dock. Kept for the record: docs/internal/betterment/shell/RECIPE.md S1. */
export const PHONE_GO_CHAIR: readonly (readonly [string, string?])[] = [
  ["chair.window.needs"],
  ["desk.intelligence-brief", "Brief"],
  ["chair.window.week"],
  ["chair.window.capture"],
];
export const PHONE_GO_PLACES: readonly (readonly [string, string])[] = [
  ["go.review-meetings", "Meetings"],
  ["go.ask", "Ask AI"],
  ["desk.open-people", "People"],
  ["go.open-conductor", "Conductor"],
];
/** The phone has no Desk menu, so its Go ends with New ▸ (four kinds). */
export const PHONE_NEW: readonly (readonly [string, string])[] = [
  ["desk.new-thought", "Note"],
  ["desk.new-meeting", "Meeting"],
  ["desk.new-project", "Project"],
  ["desk.new-person", "Person"],
];

/** What Go draws from: `row(id, label?)` is one registry verb as a menu row
 * (null when it has no such verb or the verb cannot run); the desk's
 * projects and root drawers; the announced dock launchers; and whether the
 * Builder tools setting is on. */
export interface GoInputs {
  row: (verbId: string, label?: string) => WorkMenuEntry | null;
  projects: readonly { id: string; name: string }[];
  openProject: (id: string) => void;
  drawers?: readonly { ref: string; name: string }[];
  openDrawer?: (ref: string) => void;
  launchers?: readonly { id: string; activate: () => void }[];
  builder?: boolean;
  /** The phone: a row with a `phoneVerbId` runs that verb there. */
  phone?: boolean;
}

/** Betterment shell S1 — Go is every application, from one list: Daily
 * (Today, Needs you, Meetings, People, Projects ▸, Conductor, Ask AI, Speak),
 * then Work (Workbenches, Memory, Voice commands, Drawers ▸), then Builder ▸
 * when Builder tools is on. The manifest's `go` and GO_EXTRA_ROWS are the
 * truth (applications.ts `goRows`). A submenu with no rows is not drawn.
 * Pure over its inputs. */
export function goEntries(inputs: GoInputs): WorkMenuEntry[] {
  const { row, projects, openProject, drawers = [], openDrawer, launchers = [], builder = false, phone = false } = inputs;
  const draw = (r: GoRow): WorkMenuEntry | null => {
    switch (r.kind) {
      case "app":
        return row(applicationVerbId(r.app), r.label);
      case "verb":
        return row(phone && r.phoneVerbId ? r.phoneVerbId : r.verbId, r.label);
      case "projects":
        return projects.length
          ? {
              type: "sub", id: "go-projects", label: "Projects",
              entries: projects.map((p) => ({
                type: "item" as const, id: `go-project-${p.id}`, label: p.name,
                glyph: KIND_GLYPH.project, onSelect: () => openProject(p.id),
              })),
            }
          : null;
      case "drawers":
        return drawers.length && openDrawer
          ? {
              type: "sub", id: "go-drawers", label: "Drawers",
              entries: drawers.map((d) => ({
                type: "item" as const, id: d.ref, label: d.name || "Drawer",
                glyph: KIND_GLYPH.zone, onSelect: () => openDrawer(d.ref),
              })),
            }
          : null;
      case "launcher": {
        // A launcher row exists only while its launcher is announced.
        const launcher = launchers.find((l) => l.id === r.launcherId);
        return launcher
          ? { type: "item", id: `go-launcher-${r.launcherId}`, label: r.label, glyph: r.glyph, onSelect: () => launcher.activate() }
          : null;
      }
    }
  };
  const group = (g: GoGroup) =>
    goRows(g).map(draw).filter((e): e is WorkMenuEntry => e !== null);
  const out: WorkMenuEntry[] = group("daily");
  const work = group("work");
  if (work.length) out.push({ type: "sep", id: "go-work-sep" }, ...work);
  if (builder) {
    const tools = group("builder");
    if (tools.length)
      out.push({ type: "sep", id: "go-builder-sep" }, { type: "sub", id: "go-builder", label: "Builder", entries: tools });
  }
  return out;
}

/** Go at 393: the same groups as the desktop, then New ▸ (the phone has no
 * Desk menu). No row carries a keycap: a phone has no ⌘ key. */
export function phoneGo(inputs: GoInputs): WorkMenuEntry[] {
  const newRows = PHONE_NEW.map(([id, label]) => inputs.row(id, label))
    .filter((e): e is WorkMenuEntry => e !== null);
  return [
    ...goEntries({ ...inputs, phone: true }),
    { type: "sep", id: "go-new-sep" },
    { type: "sub", id: "go-new", label: "New", entries: newRows },
  ];
}

/** Go at 1440 (betterment shell S1): `goEntries`. Settings, Engines,
 * Accounts and Setup are in the HoldSpeak menu. */
export function deskGo(inputs: GoInputs): WorkMenuEntry[] {
  return goEntries(inputs);
}

/** The Window menu ends with the open windows, a check on the front one;
 * a pick brings that window to the front (owner ratified 2026-10-04). The
 * rows are windows, not verbs: they come from the window registry, with the
 * same one name the title bar and the Dock chip show. Pure over its inputs. */
export function appendOpenWindows(
  out: WorkMenuEntry[],
  windows: readonly { id: string; label: string }[],
  front: string | null,
  pick: (id: string) => void,
): void {
  if (!windows.length) return;
  if (out.length) out.push({ type: "sep", id: "sep-open-windows" });
  for (const w of windows)
    out.push({
      type: "item",
      id: `open-window-${w.id}`,
      label: w.label,
      checked: w.id === front,
      onSelect: () => pick(w.id),
    });
}

export function DeskMenuBar() {
  const settled = useSettleState((s) => s.settled);
  // HS-202-02 — the phone bar has room for ONE navigator. Go is that door
  // (the chrome-menus.css phone block already declared the design), so at
  // phone width Desk, Object and Window are not rendered at all and their
  // verbs ride inside Go. Before this they were rendered and then hidden
  // by CSS: every `New …` verb, `New Note` among them, was unreachable at
  // 393 (03-interaction-walk.md finding 2).
  const compact = useCompactViewport();
  const [open, setOpen] = useState<MenuId | null>(null);
  useEffect(() => {
    if (settled) setOpen(null);
  }, [settled]);
  // HS-148-01: track whether the open was intentional (click/keyboard)
  // vs hover-switch. Only intentional opens autoFocus the first item.
  const [intentional, setIntentional] = useState(false);
  const barRef = useRef<HTMLElement | null>(null);
  const openerRef = useRef<HTMLElement | null>(null);
  const [at, setAt] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const selectedIds = useDesk((s) => s.selectedIds);
  // S0: the Object menu's target resolves against the desk's objects.
  useDesk((s) => s.items);
  // S1: Go draws the announced launchers and Builder ▸ behind its switch.
  const launchers = useLaunchers();
  const builder = useBuilderTools((s) => s.on);
  // PHILO-15 11: the phone Go lists the projects.
  const projects = useDesk((s) => s.items.project);
  // The Window menu lists the open windows: re-render on a registry change
  // and on a change of the front window.
  useAllOpenWindows();
  useDesk((s) => s.panelOrder);
  useDesk((s) => s.panelMin);
  // PHILO-13-15 (C5): an open menu re-renders when a Send to read lands;
  // the Object menu (393: Go) reads the front window's facts as it opens.
  useSendToTick(open !== null);
  useEffect(() => {
    if (open === "object" || (compact && open === "go")) primeSendTo(frontWindowId());
  }, [open, compact]);
  const ctx: VerbContext = {
    selectedRef: selectedIds.length === 1 ? selectedIds[0] : null,
  };
  const objectTarget = menuBarObjectTarget(frontWindowId(), selectedIds);
  // S0: the right-click rows of the thing in front; a Delete on a window's
  // object closes that window first (the window's own Object ▸ rule).
  const objectRows = objectTarget
    ? withholdGhosts(objectMenuEntries({ ref: objectTarget.ref }).map((e) =>
        objectTarget.fromWindow && e.type === "item" && e.id === "object.delete"
          ? { ...e, onSelect: () => { closeFrontWindow(); e.onSelect(); } }
          : e,
      ))
    : [];
  const titles = MENUS.flatMap((m) =>
    m.id !== "object"
      ? [m]
      : objectTarget && objectRows.length
        ? [{ ...m, label: objectMenuTitle(objectTarget.kind) }]
        : [],
  );
  // The Object menu closes when its target goes.
  const objectShown = titles.some((m) => m.id === "object");
  useEffect(() => {
    if (open === "object" && !objectShown) setOpen(null);
  }, [open, objectShown]);
  // The desktop dismissal rule (caught live by the 105-05 walk): an open
  // menu closes on ANY outside pointer-down and on Escape from anywhere.
  // (The WorkMenu panel guards its own inside; the bar guards its titles.)
  useEffect(() => {
    if (!open) return;
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(null);
    };
    document.addEventListener("keydown", key, true);
    return () => document.removeEventListener("keydown", key, true);
  }, [open]);

  const openMenu = (id: MenuId, el: HTMLElement, isIntentional: boolean) => {
    openerRef.current = el;
    const r = el.getBoundingClientRect();
    setAt({ x: r.left, y: r.bottom });
    setIntentional(isIntentional);
    setOpen(id);
  };

  const menuEntries = (id: MenuId, out: WorkMenuEntry[]): void => {
    let lastGroup: string | undefined;
    // PHILO-13-15 (C5, fork 5): the Object menu leads with the front
    // window's `Send to ▸`, its own group (the same composition as the
    // window menu). At 393 it leads the Object group inside Go.
    if (id === "object") {
      const sendTo = frontSendTo();
      if (sendTo) {
        if (out.length) out.push({ type: "sep", id: "sep-send-to-lead" });
        out.push(sendTo);
      }
      // S0: the same rows as the right-click menu of the thing in front.
      if (sendTo && objectRows.length) out.push({ type: "sep", id: "sep-send-to" });
      out.push(...objectRows);
      return;
    }
    // S0: with no window open, the Window menu holds one line.
    if (id === "window" && openWindowCount() === 0) {
      out.push({ type: "note", id: "window-none", label: "No windows open" });
      return;
    }
    // PHILO-13-11 (C1, slice two): a verb with a `submenu` rides in ONE
    // submenu of that name (Window ▸ Chair), at the place of its first verb.
    const subs = new Map<string, WorkMenuEntry[]>();
    for (const v of menuVerbs(id)) {
      if (!offeredHere(v)) continue;
      const item: WorkMenuEntry = {
        type: "item",
        id: v.id,
        label: verbLabel(v, ctx),
        glyph: v.glyph,
        keycap: v.key,
        ghost: v.ghost(ctx),
        ...(v.checked ? { checked: v.checked(ctx) } : {}),
        onSelect: () => v.run(ctx),
      };
      if (v.submenu) {
        const known = subs.get(v.submenu);
        if (known) {
          known.push(item);
          continue;
        }
        const entries: WorkMenuEntry[] = [item];
        subs.set(v.submenu, entries);
        if (out.length && v.group !== lastGroup)
          out.push({ type: "sep", id: `sep-${v.id}` });
        lastGroup = v.group;
        out.push({ type: "sub", id: `sub-${v.group ?? v.id}`, label: v.submenu, entries });
        continue;
      }
      if (out.length && v.group !== lastGroup)
        out.push({ type: "sep", id: `sep-${v.id}` });
      lastGroup = v.group;
      out.push(item);
    }
    // One window, one row: Window ▸ Chair already offers the Chair windows
    // (a check on each open one), so the open-windows list leaves them out.
    if (id === "window")
      appendOpenWindows(
        out,
        registrySnapshot.filter((w) => !CHAIR_WINDOW_IDS.includes(w.id)),
        frontWindowId(),
        (w) => { focusOrRestoreApp(w); },
      );
  };

  /** One registry verb as a Go row: its label (or Go's word for it),
   * glyph, ghost and check; a keycap at desktop width only (a phone has no
   * ⌘ key). */
  const goRow = (verbId: string, label?: string): WorkMenuEntry | null => {
    const v = VERBS.find((x) => x.id === verbId);
    if (!v || v.ghost(ctx) || !offeredHere(v)) return null;
    return {
      type: "item",
      id: v.id,
      label: label ?? verbLabel(v, ctx),
      glyph: v.glyph,
      ...(!compact && v.key ? { keycap: v.key } : {}),
      ghost: v.ghost(ctx),
      ...(v.checked ? { checked: v.checked(ctx) } : {}),
      onSelect: () => v.run(ctx),
    };
  };

  const goInputs = (): GoInputs => ({
    row: goRow,
    projects: projects ?? [],
    openProject: openProjectRoom,
    drawers: rootDirectories(useDesk.getState().items).map((d) => ({
      ref: qualifiedRef("directory", d.id), name: d.name,
    })),
    openDrawer: openScreenRef,
    launchers,
    builder,
  });
  const entries = (id: MenuId): WorkMenuEntry[] => {
    // Betterment shell S1: Go is the manifest's groups at both widths.
    if (compact && id === "go") return phoneGo(goInputs());
    if (id === "go") return deskGo(goInputs());
    const out: WorkMenuEntry[] = [];
    menuEntries(id, out);
    return out;
  };

  return (
    <nav ref={barRef} className="desk-verbbar" aria-label="Desk menus">
      {(compact ? titles.filter((m) => m.id === "go") : titles).map((m) => (
        <span key={m.id} className="desk-verbbar-item" data-menu-id={m.id}>
          <Button
            variant="chrome"
            className={`desk-verbbar-title${open === m.id ? " on" : ""}`}
            aria-haspopup="menu"
            aria-expanded={open === m.id}
            // The menu treats its opener as inside. This title owns the
            // pointer toggle; a sibling title opens its own menu.
            onPointerDown={(e) => {
              if (e.button !== 0) return;
              if (open === m.id) setOpen(null);
              else openMenu(m.id, e.currentTarget, true);
            }}
            onClick={(e) => {
              // Keyboard activation (Enter/Space) arrives as a click
              // with no preceding pointerdown.
              if (e.detail === 0 && open !== m.id)
                openMenu(m.id, e.currentTarget, true);
            }}
            // HS-148-01: hover-switch is NOT intentional — no autoFocus.
            onMouseEnter={(e) =>
              open && openMenu(m.id, e.currentTarget, false)
            }
          >
            {m.label}
          </Button>
          {!settled && open === m.id && (
            <WorkMenu
              className="desk-verbbar-menu"
              label={`${m.label} menu`}
              anchor="below"
              x={at.x}
              y={at.y}
              entries={entries(m.id)}
              onClose={() => setOpen(null)}
              opener={openerRef.current}
              autoFocus={intentional}
              menuContext={m.id === "go" ? "launcher" : "verb"}
            />
          )}
        </span>
      ))}
    </nav>
  );
}
