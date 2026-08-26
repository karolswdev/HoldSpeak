import { useRef, useState, type KeyboardEvent } from "react";
import { EgressChip } from "../../desk/surface/gadgets";
import { useRovingRows } from "../../desk/surface/roving";
import type { AssignmentCandidate } from "./assignmentExperience";

function isCloud(candidate: Pick<AssignmentCandidate, "boundary">): boolean {
  return candidate.boundary === "cloud";
}

/**
 * Server-filtered candidate rows for the shared assignment editor.
 *
 * The active radio is deliberately separate from draft membership: arrowing
 * through candidates is an inspection/selection operation, never a save.
 */
export function AssignmentModelChooser({
  candidates,
  draftProfileIds,
  onChoose,
}: {
  candidates: AssignmentCandidate[];
  draftProfileIds: ReadonlySet<string>;
  onChoose: (candidate: AssignmentCandidate) => void;
}) {
  const root = useRef<HTMLDivElement>(null);
  const [activeId, setActiveId] = useState(() => candidates[0]?.profile_id ?? "");
  useRovingRows(root, { selector: "button[role='radio']" });

  const moveSelection = (event: KeyboardEvent<HTMLDivElement>) => {
    const index = Math.max(0, candidates.findIndex((candidate) => candidate.profile_id === activeId));
    let next = index;
    switch (event.key) {
      case "ArrowDown": next = Math.min(candidates.length - 1, index + 1); break;
      case "ArrowUp": next = Math.max(0, index - 1); break;
      case "Home": next = 0; break;
      case "End": next = candidates.length - 1; break;
      default: return;
    }
    setActiveId(candidates[next]?.profile_id ?? "");
  };

  return <div
    ref={root}
    className="assignment-candidates"
    role="radiogroup"
    aria-label="Compatible models"
    onKeyDownCapture={moveSelection}
  >
    {candidates.map((candidate) => {
      const added = draftProfileIds.has(candidate.profile_id);
      const selected = activeId === candidate.profile_id;
      return <button
        type="button"
        role="radio"
        aria-checked={selected}
        aria-label={`${candidate.label}, ${candidate.readiness}${added ? ", in draft" : ""}`}
        data-selected={selected || undefined}
        data-added={added || undefined}
        key={candidate.profile_id}
        onClick={() => { setActiveId(candidate.profile_id); onChoose(candidate); }}
      >
        <span><strong>{candidate.label}</strong><small>{candidate.readiness}{candidate.status === "savable_with_repair" ? " · needs repair" : ""}</small></span>
        {isCloud(candidate) ? <EgressChip label="Egress" scope="cloud" title="This model can leave this device." /> : null}
      </button>;
    })}
  </div>;
}
