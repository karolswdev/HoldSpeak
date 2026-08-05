// HS-117-09 — extracted from MeetingDetail (lines 667-688 render).
import { GadgetTable } from "../../../desk/surface/gadgets";
import type { NeedsRow } from "./helpers";

export function NeedsYouTable({
  needsRows,
  needsCount,
  intelOff,
  hasOutcomes,
}: {
  needsRows: NeedsRow[];
  needsCount: number;
  intelOff: boolean;
  hasOutcomes: boolean;
}) {
  return (
    <div className="surface-outcome-sec">
      {intelOff && !hasOutcomes ? (
        <span className="surface-token">
          INTELLIGENCE OFF · NO OUTCOMES
        </span>
      ) : needsRows.length ? (
        <>
          <span className="surface-eyebrow">
            {`Needs you: ${needsCount}`}
          </span>
          <GadgetTable
            head={["ITEM", "FACTS"]}
            rows={needsRows.map((row) => row.cells)}
            verbs={(index) => needsRows[index].verbs}
          />
        </>
      ) : (
        <span className="surface-token">QUEUE 0</span>
      )}
    </div>
  );
}
