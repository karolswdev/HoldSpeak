import { SurfaceFooter } from "../surface/SurfaceFooter";
/** Recipe (Persona) pullout content (HS-117-15).
 * HS-151-07: "Chat with" retired; "Continue in thread" creates/opens a
 * thread bound to the recipe via POST /api/threads {recipe_id}. */
import { useState } from "react";
import { Button } from "../../components/signal/Signal";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { qualifiedRef } from "../api";
import { openNewThread } from "../newThread";
import { useWriteReceipt } from "../hooks/useWriteReceipt";
import { DeskFilingStrip } from "../components/DeskFilingStrip";
import { AgentAvatar } from "../components/AgentAvatar";
import { Material } from "../surface/Material";
import { FoldGadget } from "../surface/gadgets";
import { StatusBar, ToolGlyph, Toolbar } from "../surface/kit";
import { ContextualAssignment } from "../../pages/cores/ContextualAssignment";
import { INLINE_EDITOR_CONTENT } from "./editors";
import { CapabilitySection } from "./shared/CapabilitySection";
import type { PulloutContentProps } from "./types";
import { useEditorSession } from "./editors/useDebouncedSave";
import "./capability-window.css";

export function RecipePullout({ object: o, registerClose }: PulloutContentProps) {
  const editing = useDesk((s) => s.editingId === o.id);
  const { openEditor, closeEditor } = useDesk.getState();
  const session = useEditorSession(closeEditor, editing ? registerClose : undefined);
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
      await openNewThread({ recipe_id: o.id });
    });
    setThreadBusy(false);
  };

  // W2-BUILDER (atlas 2026-10-27): the Mode on the window grammar. Toolbar
  // (Continue in thread · Edit · Dictate about this), the Mode's line (its
  // face, name and role, left-aligned), which engine answers and which runs
  // it in plain words, the instructions, the material, the filing fold.
  if (editing && Content) {
    return (
      <>
        <div className="desk-pullout-body desk-surface-body desk-editor-body">
          <Content object={o} onClose={() => void session.done()} onWriter={session.onWriter} />
        </div>
        <SurfaceFooter receipt={session.receipt} verbs={session.verbs} />
      </>
    );
  }
  return (
    <>
      <div className="desk-pullout-body desk-surface-body capw-window" data-interior="editor" data-testid="mode-window">
        <Toolbar label="Mode" data-testid="mode-toolbar">
          <Button
            dense
            variant="primary"
            className="desk-pullout-agent-chat"
            disabled={threadBusy}
            onClick={() => void continueInThread()}
          >
            <ToolGlyph kind="ask" />{threadBusy ? "Opening..." : "Continue in thread"}
          </Button>
          <Button dense variant="secondary" onClick={() => openEditor(o.id)}>
            <ToolGlyph kind="edit" />Edit
          </Button>
          <Button dense variant="ghost" onClick={() => openSurfaceOr("dictate", "/dictation", resourceRef)}>
            Dictate about this
          </Button>
        </Toolbar>
        <div className="capw-page">
          <div className="capw-identity" role="group" aria-label={o.title}>
            <span className="capw-identity-face" aria-hidden="true">
              <AgentAvatar avatar={String(ir.avatar || "")} id={o.id} size={32} />
            </span>
            <span className="capw-identity-text">
              <strong>{o.title}</strong>
              {ir.role ? <small>{String(ir.role)}</small> : null}
            </span>
          </div>
          <ContextualAssignment
            label="Which engine answers in a thread"
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
          <CapabilitySection object={o} />
          <DeskFilingStrip
            objectRef={resourceRef}
            objectKind={o.kind}
            objectId={o.id}
          />
        </div>
      </div>
      <StatusBar data-testid="mode-status" items={[receipt ? { key: "receipt", text: receipt } : null]} />
    </>
  );
}
