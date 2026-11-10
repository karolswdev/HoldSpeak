/* The same automation body in its app pane and object window: one editable
 * sentence in the mast, Run now, the run plate and the ledger of results.
 * Empty parts use these same editors. There is no separate setup body. */
import "./automation.css";
import { useCallback, useEffect, useRef, useState, type DragEvent } from "react";
import { fetchWorkbenchDetail, fetchWorkbenchMemory, forgetAutomationLesson, makeOneAutomation, openAutomationResult, setAutomationEngine, setAutomationWhen, setWorkbenchAutomationEnabled, type AutomationWhenChoice, triggerWorkbenchRun, updateWorkbenchField } from "../../api";
import type { MemoryEntry } from "../../detail-types";
import { readableError } from "../../../lib/api";
import { Button } from "../../../components/signal/Signal";
import { CheckGadget, PadGadget, SurfaceLedger, SurfaceLedgerRow, SurfaceState } from "../../surface";
import { Mast } from "../../surface/patterns/Mast";
import { Spine } from "../../surface/patterns/Spine";
import { useOptionalRuntimeBus } from "../../../runtime/RuntimeBus";
import { WORKBENCH_CHANGE_KINDS, useOnDeskChanged } from "../../useDeskChangedRefresh";
import { WORKBENCH_RUN_FRAME_TYPES } from "../workbench/runLifecycle";
import { SentenceLine } from "./SentenceLine";
import { WhenEditor } from "./WhenEditor";
import { readNativeAgentOptions, WithEditor, type NativeAgentOption } from "./WithEditor";
import { AboutEditor } from "./AboutEditor";
import { PutEditor, PutValue } from "./PutEditor";
import { useDropHand } from "../../hand";
import { openRef } from "../../openObject";
import { ResultBody, RunPlate } from "./ResultCard";
import { ProgramAgent, ProgramDo, programDraft, programFields, sameProgram, type ProgramDraft } from "./ProgramDo";
import { openNewProgram } from "../../programs/newProgram";
import { openProgram } from "../../programs/open";
import { canMakeOne, endedRuns, engineWords, eventSubjectWords, failureWords, hasStarts, isOldQueue, oldQueuePrefill, isOn, lastResultWords, nextWords, programDoWords, queueTasks, resultDay, resultLine, resultWhen, runSpine, runSpineWords, runTone, taskStateWords, whenWords, type AutomationDetail, type AutomationResult } from "./model";
import { ShowMe } from "../../walk/ShowMe";

/** What a drop on the body can add to About (the hand's kinds that are
 *  desk sources; an issue is not one). */
const ABOUT_DROP_KINDS: ReadonlySet<string> = new Set([
  "note", "meeting", "artifact", "decision", "decision_record", "action", "project_item",
]);

type DoKind = "run" | "hand_to_agent" | "run_program";

function DoEditor({
  kind,
  instruction,
  program,
  agent,
  saving,
  onSave,
  onCancel,
}: {
  kind: DoKind;
  instruction: string;
  program: ProgramDraft;
  agent: string | null;
  saving: boolean;
  onSave: (kind: DoKind, instruction: string, program?: ProgramDraft) => Promise<boolean>;
  onCancel: () => void;
}) {
  const [draftKind, setDraftKind] = useState(kind);
  const [draft, setDraft] = useState(instruction);
  const [programDraftNow, setProgramDraft] = useState(program);
  const current = useRef({ kind: draftKind, draft, program: programDraftNow });
  current.current = { kind: draftKind, draft, program: programDraftNow };
  const save = async () => {
    const submitted = current.current;
    if (!(await onSave(submitted.kind, submitted.draft.trim(), submitted.kind === "run_program" ? submitted.program : undefined))) return;
    const latest = current.current;
    if (latest.kind === submitted.kind && latest.draft === submitted.draft && sameProgram(latest.program, submitted.program)) onCancel();
  };
  const changed = draftKind !== kind || draft.trim() !== instruction.trim()
    || (draftKind === "run_program" && !sameProgram(programDraftNow, program));
  // PG14: a program needs its template; From the desk needs no goal.
  const ready = draftKind === "run_program"
    ? Boolean(programDraftNow.template) && (programDraftNow.template === "from-the-desk" || Boolean(draft.trim()))
    : Boolean(draft.trim());
  return (
    <div className="automation-do-editor" data-testid="automation-do-editor">
      <div className="automation-editor-verbs" aria-label="Do kind">
        <Button dense variant={draftKind === "run" ? "secondary" : "ghost"}
          aria-pressed={draftKind === "run"} onClick={() => setDraftKind("run")}>
          Run
        </Button>
        <Button dense variant={draftKind === "hand_to_agent" ? "secondary" : "ghost"}
          aria-pressed={draftKind === "hand_to_agent"} onClick={() => setDraftKind("hand_to_agent")}>
          Hand to an agent session
        </Button>
        <Button dense variant={draftKind === "run_program" ? "secondary" : "ghost"}
          aria-pressed={draftKind === "run_program"} onClick={() => setDraftKind("run_program")}
          data-testid="automation-do-run-program">
          Run a program
        </Button>
      </div>
      {draftKind === "run_program" ? (
        <ProgramDo draft={programDraftNow} fallbackAgent={agent} onChange={setProgramDraft} />
      ) : null}
      <PadGadget
        label={draftKind === "hand_to_agent" ? "Agent brief" : draftKind === "run_program" ? "Goal" : "What it does"}
        value={draft}
        onChange={setDraft}
        rows={4}
        autoGrow
        autoFocus
        placeholder={draftKind === "hand_to_agent" ? "Say what the agent should do"
          : draftKind === "run_program" ? "Say what the program should do" : "Say what it should do each time"}
      />
      <div className="automation-editor-verbs">
        <Button dense variant="secondary" disabled={!changed || !ready} loading={saving}
          onClick={() => void save()}
          data-testid="automation-do-save">
          Save
        </Button>
        <Button dense variant="ghost" onClick={onCancel}>Cancel</Button>
      </div>
    </div>
  );
}

function ReviewEditor({
  value,
  saving,
  onChoose,
}: {
  value: string;
  saving: boolean;
  onChoose: (value: string) => void;
}) {
  const [agents, setAgents] = useState<NativeAgentOption[] | null>(null);
  useEffect(() => { void readNativeAgentOptions().then(setAgents).catch(() => setAgents([])); }, []);
  const choices = [
    ["none", "None"],
    ...(agents ?? []).filter((agent) => agent.ready).map((agent) => [
      agent.agentId,
      agent.agentId === "codex" ? "Codex" : agent.label,
    ] as const),
  ] as ReadonlyArray<readonly [string, string]>;
  return (
    <div className="automation-editor-verbs" data-testid="automation-review-editor">
      {choices.map(([key, label]) => (
        <Button key={key} dense variant={value === key ? "secondary" : "ghost"}
          loading={saving && value !== key} onClick={() => onChoose(key)}
          aria-pressed={value === key}>
          {label}
        </Button>
      ))}
    </div>
  );
}

function Lessons({
  entries,
  onForget,
}: {
  entries: MemoryEntry[];
  onForget: (index: number, entry: MemoryEntry) => void;
}) {
  // Nothing learned yet: the fold would hold nothing (no counter of zero).
  if (!entries.length) return null;
  return (
    <section className="automation-lessons" aria-label="What it has learned"><h3 className="automation-ledger-title">What it has learned</h3>
      <ul className="automation-lesson-list" data-testid="automation-lessons">
        {entries.map((entry, index) => (
          <li key={`${entry.timestamp}-${index}`} className="automation-lesson">
            <span className="automation-lesson-text">{entry.content}</span>
            <Button dense variant="ghost" onClick={() => onForget(index, entry)}
              aria-label={`Forget: ${entry.content}`}>
              Forget
            </Button>
          </li>
        ))}
      </ul>
    </section>
  );
}

/** Betterment A9: one typed task of an old queue automation. A done or a
 *  failed task opens in place to its answer or its reason. */
function QueueTask({
  task,
  open,
  onToggle,
  onRunAgain,
  running,
}: {
  task: AutomationResult;
  open: boolean;
  onToggle: () => void;
  onRunAgain: () => void;
  running: boolean;
}) {
  const ended = task.status === "done" || task.status === "failed";
  return (
    <SurfaceLedgerRow
      time={resultDay(task.completed_at)}
      primary={task.title || resultLine(task)}
      meta={taskStateWords(task.status)}
      metaTone={task.status === "failed" ? "fail" : task.status === "done" ? "ok" : undefined}
      expands={ended}
      open={ended ? open : undefined}
      onToggle={ended ? onToggle : undefined}
      lineLabel={ended ? `${task.title}: ${taskStateWords(task.status)}` : undefined}
      data-testid="automation-task"
    >
      {ended ? (
        <div className="automation-older-open">
          <ResultBody result={task} onRunAgain={onRunAgain} runAgainDisabled={running} />
        </div>
      ) : null}
    </SurfaceLedgerRow>
  );
}

const RUN_WORDS: Record<string, string> = { coral: "Failed", brass: "New", moss: "Done", steel: "Running" };

/** One run in the ledger: its state spine, when, one line of result, its
 *  state word and Open. A press on the line shows it on the plate. */
function RunRow({ result, shown, isNew, onShow }: {
  result: AutomationResult;
  shown: boolean;
  isNew: boolean;
  onShow: () => void;
}) {
  const failed = result.status === "failed";
  const program = result.program_run ? undefined : result.program;
  const tone = isNew && !failed ? "brass" : runTone(result);
  const state = program && !failed ? program.state_word : RUN_WORDS[tone];
  const line = failed
    ? `Failed: ${failureWords(result.error)}`
    : program
      ? (program.total ? `${program.title} · ${resultWhen(result.completed_at)} · ${program.done} of ${program.total}` : program.title)
      : resultLine(result);
  const open = program ? () => openProgram(program.id)
    : result.note_id ? () => openRef(`note:${result.note_id}`) : null;
  return (
    <li className="automation-run" data-tone={tone} aria-current={shown ? "true" : undefined}
      data-testid="automation-result-row">
      <span className="automation-run-line">
        <Spine className="automation-run-spine" tone={tone} />
        <span className="automation-run-when">{resultDay(result.completed_at) || "now"}</span>
        <span className="automation-run-text">{line}</span>
        <span className="automation-run-state" data-tone={tone} data-testid="automation-result-state">{state}</span>
      </span>
      <Button dense variant="ghost" className="automation-run-open" onClick={onShow} aria-pressed={shown}>Open result</Button>
    </li>
  );
}

/** Sources in the sentence are words; the picker keeps its removable chips. */
function SentenceSources({ sources }: { sources: AutomationDetail["sources_shown"] }) {
  return <>{(sources ?? []).map((source, index) => <span key={source.ref}>
    {index ? ", " : ""}<span>{source.missing ? "Missing source" : source.kind === "folder" ? `Folder ${source.label}` : source.label}</span>
  </span>)}</>;
}

export function AutomationBody({
  workbenchId,
  onRead,
}: {
  workbenchId: string;
  /** Each read of the automation (the window's title, the app's rail). */
  onRead?: (detail: AutomationDetail) => void;
}) {
  const [detail, setDetail] = useState<AutomationDetail | null>(null);
  const sentenceAnchor = useRef<HTMLSpanElement>(null);
  const scroll = useRef<HTMLDivElement>(null);
  const [lessons, setLessons] = useState<MemoryEntry[]>([]);
  const [readError, setReadError] = useState<string | null>(null);
  const [runStart, setRunStart] = useState<number | null>(null);
  const [runRefusal, setRunRefusal] = useState<string | null>(null);
  // PG14: a run that started nothing says why ("still running").
  const [runNotice, setRunNotice] = useState<string | null>(null);
  const [editing, setEditing] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [, setEnginePending] = useState(false);
  const [, setPutSaving] = useState(false);
  const [reviewSaving, setReviewSaving] = useState(false);
  const [, setSpendSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  // The run the plate shows (the newest until he picks another).
  const [shownId, setShownId] = useState<string | null>(null);
  const [openTask, setOpenTask] = useState<string | null>(null);
  const [makingOne, setMakingOne] = useState(false);
  // A result shown as NEW keeps its NEW mark while this body is open,
  // although showing it has read it on the hub.
  const [shownNew, setShownNew] = useState<Set<string>>(() => new Set());
  const reading = useRef(0);

  const load = useCallback(async () => {
    const ask = ++reading.current;
    try {
      const [wb, memory] = await Promise.all([
        fetchWorkbenchDetail(workbenchId) as Promise<AutomationDetail>,
        fetchWorkbenchMemory(workbenchId).catch(() => [] as MemoryEntry[]),
      ]);
      if (ask !== reading.current) return;
      setDetail(wb);
      setLessons(memory);
      setReadError(null);
    } catch (error) {
      if (ask !== reading.current) return;
      setReadError(readableError(error));
    }
  }, [workbenchId]);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => { if (detail) onRead?.(detail); }, [detail, onRead]);

  const bus = useOptionalRuntimeBus();
  useOnDeskChanged(load, WORKBENCH_CHANGE_KINDS);
  useEffect(() => {
    if (!bus) return undefined;
    const offs = WORKBENCH_RUN_FRAME_TYPES.map((type) => bus.subscribe(type, (frame) => {
      const data = (frame.data ?? {}) as { workbench_id?: unknown };
      if (String(data.workbench_id ?? "") === workbenchId) void load();
    }));
    return () => offs.forEach((off) => off());
  }, [bus, load, workbenchId]);

  const results = endedRuns(detail);
  const newest = results[0] ?? null;
  const shown = results.find((r) => r.item_id === shownId) ?? newest;

  // The hub's own fact: a claimed occurrence is a run in progress (a
  // schedule or an event started it, or another view pressed Run now).
  const hubRunning = (detail?.items ?? []).some((item) => item.status === "claimed");
  const [hubRunSeen, setHubRunSeen] = useState<number | null>(null);
  useEffect(() => {
    if (hubRunning) setHubRunSeen((seen) => seen ?? Date.now());
    else setHubRunSeen(null);
  }, [hubRunning]);
  const startedAt = runStart ?? hubRunSeen;
  const engine = detail ? engineWords(detail) : null;
  const working = startedAt ? { startedAt, engine: engine ?? "" } : null;

  // Showing the newest result reads it (NEW until he opens it).
  useEffect(() => {
    if (!newest?.new || !newest.artifact_id) return;
    const artifactId = newest.artifact_id;
    setShownNew((seen) => (seen.has(artifactId) ? seen : new Set(seen).add(artifactId)));
    void openAutomationResult(workbenchId, artifactId).catch(() => undefined);
  }, [newest?.artifact_id, newest?.new, workbenchId]);

  const isNew = (result: AutomationResult) =>
    Boolean(result.artifact_id && (result.new || shownNew.has(result.artifact_id)));

  // A6: With > Add and Use save the engine first. A Run now pressed
  // meanwhile waits for that save, so it never runs on the engine from
  // before the press.
  const engineSave = useRef<Promise<unknown> | null>(null);
  const savingEngine = (pending: Promise<unknown>) => {
    setEnginePending(true);
    const settled = pending.catch(() => undefined);
    engineSave.current = settled;
    void settled.then(() => {
      if (engineSave.current === settled) {
        engineSave.current = null;
        setEnginePending(false);
      }
    });
  };

  const runNow = async () => {
    if (runStart) return;
    setRunRefusal(null);
    setRunNotice(null);
    setShownId(null);
    setRunStart(Date.now());
    try {
      if (engineSave.current) await engineSave.current;
      const ran = await triggerWorkbenchRun(workbenchId);
      if (ran?.program_id && ran.skipped && typeof ran.reason === "string") setRunNotice(ran.reason);
    } catch (error) {
      setRunRefusal(readableError(error));
    } finally {
      await load();
      setRunStart(null);
    }
  };

  /** One write to the automation, then a read; the error stays in words. */
  const write = async (busy: (on: boolean) => void, act: () => Promise<unknown>): Promise<boolean> => {
    busy(true);
    setSaveError(null);
    try {
      await act();
      await load();
      return true;
    } catch (error) {
      setSaveError(readableError(error));
      return false;
    } finally {
      busy(false);
    }
  };

  const saveDo = async (kind: DoKind, instruction: string, program?: ProgramDraft): Promise<boolean> => {
    const saved = await write(setSaving, () =>
      updateWorkbenchField(workbenchId, { do_kind: kind, instruction, ...(program ? programFields(program) : {}) }));
    return saved;
  };

  const setOn = async (on: boolean) => {
    if (!detail) return;
    await write(() => undefined, async () => {
      if (detail.schedule) await updateWorkbenchField(workbenchId, { schedule_enabled: on });
      for (const start of detail.event_starts ?? []) {
        if (start.id) await setWorkbenchAutomationEnabled(workbenchId, start.id, on);
      }
    });
  };

  // A4: one When press saves that choice at once; looking never does.
  const [whenSaving, setWhenSaving] = useState<string | null>(null);
  const chooseWhen = (choice: AutomationWhenChoice, key: string): Promise<boolean> =>
    write((on) => setWhenSaving(on ? key : null), () => setAutomationWhen(workbenchId, choice));
  const choosePut = (target: string) => write(setPutSaving, () => updateWorkbenchField(workbenchId, { output_target: target }));
  const chooseEngine = (profileId: string) => write(setEnginePending, () => setAutomationEngine(workbenchId, { profile_id: profileId }));
  const chooseReview = (reviewBy: string) => write(setReviewSaving, () => updateWorkbenchField(workbenchId, { review_by: reviewBy }));
  const saveSpendLimit = (limit: number | null) => write(setSpendSaving, () => setAutomationEngine(workbenchId, { spend_limit_usd: limit }));
  // A5: About saves each pick at once (a chip added or removed).
  const [aboutSaving, setAboutSaving] = useState(false);
  const saveSources = (sources: string[]) => write(setAboutSaving, () => updateWorkbenchField(workbenchId, { sources }));

  // A5: a desk object dropped on the body becomes an About chip.
  const [dropReady, setDropReady] = useState(false);
  const droppable = () => {
    const drag = useDropHand.getState().drag;
    return drag && ABOUT_DROP_KINDS.has(drag.origin.kind) ? drag : null;
  };
  const onDragOver = (event: DragEvent) => {
    if (!detail || eventSubjectWords(detail) || !droppable()) return;
    event.preventDefault();
    if (event.dataTransfer) event.dataTransfer.dropEffect = "copy";
    if (!dropReady) setDropReady(true);
  };
  const onDrop = (event: DragEvent) => {
    const drag = droppable();
    setDropReady(false);
    if (!detail || !drag || eventSubjectWords(detail)) return;
    event.preventDefault();
    useDropHand.getState().endDrag();
    const ref = `${drag.origin.kind}:${drag.origin.id}`;
    const refs = (detail.sources_shown ?? []).map((source) => source.ref);
    if (!refs.includes(ref)) void saveSources([...refs, ref]);
  };

  const toggle = (line: string) => { setSaveError(null); setEditing(editing === line ? null : line); };

  // A9: one press makes an old queue automation one automation.
  const makeOne = () => write(setMakingOne, () => makeOneAutomation(workbenchId));

  const forget = async (index: number, entry: MemoryEntry) => {
    try {
      await forgetAutomationLesson(workbenchId, index, entry.timestamp);
    } catch (error) {
      setSaveError(readableError(error));
    }
    await load();
  };

  // A press on a run shows it on the plate; showing a NEW result reads it
  // on the hub (it keeps NEW while this body is open).
  const showResult = (id: string) => {
    const result = results.find((r) => r.item_id === id);
    // PG14: a program run's row opens its Program window.
    if (result?.program && !result.program_run) openProgram(result.program.id);
    setShownId(id);
    requestAnimationFrame(() => scroll.current?.querySelector<HTMLElement>('[data-testid="automation-newest"]')?.scrollIntoView?.({ block: "nearest" }));
    setRunRefusal(null);
    if (result?.new && result.artifact_id) {
      const artifactId = result.artifact_id;
      setShownNew((seen) => (seen.has(artifactId) ? seen : new Set(seen).add(artifactId)));
      void openAutomationResult(workbenchId, artifactId).then(load).catch(() => undefined);
    }
  };

  const name = detail?.name || "Automation";
  const isProgram = detail?.do_kind === "run_program";
  // An old queue (an agent and no Do text of its own): Programs run it now.
  const oldQueue = Boolean(detail && (detail.do_kind ?? "run") === "run" && detail.instruction_from !== "automation"
    && isOldQueue(detail));
  const doText = detail?.do_kind === "hand_to_agent"
    ? "Hand to an agent session"
    : detail && isProgram ? programDoWords(detail) : detail?.instruction_shown ?? "";
  const firstLine = doText.split("\n")[0].replace(/[.]+$/, "");
  const doWords = firstLine.length > 180 ? `${firstLine.slice(0, 177).replace(/\s+\S*$/, "")}…` : firstLine;
  const sources = detail?.sources_shown ?? [];
  const happened = detail ? eventSubjectWords(detail) : null;
  const tasks = detail ? queueTasks(detail) : [];
  /** A10: the vendor of an agent engine (Claude Code, Codex); null otherwise. */
  const vendor = detail?.assignment_summary?.vendor || null;
  const next = detail ? nextWords(detail.next_run_at) : null;
  const spine = detail ? runSpine(detail) : [];

  let content = null;
  if (readError && !detail) content = <SurfaceState error={readError} onRetry={() => void load()} />;
  else if (!detail) content = <SurfaceState loading />;
  else {
    content = (
      <>
        {saveError ? <p className="automation-refusal automation-pane" role="alert">{saveError}</p> : null}
        {runNotice ? (
          <p className="automation-refusal automation-pane" role="status" data-testid="automation-run-notice">{runNotice}</p>
        ) : null}

        {oldQueue ? (
          // A9: an old queue is set up as a program: its tasks are the steps.
          <article className="automation-plate" data-tone="brass" data-testid="automation-old-queue">
            <header className="automation-plate-head">
              <h3 className="automation-plate-title">{tasks.length === 1 ? "1 task waits" : `${tasks.length} tasks wait`}</h3>
            </header>
            <div className="automation-plate-verbs">
              <Button dense variant="primary" onClick={() => openNewProgram(oldQueuePrefill(detail))}
                data-testid="automation-set-up-program">
                Set this up as a program
              </Button>
              {canMakeOne(detail) ? (
                <Button dense variant="secondary" loading={makingOne} onClick={() => void makeOne()} data-testid="automation-make-one">
                  Make this one automation
                </Button>
              ) : null}
            </div>
          </article>
        ) : null}
        {!oldQueue && canMakeOne(detail) ? (
          <div className="automation-pane">
            <Button dense variant="secondary" loading={makingOne} onClick={() => void makeOne()} data-testid="automation-make-one">
              Make this one automation
            </Button>
          </div>
        ) : null}
        {/* A9: an old queue with no run result yet shows its tasks, not an empty plate. */}
        {shown || working || runRefusal ? (
          <RunPlate
            result={shown}
            isNew={shown ? isNew(shown) : false}
            working={working}
            refusal={runRefusal}
            next={next}
            canRun={!oldQueue}
            onRunNow={() => void runNow()}
          />
        ) : null}

        {!oldQueue && !shown && !working && !runRefusal ? <span className="automation-quiet" data-testid="automation-no-runs">No runs yet</span> : null}

        {results.length ? (
          <section className="automation-ledger" aria-label="Runs" data-testid="automation-result-list">
            <h3 className="automation-ledger-title">Runs</h3>
            <ol className="automation-runs">
              {results.map((result) => (
                <RunRow key={result.item_id} result={result} shown={result.item_id === shown?.item_id}
                  isNew={isNew(result)} onShow={() => showResult(result.item_id)} />
              ))}
            </ol>
          </section>
        ) : null}
        {tasks.length ? (
          <SurfaceLedger label="Tasks" data-testid="automation-tasks">
            {tasks.map((task) => (
              <QueueTask
                key={task.item_id}
                task={task}
                open={openTask === task.item_id}
                onToggle={() => setOpenTask(openTask === task.item_id ? null : task.item_id)}
                onRunAgain={() => void runNow()}
                running={Boolean(working)}
              />
            ))}
          </SurfaceLedger>
        ) : null}
        <div className="automation-pane">
          <Lessons entries={lessons} onForget={(index, entry) => void forget(index, entry)} />
        </div>
      </>
    );
  }

  const sentence = detail ? (
        <span ref={sentenceAnchor} className="automation-sentence" data-testid="automation-sentence">
            <SentenceLine anchor={sentenceAnchor} name="when" label="When" variant="fact" open={editing === "when"} onPress={() => toggle("when")}
              editor={<WhenEditor detail={detail} saving={whenSaving} onChoose={(choice, key) => void chooseWhen(choice, key)} />}>
              {whenWords(detail)}
            </SentenceLine>
          <span className="automation-join">, </span>
          <SentenceLine anchor={sentenceAnchor}
            name="do"
            label="Do"
            variant="lead"
            blank={!doText}
            open={editing === "do"}
            onPress={() => toggle("do")}
            editor={
              <DoEditor key={workbenchId}
                kind={detail.do_kind === "hand_to_agent" || detail.do_kind === "run_program" ? detail.do_kind : "run"}
                instruction={detail.instruction ?? ""} program={programDraft(detail)}
                agent={detail.program?.runs_on_words ?? null} saving={saving}
                onSave={saveDo} onCancel={() => setEditing(null)} />
            }
          >
            <span className="automation-do-text">
              {doWords || "choose what to do"}
            </span>
          </SentenceLine>
          <span className="automation-head-facts">
            {happened && vendor ? (
              // A10: an event start reads the thing that happened; with an
              // agent engine, a folder can still be added for it to read.
              <SentenceLine anchor={sentenceAnchor} name="about" label="About" variant="fact" open={editing === "about"} onPress={() => toggle("about")}
                editor={<AboutEditor sources={sources} busy={aboutSaving} folders foldersOnly onChange={(refs) => void saveSources(refs)} />}>
                {happened}
                <SentenceSources sources={sources.filter((source) => source.kind === "folder")} />
              </SentenceLine>
            ) : happened ? (
              <SentenceLine anchor={sentenceAnchor} name="about" label="About" variant="fact">{happened}</SentenceLine>
            ) : (
              <SentenceLine anchor={sentenceAnchor} name="about" label="About" variant="fact" blank={!sources.length} open={editing === "about"}
                onPress={() => toggle("about")}
                editor={<AboutEditor sources={sources} busy={aboutSaving} folders={Boolean(vendor)} onChange={(refs) => void saveSources(refs)} />}>
                {sources.length ? <SentenceSources sources={sources} /> : dropReady ? "Drop it here"
                  : detail.blanks?.about ?? "What is it about?"}
              </SentenceLine>
            )}
            <SentenceLine anchor={sentenceAnchor} name="with" label="With" variant="fact" blank={!engine} open={editing === "with"} onPress={() => toggle("with")}
              editor={isProgram ? (
                <div className="automation-editor-verbs" data-testid="automation-program-with">
                  <ProgramAgent draft={programDraft(detail)} fallback={detail.program?.runs_on_words}
                    onChange={(choice) => void saveDo("run_program", detail.instruction ?? "", choice)} />
                </div>
              ) : <WithEditor detail={detail} handMode={detail.do_kind === "hand_to_agent"}
                onUse={async (profileId) => {
                  if (!(await chooseEngine(profileId))) throw new Error("Engine choice not saved. Automation stays open. Choose again.");
                }}
                onSpendLimit={async (limit) => {
                  if (!(await saveSpendLimit(limit))) throw new Error("Spend limit not saved. Automation stays open. Try again.");
                }}
                onPending={savingEngine} />}>
              {engine ?? (detail.do_kind === "hand_to_agent" || isProgram ? "Choose an agent" : "Choose an engine")}
            </SentenceLine>
            {detail.do_kind === "hand_to_agent" ? (
              <SentenceLine anchor={sentenceAnchor} name="review" label="Review by" variant="fact" open={editing === "review"} onPress={() => toggle("review")}
                editor={<ReviewEditor value={detail.review_by || "none"} saving={reviewSaving} onChoose={(value) => void chooseReview(value)} />}>
                {detail.review_by && detail.review_by !== "none"
                  ? ({ claude: "Claude Code", codex: "Codex CLI", pi: "pi" }[detail.review_by] ?? detail.review_by)
                  : "No review"}
              </SentenceLine>
            ) : null}
            {isProgram ? null : (
              <SentenceLine anchor={sentenceAnchor} name="put" label="Put it in" variant="fact" open={editing === "put"} onPress={() => toggle("put")}
                editor={<PutEditor target={detail.output_target} onChoose={async (target) => {
                  if (!(await choosePut(target))) throw new Error("Destination not saved. Automation stays open. Choose again.");
                }} />}>
                <PutValue target={detail.output_target} />
              </SentenceLine>
            )}
          </span>
        </span>
  ) : null;

  const last = detail ? lastResultWords(detail) : null;
  const facts = detail ? (
    <>
      {[name, last].filter(Boolean).join(" · ")}
      {next ? <> · <span data-testid="automation-next">{next}</span></> : null}
    </>
  ) : null;

  return (
    <div className="automation-body" data-testid="automation-window"
      data-drop-ready={dropReady || undefined}
      onDragOver={onDragOver}
      onDragLeave={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setDropReady(false);
      }}
      onDrop={onDrop}>
      <div ref={scroll} className="automation-scroll">
        {detail ? (
          <div className="automation-masthead">
            <Mast kind="automation" id={workbenchId} title={sentence} facts={facts} data-testid="automation-mast">
              {hasStarts(detail) ? (
                <span className="automation-switch" data-testid="automation-on">
                  <CheckGadget variant="state" label={`${name} is on`} checked={isOn(detail)}
                    onChange={(on) => void setOn(on)} />
                </span>
              ) : null}
              {!oldQueue ? <Button variant="primary" disabled={!doText.trim() || Boolean(working)} loading={Boolean(working)}
                onClick={() => void runNow()} data-testid="automation-run-now">Run now</Button> : null}
              <ShowMe app="surface-workbenches" />
            </Mast>
            {spine.length ? (
              <Spine className="automation-mast-spine" segments={spine} label={runSpineWords(detail) ?? undefined}
                data-testid="automation-spine" />
            ) : null}
          </div>
        ) : null}
        {content}
      </div>
    </div>
  );
}
