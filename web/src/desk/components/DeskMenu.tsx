// HS-99-04 - the ONE menu vocabulary (DESIGN_SYSTEM.md, the chrome
// ladder): every desk popover - the room menu, the window-head menu,
// the dock chip menu - renders through this primitive, carrying the
// HS-96-05 keyboard pattern (roving arrows, Home/End, Escape with
// focus return) and the Workbench menu material.
// HS-111-07 - species v2 (WorkMenu): portal to the body (kills the
// chrome z-trap), separators, a right-aligned key column, type-ahead,
// and ONE-deep submenus (adjacent at 1440; at 393 a submenu REPLACES
// the panel with a back row - it never floats beside it).
// HS-148-01 - the grammar core: drawn keycap wells, checkable lane
// (menuitemcheckbox/menuitemradio), the lane law, recessed separators,
// submenu indicator.
// PHILO-13-15 (C5) - at 393 a submenu inside a submenu opens (the back row
// climbs one level); at 1440 a submenu opens next to its parent panel.
// Betterment shell S0 (UX-CANON A.11, "withhold, never ghost"): a WorkMenu
// entry whose `ghost` is a string is not drawn. The stipple and the
// ghost-reason footer are gone; `ghost` stays on the entry (the registry,
// the keys and the tests read it), and the menu shows only rows that run.
import {
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";
import { Button } from "../../components/signal/Signal";
import { VerbGlyph } from "./window/VerbGlyph";

/** HS-148-01: each live menu-item role participates in focus and keys.
 * A disabled first item cannot receive the autofocus attempt. */
const MENUITEM_SELECTOR =
  "[role='menuitem']:not(:disabled),[role='menuitemcheckbox']:not(:disabled),[role='menuitemradio']:not(:disabled)";

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
  /** A disabled item refuses to run (aria-disabled). UX-CANON A.11
   * ("withhold, never ghost"): a caller withholds a verb that cannot run;
   * it does not pass it here disabled. */
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
    <Button
      variant="chrome"
      role={role}
      aria-label={ariaLabel}
      aria-disabled={disabled || undefined}
      aria-checked={ariaChecked}
      onClick={() => {
        if (!disabled) onSelect();
      }}
    >
      {glyph}
      {children}
      {keycap && !NARROW() ? <kbd className="desk-menu-key">{keycap}</kbd> : null}
    </Button>
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
      title?: string;
      /** null/undefined = runnable; a string = ghosted WITH that reason. */
      ghost?: string | null;
      /** Selection verbs stay visible when no row is selected. */
      disabled?: boolean;
      /** HS-148-01: checkable. boolean = checkbox, "exclusive" = radio. */
      checked?: boolean | "exclusive";
      onSelect(): void;
    }
  | { type: "sep"; id?: string }
  /** One line of plain text that is not a verb ("No windows open"). */
  | { type: "note"; id: string; label: string }
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

/** Start at the anchor; the measured layout below decides the available seat. */
function menuStyle(x: number, y: number): CSSProperties {
  return {position: "fixed", left: x, top: y};
}

/** HS-148-01: render a keycap string as drawn keycap wells.
 * Each modifier/key character gets its own well. */
export function KeycapWells({ keycap }: { keycap: string }) {
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

/** Betterment shell S0 (UX-CANON A.11): the rows a menu draws. An item
 * whose `ghost` is a string is withheld; a submenu left empty goes with it;
 * separators never lead, trail or double. Pure. */
export function withholdGhosts(entries: readonly WorkMenuEntry[]): WorkMenuEntry[] {
  const out: WorkMenuEntry[] = [];
  for (const entry of entries) {
    if (entry.type === "item" && typeof entry.ghost === "string") continue;
    if (entry.type === "sub") {
      const inner = withholdGhosts(entry.entries);
      if (!inner.some((e) => e.type !== "sep")) continue;
      out.push({ ...entry, entries: inner });
      continue;
    }
    if (entry.type === "sep" && (!out.length || out[out.length - 1].type === "sep")) continue;
    out.push(entry);
  }
  while (out.length && out[out.length - 1].type === "sep") out.pop();
  return out;
}

function WorkMenuRows({
  entries,
  onClose,
  openSub,
  setOpenSub,
  onSubAnchor,
  hasLane,
}: {
  entries: WorkMenuEntry[];
  onClose(): void;
  openSub: string | null;
  setOpenSub(id: string | null): void;
  onSubAnchor(id: string, el: HTMLElement): void;
  /** HS-148-01: lane law — every row reserves the lane when the panel has any. */
  hasLane: boolean;
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
        if (entry.type === "note")
          return (
            <span key={entry.id} className="desk-menu-note" role="none">
              {entry.label}
            </span>
          );
        if (entry.type === "sub") {
          return (
            <Button
              key={entry.id}
              variant="chrome"
              role="menuitem"
              aria-haspopup="menu"
              aria-expanded={openSub === entry.id}
              className={openSub === entry.id ? "is-subopen" : ""}
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
            </Button>
          );
        }
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
        return (
          <Button
            key={entry.id}
            variant="chrome"
            role={role}
            title={entry.title}
            aria-checked={ariaChecked}
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
            disabled={entry.disabled}
            onClick={() => {
              if (entry.disabled) return;
              onClose();
              entry.onSelect();
            }}
          >
            {laneMark}
            <span className="desk-menu-label">{entry.label}</span>
            {/* PHILO-15 11 (B21): a phone has no ⌘ key, so no menu at 393
                draws a keycap (the window menu and its Desk ▸ too). */}
            {entry.keycap && !NARROW() ? <KeycapWells keycap={entry.keycap} /> : null}
          </Button>
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
  entries: given,
  onClose,
  opener: suppliedOpener,
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
  /** The title Button owns its own toggle; its press is inside this menu. */
  opener?: HTMLElement | null;
  returnFocus?: () => void;
  autoFocus?: boolean;
  /** HS-148-01: panel-level context declaration (mechanism — default "verb"). */
  menuContext?: string;
}) {
  // Older point-opened menus still belong to the object under their anchor.
  // Capture it before the portal paints; explicit openers keep their identity.
  const opener = useMemo(() => {
    if (suppliedOpener) return suppliedOpener;
    const focused = document.activeElement;
    if (focused instanceof HTMLElement && focused !== document.body && focused !== document.documentElement && !focused.closest(".desk-work-menu")) {
      const box = focused.getBoundingClientRect();
      if (box.width && x >= box.left-1 && x <= box.right+1 && y >= box.top-1 && y <= box.bottom+1) return focused;
    }
    return document.elementsFromPoint?.(x,y).find(node => node instanceof HTMLElement && !node.closest(".desk-work-menu")) as HTMLElement | undefined;
  }, [suppliedOpener,x,y]);
  const owner = opener?.closest<HTMLElement>('[data-layer="window"][data-guide-running]') ?? null;
  const ownerBox = owner?.getBoundingClientRect();
  const guideStyle: CSSProperties | null = ownerBox ? {
    position: "absolute", left: x-ownerBox.left, top: y-ownerBox.top,
    width: NARROW() ? Math.min(ownerBox.width-16, innerWidth-16) : undefined,
    zIndex: "var(--desk-z-local)",
  } : null;
  // Betterment shell S0 (UX-CANON A.11): only the rows that run are drawn.
  const entries = withholdGhosts(given);
  const [openSub, setOpenSub] = useState<string | null>(null);
  // PHILO-13-15 (C5, Astra canvas r1 condition 2): at 393 a submenu inside a
  // submenu opens too (Go ▸ Object ▸ Send to ▸). `deeper` is the path below
  // `openSub`; the back row climbs one level.
  const [deeper, setDeeper] = useState<string[]>([]);
  useEffect(() => { setDeeper([]); }, [openSub]);
  const [subAt, setSubAt] = useState<{ x: number; y: number } | null>(null);
  const panelRef = useRef<HTMLElement | null>(null);
  const subRef = useRef<HTMLElement | null>(null);
  const subOpener = useRef<HTMLElement | null>(null);

  // One measured placement for every menu. Protected rows split the owner
  // window into free seats; fitting never clamps a panel back over a row.
  useLayoutEffect(() => {
    const place = () => {
      const windowOwner = opener?.closest<HTMLElement>('[data-layer="window"]');
      const windowBox = windowOwner?.getBoundingClientRect();
      const margin = 8;
      const bounds = {
        left: Math.max(margin, (windowBox?.left ?? 0) + margin),
        right: Math.min(innerWidth - margin, (windowBox?.right ?? innerWidth) - margin),
        top: Math.max(margin, (windowBox?.top ?? 0) + margin),
        bottom: Math.min(innerHeight - margin, (windowBox?.bottom ?? innerHeight) - margin),
      };
      // A nested list toolbar can belong to a whole labelled form row.
      const row = opener?.closest<HTMLElement>('.gadget-row') ?? opener?.closest<HTMLElement>('[role="row"], [role="listitem"], .kit-toolbar, .surface-pane-actions, .desk-pullout-head, [role="menubar"]') ?? opener?.closest<HTMLElement>('button, [role="button"], [data-object-id], [data-object-ref]');
      const edge = row?.getBoundingClientRect() ?? {top: y, bottom: y, left: x, right: x};
      const protectedNodes = new Set<HTMLElement>(row ? [row] : []);
      if (!windowOwner) document.querySelectorAll<HTMLElement>(".desk-menubar, .desk-dock").forEach(node => protectedNodes.add(node));
      windowOwner?.querySelectorAll<HTMLElement>('.desk-pullout-head, [role="tablist"], .object-list-head, .object-list-inner-toolbar, .object-list-row[aria-selected="true"]').forEach(node => protectedNodes.add(node));
      const protectedRects = [...protectedNodes].map(node => node.getBoundingClientRect()).filter(rect => rect.width > 0 && rect.height > 0 && rect.bottom > bounds.top && rect.top < bounds.bottom);
      const keepInView = (el: HTMLElement | null, parent?: DOMRect) => {
        if (!el) return;
        el.style.boxSizing = "border-box";
        el.style.maxWidth = `${Math.max(0, bounds.right-bounds.left)}px`;
        el.style.width = NARROW() ? `${Math.max(0,bounds.right-bounds.left)}px` : "max-content";
        el.style.maxHeight = "none";
        el.style.overflowY = "auto";
        const size = el.getBoundingClientRect();
        const left = parent
          ? parent.right + 1 + size.width <= bounds.right ? parent.right + 1 : Math.max(bounds.left,parent.left-size.width-1)
          : Math.max(bounds.left,Math.min(x,bounds.right-size.width));
        const beside = Boolean(parent && (left >= parent.right || left+size.width <= parent.left));
        const reference = parent ? subOpener.current?.getBoundingClientRect() ?? edge : edge;
        const avoid = parent && !beside ? [...protectedRects,parent] : protectedRects;
        const obstacles = avoid.filter(rect => rect.right > left && rect.left < left+size.width).sort((a,b) => a.top-b.top);
        let start = bounds.top;
        const gaps: {top: number; bottom: number}[] = [];
        for (const rect of obstacles) {
          if (rect.top-1 > start) gaps.push({top:start,bottom:Math.min(bounds.bottom,rect.top-1)});
          start = Math.max(start,rect.bottom+1);
        }
        if (start < bounds.bottom) gaps.push({top:start,bottom:bounds.bottom});
        const below = gaps.map(gap=>({...gap,top:Math.max(gap.top,reference.bottom+1)})).filter(gap=>gap.bottom>gap.top);
        const above = gaps.map(gap=>({...gap,bottom:Math.min(gap.bottom,reference.top-1)})).filter(gap=>gap.bottom>gap.top).reverse();
        const preferred = anchor === "above" ? [...above,...below] : [...below,...above];
        const height = size.height;
        // Full panels flip before they scroll. If neither side fits, use the
        // largest free seat, preserving every item through internal scrolling.
        const alignedTop = (gap: {top: number; bottom: number}) => Math.max(gap.top,Math.min(reference.top,gap.bottom-height));
        const alongside = beside ? gaps.filter(gap=>gap.bottom-gap.top >= height)
          .sort((a,b)=>Math.abs(alignedTop(a)-reference.top)-Math.abs(alignedTop(b)-reference.top))[0] : undefined;
        const seat = alongside
          ?? preferred.find(gap=>gap.bottom-gap.top >= height)
          ?? [...preferred].sort((a,b)=>(b.bottom-b.top)-(a.bottom-a.top))[0]
          ?? gaps[0];
        const room = seat ? seat.bottom-seat.top : 0;
        const style = getComputedStyle(el);
        const foot = (parseFloat(style.paddingBottom)||0)+(parseFloat(style.borderBottomWidth)||0);
        const endings = [...el.querySelectorAll<HTMLElement>(":scope > [role^=menuitem], :scope > [role=none]")]
          .map(item=>item.getBoundingClientRect().bottom-size.top+foot).filter(end=>end<=room);
        const fitted = height <= room ? height : endings.at(-1) ?? room;
        const top = alongside ? alignedTop(alongside)
          : seat ? seat.bottom <= reference.top ? seat.bottom-fitted : seat.top
          : bounds.top;
        el.style.scrollPaddingTop = style.paddingTop;
        el.style.scrollPaddingBottom = style.paddingBottom;
        el.style.left = `${left-(ownerBox?.left ?? 0)}px`;
        el.style.top = `${top-(ownerBox?.top ?? 0)}px`;
        el.style.maxHeight = `${fitted}px`;
      };
      keepInView(panelRef.current);
      keepInView(subRef.current,panelRef.current?.getBoundingClientRect());
    };
    place();
    const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(place);
    if (opener) observer?.observe(opener.closest('[data-layer="window"]') ?? opener);
    window.addEventListener("resize",place);
    document.fonts?.addEventListener("loadingdone",place);
    return () => {observer?.disconnect();window.removeEventListener("resize",place);document.fonts?.removeEventListener("loadingdone",place);};
  });

  // The desktop dismissal rule: any outside pointer-down, Escape from
  // anywhere. Capture phase so a press on the world canvas closes too.
  useEffect(() => {
    const down = (e: PointerEvent) => {
      const t = e.target as Node;
      // Guide actions keep their disclosed menu visible until Next/Stop.
      if (t instanceof Element && t.closest("[data-guide-layer]")?.parentElement === opener?.closest('[data-layer="window"]')) return;
      if (!panelRef.current?.contains(t) && !opener?.contains(t)) onClose();
    };
    // The menu owns Escape even before its deferred focus settles.
    const key = (event: KeyboardEvent) => {
      if (event.key !== "Escape" || event.defaultPrevented) return;
      event.preventDefault(); event.stopPropagation();
      onClose(); returnFocus?.();
    };
    document.addEventListener("pointerdown", down, true);
    document.addEventListener("keydown", key, true);
    return () => {
      document.removeEventListener("pointerdown", down, true);
      document.removeEventListener("keydown", key, true);
    };
  }, [onClose, opener, returnFocus]);

  // HS-148-01 D3 repair: defer focus past the browser's native click-to-focus.
  // On a real pointer-down open, the browser's click sequence
  // (pointerdown -> mousedown -> focus -> mouseup -> click) focuses the
  // bar title button AFTER React's synchronous useEffect runs .focus().
  // A double-rAF escapes the browser's focus-assignment frame so the
  // menu item wins. Keyboard opens (Enter/Space) are unaffected but the
  // deferral is harmless there.
  useEffect(() => {
    if (!autoFocus) return;
    const id = requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        panelRef.current
          ?.querySelector<HTMLElement>(MENUITEM_SELECTOR)
          ?.focus();
      });
    });
    return () => cancelAnimationFrame(id);
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
  // 393: the deepest submenu on the path that still resolves (a re-render
  // that drops a nested submenu falls back to its parent).
  const current = useMemo(() => {
    let at = sub;
    for (const id of deeper) {
      const next = at?.entries.find((e) => e.type === "sub" && e.id === id) as
        | Extract<WorkMenuEntry, { type: "sub" }>
        | undefined;
      if (!next) break;
      at = next;
    }
    return at;
  }, [sub, deeper]);
  const openDeeper = (id: string | null) => {
    if (!id) return;
    setDeeper((d) => (d[d.length - 1] === id ? d : [...d, id]));
  };

  const onSubAnchor = (_id: string, el: HTMLElement) => {
    subOpener.current = el;
    const r = el.getBoundingClientRect();
    setSubAt({ x: r.right + 1, y: r.top - 3 });
  };

  // HS-148-01: lane law computed once per render.
  const hasLane = panelHasLane(entries);

  const panel = (
    <nav
      ref={panelRef}
      className={
        "desk-menu-list desk-work-menu" +
        ` is-${anchor}` +
        (className ? ` ${className}` : "")
      }
      role="menu"
      aria-label={narrow && current ? `${current.label} submenu` : label}
      style={guideStyle ?? menuStyle(x, y)}
      data-menu-context={menuContext || "verb"}
      data-menu-owner={opener?.closest('[data-layer="window"]')?.id}
      onPointerDown={(e) => e.stopPropagation()}
      onKeyDown={(e) => {
        if (openSub && e.key === "ArrowLeft") {
          e.preventDefault();
          e.stopPropagation();
          if (narrow && deeper.length) setDeeper((path) => path.slice(0, -1));
          else setOpenSub(null);
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
      {narrow && current ? (
        // 393: the submenu REPLACES the panel; a back row leads. A nested
        // submenu replaces it again; the back row climbs one level.
        <>
          <Button
            variant="chrome"
            role="menuitem"
            className="desk-menu-back"
            onClick={() =>
              deeper.length ? setDeeper((d) => d.slice(0, -1)) : setOpenSub(null)
            }
          >
            {/* HS-148-01: the back row participates in the lane law. */}
            <span className="desk-menu-glyph" aria-hidden="true">
              {"◂"}
            </span>
            <span className="desk-menu-label">{current.label}</span>
          </Button>
          <WorkMenuSep />
          <WorkMenuRows
            key={current.id}
            entries={current.entries}
            onClose={onClose}
            openSub={null}
            setOpenSub={openDeeper}
            onSubAnchor={() => {}}
            hasLane={panelHasLane(current.entries)}
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
        />
      )}
      {!narrow && sub && subAt ? (
        <nav
          ref={subRef}
          className="desk-menu-list desk-work-menu desk-work-submenu is-below"
          role="menu"
          aria-label={`${sub.label} submenu`}
          style={menuStyle(subAt.x, subAt.y)}
          data-menu-context={sub.menuContext || menuContext || "verb"}
          onKeyDown={(e) => {
            // The submenu owns its own keys; never let them bubble to
            // the parent panel (whose item query would move focus twice).
            if (e.key === "ArrowLeft") {
              e.preventDefault();
              e.stopPropagation();
              setOpenSub(null);
              subOpener.current?.focus();
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
          />
        </nav>
      ) : null}
    </nav>
  );
  // Portal INSIDE the desk root when it exists: the Workbench menu
  // material is scoped `.desk-next .desk-menu-list`.
  return createPortal(
    panel,
    owner ?? document.getElementById("desk-next") ?? document.body,
  );
}
