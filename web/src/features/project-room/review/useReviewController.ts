// HS-160-06 — the review controller: queue, selection, dispositions,
// undo-on-dismiss session stack, exhausted->Finish flow.
// Targeted query invalidation of /room after decisions (WEB-ARC-005 spirit).

import { useCallback, useRef, useState } from "react";
import { readableError } from "../../../lib/api";
import type { RoomReviewData } from "./model";
import type {
  DecisionVerb,
  DispositionEntry,
  Proposal,
  ProposalGroup,
  ReviewWindow,
  UndoEntry,
} from "./model";
import { groupProposalsByKind } from "./model";
import * as reviewApi from "./api";

export type ReviewPosture = "off" | "active";

export function useReviewController(
  projectId: string,
  reviewSection: RoomReviewData | null,
  onRoomRefresh: () => void,
) {
  // ── Posture (off = normal Now, active = review face) ──
  const [posture, setPosture] = useState<ReviewPosture>("off");

  // ── Window + proposals ──
  const [window, setWindow] = useState<ReviewWindow | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // ── Queue state ──
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [dispositions, setDispositions] = useState<Map<string, DispositionEntry>>(new Map());
  const [decidingId, setDecidingId] = useState<string | null>(null);
  const [undoStack, setUndoStack] = useState<UndoEntry[]>([]);
  const [exhausted, setExhausted] = useState(false);
  const [checkpointed, setCheckpointed] = useState(false);
  const [acceptedAt, setAcceptedAt] = useState<string | null>(null);

  // ── Editing state ──
  const [editingPatch, setEditingPatch] = useState<Record<string, unknown> | null>(null);
  const [deferDate, setDeferDate] = useState("");

  // Ref for stable callback identity
  const windowRef = useRef(window);
  windowRef.current = window;

  // ── Derived: the undecided proposals (not yet decided in this session) ──
  const openProposals = window
    ? window.proposals.filter((p) => p.lifecycle === "open" && !dispositions.has(p.id))
    : [];

  const groups: ProposalGroup[] = groupProposalsByKind(
    window?.proposals ?? [],
  );

  const selectedProposal: Proposal | null = openProposals[selectedIndex] ?? null;

  // ── Check if all proposals are decided ──
  const allDecided = window
    ? window.proposals.every(
        (p) => p.lifecycle !== "open" || dispositions.has(p.id),
      )
    : false;

  // ── Open/enter review ──
  const enterReview = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError("");
    try {
      const w = await reviewApi.openReview(projectId);
      setWindow(w);
      setPosture("active");
      setSelectedIndex(0);
      setDispositions(new Map());
      setUndoStack([]);
      setExhausted(false);
      setCheckpointed(false);
      setAcceptedAt(null);
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  // ── Exit review posture ──
  const exitReview = useCallback(() => {
    setPosture("off");
    setWindow(null);
    setDispositions(new Map());
    setUndoStack([]);
    setExhausted(false);
    setCheckpointed(false);
    setEditingPatch(null);
    setDeferDate("");
    onRoomRefresh();
  }, [onRoomRefresh]);

  // ── Decide a proposal ──
  const decide = useCallback(
    async (proposalId: string, verb: DecisionVerb, opts?: {
      patch?: Record<string, unknown>;
      deferredUntil?: string;
    }) => {
      if (!window || !projectId) return;
      setDecidingId(proposalId);
      setError("");
      try {
        await reviewApi.decideProposal(
          projectId,
          window.reviewId,
          proposalId,
          {
            verb,
            patch: opts?.patch,
            deferred_until: opts?.deferredUntil,
          },
        );
        const proposal = window.proposals.find((p) => p.id === proposalId);
        if (proposal) {
          setDispositions((prev) => {
            const next = new Map(prev);
            next.set(proposalId, {
              verb,
              proposalId,
              proposalKind: proposal.proposalKind,
              title: proposal.title,
              deferredUntil: opts?.deferredUntil,
              editedPatch: opts?.patch,
            });
            return next;
          });
          // Add undo entry for dismiss
          if (verb === "dismiss") {
            setUndoStack((prev) => [
              ...prev,
              {
                proposalId,
                verb,
                previousLifecycle: proposal.lifecycle,
              },
            ]);
          }
        }

        // Move to next undecided proposal or mark exhausted
        setSelectedIndex((prev) => {
          const remaining = window.proposals.filter(
            (p) =>
              p.lifecycle === "open" &&
              !dispositions.has(p.id) &&
              p.id !== proposalId,
          );
          if (remaining.length === 0) {
            setExhausted(true);
            return 0;
          }
          return Math.min(prev, remaining.length - 1);
        });

        setEditingPatch(null);
        setDeferDate("");
      } catch (reason) {
        setError(readableError(reason));
      } finally {
        setDecidingId(null);
      }
    },
    [window, projectId, dispositions],
  );

  // ── Convenience verb methods ──
  const acceptProposal = useCallback(
    (proposalId: string) => decide(proposalId, "accept"),
    [decide],
  );

  const editAcceptProposal = useCallback(
    (proposalId: string, patch: Record<string, unknown>) =>
      decide(proposalId, "edit_accept", { patch }),
    [decide],
  );

  const deferProposal = useCallback(
    (proposalId: string, deferredUntil?: string) =>
      decide(proposalId, "defer", { deferredUntil }),
    [decide],
  );

  const dismissProposal = useCallback(
    (proposalId: string) => decide(proposalId, "dismiss"),
    [decide],
  );

  // ── Undo last dismiss ──
  const undoLastDismiss = useCallback(() => {
    if (undoStack.length === 0) return;
    const last = undoStack[undoStack.length - 1];
    setUndoStack((prev) => prev.slice(0, -1));
    setDispositions((prev) => {
      const next = new Map(prev);
      next.delete(last.proposalId);
      return next;
    });
    setExhausted(false);
    // Navigate to the undone proposal
    if (window) {
      const idx = openProposals.findIndex((p) => p.id === last.proposalId);
      if (idx >= 0) setSelectedIndex(idx);
    }
  }, [undoStack, window, openProposals]);

  // ── Finish review (accept_review) ──
  const finishReview = useCallback(async () => {
    if (!window || !projectId) return;
    setLoading(true);
    setError("");
    try {
      const result = await reviewApi.acceptReview(
        projectId,
        window.reviewId,
      );
      setCheckpointed(true);
      setAcceptedAt(result.acceptedAt);
      onRoomRefresh();
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setLoading(false);
    }
  }, [window, projectId, onRoomRefresh]);

  // ── Navigation ──
  const selectNext = useCallback(() => {
    setSelectedIndex((prev) => Math.min(prev + 1, openProposals.length - 1));
  }, [openProposals.length]);

  const selectPrev = useCallback(() => {
    setSelectedIndex((prev) => Math.max(prev - 1, 0));
  }, []);

  const selectByIndex = useCallback((index: number) => {
    setSelectedIndex(index);
  }, []);

  // ── Editing ──
  const startEdit = useCallback(() => {
    if (selectedProposal) {
      setEditingPatch({ ...selectedProposal.patchJson });
    }
  }, [selectedProposal]);

  const cancelEdit = useCallback(() => {
    setEditingPatch(null);
  }, []);

  const updateEditField = useCallback(
    (key: string, value: unknown) => {
      setEditingPatch((prev) =>
        prev ? { ...prev, [key]: value } : prev,
      );
    },
    [],
  );

  // ── Primary verb for the orientation band ──
  const hasPending =
    reviewSection != null && reviewSection.pendingCount > 0;
  const hasOpenReview =
    reviewSection != null && reviewSection.openReviewId != null;

  // WEB-NOW-002: when pending_count > 0, primary verb = "Review changes"
  // Open review when none open; enter the open one when it exists
  const primaryVerb: string | null = hasPending
    ? "Review changes"
    : null;

  // ── Disposition summary (for exhausted/checkpointed) ──
  const dispositionSummary = () => {
    const counts: Record<string, number> = {};
    for (const [, d] of dispositions) {
      counts[d.verb] = (counts[d.verb] ?? 0) + 1;
    }
    return counts;
  };

  return {
    // Posture
    posture,
    primaryVerb,
    hasPending,
    hasOpenReview,
    enterReview,
    exitReview,

    // Window
    window,
    loading,
    error,

    // Queue
    openProposals,
    groups,
    selectedIndex,
    selectedProposal,
    allDecided,
    exhausted,
    checkpointed,
    acceptedAt,

    // Navigation
    selectNext,
    selectPrev,
    selectByIndex,

    // Verbs
    acceptProposal,
    editAcceptProposal,
    deferProposal,
    dismissProposal,
    decidingId,

    // Undo
    undoStack,
    undoLastDismiss,

    // Editing
    editingPatch,
    startEdit,
    cancelEdit,
    updateEditField,
    deferDate,
    setDeferDate,

    // Finish
    finishReview,
    dispositionSummary,
    dispositions,
  } as const;
}

export type ReviewController = ReturnType<typeof useReviewController>;
