// Real ReviewPosture, local direction specimen controller. No hub calls.
import { useState } from "react";
import { createRoot } from "react-dom/client";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import { DeskWindowFrame } from "@w/desk/components/DeskWindow";
import { ReviewPosture } from "@w/features/project-room/review/ReviewPosture";
import type { ReviewController } from "@w/features/project-room/review/useReviewController";
import { decodeReviewWindow, groupProposalsByKind } from "@w/features/project-room/review/model";
import "./canvas.css";

const noop = () => {};
const asyncNoop = async () => {};
const review = decodeReviewWindow({
  review_id: "canvas-review", project_id: "canvas-project", status: "open",
  source_manifest: {}, materiality_version: "1", opened_at: "2026-10-16T12:00:00Z",
  proposals: [{
    id: "proposal-fixture", proposal_kind: "risk_attention", target_ref: "action_item:checkpoint",
    title: "Update compliance docs", rationale: "Review the release checks.",
    patch_json: { card_id: "checkpoint", text: "Update compliance docs", owner: "Jordan", due: "2026-10-20", lane: "overdue" },
    materiality: "0.8", producer_kind: "", lifecycle: "open",
  }],
});

function Canvas() {
  const [editingPatch, setEditingPatch] = useState<Record<string, unknown> | null>({ ...review.proposals[0].patchJson });
  const [deferDate, setDeferDate] = useState("");
  const ctrl: ReviewController = {
    posture: "active", primaryVerb: "Review changes", hasPending: true, hasOpenReview: true,
    enterReview: asyncNoop, exitReview: noop, window: review, loading: false, error: "",
    openProposals: review.proposals, groups: groupProposalsByKind(review.proposals), selectedIndex: 0,
    selectedProposal: review.proposals[0], allDecided: false, exhausted: false, checkpointed: false, acceptedAt: null,
    selectNext: noop, selectPrev: noop, selectByIndex: noop, acceptProposal: asyncNoop,
    editAcceptProposal: asyncNoop, deferProposal: asyncNoop, dismissProposal: asyncNoop, decidingId: null,
    undoStack: [], undoLastDismiss: asyncNoop,
    editingPatch, startEdit: () => setEditingPatch({ ...review.proposals[0].patchJson }), cancelEdit: () => setEditingPatch(null),
    updateEditField: (key, value) => setEditingPatch(previous => previous ? { ...previous, [key]: value } : previous),
    deferDate, setDeferDate, finishReview: asyncNoop, dispositionSummary: () => ({}), dispositions: new Map(),
  };
  return <main className="desk-next canvas-desk"><DeskWindowFrame id="review-fit-canvas" title="Release review" label="Release review" minW={320} defaultW={860} defaultH={760} fitContent open entrance={false} dockChip="minimized" onClose={noop} className="desk-surface-window"><div className="desk-surface-body canvas-body"><ReviewPosture ctrl={ctrl}/></div></DeskWindowFrame></main>;
}
createRoot(document.getElementById("root")!).render(<Canvas/>);
