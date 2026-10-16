import { useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import type { ResourcefulPolicy } from "../detail-types";
import { updateResourcefulPolicy } from "../api";
import type { WriteAttempt } from "../hooks/useWriteReceipt";
import { ConfirmVerb, SurfaceState } from "../surface/Surface";
import { CheckGadget, GadgetGroup, GadgetRow, StepperGadget } from "../surface/gadgets";
import { humanTime } from "../surface/format";

const ROUTINES = [
  {
    id: "loose_ideas" as const,
    label: "Develop loose ideas",
    detail: "LOOSE IDEAS DIRECTORY · OLDEST REVISED NOTE",
  },
  {
    id: "failed_work" as const,
    label: "Prepare recovery plans",
    detail: "INCOMPLETE WORK · DRAFT PLAN",
  },
];

export function WorkbenchResourceful({
  workbenchId,
  policy,
  write,
  onChanged,
}: {
  workbenchId: string;
  policy: ResourcefulPolicy | null;
  write: WriteAttempt;
  onChanged: () => void;
}) {
  const [pending, setPending] = useState(false);
  const pendingRef = useRef(false);
  const [routines, setRoutines] = useState<ResourcefulPolicy["routines"]>(
    policy?.routines ?? [],
  );
  const [settings, setSettings] = useState<Pick<ResourcefulPolicy,
    "idle_after_minutes" | "cooldown_hours" | "nightly_target" |
    "night_only" | "night_start_hour" | "night_end_hour"
  > | null>(policy ? {
    idle_after_minutes: policy.idle_after_minutes,
    cooldown_hours: policy.cooldown_hours,
    nightly_target: policy.nightly_target,
    night_only: policy.night_only,
    night_start_hour: policy.night_start_hour,
    night_end_hour: policy.night_end_hour,
  } : null);

  useEffect(() => {
    if (!policy) return;
    setRoutines(policy.routines);
    setSettings({
      idle_after_minutes: policy.idle_after_minutes,
      cooldown_hours: policy.cooldown_hours,
      nightly_target: policy.nightly_target,
      night_only: policy.night_only,
      night_start_hour: policy.night_start_hour,
      night_end_hour: policy.night_end_hour,
    });
  }, [policy]);

  if (!policy || !settings) return <SurfaceState loading />;

  const idleMin = settings.idle_after_minutes;
  const cdHours = settings.cooldown_hours;
  const nightlyTarget = settings.nightly_target;
  const lastFiredAt = policy.last_fired_at;

  const commit = (enabled: boolean, verb = enabled ? "ENABLE RESOURCEFULNESS" : "PAUSE RESOURCEFULNESS") => write(verb, async () => {
    // Receipt Retry replays this callback, so it owns the same busy guard.
    if (pendingRef.current) return;
    pendingRef.current = true;
    setPending(true);
    try {
      await updateResourcefulPolicy(workbenchId, { enabled, ...settings, routines });
      onChanged();
    } finally {
      pendingRef.current = false;
      setPending(false);
    }
  });

  return (
    <div className="wb-resourceful">
      <div className="wb-resourceful-contract" role="status">
        <span className="surface-token">LOCAL DATA</span>
        <span className="surface-token">ONE ITEM / RUN</span>
        <span className="desk-chip">{idleMin} MIN IDLE</span>
        <span className="desk-chip">{cdHours}H COOLDOWN</span>
        <span className="desk-chip">TARGET {nightlyTarget} / NIGHT</span>
        <span className="desk-chip">
          {settings.night_only
            ? `${String(settings.night_start_hour).padStart(2, "0")}:00–${String(settings.night_end_hour).padStart(2, "0")}:00`
            : "ANY TIME"}
        </span>
      </div>
      <GadgetGroup label="Idle policy">
        <GadgetRow label="Idle after" fact="1–1440 min">
          <StepperGadget
            label="Idle after minutes"
            value={settings.idle_after_minutes}
            min={1}
            max={1440}
            unit="min"
            onChange={(idle_after_minutes) => setSettings((current) => current
              ? { ...current, idle_after_minutes }
              : current)}
          />
        </GadgetRow>
        <GadgetRow label="Cooldown" fact="1–168 hr">
          <StepperGadget
            label="Cooldown hours"
            value={settings.cooldown_hours}
            min={1}
            max={168}
            unit="hr"
            onChange={(cooldown_hours) => setSettings((current) => current
              ? { ...current, cooldown_hours }
              : current)}
          />
        </GadgetRow>
        <GadgetRow label="Nightly target" fact="1–8 items">
          <StepperGadget
            label="Nightly target"
            value={settings.nightly_target}
            min={1}
            max={8}
            unit="items"
            onChange={(nightly_target) => setSettings((current) => current
              ? { ...current, nightly_target }
              : current)}
          />
        </GadgetRow>
        <GadgetRow label="Overnight only">
          <CheckGadget
            label="Overnight only"
            checked={settings.night_only}
            onChange={(night_only) => setSettings((current) => current
              ? { ...current, night_only }
              : current)}
          />
        </GadgetRow>
        {settings.night_only ? (
          <>
            <GadgetRow label="Night starts" fact="local time">
              <StepperGadget
                label="Night starts hour"
                value={settings.night_start_hour}
                min={0}
                max={23}
                unit=":00"
                onChange={(night_start_hour) => setSettings((current) => current
                  ? { ...current, night_start_hour }
                  : current)}
              />
            </GadgetRow>
            <GadgetRow label="Night ends" fact="local time">
              <StepperGadget
                label="Night ends hour"
                value={settings.night_end_hour}
                min={0}
                max={23}
                unit=":00"
                onChange={(night_end_hour) => setSettings((current) => current
                  ? { ...current, night_end_hour }
                  : current)}
              />
            </GadgetRow>
          </>
        ) : null}
      </GadgetGroup>
      <div className="wb-resourceful-routines">
        {ROUTINES.map((routine) => (
          <div className="wb-resourceful-routine" key={routine.id}>
            <CheckGadget
              variant="token"
              label={routine.label}
              checked={routines.includes(routine.id)}
              onChange={(checked) => setRoutines((current) => checked
                ? [...current, routine.id]
                : current.filter((value) => value !== routine.id))}
            />
            <span className="surface-token wb-resourceful-routine-fact">{routine.detail}</span>
          </div>
        ))}
        <div className="wb-resourceful-limits" aria-label="Execution limits">
          <span className="surface-token">SELECTED MAINTENANCE ONLY</span>
          <span className="surface-token">PENDING WORK UNTOUCHED</span>
          <span className="surface-token">SOURCE DATA · REVIEW-ONLY</span>
        </div>
      </div>
      <div className="wb-automation-verbs">
        <span className="surface-token">RUNS AS OWNER</span>
        {policy.enabled ? (
          <>
            <Button
              dense
              loading={pending}
              onClick={() => void commit(true, "SAVE POLICY")}
              disabled={!routines.length || pending}
            >
              Save policy
            </Button>
            <Button
              dense
              loading={pending}
              data-tone="warn"
              onClick={() => void commit(false)}
            >
              Pause
            </Button>
          </>
        ) : (
          <ConfirmVerb
            label={settings.night_only ? "Enable overnight resourcefulness" : "Enable resourcefulness"}
            confirmLabel="RUN AS OWNER?"
            busy={pending}
            disabled={!routines.length || pending}
            onConfirm={() => void commit(true)}
          />
        )}
      </div>
      <div className="wb-resourceful-status" role="status">
        <span className="surface-token">{policy.enabled ? "READY WHEN IDLE" : "PAUSED"}</span>
        {policy.enabled && policy.nightly_count > 0 ? (
          <span className="surface-token">{policy.nightly_count}/{policy.nightly_target} THIS NIGHT</span>
        ) : null}
        {!policy.enabled ? <span className="surface-token">NO RESOURCEFUL WORK STARTS</span> : null}
      </div>
      {lastFiredAt ? (
        <span className="wb-automation-last surface-token">LAST RUN {humanTime(lastFiredAt)}</span>
      ) : null}
      {policy.last_error ? <SurfaceState error={policy.last_error} /> : null}
    </div>
  );
}
