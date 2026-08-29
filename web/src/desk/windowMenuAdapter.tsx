/** HS-148-04 — head + dock menus derive from the verb registry.
 * One adapter, no parallel verb system — the registry is the single
 * source of label/keycap truth; onSelect dispatches to per-window
 * store methods (requestMinimize/requestClose/toggleMaximizePanel for
 * THIS window, not the front-window actions the registry verbs fire). */
import { verbById, verbLabel, type VerbContext } from "./verbRegistry";
import type { WorkMenuEntry } from "./components/DeskMenu";
import { VerbGlyph } from "./components/window/VerbGlyph";

const CTX: VerbContext = { selectedRef: null };

/** Build WorkMenuEntry[] for the window-head right-click menu.
 * Labels + keycaps come FROM the registry; onSelect dispatches to the
 * caller's per-window actions. WorkMenu calls onClose before onSelect,
 * so the adapter need not dismiss the menu itself. */
export function headMenuEntries(opts: {
  maximized: boolean;
  compact: boolean;
  requestMinimize: () => void;
  toggleMaximize: () => void;
  requestClose: () => void;
}): WorkMenuEntry[] {
  const entries: WorkMenuEntry[] = [];
  const minVerb = verbById("window.minimize");
  if (minVerb) {
    entries.push({
      type: "item",
      id: "window.minimize",
      label: verbLabel(minVerb, CTX),
      keycap: minVerb.key,
      glyph: <VerbGlyph kind="minimize" />,
      onSelect: opts.requestMinimize,
    });
  }
  if (!opts.compact) {
    const maxVerb = verbById("window.maximize");
    if (maxVerb) {
      entries.push({
        type: "item",
        id: "window.maximize",
        label: opts.maximized ? "Restore" : verbLabel(maxVerb, CTX),
        keycap: maxVerb.key,
        glyph: <VerbGlyph kind={opts.maximized ? "restore" : "maximize"} />,
        onSelect: opts.toggleMaximize,
      });
    }
  }
  const closeVerb = verbById("window.close");
  if (closeVerb) {
    entries.push({
      type: "item",
      id: "window.close",
      label: verbLabel(closeVerb, CTX),
      keycap: closeVerb.key,
      glyph: <VerbGlyph kind="close" />,
      onSelect: opts.requestClose,
    });
  }
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
