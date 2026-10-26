import { Button } from "../../components/signal/Signal";
import type { EngineFact } from "../hooks/useEngine";

export function EngineLine({
  engine,
  onChoose,
  onRetry,
}: {
  engine: EngineFact;
  onChoose?: () => void;
  onRetry?: () => void;
}) {
  if (engine.state === "set") {
    return <div className="surface-engine-line" data-testid="engine-line">{engine.model}</div>;
  }
  if (engine.state === "failed") {
    return (
      <div className="surface-engine-line" data-testid="engine-line" data-state="failed">
        <span>Engine not read</span>
        {onRetry ? <Button dense variant="ghost" onClick={onRetry}>Try again</Button> : null}
      </div>
    );
  }
  if (engine.state === "unread") {
    return null;
  }
  return (
    <div className="surface-engine-line" data-testid="engine-line" data-state="none">
      <span>No engine</span>
      {onChoose ? <Button dense variant="ghost" onClick={onChoose}>Choose engine</Button> : null}
    </div>
  );
}
