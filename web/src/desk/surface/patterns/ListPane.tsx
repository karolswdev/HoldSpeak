import { useEffect, useRef, type ReactNode } from "react";
import "./list-pane.css";

/** A bounded list with a plain reading well below it, at every width. */
export function ListPane({ list, children, label, listTestId, previewTestId }: { list: ReactNode; children?: ReactNode; label: string; listTestId?: string; previewTestId?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (typeof ResizeObserver === "undefined" || !ref.current) return;
    const observer = new ResizeObserver(() => {
      const row = ref.current?.querySelector<HTMLElement>('[data-object-id][aria-selected="true"]');
      const well = row?.closest<HTMLElement>(".object-list-rows");
      if (!row || !well) return;
      const r = row.getBoundingClientRect(), w = well.getBoundingClientRect();
      if (r.bottom > w.bottom) well.scrollTop += r.bottom - w.bottom;
      else if (r.top < w.top) well.scrollTop -= w.top - r.top;
    });
    observer.observe(ref.current); return () => observer.disconnect();
  }, []);
  return <div className="surface-list-pane"><div ref={ref} className="surface-list-pane-list" data-testid={listTestId}>{list}</div>
    {children ? <section className="surface-list-pane-preview" data-testid={previewTestId} aria-label={label}>{children}</section> : null}</div>;
}
