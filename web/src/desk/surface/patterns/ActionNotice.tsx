/** ActionNotice — a notice with at most ONE named next action.
 *  Icon + message + optional single action button.
 *  Tone variants: ok, warn, danger, info. */
import type { ReactNode } from "react";
import "./action-notice.css";
import { Button } from "../../../components/signal/Signal";

export function ActionNotice({
  tone,
  icon,
  children,
  action,
  keeps,
  role: roleProp = "status",
}: {
  tone?: "ok" | "warn" | "danger" | "info";
  icon?: string;
  children: ReactNode;
  /** What the failed attempt kept, beside its reason and next action. */
  keeps?: ReactNode;
  action?: { label: string; onClick: () => void; disabled?: boolean; busy?: boolean };
  role?: string;
}) {
  return (
    <div
      className="surface-action-notice"
      data-tone={tone}
      role={roleProp}
    >
      {icon ? (
        <span className="surface-action-notice-icon" aria-hidden="true">
          {icon}
        </span>
      ) : null}
      <div className="surface-action-notice-body">{children}{keeps ? <span className="surface-action-notice-keeps">{keeps}</span> : null}</div>
      {action ? (
        <Button
          variant="secondary"
          className="surface-action-notice-btn"
          onClick={action.onClick}
          disabled={action.disabled}
          loading={action.busy}
        >
          {action.label}
        </Button>
      ) : null}
    </div>
  );
}
