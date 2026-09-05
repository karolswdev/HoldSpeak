// HS-172 — the detail's NEEDS YOU section.
// Board: caption `NEEDS YOU 3` with optional `Run intelligence` at trailing.
// Each row: Decide:/Confirm: prefix (accent) + text + verbs.
// UX-CANON A.8: when zero rows AND not OFF-with-words, the section is ABSENT.
// HS-172: QUEUED/FAILED verbs (Skip, Retry) in the header verb slot.
import { Button } from "../../../components/signal/Signal";
import { countLabel } from "../../../desk/surface";
import type { NeedsRow } from "./helpers";

export function NeedsYouTable({
  needsRows,
  needsCount,
  intelOff,
  intelState,
  hasTranscript,
  onRunIntelligence,
  onRetryIntelligence,
  onSkipIntelligence,
}: {
  needsRows: NeedsRow[];
  needsCount: number;
  intelOff: boolean;
  /** The raw intel state string: "disabled", "queued", "running", "error", "failed", "complete". */
  intelState?: string;
  hasTranscript: boolean;
  onRunIntelligence?: () => void;
  onRetryIntelligence?: () => void;
  onSkipIntelligence?: () => void;
}) {
  const showRunIntel = intelOff && hasTranscript && Boolean(onRunIntelligence);
  const isFailed = intelState === "error" || intelState === "failed";
  const isQueued = intelState === "queued" || intelState === "pending";
  const showRetry = isFailed && Boolean(onRetryIntelligence);
  const showSkip = (isFailed || isQueued) && Boolean(onSkipIntelligence);
  const hasVerbs = showRunIntel || showRetry || showSkip;

  if (needsRows.length === 0 && !hasVerbs) return null;

  return (
    <div className="meetings-detail-needs" data-testid="meeting-needs-you">
      <div className="meetings-detail-needs-head">
        <span className="surface-caption">
          {countLabel("NEEDS YOU", needsCount)}
        </span>
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
        {showRetry ? (
          <Button
            dense
            variant="ghost"
            onClick={onRetryIntelligence}
            data-testid="detail-retry-btn"
          >
            Retry
          </Button>
        ) : null}
        {showSkip ? (
          <Button
            dense
            variant="ghost"
            onClick={onSkipIntelligence}
            data-testid="detail-skip-btn"
          >
            Skip
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
