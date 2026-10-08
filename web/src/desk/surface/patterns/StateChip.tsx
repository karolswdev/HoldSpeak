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

/** PHILO-14 B2 (Astra r1 on #958): the word a LIT lamp says when its
 *  caller gives no label. A lamp is never colour alone: with `label=""`
 *  it shows this word, unless the caller marks it `wordless` (the row
 *  already says the same word); its accessible name carries it always. */
export const LAMP_WORDS: Partial<Record<ChipState, string>> = {
  success: "OK",
  working: "WORKING",
  warning: "WARN",
  failure: "FAILED",
  active: "ASKS",
};

export function StateChip({
  state,
  label,
  icon,
  wordless = false,
  wrap = false,
  className,
  "data-testid": dataTestId,
}: {
  state: ChipState;
  label?: string;
  icon?: string;
  /** With `label=""`: the row already says this state in words (its
   *  primary or a cell), so the lamp draws no word of its own. It still
   *  carries the state word as its accessible name. */
  wordless?: boolean;
  /** PHILO-15 B31 (Astra r2): a long state may wrap inside a narrow card
   *  (at 393 "… · FROM GH CONFIG" was cut at FROM). */
  wrap?: boolean;
  className?: string;
  "data-testid"?: string;
}) {
  const lampWord = LAMP_WORDS[state];
  const name = label || (label === "" ? lampWord ?? DEFAULT_LABELS[state] : DEFAULT_LABELS[state]);
  const shown = label === "" ? (wordless || !lampWord ? "" : lampWord) : name;
  return (
    <span
      className={className ? `surface-state-chip ${className}` : "surface-state-chip"}
      data-state={state}
      data-wrap={wrap ? "" : undefined}
      role="status"
      aria-label={name}
      data-testid={dataTestId}
    >
      <span className="surface-state-chip-icon" aria-hidden="true">
        {icon ?? DEFAULT_ICONS[state]}
      </span>
      {shown}
    </span>
  );
}
