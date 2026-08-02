// HS-105-03 — a drawer opens into a REAL desk window (the Workbench
// drawer rule): the desk stays visible, several zone windows coexist,
// and THE WINDOW REMEMBERS — rect (the panel system), view, and sort
// (`hs.desk.zone-views`). Icons view speaks the world's cell contract;
// List view is the density altitude (Name / Kind / Modified, sortable).
import { useMemo, useState } from "react";
// @ts-ignore — shared ESM module (see ../sprites.d.ts)
import { spriteUrl } from "../sprites";
import { useDesk, type ZoneViewPref } from "../store";
import { objectByRef, type WorldObject } from "../world";
import { productLabel } from "../../lib/productLanguage";
import { humanTime } from "../surface/format";
import { SurfaceState } from "../surface/Surface";
import { SurfaceWings } from "../surface/wings";
import { DeskWindowFooter } from "./DeskWindowFooter";
import { DeskWindowFrame } from "./DeskWindow";

type SortKey = ZoneViewPref["sort"];

const DEFAULT_PREF: ZoneViewPref = { view: "icons", sort: "name", dir: "asc" };

function memberTime(o: WorldObject): string {
  const r = o.ref as Record<string, unknown>;
  return String(r.lastModified || r.endedAt || r.createdAt || "");
}

export function ZoneWindow({
  zoneId,
  origin,
}: {
  zoneId: string;
  origin?: { x: number; y: number } | null;
}) {
  const items = useDesk((s) => s.items);
  // Select the RAW slot (may be undefined) and default outside the
  // selector — an inline fallback object is a new snapshot every check
  // and loops React (caught live by the first zone-window walk).
  const savedPref = useDesk((s) => s.zoneViewPrefs[zoneId]);
  const pref: ZoneViewPref = savedPref ?? DEFAULT_PREF;
  const { closeZoneWindow, setZoneViewPref, openPullout, removeFromDir } =
    useDesk.getState();
  const zone = (items.directory || []).find((d) => d.id === zoneId);
  const memberIds: string[] = ((zone as any)?.memberIds as string[]) || [];
  const [selected, setSelected] = useState<string | null>(null);

  const members = useMemo(() => {
    const resolved = memberIds
      .map((ref) => objectByRef(items, ref))
      .filter((o): o is WorldObject => Boolean(o));
    const dirMul = pref.dir === "desc" ? -1 : 1;
    const by: Record<SortKey, (a: WorldObject, b: WorldObject) => number> = {
      name: (a, b) => a.title.localeCompare(b.title),
      kind: (a, b) =>
        a.kind.localeCompare(b.kind) || a.title.localeCompare(b.title),
      // Newest first is the natural ascending read for time.
      modified: (a, b) => memberTime(b).localeCompare(memberTime(a)),
    };
    return [...resolved].sort((a, b) => dirMul * by[pref.sort](a, b));
  }, [items, memberIds.join(","), pref.sort, pref.dir]);

  if (!zone) return null;
  const title = String(zone.name || zone.title || "Zone");
  const unresolved = memberIds.length - members.length;

  const sortHeader = (key: SortKey, label: string) => (
    <button
      type="button"
      className={`zone-sort${pref.sort === key ? " on" : ""}`}
      aria-sort={
        pref.sort === key
          ? pref.dir === "asc"
            ? "ascending"
            : "descending"
          : undefined
      }
      onClick={() =>
        setZoneViewPref(zoneId, {
          sort: key,
          dir: pref.sort === key && pref.dir === "asc" ? "desc" : "asc",
        })
      }
    >
      {label}
      {pref.sort === key ? (pref.dir === "asc" ? " ↑" : " ↓") : ""}
    </button>
  );

  return (
    <DeskWindowFrame
      id={`zone:${zoneId}`}
      glyph="▦"
      label={title}
      className="desk-pullout is-card desk-zone-window"
      fitContent
      origin={origin}
      icon={
        <img src={spriteUrl("directory", zoneId)} alt="" width={30} height={30} />
      }
      title={title}
      open
      onClose={() => closeZoneWindow(zoneId)}
      wings={
        <SurfaceWings
          wings={[
            { id: "icons", label: "Icons" },
            { id: "list", label: "List" },
          ]}
          active={pref.view}
          onChange={(view) => setZoneViewPref(zoneId, { view: view as ZoneViewPref["view"] })}
        />
      }
    >
      <div className="desk-pullout-body desk-surface-body">
        {members.length === 0 ? (
          <SurfaceState empty emptyLabel="Empty" />
        ) : pref.view === "icons" ? (
          <div className="zone-grid" role="list">
            {members.map((m) => (
              <button
                key={`${m.kind}:${m.id}`}
                type="button"
                role="listitem"
                className={`zone-cell${selected === `${m.kind}:${m.id}` ? " is-selected" : ""}`}
                aria-selected={selected === `${m.kind}:${m.id}`}
                onClick={() => setSelected(`${m.kind}:${m.id}`)}
                onDoubleClick={(e) =>
                  openPullout(m.id, { x: e.clientX, y: e.clientY })
                }
              >
                <img
                  src={spriteUrl(m.kind, m.id)}
                  alt=""
                  width={48}
                  height={48}
                />
                <span className="zone-cell-label">{m.title}</span>
              </button>
            ))}
          </div>
        ) : (
          <table className="zone-list">
            <thead>
              <tr>
                <th aria-hidden="true" />
                <th>{sortHeader("name", "Name")}</th>
                <th>{sortHeader("kind", "Kind")}</th>
                <th>{sortHeader("modified", "Modified")}</th>
                <th aria-hidden="true" />
              </tr>
            </thead>
            <tbody>
              {members.map((m) => {
                const t = memberTime(m);
                return (
                  <tr
                    key={`${m.kind}:${m.id}`}
                    className={selected === `${m.kind}:${m.id}` ? "is-selected" : ""}
                    onClick={() => setSelected(`${m.kind}:${m.id}`)}
                  >
                    <td className="zone-list-ic">
                      <img
                        src={spriteUrl(m.kind, m.id)}
                        alt=""
                        width={20}
                        height={20}
                      />
                    </td>
                    <td>
                      <button
                        type="button"
                        className="zone-list-open"
                        aria-selected={selected === `${m.kind}:${m.id}`}
                        onClick={() => setSelected(`${m.kind}:${m.id}`)}
                        onDoubleClick={(e) =>
                          openPullout(m.id, { x: e.clientX, y: e.clientY })
                        }
                      >
                        {m.title}
                      </button>
                    </td>
                    <td className="quiet">{productLabel(m.kind)}</td>
                    <td className="quiet">{t ? humanTime(t) : "—"}</td>
                    <td>
                      <button
                        type="button"
                        className="desk-chip quiet zone-unfile"
                        aria-label={`Take ${m.title} out of ${title}`}
                        onClick={() =>
                          void removeFromDir(m.id, zoneId, m.kind)
                        }
                      >
                        Take out
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
      <DeskWindowFooter
        status={
          <span className="quiet">
            {members.length} {members.length === 1 ? "item" : "items"}
            {unresolved > 0 ? ` · ${unresolved} unavailable` : ""}
          </span>
        }
      />
    </DeskWindowFrame>
  );
}
