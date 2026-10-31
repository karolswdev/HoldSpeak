// The disclosure species on its own (PG-DIRECTION DIR2, 2026-10-31): the
// briefing page composes it without the microphone and the desk's auth
// client that ./gadgets.tsx brings. ./gadgets.tsx re-exports it, so every
// existing import stays as it is. Its material (gadgets.css) is imported by
// ./gadgets.tsx for the desk and by web/src/briefing/briefing.css for the
// page: a stylesheet imported here would move into the shared chunk and
// change the desk's stylesheet order.
import type { ReactNode } from "react";
import { sentenceChildren } from "./words";

/* ── FoldGadget: the ONE disclosure species (HS-111-08, audit §3.3) —
   <details> semantics (free keyboard + a11y), the house quiet-row
   face, a trailing token slot (the 05 budget gap). ── */

export function FoldGadget({
  title,
  token,
  glyph,
  open,
  onToggle,
  className,
  children,
}: {
  /** The summary line — reads as a token, never a sentence. */
  title: ReactNode;
  /** Trailing budget/count token, right-aligned (mono, dim). */
  token?: ReactNode;
  /** Optional leading glyph beside the caret. */
  glyph?: ReactNode;
  open?: boolean;
  /** Optional controlled hook — fires with the <details> open state. */
  onToggle?: (open: boolean) => void;
  className?: string;
  children: ReactNode;
}) {
  return (
    <details
      className={className ? `gadget-fold ${className}` : "gadget-fold"}
      data-token={token != null ? "" : undefined}
      open={open}
      onToggle={
        onToggle
          ? (event) => onToggle((event.target as HTMLDetailsElement).open)
          : undefined
      }
    >
      <summary>
        {glyph ? (
          <span className="gadget-fold-glyph" aria-hidden="true">
            {glyph}
          </span>
        ) : null}
        <span className="gadget-fold-title">{sentenceChildren(title)}</span>
        {token != null ? (
          <span className="gadget-fold-token">{sentenceChildren(token)}</span>
        ) : null}
      </summary>
      <div className="gadget-fold-body">{children}</div>
    </details>
  );
}
