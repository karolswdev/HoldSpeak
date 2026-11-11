import { useState } from "react";
import { FoldGadget, ListView } from "../surface";
import { openDecisionRecord } from "../openObject";
import type { RoomProposedDecision } from "../../features/project-room/model";
export function proposedFrom(row: RoomProposedDecision): string {
  const prs = row.prs
    .map((pr) => (pr.number != null ? `PR #${pr.number}` : "PR"))
    .join(", ");
  return [row.program.title, prs].filter(Boolean).join(" · ");
}

export function RoomDecisions({
  proposed,
}: {
  proposed: readonly RoomProposedDecision[];
}) {
  const [picked, setPicked] = useState<string | null>(null);
  return proposed.length ? (
    <FoldGadget title="Proposed decisions" open>
      <ListView
        label="Proposed decisions"
        headerless
        rows={proposed.map((row) => ({
          id: row.id,
          kind: "decision",
          name: row.text,
          detail: proposedFrom(row),
          leadingLamp: { state: "waiting", label: "Proposed" },
        }))}
        columns={[{ key: "name", word: "Decision" }]}
        selectedId={picked}
        onSelect={setPicked}
        onOpen={openDecisionRecord}
        verbs={[
          {
            id: "open",
            label: "Open decision",
            run: (row) => {
              if (row) openDecisionRecord(row.id);
            },
          },
        ]}
      />
    </FoldGadget>
  ) : null;
}
