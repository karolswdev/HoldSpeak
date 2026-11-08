// Settings > Reach: the channels, quiet hours, Cadence and the morning brief. Moved out of SettingsCore.tsx.
import { FoldGadget, GadgetGroup } from "../../../desk/surface/gadgets";
import { SurfaceColumns } from "../../../desk/surface";
import { RhythmNoticeRows, RhythmSweepFold } from "../settingsRhythm";
import { ReachSettingsPane } from "../../../desk/reach/ReachSettings";
import { CADENCE_PRESSURE_OPTIONS } from "../settingsPrefs";
import type { SettingsBindings } from "./bindings";

/* ── Reach (PG-DIRECTION DIR6, ruled 2026-10-31: Notices becomes
         Reach): the channels, Telegram, when to reach you, quiet hours,
         the digest, Later means; Cadence and the morning brief folded. ── */
export function ReachSection({ b, focusHighlight, onSaved, heartbeatRevision, onHeartbeatWrite }: {
  b: SettingsBindings;
  focusHighlight: string;
  onSaved: () => void;
  heartbeatRevision: number;
  onHeartbeatWrite: () => void;
}) {
  const { check, num, cyc } = b;
        return (
          <ReachSettingsPane
            highlight={focusHighlight}
            onSaved={onSaved}
            quiet={
              /* Betterment setup ST1: quiet hours have one store, the
                 heartbeat policy the notices loop reads (shared with the Phone). */
              <RhythmNoticeRows
                highlight={focusHighlight}
                onSaved={onSaved}
                onWrite={onHeartbeatWrite}
              />
            }
            cadence={<>
            <SurfaceColumns variant="preferences" main={<>
              <GadgetGroup material="inset" label="Cadence">
                {check(["cadence", "enabled"], "Enabled")}
                {cyc(
                  ["cadence", "pressure"],
                  "Pressure",
                  CADENCE_PRESSURE_OPTIONS,
                )}
                {num(["cadence", "max_nudges_per_day"], "Max nudges", {
                  unit: "/day",
                  min: 0,
                })}
              </GadgetGroup>
            </>} side={<>
              {/* PHILO-15 05: the morning Brief job, ON by default; its own setting. */}
              <GadgetGroup material="inset" label="Morning brief">
                {check(["cadence", "brief_enabled"], "Enabled")}
                {num(["cadence", "brief_hour"], "Make at", {
                  unit: "h",
                  min: 0,
                  max: 23,
                })}
              </GadgetGroup>
            </>} />
            {/* HS-139-04: operator knobs fold behind RAW. */}
            <FoldGadget title="More">
              <GadgetGroup material="inset">
                {check(["cadence", "use_llm"], "Use LLM")}
                {num(["cadence", "tick_interval_seconds"], "Tick interval", {
                  unit: "s",
                  min: 30,
                  step: 30,
                })}
                {/* PG-DIRECTION DIR5: one bot; Cadence's nudges and brief go to
                    the chat paired in Reach (the old allow-list is read once). */}
                {check(["cadence_telegram", "enabled"], "Cadence on Telegram")}
              </GadgetGroup>
              {/* Betterment setup ST1: the parked Rhythm window's sweep
                  interval, Run now, Where it runs, mutes and loops. */}
              <RhythmSweepFold revision={heartbeatRevision} />
            </FoldGadget>
            </>}
          />
        );
}
