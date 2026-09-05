// HS-171-02 + HS-171-06 — the Rhythm face: sweep, brief, notify, loops.
// Composed from the surface kit on the window material (UX-CANON.md).
// Board truth: RhythmCadence.png, RhythmCadenceRunning.png,
// RhythmCadenceQuiet.png, RhythmPhone.png, SettingsHubHeartbeat.png.
//
// The existing cadence loop rows + their verbs (reply, snooze, mark done,
// kill) are preserved BELOW the new heartbeat rows under a `NOW N` caption,
// absent at zero.
import { useCallback, useState } from "react";
import type {
  CoreProps,
  CadenceLoopsResponse,
  CadenceHistoryResponse,
} from "./core-types";
import { Button } from "../../components/signal/Signal";
import {
  CheckGadget,
  CycleGadget,
  EgressChip,
  LampGadget,
  PadGadget,
} from "../../desk/surface/gadgets";
import {
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceSection,
  StateChip,
  countLabel,
} from "../../desk/surface";
import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
import { egressForEvent } from "../../desk/surface/egress";
import {
  ConfirmVerb,
  SurfaceRows,
  SurfaceRow,
  SurfaceState,
} from "../../desk/surface/Surface";
import { apiFetch } from "../../lib/api";
import { useResource, asRows, rowId } from "../pageSupport";
import { useAction } from "./core-hooks";
import { renderHeroSlot } from "./core-layout";
import { deSnake, humanTime } from "../../desk/surface/format";
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

const CONTENT_OPTIONS = [
  { value: "count_only", label: "COUNT ONLY" },
  { value: "room_names", label: "ROOM NAMES" },
];

/* ── Helpers ────────────────────────────────────────────────────── */

/** Format a 24h hour as HH:00. */
function fmtHour(h: number): string {
  return `${String(h).padStart(2, "0")}:00`;
}

/** Extract HH:MM from an ISO timestamp. */
function fmtTime(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const m = /(\d{2}:\d{2})/.exec(iso);
  return m ? m[1] : null;
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

/** Format epoch seconds as HH:MM. */
function fmtEpoch(epoch: number | null | undefined): string | null {
  if (epoch == null) return null;
  const d = new Date(epoch * 1000);
  return d.toTimeString().slice(0, 5);
}

/* ── The face ───────────────────────────────────────────────────── */

export function CadenceCore({ hero }: CoreProps) {
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
  const loopsResource = useResource<CadenceLoopsResponse>("/api/cadence/loops", {});
  const history = useResource<CadenceHistoryResponse>("/api/cadence/history?limit=20", {});
  const loops = asRows(loopsResource.data, ["loops"]);
  const [replies, setReplies] = useState<Record<string, string>>({});
  const [replyReceipt, setReplyReceipt] = useState("");
  const action = useAction();

  // ── Heartbeat state ──
  const [sweeping, setSweeping] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [receipt, setReceipt] = useState<SweepReceipt | null>(null);
  const [writtenAt, setWrittenAt] = useState<number | null>(null);
  // Notify content preference (not yet a server setting -- local only)
  const [notifyContent, setNotifyContent] = useState("count_only");

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
  };
  const projects = projectsRes.data?.projects ?? [];

  // ── Heartbeat mutations ──
  const putSetting = useCallback(async (patch: Partial<HeartbeatSettings>) => {
    const now = Date.now() / 1000;
    setWrittenAt(now);
    await apiFetch("/api/settings/heartbeat", { method: "PUT", json: patch });
    await heartbeat.reload();
  }, [heartbeat]);

  const runNow = useCallback(async () => {
    setSweeping(true);
    try {
      const result = await apiFetch<SweepReceipt>("/api/settings/heartbeat/run-now", {
        method: "POST",
        json: {},
      });
      setReceipt(result);
      await heartbeat.reload();
    } finally {
      setSweeping(false);
    }
  }, [heartbeat]);

  const generateBrief = useCallback(async () => {
    setGenerating(true);
    try {
      await apiFetch("/api/brief/generate", { method: "POST", json: {} });
      await briefRes.reload();
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
  const briefSummary = (() => {
    const tw = brief?.sections?.this_week;
    if (!tw || tw.length === 0) return null;
    const parts: string[] = [];
    for (const item of tw) {
      const ref = item.source_ref ?? "";
      const text = item.text ?? "";
      if (ref === "calendar:week") {
        const m = text.match(/^(\d+)\s+meeting/);
        if (m) parts.push(`${m[1]} MEETINGS`);
      } else if (ref === "meeting_watch:commitments_due") {
        const m = text.match(/^(\d+)\s+commitment/);
        if (m) parts.push(`${m[1]} COMMITMENTS DUE`);
      } else if (ref === "meeting_watch:decisions" || ref === "calendar:armed") {
        const m = text.match(/^(\d+)\s+/);
        if (m) parts.push(`${m[1]} WATCH ITEMS`);
      }
    }
    return parts.length > 0 ? parts.join(" · ") : null;
  })();

  return (
    <>
      {renderHeroSlot(hero, null, null)}

      {/* Display headline: accent when the sweep runs, muted when not */}
      <span
        className="surface-display"
        data-testid="rhythm-headline"
        data-tone={settings.sweep_every_minutes > 0 ? "accent" : undefined}
        data-muted={settings.sweep_every_minutes <= 0 || undefined}
      >
        {settings.sweep_every_minutes > 0 ? sweepLabel : "Not running"}
      </span>

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
              disabled={sweeping}
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
      </div>{/* /rhythm-section sweep */}

      {/* ── RUNS ON row (HS-174-08) ────────────────────────────── */}
      <div className="rhythm-section">
      <SurfaceLedger count="" cols="hub">
        <SurfaceLedgerRow
          primary="Runs on"
          expands={false}
          data-testid="rhythm-runs-on-row"
          cells={
            <CycleGadget
              label="Runner host"
              value={settings.runs_on || "local"}
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
                <EgressChip
                  label={`REMOTE · ${settings.runs_on}`}
                  scope="remote"
                  data-testid="rhythm-receipt-egress"
                />
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
          primary={calendarConfigured ? "Weekly brief" : "Monday brief"}
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
              <span className="surface-token" data-chip data-muted data-testid="rhythm-brief-cadence">
                {calendarConfigured
                  ? `WEEKLY MON ${fmtHour(settings.quiet_hours.end)}`
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
      </div>{/* /rhythm-section brief */}

      {/* ── NOTIFY row ─────────────────────────────────────────── */}
      <div className="rhythm-section">
      <SurfaceLedger count="" cols="hub">
        <SurfaceLedgerRow
          primary="Notify"
          expands={false}
          data-testid="rhythm-notify-row"
          cells={
            <>
              <CycleGadget
                label="Notification mode"
                value={settings.notify}
                options={NOTIFY_OPTIONS}
                onChange={(v) => void putSetting({ notify: v })}
              />
              <CycleGadget
                label="Notification content"
                value={notifyContent}
                options={CONTENT_OPTIONS}
                onChange={setNotifyContent}
              />
            </>
          }
          trailing={
            inQuiet ? (
              <span className="surface-token" data-chip data-tone="warn">HELD</span>
            ) : null
          }
        />
      </SurfaceLedger>
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

      {/* ── Footer ─────────────────────────────────────────────── */}
      <SurfaceFooter
        egress={<EgressChip />}
        receipt={
          <span className="surface-token" data-chip data-muted>
            WRITTEN {writtenAt
              ? fmtEpoch(writtenAt)
              : fmtTime(settings.last_sweep_at) ?? new Date().toTimeString().slice(0, 5)}
          </span>
        }
      />
    </>
  );
}
