// HS-93-08 — the semantic list mode: the SAME Desk, expressed as an
// accessible table for keyboard and screen-reader use. It consumes the one
// store (items, selection, pull-out, dive) and the same world.ts records the
// spatial stage renders — zero new data paths, no second dashboard. Every
// spatial action has a named equivalent here: Enter on a row title opens the
// same pull-out, the row checkbox ropes the same ref into the Ask context,
// a zone chip dives into the same zone.
import { useEffect, useMemo, useRef, useState } from "react";
import { qualifiedRef } from "../api";
import { useDesk } from "../store";
import { useProjections } from "../projections";
import { allObjects, objectByRef, worldObjects, worldZones } from "../world";
import { KIND_LABEL } from "./DeskToolShelf";
import { InlineEditor } from "./InlineEditor";
import { Pullout } from "./Pullout";
import { AskBar, AskPanel } from "./AskPanel";
import { DeliveryListSection } from "./DeliveryListSection";

/** Rows per page — a plain "show more" pagination, no virtualization dep. */
export const LIST_PAGE = 100;

export function DeskListView() {
  const items = useDesk((s) => s.items);
  const divedZone = useDesk((s) => s.divedZone);
  const selectedIds = useDesk((s) => s.selectedIds);
  const pulloutId = useDesk((s) => s.pulloutId);
  const editingId = useDesk((s) => s.editingId);
  const askOpen = useDesk((s) => s.askOpen);
  const subjectCounts = useProjections((s) => s.subject_counts);
  const { openPullout, toggleSelected, diveInto, surface } =
    useDesk.getState();

  const zones = worldZones(items, divedZone);
  // The root list shows EVERY object (filed ones carry their zone in the
  // Zone column) so nothing is stranded behind a spatial-only affordance;
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

  const pullout = pulloutId ? objectByRef(items, pulloutId) : null;
  const editing = editingId ? objectByRef(items, editingId) : null;

  const showMore = () => {
    const next = Math.min(objects.length, limit + LIST_PAGE);
    setLimit(next);
    // The last page removes the button; settle focus on the count so the
    // keyboard never falls back to the document body.
    if (next >= objects.length) statusRef.current?.focus();
  };

  return (
    <div className="desk-listmode">
      {divedZone && (
        <button
          type="button"
          className="desk-chip desk-surface"
          onClick={surface}
        >
          ← All
        </button>
      )}
      <section aria-labelledby="desk-list-title">
        <header className="desk-list-head">
          <h2 id="desk-list-title">
            {divedTitle ? `${divedTitle} zone` : "Desk items"}
          </h2>
          <p
            className="desk-list-status"
            role="status"
            tabIndex={-1}
            ref={statusRef}
          >
            Showing {visible.length} of {objects.length}
          </p>
        </header>
        {!divedZone && zones.length ? (
          <nav className="desk-list-zones" aria-label="Zones">
            <ul>
              {zones.map((z) => (
                <li key={z.id}>
                  <button
                    type="button"
                    className="desk-chip"
                    onClick={() => diveInto(z.id)}
                  >
                    {z.title}
                    <small>
                      {z.count === 1 ? "1 item" : `${z.count} items`}
                    </small>
                  </button>
                </li>
              ))}
            </ul>
          </nav>
        ) : null}
        <div className="desk-list-scroll">
          <table className="desk-list-table" aria-labelledby="desk-list-title">
            <thead>
              <tr>
                <th scope="col">
                  <span className="sr-only">Select for Ask context</span>
                </th>
                <th scope="col">Item</th>
                <th scope="col">Kind</th>
                <th scope="col">Attention</th>
                <th scope="col">Zone</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((o) => {
                const ref = qualifiedRef(o.kind, o.id);
                const selected =
                  selectedIds.includes(ref) || selectedIds.includes(o.id);
                const subject =
                  o.kind === "coder"
                    ? `coder_session:${String(o.ref.agent || "claude")}:${o.id}`
                    : ref;
                const attention =
                  subjectCounts[subject]?.needs_attention || 0;
                return (
                  <tr key={`${o.kind}:${o.id}`}>
                    <td className="desk-list-select">
                      <input
                        type="checkbox"
                        checked={selected}
                        onChange={() => toggleSelected(ref)}
                        aria-label={`Select ${o.title} for Ask context`}
                      />
                    </td>
                    <th scope="row">
                      <button
                        type="button"
                        className="desk-list-open"
                        onClick={() => openPullout(ref)}
                      >
                        {o.title}
                      </button>
                    </th>
                    <td>{KIND_LABEL[o.kind] ?? o.kind}</td>
                    <td className="desk-list-attention">
                      {attention
                        ? `${attention} need${attention === 1 ? "s" : ""} attention`
                        : ""}
                    </td>
                    <td>{zoneNames.get(ref) ?? zoneNames.get(o.id) ?? ""}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
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
      <DeliveryListSection />
      {editing && (
        <InlineEditor key={editing.id} o={editing} u={{ x: 0.5, y: 0.4 }} />
      )}
      {pullout && <Pullout key={pullout.id} o={pullout} />}
      <AskBar />
      {askOpen && <AskPanel />}
    </div>
  );
}
