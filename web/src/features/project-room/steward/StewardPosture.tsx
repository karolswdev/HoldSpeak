// HS-163-05 / HS-164-05 -- the Steward posture: run, watch, stop,
// receipts, policy, unattended controls, provenance, circuit state.
// Architecture mirrors UpdatePosture (162): a verb in the Room chrome,
// MOUNTED path proven, surface barrel imports only.
// Laws: no raw IDs on glass; no modals; MicButton on text inputs;
// EgressChip on model-touching effect kinds; no em/en dashes; no prose.

import { useCallback, useEffect, useRef } from "react";
import { Button } from "../../../components/signal/Signal";
import {
  EgressChip,
  SurfaceFooter,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceSection,
  SurfaceState,
  SurfaceToggle,
  SurfaceVerbs,
  humanTime,
} from "../../../desk/surface";
import { openSourceRef } from "../../../desk/surface/citations";
import type { StewardController } from "./useStewardController";
import type { StewardRun, StewardStep } from "./model";
import {
  EFFECT_KINDS,
  assembleGrantText,
  circuitStateLabel,
  circuitStateTone,
  computeVerticalScrollHint,
  coverageSummary,
  effectKindLabel,
  isActive,
  isModelTouchingKind,
  phaseLabel,
  pluralize,
  provenanceLabel,
  provenanceTone,
  receiptRefs,
  runRowSubstance,
  runStateLabel,
  runStateTone,
  stepIsPartial,
  stepStateLabel,
  stepStateTone,
  summaryReasonLabel,
} from "./model";
import "./steward-posture.css";

/* ── Step row: effect kind in words + state + receipt refs ── */

function StepRow({
  step,
  onOpenRef,
}: {
  step: StewardStep;
  onOpenRef: (ref: string) => void;
}) {
  const refs = receiptRefs(step);
  const tone = stepStateTone(step.state);
  const partial = stepIsPartial(step);
  return (
    <span className="steward-step-row" data-testid="steward-step-row">
      <span className="steward-step-primary">
        <span className="surface-token" data-tone={tone}>
          {stepStateLabel(step.state)}
        </span>
        <span>{effectKindLabel(step.effectKind)}</span>
        {partial ? (
          <span className="surface-token" data-tone="warn" data-testid="steward-step-partial">
            PARTIAL
          </span>
        ) : null}
      </span>
      {refs.length > 0 ? (
        <span className="steward-step-secondary">
          <span className="steward-receipt-refs" data-testid="steward-receipt-refs">
            {refs.map((ref) => (
              <button
                key={ref}
                type="button"
                className="desk-chip quiet steward-receipt-ref"
                data-testid="steward-receipt-ref"
                data-ref={ref}
                onClick={() => onOpenRef(ref)}
              >
                {refHumanLabel(ref)}
              </button>
            ))}
          </span>
        </span>
      ) : null}
      {step.error ? (
        <span className="steward-step-secondary">
          <span className="surface-token" data-tone="danger" data-testid="steward-step-error">
            {step.error.message ?? "Error"}
          </span>
        </span>
      ) : null}
    </span>
  );
}

/** Human label for a receipt ref (no raw IDs on glass). */
function refHumanLabel(ref: string): string {
  const colon = ref.indexOf(":");
  if (colon < 0) return "Open";
  const prefix = ref.slice(0, colon);
  const KIND_LABELS: Record<string, string> = {
    item: "Open item",
    action_item: "Open action item",
    risk: "Open risk",
    dependency: "Open dependency",
    workstream: "Open workstream",
    milestone: "Open milestone",
    signal: "Open signal",
    decision: "Open decision",
    meeting: "Open meeting",
    artifact: "Open artifact",
    observation: "Open observation",
    update: "Open update",
  };
  return KIND_LABELS[prefix] ?? "Open";
}

/* ── Run detail view: phases, steps, stop ── */

function RunDetail({
  ctrl,
  onOpenRef,
}: {
  ctrl: StewardController;
  onOpenRef: (ref: string) => void;
}) {
  const run = ctrl.currentRun;
  if (!run) return null;

  const tone = runStateTone(run.state);
  const reason = summaryReasonLabel(run.summary.reason);
  const degraded = coverageSummary(run);

  return (
    <div className="steward-detail" data-testid="steward-detail">
      {/* State band */}
      <div className="steward-detail-band" data-testid="steward-detail-band">
        <span className="surface-token" data-tone={tone} data-testid="steward-run-state">
          {runStateLabel(run.state)}
        </span>
        <span
          className="surface-token"
          data-tone={provenanceTone(run)}
          data-testid="steward-run-provenance"
        >
          {provenanceLabel(run)}
        </span>
        {run.phase ? (
          <span className="steward-phase-label" data-testid="steward-phase-label">
            {phaseLabel(run.phase)}
          </span>
        ) : null}
        {reason ? (
          <span className="surface-token" data-tone="warn" data-testid="steward-run-reason">
            {reason}
          </span>
        ) : null}
        {degraded ? (
          <span className="surface-token" data-tone="warn" data-testid="steward-coverage-degraded">
            {`PARTIAL COVERAGE: ${degraded}`}
          </span>
        ) : null}
      </div>

      {/* Steps */}
      {ctrl.currentSteps.length > 0 ? (
        <SurfaceLedger count={`STEPS ${ctrl.currentSteps.length}`}>
          <ul className="surface-ledger-rows">
            {ctrl.currentSteps.map((step) => (
              <SurfaceLedgerRow
                key={step.id}
                data-testid="steward-step-item"
                expands={false}
                primary={
                  <StepRow step={step} onOpenRef={onOpenRef} />
                }
              />
            ))}
          </ul>
        </SurfaceLedger>
      ) : null}

      {/* Verbs */}
      <SurfaceVerbs>
        <Button dense variant="ghost" onClick={() => void ctrl.backToList()}>
          Back
        </Button>
        {ctrl.canStop ? (
          <span className="steward-stop-action" data-testid="steward-stop-action">
            <Button
              dense
              variant="primary"
              loading={ctrl.stopBusy}
              onClick={() => void ctrl.stopRun()}
              data-testid="steward-verb-stop"
              className="is-consequential"
            >
              Stop
            </Button>
          </span>
        ) : null}
      </SurfaceVerbs>
    </div>
  );
}

/* ── Run history list ── */

function RunList({ ctrl }: { ctrl: StewardController }) {
  return (
    <div className="steward-list" data-testid="steward-list">
      <SurfaceLedger count={`RUNS ${ctrl.runs.length}`}>
        <ul className="surface-ledger-rows">
          {ctrl.runs.map((run) => {
            const tone = runStateTone(run.state);
            const substance = runRowSubstance(run);
            return (
              <SurfaceLedgerRow
                key={run.id}
                data-testid="steward-list-item"
                expands={false}
                primary={
                  <span
                    className="steward-list-row"
                    data-state={run.state}
                    title={run.id}
                  >
                    <span className="steward-list-primary">
                      <span className="surface-token" data-tone={tone}>
                        {runStateLabel(run.state)}
                      </span>
                      <span
                        className="surface-token steward-provenance-chip"
                        data-tone={provenanceTone(run)}
                        data-testid="steward-run-provenance"
                      >
                        {provenanceLabel(run)}
                      </span>
                      <span className="steward-list-time">
                        {humanTime(run.createdAt)}
                      </span>
                      <span className="steward-list-chevron" aria-hidden="true" data-testid="steward-list-chevron">{">"}</span>
                    </span>
                    {substance ? (
                      <span className="steward-list-secondary" data-testid="steward-list-summary">
                        {substance}
                      </span>
                    ) : null}
                  </span>
                }
                onToggle={() => ctrl.openRun(run)}
              />
            );
          })}
        </ul>
      </SurfaceLedger>
    </div>
  );
}

/* ── Policy editor (in-world, no modals) ── */

function PolicyEditor({ ctrl }: { ctrl: StewardController }) {
  const draft = ctrl.policyDraft;
  if (!draft) return null;

  // HS-164-05: assemble grant text from draft + watches for live preview
  const grantPolicy = ctrl.policy
    ? {
        ...ctrl.policy,
        unattendedEnabled: draft.unattended_enabled,
        eligibleEffectKinds: draft.eligible_effect_kinds,
        maxActionsPerRun: draft.max_actions_per_run,
      }
    : null;
  const grantText = grantPolicy
    ? assembleGrantText(grantPolicy, ctrl.watches)
    : null;

  // HS-164-05: watches with non-closed circuits
  const circuitWatches = ctrl.watches.filter(
    (w) => w.circuitState !== "closed",
  );

  return (
    <div className="steward-policy" data-testid="steward-policy">
      {/* HS-164-05: Source circuits render FIRST when any circuit is
          not closed. A broken source outranks configuration. */}
      {/* HS-164-05: Circuit state section (watches with non-closed circuits) */}
      {circuitWatches.length > 0 ? (
        <SurfaceSection label="Source circuits">
          <SurfaceLedger count={`CIRCUITS ${circuitWatches.length}`}>
            <ul className="surface-ledger-rows">
              {circuitWatches.map((w) => (
                <SurfaceLedgerRow
                  key={w.id}
                  data-testid="steward-circuit-row"
                  expands={false}
                  time={w.circuitOpenedAt ? humanTime(w.circuitOpenedAt) : ""}
                  primary={
                    <span className="steward-circuit-row-content">
                      <span
                        className="surface-token"
                        data-tone={circuitStateTone(w.circuitState)}
                        data-testid="steward-circuit-state"
                      >
                        {circuitStateLabel(w.circuitState)}
                      </span>
                      <span className="steward-circuit-name" title={w.name || w.connectorId}>
                        {w.name || w.connectorId}
                      </span>
                      {w.circuitFailureStreak > 0 ? (
                        <span className="steward-circuit-streak" data-testid="steward-circuit-streak">
                          {pluralize(w.circuitFailureStreak, "failure")}
                        </span>
                      ) : null}
                    </span>
                  }
                />
              ))}
            </ul>
          </SurfaceLedger>
        </SurfaceSection>
      ) : null}

      <SurfaceSection label="Steward policy">
        {/* Enabled toggle */}
        <div className="steward-policy-toggle-row" data-testid="steward-policy-enabled-row">
          <SurfaceToggle
            label="Steward enabled"
            checked={draft.enabled}
            onChange={(v) => ctrl.updatePolicyDraft("enabled", v)}
          />
          <span className="steward-policy-toggle-label">Steward enabled</span>
        </div>

        {/* HS-164-05: Unattended operation toggle with assembled grant text */}
        <div className="steward-unattended-section" data-testid="steward-unattended-section">
          <div className="steward-policy-toggle-row" data-testid="steward-unattended-row">
            <SurfaceToggle
              label="Unattended operation"
              checked={draft.unattended_enabled}
              onChange={(v) => ctrl.updatePolicyDraft("unattended_enabled", v)}
            />
            <span className="steward-policy-toggle-label">Unattended operation</span>
          </div>
          {grantText ? (
            <p
              className="steward-grant-text"
              data-testid="steward-grant-text"
              role="status"
              aria-live="polite"
            >
              {grantText}
            </p>
          ) : null}
        </div>

        {/* Eligible effect kinds */}
        <div className="steward-policy-effects" data-testid="steward-policy-effects">
          <label>Eligible effects</label>
          {EFFECT_KINDS.map((kind) => (
            <div key={kind} className="steward-policy-effect-row">
              <SurfaceToggle
                label={effectKindLabel(kind)}
                checked={draft.eligible_effect_kinds.includes(kind)}
                onChange={() => ctrl.toggleEffectKind(kind)}
                data-testid={`steward-policy-kind-${kind}`}
              />
              <span className="steward-policy-toggle-label" data-testid={`steward-policy-kind-label-${kind}`}>
                {effectKindLabel(kind)}
              </span>
              {isModelTouchingKind(kind) ? (
                <EgressChip
                  label="model"
                  scope="mixed"
                  title="Drafting uses the model assigned to project.update_draft in Settings > Models; if the model fails, drafting falls back to the deterministic composer with a receipt."
                />
              ) : null}
            </div>
          ))}
        </div>

        {/* Numeric bounds */}
        <div className="steward-policy-field">
          <label htmlFor="steward-max-retries">Max retries</label>
          <input
            id="steward-max-retries"
            type="number"
            min={0}
            max={100}
            value={draft.max_retries}
            onChange={(e) =>
              ctrl.updatePolicyDraft("max_retries", Number(e.target.value))
            }
            data-testid="steward-policy-max-retries"
          />
        </div>
        <div className="steward-policy-field">
          <label htmlFor="steward-max-actions">Max actions per run</label>
          <input
            id="steward-max-actions"
            type="number"
            min={0}
            max={1000}
            value={draft.max_actions_per_run}
            onChange={(e) =>
              ctrl.updatePolicyDraft(
                "max_actions_per_run",
                Number(e.target.value),
              )
            }
            data-testid="steward-policy-max-actions"
          />
        </div>
        <div className="steward-policy-field">
          <label htmlFor="steward-cooldown">Cooldown (seconds)</label>
          <input
            id="steward-cooldown"
            type="number"
            min={0}
            max={86400}
            value={draft.cooldown_seconds}
            onChange={(e) =>
              ctrl.updatePolicyDraft(
                "cooldown_seconds",
                Number(e.target.value),
              )
            }
            data-testid="steward-policy-cooldown"
          />
        </div>

        {/* Policy error feedback */}
        {ctrl.policyError ? (
          <SurfaceState error={ctrl.policyError} />
        ) : null}
      </SurfaceSection>

      {/* Verbs */}
      <SurfaceVerbs>
        <Button dense variant="ghost" onClick={() => void ctrl.backToList()}>
          Back
        </Button>
        <Button
          dense
          loading={ctrl.policyBusy}
          onClick={() => void ctrl.savePolicy()}
          data-testid="steward-verb-save-policy"
        >
          Save
        </Button>
      </SurfaceVerbs>
    </div>
  );
}

/* ── Vertical scroll-hint: the DoorBoardLane species on the Y axis ── */

/**
 * Attach a vertical scroll-hint edge fade to the posture root.
 * The scroll parent is `.desk-surface-body` (the window body that owns
 * overflow:auto). Pattern reuses DoorBoardLane (HS-145-01): ref on the
 * child, parentElement for the scroll container, data attribute on the
 * ref element, CSS pseudo-elements for the gradient.
 * Constraint: no querySelector/document listeners -- refs only.
 */
function useVerticalScrollHint(ref: React.RefObject<HTMLDivElement | null>) {
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    // The scroll container is the parent (.desk-surface-body).
    const scrollParent = el.parentElement;
    if (!scrollParent) return;

    let raf = 0;
    const update = () => {
      raf = 0;
      const hint = computeVerticalScrollHint(
        scrollParent.scrollTop,
        scrollParent.scrollHeight,
        scrollParent.clientHeight,
      );
      if (el.dataset.scrollHint !== hint) el.dataset.scrollHint = hint;
    };
    const schedule = () => {
      if (!raf) raf = requestAnimationFrame(update);
    };
    update();
    scrollParent.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    return () => {
      if (raf) cancelAnimationFrame(raf);
      scrollParent.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
    };
    // Counsel S-1: mount-once -- the ref identity is stable.
  }, []);
}

/* ── Main Steward posture ── */

export function StewardPosture({ ctrl }: { ctrl: StewardController }) {
  const onOpenRef = useCallback((ref: string) => {
    openSourceRef(ref);
  }, []);
  const postureRef = useRef<HTMLDivElement>(null);
  useVerticalScrollHint(postureRef);

  // ── Loading / error ──
  if (ctrl.loading && ctrl.posture === "off") {
    return <SurfaceState loading />;
  }

  // ── List view ──
  if (ctrl.posture === "list") {
    return (
      <div ref={postureRef} className="steward-posture" data-testid="steward-posture" data-phase="list">
        <SurfaceVerbs>
          <Button dense variant="ghost" onClick={ctrl.exitSteward}>
            Close
          </Button>
          <Button
            dense
            loading={ctrl.runBusy}
            disabled={!ctrl.canRun}
            onClick={() => void ctrl.runOnce()}
            data-testid="steward-verb-run"
            title={ctrl.runDisabledReason || undefined}
            aria-label={ctrl.runDisabledReason ? `Run once: ${ctrl.runDisabledReason}` : "Run once"}
          >
            Run once
          </Button>
          {ctrl.runDisabledReason ? (
            <span className="surface-token" data-tone="warn" data-testid="steward-run-disabled-reason">
              {ctrl.runDisabledReason}
            </span>
          ) : null}
          <Button
            dense
            variant="ghost"
            onClick={() => void ctrl.enterPolicy()}
            data-testid="steward-verb-policy"
          >
            Policy
          </Button>
        </SurfaceVerbs>

        {ctrl.error ? (
          <SurfaceState error={ctrl.error} onRetry={() => void ctrl.enterSteward()} />
        ) : null}

        {ctrl.runs.length === 0 && !ctrl.loading ? (
          <SurfaceState
            empty
            emptyLabel="No steward runs yet. Run once to start."
            emptyGlyph={"*"}
          />
        ) : (
          <RunList ctrl={ctrl} />
        )}

        <SurfaceFooter
          receipt={
            <span className="surface-footer-receipt-line" data-testid="steward-footer-receipt" role="status">
              {`STEWARD RUNS ${ctrl.runs.length}`}
            </span>
          }
        />
      </div>
    );
  }

  // ── Detail view (single run) ──
  if (ctrl.posture === "detail") {
    return (
      <div ref={postureRef} className="steward-posture" data-testid="steward-posture" data-phase="detail">
        {ctrl.error ? <SurfaceState error={ctrl.error} /> : null}
        <RunDetail ctrl={ctrl} onOpenRef={onOpenRef} />
        <SurfaceFooter
          receipt={
            <span className="surface-footer-receipt-line" data-testid="steward-footer-receipt" role="status">
              {ctrl.currentRun
                ? `STEWARD ${runStateLabel(ctrl.currentRun.state).toUpperCase()} ${pluralize(ctrl.currentSteps.length, "STEP", "STEPS")}`
                : "STEWARD"}
            </span>
          }
        />
      </div>
    );
  }

  // ── Policy view ──
  if (ctrl.posture === "policy") {
    return (
      <div ref={postureRef} className="steward-posture" data-testid="steward-posture" data-phase="policy">
        <PolicyEditor ctrl={ctrl} />
        <SurfaceFooter
          receipt={
            <span className="surface-footer-receipt-line" data-testid="steward-footer-receipt" role="status">
              STEWARD POLICY
            </span>
          }
        />
      </div>
    );
  }

  // ── Off posture (should not render) ──
  return null;
}
