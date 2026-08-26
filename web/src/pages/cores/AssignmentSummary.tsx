/**
 * The small server-fact summary reused by the overview now and contextual
 * owner surfaces later. It owns no assignment state; Change only opens the
 * common editor supplied by its host.
 */
export function AssignmentSummary({
  label,
  effective,
  repair,
  onChange,
}: {
  label: string;
  effective: string;
  repair: string | null;
  onChange: (opener: HTMLButtonElement) => void;
}) {
  return <article className="capability-assignment-row" data-issue={repair ? "true" : undefined}>
    <div><strong>{label}</strong><span>{effective}</span></div>
    <div><button type="button" onClick={(event) => onChange(event.currentTarget)}>{repair ?? "Change"}</button></div>
  </article>;
}
