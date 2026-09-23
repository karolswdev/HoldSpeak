/** PHILO-3-01 — the owner's ruling (2026-09-23): "Full-width row, work
 * moves down". At phone width the desk's backstop write receipt is its own
 * full-width row IN THE FLOW between the bar and the work, so the whole
 * cause reads; the Chair gives up exactly the row's height while it
 * stands, and a clean desk has no row and no reserved space.
 *
 * The seat (bar or row) follows the shell's one phone fact
 * (`useCompactViewport`, HS-202-02 — the same fact that folds the bar's
 * menus into Go). The row's own reflow needs no query: it wraps. */
import { useLayoutEffect, useRef } from "react";
import { useDeskWriteReceipt } from "../hooks/useWriteReceipt";

export function DeskReceiptRow() {
  const { receipt } = useDeskWriteReceipt({ fallback: true });
  const ref = useRef<HTMLDivElement | null>(null);

  useLayoutEffect(() => {
    const host = document.getElementById("desk-next");
    const row = ref.current;
    if (!host) return;
    if (!row) {
      host.style.removeProperty("--desk-receipt-row-h");
      return;
    }
    const seat = () =>
      host.style.setProperty("--desk-receipt-row-h", `${row.getBoundingClientRect().height}px`);
    seat();
    const observer =
      typeof ResizeObserver === "function" ? new ResizeObserver(seat) : null;
    observer?.observe(row);
    return () => {
      observer?.disconnect();
      host.style.removeProperty("--desk-receipt-row-h");
    };
  }, [receipt]);

  if (!receipt) return null;
  return (
    <div className="desk-receipt-row" ref={ref}>
      {receipt}
    </div>
  );
}
