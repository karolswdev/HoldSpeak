/** Knowledge pullout content (HS-117-15). */
// @ts-ignore — shared ESM module (see ../sprites.d.ts)
import { spriteUrl } from "../sprites";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { qualifiedRef } from "../api";
import { objectByRef } from "../world";
import { DeskFilingStrip } from "../components/DeskFilingStrip";
import { productLabel } from "../../lib/productLanguage";
import { Material } from "../surface/Material";
import {
  SurfaceRow,
  SurfaceRows,
  SurfaceState,
} from "../surface/Surface";
import type { PulloutContentProps } from "./types";

export function KbPullout({ object: o }: PulloutContentProps) {
  const items = useDesk((s) => s.items);
  const { openPullout, openEditor } = useDesk.getState();
  if (o.ref.kind !== "kb") return null;
  const ir = o.ref;
  const resourceRef = qualifiedRef(o.kind, o.id);

  const body = String("bodyMarkdown" in ir ? ir.bodyMarkdown || "" : "");
  const members = (ir.memberIds || [])
    .map((m) => ({ ref: m, member: objectByRef(items, m) }))
    .filter(({ member }) => member);

  return (
    <>
      <div className="desk-pullout-body desk-surface-body">
        {body ? (
          <section>
            <Material>{body}</Material>
          </section>
        ) : members.length ? (
          <section>
            <SurfaceRows>
              {members.map(({ ref, member }) => (
                <SurfaceRow
                  key={ref}
                  glyph={
                    <img
                      src={spriteUrl(member!.kind, member!.id)}
                      width={22}
                      height={22}
                      alt=""
                    />
                  }
                  title={member!.title}
                  detail={productLabel(member!.kind)}
                  onOpen={() => openPullout(member!.id)}
                />
              ))}
            </SurfaceRows>
          </section>
        ) : (
          <section>
            <SurfaceState empty emptyLabel="Empty note" />
          </section>
        )}
        <DeskFilingStrip
          objectRef={resourceRef}
          objectKind={o.kind}
          objectId={o.id}
        />
      </div>
      <footer className="desk-pullout-foot">
        <button
          type="button"
          className="desk-chip quiet"
          onClick={() =>
            openSurfaceOr("dictate", "/dictation", resourceRef)
          }
        >
          Dictate about this
        </button>
        <button
          type="button"
          className="desk-chip is-primary"
          onClick={() => openEditor(o.id)}
        >
          Edit
        </button>
      </footer>
    </>
  );
}
