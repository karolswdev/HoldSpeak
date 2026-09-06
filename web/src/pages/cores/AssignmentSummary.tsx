import { Button } from "../../components/signal/Signal";

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
    <div><Button dense variant="ghost" onClick={(event) => onChange(event.currentTarget as HTMLButtonElement)}>{repair ?? "Change"}</Button></div>
  </article>;
}
