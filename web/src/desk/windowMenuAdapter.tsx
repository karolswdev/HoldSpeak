/** HS-148-04 — head + dock menus derive from the verb registry.
 * One adapter, no parallel verb system — the registry is the single
 * source of label/keycap truth; onSelect dispatches to per-window
 * store methods (requestMinimize/requestClose/toggleMaximizePanel for
 * THIS window, not the front-window actions the registry verbs fire). */
import { verbById, verbLabel, type VerbContext } from "./verbRegistry";
import type { WorkMenuEntry } from "./components/DeskMenu";
import { VerbGlyph } from "./components/window/VerbGlyph";
import { GadgetGlyph } from "./components/window/GadgetGlyph";

const CTX: VerbContext = { selectedRef: null };

/** PHILO-13-12 (C2) — the registry verbs the window menu's Desk ▸ and
 * Go ▸ carry (board C1-2b: the canvas's choice, verbatim). */
export const WINDOW_MENU_DESK = [
  "desk.new-note",
  "desk.new-decision",
  "system.search",
  "system.sheet",
] as const;
export const WINDOW_MENU_GO = [
  "desk.open-intelligence",
  "desk.open-people",
  "desk.overview",
] as const;

function registryItem(id: string): WorkMenuEntry | null {
  const v = verbById(id);
  if (!v) return null;
  return {
    type: "item",
    id: v.id,
    label: verbLabel(v, CTX),
    keycap: v.key,
    ghost: v.ghost(CTX),
    onSelect: () => v.run(CTX),
  };
}

function registrySub(id: string, label: string, ids: readonly string[]): WorkMenuEntry {
  return {
    type: "sub",
    id,
    label,
    entries: ids
      .map(registryItem)
      .filter((e): e is WorkMenuEntry => e !== null),
  };
}

/** Build WorkMenuEntry[] for the window's right-button menu: the active
 * window's menu bar (PHILO-13-12, C2; board C1-2b). Iconify, Zoom,
 * To back, Close window, then Desk ▸ and Go ▸. Labels + keycaps
 * come FROM the registry (⌘ stands for the Amiga key); onSelect
 * dispatches to the caller's per-window actions. WorkMenu calls onClose
 * before onSelect, so the adapter need not dismiss the menu itself.
 * At 393 a window fills the work area: Zoom stays, ghosted with the
 * registry's reason. */
export function headMenuEntries(opts: {
  maximized: boolean;
  compact: boolean;
  requestMinimize: () => void;
  toggleMaximize: () => void;
  requestClose: () => void;
  toBack?: () => void;
}): WorkMenuEntry[] {
  const entries: WorkMenuEntry[] = [];
  const minVerb = verbById("window.minimize");
  if (minVerb) {
    entries.push({
      type: "item",
      id: "window.minimize",
      label: verbLabel(minVerb, CTX),
      keycap: minVerb.key,
      glyph: <GadgetGlyph kind="iconify" />,
      onSelect: opts.requestMinimize,
    });
  }
  const zoomVerb = verbById("window.maximize");
  if (zoomVerb) {
    entries.push({
      type: "item",
      id: "window.maximize",
      label: verbLabel(zoomVerb, CTX),
      keycap: zoomVerb.key,
      glyph: <GadgetGlyph kind="zoom" />,
      ghost: opts.compact ? "Fills the screen" : null,
      onSelect: opts.toggleMaximize,
    });
  }
  const depthVerb = verbById("window.depth");
  if (depthVerb && opts.toBack) {
    entries.push({
      type: "item",
      id: "window.depth",
      label: verbLabel(depthVerb, CTX),
      keycap: depthVerb.key,
      glyph: <GadgetGlyph kind="depth" />,
      onSelect: opts.toBack,
    });
  }
  const closeVerb = verbById("window.close");
  if (closeVerb) {
    entries.push(
      { type: "sep", id: "window-sep" },
      {
        type: "item",
        id: "window.close",
        label: verbLabel(closeVerb, CTX),
        keycap: closeVerb.key,
        glyph: <GadgetGlyph kind="close" />,
        onSelect: opts.requestClose,
      },
    );
  }
  entries.push(
    { type: "sep", id: "bar-sep" },
    registrySub("bar-desk", "Desk", WINDOW_MENU_DESK),
    registrySub("bar-go", "Go", WINDOW_MENU_GO),
  );
  return entries;
}

/** Build WorkMenuEntry[] for the dock chip context menu.
 * Same registry derivation; Restore/Minimize toggles on minimized state. */
export function dockChipMenuEntries(opts: {
  minimized: boolean;
  restore: () => void;
  minimize: () => void;
  close: () => void;
}): WorkMenuEntry[] {
  const entries: WorkMenuEntry[] = [];
  const minVerb = verbById("window.minimize");
  if (minVerb) {
    entries.push({
      type: "item",
      id: "window.minimize",
      label: opts.minimized ? "Restore" : verbLabel(minVerb, CTX),
      keycap: minVerb.key,
      glyph: <VerbGlyph kind={opts.minimized ? "restore" : "minimize"} />,
      onSelect: () => {
        if (opts.minimized) opts.restore();
        else opts.minimize();
      },
    });
  }
  const closeVerb = verbById("window.close");
  if (closeVerb) {
    entries.push({
      type: "item",
      id: "window.close",
      label: verbLabel(closeVerb, CTX),
      keycap: closeVerb.key,
      glyph: <VerbGlyph kind="close" />,
      onSelect: opts.close,
    });
  }
  return entries;
}
