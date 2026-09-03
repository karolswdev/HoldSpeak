// HS-167-05 -- the Steward posture recomposed on the surface library.
// D7: circuit FIRST (ActionNotice + ledger), THE RUN as ProgressPlan,
// RUNS ledger, POLICY as GadgetGroup with StepperGadgets.
// R4: rate=counts-only, effect chips, grant tokens, label dedup, circuit glyph.

import { useCallback, useRef } from "react";
import { Button } from "../../../components/signal/Signal";
import {
  EgressChip,
  SurfaceFooter,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceState,
  SurfaceToggle,
  SurfaceVerbs,
  StateChip,
  ActionNotice,
  ProgressPlan,
  GadgetGroup,
  GadgetRow,
  CheckGadget,
  StepperGadget,
  humanTime,
  useScrollHint,
  type PlanStep,
} from "../../../desk/surface";
import { openSourceRef } from "../../../desk/surface/citations";
import type { StewardController } from "./useStewardController";
import type { StewardRun, StewardStep } from "./model";
import {
  EFFECT_KINDS,
  circuitStateLabel,
  circuitStateTone,
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
  summaryReasonLabel,
} from "./model";
import "./steward-posture.css";

/* ── Grant vocabulary (coordinator's uppercase tokens) ── */

const GRANT_TOKENS: Record<string, string> = {
  refresh_sources: "REFRESH SOURCES",
  create_proposals: "CREATE PROPOSALS",
  apply_proposal_effects: "APPLY EFFECTS",
  draft_update: "DRAFT UPDATE",
  create_door_item: "DOOR ITEM",
};

function grantToken(kind: string): string {
  return GRANT_TOKENS[kind] ?? kind.replace(/_/g, " ").toUpperCase();
}

/* ── Ref human label (no raw IDs on glass) ── */

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

/* ── Build ProgressPlan steps from the six canonical phases ── */

const PHASES = ["observe", "compare", "propose", "act", "verify", "record"] as const;

interface PlanResult {
  planSteps: PlanStep[];
  allRefs: string[];
  effectChips: { label: string; ref?: string }[];
  hasPartial: boolean;
  phaseCount: number;
}

function buildPlanSteps(steps: StewardStep[], run: StewardRun): PlanResult {
  const byPhase = new Map<string, StewardStep[]>();
  for (const step of steps) {
    const phase = step.phase || "unknown";
    const list = byPhase.get(phase);
    if (list) list.push(step);
    else byPhase.set(phase, [step]);
  }

  const completedPhases = new Set(run.summary.phasesCompleted ?? []);
  const stoppedPhase = run.summary.interruptedPhase;
  const allRefs: string[] = [];
  const effectChips: { label: string; ref?: string }[] = [];
  let hasPartial = false;
  let phaseCount = 0;

  const planSteps: PlanStep[] = PHASES.map((phase) => {
    const phaseSteps = byPhase.get(phase) ?? [];

    for (const s of phaseSteps) {
      if (stepIsPartial(s)) hasPartial = true;
      for (const ref of receiptRefs(s)) {
        if (!allRefs.includes(ref)) allRefs.push(ref);
      }
      effectChips.push({
        label: effectKindLabel(s.effectKind),
        ref: receiptRefs(s)[0],
      });
    }

    let status: PlanStep["status"] = "queued";
    if (phaseSteps.length > 0) {
      const hasRunning = phaseSteps.some((s) => s.state === "running");
      const hasFailed = phaseSteps.some((s) => s.state === "failed" || s.state === "interrupted");
      const allDone = phaseSteps.every((s) => s.state === "completed" || s.state === "skipped");
      if (hasRunning) status = "running";
      else if (hasFailed) status = "failed";
      else if (allDone) status = "done";
    } else if (completedPhases.has(phase)) {
      status = "done";
    }
    if (stoppedPhase === phase && status !== "done") {
      status = "failed";
    }
    if (status !== "queued") phaseCount++;

    // Rate = COUNTS ONLY, never effect-kind names
    const rateParts: string[] = [];
    if (phase === "observe" && phaseSteps.length > 0) {
      rateParts.push(`${phaseSteps.length} source${phaseSteps.length === 1 ? "" : "s"}`);
      const totalCalls = phaseSteps.reduce((sum, s) => sum + (s.receipt.calls ?? 0), 0);
      if (totalCalls > 0) {
        rateParts.push(`${totalCalls} call${totalCalls === 1 ? "" : "s"}`);
      }
    } else if (phase === "propose" && phaseSteps.length > 0) {
      rateParts.push(String(phaseSteps.length));
    } else if (phase === "act" && phaseSteps.length > 0) {
      rateParts.push(`${phaseSteps.length} effect${phaseSteps.length === 1 ? "" : "s"}`);
    }

    let detail: string | undefined;
    if (phaseSteps.some((s) => stepIsPartial(s))) {
      detail = "PARTIAL";
    }

    return {
      id: phase,
      label: phaseLabel(phase),
      status,
      rate: rateParts.length > 0 ? rateParts.join(" · ") : undefined,
      detail,
    };
  });

  return { planSteps, allRefs, effectChips, hasPartial, phaseCount };
}

/* ── Run detail view: ProgressPlan + effect/receipt chips ── */

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

  const { planSteps, allRefs, effectChips, hasPartial, phaseCount } =
    buildPlanSteps(ctrl.currentSteps, run);

  const runIndex = ctrl.runs.findIndex((r) => r.id === run.id);
  const runNumber = runIndex >= 0 ? ctrl.runs.length - runIndex : 1;

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

      {/* D7 R4: THE RUN as ProgressPlan — rate=counts only */}
      <div data-testid="steward-run-plan">
        <ProgressPlan
          steps={planSteps}
          ariaLabel="Steward run phases"
        />
      </div>

      {/* Partial marker for glass compat */}
      {hasPartial ? (
        <span className="surface-token" data-tone="warn" data-testid="steward-step-partial" hidden>
          PARTIAL
        </span>
      ) : null}

      {/* R4: effect-kind labels as tokens + receipt refs as openable chips */}
      {(effectChips.length > 0 || allRefs.length > 0) ? (
        <div className="steward-receipt-refs" data-testid="steward-receipt-refs">
          {effectChips.map((chip, i) => (
            <span key={`ek-${i}`} className="surface-token">
              {chip.label}
            </span>
          ))}
          {allRefs.map((ref) => (
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
        </div>
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
      <SurfaceLedger count={`RUNS ${ctrl.runs.length}`} cols="room">
        <ul className="surface-ledger-rows">
          {ctrl.runs.map((run) => {
            const tone = runStateTone(run.state);
            const substance = runRowSubstance(run);
            return (
              <SurfaceLedgerRow
                key={run.id}
                data-testid="steward-list-item"
                expands={false}
                wrap
                lead={
                  <span className="surface-token" data-tone={tone}>
                    {runStateLabel(run.state)}
                  </span>
                }
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
                time={humanTime(run.createdAt ?? "")}
                trailing={
                  <span aria-hidden="true">{">"}</span>
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

  const activeWatches = ctrl.watches.filter((w) => w.state === "active" || w.state === "tested");
  const cadences = activeWatches.map((w) => w.evaluationCadenceMinutes).filter((c) => c > 0);
  const cadence = cadences.length > 0 ? Math.min(...cadences) : 60;

  const circuitWatches = ctrl.watches.filter(
    (w) => w.circuitState !== "closed",
  );

  // R4: dirty check for primary Save
  const policyDirty = ctrl.policy
    ? draft.enabled !== ctrl.policy.enabled ||
      draft.unattended_enabled !== ctrl.policy.unattendedEnabled ||
      draft.max_retries !== ctrl.policy.maxRetries ||
      draft.max_actions_per_run !== ctrl.policy.maxActionsPerRun ||
      draft.cooldown_seconds !== ctrl.policy.cooldownSeconds ||
      JSON.stringify(draft.eligible_effect_kinds) !==
        JSON.stringify(ctrl.policy.eligibleEffectKinds)
    : true;

  return (
    <div className="steward-policy" data-testid="steward-policy">
      {/* R4 item 4: circuit — ActionNotice with tokens, lead=glyph ⌁, StateChip in cells */}
      {circuitWatches.length > 0 ? (
        <>
          <ActionNotice tone="warn" icon="⚡">
            <span className="surface-token">CIRCUIT OPEN</span>
            {" "}
            <span className="surface-token">{pluralize(circuitWatches.length, "SOURCE")}</span>
          </ActionNotice>
          <SurfaceLedger count={`CIRCUITS ${circuitWatches.length}`} cols="room">
            <ul className="surface-ledger-rows">
              {circuitWatches.map((w) => (
                <SurfaceLedgerRow
                  key={w.id}
                  data-testid="steward-circuit-row"
                  expands={false}
                  wrap
                  lead={
                    <span className="steward-circuit-glyph" aria-hidden="true">⌁</span>
                  }
                  time={w.circuitOpenedAt ? humanTime(w.circuitOpenedAt) : ""}
                  primary={w.name || w.connectorId}
                  cells={
                    <>
                      <span
                        className="surface-token"
                        data-tone={circuitStateTone(w.circuitState)}
                        data-testid="steward-circuit-state"
                      >
                        {circuitStateLabel(w.circuitState)}
                      </span>
                      {w.circuitFailureStreak > 0 ? (
                        <span className="surface-token" data-testid="steward-circuit-streak">
                          {pluralize(w.circuitFailureStreak, "failure")}
                        </span>
                      ) : null}
                    </>
                  }
                  trailing={
                    <Button dense variant="ghost" aria-label={`Retry ${w.name || w.connectorId}`}>
                      Retry
                    </Button>
                  }
                />
              ))}
            </ul>
          </SurfaceLedger>
        </>
      ) : null}

      {/* R4 item 2: POLICY as ONE GadgetGroup — label ONCE per row */}
      <GadgetGroup label="Steward policy">
        <div data-testid="steward-policy-enabled-row">
          <GadgetRow label="Steward enabled">
            <SurfaceToggle
              label="Steward enabled"
              checked={draft.enabled}
              onChange={(v) => ctrl.updatePolicyDraft("enabled", v)}
            />
          </GadgetRow>
        </div>

        <div data-testid="steward-unattended-section">
          <GadgetRow label="Unattended">
            <div data-testid="steward-unattended-row">
              <SurfaceToggle
                label="Unattended operation"
                checked={draft.unattended_enabled}
                onChange={(v) => ctrl.updatePolicyDraft("unattended_enabled", v)}
              />
            </div>
          </GadgetRow>
          {/* R4: grant as SEPARATE surface-token chips, 6px gap */}
          <div
            data-testid="steward-grant-text"
            role="status"
            aria-live="polite"
            className="steward-grant-tokens"
          >
            {draft.unattended_enabled ? (
              <>
                <span className="surface-token">WHILE ENABLED</span>
                <span className="surface-token">EVERY {draft.evaluation_cadence_minutes ?? cadence} MIN</span>
                {draft.eligible_effect_kinds.length > 0
                  ? draft.eligible_effect_kinds.map((kind: string) => (
                      <span key={kind} className="surface-token">{grantToken(kind)}</span>
                    ))
                  : <span className="surface-token">NO EFFECTS</span>
                }
                <span className="surface-token">MAX {draft.max_actions_per_run} / RUN</span>
              </>
            ) : (
              <span className="surface-token">UNATTENDED OFF</span>
            )}
          </div>
        </div>

        <GadgetRow label="Every">
          <span className="steward-cadence-stepper">
            <StepperGadget
              label="Evaluation cadence"
              value={draft.evaluation_cadence_minutes ?? cadence}
              onChange={(v) => ctrl.updatePolicyDraft("evaluation_cadence_minutes", v)}
              min={1}
              max={1440}
              step={1}
              unit="min"
            />
          </span>
        </GadgetRow>

        <GadgetRow label="Effects">
          <div data-testid="steward-policy-effects">
            {EFFECT_KINDS.map((kind) => (
              <div key={kind} className="steward-policy-effect-row">
                <CheckGadget
                  label={effectKindLabel(kind)}
                  checked={draft.eligible_effect_kinds.includes(kind)}
                  onChange={() => ctrl.toggleEffectKind(kind)}
                />
                <span data-testid={`steward-policy-kind-label-${kind}`}>
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
        </GadgetRow>

        <GadgetRow label="Max actions">
          <span data-testid="steward-policy-max-actions">
            <StepperGadget
              label="Max actions per run"
              value={draft.max_actions_per_run}
              onChange={(v) => ctrl.updatePolicyDraft("max_actions_per_run", v)}
              min={0}
              max={1000}
              step={1}
            />
          </span>
        </GadgetRow>
        <GadgetRow label="Max retries">
          <span data-testid="steward-policy-max-retries">
            <StepperGadget
              label="Max retries"
              value={draft.max_retries}
              onChange={(v) => ctrl.updatePolicyDraft("max_retries", v)}
              min={0}
              max={100}
              step={1}
            />
          </span>
        </GadgetRow>
        <GadgetRow label="Cooldown">
          <span data-testid="steward-policy-cooldown">
            <StepperGadget
              label="Cooldown seconds"
              value={draft.cooldown_seconds}
              onChange={(v) => ctrl.updatePolicyDraft("cooldown_seconds", v)}
              min={0}
              max={86400}
              step={1}
              unit="s"
            />
          </span>
        </GadgetRow>
      </GadgetGroup>

      {ctrl.policyError ? (
        <SurfaceState error={ctrl.policyError} />
      ) : null}

      {/* R4: Save is primary while dirty, Back is quiet */}
      <SurfaceVerbs>
        <Button dense variant="ghost" onClick={() => void ctrl.backToList()}>
          Back
        </Button>
        <Button
          dense
          variant={policyDirty ? "primary" : undefined}
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

/* ── Main Steward posture ── */

export function StewardPosture({ ctrl }: { ctrl: StewardController }) {
  const onOpenRef = useCallback((ref: string) => {
    openSourceRef(ref);
  }, []);
  const postureRef = useRef<HTMLDivElement>(null);
  useScrollHint(postureRef, null, "y");

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
    const run = ctrl.currentRun;
    const runIndex = run ? ctrl.runs.findIndex((r) => r.id === run.id) : -1;
    const runNumber = runIndex >= 0 ? ctrl.runs.length - runIndex : 1;
    const { phaseCount } = run
      ? buildPlanSteps(ctrl.currentSteps, run)
      : { phaseCount: 0 };
    return (
      <div ref={postureRef} className="steward-posture" data-testid="steward-posture" data-phase="detail">
        {ctrl.error ? <SurfaceState error={ctrl.error} /> : null}
        <RunDetail ctrl={ctrl} onOpenRef={onOpenRef} />
        <SurfaceFooter
          receipt={
            <span className="surface-footer-receipt-line" data-testid="steward-footer-receipt" role="status">
              {run
                ? `RUN ${runNumber} · ${runStateLabel(run.state).toUpperCase()} · ${phaseCount} PHASE${phaseCount === 1 ? "" : "S"}`
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

  return null;
}
