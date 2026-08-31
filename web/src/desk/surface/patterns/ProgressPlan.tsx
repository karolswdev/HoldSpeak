/** ProgressPlan — a live plan with per-step progress.
 *  Step states: queued, running, done, failed.
 *  Receipt/egress slots, one resume/retry action. */
import { useRef, type ReactNode } from "react";
import "./progress-plan.css";

export type PlanStep = {
  id: string;
  label: string;
  status: "queued" | "running" | "done" | "failed";
  progress?: number;
  rate?: string;
  detail?: string;
};

const STEP_ICONS: Record<PlanStep["status"], string> = {
  queued: "○",   // circle outline
  running: "●",  // filled circle (pulses via CSS)
  done: "✓",     // check
  failed: "✗",   // X mark
};

export function ProgressPlan({
  steps,
  compact,
  receipt,
  egress,
  action,
  ariaLabel,
}: {
  steps: PlanStep[];
  compact?: boolean;
  receipt?: ReactNode;
  egress?: ReactNode;
  action?: { label: string; onClick: () => void };
  ariaLabel?: string;
}) {
  const statusRef = useRef<HTMLDivElement>(null);

  const hasFooter = receipt != null || egress != null || action != null;

  return (
    <div
      className="surface-progress-plan"
      data-compact={compact || undefined}
      aria-label={ariaLabel ?? "Progress plan"}
      role="group"
    >
      <div className="surface-plan-steps" role="list">
        {steps.map((step) => (
          <div key={step.id}>
            <div
              className="surface-plan-step"
              data-status={step.status}
              role="listitem"
            >
              <span className="surface-plan-step-icon" aria-hidden="true">
                {STEP_ICONS[step.status]}
              </span>
              <span className="surface-plan-step-label">{step.label}</span>
              {step.progress != null ? (
                <div
                  className="surface-plan-progress"
                  role="progressbar"
                  aria-label={`${step.label} progress`}
                  aria-valuenow={Math.round(step.progress * 100)}
                  aria-valuemin={0}
                  aria-valuemax={100}
                >
                  <div
                    className="surface-plan-progress-fill"
                    style={{ width: `${Math.round(step.progress * 100)}%` }}
                  />
                </div>
              ) : null}
              {step.rate ? (
                <span className="surface-plan-step-rate">{step.rate}</span>
              ) : null}
            </div>
            {!compact && step.detail ? (
              <div className="surface-plan-step-detail">{step.detail}</div>
            ) : null}
          </div>
        ))}
      </div>
      {/* Status region: updates only on transitions */}
      <div ref={statusRef} aria-live="polite" className="sr-only">
        {steps.filter((s) => s.status === "running").map((s) => s.label).join(", ") || null}
      </div>
      {hasFooter ? (
        <div className="surface-plan-footer">
          {receipt != null ? (
            <div className="surface-plan-footer-slot">{receipt}</div>
          ) : null}
          {egress != null ? (
            <div className="surface-plan-footer-slot">{egress}</div>
          ) : null}
          {action ? (
            <button
              type="button"
              className="surface-plan-action-btn"
              onClick={action.onClick}
            >
              {action.label}
            </button>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
