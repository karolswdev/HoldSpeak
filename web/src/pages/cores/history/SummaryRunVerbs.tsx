// The summary run's verbs on the meeting record (the language, 2026-11-08):
// Run summary, Retry and Skip go to the plate (MeetingRunVerb); the route
// they would use and the hub's refusal are one quiet line at the ledger's
// head. What the meeting asks of him is the ledger's rows (MeetingDetail).
import { Button } from "../../../components/signal/Signal";
import { RefusalToken, RouteDisclosure, routeTitle } from "../../../meetings/RouteDisclosure";
import {
  routeReady,
  type PlannedRoute,
  type RunReceipt,
  type SummaryRefusal,
} from "../../../meetings/summaryRoute";
import { MeetingRunVerb } from "../../../meetings/runSlot";
import { ToolGlyph } from "../../../desk/surface/kit";

/** True when the record draws its filled `Run summary`. One rule, two
 *  readers: this table draws the verb, and the Decide well steps down to
 *  ghost while it is on the face (surface/contract.md: one filled primary). */
export function showsRunSummary({
  intelOff, hasTranscript, plannedRoute, onRunIntelligence,
}: {
  intelOff: boolean;
  hasTranscript: boolean;
  plannedRoute?: PlannedRoute | null;
  onRunIntelligence?: () => void;
}): boolean {
  return intelOff && hasTranscript && Boolean(onRunIntelligence) && routeReady(plannedRoute);
}

export function SummaryRunVerbs({
  intelOff,
  intelState,
  hasTranscript,
  plannedRoute,
  refusal,
  durableRefusal,
  onRunIntelligence,
  onRetryIntelligence,
  onSkipIntelligence,
}: {
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
  const showRunIntel = showsRunSummary({ intelOff, hasTranscript, plannedRoute, onRunIntelligence });
  const showRetry = wantsRetry && canRun;
  const showSkip = (isFailed || isQueued) && Boolean(onSkipIntelligence);
  // The disclosure rides beside the verb the gesture WOULD use.
  const showRoute = wantsRun || wantsRetry;
  const hasVerbs =
    showRunIntel || showRetry || showSkip || showRoute ||
    Boolean(refusal) || Boolean(durableRefusal);

  if (!hasVerbs) return null;

  return (
    <div className="meetings-detail-needs" data-testid="meeting-run-verbs">
      <div className="meetings-detail-needs-head">
        {showRoute ? (
          <RouteDisclosure route={plannedRoute} testId="detail-route" />
        ) : null}
        <RefusalToken
          refusal={refusal}
          durable={durableRefusal}
          testId="detail-refusal"
        />
        {/* Window grammar: the run verbs sit in the meeting window's toolbar. */}
        <MeetingRunVerb>
          {showRunIntel ? (
            <Button
              dense
              variant="primary"
              title={routeTitle(plannedRoute)}
              onClick={onRunIntelligence}
              data-testid="detail-run-intelligence-btn"
            >
              <ToolGlyph kind="summary" />
              Run summary
            </Button>
          ) : null}
          {showRetry ? (
            <Button
              dense
              variant="ghost"
              title={routeTitle(plannedRoute)}
              onClick={onRetryIntelligence}
              data-testid="detail-retry-btn"
            >
              <ToolGlyph kind="retry" />
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
        </MeetingRunVerb>
      </div>
    </div>
  );
}
