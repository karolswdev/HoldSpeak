// HS-171-02 + HS-171-06 — the Rhythm face: sweep, brief, notify, loops.
// Composed from the surface kit on the window material (UX-CANON.md).
// Board truth: RhythmCadence.png, RhythmCadenceRunning.png,
// RhythmCadenceQuiet.png, RhythmPhone.png, SettingsHubHeartbeat.png.
//
// The existing cadence loop rows + their verbs (reply, snooze, mark done,
// kill) are preserved BELOW the new heartbeat rows under a `NOW N` caption,
// absent at zero.
import { useCallback, useEffect, useLayoutEffect, useState } from "react";
import type {
  CoreProps,
  CadenceLoopsResponse,
  CadenceHistoryResponse,
} from "./core-types";
import { Button } from "../../components/signal/Signal";
import {
  CheckGadget,
  CycleGadget,
  LampGadget,
  PadGadget,
} from "../../desk/surface/gadgets";
import {
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceSection,
  StateChip,
  countLabel,
  countToken,
} from "../../desk/surface";
import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
import { egressForEvent } from "../../desk/surface/egress";
import {
  ConfirmVerb,
  SurfaceRows,
  SurfaceRow,
  SurfaceState,
} from "../../desk/surface/Surface";
import { apiFetch, readableError } from "../../lib/api";
import { useResource, asRows, rowId } from "../pageSupport";
import { useAction } from "./core-hooks";
import { renderHeroSlot } from "./core-layout";
import { deSnake, humanTime, wireClock } from "../../desk/surface/format";
import "./rhythm.css";

/* ── Wire shapes ────────────────────────────────────────────────── */

type HeartbeatSettings = {
  sweep_every_minutes: number;
  quiet_hours: { start: number; end: number };
  notify: string;
  muted_projects: string[];
  last_sweep_at: string | null;
  next_sweep_at: string | null;
  /** HS-174-08: host the sweep runs on ("local" or a remote host). */
  runs_on?: string | null;
  /** HS-174-08: known remote hosts from pipeline events. */
  remote_hosts?: string[];
  /** HS-174-08: last remote run timestamp (ISO). */
  last_remote_run_at?: string | null;
  /** Betterment daily D8: a quiet notice when an automation has a new result. */
  notify_finished?: boolean;
};

type SweepReceipt = {
  rooms: number;
  watches: number;
  duration_ms: number;
  held: boolean;
  errors: number;
};

type BriefLatest = {
  id?: string;
  generated_at?: string;
  items?: unknown[];
  sections?: Record<string, Array<{ text: string; source_ref?: string }>>;
} | null;

type DoorProjection = {
  calendar_configured?: boolean;
};

type ProjectItem = {
  id: string;
  name?: string;
  title?: string;
};

/* ── Option constants ───────────────────────────────────────────── */

const SWEEP_OPTIONS = [
  { value: "5", label: "EVERY 5 MIN" },
  { value: "15", label: "EVERY 15 MIN" },
  { value: "30", label: "EVERY 30 MIN" },
  { value: "60", label: "EVERY 1 HR" },
];

const NOTIFY_OPTIONS = [
  { value: "off", label: "OFF" },
  { value: "edge", label: "ON THE EDGE" },
  { value: "every_sweep", label: "EVERY SWEEP" },
];

/* ── Helpers ────────────────────────────────────────────────────── */

/** Format a 24h hour as HH:00. */
function fmtHour(h: number): string {
  return `${String(h).padStart(2, "0")}:00`;
}

/** Extract HH:MM from an ISO timestamp. */
function fmtTime(iso: string | null | undefined): string | null {
  // The hub stamps the sweep clock in UTC; the face shows local time.
  return wireClock(iso) || null;
}

/** Format a date as MON DD (e.g. SEP 04). */
function fmtDate(iso: string | null | undefined): string | null {
  if (!iso) return null;
  try {
    const d = new Date(iso);
    if (isNaN(d.getTime())) return null;
    const months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
    return `${months[d.getMonth()]} ${String(d.getDate()).padStart(2, "0")}`;
  } catch {
    return null;
  }
}

/** HS-175 counsel C9(a): the Rhythm summary line, honest at one and zero.
 * `1 MEETING · 1 ARMED · 1 WATCH ITEM · 1 COMMITMENT DUE`; null when no
 * part counts (A.8). */
export function briefSummaryLine(
  items: Array<{ source_ref?: string | null; text?: string | null }> | undefined,
): string | null {
  if (!items || items.length === 0) return null;
  let meetings = 0, armed = 0, watch = 0, due = 0;
  const lead = (text: string) => { const m = text.match(/^(\d+)\s+/); return m ? parseInt(m[1], 10) : 0; };
  for (const item of items) {
    const ref = item.source_ref ?? "";
    const text = item.text ?? "";
    if (ref === "calendar:week") meetings += lead(text);
    else if (ref === "calendar:armed") armed += lead(text);
    else if (ref === "meeting_watch:commitments_due") due += lead(text);
    else if (ref === "meeting_watch:decisions") watch += lead(text);
  }
  const parts = [
    countToken(meetings, "MEETING"),
    countToken(armed, "ARMED", "ARMED"),
    countToken(watch, "WATCH ITEM"),
    countToken(due, "COMMITMENT DUE", "COMMITMENTS DUE"),
  ].filter((p): p is string => Boolean(p));
  return parts.length > 0 ? parts.join(" · ") : null;
}

/** Format epoch seconds as HH:MM. */
function fmtEpoch(epoch: number | null | undefined): string | null {
  if (epoch == null) return null;
  const d = new Date(epoch * 1000);
  return d.toTimeString().slice(0, 5);
}

/* ── The face ───────────────────────────────────────────────────── */

/** Rhythm is drawn after this long even when a read is still out (the
 *  Room's cap, roomReads.ts ROOM_READS_CAP_MS). */
const RHYTHM_READS_CAP_MS = 8000;

/** Betterment setup ST1: the Rhythm window is parked; Settings ▸ Rhythm
 *  embeds this face under its Advanced fold. `embedded` leaves out what the
 *  section already says (the headline, Notify) and the window's hero and
 *  foot (Settings owns its foot). */
export function CadenceCore({ hero, embedded = false }: CoreProps & { embedded?: boolean }) {
  // ── Heartbeat resources ──
  const heartbeat = useResource<HeartbeatSettings>("/api/settings/heartbeat", {
    sweep_every_minutes: 15,
    quiet_hours: { start: 22, end: 8 },
    notify: "edge",
    muted_projects: [],
    last_sweep_at: null,
    next_sweep_at: null,
  });
  const briefRes = useResource<BriefLatest>("/api/brief/latest", null);
  const doorRes = useResource<DoorProjection>("/api/door", {});
  const projectsRes = useResource<{ projects: ProjectItem[] }>("/api/projects", { projects: [] });

  // ── Existing cadence loop + nudge resources (kept for the NOW N section) ──
  const cadenceStatus = useResource<Record<string, unknown>>("/api/cadence/status", {});
  const briefJobRaw = cadenceStatus.data?.brief_job as { enabled?: unknown; hour?: unknown } | undefined;
  const briefJob = briefJobRaw && typeof briefJobRaw.hour === "number"
    ? { enabled: briefJobRaw.enabled === true, hour: briefJobRaw.hour }
    : null;
  const loopsResource = useResource<CadenceLoopsResponse>("/api/cadence/loops", {});
  const history = useResource<CadenceHistoryResponse>("/api/cadence/history?limit=20", {});
  const loops = asRows(loopsResource.data, ["loops"]);
  // PHILO-17 (the desk sweep, sweepreds r2): Rhythm is drawn once its first
  // reads have ended (each read or failed), or at the cap: under load a late
  // read moved the notify row, the mute toggles and the project rows 18 px
  // after the window settled (UX-CANON D; the Room's pattern). Once drawn it
  // stays drawn: a later reload never hides it again.
  const firstReads = [heartbeat, briefRes, doorRes, projectsRes, cadenceStatus, loopsResource, history];
  const readsEnded = firstReads.every((r) => !r.loading);
  const [capped, setCapped] = useState(false);
  useEffect(() => {
    const timer = window.setTimeout(() => setCapped(true), RHYTHM_READS_CAP_MS);
    return () => window.clearTimeout(timer);
  }, []);
  const [drawn, setDrawn] = useState(false);
  useLayoutEffect(() => { if (!drawn && (readsEnded || capped)) setDrawn(true); }, [drawn, readsEnded, capped]);
  const shown = drawn || readsEnded || capped;
  const [replies, setReplies] = useState<Record<string, string>>({});
  const [replyReceipt, setReplyReceipt] = useState("");
  const action = useAction();

  // ── Heartbeat state ──
  const [sweeping, setSweeping] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [receipt, setReceipt] = useState<SweepReceipt | null>(null);
  const [writtenAt, setWrittenAt] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [sweepError, setSweepError] = useState("");
  const [briefError, setBriefError] = useState("");

  // Defensive: the wire may return a partial shape (especially in tests
  // where the fetch stub returns a catch-all).
  const raw = heartbeat.data;
  const settings: HeartbeatSettings = {
    sweep_every_minutes: raw?.sweep_every_minutes ?? 15,
    quiet_hours: {
      start: raw?.quiet_hours?.start ?? 22,
      end: raw?.quiet_hours?.end ?? 8,
    },
    notify: raw?.notify ?? "edge",
    muted_projects: raw?.muted_projects ?? [],
    last_sweep_at: raw?.last_sweep_at ?? null,
    next_sweep_at: raw?.next_sweep_at ?? null,
    runs_on: raw?.runs_on ?? null,
    remote_hosts: Array.isArray(raw?.remote_hosts) ? raw.remote_hosts : [],
    last_remote_run_at: raw?.last_remote_run_at ?? null,
    notify_finished: raw?.notify_finished ?? true,
  };
  const projects = projectsRes.data?.projects ?? [];

  // ── Heartbeat mutations ──
  const putSetting = useCallback(async (patch: Partial<HeartbeatSettings>) => {
    setSaving(true);
    setSaveError("");
    try {
      await apiFetch("/api/settings/heartbeat", { method: "PUT", json: patch });
      setWrittenAt(Date.now() / 1000);
      await heartbeat.reload();
    } catch (error) {
      setSaveError(`Settings save not confirmed · Shown settings kept · Reload · ${readableError(error)}`);
    } finally {
      setSaving(false);
    }
  }, [heartbeat]);

  const runNow = useCallback(async () => {
    setSweeping(true);
    setSweepError("");
    setReceipt(null);
    try {
      const result = await apiFetch<SweepReceipt>("/api/settings/heartbeat/run-now", {
        method: "POST",
        json: {},
      });
      setReceipt(result);
      await heartbeat.reload();
    } catch (error) {
      setSweepError(`Sweep failed · ${readableError(error)}`);
    } finally {
      setSweeping(false);
    }
  }, [heartbeat]);

  const generateBrief = useCallback(async () => {
    setGenerating(true);
    setBriefError("");
    try {
      await apiFetch("/api/brief/generate", { method: "POST", json: {} });
      await briefRes.reload();
    } catch (error) {
      setBriefError(`Brief not generated · ${readableError(error)}`);
    } finally {
      setGenerating(false);
    }
  }, [briefRes]);

  // ── Existing loop verbs (preserved from the old CadenceCore) ──
  const act = async (id: string, verb: string) => {
    await action.run(async () => {
      await apiFetch(`/api/cadence/loops/${encodeURIComponent(id)}/${verb}`, {
        method: "POST",
        json: verb === "snooze" ? { hours: 24 } : {},
      });
      await loopsResource.reload();
      await history.reload();
    });
  };
  const sendReply = async (id: string) => {
    const text = (replies[id] ?? "").trim();
    if (!text) return;
    setReplyReceipt("");
    await action.run(async () => {
      const result = await apiFetch<{ pane?: string }>(
        `/api/cadence/loops/${encodeURIComponent(id)}/reply`,
        { method: "POST", json: { text } },
      );
      setReplyReceipt(`Sent to ${result.pane || "the agent"}`);
      setReplies((prev) => ({ ...prev, [id]: "" }));
      await loopsResource.reload();
      await history.reload();
    });
  };

  // ── Derived state ──
  const inQuiet = (() => {
    const now = new Date();
    const hour = now.getHours();
    const start = settings.quiet_hours.start;
    const end = settings.quiet_hours.end;
    if (start === end) return false;
    if (start < end) return hour >= start && hour < end;
    return hour >= start || hour < end;
  })();

  const sweepLabel = settings.sweep_every_minutes >= 60
    ? `Every ${Math.round(settings.sweep_every_minutes / 60)} hr`
    : `Every ${settings.sweep_every_minutes} min`;

  // Brief info
  const brief = briefRes.data;
  const briefDate = brief?.generated_at ? fmtDate(brief.generated_at) : null;
  const calendarConfigured = doorRes.data?.calendar_configured ?? false;

  // HS-175: brief summary line from this_week section items.
  // Counsel C9(a) / H10-3: every part through countToken (singular at one,
  // absent at zero) and ARMED named as ARMED, not folded into WATCH ITEMS.
  const briefSummary = briefSummaryLine(brief?.sections?.this_week);

  return (
    <>
      {embedded ? null : renderHeroSlot(hero, null, null)}
      <div className="cadence-body" data-settling={shown ? undefined : "true"} aria-busy={shown ? undefined : true}>
      {shown ? null : <div className="cadence-settling-line"><SurfaceState loading /></div>}
      {saveError ? <SurfaceState error={saveError} onRetry={async () => { if (await heartbeat.reload()) setSaveError(""); }} /> : null}
      {heartbeat.error ? <SurfaceState error={`Rhythm settings not loaded · ${heartbeat.error}`} onRetry={() => void heartbeat.reload()} /> : null}

      {/* Display headline: accent when the sweep runs, muted when not */}
      {embedded ? null : <span
        className="surface-display"
        data-testid="rhythm-headline"
        data-tone={settings.sweep_every_minutes > 0 ? "accent" : undefined}
        data-muted={settings.sweep_every_minutes <= 0 || undefined}
      >
        {settings.sweep_every_minutes > 0 ? sweepLabel : "Not running"}
      </span>}

      {/* ── SWEEP row ──────────────────────────────────────────── */}
      <div className="rhythm-section">
      <SurfaceLedger count="" cols="hub">
        <SurfaceLedgerRow
          primary="Sweep"
          expands={false}
          data-testid="rhythm-sweep-row"
          trailing={
            <Button
              variant="ghost"
              dense
              disabled={sweeping || saving}
              onClick={() => void runNow()}
              data-testid="rhythm-run-now"
            >
              Run now
            </Button>
          }
          cells={
            <CycleGadget
              label="Sweep interval"
              value={String(settings.sweep_every_minutes)}
              options={SWEEP_OPTIONS}
              disabled={saving || sweeping}
              onChange={(v) => void putSetting({ sweep_every_minutes: parseInt(v, 10) })}
            />
          }
        />
      </SurfaceLedger>
      <div className="rhythm-facts" data-testid="rhythm-sweep-facts">
        {sweeping ? (
          <StateChip state="active" label="RUNNING" />
        ) : inQuiet ? (
          <StateChip state="warning" label={`HELD · QUIET UNTIL ${fmtHour(settings.quiet_hours.end)}`} />
        ) : null}
        {!sweeping && (
          <>
            <span className="surface-token" data-chip data-muted>
              QUIET {fmtHour(settings.quiet_hours.start)}&ndash;{fmtHour(settings.quiet_hours.end)}
            </span>
            {settings.next_sweep_at ? (
              <>
                <span className="surface-token" data-chip data-muted>{"·"}</span>
                <span className="surface-token" data-chip data-muted>
                  NEXT {fmtTime(settings.next_sweep_at)}
                </span>
              </>
            ) : null}
            {settings.last_sweep_at ? (
              <>
                <span className="surface-token" data-chip data-muted>{"·"}</span>
                <span className="surface-token" data-chip data-muted>
                  LAST {fmtTime(settings.last_sweep_at)}
                </span>
              </>
            ) : null}
            {receipt ? (
              <>
                <span className="surface-token" data-chip data-muted>{"·"}</span>
                <span className="surface-token" data-chip data-muted>
                  {receipt.rooms} {receipt.rooms === 1 ? "ROOM" : "ROOMS"}
                </span>
                <span className="surface-token" data-chip data-muted>{"·"}</span>
                <span className="surface-token" data-chip data-muted>
                  {Math.round(receipt.duration_ms)} MS
                </span>
              </>
            ) : null}
          </>
        )}
      </div>
      {sweepError ? <SurfaceState error={sweepError} /> : null}
      </div>{/* /rhythm-section sweep */}

      {/* ── RUNS ON row (HS-174-08) ────────────────────────────── */}
      <div className="rhythm-section">
      <SurfaceLedger count="" cols="hub">
        <SurfaceLedgerRow
          primary="Where it runs"
          expands={false}
          data-testid="rhythm-runs-on-row"
          cells={
            <CycleGadget
              label="Runner host"
              value={settings.runs_on || "local"}
              disabled={saving || sweeping}
              options={[
                { value: "local", label: "THIS DEVICE" },
                ...(settings.remote_hosts ?? []).map((h) => ({ value: h, label: h })),
              ]}
              onChange={(v) => void putSetting({ runs_on: v })}
              data-testid="rhythm-runs-on-gadget"
            />
          }
        />
      </SurfaceLedger>
      <div className="rhythm-facts" data-testid="rhythm-runs-on-facts">
        {settings.runs_on && settings.runs_on !== "local" ? (
          <>
            {settings.last_remote_run_at ? (
              <span className="surface-token" data-chip data-muted>
                LAST RUN {humanTime(settings.last_remote_run_at)}
              </span>
            ) : (
              <span className="surface-token" data-chip data-muted data-testid="rhythm-runs-on-no-runs">
                NO RUNS YET
              </span>
            )}
            {receipt ? (
              <>
                <span className="surface-token" data-chip data-muted>
                  SWEEP · {receipt.rooms} {receipt.rooms === 1 ? "ROOM" : "ROOMS"}
                </span>
                {settings.last_remote_run_at ? (
                  <span className="surface-token" data-chip data-muted>
                    {fmtTime(settings.last_remote_run_at)}
                  </span>
                ) : null}
              </>
            ) : null}
            <span className="rhythm-runs-on-caption" data-testid="rhythm-runs-on-caption">
              WHILE THIS MAC IS AWAKE
            </span>
          </>
        ) : null}
      </div>
      </div>{/* /rhythm-section runs-on */}

      {/* ── WEEKLY / MONDAY BRIEF row (HS-175) ─────────────────── */}
      <div className="rhythm-section">
      <SurfaceLedger count="" cols="hub">
        <SurfaceLedgerRow
          primary={calendarConfigured ? "Weekly brief" : "Daily brief"}
          expands={false}
          data-testid="rhythm-brief-row"
          trailing={
            <Button
              variant="ghost"
              dense
              disabled={generating}
              onClick={() => void generateBrief()}
              data-testid="rhythm-generate-now"
            >
              Generate
            </Button>
          }
          cells={
            <>
              {/* HS-175 counsel C9(a) / H4-0: the brief regenerates once a
                  DAY (runtime/cadence.py _maybe_regenerate_brief); no weekly
                  cadence exists, so the token says DAILY on both rows.  The
                  row's name stays "Weekly brief" -- it is the week-window
                  brief.  PHILO-15 05: the hour is the Brief job's own
                  (cadence.brief_hour, 06:00 by default), OFF when the job is
                  off; an older hub without it keeps the quiet-hours end. */}
              <span className="surface-token" data-chip data-muted data-testid="rhythm-brief-cadence">
                {briefJob
                  ? briefJob.enabled ? `DAILY ${fmtHour(briefJob.hour)}` : "OFF"
                  : `DAILY ${fmtHour(settings.quiet_hours.end)}`}
              </span>
              <span data-testid="rhythm-brief-last">
                {briefDate ? (
                  <StateChip state="success" label={`LAST ${briefDate}`} />
                ) : (
                  <StateChip state="idle" label="NEVER" />
                )}
              </span>
            </>
          }
        />
      </SurfaceLedger>

      {/* HS-175: brief summary line -- absent when all zero (A.8) */}
      <div className="rhythm-facts" data-testid="rhythm-brief-facts">
        {generating ? (
          <StateChip state="active" label="GENERATING" />
        ) : null}
        {!generating && briefSummary ? (
          <span className="surface-token" data-chip data-muted data-testid="rhythm-brief-summary">
            {briefSummary}
          </span>
        ) : null}
      </div>
      {briefError ? <SurfaceState error={briefError} /> : null}
      {briefRes.error ? <SurfaceState error={`Brief not loaded · ${briefRes.error}`} onRetry={() => void briefRes.reload()} /> : null}
      </div>{/* /rhythm-section brief */}

      {/* ── NOTIFY row ─────────────────────────────────────────── */}
      <div className="rhythm-section">
      {embedded ? null : <SurfaceLedger count="" cols="hub">
        <SurfaceLedgerRow
          primary="Notify"
          expands={false}
          // PHILO-17: in quiet hours the HELD pill joins the gadget; at a
          // phone width the row wraps (it squeezed "Notify" to 14 px).
          wrap
          data-testid="rhythm-notify-row"
          cells={
            <>
              <CycleGadget
                label="Notification mode"
                value={settings.notify}
                options={NOTIFY_OPTIONS}
                disabled={saving || sweeping}
                onChange={(v) => void putSetting({ notify: v })}
              />
              {/* Betterment daily D8 (decision 2): the quiet notice for a new
                  automation result. Notify off turns it off too. */}
              <CheckGadget
                label="FINISHED WORK"
                variant="token"
                checked={settings.notify_finished !== false}
                disabled={saving || sweeping || settings.notify === "off"}
                onChange={(on) => void putSetting({ notify_finished: on })}
              />
            </>
          }
          trailing={
            inQuiet ? (
              <span className="surface-token" data-chip data-tone="warn">HELD</span>
            ) : null
          }
        />
      </SurfaceLedger>}
      {/* Project mute toggles */}
      {projects.length > 0 ? (
        <div className="rhythm-mutes" data-testid="rhythm-mute-toggles">
          {projects.map((p) => {
            const name = (p.name || p.title || p.id).toUpperCase();
            const muted = (settings.muted_projects ?? []).includes(p.id);
            return (
              <CheckGadget
                key={p.id}
                label={name}
                variant="token"
                checked={!muted}
                disabled={saving || sweeping}
                onChange={(on) => {
                  const list = settings.muted_projects.filter((id: string) => id !== p.id);
                  if (!on) list.push(p.id);
                  void putSetting({ muted_projects: list });
                }}
              />
            );
          })}
        </div>
      ) : null}
      </div>{/* /rhythm-section notify */}

      {/* ── NOW N: existing cadence loops (kept from the old face) ── */}
      {action.message ? <SurfaceState error={action.message} /> : null}
      {replyReceipt ? (
        <p className="surface-receipt-line" data-tone="ok" role="status">
          <svg width="12" height="12" viewBox="0 0 16 16" aria-hidden="true" style={{ flexShrink: 0 }}><path d="M3.5 8.5 6.5 11.5 12.5 4.5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
          {replyReceipt}
        </p>
      ) : null}
      {loops.length > 0 ? (
        <SurfaceSection label={countLabel("NOW", loops.length)} data-engine={cadenceStatus.data?.enabled ?? false}>
          <SurfaceRows>
            {loops.map((loop, index) => {
              const id = rowId(loop, index);
              const next = loop.next_action as Record<string, unknown> | undefined;
              const score = Number(loop.stale_score ?? 0);
              const isQuestion = loop.source_type === "agent_question";
              return (
                <SurfaceRow
                  key={id}
                  title={String(loop.title ?? "Open loop")}
                  detail={
                    <>
                      {loop.needs_review ? (
                        <LampGadget on tone="warn" label="review" />
                      ) : null}{" "}
                      {deSnake(loop.source_type)}
                    </>
                  }
                  meta={score > 0 ? score.toFixed(0) : undefined}
                  verbs={
                    <>
                      {isQuestion ? (
                        <Button
                          dense
                          disabled={!replies[id]?.trim()}
                          onClick={() => void sendReply(id)}
                        >
                          Send reply
                        </Button>
                      ) : null}
                      <Button
                        dense
                        variant="ghost"
                        onClick={() => void act(id, "snooze")}
                      >
                        Snooze 1 day
                      </Button>
                      <ConfirmVerb
                        label="Mark done"
                        confirmLabel="Done?"
                        busy={action.busy}
                        onConfirm={() => void act(id, "close")}
                      />
                      <ConfirmVerb
                        label="Kill loop"
                        confirmLabel="Kill?"
                        busy={action.busy}
                        onConfirm={() => void act(id, "kill")}
                      />
                    </>
                  }
                >
                  {next ? (
                    <div className="surface-next-move">
                      <strong>{String(next.title ?? "Next action")}</strong>
                      <p>{String(next.body ?? next.body_markdown ?? "")}</p>
                    </div>
                  ) : null}
                  {isQuestion ? (
                    <PadGadget
                      label={`Reply to ${String(loop.title)}`}
                      value={replies[id] ?? ""}
                      onChange={(nextVal) =>
                        setReplies({ ...replies, [id]: nextVal })
                      }
                    />
                  ) : null}
                </SurfaceRow>
              );
            })}
          </SurfaceRows>
        </SurfaceSection>
      ) : null}

      </div>
      {/* ── Footer ─────────────────────────────────────────────── */}
      {embedded ? null : <SurfaceFooter
        receipt={saving || saveError || writtenAt ? (
          <span className="surface-token" data-chip data-muted={!saveError || undefined} data-tone={saveError ? "fail" : undefined} role="status">
            {saving ? "Saving" : saveError ? "Unconfirmed" : `Saved ${fmtEpoch(writtenAt)}`}
          </span>
        ) : null}
      />}
    </>
  );
}
