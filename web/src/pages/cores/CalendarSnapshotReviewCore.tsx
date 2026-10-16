// HS-146-07 — Calendar snapshot review surface: extracted events from
// a screenshot are shown as an editable list; the owner confirms the
// anchor date and the events before they become a .ics source.
import { useCallback, useMemo, useRef, useState } from "react";
import { apiFetch, readableError } from "../../lib/api";
import { CycleGadget, StringGadget } from "../../desk/surface/gadgets";
import { countLabel, StateChip } from "../../desk/surface";
import { humanizeWireValue } from "../../lib/productLanguage";
import { useWindowTitle } from "../../desk/surface/title";
import { windowName } from "../../desk/windowName";
import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
import {
  ConfirmVerb,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceSection,
} from "../../desk/surface/Surface";
import { Button } from "../../components/signal/Signal";
import type { CoreProps } from "./core-types";
import "./calendar-snapshot-review.css";

interface SnapshotEvent {
  title: string;
  weekday: string;
  start_time: string;
  end_time: string;
  location: string | null;
}

interface ReviewEvent extends SnapshotEvent {
  rowId: string;
}

type Phase =
  | {
      step: "review";
      events: ReviewEvent[];
      anchor: string;
      confidence: string;
      saving: boolean;
      saveError?: string;
    }
  | { step: "error"; verb: "READ" | "SAVE"; message: string }
  | { step: "done"; count?: number; sourceLabel?: string };

/** UX-CANON A10 (honest states, plain reasons): a refusal reads
 * `CAN'T READ · <plain reason>`, never the hub's code
 * (`no_vision_model_assigned`) or a sentence (B0-L1, Tenet 4). */
const REASONS: Record<string, string> = {
  no_vision_model_assigned: "No vision model",
  unreadable_screenshot: "Not a calendar image",
  no_import: "No screenshot",
};

export function refusalReason(message: string): string {
  const m = message.trim();
  if (REASONS[m]) return REASONS[m];
  // Any other code the hub sends: its words, never its snake_case.
  return /^[a-z0-9]+(_[a-z0-9]+)+$/.test(m) ? humanizeWireValue(m) : m;
}

const WEEKDAYS = [
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
  "sunday",
];

function parseScope(scope: string | undefined): {
  events: SnapshotEvent[];
  anchor: string;
  confidence: string;
  error: string | null;
} {
  if (!scope)
    return { events: [], anchor: "", confidence: "absent", error: "no_import" };
  try {
    const data = JSON.parse(scope);
    if (data.error) {
      return {
        events: [],
        anchor: "",
        confidence: "absent",
        error: data.error,
      };
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
      error: "unreadable_screenshot",
    };
  }
}

function isAnchorValid(anchor: string): boolean {
  if (!anchor) return false;
  return /^\d{4}-\d{2}-\d{2}$/.test(anchor.trim());
}

export function CalendarSnapshotReviewCore({ scope }: CoreProps) {
  const initial = useMemo(() => parseScope(scope), [scope]);
  // The window is named by the calendar the import went to, when the hub
  // has named it (the review payload names no calendar before the import).

  const [phase, setPhase] = useState<Phase>(() => {
    if (initial.error) {
      return { step: "error", verb: "READ", message: initial.error };
    }
    return {
      step: "review",
      // Identity belongs to the imported row, once, through edits/removals.
      events: initial.events.map((event, index) => ({
        ...event,
        rowId: `snapshot-event-${index}`,
      })),
      anchor: initial.anchor ?? "",
      confidence: initial.confidence,
      saving: false,
    };
  });
  const confirming = useRef(false);
  const calendarName = phase.step === "done" ? phase.sourceLabel : null;
  useWindowTitle(
    calendarName ? windowName({ kind: "calendar", name: calendarName }) : null,
    [calendarName],
  );

  const handleConfirm = useCallback(async () => {
    if (
      phase.step !== "review" ||
      confirming.current ||
      !isAnchorValid(phase.anchor) ||
      !phase.events.length
    )
      return;
    // The ref closes the gap before React paints the disabled Confirm.
    confirming.current = true;
    const body = JSON.stringify({
      anchor_date: phase.anchor.trim(),
      events: phase.events.map(({ rowId: _rowId, ...event }) => event),
    });
    setPhase({ ...phase, saving: true, saveError: undefined });
    try {
      const result = await apiFetch<{
        success: boolean;
        events_count?: number;
        source_label?: string;
        error?: string;
      }>("/api/calendar/snapshot/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
      });
      if (result.success) {
        setPhase({
          step: "done",
          count: result.events_count,
          sourceLabel: result.source_label,
        });
      } else {
        setPhase({
          ...phase,
          saving: false,
          saveError: result.error ?? "Events not saved",
        });
      }
    } catch (err) {
      setPhase({ ...phase, saving: false, saveError: readableError(err) });
    } finally {
      confirming.current = false;
    }
  }, [phase]);

  if (phase.step === "error") {
    return (
      <div className="surface-padded">
        <SurfaceSection label="Calendar snapshot">
          <p
            className="surface-state-quiet"
            data-testid="calendar-snapshot-refusal"
          >
            <StateChip state="failure" label={`CAN'T ${phase.verb}`} />{" "}
            <span className="surface-token" data-chip="">
              {refusalReason(phase.message)}
            </span>
          </p>
        </SurfaceSection>
        <SurfaceFooter />
      </div>
    );
  }

  if (phase.step === "done") {
    return (
      <div className="surface-padded">
        <SurfaceSection label="Import">
          <div
            className="calendar-snapshot-status"
            role="status"
            data-testid="calendar-snapshot-receipt"
          >
            <StateChip state="success" label="SAVED" />
            {phase.count != null && phase.count > 0 ? (
              <span className="surface-token" data-chip="">
                {countLabel("EVENTS", phase.count)}
              </span>
            ) : null}
            {phase.sourceLabel ? (
              <span className="surface-token" data-chip="">
                {phase.sourceLabel}
              </span>
            ) : null}
          </div>
        </SurfaceSection>
        <SurfaceFooter />
      </div>
    );
  }

  // Review step
  const anchorValid = isAnchorValid(phase.anchor);

  const updateEvent = (rowId: string, patch: Partial<SnapshotEvent>) => {
    setPhase((prev) => {
      if (prev.step !== "review" || confirming.current) return prev;
      const next = prev.events.map((event) =>
        event.rowId === rowId ? { ...event, ...patch } : event,
      );
      return { ...prev, events: next, saveError: undefined };
    });
  };

  const deleteEvent = (rowId: string) => {
    setPhase((prev) => {
      if (prev.step !== "review" || confirming.current) return prev;
      return {
        ...prev,
        events: prev.events.filter((event) => event.rowId !== rowId),
        saveError: undefined,
      };
    });
  };

  return (
    <div className="surface-padded calendar-snapshot-review">
      <fieldset className="calendar-snapshot-fields" disabled={phase.saving}>
        <SurfaceSection label="Week anchor">
          <div className="calendar-snapshot-anchor">
            <StringGadget
              label="Week of"
              caption
              value={phase.anchor}
              placeholder="YYYY-MM-DD"
              onChange={(next) =>
                setPhase((prev) =>
                  prev.step === "review" && !confirming.current
                    ? { ...prev, anchor: next, saveError: undefined }
                    : prev,
                )
              }
            />
          </div>
          {!anchorValid && phase.anchor ? (
            <small className="surface-state-quiet">YYYY-MM-DD</small>
          ) : null}
        </SurfaceSection>

        <SurfaceSection label={countLabel("EVENTS", phase.events.length)}>
          <div className="calendar-snapshot-events">
            <SurfaceLedger label="Events">
              <ul className="surface-ledger-rows">
                {phase.events.map((event, index) => (
                  <SurfaceLedgerRow
                    key={event.rowId}
                    primary={`Event ${index + 1}`}
                    open
                    expands={false}
                    trailing={
                      <ConfirmVerb
                        label="Remove"
                        confirmLabel="Remove?"
                        ariaLabel={`Remove event ${index + 1}`}
                        disabled={phase.saving}
                        onConfirm={() => deleteEvent(event.rowId)}
                      />
                    }
                  >
                    <div className="calendar-snapshot-editor">
                      <StringGadget
                        label={`Event ${index + 1} title`}
                        caption
                        value={event.title}
                        onChange={(next) =>
                          updateEvent(event.rowId, { title: next })
                        }
                      />
                      <div className="calendar-snapshot-schedule">
                        <div className="calendar-snapshot-day">
                          <span aria-hidden="true">Day</span>
                          <CycleGadget
                            label={`Event ${index + 1} weekday`}
                            value={event.weekday}
                            options={WEEKDAYS.map((d) => ({
                              value: d,
                              label: d.charAt(0).toUpperCase() + d.slice(1),
                            }))}
                            onChange={(next) =>
                              updateEvent(event.rowId, { weekday: next })
                            }
                          />
                        </div>
                        <StringGadget
                          key="start"
                          label={`Event ${index + 1} start`}
                          caption
                          value={event.start_time}
                          placeholder="HH:MM"
                          mic={false}
                          onChange={(next) =>
                            updateEvent(event.rowId, { start_time: next })
                          }
                        />
                        <StringGadget
                          key="end"
                          label={`Event ${index + 1} end`}
                          caption
                          value={event.end_time}
                          placeholder="HH:MM"
                          mic={false}
                          onChange={(next) =>
                            updateEvent(event.rowId, { end_time: next })
                          }
                        />
                      </div>
                      <StringGadget
                        label={`Event ${index + 1} location`}
                        caption
                        value={event.location ?? ""}
                        placeholder=""
                        onChange={(next) =>
                          updateEvent(event.rowId, { location: next || null })
                        }
                      />
                    </div>
                  </SurfaceLedgerRow>
                ))}
              </ul>
            </SurfaceLedger>
          </div>
        </SurfaceSection>
      </fieldset>

      <SurfaceFooter
        receipt={
          phase.saving ? (
            <StateChip state="idle" label="Saving" />
          ) : phase.saveError ? (
            <span
              className="surface-footer-receipt-line"
              data-wrap=""
              data-tone="danger"
              role="alert"
              data-testid="calendar-snapshot-save-refusal"
            >
              <StateChip state="failure" label="CAN'T SAVE" />{" "}
              <span className="surface-token" data-chip="" data-wrap="">
                {refusalReason(phase.saveError)}
              </span>
            </span>
          ) : undefined
        }
        verbs={
          <>
            <Button
              dense
              variant="primary"
              loading={phase.saving}
              disabled={!anchorValid || phase.events.length === 0}
              onClick={handleConfirm}
            >
              {phase.saveError ? "Retry" : "CONFIRM"}
            </Button>
          </>
        }
      />
    </div>
  );
}
