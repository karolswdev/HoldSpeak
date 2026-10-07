// HS-170-04 -- ChairHome: THE ARRIVAL.
// The Tuesday face: one display headline, sections only when populated,
// every verb the library Button, no counters of zero, no sentences.
// The lane vocabulary is PARKED; the arrival composes directly from
// the surface library and the needs-you wire.

import { HandRowVerb } from "../components/HandRowVerb";
import { wireDate } from "../surface/format";
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Chair } from "./Chair";
import { ChairDesk } from "./ChairDesk";
import { Screen } from "../screen";
import { FirstRun } from "../firstrun/FirstRun";
import { useDesk } from "../store";
import { openNewThought } from "../newThought";
import { BriefEgress, briefReceipt } from "./briefEgress";
import { BriefHeadVerbs, BriefSendWells } from "../documentSendsLazy";
import { generatedLabelLocal } from "../pullouts/views/BriefView";
import { openSurface, openSurfaceOr, openCoderSession, openProjectRoom } from "../shell";
import { reportWriteFailure, clearWriteFailure } from "../hooks/useWriteReceipt";
import { ApiError, apiFetch, readableError } from "../../lib/api";
import { Button } from "../../components/signal/Signal";
import { MicButton } from "../components/MicButton";
import { intelBadge } from "./intelBadge";
import { onReturnToTask } from "../returnToTask";
import { refreshNeedsYou, useNeedsYou } from "../needsYou";
import { burstTimer } from "../burstTimer";
import { useRuntimeBus, useRuntimeFrame } from "../../runtime/RuntimeBus";
import { labelFor, supportsDoorVerb, commandForDoorVerb } from "./doorVerbs";
import {
  SurfaceSection,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceWell,
  EgressChip,
  StateChip,
  Disclosure,
  FilterTokens,
  CoverageLedger,
  ProjectButton,
  LedgerRemainder,
  countLabel,
  countToken,
  StringGadget,
  needYouWords,
} from "../surface";
import { openIntelligence } from "../intelligenceNavigation";
import { calendarOpener, openProjectProposal, refOpener, resolveOwner, type Opener } from "../openObject";
import { readCoverage, type CoverageRecord } from "../coverage";
import {
  ATTENTION_CAP,
  RANK_CLASSES,
  RANK_LABEL,
  ageToken,
  attentionCaption,
  observedAtToken,
  rankClassOf,
  reasonToken,
  type AttentionSource,
  type RankClass,
} from "../attention";
import { unfinishedThoughts, type UnfinishedThought } from "../thoughts";
import type { Meeting } from "../../lib/primitives";
import { fromWireMeeting } from "../api";
import { MeetingSummarySlab } from "../../meetings/MeetingSummarySlab";
import { MeetingSendWellLazy } from "../../meetings/MeetingSendWellLazy";
import { TranscriptWell } from "../../pages/cores/history/TranscriptWell";
import {
  RefusalToken,
  RouteDisclosure,
  RunAttempts,
} from "../../meetings/RouteDisclosure";
import { egressFor } from "../surface/egress";
import { useOnCoderFrame } from "../useDeskChangedRefresh";
import {
  agentWord,
  flightForItem,
  isInFlight,
  liveAgentSessions,
  useAgentFlights,
  useAgentFlightsLive,
  type CoderSessionRow,
} from "../agentFlights";
import { FlightChip, FlightVerbs } from "../components/AgentFlight";
import {
  executedReceipt,
  postSummaryRun,
  routeReady,
  type PlannedRoute,
  type SummaryRefusal,
} from "../../meetings/summaryRoute";
import { openDrawer } from "../drawer/store";

// ── Types ──────────────────────────────────────────────────────────

interface NeedsYouItem {
  projectId: string;
  projectName: string;
  ref: string;
  title: string;
  why: string;
  ageToken: string;
  source: string;
  verbHref: string | null;
  severity: string;
  /** HS-171: true when the item's Room is muted. */
  muted?: boolean;
  /** True when the owner waits on someone else for the row (not counted). */
  waiting?: boolean;
  /** The Desk route token the row opens (a decision: `decision:<id>`). */
  openRef?: string | null;
  /** HS-172-03: proposal fields from the aggregate. */
  proposalId?: string;
  proposalKind?: string;
  proposalHost?: string;
  proposalDue?: string;
  meetingTitle?: string;
  /** HS-200-07: a stable id, and the last-observation marks. */
  id?: string;
  fromLastObservation?: boolean;
  observedAt?: string | null;
  /** HS-200-15: the observable facts the ranking reads, the wire's
   *  class, and the constituent projections of a deduplicated row. */
  since?: string;
  dueAt?: string | null;
  kind?: string | null;
  rankClass?: string;
  rank?: number;
  sources?: AttentionSource[];
  dedupCount?: number;
  /** HS-200-13: a commitment row's verbs write to its action item; the
   *  producer names the typed unknowns and the ONE lawful next action. */
  commitmentId?: string;
  actionItemId?: string | null;
  owner?: string | null;
  unknowns?: string[];
  nextAction?: "name_owner" | "set_date" | "mark_done" | null;
  decisionRecordId?: string | null;
  /** Conductor K3 (R5): a coder row's session, agent, question and wait. */
  sessionKey?: string;
  agent?: string;
  question?: string;
  waitStartedAt?: string;
  ageSeconds?: number;
}

interface NeedsYouPayload {
  count: number;
  mutedCount?: number;
  projects: string[];
  items: NeedsYouItem[];
  next: { label: string; at: string } | null;
  /** HS-200-07 (C4): one record per expected source. */
  coverage?: CoverageRecord[];
  complete?: boolean;
  /** The aggregate's own clock (HS-171-03). */
  computedAt?: string;
}

interface BriefItem {
  id: string;
  section: string;
  text: string;
  detail?: string | null;
  source_ref?: string | null;
  priority: number;
  created_at?: string | null;
}

interface MondayBrief {
  id: string;
  headline: string;
  sections: Record<string, BriefItem[]>;
  is_empty: boolean;
  generated_at?: string;
  shelf?: Record<string, string>;
  /* PHILO-3-03: the route's own date labels (holdspeak/web/routes/monday_brief.py). */
  period_label?: string | null;
  generated_label?: string | null;
}

/** PHILO-3-03: why the brief read failed — the status, or no answer at all. */
function briefLoadCause(error: unknown): string {
  return error instanceof ApiError ? `HTTP ${error.status}` : "NO ANSWER";
}

/** PHILO-3-03: the brief's period and generated date, one caption line.
 *  PHILO-6-02 (a): the generated time is the producer's `generated_at` in
 *  the viewer's zone, the same clock as the receipt; the hub's own label
 *  (formatted in the hub's offset) is the fallback only. */
function BriefDate({ brief }: { brief: MondayBrief }) {
  const parts = [
    brief.period_label,
    generatedLabelLocal(brief.generated_at) ?? brief.generated_label,
  ].filter(Boolean);
  if (parts.length === 0) return null;
  return (
    <span className="surface-receipt-line" data-testid="arrival-brief-date">
      {parts.join(" · ")}
    </span>
  );
}

/** Door card (from GET /api/door .board columns). */
interface DoorCard {
  id: string;
  source: string;
  target_ref: string;
  open_ref?: string;
  title?: string;
  text?: string;
  owner?: string | null;
  due?: string | null;
  continuity_state?: string;
  /** HS-150-02: the owner mapped to a People relationship (only when mapped). */
  person_relationship_id?: string;
  lawful_verbs?: Array<{ name: string; arguments: Record<string, string | number | null | undefined>; required_arguments?: string[] }>;
}

interface UpcomingArmed {
  recording_id: string;
  arms_at: string;
  /** HS-175 C2: the recording's state; Cancel is withheld while `recording`. */
  state?: string;
}

interface UpcomingFrom {
  event_title: string;
  source_label: string;
}

interface UpcomingItem {
  id: string;
  source: string;
  title: string;
  starts_at: string;
  ends_at?: string;
  source_label?: string;
  project_id?: string;
  project_name?: string;
  /** HS-149-03: the person a linked series belongs to (only when linked). */
  person_relationship_id?: string;
  armed_schedule_id?: string;
  armed?: UpcomingArmed;
  state?: string;
  from?: UpcomingFrom;
}

interface WeekDay {
  date: string;
  dow: string;
  count: number;
}

interface WeekStripData {
  days: WeekDay[];
  total: number;
  has_calendar: boolean;
  /** HS-175 C9: the local week's bounds as UTC instants (ends_at exclusive). */
  starts_at?: string;
  ends_at?: string;
}

interface DoorProjection {
  board: Record<string, DoorCard[]>;
  counts: Record<string, number>;
  upcoming: UpcomingItem[];
  calendar_configured: boolean;
  week?: WeekStripData;
}

// ── Helpers ────────────────────────────────────────────────────────

const MONTHS = [
  "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
  "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
];

function ledgerDate(iso: string): string {
  const d = wireDate(iso);
  if (!d) return "";
  return `${MONTHS[d.getMonth()]} ${String(d.getDate()).padStart(2, "0")}`;
}

function durationMin(seconds: number | null | undefined): string {
  if (!seconds || seconds <= 0) return "";
  if (seconds < 60) return `${Math.max(1, Math.round(seconds))} S`;
  const minutes = Math.round(seconds / 60);
  if (minutes <= 0) return "";
  return `${minutes} MIN`;
}

function arrivalIntelBadge(meeting: Meeting): string {
  const job = meeting.intelJob;
  // A queued successor with a failed lineage remains RETRYING after its
  // scheduled time. Manual and initial queues have no failure fact.
  if (
    (job?.status === "queued" || job?.status === "retrying") &&
    job.attempts > 0 &&
    Boolean(job.lastError)
  ) {
    return "RETRYING";
  }
  if (job?.status === "failed") return "FAILED";
  return intelBadge(meeting.intelStatus);
}

/** PHILO-13-11 (A3-W ledger): a summary is stored for this meeting — the
 * list row's `has_summary` (H-A3, #729) or the summary the detail read. */
function summaryStored(...rows: Meeting[]): boolean {
  return rows.some(
    (row) => row.hasSummary === true || Boolean(String(row.intelSummary ?? "").trim()),
  );
}

interface ArrivalMeetingDetail {
  meeting: Meeting | null;
  error: string | null;
}

/** Source emblem token: GH for github, J for jira, MTG for proposals, etc. */
function sourceEmblem(source: string): string {
  const s = source.toLowerCase();
  if (s === "github") return "GH";
  if (s === "jira") return "J";
  if (s === "delta") return "D";
  if (s === "proposal" || s === "meeting" || s === "action_item") return "MTG";
  if (s === "commitment") return "CMT";
  if (s === "decision") return "DEC";
  if (s === "thought") return "TH";
  return s.slice(0, 2).toUpperCase();
}

/** Door source emblem: MTG for meetings, TH for thoughts, DOOR for unknown. */
function doorEmblem(source: string): string {
  if (source === "meeting" || source === "action_item") return "MTG";
  if (source === "thought") return "TH";
  return "DOOR";
}

/** A brief item whose text is a raw Service.method / dotted-id / snake_case
 *  internal name is NOT human-facing and must never render on the arrival.
 *  Examples: "PrimitiveService.delete_directory", "RecipeService.run". */
const RAW_ID_RE = /^[A-Z][a-zA-Z]*(?:Service|Manager|Handler|Provider)\b|\b[a-z_]+\.[a-z_]+$/;
function isRawId(text: string): boolean {
  return RAW_ID_RE.test(text.trim());
}

/** WHY token colour: danger = warning/orange, warning = amber, info = muted. */
function whySeverityTone(severity: string): string {
  if (severity === "danger") return "failure";
  if (severity === "warning") return "warning";
  return "idle";
}

/** Headline for the arrival: zero = "Nothing needs you" (UX-CANON A8).
 *  HS-200-07 (C4): the all-clear line is spoken ONLY over complete
 *  coverage; an empty PARTIAL result names the coverage instead.
 *  HS-200-15 (verdict): the display line is the TRUE total; the Project
 *  clause is withheld when there is exactly one Project (`3 need you`). */
export function headlineFor(
  count: number,
  projectCount: number,
  complete = true,
  pending = 0,
): string {
  // HS-201-01: `pending` is what needs the owner but is not an attention
  // row -- the meeting-path blocker and every FAILED meeting on the face.
  // The all-clear is never spoken over one (audits/face-walk-opus.md
  // defect 8: `Nothing needs you` above a FAILED meeting).
  // HS-201-11: the number the head speaks is ONE total -- the attention
  // list plus what asks beside it (the SETUP row, a FAILED meeting). The
  // rehearsal read `1 need you` while the attention list and the blocker
  // were counted separately (audits/rehearsal-07-opus.md, step 1). The
  // calendar row is an OFFER and is counted by neither (owner's ruling).
  const total = count + Math.max(0, pending);
  if (total <= 0) {
    return complete ? "Nothing needs you" : "Coverage incomplete";
  }
  const n = String(total);
  // The Project clause speaks only for the attention list, which is what
  // the Projects are counted over.
  if (count > 0 && projectCount > 1) {
    return needYouWords(n) + " across " + String(projectCount) + " projects";
  }
  // PHILO-15-09 (B11): `1 needs you`.
  return needYouWords(n);
}

/** Format NEXT line from the payload. */
/** HS-175-02: the NEXT line may carry a Room token when the next
 *  calendar event is linked to a project (the board: NEXT . STANDUP . 10:00 . ROOM . Q4 PLATFORM). */
function nextLine(next: NeedsYouPayload["next"] & { room?: string } | null): string | null {
  if (!next) return null;
  const parts: string[] = ["NEXT"];
  if (next.label) parts.push(next.label.toUpperCase());
  if (next.at) {
    const d = new Date(next.at);
    if (!Number.isNaN(d.getTime())) {
      parts.push(
        d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false }),
      );
    }
  }
  if (next.room) {
    parts.push("ROOM");
    parts.push(next.room.toUpperCase());
  }
  return parts.join(" · ");
}

/** Format event time: HH:MM for today, DOW HH:MM for other days. */
function formatEventTime(startsAt: string): string {
  const d = wireDate(startsAt);
  if (!d) return "";
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  const now = new Date();
  const isToday =
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate();
  if (isToday) return `${hh}:${mm}`;
  const DOW = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
  return `${DOW[d.getDay()]} ${hh}:${mm}`;
}

/** Format arms_at ISO to local HH:MM. */
function formatArmsTime(iso: string): string {
  const d = wireDate(iso);
  if (!d) return "";
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

/** Today's date as YYYY-MM-DD in local timezone. */
function todayDateStr(): string {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, "0");
  const dd = String(now.getDate()).padStart(2, "0");
  return `${y}-${m}-${dd}`;
}

const continuityLabels: Record<string, string> = {
  idle: "Continue",
  reserved: "Working",
  in_flight: "Working",
  awaiting_projection: "Working",
  review_ready: "Ready for you",
  stale: "Needs attention",
  named_failure: "Needs attention",
  unavailable_remote: "Needs attention",
};

// ── ChairHome ──────────────────────────────────────────────────────

export function ChairHome({ arrivalRequired = false }: { arrivalRequired?: boolean }) {
  if (arrivalRequired) {
    return (
      <main className="chair chair-first-value" data-testid="chair-first-value">
        {/* First run C1 "Heard first" (owner ratified 2026-10-05). */}
        <FirstRun />
      </main>
    );
  }

  return (
    <Chair>
      <Arrival />
    </Chair>
  );
}

// ── The Arrival face ───────────────────────────────────────────────

function Arrival() {
  // ── needs-you (PHILO-13-03, A2-W) ──
  // ONE membership for the whole Desk: the Chair, the bell and the Dock read
  // the same snapshot from `needsYou.ts` (R1 rows + R2 blockers + R3
  // meetings). The Chair keeps no copy of the rule. HS-200-07 (C4): a read
  // that never landed is itself a coverage gap.
  const needs = useNeedsYou();
  const needsYou = needs.room as (NeedsYouPayload & { next?: NeedsYouPayload["next"] }) | null;
  const needsYouUnread = Boolean(needs.errors.room);
  const readNeedsYou = useCallback((fresh = false) => refreshNeedsYou(fresh), []);

  // ── door wire (owner's action items) ──
  const [door, setDoor] = useState<DoorProjection | null>(null);
  useEffect(() => {
    void apiFetch<DoorProjection>("/api/door").then(setDoor).catch(() => null);
  }, []);

  // ── thoughts ──
  const deskUpdatedAt = useDesk((state) => state.updatedAt);
  const [thoughts, setThoughts] = useState<UnfinishedThought[]>([]);
  useEffect(() => {
    void unfinishedThoughts()
      .then((page) => setThoughts(page.items))
      .catch(() => undefined);
  }, [deskUpdatedAt]);

  // ── brief ──
  const [brief, setBrief] = useState<MondayBrief | null>(null);
  /* PHILO-5-04: the existing Article III receipt also identifies the
     latest durable brief on arrival. A failed read retains it. */
  const [briefKept, setBriefKept] = useState<string | null>(null);
  const [briefLoading, setBriefLoading] = useState(true);
  /* PHILO-3-03: a failed read is NOT an absent brief. `null` = the read
     answered (or has not failed); a string = the cause the face names. */
  const [briefLoadFailed, setBriefLoadFailed] = useState<string | null>(null);
  /* PHILO-4-01 (ratified canvas, boards 3a, 6b, 8b): a failed generation
     names its cause in the section's status slot. No Retry: the enabled
     head Generate repeats the same POST. */
  const [generateFailed, setGenerateFailed] = useState<string | null>(null);
  const generatedBriefScrollPending = useRef(false);
  const readBrief = useCallback(() => {
    setBriefLoading(true);
    setBriefLoadFailed(null);
    setGenerateFailed(null);
    void apiFetch<MondayBrief | null>("/api/brief/latest")
      .then((data) => {
        setBrief(data);
        setBriefKept(briefReceipt(data));
      })
      .catch((error) => setBriefLoadFailed(briefLoadCause(error)))
      .finally(() => setBriefLoading(false));
  }, []);
  useEffect(() => { readBrief(); }, [readBrief]);

  // ── meetings ──
  const meetings = useDesk((s) => s.items.meeting);
  // PHILO-15-09 (B07): what the desk knows for this week.
  const deskDecisions = useDesk((s) => s.items.decision);
  const meetingDetailKey = useMemo(
    () => [...meetings]
      .sort((a, b) => new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime())
      .slice(0, 3)
      .map((meeting) => meeting.id)
      .join("|"),
    [meetings],
  );
  const [meetingDetails, setMeetingDetails] = useState<Record<string, ArrivalMeetingDetail>>({});
  const meetingReadGeneration = useRef(0);
  useEffect(() => {
    const ids = meetingDetailKey ? meetingDetailKey.split("|") : [];
    const generation = ++meetingReadGeneration.current;
    // A desk refresh starts a new read generation. Keep wells already rendered
    // for the same meeting in place until its replacement arrives; this also
    // preserves a transcript fold the owner opened. Drop identities that left
    // the visible top-three set so removed meetings cannot linger.
    setMeetingDetails((current) => {
      const visible = new Set(ids);
      const retained = Object.fromEntries(
        Object.entries(current).filter(([id]) => visible.has(id)),
      );
      return Object.keys(retained).length === Object.keys(current).length
        ? current
        : retained;
    });
    if (ids.length === 0) return;
    let active = true;
    for (const id of ids) {
      void apiFetch<unknown>(`/api/meetings/${encodeURIComponent(id)}`)
        .then((wire) => {
          if (!active || generation !== meetingReadGeneration.current) return;
          const detail = fromWireMeeting(wire);
          if (!detail) {
            setMeetingDetails((current) => ({
              ...current,
              [id]: { meeting: null, error: "SUMMARY READ FAILED" },
            }));
            return;
          }
          if (detail.id !== id) {
            setMeetingDetails((current) => ({
              ...current,
              [id]: {
                meeting: null,
                error: "SUMMARY READ FAILED",
              },
            }));
            return;
          }
          setMeetingDetails((current) => ({
            ...current,
            [id]: { meeting: detail, error: null },
          }));
        })
        .catch((cause) => {
          if (!active || generation !== meetingReadGeneration.current) return;
          setMeetingDetails((current) => ({
            ...current,
            [id]: { meeting: null, error: readableError(cause) },
          }));
        });
    }
    return () => { active = false; };
  }, [meetingDetailKey, deskUpdatedAt]);

  // ── the meeting-path blockers (HS-201-01) ──
  // The assignment roster, re-read whenever it can have changed. Counsel
  // fix round (Astra finding 1): a mount-only read left the repaired row
  // on an OPEN desk until the owner navigated -- the product knew the
  // path was clear and the face still asked for an engine. So the Chair
  // re-reads on the hub's `desk_changed` frame (the burst is debounced,
  // as `useDeskChangedRefresh` does) and when the window takes focus
  // again (the owner comes back from Models, or from anywhere else).
  // A read that has not landed is an UNKNOWN, never a clear desk.
  // PHILO-13-03: the roster is one of the membership's inputs, so a re-read
  // is a needs-you refresh (the shared snapshot reads the roster itself).
  const readAssignments = useCallback(() => refreshNeedsYou(false), []);
  // Counsel round 2 (condition 1): the product's OWN return signal. Models
  // announces `holdspeak:settings-updated` the moment it applies a set
  // (`features/concierge/useConciergeController.ts:507` ->
  // `desk/returnToTask.ts:113`), and every face holding an unfinished task
  // re-reads on it. The Chair is such a face: its SETUP row IS the
  // unfinished task the owner left to repair.
  useEffect(() => onReturnToTask(() => { void readAssignments(); }), [readAssignments]);
  const { subscribe: subscribeFrames } = useRuntimeBus();
  useEffect(() => {
    const burst = burstTimer(() => { void refreshNeedsYou(true); }, 300);
    const unsubscribe = subscribeFrames("desk_changed", burst.bump);
    const onFocus = () => { void readAssignments(); };
    window.addEventListener("focus", onFocus);
    return () => {
      burst.cancel();
      unsubscribe();
      window.removeEventListener("focus", onFocus);
    };
  }, [subscribeFrames, readAssignments]);
  const blockers = needs.blockers;

  // HS-200-42 (counsel N1): WHO will execute the queue. The `runtime_queue`
  // frame (the same one the ambient HUD chip reads) now carries the hub
  // drainer's state, so "queued with nothing to run it" is a durable fact on
  // the row rather than a sub-second flash of the click receipt. `null` means
  // no frame has arrived yet: unknown, and never reported as absent.
  const queueFrame = useRuntimeFrame<{ drainer?: string }>("runtime_queue");
  const drainerAbsent = queueFrame?.drainer === "absent";

  // ── agents (coders sessions) ──
  // Conductor F2 (K4c): every live session, from `/api/coders/sessions`
  // (the agents store). `/api/coders/status` lists only sessions that set
  // `awaiting_response` in the last 30 minutes, so a working agent and an
  // agent a Notification stopped were never listed. The store re-reads on
  // the `scope:"coder"` frame and on `desk_changed`.
  // PHILO-14 C4: the AGENTS section is parked; the store stays live here
  // (the screen and the Conductor drawer read it).
  useAgentFlightsLive();
  // Conductor K3: an agent that begins or stops waiting moves Needs you now
  // (the `scope:"coder"` frame), not at the next minute's poll.
  const onCoderFrame = useCallback(() => {
    void refreshNeedsYou(true);
  }, []);
  useOnCoderFrame(onCoderFrame);

  // ── brief generate ──
  const [generating, setGenerating] = useState(false);
  // PHILO-13-11 (C1, slice two): the capture bar lives in its own Chair
  // window now; the scroll well's clearance for a sticky bar is gone.

  const generateBrief = async () => {
    setGenerating(true);
    setGenerateFailed(null);
    try {
      const data = await apiFetch<MondayBrief>("/api/brief/generate", { method: "POST" });
      generatedBriefScrollPending.current = true;
      setBrief(data);
      setBriefLoadFailed(null);
      setBriefKept(briefReceipt(data));
      clearWriteFailure();
    } catch (error) {
      setGenerateFailed(briefLoadCause(error));
    }
    finally { setGenerating(false); }
  };
  /* PHILO-4-01 (ratified canvas, ask 1): the head verbs of the BRIEF
     section in EVERY branch — the egress badge, then Generate. Disabled
     only while a read or a generation is open. */
  const briefHeadVerbs = (
    <>
      {/* Article III / UX-CANON A.9 — the destination is named ON the
          row, BEFORE the verb that reaches it. */}
      <BriefEgress />
      <Button
        variant="ghost"
        dense
        disabled={generating || briefLoading}
        onClick={() => void generateBrief()}
        data-testid="arrival-brief-generate"
      >
        Generate
      </Button>
    </>
  );
  /* PHILO-11-05a (canvas A4): with a brief, PREPARED ×K leads the verbs and,
     while a send waits, the chip and the verbs are one group that wraps under
     the label at narrow width (desk/documentSends.tsx `BriefHeadVerbs`). */
  const briefVerbs = brief
    ? <BriefHeadVerbs brief={brief}>{briefHeadVerbs}</BriefHeadVerbs>
    : briefHeadVerbs;
  /* The one status line of a generation: open (GENERATING…, the READING…
     idiom) or failed (BRIEF DID NOT GENERATE · <cause>). */
  const generateStatus = generating ? (
    <span className="surface-receipt-line" role="status" data-testid="arrival-brief-generating">
      GENERATING…
    </span>
  ) : generateFailed ? (
    <span className="arrival-brief-failed">
      <span
        className="surface-receipt-line"
        role="status"
        data-tone="danger"
        data-testid="arrival-brief-generate-failed"
      >
        {`BRIEF DID NOT GENERATE · ${generateFailed}`}
      </span>
    </span>
  ) : null;

  // HS-200-15: ONE clock per render for every age and OBSERVED token.
  const now = useMemo(() => new Date(), [needs.members, needsYou]);
  // HS-171 / HS-200-13 / HS-200-15: the Door's cards and the Room's rows,
  // the Room's commitment winning over its Door card, deduplicated, ranked,
  // the muted rows apart: all of it is the module's (`computeNeedsYou`).
  const unmutedItems = needs.unmutedItems as unknown as NeedsYouItem[];
  const mutedItems = needs.mutedItems as unknown as NeedsYouItem[];

  // ── the ranking filter (RANKED = the full key) ──
  const [rankFilter, setRankFilter] = useState<"" | RankClass>("");

  // ── headline: what needs the owner (unmuted) ──
  // Owner ruling 2026-10-04: a row he waits on someone else for is listed
  // (the WAITING filter shows it) and the headline does not count it.
  const count = unmutedItems.length - needs.waitingCount;
  const projectCount = needsYou?.projects?.length ?? 0;
  // The way back is drawn on every row, withheld when the desk holds ONE
  // Project (repeating one word on every row says nothing).
  const multipleProjects = projectCount > 1;
  // HS-200-07: coverage decides whether zero may be spoken as an all-clear.
  const coverage = useMemo(
    () => readCoverage(needsYou?.coverage, needsYou?.complete, needsYouUnread),
    [needsYou, needsYouUnread],
  );
  // HS-201-01: what needs the owner but is not an attention row -- the
  // meeting-path blockers (R2) and every FAILED or RETRYING meeting (R3,
  // the module's bounded server read). `Nothing needs you` is never spoken
  // over one (audits/face-walk-opus.md defect 8).
  // HS-201-11 (owner's ruling): the calendar row is an OFFER, not a row
  // that asks, so `Connect calendar` renders and the head never counts it.
  const pending = needs.count - count;
  // Counsel fix round, second pass (ruling 1): a read still in flight (or
  // one that failed) draws no all-clear -- an unknown is never spoken as a
  // clear desk.
  const headline = headlineFor(
    count,
    projectCount,
    coverage.complete && needs.complete,
    pending,
  );
  const headlineAccent = count > 0 || pending > 0;
  const mutedCount = mutedItems.length > 0 ? mutedItems.length : 0;
  // HS-200-15 (D1): the head states coverage only when it is COMPLETE;
  // an incomplete read is stated by the COVERAGE section, once.
  const coverageChip =
    coverage.complete && coverage.expected > 0
      ? `${coverage.available} OF ${coverage.expected} AVAILABLE`
      : null;
  const checkedAge = coverageChip ? ageToken(needsYou?.computedAt, now) : "";
  const checkedToken = checkedAge
    ? checkedAge === "JUST NOW" ? "CHECKED JUST NOW" : `CHECKED ${checkedAge} AGO`
    : "";

  // PHILO-14 A2b: a generic open of a Project opens its drawer; only an
  // explicit Room verb opens the Room.
  const openProject = useCallback((projectId: string) => {
    openDrawer(projectId);
  }, []);

  // The owning verb of a coverage gap: `Retry` re-reads the aggregate
  // fresh; every other verb opens the source where its repair lives.
  const repairCoverage = useCallback((gap: CoverageRecord) => {
    const repair = gap.repair;
    if (!repair) return;
    if (repair.verb === "Retry") { void readNeedsYou(true); return; }
    if (repair.href.startsWith("/settings")) {
      openSurfaceOr("configure-settings", "/settings", "connections");
      return;
    }
    // The repair lives in the Room's Sources (as the shade's repair): Room.
    openProjectRoom(gap.project_id);
  }, [readNeedsYou]);

  // ── NEXT line: prefer door upcoming (schedule/calendar), fall back to rooms ──
  // HS-175-02: when the next item is a calendar_event with a Room link,
  // carry the project_name so the NEXT line reads ROOM . Q4 PLATFORM.
  const doorNext = door?.upcoming?.[0];
  const nextPayload = doorNext
    ? { label: doorNext.title, at: doorNext.starts_at, room: doorNext.project_name || undefined }
    : needsYou?.next ?? null;
  const next = nextLine(nextPayload);

  // ── brief items (untriaged only) ──
  const sortDecisionItems = (items: BriefItem[]) => [...items].sort((a, b) => {
    const aTime = a.created_at ? Date.parse(a.created_at) : Number.NEGATIVE_INFINITY;
    const bTime = b.created_at ? Date.parse(b.created_at) : Number.NEGATIVE_INFINITY;
    return bTime - aTime;
  });
  const briefItems: BriefItem[] = brief && !brief.is_empty
    ? [
      ...sortDecisionItems(brief.sections.decisions ?? []),
      ...(brief.sections.changed ?? []),
      ...(brief.sections.broke ?? []),
      ...(brief.sections.waiting ?? []),
    ]
    : [];
  const briefShelf = brief?.shelf ?? {};
  const untriagedBrief = briefItems
    .filter((item) => !briefShelf[item.id])
    .filter((item) => !isRawId(item.text));
  /* PHILO-4-04 (ratified board 7c): the stored headline remains the
     producer's snapshot. Name the current Arrival triage only when every
     Arrival item has a durable Ack or Defer shelf state. `briefItems` is the
     Arrival projection above, so THIS WEEK is outside this count; raw-id
     rows remain in it until shelved and therefore cannot claim completion
     while hidden from the face. */
  const handledBriefItems = briefItems.filter((item) => (
    briefShelf[item.id] === "acknowledged" || briefShelf[item.id] === "deferred"
  ));
  const handledBriefCount = (
    briefItems.length > 0 && handledBriefItems.length === briefItems.length
  ) ? handledBriefItems.length : null;
  const handledBriefLine = handledBriefCount === null ? null : `ALL ${handledBriefCount} HANDLED`;

  // Generate owns the only automatic move. Initial loads, failures and shelf
  // changes leave the owner's scroll position alone. The native nearest rule
  // moves the result without adding a focus change of its own.
  useLayoutEffect(() => {
    if (!generatedBriefScrollPending.current) return;
    generatedBriefScrollPending.current = false;
    const firstRow = document.querySelector<HTMLElement>('[data-testid="arrival-brief-row"]');
    firstRow?.scrollIntoView?.({ block: "nearest", behavior: "instant" });
  }, [brief]);

  // ── shelf verbs ──
  const [busyBriefId, setBusyBriefId] = useState<string | null>(null);
  const doBriefShelf = async (itemId: string, state: "acknowledged" | "deferred") => {
    const current = briefShelf[itemId];
    const next: string | null = current === state ? null : state;
    setBusyBriefId(itemId);
    try {
      await apiFetch(`/api/brief/items/${encodeURIComponent(itemId)}/shelf`, {
        method: "POST",
        json: { state: next },
      });
      setBrief((prev) => {
        if (!prev) return prev;
        const updated = { ...prev.shelf };
        if (next === null) delete (updated as Record<string, string>)[itemId];
        else (updated as Record<string, string>)[itemId] = next;
        return { ...prev, shelf: updated };
      });
      clearWriteFailure(`brief-item:${itemId}`);
    } catch (error) {
      reportWriteFailure(state === "acknowledged" ? "Acknowledge" : "Defer", error, () => void doBriefShelf(itemId, state), `brief-item:${itemId}`);
    }
    finally { setBusyBriefId(null); }
  };

  // ── intel run ──
  const [runningIntel, setRunningIntel] = useState<string | null>(null);
  // HS-200-42: the receipt carries the DRAINER's state too. The verb
  // enqueues; whether anything executes the queue is a separate fact, and
  // the face must not say "Running..." when the answer is "nothing will".
  const [intelReceipt, setIntelReceipt] = useState<
    { meetingId: string; drainer: string } | null
  >(null);
  // HS-201-04: the hub's 409, kept as a refusal with its plain reason.
  const [intelRefusal, setIntelRefusal] = useState<
    { meetingId: string; refusal: SummaryRefusal } | null
  >(null);
  const runIntelligence = async (meetingId: string, route: PlannedRoute | null) => {
    setRunningIntel(meetingId);
    setIntelReceipt(null);
    setIntelRefusal(null);
    try {
      // The disclosed selection travels with the gesture (story 03's
      // contract): the hub binds this exact selection, or refuses.
      const outcome = await postSummaryRun<{
        jobId: string;
        state: string;
        host: string;
        drainer?: string;
      }>(
        `/api/meetings/${encodeURIComponent(meetingId)}/intelligence/run`,
        route,
      );
      if (!outcome.ok) {
        setIntelRefusal({ meetingId, refusal: outcome.refusal });
        void useDesk.getState().refresh();
        clearWriteFailure(`meeting:${meetingId}`);
        return;
      }
      setIntelReceipt({
        meetingId,
        drainer: outcome.result.drainer === "running" ? "running" : "absent",
      });
      void useDesk.getState().refresh();
      // PHILO-13-03: a run moves a FAILED meeting out of the membership.
      void refreshNeedsYou(true);
      clearWriteFailure(`meeting:${meetingId}`);
    } catch (error) {
      reportWriteFailure("Run summary", error, () => void runIntelligence(meetingId, route), `meeting:${meetingId}`);
    }
    finally { setRunningIntel(null); }
  };

  // HS-200-42 (counsel F2): the receipt is a PRE-REFRESH optimistic state and
  // nothing more. It used to pin the Chair badge to QUEUED forever, so the
  // story-42 walk caught the Chair reading QUEUED while the Meetings window
  // read RUNNING at the same instant. The moment the server's own status for
  // that meeting leaves `off`, the receipt is dropped and the badge follows
  // the server: which is also what puts the verb back after a failed job
  // that returns to an off-with-transcript row.
  useEffect(() => {
    if (!intelReceipt) return;
    const row = meetings.find((m) => m.id === intelReceipt.meetingId);
    if (!row) return;
    if (intelBadge(row.intelStatus) !== "OFF") setIntelReceipt(null);
  }, [meetings, intelReceipt]);

  // ── proposal confirm: optimistically remove from needs-you ──
  // PHILO-13-03: a confirm changes the membership, so the ONE snapshot is
  // re-read fresh: the Chair, the bell and the Dock move together.
  const handleProposalConfirm = useCallback((_proposalId: string) => {
    void refreshNeedsYou(true);
  }, []);

  // ── arming countdown (lost door 2) ──
  const arming = useDesk((s) => s.scheduledArming);
  const [countdown, setCountdown] = useState<number | null>(null);
  useEffect(() => {
    if (!arming || arming.outcome) { setCountdown(null); return; }
    const tick = () => {
      const remaining = Math.max(0, Math.ceil((arming.fireAt - Date.now()) / 1000));
      setCountdown(remaining);
    };
    tick();
    const t = window.setInterval(tick, 250);
    return () => window.clearInterval(t);
  }, [arming]);
  const isArming = arming && !arming.outcome && countdown !== null;

  // ── connect calendar (lost door 4) ──
  const calendarConfigured = door?.calendar_configured ?? true;

  // ── HS-175-02: calendar events and week strip from door ──
  const week = door?.week;
  // HS-175 C9: the THIS WEEK section is bounded to the week the strip
  // draws (the door's `upcoming` is a longer projection; the NEXT line
  // may still name next week's very next event).
  const calendarEvents = useMemo(() => {
    if (!door?.upcoming) return [];
    const weekEnd = week?.ends_at ? new Date(week.ends_at).getTime() : NaN;
    return door.upcoming.filter((item) => {
      if (item.source !== "calendar_event") return false;
      if (Number.isNaN(weekEnd)) return true;
      const at = new Date(item.starts_at).getTime();
      return Number.isNaN(at) || at < weekEnd;
    });
  }, [door, week]);

  const orphanRecordings = useMemo(() => {
    if (!door?.upcoming) return [];
    return door.upcoming.filter(
      (item) => item.source === "scheduled_recording" && item.from,
    );
  }, [door]);

  // HS-175 C2: a refused Cancel is named on its row (A.10 plain reason),
  // never swallowed; a success clears any earlier refusal for that row.
  const [cancelRefusals, setCancelRefusals] = useState<Record<string, string>>({});
  const cancelArmedRecording = useCallback(async (recordingId: string) => {
    const result = await useDesk.getState().cancelArmedSchedule(recordingId);
    setCancelRefusals((prev) => {
      const next = { ...prev };
      if (result.ok) delete next[recordingId];
      else next[recordingId] = result.reason;
      return next;
    });
    void apiFetch<DoorProjection>("/api/door").then(setDoor).catch(() => null);
  }, []);

  // HS-175 C5: Unlink on the event row -- DELETE /api/calendar/events/{id}/link
  // (the route writes the receipt); the ROOM token leaves with the link.
  const [unlinkRefusals, setUnlinkRefusals] = useState<Record<string, string>>({});
  const [busyUnlink, setBusyUnlink] = useState<string | null>(null);
  const unlinkRoom = useCallback(async (eventId: string) => {
    setBusyUnlink(eventId);
    try {
      await apiFetch(`/api/calendar/events/${encodeURIComponent(eventId)}/link`, {
        method: "DELETE",
      });
      setUnlinkRefusals((prev) => {
        const next = { ...prev };
        delete next[eventId];
        return next;
      });
      const fresh = await apiFetch<DoorProjection>("/api/door").catch(() => null);
      if (fresh) setDoor(fresh);
    } catch (err) {
      setUnlinkRefusals((prev) => ({ ...prev, [eventId]: readableError(err) }));
    } finally {
      setBusyUnlink(null);
    }
  }, []);

  /* PHILO-13-11 (C1, slice two) — the Chair composed of windows (design
     §5, boards C1-1, C1-4a–e, C1-6a): the Arrival's sections move,
     unchanged, into four DeskWindowFrame windows. The work first (R3): the
     Needs-you window leads with the number, the ranking strip and the
     actions; SETUP drops below the actions.
     PHILO-14 A1 (board A-1, RATIFIED 2026-10-07): the Chair IS the screen
     of objects; the four windows open from it, the Dock and Window ▸ Chair.
     The Phase-13 tiles are PARKED in ChairDesk (`data-layout="tiles"`). */
  return (
    <ChairDesk
      screen={<Screen />}
      needs={
        <>
          {/* ── Headline ── */}
          <div className="arrival-headline" data-testid="arrival-headline">
            <h1
              className={headlineAccent ? "arrival-display arrival-display--accent" : "arrival-display arrival-display--muted"}
              data-testid="arrival-display"
            >
              {headline}
            </h1>
            {next ? (
              <p className="arrival-next" data-testid="arrival-next">{next}</p>
            ) : null}
            {/* HS-200-15: the head token row: the ranking key stated on the
                face (a real filter strip, one tap per class), the coverage
                chip when coverage is complete, the calendar state. One
                wrapping line: nothing here ever scrolls sideways. */}
            {unmutedItems.length > 0 || coverageChip || (!next && !calendarConfigured) ? (
              <div className="arrival-head-tokens" data-testid="arrival-head-tokens">
                {/* The strip stays while a row is listed: a desk that only
                    waits on others still reaches its WAITING rows. */}
                {unmutedItems.length > 0 ? (
                  <FilterTokens
                    className="arrival-ranking"
                    label="Ranking"
                    value={rankFilter}
                    onChange={(next) => setRankFilter(next as "" | RankClass)}
                    options={[
                      { value: "", label: "RANKED" },
                      ...RANK_CLASSES.map((cls) => ({ value: cls, label: RANK_LABEL[cls] })),
                    ]}
                  />
                ) : null}
                {coverageChip ? (
                  <StateChip
                    state="success"
                    icon="●"
                    label={coverageChip}
                    data-testid="arrival-coverage-complete"
                  />
                ) : null}
                {checkedToken ? (
                  <span className="arrival-checked-token" data-testid="arrival-checked">
                    {checkedToken}
                  </span>
                ) : null}
                {!next && !calendarConfigured ? (
                  <span className="arrival-next" data-testid="arrival-no-calendar">
                    <span className="arrival-no-calendar-token">NO CALENDAR</span>
                    {" "}
                    <Button
                      variant="ghost"
                      dense
                      onClick={() => openSurfaceOr("configure-settings", "/settings", "meetings")}
                      data-testid="arrival-connect-calendar"
                    >
                      Connect calendar
                    </Button>
                  </span>
                ) : null}
              </div>
            ) : null}
            {isArming ? (
              <p className="arrival-arming" data-testid="arrival-arming">
                <span className="arrival-arming-token">ARMED</span>
                {" "}
                <span>{arming.title || "Scheduled recording"}</span>
                {" "}
                <span className="arrival-arming-countdown">IN {Math.floor(countdown! / 60)}:{String(countdown! % 60).padStart(2, "0")}</span>
                {" "}
                <Button
                  variant="danger"
                  dense
                  onClick={() => void useDesk.getState().cancelArmedSchedule(arming.scheduleId)}
                  data-testid="arrival-cancel-armed"
                >
                  Cancel
                </Button>
              </p>
            ) : null}
          </div>

          {/* ── Coverage (HS-200-07 / C4): what was NOT observed ──
              HS-200-15: ABOVE the answer, as the library CoverageLedger; one
              row per unreadable source with its reason, its token, its
              observation time and its owning verb. */}
          {!coverage.complete ? (
            <div data-testid="arrival-coverage">
              <SurfaceSection label={coverage.token ?? "COVERAGE"}>
                <CoverageLedger
                  gaps={coverage.gaps}
                  onRepair={repairCoverage}
                  now={now}
                  rowTestId="arrival-coverage-row"
                />
              </SurfaceSection>
            </div>
          ) : null}

          {/* ── Needs You (unmuted): five in the first view, the rest behind
              `N MORE · Show all` ── */}
          {unmutedItems.length > 0 ? (
            <div data-testid="arrival-needs-you">
              <NeedsYouSection
                items={unmutedItems}
                filter={rankFilter}
                multipleProjects={multipleProjects}
                now={now}
                onProposalConfirm={handleProposalConfirm}
                onOpenProject={openProject}
                onCommitmentChanged={() => void readNeedsYou(true)}
              />
            </div>
          ) : null}

          {/* ── Muted (dimmed, under a MUTED caption; A8: count pre-extracted) ── */}
          {mutedCount > 0 ? (
            <div data-testid="arrival-muted" className="arrival-muted-section">
              <NeedsYouSection
                items={mutedItems}
                filter={rankFilter}
                multipleProjects={multipleProjects}
                now={now}
                muted
                onProposalConfirm={handleProposalConfirm}
                onOpenProject={openProject}
                onCommitmentChanged={() => void readNeedsYou(true)}
              />
            </div>
          ) : null}

          {/* ── The one thing the meeting path needs (HS-201-01) ──
              ONE row, ONE library Button, and it is gone the moment an
              engine is assigned to the summary capability. */}
          {blockers.length > 0 ? (
            <div data-testid="arrival-blocker">
              <SurfaceSection label="SETUP">
                <SurfaceLedger count={null} cols="room">
                  {blockers.map((blocker) => (
                    <SurfaceLedgerRow
                      key={blocker.key}
                      primary={blocker.label}
                      trailing={
                        // HS-201-01 (full-suite fallout): the SETUP verb is
                        // the library Button, never a second FILLED primary.
                        // The ratified face law is one filled primary on a
                        // face with attention work and ZERO on a quiet one
                        // (test_hs200_attention_glass.py:463, :694), and the
                        // first attention row's Open owns it.
                        <Button
                          dense
                          onClick={
                            blocker.key === "unknown"
                              ? () => void readAssignments()
                              : () => openSurfaceOr("open-concierge", "/models")
                          }
                          data-testid={`arrival-blocker-verb-${blocker.key}`}
                        >
                          {blocker.verb}
                        </Button>
                      }
                      expands={false}
                      wrap
                      data-testid="arrival-blocker-row"
                    />
                  ))}
                </SurfaceLedger>
              </SurfaceSection>
            </div>
          ) : null}

        </>
      }
      brief={
        <>
          {/* ── Brief (M-2: no-brief-yet generates; existing brief with human items shows) ──
              PHILO-4-01 (ratified canvas): every branch carries the head verbs
              (`briefVerbs`: the badge, then Generate) and one status slot. */}
          {briefLoading && !brief ? (
            /* PHILO-3-03 (ratified canvas, state 2): the read is open.
               PHILO-4-01 board 2b: Generate is in the head, disabled. */
            <div data-testid="arrival-brief">
              <SurfaceSection label="BRIEF" actions={briefVerbs}>
                <span className="surface-receipt-line" role="status" data-testid="arrival-brief-loading">
                  READING…
                </span>
              </SurfaceSection>
            </div>
          ) : briefLoadFailed && !brief ? (
            /* PHILO-3-03 (ratified canvas, state 3): the read failed. Never
               "No brief yet": that is a claim about the hub it did not make.
               PHILO-4-01 boards 3b, 3c: Generate in the head; while a
               generation is open, or after it failed, its line takes the one
               status slot (the read failure and its Retry go). */
            <div data-testid="arrival-brief">
              <SurfaceSection label="BRIEF" actions={briefVerbs}>
                {generateStatus ?? (
                  <span className="arrival-brief-failed">
                    <span
                      className="surface-receipt-line"
                      role="status"
                      data-tone="danger"
                      data-testid="arrival-brief-load-failed"
                    >
                      {`BRIEF DID NOT LOAD · ${briefLoadFailed}`}
                    </span>
                    <Button variant="ghost" dense onClick={readBrief} data-testid="arrival-brief-retry">
                      Retry
                    </Button>
                  </span>
                )}
              </SurfaceSection>
            </div>
          ) : !briefLoading && !brief ? (
            /* PHILO-4-01 boards 6, 6b: GENERATING… or the failure line takes
               the place of `No brief yet`. */
            <div data-testid="arrival-brief">
              <SurfaceSection label="BRIEF" actions={briefVerbs}>
                {briefKept ? (
                  <span
                    className="surface-receipt-line"
                    role="status"
                    data-testid="arrival-brief-receipt"
                  >
                    {briefKept}
                  </span>
                ) : generateStatus ?? (
                  <span className="arrival-brief-empty">No brief yet</span>
                )}
              </SurfaceSection>
            </div>
          ) : !briefLoading && untriagedBrief.length > 0 ? (
            /* PHILO-4-01 boards 1, 2a, 3a, 4: Generate in the head while rows
               are untriaged. Generate never touches their triage: the next
               brief has new item ids; this brief's shelf stays on it. */
            <div data-testid="arrival-brief">
              <BriefSection
                items={untriagedBrief}
                waiting={needs.count}
                busyId={busyBriefId}
                onShelf={doBriefShelf}
                actions={briefVerbs}
              />
              {brief ? <BriefDate brief={brief} /> : null}
              {/* HS-202-02 (Astra's counsel finding 2) — the receipt lived
                  ONLY under `!brief`, so success replaced the branch that
                  held it and the owner saw no receipt at all. Article III
                  wants the receipt AFTER the click, wherever the click
                  leaves the face. */}
              {briefKept ? (
                <span
                  className="surface-receipt-line"
                  role="status"
                  data-testid="arrival-brief-receipt"
                >
                  {briefKept}
                </span>
              ) : null}
              {generateStatus}
              {/* PHILO-11-05a (canvas A, T3): the brief's SEND well. Keyed, so the
                  same well (its pick, its receipt) stays when the last item is
                  triaged and the Chair changes branch below. */}
              {brief ? <BriefSendWells key="brief-send" brief={brief} /> : null}
            </div>
          ) : !briefLoading && brief ? (
            /* A brief with nothing untriaged still happened — tonight, or on a
               day before this reload. The section survives with the brief's own
               words (its headline: "No changes" is a result, not an absence),
               the receipt when this gesture made it, and the verb to make
               another. The owner's first sitting (2026-09-21) met the previous
               shape: Generate answered, the whole row vanished, and a reload
               showed nothing at all — "one day later, still no brief".
               PHILO-4-01 boards 7a, 7b, 8a, 8b, 9. */
            <div data-testid="arrival-brief">
              <SurfaceSection label="BRIEF" actions={briefVerbs}>
                {brief.headline ? (
                  <span className="arrival-brief-headline" data-testid="arrival-brief-headline">
                    {brief.headline}
                  </span>
                ) : null}
                <BriefDate brief={brief} />
                {handledBriefLine ? (
                  <span
                    className="surface-receipt-line"
                    data-testid="arrival-brief-handled"
                  >
                    {handledBriefLine}
                  </span>
                ) : null}
                {briefKept ? (
                  <span
                    className="surface-receipt-line"
                    role="status"
                    data-testid="arrival-brief-receipt"
                  >
                    {briefKept}
                  </span>
                ) : null}
                {generateStatus}
              </SurfaceSection>
              <BriefSendWells key="brief-send" brief={brief} />
            </div>
          ) : null}

        </>
      }
      week={
        <>
          {/* ── Week Strip (HS-175-02) ── */}
          {week && week.has_calendar && week.total > 0 ? (
            <WeekStripSection week={week} />
          ) : null}

          {/* ── Calendar Meetings (HS-175-02) ── */}
          {/* P2-14 / counsel re-read: the calendar section wears its own
              testid; the recorded-meetings ledger below keeps `arrival-meetings`. */}
          {calendarEvents.length > 0 ? (
            <div data-testid="arrival-this-week">
              <CalendarMeetingsSection
                events={calendarEvents}
                onCancel={cancelArmedRecording}
                onUnlink={unlinkRoom}
                busyUnlink={busyUnlink}
                cancelRefusals={cancelRefusals}
                unlinkRefusals={unlinkRefusals}
              />
            </div>
          ) : null}

          {/* ── Orphan Armed Recordings (HS-175-02) ── */}
          {orphanRecordings.length > 0 ? (
            <div data-testid="arrival-orphan-section">
              {orphanRecordings.map((rec) => (
                <OrphanArmedRow
                  key={rec.id}
                  recording={rec}
                  onCancel={cancelArmedRecording}
                  refusal={cancelRefusals[rec.id]}
                />
              ))}
            </div>
          ) : null}

          {/* ── Meetings ── */}
          {meetings.length > 0 ? (
            <div data-testid="arrival-meetings">
              <MeetingsSection
                meetings={meetings}
                details={meetingDetails}
                runningIntel={runningIntel}
                intelReceipt={intelReceipt}
                intelRefusal={intelRefusal}
                drainerAbsent={drainerAbsent}
                onRunIntel={runIntelligence}
              />
            </div>
          ) : null}

          {/* ── Thoughts ── */}
          {thoughts.length > 0 ? (
            <div data-testid="arrival-thoughts">
              <ThoughtsSection thoughts={thoughts} />
            </div>
          ) : null}

          {/* ── PHILO-15-09 (B07): the decisions and the due action items
              of this week, and the calendar offer. The week is never an
              empty window. ── */}
          <WeekDeskSection
            decisions={deskDecisions ?? []}
            door={door}
            calendarConfigured={calendarConfigured}
            othersShown={
              (week?.has_calendar === true && week.total > 0) ||
              calendarEvents.length > 0 ||
              orphanRecordings.length > 0 ||
              meetings.length > 0 ||
              thoughts.length > 0
            }
          />

          {/* ── Agents: PARKED (PHILO-14 C4). The arrival's AGENTS section
              folded into the Conductor drawer (`desk/conductor/`): the
              screen's agent objects and the Conductor carry every live
              session. `AgentsSection` below is kept, unrendered. ── */}

        </>
      }
      capture={
        <>
          {/* ── Capture Bar ── */}
          <div
            data-testid="arrival-aftercare-slot"
            data-aftercare-slot="before-capture"
          />
          <CaptureBar />
        </>
      }
    />
  );
}

// ── Sections ───────────────────────────────────────────────────────

function NeedsYouSection({
  items,
  filter = "",
  multipleProjects,
  now,
  muted = false,
  onProposalConfirm,
  onOpenProject,
  onCommitmentChanged,
}: {
  /** The ranked rows (already deduplicated). */
  items: NeedsYouItem[];
  /** The active class of the ranking strip; "" = the full key. */
  filter?: "" | RankClass;
  multipleProjects: boolean;
  now: Date;
  muted?: boolean;
  onProposalConfirm?: (proposalId: string) => void;
  onOpenProject: (projectId: string) => void;
  onCommitmentChanged?: () => void;
}) {
  // HS-200-15 (verdict Q1): five in the first view; the rest reveal IN
  // PLACE behind `N MORE · Show all`. The caption carries the cap
  // (`ACTIONS 5 OF 17`); the display line above carries the true total.
  // PHILO-13-03: the list is narrower than "needs you" (no SETUP row, no
  // failed meeting), so it says what it counts.
  const [showAll, setShowAll] = useState(false);
  const remainderRef = useRef<HTMLButtonElement>(null);
  useEffect(() => { setShowAll(false); }, [filter]);

  // Owner ruling 2026-10-04: a row he waits on someone else for shows only
  // under the WAITING filter. RANKED lists what the headline counts.
  const filtered = filter
    ? items.filter((item) => rankClassOf(item, now) === filter)
    : items.filter((item) => !item.waiting);
  const visible = showAll ? filtered : filtered.slice(0, ATTENTION_CAP);
  // What the cap hides (the remainder row stays while expanded, as the
  // way back).
  const remaining = Math.max(0, filtered.length - ATTENTION_CAP);
  const label = muted ? "MUTED" : "ACTIONS";

  // Escape inside the revealed rows returns focus to the remainder verb.
  const onKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Escape" && showAll) {
      event.stopPropagation();
      setShowAll(false);
      window.setTimeout(() => remainderRef.current?.focus(), 0);
    }
  };

  // Every row waits on someone else: RANKED has no row and draws no section.
  if (filtered.length === 0 && !filter) return null;

  return (
    <SurfaceSection label={attentionCaption(visible.length, filtered.length, label)}>
      {filtered.length === 0 && filter ? (
        <span className="arrival-needs-you-none" data-testid="arrival-needs-you-none">
          NOTHING {RANK_LABEL[filter]}
        </span>
      ) : (
        <div onKeyDown={onKeyDown} data-testid={muted ? "arrival-muted-ledger" : "arrival-needs-you-ledger"}>
          <SurfaceLedger count={null} cols="room">
            {visible.map((item, i) => (
              <NeedsYouRow
                key={item.id ?? `${item.projectId || "door"}-${item.ref || item.proposalId}-${i}`}
                item={item}
                now={now}
                muted={muted}
                // One filled primary per face: the top-ranked row's verb.
                primary={!muted && i === 0}
                multipleProjects={multipleProjects}
                onProposalConfirm={onProposalConfirm}
                onOpenProject={onOpenProject}
                onCommitmentChanged={onCommitmentChanged}
              />
            ))}
          </SurfaceLedger>
          <LedgerRemainder
            ref={remainderRef}
            remaining={remaining}
            expanded={showAll}
            onToggle={() => setShowAll((open) => !open)}
            data-testid={muted ? "arrival-muted-remainder" : "arrival-needs-you-remainder"}
          />
        </div>
      )}
    </SurfaceSection>
  );
}

/** ONE row grammar at both widths (design D2(b) §5): emblem · name ·
 *  reason token · [STILL TRUE · OBSERVED hh:mm] · ProjectButton ·
 *  [N SOURCES] · one verb. At 393 the meta wraps under the name; the
 *  same object, the same verbs, the same rows. */
function NeedsYouRow({
  item,
  now,
  muted,
  primary,
  multipleProjects,
  onProposalConfirm,
  onOpenProject,
  onCommitmentChanged,
}: {
  item: NeedsYouItem;
  now: Date;
  muted: boolean;
  primary: boolean;
  multipleProjects: boolean;
  onProposalConfirm?: (proposalId: string) => void;
  onOpenProject: (projectId: string) => void;
  /** HS-200-13: a commitment's owner or date was written; re-read the aggregate. */
  onCommitmentChanged?: () => void;
}) {
  // The `N SOURCES` body lives in the row's own expansion slot beneath the
  // line (full width at both viewports); the Disclosure is its trigger.
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const sourcesId = `arrival-sources-${(item.id ?? item.ref ?? "").replace(/[^A-Za-z0-9_-]/g, "_")}`;
  // HS-200-13 (counsel P2): a commitment row's `Name an owner` / `Set a
  // date` unfold an in-place well under the row -- no detour, no modal.
  const [commitWell, setCommitWell] = useState<"owner" | "date" | null>(null);
  const [commitDraft, setCommitDraft] = useState("");
  const [commitBusy, setCommitBusy] = useState(false);
  const [commitResult, setCommitResult] = useState<{ owner?: string | null; dueAt?: string | null }>({});
  // An UNASSIGNED Door card that is an action item takes the same well: its
  // own lawful `delegate` verb names the card the owner is written to.
  const doorOwnerCardId = doorDelegateCardId(
    (item as NeedsYouItem & { _doorCard?: DoorCard })._doorCard,
  );
  const commitCardId = item.actionItemId ?? doorOwnerCardId;
  const saveCommit = async () => {
    const value = commitDraft.trim();
    if (!value || !commitCardId || commitBusy) return;
    setCommitBusy(true);
    const verb = commitWell === "owner" ? "delegate" : "due";
    try {
      await apiFetch("/api/follow-through/complete", {
        method: "POST",
        json: { card_id: commitCardId, verb, payload: verb === "delegate" ? { to: value } : { due_at: value } },
      });
      setCommitResult((prev) => (verb === "delegate" ? { ...prev, owner: value } : { ...prev, dueAt: value }));
      setCommitWell(null);
      setCommitDraft("");
      clearWriteFailure(`action-item:${commitCardId}`);
      onCommitmentChanged?.();
    } catch (error) {
      reportWriteFailure(verb === "delegate" ? "Name an owner" : "Set a date", error, () => void saveCommit(), `action-item:${commitCardId}`);
    } finally { setCommitBusy(false); }
  };
  // The row reflects what it just wrote until the arrival re-reads.
  const rowItem: NeedsYouItem = {
    ...item,
    ...(commitResult.owner !== undefined ? { owner: commitResult.owner, unknowns: (item.unknowns ?? []).filter((u) => u !== "owner") } : {}),
    ...(commitResult.dueAt !== undefined ? { dueAt: commitResult.dueAt, unknowns: (item.unknowns ?? []).filter((u) => u !== "due") } : {}),
  };
  if (commitResult.owner !== undefined || commitResult.dueAt !== undefined) {
    rowItem.nextAction = (rowItem.unknowns ?? []).includes("owner") ? "name_owner"
      : (rowItem.unknowns ?? []).includes("due") ? "set_date" : "mark_done";
    if (commitResult.owner) rowItem.why = rowItem.dueAt ? rowItem.why : "DUE · UNKNOWN";
  }
  const ext = item as NeedsYouItem & { _isDoor?: boolean; _isUnassigned?: boolean; _doorCard?: DoorCard };
  const isDoor = ext._isDoor === true;
  // An item that HAS an owner and is not reviewed yet: "To review", never
  // "Name an owner".
  const isToReview = (ext as { _toReview?: boolean })._toReview === true;
  // A Door row that just took an owner is no longer UNASSIGNED. It says who
  // it waits on only until the board is read again; then the hub's own lane
  // names the row (WAITING ON <owner>, or TO REVIEW for an item not reviewed).
  const doorOwnerNamed = isDoor && !item.actionItemId && Boolean(commitResult.owner)
    && !String(item.owner ?? "").trim();
  const isUnassigned = ext._isUnassigned === true && !doorOwnerNamed && !isToReview;
  if (doorOwnerNamed) rowItem.why = `WAITING ON ${String(commitResult.owner).toUpperCase()}`;
  const isProposal = Boolean(item.proposalId);
  const emblem = isDoor ? doorEmblem(item.source) : sourceEmblem(item.source);
  const proposalPrefix = isProposal
    ? (item.proposalKind === "decision" ? "Decide:" : "Confirm:")
    : null;
  const sources = item.sources ?? [];
  const cls = rankClassOf(item, now);
  // The reason token wears the class ink: overdue is danger, due today
  // is warning, the rest muted: severity rides the token, never the order.
  const tone =
    cls === "overdue" ? "failure"
    : cls === "due_today" ? "warning"
    : isProposal ? undefined
    : whySeverityTone(item.severity) === "idle" ? undefined
    : whySeverityTone(item.severity);
  // The cells hold verbs (the Project button, the sources disclosure): a
  // key or click inside them must not reach the row line's own handler.
  const swallow = (event: React.SyntheticEvent) => {
    if (event.target !== event.currentTarget) event.stopPropagation();
  };
  const opener = useNeedsYouOpener(item, ext._doorCard);
  // Conductor F2 (K4a): the item wears its agent where it lives.
  const flight = flightForItem(useAgentFlights((s) => s.flights), {
    ...item, _doorCard: ext._doorCard ?? null,
  });
  if (item.kind === "coder" && item.sessionKey) {
    return <CoderNeedsYouRow item={item} now={now} primary={primary} />;
  }
  return (
    <SurfaceLedgerRow
      // PHILO-13-06 (B1): the row opens its object (a commitment, its person).
      onToggle={opener ?? undefined}
      lead={
        <span className="arrival-source-emblem" data-testid="arrival-source-emblem">
          {emblem}
        </span>
      }
      primary={
        isProposal ? (
          <span data-testid="arrival-proposal-text">
            <span className="arrival-proposal-prefix" data-testid="arrival-proposal-prefix">
              {proposalPrefix}
            </span>{" "}
            {item.title}
            {item.proposalDue ? ` · by ${item.proposalDue}` : null}
          </span>
        ) : item.title
      }
      cells={
        <span
          className="arrival-needs-you-meta"
          onClick={swallow}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") swallow(event);
          }}
        >
          <span
            className="arrival-why-token"
            data-tone={tone}
            data-rank-class={cls}
            data-testid="arrival-why"
          >
            {reasonToken(doorOwnerNamed ? rowItem : item, now)}
          </span>
          <FlightChip flight={flight} />
          {muted ? (
            <span className="arrival-project-token">MUTED</span>
          ) : null}
          {/* HS-200-07 / HS-200-15: a row kept from the last successful
              read of a source that has since failed is STILL TRUE, and
              says when it was observed. */}
          {item.fromLastObservation ? (
            <span
              className="arrival-project-token"
              data-testid="arrival-remembered"
            >
              STILL TRUE · {observedAtToken(item.observedAt, now)}
            </span>
          ) : null}
          {item.projectName && item.projectId ? (
            <ProjectButton
              name={item.projectName}
              withheld={!multipleProjects}
              onOpen={() => onOpenProject(item.projectId)}
              data-testid="arrival-project"
            />
          ) : null}
          {sources.length > 1 ? (
            <Disclosure
              label={countToken(sources.length, "SOURCE", "SOURCES") ?? "SOURCES"}
              ariaLabel={`Sources: ${item.title}`}
              open={sourcesOpen}
              onOpenChange={setSourcesOpen}
              controlsId={sourcesId}
              variant="dense"
            >
              {null}
            </Disclosure>
          ) : null}
        </span>
      }
      trailing={<>
        <NeedsYouRowVerbs
          item={rowItem}
          isDoor={isDoor}
          isUnassigned={isUnassigned}
          isToReview={isToReview}
          doorCard={ext._doorCard}
          ownerCardId={doorOwnerCardId}
          primary={primary}
          onProposalConfirm={onProposalConfirm}
          commitWell={commitWell}
          onCommitWell={(well) => { setCommitDraft(""); setCommitWell(well); }}
        />
        {/* Conductor F2: an item in flight shows its flight and its verb;
            Hand to agent (Conductor K2d) only on an item no agent holds. */}
        {isInFlight(flight)
          ? <FlightVerbs flight={flight} title={item.title} />
          : <HandRowVerb item={item} />}
      </>}
      wrap
      expands={false}
      open={(sourcesOpen && sources.length > 1) || commitWell !== null}
      data-testid={isProposal ? "arrival-proposal-row" : "arrival-needs-you-row"}
    >
      {commitWell ? (
        <div
          className="arrival-commit-well"
          role="region"
          aria-label={`${commitWell === "owner" ? "Owner" : "Due"}: ${item.title}`}
          data-testid="arrival-commit-well"
          onKeyDown={(event) => {
            if (event.key === "Escape") { event.stopPropagation(); setCommitWell(null); }
          }}
        >
          <StringGadget
            label={commitWell === "owner" ? "Owner" : "Due"}
            type={commitWell === "owner" ? "text" : "date"}
            value={commitDraft}
            onChange={setCommitDraft}
            autoFocus
            onKeyDown={(event) => { if (event.key === "Enter") void saveCommit(); }}
          />
          <Button
            dense
            variant="secondary"
            disabled={!commitDraft.trim() || commitBusy}
            aria-label={commitWell === "owner" ? `Save owner: ${item.title}` : `Save date: ${item.title}`}
            data-testid="arrival-commit-save"
            onClick={() => void saveCommit()}
          >
            Save
          </Button>
        </div>
      ) : null}
      {sources.length > 1 ? (
        <div
          id={sourcesId}
          role="region"
          aria-label={`Sources: ${item.title}`}
          onKeyDown={(event) => {
            if (event.key === "Escape") {
              // Close the sources; the Disclosure returns focus to its
              // trigger. The section's own Escape (Show fewer) must not
              // also fire.
              event.stopPropagation();
              setSourcesOpen(false);
            }
          }}
        >
          <ul className="arrival-sources" data-testid="arrival-sources">
            {sources.map((source, i) => (
              <li key={source.id ?? `${source.source}-${i}`} data-testid="arrival-source">
                <span className="arrival-source-emblem">{sourceEmblem(source.source)}</span>
                <span className="arrival-source-title">{source.title || item.title}</span>
                <span className="arrival-why-token">{source.why || source.source.toUpperCase()}</span>
                {source.fromLastObservation ? (
                  <span className="arrival-project-token">
                    STILL TRUE · {observedAtToken(source.observedAt, now)}
                  </span>
                ) : null}
                {/* Every projection keeps its OWN way in (A.11): a
                    swallowed obligation with no verb is a lie. */}
                <SourceVerb source={source} fallbackTitle={item.title} projectId={item.projectId} />
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </SurfaceLedgerRow>
  );
}

/** PHILO-13-06 (B1): what a NEEDS YOU row opens. A commitment opens its
 *  person (the door's mapped relationship, or the aggregate's owner through
 *  the People route); any other door card its own ref; a Room row its
 *  Room. Null = the row names nothing that opens and draws no open. */
function useNeedsYouOpener(item: NeedsYouItem, card?: DoorCard): Opener | null {
  const isCommitment = item.source === "commitment" && Boolean(item.actionItemId);
  const owner = isCommitment ? (item.owner ?? "").trim() : "";
  const [ownerPerson, setOwnerPerson] = useState<string | null>(null);
  useEffect(() => {
    setOwnerPerson(null);
    if (!owner) return;
    let live = true;
    void resolveOwner(owner).then((id) => { if (live) setOwnerPerson(id); });
    return () => { live = false; };
  }, [owner]);
  if (card) {
    const person = card.target_ref?.startsWith("people:")
      ? card.target_ref
      : card.person_relationship_id
        ? `people:${card.person_relationship_id}`
        : null;
    return refOpener(person) ?? refOpener(card.open_ref) ?? refOpener(card.target_ref);
  }
  if (isCommitment) return ownerPerson ? refOpener(`people:${ownerPerson}`) : null;
  // A decision that waits for review opens its own window.
  if (item.source === "decision") return refOpener(item.openRef);
  // Conductor R1: a held tool call of a launch opens the system shade, where
  // the held call is listed with Approve and Deny.
  if (item.source === "gate") return refOpener(item.openRef);
  // PHILO-14 A2b (Astra r1): a proposal is an object; its row opens the
  // Room with that proposal selected (the drawer does not hold proposals).
  const projectId = item.projectId;
  const proposalId = item.proposalId;
  if (proposalId && projectId) return () => openProjectProposal(projectId, proposalId);
  // A row that names only its Project opens the drawer.
  return projectId ? () => openDrawer(projectId) : null;
}

/** The one verb of a constituent projection inside the `N SOURCES`
 *  disclosure: `Open` on its own URL, or on its proposal in the Room. */
function SourceVerb({
  source,
  fallbackTitle,
  projectId,
}: {
  source: AttentionSource;
  fallbackTitle: string;
  projectId?: string;
}) {
  const title = source.title || fallbackTitle;
  const proposalId = source.id?.startsWith("proposal:") ? source.id.slice("proposal:".length) : null;
  if (source.verbHref) {
    return (
      <Button
        variant="ghost"
        dense
        onClick={() => window.open(source.verbHref!, "_blank", "noopener")}
        aria-label={`Open: ${title}`}
        data-testid="arrival-source-open"
      >
        Open
      </Button>
    );
  }
  // A proposal lives in the Room (the drawer lists no proposals): the
  // explicit Room verb, with the proposal selected.
  if (proposalId && projectId) {
    return (
      <Button
        variant="ghost"
        dense
        onClick={() => openProjectProposal(projectId, proposalId)}
        aria-label={`Room: ${title}`}
        data-testid="arrival-source-open"
      >
        Room
      </Button>
    );
  }
  return null;
}

/** The action item an UNASSIGNED Door card writes an owner to: the card of
 *  its lawful `follow_through.complete` / `delegate` verb, or null. */
function doorDelegateCardId(card?: DoorCard): string | null {
  for (const verb of card?.lawful_verbs ?? []) {
    if (verb.arguments?.verb === "delegate") {
      const id = verb.arguments.card_id;
      return id ? String(id) : null;
    }
  }
  return null;
}

/** Verb buttons for a NEEDS YOU row: door lawful verb (primary dense) + Open (ghost),
 *  or proposal Confirm + Open, or "Name an owner" for unassigned, or external Open. */
function NeedsYouRowVerbs({
  item,
  isDoor,
  isUnassigned,
  isToReview,
  doorCard,
  primary = false,
  onProposalConfirm,
  commitWell = null,
  onCommitWell,
  ownerCardId = null,
}: {
  item: NeedsYouItem;
  isDoor: boolean;
  isUnassigned: boolean;
  isToReview?: boolean;
  doorCard?: DoorCard;
  /** The action item an UNASSIGNED Door card can write an owner to. */
  ownerCardId?: string | null;
  /** HS-200-15: ONE filled primary per face: the top-ranked row's verb. */
  primary?: boolean;
  onProposalConfirm?: (proposalId: string) => void;
  /** HS-200-13: the row's open in-place well (owner / date) and its toggle. */
  commitWell?: "owner" | "date" | null;
  onCommitWell?: (well: "owner" | "date" | null) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const lead = primary ? "primary" : "ghost";

  // HS-200-13 (AC3/AC4): a commitment row carries ONE lawful next action.
  // `Mark done` is the explicit act (receipted by the service); naming an
  // owner or setting a date happens on the Desk memory face, where the
  // well unfolds under the row -- never here as a modal.
  if (item.source === "commitment" && item.actionItemId) {
    const next = item.nextAction
      ?? (item.unknowns?.includes("owner") ? "name_owner"
        : item.unknowns?.includes("due") ? "set_date" : "mark_done");
    const label = next === "name_owner" ? "Name an owner" : next === "set_date" ? "Set a date" : "Mark done";
    const markDone = async () => {
      if (busy) return;
      setBusy(true);
      try {
        await apiFetch("/api/follow-through/complete", {
          method: "POST",
          json: { card_id: item.actionItemId, verb: "done", payload: {} },
        });
        setDone(true);
        // PHILO-13-03: the membership changed; the bell and the Dock follow.
        void refreshNeedsYou(true);
        clearWriteFailure(`action-item:${item.actionItemId}`);
      } catch (error) {
        reportWriteFailure("Mark done", error, () => void markDone(), `action-item:${item.actionItemId}`);
      } finally { setBusy(false); }
    };
    if (done) return null;
    // Counsel P2 ruling: no detour.  `Name an owner` / `Set a date` unfold
    // the row's own well (the expansion slot beneath the line); `Mark done`
    // is the row's act.
    return (
      <Button
        variant={lead}
        dense
        disabled={busy}
        aria-label={`${label}: ${item.title}`}
        aria-expanded={next !== "mark_done" ? Boolean(commitWell) : undefined}
        data-testid="arrival-commitment-verb"
        data-next-action={next}
        onClick={() => {
          if (next === "mark_done") { void markDone(); return; }
          onCommitWell?.(commitWell ? null : next === "name_owner" ? "owner" : "date");
        }}
      >
        {busy ? "..." : label}
      </Button>
    );
  }

  // A decision that waits for the owner's review: the same Review verb, on
  // the decision's own window (`openRef` is its Desk route token).
  if (item.source === "decision" && item.openRef) {
    return (
      <Button
        variant={lead}
        dense
        onClick={() => refOpener(item.openRef)?.()}
        aria-label={`Review: ${item.title}`}
        data-testid="arrival-to-review"
      >
        Review
      </Button>
    );
  }

  if (isToReview) {
    return (
      <Button
        variant={lead}
        dense
        onClick={() => {
          // The real producer's card names itself in `target_ref`
          // (`action_item:<id>`, DoorService._follow_through_card); `open_ref`
          // is optional. Review opens the card in Follow-through, where the
          // owner reviews it.
          (refOpener(doorCard?.open_ref) ?? refOpener(doorCard?.target_ref))?.();
        }}
        aria-label={`Review: ${item.title}`}
        data-testid="arrival-to-review"
      >
        Review
      </Button>
    );
  }

  if (isUnassigned) {
    // The verb unfolds the row's owner well when the card can take an owner,
    // or opens the card's own object. With neither it is withheld (A.11):
    // a verb that does nothing is not drawn.
    const openRef = doorCard?.open_ref;
    if (!ownerCardId && !openRef) return null;
    return (
      <Button
        variant={lead}
        dense
        onClick={() => {
          if (ownerCardId) onCommitWell?.(commitWell ? null : "owner");
          else if (openRef) useDesk.getState().openPullout(openRef);
        }}
        aria-label={`Name an owner: ${item.title}`}
        aria-expanded={ownerCardId ? Boolean(commitWell) : undefined}
        data-testid="arrival-name-owner"
      >
        Name an owner
      </Button>
    );
  }

  if (item.proposalId) {
    const confirmProposal = async () => {
      if (busy) return;
      setBusy(true);
      try {
        await apiFetch(
          `/api/proposals/${encodeURIComponent(item.proposalId!)}/confirm`,
          { method: "POST" },
        );
        setDone(true);
        onProposalConfirm?.(item.proposalId!);
        clearWriteFailure(`proposal:${item.proposalId}`);
      } catch (error) {
        reportWriteFailure("Confirm", error, () => void confirmProposal(), `proposal:${item.proposalId}`);
      }
      finally { setBusy(false); }
    };
    if (done) return null;
    // One verb per row (design D1): `Confirm` on the row, `Open` inside
    // the row's MORE disclosure.
    return (
      <>
        <Button
          variant={lead}
          dense
          disabled={busy}
          onClick={() => void confirmProposal()}
          aria-label={`Confirm: ${item.title}`}
          data-testid="arrival-proposal-confirm"
        >
          {busy ? "..." : "Confirm"}
        </Button>
        <Disclosure label="MORE" ariaLabel={`More: ${item.title}`}>
          {/* The proposal lives in the Room (the drawer lists no proposals):
              the explicit Room verb, with the proposal selected. */}
          <Button
            variant="ghost"
            dense
            onClick={() => openProjectProposal(item.projectId, item.proposalId ?? "")}
            aria-label={`Room: ${item.title}`}
            data-testid="arrival-proposal-open"
          >
            Room
          </Button>
        </Disclosure>
      </>
    );
  }

  if (isDoor && doorCard) {
    const verbs = (doorCard.lawful_verbs ?? []).filter(supportsDoorVerb);
    const firstVerb = verbs[0];
    const openRef = doorCard.open_ref;

    const fireVerb = async () => {
      if (!firstVerb || busy) return;
      const cmd = commandForDoorVerb(firstVerb);
      if (!cmd) return;
      setBusy(true);
      try {
        await apiFetch(cmd.endpoint, { method: "POST", json: cmd.body });
        setDone(true);
        // PHILO-13-03: a Done changes the membership; one fresh re-read moves
        // the Chair, the bell and the Dock together (no minute lag).
        void refreshNeedsYou(true);
        clearWriteFailure(`door:${cmd.endpoint}`);
      } catch (error) {
        reportWriteFailure(labelFor(firstVerb), error, () => void fireVerb(), `door:${cmd.endpoint}`);
      }
      finally { setBusy(false); }
    };

    if (done) return null;
    return (
      <>
        {firstVerb ? (
          <Button
            variant={lead}
            dense
            disabled={busy}
            onClick={() => void fireVerb()}
            aria-label={`${labelFor(firstVerb)}: ${item.title}`}
            data-testid="arrival-door-verb"
          >
            {busy ? "..." : labelFor(firstVerb)}
          </Button>
        ) : null}
        {openRef ? (
          <Button
            variant="ghost"
            dense
            onClick={() => useDesk.getState().openPullout(openRef)}
          >
            Open
          </Button>
        ) : null}
      </>
    );
  }

  if (item.verbHref) {
    return (
      <Button
        variant={lead}
        dense
        onClick={() => window.open(item.verbHref!, "_blank", "noopener")}
        aria-label={`Open: ${item.title}`}
        data-testid="arrival-open"
      >
        Open
      </Button>
    );
  }

  return null;
}

/** PHILO-15-09 (B07): the local week, Monday 00:00 to the next Monday. */
function localWeek(now = new Date()): { start: number; end: number } {
  const start = new Date(now.getFullYear(), now.getMonth(), now.getDate() - ((now.getDay() + 6) % 7));
  const end = new Date(start.getFullYear(), start.getMonth(), start.getDate() + 7);
  return { start: start.getTime(), end: end.getTime() };
}

/** A due value as a local instant: a bare date is that local day. */
function dueTime(due: string | null | undefined): number {
  const text = String(due ?? "").trim();
  const day = /^(\d{4})-(\d{2})-(\d{2})$/.exec(text);
  if (day) return new Date(Number(day[1]), Number(day[2]) - 1, Number(day[3])).getTime();
  const at = wireDate(text);
  return at ? at.getTime() : NaN;
}

/** PHILO-15-09 (B07): what the desk knows for this week, beside the
 *  calendar. The decisions made this week and the action items due by its
 *  end (an overdue one too); with no calendar, one row offers to connect
 *  one. A week with nothing says so: never an empty window. */
function WeekDeskSection({
  decisions,
  door,
  calendarConfigured,
  othersShown,
}: {
  decisions: readonly { id: string; title: string; status: string; createdAt: string }[];
  door: DoorProjection | null;
  calendarConfigured: boolean;
  othersShown: boolean;
}) {
  const { start, end } = localWeek();
  const decided = decisions.filter((d) => {
    if (d.status === "superseded" || d.status === "deprecated") return false;
    const at = wireDate(d.createdAt)?.getTime() ?? NaN;
    return at >= start && at < end;
  });
  const seen = new Set<string>();
  const due: DoorCard[] = [];
  for (const column of ["overdue", "now", "waiting", "unassigned"]) {
    for (const card of door?.board?.[column] ?? []) {
      const at = dueTime(card.due);
      if (Number.isNaN(at) || at >= end || seen.has(card.id)) continue;
      seen.add(card.id);
      due.push(card);
    }
  }
  due.sort((a, b) => dueTime(a.due) - dueTime(b.due));
  const nothing = !othersShown && decided.length === 0 && due.length === 0;
  return (
    <>
      {!calendarConfigured ? (
        <p className="arrival-next" data-testid="week-no-calendar">
          <span className="arrival-no-calendar-token">NO CALENDAR</span>
          {" "}
          <Button
            variant="ghost"
            dense
            aria-label="Connect calendar"
            onClick={() => openSurfaceOr("configure-settings", "/settings", "meetings")}
            data-testid="week-connect-calendar"
          >
            Connect
          </Button>
        </p>
      ) : nothing ? (
        <p className="arrival-next" data-testid="week-nothing">
          <span className="arrival-no-calendar-token">NOTHING THIS WEEK</span>
        </p>
      ) : null}
      {decided.length > 0 ? (
        <div data-testid="week-decisions">
          <SurfaceSection label={countLabel("DECISIONS", decided.length)}>
            <SurfaceLedger count={null} cols="room">
              {decided.map((d) => (
                <SurfaceLedgerRow
                  key={d.id}
                  primary={String(d.title ?? "").trim() || "Untitled decision"}
                  cells={
                    <span className="arrival-thought-state">
                      {d.status === "proposed" ? "PROPOSED" : "DECIDED"}
                    </span>
                  }
                  onToggle={() => useDesk.getState().openPullout(d.id)}
                  expands={false}
                  data-testid="week-decision-row"
                />
              ))}
            </SurfaceLedger>
          </SurfaceSection>
        </div>
      ) : null}
      {due.length > 0 ? (
        <div data-testid="week-due">
          <SurfaceSection label={countLabel("DUE", due.length)}>
            <SurfaceLedger count={null} cols="room">
              {due.map((card) => {
                const at = dueTime(card.due);
                const late = at < new Date(new Date().setHours(0, 0, 0, 0)).getTime();
                const open = refOpener(card.open_ref || card.target_ref);
                return (
                  <SurfaceLedgerRow
                    key={card.id}
                    primary={String(card.title || card.text || "Untitled action")}
                    cells={
                      <span className="arrival-thought-state">
                        {late ? "OVERDUE" : `DUE ${ledgerDate(new Date(at).toISOString())}`}
                      </span>
                    }
                    onToggle={open ? () => open() : undefined}
                    expands={false}
                    data-testid="week-due-row"
                  />
                );
              })}
            </SurfaceLedger>
          </SurfaceSection>
        </div>
      ) : null}
    </>
  );
}

function ThoughtsSection({ thoughts }: { thoughts: UnfinishedThought[] }) {
  return (
    <SurfaceSection label={countLabel("THOUGHTS", thoughts.length)}>
      <SurfaceLedger count={null} cols="room">
        {thoughts.map((thought, i) => {
          const stateLabel = continuityLabels[thought.continuity_state] ?? "Continue";
          const isFirst = i === 0;
          // Omit the state token when it says the same as the verb
          // ("CONTINUE" beside "Continue" is the name said twice).
          const showStateToken = stateLabel !== "Continue";
          return (
            <SurfaceLedgerRow
              key={thought.id}
              primary={thought.title.trim() || "Untitled thought"}
              cells={
                showStateToken ? (
                  <span className="arrival-thought-state" data-testid="arrival-thought-state">
                    {stateLabel.toUpperCase()}
                  </span>
                ) : null
              }
              trailing={
                isFirst ? (
                  <Button
                    variant="primary"
                    dense
                    onClick={() =>
                      useDesk.getState().openPullout(`note:${thought.working_note_id}`)
                    }
                  >
                    Continue
                  </Button>
                ) : null
              }
              onToggle={() =>
                useDesk.getState().openPullout(`note:${thought.working_note_id}`)
              }
              expands={false}
              data-testid="arrival-thought-row"
            />
          );
        })}
      </SurfaceLedger>
    </SurfaceSection>
  );
}

/** Cap: the arrival shows at most 3 brief rows + a "N more" verb. */
const BRIEF_CAP = 3;

function BriefSection({
  items,
  waiting,
  busyId,
  onShelf,
  actions,
}: {
  items: BriefItem[];
  /** The hub's one needs-you count (`desk.needs_you`): the number the bell,
   *  the Chair head and the Brief headline say. The caption never counts the
   *  Brief's own rows (changed and broke rows are not waiting). */
  waiting: number;
  busyId: string | null;
  onShelf: (id: string, state: "acknowledged" | "deferred") => void;
  /** PHILO-4-01: the head verbs (the badge, then Generate). */
  actions?: ReactNode;
}) {
  const visible = items.slice(0, BRIEF_CAP);
  const overflow = items.length - visible.length;
  const waitingToken = countToken(waiting, "THING WAITING", "THINGS WAITING");

  return (
    <SurfaceSection
      label={waitingToken ? `BRIEF · ${waitingToken}` : "BRIEF"}
      actions={actions}
    >
      <SurfaceLedger count={null} cols="room">
        {visible.map((item) => (
          <SurfaceLedgerRow
            key={item.id}
            primary={item.text}
            // PHILO-13-06 (B1): the row opens the object it names.
            onToggle={refOpener(item.source_ref) ?? undefined}
            trailing={
              <>
                <Button
                  variant="ghost"
                  dense
                  disabled={busyId === item.id}
                  onClick={() => onShelf(item.id, "acknowledged")}
                >
                  Ack
                </Button>
                <Button
                  variant="ghost"
                  dense
                  disabled={busyId === item.id}
                  onClick={() => onShelf(item.id, "deferred")}
                >
                  Defer
                </Button>
              </>
            }
            expands={false}
            wrap
            data-testid="arrival-brief-row"
          />
        ))}
      </SurfaceLedger>
      {overflow > 0 ? (
        <Button
          variant="ghost"
          dense
          onClick={() => openIntelligence({ view: "brief" })}
          data-testid="arrival-brief-more"
        >
          {overflow} more
        </Button>
      ) : null}
    </SurfaceSection>
  );
}

function ArrivalMeetingWells({
  meeting,
  error,
  receipt,
}: {
  meeting: Meeting | null;
  error: string | null;
  receipt: ReturnType<typeof executedReceipt>;
}) {
  if (error) {
    return (
      <SurfaceWell head="SUMMARY · READ FAILED">
        <span className="arrival-meeting-read-error" data-testid="arrival-detail-error">
          {error}
        </span>
        <span
          className="arrival-meeting-status-fact"
          data-testid="arrival-detail-retained"
        >
          MEETING SAVED
        </span>
      </SurfaceWell>
    );
  }
  if (!meeting) return null;
  const summary = String(meeting.intelSummary ?? "").trim();
  const job = meeting.intelJob;
  const badge = arrivalIntelBadge(meeting);
  // PHILO-6-01 round 2 (Astra's check on built, finding 2): the well names
  // WHAT failed. A failed import is not a failed summary: its well head is
  // IMPORT and its cause line is the import's (the worker's
  // `intel_status_detail`, meeting_service.py `_set_import_status`).
  const importFailed =
    badge === "FAILED" &&
    job?.status !== "failed" &&
    String(meeting.intelStatus ?? "").toLowerCase() === "import_failed";
  const wellHead = importFailed ? "IMPORT" : "SUMMARY";
  const cause = importFailed ? meeting.intelStatusDetail : job?.lastError;
  const hasFailureFact = badge === "RETRYING" || badge === "FAILED" || Boolean(job?.lastError);
  const statusFacts = [
    hasFailureFact ? badge : "",
    hasFailureFact && job?.attempts && job.attempts > 0 && receipt
      ? `LAST ATTEMPT · ${egressFor(receipt.attempts[receipt.attempts.length - 1]?.host ?? "").label}`
      : "",
    cause ? `LAST ERROR · ${cause}` : "",
  ].filter(Boolean);
  const hasStatusFacts = statusFacts.length > 0;
  const factsLine = (
    <div className="arrival-meeting-status-facts" data-testid="arrival-summary-status">
      {statusFacts.map((fact, index) => (
        <span
          key={`${fact}-${index}`}
          className="arrival-meeting-status-fact"
          data-tone={fact === "FAILED" || fact.startsWith("LAST ERROR") ? "danger" : undefined}
        >
          {fact}
        </span>
      ))}
    </div>
  );
  const segments = (meeting.segments ?? []).map((segment) => ({
    speaker: segment.speaker,
    text: segment.text,
    start_time: segment.startedAt,
  }));
  return (
    <>
      {summary ? (
        // PHILO-15-03: the slab owns the summary; the Chair composes it once
        // and hands it the run's facts, never a second copy of the text.
        <MeetingSummarySlab
          intel={{ summary, topics: meeting.intelTopics ?? [] }}
          receipt={receipt}
          facts={hasStatusFacts ? factsLine : null}
        />
      ) : hasStatusFacts ? (
        <SurfaceWell head={<span data-testid="arrival-status-well-head">{wellHead}</span>}>
          {factsLine}
        </SurfaceWell>
      ) : null}
      {/* PHILO-11-05 (canvas C6b): the meeting's SEND well under its summary,
          in both branches that show one (the healthy slab and the retained
          summary with status facts). No summary, no well (C4). */}
      {summary ? (
        <MeetingSendWellLazy meetingId={meeting.id} title={meeting.title} startedAt={meeting.startedAt} />
      ) : null}
      {segments.length > 0 ? (
        <TranscriptWell
          id={meeting.id}
          segments={segments}
          defaultOpen={false}
          wordCount={meeting.transcriptWords}
        />
      ) : null}
    </>
  );
}

function MeetingsSection({
  meetings,
  details,
  runningIntel,
  intelReceipt,
  intelRefusal,
  drainerAbsent,
  onRunIntel,
}: {
  meetings: Meeting[];
  details: Record<string, ArrivalMeetingDetail>;
  runningIntel: string | null;
  intelReceipt: { meetingId: string; drainer: string } | null;
  /** HS-201-04 — the hub's 409 on the last run gesture, with its row. */
  intelRefusal: { meetingId: string; refusal: SummaryRefusal } | null;
  /** The `runtime_queue` frame says no hub drainer will execute the queue. */
  drainerAbsent: boolean;
  onRunIntel: (id: string, route: PlannedRoute | null) => void;
}) {
  // Sort by startedAt descending, limit to 3.
  const sorted = [...meetings]
    .sort((a, b) => new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime())
    .slice(0, 3);
  // HS-201-04 (Astra's counsel round 2; one filled primary per face): the
  // same rule the ledger keeps. Two summary-ready meetings on the arrival
  // drew two filled `Run summary` verbs; only the top-most that can run
  // wears the filled species.
  const leadRunId =
    sorted.find(
      (m) => {
        const row = details[m.id]?.meeting ?? m;
        return arrivalIntelBadge(row) === "OFF" &&
          !summaryStored(row, m) &&
          ((row.segments?.length ?? 0) > 0 ||
            (row.transcriptWords != null && row.transcriptWords > 0)) &&
          routeReady(row.plannedRoute ?? null);
      },
    )?.id ?? null;

  return (
    <SurfaceSection label={countLabel("MEETINGS", sorted.length)}>
      <SurfaceLedger count={null} cols="room">
        {sorted.map((m) => {
          const detailState = details[m.id];
          const rowMeeting = detailState?.meeting ?? m;
          const receipt = intelReceipt?.meetingId === m.id ? intelReceipt : null;
          // HS-200-42 (counsel F1): the honest surface is the BADGE. The verb
          // label could never carry the drainer fact: the moment a receipt
          // exists the row is no longer OFF and the verb leaves the DOM (the
          // story-42 walk shot both worlds and got identical pixels). A queued
          // job with nothing to execute it says so here, in the badge species'
          // own vocabulary.
          const serverBadge = arrivalIntelBadge(rowMeeting);
          const badge = receipt
            ? receipt.drainer === "running"
              ? "QUEUED"
              : "NOT DRAINING"
            : serverBadge === "QUEUED" && drainerAbsent
              ? "NOT DRAINING"
              : serverBadge;
          const hasTranscript =
            (rowMeeting.segments?.length ?? 0) > 0 ||
            (rowMeeting.transcriptWords != null && rowMeeting.transcriptWords > 0);
          const isOff = badge === "OFF";
          // PHILO-13-04 (A3): OFF names the run switch. A meeting that holds
          // a summary says so, never OFF above its own summary (J2-02).
          // PHILO-13-11 (A3-W ledger): the verb follows the SAME stored fact
          // as the badge (the list row's `has_summary`, H-A3 #729, or the
          // summary the detail read): no `Run summary` beside SUMMARY STORED.
          const stored = isOff && summaryStored(rowMeeting, m);
          const shownBadge = stored ? "SUMMARY STORED" : badge;
          const isComplete = badge === "RAN" || badge === "SAVED";
          // HS-201-04 (Article III): the route this row's Run WILL use,
          // read before the click; the refusal's fresh route wins.
          const rowRefusal =
            intelRefusal?.meetingId === m.id ? intelRefusal.refusal : null;
          const route = rowRefusal?.route ?? rowMeeting.plannedRoute ?? m.plannedRoute ?? null;
          const canRun = routeReady(route);
          return (
            <SurfaceLedgerRow
              key={m.id}
              time={ledgerDate(m.startedAt)}
              primary={m.title || "Meeting with no title"}
              cells={
                <>
                  {durationMin(rowMeeting.durationSeconds) ? (
                    <span className="arrival-meeting-duration">
                      {durationMin(rowMeeting.durationSeconds)}
                    </span>
                  ) : null}
                  {rowMeeting.transcriptWords != null && rowMeeting.transcriptWords > 0 ? (
                    <span className="arrival-meeting-duration">
                      {`${rowMeeting.transcriptWords} WORDS`}
                    </span>
                  ) : null}
                  {badge === "RAN" ? (
                    <StateChip state="success" label="RAN" icon="●" />
                  ) : (
                    <span
                      className="arrival-meeting-badge"
                      data-badge={shownBadge.toLowerCase().replace(/\s+/g, "-")}
                      data-testid="arrival-meeting-badge"
                    >
                      {shownBadge}
                    </span>
                  )}
                  {/* After the run: the destinations actually contacted. */}
                  <RunAttempts
                    receipt={executedReceipt(
                      m.id,
                      rowRefusal?.receipt,
                      rowMeeting.runReceipt,
                      rowMeeting.intelJob?.runReceipt,
                    )}
                    testId="arrival-attempts"
                  />
                  <RefusalToken
                    refusal={rowRefusal}
                    durable={rowMeeting.lastRefusal ?? null}
                    testId="arrival-refusal"
                  />
                </>
              }
              trailing={
                isOff && hasTranscript && !stored ? (
                  <>
                    {/* Before the click: where this run will go. */}
                    <RouteDisclosure route={route} testId="arrival-route" />
                    {/* UX-CANON A.11: withheld when nothing can run. */}
                    {canRun ? (
                      <Button
                        variant={m.id === leadRunId ? "primary" : "ghost"}
                        dense
                        disabled={runningIntel === m.id}
                        onClick={() => onRunIntel(m.id, route)}
                        data-testid="arrival-run-intel"
                      >
                        {/* In flight: the same label, disabled. Nothing is
                            queued until the route answers 2xx, and the badge
                            says the rest. */}
                        Run summary
                      </Button>
                    ) : null}
                  </>
                ) : isComplete || stored ? (
                  <Button
                    variant="ghost"
                    dense
                    onClick={() =>
                      openSurfaceOr("review-meetings", "/meetings", `meeting:${m.id}`)
                    }
                    data-testid="arrival-meeting-open"
                  >
                    Open
                  </Button>
                ) : null
              }
              onToggle={() =>
                openSurfaceOr("review-meetings", "/meetings", `meeting:${m.id}`)
              }
              open={Boolean(detailState)}
              expands={false}
              wrap
              children={
                <ArrivalMeetingWells
                  meeting={detailState?.meeting ?? null}
                  error={detailState?.error ?? null}
                  receipt={executedReceipt(
                    m.id,
                    rowRefusal?.receipt,
                    rowMeeting.runReceipt,
                    rowMeeting.intelJob?.runReceipt,
                  )}
                />
              }
              data-testid="arrival-meeting-row"
            />
          );
        })}
      </SurfaceLedger>
    </SurfaceSection>
  );
}

// ── Agents (M-3) — PARKED (PHILO-14 C4) ───────────────────────────
// Unrendered: the Conductor drawer (`desk/conductor/`) lists the agents.
// Kept whole, nothing deleted (CLAUDE.md: park, never delete).

/** Conductor F2 (K4c): the item a session works on, as its row names it. */
function originWord(title: string): string {
  return title;
}

function AgentsSection({ sessions }: { sessions: CoderSessionRow[] }) {
  const blocked = sessions.filter((row) => row.blocked);
  const running = sessions.filter((row) => !row.blocked);
  const ordered = [...blocked, ...running];

  return (
    <SurfaceSection label={countLabel("AGENTS", ordered.length)}>
      <SurfaceLedger count={null} cols="room">
        {ordered.map((row) => {
          const key = row.key;
          const rowBlocked = row.blocked;
          const flight = row.flight;
          return (
            <SurfaceLedgerRow
              key={key}
              primary={row.name}
              cells={
                flight ? (
                  <span className="arrival-agent-flight" data-testid="arrival-agent-flight">
                    <StateChip
                      state={rowBlocked ? "warning" : "working"}
                      label={`${agentWord(row.agent)} · ${rowBlocked ? "WAITING" : "WORKING"}`}
                    />
                    <span className="surface-token" data-testid="arrival-agent-origin" title={flight.title}>
                      ↳ {originWord(flight.title)}
                    </span>
                  </span>
                ) : (
                  <span className="arrival-meeting-badge" data-badge={rowBlocked ? "off" : "saved"}>
                    {rowBlocked ? "BLOCKED" : "RUNNING"}
                  </span>
                )
              }
              trailing={
                rowBlocked ? (
                  <Button
                    variant="primary"
                    dense
                    onClick={() => openCoderSession(key, { answer: true })}
                  >
                    Answer
                  </Button>
                ) : (
                  <Button
                    variant="ghost"
                    dense
                    onClick={() => openCoderSession(key)}
                  >
                    Open
                  </Button>
                )
              }
              onToggle={() => openCoderSession(key)}
              expands={false}
              data-testid="arrival-agent-row"
            />
          );
        })}
      </SurfaceLedger>
    </SurfaceSection>
  );
}

/** Conductor F2 (K5a): the Needs you row of an agent that waits (R5, TO
 *  ANSWER / TO APPROVE). The question, `CLAUDE CODE · WAITING · <age>`, the
 *  Project of the item it works on; `Speak answer` (the session window,
 *  its steer composer recording) and `Open`. */
function CoderNeedsYouRow({ item, now, primary }: { item: NeedsYouItem; now: Date; primary: boolean }) {
  const key = String(item.sessionKey);
  const agent = String(item.agent ?? key.split(":", 1)[0]);
  const session = useAgentFlights((s) => s.sessions.find((row) => row.key === key));
  const flights = useAgentFlights((s) => s.flights);
  const flight = session?.flight ?? flights.find((f) => f.sessionKey === key) ?? null;
  const name = agentWord(agent);
  const projectId = flight?.projectId || item.projectId || "";
  const projectName = flight?.projectName || (item.projectId ? item.projectName : "") || "";
  const speak = () => openCoderSession(key, { answer: true });
  return (
    <SurfaceLedgerRow
      onToggle={() => openCoderSession(key)}
      lead={
        <span className="arrival-source-emblem" data-testid="arrival-source-emblem">
          {agent === "codex" ? "CX" : "CC"}
        </span>
      }
      primary={<span data-testid="arrival-coder-question">{item.question || item.title}</span>}
      cells={
        <span className="arrival-needs-you-meta">
          <span className="arrival-why-token" data-tone="warning" data-testid="arrival-why">
            {`${name} · WAITING · ${coderAgeWord(item, now)}`}
          </span>
          {projectId && projectName ? (
            <ProjectButton
              name={projectName}
              onOpen={() => openDrawer(projectId)}
              data-testid="arrival-project"
            />
          ) : null}
        </span>
      }
      trailing={
        <>
          <Button
            dense
            variant={primary ? "primary" : "ghost"}
            aria-label={`Speak answer: ${name === "CODEX" ? "Codex" : "Claude Code"}`}
            data-testid="arrival-speak-answer"
            onClick={speak}
          >
            Speak answer
          </Button>
          <Button
            dense
            variant="ghost"
            aria-label={`Open: ${name === "CODEX" ? "Codex" : "Claude Code"} session`}
            data-testid="arrival-coder-open"
            onClick={() => openCoderSession(key)}
          >
            Open
          </Button>
        </>
      }
      wrap
      expands={false}
      data-testid="arrival-coder-row"
    />
  );
}

/** How long the agent has waited: `JUST NOW`, `<n> MIN`, `<n> H`. */
export function coderAgeWord(item: { since?: string | null; waitStartedAt?: string | null; ageSeconds?: number | null }, now: Date): string {
  const stamp = Date.parse(String(item.waitStartedAt || item.since || ""));
  const seconds = Number.isFinite(stamp)
    ? Math.max(0, Math.floor((now.getTime() - stamp) / 1000))
    : Math.max(0, Number(item.ageSeconds ?? 0));
  if (seconds < 60) return "JUST NOW";
  if (seconds < 3600) return `${Math.floor(seconds / 60)} MIN`;
  return `${Math.floor(seconds / 3600)} H`;
}

// ── Week Strip (HS-175-02) ─────────────────────────────────────────

/** The strip counts the WEEK'S SHAPE -- every event Mon-Sun including those
 *  already past; dots == total, always. The MEETINGS section lists what is
 *  STILL COMING this week and its count == its rows. Those are two honest
 *  facts; a mismatch between them on a Thursday is not a defect.
 *  (Ruling: coordinator, 2026-09-05.) */
function WeekStripSection({ week }: { week: WeekStripData }) {
  const today = todayDateStr();
  // MON-FRI always; SAT/SUN appended only when count > 0.
  const days = week.days.filter((_d, i) => i < 5 || _d.count > 0);

  return (
    <div className="arrival-week-strip" data-testid="arrival-week-strip">
      <div className="arrival-week-days">
        {days.map((d) => {
          const isToday = d.date === today;
          return (
            <div
              key={d.dow}
              className="arrival-week-day"
              data-today={isToday || undefined}
            >
              <div className="arrival-week-dots">
                {d.count > 0 && d.count <= 4
                  ? Array.from({ length: d.count }, (_, i) => (
                      <span
                        key={i}
                        className="arrival-week-dot"
                        data-testid="arrival-week-dot"
                      />
                    ))
                  : d.count > 4
                    ? (
                        // The design: five or more reads exactly `5+`.
                        <span
                          className="arrival-week-overflow"
                          data-testid="arrival-week-overflow"
                          data-count={d.count}
                        >
                          5+
                        </span>
                      )
                    : null}
              </div>
              <span className="arrival-week-day-label">{d.dow}</span>
            </div>
          );
        })}
      </div>
      <span className="arrival-week-total" data-testid="arrival-week-total">
        {countToken(week.total, "MEETING THIS WEEK", "MEETINGS THIS WEEK")}
      </span>
    </div>
  );
}

// ── Calendar Meetings (HS-175-02) ─────────────────────────────────

function CalendarMeetingsSection({
  events,
  onCancel,
  onUnlink,
  busyUnlink,
  cancelRefusals,
  unlinkRefusals,
}: {
  events: UpcomingItem[];
  onCancel: (recordingId: string) => void;
  onUnlink: (eventId: string) => void;
  busyUnlink: string | null;
  cancelRefusals: Record<string, string>;
  unlinkRefusals: Record<string, string>;
}) {
  // Ruling B10 (2026-09-05): captioned THIS WEEK, not MEETINGS -- the
  // recorded-meetings ledger already owns MEETINGS (UX-CANON D one grammar
  // per object; A.7 said once). The strip says N MEETINGS THIS WEEK; the
  // brief's section is THIS WEEK too. Count unchanged.
  return (
    <SurfaceSection label={countLabel("THIS WEEK", events.length)}>
      <SurfaceLedger count={null} cols="room">
        {events.map((ev) => {
          const recordingId = ev.armed?.recording_id;
          const isRecording = ev.armed?.state === "recording";
          const cancelRefusal = recordingId ? cancelRefusals[recordingId] : undefined;
          const unlinkRefusal = unlinkRefusals[ev.id];
          return (
            <SurfaceLedgerRow
              key={ev.id}
              time={formatEventTime(ev.starts_at)}
              primary={ev.title || "Untitled event"}
              // PHILO-13-06 (B1): its person at Prep, else its Room.
              onToggle={calendarOpener(ev) ?? undefined}
              cells={
                <>
                  {ev.project_name ? (
                    <>
                      <span className="arrival-meeting-room" data-testid="arrival-meeting-room">
                        ROOM &middot; {ev.project_name.toUpperCase()}
                      </span>
                      {/* HS-175 C5: Unlink beside the ROOM token -- a hover
                          verb at the desk width, visible at the phone width. */}
                      <span className="arrival-meeting-verbs" onClick={(e) => e.stopPropagation()} onKeyDown={(e) => e.stopPropagation()}>
                        <Button
                          variant="ghost"
                          dense
                          loading={busyUnlink === ev.id}
                          onClick={() => onUnlink(ev.id)}
                          data-testid="arrival-unlink-room"
                        >
                          Unlink
                        </Button>
                      </span>
                    </>
                  ) : null}
                  {unlinkRefusal ? (
                    <span data-testid="arrival-unlink-refused">
                      <StateChip state="failure" label="CAN'T UNLINK" />{" "}<span className="surface-token" data-chip="">{unlinkRefusal}</span>
                    </span>
                  ) : null}
                  {ev.source_label ? (
                    <span className="arrival-meeting-source">
                      {ev.source_label.toUpperCase()}
                    </span>
                  ) : null}
                  {ev.armed && isRecording ? (
                    // HS-175 C2: capture is running -- ARMS would be a lie and
                    // Cancel a dead verb; the meeting's Stop is the honest one.
                    <StateChip state="active" label="RECORDING" icon="●" />
                  ) : ev.armed ? (
                    <StateChip
                      state="success"
                      label={`ARMS ${formatArmsTime(ev.armed.arms_at)}`}
                      icon="●"
                    />
                  ) : null}
                  {cancelRefusal ? (
                    <span data-testid="arrival-cancel-refused">
                      <StateChip state="failure" label="CAN'T CANCEL" />{" "}<span className="surface-token" data-chip="">{cancelRefusal}</span>
                    </span>
                  ) : null}
                </>
              }
              trailing={
                ev.armed && !isRecording ? (
                  <Button
                    variant="ghost"
                    dense
                    onClick={() => onCancel(ev.armed!.recording_id)}
                    data-testid="arrival-cancel-armed"
                  >
                    Cancel
                  </Button>
                ) : null
              }
              expands={false}
              wrap
              data-testid="arrival-meeting-row"
            />
          );
        })}
      </SurfaceLedger>
    </SurfaceSection>
  );
}

// ── Orphan Armed Recording (HS-175-02) ────────────────────────────

function OrphanArmedRow({
  recording,
  onCancel,
  refusal,
}: {
  recording: UpcomingItem;
  onCancel: (recordingId: string) => void;
  /** HS-175 C2: the hub's plain reason when Cancel was refused. */
  refusal?: string;
}) {
  const isRecording = recording.state === "recording";
  return (
    <div className="arrival-orphan-row" data-testid="arrival-orphan-row">
      <span className="arrival-orphan-title">{recording.title}</span>
      {isRecording ? (
        <StateChip state="active" label="RECORDING" icon="●" />
      ) : (
        <StateChip state="success" label="ARMED" icon="●" />
      )}
      <span className="arrival-meeting-time">
        {formatArmsTime(recording.starts_at)}
      </span>
      {recording.from ? (
        <span className="arrival-orphan-from">
          FROM &middot; {recording.from.event_title}
          {recording.from.source_label
            ? ` (${recording.from.source_label.toUpperCase()})`
            : null}
        </span>
      ) : null}
      {refusal ? (
        <span data-testid="arrival-cancel-refused">
          <StateChip state="failure" label="CAN'T CANCEL" />{" "}<span className="surface-token" data-chip="">{refusal}</span>
        </span>
      ) : null}
      <span className="arrival-orphan-spacer" />
      {isRecording ? null : (
        <Button
          variant="ghost"
          dense
          onClick={() => onCancel(recording.id)}
          data-testid="arrival-cancel-armed"
        >
          Cancel
        </Button>
      )}
    </div>
  );
}

// ── Capture Bar ────────────────────────────────────────────────────

function CaptureBar() {
  const [dictating, setDictating] = useState(false);

  const handleMicText = useCallback((text: string) => {
    // Voice commands handled by the MicButton pipeline.
  }, []);

  return (
    <footer className="arrival-capture-bar" data-testid="arrival-capture-bar">
      <span className="arrival-capture-talk">
        <MicButton
          onText={handleMicText}
          label="Talk"
          variant="transport"
          onState={(state) => setDictating(state === "listening")}
        />
      </span>
      {/* HS-202-02 job 3 — this verb opened the Speak dictation router.
          It opens a new note in the Thought window now (HS-201-12's
          face), which is what its name says (04-sober-eye.md rank 3). */}
      <Button
        variant="ghost"
        onClick={() => void openNewThought()}
        data-testid="arrival-develop-thought"
      >
        Write a thought
      </Button>
      <Button
        variant="ghost"
        onClick={() => void useDesk.getState().startRecording()}
        data-testid="arrival-record-meeting"
      >
        Record meeting
      </Button>
      <Button
        variant="ghost"
        onClick={() => useDesk.getState().openScheduleCreate()}
        data-testid="arrival-schedule"
      >
        Schedule
      </Button>
    </footer>
  );
}
