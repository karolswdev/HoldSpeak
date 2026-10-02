import { SurfaceFooter } from "../surface/SurfaceFooter";
/** Coder pullout content (HS-117-15). */
import { useState } from "react";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { qualifiedRef } from "../api";
import { useDurableDraft } from "../../lib/durableDraft";
import { useSteering } from "../steering";
import { MicButton } from "../components/MicButton";
import { humanizeWireValue } from "../../lib/productLanguage";
import { Material } from "../surface/Material";
import { FoldGadget } from "../surface/gadgets";
import {
  SurfaceCode,
  SurfaceWell,
} from "../surface/Surface";
import {
  contextualCoderSessions,
} from "../contextual";
import type { PulloutContentProps } from "./types";
import { Button } from "../../components/signal/Signal";

export function CoderPullout({ object: o, onClose }: PulloutContentProps) {
  const items = useDesk((s) => s.items);
  const selectedIds = useDesk((s) => s.selectedIds);
  const { speakToCoder, answerCoder } = useDesk.getState();
  if (o.ref.kind !== "coder") return null;
  const ir = o.ref;
  const resourceRef = qualifiedRef(o.kind, o.id);

  const [answered, setAnswered] = useState<
    "selected" | "sent" | "failed" | null
  >(null);

  const coderSessionId = String(ir.sessionId || o.id);
  const {
    value: coderDraft,
    setDraft: setCoderDraft,
    recovered: coderDraftRecovered,
  } = useDurableDraft(`coder-reply:${coderSessionId}`);

  const contextualCoderAction = contextualCoderSessions(
    items,
    selectedIds,
  ).find((action) => action.id === o.id);

  const coderWaiting =
    String(ir.state || "") === "waiting" || Boolean(ir.question);

  return (
    <>
      <div className="desk-pullout-body desk-surface-body">
        <section>
          <p className="quiet">
            {humanizeWireValue(String(ir.model || ""))} · {humanizeWireValue(String(ir.state || ""))}
          </p>
          {ir.question ? (
            <Material className="desk-coder-question">
              {String(ir.question)}
            </Material>
          ) : null}
          <div className="desk-coder-answer">
            {coderWaiting ? (
              <>
                {contextualCoderAction ? (
                  <div className="desk-coder-context">
                    <strong>
                      Selected source · {contextualCoderAction.source.title}
                    </strong>
                    <FoldGadget title="RAW · SELECTED TEXT">
                      <SurfaceWell
                        head={`RAW · ${contextualCoderAction.source.title.toUpperCase()}`}
                      >
                        <SurfaceCode>
                          {contextualCoderAction.source.text}
                        </SurfaceCode>
                      </SurfaceWell>
                    </FoldGadget>
                    <Button dense variant="ghost"
                      onClick={() => {
                        setAnswered(null);
                        void speakToCoder(
                          String(ir.agent || "claude"),
                          String(ir.sessionId || o.id),
                          contextualCoderAction.source.text,
                        ).then((ok) => setAnswered(ok ? "sent" : "failed"));
                      }}
                    >
                      {answered === "sent"
                        ? `Sent ${contextualCoderAction.source.title}`
                        : answered === "failed"
                          ? `Retry sending ${contextualCoderAction.source.title}`
                          : contextualCoderAction.label}
                    </Button>
                  </div>
                ) : null}
                <div className="desk-chat-well">
                  <div className="desk-chat-composer">
                    <MicButton
                      label="Speak to answer"
                      draftScope={`coder-reply:${coderSessionId}`}
                      onText={(t) =>
                        setCoderDraft((current) =>
                          current ? `${current} ${t}` : t,
                        )
                      }
                    />
                    <textarea
                      className="desk-coder-draft-input"
                      aria-label="Coder reply draft"
                      value={coderDraft}
                      placeholder="Reply"
                      rows={2}
                      onChange={(event) => setCoderDraft(event.target.value)}
                    />
                    <Button dense variant="primary"
                      disabled={!coderDraft.trim()}
                      onClick={() => {
                        setAnswered(null);
                        const retained = coderDraft.trim();
                        void speakToCoder(
                          String(ir.agent || "claude"),
                          coderSessionId,
                          retained,
                        ).then((ok) => {
                          setAnswered(ok ? "sent" : "failed");
                          if (ok) setCoderDraft("");
                        });
                      }}
                    >
                      {answered === "failed" ? "Retry reply" : "Send reply"}
                    </Button>
                  </div>
                </div>
                <span className="quiet desk-coder-answer-state" role="status">
                  {answered === "sent"
                    ? "REPLY SENT"
                    : answered === "failed"
                      ? "REPLY FAILED · RETRY"
                      : coderDraftRecovered
                        ? "DRAFT RECOVERED"
                        : "REPLY"}
                </span>
                <Button dense variant="ghost"
                  onClick={() => {
                    void answerCoder(
                      String(ir.agent || "claude"),
                      String(ir.sessionId || o.id),
                    ).then((ok) => setAnswered(ok ? "selected" : "failed"));
                  }}
                >
                  {answered === "selected"
                    ? "Dictation target"
                    : "Use the hotkey"}
                </Button>
              </>
            ) : null}
          </div>
        </section>
      </div>
      <SurfaceFooter verbs={<> <Button dense variant="ghost"
          onClick={() => openSurfaceOr("dictate", "/dictation", resourceRef)}
        >
          Dictate about this
        </Button>
        <Button dense variant="ghost"
          onClick={() => {
            // PHILO-13-05: close by the store's own id (the card's onClose);
            // the bare `o.id` left a card opened as `coder:s1` open.
            onClose();
            useSteering
              .getState()
              .openSession(
                `${String(ir.agent || "claude")}:${String(ir.sessionId || o.id)}`,
              );
          }}
        >
          Watch live
        </Button> </>} />
    </>
  );
}
