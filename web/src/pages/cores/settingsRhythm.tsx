// Betterment setup ST1 — Rhythm has one home, Settings ▸ Rhythm.
//
// Notify and quiet hours read and write the heartbeat policy
// (`/api/settings/heartbeat`), the one store the notices loop, the cadence
// tick and the Telegram brief read (heartbeat_service.read_quiet_hours). The
// retired `cadence.quiet_hours_*` keys are not shown. The parked Rhythm
// window's sweep, Where it runs, the Project mutes and the loops are under
// the section's Advanced fold: CadenceCore, mounted there on first open.
import { useState } from "react";
import { CycleGadget, FoldGadget, GadgetGroup, GadgetRow, StepperGadget } from "../../desk/surface";
import { SurfaceState } from "../../desk/surface/Surface";
import { apiFetch, readableError } from "../../lib/api";
import { useResource } from "../pageSupport";
import { CadenceCore } from "./CadenceCore";

type Heartbeat = {
  notify?: string;
  quiet_hours?: { start?: number; end?: number };
};

const NOTIFY_OPTIONS = [
  { value: "off", label: "Off" },
  { value: "edge", label: "On the edge" },
  { value: "every_sweep", label: "Every sweep" },
];

/** Notify and Quiet hours, on the heartbeat policy. `onSaved` lets the
 *  Settings foot say Saved; `highlight` lights the row a deep link names. */
export function RhythmNoticeRows({
  onSaved,
  onWrite,
  highlight,
}: {
  onSaved?: () => void;
  onWrite?: () => void;
  highlight?: string | null;
}) {
  const heartbeat = useResource<Heartbeat | null>("/api/settings/heartbeat", null);
  const [error, setError] = useState("");
  const data = heartbeat.data;
  const start = data?.quiet_hours?.start ?? 22;
  const end = data?.quiet_hours?.end ?? 8;
  const put = async (patch: Heartbeat) => {
    setError("");
    // Shown at once; the hub's answer is the truth after it.
    heartbeat.setData({ ...(data ?? {}), ...patch, quiet_hours: { start, end, ...patch.quiet_hours } });
    try {
      const saved = await apiFetch<Heartbeat>("/api/settings/heartbeat", { method: "PUT", json: patch });
      heartbeat.setData(saved);
      onSaved?.();
      onWrite?.();
    } catch (cause) {
      setError(`Not saved · ${readableError(cause)}`);
      void heartbeat.reload();
    }
  };
  return (
    <GadgetGroup material="inset" label="Notices">
      {heartbeat.error && !data ? (
        <SurfaceState error={`Not read · ${heartbeat.error}`} onRetry={() => void heartbeat.reload()} />
      ) : null}
      {error ? <SurfaceState error={error} onRetry={() => void heartbeat.reload().then(() => setError(""))} /> : null}
      <GadgetRow label="Notify" highlight={highlight === "heartbeat.notify"} controlWidth="standard">
        <CycleGadget
          label="Notify"
          value={data?.notify ?? "edge"}
          options={NOTIFY_OPTIONS}
          onChange={(next) => void put({ notify: next })}
        />
      </GadgetRow>
      <GadgetRow label="Quiet from" highlight={highlight === "heartbeat.quiet_hours"} controlWidth="short">
        <StepperGadget label="Quiet from" value={start} unit="h" min={0} max={23}
          onChange={(next) => void put({ quiet_hours: { start: next } })} />
      </GadgetRow>
      <GadgetRow label="Quiet until" controlWidth="short">
        <StepperGadget label="Quiet until" value={end} unit="h" min={0} max={23}
          onChange={(next) => void put({ quiet_hours: { end: next } })} />
      </GadgetRow>
    </GadgetGroup>
  );
}

/** The parked Rhythm window's sweep, Where it runs, mutes and loops, behind
 *  a fold. It mounts on first open (its reads wait until he asks), and a
 *  Notify or quiet-hours write above draws it again (`revision`). */
export function RhythmSweepFold({ revision = 0 }: { revision?: number }) {
  const [opened, setOpened] = useState(false);
  return (
    <FoldGadget title="Sweep and loops" onToggle={(open) => { if (open) setOpened(true); }}>
      <div className="prefs-rhythm-sweep" data-testid="settings-rhythm-sweep">
        {opened ? <CadenceCore key={revision} embedded /> : null}
      </div>
    </FoldGadget>
  );
}
