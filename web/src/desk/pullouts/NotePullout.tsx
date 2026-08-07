import { SurfaceFooter } from "../surface/SurfaceFooter";
/** Note pullout content (HS-117-15). */
import { useState } from "react";
import type { EditorView } from "@codemirror/view";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { qualifiedRef } from "../api";
import { DeskFilingStrip } from "../components/DeskFilingStrip";
import { MicButton } from "../components/MicButton";
import { DeskEditor } from "../components/DeskEditor";
import { EditorAIBar } from "../components/EditorAIBar";
import { Material } from "../surface/Material";
import { SurfaceState } from "../surface/Surface";
import { useCopyReceipt } from "../hooks/useCopyReceipt";
import type { PulloutContentProps } from "./types";

export function NotePullout({ object: o }: PulloutContentProps) {
  const { updatePrimitive } = useDesk.getState();
  if (o.ref.kind !== "note") return null;
  const ir = o.ref;
  const resourceRef = qualifiedRef(o.kind, o.id);

  const [editingBody, setEditingBody] = useState(false);
  const [bodyDraft, setBodyDraft] = useState("");
  const [editorView, setEditorView] = useState<EditorView | null>(null);
  const [aiBarForced, setAIBarForced] = useState(false);
  const { copy, receipt: copyReceipt } = useCopyReceipt();

  const startBodyEdit = () => {
    setBodyDraft(String(ir.bodyMarkdown || ""));
    setEditingBody(true);
  };
  const commitBodyEdit = () => {
    void updatePrimitive("note", o.id, { body_markdown: bodyDraft });
    setEditingBody(false);
  };

  const body = String(ir.bodyMarkdown || "");

  return (
    <>
      <div className="desk-pullout-body desk-surface-body">
        {editingBody ? (
          <section>
            <DeskEditor
              className="desk-pullout-markdown-editor"
              ariaLabel={`${o.title} content`}
              value={bodyDraft}
              autoFocus
              minHeight={`${Math.max(6, bodyDraft.split("\n").length + 1) * 1.55}em`}
              placeholder="Write"
              onChange={setBodyDraft}
              onEscape={() => setEditingBody(false)}
              onModEnter={commitBodyEdit}
              onViewChange={setEditorView}
              onAIBarToggle={() => setAIBarForced((shown) => !shown)}
            />
            <EditorAIBar
              editorView={editorView}
              forceVisible={aiBarForced}
              onDismiss={() => setAIBarForced(false)}
            />
          </section>
        ) : body ? (
          <section>
            <Material>{body}</Material>
          </section>
        ) : (
          <section>
            <SurfaceState
              empty
              emptyLabel="Empty note"
              actionLabel="Start writing"
              onAction={startBodyEdit}
            />
          </section>
        )}
        <DeskFilingStrip
          objectRef={resourceRef}
          objectKind={o.kind}
          objectId={o.id}
        />
      </div>
      <SurfaceFooter receipt={copyReceipt} verbs={<>
        <button
          type="button"
          className="desk-chip quiet"
          onClick={() => void copy(editingBody ? bodyDraft : body)}
        >
          Copy
        </button>
        {!editingBody && (
          <button
            type="button"
            className="desk-chip quiet"
            onClick={() =>
              openSurfaceOr("dictate", "/dictation", resourceRef)
            }
          >
            Dictate about this
          </button>
        )}
        {editingBody ? (
          <>
            <MicButton
              label="Speak to fill"
              draftScope={`card-edit:${o.id}`}
              onText={(t) =>
                setBodyDraft((current) => (current ? `${current} ${t}` : t))
              }
            />
            <button
              type="button"
              className="desk-chip quiet"
              onClick={() => setEditingBody(false)}
            >
              Cancel
            </button>
            <button
              type="button"
              className="desk-chip is-primary"
              onClick={commitBodyEdit}
            >
              Done
            </button>
          </>
        ) : (
          <button
            type="button"
            className="desk-chip is-primary"
            onClick={startBodyEdit}
          >
            Edit
          </button>
        )} </>} />
    </>
  );
}
