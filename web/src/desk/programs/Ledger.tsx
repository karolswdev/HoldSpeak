import { useState } from "react";
import { programFailure as readableError } from "./liveModel";
import { openRef, openDecisionRecord } from "../openObject";
import {
  SegmentedTabs,
  streamTime,
  InspectorFacts,
  ListPane,
  ListView,
  type ListVerb,
} from "../surface";
import { ProgramContext, ProgramHandoffs } from "./ProgramRecords";
import { overturn, startFrom } from "./api";
import type { Program } from "./types";

/** The ledger, decisions, findings, family and lessons share selection grammar. */
export function ProgramLedger({
  program,
  onApplied,
  onError,
}: {
  program: Program;
  onApplied(next: Program | null): void;
  onError(words: string): void;
}) {
  const [part, setPart] = useState("ledger"),
    [picked, setPicked] = useState<string | null>(null);
  const rows =
    part === "family"
      ? [program.family?.parent, ...(program.family?.children ?? [])]
          .filter((row) => Boolean(row))
          .map((row) => ({
            id: row!.id,
            name: row!.name,
            detail: row!.line,
            at: "",
            source: row!,
          }))
      : part === "findings"
        ? (program.findings_board?.rows ?? []).map((row) => ({
            id: row.key,
            name: row.text,
            detail: row.words,
            at: "",
            source: row,
          }))
        : part === "decisions"
          ? (program.decided_for_you ?? []).map((row) => ({
              id: String(row.id),
              name: row.line,
              detail: row.rule ?? "",
              at: row.at,
              source: row,
            }))
          : program.checkpoints
              .filter((row) => part !== "lessons" || row.kind === "lesson")
              .map((row) => ({
                id: String(row.id),
                name: row.line,
                detail:
                  row.by === "owner"
                    ? "You"
                    : row.by === "engine"
                      ? "HoldSpeak"
                      : row.by,
                at: row.at,
                source: row,
              }));
  const finding = program.findings_board?.rows.find(
    (row) => row.key === picked,
  );
  const selected = rows.find((row) => row.id === picked);
  const checkpoint = program.checkpoints.find(
    (row) => String(row.id) === picked,
  );
  const decision = program.decided_for_you?.find(
    (row) => String(row.id) === picked,
  );
  const work = async (call: () => Promise<Program | null>) => {
    try {
      onApplied(await call());
    } catch (cause) {
      onError(readableError(cause));
    }
  };
  const verbs: ListVerb[] =
    part === "family"
      ? [
          {
            id: "open",
            label: "Open program",
            run: (row) => {
              if (row) openRef(`program:${row.id}`);
            },
          },
        ]
      : part === "findings"
        ? [
            {
              id: "door",
              label: "Open Door task",
              enabled: () => Boolean(finding?.task_id),
              run: () => {
                if (finding?.task_id) openRef(`action:${finding.task_id}`);
              },
            },
            {
              id: "fix",
              label: "Open fix program",
              enabled: () => Boolean(program.fix_program_id),
              run: () => {
                if (program.fix_program_id)
                  openRef(`program:${program.fix_program_id}`);
              },
            },
          ]
        : part === "decisions"
          ? [
              {
                id: "overturn",
                label: "Overturn",
                enabled: () =>
                  Boolean(decision?.overturnable && !decision.overturned_at),
                run: () => void work(() => overturn(program.id, picked!)),
              },
            ]
          : [
              {
                id: "start",
                label: "Start from here",
                enabled: () => Boolean(checkpoint?.ref),
                run: () => void work(() => startFrom(program.id, picked!)),
              },
            ];
  verbs.push({
    id: "decision",
    label: "Open decision",
    enabled: () =>
      Boolean(checkpoint?.decision_record_id) && !decision?.overturned_at,
    run: () => {
      if (checkpoint?.decision_record_id)
        openDecisionRecord(checkpoint.decision_record_id);
    },
  });
  return (
    <SegmentedTabs
      label="Ledger view"
      value={part}
      onChange={(id) => {
        setPart(id);
        setPicked(null);
      }}
      tabs={[
        { id: "ledger", label: "Ledger" },
        { id: "decisions", label: "Decisions" },
        { id: "findings", label: "Findings" },
        { id: "family", label: "Family" },
        { id: "lessons", label: "Lessons" },
        { id: "handoffs", label: "Handoffs" },
        { id: "context", label: "Context" },
      ]}
    >
      {part === "context" ? (
        <ProgramContext program={program} onError={onError} />
      ) : part === "handoffs" ? (
        <ProgramHandoffs program={program} />
      ) : (
        <ListPane
          label="Selected ledger entry"
          list={
            <ListView
              label="Program ledger"
              headerless
              ordered
              columns={[{ key: "name", word: "Entry" }]}
              rows={rows.map((row) => ({
                id: row.id,
                kind: "program",
                name: row.name,
                detail: row.detail,
              }))}
              selectedId={picked}
              onSelect={setPicked}
              verbs={verbs}
              toolbar={{}}
            />
          }
        >
          {selected ? (
            <InspectorFacts
              name="Entry"
              rows={[
                { label: "Words", value: selected.name },
                {
                  label: "Decision",
                  value:
                    checkpoint?.decision_record_id && !decision?.overturned_at
                      ? "Proposed as a decision"
                      : undefined,
                },
                { label: "Pinned ref", value: checkpoint?.ref },
                {
                  label: part === "findings" ? "Priority" : "By",
                  value: selected.detail,
                },
                { label: "Evidence", value: finding?.evidence.join(" · ") },
                { label: "Steps", value: finding?.steps.join(", ") },
                {
                  label: "When",
                  value: selected.at ? clock(selected.at) : undefined,
                },
              ]}
            />
          ) : null}
        </ListPane>
      )}
    </SegmentedTabs>
  );
}
export function clock(at: string) {
  const date = new Date(at);
  return Number.isFinite(date.getTime()) ? streamTime(date) : "";
}
