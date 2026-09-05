// HS-170-04 — the detail's NEEDS YOU section.
// Board: caption `NEEDS YOU 3` with optional `Run intelligence` at trailing.
// Each row: outcome text + its verb (Decide / Open).
// UX-CANON A.8: when zero rows AND not OFF-with-words, the section is ABSENT.
import { Button } from "../../../components/signal/Signal";
import { countLabel } from "../../../desk/surface";
import type { NeedsRow } from "./helpers";

export function NeedsYouTable({
  needsRows,
  needsCount,
  intelOff,
  hasTranscript,
  onRunIntelligence,
}: {
  needsRows: NeedsRow[];
  needsCount: number;
  intelOff: boolean;
  hasTranscript: boolean;
  onRunIntelligence?: () => void;
}) {
  const showRunIntel = intelOff && hasTranscript && Boolean(onRunIntelligence);

  // Section absent when zero rows AND no Run intelligence verb
  if (needsRows.length === 0 && !showRunIntel) return null;

  return (
    <div className="meetings-detail-needs">
      <div className="meetings-detail-needs-head">
        <span className="surface-caption">
          {countLabel("NEEDS YOU", needsCount)}
        </span>
        {/* When OFF with transcript, Run intelligence at trailing edge */}
        {showRunIntel ? (
          <Button
            dense
            variant="primary"
            onClick={onRunIntelligence}
            data-testid="detail-run-intelligence-btn"
          >
            Run intelligence
          </Button>
        ) : null}
      </div>
      {needsRows.length > 0 ? (
        <ul className="meetings-detail-outcomes">
          {needsRows.map((row, i) => (
            <li key={i} className="meetings-detail-outcome-row">
              <span className="meetings-detail-outcome-text">{row.cells[0]}</span>
              <span className="meetings-detail-outcome-verb">{row.verbs}</span>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
