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
  /** Share of a wide deck given to the list; omitted keeps the standard split. */
  listShare?: number;
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
        if (!image && rows.length > rowCount) rowsHeight += Math.min(14, rowHeight / 3);
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
        let formBudget = Infinity;
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
          if (fields && budget > 0) formBudget = budget;
          if (fields || minimum > budget) {
            const base = chrome + height(".object-list-head") + (height(".object-list-inner-toolbar") || height(".object-list-verbs")) + ruleHeight;
            const end = (row: HTMLElement) => well ? row.getBoundingClientRect().bottom - well.getBoundingClientRect().top + well.scrollTop - well.clientTop : rowHeight;
            const picked = [...rows].find(row => row.getAttribute("aria-selected") === "true");
            const spans = picked && end(picked) > budget - base ? [...rows].filter(row => end(row) <= end(picked)).reverse().map(row => end(picked) - end(row) + row.getBoundingClientRect().height) : [...rows].map(end);
            const floor = spans[0] ?? (rows.length ? rowHeight : 0);
            minimum = base + Math.max(floor, ...spans.filter(span => base + span <= budget));
            if (rows.length > rowCount && minimum + 14 <= chrome + contentFloor) minimum += 14;
          }
        }
        if (well && rows.length && !image && getComputedStyle(pane!).display !== "grid") {
          const base = well.getBoundingClientRect().top - seat.getBoundingClientRect().top + well.clientTop;
          const room = minimum - base;
          const boxes = [...rows].map(row=>{const r=row.getBoundingClientRect(),top=well.getBoundingClientRect().top;return {start:r.top-top+well.scrollTop,end:r.bottom-top+well.scrollTop,height:r.height};});
          if (boxes.at(-1)!.end > room+1) {
            const edge = boxes.find(row=>row.end > room+1);
            if (edge && room < edge.start+Math.min(14,edge.height/3)) minimum += edge.start+Math.min(14,edge.height/3)-room;
            if (minimum > formBudget) {
              const last = boxes.filter(row=>base+row.start+Math.min(14,row.height/3)<=formBudget).at(-1);
              if (last) minimum = Math.max(base+Math.min(rowHeight,boxes[0].height),base+last.start+Math.min(14,last.height/3));
            }
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
            const base=well.getBoundingClientRect().top-seat.getBoundingClientRect().top+well.clientTop;
            const top=well.getBoundingClientRect().top;
            const boxes=[...rows].map(row=>{const box=row.getBoundingClientRect();return {start:box.top-top+well.scrollTop,end:box.bottom-top+well.scrollTop,height:box.height};});
            // A group heading can stand between rows. Put the edge inside
            // the next row, rather than fourteen pixels after the last one.
            const cues=boxes.slice(1).map(row=>row.start+Math.min(14,row.height/3));
            const fitting=cues.filter(cue=>base+cue<=budget);
            minimum=base+Math.max(boxes[0].end,...fitting);
          }
        }
        const picked = [...rows].find(row => row.getAttribute("aria-selected") === "true");
        const group = picked?.closest(".object-list-group")?.querySelector<HTMLElement>(".object-list-group-label");
        if (form && picked && group && well) {
          const base = well.getBoundingClientRect().top - seat.getBoundingClientRect().top + well.clientTop;
          minimum = Math.max(minimum, base + picked.getBoundingClientRect().height + group.getBoundingClientRect().height);
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
      const group = row.closest(".object-list-group")?.querySelector<HTMLElement>(".object-list-group-label");
      const top = w.top + (group?.getBoundingClientRect().height ?? 0);
      if (r.bottom > w.bottom) well.scrollTop += r.bottom - w.bottom;
      else if (r.top < top) well.scrollTop -= top - r.top;
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
  }, [minimumRows]);
  return (
    <div
      className="surface-list-pane"
      data-layout={deck ? "deck" : undefined}
      style={listShare == null ? undefined : {"--surface-list-share": `${Math.max(.1,Math.min(.9,listShare))}fr`, "--surface-preview-share": `${1-Math.max(.1,Math.min(.9,listShare))}fr`} as CSSProperties}
      data-detail-open={(hasPreview && open) || undefined}
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
        <PaneNoticeContext.Provider value={notice}><ListPaneDepth.Provider value={depth}>{list}</ListPaneDepth.Provider></PaneNoticeContext.Provider>
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
