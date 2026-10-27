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
  SurfaceState,
} from "../surface/Surface";
import { StatusBar, ToolGlyph, Toolbar, countWords } from "../surface/kit";
import { useState } from "react";
import { INLINE_EDITOR_CONTENT } from "./editors";
import type { PulloutContentProps } from "./types";
import { useCopyReceipt } from "../hooks/useCopyReceipt";
import { useEditorSession } from "./editors/useDebouncedSave";
import "./capability-window.css";

export function KbPullout({ object: o, registerClose }: PulloutContentProps) {
  const items = useDesk((s) => s.items);
  const editing = useDesk((s) => s.editingId === o.id);
  const { openEditor, closeEditor } = useDesk.getState();
  const session = useEditorSession(closeEditor, editing ? registerClose : undefined);
  const [addOnOpen, setAddOnOpen] = useState(false);
  const { copy, receipt: copyReceipt } = useCopyReceipt();
  if (o.ref.kind !== "kb") return null;
  const ir = o.ref;
  const Content = INLINE_EDITOR_CONTENT[o.kind];
  const resourceRef = qualifiedRef(o.kind, o.id);

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

  // W2-BUILDER (atlas 2026-10-27): the reader on the window grammar.
  // Toolbar (Add · Edit · Copy · Dictate about this); Add opens the editor
  // on its item picker (the hub's member route, PUT /api/kbs/{id}/members);
  // the contents edge to edge; the count and receipts in the status bar.
  if (editing && Content) {
    return (
      <>
        {/* W3-B: the editor draws the toolbar (Done, Add items); the save
            receipt is the status bar's. */}
        <div className="desk-pullout-body desk-surface-body desk-editor-body kb-window" data-interior="editor" data-testid="knowledge-editor">
          <Content object={o} openAdd={addOnOpen} onClose={() => void session.done()} onWriter={session.onWriter} toolbar={session.verbs} />
        </div>
        <StatusBar data-testid="knowledge-editor-status" items={[session.receipt ? { key: "save", text: session.receipt } : null]} />
      </>
    );
  }
  return (
    <>
      <div className="desk-pullout-body desk-surface-body kb-window" data-interior="editor" data-testid="knowledge-window">
        <Toolbar label="Knowledge" data-testid="knowledge-toolbar">
          <Button
            dense
            variant="primary"
            data-testid="knowledge-add"
            onClick={() => { setAddOnOpen(true); openEditor(o.id); }}
          >
            <ToolGlyph kind="new" />Add
          </Button>
          <Button dense variant="secondary" onClick={() => { setAddOnOpen(false); openEditor(o.id); }}>
            <ToolGlyph kind="edit" />Edit
          </Button>
          {members.length ? (
            <Button
              dense
              variant="ghost"
              onClick={() => void copy(members.map(({ ref, member }) => member?.title || ref).join("\n"))}
            >
              <ToolGlyph kind="copy" />Copy
            </Button>
          ) : null}
          <Button dense variant="ghost" onClick={() => openSurfaceOr("dictate", "/dictation", resourceRef)}>
            Dictate about this
          </Button>
        </Toolbar>
        <div className="kb-page">
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
          <DeskFilingStrip
            objectRef={resourceRef}
            objectKind={o.kind}
            objectId={o.id}
          />
        </div>
      </div>
      <StatusBar
        data-testid="knowledge-status"
        items={[
          { key: "count", text: countWords(members.length, "item") },
          copyReceipt ? { key: "receipt", text: copyReceipt } : null,
        ]}
      />
    </>
  );
}
