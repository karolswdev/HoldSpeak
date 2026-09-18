// HS-200-11 — Posture 3, preparation, on the ratified boards:
//   P3Prepare (the ask, ONE `SOURCES M` ledger with the gaps marked, CARRIED
//   FORWARD), P3Brief / P3BriefPhone (the kept brief: document, CLAIMS on
//   three axes, NOT READ carrying the state chip and the repair), and
//   P3PrepareNoModel (the refusal: purpose kept, the invoke receipt told
//   honestly, `Prepare` drawn refused, `Set up model`).  `Write it myself`
//   is DROPPED (verdict Q3).
// Every verb is the library Button; coverage rides above the answer as a head
// TOKEN because a sources ledger exists on this face (verdict Q2; design D1).
//
// Counsel-on-built (2026-09-17): the refusal's head, route, footer and receipt
// all read the INVOKE RECEIPT (P0) — `NOTHING SENT` only when no kernel
// operation exists; `SUPERSEDED n` and `NOT INCLUDED n` ledgers under the
// claims (P1-2, P1-3); `STOPPED · REQUEST HAD LEFT · <host>` after a Stop
// whose request had gone (P1-4); the purpose is a PadGadget so it wraps at
// 393 (P2 iv); `Discard` on a draft brief (P2 v); the MANIFEST disclosure
// lists what was READ and the decisions carried, never the NOT READ rows a
// second time (P2 ii).

import { useEffect, useRef, type KeyboardEvent } from "react";
import { Button } from "../../../components/signal/Signal";
import {
  SurfaceFooter,
  SurfaceIdentity,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceSection,
  SurfaceState,
  EgressChip,
  StateChip,
  Material,
  Disclosure,
  ProgressPlan,
  ClaimAxes,
  ConfirmVerb,
  countLabel,
} from "../../../desk/surface";
import { CycleGadget, PadGadget } from "../../../desk/surface/gadgets";
import { egressFor } from "../../../desk/surface/egress";
import { openSurfaceOr } from "../../../desk/shell";
import { rememberTaskFocus } from "../../../desk/returnToTask";
import type { UpdateClaim } from "../update/model";
import type { PrepareController } from "./usePrepareController";
import {
  clockToken,
  coverageToken,
  elapsedToken,
  observedToken,
  refLabel,
  refusalReceipt,
  sourceEmblem,
  sourceStateToken,
  type Brief,
  type BriefManifest,
  type ManifestSource,
} from "./model";
import "./prepare-posture.css";

export const RESULT_OPTIONS = [
  { value: "answer", label: "Answer" },
  { value: "brief", label: "Preparation brief" },
];

/* ── the way back: a library Button inside a region (design D1, C8) ── */

function ProjectButton({ name, onOpen }: { name: string; onOpen: () => void }) {
  return (
    <span role="group" aria-label="Project" className="prepare-project-group">
      <Button
        dense
        variant="ghost"
        aria-label={`Open the Project: ${name}`}
        onClick={onOpen}
        data-testid="prepare-project-button"
      >
        {name.toUpperCase()}
      </Button>
    </span>
  );
}

function Token({ children, testId, tone }: { children: string; testId?: string; tone?: string }) {
  return (
    <span className="surface-token" data-chip data-tone={tone} data-testid={testId}>
      {children}
    </span>
  );
}

/** `COVERAGE · N OF M`: warn when a source is not in `available`, success
 *  when the read is complete, absent when there is nothing to count. */
function CoverageChip({ manifest }: { manifest: BriefManifest | null }) {
  if (!manifest) return null;
  const token = coverageToken(manifest.coverage);
  if (!token) return null;
  return (
    <span data-testid="prepare-coverage" data-complete={manifest.coverage.complete ? "true" : "false"}>
      <StateChip state={manifest.coverage.complete ? "success" : "warning"} label={token} />
    </span>
  );
}

function RouteChip({ ctrl }: { ctrl: PrepareController }) {
  const route = ctrl.refusal?.route ?? ctrl.route;
  if (!route) return null;
  const egress = egressFor(route.host);
  const ready = route.state === "ready";
  const detail = [route.model, route.host].filter(Boolean).join(" · ");
  return (
    <span className="prepare-route" data-testid="prepare-route" data-state={route.state}>
      <StateChip state={ready ? "success" : "failure"} label={route.token} icon={"●"} />
      {ready ? (
        <>
          {route.model ? <Token testId="prepare-route-model">{route.model.toUpperCase()}</Token> : null}
          <EgressChip label={egress.label || route.host} scope={egress.scope} title={route.host} />
        </>
      ) : detail ? (
        <Token testId="prepare-route-detail">{detail.toUpperCase()}</Token>
      ) : null}
    </span>
  );
}

/* ── the ask well (P3Prepare / P3PrepareNoModel) ── */

function PrepareWell({ ctrl, onResultChange }: { ctrl: PrepareController; onResultChange: (purpose: string) => void }) {
  const refused = ctrl.posture === "refused";
  const route = ctrl.refusal?.route ?? ctrl.route;
  const routeReady = !route || route.state === "ready";
  const canPrepare = !refused && routeReady && ctrl.purpose.trim().length > 0;
  const prepareRef = useRef<HTMLButtonElement>(null);
  // P2 iii: a return-to-task that found Prepare refused lands on Prepare
  // once it is enabled again.
  useEffect(() => {
    if (!ctrl.focusPrepareWhenReady || !canPrepare) return;
    prepareRef.current?.focus();
    ctrl.setFocusPrepareWhenReady(false);
  }, [ctrl, canPrepare]);
  const onKey = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey && canPrepare) {
      event.preventDefault();
      void ctrl.prepare();
    }
  };
  return (
    <div className="prepare-well surface-aerogel" data-testid="prepare-well">
      <div className="prepare-well-purpose">
        <PadGadget
          label="Purpose"
          value={ctrl.purpose}
          onChange={ctrl.setPurpose}
          placeholder="What this meeting is for"
          rows={1}
          autoGrow
          onKeyDown={onKey}
          autoFocus={ctrl.posture === "prepare"}
        />
      </div>
      <div className="prepare-well-row">
        <CycleGadget
          label="Result"
          value="brief"
          options={RESULT_OPTIONS}
          onChange={(next) => { if (next === "answer") onResultChange(ctrl.purpose); }}
        />
        <RouteChip ctrl={ctrl} />
        {ctrl.stopped ? (
          <Token testId="prepare-stopped" tone="warn">
            {`STOPPED · REQUEST HAD LEFT${ctrl.stopped.host ? ` · ${ctrl.stopped.host}` : ""}`}
          </Token>
        ) : null}
        <span className="prepare-well-verbs">
          {!routeReady || refused ? (
            <Button
              dense
              variant="ghost"
              data-testid="prepare-set-up-model"
              onClick={() => {
                // Prepare is the return target even while native-disabled:
                // the controller focuses it once the route is ready (P2 iii).
                rememberTaskFocus(prepareRef.current);
                ctrl.setFocusPrepareWhenReady(true);
                openSurfaceOr("configure-runs-on", "/settings", "models");
              }}
            >
              {route?.repair || "Set up model"}
            </Button>
          ) : null}
          <Button
            ref={prepareRef}
            variant="primary"
            className="prepare-verb"
            disabled={!canPrepare}
            aria-disabled={!canPrepare || undefined}
            aria-label="Prepare: build the brief from these sources"
            data-testid="prepare-verb"
            onClick={() => void ctrl.prepare()}
          >
            Prepare
          </Button>
        </span>
      </div>
    </div>
  );
}

/* ── ONE source ledger grammar: emblem · label · tokens · state · OBSERVED · repair ── */

function SourceRow({
  source,
  ctrl,
  omitted,
}: {
  source: ManifestSource;
  ctrl: PrepareController;
  omitted?: boolean;
}) {
  const state = sourceStateToken(source);
  const observed = observedToken(source.observedAt);
  const reason = source.reason ? `${source.reason.toUpperCase()}${omitted ? " · OMITTED" : ""}` : omitted ? "OMITTED" : "";
  const openHref =
    source.kind === "github" && source.label ? `https://github.com/${source.label}` : "";
  return (
    <SurfaceLedgerRow
      lead={<span className="prepare-emblem" aria-hidden="true">{sourceEmblem(source.kind)}</span>}
      primary={
        <span className="prepare-source-primary">
          <span className="surface-primary" data-testid="prepare-source-label">{source.label}</span>
          {source.tokens.map((tok) => (
            <Token key={tok}>{tok}</Token>
          ))}
          {reason ? <Token testId="prepare-source-reason">{reason}</Token> : null}
        </span>
      }
      cells={
        <span className="prepare-source-cells">
          <span data-testid="prepare-source-state" data-state={source.state}>
            <StateChip state={state.state} label={state.label} icon={"●"} />
          </span>
          {observed ? <Token testId="prepare-source-observed">{observed}</Token> : null}
        </span>
      }
      trailing={
        source.repair ? (
          <Button
            dense
            variant="secondary"
            aria-label={`${source.repair.verb}: ${source.label}`}
            data-testid="prepare-source-repair"
            onClick={() => void ctrl.repairSource(source.repair!.verb, source.watchIds)}
          >
            {source.repair.verb}
          </Button>
        ) : openHref ? (
          <Button
            dense
            variant="ghost"
            aria-label={`Open: ${source.label}`}
            data-testid="prepare-source-open"
            onClick={() => window.open(openHref, "_blank", "noopener")}
          >
            Open
          </Button>
        ) : null
      }
      wrap
      open
      expands={false}
      data-testid={omitted ? "prepare-not-read-row" : "prepare-source-row"}
    />
  );
}

function SourcesSection({ manifest, ctrl }: { manifest: BriefManifest | null; ctrl: PrepareController }) {
  if (!manifest || manifest.sources.length === 0) return null;
  return (
    <SurfaceSection label={countLabel("SOURCES", manifest.sources.length)}>
      <SurfaceLedger count="" cols="room">
        <ul className="surface-ledger-rows" data-testid="prepare-sources">
          {manifest.sources.map((source) => (
            <SourceRow key={source.sourceId} source={source} ctrl={ctrl} />
          ))}
        </ul>
      </SurfaceLedger>
    </SurfaceSection>
  );
}

function CarriedForwardSection({ manifest, onOpenRef }: { manifest: BriefManifest | null; onOpenRef: (ref: string) => void }) {
  if (!manifest) return null;
  const current = manifest.decisions.filter((d) => d.lifecycle === "current");
  const rows = current.length + manifest.commitments.length;
  if (rows === 0) return null;
  return (
    <SurfaceSection label={countLabel("CARRIED FORWARD", rows)}>
      <SurfaceLedger count="" cols="room">
        <ul className="surface-ledger-rows" data-testid="prepare-carried">
          {current.map((decision) => (
            <SurfaceLedgerRow
              key={decision.ref}
              lead={<span className="prepare-emblem" aria-hidden="true">DEC</span>}
              primary={<span className="surface-primary">{decision.text}</span>}
              cells={<StateChip state="success" label="CURRENT" />}
              trailing={
                <Button dense variant="ghost" aria-label={`Open: ${decision.text}`} onClick={() => onOpenRef(decision.ref)}>
                  Open
                </Button>
              }
              wrap
              open
              expands={false}
              data-testid="prepare-carried-decision"
            />
          ))}
          {manifest.commitments.map((commitment) => {
            const due = commitment.dueAt ? clockToken("DUE", commitment.dueAt) : null;
            return (
              <SurfaceLedgerRow
                key={commitment.ref}
                lead={<span className="prepare-emblem" aria-hidden="true">CMT</span>}
                primary={<span className="surface-primary">{commitment.text}</span>}
                cells={
                  <span className="prepare-source-cells">
                    {commitment.owner ? <Token>{`OWNER ${commitment.owner.toUpperCase()}`}</Token> : null}
                    {due ? <Token>{due}</Token> : null}
                  </span>
                }
                trailing={
                  <Button dense variant="ghost" aria-label={`Open: ${commitment.text}`} onClick={() => onOpenRef(commitment.ref)}>
                    Open
                  </Button>
                }
                wrap
                open
                expands={false}
                data-testid="prepare-carried-commitment"
              />
            );
          })}
        </ul>
      </SurfaceLedger>
    </SurfaceSection>
  );
}

/* ── the kept brief (P3Brief / P3BriefPhone) ── */

function ClaimRow({ claim, manifest, onOpenRef, onFindSupport }: { claim: UpdateClaim; manifest: BriefManifest; onOpenRef: (ref: string) => void; onFindSupport: (text: string) => void }) {
  const ref = claim.refs[0] ?? "";
  const label = ref ? refLabel(ref, manifest) : "";
  // A commitment ref has no source surface to open (ledgered for BACKLOG);
  // the chip names it and the verb is withheld rather than shipped dead.
  const openable = ref && !ref.startsWith("commitment:");
  return (
    <SurfaceLedgerRow
      primary={<span className="surface-primary prepare-claim-text">{claim.text}</span>}
      cells={
        <span className="prepare-claim-source">
          {ref ? (
            <>
              <Token testId="prepare-claim-ref">{label}</Token>
              {openable ? (
                <Button
                  dense
                  variant="ghost"
                  aria-label={`Open source: ${label}`}
                  data-testid="prepare-claim-open"
                  onClick={() => onOpenRef(ref)}
                >
                  Open source
                </Button>
              ) : null}
            </>
          ) : (
            <>
              <span data-testid="prepare-claim-no-source">
                <StateChip state="warning" label="NO SOURCE" />
              </span>
              <Button
                dense
                variant="ghost"
                aria-label={`Find support: ${claim.text}`}
                data-testid="prepare-claim-find"
                onClick={() => onFindSupport(claim.text)}
              >
                Find support
              </Button>
            </>
          )}
        </span>
      }
      wrap
      open
      expands={false}
      data-testid="prepare-claim-row"
    >
      <div className="prepare-claim-axes">
        <ClaimAxes
          kind={claim.kind}
          support={claim.support}
          acceptance={claim.acceptance}
          supportEdited={Boolean(claim.supportRecord?.invalidatedAt)}
          supportMigrated={Boolean(claim.supportMappingVersion)}
          unknowns={claim.unknowns}
          testIdPrefix="prepare-claim"
        />
      </div>
    </SurfaceLedgerRow>
  );
}

/** P1-2: a sentence the model cited to a SUPERSEDED decision -- never a line
 *  of the document; a ledger row with its successor linked. */
function SupersededRow({ claim, manifest, onOpenRef }: { claim: UpdateClaim; manifest: BriefManifest; onOpenRef: (ref: string) => void }) {
  const ref = claim.refs[0] ?? "";
  const successor = claim.unknowns.find((u) => u.type === "superseded_by")?.value ?? "";
  return (
    <SurfaceLedgerRow
      primary={<span className="surface-primary prepare-claim-text">{claim.text}</span>}
      cells={
        <span className="prepare-claim-source">
          {ref ? <Token testId="prepare-superseded-ref">{refLabel(ref, manifest)}</Token> : null}
          <span data-testid="prepare-superseded-chip">
            <StateChip state="warning" label={successor ? `SUPERSEDED BY ${refLabel(successor, manifest)}` : "SUPERSEDED"} />
          </span>
          {successor ? (
            <Button dense variant="ghost" aria-label={`Open successor: ${refLabel(successor, manifest)}`} data-testid="prepare-superseded-open" onClick={() => onOpenRef(successor)}>
              Open successor
            </Button>
          ) : null}
        </span>
      }
      wrap
      open
      expands={false}
      data-testid="prepare-superseded-row"
    />
  );
}

function BriefBody({ brief, ctrl, onOpenRef }: { brief: Brief; ctrl: PrepareController; onOpenRef: (ref: string) => void }) {
  const findSupport = (text: string) => {
    openSurfaceOr("open-project-memory", "/", `q:${text}`);
  };
  const openRef = (ref: string) => {
    if (ref.startsWith("source:")) {
      const id = ref.slice("source:".length);
      const source = brief.manifest.sources.find((s) => s.sourceId === id);
      if (source?.kind === "github" && source.label) {
        window.open(`https://github.com/${source.label}`, "_blank", "noopener");
        return;
      }
      ctrl.setSourcesOpen(true);
      return;
    }
    if (ref.startsWith("decision_record:")) {
      onOpenRef(`decision:${ref.slice("decision_record:".length)}`);
      return;
    }
    onOpenRef(ref);
  };
  const documentClaims = brief.claims.filter((c) => c.section !== "superseded");
  const supersededClaims = brief.claims.filter((c) => c.section === "superseded");
  const readSources = brief.manifest.sources.filter((s) => s.state === "available");
  return (
    <>
      <div className="prepare-document surface-aerogel" data-testid="prepare-document">
        <Material>{brief.bodyMd}</Material>
      </div>
      {documentClaims.length > 0 ? (
        <SurfaceSection label={countLabel("CLAIMS", documentClaims.length)}>
          <SurfaceLedger count="" cols="room">
            <ul className="surface-ledger-rows" data-testid="prepare-claims">
              {documentClaims.map((claim) => (
                <ClaimRow key={claim.spanId} claim={claim} manifest={brief.manifest} onOpenRef={openRef} onFindSupport={findSupport} />
              ))}
            </ul>
          </SurfaceLedger>
        </SurfaceSection>
      ) : null}
      {supersededClaims.length > 0 ? (
        <SurfaceSection label={countLabel("SUPERSEDED", supersededClaims.length)}>
          <SurfaceLedger count="" cols="room">
            <ul className="surface-ledger-rows" data-testid="prepare-superseded">
              {supersededClaims.map((claim) => (
                <SupersededRow key={claim.spanId} claim={claim} manifest={brief.manifest} onOpenRef={openRef} />
              ))}
            </ul>
          </SurfaceLedger>
        </SurfaceSection>
      ) : null}
      {brief.manifest.omitted.length > 0 ? (
        <SurfaceSection label={countLabel("NOT READ", brief.manifest.omitted.length)}>
          <SurfaceLedger count="" cols="room">
            <ul className="surface-ledger-rows" data-testid="prepare-not-read">
              {brief.manifest.omitted.map((source) => (
                <SourceRow key={source.sourceId} source={source} ctrl={ctrl} omitted />
              ))}
            </ul>
          </SurfaceLedger>
        </SurfaceSection>
      ) : null}
      {brief.manifest.notIncluded.length > 0 ? (
        <Disclosure
          label={countLabel("NOT INCLUDED", brief.manifest.notIncluded.length)}
          token={<Token testId="prepare-not-included-token">{brief.generator.startsWith("model:") ? "OVER THE BOUND" : "OVER THE BOUND · NEWEST FIRST"}</Token>}
        >
          <SurfaceLedger count="" cols="room">
            <ul className="surface-ledger-rows" data-testid="prepare-not-included">
              {brief.manifest.notIncluded.map((item, index) => (
                <SurfaceLedgerRow
                  key={`${item.ref}:${index}`}
                  primary={<span className="surface-primary prepare-claim-text">{item.title}</span>}
                  cells={
                    <span className="prepare-claim-source">
                      {item.ref ? <Token>{refLabel(item.ref, brief.manifest)}</Token> : null}
                      <Token testId="prepare-not-included-why">{item.why.toUpperCase()}</Token>
                    </span>
                  }
                  wrap
                  open
                  expands={false}
                  data-testid="prepare-not-included-row"
                />
              ))}
            </ul>
          </SurfaceLedger>
        </Disclosure>
      ) : null}
      {/* P2 ii: the manifest is what was READ and what was carried; the
          omitted rows are drawn once, under NOT READ, never here. */}
      <Disclosure
        label="MANIFEST"
        open={ctrl.sourcesOpen}
        onOpenChange={ctrl.setSourcesOpen}
        token={<Token>{`REV ${brief.manifestRevision}`}</Token>}
      >
        {readSources.length > 0 ? (
          <SurfaceSection label={countLabel("READ", readSources.length)}>
            <SurfaceLedger count="" cols="room">
              <ul className="surface-ledger-rows" data-testid="prepare-manifest-sources">
                {readSources.map((source) => (
                  <SourceRow key={source.sourceId} source={source} ctrl={ctrl} />
                ))}
              </ul>
            </SurfaceLedger>
          </SurfaceSection>
        ) : null}
        {brief.manifest.decisions.length > 0 ? (
          <SurfaceSection label={countLabel("CARRIED", brief.manifest.decisions.length)}>
            <SurfaceLedger count="" cols="room">
              <ul className="surface-ledger-rows" data-testid="prepare-manifest-decisions">
                {brief.manifest.decisions.map((decision) => (
                  <SurfaceLedgerRow
                    key={decision.ref}
                    lead={<span className="prepare-emblem" aria-hidden="true">DEC</span>}
                    primary={<span className="surface-primary">{decision.text}</span>}
                    cells={
                      <StateChip
                        state={decision.lifecycle === "current" ? "success" : "warning"}
                        label={decision.lifecycle === "current" ? "CURRENT" : "SUPERSEDED"}
                      />
                    }
                    wrap
                    open
                    expands={false}
                    data-testid="prepare-manifest-decision"
                  />
                ))}
              </ul>
            </SurfaceLedger>
          </SurfaceSection>
        ) : null}
      </Disclosure>
    </>
  );
}

/* ── the posture ── */

export function PreparePosture({
  ctrl,
  projectName,
  onOpenRef,
  onResultChange,
}: {
  ctrl: PrepareController;
  projectName: string;
  onOpenRef: (ref: string) => void;
  onResultChange: (purpose: string) => void;
}) {
  const { posture, brief } = ctrl;
  const keepRef = useRef<HTMLButtonElement>(null);
  const manifest = posture === "brief" && brief ? brief.manifest : ctrl.manifest;
  const kept = brief?.lifecycle === "kept";
  // The head NAME stays `Brief ready` after Keep; the KEPT chip is the receipt.
  const headName =
    posture === "brief" ? "Brief ready"
    : posture === "refused" ? "Cannot draft"
    : posture === "running" ? "Preparing"
    : "Prepare a brief";
  const prepared = brief ? clockToken("PREPARED", brief.createdAt) : null;
  const generatorEgress = brief
    ? brief.generator.startsWith("model:")
      ? egressFor(brief.generatorHost || "")
      : { label: "THIS DEVICE", scope: "local" as const }
    : null;
  const elapsed = brief ? elapsedToken(brief.elapsedMs) : null;
  const receipt = brief
    ? [brief.generator.startsWith("model:") ? (brief.generatorModel || "MODEL").toUpperCase() : "DETERMINISTIC", elapsed]
        .filter(Boolean)
        .join(" · ")
    : "";
  // P0: the refusal tells what happened to the request, from the receipt.
  const refusalTruth = ctrl.refusal ? refusalReceipt(ctrl.refusal.route) : null;
  const refusalEgress = refusalTruth?.sent ? egressFor(refusalTruth.host) : null;

  return (
    <div className="prepare-posture" data-testid="prepare-posture" data-posture={posture}>
      <SurfaceIdentity
        name={headName}
        nameTestId="prepare-head-name"
        data-testid="prepare-head"
        chips={
          <>
            <ProjectButton name={projectName} onOpen={ctrl.exit} />
            {posture === "brief" && brief ? (
              <>
                <span data-testid="prepare-lifecycle">
                  <StateChip state={kept ? "success" : "idle"} label={kept ? "KEPT" : "DRAFT"} icon={"●"} />
                </span>
                <Token testId="prepare-manifest-token">{`MANIFEST · REV ${brief.manifestRevision}`}</Token>
                {brief.integrity === "mismatch" ? (
                  <span data-testid="prepare-integrity">
                    <StateChip state="failure" label="MANIFEST MISMATCH" />
                  </span>
                ) : null}
              </>
            ) : null}
            <CoverageChip manifest={manifest} />
            {posture === "brief" ? (
              prepared ? <Token testId="prepare-prepared">{prepared}</Token> : null
            ) : posture === "refused" ? (
              <>
                <Token testId="prepare-purpose-kept">PURPOSE KEPT</Token>
                <Token testId="prepare-sent-token" tone={refusalTruth?.sent ? "warn" : undefined}>
                  {refusalTruth?.line ?? "NOTHING SENT"}
                </Token>
              </>
            ) : (
              <>
                <Token testId="prepare-purpose-by-hand">PURPOSE SET BY HAND</Token>
                {manifest && !manifest.calendar.present ? <Token testId="prepare-no-calendar">NO CALENDAR</Token> : null}
              </>
            )}
          </>
        }
      />

      {posture === "running" ? (
        <div className="prepare-running" data-testid="prepare-running">
          <ProgressPlan
            ariaLabel="Preparing the brief"
            steps={[
              { id: "sources", label: "Read sources", status: "done" },
              { id: "draft", label: "Draft the brief", status: "running" },
              { id: "bind", label: "Bind the manifest", status: "queued" },
            ]}
            egress={ctrl.route ? <EgressChip label={egressFor(ctrl.route.host).label || ctrl.route.host} scope={egressFor(ctrl.route.host).scope} /> : undefined}
            action={{ label: "Stop", onClick: ctrl.stop }}
          />
        </div>
      ) : null}

      {posture === "prepare" || posture === "refused" ? (
        <>
          <PrepareWell ctrl={ctrl} onResultChange={onResultChange} />
          {ctrl.error ? <SurfaceState error={ctrl.error} /> : null}
          <SourcesSection manifest={manifest} ctrl={ctrl} />
          <CarriedForwardSection manifest={manifest} onOpenRef={onOpenRef} />
        </>
      ) : null}

      {posture === "brief" && brief ? <BriefBody brief={brief} ctrl={ctrl} onOpenRef={onOpenRef} /> : null}

      <SurfaceFooter
        className="prepare-footer"
        egress={
          posture === "brief" && generatorEgress ? (
            <span data-testid="prepare-footer-egress">
              <EgressChip label={generatorEgress.label} scope={generatorEgress.scope} />
            </span>
          ) : posture === "refused" ? (
            <span data-testid="prepare-footer-egress">
              {refusalEgress ? (
                <EgressChip label={refusalEgress.label || refusalTruth!.host} scope={refusalEgress.scope} />
              ) : (
                <EgressChip label="THIS DEVICE" scope="local" />
              )}
            </span>
          ) : undefined
        }
        receipt={
          <span className="surface-footer-receipt-line" role="status" data-testid="prepare-footer-receipt">
            {posture === "brief" ? receipt : posture === "refused" ? (refusalTruth?.line ?? "NOTHING SENT") : ctrl.kept.length ? countLabel("KEPT", ctrl.kept.length) : "NOTHING KEPT YET"}
          </span>
        }
        verbs={
          posture === "brief" && brief ? (
            <>
              <Button dense variant="ghost" aria-label="Copy the brief" data-testid="prepare-copy" onClick={() => void ctrl.copy()}>
                {ctrl.copyState === "copied" ? "Copied" : "Copy"}
              </Button>
              <Button
                dense
                variant="ghost"
                aria-label="Open sources"
                aria-expanded={ctrl.sourcesOpen}
                data-testid="prepare-open-sources"
                onClick={() => ctrl.setSourcesOpen(!ctrl.sourcesOpen)}
              >
                Open sources
              </Button>
              {!kept ? (
                <span data-testid="prepare-discard">
                  <ConfirmVerb
                    label="Discard"
                    confirmLabel="Discard?"
                    ariaLabel="Discard this draft"
                    busy={ctrl.discardBusy}
                    onConfirm={() => void ctrl.discard()}
                  />
                </span>
              ) : null}
              {/* Keep-after-Keep: DRAWN refused (aria-disabled, dashed) but
                  never native-disabled, so focus stays on Keep and the head
                  token KEPT is the receipt (design D2(c), focus return).
                  Counsel accepted this deviation from native `disabled`
                  (2026-09-17): an inert, aria-disabled verb that keeps the
                  caret, with the second press writing nothing. */}
              <Button
                ref={keepRef}
                dense
                variant="primary"
                className={kept ? "prepare-verb prepare-verb--refused" : "prepare-verb"}
                aria-label="Keep this brief"
                data-testid="prepare-keep"
                aria-busy={ctrl.keepBusy || undefined}
                aria-disabled={kept || undefined}
                onClick={() => {
                  if (kept || ctrl.keepBusy) return;
                  void ctrl.keep().then(() => keepRef.current?.focus());
                }}
              >
                Keep
              </Button>
            </>
          ) : undefined
        }
      />
    </div>
  );
}
