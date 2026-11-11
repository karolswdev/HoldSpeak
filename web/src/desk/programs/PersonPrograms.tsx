import { useState } from "react";
import { ListView } from "../surface";
import { programRow } from "./liveModel";
import { openProgram } from "./open";
import type { PersonProgramRow } from "./types";
export function personProgramsOf(...sources: unknown[]): PersonProgramRow[] {
  for (const source of sources) {
    const rows = (source as { programs?: unknown } | null | undefined)
      ?.programs;
    if (Array.isArray(rows))
      return rows.filter((row): row is PersonProgramRow =>
        Boolean(row && typeof row === "object" && (row as PersonProgramRow).id),
      );
  }
  return [];
}

export function PersonPrograms({
  programs,
  name,
}: {
  programs: readonly PersonProgramRow[];
  name: string;
}) {
  const [picked, setPicked] = useState<string | null>(null);
  if (!programs.length) return null;
  const rows = programs.flatMap((row) => [
    { ...programRow(row), group: 0 },
    ...(row.to_show ?? []).map((step) => ({
      id: `${row.id}:${step.step_id}:show`,
      kind: "program",
      name: step.title,
      detail: `${row.title}${step.pr_number ? ` · Merged #${step.pr_number}` : ""}`,
      group: 1,
    })),
    ...(row.to_ask ?? []).map((step) => ({
      id: `${row.id}:${step.step_id}:ask`,
      kind: "program",
      name:
        step.kind === "ask_review"
          ? `Ask ${name} to review ${step.title}`
          : step.title,
      detail: row.title,
      group: 2,
    })),
  ]);
  const open = (id: string) => openProgram(id.split(":")[0]);
  return (
    <ListView
      label="Programs"
      data-testid="person-programs"
      headerless
      ordered
      rows={rows}
      groups={[
        { id: 0, label: "Programs" },
        { id: 1, label: "To show them" },
        { id: 2, label: "To ask" },
      ]}
      columns={[{ key: "name", word: "Program" }]}
      selectedId={picked}
      onSelect={setPicked}
      onOpen={open}
      verbs={[
        {
          id: "open",
          label: "Open program",
          run: (row) => {
            if (row) open(row.id);
          },
        },
      ]}
    />
  );
}
