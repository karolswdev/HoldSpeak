// The Room's Ask row: the Ask window's composer, scoped to this project.
import { useEffect, useRef, useState } from "react";
import { MicButton } from "../../../desk/surface";
import { CycleGadget, StringGadget } from "../../../desk/surface/gadgets";
import { AskComposer, AskEngineWord, AskSendButton, kindGlyph } from "../../../desk/components/askFace";
import { onReturnToTask, rememberTaskFocus } from "../../../desk/returnToTask";
import type { InferenceTarget } from "../../../desk/api";
import { openSurfaceOr } from "../../../desk/shell";
import { useDesk } from "../../../desk/store";
import { apiFetch } from "../../../lib/api";
import { getAssignmentEditor } from "../../../pages/cores/assignmentExperience";
import { RESULT_OPTIONS } from "../prepare/PreparePosture";

import { runAsk, type AskRunResult } from "../../../desk/ask";

/* ── Ask well ── */

/** The engine that answers this project's questions: its name, or `none`
 *  when unassigned, `unread` before the first read. Owner ruling
 *  2026-10-25: the engine is named by name only; no host and no place word
 *  on the Room. Settings ▸ Engines and the Ask window name where it runs. */
function useModelLabel(projectId: string): { state: "unread" | "set" | "none"; name: string } {
  const [label, setLabel] = useState<{ state: "unread" | "set" | "none"; name: string }>({ state: "unread", name: "" });
  const deskTargets = useDesk((s) => s.inferenceTargets);
  // HS-200-41 — the defect on this very seam. The hook used to re-read only
  // on `[projectId, targets]`, and `inferenceTargets` moves only when the
  // whole desk calls `refresh()`. So the owner pressed `Choose`, assigned a
  // model, came back — and the chip still read `MODEL · NOT SET`. That is
  // the STATE half of return-to-task failing on the surface this story
  // sends him back to, so it is fixed here, on the same subscription.
  const [freshTargets, setFreshTargets] = useState<InferenceTarget[] | null>(null);
  const [reread, setReread] = useState(0);
  const targets = freshTargets ?? deskTargets;
  useEffect(
    () =>
      onReturnToTask(() => {
        void apiFetch<{ targets?: InferenceTarget[] }>("/api/inference-targets")
          .then((r) => setFreshTargets(r.targets ?? []))
          .catch(() => { /* the assignment re-read below still runs */ });
        setReread((n) => n + 1);
      }),
    [],
  );
  useEffect(() => {
    if (!projectId) return;
    let cancelled = false;
    getAssignmentEditor(
      { kind: "subject", subject_kind: "project", subject_id: projectId, capability_id: "ask.answer" },
      "ask.answer",
    ).then((editor) => {
      if (cancelled) return;
      const eff = editor.effective;
      if (eff.status === "assigned" && eff.assignment?.entries?.length) {
        const entry = eff.assignment.entries[0];
        const target = targets.find((t) => t.profile_id === entry.profile_id);
        setLabel({ state: "set", name: entry.label || target?.name || "Assigned engine" });
      } else {
        setLabel({ state: "none", name: "" });
      }
    }).catch(() => { /* non-fatal */ });
    return () => { cancelled = true; };
  }, [projectId, targets, reread]);
  return label;
}

/** The Room runs the canonical Ask request inline. Other callers keep
 * the Ask window bridge with the same project context. */
export function useRoomAsk(projectId: string, projectName: string, inline = false) {
  const [prompt, setPrompt] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const [result, setResult] = useState<AskRunResult | null>(null);
  const [busy, setBusy] = useState(false);
  const pending = useRef(false);
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  const ask = async () => {
    const question = prompt.trim();
    if (!question || !projectId || pending.current) return;
    if (inline) {
      pending.current = true; setBusy(true);
      const request = new AbortController(); controller.current = request;
      try {
        const answer = await runAsk({ prompt: question, lens: "Project", context: [{ id: projectId, kind: "project", ref: `project:${projectId}`, title: projectName }], grounding: { meeting_ids: [], artifact_ids: [], refs: [`project:${projectId}`], expand: "summary" }, signal: request.signal });
        if (!request.signal.aborted) setResult(answer);
      } finally { pending.current = false; if (!request.signal.aborted) setBusy(false); }
      return;
    }
    useDesk.getState().askAbout(
      [{ id: projectId, kind: "project", ref: `project:${projectId}`, title: projectName || "Project" }],
      { question, run: true },
    );
    setPrompt("");
  };
  return { prompt, setPrompt, inputRef, ask, projectName, result, busy, clearResult: () => setResult(null) };
}

export type RoomAsk = ReturnType<typeof useRoomAsk>;

/** The Room's ask (Window Program W2, 2026-10-27): the Ask window's own
 *  composer row (askFace AskComposer), its scope preset to this project:
 *  [project ▸ name] [field] [mic] [Result] [● engine] [Ask ⏎]. The question
 *  runs in the Ask window, so it lands in Ask's Recent too. The Room's
 *  well, engine chip and hidden Submit are parked
 *  (`_parked/roomAskWell.v1-2026-10-27.tsx`). The Room window on the desk
 *  (the Project's drawer) draws the same row. */
export function RoomAskWell({
  ask,
  projectId,
  onPrepare,
}: {
  ask: RoomAsk;
  projectId: string;
  onOpenRef?: (ref: string) => void;
  /** HS-200-11: `Result → Preparation brief` hands the words to the Prepare
   *  posture; nothing here requires a calendar (AC1). */
  onPrepare?: (purpose: string) => void;
}) {
  const { prompt, setPrompt, inputRef } = ask;
  const engine = useModelLabel(projectId);
  const name = ask.projectName || "This project";
  const chooseEngine = () => {
    // The verb he leaves is the engine word; the place to come back to is
    // the field he was typing in, with his words still in it (design D2(a)).
    rememberTaskFocus(inputRef.current);
    openSurfaceOr("configure-runs-on", "/settings", "models");
  };

  return (
    <div className="room-ask-section" data-testid="room-ask-well">
      <AskComposer
        className="room-ask-composer"
        data-testid="room-ask-input-well"
        scope={
          <span className="desk-ask-scope-word desk-ask-scope-preset" title={`About: ${name}`}>
            <img src={kindGlyph("project", `project:${projectId}`)} alt="" width={16} height={16} draggable={false} />
            <span className="desk-ask-scope-text">{name}</span>
          </span>
        }
        field={
          <StringGadget
            label="Ask this project"
            mic={false}
            value={prompt}
            onChange={setPrompt}
            placeholder="Ask this project…"
            inputRef={inputRef}
            inputProps={{ className: "room-ask-input" }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
                e.preventDefault();
                void ask.ask();
              }
            }}
          />
        }
        capture={
          <>
            <MicButton
              label="Speak to ask this project"
              draftScope={`project-ask-${projectId}`}
              onText={(text) => setPrompt((current) => (current ? `${current} ${text}` : text))}
            />
            {onPrepare ? (
              <span className="room-ask-result" data-testid="room-ask-result">
                <CycleGadget
                  label="Result"
                  value="answer"
                  options={RESULT_OPTIONS}
                  onChange={(next) => { if (next === "brief") onPrepare(prompt); }}
                />
              </span>
            ) : null}
          </>
        }
        engine={(
          // Always drawn in a fixed slot (the desk sweep's still fence).
          <span className="room-ask-engine-slot" data-testid={engine.state === "set" ? "room-ask-engine" : engine.state === "none" ? "room-ask-no-engine" : undefined}>
            <AskEngineWord
              state={engine.state}
              name={engine.name}
              onPress={chooseEngine}
            />
          </span>
        )}
        action={<AskSendButton variant="secondary" disabled={!prompt.trim()} onClick={() => void ask.ask()} />}
      />
    </div>
  );
}
