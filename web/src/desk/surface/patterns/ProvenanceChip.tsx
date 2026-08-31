/** ProvenanceChip + Receipt — promoted provenance/receipt patterns
 *  for composing into SurfaceFooter. */
import "./provenance.css";

/** ProvenanceChip: typed source/boundary label with inspect action. */
export function ProvenanceChip({
  source,
  boundary,
  onInspect,
}: {
  source: string;
  boundary?: string;
  onInspect?: () => void;
}) {
  return (
    <span className="surface-provenance-chip">
      <span className="surface-provenance-source">{source}</span>
      {boundary ? (
        <span className="surface-provenance-boundary">{boundary}</span>
      ) : null}
      {onInspect ? (
        <button
          type="button"
          className="surface-provenance-inspect"
          onClick={onInspect}
          aria-label={`Inspect ${source}`}
        >
          {"ℹ"}
        </button>
      ) : null}
    </span>
  );
}

/** Receipt: typed receipt with status lamp, label, and timestamp. */
export function Receipt({
  status,
  label,
  timestamp,
  onInspect,
}: {
  status: "ok" | "warn" | "danger";
  label: string;
  timestamp?: string;
  onInspect?: () => void;
}) {
  return (
    <span className="surface-receipt" data-status={status}>
      <span className="surface-receipt-lamp" aria-hidden="true" />
      <span className="surface-receipt-label">{label}</span>
      {timestamp ? (
        <span className="surface-receipt-time">{timestamp}</span>
      ) : null}
      {onInspect ? (
        <button
          type="button"
          className="surface-receipt-inspect"
          onClick={onInspect}
          aria-label={`Inspect ${label}`}
        >
          {"ℹ"}
        </button>
      ) : null}
    </span>
  );
}
