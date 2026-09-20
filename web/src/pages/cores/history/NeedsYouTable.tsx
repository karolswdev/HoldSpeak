// HS-172 — the detail's NEEDS YOU section.
// Board: caption `NEEDS YOU 3` with optional `Run summary` at trailing.
// Each row: Decide:/Confirm: prefix (accent) + text + verbs.
// UX-CANON A.8: when zero rows AND not OFF-with-words, the section is ABSENT.
// HS-172: QUEUED/FAILED verbs (Skip, Retry) in the header verb slot.
import { Button } from "../../../components/signal/Signal";
import { countLabel } from "../../../desk/surface";
import { RefusalToken, RouteDisclosure } from "../../../meetings/RouteDisclosure";
import {
  routeReady,
  type PlannedRoute,
  type RunReceipt,
  type SummaryRefusal,
} from "../../../meetings/summaryRoute";
import type { NeedsRow } from "./helpers";

export function NeedsYouTable({
  needsRows,
  needsCount,
  intelOff,
  intelState,
  hasTranscript,
  plannedRoute,
  refusal,
  durableRefusal,
  onReview,
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
  /** HS-201-04 — the disclosed route the next run will use (Article III). */
  plannedRoute?: PlannedRoute | null;
  /** HS-201-04 — the hub's 409 on this record's last run gesture. */
  refusal?: SummaryRefusal | null;
  /** HS-201-04 — the hub's own durable `last_refusal` receipt. */
  durableRefusal?: RunReceipt | null;
  /** HS-200-12 — proposals are reviewed on the Review wing; this is the way there. */
  onReview?: () => void;
  onRunIntelligence?: () => void;
  onRetryIntelligence?: () => void;
  onSkipIntelligence?: () => void;
}) {
  // HS-201-04 (UX-CANON A.11): a run verb with no route to run on is a
  // lie. It is withheld, and the disclosure says the reason in its place.
  const canRun = routeReady(plannedRoute);
  const wantsRun = intelOff && hasTranscript && Boolean(onRunIntelligence);
  const isFailed = intelState === "error" || intelState === "failed";
  const isQueued = intelState === "queued" || intelState === "pending";
  const wantsRetry = isFailed && Boolean(onRetryIntelligence);
  const showRunIntel = wantsRun && canRun;
  const showRetry = wantsRetry && canRun;
  const showSkip = (isFailed || isQueued) && Boolean(onSkipIntelligence);
  const showReview = needsRows.length > 0 && Boolean(onReview);
  // The disclosure rides beside the verb the gesture WOULD use.
  const showRoute = wantsRun || wantsRetry;
  const hasVerbs =
    showRunIntel || showRetry || showSkip || showReview || showRoute ||
    Boolean(refusal) || Boolean(durableRefusal);

  if (needsRows.length === 0 && !hasVerbs) return null;

  return (
    <div className="meetings-detail-needs" data-testid="meeting-needs-you">
      <div className="meetings-detail-needs-head">
        <span className="surface-caption">
          {countLabel("NEEDS YOU", needsCount)}
        </span>
        {showReview ? (
          <Button
            dense
            variant="ghost"
            onClick={onReview}
            data-testid="detail-review-btn"
          >
            Review
          </Button>
        ) : null}
        {showRoute ? (
          <RouteDisclosure route={plannedRoute} testId="detail-route" />
        ) : null}
        <RefusalToken
          refusal={refusal}
          durable={durableRefusal}
          testId="detail-refusal"
        />
        {showRunIntel ? (
          <Button
            dense
            variant="primary"
            onClick={onRunIntelligence}
            data-testid="detail-run-intelligence-btn"
          >
            Run summary
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
