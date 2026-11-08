// Settings > Meetings: summary, recording, export and the operator fold. Moved out of SettingsCore.tsx.
import { wireClock } from "../../../desk/surface/format";
import { Button } from "../../../components/signal/Signal";
import {
  CheckGadget,
  CycleGadget,
  EgressChip,
  FoldGadget,
  GadgetGroup,
  GadgetRow,
  StringGadget,
} from "../../../desk/surface/gadgets";
import { StateChip, SurfaceColumns } from "../../../desk/surface";
import { egressFor } from "../../../desk/surface/egress";
import { openSurfaceOr } from "../../../desk/shell";
import { LiveMeetingTools } from "../LiveMeetingTools";
import { INTELLIGENCE_AUTO_OPTIONS, MIR_PROFILE_OPTIONS, type SettingsHubWire } from "./prefs";
import type { SettingsBindings } from "./bindings";

/* ── Meetings: display fact + intel row + capture + calendar + RAW (incl. actuators) ── */
export function MeetingsSection({ b, hub, focusHighlight }: {
  b: SettingsBindings;
  hub: { data: SettingsHubWire };
  focusHighlight: string;
}) {
  const { update, val, hl, check, num, cyc, prop, csv } = b;
        const autoVal = String(val(["meeting", "intelligence_auto"]) ?? "every");
        const meetingsHub = (hub.data as Record<string, unknown>).meetings as Record<string, unknown> | undefined;
        // HS-172: null host = no model assigned; real host = chip.
        // The hub returns a host only when a model is actually assigned;
        // until the wire fix lands, fall back to defaultSet as the signal.
        const hubHost = meetingsHub?.host ? String(meetingsHub.host) : null;
        // PHILO-15 B33: the summary ROUTE decides (the hub's `engineSet`, the
        // queue's answer); the host and the default are fallbacks for a hub
        // that sends no route fact.
        const routeEngine = typeof meetingsHub?.engineSet === "boolean" ? meetingsHub.engineSet : null;
        // Astra r1 P2: the owner's OFF is a choice, never a missing model.
        const summariesOff = meetingsHub?.summariesOff === true;
        const hasModel = routeEngine !== null
          ? routeEngine
          : Boolean(hubHost) && hubHost !== "THIS DEVICE"
            ? true
            : Boolean(hub.data.models?.defaultSet);
        const intelHost = hasModel ? hubHost : null;
        const lastRunAt = meetingsHub?.lastRunAt ? String(meetingsHub.lastRunAt) : null;
        const lastRunS = meetingsHub?.lastRunS != null ? Number(meetingsHub.lastRunS) : null;
        const lastRunReceipt = lastRunAt
          ? `LAST RAN ${wireClock(lastRunAt)}${lastRunS != null ? " · " + lastRunS + " S" : ""}`
          : null;
        const autoRecordLink = <Button
          variant="ghost"
          dense
          data-testid="settings-auto-record-link"
          onClick={() => openSurfaceOr("review-meetings", "/history", "record")}
        >Meetings › Record</Button>;
        return (
          <>
            <SurfaceColumns variant="preferences" main={<>
              <GadgetGroup material="inset" label="Summary">
                <GadgetRow label="Make summary" highlight={hl(["meeting", "intelligence_auto"])}>
                  <CycleGadget label="Auto-run the summary" value={autoVal} options={INTELLIGENCE_AUTO_OPTIONS} onChange={(next) => update(["meeting", "intelligence_auto"], next)} />
                </GadgetRow>
                {/* Betterment setup ST1: the engine is a fact line; Engines
                    is its one home (`Engines ›` opens it at Meetings). */}
                <GadgetRow label="Summaries run on" controlWidth="full" highlight={focusHighlight === "engines"}>
                  <span className="prefs-summary-controls" data-testid="settings-summary-controls">
                    {summariesOff ? <StateChip state="idle" label="Summaries off" data-testid="settings-summaries-off" />
                      : hasModel ? <>
                        <span className="prefs-value">{String(meetingsHub?.engine || "Assigned engine")}</span>
                        {intelHost && egressFor(intelHost).label ? <EgressChip label={egressFor(intelHost).label} scope={egressFor(intelHost).scope} /> : null}
                      </> : <StateChip state="warning" label="No engine" data-testid="settings-no-model" />}
                    <Button variant={!hasModel && !summariesOff ? "secondary" : "ghost"} dense onClick={() => openSurfaceOr("configure-runs-on", "/models")} data-testid="settings-engines-link">
                      Engines ›
                    </Button>
                  </span>
                </GadgetRow>
              </GadgetGroup>
              <GadgetGroup material="inset" label="Recording">
                <GadgetRow label="Microphone" highlight={hl(["meeting", "mic_device"])}>
                  <span className="prefs-value">
                    {String(val(["meeting", "mic_device"]) || "System default")}
                  </span>
                </GadgetRow>
                <GadgetRow label="System audio">
                  <span className="prefs-value">
                    {String(val(["meeting", "system_audio_device"]) || "Auto")}
                  </span>
                </GadgetRow>
                <div data-testid="settings-auto-record"><GadgetRow label="Auto-record" highlight={hl(["meeting", "auto_record"])}>{autoRecordLink}</GadgetRow></div>
                <FoldGadget title="Audio devices">
                  <GadgetRow wide label="Mic device" fact="Custom name" controlWidth="full">
                    <StringGadget
                      label="Mic device"
                      placeholder="System default"
                      value={String(val(["meeting", "mic_device"]) ?? "")}
                      onChange={(next) => update(["meeting", "mic_device"], next || null)}
                    />
                  </GadgetRow>
                  <GadgetRow wide label="System audio name" fact="Custom name" controlWidth="full">
                    <StringGadget
                      label="System audio device"
                      placeholder="Auto"
                      value={String(val(["meeting", "system_audio_device"]) ?? "")}
                      onChange={(next) => update(["meeting", "system_audio_device"], next || null)}
                    />
                  </GadgetRow>
                </FoldGadget>
              </GadgetGroup>
              {/* W2-LIVE (2026-10-27): the Live window's old gear wing
                  lives here now; Live's toolbar verb Settings opens it. */}
              <LiveMeetingTools />
            </>} side={<>
            <GadgetGroup material="inset" label="Export">
              <GadgetRow label="Auto export" controlWidth="short" highlight={hl(["meeting", "auto_export"])}>
                <CheckGadget
                  variant="state"
                  label="Auto export"
                  checked={Boolean(val(["meeting", "auto_export"]))}
                  onChange={(next) => update(["meeting", "auto_export"], next)}
                />
              </GadgetRow>
              {Boolean(val(["meeting", "auto_export"])) ? (
                <GadgetRow label="Format">
                  <CycleGadget
                    label="Export format"
                    value={String(val(["meeting", "export_format"]) ?? "markdown")}
                    options={[
                      { value: "txt", label: "TXT" },
                      { value: "markdown", label: "MD" },
                      { value: "json", label: "JSON" },
                      { value: "srt", label: "SRT" },
                    ]}
                    onChange={(next) => update(["meeting", "export_format"], next)}
                  />
                </GadgetRow>
              ) : null}
            </GadgetGroup>
            </>} />
            {/* HS-139-04: all operator knobs fold behind one RAW well.
                PHILO-17 U35: Allow actuators is one of them (it sat on the
                face), and the fold carries no hand-kept count. */}
            <FoldGadget title="More">
              {lastRunReceipt ? <span className="gadget-fact" data-testid="settings-last-ran">{lastRunReceipt}</span> : null}
              <GadgetGroup material="inset" label="Capture">
                {check(["meeting", "diarization_enabled"], "Diarization")}
                {check(["meeting", "diarize_mic"], "Diarize mic")}
                {prop(["meeting", "similarity_threshold"], "Similarity", {
                  min: 0,
                  max: 1,
                  step: 0.05,
                })}
              </GadgetGroup>
              {/* HS-202-04 (F06): same rule, the advanced sheet. */}
              <GadgetGroup material="inset" label="Summary">
                {check(["meeting", "intel_cloud_store"], "Cloud store")}
              </GadgetGroup>
              <GadgetGroup material="inset" label="Deferred queue">
                {num(["meeting", "intel_retry_base_seconds"], "Retry base", {
                  unit: "s",
                  min: 1,
                  step: 5,
                })}
                {num(["meeting", "intel_retry_max_seconds"], "Retry max", {
                  unit: "s",
                  min: 1,
                  step: 60,
                })}
                {num(
                  ["meeting", "intel_retry_max_attempts"],
                  "Retry attempts",
                  {
                    min: 1,
                  },
                )}
                {/* PARKED: alert webhook header is not persisted by this writer. */}
              </GadgetGroup>
              <GadgetGroup material="inset" label="Routing">
                {cyc(
                  ["meeting", "routing_profile"],
                  "Routing profile",
                  MIR_PROFILE_OPTIONS,
                )}
                {check(["meeting", "intent_router_enabled"], "Intent router")}
                {num(["meeting", "intent_window_seconds"], "Intent window", {
                  unit: "s",
                  min: 10,
                  step: 10,
                })}
                {num(["meeting", "intent_step_seconds"], "Intent step", {
                  unit: "s",
                  min: 5,
                  step: 5,
                })}
                {prop(
                  ["meeting", "intent_score_threshold"],
                  "Score threshold",
                  {
                    min: 0,
                    max: 1,
                    step: 0.05,
                  },
                )}
                {num(
                  ["meeting", "intent_hysteresis_windows"],
                  "Hysteresis windows",
                  { min: 0, max: 10 },
                )}
                {check(
                  ["meeting", "intent_segment_probe_enabled"],
                  "Segment probe",
                )}
                {csv(["meeting", "disabled_plugins"], "Disabled plugins")}
              </GadgetGroup>
              <GadgetGroup material="inset" label="Actuators">
                {check(["meeting", "allow_actuators"], "Allow actuators")}
                {csv(["meeting", "allowed_actuators"], "Allowed actuators")}
                {csv(["meeting", "webhook_allowed_hosts"], "Webhook hosts")}
              </GadgetGroup>
            </FoldGadget>
          </>
        );
}
