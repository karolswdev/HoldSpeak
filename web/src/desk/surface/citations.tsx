// HS-111-05 — the citation token, promoted out of ProjectMemoryCore so
// "openable citation" has exactly ONE rendering (the HS-109-04 grounding
// receipt's source_refs). A citation is a quiet mono token that OPENS the
// underlying object: meetings through the Meetings surface, everything
// else through the primitive opener. Ask and Project Memory both speak
// this species; a third rendering is a defect.
import { openPrimitive, openSurfaceOr } from "../shell";

/** The honest "grounded on N" arithmetic: matches minus overflow —
 * the receipt never counts material the hub did not actually read. */
export function groundedMatchCount(
  receipt: { matchedCount: number; overflowCount: number } | null,
): number {
  return receipt
    ? Math.max(0, receipt.matchedCount - receipt.overflowCount)
    : 0;
}

/** The token's label grammar: `Kind · id`. */
export function sourceLabel(ref: string): string {
  const [kind, ...rest] = ref.split(":");
  return `${kind[0]?.toUpperCase() || ""}${kind.slice(1)} · ${rest.join(":")}`;
}

export function openSourceRef(ref: string) {
  if (ref.startsWith("meeting:")) {
    openSurfaceOr("review-meetings", "/history", ref);
    return;
  }
  openPrimitive(ref);
}

export function CitationChips({
  refs,
  onOpen = openSourceRef,
}: {
  refs: string[];
  onOpen?: (ref: string) => void;
}) {
  if (!refs.length) return null;
  return (
    <div className="surface-citations" aria-label="Citations">
      {refs.map((ref) => (
        <button
          key={ref}
          type="button"
          className="desk-chip quiet"
          onClick={() => onOpen(ref)}
        >
          {sourceLabel(ref)}
        </button>
      ))}
    </div>
  );
}
