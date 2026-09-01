// HS-160-06 — the review posture: a posture in Now, judged from the keyboard.
// Wide (>=560px container): queue left, comparison right, four verbs.
// Narrow: one card at a time, persistent footer verbs (SurfaceFooter).
// No modal — WEB-IA-003.

import { useCallback, useEffect, useRef, type KeyboardEvent } from "react";
import { Button } from "../../../components/signal/Signal";
import {
  SurfaceFooter,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceSection,
  SurfaceState,
  SurfaceVerbs,
  humanTime,
  Disclosure,
  ChoiceCardShell,
  useRovingRows,
  MicButton,
} from "../../../desk/surface";
import type { ReviewController } from "./useReviewController";
import type { Proposal, ProposalGroup, ProposalKind } from "./model";
import { kindLabel } from "./model";
import "./review-posture.css";

/* ── Proposal kind count chip ── */

function KindCountChip({ kind, count }: { kind: ProposalKind; count: number }) {
  return (
    <span className="review-kind-group" data-testid="review-kind-group">
      <span className="surface-token" data-testid="review-kind-label">
        {kindLabel(kind)}
      </span>
      <span className="project-room-count-chip" data-testid="review-kind-count">
        {count}
      </span>
    </span>
  );
}

/* ── Comparison: current truth vs proposed patch ── */

function PatchComparison({
  proposal,
  editingPatch,
  onEditField,
}: {
  proposal: Proposal;
  editingPatch: Record<string, unknown> | null;
  onEditField?: (key: string, value: string) => void;
}) {
  const patch = editingPatch ?? proposal.patchJson;
  const isRecordOnly =
    proposal.proposalKind === "review_flag" ||
    proposal.proposalKind === "observation_attention" ||
    proposal.proposalKind === "coverage_degraded";

  if (isRecordOnly) {
    // For record-only kinds: show rationale/evidence as the "current" side
    return (
      <div className="review-comparison" data-testid="review-comparison">
        <div className="review-comparison-side" data-testid="review-comparison-rationale">
          <span className="review-comparison-label">Rationale</span>
          <p className="review-comparison-value">{proposal.rationale}</p>
        </div>
        <div className="review-comparison-side" data-testid="review-comparison-evidence">
          <span className="review-comparison-label">Evidence</span>
          <div className="review-comparison-fields">
            {Object.entries(patch).map(([key, value]) => (
              <div key={key} className="review-field-row">
                <span className="review-field-key">{key}</span>
                <span className="review-field-value">{String(value ?? "")}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // For actionable kinds: current truth vs proposed patch
  return (
    <div className="review-comparison" data-testid="review-comparison">
      <div className="review-comparison-side" data-testid="review-comparison-current">
        <span className="review-comparison-label">Current</span>
        <p className="review-comparison-value">{proposal.rationale}</p>
      </div>
      <div className="review-comparison-side" data-testid="review-comparison-proposed">
        <span className="review-comparison-label">Proposed</span>
        <div className="review-comparison-fields">
          {Object.entries(patch).map(([key, value]) => (
            <div key={key} className="review-field-row">
              <span className="review-field-key">{key}</span>
              {editingPatch && onEditField ? (
                <input
                  className="review-field-input"
                  aria-label={`Edit ${key}`}
                  value={String(value ?? "")}
                  onChange={(e) => onEditField(key, e.target.value)}
                />
              ) : (
                <span className="review-field-value">{String(value ?? "")}</span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ── Source chips ── */

function SourceChips({ proposal }: { proposal: Proposal }) {
  const ref = proposal.targetRef;
  if (!ref) return null;
  return (
    <span className="review-source-chip" data-testid="review-source-chip" title={ref}>
      {ref.split(":").pop() || ref}
    </span>
  );
}

/* ── Conflict both-sources (WEB-STA-006) ── */

function ConflictSources({ proposal }: { proposal: Proposal }) {
  if (proposal.proposalKind !== "conflict") return null;
  const patch = proposal.patchJson;
  const sources = patch.sources ?? patch.source_refs;
  if (!Array.isArray(sources)) return null;
  return (
    <div className="review-conflict-sources" data-testid="review-conflict-sources">
      <span className="review-comparison-label">Conflicting sources</span>
      {(sources as string[]).map((src, i) => (
        <span key={i} className="review-source-chip">{String(src)}</span>
      ))}
    </div>
  );
}

/* ── Queue sidebar (wide layout) ── */

function ReviewQueue({
  ctrl,
}: {
  ctrl: ReviewController;
}) {
  const rootRef = useRef<HTMLDivElement>(null);
  useRovingRows(rootRef, { selector: ".surface-ledger-line" });

  return (
    <div className="review-queue" data-testid="review-queue" ref={rootRef}>
      <SurfaceLedger
        count={`PROPOSALS ${ctrl.openProposals.length}`}
      >
        <div role="listbox" aria-label="Review proposals">
          {ctrl.groups.map((group) => (
            <div key={group.kind} className="review-queue-group" role="group" aria-label={group.label}>
              <KindCountChip kind={group.kind} count={group.count} />
              <ul className="surface-ledger-rows">
                {group.proposals
                  .filter((p) => p.lifecycle === "open" && !ctrl.dispositions.has(p.id))
                  .map((proposal) => {
                    const globalIndex = ctrl.openProposals.indexOf(proposal);
                    const isSelected = globalIndex === ctrl.selectedIndex;
                    return (
                      <SurfaceLedgerRow
                        key={proposal.id}
                        data-testid="review-queue-item"
                        primary={
                          <span
                            data-selected={isSelected || undefined}
                            aria-current={isSelected ? "true" : undefined}
                            role="option"
                            aria-selected={isSelected}
                            aria-label={`${proposal.title}, ${kindLabel(proposal.proposalKind)}, ${globalIndex + 1} of ${ctrl.openProposals.length}`}
                          >
                            {proposal.title}
                          </span>
                        }
                        cells={
                          <span className="review-queue-materiality">
                            {proposal.materiality}
                          </span>
                        }
                        open={isSelected}
                        onToggle={() => ctrl.selectByIndex(globalIndex)}
                        lineLabel={`${proposal.title}, ${globalIndex + 1} of ${ctrl.openProposals.length}`}
                        expands={false}
                      />
                    );
                  })}
              </ul>
            </div>
          ))}
        </div>
      </SurfaceLedger>
    </div>
  );
}

/* ── Disposition summary (exhausted / checkpointed) ── */

function DispositionSummary({ ctrl }: { ctrl: ReviewController }) {
  const counts = ctrl.dispositionSummary();
  return (
    <div className="review-summary" data-testid="review-summary">
      <SurfaceSection label="Review complete">
        <div className="review-summary-counts">
          {counts.accept ? (
            <span className="surface-token" data-tone="ok" data-testid="summary-accepted">
              {counts.accept} accepted
            </span>
          ) : null}
          {counts.edit_accept ? (
            <span className="surface-token" data-tone="ok" data-testid="summary-edited">
              {counts.edit_accept} edited
            </span>
          ) : null}
          {counts.defer ? (
            <span className="surface-token" data-testid="summary-deferred">
              {counts.defer} deferred
            </span>
          ) : null}
          {counts.dismiss ? (
            <span className="surface-token" data-testid="summary-dismissed">
              {counts.dismiss} dismissed
            </span>
          ) : null}
        </div>
        {ctrl.checkpointed ? (
          <p className="review-summary-accepted" data-testid="review-accepted-notice">
            Review accepted{ctrl.acceptedAt ? ` at ${humanTime(ctrl.acceptedAt)}` : ""}
          </p>
        ) : null}
        {/* Draft update slot: honestly absent (P3) */}
        <div className="review-draft-slot" data-testid="review-draft-slot" hidden>
          Draft update (P3)
        </div>
      </SurfaceSection>
    </div>
  );
}

/* ── Verb bar ── */

function ReviewVerbBar({
  ctrl,
  dense,
}: {
  ctrl: ReviewController;
  dense?: boolean;
}) {
  const p = ctrl.selectedProposal;
  if (!p) return null;

  const isConflict = p.proposalKind === "conflict";
  const editing = ctrl.editingPatch != null;
  const deciding = ctrl.decidingId != null;

  return (
    <span className="review-verb-bar" data-testid="review-verb-bar" role="toolbar" aria-label="Review verbs">
      {/* Accept: disabled for conflicts (WEB-STA-006 / HANDLER_MAP refuse) */}
      {editing ? (
        <Button
          dense={dense}
          variant="primary"
          loading={deciding}
          disabled={isConflict}
          onClick={() => {
            if (ctrl.editingPatch) {
              void ctrl.editAcceptProposal(p.id, ctrl.editingPatch);
            }
          }}
          aria-label={`Edit and accept ${p.title}`}
        >
          Save & accept
        </Button>
      ) : (
        <Button
          dense={dense}
          variant="primary"
          loading={deciding}
          disabled={isConflict}
          onClick={() => void ctrl.acceptProposal(p.id)}
          aria-label={`Accept ${p.title}`}
        >
          Accept
        </Button>
      )}

      {/* Edit: toggle edit mode */}
      {!editing ? (
        <Button
          dense={dense}
          disabled={isConflict || deciding}
          onClick={ctrl.startEdit}
          aria-label={`Edit ${p.title}`}
        >
          Edit
        </Button>
      ) : (
        <Button
          dense={dense}
          onClick={ctrl.cancelEdit}
        >
          Cancel edit
        </Button>
      )}

      {/* Defer */}
      <span className="review-defer-group">
        <Button
          dense={dense}
          loading={deciding}
          onClick={() => void ctrl.deferProposal(p.id, ctrl.deferDate || undefined)}
          aria-label={`Defer ${p.title}`}
        >
          Defer
        </Button>
        <input
          type="date"
          className="review-defer-date"
          aria-label="Defer until date"
          value={ctrl.deferDate}
          onChange={(e) => ctrl.setDeferDate(e.target.value)}
        />
      </span>

      {/* Dismiss: no confirmation (WEB-DLT-006) */}
      <Button
        dense={dense}
        variant="ghost"
        loading={deciding}
        onClick={() => void ctrl.dismissProposal(p.id)}
        aria-label={`Dismiss ${p.title}`}
      >
        Dismiss
      </Button>
    </span>
  );
}

/* ── No-delta state (WEB-STA-004) ── */

function NoDeltaState({
  lastAcceptedAt,
}: {
  lastAcceptedAt: string | null;
}) {
  return (
    <div className="review-no-delta" data-testid="review-no-delta">
      <SurfaceState
        empty
        emptyLabel={
          lastAcceptedAt
            ? `Last reviewed ${humanTime(lastAcceptedAt)}`
            : "No reviews yet"
        }
        emptyGlyph={"⊘"}
      />
    </div>
  );
}

/* ── Main review posture ── */

export function ReviewPosture({ ctrl }: { ctrl: ReviewController }) {
  const containerRef = useRef<HTMLDivElement>(null);

  // ── Keyboard handler (WEB-CMD-002) ──
  // Letters are dead while inputs own focus (WEB-CMD-003).
  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLDivElement>) => {
      const target = e.target as HTMLElement;
      const inInput =
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable;

      // Always allow Escape (layered)
      if (e.key === "Escape") {
        e.preventDefault();
        if (ctrl.editingPatch) {
          ctrl.cancelEdit();
        } else {
          ctrl.exitReview();
        }
        return;
      }

      // Modifier combos
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        e.preventDefault();
        if (ctrl.exhausted || ctrl.allDecided) {
          void ctrl.finishReview();
        }
        return;
      }

      // Letters dead while in inputs (WEB-CMD-003)
      if (inInput) return;

      const p = ctrl.selectedProposal;

      switch (e.key) {
        case "j":
        case "ArrowDown":
          e.preventDefault();
          ctrl.selectNext();
          break;
        case "k":
        case "ArrowUp":
          e.preventDefault();
          ctrl.selectPrev();
          break;
        case " ":
          // Space: expand/focus comparison (no-op in wide, scrolls to comparison in narrow)
          e.preventDefault();
          break;
        case "a":
        case "A":
          if (p && p.proposalKind !== "conflict") {
            e.preventDefault();
            void ctrl.acceptProposal(p.id);
          }
          break;
        case "e":
        case "E":
          if (p && p.proposalKind !== "conflict") {
            e.preventDefault();
            if (ctrl.editingPatch) {
              // Save & accept
              void ctrl.editAcceptProposal(p.id, ctrl.editingPatch);
            } else {
              ctrl.startEdit();
            }
          }
          break;
        case "l":
        case "L":
          if (p) {
            e.preventDefault();
            void ctrl.deferProposal(p.id, ctrl.deferDate || undefined);
          }
          break;
        case "x":
        case "X":
          if (p) {
            e.preventDefault();
            void ctrl.dismissProposal(p.id);
          }
          break;
        case "z":
        case "Z":
          // Undo last dismiss
          if (ctrl.undoStack.length > 0) {
            e.preventDefault();
            ctrl.undoLastDismiss();
          }
          break;
      }
    },
    [ctrl],
  );

  // ── Undo notice ──
  const lastUndo = ctrl.undoStack.length > 0
    ? ctrl.undoStack[ctrl.undoStack.length - 1]
    : null;

  // ── Loading / error ──
  if (ctrl.loading && !ctrl.window) {
    return <SurfaceState loading />;
  }

  if (ctrl.error && !ctrl.window) {
    return <SurfaceState error={ctrl.error} />;
  }

  // ── Exhausted / checkpointed ──
  if (ctrl.exhausted || ctrl.checkpointed) {
    return (
      <div
        className="review-posture"
        data-testid="review-posture"
        data-phase="exhausted"
        onKeyDown={handleKeyDown}
        tabIndex={-1}
      >
        <SurfaceVerbs>
          <Button dense variant="ghost" onClick={ctrl.exitReview}>
            Close
          </Button>
          {!ctrl.checkpointed ? (
            <Button
              dense
              variant="primary"
              loading={ctrl.loading}
              onClick={() => void ctrl.finishReview()}
            >
              Finish review
            </Button>
          ) : null}
        </SurfaceVerbs>
        <DispositionSummary ctrl={ctrl} />
      </div>
    );
  }

  // ── Active review ──
  const p = ctrl.selectedProposal;

  return (
    <div
      className="review-posture"
      data-testid="review-posture"
      data-phase="reviewing"
      onKeyDown={handleKeyDown}
      tabIndex={-1}
      ref={containerRef}
      role="region"
      aria-label="Review changes"
    >
      <SurfaceVerbs
        status={
          <span className="review-position" data-testid="review-position" role="status"
            aria-live="polite"
            aria-label={
              p
                ? `Proposal ${ctrl.selectedIndex + 1} of ${ctrl.openProposals.length}, ${kindLabel(p.proposalKind)}`
                : "No proposals"
            }
          >
            {ctrl.openProposals.length > 0
              ? `${ctrl.selectedIndex + 1} / ${ctrl.openProposals.length}`
              : "0 proposals"}
          </span>
        }
      >
        <Button dense variant="ghost" onClick={ctrl.exitReview}>
          Close
        </Button>
        {ctrl.allDecided ? (
          <Button
            dense
            variant="primary"
            loading={ctrl.loading}
            onClick={() => void ctrl.finishReview()}
          >
            Finish review
          </Button>
        ) : null}
      </SurfaceVerbs>

      {/* Undo notice */}
      {lastUndo ? (
        <div className="review-undo-notice" data-testid="review-undo-notice" role="status">
          <span>Dismissed</span>
          <Button dense variant="ghost" onClick={ctrl.undoLastDismiss}>
            Undo
          </Button>
        </div>
      ) : null}

      {/* Wide: queue + comparison | Narrow: one card with footer verbs */}
      <div className="review-body">
        {/* Queue (left side on wide) */}
        <ReviewQueue ctrl={ctrl} />

        {/* Selected proposal detail (right side on wide) */}
        {p ? (
          <div className="review-detail" data-testid="review-detail">
            <ChoiceCardShell
              label={p.title}
              description={kindLabel(p.proposalKind)}
              tier={p.proposalKind}
              facts={[
                { label: "Materiality", value: p.materiality },
                { label: "Target", value: p.targetRef.split(":").pop() || p.targetRef },
              ]}
              selected
            >
              <PatchComparison
                proposal={p}
                editingPatch={ctrl.editingPatch}
                onEditField={ctrl.updateEditField}
              />
              <SourceChips proposal={p} />
              <ConflictSources proposal={p} />
            </ChoiceCardShell>

            {/* Verb bar (inline on wide) */}
            <div className="review-verbs-inline" data-testid="review-verbs-inline">
              <ReviewVerbBar ctrl={ctrl} />
            </div>
          </div>
        ) : (
          <div className="review-detail" data-testid="review-detail">
            <SurfaceState empty emptyLabel="No proposals to review" emptyGlyph={"⊘"} />
          </div>
        )}
      </div>

      {/* Footer verbs (narrow layout) */}
      <SurfaceFooter
        verbs={
          <span className="review-verbs-footer">
            <ReviewVerbBar ctrl={ctrl} dense />
          </span>
        }
        receipt={
          <span className="surface-footer-receipt-line" role="status">
            {p
              ? `REVIEW ${ctrl.selectedIndex + 1}/${ctrl.openProposals.length}`
              : "REVIEW"}
          </span>
        }
      />
    </div>
  );
}
