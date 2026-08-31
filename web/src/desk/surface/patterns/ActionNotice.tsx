/** ActionNotice — a notice with at most ONE named next action.
 *  Icon + message + optional single action button.
 *  Tone variants: ok, warn, danger, info. */
import type { ReactNode } from "react";
import "./action-notice.css";

export function ActionNotice({
  tone,
  icon,
  children,
  action,
  role: roleProp = "status",
}: {
  tone?: "ok" | "warn" | "danger" | "info";
  icon?: string;
  children: ReactNode;
  action?: { label: string; onClick: () => void };
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
      <div className="surface-action-notice-body">{children}</div>
      {action ? (
        <button
          type="button"
          className="surface-action-notice-btn"
          onClick={action.onClick}
        >
          {action.label}
        </button>
      ) : null}
    </div>
  );
}
