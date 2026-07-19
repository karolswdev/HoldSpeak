// HS-99-04 — the ONE menu vocabulary (DESIGN_SYSTEM.md, the chrome
// ladder): every desk popover — the room menu, the window-head menu,
// the dock chip menu — renders through this primitive, carrying the
// HS-96-05 keyboard pattern (roving arrows, Home/End, Escape with
// focus return) and the transient material.
import { type CSSProperties, type ReactNode } from "react";

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
      onKeyDown={(e) => {
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
        }
      }}
    >
      {children}
    </nav>
  );
}

export function DeskMenuItem({
  glyph,
  onSelect,
  children,
}: {
  glyph?: ReactNode;
  onSelect(): void;
  children: ReactNode;
}) {
  return (
    <button type="button" role="menuitem" onClick={onSelect}>
      {glyph}
      {children}
    </button>
  );
}
