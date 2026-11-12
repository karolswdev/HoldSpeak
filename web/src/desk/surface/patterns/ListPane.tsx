import { Button } from "../../../components/signal/Signal";
import {
  createContext,
  useContext,
  useEffect,
  useRef,
  type ReactNode,
} from "react";
import "./list-pane.css";
import { hasWords } from "../content";

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
  const hasPreview = hasWords(children);
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
          (grid.hasAttribute("data-empty") ? 0 : Math.max(0, box.bottom - content.bottom));
        const gridFloor = parseFloat(getComputedStyle(grid).minHeight) || 0;
        const preview = seat.parentElement?.querySelector<HTMLElement>(":scope > .surface-list-pane-preview");
        const facts = preview?.querySelector<HTMLElement>(":scope > .surface-inspector-facts[data-headerless], :scope > .surface-tab-panel > .surface-inspector-facts[data-headerless]");
        const image = preview?.querySelector<HTMLElement>(".surface-image-well");
        const rowCount = image ? 1 : Math.max(1, Math.min(3, grid.querySelectorAll(".object-list-row").length));
        const well = grid.querySelector<HTMLElement>(".object-list-rows");
        const rows = grid.querySelectorAll<HTMLElement>(".object-list-row");
        // Groups and two-line rows take real space, too. Measure through the
        // last reserved row, independent of the well's current scroll position.
        let rowsHeight = rows.length ? rowHeight * rowCount : 0;
        if (image) rowsHeight = [...rows].find(row => row.getAttribute("aria-selected") === "true")?.getBoundingClientRect().height || rowHeight;
        else if (well && rows.length) {
          const bottom = (row: HTMLElement) => row.getBoundingClientRect().bottom - well.getBoundingClientRect().top + well.scrollTop - well.clientTop;
          rowsHeight = bottom(rows[Math.min(rowCount, rows.length) - 1]);
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
          image ? 0 : gridFloor,
          height(".object-list-head") +
            rowsHeight +
            (height(".object-list-inner-toolbar") ||
              height(".object-list-verbs")) +
            ruleHeight,
        );
        let minimum = chrome + contentFloor;
        const pane = seat.parentElement;
        const form = preview?.querySelector<HTMLElement>(".surface-inspector-form[data-completion]");
        const fields = form?.querySelector<HTMLElement>(":scope > .surface-inspector-fields");
        const reading = fields || facts || image;
        if (pane && preview && reading && getComputedStyle(pane).display !== "grid") {
          // Insets, tabs and completion keep their seats. The list yields
          // before the form, facts or image starts its own scroll well.
          const box = reading.getBoundingClientRect();
          const content = fields || facts;
          // A filling facts well has spare height. Reserve its actual rows,
          // not that spare height, before giving the list its whole rows.
          const contentHeight = content ? Math.max(0, ...[...content.children].map(child => child.getBoundingClientRect().top - box.top + content.scrollTop + Math.max(child.scrollHeight, child.getBoundingClientRect().height))) + (parseFloat(getComputedStyle(content).paddingBottom) || 0)
            : parseFloat(getComputedStyle(reading).minHeight) || 0;
          const previewBox = preview.getBoundingClientRect();
          const factsOnly = facts?.parentElement === preview && preview.children.length === 1;
          const previewChrome = factsOnly ? box.top - previewBox.top + (parseFloat(getComputedStyle(preview).paddingBottom) || 0) : previewBox.height - box.height;
          const wanted = previewChrome + contentHeight;
          const budget = pane.getBoundingClientRect().height - wanted;
          if (fields || minimum > budget) {
            const base = chrome + height(".object-list-head") + (height(".object-list-inner-toolbar") || height(".object-list-verbs")) + ruleHeight;
            const end = (row: HTMLElement) => well ? row.getBoundingClientRect().bottom - well.getBoundingClientRect().top + well.scrollTop - well.clientTop : rowHeight;
            const picked = [...rows].find(row => row.getAttribute("aria-selected") === "true");
            const spans = picked && end(picked) > budget - base ? [...rows].filter(row => end(row) <= end(picked)).reverse().map(row => end(picked) - end(row) + row.getBoundingClientRect().height) : [...rows].map(end);
            const floor = spans[0] ?? (rows.length ? rowHeight : 0);
            minimum = base + Math.max(floor, ...spans.filter(span => base + span <= budget));
          }
        }
        pane?.style.setProperty("--surface-list-min", Math.ceil(minimum) + "px");
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
      {hasPreview && deck && !hostBack ? (
        <Button variant="ghost" className="surface-list-back" onClick={onBack}>
          {backLabel}
        </Button>
      ) : null}
      {hasPreview ? (
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
