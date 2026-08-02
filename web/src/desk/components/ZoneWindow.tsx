// HS-105-03 — a drawer opens into a REAL desk window (the Workbench
// drawer rule): the desk stays visible, several zone windows coexist,
// and THE WINDOW REMEMBERS — rect (the panel system), view, and sort
// (`hs.desk.zone-views`). Icons view speaks the world's cell contract;
// List view is the shared DeskSortableTable density altitude.
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
import { DeskSortableTable, type Column } from "./DeskSortableTable";

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
  const [selectedMemberKey, setSelectedMemberKey] = useState<string | null>(null);
  const zone = (items.directory || []).find((d) => d.id === zoneId);
  const memberIds: string[] = ((zone as any)?.memberIds as string[]) || [];

  const members = useMemo(() => {
    const resolved = memberIds
      .map((ref) => objectByRef(items, ref))
      .filter((o): o is WorldObject => Boolean(o));
    const dirMul = pref.dir === "desc" ? -1 : 1;
    const by: Record<SortKey, (a: WorldObject, b: WorldObject) => number> = {
      name: (a, b) => a.title.localeCompare(b.title),
      kind: (a, b) => a.kind.localeCompare(b.kind) || a.title.localeCompare(b.title),
      // Newest first is the natural ascending read for time.
      modified: (a, b) => memberTime(b).localeCompare(memberTime(a)),
    };
    return [...resolved].sort((a, b) => dirMul * by[pref.sort](a, b));
  }, [items, memberIds.join(","), pref.sort, pref.dir]);

  if (!zone) return null;
  const title = String(zone.name || zone.title || "Zone");
  const unresolved = memberIds.length - members.length;
  const columns: Column<WorldObject>[] = [
    {
      key: "icon",
      label: "",
      width: "36px",
      render: (member) => (
        <img
          className="desk-sortable-table-sprite"
          src={spriteUrl(member.kind, member.id)}
          alt=""
          width={28}
          height={28}
        />
      ),
    },
    { key: "name", label: "Name", sortable: true, render: (member) => member.title },
    {
      key: "kind",
      label: "Kind",
      sortable: true,
      render: (member) => <span className="quiet">{productLabel(member.kind)}</span>,
    },
    {
      key: "modified",
      label: "Modified",
      sortable: true,
      render: (member) => {
        const time = memberTime(member);
        return <span className="quiet">{time ? humanTime(time) : "—"}</span>;
      },
    },
  ];

  return (
    <DeskWindowFrame
      id={`zone:${zoneId}`}
      glyph="▦"
      label={title}
      className="desk-pullout is-card desk-zone-window"
      fitContent
      origin={origin}
      icon={<img src={spriteUrl("directory", zoneId)} alt="" width={30} height={30} />}
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
            {members.map((member) => (
              <button
                key={`${member.kind}:${member.id}`}
                type="button"
                role="listitem"
                className={`zone-cell${selectedMemberKey === `${member.kind}:${member.id}` ? " is-selected" : ""}`}
                aria-selected={selectedMemberKey === `${member.kind}:${member.id}`}
                onClick={() => setSelectedMemberKey(`${member.kind}:${member.id}`)}
                onDoubleClick={(event) =>
                  openPullout(member.id, { x: event.clientX, y: event.clientY })
                }
              >
                <img src={spriteUrl(member.kind, member.id)} alt="" width={48} height={48} />
                <span className="zone-cell-label">{member.title}</span>
              </button>
            ))}
          </div>
        ) : (
          <DeskSortableTable
            className="desk-zone-list"
            data={members}
            columns={columns}
            sort={{ key: pref.sort, dir: pref.dir }}
            onSort={(key, dir) => setZoneViewPref(zoneId, { sort: key as SortKey, dir })}
            rowKey={(member) => `${member.kind}:${member.id}`}
            selectedKey={selectedMemberKey}
            rowLabel={(member) => member.title}
            onRowClick={(member) => setSelectedMemberKey(`${member.kind}:${member.id}`)}
            onRowDoubleClick={(member) => openPullout(member.id)}
            rowActions={(member) => (
              <button
                type="button"
                className="desk-chip quiet zone-unfile"
                aria-label={`Take ${member.title} out of ${title}`}
                onClick={(event) => {
                  event.stopPropagation();
                  void removeFromDir(member.id, zoneId, member.kind);
                }}
              >
                Take out
              </button>
            )}
          />
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
