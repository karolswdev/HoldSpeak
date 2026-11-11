import { ApiError } from "../../lib/api";
import { Button } from "../../components/signal/Signal";
import { useEffect, useState } from "react";
import { openRef } from "../openObject";
import { programFailure as readableError } from "./liveModel";
import {
  CheckGadget,
  CycleGadget,
  InspectorFacts,
  InspectorForm,
  InspectorQuestion,
  ListPane,
  ListView,
  PaneInspector,
  PadGadget,
  StringGadget,
  SegmentedTabs,
  type ListVerb,
} from "../surface";
import {
  amendStep,
  changeStep,
  decide,
  handLaneBack,
  handoff,
  insertStep,
  planProgram,
  refreshProgram,
  removeProgramStep,
  takeLane,
  type StepChangeBody,
} from "./api";
import { RunsOnPicker, type RunsOnChoice } from "./RunsOn";
import { ProgramRequirements } from "./ProgramRequirements";
import {
  ProgramRace,
  ProgramHandoffs,
  ProgramBulkAgents,
} from "./ProgramRecords";
import { ProgramInterview } from "./ProgramInterview";
import {
  answerBinding,
  bindingId,
  choiceWord,
  liveLamp,
  stepResult,
} from "./liveModel";
import type { Program, ProgramStep } from "./types";

export function ProgramSteps({
  program,
  selected,
  onSelect,
  onApplied,
  onError,
}: {
  program: Program;
  selected: string | null;
  onSelect(id: string): void;
  onApplied(next: Program | null): void;
  onError(words: string): void;
}) {
  const [handing, setHanding] = useState(false),
    [inserting, setInserting] = useState<string | null>(null);
  const [editing, setEditing] = useState(false),
    [question, setQuestion] = useState<"remove" | "skip" | null>(null),
    [adding, setAdding] = useState(false);
  const [amending, setAmending] = useState(false);
  const [uncertain, setUncertain] = useState(false);
  const [racing, setRacing] = useState(false);
  const [busy, setBusy] = useState(false),
    [part, setPart] = useState("brief");
  const step =
    program.steps.find(
      (row) =>
        row.id === selected ||
        row.contenders?.some((child) => child.id === selected),
    ) ?? null;
  useEffect(() => {
    if (step && selected !== step.id) setPart("race");
  }, [selected, step?.id]);
  const result = step ? stepResult(step) : null;
  const work = async (call: () => Promise<Program | null>) => {
    if (busy) return;
    setBusy(true);
    try {
      onApplied(await call());
      onError("");
      setQuestion(null);
      setEditing(false);
      setAdding(false);
      setHanding(false);
      setInserting(null);
    } catch (cause) {
      if (
        adding &&
        !(
          cause instanceof ApiError &&
          cause.status >= 400 &&
          cause.status < 500
        )
      ) {
        setUncertain(true);
        onError(
          "The hub did not confirm the new step. Read the steps before you add it again.",
        );
      } else onError(readableError(cause));
    } finally {
      setBusy(false);
    }
  };
  const move = (dir: number) => {
    if (!step) return;
    const steps = program.steps.filter((row) => !row.race_of),
      at = steps.findIndex((row) => row.id === step.id);
    const before = dir < 0 ? steps[at - 1]?.id : (steps[at + 2]?.id ?? "end");
    if (
      dir < 0 &&
      steps[at - 1] &&
      step.after.includes(steps[at - 1].ordinal)
    ) {
      onError("This step must stay after its dependency.");
      return;
    }
    if (before) void work(() => changeStep(program.id, step.id, { before }));
  };
  const verbs: ListVerb[] = [
    {
      id: "log",
      label: "Open log",
      enabled: () => Boolean(step?.check.log),
      run: () => {
        if (step?.check.log)
          openRef(
            step.check.log.startsWith("note:")
              ? step.check.log
              : `note:${step.check.log}`,
          );
      },
    },
    {
      id: "pr",
      label: "Open PR",
      enabled: () => Boolean(step?.pr?.url),
      run: () => {
        if (step?.pr?.url)
          window.open(step.pr.url, "_blank", "noopener,noreferrer");
      },
    },
    {
      id: "add",
      label: "Add step",
      enabled: () => program.state !== "done",
      run: () => setAdding(true),
    },
    {
      id: "insert",
      label: "Insert before",
      enabled: () => Boolean(step?.editable?.includes("position")),
      run: () => {
        setInserting(step!.id);
        setAdding(true);
      },
    },
    {
      id: "race",
      label: "Race",
      enabled: () => Boolean(step && ["planned", "ready"].includes(step.state)),
      run: () => {
        setPart("race");
        setRacing(true);
      },
    },
    {
      id: "take",
      label: step?.taken ? "Hand it back" : "Take it over",
      enabled: () => Boolean(step?.launch_id),
      run: () =>
        void work(() =>
          step!.taken
            ? handLaneBack(program.id, step!.id)
            : takeLane(program.id, step!.id),
        ),
    },
    {
      id: "handoff",
      label: "Hand off",
      enabled: () => Boolean(step?.launch_id),
      run: () => setHanding(true),
    },
    {
      id: "edit",
      label: "Edit step",
      enabled: () => Boolean(step),
      run: () => {
        setAmending(false);
        setEditing(true);
      },
    },
    {
      id: "amend-brief",
      label: "Amend brief",
      enabled: () => Boolean(step?.editable?.includes("amend")),
      run: () => {
        setAmending(true);
        setEditing(true);
      },
    },
    {
      id: "up",
      label: "Move up",
      key: "Alt+ArrowUp",
      enabled: () =>
        Boolean(step?.editable?.includes("position") && step.ordinal > 1),
      run: () => move(-1),
    },
    {
      id: "down",
      label: "Move down",
      key: "Alt+ArrowDown",
      enabled: () =>
        Boolean(
          step?.editable?.includes("position") &&
          step.ordinal < program.steps.length,
        ),
      run: () => move(1),
    },
    {
      id: "skip",
      label: "Skip",
      enabled: () => step?.state === "parked",
      run: () => setQuestion("skip"),
    },
    {
      id: "remove",
      label: "Remove step",
      enabled: () => Boolean(step && ["planned", "ready"].includes(step.state)),
      run: () => setQuestion("remove"),
    },
  ];
  const tabs = [
    { id: "brief", label: "Step" },
    { id: "requirements", label: "Requirements" },
    { id: "gate", label: "Gate" },
    { id: "rounds", label: "Rounds" },
    { id: "report", label: "Report" },
    { id: "handoffs", label: "Handoffs" },
    { id: "race", label: "Race" },
    { id: "agents", label: "Agents" },
  ];
  const rank = (id: string) => {
    const at = ["edit", "add", "up", "down", "remove"].indexOf(id);
    return at < 0 ? Number.POSITIVE_INFINITY : at;
  };
  verbs.sort((a, b) => rank(a.id) - rank(b.id));
  if (
    !["brief", "gate", "report"].includes(part) &&
    !editing &&
    !adding &&
    !question &&
    !handing
  )
    return (
      <SegmentedTabs
        label="Step view"
        value={part}
        onChange={setPart}
        tabs={tabs}
      >
        {part === "agents" ? (
          <ProgramBulkAgents
            program={program}
            onApplied={onApplied}
            onError={onError}
          />
        ) : part === "requirements" ? (
          <ProgramRequirements
            key={step?.id}
            program={program}
            step={step}
            onApplied={onApplied}
            onError={onError}
          />
        ) : part === "rounds" ? (
          <ProgramInterview
            program={program}
            onApplied={onApplied}
            onError={onError}
          />
        ) : part === "race" ? (
          <ProgramRace
            program={program}
            step={step}
            selectedChild={selected !== step?.id ? selected : null}
            creating={racing}
            onCreated={() => setRacing(false)}
            onApplied={onApplied}
            onError={onError}
          />
        ) : (
          <ProgramHandoffs program={program} step={step} />
        )}
      </SegmentedTabs>
    );
  const detail = adding ? (
    <StepEditor
      program={program}
      uncertain={uncertain}
      onRead={() => {
        void refreshProgram(program.id)
          .then((next) => {
            onApplied(next);
            setAdding(false);
            setUncertain(false);
          })
          .catch((cause) => onError(readableError(cause)));
      }}
      onCancel={() => {
        setAdding(false);
        setUncertain(false);
      }}
      onSave={(body) =>
        void work(() =>
          inserting
            ? insertStep(program.id, inserting, {
                ...body,
                title: body.title || "New step",
              })
            : planProgram(
                program.id,
                [{ ...body, title: body.title || "New step" }],
                false,
              ),
        )
      }
      busy={busy}
    />
  ) : step ? (
    question ? (
      <InspectorQuestion
        actionId={question}
        targetId={bindingId(program, step.id)}
        question={`${question === "remove" ? "Remove" : "Skip"} ${step.title}?`}
        cancel={() => setQuestion(null)}
        keeps={["The other steps"]}
        verb={{
          label: question === "remove" ? "Remove step" : "Skip",
          busy,
          run: () =>
            void work(async () =>
              question === "skip"
                ? decide(program.id, step.id, {
                    kind: "parked",
                    choice: "skip",
                    binding: answerBinding(program, step.id),
                  })
                : removeProgramStep(
                    program.id,
                    step.id,
                    answerBinding(program, step.id),
                  ),
            ),
        }}
      />
    ) : handing ? (
      <StepEditor
        key={`${step.id}:hand`}
        handoffOnly
        step={step}
        program={program}
        busy={busy}
        onCancel={() => setHanding(false)}
        onSave={(body) =>
          void work(() =>
            handoff(program.id, step.id, {
              profile: body.profile || step.profile || "claude-default",
              engine: body.engine || null,
            }),
          )
        }
      />
    ) : editing ? (
      <StepEditor
        key={`${step.id}:${amending}`}
        amendOnly={amending}
        step={step}
        program={program}
        busy={busy}
        onCancel={() => setEditing(false)}
        onSave={(body) =>
          void work(() =>
            amending
              ? amendStep(program.id, step.id, body.brief || "")
              : changeStep(program.id, step.id, body),
          )
        }
      />
    ) : (
      <PaneInspector label={step.title} onClose={() => onSelect("")}>
        <InspectorFacts
          name={step.title}
          rows={
            part === "gate"
              ? [
                  {
                    label: "Check",
                    value:
                      step.check.command || (step.gate.check ? "On" : "Off"),
                  },
                  { label: "Review", value: step.gate.review },
                  {
                    label: "Merge",
                    value: step.gate.merge || "Program rule",
                  },
                  { label: "Rounds", value: step.rounds },
                ]
              : part === "report"
                ? [
                    {
                      label: "Observed",
                      value:
                        step.report?.observed
                          .map((row) => row.line)
                          .join(" · ") || step.last_checkpoint?.line,
                    },
                    {
                      label: "Agent said",
                      value:
                        step.report_text ||
                        step.report?.claimed.map((row) => row.line).join(" · "),
                    },
                    {
                      label: "Not checked",
                      value: step.report?.not_checked
                        .map((row) => row.line)
                        .join(" · "),
                    },
                    {
                      label: "Files",
                      value: step.report?.files.join(" · "),
                    },
                  ]
                : [
                    { label: "Brief", value: step.brief },
                    { label: "Owns", value: step.owns.join(" · ") },
                    {
                      label: "Check",
                      value:
                        step.check.command ||
                        (step.gate.check ? "Program check" : "No check"),
                    },
                    { label: "Agent", value: result?.agent },
                    { label: "State", value: result?.state_word },
                    ...(step.race > 1
                      ? [{ label: "Contenders", value: step.race }]
                      : []),
                    {
                      label: "Requirement",
                      value:
                        step.requirements?.map((row) => row.text).join(" · ") ||
                        "The step brief",
                    },
                  ]
          }
        />
      </PaneInspector>
    )
  ) : null;
  if (adding || editing || handing || question)
    return (
      <SegmentedTabs
        label="Step view"
        value={part}
        onChange={setPart}
        tabs={tabs}
      >
        {detail}
      </SegmentedTabs>
    );
  return (
    <SegmentedTabs
      label="Step view"
      value={part}
      onChange={setPart}
      tabs={tabs}
    >
      <ListPane
        label="Selected step"
        list={
          <ListView
            label="Steps"
            headerless
            ordered
            rows={program.steps.map((row) => ({
              id: row.id,
              kind: "program",
              name: row.title,
              detail: `${stepResult(row).agent} · ${row.requirements_met ? `${row.requirements_met.met} of ${row.requirements_met.total} met` : stepResult(row).state_word}`,
              leadingLamp: {
                state: liveLamp(stepResult(row).state),
                label: stepResult(row).state_word,
              },
            }))}
            columns={[{ key: "name", word: "Step" }]}
            verbs={verbs}
            selectedId={step?.id}
            onSelect={(id) => {
              onSelect(id);
              setHanding(false);
              setInserting(null);
              setEditing(false);
              setQuestion(null);
              setAdding(false);
            }}
            onOpen={() => setEditing(true)}
            toolbar={{}}
          />
        }
      >
        {detail}
      </ListPane>
    </SegmentedTabs>
  );
}
function StepEditor({
  step,
  program,
  onSave,
  onCancel,
  busy,
  handoffOnly = false,
  amendOnly = false,
  uncertain = false,
  onRead,
}: {
  step?: ProgramStep;
  program: Program;
  onSave(body: StepChangeBody & { origin_ref?: string }): void;
  onCancel(): void;
  busy: boolean;
  handoffOnly?: boolean;
  amendOnly?: boolean;
  uncertain?: boolean;
  onRead?(): void;
}) {
  const [part, setPart] = useState("brief"),
    [title, setTitle] = useState(step?.title ?? ""),
    [brief, setBrief] = useState(amendOnly ? "" : (step?.brief ?? "")),
    [owns, setOwns] = useState(step?.owns.join("\n") ?? ""),
    [after, setAfter] = useState(step?.after.join(", ") ?? ""),
    [effort, setEffort] = useState(step?.effort ?? "medium"),
    [carry, setCarry] = useState(false);
  const [agent, setAgent] = useState<RunsOnChoice>({
    profile: step?.profile || program.default.profile || "claude-default",
    engine: step?.engine?.id ?? null,
  });

  const [check, setCheck] = useState(step?.gate.check ?? true),
    [review, setReview] = useState(step?.gate.review ?? "none"),
    [merge, setMerge] = useState(step?.gate.merge ?? "level");
  const can = (field: string) =>
    !step || Boolean(step.editable?.includes(field));
  const body = (): StepChangeBody & { origin_ref?: string } =>
    handoffOnly
      ? { profile: agent.profile, engine: agent.engine }
      : amendOnly
        ? { brief }
        : {
            ...(can("title") ? { title } : {}),
            ...(can("brief") ? { brief } : {}),
            ...(can("owns")
              ? {
                  owns: owns
                    .split("\n")
                    .map((s) => s.trim())
                    .filter(Boolean),
                }
              : {}),
            ...(can("after")
              ? { after: after.split(/[, ]+/).filter(Boolean).map(Number) }
              : {}),
            ...(can("effort")
              ? { effort: effort as "low" | "medium" | "high" }
              : {}),
            ...(can("agent")
              ? { profile: agent.profile, engine: agent.engine }
              : {}),
            ...(can("gate_check") ? { gate_check: check } : {}),
            ...(can("gate_review")
              ? { gate_review: review as "none" | "agent" | "person" }
              : {}),
            ...(can("gate_merge")
              ? { gate_merge: merge as "level" | "owner" | "none" }
              : {}),
            ...(!step && carry && program.origin_ref?.startsWith("action:")
              ? { origin_ref: program.origin_ref }
              : {}),
          };
  const facts = (field: string, value: string) =>
    `${value}${step?.frozen?.[field] ? ` · ${step.frozen[field]}` : ""}`;
  return (
    <PaneInspector
      label={
        handoffOnly
          ? "Hand off"
          : amendOnly
            ? "Amend brief"
            : step
              ? "Edit step"
              : "Add step"
      }
    >
      <SegmentedTabs
        label="Step form"
        value={part}
        onChange={setPart}
        tabs={
          handoffOnly || amendOnly
            ? [{ id: "brief", label: handoffOnly ? "Agent" : "Brief" }]
            : [
                { id: "brief", label: "Step" },
                { id: "work", label: "Work" },
                { id: "gates", label: "Gates" },
              ]
        }
      >
        <InspectorForm
          rows={
            handoffOnly
              ? [
                  {
                    label: "Agent",
                    control: (
                      <RunsOnPicker
                        label="Step agent"
                        value={agent}
                        onPick={setAgent}
                      />
                    ),
                  },
                ]
              : amendOnly
                ? [
                    { label: "Sent brief", control: step?.brief },
                    {
                      label: "Add to brief",
                      control: (
                        <PadGadget
                          label="Step brief"
                          value={brief}
                          onChange={setBrief}
                        />
                      ),
                    },
                  ]
                : part === "brief"
                  ? [
                      {
                        label: "Name",
                        control: can("title") ? (
                          <StringGadget
                            label="Step name"
                            value={title}
                            onChange={setTitle}
                          />
                        ) : (
                          facts("title", title)
                        ),
                      },
                      {
                        label: "Brief",
                        control: can("brief") ? (
                          <PadGadget
                            label="Step brief"
                            value={brief}
                            onChange={setBrief}
                          />
                        ) : (
                          facts("brief", step?.brief ?? "")
                        ),
                      },
                      ...(!step && program.origin_ref?.startsWith("action:")
                        ? [
                            {
                              label: "Action",
                              control: (
                                <CheckGadget
                                  label="Carry the program action"
                                  checked={carry}
                                  onChange={setCarry}
                                />
                              ),
                            },
                          ]
                        : []),
                    ]
                  : part === "work"
                    ? [
                        {
                          label: "Agent",
                          control: can("agent") ? (
                            <RunsOnPicker
                              label="Step agent"
                              value={agent}
                              onPick={setAgent}
                            />
                          ) : (
                            facts("agent", step?.agent ?? "")
                          ),
                        },
                        {
                          label: "Owns",
                          control: can("owns") ? (
                            <PadGadget
                              label="Owned files"
                              value={owns}
                              onChange={setOwns}
                            />
                          ) : (
                            facts("owns", owns)
                          ),
                        },
                        {
                          label: "After",
                          control: can("after") ? (
                            <StringGadget
                              label="After step numbers"
                              value={after}
                              onChange={setAfter}
                            />
                          ) : (
                            facts("after", after)
                          ),
                        },
                        {
                          label: "Effort",
                          control: can("effort") ? (
                            <CycleGadget
                              label="Step effort"
                              value={effort}
                              options={[
                                { value: "low", label: "Low" },
                                { value: "medium", label: "Medium" },
                                { value: "high", label: "High" },
                              ]}
                              onChange={(v) =>
                                setEffort(v as "low" | "medium" | "high")
                              }
                            />
                          ) : (
                            facts("effort", effort)
                          ),
                        },
                      ]
                    : [
                        {
                          label: "Check",
                          control: can("gate_check") ? (
                            <CheckGadget
                              label="Run the check"
                              checked={check}
                              onChange={setCheck}
                            />
                          ) : (
                            facts("gate_check", check ? "On" : "Off")
                          ),
                        },
                        {
                          label: "Review",
                          control: can("gate_review") ? (
                            <CycleGadget
                              label="Step review"
                              value={review}
                              options={[
                                { value: "none", label: "No review" },
                                { value: "agent", label: "Agent review" },
                                { value: "person", label: "Person review" },
                              ]}
                              onChange={(v) =>
                                setReview(v as "none" | "agent" | "person")
                              }
                            />
                          ) : (
                            facts("gate_review", review)
                          ),
                        },
                        {
                          label: "Merge",
                          control: can("gate_merge") ? (
                            <CycleGadget
                              label="Step merge"
                              value={merge}
                              options={[
                                { value: "level", label: "Program rule" },
                                { value: "owner", label: "Ask you" },
                                { value: "none", label: "No merge" },
                              ]}
                              onChange={setMerge}
                            />
                          ) : (
                            facts("gate_merge", merge)
                          ),
                        },
                      ]
          }
          completion={{
            leading: uncertain ? (
              <Button variant="ghost" onClick={onRead}>
                Read the steps
              </Button>
            ) : undefined,
            cancel: onCancel,
            primary: {
              label: handoffOnly
                ? "Hand off"
                : amendOnly
                  ? "Amend brief"
                  : step
                    ? "Save"
                    : "Add step",
              busy,
              disabled:
                uncertain ||
                (amendOnly ? !brief.trim() : !handoffOnly && !title.trim()),
              run: () => onSave(body()),
            },
          }}
        />
      </SegmentedTabs>
    </PaneInspector>
  );
}
