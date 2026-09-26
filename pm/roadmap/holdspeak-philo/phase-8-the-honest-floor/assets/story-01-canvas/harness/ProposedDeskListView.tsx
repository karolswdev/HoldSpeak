/* PHILO-8-01 canvas — the list's in-row zone name field (PROPOSAL, not built).
 *
 * A copy of web/src/desk/components/DeskListView.tsx at this branch, with the
 * imports moved to the "@w" alias and three marked PROPOSAL changes:
 *   1. a zone row whose id is `renamingZoneId` draws the name field in its
 *      Name cell: the input `.desk-zone-rename` + the speak-to-fill MicButton,
 *      from the ONE rename behaviour `useZoneRenameField` (Enter commits, blur
 *      commits, Escape cancels);
 *   2. a refused name (the hub's 409 `zone_name_taken`) shows on the row as
 *      the library StateChip `failure`, `✗ NAME TAKEN`, `data-code`; the field
 *      stays open with focus;
 *   3. F2 on a focused zone row opens the same field (zone rows are not
 *      selectable, so the registry's F2 never reaches them).
 * The harness vite config swaps this module in for the real DeskListView; the
 * rest of the Desk (DeskApp, DeskChrome, the store, the hub) is the product.
 */
// HS-93-08 — the semantic list mode: the SAME Desk, expressed for
// keyboard and screen-reader use. It consumes the one store (items,
// selection, pull-out, dive) and the same world.ts records the spatial
// stage renders — zero new data paths, no second dashboard.
// HS-113-03 — the floor and zone-window lists now share DeskSortableTable:
// compact real table rows, sortable headers, sprites, and kind bands.
import "@w/desk/components/list-view.css";
import { useEffect, useMemo, useRef, useState } from "react";
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
import { WorkMenu } from "@w/desk/components/DeskMenu";
import { InlineEditor } from "@w/desk/components/InlineEditor";
import { Pullout } from "@w/desk/components/Pullout";
import { AskBar, AskPanel } from "@w/desk/components/AskPanel";
import { DeliveryListSection } from "@w/desk/components/DeliveryListSection";
import { PrReceiptsSection } from "@w/desk/components/PrReceiptsSection";
import { DeskSortableTable, type Column } from "@w/desk/components/DeskSortableTable";
import { MicButton } from "@w/desk/components/MicButton";
import { StateChip } from "@w/desk/surface";
import { useZoneRenameField } from "@w/desk/hooks/useZoneRenameField";

/* PROPOSAL 1 + 2 — the in-row field, composed from the one behaviour. */
function ZoneNameField({ zoneId, title }: { zoneId: string; title: string }) {
  const field = useZoneRenameField(zoneId, title);
  return (
    <span
      className="desk-zone-rename-row is-inrow"
      // The row's own click dives into the zone and its Enter opens it; the
      // field keeps both to itself.
      onClick={(e) => e.stopPropagation()}
      onKeyDown={(e) => e.stopPropagation()}
      {...field.rowProps}
    >
      {/* The name opens selected: typing replaces it (the Finder convention). */}
      <input
        className="desk-zone-rename"
        aria-label="Zone name"
        {...field.inputProps}
        onFocus={(e) => e.currentTarget.select()}
      />
      <MicButton draftScope={`zone-rename:${zoneId}`} onText={(t) => field.setName(t)} />
      {field.error ? (
        <span data-code="zone_name_taken" title={field.error}>
          <StateChip state="failure" label="NAME TAKEN" data-testid="zone-name-refused" />
        </span>
      ) : null}
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

export function DeskListView() {
  const items = useDesk((s) => s.items);
  const divedZone = useDesk((s) => s.divedZone);
  const selectedIds = useDesk((s) => s.selectedIds);
  const pullouts = useDesk((s) => s.pullouts);
  const editingId = useDesk((s) => s.editingId);
  const askOpen = useDesk((s) => s.askOpen);
  const renamingZoneId = useDesk((s) => s.renamingZoneId); // PROPOSAL
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
          // PROPOSAL 1 — the zone being named draws the field in its row.
          if (row.id === renamingZoneId) return <ZoneNameField key={row.id} zoneId={row.id} title={row.title} />;
          return (
            /* HS-202-04 (UX-CANON A.8) — an empty zone announced
               "<name> zone, 0 items" to a screen reader and printed
               `0 ITEMS` in its own cell. A counter of zero is a bounce in
               text AND in an accessible name; `countToken` is the one way
               a face says "N things" and it withholds the zero
               (`desk/surface/count.ts:39`). */
            <Button variant="ghost" dense className="desk-sortable-table-open" aria-label={[`${row.title} zone`, countToken(row.count, "item", "items")].filter(Boolean).join(", ")}>
              {row.title}
            </Button>
          );
        }
        const ref = qualifiedRef(row.object.kind, row.object.id);
        const selected = selectedIds.includes(ref) || selectedIds.includes(row.object.id);
        return (
          <Button variant="ghost" dense className="desk-sortable-table-open desk-list-name-cell" aria-label={selected ? `${row.object.title}, in Ask context` : row.object.title}>
            <span className="desk-list-mark" data-selected={selected || undefined} aria-hidden="true">
              {selected ? "[x]" : "[ ]"}
            </span>
            {row.object.title}
            {row.zoneName ? <span className="sr-only"> {row.zoneName.toUpperCase()}</span> : null}
            {row.attention ? <span className="sr-only"> ATTN {row.attention}</span> : null}
          </Button>
        );
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
    <div className="desk-listmode">
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
            {countToken(visible.length, "SHOWN") || "EMPTY"} of {objects.length}
          </p>
        </div>
        <DeskSortableTable
          className="desk-list-sortable"
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
            // PROPOSAL 3 — F2 on a focused zone row opens its name field.
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
      <AskBar />
      {askOpen && <AskPanel />}
    </div>
  );
}
