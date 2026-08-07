import { SurfaceFooter } from "../surface/SurfaceFooter";
/** Recipe (Persona) pullout content (HS-117-15). */
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { qualifiedRef } from "../api";
import { DeskFilingStrip } from "../components/DeskFilingStrip";
import { AgentAvatar } from "../components/AgentAvatar";
import { Material } from "../surface/Material";
import { FoldGadget } from "../surface/gadgets";
import { CapabilitySection } from "./shared/CapabilitySection";
import type { PulloutContentProps } from "./types";

export function RecipePullout({ object: o }: PulloutContentProps) {
  const { openChat, openEditor } = useDesk.getState();
  if (o.ref.kind !== "recipe") return null;
  const ir = o.ref;
  const resourceRef = qualifiedRef(o.kind, o.id);

  return (
    <>
      <div className="desk-pullout-body desk-surface-body">
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
            onClick={() => openChat(o.id)}
          >
            Chat with {o.title}
          </button>
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
      </div>
      <SurfaceFooter verbs={<> <button
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
