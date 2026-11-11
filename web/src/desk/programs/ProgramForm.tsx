import { useEffect, useState } from "react";
import { ApiError } from "../../lib/api";
import { programFailure as readableError } from "./liveModel";
import {
  CycleGadget,
  InspectorForm,
  PadGadget,
  PaneInspector,
  StringGadget,
} from "../surface";
import {
  createProgram,
  defaultProjectId,
  planDraft,
  readProjectChoices,
  readShapeEngine,
  shapeProgram,
  TEMPLATES,
  type ProjectChoice,
} from "./api";
import { answerBinding, bindingId, currentStep } from "./liveModel";
import { readControlMode } from "../hand/begin";
import { controlValue } from "./model";
import { RunsOnPicker, type RunsOnChoice } from "./RunsOn";
import { PersonPicker, type PersonChoice } from "./PersonPicker";
import { TextChanges, type ChangeProposal } from "./ProgramText";
import type { NewProgramPrefill } from "./newProgram";
import type { Control, Program } from "./types";

/** Creation and sentence planning keep the master list and one completion row. */
export function ProgramForm({
  kind,
  program,
  prefill,
  scopeProjectId,
  onCancel,
  onApplied,
}: {
  kind: "new" | "amend";
  program: Program | null;
  prefill?: NewProgramPrefill;
  scopeProjectId?: string;
  onCancel(): void;
  onApplied(next: Program | null): void;
}) {
  useEffect(() => {
    if (kind === "new")
      void readControlMode().then((value) => {
        if (value) setControl(controlValue(value));
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
  const [sentence, setSentence] = useState(""),
    [mode, setMode] = useState("amend"),
    [engine, setEngine] = useState<string | null>(null);
  const [busy, setBusy] = useState(false),
    [failed, setFailed] = useState(""),
    [unknown, setUnknown] = useState(false),
    [proposal, setProposal] = useState<ChangeProposal | null>(null);
  useEffect(() => {
    let active = true;
    void readProjectChoices()
      .then((rows) => {
        if (active) {
          setProjects(rows);
          setProject(defaultProjectId(rows, scopeProjectId));
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
        .catch(() => setEngine(null));
  }, [kind, program?.id]);
  const save = async () => {
    if (busy || unknown) return;
    setBusy(true);
    setFailed("");
    try {
      if (kind === "new")
        onApplied(
          await createProgram({
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
          }),
        );
      else if (program) {
        const answer =
          mode === "plan"
            ? await planDraft(program.id, { goal: sentence || program.goal })
            : await shapeProgram(program.id, { sentence, apply: false });
        const binding = answerBinding(program, currentStep(program)?.id);
        setProposal({
          answer,
          text: answer.proposed_text || answer.allowed_text,
          base: answer.base,
          binding,
          target: bindingId(program, binding.step_id),
        });
      }
    } catch (cause) {
      setFailed(readableError(cause));
      if (
        kind === "new" &&
        !(cause instanceof ApiError && [400, 409].includes(cause.status))
      )
        setUnknown(true);
    } finally {
      setBusy(false);
    }
  };
  if (proposal && program)
    return (
      <TextChanges
        program={program}
        proposal={proposal}
        onCancel={() => setProposal(null)}
        onApplied={onApplied}
        onError={setFailed}
      />
    );
  return (
    <PaneInspector label={kind === "new" ? "New program" : "Amend program"}>
      <InspectorForm
        rows={
          kind === "new"
            ? [
                {
                  label: "Name",
                  control: (
                    <StringGadget
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
                      label="Project"
                      value={project}
                      options={[
                        { value: "", label: "A folder on this machine" },
                        ...projects.map((row) => ({
                          value: row.id,
                          label: row.name,
                        })),
                      ]}
                      onChange={setProject}
                    />
                  ),
                },
                ...(!project
                  ? [
                      {
                        label: "Folder",
                        control: (
                          <StringGadget
                            label="Repository folder"
                            value={repository}
                            onChange={setRepository}
                          />
                        ),
                      },
                    ]
                  : []),
                {
                  label: "Template",
                  control: (
                    <CycleGadget
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
                {
                  label: "Control",
                  control: (
                    <CycleGadget
                      label="Control"
                      value={control}
                      options={[
                        { value: "yolo", label: "Runs by itself" },
                        {
                          value: "normal",
                          label: "Asks before it merges or sends",
                        },
                        { value: "secure", label: "Asks at every step" },
                      ]}
                      onChange={(id) => setControl(id as Control)}
                    />
                  ),
                },
                {
                  label: "Agent",
                  control: (
                    <RunsOnPicker
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
                      label="Choose reviewer"
                      value={reviewer}
                      onPick={setReviewer}
                    />
                  ),
                },
                {
                  label: "For",
                  control: <PersonPicker value={person} onPick={setPerson} />,
                },
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
              ]
            : [
                {
                  label: "Do",
                  control: (
                    <CycleGadget
                      label="Amend or plan"
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
                    <PadGadget
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
            : failed ||
              (readFailed
                ? "The projects did not load. Choose a folder."
                : undefined)
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
    </PaneInspector>
  );
}
