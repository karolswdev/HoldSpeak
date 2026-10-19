// Betterment capture C7 "One home for recording": Meetings ▸ Record.
// Record and Import, then Coming up (the calendar's next meetings and every
// armed recording), Another time… (the manual form, in place) and the
// auto-record switch (`meeting.auto_record`, moved here from Settings ▸
// Meetings; Settings keeps its own control). It replaces the drop-zone page;
// a chosen file still opens the import form (ImportSection).
import { useCallback, useEffect, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch, readableError } from "../../../lib/api";
import { useDesk } from "../../../desk/store";
import { Disclosure } from "../../../desk/surface/patterns/Disclosure";
import { CheckGadget } from "../../../desk/surface/gadgets";
import { SurfaceSettingRow } from "../../../desk/surface/Surface";
import { ScheduleFormInline } from "../../../desk/components/ScheduleCreateWindow";
import { ComingUp } from "./ComingUp";
import "./coming-up.css";

type AutoRecord = "off" | "all_calendar" | "room_linked";

/** Record every meeting on my calendar: Off, or all calendar meetings. A
 *  desk set to Room meetings in Settings reads On and says so. */
function AutoRecordSwitch() {
  const [value, setValue] = useState<AutoRecord | null>(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  useEffect(() => {
    let live = true;
    apiFetch<{ meeting?: { auto_record?: string } }>("/api/settings")
      .then((settings) => {
        if (!live) return;
        const read = String(settings?.meeting?.auto_record ?? "off");
        setValue(read === "all_calendar" || read === "room_linked" ? read : "off");
      })
      .catch(() => undefined);
    return () => { live = false; };
  }, []);
  const change = useCallback(async (on: boolean) => {
    const next: AutoRecord = on ? "all_calendar" : "off";
    const before = value;
    setValue(next);
    setError("");
    setSaving(true);
    try {
      await apiFetch("/api/settings", { method: "PUT", json: { meeting: { auto_record: next } } });
    } catch (reason) {
      setValue(before);
      setError(`Not saved · ${readableError(reason)}`);
    } finally {
      setSaving(false);
    }
  }, [value]);
  if (value === null) return null;
  return (
    <div className="record-home-auto" data-testid="record-home-auto">
      <SurfaceSettingRow
        label="Record every meeting on my calendar"
        description={value === "room_linked" ? "Project meetings only" : undefined}
        control={
          <CheckGadget
            variant="state"
            label="Record every meeting on my calendar"
            checked={value !== "off"}
            disabled={saving}
            onChange={(next) => void change(next)}
          />
        }
      />
      {error ? <span className="kit-pill" data-tone="danger" role="alert">{error}</span> : null}
    </div>
  );
}

export function RecordHome({ onRecord, onImport }: { onRecord(): void; onImport(): void }) {
  const calendar = useDesk((s) => s.comingUp?.calendar ?? false);
  const [another, setAnother] = useState(false);
  return (
    <div className="record-home" data-testid="record-home">
      <div className="record-home-verbs">
        <Button variant="primary" data-testid="record-home-record" onClick={onRecord}>
          <span className="live-rec-lamp" aria-hidden="true" /> Record
        </Button>
        <Button variant="secondary" data-testid="record-home-import" onClick={onImport}>
          Import
        </Button>
      </div>
      <ComingUp data-testid="record-home-coming-up" />
      <Disclosure label="Another time…" open={another} onOpenChange={setAnother}>
        <ScheduleFormInline onDone={() => setAnother(false)} />
      </Disclosure>
      {calendar ? <AutoRecordSwitch /> : null}
    </div>
  );
}
