// HS-167-05 -- the Update posture recomposed on the surface library.
// UPDATES ledger (D6; PHILO-9-03 F11): lead edit + primary + ProvenanceChip + StateChip + time + chevron.
// DeskEditor stays (sanctioned non-barrel import). CitationChips per section.
// ActionNotice for unverified claims. Dead hand-rolled blocks removed.

import { useCallback, useEffect, useState, type KeyboardEvent } from "react";
import { Button, TextArea } from "../../../components/signal/Signal";
import {
  SurfaceFooter,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceSection,
  SurfaceState,
  SurfaceVerbs,
  MicButton,
  Material,
  StateChip,
  DotWord,
  ActionNotice,
  CitationChips,
  ClaimAxes as LibraryClaimAxes,
  EngineLine,
  RunLine,
  countLabel,
  humanTime,
} from "../../../desk/surface";
import { openRef } from "../../../desk/openObject";
import type { EnginePass, UpdateController } from "./useUpdateController";
import type { ProjectUpdate, UpdateClaim } from "./model";
import { claimSends } from "./model";
import {
  claimChipTitle,
  generatorLabel,
  humanFallbackReason,
  lifecycleLabel,
  provenancePhrase,
  refChipLabel,
  refIdentityLabel,
  refKind,
} from "./model";
import "./update-posture.css";
import { ListChips, PublishedWells } from "../../channels/SendWell";
import { openSurfaceOr } from "../../../desk/shell";
import { useEngine, refreshEngine } from "../../../desk/hooks/useEngine";
import { spriteUrl } from "../../../desk/sprites";

/** The capability that drafts a project update (`project_update_service`). */
const UPDATE_DRAFT_CAPABILITY = "project.update_draft";


/* PHILO-10-04 (the owner's A2 ruling, 2026-09-29): the SEND well and the
   one DELIVERY history live in features/channels/SendWell.tsx; the record
   word is DELIVERY ×N / DELIVERY N (the same counts, `isDelivered`). */

/** W5-WORDS: the lifecycle's dot (published green, superseded red). */
function lifecycleDotTone(lifecycle: string): "ok" | "fail" | "idle" {
  if (lifecycle === "published") return "ok";
  if (lifecycle === "superseded") return "fail";
  return "idle";
}



/** PHILO-15 B72: a model draft names its model; never the assignment id.
 *  Owner ruling 2026-10-25: by name only, no host and no place word on a
 *  working window (Settings ▸ Engines says where the model runs). */
export function generatorChipBoundary(update: {
  generator: string; generatorModel?: string | null; generatorHost?: string | null;
}): string | undefined {
  if (!update.generator.startsWith("model:")) return undefined;
  const model = String(update.generatorModel ?? "").trim().toUpperCase();
  return model || undefined;
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
  const uniqueRefs: { ref: string; title: string; verified: boolean }[] = [];
  for (const claim of claims) {
    for (const ref of claim.refs) {
      if (!seen.has(ref)) {
        seen.add(ref);
        const derived = claimChipTitle(claim.text);
        uniqueRefs.push({
          ref,
          title: derived ?? refChipLabel(ref),
          // HS-200-06: a claim carrying the C2 axes states its support
          // once, inline; the legacy marker stays for records without.
          verified: claim.verified || claim.hasAxes,
        });
      }
    }
  }
  const unverifiedNoRef = claims.filter(
    (c) => !c.verified && !c.hasAxes && c.refs.length === 0,
  );

  if (uniqueRefs.length === 0 && unverifiedNoRef.length === 0) return null;

  return (
    <div data-testid="update-source-row">
      {uniqueRefs.map(({ ref, title, verified }) => {
        const kind = refChipLabel(ref);
        return (
          <span key={ref} className="update-claim-chip-group">
            <Button variant="ghost" dense
              className="desk-chip quiet"
              data-testid="update-claim-ref"
              data-ref={ref}
              data-ref-kind={refKind(ref)}
              title={`${kind}: ${ref}`}
              aria-label={`${kind}: ${title}`}
              onClick={() => onOpen(ref)}
            >
              {title}
            </Button>
            {!verified ? (
              <span data-testid="update-claim-unverified">
                <StateChip state="failure" label="UNVERIFIED" />
              </span>
            ) : null}
          </span>
        );
      })}
      {unverifiedNoRef.map((claim) => (
        <span key={claim.spanId} data-testid="update-claim-unverified">
          <StateChip state="failure" label="UNVERIFIED" />
        </span>
      ))}
    </div>
  );
}

/* ── HS-200-06 (C2): the three axes on one claim — the library species
   (`ClaimAxes`, promoted by HS-200-11); the update posture keeps its ids. ── */

function ClaimAxes({ claim }: { claim: UpdateClaim }) {
  if (!claim.hasAxes) return null;
  return (
    <LibraryClaimAxes
      kind={claim.kind}
      support={claim.support}
      acceptance={claim.acceptance}
      supportEdited={Boolean(claim.supportRecord?.invalidatedAt)}
      supportMigrated={Boolean(claim.supportMappingVersion)}
      unknowns={claim.unknowns}
      testIdPrefix="update-claim"
      className="update-claim-axes"
    />
  );
}

/* ── HS-173-02: Inline claims view — each sentence with its chip(s) ── */

function InlineClaimsView({
  claims,
  onOpen,
  review,
}: {
  claims: UpdateClaim[];
  onOpen: (ref: string) => void;
  /** PHILO-15 B64: the owner's Accept / Reject (a draft only). */
  review?: { busy: string | null; receipt: string | null; act: (spanId: string, a: "accepted" | "rejected") => void };
}) {
  if (claims.length === 0) return null;

  return (
    <div className="update-inline-claims" data-testid="update-inline-claims">
      {review?.receipt ? (
        <span className="surface-token" role="status" data-testid="update-claim-receipt">{review.receipt}</span>
      ) : null}
      {claims.map((claim) => (
        <div key={claim.spanId} className="update-inline-claim" data-testid="update-inline-claim"
          data-span-id={claim.spanId} data-sends={claimSends(claim) ? "true" : "false"}>
          <span className="update-inline-claim-text">{claim.text}</span>
          {claim.refs.map((ref) => {
            const label = refIdentityLabel(ref);
            return (
              <Button variant="ghost" dense
                key={ref}
                className="desk-chip quiet"
                data-testid="update-claim-ref"
                data-ref={ref}
                data-ref-kind={refKind(ref)}
                title={ref}
                aria-label={label}
                onClick={() => onOpen(ref)}
              >
                {label}
              </Button>
            );
          })}
          {!claim.verified && !claim.hasAxes ? (
            <span data-testid="update-claim-unverified">
              <StateChip state="failure" label="UNVERIFIED" />
            </span>
          ) : null}
          <ClaimAxes claim={claim} />
          {/* PHILO-15 B64: what leaves the desk: an unsent claim reads OMITTED. */}
          {claimSends(claim) ? null : (
            <span className="surface-token" data-tone="warn" data-testid="update-claim-omitted">OMITTED</span>
          )}
          {review ? (
            <span className="update-inline-claim-verbs">
              <Button dense variant="ghost" disabled={review.busy === claim.spanId || claim.acceptance === "rejected"}
                aria-label={`Reject: ${claim.text}`} data-testid="update-claim-reject"
                onClick={() => review.act(claim.spanId, "rejected")}>Reject</Button>
              <Button dense variant="secondary" disabled={review.busy === claim.spanId || claim.acceptance === "accepted"}
                aria-label={`Accept: ${claim.text}`} data-testid="update-claim-accept"
                onClick={() => review.act(claim.spanId, "accepted")}>Accept</Button>
            </span>
          ) : null}
        </div>
      ))}
    </div>
  );
}

/* ── Rendered document view: Material body + citations ── */

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

  return (
    <div data-testid="update-document">
      {/* The rendered markdown body is the hero */}
      <div className="update-document-body" data-testid="update-document-body">
        <Material>{update.bodyMd}</Material>
      </div>

      {/* D6: source rows per section (CitationChips grammar, deduplicated) */}
      {sectionOrder.length > 0 ? (
        <SurfaceSection label={update.generator.startsWith("agent:") ? "LOOKED AT" : "SOURCES"}>
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
      {/* PHILO-9-03 (F11): the head counts updates, not drafts. */}
      <SurfaceLedger count={countLabel("UPDATES", ctrl.updates.length)} cols="room">
        <ul className="surface-ledger-rows">
          {ctrl.updates.map((update) => {
            return (
              <SurfaceLedgerRow
                key={update.id}
                data-testid="update-list-item"
                expands={false}
                wrap
                lead={
                  // PHILO-9-03 (F11): the update glyph, not a fixed "E".
                  <span className="update-lead-emblem" aria-hidden="true">
                    {"▤"}
                  </span>
                }
                primary={
                  // PHILO-9-03 (F11): the words spaced; the time lives in the row's time slot.
                  <span
                    className="update-list-row" data-update-id={update.id}
                    data-lifecycle={update.lifecycle}
                    data-generator={update.generator}
                  >
                    {/* W5-WORDS: a state is a dot and a word (`● Draft · rev 1`). */}
                    <DotWord tone={lifecycleDotTone(update.lifecycle)}>
                      {`${lifecycleLabel(update.lifecycle)} · rev ${update.draftRevision}`}
                    </DotWord>
                    {update.fallbackReason ? (
                      <span
                        className="update-quiet"
                        data-tone="warn"
                        data-testid="update-fallback-reason"
                      >
                        {humanFallbackReason(update.fallbackReason)}
                      </span>
                    ) : null}
                  </span>
                }
                cells={
                  <>
                    <ListChips update={update} />
                    {/* W5-WORDS: where the text came from, in quiet words. */}
                    <span className="update-quiet" data-testid="update-row-provenance">
                      {generatorLabel(update.generator, update.generatorModel)}
                    </span>
                  </>
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
      <span className="update-quiet" data-testid="update-generator-label">
        {generatorLabel(update.generator, update.generatorModel)}
      </span>
      {fallbackLabel ? (
        <span
          className="update-quiet"
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
      {/* PHILO-9-03 (the 393 Back defect, measured on the canvas): Back sits
          in the sticky head verbs, the seat the SurfaceVerbs species is made
          for. At the foot of the editor the button moved 36 px at focusin on
          pointerdown (the body scrolled; the top-sticky bar), so pointerup
          landed outside it and no click fired. */}
      <SurfaceVerbs>
        <Button dense variant="ghost" onClick={() => void ctrl.backToList()} data-testid="update-verb-back">
          Back
        </Button>
      </SurfaceVerbs>
      {/* Provenance + lifecycle band */}
      <div className="update-editor-band" data-testid="update-editor-band">
        {/* W5-WORDS: `● Published · rev 1`, then where the text came from. */}
        <DotWord tone={lifecycleDotTone(update.lifecycle)} data-testid="update-lifecycle">
          {`${lifecycleLabel(update.lifecycle)} · rev ${update.draftRevision}`}
        </DotWord>
        <ProvenanceLabel update={update} />
      </div>

      {/* Betterment P1: a draft reads as text and is edited in place (no
          format toolbar, no markdown marks); published updates render. */}
      {isDraft ? (
        <div className="update-body-editor" data-testid="update-body-editor">
          <TextArea
            className="update-plain-text"
            value={ctrl.editBody}
            onChange={(e) => ctrl.handleEditBody(e.target.value)}
            placeholder="Write your update"
            aria-label="Update body"
            data-testid="update-plain-text"
            rows={Math.min(40, Math.max(10, ctrl.editBody.split("\n").length + 1))}
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
          {/* PHILO-10-04: SEND first, then the one DELIVERY history (every
              channel + the manual Mark delivered, kept). A draft has no Send. */}
          {update.lifecycle === "published" ? <PublishedWells ctrl={ctrl} update={update} /> : null}
          <SurfaceSection label="Update">
            {/* W5-WORDS: one quiet line, never a caps token. */}
            <p className="update-quiet update-readonly-line" data-testid="update-readonly-reason">
              {update.lifecycle === "superseded"
                ? "Superseded drafts are read-only"
                : "Published updates are read-only"}
            </p>
            <RenderedUpdateDocument update={update} onOpenRef={onOpenRef} />
          </SurfaceSection>
        </div>
      )}

      {/* HS-173-02: inline claims — each sentence with its chip(s) beside it */}
      {isDraft && update.claims.length > 0 ? (
        <InlineClaimsView claims={update.claims} onOpen={onOpenRef}
          review={{ busy: ctrl.reviewBusy, receipt: ctrl.reviewReceipt, act: (span, a) => void ctrl.reviewClaim(span, a) }} />
      ) : null}

    </div>
  );
}

/* ── Betterment P1: the engine pass, under the text ── */

function EnginePassLine({
  pass,
  engineModel,
  onStop,
  onUndo,
  onUse,
  onRetry,
  onChooseEngine,
}: {
  pass: EnginePass;
  engineModel: string;
  onStop: () => void;
  onUndo: () => void;
  onUse: () => void;
  onRetry: () => void;
  onChooseEngine: () => void;
}) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (pass.phase !== "running") return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [pass.phase]);
  if (pass.phase === "idle") return null;
  const who = engineModel || "The engine";
  if (pass.phase === "running") {
    const s = Math.max(0, Math.round((now - pass.startedAt) / 1000));
    return (
      <div className="surface-run-line" data-testid="update-engine-pass" data-state="running" role="status">
        <span>{who} is improving this draft · {s} s</span>
        <Button dense variant="ghost" onClick={onStop}>Stop</Button>
      </div>
    );
  }
  if (pass.phase === "written") {
    return (
      <div className="surface-run-line" data-testid="update-engine-pass" data-state="success" role="status">
        <span>Written by {engineModel || pass.model || "the engine"} · {pass.seconds} s</span>
        <Button dense variant="ghost" onClick={onUndo}>Undo</Button>
      </div>
    );
  }
  if (pass.phase === "ready") {
    return (
      <div className="surface-run-line" data-testid="update-engine-pass" data-state="ready" role="status">
        <span>A better draft is ready</span>
        <Button dense variant="secondary" onClick={onUse}>Use it</Button>
      </div>
    );
  }
  return (
    <div data-testid="update-engine-pass" data-state="failure">
      <RunLine
        phase="failure"
        model={who}
        elapsedSeconds={pass.seconds}
        reason={pass.reason}
        detail={pass.detail}
        onRetry={onRetry}
        onAction={pass.reason === "no_engine" ? onChooseEngine : undefined}
      />
    </div>
  );
}

/* ── Main Update posture ── */

export function UpdatePosture({ ctrl }: { ctrl: UpdateController }) {
  const onOpenRef = useCallback((ref: string) => {
    openRef(ref);
  }, []);
  const engine = useEngine(UPDATE_DRAFT_CAPABILITY);

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
            variant="primary"
            loading={ctrl.draftBusy}
            disabled={engine.state === "unread"}
            onClick={() => void ctrl.write(engine.state === "set")}
            data-testid="update-verb-draft"
            data-verb="draft-update"
          >
            Write update
          </Button>
        </SurfaceVerbs>

        {ctrl.error ? (
          <SurfaceState error={ctrl.error} onRetry={() => void ctrl.enterUpdates()} />
        ) : null}

        <EngineLine
          engine={engine}
          onChoose={() => openSurfaceOr("configure-runs-on", "/settings", "models")}
          onRetry={() => void refreshEngine(UPDATE_DRAFT_CAPABILITY)}
        />
        <RunLine
          phase={ctrl.draftRun.phase}
          verb="Drafting"
          pastVerb="Drafted"
          model={engine.model}
          startedAt={ctrl.draftRun.startedAt}
          elapsedSeconds={ctrl.draftRun.elapsedSeconds}
          reason={ctrl.draftRun.reason}
          onRetry={ctrl.draftRun.generator ? () => void ctrl.draft(ctrl.draftRun.generator!) : undefined}
        />
        {ctrl.draftRun.phase === "failure" && ctrl.draftRun.generator === "model" ? (
          <Button dense variant="ghost" onClick={() => void ctrl.draft("deterministic")}>
            Draft from the Room's facts
          </Button>
        ) : null}

        {ctrl.updates.length === 0 && !ctrl.loading ? (
          /* DELIGHT slice 3: the object, one line, the making verb. */
          <SurfaceState
            empty
            emptyLabel="No updates yet"
            emptyImage={spriteUrl("artifact", "update")}
            emptyKind="project"
            actionLabel="Draft the first one"
            onAction={() => void ctrl.write(engine.state === "set")}
          />
        ) : (
          <UpdateList ctrl={ctrl} />
        )}

        <SurfaceFooter
          receipt={
            <span className="surface-footer-receipt-line update-footer-words" data-testid="update-footer-receipt" role="status">
              {`${ctrl.updates.length} ${ctrl.updates.length === 1 ? "update" : "updates"}`}
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
          <SurfaceState error={ctrl.error} onRetry={ctrl.retryFailed ?? undefined} />
        ) : null}

        {/* Betterment P1: the records draft is made in under a second; its
            line shows only while it runs or when it failed. */}
        {/* With no engine the records draft is the draft: the engine line
            says so. */}
        {engine.state !== "set" && ctrl.draftRun.phase === "success" ? <EngineLine engine={engine} /> : null}
        {ctrl.draftRun.phase === "running" || ctrl.draftRun.phase === "failure" ? (
          <>
            <EngineLine engine={engine} />
            <RunLine
              phase={ctrl.draftRun.phase}
              verb="Drafting"
              pastVerb="Drafted"
              model={engine.model}
              startedAt={ctrl.draftRun.startedAt}
              elapsedSeconds={ctrl.draftRun.elapsedSeconds}
              reason={ctrl.draftRun.reason}
            />
          </>
        ) : null}

        <UpdateEditor ctrl={ctrl} onOpenRef={onOpenRef} />

        <EnginePassLine
          pass={ctrl.enginePass}
          engineModel={engine.model}
          onStop={() => void ctrl.stopEnginePass()}
          onUndo={() => void ctrl.undoEngineDraft()}
          onUse={() => void ctrl.takeBetterDraft()}
          onRetry={() => void ctrl.retryEnginePass()}
          onChooseEngine={() => openSurfaceOr("configure-runs-on", "/settings", "models")}
        />

        <SurfaceFooter
          egress={
            ctrl.current && ctrl.current.generator !== "deterministic" && ctrl.current.generatorModel
              ? (
                  <span className="surface-token" data-chip data-testid="update-footer-model">
                    {ctrl.current.generatorModel.toUpperCase()}
                  </span>
                )
              : undefined
          }
          receipt={
            <span className="surface-footer-receipt-line update-footer-words" data-testid="update-footer-receipt" role="status">
              {ctrl.current
                ? `${lifecycleLabel(ctrl.current.lifecycle)} · rev ${ctrl.current.draftRevision}${ctrl.dirty ? " · Not saved" : ""}`
                : "Update"}
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
