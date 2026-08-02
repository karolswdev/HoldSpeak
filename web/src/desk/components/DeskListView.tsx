// HS-93-08 — the semantic list mode: the SAME Desk, expressed for
// keyboard and screen-reader use. It consumes the one store (items,
// selection, pull-out, dive) and the same world.ts records the spatial
// stage renders — zero new data paths, no second dashboard.
// HS-111-07 — re-rendered as the SurfaceLedger face of the floor
// (owner P0): an opaque ground in the stage band, 26px mono rows
// (`title | kind | fact | STATE`) under kind bands, the checkbox column
// replaced by a leading [x] mono token. Row verbs: Enter/click opens
// the same pull-out, Space ropes the same ref into the Ask context,
// the ContextMenu key (or right-click) opens the object WorkMenu.
// Roving focus / arming conformance is the 08 kit sweep; these rows
// are kit-shaped so 08 inherits them.
import { useEffect, useMemo, useRef, useState } from "react";
import { qualifiedRef } from "../api";
import { useDesk } from "../store";
import { useProjections } from "../projections";
import { allObjects, objectByRef, worldObjects, worldZones } from "../world";
import { KIND_LABEL } from "../tools";
import { objectMenuEntries } from "../floorMenu";
import { WorkMenu } from "./DeskMenu";
import { SurfaceLedger, SurfaceLedgerRow } from "../surface/Surface";
import { InlineEditor } from "./InlineEditor";
import { Pullout } from "./Pullout";
import { AskBar, AskPanel } from "./AskPanel";
import { DeliveryListSection } from "./DeliveryListSection";
import { PrReceiptsSection } from "./PrReceiptsSection";

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
};

export function DeskListView() {
  const items = useDesk((s) => s.items);
  const divedZone = useDesk((s) => s.divedZone);
  const selectedIds = useDesk((s) => s.selectedIds);
  const pullouts = useDesk((s) => s.pullouts);
  const editingId = useDesk((s) => s.editingId);
  const askOpen = useDesk((s) => s.askOpen);
  const subjectCounts = useProjections((s) => s.subject_counts);
  const { openPullout, toggleSelected, diveInto, surface } =
    useDesk.getState();

  const zones = worldZones(items, divedZone);
  // The root list shows EVERY object (filed ones carry their zone as the
  // fact token) so nothing is stranded behind a spatial-only affordance;
  // a dive narrows to the zone's members, exactly like the stage.
  const objects = useMemo(
    () => (divedZone ? worldObjects(items, divedZone) : allObjects(items)),
    [items, divedZone],
  );
  const zoneNames = useMemo(() => {
    const map = new Map<string, string>();
    for (const d of items.directory || []) {
      const name = String(d.title || d.name || "Zone");
      for (const mid of ((d as any).memberIds as string[]) || [])
        map.set(mid, name);
    }
    return map;
  }, [items.directory]);

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
  const visible = objects.slice(0, limit);
  const remaining = objects.length - visible.length;
  const divedTitle = divedZone
    ? String(
        (items.directory || []).find((d) => d.id === divedZone)?.name ||
          "Zone",
      )
    : null;

  const attentionOf = (o: (typeof visible)[number]) => {
    const ref = qualifiedRef(o.kind, o.id);
    const subject =
      o.kind === "coder"
        ? `coder_session:${String(o.ref.agent || "claude")}:${o.id}`
        : ref;
    return subjectCounts[subject]?.needs_attention || 0;
  };
  const attnTotal = useMemo(
    () => objects.reduce((n, o) => n + attentionOf(o), 0),
    [objects, subjectCounts],
  );

  const openCards = pullouts
    .map((p) => ({ ...p, obj: objectByRef(items, p.id) }))
    .filter((p) => Boolean(p.obj));
  const editing = editingId ? objectByRef(items, editingId) : null;

  const showMore = () => {
    const next = Math.min(objects.length, limit + LIST_PAGE);
    setLimit(next);
    // The last page removes the button; settle focus on the count so the
    // keyboard never falls back to the document body.
    if (next >= objects.length) statusRef.current?.focus();
  };

  // Band the visible slice: the dived zone IS the band; the root floor
  // bands by kind (ZONES lead so the dive path stays one keystroke).
  const bands: { head: string; rows: typeof visible }[] = useMemo(() => {
    if (divedZone) return [{ head: (divedTitle || "ZONE").toUpperCase(), rows: visible }];
    const by = new Map<string, typeof visible>();
    for (const o of visible) {
      const head = BAND_LABEL[o.kind] ?? o.kind.toUpperCase();
      const list = by.get(head) ?? [];
      list.push(o);
      by.set(head, list);
    }
    return Array.from(by, ([head, rows]) => ({ head, rows }));
  }, [visible, divedZone, divedTitle]);

  return (
    <div className="desk-listmode">
      <section aria-labelledby="desk-list-title" className="desk-list-face">
        <h2 id="desk-list-title" className="sr-only">
          {divedTitle ? `${divedTitle} zone` : "Desk items"}
        </h2>
        <SurfaceLedger
          cols="desk"
          count={
            <>
              {divedZone ? (
                <button
                  type="button"
                  className="desk-list-open desk-surface"
                  onClick={surface}
                >
                  ← ALL
                </button>
              ) : null}
              {`ITEMS ${objects.length} · ZONES ${zones.length} · ATTN ${attnTotal}`}
            </>
          }
          controls={
            <p
              className="desk-list-status"
              role="status"
              tabIndex={-1}
              ref={statusRef}
            >
              Showing {visible.length} of {objects.length}
            </p>
          }
        >
          {!divedZone && zones.length ? (
            <>
              <span className="desk-list-band" role="presentation">
                ZONES
              </span>
              <ul className="surface-ledger-rows" aria-label="Zones">
                {zones.map((z) => (
                  <SurfaceLedgerRow
                    key={`zone:${z.id}`}
                    expands={false}
                    lead={<span className="desk-list-mark" aria-hidden="true" />}
                    primary={z.title}
                    lineLabel={`${z.title} zone, ${z.count} ${
                      z.count === 1 ? "item" : "items"
                    }`}
                    cells={
                      <>
                        <span className="surface-ledger-cell">ZONE</span>
                        <span className="surface-ledger-cell">
                          {z.count === 1 ? "1 ITEM" : `${z.count} ITEMS`}
                        </span>
                        <span className="surface-ledger-cell desk-list-state" />
                      </>
                    }
                    onToggle={() => diveInto(z.id)}
                  />
                ))}
              </ul>
            </>
          ) : null}
          {bands.map((band) => (
            <div key={band.head}>
              <span className="desk-list-band" role="presentation">
                {band.head}
              </span>
              <ul className="surface-ledger-rows">
                {band.rows.map((o) => {
                  const ref = qualifiedRef(o.kind, o.id);
                  const selected =
                    selectedIds.includes(ref) || selectedIds.includes(o.id);
                  const attention = attentionOf(o);
                  const zoneName =
                    zoneNames.get(ref) ?? zoneNames.get(o.id) ?? "";
                  const openMenuAt = (x: number, y: number) =>
                    setRowMenu({
                      id: o.id,
                      ref,
                      kind: o.kind,
                      title: o.title,
                      x,
                      y,
                    });
                  return (
                    <SurfaceLedgerRow
                      key={`${o.kind}:${o.id}`}
                      expands={false}
                      lead={
                        <span
                          className="desk-list-mark"
                          data-selected={selected || undefined}
                          aria-hidden="true"
                        >
                          {selected ? "[x]" : "[ ]"}
                        </span>
                      }
                      primary={o.title}
                      lineLabel={
                        selected
                          ? `${o.title}, in Ask context`
                          : o.title
                      }
                      cells={
                        <>
                          <span className="surface-ledger-cell">
                            {(KIND_LABEL[o.kind] ?? o.kind).toUpperCase()}
                          </span>
                          <span className="surface-ledger-cell">
                            {zoneName.toUpperCase()}
                          </span>
                          <span className="surface-ledger-cell desk-list-state">
                            {attention ? `ATTN ${attention}` : ""}
                          </span>
                        </>
                      }
                      onToggle={() => openPullout(ref)}
                      onLineKeyDown={(e) => {
                        if (e.key === " ") {
                          // Space = the Ask-context rope (the checkbox's
                          // exact store path).
                          e.preventDefault();
                          toggleSelected(ref);
                        } else if (
                          e.key === "ContextMenu" ||
                          (e.shiftKey && e.key === "F10")
                        ) {
                          e.preventDefault();
                          const r = e.currentTarget.getBoundingClientRect();
                          openMenuAt(r.left + 24, r.bottom);
                        }
                      }}
                      onLineContextMenu={(e) => {
                        e.preventDefault();
                        openMenuAt(e.clientX, e.clientY);
                      }}
                    />
                  );
                })}
              </ul>
            </div>
          ))}
        </SurfaceLedger>
        {remaining > 0 ? (
          <button
            type="button"
            className="desk-chip desk-list-more"
            onClick={showMore}
          >
            Show {Math.min(LIST_PAGE, remaining)} more
          </button>
        ) : null}
      </section>
      {rowMenu ? (
        <WorkMenu
          className="desk-world-menu"
          label={`${rowMenu.title} menu`}
          anchor="below"
          x={rowMenu.x}
          y={rowMenu.y}
          autoFocus
          entries={objectMenuEntries({
            type: "object",
            id: rowMenu.id,
            ref: rowMenu.ref,
            kind: rowMenu.kind,
            title: rowMenu.title,
          })}
          onClose={() => setRowMenu(null)}
        />
      ) : null}
      <DeliveryListSection />
      <PrReceiptsSection />
      {editing && (
        <InlineEditor key={editing.id} o={editing} u={{ x: 0.5, y: 0.4 }} />
      )}
      {openCards.map((p) => (
        <Pullout key={p.id} o={p.obj!} origin={p.origin} />
      ))}
      <AskBar />
      {askOpen && <AskPanel />}
    </div>
  );
}
