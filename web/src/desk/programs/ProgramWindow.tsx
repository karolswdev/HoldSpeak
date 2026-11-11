import { useEffect, useRef, useState } from "react";
import { apiFetch } from "../../lib/api";
import { programFailure as readableError } from "./liveModel";
import { Button } from "../../components/signal/Signal";
import { useAgentFlights } from "../agentFlights";
import { openAgentLane } from "../shell";
import {
  PROGRAM_STEP_EVENT,
  openRef,
  takeProgramStepRequest,
} from "../openObject";
import {
  CycleGadget,
  Elapsed,
  InspectorFigures,
  InspectorQuestion,
  Lamp,
  LivePane,
  LiveWell,
  PaneActions,
  SegmentedTabs,
  StepTrack,
  StringGadget,
  SurfaceState,
  type LiveLine,
} from "../surface";
import {
  decide,
  decideRequirement,
  programVerb,
  type RequirementChoice,
} from "./api";
import {
  staleAnswer,
  answerBinding,
  bindingId,
  choiceWord,
  currentStep,
  liveLamp,
} from "./liveModel";
import { ProgramsCore } from "./ProgramsWindow";
import { ProgramSteps } from "./ProgramSteps";
import { ProgramText } from "./ProgramText";
import { ProgramLedger } from "./Ledger";
import type { Program, ProgramStep, YourTurnItem } from "./types";

export { durationWords } from "./model";

export function ProgramDetail({
  program,
  loading,
  error,
  reload,
  onApplied,
  onError,
}: {
  program: Program | null;
  loading: boolean;
  error: unknown;
  reload(): Promise<unknown>;
  onApplied(next: Program | null): void;
  onError(words: string): void;
}) {
  const [tab, setTab] = useState("now"),
    [selected, setSelected] = useState<string | null>(null);
  useEffect(() => {
    if (!program) return;
    const take = () => {
      const id = takeProgramStepRequest(program.id);
      if (id) {
        setSelected(id);
        setTab("steps");
      }
    };
    take();
    window.addEventListener(PROGRAM_STEP_EVENT, take);
    return () => window.removeEventListener(PROGRAM_STEP_EVENT, take);
  }, [program?.id]);
  useEffect(() => {
    setTab("now");
    setSelected(null);
  }, [program?.id]);
  if (loading || (error && !program))
    return (
      <SurfaceState
        loading={loading}
        error={error ? "The program did not load." : undefined}
        onRetry={() => void reload()}
      />
    );
  if (!program) return null;
  const step = currentStep(program);
  return (
    <>
      <StepTrack
        label="Program steps"
        steps={program.steps
          .filter((row) => !row.race_of)
          .map((row) => ({
            id: row.id,
            name: row.title,
            state: program.your_turn_items.some(
              (item) => item.step_id === row.id,
            )
              ? "waiting"
              : row.state,
          }))}
        current={step?.id ?? null}
        selected={selected}
        onSelect={(id) => {
          setSelected(id);
          setTab("steps");
        }}
      />
      <SegmentedTabs
        label="Program view"
        tabs={[
          { id: "now", label: "Now" },
          { id: "steps", label: "Steps" },
          { id: "text", label: "Text" },
          { id: "ledger", label: "Ledger" },
        ]}
        value={tab}
        onChange={setTab}
      >
        {tab === "now" ? (
          <ProgramNow
            key={program.id}
            program={program}
            onApplied={onApplied}
            onError={onError}
          />
        ) : tab === "steps" ? (
          <ProgramSteps
            key={program.id}
            program={program}
            selected={selected}
            onSelect={setSelected}
            onApplied={onApplied}
            onError={onError}
          />
        ) : tab === "text" ? (
          <ProgramText
            key={program.id}
            program={program}
            onApplied={onApplied}
            onError={onError}
          />
        ) : (
          <ProgramLedger
            program={program}
            onApplied={onApplied}
            onError={onError}
          />
        )}
      </SegmentedTabs>
    </>
  );
}

/** Read the existing coder.peek operation. A step with no matching session
 * shows only its own ledger; no fabricated terminal text or global events. */
function useStepScreen(
  program: Program,
  step: ProgramStep | null,
  working: boolean,
): LiveLine[] {
  const sessions = useAgentFlights((s) => s.sessions);
  const session = sessions.find(
    (row) => row.flight?.launchId === step?.launch_id,
  );
  const [screen, setScreen] = useState<{
    key: string;
    lines: LiveLine[];
  } | null>(null);
  useEffect(() => {
    if (working && step?.launch_id) void useAgentFlights.getState().load(true);
  }, [working, step?.launch_id]);
  const key = session?.key;
  useEffect(() => {
    if (!working || !key) return;
    let active = true,
      pending = false;
    const read = async () => {
      if (pending || document.hidden) return;
      pending = true;
      try {
        const answer = await apiFetch<{
          peek?: { status: string; lines?: string[] };
        }>(`/api/coders/${encodeURIComponent(key)}/peek?lines=12`);
        if (active)
          setScreen(
            answer.peek?.status === "live"
              ? {
                  key,
                  lines: (answer.peek.lines ?? []).map((text, i) => ({
                    id: `${i}:${text}`,
                    text,
                  })),
                }
              : null,
          );
      } catch {
        if (active) setScreen(null);
      } finally {
        pending = false;
      }
    };
    void read();
    const timer = window.setInterval(() => void read(), 1500);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [key, working]);
  return key && screen?.key === key
    ? screen.lines
    : program.checkpoints
        .filter((row) => row.step_id === step?.id)
        .sort((a, b) => Number(a.id) - Number(b.id))
        .map((row) => ({ id: String(row.id), text: row.line }));
}

export function ProgramNow({
  program,
  onApplied,
  onError,
}: {
  program: Program;
  onApplied(next: Program | null): void;
  onError(words: string): void;
}) {
  const [itemId, setItemId] = useState(program.your_turn_items[0]?.id);
  const item =
    program.your_turn_items.find((row) => row.id === itemId) ??
    program.your_turn_items[0];
  const step =
    program.steps.find((row) => row.id === item?.step_id) ??
    currentStep(program);
  const waiting = Boolean(item),
    done = program.state === "done",
    parked = program.state === "parked" || program.state === "failed";
  const working =
    !waiting &&
    !done &&
    !parked &&
    Boolean(
      step &&
      ["briefed", "working", "checking", "review", "pr_open"].includes(
        step.state,
      ),
    );
  const lines = useStepScreen(program, step, working);
  const label = done
    ? program.title
    : step
      ? `Step ${step.ordinal} · ${step.title}`
      : program.title;
  const facts = done
    ? [
        { label: "Result", value: program.goal },
        {
          label: "Recap",
          value: program.checkpoints.find((row) => !row.step_id)?.line,
        },
      ]
    : parked
      ? [
          { label: "State", value: program.state_word },
          { label: "Last step", value: step?.title },
          {
            label: "What the agent did",
            value: step?.report_text || step?.last_checkpoint?.line,
          },
        ]
      : [
          {
            label: "What it must prove",
            value:
              step?.requirements?.map((row) => row.text).join(" · ") ||
              step?.brief ||
              program.goal,
          },
          ...(waiting
            ? [
                {
                  label: "What the agent did",
                  value:
                    item?.brief?.happened ||
                    step?.story?.map((row) => row.line).join(" ") ||
                    step?.last_checkpoint?.line,
                },
              ]
            : []),
          {
            label: "Then",
            value:
              program.steps.find(
                (row) => row.ordinal === (step?.ordinal ?? 0) + 1,
              )?.title || "The program recap",
          },
        ];
  return (
    <>
      {program.your_turn_items.length > 1 ? (
        <PaneActions>
          <CycleGadget
            label="Question"
            value={item.id}
            options={program.your_turn_items.map((row) => ({
              value: row.id,
              label: row.title,
            }))}
            onChange={setItemId}
          />
        </PaneActions>
      ) : null}
      <LivePane
        label={label}
        trailing={
          <>
            <Lamp
              state={waiting ? "waiting" : liveLamp(program.state)}
              label={waiting ? "Waits on you" : program.state_word}
            />
            <span>
              {working
                ? `${step?.agent} works`
                : waiting
                  ? "Waits on you"
                  : program.state_word}
            </span>
            {(waiting ? item?.since : working ? step?.started_at : null) ? (
              <Elapsed start={(waiting ? item?.since : step?.started_at)!} />
            ) : null}
          </>
        }
        well={
          working ? (
            <LiveWell
              lines={lines}
              show={5}
              working
              label={
                lines === undefined
                  ? "Step events"
                  : "Agent screen or step events"
              }
              data-feedback-redact="true"
            />
          ) : undefined
        }
        figures={
          done ? (
            <InspectorFigures
              label="Program recap"
              figures={[
                { value: program.done, label: "steps done" },
                {
                  value: program.checkpoints.filter((row) =>
                    row.line.startsWith("A core question for you:"),
                  ).length,
                  label: "core questions to you",
                },
                { value: program.done_in || "—", label: "from start to end" },
              ]}
            />
          ) : undefined
        }
        facts={facts}
        question={
          waiting ? (
            <>
              {item.kind === "answer" ? (
                <PaneActions>
                  <Button
                    variant="brass"
                    onClick={() => {
                      if (item.launch_id) openAgentLane(item.launch_id);
                    }}
                  >
                    Open agent session
                  </Button>
                </PaneActions>
              ) : (
                <ProgramAnswer
                  key={item.id}
                  program={program}
                  item={item}
                  onApplied={onApplied}
                  onError={onError}
                />
              )}
            </>
          ) : program.state === "drafting" ? (
            <PaneActions>
              <Button
                variant="primary"
                onClick={() =>
                  void programVerb(program.id, parked ? "resume" : "start")
                    .then(onApplied)
                    .catch((cause) => onError(readableError(cause)))
                }
              >
                {parked ? "Resume" : program.night ? "Start tonight" : "Start"}
              </Button>
            </PaneActions>
          ) : done && program.note_id ? (
            <PaneActions>
              <Button
                variant="ghost"
                onClick={() => openRef(`note:${program.note_id}`)}
              >
                Open recap
              </Button>
            </PaneActions>
          ) : undefined
        }
      />
    </>
  );
}

function ProgramAnswer({
  program,
  item,
  onApplied,
  onError,
}: {
  program: Program;
  item: YourTurnItem;
  onApplied(next: Program | null): void;
  onError(words: string): void;
}) {
  const target = bindingId(program, item.step_id || "");
  const [armed, setArmed] = useState(target),
    [busy, setBusy] = useState(false),
    [choice, setChoice] = useState(
      item.choices.find((row) => row !== "park") || item.choices[0],
    ),
    [line, setLine] = useState("");
  const pending = useRef(false),
    draft = useRef({ choice, line });
  draft.current = { choice, line };
  const run = async (park = false) => {
    if (pending.current || armed !== target) return;
    pending.current = true;
    setBusy(true);
    const binding = answerBinding(program, item.step_id || "");
    const { choice: answer, line: reason } = draft.current;
    try {
      const next =
        park && item.kind !== "core"
          ? await programVerb(program.id, "park", binding)
          : item.requirement_id
            ? await decideRequirement(
                program.id,
                item.requirement_id,
                answer as RequirementChoice,
                reason,
                binding,
              )
            : await decide(program.id, item.step_id || "program", {
                kind: item.kind === "answer" ? "core" : item.kind,
                choice: park ? "park" : answer,
                binding,
                proposal_id: item.proposal_id,
                finding_id:
                  item.finding_id ??
                  (item.proposal != null ? String(item.proposal) : undefined),
                reason,
                lesson_id: item.lesson_id,
                expected_delivery_checkpoint_id:
                  item.expected_delivery_checkpoint_id,
              });
      onApplied(next);
      onError("");
    } catch (cause) {
      onError(readableError(cause));
      if (staleAnswer(cause)) {
        setArmed("");
        onApplied(null);
      }
    } finally {
      pending.current = false;
      setBusy(false);
    }
  };
  if (armed !== target)
    return (
      <PaneActions>
        <Button variant="ghost" onClick={() => setArmed(target)}>
          Read the new question
        </Button>
      </PaneActions>
    );
  return (
    <InspectorQuestion
      targetId={target}
      question={item.brief?.question || item.title}
      cancelLabel="Park"
      variant="brass"
      rows={[
        ...(item.choices.filter((row) => row !== "park").length > 1
          ? [
              {
                label: "Answer",
                control: (
                  <CycleGadget
                    label="Answer"
                    value={choice}
                    options={item.choices
                      .filter((row) => row !== "park")
                      .map((value) => ({ value, label: choiceWord(value) }))}
                    onChange={setChoice}
                  />
                ),
              },
            ]
          : []),
        ...(item.requirement_id
          ? [
              {
                label: "Reason",
                control: (
                  <StringGadget
                    label="Reason"
                    value={line}
                    onChange={setLine}
                  />
                ),
              },
            ]
          : []),
      ]}
      cancel={() => void run(true)}
      onDisarm={() => setArmed("")}
      verb={{
        label: choiceWord(choice),
        run: () => void run(),
        busy,
        disabled: !choice || (choice === "waive" && !line.trim()),
        testId: "program-go-on",
      }}
      testId="program-question"
    />
  );
}

/** Retained pullout entry resolves to the same Programs application. */
export function ProgramBody({
  programId,
}: {
  programId: string;
  host?: string;
}) {
  return <ProgramsCore initialProgramId={programId} />;
}
export function ProgramPullout({ object }: { object: { id: string } }) {
  return <ProgramBody programId={object.id} />;
}
export default ProgramPullout;
