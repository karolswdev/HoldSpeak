import { SurfaceFooter } from "../surface/SurfaceFooter";
/** Knowledge pullout content (HS-117-15). */
import { Button } from "../../components/signal/Signal";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { qualifiedRef } from "../api";
import { objectByRef } from "../world";
import { DeskFilingStrip } from "../components/DeskFilingStrip";
import { KIND_LABEL } from "../tools";
import { kindWord } from "../windowName";
import {
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceSection,
  SurfaceState,
} from "../surface/Surface";
import { StateChip } from "../surface";
import { INLINE_EDITOR_CONTENT } from "./editors";
import type { PulloutContentProps } from "./types";
import { useCopyReceipt } from "../hooks/useCopyReceipt";
import { useEditorSession } from "./editors/useDebouncedSave";

export function KbPullout({ object: o, registerClose }: PulloutContentProps) {
  const items = useDesk((s) => s.items);
  const editing = useDesk((s) => s.editingId === o.id);
  const { openPullout, openEditor, closeEditor } = useDesk.getState();
  const session = useEditorSession(closeEditor, editing ? registerClose : undefined);
  if (o.ref.kind !== "kb") return null;
  const ir = o.ref;
  const Content = INLINE_EDITOR_CONTENT[o.kind];
  const resourceRef = qualifiedRef(o.kind, o.id);
  const { copy, receipt: copyReceipt } = useCopyReceipt();

  const members = (ir.memberIds || [])
    .map((m) => ({ ref: m, member: objectByRef(items, m) }));

  return (
    <>
      <div className="desk-pullout-body desk-surface-body desk-editor-body">
        {editing && Content ? (
          <Content object={o} onClose={() => void session.done()} onWriter={session.onWriter} />
        ) : members.length ? (
          <SurfaceSection label="Entries">
            <SurfaceLedger count={null} cols="room" label="Knowledge entries">
              {members.map(({ ref, member }) => (
                <SurfaceLedgerRow
                  key={ref}
                  wrap
                  lineLabel={ref}
                  primary={<span data-member-ref={ref} title={ref}>{member?.title || "Item unavailable"}</span>}
                  meta={member ? KIND_LABEL[member.kind] || kindWord(member.kind) : undefined}
                  cells={member ? undefined : <StateChip state="unreachable" label="Unavailable" />}
                  trailing={member ? <Button dense variant="ghost" onClick={() => openPullout(ref)}>Open</Button> : undefined}
                />
              ))}
            </SurfaceLedger>
          </SurfaceSection>
        ) : (
          <SurfaceSection label="Entries">
            <SurfaceState empty emptyLabel="No entries" />
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
