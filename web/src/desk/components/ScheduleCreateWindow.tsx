// HS-136-03 -- in-world schedule-creation window (no modal).
//
// Reached from the capture hero or the Meetings lane. A DeskWindow
// with title, mode (one-shot/recurring), date-time or cron, duration,
// and the create verb. The title field carries a speak-to-fill mic
// (house law: voice mic on every text input).
//
// Honest labels (Article VI): names WHAT happens in fewest words.
// No accent gradient (hero/Record-Orb only), ember on the create verb.

import { useCallback, useState } from "react";
import { useDesk } from "../store";
import { DeskWindowFrame } from "./DeskWindow";
import {
  GadgetGroup,
  GadgetRow,
  StringGadget,
  CycleGadget,
} from "../surface/gadgets";
import { Button } from "../../components/signal/Signal";
import { MicButton } from "./MicButton";

/** Build a cron expression from a JS Date for one-shot mode. */
function dateToCron(d: Date): string {
  return `${d.getMinutes()} ${d.getHours()} ${d.getDate()} ${d.getMonth() + 1} *`;
}

/** Format a Date as a local datetime-local input value. */
function toDatetimeLocal(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** The local IANA timezone name (best effort). */
function localTz(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch {
    return "UTC";
  }
}

const DURATION_OPTIONS = [
  { value: "15", label: "15 min" },
  { value: "30", label: "30 min" },
  { value: "60", label: "60 min" },
  { value: "90", label: "90 min" },
  { value: "120", label: "2 hours" },
];

const MODE_OPTIONS = [
  { value: "one-shot", label: "Once" },
  { value: "recurring", label: "Recurring" },
];

export function ScheduleCreateWindow() {
  const chooser = useDesk((s) => s.scheduleCreateWindow);
  const close = useDesk((s) => s.closeScheduleCreate);
  if (!chooser) return null;
  return <ScheduleCreateForm origin={chooser.origin} onClose={close} />;
}

function ScheduleCreateForm({
  origin,
  onClose,
}: {
  origin: { x: number; y: number } | null;
  onClose: () => void;
}) {
  const [title, setTitle] = useState("");
  const [mode, setMode] = useState("one-shot");
  const [dateTime, setDateTime] = useState(() => {
    const d = new Date();
    d.setMinutes(d.getMinutes() + 30);
    d.setSeconds(0, 0);
    return toDatetimeLocal(d);
  });
  const [cronExpr, setCronExpr] = useState("0 9 * * 1-5");
  const [duration, setDuration] = useState("60");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = useCallback(async () => {
    setError(null);
    setSubmitting(true);

    const isOneShot = mode === "one-shot";
    let cron: string;
    if (isOneShot) {
      const d = new Date(dateTime);
      if (Number.isNaN(d.getTime()) || d.getTime() <= Date.now()) {
        setError("Pick a time in the future");
        setSubmitting(false);
        return;
      }
      cron = dateToCron(d);
    } else {
      cron = cronExpr.trim();
      if (!cron) {
        setError("Enter a cron expression");
        setSubmitting(false);
        return;
      }
    }

    const ok = await useDesk.getState().createSchedule({
      title: title.trim() || "Scheduled recording",
      cron_expr: cron,
      tz: localTz(),
      one_shot: isOneShot,
      duration_minutes: Number(duration) || 60,
      enabled: true,
    });

    setSubmitting(false);
    if (ok) {
      onClose();
    } else {
      setError("Could not save. Your entries are kept. Check the time and try again.");
    }
  }, [title, mode, dateTime, cronExpr, duration, onClose]);

  return (
    <DeskWindowFrame
      id="schedule:__create__"
      glyph="⏱"
      label="Schedule recording"
      title="Schedule recording"
      minW={380}
      minH={280}
      fitContent
      open
      origin={origin}
      onClose={onClose}
      className="desk-pullout"
    >
      <div className="desk-surface-body" style={{ padding: "var(--space-3)" }}>
        <GadgetGroup label="Recording starts on its own at the set time">
          <GadgetRow label="Title">
            <StringGadget
              label="Title"
              value={title}
              onChange={setTitle}
              placeholder="Scheduled recording"
              autoFocus
            />
            <MicButton draftScope="schedule-title" onText={setTitle} />
          </GadgetRow>
          <GadgetRow label="Mode">
            <CycleGadget
              label="Mode"
              value={mode}
              options={MODE_OPTIONS}
              onChange={setMode}
            />
          </GadgetRow>
          {mode === "one-shot" ? (
            <GadgetRow label="When">
              <span className="gadget-string">
                <input
                  type="datetime-local"
                  aria-label="When"
                  value={dateTime}
                  onChange={(e) => setDateTime(e.target.value)}
                  style={{ width: "100%" }}
                />
              </span>
            </GadgetRow>
          ) : (
            <GadgetRow label="Cron">
              <StringGadget
                label="Cron expression"
                value={cronExpr}
                onChange={setCronExpr}
                placeholder="0 9 * * 1-5"
                mic={false}
              />
            </GadgetRow>
          )}
          <GadgetRow label="Duration">
            <CycleGadget
              label="Duration"
              value={duration}
              options={DURATION_OPTIONS}
              onChange={setDuration}
            />
          </GadgetRow>
        </GadgetGroup>

        {error ? (
          <p className="gadget-inline-error" role="alert" style={{
            color: "var(--kind-error)",
            fontSize: "var(--font-size-xs)",
            margin: "var(--space-2) 0 0",
          }}>
            {error}
          </p>
        ) : null}

        <div style={{ marginTop: "var(--space-3)", display: "flex", gap: "var(--space-2)", justifyContent: "flex-end" }}>
          <Button variant="ghost" onClick={onClose} dense>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={() => void handleSubmit()}
            loading={submitting}
            dense
            data-testid="schedule-create-submit"
          >
            Schedule
          </Button>
        </div>
      </div>
    </DeskWindowFrame>
  );
}
