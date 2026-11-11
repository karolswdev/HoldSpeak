import { useState } from "react";
import { programFailure as readableError } from "./liveModel";
import { openRef } from "../openObject";
import {
  CycleGadget,
  InspectorFacts,
  ListPane,
  ListView,
  type ListVerb,
} from "../surface";
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
                detail: row.by,
                at: row.at,
                source: row,
              }));
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
  return (
    <ListPane
      label="Selected ledger entry"
      list={
        <ListView
          label="Program ledger"
          headerless
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
          toolbar={{
            trailing: (
              <CycleGadget
                label="Ledger section"
                value={part}
                options={[
                  { value: "ledger", label: "Ledger" },
                  { value: "decisions", label: "Decisions" },
                  { value: "findings", label: "Findings" },
                  { value: "family", label: "Family" },
                  { value: "lessons", label: "Lessons" },
                ]}
                onChange={(id) => {
                  setPart(id);
                  setPicked(null);
                }}
              />
            ),
          }}
        />
      }
    >
      {selected ? (
        <InspectorFacts
          name="Entry"
          rows={[
            { label: "Words", value: selected.name },
            { label: "By", value: selected.detail },
            { label: "When", value: selected.at },
          ]}
        />
      ) : null}
    </ListPane>
  );
}
export function clock(at: string) {
  return new Date(at).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}
