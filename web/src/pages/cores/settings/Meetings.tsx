// Meetings preferences share the bounded pane and label/control rows.
import { useState } from "react";
import { PreferencePane, SegmentedTabs, GadgetGroup, GadgetRow, CycleGadget } from "../../../desk/surface";
import { LiveMeetingTools } from "../LiveMeetingTools";
import { INTELLIGENCE_AUTO_OPTIONS, type SettingsHubWire } from "./prefs";
import type { SettingsBindings } from "./bindings";

export function MeetingsSection({ b, hub, focusHighlight }: { b: SettingsBindings; hub: { data: SettingsHubWire }; focusHighlight: string }) {
  const { val, update, check, str, cyc, csv } = b;
  const [tab, setTab] = useState(focusHighlight === "live-meeting" ? "recording" : "summary");
  return (
    <PreferencePane label="Meetings">
      <SegmentedTabs
        label="Meetings"
        value={tab}
        onChange={setTab}
        tabs={[
          { id: "summary", label: "Summary" },
          { id: "recording", label: "Recording" },
          { id: "actuators", label: "Actions" },
        ]}
      >
        {tab === "summary" ? (
          <>
            <GadgetGroup label="Summary">
              <GadgetRow label="Make summary" highlight={b.hl(["meeting", "intelligence_auto"])}>
                <CycleGadget
                  label="Auto-run the summary"
                  value={String(val(["meeting", "intelligence_auto"]) ?? "every")}
                  options={INTELLIGENCE_AUTO_OPTIONS}
                  onChange={(next) => update(["meeting", "intelligence_auto"], next)}
                />
              </GadgetRow>
              <GadgetRow label="Summaries run on">
                <span data-testid="settings-summary-controls">
                  {hub.data.meetings?.summariesOff ? (
                    <span data-testid="settings-summaries-off">Summaries off</span>
                  ) : hub.data.meetings?.engineSet === false || (!hub.data.models.defaultSet && !hub.data.meetings?.engine) ? (
                    <span data-testid="settings-no-model">No engine</span>
                  ) : (
                    hub.data.meetings?.engine || "Assigned engine"
                  )}
                </span>
              </GadgetRow>
              {check(["meeting", "intel_cloud_store"], "Cloud store")}
            </GadgetGroup>
            <GadgetGroup label="Export">
              {check(["meeting", "auto_export"], "Auto export")}
              {cyc(["meeting", "export_format"], "Export format", [
                { value: "txt", label: "TXT" },
                { value: "markdown", label: "MD" },
                { value: "json", label: "JSON" },
                { value: "srt", label: "SRT" },
              ])}
            </GadgetGroup>
          </>
        ) : null}
        {tab === "recording" ? (
          <>
            <GadgetGroup label="Audio devices">
              {str(["meeting", "mic_device"], "Microphone", {
                placeholder: "System default",
              })}
              {str(["meeting", "system_audio_device"], "System audio", {
                placeholder: "Auto",
              })}
            </GadgetGroup>
            <GadgetGroup label="Speakers">
              {check(["meeting", "diarization_enabled"], "Identify speakers")}
              {check(["meeting", "diarize_mic"], "Identify microphone speakers")}
            </GadgetGroup>
            <LiveMeetingTools />
          </>
        ) : null}
        {tab === "actuators" ? (
          <GadgetGroup label="Allowed actions">
            {check(["meeting", "allow_actuators"], "Allow actions")}
            {csv(["meeting", "disabled_plugins"], "Disabled plugins")}
            {csv(["meeting", "allowed_actuators"], "Allowed actions")}
            {csv(["meeting", "webhook_allowed_hosts"], "Webhook hosts")}
          </GadgetGroup>
        ) : null}
      </SegmentedTabs>
    </PreferencePane>
  );
}
