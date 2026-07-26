// HS-105-05 — the menu bar: the browsable face of the ONE verb registry.
// Menus derive from verbRegistry (never hardcode a verb here — the guard
// census enforces it); a verb that cannot run now is GHOSTED with its
// reason, never hidden: the system admits what it can do.
import { useEffect, useRef, useState } from "react";
import { useDesk } from "../store";
import { menuVerbs, type MenuId, type VerbContext } from "../verbRegistry";
import { DeskMenuItem, DeskMenuList } from "./DeskMenu";

const MENUS: { id: MenuId; label: string }[] = [
  { id: "desk", label: "Desk" },
  { id: "object", label: "Object" },
  { id: "go", label: "Go" },
];

export function DeskMenuBar() {
  const [open, setOpen] = useState<MenuId | null>(null);
  const barRef = useRef<HTMLElement | null>(null);
  const selectedIds = useDesk((s) => s.selectedIds);
  const ctx: VerbContext = {
    selectedRef: selectedIds.length === 1 ? selectedIds[0] : null,
  };
  // The desktop dismissal rule (caught live by the 105-05 walk): an open
  // menu closes on ANY outside pointer-down and on Escape from anywhere.
  useEffect(() => {
    if (!open) return;
    const down = (e: PointerEvent) => {
      if (!barRef.current?.contains(e.target as Node)) setOpen(null);
    };
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(null);
    };
    document.addEventListener("pointerdown", down, true);
    document.addEventListener("keydown", key, true);
    return () => {
      document.removeEventListener("pointerdown", down, true);
      document.removeEventListener("keydown", key, true);
    };
  }, [open]);
  return (
    <nav ref={barRef} className="desk-verbbar" aria-label="Desk menus">
      {MENUS.map((m) => (
        <span key={m.id} className="desk-verbbar-item">
          <button
            type="button"
            className={`desk-verbbar-title${open === m.id ? " on" : ""}`}
            aria-haspopup="menu"
            aria-expanded={open === m.id}
            onClick={() => setOpen(open === m.id ? null : m.id)}
            onMouseEnter={() => open && setOpen(m.id)}
          >
            {m.label}
          </button>
          {open === m.id && (
            <DeskMenuList
              className="desk-verbbar-menu"
              label={`${m.label} menu`}
              anchor="below"
              onClose={() => setOpen(null)}
            >
              {menuVerbs(m.id).map((v) => {
                const ghost = v.ghost(ctx);
                return (
                  <DeskMenuItem
                    key={v.id}
                    disabled={Boolean(ghost)}
                    onSelect={() => {
                      setOpen(null);
                      if (!ghost) v.run(ctx);
                    }}
                  >
                    <span className="desk-verbbar-verb">
                      {v.label}
                      {ghost ? (
                        <small className="quiet"> · {ghost}</small>
                      ) : v.key ? (
                        <small className="quiet"> {v.key}</small>
                      ) : null}
                    </span>
                  </DeskMenuItem>
                );
              })}
            </DeskMenuList>
          )}
        </span>
      ))}
    </nav>
  );
}
