// HS-139-03 -- Capture + export config lives ON the Meetings surface
// (edit-in-world law). The four controls (mic device, system audio
// device, auto-export, export format) moved from Settings > Meetings
// to here. Writes still round-trip through /api/settings with revision
// concurrency via withRevision().
import { useEffect, useRef, useState } from "react";
import { apiFetch, readableError } from "../../../lib/api";
import { withRevision } from "../../../lib/settingsWrite";
import {
  CheckGadget,
  CycleGadget,
  GadgetGroup,
  GadgetRow,
  StringGadget,
} from "../../../desk/surface/gadgets";

const EXPORT_FORMAT_OPTIONS = [
  { value: "txt", label: "TXT" },
  { value: "markdown", label: "MD" },
  { value: "json", label: "JSON" },
  { value: "srt", label: "SRT" },
];

/** Compact capture + export config section for the Meetings surface. */
export function MeetingsConfig() {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");
  const revisionRef = useRef<string | undefined>(undefined);
  const saveTimer = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => {
    void apiFetch<Record<string, unknown>>("/api/settings").then((result) => {
      setData(result);
      revisionRef.current = result._revision as string | undefined;
    });
    return () => clearTimeout(saveTimer.current);
  }, []);

  if (!data) return null;

  const meeting = (data.meeting ?? {}) as Record<string, unknown>;

  const save = async (patch: Record<string, unknown>) => {
    setError("");
    try {
      const result = await apiFetch<{ settings?: Record<string, unknown> }>(
        "/api/settings",
        {
          method: "PUT",
          json: withRevision(patch, { _revision: revisionRef.current }),
        },
      );
      const next = result.settings ?? patch;
      setData(next as Record<string, unknown>);
      revisionRef.current = (next as Record<string, unknown>)._revision as
        | string
        | undefined;
    } catch (reason) {
      setError(readableError(reason));
    }
  };

  const update = (key: string, value: unknown) => {
    const nextMeeting = { ...meeting, [key]: value };
    const nextData = { ...data, meeting: nextMeeting };
    setData(nextData);
    revisionRef.current = nextData._revision as string | undefined;
    clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => void save(nextData), 700);
  };

  return (
    <GadgetGroup label="Capture + export">
      <GadgetRow label="Mic device" fact="device name">
        <StringGadget
          label="Mic device"
          value={String(meeting.mic_device ?? "")}
          onChange={(next) => update("mic_device", next || null)}
        />
      </GadgetRow>
      <GadgetRow label="System audio" fact="device name">
        <StringGadget
          label="System audio device"
          value={String(meeting.system_audio_device ?? "")}
          onChange={(next) => update("system_audio_device", next || null)}
        />
      </GadgetRow>
      <GadgetRow label="Auto export">
        <CheckGadget
          label="Auto export"
          checked={Boolean(meeting.auto_export)}
          onChange={(next) => update("auto_export", next)}
        />
      </GadgetRow>
      <GadgetRow label="Format">
        <CycleGadget
          label="Export format"
          value={String(meeting.export_format ?? "txt")}
          options={EXPORT_FORMAT_OPTIONS}
          onChange={(next) => update("export_format", next)}
        />
      </GadgetRow>
      {error ? (
        <div className="prefs-egress-line">
          <span className="gadget-fact" data-tone="danger">
            {error}
          </span>
        </div>
      ) : null}
    </GadgetGroup>
  );
}
