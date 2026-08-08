import { SurfaceFooter } from "../surface/SurfaceFooter";
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
import { INLINE_EDITOR_CONTENT } from "./editors";
import type { PulloutContentProps } from "./types";
import { useCopyReceipt } from "../hooks/useCopyReceipt";

export function KbPullout({ object: o }: PulloutContentProps) {
  const items = useDesk((s) => s.items);
  const editing = useDesk((s) => s.editingId === o.id);
  const { openPullout, openEditor, closeEditor } = useDesk.getState();
  if (o.ref.kind !== "kb") return null;
  const ir = o.ref;
  const Content = INLINE_EDITOR_CONTENT[o.kind];
  const resourceRef = qualifiedRef(o.kind, o.id);
  const { copy, receipt: copyReceipt } = useCopyReceipt();

  const body = String("bodyMarkdown" in ir ? ir.bodyMarkdown || "" : "");
  const members = (ir.memberIds || [])
    .map((m) => ({ ref: m, member: objectByRef(items, m) }))
    .filter(({ member }) => member);

  return (
    <>
      <div className="desk-pullout-body desk-surface-body desk-editor-body">
        {editing && Content ? (
          <Content object={o} onClose={closeEditor} />
        ) : body ? (
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
            <SurfaceState empty emptyLabel="No entries" />
          </section>
        )}
        {!editing && (
          <DeskFilingStrip
            objectRef={resourceRef}
            objectKind={o.kind}
            objectId={o.id}
          />
        )}
      </div>
      <SurfaceFooter receipt={editing ? null : copyReceipt} verbs={editing ? <>
        <button type="button" className="desk-chip quiet" onClick={closeEditor}>Cancel</button>
        <button type="button" className="desk-chip is-primary" onClick={closeEditor}>Save</button>
      </> : <>
        <button
          type="button"
          className="desk-chip quiet"
          onClick={() => void copy(body || members.map(({ member }) => member!.title).join("\n"))}
        >
          Copy
        </button>
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
      </>} />
    </>
  );
}
