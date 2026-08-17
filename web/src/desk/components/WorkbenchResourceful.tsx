import { useEffect, useState } from "react";
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
    detail: "Take the oldest revised Note filed in the Loose Ideas directory.",
  },
  {
    id: "failed_work" as const,
    label: "Prepare recovery plans",
    detail: "Diagnose incomplete work and draft a recovery plan.",
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

  const commit = (enabled: boolean) => write(
    enabled ? "ENABLE RESOURCEFULNESS" : "PAUSE RESOURCEFULNESS",
    async () => {
      await updateResourcefulPolicy(workbenchId, {
        enabled,
        ...settings,
        routines,
      });
      onChanged();
    },
  );

  return (
    <div className="wb-resourceful">
      <p className="wb-automation-safety">
        WHEN IDLE · ONE BOUNDED IMPROVEMENT FROM LOCAL DATA
      </p>
      <div className="wb-resourceful-contract" role="status">
        <span className="desk-chip">{settings.idle_after_minutes} MIN IDLE</span>
        <span className="desk-chip">{settings.cooldown_hours}H COOLDOWN</span>
        <span className="desk-chip">TARGET {settings.nightly_target} / NIGHT</span>
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
              label={routine.label}
              checked={routines.includes(routine.id)}
              onChange={(checked) => setRoutines((current) => checked
                ? [...current, routine.id]
                : current.filter((value) => value !== routine.id))}
            />
            <small>{routine.detail}</small>
          </div>
        ))}
      </div>
      <p className="wb-automation-safety">
        RUNS AS OWNER · ONLY THE SELECTED MAINTENANCE ITEM RUNS · ORDINARY
        PENDING WORK IS NEVER SWEPT · SOURCE DATA IS REVIEW-ONLY
      </p>
      <div className="wb-automation-verbs">
        {policy.enabled ? (
          <>
            <button
              type="button"
              className="desk-chip"
              onClick={() => void commit(true)}
              disabled={!routines.length}
            >
              Save policy
            </button>
            <button
              type="button"
              className="desk-chip"
              data-tone="warn"
              onClick={() => void commit(false)}
            >
              Pause
            </button>
          </>
        ) : (
          <ConfirmVerb
            label={settings.night_only ? "Enable overnight resourcefulness" : "Enable resourcefulness"}
            confirmLabel="RUN AS OWNER?"
            disabled={!routines.length}
            onConfirm={() => void commit(true)}
          />
        )}
      </div>
      <p className="wb-resourceful-status" role="status">
        {policy.enabled
          ? `READY WHEN IDLE · ${policy.nightly_count}/${policy.nightly_target} THIS NIGHT`
          : "PAUSED · NO RESOURCEFUL WORK WILL START"}
      </p>
      {policy.last_fired_at ? (
        <p className="wb-automation-last">Last resourceful work {humanTime(policy.last_fired_at)}</p>
      ) : null}
      {policy.last_error ? <SurfaceState error={policy.last_error} /> : null}
    </div>
  );
}
