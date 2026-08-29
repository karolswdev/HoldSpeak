// HS-99-04 - the ONE menu vocabulary (DESIGN_SYSTEM.md, the chrome
// ladder): every desk popover - the room menu, the window-head menu,
// the dock chip menu - renders through this primitive, carrying the
// HS-96-05 keyboard pattern (roving arrows, Home/End, Escape with
// focus return) and the Workbench menu material.
// HS-111-07 - species v2 (WorkMenu): portal to the body (kills the
// chrome z-trap), separators, a right-aligned key column, type-ahead,
// and ONE-deep submenus (adjacent at 1440; at 393 a submenu REPLACES
// the panel with a back row - it never floats beside it).
// HS-148-01 - the grammar core: stipple ghosting, drawn keycap wells,
// checkable lane (menuitemcheckbox/menuitemradio), the lane law,
// recessed separators, ghost-reason collapse, submenu indicator.
import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";
import { VerbGlyph } from "./window/VerbGlyph";

/** HS-148-01: selector that finds ALL menu-item roles (menuitem,
 * menuitemcheckbox, menuitemradio) for keyboard navigation. */
const MENUITEM_SELECTOR =
  "[role='menuitem'],[role='menuitemcheckbox'],[role='menuitemradio']";

/** Type-ahead + roving-arrow keyboard grammar shared by every panel. */
function menuKeyDown(
  e: React.KeyboardEvent<HTMLElement>,
  onClose: () => void,
  returnFocus?: () => void,
) {
  const items = Array.from(
    e.currentTarget.querySelectorAll<HTMLElement>(MENUITEM_SELECTOR),
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
  menuContext,
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
  /** HS-148-02: panel-level context declaration for glyph gating. */
  menuContext?: string;
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
      data-menu-context={menuContext}
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
  checked,
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
  /** HS-148-01 - checkable: boolean = checkbox, "exclusive" = radio. */
  checked?: boolean | "exclusive";
  children: ReactNode;
}) {
  // HS-148-01: role is conditional on checkable props (counsel should-fix).
  const role =
    checked !== undefined
      ? checked === "exclusive"
        ? "menuitemradio"
        : "menuitemcheckbox"
      : "menuitem";
  const ariaChecked =
    checked !== undefined
      ? checked === true || checked === "exclusive"
        ? true
        : false
      : undefined;
  return (
    <button
      type="button"
      role={role}
      aria-label={ariaLabel}
      aria-disabled={disabled || undefined}
      aria-checked={ariaChecked}
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

/** HS-111-07 - the separator: a 1px rule between verb groups.
 * HS-148-01 - recessed: shadow + shine pair. */
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
      /** HS-148-01: checkable. boolean = checkbox, "exclusive" = radio. */
      checked?: boolean | "exclusive";
      onSelect(): void;
    }
  | { type: "sep"; id?: string }
  | {
      type: "sub";
      id: string;
      label: string;
      entries: WorkMenuEntry[];
      /** HS-148-02: override the parent panel's context for this submenu. */
      menuContext?: string;
    };

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

/** HS-148-01: render a keycap string as drawn keycap wells.
 * Each modifier/key character gets its own well. */
function KeycapWells({ keycap }: { keycap: string }) {
  // The keycap is already in symbol notation (e.g. "⌘N", "⌃⇧`", "F2").
  // Split into individual keys: each modifier symbol (⌘⇧⌃⌥) is one key,
  // remaining characters form the final key (handles "F2", "Delete", etc.).
  const parts: string[] = [];
  let rest = keycap;
  for (const ch of rest) {
    if ("⌘⇧⌃⌥".includes(ch)) {
      parts.push(ch);
    } else {
      break;
    }
  }
  const remainder = rest.slice(parts.length);
  if (remainder) parts.push(remainder);
  return (
    <span className="desk-menu-keycaps" aria-label={keycap}>
      {parts.map((k, i) => (
        <kbd key={i} className="desk-menu-well">
          {k}
        </kbd>
      ))}
    </span>
  );
}

/** HS-148-01: detect whether a panel's entries need the glyph/check lane.
 * Returns true if ANY item has a glyph or is checkable. */
function panelHasLane(entries: WorkMenuEntry[]): boolean {
  return entries.some(
    (e) =>
      e.type === "item" && (e.glyph != null || e.checked !== undefined),
  );
}

/** HS-148-01: compute ghost-reason MAJORITY collapse for a panel.
 * The single most common ghost reason, when it appears on >=3 ghosted
 * rows, collapses to the panel footer; rows carrying a DIFFERENT reason
 * keep their per-row echo. On tie, collapse only the first-encountered. */
function collapseGhostReason(
  entries: WorkMenuEntry[],
): string | null {
  const ghosts = entries.filter(
    (e): e is Extract<WorkMenuEntry, { type: "item" }> =>
      e.type === "item" && typeof e.ghost === "string",
  );
  if (ghosts.length < 3) return null;
  // Count occurrences, track first-encountered order.
  const counts = new Map<string, number>();
  for (const g of ghosts) {
    counts.set(g.ghost!, (counts.get(g.ghost!) ?? 0) + 1);
  }
  let best: string | null = null;
  let bestCount = 0;
  for (const [reason, count] of counts) {
    if (count > bestCount) {
      best = reason;
      bestCount = count;
    }
  }
  return bestCount >= 3 ? best : null;
}

function WorkMenuRows({
  entries,
  onClose,
  openSub,
  setOpenSub,
  onSubAnchor,
  hasLane,
  collapsedReason,
}: {
  entries: WorkMenuEntry[];
  onClose(): void;
  openSub: string | null;
  setOpenSub(id: string | null): void;
  onSubAnchor(id: string, el: HTMLElement): void;
  /** HS-148-01: lane law — every row reserves the lane when the panel has any. */
  hasLane: boolean;
  /** HS-148-01: collapsed ghost reason (null = show per-row reasons). */
  collapsedReason: string | null;
}) {
  const intent = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(
    () => () => {
      if (intent.current) clearTimeout(intent.current);
    },
    [],
  );
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
              {/* HS-148-01: lane law — sub rows reserve the lane too. */}
              {hasLane ? (
                <span className="desk-menu-glyph" aria-hidden="true" />
              ) : null}
              <span className="desk-menu-label">{entry.label}</span>
              <span className="desk-menu-submark" aria-hidden="true">
                {"»"}
              </span>
            </button>
          );
        }
        const ghost = entry.ghost ?? null;
        const isCheckable = entry.checked !== undefined;
        // HS-148-01: role is conditional on checkable props.
        const role = isCheckable
          ? entry.checked === "exclusive"
            ? "menuitemradio"
            : "menuitemcheckbox"
          : "menuitem";
        const ariaChecked = isCheckable
          ? entry.checked === true || entry.checked === "exclusive"
          : undefined;
        // HS-148-01: the glyph lane — checkable mark, entry glyph, or spacer.
        let laneMark: ReactNode = null;
        if (isCheckable && ariaChecked) {
          laneMark = (
            <span className="desk-menu-glyph" aria-hidden="true">
              <VerbGlyph
                kind={entry.checked === "exclusive" ? "dot" : "check"}
              />
            </span>
          );
        } else if (entry.glyph) {
          laneMark = (
            <span className="desk-menu-glyph" aria-hidden="true">
              {entry.glyph}
            </span>
          );
        } else if (hasLane) {
          // Lane law: reserve the column even when this row has nothing.
          laneMark = (
            <span className="desk-menu-glyph" aria-hidden="true" />
          );
        }
        // HS-148-01: per-row ghost reason — suppressed when collapsed.
        // HS-148-01: majority collapse — suppress per-row reason only
        // when it matches the collapsed majority; different reasons stay.
        const showPerRowReason = ghost && ghost !== collapsedReason;
        return (
          <button
            key={entry.id}
            type="button"
            role={role}
            aria-disabled={ghost ? true : undefined}
            aria-checked={ariaChecked}
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
            {laneMark}
            <span className="desk-menu-label">
              {entry.label}
              {showPerRowReason ? (
                <small className="quiet"> &middot; {ghost}</small>
              ) : null}
            </span>
            {/* HS-148-01: keycaps render on ghosted rows too (stippled with
                the row) — the `&& !ghost` suppression is removed. */}
            {entry.keycap ? <KeycapWells keycap={entry.keycap} /> : null}
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
  menuContext,
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
  /** HS-148-01: panel-level context declaration (mechanism — default "verb"). */
  menuContext?: string;
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
        ?.querySelector<HTMLElement>(MENUITEM_SELECTOR)
        ?.focus();
  }, [autoFocus]);

  // An adjacent submenu receives focus as it opens (ArrowLeft returns).
  useEffect(() => {
    if (openSub && subAt)
      subRef.current
        ?.querySelector<HTMLElement>(MENUITEM_SELECTOR)
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

  // HS-148-01: lane law + ghost collapse computed once per render.
  const hasLane = panelHasLane(entries);
  const collapsedReason = collapseGhostReason(entries);

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
      data-menu-context={menuContext || "verb"}
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
            {/* HS-148-01: the back row participates in the lane law. */}
            <span className="desk-menu-glyph" aria-hidden="true">
              {"◂"}
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
            hasLane={panelHasLane(sub.entries)}
            collapsedReason={collapseGhostReason(sub.entries)}
          />
        </>
      ) : (
        <WorkMenuRows
          entries={entries}
          onClose={onClose}
          openSub={openSub}
          setOpenSub={setOpenSub}
          onSubAnchor={onSubAnchor}
          hasLane={hasLane}
          collapsedReason={collapsedReason}
        />
      )}
      {/* HS-148-01: ghost-reason collapse footer. */}
      {collapsedReason && !narrow ? (
        <span className="desk-menu-ghost-hint">{collapsedReason}</span>
      ) : null}
      {!narrow && sub && subAt ? (
        <nav
          ref={subRef}
          className="desk-menu-list desk-work-menu desk-work-submenu is-below"
          role="menu"
          aria-label={`${sub.label} submenu`}
          style={clampStyle(subAt.x, subAt.y)}
          data-menu-context={sub.menuContext || menuContext || "verb"}
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
            hasLane={panelHasLane(sub.entries)}
            collapsedReason={collapseGhostReason(sub.entries)}
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
