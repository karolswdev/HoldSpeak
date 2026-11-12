import { Button } from "../../../components/signal/Signal";
import { PaneActions } from "../../../desk/surface";
import { intelStateOf } from "./helpers";

export function summaryFailureReason(meeting: Record<string, unknown> | null): string {
  if (!meeting || !["error", "failed"].includes(intelStateOf(meeting.intel_status))) return "";
  const status = typeof meeting.intel_status === "object" && meeting.intel_status ? meeting.intel_status as Record<string, unknown> : {};
  const job = meeting.intel_job as Record<string, unknown> | null;
  return String(status.detail || meeting.intel_status_detail || job?.last_error || job?.error || "The summary did not finish.").replace(/\s+/g, " ").trim();
}
export function SummaryFailure({ meeting, retry, disabled }: { meeting: Record<string, unknown> | null; retry?(): void; disabled?: boolean }) {
  const reason = summaryFailureReason(meeting);
  return reason ? <PaneActions data-testid="meeting-summary-failure" data-feedback-redact="true"><span role="alert">{reason}</span>{retry ? <Button dense disabled={disabled} onClick={retry}>Try again</Button> : null}</PaneActions> : null;
}
