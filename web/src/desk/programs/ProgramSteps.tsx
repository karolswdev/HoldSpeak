import { useRef, useState } from "react";
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
  type ListVerb,
} from "../surface";
import {
  addRequirement,
  amendStep,
  changeStep,
  decide,
  decideRequirement,
  editRequirement,
  handLaneBack,
  handoff,
  insertStep,
  planProgram,
  race,
  removeProgramStep,
  takeLane,
  type RequirementChoice,
  type StepChangeBody,
} from "./api";
import { RunsOnPicker, type RunsOnChoice } from "./RunsOn";
import { ProgramInterview } from "./ProgramInterview";
import { answerBinding, bindingId, choiceWord, liveLamp } from "./liveModel";
import type { Program, ProgramStep, Requirement } from "./types";

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
  const [busy, setBusy] = useState(false),
    [part, setPart] = useState("brief");
  const step = program.steps.find((row) => row.id === selected) ?? null;
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
      onError(readableError(cause));
    } finally {
      setBusy(false);
    }
  };
  const move = (dir: number) => {
    if (!step) return;
    const steps = program.steps.filter((row) => !row.race_of),
      at = steps.findIndex((row) => row.id === step.id);
    const before = dir < 0 ? steps[at - 1]?.id : (steps[at + 2]?.id ?? "end");
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
      run: () => void work(() => race(program.id, step!.id, 2)),
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
      run: () => setEditing(true),
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
  if (part === "rounds" && step && !editing && !adding && !question && !handing)
    return (
      <ProgramInterview
        program={program}
        onApplied={onApplied}
        onError={onError}
        onClose={() => setPart("brief")}
      />
    );
  return (
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
            detail: `${row.agent} · ${row.requirements_met ? `${row.requirements_met.met} of ${row.requirements_met.total} met` : row.state_word}`,
            leadingLamp: { state: liveLamp(row.state), label: row.state_word },
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
      {adding ? (
        <StepEditor
          program={program}
          onCancel={() => setAdding(false)}
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
                    : removeProgramStep(program.id, step.id),
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
            key={step.id}
            step={step}
            program={program}
            busy={busy}
            onCancel={() => setEditing(false)}
            onSave={(body) =>
              void work(() =>
                step.editable?.includes("brief")
                  ? changeStep(program.id, step.id, body)
                  : amendStep(program.id, step.id, body.brief || ""),
              )
            }
          />
        ) : (
          <PaneInspector label={step.title} onClose={() => onSelect("")}>
            <StepFacts
              program={program}
              step={step}
              part={part}
              onPart={setPart}
              onApplied={onApplied}
              onError={onError}
            />
          </PaneInspector>
        )
      ) : null}
    </ListPane>
  );
}
function StepEditor({
  step,
  program,
  onSave,
  onCancel,
  busy,
  handoffOnly = false,
}: {
  step?: ProgramStep;
  program: Program;
  onSave(body: StepChangeBody): void;
  onCancel(): void;
  busy: boolean;
  handoffOnly?: boolean;
}) {
  const frozen = Boolean(step && !step.editable?.includes("brief"));
  const [title, setTitle] = useState(step?.title || ""),
    [brief, setBrief] = useState(frozen ? "" : step?.brief || "");
  const [owns, setOwns] = useState(step?.owns.join("\n") || ""),
    [after, setAfter] = useState(step?.after.join(", ") || "");
  const [agent, setAgent] = useState<RunsOnChoice>({
    profile: step?.profile || program.default.profile || "claude-default",
    engine: step?.engine?.id || null,
  });
  const [check, setCheck] = useState(step?.gate.check ?? true),
    [review, setReview] = useState(step?.gate.review ?? "none"),
    [merge, setMerge] = useState(step?.gate.merge ?? "level");
  const can = (field: string) =>
    !step || Boolean(step.editable?.includes(field));
  const body = (): StepChangeBody =>
    handoffOnly
      ? { profile: agent.profile, engine: agent.engine }
      : frozen
        ? { brief }
        : {
            title,
            brief,
            ...(can("agent")
              ? { profile: agent.profile, engine: agent.engine }
              : {}),
            ...(can("owns")
              ? {
                  owns: owns
                    .split("\n")
                    .map((row) => row.trim())
                    .filter(Boolean),
                }
              : {}),
            ...(can("after")
              ? { after: after.split(/[, ]+/).filter(Boolean).map(Number) }
              : {}),
            ...(can("gate_check") ? { gate_check: check } : {}),
            ...(can("gate_review")
              ? { gate_review: review as "none" | "agent" | "person" }
              : {}),
            ...(can("gate_merge")
              ? { gate_merge: merge as "level" | "owner" | "none" }
              : {}),
          };
  return (
    <PaneInspector
      label={handoffOnly ? "Hand off" : step ? "Edit step" : "Add step"}
    >
      <InspectorForm
        rows={[
          ...(!frozen && !handoffOnly
            ? [
                {
                  label: "Name",
                  control: (
                    <StringGadget
                      label="Step name"
                      value={title}
                      onChange={setTitle}
                    />
                  ),
                },
              ]
            : []),
          ...(!handoffOnly
            ? [
                {
                  label: frozen ? "Add to brief" : "Brief",
                  control: (
                    <PadGadget
                      label="Step brief"
                      value={brief}
                      onChange={setBrief}
                    />
                  ),
                },
              ]
            : []),
          ...(handoffOnly || can("agent")
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
            : []),
          ...(!frozen && !handoffOnly
            ? [
                ...(can("owns")
                  ? [
                      {
                        label: "Owns",
                        control: (
                          <PadGadget
                            label="Owned files"
                            value={owns}
                            onChange={setOwns}
                          />
                        ),
                      },
                    ]
                  : []),
                ...(can("after")
                  ? [
                      {
                        label: "After",
                        control: (
                          <StringGadget
                            label="After step numbers"
                            value={after}
                            onChange={setAfter}
                          />
                        ),
                      },
                    ]
                  : []),
                ...(can("gate_check")
                  ? [
                      {
                        label: "Check",
                        control: (
                          <CheckGadget
                            label="Run the check"
                            checked={check}
                            onChange={setCheck}
                          />
                        ),
                      },
                    ]
                  : []),
                ...(can("gate_review")
                  ? [
                      {
                        label: "Review",
                        control: (
                          <CycleGadget
                            label="Step review"
                            value={review}
                            options={[
                              { value: "none", label: "No review" },
                              { value: "agent", label: "Agent review" },
                              { value: "person", label: "Person review" },
                            ]}
                            onChange={(value) =>
                              setReview(value as "none" | "agent" | "person")
                            }
                          />
                        ),
                      },
                    ]
                  : []),
                ...(can("gate_merge")
                  ? [
                      {
                        label: "Merge",
                        control: (
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
                        ),
                      },
                    ]
                  : []),
              ]
            : []),
        ]}
        completion={{
          cancel: onCancel,
          primary: {
            label: handoffOnly
              ? "Hand off"
              : frozen
                ? "Amend brief"
                : step
                  ? "Save"
                  : "Add step",
            busy,
            disabled:
              !handoffOnly && (!brief.trim() || (!frozen && !title.trim())),
            run: () => onSave(body()),
          },
        }}
      />
    </PaneInspector>
  );
}
function StepFacts({
  program,
  step,
  part,
  onPart,
  onApplied,
  onError,
}: {
  program: Program;
  step: ProgramStep;
  part: string;
  onPart(id: string): void;
  onApplied(next: Program | null): void;
  onError(words: string): void;
}) {
  return (
    <InspectorForm
      rows={[
        {
          label: "Read",
          control: (
            <CycleGadget
              label="Step details"
              value={part}
              options={[
                { value: "brief", label: "Brief" },
                { value: "requirements", label: "Requirements" },
                { value: "gate", label: "Gate" },
                { value: "rounds", label: "Rounds" },
                { value: "report", label: "Report" },
                { value: "handoffs", label: "Handoffs" },
              ]}
              onChange={onPart}
            />
          ),
        },
        ...(part === "requirements"
          ? [
              {
                label: "Requirements",
                control: (
                  <StepRequirements
                    program={program}
                    step={step}
                    onApplied={onApplied}
                    onError={onError}
                  />
                ),
              },
            ]
          : part === "gate"
            ? [
                {
                  label: "Check",
                  control:
                    step.check.command || (step.gate.check ? "On" : "Off"),
                },
                { label: "Review", control: step.gate.review },
                { label: "Merge", control: step.gate.merge || "Program rule" },
                { label: "Rounds", control: step.rounds },
              ]
            : part === "rounds"
              ? [
                  {
                    label: "Rounds",
                    control: (
                      <ProgramInterview
                        program={program}
                        onApplied={onApplied}
                        onError={onError}
                      />
                    ),
                  },
                ]
              : part === "report"
                ? [
                    {
                      label: "Observed",
                      control:
                        step.report?.observed
                          .map((row) => row.line)
                          .join(" · ") || step.last_checkpoint?.line,
                    },
                    {
                      label: "Agent said",
                      control:
                        step.report_text ||
                        step.report?.claimed.map((row) => row.line).join(" · "),
                    },
                    {
                      label: "Not checked",
                      control: step.report?.not_checked
                        .map((row) => row.line)
                        .join(" · "),
                    },
                    { label: "Files", control: step.report?.files.join(" · ") },
                  ]
                : part === "handoffs"
                  ? (step.handoffs ?? []).map((row) => ({
                      label: row.to,
                      control: row.brief,
                    }))
                  : [
                      { label: "Brief", control: step.brief },
                      { label: "Owner", control: step.agent },
                      { label: "Owns", control: step.owns.join(" · ") },
                      { label: "After", control: step.after.join(", ") },
                      {
                        label: "What it must prove",
                        control:
                          step.requirements
                            ?.map((row) => row.text)
                            .join(" · ") ||
                          step.check.command ||
                          "The step brief",
                      },
                    ]),
      ]}
    />
  );
}
function StepRequirements({
  program,
  step,
  onApplied,
  onError,
}: {
  program: Program;
  step: ProgramStep;
  onApplied(next: Program | null): void;
  onError(words: string): void;
}) {
  const [picked, setPicked] = useState<string | null>(null),
    [answer, setAnswer] = useState<string | null>(null),
    [line, setLine] = useState(""),
    [busy, setBusy] = useState(false);
  const reason = useRef(line);
  reason.current = line;
  const rows = [...(program.requirements ?? []), ...(step.requirements ?? [])];
  const row = rows.find((row) => row.id === picked);
  const verbs: ListVerb[] =
    row?.choices.map((choice) => ({
      id: choice,
      label: choiceWord(choice),
      run: () => setAnswer(choice),
    })) ?? [];
  const press = async () => {
    if (!row || !answer || busy) return;
    setBusy(true);
    try {
      onApplied(
        await decideRequirement(
          program.id,
          row.id,
          answer as RequirementChoice,
          reason.current,
          answerBinding(program, row.step_id || ""),
        ),
      );
      setAnswer(null);
      setLine("");
    } catch (cause) {
      onError(readableError(cause));
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <ListView
        label="Requirements"
        headerless
        rows={rows.map((row) => ({
          id: row.id,
          kind: "program",
          name: row.text,
          detail: `${row.label} · ${row.state_word}`,
        }))}
        columns={[{ key: "name", word: "Requirement" }]}
        selectedId={picked}
        onSelect={(id) => {
          setPicked(id);
          setAnswer(null);
        }}
        verbs={verbs}
      />
      {row ? (
        <InspectorFacts
          name={row.label}
          rows={[
            { label: "Proof", value: row.evidence.line || row.kind_word },
            { label: "State", value: row.state_word },
          ]}
        />
      ) : null}
      {answer && row ? (
        <>
          <StringGadget label="Reason" value={line} onChange={setLine} />
          <InspectorQuestion
            targetId={`${bindingId(program, step.id)}:${row.id}`}
            question={`${choiceWord(answer)} ${row.label}?`}
            cancel={() => setAnswer(null)}
            verb={{
              label: choiceWord(answer),
              run: () => void press(),
              busy,
              disabled: answer === "waive" && !line.trim(),
            }}
          />
        </>
      ) : null}
    </>
  );
}
