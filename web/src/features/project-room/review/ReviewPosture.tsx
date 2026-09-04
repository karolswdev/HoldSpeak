// HS-167-05 -- the review posture recomposed on the surface library.
// Full-width SurfaceLedger with expandable rows (D5). No ChoiceCardShell,
// no hand-rolled comparison layout, no hand-rolled source chips.
// Keyboard grammar UNCHANGED (j/k/a/e/l/x/z, layered Escape, Cmd+Enter).

import { useCallback, useRef, useState, type KeyboardEvent } from "react";
import { Button } from "../../../components/signal/Signal";
import {
  SurfaceFooter,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceColumns,
  SurfaceFacts,
  SurfaceSection,
  SurfaceState,
  SurfaceVerbs,
  SurfaceCode,
  StateChip,
  ProvenanceChip,
  Disclosure,
  humanTime,
  MicButton,
  type ChipState,
} from "../../../desk/surface";
import type { ReviewController } from "./useReviewController";
import type { Proposal, ProposalKind } from "./model";
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

/* ── Severity: emblem + chip state ── */

const KIND_EMBLEMS: Record<string, string> = {
  risk_attention: "▲",
  review_flag: "◆",
  observation_attention: "◉",
  conflict: "⫘",
  coverage_degraded: "⌁",
};

function severityEmblem(kind: ProposalKind): string {
  return KIND_EMBLEMS[kind] ?? "●";
}

function severityChipState(level: string): ChipState {
  if (level === "High") return "warning";
  return "idle";
}

/* ── Build display object for SurfaceFacts ── */

function patchFactsObject(patch: Record<string, unknown>): Record<string, string> {
  const result: Record<string, string> = {};
  for (const { label, value } of humanFields(patch)) {
    result[label] = renderValue(value);
  }
  return result;
}

/* ── Human text for a queue row ── */

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

/* ── Source label for ProvenanceChip ── */

function sourceLabel(proposal: Proposal): string | null {
  if (proposal.producerKind) return proposal.producerKind;
  const ref = proposal.targetRef;
  if (!ref) return null;
  const colon = ref.indexOf(":");
  if (colon > 0) return ref.slice(0, colon).replace(/_/g, " ");
  return null;
}

/* ── Edit fields (D5: each field carries MicButton) ── */

function EditFields({
  editingPatch,
  onEditField,
}: {
  editingPatch: Record<string, unknown>;
  onEditField: (key: string, value: string) => void;
}) {
  const fields = humanFields(editingPatch);
  return (
    <div className="review-edit-fields">
      {fields.map(({ key, label, value }) => (
        <div key={key} className="review-edit-row">
          <label className="review-edit-label">{label}</label>
          <span className="review-edit-input-wrap">
            <input
              className="review-edit-input"
              aria-label={`Edit ${label}`}
              value={renderValue(value)}
              onChange={(e) => onEditField(key, e.target.value)}
            />
            <MicButton
              draftScope={`review-edit-${key}`}
              onText={(text) => onEditField(key, text)}
            />
          </span>
        </div>
      ))}
    </div>
  );
}

/* ── Expanded detail for a selected row (D5: inline in the ledger) ── */

function ExpandedDetail({
  proposal,
  ctrl,
  deferArmed,
  onArmDefer,
  onCancelDefer,
  onConfirmDefer,
}: {
  proposal: Proposal;
  ctrl: ReviewController;
  deferArmed: boolean;
  onArmDefer: () => void;
  onCancelDefer: () => void;
  onConfirmDefer: () => void;
}) {
  const patch = proposal.patchJson;
  const anchor = proposalAnchor(proposal);
  const matLevel = materialityLevel(proposal.materiality);
  const attrs = machineAttrs(patch);

  const isRecordOnly =
    proposal.proposalKind === "review_flag" ||
    proposal.proposalKind === "observation_attention" ||
    proposal.proposalKind === "coverage_degraded";

  const isConflict = proposal.proposalKind === "conflict";
  const editing = ctrl.editingPatch != null;
  const deciding = ctrl.decidingId != null;

  // The PROPOSED side: SurfaceFacts or edit fields
  const proposedContent = editing && ctrl.editingPatch ? (
    <EditFields editingPatch={ctrl.editingPatch} onEditField={ctrl.updateEditField} />
  ) : (
    <SurfaceFacts value={patchFactsObject(patch)} />
  );

  return (
    <div className="review-expanded" data-testid="review-detail" {...attrs}>
      {/* Headline + subject */}
      <span className="review-detail-headline" data-testid="review-detail-headline">
        {anchor.headline}
      </span>
      {anchor.subject ? (
        <span className="review-detail-subject" data-testid="review-detail-subject">
          {anchor.subject}
        </span>
      ) : null}

      {/* Chips: Materiality + Kind */}
      <span className="review-detail-chips">
        <StateChip state={severityChipState(matLevel)} label={`Materiality ${matLevel}`} />
        <StateChip state="idle" label={`Kind ${kindLabel(proposal.proposalKind)}`} />
      </span>

      {/* Comparison: CURRENT / PROPOSED */}
      <div data-testid="review-comparison">
        {isConflict ? (
          /* D3/D5: conflict shows sources as ProvenanceChips, hashes in a Disclosure */
          (() => {
            const sources = patch.sources ?? patch.source_refs;
            const sourceList = Array.isArray(sources) ? (sources as string[]) : [];
            // Any hash-shaped values from the patch (not sources or source_refs)
            const hashEntries = Object.entries(patch).filter(
              ([k]) => k !== "sources" && k !== "source_refs",
            );
            return (
              <div data-testid="review-conflict-sources">
                <SurfaceSection label="CONFLICTING SOURCES">
                  <span className="review-detail-chips">
                    {sourceList.map((src, i) => (
                      <ProvenanceChip key={i} source={String(src)} />
                    ))}
                  </span>
                </SurfaceSection>
                {hashEntries.length > 0 ? (
                  <Disclosure label={`hashes ${hashEntries.length}`}>
                    <SurfaceCode>
                      {hashEntries.map(([k, v]) => `${k}: ${renderValue(v)}`).join("\n")}
                    </SurfaceCode>
                  </Disclosure>
                ) : null}
              </div>
            );
          })()
        ) : (
          <SurfaceColumns
            main={
              <SurfaceSection label={isRecordOnly ? "RATIONALE" : "CURRENT"}>
                <p className="review-rationale-text">{proposal.rationale}</p>
              </SurfaceSection>
            }
            side={
              <SurfaceSection label={isRecordOnly ? "EVIDENCE" : "PROPOSED"}>
                {proposedContent}
              </SurfaceSection>
            }
          />
        )}
      </div>

      {/* Source chip (non-conflict) */}
      {!isConflict && sourceLabel(proposal) ? (
        <ProvenanceChip source={sourceLabel(proposal)!} />
      ) : null}

      {/* ID as quiet lowercase mono token inside the fold */}
      <span className="review-detail-id">{proposal.id.toLowerCase()}</span>

      {/* Verb bar (D5: inline in the expanded row) */}
      <div className="review-verbs-inline" data-testid="review-verbs-inline">
        <span className="review-verb-bar" data-testid="review-verb-bar" role="toolbar" aria-label="Review verbs">
          {editing ? (
            <Button
              variant="primary"
              loading={deciding}
              disabled={isConflict}
              onClick={() => {
                if (ctrl.editingPatch) {
                  void ctrl.editAcceptProposal(proposal.id, ctrl.editingPatch);
                }
              }}
              aria-label={`Edit and accept ${proposal.title}`}
            >
              Save & accept
            </Button>
          ) : (
            <Button
              variant="primary"
              loading={deciding}
              disabled={isConflict}
              onClick={() => void ctrl.acceptProposal(proposal.id)}
              aria-label={`Accept ${proposal.title}`}
            >
              Accept
            </Button>
          )}

          {!editing ? (
            <Button
              disabled={isConflict || deciding}
              onClick={ctrl.startEdit}
              aria-label={`Edit ${proposal.title}`}
            >
              Edit
            </Button>
          ) : (
            <Button onClick={ctrl.cancelEdit}>Cancel edit</Button>
          )}

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
                variant="primary"
                loading={deciding}
                onClick={onConfirmDefer}
                aria-label="Confirm defer"
                data-testid="review-defer-confirm"
              >
                Confirm
              </Button>
              <Button variant="ghost" onClick={onCancelDefer} aria-label="Cancel defer">
                Cancel
              </Button>
            </span>
          ) : (
            <Button
              loading={deciding}
              onClick={onArmDefer}
              aria-label={`Defer ${proposal.title}`}
            >
              Defer
            </Button>
          )}

          <Button
            variant="ghost"
            loading={deciding}
            onClick={() => void ctrl.dismissProposal(proposal.id)}
            aria-label={`Dismiss ${proposal.title}`}
          >
            Dismiss
          </Button>
        </span>
      </div>
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
        <div className="review-draft-slot" data-testid="review-draft-slot" hidden>
          Draft update (P3)
        </div>
      </SurfaceSection>
    </div>
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

  // ── Active review: full-width SurfaceLedger with expandable rows ──
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

      {/* D5: full-width SurfaceLedger, SurfaceSection per kind, expandable rows */}
      <div data-testid="review-queue">
      <SurfaceLedger count={`PROPOSALS ${ctrl.openProposals.length}`} cols="room">
        <div role="listbox" aria-label="Review proposals">
          {ctrl.groups.map((group) => {
            const openInGroup = group.proposals.filter(
              (gp) => gp.lifecycle === "open" && !ctrl.dispositions.has(gp.id),
            );
            if (openInGroup.length === 0) return null;
            return (
              <section key={group.kind} className="surface-section review-kind-section" data-testid="review-kind-group">
                <header className="surface-section-head">
                  <h3 data-testid="review-kind-label">{kindLabel(group.kind)}</h3>
                  <span data-testid="review-kind-count" className="surface-token">
                    {openInGroup.length}
                  </span>
                </header>
                <ul className="surface-ledger-rows">
                  {openInGroup.map((proposal) => {
                    const globalIndex = ctrl.openProposals.indexOf(proposal);
                    const isSelected = globalIndex === ctrl.selectedIndex;
                    const rowText = proposalRowText(proposal);
                    const matLevel = materialityLevel(proposal.materiality);
                    const matTone = materialityTone(matLevel);
                    return (
                      <SurfaceLedgerRow
                        key={proposal.id}
                        data-testid="review-queue-item"
                        wrap
                        lead={
                          <span
                            className="review-severity-emblem"
                            data-tone={matTone}
                            aria-hidden="true"
                          >
                            {severityEmblem(proposal.proposalKind)}
                          </span>
                        }
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
                          <>
                            <span
                              className="surface-token review-queue-materiality"
                              data-tone={matTone}
                              data-materiality={proposal.materiality}
                            >
                              {matLevel}
                            </span>
                            {sourceLabel(proposal) ? (
                              <ProvenanceChip source={sourceLabel(proposal)!} />
                            ) : null}
                          </>
                        }
                        time={humanTime(proposal.patchJson.due as string || "")}
                        trailing={
                          <span className="review-row-chevron" aria-hidden="true">
                            {isSelected ? "▾" : "▸"}
                          </span>
                        }
                        open={isSelected}
                        onToggle={() => ctrl.selectByIndex(globalIndex)}
                        lineLabel={`${rowText}, ${globalIndex + 1} of ${ctrl.openProposals.length}`}
                      >
                        {/* D5: expanded detail inline in the ledger row */}
                        <ExpandedDetail
                          proposal={proposal}
                          ctrl={ctrl}
                          deferArmed={deferArmed}
                          onArmDefer={armDefer}
                          onCancelDefer={cancelDefer}
                          onConfirmDefer={confirmDefer}
                        />
                      </SurfaceLedgerRow>
                    );
                  })}
                </ul>
              </section>
            );
          })}
        </div>
      </SurfaceLedger>
      </div>

      {ctrl.openProposals.length === 0 ? (
        <SurfaceState empty emptyLabel="No proposals to review" emptyGlyph={"⊘"} />
      ) : null}

      {/* Footer: tally + Close (D5) */}
      <SurfaceFooter
        verbs={
          <Button dense variant="ghost" onClick={ctrl.exitReview}>
            Close
          </Button>
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
