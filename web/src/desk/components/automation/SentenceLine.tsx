/** Betterment A3 — one line of the automation's sentence (DESIGN §4).
 *
 * The label (When, Do, About, With, Put it in) and its value. A line with an
 * editor is the control: pressing it unfolds the editor in place, under the
 * line, and never opens another window. A line whose editor has not landed
 * yet (A5, A6) shows its value and is not pressable (UX-CANON A.11: a verb
 * that does nothing is a lie).
 *
 * Window grammar (2026-10-24): the sentence is the window's compact head.
 * `lead` is the Do sentence (sans 15/500, its label for assistive tech
 * only); `fact` is one quiet fact of the line under it (When, About, With,
 * Put it in: the label in muted sans 12, the value after it). A fact's
 * editor still unfolds in place, under the whole fact line. */
import { useId, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";

export function SentenceLine({
  name,
  label,
  icon,
  children,
  aside,
  open = false,
  onPress,
  editor,
  blank = false,
  variant = "line",
}: {
  /** Window grammar: `lead` (the Do sentence) or `fact` (one head fact). */
  variant?: "line" | "lead" | "fact";
  /** The line's key (`when`, `do`, `about`, `with`, `put`). */
  name: string;
  label: string;
  /** The Workbench sprite for the sentence line. */
  icon?: ReactNode;
  /** The value, in words. */
  children: ReactNode;
  /** A fact at the end of the line (a chip). */
  aside?: ReactNode;
  open?: boolean;
  /** Present when the line has its editor. */
  onPress?: () => void;
  /** The editor, drawn under the line while open. */
  editor?: ReactNode;
  /** The value is a blank he has to fill (a starter could not guess it). */
  blank?: boolean;
}) {
  const uid = useId();
  const labelId = `${uid}-label`;
  const valueId = `${uid}-value`;
  const value = (
    <span className="automation-line-value" data-blank={blank || undefined}>
      {children}
    </span>
  );
  return (
    <div className="automation-line" data-line={name} data-open={open || undefined}
      data-variant={variant === "line" ? undefined : variant}
      data-testid={`automation-line-${name}`}>
      <span className="automation-line-label" id={labelId}>
        {icon && variant === "line" ? <span className="automation-line-label-icon" aria-hidden="true">{icon}</span> : null}
        {label}
      </span>
      {onPress ? (
        <Button
          variant="chrome"
          className="automation-line-press"
          aria-expanded={open}
          aria-labelledby={labelId}
          aria-describedby={valueId}
          onClick={onPress}
        >
          <span id={valueId} className="automation-line-press-value">{value}</span>
          <span className="automation-line-chevron" aria-hidden="true">{open ? "▾" : "▸"}</span>
        </Button>
      ) : (
        <span className="automation-line-static">{value}</span>
      )}
      {aside ? <span className="automation-line-aside">{aside}</span> : null}
      {open && editor ? <div className="automation-line-editor">{editor}</div> : null}
    </div>
  );
}
