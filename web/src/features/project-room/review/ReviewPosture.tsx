// HS-160-06 — the review posture: a posture in Now, judged from the keyboard.
// Wide (>=560px container): queue left, comparison right, four verbs.
// Narrow: one card at a time, persistent footer verbs (SurfaceFooter).
// No modal — WEB-IA-003.
//
// Beauty pass (HS-160-06 defects 1-7):
//  1. Card anchor is plain-words, not machine speech.
//  2. Queue rows show human text, not truncated kind strings.
//  3. Nested objects render as compact key:value, never [object Object].
//  4. Field keys are humanized; machine ids hidden in data-attrs.
//  5. Verb bar coherent row; defer is a two-step (button arms, L immediate).
//  6. Materiality is a temperature token (High/Medium/Low), not raw float.
//  7. Position stated once (header only); footer carries disposition tally.

import { useCallback, useRef, useState, type KeyboardEvent } from "react";
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
import {
  kindLabel,
  proposalAnchor,
  humanFields,
  machineAttrs,
  renderValue,
  materialityLevel,
  materialityTone,
} from "./model";
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

/** Render human-visible fields from a patch object (defects 3, 4). */
function FieldRows({
  patch,
  editingPatch,
  onEditField,
}: {
  patch: Record<string, unknown>;
  editingPatch: Record<string, unknown> | null;
  onEditField?: (key: string, value: string) => void;
}) {
  const fields = humanFields(editingPatch ?? patch);
  const attrs = machineAttrs(patch);
  return (
    <div className="review-comparison-fields" {...attrs}>
      {fields.map(({ key, label, value }) => (
        <div key={key} className="review-field-row">
          <span className="review-field-key">{label}</span>
          {editingPatch && onEditField ? (
            <input
              className="review-field-input"
              aria-label={`Edit ${label}`}
              value={renderValue(value)}
              onChange={(e) => onEditField(key, e.target.value)}
            />
          ) : (
            <span className="review-field-value">{renderValue(value)}</span>
          )}
        </div>
      ))}
    </div>
  );
}

function PatchComparison({
  proposal,
  editingPatch,
  onEditField,
}: {
  proposal: Proposal;
  editingPatch: Record<string, unknown> | null;
  onEditField?: (key: string, value: string) => void;
}) {
  const patch = proposal.patchJson;
  const isRecordOnly =
    proposal.proposalKind === "review_flag" ||
    proposal.proposalKind === "observation_attention" ||
    proposal.proposalKind === "coverage_degraded";

  if (isRecordOnly) {
    return (
      <div className="review-comparison" data-testid="review-comparison">
        <div className="review-comparison-side" data-testid="review-comparison-rationale">
          <span className="review-comparison-label">Rationale</span>
          <p className="review-comparison-value">{proposal.rationale}</p>
        </div>
        <div className="review-comparison-side" data-testid="review-comparison-evidence">
          <span className="review-comparison-label">Evidence</span>
          <FieldRows patch={patch} editingPatch={null} />
        </div>
      </div>
    );
  }

  return (
    <div className="review-comparison" data-testid="review-comparison">
      <div className="review-comparison-side" data-testid="review-comparison-current">
        <span className="review-comparison-label">Current</span>
        <p className="review-comparison-value">{proposal.rationale}</p>
      </div>
      <div className="review-comparison-side" data-testid="review-comparison-proposed">
        <span className="review-comparison-label">Proposed</span>
        <FieldRows
          patch={patch}
          editingPatch={editingPatch}
          onEditField={onEditField}
        />
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

/** Human text for a queue row: patch text / title / target name (defect 2). */
function proposalRowText(proposal: Proposal): string {
  const patch = proposal.patchJson;
  return (
    (patch.text as string) ||
    (patch.title as string) ||
    (patch.owner as string) ||
    proposal.targetRef.split(":").pop() ||
    proposal.title
  );
}

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
                    const rowText = proposalRowText(proposal);
                    const matLevel = materialityLevel(proposal.materiality);
                    const matTone = materialityTone(matLevel);
                    return (
                      <SurfaceLedgerRow
                        key={proposal.id}
                        data-testid="review-queue-item"
                        primary={
                          <span
                            className="review-queue-row-text"
                            data-selected={isSelected || undefined}
                            aria-current={isSelected ? "true" : undefined}
                            role="option"
                            aria-selected={isSelected}
                            aria-label={`${rowText}, ${kindLabel(proposal.proposalKind)}, ${globalIndex + 1} of ${ctrl.openProposals.length}`}
                            data-kind={proposal.proposalKind}
                            data-ref={proposal.targetRef}
                          >
                            {rowText}
                          </span>
                        }
                        cells={
                          <span
                            className="surface-token review-queue-materiality"
                            data-tone={matTone}
                            data-materiality={proposal.materiality}
                          >
                            {matLevel}
                          </span>
                        }
                        open={isSelected}
                        onToggle={() => ctrl.selectByIndex(globalIndex)}
                        lineLabel={`${rowText}, ${globalIndex + 1} of ${ctrl.openProposals.length}`}
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

/* ── Verb bar (defect 5: coherent row, defer two-step) ── */

function ReviewVerbBar({
  ctrl,
  dense,
  deferArmed,
  onArmDefer,
  onCancelDefer,
  onConfirmDefer,
}: {
  ctrl: ReviewController;
  dense?: boolean;
  deferArmed: boolean;
  onArmDefer: () => void;
  onCancelDefer: () => void;
  onConfirmDefer: () => void;
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

      {/* Defer: two-step -- button arms, date+confirm appears inline */}
      {deferArmed ? (
        <span className="review-defer-group" data-testid="review-defer-armed">
          <input
            type="date"
            className="review-defer-date"
            data-testid="review-defer-date"
            aria-label="Defer until date"
            value={ctrl.deferDate}
            onChange={(e) => ctrl.setDeferDate(e.target.value)}
            autoFocus
          />
          <Button
            dense={dense}
            variant="primary"
            loading={deciding}
            onClick={onConfirmDefer}
            aria-label="Confirm defer"
            data-testid="review-defer-confirm"
          >
            Confirm
          </Button>
          <Button
            dense={dense}
            variant="ghost"
            onClick={onCancelDefer}
            aria-label="Cancel defer"
          >
            Cancel
          </Button>
        </span>
      ) : (
        <Button
          dense={dense}
          loading={deciding}
          onClick={onArmDefer}
          aria-label={`Defer ${p.title}`}
        >
          Defer
        </Button>
      )}

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
  const [deferArmed, setDeferArmed] = useState(false);

  // Reset armed state when selected proposal changes
  const prevSelectedId = useRef(ctrl.selectedProposal?.id);
  if (ctrl.selectedProposal?.id !== prevSelectedId.current) {
    prevSelectedId.current = ctrl.selectedProposal?.id;
    if (deferArmed) setDeferArmed(false);
  }

  const armDefer = useCallback(() => setDeferArmed(true), []);
  const cancelDefer = useCallback(() => {
    setDeferArmed(false);
    ctrl.setDeferDate("");
  }, [ctrl]);
  const confirmDefer = useCallback(() => {
    const p = ctrl.selectedProposal;
    if (p) {
      void ctrl.deferProposal(p.id, ctrl.deferDate || undefined);
      setDeferArmed(false);
    }
  }, [ctrl]);

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
        if (deferArmed) {
          setDeferArmed(false);
          ctrl.setDeferDate("");
        } else if (ctrl.editingPatch) {
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

      // Enter confirms armed defer when in the date input
      if (e.key === "Enter" && deferArmed && inInput) {
        e.preventDefault();
        confirmDefer();
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
              void ctrl.editAcceptProposal(p.id, ctrl.editingPatch);
            } else {
              ctrl.startEdit();
            }
          }
          break;
        case "l":
        case "L":
          // Keyboard L: immediate defer (glass-compat).
          // The two-step is the button UX; L is the power-user shortcut.
          if (p) {
            e.preventDefault();
            void ctrl.deferProposal(p.id, ctrl.deferDate || undefined);
            setDeferArmed(false);
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
          if (ctrl.undoStack.length > 0) {
            e.preventDefault();
            ctrl.undoLastDismiss();
          }
          break;
      }
    },
    [ctrl, deferArmed, confirmDefer],
  );

  // ── Undo notice ──
  const lastUndo = ctrl.undoStack.length > 0
    ? ctrl.undoStack[ctrl.undoStack.length - 1]
    : null;

  // ── Disposition tally for the footer (defect 7) ──
  const dispositionTally = (): string => {
    const total = ctrl.openProposals.length;
    const summary = ctrl.dispositionSummary();
    const accepted = (summary.accept ?? 0) + (summary.edit_accept ?? 0);
    const parts: string[] = [];
    if (total > 0) parts.push(`${total} left`);
    if (accepted > 0) parts.push(`${accepted} accepted`);
    if (summary.defer) parts.push(`${summary.defer} deferred`);
    if (summary.dismiss) parts.push(`${summary.dismiss} dismissed`);
    return parts.join(" · ") || "";
  };

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
  const anchor = p ? proposalAnchor(p) : null;
  const matLevel = p ? materialityLevel(p.materiality) : null;
  const matTone = matLevel ? materialityTone(matLevel) : undefined;

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
        {p && anchor ? (
          <div className="review-detail" data-testid="review-detail">
            <ChoiceCardShell
              label={anchor.headline}
              description={anchor.subject}
              tier={p.proposalKind}
              facts={[
                { label: "Materiality", value: matLevel ?? "Low" },
                { label: "Kind", value: kindLabel(p.proposalKind) },
              ]}
              data-materiality={p.materiality}
              data-kind={p.proposalKind}
              data-ref={p.targetRef}
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
              <ReviewVerbBar
                ctrl={ctrl}
                deferArmed={deferArmed}
                onArmDefer={armDefer}
                onCancelDefer={cancelDefer}
                onConfirmDefer={confirmDefer}
              />
            </div>
          </div>
        ) : (
          <div className="review-detail" data-testid="review-detail">
            <SurfaceState empty emptyLabel="No proposals to review" emptyGlyph={"⊘"} />
          </div>
        )}
      </div>

      {/* Footer (narrow layout): disposition tally, not position (defect 7) */}
      <SurfaceFooter
        verbs={
          <span className="review-verbs-footer">
            <ReviewVerbBar
              ctrl={ctrl}
              dense
              deferArmed={deferArmed}
              onArmDefer={armDefer}
              onCancelDefer={cancelDefer}
              onConfirmDefer={confirmDefer}
            />
          </span>
        }
        receipt={
          <span className="surface-footer-receipt-line" data-testid="review-footer-tally" role="status">
            {dispositionTally()}
          </span>
        }
      />
    </div>
  );
}
