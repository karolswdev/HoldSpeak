/* PHILO-9-04 CANVAS — the list face (PROPOSAL, not built).
 *
 * A copy of web/src/desk/components/DeskListView.tsx at this branch, with the
 * imports moved to the "@w" alias and four marked PROPOSAL changes:
 *   1. the status says SHOWN for any count ("27 SHOWN OF 27", "1 SHOWN OF 1");
 *   2. in a `surface` of 720 px or less the Kind, Zone and Attention columns fold into a second
 *      line under the name (the same tokens), and their sort Buttons join the
 *      Name header (ProposedDeskSortableTable `foldColumns`);
 *   3. the sort headers are the library Button (ProposedDeskSortableTable);
 *   4. the row menu is the WorkMenu species with the keep-in-view rule
 *      (ProposedDeskMenu).
 * The 12 px floor and the selection token are CSS (./canvas.css). The harness
 * vite config swaps this module in for the real DeskListView; the rest of the
 * Desk (DeskApp, DeskChrome, the store, the hub) is the product.
 */
// HS-93-08 — the semantic list mode: the SAME Desk, expressed for
// keyboard and screen-reader use. It consumes the one store (items,
// selection, pull-out, dive) and the same world.ts records the spatial
// stage renders — zero new data paths, no second dashboard.
// HS-113-03 — the floor and zone-window lists now share DeskSortableTable:
// compact real table rows, sortable headers, sprites, and kind bands.
import "@w/desk/components/list-view.css";
import "./canvas.css";
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { Button } from "@w/components/signal/Signal";
import { qualifiedRef } from "@w/desk/api";
import { countToken } from "@w/desk/surface";
import { useDesk } from "@w/desk/store";
import { useProjections } from "@w/desk/projections";
import { allObjects, objectByRef, worldObjects, worldZones, type WorldObject } from "@w/desk/world";
import { KIND_LABEL } from "@w/desk/tools";
// @ts-ignore — shared ESM module (see ../sprites.d.ts)
import { spriteUrl } from "@w/desk/sprites";
import { spriteVariantKey } from "@w/lib/spriteVariants";
import { spriteStateCssClass } from "@w/lib/spriteStates";
import { objectMenuEntries } from "@w/desk/floorMenu";
import { WorkMenu } from "./ProposedDeskMenu";
import { InlineEditor } from "@w/desk/components/InlineEditor";
import { Pullout } from "@w/desk/components/Pullout";
import { AskBar, AskPanel } from "@w/desk/components/AskPanel";
import { DeliveryListSection } from "@w/desk/components/DeliveryListSection";
import { PrReceiptsSection } from "@w/desk/components/PrReceiptsSection";
import { DeskSortableTable, type Column } from "./ProposedDeskSortableTable";
import { DeskDeleteSeat } from "@w/desk/deleteReceipt";
import { useDeskWriteReceipt } from "@w/desk/hooks/useWriteReceipt";
import { ZoneRenameRow } from "@w/desk/components/ZoneRenameRow";

/* PROPOSAL 2 — the second line under the name in a surface of 720 px or less (hidden wider):
 * the row's Kind, Zone and Attention, the same words as the columns. The
 * separator dot is drawn by CSS, so no empty token is ever printed. */
function FoldLine({ tokens, attention }: { tokens: string[]; attention?: number }) {
  const shown = tokens.filter(Boolean);
  if (!shown.length && !attention) return null;
  return (
    <span className="desk-list-fold" aria-hidden="true">
      {shown.map((t) => <span key={t} className="desk-list-fold-token">{t}</span>)}
      {attention ? <span className="desk-list-fold-token desk-list-attention">ATTN {attention}</span> : null}
    </span>
  );
}

/** Rows per page — a plain "show more" pagination, no virtualization dep. */
export const LIST_PAGE = 100;

/** Band heads per kind (the zone chip strip's replacement). */
const BAND_LABEL: Record<string, string> = {
  meeting: "MEETINGS",
  note: "NOTES",
  kb: "KNOWLEDGE",
  recipe: "AGENTS",
  workflow: "WORKFLOWS",
  chain: "WORKFLOWS",
  coder: "CODER SESSIONS",
  artifact: "ARTIFACTS",
  project: "PROJECTS",
  thread: "THREADS",
};

type ListSortKey = "name" | "kind" | "zone" | "attention";
type ListSort = { key: ListSortKey; dir: "asc" | "desc" };
type DeskListRow =
  | { type: "zone"; id: string; title: string; count: number }
  | { type: "object"; object: WorldObject; zoneName: string; attention: number };

const LIST_SORT_KEY = "hs.desk.list-sort";
const DEFAULT_SORT: ListSort = { key: "name", dir: "asc" };

function loadListSort(): ListSort {
  try {
    const saved = JSON.parse(localStorage.getItem(LIST_SORT_KEY) || "null");
    if (
      saved &&
      ["name", "kind", "zone", "attention"].includes(saved.key) &&
      (saved.dir === "asc" || saved.dir === "desc")
    ) {
      return saved as ListSort;
    }
  } catch {
    // Storage is optional; the list remains useful with its default order.
  }
  return DEFAULT_SORT;
}

/** PHILO-8-02 round three — the list's foot is held to the viewport, so the
 * list reserves the foot's measured reach at its end (the Chair's dock-lift
 * idiom): every row can scroll clear of the receipt and the selection bar. */
function useFootReserve() {
  const rootRef = useRef<HTMLDivElement | null>(null);
  const footRef = useRef<HTMLDivElement | null>(null);
  useLayoutEffect(() => {
    const root = rootRef.current;
    const foot = footRef.current;
    if (!root || !foot) return;
    const seat = () => {
      const reach = window.innerHeight - foot.getBoundingClientRect().top;
      root.style.setProperty("--desk-list-foot-reserve", `${Math.max(0, Math.ceil(reach)) + 12}px`);
    };
    seat();
    const observer = typeof ResizeObserver === "function" ? new ResizeObserver(seat) : null;
    observer?.observe(foot);
    window.addEventListener("resize", seat);
    return () => {
      observer?.disconnect();
      window.removeEventListener("resize", seat);
      root.style.removeProperty("--desk-list-foot-reserve");
    };
  }, []);
  return { rootRef, footRef };
}

export function DeskListView() {
  const { rootRef, footRef } = useFootReserve();
  // PHILO-8-02 round five: on the scrolling list a desk write failure (a
  // refused delete, with Retry) seats in the foot, where the undo receipt
  // was, never above the work off-screen. The near mount makes the bar's
  // fallback yield, so the failure shows once.
  const { receipt: failureReceipt } = useDeskWriteReceipt();
  const items = useDesk((s) => s.items);
  const divedZone = useDesk((s) => s.divedZone);
  const selectedIds = useDesk((s) => s.selectedIds);
  const pullouts = useDesk((s) => s.pullouts);
  const editingId = useDesk((s) => s.editingId);
  const askOpen = useDesk((s) => s.askOpen);
  // PHILO-8-01 — the zone being named draws its field in its own row.
  const renamingZoneId = useDesk((s) => s.renamingZoneId);
  const subjectCounts = useProjections((s) => s.subject_counts);
  const { openPullout, toggleSelected, diveInto, surface } = useDesk.getState();

  const zones = worldZones(items, divedZone);
  // The root list shows every owner object (filed ones carry their zone as
  // the fact token), but repository roadmaps belong to explicit Delivery,
  // not the ordinary Floor. A dived zone keeps its existing world projection.
  const objects = useMemo(
    () => (
      divedZone
        ? worldObjects(items, divedZone)
        : allObjects(items).filter((object) => object.kind !== "roadmap")
    ),
    [items, divedZone],
  );
  const zoneNames = useMemo(() => {
    const map = new Map<string, string>();
    for (const d of items.directory || []) {
      const name = String(d.name || "Zone");
      for (const mid of d.memberIds || []) map.set(mid, name);
    }
    return map;
  }, [items.directory]);

  const attentionOf = (o: WorldObject) => {
    const ref = qualifiedRef(o.kind, o.id);
    const subject =
      o.kind === "coder"
        ? `coder_session:${String(o.ref.kind === "coder" ? o.ref.agent : "claude")}:${o.id}`
        : ref;
    return subjectCounts[subject]?.needs_attention || 0;
  };
  const [sort, setSort] = useState<ListSort>(loadListSort);
  const [limit, setLimit] = useState(LIST_PAGE);
  const [rowMenu, setRowMenu] = useState<{
    id: string;
    ref: string;
    kind: string;
    title: string;
    x: number;
    y: number;
  } | null>(null);
  const statusRef = useRef<HTMLParagraphElement | null>(null);

  useEffect(() => setLimit(LIST_PAGE), [divedZone]);
  useEffect(() => {
    try {
      localStorage.setItem(LIST_SORT_KEY, JSON.stringify(sort));
    } catch {
      // Storage is optional; sorting is still live for this session.
    }
  }, [sort]);

  const sortedObjects = useMemo(() => {
    const direction = sort.dir === "asc" ? 1 : -1;
    const compare = (a: WorldObject, b: WorldObject) => {
      const zoneA = zoneNames.get(qualifiedRef(a.kind, a.id)) ?? zoneNames.get(a.id) ?? "";
      const zoneB = zoneNames.get(qualifiedRef(b.kind, b.id)) ?? zoneNames.get(b.id) ?? "";
      if (sort.key === "attention") return attentionOf(a) - attentionOf(b);
      if (sort.key === "kind") return a.kind.localeCompare(b.kind) || a.title.localeCompare(b.title);
      if (sort.key === "zone") return zoneA.localeCompare(zoneB) || a.title.localeCompare(b.title);
      return a.title.localeCompare(b.title);
    };
    return [...objects].sort((a, b) => direction * compare(a, b));
  }, [objects, sort, zoneNames, subjectCounts]);
  const visible = sortedObjects.slice(0, limit);
  const remaining = objects.length - visible.length;
  const divedTitle = divedZone
    ? String((items.directory || []).find((d) => d.id === divedZone)?.name || "Zone")
    : null;
  const attnTotal = useMemo(
    () => objects.reduce((n, o) => n + attentionOf(o), 0),
    [objects, subjectCounts],
  );
  const rows = useMemo<DeskListRow[]>(
    () => [
      ...(!divedZone
        ? zones.map((zone) => ({
            type: "zone" as const,
            id: zone.id,
            title: zone.title,
            count: zone.count,
          }))
        : []),
      ...visible.map((object) => {
        const ref = qualifiedRef(object.kind, object.id);
        return {
          type: "object" as const,
          object,
          zoneName: zoneNames.get(ref) ?? zoneNames.get(object.id) ?? "",
          attention: attentionOf(object),
        };
      }),
    ],
    [divedZone, zones, visible, zoneNames, subjectCounts],
  );
  const selectedKey = rows.find(
    (row) =>
      row.type === "object" &&
      (selectedIds.includes(qualifiedRef(row.object.kind, row.object.id)) ||
        selectedIds.includes(row.object.id)),
  );
  const openCards = pullouts
    .map((p) => ({ ...p, obj: objectByRef(items, p.id) }))
    .filter((p) => Boolean(p.obj));
  const editing = editingId ? objectByRef(items, editingId) : null;

  const columns: Column<DeskListRow>[] = [
    {
      key: "icon",
      label: "",
      width: "40px",
      render: (row) => {
        const ss = row.type === "zone" ? null : row.object.ref.spriteState;
        const state = typeof ss === "string" ? ss : null;
        const cssHint = spriteStateCssClass(state);
        const kind = row.type === "zone" ? "directory" : row.object.kind;
        return (
          <img
            className={"desk-sortable-table-sprite" + (cssHint ? ` ${cssHint}` : "")}
            src={spriteUrl(kind, row.type === "zone" ? row.id : row.object.id)}
            alt=""
            width={28}
            height={28}
            data-sprite-variant={spriteVariantKey(kind, state)}
          />
        );
      },
    },
    {
      key: "name",
      label: "Name",
      sortable: true,
      render: (row) => {
        if (row.type === "zone") {
          // PHILO-8-01 (the owner's ratified canvas, 2026-09-26): the zone
          // being named holds the one name field in its Name cell.
          if (row.id === renamingZoneId)
            return <ZoneRenameRow key={row.id} zoneId={row.id} title={row.title} placement="inrow" />;
          return (<>
            {/* HS-202-04 (UX-CANON A.8) — an empty zone announced
               "<name> zone, 0 items" to a screen reader and printed
               `0 ITEMS` in its own cell. A counter of zero is a bounce in
               text AND in an accessible name; `countToken` is the one way
               a face says "N things" and it withholds the zero
               (`desk/surface/count.ts:39`). */}
            <Button variant="ghost" dense className="desk-sortable-table-open" aria-label={[`${row.title} zone`, countToken(row.count, "item", "items")].filter(Boolean).join(", ")}>
              {row.title}
              <FoldLine tokens={["ZONE", countToken(row.count, "ITEM") ?? "EMPTY"]} />
            </Button>
          </>);
        }
        const ref = qualifiedRef(row.object.kind, row.object.id);
        const selected = selectedIds.includes(ref) || selectedIds.includes(row.object.id);
        return (<>
          <Button variant="ghost" dense className="desk-sortable-table-open desk-list-name-cell" aria-label={selected ? `${row.object.title}, in Ask context` : row.object.title}>
            <span className="desk-list-mark" data-selected={selected || undefined} aria-hidden="true">
              {selected ? "[x]" : "[ ]"}
            </span>
            {row.object.title}
            {row.zoneName ? <span className="sr-only"> {row.zoneName.toUpperCase()}</span> : null}
            {row.attention ? <span className="sr-only"> ATTN {row.attention}</span> : null}
            <FoldLine
              tokens={[(KIND_LABEL[row.object.kind] ?? row.object.kind).toUpperCase(), row.zoneName.toUpperCase()]}
              attention={row.attention}
            />
          </Button>
        </>);
      },
    },
    {
      key: "kind",
      label: "Kind",
      sortable: true,
      render: (row) => row.type === "zone" ? "ZONE" : (KIND_LABEL[row.object.kind] ?? row.object.kind).toUpperCase(),
    },
    {
      key: "zone",
      label: "Zone",
      sortable: true,
      // HS-202-04 (UX-CANON A.8): `0 ITEMS` is a counter of zero. The
      // zone's own cell says the true thing instead.
      render: (row) => row.type === "zone" ? (countToken(row.count, "ITEM") ?? "EMPTY") : row.zoneName.toUpperCase(),
    },
    {
      key: "attention",
      label: "Attention",
      sortable: true,
      render: (row) => row.type === "object" && row.attention ? <span className="desk-list-attention">ATTN {row.attention}</span> : "",
    },
  ];

  const showMore = () => {
    const next = Math.min(objects.length, limit + LIST_PAGE);
    setLimit(next);
    if (next >= objects.length) statusRef.current?.focus();
  };
  const openMenu = (object: WorldObject, x: number, y: number) =>
    setRowMenu({
      id: object.id,
      ref: qualifiedRef(object.kind, object.id),
      kind: object.kind,
      title: object.title,
      x,
      y,
    });

  return (
    <div className="desk-listmode" ref={rootRef}>
      <div data-aftercare-floor-slot="top" />
      <section aria-labelledby="desk-list-title" className="desk-list-face">
        <h2 id="desk-list-title" className="sr-only">
          {divedTitle ? `${divedTitle} zone` : "Desk items"}
        </h2>
        <div className="desk-list-census">
          <span>
            {divedZone ? <Button dense variant="ghost" className="desk-list-open desk-surface" onClick={surface}>ALL</Button> : null}
            {[countToken(objects.length, "ITEM"), countToken(zones.length, "ZONE"), countToken(attnTotal, "ATTN")].filter(Boolean).join(" · ") || "EMPTY"}
          </span>
          <p className="desk-list-status" role="status" tabIndex={-1} ref={statusRef}>
            {countToken(visible.length, "SHOWN", "SHOWN") || "EMPTY"} OF {objects.length}
          </p>
        </div>
        <DeskSortableTable
          className="desk-list-sortable"
          foldColumns={["kind", "zone", "attention"]}
          data={rows}
          columns={columns}
          sort={sort}
          onSort={(key, dir) => setSort({ key: key as ListSortKey, dir })}
          rowKey={(row) => row.type === "zone" ? `zone:${row.id}` : qualifiedRef(row.object.kind, row.object.id)}
          selectedKey={selectedKey && selectedKey.type === "object" ? qualifiedRef(selectedKey.object.kind, selectedKey.object.id) : null}
          groupBy={(row) => row.type === "zone" ? "ZONES" : divedZone ? (divedTitle || "ZONE").toUpperCase() : BAND_LABEL[row.object.kind] ?? row.object.kind.toUpperCase()}
          onRowClick={(row) => {
            if (row.type === "zone") diveInto(row.id);
            else openPullout(qualifiedRef(row.object.kind, row.object.id));
          }}
          onRowKeyDown={(event, row) => {
            // PHILO-8-01 — F2 on a focused zone row opens its name field
            // (zone rows are not selectable, so the registry's F2 never
            // reaches them; "Keep F2 on zone rows", the owner, 2026-09-26).
            if (row.type === "zone") {
              if (event.key === "F2") {
                event.preventDefault();
                event.stopPropagation();
                useDesk.getState().setRenamingZone(row.id);
              }
              return;
            }
            if (event.key === " ") {
              event.preventDefault();
              toggleSelected(qualifiedRef(row.object.kind, row.object.id));
            } else if (event.key === "ContextMenu" || (event.shiftKey && event.key === "F10")) {
              event.preventDefault();
              const rect = event.currentTarget.getBoundingClientRect();
              openMenu(row.object, rect.left + 24, rect.bottom);
            }
          }}
          onRowContextMenu={(event, row) => {
            if (row.type !== "object") return;
            event.preventDefault();
            openMenu(row.object, event.clientX, event.clientY);
          }}
        />
        {remaining > 0 ? <Button dense variant="ghost" className="desk-list-more" onClick={showMore}>Show {Math.min(LIST_PAGE, remaining)} more</Button> : null}
      </section>
      {rowMenu ? (
        <WorkMenu
          className="desk-world-menu"
          label={`${rowMenu.title} menu`}
          anchor="below"
          x={rowMenu.x}
          y={rowMenu.y}
          autoFocus
          entries={objectMenuEntries({ type: "object", id: rowMenu.id, ref: rowMenu.ref, kind: rowMenu.kind, title: rowMenu.title })}
          onClose={() => setRowMenu(null)}
        />
      ) : null}
      <DeliveryListSection />
      <PrReceiptsSection />
      {editing && <InlineEditor key={editing.id} o={editing} u={{ x: 0.5, y: 0.4 }} />}
      {openCards.map((p) => <Pullout key={p.id} o={p.obj!} origin={p.origin} />)}
      {/* PHILO-8-02 — the Floor's foot (#665): the delete receipt sits in
          flow directly above the selection bar it acted on. */}
      <div className="desk-world-foot" ref={footRef}>
        {failureReceipt}
        <DeskDeleteSeat />
        <AskBar />
      </div>
      {askOpen && <AskPanel />}
    </div>
  );
}
