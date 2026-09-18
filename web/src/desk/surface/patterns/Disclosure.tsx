/** Disclosure — controlled/uncontrolled fold with proper focus management.
 *  Uses a button trigger (not details/summary) for full control.
 *  Escape closes; focus returns to trigger on close. */
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import "./disclosure.css";

export function Disclosure({
  label,
  defaultOpen = false,
  open: controlledOpen,
  onOpenChange,
  persistKey,
  variant = "default",
  children,
  token,
  ariaLabel,
  controlsId,
}: {
  label: string;
  defaultOpen?: boolean;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  persistKey?: string;
  /** `dense` (HS-200-15): the caption-step trigger for a ledger row's meta
   *  line; `raw`: no chrome, just the body. */
  variant?: "default" | "raw" | "dense";
  children: ReactNode;
  token?: ReactNode;
  /** HS-200-15: an accessible name richer than the visible label
   *  (`Sources — Priya confirms the freeze window` over `2 SOURCES`). */
  ariaLabel?: string;
  /** HS-200-15: the id of a body rendered ELSEWHERE (a ledger row's own
   *  expansion slot). The trigger then owns no body of its own and names
   *  the external one through `aria-controls`; `children` are ignored. */
  controlsId?: string;
}) {
  const triggerRef = useRef<HTMLButtonElement>(null);

  // Resolve initial state: persistKey > defaultOpen
  const readPersisted = (): boolean => {
    if (!persistKey) return defaultOpen;
    try {
      const stored = localStorage.getItem(persistKey);
      if (stored !== null) return stored === "true";
    } catch {
      // localStorage unavailable
    }
    return defaultOpen;
  };

  const [internalOpen, setInternalOpen] = useState(readPersisted);
  const isControlled = controlledOpen !== undefined;
  const isOpen = isControlled ? controlledOpen : internalOpen;

  const setOpen = useCallback(
    (next: boolean) => {
      if (!isControlled) setInternalOpen(next);
      onOpenChange?.(next);
      if (persistKey) {
        try {
          localStorage.setItem(persistKey, String(next));
        } catch {
          // localStorage unavailable
        }
      }
    },
    [isControlled, onOpenChange, persistKey],
  );

  // Focus return on close
  const prevOpen = useRef(isOpen);
  useEffect(() => {
    if (prevOpen.current && !isOpen) {
      triggerRef.current?.focus();
    }
    prevOpen.current = isOpen;
  }, [isOpen]);

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === "Escape" && isOpen) {
      event.stopPropagation();
      setOpen(false);
    }
  };

  return (
    <div
      className="surface-disclosure"
      data-open={isOpen || undefined}
      data-variant={variant !== "default" ? variant : undefined}
      data-token={token != null ? "" : undefined}
      onKeyDown={handleKeyDown}
    >
      <button
        ref={triggerRef}
        type="button"
        className="surface-disclosure-trigger"
        aria-expanded={isOpen}
        aria-controls={controlsId}
        aria-label={ariaLabel}
        onClick={() => setOpen(!isOpen)}
      >
        <span className="surface-disclosure-caret" aria-hidden="true">
          {"▸"}
        </span>
        <span className="surface-disclosure-label">{label}</span>
        {token != null ? (
          <span className="surface-disclosure-token">{token}</span>
        ) : null}
      </button>
      {isOpen && !controlsId ? (
        <div className="surface-disclosure-body" role="region" aria-label={ariaLabel ?? label}>
          {children}
        </div>
      ) : null}
    </div>
  );
}
