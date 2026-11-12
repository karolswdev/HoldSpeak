import { Button } from "../../../components/signal/Signal";
import {
  createContext,
  useContext,
  useEffect,
  useRef,
  type ReactNode,
} from "react";
import "./list-pane.css";

export const ListPaneDepth = createContext(0);

/** A bounded list with a plain reading well below it, at every width. */
export function ListPane({
  list,
  children,
  label,
  listTestId,
  previewTestId,
  deck,
  open = false,
  onBack,
  backLabel = "Back",
  hostBack = false,
  onReveal,
}: {
  onReveal?(): void;
  hostBack?: boolean;
  backLabel?: string;
  deck?: boolean;
  open?: boolean;
  onBack?(): void;
  list: ReactNode;
  children?: ReactNode;
  label: string;
  listTestId?: string;
  previewTestId?: string;
}) {
  const depth = useContext(ListPaneDepth);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (typeof ResizeObserver === "undefined" || !ref.current) return;
    const update = () => {
      const seat = ref.current;
      const grid = [
        ...(seat?.querySelectorAll<HTMLElement>(".object-list") ?? []),
      ].find((el) => el.getBoundingClientRect().height > 0);
      if (seat && grid) {
        const height = (selector: string) =>
          grid.querySelector<HTMLElement>(selector)?.getBoundingClientRect()
            .height ?? 0;
        const rowHeight = height(".object-list-row") || 44;
        const box = seat.getBoundingClientRect(),
          content = grid.getBoundingClientRect();
        const chrome =
          Math.max(0, content.top - box.top) +
          Math.max(0, box.bottom - content.bottom);
        const gridFloor = parseFloat(getComputedStyle(grid).minHeight) || 0;
        const preview = seat.parentElement?.querySelector<HTMLElement>(":scope > .surface-list-pane-preview");
        const facts = preview?.querySelector<HTMLElement>(":scope > .surface-inspector-facts[data-headerless]");
        const reader = preview?.querySelector(":scope > .surface-tab-panel");
        const rowCount = preview?.querySelector(".surface-image-well") ? 1 : reader ? Math.max(1, Math.min(3, grid.querySelectorAll(".object-list-row").length)) : 3;
        const well = grid.querySelector<HTMLElement>(".object-list-rows");
        const rows = grid.querySelectorAll<HTMLElement>(".object-list-row");
        // Groups and two-line rows take real space, too. Measure through the
        // last reserved row, independent of the well's current scroll position.
        let rowsHeight = rowHeight * rowCount;
        if (well && rows.length) {
          const bottom = (row: HTMLElement) => row.getBoundingClientRect().bottom - well.getBoundingClientRect().top + well.scrollTop - well.clientTop;
          rowsHeight = Math.max(rowsHeight, bottom(rows[Math.min(rowCount, rows.length) - 1]));
          // The three-row floor can cross another row in a mixed-height list.
          // Round it up to that row's end, rather than drawing part of it.
          const edge = [...rows].find(row => bottom(row) >= rowsHeight);
          if (edge) rowsHeight = bottom(edge);
          const picked = [...rows].find(row => row.getAttribute("aria-selected") === "true");
          if (picked) {
            const end = bottom(picked);
            const first = [...rows].reverse().find(row => bottom(row) - row.getBoundingClientRect().height <= end - rowsHeight);
            if (first) rowsHeight = Math.max(rowsHeight, end - bottom(first) + first.getBoundingClientRect().height);
          }
        }
        const ruleHeight = well ? well.clientTop + (parseFloat(getComputedStyle(well).borderBottomWidth) || 0) : 2;
        const contentFloor = Math.max(
          preview?.querySelector(".surface-image-well") ? 0 : gridFloor,
          height(".object-list-head") +
            rowsHeight +
            (height(".object-list-inner-toolbar") ||
              height(".object-list-verbs")) +
            ruleHeight,
        );
        let minimum = chrome + contentFloor;
        if (facts && facts.scrollHeight > 0 && seat.parentElement) {
          const space = seat.parentElement.getBoundingClientRect().height - facts.scrollHeight - 2;
          const oneRow = chrome + height(".object-list-head") + rowHeight + 2;
          minimum = Math.max(oneRow, Math.min(minimum, space));
        }
        const pane = seat.parentElement;
        const form = preview?.querySelector<HTMLElement>(".surface-inspector-form[data-completion]");
        const fields = form?.querySelector<HTMLElement>(":scope > .surface-inspector-fields");
        if (pane && preview && fields && getComputedStyle(pane).display !== "grid") {
          // Everything outside the field well (heading, notice, completion,
          // insets and tabs) keeps its seat. The list yields before rows scroll.
          const fieldBox = fields.getBoundingClientRect();
          const contentHeight = Math.max(0, ...[...fields.children].map(child => child.getBoundingClientRect().bottom - fieldBox.top + fields.scrollTop));
          const wanted = preview.getBoundingClientRect().height - fieldBox.height + contentHeight;
          const budget = pane.getBoundingClientRect().height - wanted;
          if (minimum > budget) {
            const base = chrome + height(".object-list-head") + (height(".object-list-inner-toolbar") || height(".object-list-verbs")) + ruleHeight;
            const end = (row: HTMLElement) => well ? row.getBoundingClientRect().bottom - well.getBoundingClientRect().top + well.scrollTop - well.clientTop : rowHeight;
            const picked = [...rows].find(row => row.getAttribute("aria-selected") === "true");
            const spans = picked ? [...rows].filter(row => end(row) <= end(picked)).reverse().map(row => end(picked) - end(row) + row.getBoundingClientRect().height) : [...rows].map(end);
            const floor = spans[0] ?? rowHeight;
            minimum = base + Math.max(floor, ...spans.filter(span => base + span <= budget));
          }
        }
        seat.style.setProperty("--surface-list-min", `${Math.ceil(minimum)}px`);
      }
      const row = seat?.querySelector<HTMLElement>(
        '[data-object-id][aria-selected="true"]',
      );
      const well = row?.closest<HTMLElement>(".object-list-rows");
      if (!row || !well) return;
      const r = row.getBoundingClientRect(),
        w = well.getBoundingClientRect();
      if (r.bottom > w.bottom) well.scrollTop += r.bottom - w.bottom;
      else if (r.top < w.top) well.scrollTop -= w.top - r.top;
    };
    const observer = new ResizeObserver(update);
    const mutations = new MutationObserver(update);
    observer.observe(ref.current);
    if (ref.current.parentElement) observer.observe(ref.current.parentElement);
    mutations.observe(ref.current.parentElement ?? ref.current, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ["aria-selected"],
    });
    update();
    return () => {
      observer.disconnect();
      mutations.disconnect();
    };
  }, []);
  return (
    <div
      className="surface-list-pane"
      data-layout={deck ? "deck" : undefined}
      data-detail-open={open || undefined}
    >
      <div
        ref={ref}
        onClickCapture={(event) => {
          if (
            deck &&
            (event.target as HTMLElement).closest(
              ".object-list-row[data-object-id]",
            )
          )
            onReveal?.();
        }}
        className="surface-list-pane-list"
        data-testid={listTestId}
      >
        <ListPaneDepth.Provider value={depth}>{list}</ListPaneDepth.Provider>
      </div>
      {children && deck && !hostBack ? (
        <Button variant="ghost" className="surface-list-back" onClick={onBack}>
          {backLabel}
        </Button>
      ) : null}
      {children ? (
        <section
          className="surface-list-pane-preview"
          data-testid={previewTestId}
          aria-label={label}
        >
          <ListPaneDepth.Provider value={depth + 1}>
            {children}
          </ListPaneDepth.Provider>
        </section>
      ) : null}
    </div>
  );
}
