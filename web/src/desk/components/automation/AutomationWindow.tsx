/** Betterment A3 — the automation window (docs/internal/betterment/workbench/
 * DESIGN.md §4, RECIPE.md A3).
 *
 * One window: the sentence on top (When, Do, About, With, Put it in), the
 * results below it, newest first. The newest result is open and rendered;
 * each older one is one line that opens in place. Run now and the On/Off
 * switch sit in the title strip. What it has learned is a fold, closed by
 * default, with Forget on each lesson.
 *
 * Do edits in place (a text box with the mic). A4: When and With edit in
 * place too (WhenEditor, WithEditor). A5: About edits in place (the one
 * About picker, by name), and a desk object dropped on the window becomes
 * a chip; for an event start, About reads the thing that happened. A6: Put
 * it in edits in place too (PutEditor: My Inbox, Needs you, a saved
 * destination that he sends). Run now waits for an engine choice that is
 * still being saved, so it runs on the engine he just chose.
 *
 * The parked queue view (WorkbenchWindow, with its event and idle starts)
 * stays reachable through RAW in the title strip: for an old queue
 * automation, and for every automation while Builder tools is on (A8). */
import "./automation.css";
import { useCallback, useEffect, useRef, useState, type DragEvent } from "react";
import { useDesk } from "../../store";
import {
  fetchWorkbenchDetail,
  fetchWorkbenchMemory,
  forgetAutomationLesson,
  makeOneAutomation,
  openAutomationResult,
  setAutomationEngine,
  setAutomationWhen,
  setWorkbenchAutomationEnabled,
  type AutomationWhenChoice,
  triggerWorkbenchRun,
  updateWorkbenchField,
} from "../../api";
import type { MemoryEntry } from "../../detail-types";
import { readableError } from "../../../lib/api";
import { Button } from "../../../components/signal/Signal";
import { DeskWindowFrame } from "../DeskWindow";
import {
  CheckGadget,
  FoldGadget,
  PadGadget,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceSection,
  SurfaceState,
  StateChip,
  EgressChip,
} from "../../surface";
import { boundaryEgressLamp } from "../../inferenceEgress";
import { useOptionalRuntimeBus } from "../../../runtime/RuntimeBus";
import { WORKBENCH_RUN_FRAME_TYPES } from "../workbench/runLifecycle";
import { SentenceLine } from "./SentenceLine";
import { AutomationBuilder } from "./AutomationBuilder";
import { spriteUrl } from "../../sprites";
import { WhenEditor } from "./WhenEditor";
import { readNativeAgentOptions, WithEditor, type NativeAgentOption } from "./WithEditor";
import { AboutChips, AboutEditor } from "./AboutEditor";
import { PutEditor, PutValue } from "./PutEditor";
import { useDropHand } from "../../hand";
import { useBuilderTools } from "../../builderTools";
import { ResultBody, ResultCard, ResultHead } from "./ResultCard";
import {
  canMakeOne,
  engineWords,
  eventSubjectWords,
  failureWords,
  hasStarts,
  isOldQueue,
  isOn,
  lessonWords,
  nextWords,
  queueTasks,
  resultDay,
  resultLine,
  secondsWords,
  taskStateWords,
  whenWords,
  type AutomationDetail,
  type AutomationResult,
} from "./model";

/** The window opens large enough for the sentence and the newest result
 *  (RECIPE A3: at least 880 x 640 at 1440). */
/** What a drop on the window can add to About (the hand's kinds that are
 *  desk sources; an issue is not one). */
const ABOUT_DROP_KINDS: ReadonlySet<string> = new Set([
  "note", "meeting", "artifact", "decision", "decision_record", "action", "project_item",
]);

export const AUTOMATION_WINDOW_SIZE = { w: 920, h: 680 } as const;

function DoEditor({
  kind,
  instruction,
  saving,
  onSave,
  onCancel,
}: {
  kind: "run" | "hand_to_agent";
  instruction: string;
  saving: boolean;
  onSave: (kind: "run" | "hand_to_agent", instruction: string) => void;
  onCancel: () => void;
}) {
  const [draftKind, setDraftKind] = useState(kind);
  const [draft, setDraft] = useState(instruction);
  const changed = draftKind !== kind || draft.trim() !== instruction.trim();
  return (
    <div className="automation-do-editor" data-testid="automation-do-editor">
      <div className="automation-editor-verbs" aria-label="Do kind">
        <Button dense variant={draftKind === "run" ? "secondary" : "ghost"}
          aria-pressed={draftKind === "run"} onClick={() => setDraftKind("run")}>
          Run
        </Button>
        <Button dense variant={draftKind === "hand_to_agent" ? "secondary" : "ghost"}
          aria-pressed={draftKind === "hand_to_agent"} onClick={() => setDraftKind("hand_to_agent")}>
          Hand to an agent
        </Button>
      </div>
      <PadGadget
        label={draftKind === "hand_to_agent" ? "Agent brief" : "What it does"}
        value={draft}
        onChange={setDraft}
        rows={4}
        autoGrow
        autoFocus
        placeholder={draftKind === "hand_to_agent" ? "Say what the agent should do" : "Say what it should do each time"}
      />
      <div className="automation-editor-verbs">
        <Button dense variant="secondary" disabled={!changed || !draft.trim()} loading={saving}
          onClick={() => onSave(draftKind, draft.trim())} data-testid="automation-do-save">
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
    <FoldGadget title="What it has learned" token={lessonWords(entries.length)} className="automation-lessons">
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
    </FoldGadget>
  );
}

function OlderResult({
  result,
  isNew,
  open,
  onToggle,
  onRunAgain,
  running,
}: {
  result: AutomationResult;
  isNew: boolean;
  open: boolean;
  onToggle: () => void;
  onRunAgain: () => void;
  running: boolean;
}) {
  const failed = result.status === "failed";
  return (
    <SurfaceLedgerRow
      time={resultDay(result.completed_at)}
      primary={failed ? `Failed: ${failureWords(result.error)}` : resultLine(result)}
      meta={failed ? undefined : [secondsWords(result.seconds), result.model].filter(Boolean).join(" · ")}
      metaTone={failed ? "fail" : undefined}
      cells={isNew ? <StateChip state="active" label="NEW" /> : undefined}
      trailing={failed ? (
        <Button dense variant="ghost" onClick={onRunAgain} disabled={running}>Run again</Button>
      ) : undefined}
      open={open}
      onToggle={onToggle}
      lineLabel={failed ? undefined : `${resultDay(result.completed_at)}: ${resultLine(result)}`}
      data-testid="automation-older"
    >
      <div className="automation-older-open">
        <header className="automation-card-head"><ResultHead result={result} isNew={false} /></header>
        <ResultBody result={result} onRunAgain={onRunAgain} runAgainDisabled={running} />
      </div>
    </SurfaceLedgerRow>
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

export function AutomationWindow({
  workbenchId,
  origin,
  onRaw,
}: {
  workbenchId: string;
  origin?: { x: number; y: number } | null;
  /** The parked queue view, for an old queue automation. */
  onRaw?: () => void;
}) {
  const [detail, setDetail] = useState<AutomationDetail | null>(null);
  const [lessons, setLessons] = useState<MemoryEntry[]>([]);
  const [readError, setReadError] = useState<string | null>(null);
  const [runStart, setRunStart] = useState<number | null>(null);
  const [runRefusal, setRunRefusal] = useState<string | null>(null);
  const [editing, setEditing] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [enginePending, setEnginePending] = useState(false);
  const [putSaving, setPutSaving] = useState(false);
  const [reviewSaving, setReviewSaving] = useState(false);
  const [spendSaving, setSpendSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [wizardAutoStarted, setWizardAutoStarted] = useState(false);
  const [wizardDismissed, setWizardDismissed] = useState(false);
  const [openOlder, setOpenOlder] = useState<string | null>(null);
  const [openTask, setOpenTask] = useState<string | null>(null);
  const [makingOne, setMakingOne] = useState(false);
  // A long Do (an old agent's prompt) is clamped to 3 lines on a phone.
  const [doExpanded, setDoExpanded] = useState(false);
  // A result shown as NEW keeps its NEW mark while this window is open,
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

  const bus = useOptionalRuntimeBus();
  useEffect(() => {
    if (!bus) return undefined;
    const offs = [
      bus.subscribe("desk_changed", () => { void load(); }),
      ...WORKBENCH_RUN_FRAME_TYPES.map((type) => bus.subscribe(type, (frame) => {
        const data = (frame.data ?? {}) as { workbench_id?: unknown };
        if (String(data.workbench_id ?? "") === workbenchId) void load();
      })),
    ];
    return () => offs.forEach((off) => off());
  }, [bus, load, workbenchId]);

  // A claimed or pending occurrence is the run in progress, not a result:
  // the working line says so in the newest card's head.
  const results = (detail?.results ?? []).filter((r) => r.status === "done" || r.status === "failed");
  const newest = results[0] ?? null;
  const older = results.slice(1);

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

  // A6 (the A7 follow-up): With > Add and Use save the engine first. A Run
  // now pressed meanwhile waits for that save, so it never runs (or is
  // refused) on the engine from before the press.
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
    setRunStart(Date.now());
    try {
      if (engineSave.current) await engineSave.current;
      await triggerWorkbenchRun(workbenchId);
    } catch (error) {
      setRunRefusal(readableError(error));
    } finally {
      await load();
      setRunStart(null);
    }
  };

  const saveDo = async (kind: "run" | "hand_to_agent", instruction: string): Promise<boolean> => {
    setSaving(true);
    setSaveError(null);
    try {
      await updateWorkbenchField(workbenchId, { do_kind: kind, instruction });
      setEditing(null);
      await load();
      return true;
    } catch (error) {
      setSaveError(readableError(error));
      return false;
    } finally {
      setSaving(false);
    }
  };

  const setOn = async (on: boolean) => {
    if (!detail) return;
    setSaveError(null);
    try {
      if (detail.schedule) await updateWorkbenchField(workbenchId, { schedule_enabled: on });
      for (const start of detail.event_starts ?? []) {
        if (start.id) await setWorkbenchAutomationEnabled(workbenchId, start.id, on);
      }
    } catch (error) {
      setSaveError(readableError(error));
    }
    await load();
  };

  // A4: one When press saves that choice at once; looking never does.
  const [whenSaving, setWhenSaving] = useState<string | null>(null);
  const chooseWhen = async (choice: AutomationWhenChoice, key: string): Promise<boolean> => {
    let saved = true;
    setWhenSaving(key);
    setSaveError(null);
    try {
      await setAutomationWhen(workbenchId, choice);
      await load();
    } catch (error) {
      setSaveError(readableError(error));
      saved = false;
    } finally {
      setWhenSaving(null);
    }
    return saved;
  };

  const choosePut = async (target: string): Promise<boolean> => {
    setPutSaving(true);
    setSaveError(null);
    try {
      await updateWorkbenchField(workbenchId, { output_target: target });
      await load();
      return true;
    } catch (error) {
      setSaveError(readableError(error));
      return false;
    } finally {
      setPutSaving(false);
    }
  };

  const chooseEngine = async (profileId: string): Promise<boolean> => {
    setEnginePending(true);
    setSaveError(null);
    try {
      await setAutomationEngine(workbenchId, { profile_id: profileId });
      await load();
      return true;
    } catch (error) {
      setSaveError(readableError(error));
      return false;
    } finally {
      setEnginePending(false);
    }
  };

  const chooseReview = async (reviewBy: string): Promise<boolean> => {
    setReviewSaving(true);
    setSaveError(null);
    try {
      await updateWorkbenchField(workbenchId, { review_by: reviewBy });
      await load();
      return true;
    } catch (error) {
      setSaveError(readableError(error));
      return false;
    } finally {
      setReviewSaving(false);
    }
  };

  const saveSpendLimit = async (limit: number | null): Promise<boolean> => {
    setSpendSaving(true);
    setSaveError(null);
    try {
      await setAutomationEngine(workbenchId, { spend_limit_usd: limit });
      await load();
      return true;
    } catch (error) {
      setSaveError(readableError(error));
      return false;
    } finally {
      setSpendSaving(false);
    }
  };

  // A5: About saves each pick at once (a chip added or removed).
  const [aboutSaving, setAboutSaving] = useState(false);
  const saveSources = async (sources: string[]): Promise<boolean> => {
    setAboutSaving(true);
    setSaveError(null);
    try {
      await updateWorkbenchField(workbenchId, { sources });
      await load();
      return true;
    } catch (error) {
      setSaveError(readableError(error));
      return false;
    } finally {
      setAboutSaving(false);
    }
  };

  // A5: a desk object dropped on the window (a floor or drawer icon's drag)
  // becomes an About chip. Anything else is not taken.
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

  // A9: one press makes an old queue automation one automation (its
  // agent's prompt becomes Do); its tasks and their results stay listed.
  const makeOne = async () => {
    setMakingOne(true);
    setSaveError(null);
    try {
      await makeOneAutomation(workbenchId);
    } catch (error) {
      setSaveError(readableError(error));
    } finally {
      setMakingOne(false);
    }
    await load();
  };

  const forget = async (index: number, entry: MemoryEntry) => {
    try {
      await forgetAutomationLesson(workbenchId, index, entry.timestamp);
    } catch (error) {
      setSaveError(readableError(error));
    }
    await load();
  };

  const openOlderResult = (result: AutomationResult) => {
    const opening = openOlder !== result.item_id;
    setOpenOlder(opening ? result.item_id : null);
    if (opening && result.new && result.artifact_id) {
      const artifactId = result.artifact_id;
      void openAutomationResult(workbenchId, artifactId).then(load).catch(() => undefined);
    }
  };

  // Betterment A8: the parked faces (the queue, event and idle starts) stay
  // behind RAW: for an old queue automation, and for any one while Builder
  // tools is on.
  const builder = useBuilderTools((state) => state.on);
  const name = detail?.name || "Automation";
  const doText = detail?.do_kind === "hand_to_agent"
    ? "Hand to an agent"
    : detail?.instruction_shown ?? "";
  const doLong = doText.split("\n").length > 3 || doText.length > 180;
  const sources = detail?.sources_shown ?? [];
  const happened = detail ? eventSubjectWords(detail) : null;
  const tasks = detail ? queueTasks(detail) : [];
  /** A10: the vendor of an agent engine (Claude Code, Codex); null otherwise. */
  const vendor = detail?.assignment_summary?.vendor || null;
  const blankScratch = Boolean(detail
    && !String(detail.instruction ?? detail.instruction_shown ?? "").trim()
    && !results.length
    && !(detail.items ?? []).length);
  useEffect(() => {
    if (blankScratch && !wizardDismissed) setWizardAutoStarted(true);
  }, [blankScratch, wizardDismissed]);
  const showBuilder = Boolean(detail
    && (wizardOpen || wizardAutoStarted || (!wizardDismissed && blankScratch)));
  const setupPending = saving || aboutSaving || putSaving || reviewSaving || spendSaving
    || enginePending || Boolean(engineSave.current) || Boolean(whenSaving);

  return (
    <DeskWindowFrame
      id={`workbench:${workbenchId}`}
      glyph="⚒"
      label={name}
      kindWord="Automation"
      title={name}
      actions={
        <span className="automation-title-verbs">
          {detail && hasStarts(detail) ? (
            <span className="automation-switch" data-testid="automation-on">
              <CheckGadget variant="state" label={`${name} is on`} checked={isOn(detail)}
                onChange={(next) => void setOn(next)} />
            </span>
          ) : null}
          {detail && onRaw && (isOldQueue(detail) || builder) ? (
            <Button dense variant="ghost" onClick={onRaw} data-testid="automation-raw">RAW</Button>
          ) : null}
          <Button
            dense
            variant="primary"
            onClick={() => void runNow()}
            disabled={!detail || Boolean(working) || showBuilder}
            data-testid="automation-run-now"
          >
            Run now
          </Button>
        </span>
      }
      minW={480}
      minH={360}
      defaultW={AUTOMATION_WINDOW_SIZE.w}
      defaultH={AUTOMATION_WINDOW_SIZE.h}
      open
      origin={origin}
      onClose={() => useDesk.getState().closeWorkbenchWindow(workbenchId)}
      className="desk-pullout automation-window"
    >
      <div className="desk-surface-body surface-host-body automation-body" data-surface-host="automation" data-testid="automation-window"
        data-drop-ready={dropReady || undefined}
        onDragOver={onDragOver}
        onDragLeave={(event) => {
          if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setDropReady(false);
        }}
        onDrop={onDrop}>
        {readError && !detail ? <SurfaceState error={readError} onRetry={() => void load()} /> : null}
        {!detail && !readError ? <SurfaceState loading /> : null}
        {detail ? showBuilder ? (
          <AutomationBuilder
            detail={detail}
            pending={setupPending}
            whenSaving={whenSaving}
            saveError={saveError}
            onSaveDo={saveDo}
            onSaveSources={saveSources}
            onChooseEngine={chooseEngine}
            onSpendLimit={saveSpendLimit}
            onChooseWhen={chooseWhen}
            onChoosePut={choosePut}
            onChooseReview={chooseReview}
            onPending={savingEngine}
            onDone={() => {
              setWizardOpen(false);
              setWizardAutoStarted(false);
              setWizardDismissed(true);
            }}
          />
        ) : (
          <>
            <div className="automation-edit-setup">
              <Button dense variant="ghost" onClick={() => {
                setWizardOpen(true);
                setWizardAutoStarted(false);
                setWizardDismissed(false);
              }}
                data-testid="automation-edit-setup">
                Edit setup
              </Button>
            </div>
            <div className="automation-sentence" data-testid="automation-sentence">
              <SentenceLine
                name="when"
                label="When"
                icon={<img src={spriteUrl("meeting", "automation-when", "rest", undefined, 32)} alt="" />}
                open={editing === "when"}
                onPress={() => toggle("when")}
                aside={nextWords(detail.next_run_at) ? (
                  <span className="automation-next" data-testid="automation-next">{nextWords(detail.next_run_at)}</span>
                ) : undefined}
                editor={<WhenEditor detail={detail} saving={whenSaving}
                  onChoose={(choice, key) => void chooseWhen(choice, key)} />}
              >
                {whenWords(detail)}
              </SentenceLine>
              <SentenceLine
                name="do"
                label="Do"
                icon={<img src={spriteUrl("artifact", "automation-do", "rest", undefined, 32)} alt="" />}
                blank={!doText}
                open={editing === "do"}
                onPress={() => toggle("do")}
                aside={doLong && editing !== "do" ? (
                  <Button dense variant="ghost" className="automation-do-more"
                    aria-expanded={doExpanded} onClick={() => setDoExpanded(!doExpanded)}
                    data-testid="automation-do-more">
                    {doExpanded ? "less" : "more"}
                  </Button>
                ) : undefined}
                editor={
                  <DoEditor key={`${detail.do_kind}:${detail.instruction ?? ""}`} kind={detail.do_kind === "hand_to_agent" ? "hand_to_agent" : "run"}
                    instruction={detail.instruction ?? ""} saving={saving}
                    onSave={(kind, next) => void saveDo(kind, next)} onCancel={() => setEditing(null)} />
                }
              >
                <span className="automation-do-text" data-clamped={doLong && !doExpanded ? "" : undefined}>
                  {doText || "What should it do?"}
                </span>
              </SentenceLine>
              {happened && vendor ? (
                // A10: an event start reads the thing that happened; with an
                // agent engine, a folder can still be added for it to read.
                <SentenceLine
                  name="about"
                  label="About"
                  icon={<img src={spriteUrl("directory", "automation-about", "rest", undefined, 32)} alt="" />}
                  open={editing === "about"}
                  onPress={() => toggle("about")}
                  editor={<AboutEditor sources={sources} busy={aboutSaving} folders foldersOnly
                    onChange={(refs) => void saveSources(refs)} />}
                >
                  {happened}
                  <AboutChips sources={sources.filter((source) => source.kind === "folder")} />
                </SentenceLine>
              ) : happened ? (
                <SentenceLine name="about" label="About"
                  icon={<img src={spriteUrl("directory", "automation-about", "rest", undefined, 32)} alt="" />}>
                  {happened}
                </SentenceLine>
              ) : (
                <SentenceLine
                  name="about"
                  label="About"
                  icon={<img src={spriteUrl("directory", "automation-about", "rest", undefined, 32)} alt="" />}
                  blank={!sources.length}
                  open={editing === "about"}
                  onPress={() => toggle("about")}
                  editor={<AboutEditor sources={sources} busy={aboutSaving}
                    folders={Boolean(vendor)}
                    onChange={(refs) => void saveSources(refs)} />}
                >
                  {sources.length ? <AboutChips sources={sources} /> : dropReady ? "Drop it here"
                    : detail.blanks?.about ?? "What is it about?"}
                </SentenceLine>
              )}
              <SentenceLine
                name="with"
                label="With"
                icon={<img src={spriteUrl("workbench", "automation-with", "rest", undefined, 32)} alt="" />}
                blank={!engine}
                open={editing === "with"}
                onPress={() => toggle("with")}
                aside={engine && vendor ? (
                  // A10: an agent engine's prompt goes to its vendor: the chip says which.
                  <EgressChip label={vendor.toUpperCase()} title={`The prompt goes to ${vendor}`} scope="cloud" />
                ) : engine && detail.assignment_summary?.boundary ? (
                  <EgressChip label={boundaryEgressLamp(detail.assignment_summary.boundary).label}
                    title={`The prompt goes: ${boundaryEgressLamp(detail.assignment_summary.boundary).label}`}
                    scope={["local", "same_device"].includes(detail.assignment_summary.boundary) ? "local" : "cloud"} />
                ) : undefined}
                editor={<WithEditor detail={detail} handMode={detail.do_kind === "hand_to_agent"}
                  onUse={async (profileId) => {
                    if (!(await chooseEngine(profileId))) throw new Error("Engine choice not saved. Automation stays open. Choose again.");
                  }}
                  onSpendLimit={async (limit) => {
                    if (!(await saveSpendLimit(limit))) throw new Error("Spend limit not saved. Automation stays open. Try again.");
                  }}
                  onPending={savingEngine} />}
              >
                {detail.do_kind === "hand_to_agent"
                  ? engine ?? "Choose an agent"
                  : engine ?? "Choose an engine"}
              </SentenceLine>
              {detail.do_kind === "hand_to_agent" ? (
                <SentenceLine
                  name="review"
                  label="Review by"
                  icon={<img src={spriteUrl("person", "automation-review", "rest", undefined, 32)} alt="" />}
                  open={editing === "review"}
                  onPress={() => toggle("review")}
                  editor={<ReviewEditor value={detail.review_by || "none"} saving={reviewSaving}
                    onChoose={(value) => void chooseReview(value)} />}
                >
                  {detail.review_by && detail.review_by !== "none"
                    ? ({ claude: "Claude Code", codex: "Codex CLI", pi: "pi" }[detail.review_by] ?? detail.review_by)
                    : "No review"}
                </SentenceLine>
              ) : null}
              <SentenceLine
                name="put"
                label="Put it in"
                icon={<img src={spriteUrl("repository", "automation-put", "rest", undefined, 32)} alt="" />}
                open={editing === "put"}
                onPress={() => toggle("put")}
                editor={<PutEditor target={detail.output_target}
                  onChoose={async (target) => {
                    if (!(await choosePut(target))) throw new Error("Destination not saved. Automation stays open. Choose again.");
                  }} />}
              >
                <PutValue target={detail.output_target} />
              </SentenceLine>
            </div>
            {saveError ? (
              <p className="automation-refusal" role="alert">{saveError}</p>
            ) : null}

            <SurfaceSection label="Results" className="automation-results" data-testid="automation-results">
              {runRefusal ? (
                <div className="automation-failure" data-testid="automation-refusal">
                  <p className="automation-failure-words">{failureWords(runRefusal)}</p>
                  <Button dense variant="secondary" onClick={() => void runNow()} disabled={Boolean(working)}>
                    Run again
                  </Button>
                </div>
              ) : null}
              {detail && canMakeOne(detail) ? (
                <div className="automation-make-one">
                  <Button dense variant="secondary" loading={makingOne} onClick={() => void makeOne()}
                    data-testid="automation-make-one">
                    Make this one automation
                  </Button>
                </div>
              ) : null}
              {/* A9: an old queue automation with no run result yet shows its
                  tasks, not an empty card. */}
              {newest || working || !tasks.length ? (
                <ResultCard
                  result={newest}
                  isNew={newest ? isNew(newest) : false}
                  working={working}
                  onRunAgain={() => void runNow()}
                />
              ) : null}
              {older.length ? (
                <SurfaceLedger label="Older results" data-testid="automation-older-list">
                  {older.map((result) => (
                    <OlderResult
                      key={result.item_id}
                      result={result}
                      isNew={isNew(result)}
                      open={openOlder === result.item_id}
                      onToggle={() => openOlderResult(result)}
                      onRunAgain={() => void runNow()}
                      running={Boolean(working)}
                    />
                  ))}
                </SurfaceLedger>
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
            </SurfaceSection>

            <Lessons entries={lessons} onForget={(index, entry) => void forget(index, entry)} />
          </>
        ) : null}
      </div>
    </DeskWindowFrame>
  );
}
