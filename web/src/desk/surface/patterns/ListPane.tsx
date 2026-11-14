import { Button } from "../../../components/signal/Signal";
import {
  createContext,
  useContext,
  useEffect,
  useRef,
  type ReactNode,
  type CSSProperties,
} from "react";
import "./list-pane.css";
import { PaneNoticeContext } from "./PreferencePane";
import { hasWords } from "../content";
import { scheduleRowLayout, cancelRowLayout } from "../objects/rowLayout";

export const ListPaneDepth = createContext(0);

/** A bounded list with a plain reading well below it, at every width. */
export function ListPane({
  list,
  notice,
  children,
  label,
  listTestId,
  previewTestId,
  deck,
  listShare,
  listPosition = "before",
  minimumRows = 4,
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
  /** List share: width in a deck, height above facts or below a reading well. */
  listShare?: number;
  /** A reading-first vertical split; listShare caps the list height. */
  listPosition?: "before" | "after";
  /** A nested picker can yield rows before its surrounding form does. */
  minimumRows?: number;
  open?: boolean;
  onBack?(): void;
  list: ReactNode;
  notice?: ReactNode;
  children?: ReactNode;
  label: string;
  listTestId?: string;
  previewTestId?: string;
}) {
  const depth = useContext(ListPaneDepth);
  const hasPreview = hasWords(children);
  const hasList = hasWords(list);
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
        const gridFloor = minimumRows < 4 ? 0 : parseFloat(getComputedStyle(grid).minHeight) || 0;
        const preview = seat.parentElement?.querySelector<HTMLElement>(":scope > .surface-list-pane-preview");
        const facts = preview?.querySelector<HTMLElement>(":scope > .surface-inspector-facts[data-headerless], :scope > .surface-tab-panel > .surface-inspector-facts[data-headerless]");
        const image = preview?.querySelector<HTMLElement>(".surface-image-well");
        const rowCount = image ? 1 : Math.max(1, Math.min(grid.closest(".surface-inspector-form") ? 1 : minimumRows, grid.querySelectorAll(".object-list-row").length));
        const well = grid.querySelector<HTMLElement>(".object-list-rows");
        const rows = grid.querySelectorAll<HTMLElement>(".object-list-row");
        // Groups and two-line rows take real space, too. Measure through the
        // last reserved row, independent of the well's current scroll position.
        let rowsHeight = rows.length ? rowHeight * rowCount : 0;
        if (image) rowsHeight = [...rows].find(row => row.getAttribute("aria-selected") === "true")?.getBoundingClientRect().height || rowHeight;
        else if (well && rows.length) {
          const bottom = (row: HTMLElement) => row.getBoundingClientRect().bottom - well.getBoundingClientRect().top + well.scrollTop - well.clientTop;
          rowsHeight = bottom(rows[Math.min(rowCount, rows.length) - 1]);
          // The row floor can cross another row in a mixed-height list.
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
          let previewChrome = factsOnly ? box.top - previewBox.top + (parseFloat(getComputedStyle(preview).paddingBottom) || 0) : previewBox.height - box.height;
          if (image && !content) {
            // A minimum-height image can overflow a compressed preview. Its
            // current bottom is not the preview's available bottom inset.
            previewChrome = box.top - previewBox.top;
            for (let parent = image.parentElement; parent; parent = parent.parentElement) {
              previewChrome += parseFloat(getComputedStyle(parent).paddingBottom) || 0;
              if (parent === preview) break;
            }
          }
          if (fields) previewChrome -= parseFloat(getComputedStyle(fields).marginBottom) || 0;
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
        // A smaller frame can yield rows; the default frame keeps its four-row
        // floor. Reserve the inspector's heading and first fact before fitting.
        if (preview && pane && well && rows.length && !form && getComputedStyle(pane).display !== "grid") {
          const paneHeight=pane.getBoundingClientRect().height;
          const heading=preview.querySelector<HTMLElement>(".surface-pane-inspector-head")?.getBoundingClientRect().height ?? 0;
          const first=preview.querySelector<HTMLElement>(".gadget-row,.object-list-row")?.getBoundingClientRect().height ?? rowHeight;
          const budget=paneHeight-Math.min(paneHeight/2,heading+first+16);
          if(paneHeight>0 && minimum>budget){
            const base=well.getBoundingClientRect().top-seat.getBoundingClientRect().top+(parseFloat(getComputedStyle(well).borderBottomWidth)||0);
            const top=well.getBoundingClientRect().top;
            const boxes=[...rows].map(row=>{const box=row.getBoundingClientRect();return {start:box.top-top+well.scrollTop,end:box.bottom-top+well.scrollTop,height:box.height};});
            const fitting=boxes.map(row=>row.end).filter(end=>base+end<=budget);
            minimum=base+Math.max(boxes[0].end,...fitting);
          }
        }
        // A declared share also reserves whole list rows above a short facts
        // pane. Forms and media keep their own measured seats.
        if (listShare != null && pane && preview && well && rows.length && !form && !image && !preview.querySelector("video,.surface-object-reader") && pane.clientWidth > 620 && getComputedStyle(pane).display !== "grid") {
          const base = chrome + height(".object-list-head") + (height(".object-list-inner-toolbar") || height(".object-list-verbs")) + ruleHeight;
          const budget = pane.clientHeight * Math.max(.1, Math.min(.9, listShare)) - base;
          const top = well.getBoundingClientRect().top;
          const ends = [...rows].map(row => row.getBoundingClientRect().bottom - top + well.scrollTop - well.clientTop);
          minimum = Math.max(minimum, base + Math.max(0, ...ends.filter(end => end <= budget)));
        }
        const picked = [...rows].find(row => row.getAttribute("aria-selected") === "true");
        const group = picked?.closest(".object-list-group")?.querySelector<HTMLElement>(".object-list-group-label");
        if (picked && group && well) {
          const base = well.getBoundingClientRect().top - seat.getBoundingClientRect().top + ruleHeight;
          minimum = Math.max(minimum, base + picked.getBoundingClientRect().height + group.getBoundingClientRect().height);
        }
        const value = Math.ceil(minimum) + "px";
        return () => {
          if (pane?.style.getPropertyValue("--surface-list-min") !== value) pane?.style.setProperty("--surface-list-min", value);
          if (seat.style.getPropertyValue("--surface-list-min") !== value) seat.style.setProperty("--surface-list-min", value);
        };
      }
    };
    const schedule = () => scheduleRowLayout(update);
    const observer = new ResizeObserver(schedule);
    const mutations = new MutationObserver(schedule);
    observer.observe(ref.current);
    if (ref.current.parentElement) observer.observe(ref.current.parentElement);
    mutations.observe(ref.current.parentElement ?? ref.current, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ["aria-selected"],
    });
    schedule();
    return () => {
      cancelRowLayout(update);
      observer.disconnect();
      mutations.disconnect();
    };
  }, [minimumRows, listShare, hasList, listPosition]);
  const listSeat = hasList ? <div
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
        <PaneNoticeContext.Provider value={notice}><ListPaneDepth.Provider value={depth}>{list}</ListPaneDepth.Provider></PaneNoticeContext.Provider>
      </div> : null;
  const previewSeat = hasPreview ? (
        <section
          className="surface-list-pane-preview"
          data-testid={previewTestId}
          aria-label={label}
        >
          <ListPaneDepth.Provider value={depth + 1}>
            {children}
          </ListPaneDepth.Provider>
        </section>
      ) : null;
  return (
    <div
      className="surface-list-pane"
      data-layout={hasPreview && listPosition === "after" ? "stack" : deck && hasList ? "deck" : undefined}
      style={listShare == null ? undefined : {"--surface-list-limit": `${Math.max(.1,Math.min(.9,listShare))*100}%`, "--surface-list-share": `${Math.max(.1,Math.min(.9,listShare))}fr`, "--surface-preview-share": `${1-Math.max(.1,Math.min(.9,listShare))}fr`} as CSSProperties}
      data-detail-open={(hasPreview && open) || undefined}
    >
      {listPosition === "after" ? previewSeat : listSeat}
      {hasPreview && hasList && deck && !hostBack ? (
        <Button variant="ghost" className="surface-list-back" onClick={onBack}>
          {backLabel}
        </Button>
      ) : null}
      {listPosition === "after" ? listSeat : previewSeat}
    </div>
  );
}
