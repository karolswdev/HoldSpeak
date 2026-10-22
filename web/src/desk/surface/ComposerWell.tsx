import type { ReactNode } from "react";
import "./composer-well.css";

/**
 * The shared paper well for a conversation editor.
 *
 * ComposerWell only arranges the material supplied by its host. Drafts,
 * submission, keyboard handling, engine choice and capture remain the
 * caller's authority.
 */
export interface ComposerWellProps {
  /** The host-owned editor slot. */
  children?: ReactNode;
  /** Engine, egress or other context that belongs at the left of the action row. */
  context?: ReactNode;
  /** The host-owned capture control, usually one MicButton. */
  capture?: ReactNode;
  /** The host-owned primary and secondary actions. */
  actions?: ReactNode;
  /** Optional in-flow material above the editor, such as selected passage. */
  details?: ReactNode;
  className?: string;
  "data-testid"?: string;
}

export function ComposerWell({
  children,
  context,
  capture,
  actions,
  details,
  className,
  "data-testid": testId,
}: ComposerWellProps) {
  const hasActions = context != null || capture != null || actions != null;

  return (
    <div
      className={["surface-compose-well", className].filter(Boolean).join(" ")}
      data-testid={testId}
    >
      {details != null ? <div className="surface-compose-details">{details}</div> : null}
      {children != null ? children : null}
      {hasActions ? (
        <div className="surface-compose-actions">
          {context != null ? <div className="surface-compose-context">{context}</div> : null}
          {capture != null ? <div className="surface-compose-capture">{capture}</div> : null}
          {actions != null ? <div className="surface-compose-verbs">{actions}</div> : null}
        </div>
      ) : null}
    </div>
  );
}
