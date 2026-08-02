// HS-105-04 — Info on everything (the Workbench "Information…" rule):
// ONE card, derived from the Info contract, for every primitive kind and
// for zones. Identity edits in place through the existing update paths;
// Properties are the declared tooltypes (real update paths only); absent
// data renders as absence. No kind hand-builds its Info.
import { useState } from "react";
// @ts-ignore — shared ESM module (see ../sprites.d.ts)
import { spriteUrl } from "../sprites";
import { useDesk } from "../store";
import { objectByRef, type WorldObject } from "../world";
import { filedZones, kindInfo, kindLabel } from "../infoContract";
import { lineage } from "../lineage";
import { humanTime } from "../surface/format";
import { StringGadget } from "../surface/gadgets";
import { DeskWindowFrame } from "./DeskWindow";

function IdentityName({ o }: { o: WorldObject }) {
  const { updatePrimitive, renameZone } = useDesk.getState();
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(o.title);
  const commit = () => {
    const name = draft.trim();
    setEditing(false);
    if (!name || name === o.title) return;
    if (o.kind === "directory") void renameZone(o.id, name);
    else if (o.kind === "note" || o.kind === "meeting")
      void updatePrimitive(o.kind, o.id, { title: name });
    else void updatePrimitive(o.kind, o.id, { name });
  };
  if (!editing)
    return (
      <button
        type="button"
        className="info-name"
        title="Rename"
        onClick={() => {
          setDraft(o.title);
          setEditing(true);
        }}
      >
        {o.title}
      </button>
    );
  // HS-111-10 mic sweep: the rename well is the kit's StringGadget.
  // Commit on focus LEAVING the well (relatedTarget check) so pressing
  // the speak-to-fill mic never commits-and-unmounts mid-utterance.
  return (
    <span
      className="info-name-edit"
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node | null))
          commit();
      }}
    >
      <StringGadget
        label="Name"
        value={draft}
        autoFocus
        onChange={setDraft}
        onKeyDown={(e) => {
          if (e.key === "Enter") commit();
          if (e.key === "Escape") {
            e.stopPropagation();
            setEditing(false);
          }
        }}
      />
    </span>
  );
}

export function InfoWindow({
  refId,
  origin,
}: {
  /** `kind:id` or bare id (objects) — or `zone:<id>` for a drawer. */
  refId: string;
  origin?: { x: number; y: number } | null;
}) {
  const items = useDesk((s) => s.items);
  const { closeInfoWindow, openZoneWindow, openPullout } = useDesk.getState();
  const zoneId = refId.startsWith("zone:") ? refId.slice(5) : null;
  const o: WorldObject | null = zoneId
    ? (() => {
        const d = (items.directory || []).find((z) => z.id === zoneId);
        return d
          ? {
              kind: "directory" as const,
              id: zoneId,
              title: String(d.name || "Zone"),
              ref: d,
            }
          : null;
      })()
    : objectByRef(items, refId);
  if (!o) return null;
  const info = kindInfo(o.kind);
  const r = o.ref as Record<string, unknown>;
  const created = String(r.createdAt || r.startedAt || "");
  const modified = String(r.lastModified || r.endedAt || "");
  const footprint = info.footprint(o, items);
  const zones = o.kind === "directory" ? [] : filedZones(o, items);
  const lin = lineage(items, (r as any).sources);

  return (
    <DeskWindowFrame
      id={`info:${o.kind}:${o.id}`}
      glyph="ⓘ"
      label={`${o.title} Info`}
      className="desk-pullout is-card desk-info-window"
      fitContent
      origin={origin}
      icon={
        <img src={spriteUrl(o.kind, o.id)} alt="" width={26} height={26} />
      }
      title={`${o.title}`}
      open
      onClose={() => closeInfoWindow(refId)}
      actions={<span className="quiet info-kind">{kindLabel(o.kind)}</span>}
    >
      <div className="desk-pullout-body desk-surface-body desk-info-body">
        <section>
          <h3>Identity</h3>
          <div className="info-kv">
            <b>Name</b>
            <IdentityName o={o} />
            <b>Kind</b>
            <span>{kindLabel(o.kind)}</span>
            <b>Id</b>
            <span className="quiet info-id">{o.id}</span>
            {created ? (
              <>
                <b>Created</b>
                <span>{humanTime(created)}</span>
              </>
            ) : null}
            {modified ? (
              <>
                <b>Modified</b>
                <span>{humanTime(modified)}</span>
              </>
            ) : null}
          </div>
        </section>
        {footprint ? (
          <section>
            <h3>Footprint</h3>
            <p>{footprint}</p>
          </section>
        ) : null}
        {zones.length > 0 ? (
          <section>
            <h3>Filed</h3>
            <div className="desk-pullout-lineage">
              {zones.map((z) => (
                <button
                  key={String(z.id)}
                  type="button"
                  className="desk-chip quiet"
                  onClick={() => openZoneWindow(String(z.id))}
                >
                  ▦ {String(z.name || z.id)}
                </button>
              ))}
            </div>
          </section>
        ) : null}
        {lin.any ? (
          <section>
            <h3>Lineage</h3>
            <div className="desk-pullout-lineage">
              {lin.via ? (
                <span className="desk-chip quiet">via {lin.via.label}</span>
              ) : null}
              {lin.from.map((f) => (
                <button
                  key={f.ref}
                  type="button"
                  className="desk-chip quiet"
                  onClick={() => f.resolved && openPullout(f.ref)}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </section>
        ) : null}
        {info.properties.length > 0 ? (
          <section>
            <h3>Properties</h3>
            <div className="info-props">
              {info.properties.map((p) => (
                <label key={p.key} className="info-prop">
                  <code>{p.key}</code>
                  <select
                    value={p.value(o)}
                    onChange={(e) => void p.set(o, e.target.value)}
                  >
                    {p.choices(o, items).map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.label}
                      </option>
                    ))}
                  </select>
                </label>
              ))}
            </div>
          </section>
        ) : null}
      </div>
    </DeskWindowFrame>
  );
}
