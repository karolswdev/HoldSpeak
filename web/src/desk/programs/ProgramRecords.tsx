import { ProgramBriefing } from "./ProgramBriefing";
import { useState } from "react";
import { openRef } from "../openObject";
import { openPhoneWing } from "../calls/phoneFocus";
import {
  CycleGadget,
  PaneNotice,
  InspectorFacts,
  InspectorBody,
  InspectorForm,
  CheckGadget,
  StringGadget,
  InspectorQuestion,
  ListPane,
  ListView,
  PaneInspector,
  TextPane,
  streamTime,
} from "../surface";
import {
  bindingId,
  answerBinding,
  liveLamp,
  programFailure,
} from "./liveModel";
import { decide, race, planProgram, refreshProgram } from "./api";
import { RunsOnPicker, type RunsOnChoice } from "./RunsOn";
import type { Program, ProgramStep } from "./types";

export function ProgramRace({
  program,
  step,
  creating,
  selectedChild,
  onCreated,
  onApplied,
  onError,
}: {
  program: Program;
  step: ProgramStep | null;
  creating: boolean;
  selectedChild?: string | null;
  onCreated(): void;
  onApplied(next: Program | null): void;
  onError(words: string): void;
}) {
  const [n, setN] = useState("2"),
    [busy, setBusy] = useState(false),
    [picked, setPicked] = useState<string | null>(selectedChild ?? null);
  const [confirm, setConfirm] = useState(false),
    [note, setNote] = useState("");
  const contenders =
    step?.race && step.race > 1
      ? [step, ...(step.contenders ?? [])]
      : program.steps.filter(
          (row) => row.race_of === (step?.race_of || step?.id),
        );
  const row = contenders.find((item) => item.id === picked);
  const work = async (call: () => Promise<Program | null>) => {
    if (busy) return;
    setBusy(true);
    try {
      onApplied(await call());
      onCreated();
    } catch (e) {
      onError(programFailure(e));
    } finally {
      setBusy(false);
    }
  };
  if (creating && step)
    return (
      <PaneInspector label="Race step">
        <InspectorForm
          rows={[
            { label: "Step", control: step.title },
            {
              label: "Contenders",
              control: (
                <CycleGadget
                  label="Race contenders"
                  value={n}
                  options={[
                    { value: "2", label: "Two agents" },
                    { value: "3", label: "Three agents" },
                  ]}
                  onChange={setN}
                />
              ),
            },
          ]}
          completion={{
            cancel: onCreated,
            primary: {
              label: "Start race",
              busy,
              run: () => void work(() => race(program.id, step.id, Number(n))),
            },
          }}
        />
      </PaneInspector>
    );
  return (
    <ListPane
      label="Selected contender"
      list={
        <ListView
          label="Race contenders"
          headerless
          rows={contenders.map((item) => ({
            id: item.id,
            kind: "program",
            name: item.title,
            detail: `${item.agent} · ${item.state_word}`,
            leadingLamp: {
              state: liveLamp(item.state),
              label: item.state_word,
            },
          }))}
          columns={[{ key: "name", word: "Contender" }]}
          selectedId={picked}
          onSelect={(id) => {
            setPicked(id);
            setConfirm(false);
          }}
          verbs={[
            {
              id: "pick",
              label: "Pick this one",
              enabled: () =>
                Boolean(
                  row &&
                  program.your_turn_items.some(
                    (item) => item.kind === "race" && item.step_id === row.id,
                  ),
                ),
              run: () => setConfirm(true),
            },
          ]}
          toolbar={{}}
        />
      }
    >
      {row && confirm ? (
        <InspectorQuestion
          actionId="pick-contender"
          targetId={bindingId(program, row.id)}
          question={`Pick ${row.agent}?`}
          rows={[
            {
              label: "Note",
              control: (
                <StringGadget
                  label="Race answer note"
                  value={note}
                  onChange={setNote}
                />
              ),
            },
          ]}
          cancel={() => setConfirm(false)}
          verb={{
            label: "Pick this one",
            busy,
            run: () =>
              void work(() =>
                decide(program.id, row.id, {
                  kind: "race",
                  choice: "pick",
                  reason: note,
                  binding: answerBinding(program, row.id),
                }),
              ),
          }}
        />
      ) : row ? (
        <InspectorFacts
          name="Contender"
          rows={[
            { label: "Agent", value: row.agent },
            { label: "State", value: row.state_word },
            { label: "Check", value: row.check.verdict },
            { label: "Brief", value: row.brief },
            {
              label: "Result",
              value: row.report_text || row.last_checkpoint?.line,
            },
            { label: "PR", value: row.pr?.url },
          ]}
        />
      ) : (
        <PaneNotice>Select a contender to read its result.</PaneNotice>
      )}
    </ListPane>
  );
}
export function ProgramHandoffs({
  program,
  step,
}: {
  program: Program;
  step?: ProgramStep | null;
}) {
  const rows = (step ? [step] : program.steps).flatMap((s) =>
    (s.handoffs ?? []).map((row, i) => ({
      ...row,
      id: `${s.id}:${i}`,
      step: s.title,
    })),
  );
  const [picked, setPicked] = useState<string | null>(rows[0]?.id ?? null);
  const row = rows.find((item) => item.id === picked);
  return (
    <ListPane
      label="Selected handoff"
      list={
        <ListView
          label="Agent handoffs"
          headerless
          rows={rows.map((item) => ({
            id: item.id,
            kind: "program",
            name: `${item.from} to ${item.to}`,
            detail: `${item.step} · ${streamTime(new Date(item.at))}`,
          }))}
          columns={[{ key: "name", word: "Handoff" }]}
          selectedId={picked}
          onSelect={setPicked}
          toolbar={{}}
        />
      }
    >
      {row ? (
        <PaneInspector label="Handoff">
          <InspectorBody>
            <InspectorFacts
              name="Handoff"
              rows={[
                { label: "Reason", value: row.reason.replaceAll("_", " ") },
                {
                  label: "Redacted",
                  value: row.redacted_words || "Nothing redacted",
                },
                { label: "Earlier turns", value: row.earlier_turns },
                {
                  label: "Continues from",
                  value: row.continues_from || row.launch_from,
                },
              ]}
            />
            <TextPane
              onChange={() => {}}
              fill
              label="Handoff brief"
              data-feedback-redact="true"
              lines={row.brief
                .split("\n")
                .map((text) => ({ text, readOnly: true }))}
            />
          </InspectorBody>
        </PaneInspector>
      ) : null}
    </ListPane>
  );
}
export function ProgramContext({
  program,
  onError,
}: {
  program: Program;
  onError(words: string): void;
}) {
  const rows = [
    ...(program.place.project
      ? [
          {
            id: `project:${program.place.project.id}`,
            name: program.place.project.name,
            detail: "Project",
          },
        ]
      : []),
    ...(program.place.origin
      ? [
          {
            id: program.place.origin.ref,
            name: program.place.origin.title,
            detail: "Source",
          },
        ]
      : []),
    ...(program.place.person
      ? [
          {
            id: `person:${program.place.person.id}`,
            name: program.place.person.name,
            detail: "Person",
          },
        ]
      : []),
    ...(program.note_id
      ? [
          {
            id: `note:${program.note_id}`,
            name: "Program note",
            detail: "Note",
          },
        ]
      : []),
  ];
  rows.push(
    ...program.your_turn_items.map((item) => ({
      id: `question:${item.id}`,
      name: item.title,
      detail: "Briefing page",
    })),
  );
  const [picked, setPicked] = useState<string | null>(null);
  const question = program.your_turn_items.find(
    (item) => `question:${item.id}` === picked,
  );
  const reach = [...(program.decided_for_you ?? [])]
    .reverse()
    .find((row) => row.kind === "reach");
  return (
    <ListPane
      label="Program context"
      list={
        <ListView
          label="Context doors"
          headerless
          rows={rows.map((row) => ({ ...row, kind: "program" }))}
          columns={[{ key: "name", word: "Context" }]}
          selectedId={picked}
          onSelect={setPicked}
          onOpen={(id) => {
            if (!id.startsWith("question:")) openRef(id);
          }}
          verbs={[
            {
              id: "open",
              label: "Open context",
              enabled: () => Boolean(picked && !question),
              run: (row) => {
                if (row) openRef(row.id);
              },
            },
            {
              id: "thread",
              label: "Open thread",
              enabled: () => Boolean(reach),
              run: () => openPhoneWing(),
            },
          ]}
          toolbar={{}}
        />
      }
    >
      {question ? (
        <ProgramBriefing
          key={question.id}
          program={program}
          item={question}
          onError={onError}
        />
      ) : reach ? (
        <InspectorFacts
          name="Reach"
          rows={[
            { label: "Reach", value: reach.line },
            { label: "When", value: streamTime(new Date(reach.at)) },
            { label: "Rule", value: reach.rule },
          ]}
        />
      ) : null}
    </ListPane>
  );
}

export function ProgramBulkAgents({
  program,
  onApplied,
  onError,
}: {
  program: Program;
  onApplied(next: Program | null): void;
  onError(words: string): void;
}) {
  const [choice, setChoice] = useState<RunsOnChoice>({
      profile: program.default.profile || "claude-default",
      engine: program.default.engine?.id ?? null,
    }),
    [busy, setBusy] = useState(false),
    [failed, setFailed] = useState("");
  const carries = (p: Program) =>
    p.origin_ref?.startsWith("action:") ||
    p.steps.some((s) => s.origin_ref?.startsWith("action:"));
  const save = async () => {
    if (busy) return;
    setBusy(true);
    try {
      const fresh = await refreshProgram(program.id);
      onApplied(fresh);
      if (fresh.state !== "drafting" || carries(fresh)) {
        setFailed(
          carries(fresh)
            ? "The steps carry an action. Change the agent in each step's brief."
            : "The program started. No step changed.",
        );
        return;
      }
      onApplied(
        await planProgram(
          fresh.id,
          fresh.steps.map((s) => ({
            title: s.title,
            brief: s.brief,
            owns: s.owns,
            after: s.after,
            effort: s.effort ?? undefined,
            prefer_idle: s.prefer_idle,
            race: s.race || undefined,
            profile: choice.profile,
            engine: choice.engine,
            gate_check: s.gate.check,
            gate_review: s.gate.review,
            gate_merge: s.gate.merge as "level" | "owner" | "none",
          })),
          true,
        ),
      );
    } catch (e) {
      setFailed(programFailure(e));
      onError(programFailure(e));
    } finally {
      setBusy(false);
    }
  };
  return (
    <PaneInspector label="Change agents">
      <InspectorForm
        rows={[
          {
            label: "For every step",
            control: (
              <RunsOnPicker
                label="Agent for all steps"
                value={choice}
                onPick={setChoice}
              />
            ),
          },
          {
            label: "Steps",
            control: program.steps.map((s) => s.title).join(" · "),
          },
        ]}
        notice={failed || undefined}
        completion={{
          cancel: () =>
            setChoice({
              profile: program.default.profile || "claude-default",
              engine: program.default.engine?.id ?? null,
            }),
          primary: {
            label: "Change all agents",
            busy,
            disabled: program.state !== "drafting" || Boolean(carries(program)),
            run: () => void save(),
          },
        }}
      />
    </PaneInspector>
  );
}
