/** StateChip — closed-vocabulary status chip with icon + text.
 *  Seven states, each mapping to a tone and a default glyph.
 *  Consistent with the gadget-chip species. */
import "./state-chip.css";

export type ChipState =
  | "idle"
  | "active"
  | "working"
  | "success"
  | "warning"
  | "failure"
  | "unreachable";

const DEFAULT_ICONS: Record<ChipState, string> = {
  idle: "○",       // circle outline
  active: "●",     // filled circle
  working: "↻",    // clockwise arrow
  success: "✓",    // check
  warning: "⚠",    // warning triangle
  failure: "✗",    // X mark
  unreachable: "—", // em dash
};

const DEFAULT_LABELS: Record<ChipState, string> = {
  idle: "Idle",
  active: "Active",
  working: "Working",
  success: "Success",
  warning: "Warning",
  failure: "Failure",
  unreachable: "Unreachable",
};

export function StateChip({
  state,
  label,
  icon,
  className,
}: {
  state: ChipState;
  label?: string;
  icon?: string;
  className?: string;
}) {
  return (
    <span
      className={className ? `surface-state-chip ${className}` : "surface-state-chip"}
      data-state={state}
      role="status"
      aria-label={label ?? DEFAULT_LABELS[state]}
    >
      <span className="surface-state-chip-icon" aria-hidden="true">
        {icon ?? DEFAULT_ICONS[state]}
      </span>
      {label ?? DEFAULT_LABELS[state]}
    </span>
  );
}
