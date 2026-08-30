import { SurfaceFooter } from "../surface/SurfaceFooter";
/** Recipe (Persona) pullout content (HS-117-15).
 * HS-150-07: "Chat with" retired; "Continue in thread" creates/opens a
 * thread bound to the recipe via POST /api/threads {recipe_id}. */
import { useState } from "react";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { qualifiedRef } from "../api";
import { createThread } from "../threads";
import { useWriteReceipt } from "../hooks/useWriteReceipt";
import { DeskFilingStrip } from "../components/DeskFilingStrip";
import { AgentAvatar } from "../components/AgentAvatar";
import { Material } from "../surface/Material";
import { FoldGadget } from "../surface/gadgets";
import { ContextualAssignment } from "../../pages/cores/ContextualAssignment";
import { INLINE_EDITOR_CONTENT } from "./editors";
import { CapabilitySection } from "./shared/CapabilitySection";
import type { PulloutContentProps } from "./types";

export function RecipePullout({ object: o }: PulloutContentProps) {
  const editing = useDesk((s) => s.editingId === o.id);
  const { openEditor, closeEditor, openPullout, refresh } = useDesk.getState();
  const [threadBusy, setThreadBusy] = useState(false);
  const { attempt, receipt } = useWriteReceipt();
  if (o.ref.kind !== "recipe") return null;
  const ir = o.ref;
  const Content = INLINE_EDITOR_CONTENT[o.kind];
  const resourceRef = qualifiedRef(o.kind, o.id);

  const continueInThread = async () => {
    if (threadBusy) return;
    setThreadBusy(true);
    await attempt("open thread", async () => {
      const t = await createThread({ recipe_id: o.id });
      openPullout(`thread:${t.id}`);
      void refresh();
    });
    setThreadBusy(false);
  };

  return (
    <>
      <div className="desk-pullout-body desk-surface-body desk-editor-body">
        {editing && Content ? (
          <Content object={o} onClose={closeEditor} />
        ) : <>
          <section className="desk-pullout-agent">
            <div className="desk-chat-hello">
              <span className="desk-chat-hello-avatar" aria-hidden="true">
                <AgentAvatar avatar={String(ir.avatar || "")} id={o.id} size={32} />
              </span>
              <strong className="surface-primary">{o.title}</strong>
              {ir.role ? <small>{String(ir.role)}</small> : null}
            </div>
            <button
              type="button"
              className="desk-chip is-primary desk-pullout-agent-chat"
              disabled={threadBusy}
              onClick={() => void continueInThread()}
            >
              {threadBusy ? "Opening..." : "Continue in thread"}
            </button>
            <ContextualAssignment
              label="Thread assignment"
              capabilityId="chat.turn"
              scope={{
                kind: "subject",
                subject_kind: "recipe",
                subject_id: o.id,
                capability_id: "chat.turn",
              }}
            />
            {ir.systemPrompt ? (
              <FoldGadget title="Instructions">
                <Material>{String(ir.systemPrompt)}</Material>
              </FoldGadget>
            ) : null}
          </section>
          <CapabilitySection object={o} />
          <DeskFilingStrip
            objectRef={resourceRef}
            objectKind={o.kind}
            objectId={o.id}
          />
        </>}
      </div>
      <SurfaceFooter receipt={receipt} verbs={editing ? <>
        <button type="button" className="desk-chip quiet" onClick={closeEditor}>Cancel</button>
        <button type="button" className="desk-chip is-primary" onClick={closeEditor}>Save</button>
      </> : <> <button
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
        </button> </>} />
    </>
  );
}
