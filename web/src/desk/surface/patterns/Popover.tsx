/** Popover — in-flow anchored popover with focus law.
 *  Escape dismisses. Focus trapped while open.
 *  Uses --desk-z-popover for z-index. */
import {
  useCallback,
  useEffect,
  useRef,
  type ReactNode,
  type RefObject,
} from "react";
import { createPortal } from "react-dom";
import "./popover.css";

export function Popover({
  anchor,
  open,
  onClose,
  children,
  placement = "below",
  ariaLabel,
}: {
  anchor: RefObject<HTMLElement | null>;
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  placement?: "above" | "below" | "start" | "end";
  ariaLabel?: string;
}) {
  const popoverRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  // Save and restore focus
  useEffect(() => {
    if (open) {
      previousFocusRef.current = document.activeElement as HTMLElement;
      // Focus the popover itself after mount
      requestAnimationFrame(() => {
        popoverRef.current?.focus();
      });
    } else if (previousFocusRef.current) {
      previousFocusRef.current.focus();
      previousFocusRef.current = null;
    }
  }, [open]);

  // Escape handler
  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (event.key === "Escape") {
        event.stopPropagation();
        onClose();
        return;
      }
      // Focus trap: Tab cycles within the popover
      if (event.key === "Tab") {
        const popover = popoverRef.current;
        if (!popover) return;
        const focusable = popover.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
        );
        if (!focusable.length) {
          event.preventDefault();
          return;
        }
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    },
    [onClose],
  );

  if (!open) return null;

  // Position relative to the anchor element
  const anchorEl = anchor.current;
  if (!anchorEl) return null;

  const rect = anchorEl.getBoundingClientRect();
  const style: React.CSSProperties = {};

  switch (placement) {
    case "above":
      style.position = "fixed";
      style.left = rect.left;
      style.bottom = window.innerHeight - rect.top + 4;
      break;
    case "below":
      style.position = "fixed";
      style.left = rect.left;
      style.top = rect.bottom + 4;
      break;
    case "start":
      style.position = "fixed";
      style.right = window.innerWidth - rect.left + 4;
      style.top = rect.top;
      break;
    case "end":
      style.position = "fixed";
      style.left = rect.right + 4;
      style.top = rect.top;
      break;
  }

  return createPortal(
    <>
      {/* Invisible backdrop to catch outside clicks */}
      <div
        className="surface-popover-backdrop"
        onClick={onClose}
        aria-hidden="true"
      />
      <div
        ref={popoverRef}
        className="surface-popover"
        role="dialog"
        aria-label={ariaLabel}
        tabIndex={-1}
        style={style}
        onKeyDown={handleKeyDown}
      >
        {children}
      </div>
    </>,
    document.body,
  );
}
