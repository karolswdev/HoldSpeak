import { useRef, useState } from "react";
import { apiFetch } from "../../lib/api";
import { useDesk } from "../store";
import { DESK_APPLICATIONS } from "../applications";
import {
  CheckGadget,
  CycleGadget,
  PaneNotice,
  ImageWell,
  InspectorFacts,
  InspectorForm,
  InspectorQuestion,
  ListPane,
  ListView,
  PaneInspector,
  SegmentedTabs,
  TextPane,
  type ListVerb,
} from "../surface";
import { StringGadget } from "../surface";
import {
  addRequirement,
  editRequirement,
  decideRequirement,
  type RequirementChoice,
} from "./api";
import {
  answerBinding,
  bindingId,
  choiceWord,
  programFailure,
} from "./liveModel";
import { guessKind, requirementTone } from "./model";
import { useEvidenceImage } from "./ProgramShot";
import type {
  Program,
  ProgramStep,
  Requirement,
  RequirementKind,
} from "./types";

type Props = {
  program: Program;
  step: ProgramStep | null;
  onApplied(next: Program | null): void;
  onError(words: string): void;
};
export function ProgramRequirements({
  program,
  step,
  onApplied,
  onError,
}: Props) {
  const [picked, setPicked] = useState<string | null>(null),
    [form, setForm] = useState<"add" | "edit" | null>(null),
    [answer, setAnswer] = useState<string | null>(null),
    [line, setLine] = useState(""),
    [busy, setBusy] = useState(false),
    [log, setLog] = useState<string | null>(null);
  const note = useRef(line);
  note.current = line;
  const rows = [...(program.requirements ?? []), ...(step?.requirements ?? [])];
  const row = rows.find((item) => item.id === picked);
  const work = async (call: () => Promise<Program | null>) => {
    if (busy) return;
    setBusy(true);
    try {
      onApplied(await call());
      setAnswer(null);
      setForm(null);
      setLine("");
      onError("");
    } catch (e) {
      onError(programFailure(e));
    } finally {
      setBusy(false);
    }
  };
  const verbs: ListVerb[] = [
    {
      id: "add",
      label: "Add requirement",
      enabled: () => !program.closed_at,
      run: () => setForm("add"),
    },
    {
      id: "edit",
      label: "Edit requirement",
      enabled: () =>
        Boolean(
          row &&
          !program.closed_at &&
          row.state !== "waived" &&
          !program.steps.find((step) => step.id === row.step_id)?.frozen
            ?.requirements,
        ),
      run: () => setForm("edit"),
    },
    ...(row?.choices ?? []).map((choice) => ({
      id: choice,
      label: choiceWord(choice),
      run: () => setAnswer(choice),
    })),
    {
      id: "shot",
      label: "Open shot",
      enabled: () => row?.evidence.kind === "shot" && Boolean(row.evidence.url),
      run: () => {
        if (row)
          useDesk
            .getState()
            .openPullout(`program-shot:${program.id}:${row.id}`);
      },
    },
    {
      id: "log",
      label: "Open log",
      enabled: () => row?.evidence.kind === "log" && Boolean(row.evidence.url),
      run: () => {
        if (row?.evidence.url)
          void apiFetch<string>(row.evidence.url, {
            headers: { Accept: "text/plain" },
          })
            .then((text) =>
              setLog(
                typeof text === "string" ? text : JSON.stringify(text, null, 2),
              ),
            )
            .catch((e) => onError(programFailure(e)));
      },
    },
  ];
  if (form)
    return (
      <RequirementEditor
        key={`${form}:${row?.id ?? step?.id}`}
        program={program}
        step={step}
        row={form === "edit" ? row : undefined}
        busy={busy}
        onCancel={() => setForm(null)}
        onSave={(body) =>
          void work(() =>
            form === "edit" && row
              ? editRequirement(program.id, row.id, body)
              : addRequirement(program.id, body),
          )
        }
      />
    );
  if (log !== null)
    return (
      <>
        <TextPane
          onChange={() => {}}
          fill
          label="Requirement log"
          lines={log.split("\n").map((text) => ({ text, readOnly: true }))}
        />
        <InspectorForm rows={[]} completion={{ done: () => setLog(null) }} />
      </>
    );
  return (
    <ListPane
      label="Selected requirement"
      list={
        <ListView
          label="Requirements"
          headerless
          ordered
          groups={[
            { id: 0, label: "The program" },
            { id: 1, label: "Every step" },
            { id: 2, label: step ? `Step ${step.ordinal}` : "Steps" },
          ]}
          columns={[{ key: "name", word: "Requirement" }]}
          rows={rows.map((item) => ({
            id: item.id,
            group:
              item.scope === "program"
                ? 0
                : item.scope === "every_step"
                  ? 1
                  : 2,
            kind: "program",
            name: item.text,
            detail: `${item.label} · ${item.scope === "program" ? "The program" : item.scope === "every_step" ? "Every step" : `Step ${step?.ordinal ?? ""}`} · ${item.state_word}`,
            leadingLamp: {
              state:
                requirementTone(item) === "ok"
                  ? "done"
                  : requirementTone(item) === "fail"
                    ? "off"
                    : item.state_word === "Waits for you"
                      ? "waiting"
                      : "off",
              label: item.state_word,
            },
          }))}
          selectedId={picked}
          onSelect={(id) => {
            setPicked(id);
            setAnswer(null);
          }}
          onOpen={() => setForm("edit")}
          verbs={verbs}
          toolbar={{}}
        />
      }
    >
      {row && answer ? (
        <InspectorQuestion
          actionId={`requirement:${row.id}:${answer}`}
          targetId={`${bindingId(program, row.step_id ?? "")}:${row.id}:${row.state}`}
          question={`${choiceWord(answer)} ${row.label}?`}
          cancel={() => setAnswer(null)}
          rows={[
            {
              label: "Answer note",
              control: (
                <StringGadget
                  label={
                    answer === "waive" ? "Why you waive it" : "Answer note"
                  }
                  value={line}
                  onChange={setLine}
                />
              ),
            },
          ]}
          verb={{
            label: choiceWord(answer),
            busy,
            disabled: answer === "waive" && !line.trim(),
            run: () =>
              void work(() =>
                decideRequirement(
                  program.id,
                  row.id,
                  answer as RequirementChoice,
                  note.current,
                  answerBinding(program, row.step_id ?? ""),
                ),
              ),
          }}
        />
      ) : row ? (
        <RequirementProof key={row.id} row={row} />
      ) : null}
    </ListPane>
  );
}
function RequirementProof({ row }: { row: Requirement }) {
  const [part, setPart] = useState(
    row.evidence.kind === "shot" ? "evidence" : "facts",
  );
  const image = useEvidenceImage(
    row.evidence.kind === "shot" ? row.evidence.url : undefined,
  );
  return (
    <SegmentedTabs
      label="Requirement view"
      value={part}
      onChange={setPart}
      tabs={
        row.evidence.kind === "shot"
          ? [
              { id: "evidence", label: "Evidence" },
              { id: "facts", label: "Facts" },
            ]
          : [{ id: "facts", label: "Facts" }]
      }
    >
      {part === "facts" ? (
        <InspectorFacts
          header={false}
          name="Requirement"
          rows={[
            { label: "Proof", value: row.evidence.line || row.kind_word },
            { label: "State", value: row.state_word },
            {
              label: "Judged on",
              value: row.evidence.commit || row.judged_commit,
            },
            { label: "Command", value: row.spec.command },
            {
              label: "Window",
              value:
                row.kind === "shot"
                  ? `${row.evidence.case ?? row.spec.case} at ${row.evidence.width ?? row.spec.width}`
                  : undefined,
            },
            { label: "Reason", value: row.waived_reason },
          ]}
        />
      ) : image.src ? (
        <ImageWell src={image.src} alt={`${row.label} evidence`} />
      ) : image.failed ? (
        <PaneNotice>
          The shot did not load. Use Open shot to try again.
        </PaneNotice>
      ) : null}
    </SegmentedTabs>
  );
}
function RequirementEditor({
  program,
  step,
  row,
  busy,
  onSave,
  onCancel,
}: {
  program: Program;
  step: ProgramStep | null;
  row?: Requirement;
  busy: boolean;
  onSave(body: Parameters<typeof addRequirement>[1]): void;
  onCancel(): void;
}) {
  const [text, setText] = useState(row?.text ?? ""),
    [kind, setKind] = useState<RequirementKind>(row?.kind ?? "review"),
    [chosen, setChosen] = useState(Boolean(row)),
    [scope, setScope] = useState(
      row?.step_id ??
        (step && !step.frozen?.requirements ? step.id : "program"),
    ),
    [required, setRequired] = useState(row?.required ?? true),
    [command, setCommand] = useState(row?.spec.command ?? ""),
    [shot, setShot] = useState(row?.spec.case ?? "people"),
    [width, setWidth] = useState(String(row?.spec.width ?? 393)),
    [part, setPart] = useState("sentence");
  const cannot =
    program.can_prove?.[kind] === false
      ? (kind === "shot" ? program.can_prove.shot_reason : undefined) ||
        "This repository cannot prove it."
      : "";
  const cases = DESK_APPLICATIONS.filter(
    (app) => !app.parked && app.windowId?.startsWith("surface-"),
  ).map((app) => ({ value: app.windowId!.slice(8), label: app.label }));
  return (
    <PaneInspector label={row ? "Edit requirement" : "Add requirement"}>
      <SegmentedTabs
        label="Requirement form"
        value={part}
        onChange={setPart}
        tabs={[
          { id: "sentence", label: "Requirement" },
          { id: "proof", label: "Proof" },
        ]}
      >
        <InspectorForm
          rows={
            part === "sentence"
              ? [
                  {
                    label: "Sentence",
                    control: (
                      <StringGadget
                        label="Requirement sentence"
                        value={text}
                        onChange={(value) => {
                          setText(value);
                          const guess = guessKind(value);
                          if (!chosen) setKind(guess.kind);
                          if (guess.command) setCommand(guess.command);
                          if (guess.case) setShot(guess.case);
                          if (guess.width) setWidth(String(guess.width));
                        }}
                      />
                    ),
                  },
                  {
                    label: "Kind",
                    control: (
                      <CycleGadget
                        label="Requirement kind"
                        value={kind}
                        options={[
                          { value: "check", label: "Check" },
                          { value: "review", label: "Review" },
                          { value: "shot", label: "Shot" },
                          { value: "word", label: "Your word" },
                        ]}
                        onChange={(value) => {
                          setKind(value as RequirementKind);
                          setChosen(true);
                        }}
                      />
                    ),
                  },
                  ...(!row
                    ? [
                        {
                          label: "Where",
                          control: (
                            <CycleGadget
                              label="Requirement scope"
                              value={scope}
                              options={[
                                { value: "program", label: "The program" },
                                { value: "every", label: "Every step" },
                                ...program.steps
                                  .filter(
                                    (s) =>
                                      !s.race_of && !s.frozen?.requirements,
                                  )
                                  .map((s) => ({
                                    value: s.id,
                                    label: `Step ${s.ordinal} · ${s.title}`,
                                  })),
                              ]}
                              onChange={setScope}
                            />
                          ),
                        },
                      ]
                    : []),
                  {
                    label: "Required",
                    control: (
                      <CheckGadget
                        label="Required"
                        checked={required}
                        onChange={setRequired}
                      />
                    ),
                  },
                ]
              : kind === "check"
                ? [
                    {
                      label: "Command",
                      control: (
                        <StringGadget
                          label="Requirement command"
                          value={command}
                          onChange={setCommand}
                        />
                      ),
                    },
                  ]
                : kind === "shot"
                  ? [
                      {
                        label: "Window",
                        control: (
                          <CycleGadget
                            label="Shot window"
                            value={shot}
                            options={[
                              ...cases,
                              { value: "program", label: "A program" },
                            ]}
                            onChange={setShot}
                          />
                        ),
                      },
                      {
                        label: "Width",
                        control: (
                          <CycleGadget
                            label="Shot width"
                            value={width}
                            options={[
                              { value: "393", label: "393" },
                              { value: "1440", label: "1440" },
                            ]}
                            onChange={setWidth}
                          />
                        ),
                      },
                    ]
                  : [
                      {
                        label: "Proof",
                        control:
                          kind === "word"
                            ? "Your answer"
                            : "The reviewer's finding",
                      },
                    ]
          }
          notice={cannot || undefined}
          completion={{
            cancel: onCancel,
            primary: {
              label: row ? "Save requirement" : "Add requirement",
              busy,
              disabled:
                !text.trim() ||
                Boolean(cannot) ||
                (kind === "check" && !command.trim()),
              run: () =>
                onSave({
                  text: text.trim(),
                  kind,
                  required,
                  ...(!row
                    ? scope === "every"
                      ? { each_step: true }
                      : scope !== "program"
                        ? { step_id: scope }
                        : {}
                    : {}),
                  spec:
                    kind === "check"
                      ? { command: command.trim() }
                      : kind === "shot"
                        ? { case: shot, width: Number(width) }
                        : {},
                }),
            },
          }}
        />
      </SegmentedTabs>
    </PaneInspector>
  );
}
