// HS-111-05 — the citation token, promoted out of ProjectMemoryCore so
// "openable citation" has exactly ONE rendering (the HS-109-04 grounding
// receipt's source_refs). A citation is a quiet mono token that OPENS the
// underlying object: meetings through the Meetings surface, everything
// else through the primitive opener. Ask and Project Memory both speak
// this species; a third rendering is a defect.
import { openRef } from "../openObject";
import { openPrimitive, openSurfaceOr } from "../shell";
import { Button } from "../../components/signal/Signal";

/** The honest "grounded on N" arithmetic: matches minus overflow —
 * the receipt never counts material the hub did not actually read. */
export function groundedMatchCount(
  receipt: { matchedCount: number; overflowCount: number } | null,
): number {
  return receipt
    ? Math.max(0, receipt.matchedCount - receipt.overflowCount)
    : 0;
}

/** Memory kinds that have no window of their own (2026-10-03): a send, a
 * published update, a Prep brief, a calendar event. ONE list: a citation or
 * a memory row of these kinds is plain text, never a verb that opens
 * nothing (UX-CANON A.11). The model-facing ref list (`DESK_REF_KINDS`, the
 * drafters' helper) must name the same kinds. */
export const NO_WINDOW_REF_KINDS: readonly string[] = [
  "send", "project_update", "prep_brief", "calendar_event",
  "brief_item", "dictation", "steward_run", "ask_answer",
];

/** True when a ref names something the Desk can open in a window. */
export function refOpensWindow(ref: string): boolean {
  return !NO_WINDOW_REF_KINDS.includes(ref.split(":", 1)[0]);
}

/** The token's label grammar: `Kind · id`. */
export function sourceLabel(ref: string): string {
  const [rawKind, ...rest] = ref.split(":");
  // A desk decision reads as what it is: a decision.
  const kind = (rawKind === "desk_decision" ? "decision" : rawKind).replaceAll("_", " ");
  return `${kind[0]?.toUpperCase() || ""}${kind.slice(1)} · ${rest.join(":")}`;
}

export function openSourceRef(ref: string) {
  if (!refOpensWindow(ref)) return;
  if (ref.startsWith("meeting:")) {
    openSurfaceOr("review-meetings", "/history", ref);
    return;
  }
  // Thread search hits carry a fragment: thread:<id>#<message_id>.
  // Parse the fragment, set the focus message in the store, and open the
  // pullout at the thread level (without the fragment).
  if (ref.startsWith("thread:")) {
    const hashIdx = ref.indexOf("#");
    if (hashIdx > 0) {
      const messageId = ref.slice(hashIdx + 1);
      const threadRef = ref.slice(0, hashIdx);
      void import("../threads").then((m) =>
        m.useThreadStore.getState().setFocusMessage(messageId),
      );
      openPrimitive(threadRef);
      return;
    }
  }
  // A desk decision's ref is `desk_decision:<id>` (memory, Send, a Project);
  // the Desk store keeps its window under `decision:<id>`.
  if (ref.startsWith("desk_decision:")) {
    openPrimitive(`decision:${ref.slice("desk_decision:".length)}`);
    return;
  }
  openPrimitive(ref);
}

/** A chip opens through the one open grammar (`openRef`): an action item in
 * Follow-through, a decision in its window; `openSourceRef` is only the
 * window dispatch under it. */
export function CitationChips({
  refs,
  onOpen = openRef,
}: {
  refs: string[];
  onOpen?: (ref: string) => void;
}) {
  if (!refs.length) return null;
  return (
    <div className="surface-citations" aria-label="Citations">
      {refs.map((ref) => !refOpensWindow(ref) ? (
        <span key={ref} className="desk-chip quiet" data-testid="citation-plain">
          {sourceLabel(ref)}
        </span>
      ) : (
        <Button
          variant="chrome"
          key={ref}
          className="desk-chip quiet"
          onClick={() => onOpen(ref)}
        >
          {sourceLabel(ref)}
        </Button>
      ))}
    </div>
  );
}
