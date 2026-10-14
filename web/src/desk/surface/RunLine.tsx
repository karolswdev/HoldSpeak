import { useEffect, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { reasonVerb, reasonWords } from "./runWords";

export type RunPhase = "idle" | "running" | "success" | "failure";

export function RunLine({
  phase,
  verb = "Running",
  pastVerb = "Done",
  model = "",
  place = "",
  startedAt,
  elapsedSeconds,
  reason,
  onRetry,
  onAction,
}: {
  phase: RunPhase;
  verb?: string;
  pastVerb?: string;
  model?: string;
  place?: string;
  startedAt?: number;
  elapsedSeconds?: number;
  reason?: string;
  onRetry?: () => void;
  onAction?: () => void;
}) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (phase !== "running") return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [phase]);
  if (phase === "idle") return null;
  const seconds = elapsedSeconds ?? (startedAt ? Math.max(0, Math.round((now - startedAt) / 1000)) : 0);
  if (phase === "running") {
    return <div className="surface-run-line" data-testid="run-line" data-state="running">{verb}{model ? ` · ${model}` : ""}{place ? ` · ${place}` : ""} · {seconds} s</div>;
  }
  if (phase === "success") {
    return <div className="surface-run-line" data-testid="run-line" data-state="success">{pastVerb} in {seconds} s</div>;
  }
  const action = reasonVerb(reason);
  return (
    <div className="surface-run-line" data-testid="run-line" data-state="failure">
      <span>{reasonWords(reason, model, seconds)}</span>
      {action && (onAction || onRetry) ? <Button dense variant="ghost" onClick={onAction || onRetry}>{action}</Button> : null}
    </div>
  );
}
