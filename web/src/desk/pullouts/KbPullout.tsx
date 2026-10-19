import { SurfaceFooter } from "../surface/SurfaceFooter";
/** Knowledge pullout content (HS-117-15). */
import { Button } from "../../components/signal/Signal";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { qualifiedRef } from "../api";
import { objectByRef } from "../world";
import { DeskFilingStrip } from "../components/DeskFilingStrip";
// @ts-ignore — shared ESM module (see ../sprites.d.ts)
import { refAgent, spriteUrl } from "../sprites";
import { normalizeRef } from "../screen/compose";
import { openScreenRef } from "../screen/open";
import { productLabel } from "../../lib/productLanguage";
import {
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceState,
} from "../surface/Surface";
import { INLINE_EDITOR_CONTENT } from "./editors";
import type { PulloutContentProps } from "./types";
import { useCopyReceipt } from "../hooks/useCopyReceipt";
import { useEditorSession } from "./editors/useDebouncedSave";

export function KbPullout({ object: o, registerClose }: PulloutContentProps) {
  const items = useDesk((s) => s.items);
  const editing = useDesk((s) => s.editingId === o.id);
  const { openEditor, closeEditor } = useDesk.getState();
  const session = useEditorSession(closeEditor, editing ? registerClose : undefined);
  if (o.ref.kind !== "kb") return null;
  const ir = o.ref;
  const Content = INLINE_EDITOR_CONTENT[o.kind];
  const resourceRef = qualifiedRef(o.kind, o.id);
  const { copy, receipt: copyReceipt } = useCopyReceipt();

  // Betterment Q10 (Knowledge becomes drawers): a collection reads as a
  // drawer, its Contents drawn as a drawer's are (DirectoryPullout).
  const seen = new Set<string>();
  const members = (ir.memberIds || []).flatMap((stored) => {
    const member = objectByRef(items, normalizeRef(stored));
    const ref = member ? qualifiedRef(member.kind, member.id) : stored;
    if (seen.has(ref)) return [];
    seen.add(ref);
    return [{ ref, member }];
  });

  return (
    <>
      <div className="desk-pullout-body desk-surface-body desk-editor-body">
        {editing && Content ? (
          <Content object={o} onClose={() => void session.done()} onWriter={session.onWriter} />
        ) : (
          <SurfaceSection label="Contents" count={members.length}>
            {members.length ? (
              <SurfaceRows>
                {members.map(({ ref, member }) => (
                  <SurfaceRow
                    key={ref}
                    glyph={member ? (
                      <img src={spriteUrl(member.kind, member.id, "rest", refAgent(member.ref))} width={22} height={22} alt="" />
                    ) : undefined}
                    title={<span data-member-ref={ref}>{member?.title || "Item unavailable"}</span>}
                    detail={member ? member.kind === "directory" || member.kind === "kb" ? "Drawer" : productLabel(member.kind) : "Unavailable"}
                    onOpen={member ? () => openScreenRef(ref) : undefined}
                  />
                ))}
              </SurfaceRows>
            ) : (
              <SurfaceState empty emptyLabel="No items" emptyGlyph="○" />
            )}
          </SurfaceSection>
        )}
        {!editing && (
          <DeskFilingStrip
            objectRef={resourceRef}
            objectKind={o.kind}
            objectId={o.id}
          />
        )}
      </div>
      <SurfaceFooter receipt={editing ? session.receipt : copyReceipt} verbs={editing ? session.verbs : <>
        <Button
          dense
          variant="ghost"
          onClick={() => void copy(members.map(({ ref, member }) => member?.title || ref).join("\n"))}
        >
          Copy
        </Button>
        <Button
          dense
          variant="ghost"
          onClick={() =>
            openSurfaceOr("dictate", "/dictation", resourceRef)
          }
        >
          Dictate about this
        </Button>
        <Button
          dense
          variant="primary"
          onClick={() => openEditor(o.id)}
        >
          Edit
        </Button>
      </>} />
    </>
  );
}
