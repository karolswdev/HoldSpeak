import { useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { openSurfaceOr } from "../shell";
import {
  programSentence,
  programVoiceGrammar,
} from "../voice/grammars/program";
import { routeVoiceIntent } from "../voice/intentRouter";
import { ApiError } from "../../lib/api";
import { programFailure as readableError } from "./liveModel";
import {
  CycleGadget,
  PaneNotice,
  ListPane,
  ListView,
  InspectorFacts,
  InspectorBody,
  PaneActions,
  InspectorForm,
  PadGadget,
  PaneInspector,
  SegmentedTabs,
  StringGadget,
} from "../surface";
import {
  applyProgram,
  createProgram,
  applyPrograms,
  dropHeldShape,
  overturn,
  defaultProjectId,
  planDraft,
  readProjectChoices,
  readShapeEngine,
  shapeProgram,
  TEMPLATES,
  type ProjectChoice,
} from "./api";
import { answerBinding, boundId, bindingId, currentStep } from "./liveModel";
import { readControlMode } from "../hand/begin";
import { controlValue } from "./model";
import { RunsOnPicker, type RunsOnChoice } from "./RunsOn";
import { openProgram } from "./open";
import { PersonPicker, type PersonChoice } from "./PersonPicker";
import { TextChanges, type ChangeProposal } from "./ProgramText";
import type { NewProgramPrefill } from "./newProgram";
import type { Control, Program, PlanAnswer, ShapeAnswer } from "./types";

/** Creation and sentence planning keep the master list and one completion row. */
export function ProgramForm({
  kind,
  program,
  prefill,
  scopeProjectId,
  onCancel,
  onApplied,
  onOpenText,
  onBusyChange,
}: {
  kind: "new" | "amend";
  program: Program | null;
  prefill?: NewProgramPrefill;
  scopeProjectId?: string;
  onCancel(): void;
  onOpenText?(): void;
  onBusyChange?(busy: boolean): void;
  onApplied(next: Program | null): void;
}) {
  const controlChosen = useRef(false);
  useEffect(() => {
    if (kind === "new")
      void readControlMode().then((value) => {
        if (value && !controlChosen.current) setControl(controlValue(value));
      });
  }, [kind]);
  const [title, setTitle] = useState(prefill?.title || ""),
    [goal, setGoal] = useState(prefill?.goal || ""),
    [repository, setRepository] = useState("");
  const [project, setProject] = useState(""),
    [projects, setProjects] = useState<ProjectChoice[]>([]),
    [readFailed, setReadFailed] = useState(false);
  const [template, setTemplate] = useState("fast-cycle"),
    [control, setControl] = useState<Control>("yolo"),
    [check, setCheck] = useState("");
  const [agent, setAgent] = useState<RunsOnChoice>({
      profile: "claude-default",
      engine: null,
    }),
    [reviewer, setReviewer] = useState<RunsOnChoice>({
      profile: "claude-default",
      engine: null,
    }),
    [person, setPerson] = useState<PersonChoice | null>(null);
  const alive = useRef(true),
    pending = useRef(false);
  useEffect(
    () => () => {
      alive.current = false;
    },
    [],
  );
  const [spend, setSpend] = useState("");
  const projectChosen = useRef(false);
  const [question, setQuestion] = useState("");
  const [firstSentence, setFirstSentence] = useState("");
  const [review, setReview] = useState("changes");
  const [part, setPart] = useState("program");
  const [sentences, setSentences] = useState<string[]>([]);
  const [sentence, setSentence] = useState(""),
    [mode, setMode] = useState("amend"),
    [engine, setEngine] = useState<string | null | undefined>(undefined);
  const [busy, setBusy] = useState(false),
    [failed, setFailed] = useState(""),
    [unknown, setUnknown] = useState(false),
    [proposal, setProposal] = useState<ChangeProposal | null>(null);
  useEffect(() => {
    onBusyChange?.(busy);
    return () => onBusyChange?.(false);
  }, [busy, onBusyChange]);
  useEffect(() => {
    let active = true;
    void readProjectChoices()
      .then((rows) => {
        if (active) {
          setProjects(rows);
          if (!projectChosen.current)
            setProject(defaultProjectId(rows, scopeProjectId));
          setReadFailed(false);
        }
      })
      .catch(() => {
        if (active) setReadFailed(true);
      });
    return () => {
      active = false;
    };
  }, [scopeProjectId]);
  useEffect(() => {
    if (kind === "amend" && program)
      void readShapeEngine(program.id)
        .then((answer) => setEngine(answer.engine ?? null))
        .catch(() => setEngine(undefined));
  }, [kind, program?.id]);
  const retryProjects = async () => {
    try {
      const rows = await readProjectChoices();
      setProjects(rows);
      setReadFailed(false);
      if (!projectChosen.current)
        setProject(defaultProjectId(rows, scopeProjectId));
    } catch {
      setReadFailed(true);
    }
  };
  const proposalOf = (answer: ShapeAnswer | PlanAnswer) => {
    if (!program) return;
    if ("sentence" in answer && answer.sentence)
      setSentences((now) =>
        now.at(-1) === answer.sentence ? now : [...now, answer.sentence],
      );
    const targetProgram = answer.program ?? program;
    const binding = answer.binding ?? answerBinding(targetProgram);
    setReview(
      answer.changes.length
        ? "changes"
        : "applied_rows" in answer && answer.applied_rows.length
          ? "applied"
          : "changes",
    );
    setProposal({
      answer,
      text: answer.proposed_text || answer.allowed_text,
      base: answer.base,
      binding,
      target: boundId(binding, targetProgram.id),
    });
  };
  useEffect(() => {
    if (kind === "amend" && program?.held_shape) proposalOf(program.held_shape);
  }, [program?.id, program?.held_shape?.at]);
  const save = async (said = sentence) => {
    if (busy || unknown || pending.current) return;
    pending.current = true;
    setBusy(true);
    setFailed("");
    try {
      if (kind === "new") {
        const made = await createProgram({
          title,
          goal,
          template,
          control,
          ...(project ? { project_id: project } : { repository }),
          check_command: check || undefined,
          default_profile: agent.profile,
          default_engine: agent.engine || undefined,
          reviewer_profile: reviewer.profile,
          reviewer_engine: reviewer.engine || undefined,
          for_person_id: person?.id,
          steps: prefill?.steps,
          ...(spend.trim()
            ? { spend_limit_usd: Number(spend.replace(/[$,\s]/g, "")) }
            : {}),
        });
        if (alive.current) onApplied(made);
      } else if (program) {
        const known =
          engine === undefined
            ? await readShapeEngine(program.id).then(
                (answer) => answer.engine,
                () => undefined,
              )
            : engine;
        if (known === null) {
          setFailed(
            "No engine is set for planning · Nothing changed · Choose an engine in Settings",
          );
          return;
        }
        const answer =
          mode === "plan"
            ? await planDraft(program.id, { goal: said || program.goal })
            : await shapeProgram(program.id, {
                sentence: firstSentence ? `${firstSentence} ${said}` : said,
                apply: program.control === "yolo",
                binding: answerBinding(program),
                ...(proposal ? { pending: proposal.text } : {}),
              });
        if (!alive.current) return;
        if ("question" in answer && answer.question && !answer.changes.length) {
          setQuestion(answer.question);
          setFirstSentence(firstSentence ? `${firstSentence} ${said}` : said);
          setSentence("");
          return;
        }
        setQuestion("");
        setFirstSentence("");
        setSentence("");
        proposalOf(answer);
        if (answer.program) applyProgram(answer.program);
      }
    } catch (cause) {
      setFailed(readableError(cause));
      if (
        kind === "new" &&
        !(cause instanceof ApiError && [400, 409].includes(cause.status))
      )
        setUnknown(true);
    } finally {
      pending.current = false;
      if (alive.current) setBusy(false);
    }
  };
  const dictated = (text: string) => {
    void routeVoiceIntent({
      transcript: text,
      surfaceKind: programVoiceGrammar.surfaceKind,
      selectionState: { hasSelection: false },
      grammar: programVoiceGrammar,
    }).then((result) => {
      const words =
        result.intentId === "shape"
          ? String(result.params.sentence ?? "")
          : programSentence(text);
      setSentence(words);
      if (words) void save(words);
    });
  };
  const repairs =
    kind === "amend" && failed ? (
      <PaneActions>
        <Button
          variant="ghost"
          onClick={() =>
            openSurfaceOr("configure-runs-on", "/settings", "models")
          }
        >
          Open Engines
        </Button>
        <Button variant="ghost" onClick={onOpenText ?? onCancel}>
          Open text
        </Button>
      </PaneActions>
    ) : null;
  const drop = async () => {
    if (program?.held_shape) {
      try {
        onApplied(await dropHeldShape(program.id));
      } catch (e) {
        setFailed(readableError(e));
        return;
      }
    }
    setProposal(null);
  };
  if (proposal && program) {
    const answer = proposal.answer as ShapeAnswer | PlanAnswer;
    if ("programs" in answer && answer.programs?.length)
      return (
        <PlannedPrograms
          program={program}
          answer={answer as PlanAnswer}
          onApplied={onApplied}
          onCancel={() => setProposal(null)}
        />
      );
    const shaped = answer as ShapeAnswer;
    return (
      <InspectorBody>
        <InspectorFacts header={false} name="Planning" rows={[
          {label:"Engine",value:"engine" in answer ? answer.engine : undefined},
          {label:"Time",value:"seconds" in answer ? `${answer.seconds} s` : undefined},
          {label:"From",value:program.held_shape ? "On a call" : undefined},
        ]} />
        <SegmentedTabs
          label="Amendment review"
          value={review}
          onChange={setReview}
          tabs={[
            { id: "changes", label: "Changes" },
            ...(shaped.applied_rows?.length
              ? [{ id: "applied", label: "Applied" }]
              : []),
            { id: "sentence", label: "Add a sentence" },
          ]}
        >
          {review === "sentence" ? (
            <InspectorForm
              rows={[
                {
                  label: "Next change",
                  control: (
                    <StringGadget
                      label="Next program change"
                      value={sentence}
                      onChange={setSentence}
                      onDictation={dictated}
                    />
                  ),
                },
                {
                  label: "Sentences",
                  control: sentences.join(" · ") || firstSentence,
                },
              ]}
              notice={failed || question || undefined}
              completion={{
                cancel: () => setReview("changes"),
                primary: {
                  label: "Add sentence",
                  busy,
                  disabled: !sentence.trim(),
                  run: () => void save(),
                },
              }}
            />
          ) : review === "applied" ? (
            <ListPane
              label="Applied changes"
              list={
                <ListView
                  label="Applied changes"
                  headerless
                  rows={(shaped.applied_rows ?? []).map((row) => ({
                    id: row.id,
                    kind: "program",
                    name: row.say,
                    detail: row.after,
                  }))}
                  columns={[{ key: "name", word: "Change" }]}
                  verbs={[
                    {
                      id: "keep",
                      label: "Keep",
                      run: () => {
                        setProposal(null);
                        onApplied(shaped.program ?? null);
                      },
                    },
                    {
                      id: "overturn",
                      label: "Overturn",
                      enabled: () => Boolean(shaped.decision) && !busy,
                      run: () => {
                        if (shaped.decision)
                          void overturn(program.id, String(shaped.decision.id))
                            .then(onApplied)
                            .catch((e) => setFailed(readableError(e)));
                      },
                    },
                  ]}
                  toolbar={{}}
                />
              }
            >
              <PaneNotice>{shaped.say}</PaneNotice>
            </ListPane>
          ) : (
            <TextChanges
              program={program}
              proposal={proposal}
              onCancel={() => void drop()}
              onApplied={onApplied}
              onError={setFailed}
              onSplit={
                "sizes" in answer
                  ? async (place) => {
                      try {
                        proposalOf(
                          await planDraft(program.id, {
                            text: proposal.text,
                            split: place,
                          }),
                        );
                      } catch (e) {
                        setFailed(readableError(e));
                      }
                    }
                  : undefined
              }
            />
          )}
        </SegmentedTabs>
        {failed ? <PaneNotice>{failed}</PaneNotice> : null}
        {repairs}
      </InspectorBody>
    );
  }
  return (
    <PaneInspector label={kind === "new" ? "New program" : "Amend program"}>
      <InspectorBody>
        <SegmentedTabs
          label="Program form"
          value={part}
          onChange={setPart}
          tabs={
            kind === "new"
              ? [
                  { id: "program", label: "Program" },
                  { id: "work", label: "Work" },
                  { id: "checks", label: "Checks" },
                ]
              : [{ id: "program", label: "Amend" }]
          }
        >
          <InspectorForm
            rows={
              kind === "new"
                ? part === "program"
                  ? [
                      {
                        label: "Name",
                        control: (
                          <StringGadget
                            disabled={busy}
                            label="Program name"
                            value={title}
                            onChange={setTitle}
                          />
                        ),
                      },
                      {
                        label: "Goal",
                        control: (
                          <PadGadget
                            disabled={busy}
                            label="Program goal"
                            value={goal}
                            onChange={setGoal}
                          />
                        ),
                      },
                      {
                        label: "Project",
                        control: (
                          <CycleGadget
                            disabled={busy}
                            label="Project" roster
                            value={project}
                            options={[
                              { value: "", label: "A folder on this machine" },
                              ...projects.map((row) => ({
                                value: row.id,
                                label: row.name,
                              })),
                            ]}
                            onChange={(value) => {
                              projectChosen.current = true;
                              setProject(value);
                            }}
                          />
                        ),
                      },
                      ...(!project
                        ? [
                            {
                              label: "Folder",
                              control: (
                                <StringGadget
                                  disabled={busy}
                                  label="Repository folder"
                                  value={repository}
                                  onChange={(value) => {
                                    projectChosen.current = true;
                                    setRepository(value);
                                  }}
                                />
                              ),
                            },
                          ]
                        : []),
                      {
                        label: "Template",
                        control: (
                          <CycleGadget
                            disabled={busy}
                            label="Template"
                            value={template}
                            options={TEMPLATES.map((row) => ({
                              value: row.id,
                              label: row.name,
                            }))}
                            onChange={setTemplate}
                          />
                        ),
                      },
                    ]
                  : part === "checks"
                    ? [
                        {
                          label: "Check",
                          control: (
                            <StringGadget
                              label="Check command"
                              value={check}
                              onChange={setCheck}
                            />
                          ),
                        },
                        {
                          label: "Spending note, USD",
                          control: (
                            <StringGadget
                              label="Spending note in USD"
                              value={spend}
                              onChange={setSpend}
                            />
                          ),
                        },
                        {
                          label: "Spending",
                          control: "This is a note. It does not stop spending.",
                        },
                      ]
                    : [
                        {
                          label: "Control",
                          control: (
                            <CycleGadget
                              disabled={busy}
                              label="Control"
                              value={control}
                              options={[
                                { value: "yolo", label: "Runs by itself" },
                                {
                                  value: "normal",
                                  label: "Asks before it merges or sends",
                                },
                                {
                                  value: "secure",
                                  label: "Asks at every step",
                                },
                              ]}
                              onChange={(id) => {
                                controlChosen.current = true;
                                setControl(id as Control);
                              }}
                            />
                          ),
                        },
                        {
                          label: "Agent",
                          control: (
                            <RunsOnPicker
                              disabled={busy}
                              label="Choose agent"
                              value={agent}
                              onPick={setAgent}
                            />
                          ),
                        },
                        {
                          label: "Reviewer",
                          control: (
                            <RunsOnPicker
                              disabled={busy}
                              label="Choose reviewer"
                              value={reviewer}
                              onPick={setReviewer}
                            />
                          ),
                        },
                        {
                          label: "For",
                          control: (
                            <PersonPicker
                              disabled={busy}
                              value={person}
                              onPick={setPerson}
                            />
                          ),
                        },
                      ]
                : [
                    {
                      label: "Change method",
                      control: (
                        <CycleGadget
                          disabled={busy}
                          label="Change method"
                          value={mode}
                          options={[
                            { value: "amend", label: "Amend" },
                            { value: "plan", label: "Plan it" },
                          ]}
                          onChange={setMode}
                        />
                      ),
                    },
                    {
                      label: mode === "plan" ? "Goal" : "Change",
                      control: (
                        <StringGadget
                          onDictation={dictated}
                          disabled={busy}
                          label="Program change"
                          value={sentence}
                          onChange={setSentence}
                        />
                      ),
                    },
                    { label: "Engine", control: engine || "No engine set" },
                  ]
            }
            notice={
              unknown
                ? "The hub did not confirm creation. Look at the list before you create it again."
                : (failed ? (
                    <>
                      {failed}
                      {repairs}
                    </>
                  ) : undefined) ||
                  question ||
                  (readFailed ? (
                    <>
                      <PaneNotice>The projects did not load.</PaneNotice>
                      <Button
                        variant="ghost"
                        onClick={() => void retryProjects()}
                      >
                        Retry projects
                      </Button>
                    </>
                  ) : undefined)
            }
            completion={{
              cancel: onCancel,
              cancelDisabled: busy,
              primary: {
                label: kind === "new" ? "Create" : "Preview",
                busy,
                disabled:
                  unknown ||
                  (kind === "new"
                    ? !title.trim() || (!project && !repository.trim())
                    : !sentence.trim()),
                run: () => void save(),
                testId: "program-form-save",
              },
            }}
          />
        </SegmentedTabs>
      </InspectorBody>
    </PaneInspector>
  );
}

function PlannedPrograms({
  program,
  answer,
  onApplied,
  onCancel,
}: {
  program: Program;
  answer: PlanAnswer;
  onApplied(next: Program | null): void;
  onCancel(): void;
}) {
  const rows = answer.programs ?? [],
    [picked, setPicked] = useState<string | null>(null),
    [done, setDone] = useState(new Set<number>()),
    [made, setMade] = useState<{ id: string; title: string }[]>([]),
    [busy, setBusy] = useState(false),
    [failed, setFailed] = useState("");
  const at = picked === null ? -1 : Number(picked),
    row = rows[at];
  const apply = async (which: "all" | number) => {
    if (busy) return;
    setBusy(true);
    try {
      const out = await applyPrograms(
        program.id,
        rows.map(({ title, goal, text }) => ({ title, goal, text })),
        which,
      );
      applyProgram(out.program);
      setMade((now) => [...now, ...out.made]);
      setDone(
        (now) =>
          new Set([
            ...now,
            ...(which === "all" ? rows.map((_, i) => i) : [which]),
          ]),
      );
    } catch (e) {
      setFailed(readableError(e));
    } finally {
      setBusy(false);
    }
  };
  return (
    <ListPane
      label="Selected planned program"
      list={
        <ListView
          label="Planned programs"
          headerless
          columns={[{ key: "name", word: "Program" }]}
          rows={[
            ...rows.map((item, i) => ({
              id: String(i),
              kind: "program",
              name: item.title,
              detail: `${item.steps.length} steps · ${done.has(i) ? "Applied" : item.goal}`,
            })),
            ...made.map((item) => ({
              id: `program:${item.id}`,
              kind: "program",
              name: item.title,
              detail: "Created",
            })),
          ]}
          selectedId={picked}
          onSelect={setPicked}
          verbs={[
            {
              id: "one",
              label: "Apply this one",
              enabled: () => Boolean(row && !done.has(at) && !busy),
              run: () => void apply(at),
            },
            {
              id: "all",
              label: "Apply all",
              enabled: () => !done.size && !busy,
              run: () => void apply("all"),
            },
            {
              id: "cancel",
              label: done.size ? "Done" : "Cancel",
              run: onCancel,
            },
            {
              id: "open",
              label: "Open program",
              enabled: () => Boolean(picked?.startsWith("program:")),
              run: () => {
                if (picked?.startsWith("program:"))
                  openProgram(picked.slice(8));
              },
            },
          ]}
          toolbar={{}}
        />
      }
    >
      {row ? (
        <InspectorFacts
          name="Planned program"
          notice={failed || undefined}
          rows={[
            { label: "Goal", value: row.goal },
            { label: "Hands the next", value: row.hands },
            { label: "Steps", value: row.steps.join(" · ") },
          ]}
        />
      ) : failed ? (
        <PaneNotice>{failed}</PaneNotice>
      ) : null}
    </ListPane>
  );
}
