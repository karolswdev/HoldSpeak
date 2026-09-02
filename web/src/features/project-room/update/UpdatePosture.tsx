// HS-162-05 -- the Update posture: draft list, editor, claim chips,
// five verbs, generator provenance, marked spans, egress badge.
// Pays 160's S-4 debt: claim chip activation OPENS the source.
// No modals. Mic on the editor. Surface barrel imports only.
//
// THE EDITOR IS THE NOTES EDITOR (DeskEditor — CodeMirror markdown).
// THE PUBLISHED VIEW IS THE RENDERED DOCUMENT (Material) with claims
// as subtle per-section source rows (deduplicated).

import { useCallback, type KeyboardEvent } from "react";
import { Button } from "../../../components/signal/Signal";
import { DeskEditor } from "../../../desk/components/DeskEditor";
import {
  SurfaceFooter,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceSection,
  SurfaceState,
  SurfaceVerbs,
  EgressChip,
  MicButton,
  Material,
  humanTime,
} from "../../../desk/surface";
import { openSourceRef } from "../../../desk/surface/citations";
import type { UpdateController } from "./useUpdateController";
import type { ProjectUpdate, UpdateClaim } from "./model";
import {
  claimChipTitle,
  generatorLabel,
  humanFallbackReason,
  lifecycleLabel,
  lifecycleTone,
  provenancePhrase,
  refChipLabel,
  refKind,
} from "./model";
import "./update-posture.css";

/* ── Per-section source row: deduplicated ref chips for a section ── */

function SectionSourceRow({
  claims,
  onOpen,
}: {
  claims: UpdateClaim[];
  onOpen: (ref: string) => void;
}) {
  // Collect unique refs; carry the FIRST claim's text per ref for the label.
  const seen = new Set<string>();
  const uniqueRefs: { ref: string; title: string }[] = [];
  for (const claim of claims) {
    for (const ref of claim.refs) {
      if (!seen.has(ref)) {
        seen.add(ref);
        const derived = claimChipTitle(claim.text);
        uniqueRefs.push({
          ref,
          title: derived ?? refChipLabel(ref),
        });
      }
    }
  }
  // Also surface unverified claims that have no refs
  const hasUnverifiedNoRef = claims.some((c) => !c.verified && c.refs.length === 0);

  if (uniqueRefs.length === 0 && !hasUnverifiedNoRef) return null;

  return (
    <div className="update-source-row" data-testid="update-source-row">
      {uniqueRefs.map(({ ref, title }) => {
        const kind = refChipLabel(ref);
        return (
          <button
            key={ref}
            type="button"
            className="desk-chip quiet update-claim-ref"
            data-testid="update-claim-ref"
            data-ref={ref}
            data-ref-kind={refKind(ref)}
            title={`${kind}: ${ref}`}
            aria-label={`${kind} — ${title}`}
            onClick={() => onOpen(ref)}
          >
            {title}
          </button>
        );
      })}
      {hasUnverifiedNoRef ? (
        <span
          className="surface-token update-unverified-notice"
          data-tone="warn"
          data-testid="update-claim-unverified"
        >
          Contains unverified claims
        </span>
      ) : null}
    </div>
  );
}

/* ── Rendered document view: Material body + subtle claim affordances ── */

function RenderedUpdateDocument({
  update,
  onOpenRef,
}: {
  update: ProjectUpdate;
  onOpenRef: (ref: string) => void;
}) {
  const claims = update.claims;

  // Group claims by section for per-section source rows
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

  // Check for any unverified claims to show a notice in the body
  const hasUnverified = claims.some((c) => !c.verified);

  return (
    <div className="update-document" data-testid="update-document">
      {/* The rendered markdown body is the hero */}
      <div className="update-document-body" data-testid="update-document-body">
        <Material>{update.bodyMd}</Material>
      </div>

      {/* Unverified notice when applicable */}
      {hasUnverified ? (
        <div className="update-unverified-banner" data-testid="update-unverified-banner" role="status">
          <span className="surface-token" data-tone="warn">
            Some claims in this update could not be verified
          </span>
        </div>
      ) : null}

      {/* Per-section source rows: subtle, deduplicated */}
      {sectionOrder.length > 0 ? (
        <div className="update-sources" data-testid="update-sources">
          <span className="update-sources-label surface-token">Sources</span>
          {sectionOrder.map((section) => (
            <SectionSourceRow
              key={section}
              claims={grouped[section]}
              onOpen={onOpenRef}
            />
          ))}
        </div>
      ) : null}
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
                    title={generatorLabel(update.generator)}
                  >
                    {/* Primary line: lifecycle + rev + time */}
                    <span className="update-list-primary">
                      <span className="surface-token" data-tone={tone}>
                        {lifecycleLabel(update.lifecycle)}
                      </span>
                      <span className="update-list-rev">Rev {update.draftRevision}</span>
                      <span className="update-list-time">
                        {humanTime(update.publishedAt ?? update.updatedAt)}
                      </span>
                    </span>
                    {/* Secondary line: provenance in plain words */}
                    <span className="update-list-secondary" data-testid="update-list-provenance">
                      {provenancePhrase(update.generator)}
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

  // Posture-scoped keyboard (WEB-CMD-002)
  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLDivElement>) => {
      // DeskEditor handles its own Escape; only catch it outside the editor
      const target = e.target as HTMLElement;
      const inEditor =
        target.closest?.(".cm-editor") != null ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable;

      if (e.key === "Escape" && !inEditor) {
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

      {/* Body: DeskEditor for drafts, Material rendered document for published */}
      {isDraft ? (
        <div className="update-body-editor" data-testid="update-body-editor">
          <div className="update-body-editor-mic">
            <MicButton
              draftScope={`update-editor-${update.id}`}
              onText={(text) => {
                ctrl.handleEditBody(
                  ctrl.editBody ? `${ctrl.editBody}\n${text}` : text,
                );
              }}
            />
          </div>
          <DeskEditor
            value={ctrl.editBody}
            onChange={ctrl.handleEditBody}
            placeholder="Write your update"
            ariaLabel="Update body"
            autoFocus
            minHeight="200px"
          />
        </div>
      ) : (
        <div data-testid="update-body-readonly">
          <SurfaceSection
            label="Update"
            actions={
              <span className="surface-token" data-testid="update-readonly-reason">
                Published updates are read-only
              </span>
            }
          >
            <RenderedUpdateDocument update={update} onOpenRef={onOpenRef} />
          </SurfaceSection>
        </div>
      )}

      {/* Draft claims: subtle source rows below the editor */}
      {isDraft && update.claims.length > 0 ? (
        <RenderedUpdateDocument update={update} onOpenRef={onOpenRef} />
      ) : null}

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
