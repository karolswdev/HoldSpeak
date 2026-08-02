// HS-99-04 - the ONE menu vocabulary (DESIGN_SYSTEM.md, the chrome
// ladder): every desk popover - the room menu, the window-head menu,
// the dock chip menu - renders through this primitive, carrying the
// HS-96-05 keyboard pattern (roving arrows, Home/End, Escape with
// focus return) and the Workbench menu material.
// HS-111-07 - species v2 (WorkMenu): portal to the body (kills the
// chrome z-trap), separators, a right-aligned key column, type-ahead,
// and ONE-deep submenus (adjacent at 1440; at 393 a submenu REPLACES
// the panel with a back row - it never floats beside it).
import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";

/** Type-ahead + roving-arrow keyboard grammar shared by every panel. */
function menuKeyDown(
  e: React.KeyboardEvent<HTMLElement>,
  onClose: () => void,
  returnFocus?: () => void,
) {
  const items = Array.from(
    e.currentTarget.querySelectorAll<HTMLElement>("[role='menuitem']"),
  );
  const at = items.indexOf(document.activeElement as HTMLElement);
  if (e.key === "ArrowDown" || e.key === "ArrowUp") {
    e.preventDefault();
    const step = e.key === "ArrowDown" ? 1 : -1;
    items[(at + step + items.length) % items.length]?.focus();
  } else if (e.key === "Escape") {
    e.preventDefault();
    e.stopPropagation();
    onClose();
    returnFocus?.();
  } else if (e.key === "Home") {
    e.preventDefault();
    items[0]?.focus();
  } else if (e.key === "End") {
    e.preventDefault();
    items[items.length - 1]?.focus();
  } else if (e.key.length === 1 && !e.metaKey && !e.ctrlKey && !e.altKey) {
    // Type-ahead: the next item (after the focused one) whose label
    // starts with the letter; wraps.
    const letter = e.key.toLocaleLowerCase();
    if (!/\S/.test(letter)) return;
    for (let step = 1; step <= items.length; step++) {
      const item = items[(at + step + items.length) % items.length];
      if (
        (item?.textContent ?? "")
          .trim()
          .toLocaleLowerCase()
          .startsWith(letter)
      ) {
        e.preventDefault();
        item.focus();
        return;
      }
    }
  }
}

export function DeskMenuList({
  className,
  label,
  style,
  anchor,
  onClose,
  returnFocus,
  onMouseLeave,
  children,
}: {
  className?: string;
  label?: string;
  style?: CSSProperties;
  /** Squares the corner nearest the anchor (the borrowed touch). */
  anchor?: "above" | "below";
  onClose(): void;
  /** Focus to restore when Escape closes the menu. */
  returnFocus?: () => void;
  onMouseLeave?: () => void;
  children: ReactNode;
}) {
  return (
    <nav
      className={
        "desk-menu-list" +
        (anchor ? ` is-${anchor}` : "") +
        (className ? ` ${className}` : "")
      }
      role="menu"
      aria-label={label}
      style={style}
      onMouseLeave={onMouseLeave}
      onPointerDown={(e) => e.stopPropagation()}
      onKeyDown={(e) => menuKeyDown(e, onClose, returnFocus)}
    >
      {children}
    </nav>
  );
}

export function DeskMenuItem({
  glyph,
  keycap,
  ariaLabel,
  onSelect,
  disabled,
  children,
}: {
  glyph?: ReactNode;
  /** Right-aligned key column (display only; the keymap binds). */
  keycap?: ReactNode;
  ariaLabel?: string;
  onSelect(): void;
  /** HS-105-05 - ghosting over hiding: a disabled item stays visible
   * (aria-disabled) and refuses to run; the caller renders the reason. */
  disabled?: boolean;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      role="menuitem"
      aria-label={ariaLabel}
      aria-disabled={disabled || undefined}
      className={disabled ? "is-ghost" : undefined}
      onClick={() => {
        if (!disabled) onSelect();
      }}
    >
      {glyph}
      {children}
      {keycap ? <kbd className="desk-menu-key">{keycap}</kbd> : null}
    </button>
  );
}

/** HS-111-07 - the separator: a 1px rule between verb groups. */
export function WorkMenuSep() {
  return <span role="separator" className="desk-menu-sep" />;
}

/* ── WorkMenu: the data-driven face of the species ────────────────── */

export type WorkMenuEntry =
  | {
      type: "item";
      id: string;
      label: string;
      glyph?: ReactNode;
      keycap?: string;
      /** null/undefined = runnable; a string = ghosted WITH that reason. */
      ghost?: string | null;
      onSelect(): void;
    }
  | { type: "sep"; id?: string }
  | { type: "sub"; id: string; label: string; entries: WorkMenuEntry[] };

const SUB_HOVER_INTENT_MS = 120;
const NARROW = () =>
  typeof window !== "undefined" && window.innerWidth <= 720;

function clampStyle(x: number, y: number): CSSProperties {
  if (NARROW()) {
    // The phone panel: full-width, pinned above the safe band.
    return {
      position: "fixed",
      left: 8,
      right: 8,
      top: Math.min(y, window.innerHeight - 280),
    };
  }
  return {
    position: "fixed",
    left: Math.min(x, (window.innerWidth || 1280) - 232),
    top: Math.min(y, (window.innerHeight || 800) - 320),
  };
}

function WorkMenuRows({
  entries,
  onClose,
  openSub,
  setOpenSub,
  onSubAnchor,
}: {
  entries: WorkMenuEntry[];
  onClose(): void;
  openSub: string | null;
  setOpenSub(id: string | null): void;
  onSubAnchor(id: string, el: HTMLElement): void;
}) {
  const intent = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => () => {
    if (intent.current) clearTimeout(intent.current);
  }, []);
  return (
    <>
      {entries.map((entry, i) => {
        if (entry.type === "sep")
          return <WorkMenuSep key={entry.id ?? `sep-${i}`} />;
        if (entry.type === "sub") {
          return (
            <button
              key={entry.id}
              type="button"
              role="menuitem"
              aria-haspopup="menu"
              aria-expanded={openSub === entry.id}
              className={openSub === entry.id ? "is-subopen" : undefined}
              onPointerEnter={(e) => {
                const el = e.currentTarget;
                if (intent.current) clearTimeout(intent.current);
                intent.current = setTimeout(() => {
                  onSubAnchor(entry.id, el);
                  setOpenSub(entry.id);
                }, SUB_HOVER_INTENT_MS);
              }}
              onPointerLeave={() => {
                if (intent.current) clearTimeout(intent.current);
              }}
              onKeyDown={(e) => {
                if (e.key === "ArrowRight" || e.key === "Enter") {
                  e.preventDefault();
                  e.stopPropagation();
                  onSubAnchor(entry.id, e.currentTarget);
                  setOpenSub(entry.id);
                }
              }}
              onClick={(e) => {
                onSubAnchor(entry.id, e.currentTarget);
                setOpenSub(openSub === entry.id ? null : entry.id);
              }}
            >
              <span className="desk-menu-label">{entry.label}</span>
              <span className="desk-menu-submark" aria-hidden="true">
                ▸
              </span>
            </button>
          );
        }
        const ghost = entry.ghost ?? null;
        return (
          <button
            key={entry.id}
            type="button"
            role="menuitem"
            aria-disabled={ghost ? true : undefined}
            className={ghost ? "is-ghost" : undefined}
            onPointerEnter={() => {
              if (intent.current) clearTimeout(intent.current);
              // Sliding onto a plain item retires an open submenu.
              intent.current = setTimeout(
                () => setOpenSub(null),
                SUB_HOVER_INTENT_MS,
              );
            }}
            onPointerLeave={() => {
              if (intent.current) clearTimeout(intent.current);
            }}
            onClick={() => {
              if (ghost) return;
              onClose();
              entry.onSelect();
            }}
          >
            {entry.glyph ? (
              <span className="desk-menu-glyph" aria-hidden="true">
                {entry.glyph}
              </span>
            ) : null}
            <span className="desk-menu-label">
              {entry.label}
              {ghost ? <small className="quiet"> · {ghost}</small> : null}
            </span>
            {entry.keycap && !ghost ? (
              <kbd className="desk-menu-key">{entry.keycap}</kbd>
            ) : null}
          </button>
        );
      })}
    </>
  );
}

/** The portal panel: one species for menubar dropdowns, the mark menu,
 * object/zone context menus, and the floor menu. Position is a fixed
 * point (context menus) or an anchor rect edge (dropdowns). */
export function WorkMenu({
  label,
  x,
  y,
  className,
  anchor = "below",
  entries,
  onClose,
  returnFocus,
  autoFocus,
}: {
  label: string;
  x: number;
  y: number;
  className?: string;
  anchor?: "above" | "below";
  entries: WorkMenuEntry[];
  onClose(): void;
  returnFocus?: () => void;
  autoFocus?: boolean;
}) {
  const [openSub, setOpenSub] = useState<string | null>(null);
  const [subAt, setSubAt] = useState<{ x: number; y: number } | null>(null);
  const panelRef = useRef<HTMLElement | null>(null);
  const subRef = useRef<HTMLElement | null>(null);

  // The desktop dismissal rule: any outside pointer-down, Escape from
  // anywhere. Capture phase so a press on the world canvas closes too.
  useEffect(() => {
    const down = (e: PointerEvent) => {
      const t = e.target as Node;
      if (!panelRef.current?.contains(t)) onClose();
    };
    document.addEventListener("pointerdown", down, true);
    return () => document.removeEventListener("pointerdown", down, true);
  }, [onClose]);

  useEffect(() => {
    if (autoFocus)
      panelRef.current
        ?.querySelector<HTMLElement>("[role='menuitem']")
        ?.focus();
  }, [autoFocus]);

  // An adjacent submenu receives focus as it opens (ArrowLeft returns).
  useEffect(() => {
    if (openSub && subAt)
      subRef.current
        ?.querySelector<HTMLElement>("[role='menuitem']")
        ?.focus();
  }, [openSub, subAt]);

  const sub = useMemo(
    () =>
      openSub
        ? (entries.find(
            (e) => e.type === "sub" && e.id === openSub,
          ) as Extract<WorkMenuEntry, { type: "sub" }> | undefined)
        : undefined,
    [entries, openSub],
  );
  const narrow = NARROW();

  const onSubAnchor = (_id: string, el: HTMLElement) => {
    const r = el.getBoundingClientRect();
    setSubAt({ x: r.right + 1, y: r.top - 3 });
  };

  const panel = (
    <nav
      ref={panelRef}
      className={
        "desk-menu-list desk-work-menu" +
        ` is-${anchor}` +
        (className ? ` ${className}` : "")
      }
      role="menu"
      aria-label={label}
      style={clampStyle(x, y)}
      onPointerDown={(e) => e.stopPropagation()}
      onKeyDown={(e) => {
        if (openSub && e.key === "ArrowLeft") {
          e.preventDefault();
          e.stopPropagation();
          setOpenSub(null);
          return;
        }
        if (e.key === "Escape" && openSub) {
          // Escape closes the WHOLE tree (one law).
          e.preventDefault();
          e.stopPropagation();
          onClose();
          returnFocus?.();
          return;
        }
        menuKeyDown(e, onClose, returnFocus);
      }}
    >
      {narrow && sub ? (
        // 393: the submenu REPLACES the panel; a back row leads.
        <>
          <button
            type="button"
            role="menuitem"
            className="desk-menu-back"
            onClick={() => setOpenSub(null)}
          >
            <span className="desk-menu-glyph" aria-hidden="true">
              ◂
            </span>
            <span className="desk-menu-label">{sub.label}</span>
          </button>
          <WorkMenuSep />
          <WorkMenuRows
            entries={sub.entries}
            onClose={onClose}
            openSub={null}
            setOpenSub={() => {}}
            onSubAnchor={() => {}}
          />
        </>
      ) : (
        <WorkMenuRows
          entries={entries}
          onClose={onClose}
          openSub={openSub}
          setOpenSub={setOpenSub}
          onSubAnchor={onSubAnchor}
        />
      )}
      {!narrow && sub && subAt ? (
        <nav
          ref={subRef}
          className="desk-menu-list desk-work-menu desk-work-submenu is-below"
          role="menu"
          aria-label={`${sub.label} submenu`}
          style={clampStyle(subAt.x, subAt.y)}
          onKeyDown={(e) => {
            // The submenu owns its own keys; never let them bubble to
            // the parent panel (whose item query would move focus twice).
            if (e.key === "ArrowLeft") {
              e.preventDefault();
              e.stopPropagation();
              setOpenSub(null);
              panelRef.current
                ?.querySelector<HTMLElement>("[aria-haspopup='menu']")
                ?.focus();
              return;
            }
            menuKeyDown(e, onClose, returnFocus);
            e.stopPropagation();
          }}
        >
          <WorkMenuRows
            entries={sub.entries}
            onClose={onClose}
            openSub={null}
            setOpenSub={() => {}}
            onSubAnchor={() => {}}
          />
        </nav>
      ) : null}
    </nav>
  );
  // Portal INSIDE the desk root when it exists: the Workbench menu
  // material is scoped `.desk-next .desk-menu-list`.
  return createPortal(
    panel,
    document.getElementById("desk-next") ?? document.body,
  );
}
