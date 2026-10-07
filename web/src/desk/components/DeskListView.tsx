// HS-93-08 — the semantic list mode: the SAME Desk, expressed for
// keyboard and screen-reader use. It consumes the one store (items,
// selection, pull-out, dive) and the same world.ts records the spatial
// stage renders — zero new data paths, no second dashboard.
// PHILO-14 A2 — the list is a list: the ObjectList species (Name, Kind,
// When, State; sort by header). A press or Space ropes the row into the Ask
// context (the selected row, never a `[ ]`/`[x]` mark); Enter or a double
// press opens it.
import "./list-view.css";
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Button } from "../../components/signal/Signal";
import { qualifiedRef } from "../api";
import { ObjectList, countToken, type ObjectListRow, type ObjectSort, type ObjectSortKey } from "../surface";
import { wireDate } from "../surface/format";
import { whenWord } from "../drawer/members";
import { useDesk } from "../store";
import { useProjections } from "../projections";
import { allObjects, objectByRef, worldObjects, worldZones, type WorldObject } from "../world";
import { KIND_LABEL } from "../tools";
// @ts-ignore — shared ESM module (see ../sprites.d.ts)
import { refAgent, spriteUrl } from "../sprites";
import { objectMenuEntries } from "../floorMenu";
import { WorkMenu } from "./DeskMenu";
import { InlineEditor } from "./InlineEditor";
import { Pullout } from "./Pullout";
import { InfoWindow } from "./InfoWindow";
import { AskBar, AskPanel } from "./AskPanel";
import { DeliveryListSection } from "./DeliveryListSection";
import { PrReceiptsSection } from "./PrReceiptsSection";
import { DeskDeleteSeat } from "../deleteReceipt";
import { useDeskWriteReceipt } from "../hooks/useWriteReceipt";
import { ZoneRenameRow } from "./ZoneRenameRow";

/** Rows per page — a plain "show more" pagination, no virtualization dep. */
export const LIST_PAGE = 100;

type ListRow = ObjectListRow & {
  /** A zone row dives; an object row selects (Ask context) and opens. */
  zoneId?: string;
  zoneCount?: number;
  object?: WorldObject;
};

const LIST_SORT_KEY = "hs.desk.list-sort";
const DEFAULT_SORT: ObjectSort = { key: "name", dir: "asc" };
const SORT_KEYS: readonly ObjectSortKey[] = ["name", "kind", "when", "state"];

function loadListSort(): ObjectSort {
  try {
    const saved = JSON.parse(localStorage.getItem(LIST_SORT_KEY) || "null");
    if (saved && SORT_KEYS.includes(saved.key) && (saved.dir === "asc" || saved.dir === "desc")) {
      return saved as ObjectSort;
    }
  } catch {
    // Storage is optional; the list remains useful with its default order.
  }
  return DEFAULT_SORT;
}

/** The order the species draws, applied before the page is cut (so "Show
 * more" pages through the sorted list, not a sorted page). */
function compareRows(sort: ObjectSort) {
  const value = (row: ListRow): string | number => {
    if (sort.key === "kind") return row.kindWord ?? row.kind;
    if (sort.key === "when") return row.whenSort ?? row.when ?? "";
    if (sort.key === "state") return row.state?.label ?? "";
    return row.name;
  };
  const sign = sort.dir === "asc" ? 1 : -1;
  return (a: ListRow, b: ListRow) => {
    const va = value(a);
    const vb = value(b);
    const order = typeof va === "number" && typeof vb === "number" ? va - vb : String(va).localeCompare(String(vb));
    return order * sign || a.name.localeCompare(b.name);
  };
}

/** PHILO-14 A2: the Floor's Ask context is a set; the species draws one
 * selected row. Every other row in the set wears the same selected state and
 * says "in Ask context" to a screen reader (never a `[x]` mark). */
function useAskContextRows(root: React.RefObject<HTMLElement | null>, selected: ReadonlySet<string>) {
  useLayoutEffect(() => {
    root.current?.querySelectorAll<HTMLElement>(".object-list-row[data-object-id]").forEach((row) => {
      const on = selected.has(row.dataset.objectId ?? "");
      row.setAttribute("aria-selected", on ? "true" : "false");
      if (on) row.dataset.selected = "true";
      else delete row.dataset.selected;
      const open = row.querySelector<HTMLElement>(".object-list-open");
      if (!open) return;
      const base = (open.getAttribute("aria-label") ?? "").replace(/, in Ask context$/, "");
      open.setAttribute("aria-label", on ? `${base}, in Ask context` : base);
    });
  });
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
  const infoWindows = useDesk((s) => s.infoWindows);
  const pullouts = useDesk((s) => s.pullouts);
  const editingId = useDesk((s) => s.editingId);
  const askOpen = useDesk((s) => s.askOpen);
  // PHILO-8-01 — the zone being named draws its field over the list.
  const renamingZoneId = useDesk((s) => s.renamingZoneId);
  const subjectCounts = useProjections((s) => s.subject_counts);
  const { openPullout, toggleSelected, diveInto, surface } = useDesk.getState();

  const zones = worldZones(items, divedZone);
  // The root list shows every owner object (filed ones too), but repository
  // roadmaps belong to explicit Delivery, not the ordinary Floor. A dived
  // zone keeps its existing world projection.
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
  const [sort, setSort] = useState<ObjectSort>(loadListSort);
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
  const listRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => setLimit(LIST_PAGE), [divedZone]);
  useEffect(() => {
    try {
      localStorage.setItem(LIST_SORT_KEY, JSON.stringify(sort));
    } catch {
      // Storage is optional; sorting is still live for this session.
    }
  }, [sort]);

  const objectRows = useMemo<ListRow[]>(
    () =>
      objects.map((object) => {
        const record = object.ref as unknown as Record<string, unknown>;
        const at = record.lastModified ?? record.endedAt ?? record.startedAt ?? record.createdAt;
        const attention = attentionOf(object);
        const kind = (KIND_LABEL[object.kind] ?? object.kind).toUpperCase();
        // The Floor spans zones: a filed object names its zone beside its kind
        // (ObjectList has no Where column; inside a drawer every object shares one).
        const zone = divedZone ? "" : zoneNames.get(qualifiedRef(object.kind, object.id)) ?? zoneNames.get(object.id) ?? "";
        return {
          id: qualifiedRef(object.kind, object.id),
          kind: object.kind === "coder" ? "agent" : object.kind,
          name: object.title,
          kindWord: zone ? `${kind} · ${zone.toUpperCase()}` : kind,
          when: whenWord(at),
          whenSort: wireDate(at)?.getTime(),
          state: attention ? { label: `ATTN ${attention}`, tone: "warn" as const } : undefined,
          sprite: spriteUrl(object.kind, object.id, "rest", refAgent(object.ref)),
          object,
        };
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [objects, subjectCounts, zoneNames, divedZone],
  );
  const sortedObjects = useMemo(() => [...objectRows].sort(compareRows(sort)), [objectRows, sort]);
  const visible = sortedObjects.slice(0, limit);
  const remaining = objects.length - visible.length;
  const divedTitle = divedZone
    ? String((items.directory || []).find((d) => d.id === divedZone)?.name || "Zone")
    : null;
  const attnTotal = useMemo(
    () => objects.reduce((n, o) => n + attentionOf(o), 0),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [objects, subjectCounts],
  );
  const rows = useMemo<ListRow[]>(
    () => [
      ...(!divedZone
        ? zones.map((zone) => ({
            id: `zone:${zone.id}`,
            kind: "directory",
            name: zone.title,
            kindWord: "ZONE",
            // HS-202-04 (UX-CANON A.8): an empty zone says EMPTY, never `0 ITEMS`.
            when: countToken(zone.count, "ITEM") ?? "EMPTY",
            zoneId: zone.id,
            zoneCount: zone.count,
          }))
        : []),
      ...visible,
    ],
    [divedZone, zones, visible],
  );
  const selectedSet = useMemo(() => {
    const set = new Set<string>();
    for (const row of rows) {
      if (row.object && (selectedIds.includes(row.id) || selectedIds.includes(row.object.id))) set.add(row.id);
    }
    return set;
  }, [rows, selectedIds]);
  const lastSelected = [...selectedSet].at(-1) ?? null;
  useAskContextRows(listRef, selectedSet);

  const openCards = pullouts
    .map((p) => ({ ...p, obj: objectByRef(items, p.id) }))
    .filter((p) => Boolean(p.obj));
  const editing = editingId ? objectByRef(items, editingId) : null;
  const rowById = (id: string | undefined) => rows.find((row) => row.id === id);
  const rowOf = (target: EventTarget | null) =>
    rowById((target as HTMLElement | null)?.closest<HTMLElement>("[data-object-id]")?.dataset.objectId);
  const renamingZone = renamingZoneId ? zones.find((zone) => zone.id === renamingZoneId) : null;
  const [renameCell, setRenameCell] = useState<HTMLElement | null>(null);
  useLayoutEffect(() => {
    const cell = renamingZone
      ? [...(listRef.current?.querySelectorAll<HTMLElement>(".object-list-row[data-object-id]") ?? [])]
          .find((row) => row.dataset.objectId === `zone:${renamingZone.id}`)
          ?.querySelector<HTMLElement>(".object-list-name") ?? null
      : null;
    if (cell !== renameCell) setRenameCell(cell);
  });

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
            {divedTitle ? <span className="desk-list-zone">{divedTitle.toUpperCase()} · </span> : null}
            {[countToken(objects.length, "ITEM"), countToken(zones.length, "ZONE"), countToken(attnTotal, "ATTN")].filter(Boolean).join(" · ") || "EMPTY"}
          </span>
          <p className="desk-list-status" role="status" tabIndex={-1} ref={statusRef}>
            {countToken(visible.length, "SHOWN", "SHOWN") || "EMPTY"} OF {objects.length}
          </p>
        </div>
        <div
          ref={listRef}
          className="desk-list-objects"
          onKeyDown={(event) => {
            const row = rowOf(event.target);
            if (!row) return;
            // PHILO-8-01 — F2 on a focused zone row opens its name field.
            if (row.zoneId) {
              if (event.key === "F2") {
                event.preventDefault();
                event.stopPropagation();
                useDesk.getState().setRenamingZone(row.zoneId);
              }
              return;
            }
            if (row.object && (event.key === "ContextMenu" || (event.shiftKey && event.key === "F10"))) {
              event.preventDefault();
              const rect = (event.target as HTMLElement).getBoundingClientRect();
              openMenu(row.object, rect.left + 24, rect.bottom);
            }
          }}
          onContextMenu={(event) => {
            const row = rowOf(event.target);
            if (!row?.object) return;
            event.preventDefault();
            openMenu(row.object, event.clientX, event.clientY);
          }}
        >
          <ObjectList
            className="desk-list-sortable"
            label={divedTitle ? `${divedTitle} zone` : "Desk items"}
            rows={rows}
            sort={sort}
            onSort={(key) =>
              setSort((now) => (now.key === key ? { key, dir: now.dir === "asc" ? "desc" : "asc" } : { key, dir: "asc" }))
            }
            selectedId={lastSelected}
            onSelect={(id) => {
              const row = rowById(id);
              if (row?.zoneId) diveInto(row.zoneId);
              // A press or Space ropes the ref into the Ask context.
              else if (row) toggleSelected(row.id);
            }}
            onOpen={(id) => {
              const row = rowById(id);
              if (row?.zoneId) diveInto(row.zoneId);
              else if (row) openPullout(row.id);
            }}
          />
        </div>
        {renamingZone && renameCell
          ? createPortal(
              // PHILO-8-01 (ratified): the zone being named holds the one name
              // field in its own Name cell.
              <ZoneRenameRow key={renamingZone.id} zoneId={renamingZone.id} title={renamingZone.title} placement="inrow" />,
              renameCell,
            )
          : null}
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
      {openCards.map((p) => <Pullout key={p.id} o={p.obj!} pulloutId={p.id} origin={p.origin} />)}
      {/* Get Info opened nothing in list mode: only the spatial Floor
          (WorldStage) mounted the Info windows the store holds. */}
      {infoWindows.map((w) => <InfoWindow key={w.ref} refId={w.ref} origin={w.origin} onOpenZone={(zoneId) => {
        // The list has no zone windows: it dives, and the Info window (full
        // screen at phone width) gets out of the way of the zone it opened.
        diveInto(zoneId);
        useDesk.getState().closeInfoWindow(w.ref);
      }} />)}
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
