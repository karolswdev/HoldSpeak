import { useEffect, useRef, type ReactNode } from "react";
import "./list-pane.css";

/** A bounded list with a plain reading well below it, at every width. */
export function ListPane({ list, children, label, listTestId, previewTestId }: { list: ReactNode; children?: ReactNode; label: string; listTestId?: string; previewTestId?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (typeof ResizeObserver === "undefined" || !ref.current) return;
    const update = () => {
      const seat = ref.current;
      const grid = [...(seat?.querySelectorAll<HTMLElement>(".object-list") ?? [])].find((el) => el.getBoundingClientRect().height > 0);
      if (seat && grid) {
        const height = (selector: string) => grid.querySelector<HTMLElement>(selector)?.getBoundingClientRect().height ?? 0;
        const rowHeight = height(".object-list-row") || 44;
        const box = seat.getBoundingClientRect(), content = grid.getBoundingClientRect();
        const chrome = Math.max(0, content.top - box.top) + Math.max(0, box.bottom - content.bottom);
        const gridFloor = parseFloat(getComputedStyle(grid).minHeight) || 0;
        const contentFloor = Math.max(gridFloor, height(".object-list-head") + rowHeight * 3 + height(".object-list-verbs") + 2);
        seat.style.setProperty("--surface-list-min", `${Math.ceil(chrome + contentFloor)}px`);
      }
      const row = seat?.querySelector<HTMLElement>('[data-object-id][aria-selected="true"]');
      const well = row?.closest<HTMLElement>(".object-list-rows");
      if (!row || !well) return;
      const r = row.getBoundingClientRect(), w = well.getBoundingClientRect();
      if (r.bottom > w.bottom) well.scrollTop += r.bottom - w.bottom;
      else if (r.top < w.top) well.scrollTop -= w.top - r.top;
    };
    const observer = new ResizeObserver(update);
    const mutations = new MutationObserver(update);
    observer.observe(ref.current);
    mutations.observe(ref.current, { subtree: true, childList: true, attributes: true, attributeFilter: ["aria-selected"] });
    update();
    return () => { observer.disconnect(); mutations.disconnect(); };
  }, []);
  return <div className="surface-list-pane"><div ref={ref} className="surface-list-pane-list" data-testid={listTestId}>{list}</div>
    {children ? <section className="surface-list-pane-preview" data-testid={previewTestId} aria-label={label}>{children}</section> : null}</div>;
}
