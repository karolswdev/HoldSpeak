// HS-162-05 -- the Update posture: draft list, editor, claim chips,
// five verbs, generator provenance, marked spans, egress badge.
// Pays 160's S-4 debt: claim chip activation OPENS the source.
// No modals. Mic on the editor. Surface barrel imports only.

import { useCallback, useRef, type KeyboardEvent } from "react";
import { Button } from "../../../components/signal/Signal";
import {
  SurfaceFooter,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceSection,
  SurfaceState,
  SurfaceVerbs,
  EgressChip,
  MicButton,
  humanTime,
} from "../../../desk/surface";
import { openSourceRef } from "../../../desk/surface/citations";
import type { UpdateController } from "./useUpdateController";
import type { ProjectUpdate, UpdateClaim } from "./model";
import {
  generatorLabel,
  humanFallbackReason,
  lifecycleLabel,
  lifecycleTone,
  refChipLabel,
  refKind,
} from "./model";
import "./update-posture.css";

/* ── Claim chip: hover names refs, click OPENS the source ── */

function ClaimChip({
  claim,
  onOpen,
}: {
  claim: UpdateClaim;
  onOpen: (ref: string) => void;
}) {
  const isUnverified = !claim.verified;
  const refsTitle = claim.refs.length > 0
    ? claim.refs.join(", ")
    : "No evidence refs";

  return (
    <span
      className={`update-claim-chip${isUnverified ? " is-unverified" : ""}`}
      data-testid="update-claim-chip"
      data-span-id={claim.spanId}
      data-verified={claim.verified}
      data-section={claim.section}
    >
      {isUnverified ? (
        <span className="update-claim-marker" data-testid="update-claim-unverified">
          [UNVERIFIED]
        </span>
      ) : null}
      <span className="update-claim-text">{claim.text}</span>
      {claim.refs.map((ref) => (
        <button
          key={ref}
          type="button"
          className="desk-chip quiet update-claim-ref"
          data-testid="update-claim-ref"
          data-ref={ref}
          data-ref-kind={refKind(ref)}
          title={ref}
          aria-label={`${refChipLabel(ref)}: ${ref}`}
          onClick={() => onOpen(ref)}
        >
          {refChipLabel(ref)}
        </button>
      ))}
      {claim.refs.length === 0 ? (
        <span
          className="desk-chip quiet update-claim-ref is-empty"
          title={refsTitle}
        >
          no ref
        </span>
      ) : null}
    </span>
  );
}

/* ── Claims grouped by section ── */

function ClaimsBySection({
  claims,
  onOpenRef,
}: {
  claims: UpdateClaim[];
  onOpenRef: (ref: string) => void;
}) {
  if (claims.length === 0) {
    return (
      <SurfaceState
        empty
        emptyLabel="No claims in this update"
        emptyGlyph={"▤"}
      />
    );
  }

  // Group by section, preserving order of first appearance
  const sectionOrder: string[] = [];
  const grouped: Record<string, UpdateClaim[]> = {};
  for (const claim of claims) {
    const s = claim.section || "other";
    if (!grouped[s]) {
      grouped[s] = [];
      sectionOrder.push(s);
    }
    grouped[s].push(claim);
  }

  return (
    <div className="update-claims" data-testid="update-claims">
      {sectionOrder.map((section) => (
        <div key={section} className="update-claims-section" data-testid="update-claims-section">
          <span className="surface-token update-claims-section-label">
            {section.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase())}
          </span>
          <div className="update-claims-list">
            {grouped[section].map((claim) => (
              <ClaimChip
                key={claim.spanId}
                claim={claim}
                onOpen={onOpenRef}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── Draft list view ── */

function UpdateList({
  ctrl,
}: {
  ctrl: UpdateController;
}) {
  return (
    <div className="update-list" data-testid="update-list">
      <SurfaceLedger count={`UPDATES ${ctrl.updates.length}`}>
        <ul className="surface-ledger-rows">
          {ctrl.updates.map((update) => {
            const tone = lifecycleTone(update.lifecycle);
            return (
              <SurfaceLedgerRow
                key={update.id}
                data-testid="update-list-item"
                primary={
                  <span
                    className="update-list-row"
                    data-lifecycle={update.lifecycle}
                    data-generator={update.generator}
                  >
                    <span className="surface-token" data-tone={tone}>
                      {lifecycleLabel(update.lifecycle)}
                    </span>
                    <span className="update-list-generator">
                      {generatorLabel(update.generator)}
                    </span>
                    {update.fallbackReason ? (
                      <span
                        className="surface-token"
                        data-tone="warn"
                        data-testid="update-fallback-reason"
                      >
                        {humanFallbackReason(update.fallbackReason)}
                      </span>
                    ) : null}
                  </span>
                }
                cells={
                  <span className="update-list-meta">
                    <span className="surface-token">
                      Rev {update.draftRevision}
                    </span>
                    {update.publishedAt ? (
                      <span>{humanTime(update.publishedAt)}</span>
                    ) : (
                      <span>{humanTime(update.updatedAt)}</span>
                    )}
                  </span>
                }
                onToggle={() => ctrl.openUpdate(update)}
              />
            );
          })}
        </ul>
      </SurfaceLedger>
    </div>
  );
}

/* ── Generator provenance chip ── */

function ProvenanceLabel({ update }: { update: ProjectUpdate }) {
  const fallbackLabel = humanFallbackReason(update.fallbackReason);
  return (
    <span className="update-provenance" data-testid="update-provenance">
      <span className="surface-token" data-testid="update-generator-label">
        {generatorLabel(update.generator)}
      </span>
      {fallbackLabel ? (
        <span
          className="surface-token"
          data-tone="warn"
          data-testid="update-fallback-reason"
        >
          {fallbackLabel}
        </span>
      ) : null}
    </span>
  );
}

/* ── The editor face: body, claims, verbs ── */

function UpdateEditor({
  ctrl,
  onOpenRef,
}: {
  ctrl: UpdateController;
  onOpenRef: (ref: string) => void;
}) {
  const update = ctrl.current;
  if (!update) return null;

  const isDraft = ctrl.isDraft;
  const isPublished = ctrl.isPublished;
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Posture-scoped keyboard (WEB-CMD-002)
  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLDivElement>) => {
      if (e.key === "Escape") {
        e.preventDefault();
        void ctrl.backToList();
        return;
      }
      if ((e.metaKey || e.ctrlKey) && e.key === "s") {
        e.preventDefault();
        if (isDraft && ctrl.dirty) void ctrl.save();
        return;
      }
    },
    [ctrl, isDraft],
  );

  return (
    <div
      className="update-editor"
      data-testid="update-editor"
      data-lifecycle={update.lifecycle}
      onKeyDown={handleKeyDown}
      tabIndex={-1}
    >
      {/* Provenance + lifecycle band */}
      <div className="update-editor-band" data-testid="update-editor-band">
        <span className="surface-token" data-tone={lifecycleTone(update.lifecycle)}>
          {lifecycleLabel(update.lifecycle)}
        </span>
        <ProvenanceLabel update={update} />
        <span className="surface-token">Rev {update.draftRevision}</span>
      </div>

      {/* Body editor: editable for drafts, read-only for published */}
      <SurfaceSection
        label="Body"
        actions={
          isPublished ? (
            <span className="surface-token" data-testid="update-readonly-reason">
              Published updates are read-only
            </span>
          ) : null
        }
      >
        {isDraft ? (
          <div className="update-body-editor" data-testid="update-body-editor">
            <div className="update-body-editor-toolbar">
              <MicButton
                draftScope={`update-editor-${update.id}`}
                onText={(text) => {
                  ctrl.handleEditBody(
                    ctrl.editBody ? `${ctrl.editBody}\n${text}` : text,
                  );
                  textareaRef.current?.focus();
                }}
              />
            </div>
            <textarea
              ref={textareaRef}
              className="update-body-textarea"
              data-testid="update-body-textarea"
              aria-label="Update body"
              value={ctrl.editBody}
              rows={Math.max(8, ctrl.editBody.split("\n").length + 2)}
              onChange={(e) => ctrl.handleEditBody(e.target.value)}
            />
          </div>
        ) : (
          <div className="update-body-readonly" data-testid="update-body-readonly">
            <pre className="update-body-pre">{update.bodyMd}</pre>
          </div>
        )}
      </SurfaceSection>

      {/* Claims inline: each claim shows its refs as chips */}
      <SurfaceSection label="Claims">
        <ClaimsBySection claims={update.claims} onOpenRef={onOpenRef} />
      </SurfaceSection>

      {/* Verb bar */}
      <SurfaceVerbs>
        {/* Back to list */}
        <Button dense variant="ghost" onClick={() => void ctrl.backToList()}>
          Back
        </Button>

        {/* Save (draft only) */}
        {isDraft ? (
          <Button
            dense
            loading={ctrl.saveBusy}
            disabled={!ctrl.dirty}
            onClick={() => void ctrl.save()}
            data-testid="update-verb-save"
          >
            Save
          </Button>
        ) : null}

        {/* Regenerate */}
        <Button
          dense
          loading={ctrl.regenerateBusy}
          onClick={() => void ctrl.regenerate("deterministic")}
          data-testid="update-verb-regenerate"
        >
          Regenerate
        </Button>

        {/* Copy Markdown */}
        <Button
          dense
          loading={ctrl.copyBusy}
          onClick={() => void ctrl.copyMarkdown()}
          data-testid="update-verb-copy"
        >
          {ctrl.copyState === "copied" ? "Copied" : ctrl.copyState === "failed" ? "Copy failed" : "Copy Markdown"}
        </Button>

        {/* Publish (draft only, consequential styling) */}
        {isDraft ? (
          <Button
            dense
            variant="primary"
            loading={ctrl.publishBusy}
            onClick={() => void ctrl.publish()}
            data-testid="update-verb-publish"
          >
            Publish
          </Button>
        ) : null}
      </SurfaceVerbs>
    </div>
  );
}

/* ── Main Update posture ── */

export function UpdatePosture({ ctrl }: { ctrl: UpdateController }) {
  const onOpenRef = useCallback((ref: string) => {
    openSourceRef(ref);
  }, []);

  // ── Loading / error ──
  if (ctrl.loading && ctrl.posture === "off") {
    return <SurfaceState loading />;
  }

  // ── List view ──
  if (ctrl.posture === "list") {
    return (
      <div className="update-posture" data-testid="update-posture" data-phase="list">
        <SurfaceVerbs>
          <Button dense variant="ghost" onClick={ctrl.exitUpdates}>
            Close
          </Button>
          {/* Draft verbs with generator choice */}
          <Button
            dense
            loading={ctrl.draftBusy}
            onClick={() => void ctrl.draft("deterministic")}
            data-testid="update-verb-draft-deterministic"
          >
            Draft
          </Button>
          <span className="update-draft-model-action" data-testid="update-draft-model-action">
            <Button
              dense
              loading={ctrl.draftBusy}
              onClick={() => void ctrl.draft("model")}
              data-testid="update-verb-draft-model"
            >
              Draft with model
            </Button>
            <EgressChip
              label="local + cloud"
              scope="mixed"
              title="Model drafting may send project data to the configured inference provider."
              data-testid="update-egress-chip"
            />
          </span>
        </SurfaceVerbs>

        {ctrl.error ? (
          <SurfaceState error={ctrl.error} onRetry={() => void ctrl.enterUpdates()} />
        ) : null}

        {ctrl.updates.length === 0 && !ctrl.loading ? (
          <SurfaceState
            empty
            emptyLabel="No updates yet. Draft the first one."
            emptyGlyph={"▤"}
          />
        ) : (
          <UpdateList ctrl={ctrl} />
        )}

        <SurfaceFooter
          receipt={
            <span className="surface-footer-receipt-line" data-testid="update-footer-receipt" role="status">
              {`UPDATES ${ctrl.updates.length}`}
            </span>
          }
        />
      </div>
    );
  }

  // ── Editor view ──
  if (ctrl.posture === "editor") {
    return (
      <div className="update-posture" data-testid="update-posture" data-phase="editor">
        {ctrl.error ? (
          <SurfaceState error={ctrl.error} />
        ) : null}

        <UpdateEditor ctrl={ctrl} onOpenRef={onOpenRef} />

        <SurfaceFooter
          receipt={
            <span className="surface-footer-receipt-line" data-testid="update-footer-receipt" role="status">
              {ctrl.current
                ? `UPDATE ${lifecycleLabel(ctrl.current.lifecycle)} · ${generatorLabel(ctrl.current.generator)}${ctrl.dirty ? " · UNSAVED" : ""}`
                : "UPDATE"}
            </span>
          }
        />
      </div>
    );
  }

  // ── Off posture (should not render) ──
  return null;
}
