// PARKED (Betterment Q5, 2026-10-18): the Room's own Ask — its answer face,
// its failure line and the UNFINISHED list. The Room's Ask field now opens the
// one Ask window with the project in About and runs the question there
// (docs/internal/betterment/asking/RECIPE.md Q5, change 3). This is the code
// as it stood in web/src/features/project-room/ProjectRoomCore.tsx, kept for
// the record; nothing imports it. Its tests are parked beside it.
/* eslint-disable */
// @ts-nocheck
/** The Room's ask, as ONE controller.
 *
 *  HS-200-41 F5: the unfinished list and the ask well are TWO faces over one
 *  state. They used to be one component, which put a ledger inside the
 *  composer's sticky foot — five rows and the Room was gone behind them. The
 *  state lives here so the list can sit in the body as its own section, where
 *  the design's posture-6 grammar puts it, while the well stays sticky. */
export function useRoomAsk(projectId: string, projectName: string) {
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState<AskRunResult | null>(null);
  const [busy, setBusy] = useState(false);
  // Betterment Q1: a failure is a reason TOKEN the face says in words
  // (`runWords.ts`), never the hub's sentence. `words` holds only the
  // browser's own line for a request that never reached the hub.
  const [error, setError] = useState<RoomAskFailure | null>(null);
  // The ask no longer dies with the tab. The words are written to
  // `project_ask_tasks` BEFORE the run goes out (ruling B3), so a restart, a
  // crash or a trip to Settings finds them again.
  const [unfinished, setUnfinished] = useState<AskTask[]>([]);
  const [working, setWorking] = useState<{ id: string; verb: "resume" | "discard" } | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const loadUnfinished = useCallback(async (): Promise<AskTask[]> => {
    if (!projectId) return [];
    const page = await listUnfinishedAsks({ projectId, limit: 5 });
    setUnfinished(page.items);
    return page.items;
  }, [projectId]);

  // PHILO-17 (phonepass): the first read resolved (the Room waits for it).
  const [unfinishedRead, setUnfinishedRead] = useState(false);
  useEffect(() => {
    void loadUnfinished().catch(() => undefined).finally(() => setUnfinishedRead(true));
  }, [loadUnfinished]);
  // The generalisation the design's D3 called MISSING: the Room's ask well
  // subscribes to return-to-task like every other face holding unfinished
  // work, so readiness and the saved row re-read WITHOUT a reload.
  useEffect(() => onReturnToTask(() => { void loadUnfinished(); }), [loadUnfinished]);

  const ask = async () => {
    const purpose = prompt.trim();
    if (!purpose || busy) return;
    setBusy(true);
    setError(null);
    const startedAt = Date.now();
    const grounding = {
      meeting_ids: [],
      artifact_ids: [],
      refs: [`project:${projectId}`],
      expand: "summary" as const,
    };
    // Save FIRST: the row and its invocation identity exist before anything
    // is dispatched, so an answer that lands after the tab is gone can be
    // claimed instead of paid for twice (ruling B3). A refusal here does not
    // block the work — durability is the bonus, never the gate.
    const task = await saveAskTask(projectId, {
      purpose,
      lens: "Project",
      grounding,
    });
    const answer = await runAsk({
      prompt: purpose,
      lens: "Project",
      context: [
        { id: projectId, kind: "project", ref: `project:${projectId}`, title: projectName },
      ],
      grounding,
      ...(task ? { invocationId: task.invocationId } : {}),
    });
    setBusy(false);
    if (!answer.ok) {
      // Record WHY it stopped, from the hub's own refusal CODE — never its
      // sentence (ruling B5). The server resolves the token against its live
      // placement and quotes the engine itself; nothing written here reaches
      // the row. The ask stays unfinished and fully resumable either way.
      // Betterment Q1: with no target code, the reason TOKEN is the code —
      // a bounded token, never a sentence (B5) — so the row can say why.
      let recorded = false;
      const code = answer.refusalCode || answer.reason || "";
      if (task && code) {
        recorded = (await stopAskTask(task.id, code)).ok;
      }
      // F6: the failure is said ONCE. When it landed on a row, the row says
      // it — in words, beside Ask again. The inline line survives only for a
      // failure that reached no row at all (no saved row, or a transport
      // failure the hub never coded), where it is the only thing that can
      // speak.
      if (!recorded) {
        setError({
          reason: answer.reason || "",
          seconds: Math.max(1, Math.round((Date.now() - startedAt) / 1000)),
          words: answer.reason ? "" : answer.output,
        });
      }
      void loadUnfinished();
      return;
    }
    setResult(answer);
    // Settle the record against the answer the run just wrote. The resume
    // route reads `ask_results` first, finds it, marks the task accepted and
    // dispatches NOTHING — there is no separate accept route, and minting a
    // second identity to settle one is the double-spend B3 forbids.
    if (task) await resumeAskTask(task.id);
    void loadUnfinished();
  };

  const resume = async (task: AskTask) => {
    setWorking({ id: task.id, verb: "resume" });
    setError(null);
    const outcome = await resumeAskTask(task.id);
    setWorking(null);
    if (!outcome.ok) {
      // Never the hub's sentence (RECON step 9 printed a raw database
      // error here). Said once: when the row now carries the reason, the
      // row says it.
      const rows = await loadUnfinished();
      const row = rows.find((candidate) => candidate.id === task.id);
      if (!(outcome.reason && row?.state === "failed" && row.stoppedCode === outcome.reason)) {
        setError({ reason: outcome.reason, words: "", task });
      }
      return;
    }
    setPrompt(task.purpose);
    if (outcome.answer) setResult(outcome.answer);
    await loadUnfinished();
    inputRef.current?.focus();
  };

  const discard = async (task: AskTask) => {
    setWorking({ id: task.id, verb: "discard" });
    await discardAskTask(task.id);
    setWorking(null);
    await loadUnfinished();
  };

  return {
    prompt, setPrompt, result, busy, error, unfinished, unfinishedRead, working,
    inputRef, ask, resume, discard,
  };
}

export type RoomAsk = ReturnType<typeof useRoomAsk>;

/** A Room ask that did not answer, as the face holds it (Betterment Q1). */
export interface RoomAskFailure {
  /** The hub's reason token; empty when the hub never answered. */
  reason: string;
  seconds?: number;
  /** The browser's own line for a request that never reached the hub. */
  words: string;
  /** The saved ask Ask again resumes; absent, Ask again asks anew. */
  task?: AskTask;
}

/** Why a saved ask stopped, in words. The reason token when the row holds
 *  one; the destination's own readiness words for a target code (B5); never
 *  a raw code or the hub's sentence. */
export function roomStopWords(task: Pick<AskTask, "stoppedCode" | "stoppedReason">): string {
  const code = task.stoppedCode || "";
  if (isRunFailureReason(code)) return reasonWords(code);
  if (code === "ask_task_host_lost") return "Stopped when the hub restarted";
  if (code.startsWith("inference_target_") && task.stoppedReason) return task.stoppedReason;
  return code || task.stoppedReason ? reasonWords("") : "";
}

/** UNFINISHED — the saved work, in the Room BODY as its own section.
 *
 *  F5: this used to render inside `.room-ask-container`, which is
 *  `position: sticky; bottom: 0`. A ledger does not belong in a composer's
 *  foot: at five rows it covered every other section and the Room was a wall
 *  of unfinished asks over dead space. */
function RoomUnfinishedSection({ ask }: { ask: RoomAsk }) {
  const { unfinished, working } = ask;
  if (unfinished.length === 0) return null;
  // PHILO-17 refit: the window's one filled verb is Draft update; a saved
  // ask resumes with a quiet verb.
  return (
    <SurfaceSection label={countLabel("UNFINISHED", unfinished.length)}>
      <TaskResumeList data-testid="room-unfinished">
        {unfinished.map((task) => (
          <TaskResume
            key={task.id}
            data-testid={`room-unfinished-${task.id}`}
            purpose={task.purpose}
            state={task.state}
            savedAt={task.savedAt}
            settledAt={task.settledAt}
            recipe={task.recipeKey}
            stoppedReason={roomStopWords(task) || undefined}
            custody={task.custody}
            {...(task.state === "failed" ? { verbLabel: "Ask again" } : {})}
            primary={false}
            busy={working?.id === task.id && working.verb === "resume"}
            onVerb={() => void ask.resume(task)}
            onDiscard={() => void ask.discard(task)}
            discardBusy={working?.id === task.id && working.verb === "discard"}
          />
        ))}
      </TaskResumeList>
    </SurfaceSection>
  );
}

