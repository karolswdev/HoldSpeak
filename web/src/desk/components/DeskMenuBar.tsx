// HS-105-05 — the menu bar: the browsable face of the ONE verb registry.
// Menus derive from verbRegistry (never hardcode a verb here — the guard
// census enforces it); a verb that cannot run now is GHOSTED with its
// reason, never hidden: the system admits what it can do.
// HS-111-07 — dropdowns render through the WorkMenu portal: inside the
// chrome cluster they inherited the z-30 stacking context and windows
// (z-42) covered open menus. The OS's own voice draws OVER the programs
// it hosts, always.
import "./chrome-menus.css";
import { useEffect, useRef, useState } from "react";
import { useDesk } from "../store";
import {
  menuVerbs,
  verbLabel,
  type MenuId,
  type VerbContext,
} from "../verbRegistry";
import { WorkMenu, type WorkMenuEntry } from "./DeskMenu";

const MENUS: { id: MenuId; label: string }[] = [
  { id: "desk", label: "Desk" },
  { id: "object", label: "Object" },
  { id: "go", label: "Go" },
];

export function DeskMenuBar() {
  const [open, setOpen] = useState<MenuId | null>(null);
  const barRef = useRef<HTMLElement | null>(null);
  const [at, setAt] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const selectedIds = useDesk((s) => s.selectedIds);
  const ctx: VerbContext = {
    selectedRef: selectedIds.length === 1 ? selectedIds[0] : null,
  };
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

  const openMenu = (id: MenuId, el: HTMLElement) => {
    const r = el.getBoundingClientRect();
    setAt({ x: r.left, y: r.bottom });
    setOpen(id);
  };

  const entries = (id: MenuId): WorkMenuEntry[] => {
    const out: WorkMenuEntry[] = [];
    let lastGroup: string | undefined;
    for (const v of menuVerbs(id)) {
      if (out.length && v.group !== lastGroup)
        out.push({ type: "sep", id: `sep-${v.id}` });
      lastGroup = v.group;
      out.push({
        type: "item",
        id: v.id,
        label: verbLabel(v, ctx),
        keycap: v.key,
        ghost: v.ghost(ctx),
        onSelect: () => v.run(ctx),
      });
    }
    return out;
  };

  return (
    <nav ref={barRef} className="desk-verbbar" aria-label="Desk menus">
      {MENUS.map((m) => (
        <span key={m.id} className="desk-verbbar-item">
          <button
            type="button"
            className={`desk-verbbar-title${open === m.id ? " on" : ""}`}
            aria-haspopup="menu"
            aria-expanded={open === m.id}
            // Pointer-down (not click): the WorkMenu's own outside-press
            // close runs first on the document capture phase; the
            // render-time `open` here still names the state BEFORE that
            // close, so the same title toggles closed and a sibling
            // title hands over in one press.
            onPointerDown={(e) => {
              if (e.button !== 0) return;
              if (open === m.id) setOpen(null);
              else openMenu(m.id, e.currentTarget);
            }}
            onClick={(e) => {
              // Keyboard activation (Enter/Space) arrives as a click
              // with no preceding pointerdown.
              if (e.detail === 0 && open !== m.id)
                openMenu(m.id, e.currentTarget);
            }}
            onMouseEnter={(e) => open && openMenu(m.id, e.currentTarget)}
          >
            {m.label}
          </button>
          {open === m.id && (
            <WorkMenu
              className="desk-verbbar-menu"
              label={`${m.label} menu`}
              anchor="below"
              x={at.x}
              y={at.y}
              entries={entries(m.id)}
              onClose={() => setOpen(null)}
            />
          )}
        </span>
      ))}
    </nav>
  );
}
