// HS-146-07 — Calendar snapshot review surface: extracted events from
// a screenshot are shown as an editable list; the owner confirms the
// anchor date and the events before they become a .ics source.
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { apiFetch, readableError } from "../../lib/api";
import { CycleGadget, StringGadget } from "../../desk/surface/gadgets";
import { DotWord, StatusBar, ToolGlyph, Toolbar, countWords, type StatusBarItem } from "../../desk/surface/kit";
import { useWindowInterior } from "../../desk/surface/interior";
import { importCalendarImage, snapshotEgressChip } from "../../desk/calendarImageImport";
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
import { SurfaceState } from "../../desk/surface/Surface";
import { spriteUrl } from "../../desk/sprites";
import type { CoreProps } from "./core-types";
import "./calendar-snapshot-review.css";
import { Token } from "../../desk/surface/Token";

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
  /** W1-TRUTH: nothing imported yet (no scope): a true empty state. */
  | { step: "empty" }
  | { step: "done"; count?: number; sourceLabel?: string };

/** UX-CANON A10 (honest states, plain reasons): a refusal reads
 * `Can't read` and the plain reason, never the hub's code
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

function phaseFrom(initial: ReturnType<typeof parseScope>): Phase {
  if (initial.error === "no_import") return { step: "empty" };
  if (initial.error) return { step: "error", verb: "READ", message: initial.error };
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
}

interface CalendarSourcesRead {
  sources?: Array<{ id: string; status?: string; enabled?: boolean }>;
  snapshot_egress?: { scope?: string; host?: string | null } | null;
}

/** W1-TRUTH: the calendar feeds as the hub reads them, so the window says
 *  "2 sources connected" when a feed works, never a red Can't read. */
function useCalendarSources(enabled: boolean) {
  const [read, setRead] = useState<CalendarSourcesRead | null>(null);
  const [checking, setChecking] = useState(false);
  const [failed, setFailed] = useState(false);
  const live = useRef(true);
  const check = useCallback(async () => {
    setChecking(true);
    try {
      const answer = await apiFetch<CalendarSourcesRead>("/api/calendar/sources");
      if (!live.current) return;
      setRead(answer ?? {});
      setFailed(false);
    } catch {
      if (live.current) setFailed(true);
    } finally {
      if (live.current) setChecking(false);
    }
  }, []);
  useEffect(() => {
    live.current = true;
    // The feeds are read on the faces with nothing to review (empty, a
    // refused read); a review has its own foot (Confirm).
    if (enabled) void check();
    return () => { live.current = false; };
  }, [check, enabled]);
  const rows = read?.sources ?? [];
  const connected = rows.filter((row) => row.status === "success").length;
  const failing = rows.filter((row) => row.status === "failure").length;
  const total = rows.length;
  return { read, checking, failed, check, connected, failing, total };
}

function isAnchorValid(anchor: string): boolean {
  if (!anchor) return false;
  return /^\d{4}-\d{2}-\d{2}$/.test(anchor.trim());
}

export function CalendarSnapshotReviewCore({ scope }: CoreProps) {
  const initial = useMemo(() => parseScope(scope), [scope]);
  // The window is named by the calendar the import went to, when the hub
  // has named it (the review payload names no calendar before the import).

  const [phase, setPhase] = useState<Phase>(() => phaseFrom(initial));
  // A second Import image opens this window again with the new read.
  const firstScope = useRef(scope);
  useEffect(() => {
    if (firstScope.current === scope) return;
    firstScope.current = scope;
    setPhase(phaseFrom(initial));
  }, [scope, initial]);
  useWindowInterior("editor");
  const sources = useCalendarSources(phase.step === "empty" || phase.step === "error");
  const [importRefusal, setImportRefusal] = useState("");
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

  /* W1-TRUTH (atlas 2026-10-27): every face of this window has the toolbar
     (Import image · Check sources) and says what the feeds do in its
     status bar; no section caption repeats the title. */
  const egressTitle = snapshotEgressChip(sources.read?.snapshot_egress)?.title;
  const busy = phase.step === "review" && phase.saving;
  const toolbar = (
    <Toolbar label="Calendar snapshot" data-testid="calendar-snapshot-toolbar">
      <Button dense variant={phase.step === "review" ? "secondary" : "primary"} title={egressTitle}
        disabled={busy} data-testid="calendar-snapshot-import" onClick={() => { setImportRefusal(""); importCalendarImage(setImportRefusal); }}>
        <ToolGlyph kind="import" />Import image
      </Button>
      <Button dense variant="secondary" loading={sources.checking} disabled={busy || sources.checking}
        data-testid="calendar-snapshot-check" onClick={() => void sources.check()}>
        <ToolGlyph kind="retry" />Check sources
      </Button>
    </Toolbar>
  );
  const sourceItems: Array<StatusBarItem | null> = [
    sources.connected ? { key: "connected", lamp: "ok", testId: "calendar-snapshot-sources",
      text: `${countWords(sources.connected, "source")} connected` } : null,
    sources.failing ? { key: "failing", lamp: "warn", text: `${countWords(sources.failing, "source")} not read` } : null,
    sources.failed ? { key: "unread", lamp: "warn", text: "Sources not read" } : null,
    importRefusal ? { key: "import", lamp: "fail", testId: "calendar-snapshot-import-refusal",
      text: <span role="alert"><DotWord tone="fail">Can't read</DotWord>{" "}<span className="calendar-snapshot-reason">{refusalReason(importRefusal)}</span></span> } : null,
  ];
  const shell = (body: ReactNode) => (
    <div className="calendar-snapshot-window">
      {toolbar}
      <div className="calendar-snapshot-body">{body}</div>
      <StatusBar data-testid="calendar-snapshot-status" items={sourceItems} />
    </div>
  );

  if (phase.step === "empty") {
    return shell(
      <div className="calendar-snapshot-empty" data-testid="calendar-snapshot-empty">
        {/* Atlas pass 3 #21: the empty face is the calendar object, one line,
            one verb, as the other empty faces are (SurfaceState's object). */}
        <SurfaceState empty emptyLabel="No screenshot yet" emptyImage={spriteUrl("meeting", "calendar-snapshot")}
          emptyKind="meeting" onAction={() => { setImportRefusal(""); importCalendarImage(setImportRefusal); }}
          actionLabel="Import image" />
      </div>,
    );
  }

  if (phase.step === "error") {
    return shell(
      <p
        className="surface-state-quiet"
        data-testid="calendar-snapshot-refusal"
      >
        {/* 2026-10-25 audit: a dot and a word in sentence case, the
            reason quiet beside it; no empty foot under it. */}
        <DotWord tone="fail">{phase.verb === "READ" ? "Can't read" : "Can't save"}</DotWord>{" "}
        <span className="calendar-snapshot-reason">
          {refusalReason(phase.message)}
        </span>
      </p>,
    );
  }

  if (phase.step === "done") {
    return shell(
      <div
        className="calendar-snapshot-status"
        role="status"
        data-testid="calendar-snapshot-receipt"
      >
        <DotWord tone="ok">Saved</DotWord>
        {phase.count != null && phase.count > 0 ? (
          <span className="calendar-snapshot-reason">
            {`${phase.count} ${phase.count === 1 ? "event" : "events"}`}
          </span>
        ) : null}
        {phase.sourceLabel ? (
          <span className="calendar-snapshot-reason">
            {phase.sourceLabel}
          </span>
        ) : null}
      </div>,
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
    <div className="calendar-snapshot-window calendar-snapshot-review">
      {toolbar}
      <div className="calendar-snapshot-body">
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

        <SurfaceSection label="Events" count={phase.events.length || undefined}>
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
      </div>

      <SurfaceFooter
        receipt={
          phase.saving ? (
            <DotWord tone="idle">Saving</DotWord>
          ) : phase.saveError ? (
            <Token
              className="surface-footer-receipt-line"
              data-wrap=""
              data-tone="danger"
              role="alert"
              data-testid="calendar-snapshot-save-refusal"
            >
              <DotWord tone="fail">Can't save</DotWord>{" "}
              <span className="calendar-snapshot-reason">
                {refusalReason(phase.saveError)}
              </span>
            </Token>
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
              {phase.saveError ? "Retry" : "Confirm"}
            </Button>
          </>
        }
      />
    </div>
  );
}
