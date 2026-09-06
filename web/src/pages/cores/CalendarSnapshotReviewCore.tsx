// HS-146-07 — Calendar snapshot review surface: extracted events from
// a screenshot are shown as an editable list; the owner confirms the
// anchor date and the events before they become a .ics source.
import { useCallback, useMemo, useState } from "react";
import { apiFetch, readableError } from "../../lib/api";
import {
  CycleGadget,
  GadgetTable,
  StringGadget,
} from "../../desk/surface/gadgets";
import { countLabel } from "../../desk/surface";
import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
import { SurfaceSection } from "../../desk/surface/Surface";
import { Button } from "../../components/signal/Signal";
import type { CoreProps } from "./core-types";

interface SnapshotEvent {
  title: string;
  weekday: string;
  start_time: string;
  end_time: string;
  location: string | null;
}

type Phase =
  | { step: "review"; events: SnapshotEvent[]; anchor: string; confidence: string }
  | { step: "error"; message: string }
  | { step: "confirming" }
  | { step: "done"; count: number; sourceLabel: string };

const WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];

function parseScope(scope: string | undefined): {
  events: SnapshotEvent[];
  anchor: string;
  confidence: string;
  error: string | null;
} {
  if (!scope) return { events: [], anchor: "", confidence: "absent", error: "This review window opened without an import. Close it and re-import the screenshot." };
  try {
    const data = JSON.parse(scope);
    if (data.error) {
      return { events: [], anchor: "", confidence: "absent", error: data.error };
    }
    return {
      events: (data.events || []).map((e: Record<string, unknown>) => ({
        title: String(e.title ?? ""),
        weekday: String(e.weekday ?? ""),
        start_time: String(e.start_time ?? ""),
        end_time: String(e.end_time ?? ""),
        location: e.location != null ? String(e.location) : null,
      })),
      anchor: data.anchor_date ?? "",
      confidence: data.anchor_confidence ?? "absent",
      error: null,
    };
  } catch {
    return {
      events: [],
      anchor: "",
      confidence: "absent",
      error: "Could not read events from this screenshot. Nothing was written. Retry with a clearer capture.",
    };
  }
}

function isAnchorValid(anchor: string): boolean {
  if (!anchor) return false;
  return /^\d{4}-\d{2}-\d{2}$/.test(anchor.trim());
}

export function CalendarSnapshotReviewCore({ scope }: CoreProps) {
  const initial = useMemo(() => parseScope(scope), [scope]);

  const [phase, setPhase] = useState<Phase>(() => {
    if (initial.error) {
      return { step: "error", message: initial.error };
    }
    return {
      step: "review",
      events: initial.events,
      anchor: initial.anchor ?? "",
      confidence: initial.confidence,
    };
  });

  const handleConfirm = useCallback(async () => {
    if (phase.step !== "review") return;
    setPhase({ step: "confirming" });
    try {
      const result = await apiFetch<{
        success: boolean;
        events_count?: number;
        source_label?: string;
        error?: string;
      }>("/api/calendar/snapshot/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          anchor_date: phase.anchor.trim(),
          events: phase.events,
        }),
      });
      if (result.success) {
        setPhase({
          step: "done",
          count: result.events_count ?? phase.events.length,
          sourceLabel: result.source_label ?? "O365 SNAPSHOT",
        });
      } else {
        setPhase({ step: "error", message: result.error ?? "Could not save the events. Your review is still open. Try again." });
      }
    } catch (err) {
      setPhase({ step: "error", message: readableError(err) });
    }
  }, [phase]);

  if (phase.step === "error") {
    return (
      <div className="surface-padded">
        <SurfaceSection label="Calendar snapshot">
          <p className="surface-state-quiet">
            {phase.message === "unreadable_screenshot"
              ? "Could not read the screenshot as a calendar. Try a clearer image."
              : phase.message}
          </p>
        </SurfaceSection>
        <SurfaceFooter />
      </div>
    );
  }

  if (phase.step === "confirming") {
    return (
      <div className="surface-padded">
        <SurfaceSection label="Calendar snapshot">
          <p className="surface-state-quiet">Writing events...</p>
        </SurfaceSection>
      </div>
    );
  }

  if (phase.step === "done") {
    return (
      <div className="surface-padded">
        <SurfaceSection label="Calendar snapshot">
          <p className="surface-state-quiet">
            {phase.count} event{phase.count !== 1 ? "s" : ""} imported as {phase.sourceLabel}
          </p>
        </SurfaceSection>
        <SurfaceFooter />
      </div>
    );
  }

  // Review step
  const anchorValid = isAnchorValid(phase.anchor);

  const updateEvent = (index: number, patch: Partial<SnapshotEvent>) => {
    setPhase((prev) => {
      if (prev.step !== "review") return prev;
      const next = prev.events.map((e, i) =>
        i === index ? { ...e, ...patch } : e,
      );
      return { ...prev, events: next };
    });
  };

  const deleteEvent = (index: number) => {
    setPhase((prev) => {
      if (prev.step !== "review") return prev;
      return { ...prev, events: prev.events.filter((_, i) => i !== index) };
    });
  };

  return (
    <div className="surface-padded">
      <SurfaceSection label="Week anchor">
        <div style={{ maxWidth: 260 }}>
          <StringGadget
            label="Week of"
            value={phase.anchor}
            placeholder="YYYY-MM-DD"
            onChange={(next) =>
              setPhase((prev) =>
                prev.step === "review" ? { ...prev, anchor: next } : prev,
              )
            }
          />
        </div>
        {!anchorValid && phase.anchor ? (
          <small className="surface-state-quiet">Enter a date as YYYY-MM-DD</small>
        ) : null}
      </SurfaceSection>

      <SurfaceSection label={countLabel("EVENTS", phase.events.length)}>
        <GadgetTable
          head={["TITLE", "DAY", "START", "END", "LOCATION"]}
          deleteLabel="REMOVE?"
          onDelete={deleteEvent}
          rowKey={(i) => `${i}-${phase.events[i]?.title}`}
          rows={phase.events.map((event, index) => [
            <StringGadget
              key="title"
              label={`Event ${index + 1} title`}
              value={event.title}
              onChange={(next) => updateEvent(index, { title: next })}
            />,
            <CycleGadget
              key="weekday"
              label={`Event ${index + 1} weekday`}
              value={event.weekday}
              options={WEEKDAYS.map((d) => ({
                value: d,
                label: d.charAt(0).toUpperCase() + d.slice(1, 3),
              }))}
              onChange={(next) => updateEvent(index, { weekday: next })}
            />,
            <StringGadget
              key="start"
              label={`Event ${index + 1} start`}
              value={event.start_time}
              placeholder="HH:MM"
              mic={false}
              onChange={(next) => updateEvent(index, { start_time: next })}
            />,
            <StringGadget
              key="end"
              label={`Event ${index + 1} end`}
              value={event.end_time}
              placeholder="HH:MM"
              mic={false}
              onChange={(next) => updateEvent(index, { end_time: next })}
            />,
            <StringGadget
              key="location"
              label={`Event ${index + 1} location`}
              value={event.location ?? ""}
              placeholder=""
              onChange={(next) =>
                updateEvent(index, { location: next || null })
              }
            />,
          ])}
        />
      </SurfaceSection>

      <SurfaceFooter
        verbs={
          <>
            <Button
              dense
              disabled={!anchorValid || phase.events.length === 0}
              onClick={handleConfirm}
            >
              CONFIRM
            </Button>
          </>
        }
      />
    </div>
  );
}
