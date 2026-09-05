// HS-167-05 -- the Update posture recomposed on the surface library.
// DRAFTS ledger (D6): lead edit + primary + ProvenanceChip + StateChip + time + chevron.
// DeskEditor stays (sanctioned non-barrel import). CitationChips per section.
// ActionNotice for unverified claims. Dead hand-rolled blocks removed.

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
  StateChip,
  ProvenanceChip,
  ActionNotice,
  CitationChips,
  countLabel,
  humanTime,
  type ChipState,
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

/* ── Lifecycle to StateChip state mapping ── */

function lifecycleChipState(lifecycle: string): ChipState {
  if (lifecycle === "published") return "success";
  if (lifecycle === "superseded") return "failure";
  return "idle";
}

/* ── Provenance chip props from generator string ── */

function generatorChipSource(generator: string): string {
  if (generator === "deterministic") return "deterministic";
  if (generator.startsWith("model:")) return "model";
  return generator;
}

function generatorChipBoundary(generator: string): string | undefined {
  if (generator.startsWith("model:")) {
    return generator.slice("model:".length);
  }
  return undefined;
}

/* ── Per-section source row: deduplicated ref chips (D6: CitationChips grammar) ── */

function SectionSourceRow({
  claims,
  onOpen,
}: {
  claims: UpdateClaim[];
  onOpen: (ref: string) => void;
}) {
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
  const hasUnverifiedNoRef = claims.some((c) => !c.verified && c.refs.length === 0);

  if (uniqueRefs.length === 0 && !hasUnverifiedNoRef) return null;

  return (
    <div data-testid="update-source-row">
      {uniqueRefs.map(({ ref, title }) => {
        const kind = refChipLabel(ref);
        return (
          <button
            key={ref}
            type="button"
            className="desk-chip quiet"
            data-testid="update-claim-ref"
            data-ref={ref}
            data-ref-kind={refKind(ref)}
            title={`${kind}: ${ref}`}
            aria-label={`${kind}: ${title}`}
            onClick={() => onOpen(ref)}
          >
            {title}
          </button>
        );
      })}
      {hasUnverifiedNoRef ? (
        <span
          className="surface-token"
          data-tone="warn"
          data-testid="update-claim-unverified"
        >
          Contains unverified claims
        </span>
      ) : null}
    </div>
  );
}

/* ── Rendered document view: Material body + citations + ActionNotice ── */

function RenderedUpdateDocument({
  update,
  onOpenRef,
}: {
  update: ProjectUpdate;
  onOpenRef: (ref: string) => void;
}) {
  const claims = update.claims;

  // Group claims by section for per-section citation rows
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

  const hasUnverified = claims.some((c) => !c.verified);

  return (
    <div data-testid="update-document">
      {/* The rendered markdown body is the hero */}
      <div className="update-document-body" data-testid="update-document-body">
        <Material>{update.bodyMd}</Material>
      </div>

      {/* D6: unverified claim as ActionNotice in flow */}
      {hasUnverified ? (
        <div data-testid="update-unverified-banner" role="status">
          <ActionNotice tone="warn">
            Some claims in this update could not be verified
          </ActionNotice>
        </div>
      ) : null}

      {/* D6: source rows per section (CitationChips grammar, deduplicated) */}
      {sectionOrder.length > 0 ? (
        <SurfaceSection label="SOURCES">
          <div data-testid="update-sources">
            {sectionOrder.map((section) => (
              <SectionSourceRow
                key={section}
                claims={grouped[section]}
                onOpen={onOpenRef}
              />
            ))}
          </div>
        </SurfaceSection>
      ) : null}
    </div>
  );
}

/* ── Draft list view (D6: DRAFTS SurfaceLedger) ── */

function UpdateList({
  ctrl,
}: {
  ctrl: UpdateController;
}) {
  return (
    <div className="update-list" data-testid="update-list">
      <SurfaceLedger count={countLabel("DRAFTS", ctrl.updates.length)} cols="room">
        <ul className="surface-ledger-rows">
          {ctrl.updates.map((update) => {
            const tone = lifecycleTone(update.lifecycle);
            return (
              <SurfaceLedgerRow
                key={update.id}
                data-testid="update-list-item"
                expands={false}
                wrap
                lead={
                  <span className="update-lead-emblem" aria-hidden="true">
                    {"E"}
                  </span>
                }
                primary={
                  <span
                    className="update-list-row"
                    data-lifecycle={update.lifecycle}
                    data-generator={update.generator}
                    title={generatorLabel(update.generator)}
                  >
                    <span className="update-list-primary">
                      <span className="surface-token" data-tone={tone}>
                        {lifecycleLabel(update.lifecycle)}
                      </span>
                      <span className="update-list-rev">Rev {update.draftRevision}</span>
                      <span className="update-list-time">
                        {humanTime(update.publishedAt ?? update.updatedAt)}
                      </span>
                    </span>
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
                cells={
                  <ProvenanceChip
                    source={generatorChipSource(update.generator)}
                    boundary={generatorChipBoundary(update.generator)}
                  />
                }
                time={humanTime(update.publishedAt ?? update.updatedAt)}
                trailing={
                  <span aria-hidden="true" data-testid="update-list-chevron">
                    {"›"}
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

  // Posture-scoped keyboard (WEB-CMD-002)
  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLDivElement>) => {
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
        <StateChip
          state={lifecycleChipState(update.lifecycle)}
          label={lifecycleLabel(update.lifecycle)}
        />
        <ProvenanceLabel update={update} />
        <span className="surface-token">Rev {update.draftRevision}</span>
      </div>

      {/* Body: DeskEditor for drafts, Material for published */}
      {isDraft ? (
        <div className="update-body-editor" data-testid="update-body-editor">
          <DeskEditor
            value={ctrl.editBody}
            onChange={ctrl.handleEditBody}
            placeholder="Write your update"
            ariaLabel="Update body"
            autoFocus
            minHeight="200px"
          />
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
        </div>
      ) : (
        <div data-testid="update-body-readonly">
          <SurfaceSection
            label="Update"
            actions={
              <span className="surface-token" data-testid="update-readonly-reason">
                {update.lifecycle === "superseded"
                  ? "Superseded drafts are read-only"
                  : "Published updates are read-only"}
              </span>
            }
          >
            <RenderedUpdateDocument update={update} onOpenRef={onOpenRef} />
          </SurfaceSection>
        </div>
      )}

      {/* Draft claims: citations below the editor */}
      {isDraft && update.claims.length > 0 ? (
        <RenderedUpdateDocument update={update} onOpenRef={onOpenRef} />
      ) : null}

      {/* Back verb stays inside the editor (non-portalling, glass locator compat) */}
      <SurfaceVerbs>
        <Button dense variant="ghost" onClick={() => void ctrl.backToList()} data-testid="update-verb-back">
          Back
        </Button>
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
              title="May send project data to the inference provider."
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
              {countLabel("UPDATES", ctrl.updates.length)}
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
          egress={
            ctrl.current?.generator.startsWith("model:")
              ? <EgressChip label="model" scope="mixed" title={`Model: ${generatorChipBoundary(ctrl.current.generator)}`} />
              : <ProvenanceChip source="deterministic" />
          }
          receipt={
            <span className="surface-footer-receipt-line" data-testid="update-footer-receipt" role="status">
              {ctrl.current
                ? `UPDATE ${lifecycleLabel(ctrl.current.lifecycle)} · ${generatorLabel(ctrl.current.generator)}${ctrl.dirty ? " · UNSAVED" : ""}`
                : "UPDATE"}
            </span>
          }
          verbs={
            <>
              {ctrl.isDraft ? (
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
              <Button
                dense
                loading={ctrl.regenerateBusy}
                onClick={() => void ctrl.regenerate("deterministic")}
                data-testid="update-verb-regenerate"
              >
                Regenerate
              </Button>
              <Button
                dense
                loading={ctrl.copyBusy}
                onClick={() => void ctrl.copyMarkdown()}
                data-testid="update-verb-copy"
              >
                {ctrl.copyState === "copied" ? "Copied" : ctrl.copyState === "failed" ? "Copy failed" : "Copy"}
              </Button>
              {ctrl.isDraft ? (
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
            </>
          }
        />
      </div>
    );
  }

  // ── Off posture ──
  return null;
}
