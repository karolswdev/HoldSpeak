// HS-170-04 -- ChairHome: THE ARRIVAL.
// The Tuesday face: one display headline, sections only when populated,
// every verb the library Button, no counters of zero, no sentences.
// The lane vocabulary is PARKED; the arrival composes directly from
// the surface library and the needs-you wire.

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Chair } from "./Chair";
import { FirstWords } from "../components/FirstWords";
import { useDesk } from "../store";
import { openSurface, openSurfaceOr, openCoderSession } from "../shell";
import { reportWriteFailure, clearWriteFailure } from "../hooks/useWriteReceipt";
import { apiFetch, readableError } from "../../lib/api";
import { Button } from "../../components/signal/Signal";
import { MicButton } from "../components/MicButton";
import { intelBadge } from "./intelBadge";
import { meetingPathBlockers, type AssignmentRead } from "./meetingPathBlocker";
import { onReturnToTask } from "../returnToTask";
import { getAssignmentSummary, type AssignmentSummary } from "../../pages/cores/assignmentExperience";
import { useRuntimeBus, useRuntimeFrame } from "../../runtime/RuntimeBus";
import { labelFor, supportsDoorVerb, commandForDoorVerb } from "./doorVerbs";
import {
  SurfaceSection,
  SurfaceLedger,
  SurfaceLedgerRow,
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
} from "../surface";
import { openIntelligence } from "../intelligenceNavigation";
import { readCoverage, type CoverageRecord } from "../coverage";
import {
  ATTENTION_CAP,
  RANK_CLASSES,
  RANK_LABEL,
  ageToken,
  attentionCaption,
  dedupAttention,
  observedAtToken,
  rankAttention,
  rankClassOf,
  reasonToken,
  type AttentionSource,
  type RankClass,
} from "../attention";
import { unfinishedThoughts, type UnfinishedThought } from "../thoughts";
import type { Meeting } from "../../lib/primitives";
import {
  RefusalToken,
  RouteDisclosure,
  RunAttempts,
} from "../../meetings/RouteDisclosure";
import { egressFor } from "../surface/egress";
import {
  executedReceipt,
  postSummaryRun,
  routeReady,
  type PlannedRoute,
  type SummaryRefusal,
} from "../../meetings/summaryRoute";

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
}

interface MondayBrief {
  id: string;
  headline: string;
  sections: Record<string, BriefItem[]>;
  is_empty: boolean;
  shelf?: Record<string, string>;
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
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return `${MONTHS[d.getMonth()]} ${String(d.getDate()).padStart(2, "0")}`;
}

function durationMin(seconds: number | null | undefined): string {
  if (!seconds || seconds <= 0) return "";
  // UX-CANON A.8 (Astra's counsel finding 5): a 30-second meeting rounded
  // to `0 MIN` on the Chair. A zero token says nothing, so it is omitted —
  // the same rule the ledger's `durationToken` already keeps.
  const minutes = Math.round(seconds / 60);
  if (minutes <= 0) return "";
  return `${minutes} MIN`;
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

/** Convert door cards to NeedsYouItem-compatible rows for the arrival. */
function doorCardsToItems(
  column: string,
  cards: DoorCard[],
): NeedsYouItem[] {
  return cards.map((card) => {
    let why = "";
    let severity = "info";
    if (column === "overdue") {
      const days = card.due ? Math.max(1, Math.floor((Date.now() - new Date(card.due).getTime()) / 86400000)) : 0;
      why = days > 0 ? `OVERDUE · ${days}D` : "OVERDUE";
      severity = "danger";
    } else if (column === "now") {
      // HS-200-15: the Door's `now` column is what is due now: the
      // DUE TODAY class of the ranking key.
      why = "DUE TODAY";
      severity = "warning";
    } else if (column === "waiting") {
      why = card.owner ? `WAITING ON ${card.owner.toUpperCase()}` : "WAITING";
      severity = "info";
    } else if (column === "unassigned") {
      why = "UNASSIGNED";
      severity = "warning";
    }
    return {
      id: `door:${card.id}`,
      projectId: "",
      projectName: "",
      ref: card.id,
      title: card.title || card.text || "Untitled",
      why,
      ageToken: "",
      since: "",
      dueAt: card.due ?? null,
      source: card.source,
      verbHref: null,
      severity,
      _doorCard: card,
      _isDoor: true,
      _isUnassigned: column === "unassigned",
    } as NeedsYouItem & { _doorCard: DoorCard; _isDoor: boolean; _isUnassigned: boolean };
  });
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
  if (count <= 0) {
    if (pending > 0) return String(pending) + " need you";
    return complete ? "Nothing needs you" : "Coverage incomplete";
  }
  const n = String(count);
  if (projectCount > 1) {
    return n + " need you across " + String(projectCount) + " projects";
  }
  return n + " need you";
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
  const d = new Date(startsAt);
  if (Number.isNaN(d.getTime())) return "";
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
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
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
        <FirstWords
          embedded
          onDismiss={() => useDesk.getState().refresh()}
        />
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
  // ── needs-you wire (rooms) ──
  // HS-200-07 (C4): a read that never landed is itself a coverage gap —
  // the arrival must not speak the all-clear over an answer it lacks.
  const [needsYou, setNeedsYou] = useState<NeedsYouPayload | null>(null);
  const [needsYouUnread, setNeedsYouUnread] = useState(false);
  const readNeedsYou = useCallback(async (fresh = false) => {
    try {
      const data = await apiFetch<NeedsYouPayload>(
        fresh ? "/api/desk/needs-you?fresh=1" : "/api/desk/needs-you",
      );
      setNeedsYou(data);
      setNeedsYouUnread(false);
    } catch {
      setNeedsYouUnread(true);
    }
  }, []);
  useEffect(() => { void readNeedsYou(); }, [readNeedsYou]);

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
  const [briefLoading, setBriefLoading] = useState(true);
  useEffect(() => {
    void apiFetch<MondayBrief | null>("/api/brief/latest")
      .then(setBrief)
      .catch(() => null)
      .finally(() => setBriefLoading(false));
  }, []);

  // ── meetings ──
  const meetings = useDesk((s) => s.items.meeting);

  // ── the meeting-path blockers (HS-201-01) ──
  // The assignment roster, re-read whenever it can have changed. Counsel
  // fix round (Astra finding 1): a mount-only read left the repaired row
  // on an OPEN desk until the owner navigated -- the product knew the
  // path was clear and the face still asked for an engine. So the Chair
  // re-reads on the hub's `desk_changed` frame (the burst is debounced,
  // as `useDeskChangedRefresh` does) and when the window takes focus
  // again (the owner comes back from Models, or from anywhere else).
  // A read that has not landed is an UNKNOWN, never a clear desk.
  const [assignments, setAssignments] = useState<AssignmentSummary | null>(null);
  const [assignmentRead, setAssignmentRead] = useState<AssignmentRead>("pending");
  const readAssignments = useCallback(async () => {
    try {
      const summary = await getAssignmentSummary();
      setAssignments(summary);
      setAssignmentRead("ok");
    } catch {
      setAssignments(null);
      setAssignmentRead("failed");
    }
  }, []);
  useEffect(() => { void readAssignments(); }, [readAssignments]);
  // Counsel round 2 (condition 1): the product's OWN return signal. Models
  // announces `holdspeak:settings-updated` the moment it applies a set
  // (`features/concierge/useConciergeController.ts:507` ->
  // `desk/returnToTask.ts:113`), and every face holding an unfinished task
  // re-reads on it. The Chair is such a face: its SETUP row IS the
  // unfinished task the owner left to repair.
  useEffect(() => onReturnToTask(() => { void readAssignments(); }), [readAssignments]);
  const { subscribe: subscribeFrames } = useRuntimeBus();
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | null = null;
    const unsubscribe = subscribeFrames("desk_changed", () => {
      if (timer !== null) clearTimeout(timer);
      timer = setTimeout(() => { timer = null; void readAssignments(); }, 300);
    });
    const onFocus = () => { void readAssignments(); };
    window.addEventListener("focus", onFocus);
    return () => {
      if (timer !== null) clearTimeout(timer);
      unsubscribe();
      window.removeEventListener("focus", onFocus);
    };
  }, [subscribeFrames, readAssignments]);
  const blockers = useMemo(
    () => meetingPathBlockers(assignments, assignmentRead),
    [assignments, assignmentRead],
  );

  // HS-200-42 (counsel N1): WHO will execute the queue. The `runtime_queue`
  // frame (the same one the ambient HUD chip reads) now carries the hub
  // drainer's state, so "queued with nothing to run it" is a durable fact on
  // the row rather than a sub-second flash of the click receipt. `null` means
  // no frame has arrived yet: unknown, and never reported as absent.
  const queueFrame = useRuntimeFrame<{ drainer?: string }>("runtime_queue");
  const drainerAbsent = queueFrame?.drainer === "absent";

  // ── agents (coders sessions) ──
  const [agentSessions, setAgentSessions] = useState<Record<string, unknown>[]>([]);
  useEffect(() => {
    void apiFetch<Record<string, unknown>>("/api/coders/status")
      .then((res) => {
        const sessions = (res as any)?.agent?.sessions;
        const raw = Array.isArray(sessions)
          ? sessions
          : (sessions as any)?.items;
        if (Array.isArray(raw)) setAgentSessions(raw.filter(Boolean));
      })
      .catch(() => undefined);
  }, []);

  // ── brief generate ──
  const [generating, setGenerating] = useState(false);
  const generateBrief = async () => {
    setGenerating(true);
    try {
      const data = await apiFetch<MondayBrief>("/api/brief/generate", { method: "POST" });
      setBrief(data);
      clearWriteFailure();
    } catch (error) {
      reportWriteFailure("Generate brief", error, () => void generateBrief());
    }
    finally { setGenerating(false); }
  };

  const roomItems = needsYou?.items ?? [];

  // ── merge door items into needs-you ──
  const doorItems = useMemo(() => {
    if (!door) return [];
    const board = door.board ?? {};
    // HS-200-13 (AC3): a commitment the Room already emits as an attention
    // row (source `commitment`, with its Project and its next action) is
    // the same action item the Door's board projects; the Room's row wins
    // and the Door's card for it is not drawn a second time.
    const covered = new Set(
      roomItems
        .filter((item) => item.source === "commitment" && item.actionItemId)
        .map((item) => String(item.actionItemId)),
    );
    // Order: overdue first, then now, then waiting, then unassigned.
    // Active items do not appear.
    return [
      ...doorCardsToItems("overdue", board.overdue ?? []),
      ...doorCardsToItems("now", board.now ?? []),
      ...doorCardsToItems("waiting", board.waiting ?? []),
      ...doorCardsToItems("unassigned", board.unassigned ?? []),
    ].filter((item) => !covered.has(String(item.ref)));
  }, [door, roomItems]);
  // HS-200-15: ONE clock per render for every age and OBSERVED token.
  const now = useMemo(() => new Date(), [needsYou, door]);
  // HS-171: separate muted from unmuted; muted render dimmed at the end.
  // HS-200-15 (AC2, AC3): the merged rows are deduplicated (one obligation,
  // one row, its sources traceable) and RANKED by the five-class key —
  // overdue, due today, not run, no due date, waiting: never by severity.
  const { unmutedItems, mutedItems } = useMemo(() => {
    const merged = rankAttention(dedupAttention([...doorItems, ...roomItems], now), now);
    const unmuted: NeedsYouItem[] = [];
    const muted: NeedsYouItem[] = [];
    for (const item of merged) {
      if (item.muted) muted.push(item);
      else unmuted.push(item);
    }
    return { unmutedItems: unmuted, mutedItems: muted };
  }, [doorItems, roomItems, now]);

  // ── the ranking filter (RANKED = the full key) ──
  const [rankFilter, setRankFilter] = useState<"" | RankClass>("");

  // ── headline: the TRUE total of what the arrival lists (unmuted) ──
  const count = unmutedItems.length;
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
  // meeting-path blocker and every FAILED meeting. `Nothing needs you`
  // is never spoken over one (audits/face-walk-opus.md defect 8).
  const failedMeetings = meetings.filter(
    (m) => intelBadge(m.intelStatus) === "FAILED",
  ).length;
  const pending = blockers.length + failedMeetings;
  // Counsel fix round, second pass (ruling 1): a roster read still in
  // flight draws no row, and the all-clear waits for it -- an unknown is
  // never spoken as a clear desk.
  const headline = headlineFor(
    count,
    projectCount,
    coverage.complete && assignmentRead !== "pending",
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

  const openProject = useCallback((projectId: string) => {
    openSurfaceOr("project-room", "/projects", projectId);
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
    openSurfaceOr("project-room", "/projects", gap.project_id ?? "");
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
  const briefSections = ["changed", "broke", "waiting", "decisions"] as const;
  const briefItems: BriefItem[] = brief && !brief.is_empty
    ? briefSections.flatMap((s) => brief.sections[s] ?? [])
    : [];
  const briefShelf = brief?.shelf ?? {};
  const untriagedBrief = briefItems
    .filter((item) => !briefShelf[item.id])
    .filter((item) => !isRawId(item.text));

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
      clearWriteFailure();
    } catch (error) {
      reportWriteFailure(state === "acknowledged" ? "Acknowledge" : "Defer", error, () => void doBriefShelf(itemId, state));
    }
    finally { setBusyBriefId(null); }
  };

  // ── intel run (S-2: response carries host for the egress chip) ──
  const [runningIntel, setRunningIntel] = useState<string | null>(null);
  // HS-200-42: the receipt carries the DRAINER's state too. The verb
  // enqueues; whether anything executes the queue is a separate fact, and
  // the face must not say "Running..." when the answer is "nothing will".
  const [intelReceipt, setIntelReceipt] = useState<
    { meetingId: string; host: string; drainer: string } | null
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
        clearWriteFailure();
        return;
      }
      setIntelReceipt({
        meetingId,
        host: outcome.route?.legs?.[0]?.host || outcome.result.host || "THIS DEVICE",
        drainer: outcome.result.drainer === "running" ? "running" : "absent",
      });
      void useDesk.getState().refresh();
      clearWriteFailure();
    } catch (error) {
      reportWriteFailure("Run summary", error, () => void runIntelligence(meetingId, route));
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
  const handleProposalConfirm = useCallback((proposalId: string) => {
    setNeedsYou((prev) => {
      if (!prev) return prev;
      const remaining = prev.items.filter((it) => it.proposalId !== proposalId);
      // UX-CANON A8: the headline guards zero; this is state, not display.
      const nextCount = remaining.reduce((n) => n + 1, 0);
      return { ...prev, items: remaining, count: nextCount };
    });
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

  return (
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
        {count > 0 || coverageChip || (!next && !calendarConfigured) ? (
          <div className="arrival-head-tokens" data-testid="arrival-head-tokens">
            {count > 0 ? (
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

      {/* ── Week Strip (HS-175-02) ── */}
      {week && week.has_calendar && week.total > 0 ? (
        <WeekStripSection week={week} />
      ) : null}

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

      {/* ── Thoughts ── */}
      {thoughts.length > 0 ? (
        <div data-testid="arrival-thoughts">
          <ThoughtsSection thoughts={thoughts} />
        </div>
      ) : null}

      {/* ── Brief (M-2: no-brief-yet generates; existing brief with human items shows) ── */}
      {!briefLoading && !brief ? (
        <div data-testid="arrival-brief">
          <SurfaceSection
            label="BRIEF"
            actions={
              <Button
                variant="ghost"
                dense
                disabled={generating}
                onClick={() => void generateBrief()}
                data-testid="arrival-brief-generate"
              >
                {generating ? "Generating..." : "Generate"}
              </Button>
            }
          >
            <span className="arrival-brief-empty">No brief yet</span>
          </SurfaceSection>
        </div>
      ) : !briefLoading && untriagedBrief.length > 0 ? (
        <div data-testid="arrival-brief">
          <BriefSection
            items={untriagedBrief}
            busyId={busyBriefId}
            onShelf={doBriefShelf}
          />
        </div>
      ) : null}

      {/* ── Meetings ── */}
      {meetings.length > 0 ? (
        <div data-testid="arrival-meetings">
          <MeetingsSection
            meetings={meetings}
            runningIntel={runningIntel}
            intelReceipt={intelReceipt}
            intelRefusal={intelRefusal}
            drainerAbsent={drainerAbsent}
            onRunIntel={runIntelligence}
          />
        </div>
      ) : null}

      {/* ── Agents (M-3: only when sessions exist) ── */}
      {agentSessions.length > 0 ? (
        <div data-testid="arrival-agents">
          <AgentsSection sessions={agentSessions} />
        </div>
      ) : null}

      {/* ── Capture Bar ── */}
      <CaptureBar />
    </>
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
  // (`NEEDS YOU 5 OF 17`); the display line above carries the true total.
  const [showAll, setShowAll] = useState(false);
  const remainderRef = useRef<HTMLButtonElement>(null);
  useEffect(() => { setShowAll(false); }, [filter]);

  const filtered = filter
    ? items.filter((item) => rankClassOf(item, now) === filter)
    : items;
  const visible = showAll ? filtered : filtered.slice(0, ATTENTION_CAP);
  // What the cap hides (the remainder row stays while expanded, as the
  // way back).
  const remaining = Math.max(0, filtered.length - ATTENTION_CAP);
  const label = muted ? "MUTED" : "NEEDS YOU";

  // Escape inside the revealed rows returns focus to the remainder verb.
  const onKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Escape" && showAll) {
      event.stopPropagation();
      setShowAll(false);
      window.setTimeout(() => remainderRef.current?.focus(), 0);
    }
  };

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
  const saveCommit = async () => {
    const value = commitDraft.trim();
    if (!value || !item.actionItemId || commitBusy) return;
    setCommitBusy(true);
    const verb = commitWell === "owner" ? "delegate" : "due";
    try {
      await apiFetch("/api/follow-through/complete", {
        method: "POST",
        json: { card_id: item.actionItemId, verb, payload: verb === "delegate" ? { to: value } : { due_at: value } },
      });
      setCommitResult((prev) => (verb === "delegate" ? { ...prev, owner: value } : { ...prev, dueAt: value }));
      setCommitWell(null);
      setCommitDraft("");
      clearWriteFailure();
      onCommitmentChanged?.();
    } catch (error) {
      reportWriteFailure(verb === "delegate" ? "Name an owner" : "Set a date", error, () => void saveCommit());
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
  const isUnassigned = ext._isUnassigned === true;
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
  return (
    <SurfaceLedgerRow
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
            {reasonToken(item, now)}
          </span>
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
      trailing={
        <NeedsYouRowVerbs
          item={rowItem}
          isDoor={isDoor}
          isUnassigned={isUnassigned}
          doorCard={ext._doorCard}
          primary={primary}
          onProposalConfirm={onProposalConfirm}
          commitWell={commitWell}
          onCommitWell={(well) => { setCommitDraft(""); setCommitWell(well); }}
        />
      }
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
                <SourceVerb source={source} fallbackTitle={item.title} />
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </SurfaceLedgerRow>
  );
}

/** The one verb of a constituent projection inside the `N SOURCES`
 *  disclosure: `Open` on its own URL, or on its proposal in the Room. */
function SourceVerb({
  source,
  fallbackTitle,
}: {
  source: AttentionSource;
  fallbackTitle: string;
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
  if (proposalId) {
    return (
      <Button
        variant="ghost"
        dense
        onClick={() => openSurfaceOr("project-room", "/projects", `?focus=proposal:${proposalId}`)}
        aria-label={`Open: ${title}`}
        data-testid="arrival-source-open"
      >
        Open
      </Button>
    );
  }
  return null;
}

/** Verb buttons for a NEEDS YOU row: door lawful verb (primary dense) + Open (ghost),
 *  or proposal Confirm + Open, or "Name an owner" for unassigned, or external Open. */
function NeedsYouRowVerbs({
  item,
  isDoor,
  isUnassigned,
  doorCard,
  primary = false,
  onProposalConfirm,
  commitWell = null,
  onCommitWell,
}: {
  item: NeedsYouItem;
  isDoor: boolean;
  isUnassigned: boolean;
  doorCard?: DoorCard;
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
        clearWriteFailure();
      } catch (error) {
        reportWriteFailure("Mark done", error, () => void markDone());
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

  if (isUnassigned) {
    return (
      <Button
        variant={lead}
        dense
        onClick={() => {
          if (doorCard?.open_ref) useDesk.getState().openPullout(doorCard.open_ref);
        }}
        aria-label={`Name an owner: ${item.title}`}
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
        clearWriteFailure();
      } catch (error) {
        reportWriteFailure("Confirm", error, () => void confirmProposal());
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
          <Button
            variant="ghost"
            dense
            onClick={() =>
              openSurfaceOr(
                "project-room",
                "/projects",
                `${item.projectId}?focus=proposal:${item.proposalId}`,
              )
            }
            aria-label={`Open: ${item.title}`}
            data-testid="arrival-proposal-open"
          >
            Open
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
        clearWriteFailure();
      } catch (error) {
        reportWriteFailure(labelFor(firstVerb), error, () => void fireVerb());
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
  busyId,
  onShelf,
}: {
  items: BriefItem[];
  busyId: string | null;
  onShelf: (id: string, state: "acknowledged" | "deferred") => void;
}) {
  const visible = items.slice(0, BRIEF_CAP);
  const overflow = items.length - visible.length;

  return (
    <SurfaceSection
      label={`BRIEF · ${countToken(items.length, "THING WAITING", "THINGS WAITING") ?? ""}`}
    >
      <SurfaceLedger count={null} cols="room">
        {visible.map((item) => (
          <SurfaceLedgerRow
            key={item.id}
            primary={item.text}
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

/** HS-201-04 — the click's egress receipt, said the ONE way the product
 *  says a host (`egressFor`). Never the raw wire word, never "cloud" by
 *  default (Article III; Astra's counsel finding 4). */
function ReceiptChip({ host }: { host: string }) {
  const eg = egressFor(host);
  if (!eg.label) return null;
  return <EgressChip label={eg.label} scope={eg.scope} />;
}

function MeetingsSection({
  meetings,
  runningIntel,
  intelReceipt,
  intelRefusal,
  drainerAbsent,
  onRunIntel,
}: {
  meetings: Meeting[];
  runningIntel: string | null;
  intelReceipt: { meetingId: string; host: string; drainer: string } | null;
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

  return (
    <SurfaceSection label={countLabel("MEETINGS", sorted.length)}>
      <SurfaceLedger count={null} cols="room">
        {sorted.map((m) => {
          const receipt = intelReceipt?.meetingId === m.id ? intelReceipt : null;
          // HS-200-42 (counsel F1): the honest surface is the BADGE. The verb
          // label could never carry the drainer fact: the moment a receipt
          // exists the row is no longer OFF and the verb leaves the DOM (the
          // story-42 walk shot both worlds and got identical pixels). A queued
          // job with nothing to execute it says so here, in the badge species'
          // own vocabulary.
          const serverBadge = intelBadge(m.intelStatus);
          const badge = receipt
            ? receipt.drainer === "running"
              ? "QUEUED"
              : "NOT DRAINING"
            : serverBadge === "QUEUED" && drainerAbsent
              ? "NOT DRAINING"
              : serverBadge;
          const hasTranscript = m.transcriptWords != null && m.transcriptWords > 0;
          const isOff = badge === "OFF";
          const isComplete = badge === "RAN" || badge === "SAVED";
          // HS-201-04 (Article III): the route this row's Run WILL use,
          // read before the click; the refusal's fresh route wins.
          const rowRefusal =
            intelRefusal?.meetingId === m.id ? intelRefusal.refusal : null;
          const route = rowRefusal?.route ?? m.plannedRoute ?? null;
          const canRun = routeReady(route);
          return (
            <SurfaceLedgerRow
              key={m.id}
              time={ledgerDate(m.startedAt)}
              primary={m.title || "Meeting with no title"}
              cells={
                <>
                  {durationMin(m.durationSeconds) ? (
                    <span className="arrival-meeting-duration">
                      {durationMin(m.durationSeconds)}
                    </span>
                  ) : null}
                  {badge === "RAN" ? (
                    <StateChip state="success" label="RAN" icon="●" />
                  ) : (
                    <span
                      className="arrival-meeting-badge"
                      data-badge={badge.toLowerCase().replace(/\s+/g, "-")}
                      data-testid="arrival-meeting-badge"
                    >
                      {badge}
                    </span>
                  )}
                  {/* HS-201-04 (Astra's counsel finding 4): the click's own
                      receipt goes through the ONE egress mapper the ledger
                      uses. It printed the wire word `same_device` verbatim
                      and called every host but "local" a cloud host. */}
                  {receipt ? <ReceiptChip host={receipt.host} /> : null}
                  {/* After the run: the destinations actually contacted. */}
                  <RunAttempts
                    receipt={executedReceipt(m.id, rowRefusal?.receipt, m.runReceipt)}
                    testId="arrival-attempts"
                  />
                  <RefusalToken
                    refusal={rowRefusal}
                    durable={m.lastRefusal ?? null}
                    testId="arrival-refusal"
                  />
                </>
              }
              trailing={
                isOff && hasTranscript ? (
                  <>
                    {/* Before the click: where this run will go. */}
                    <RouteDisclosure route={route} testId="arrival-route" />
                    {/* UX-CANON A.11: withheld when nothing can run. */}
                    {canRun ? (
                      <Button
                        variant="primary"
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
                ) : isComplete ? (
                  <Button
                    variant="ghost"
                    dense
                    onClick={() =>
                      openSurfaceOr("review-meetings", "/meetings", `meeting:${m.id}`)
                    }
                  >
                    Open
                  </Button>
                ) : null
              }
              onToggle={() =>
                openSurfaceOr("review-meetings", "/meetings", `meeting:${m.id}`)
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

// ── Agents (M-3) ──────────────────────────────────────────────────

/** Blocked predicate (from parked AgentsLane). */
function isBlocked(row: Record<string, unknown>): boolean {
  const session = (row.session as Record<string, unknown> | undefined) ?? row;
  return Boolean(
    session.awaiting_response ?? row.awaiting_response ?? row.state === "waiting",
  );
}

function sessionKey(row: Record<string, unknown>): string {
  const session = (row.session as Record<string, unknown> | undefined) ?? row;
  return String(
    row.key ?? session.key ??
      `${String(session.agent ?? "claude")}:${String(session.session_id ?? "")}`,
  );
}

function sessionName(row: Record<string, unknown>): string {
  const session = (row.session as Record<string, unknown> | undefined) ?? row;
  return String(session.project ?? session.cwd ?? session.session_id ?? "session");
}

function AgentsSection({ sessions }: { sessions: Record<string, unknown>[] }) {
  const blocked = useMemo(() => sessions.filter(isBlocked), [sessions]);
  const running = useMemo(() => sessions.filter((r) => !isBlocked(r)), [sessions]);
  const ordered = [...blocked, ...running];

  return (
    <SurfaceSection label={countLabel("AGENTS", ordered.length)}>
      <SurfaceLedger count={null} cols="room">
        {ordered.map((row) => {
          const key = sessionKey(row);
          const name = sessionName(row);
          const rowBlocked = isBlocked(row);
          return (
            <SurfaceLedgerRow
              key={key}
              primary={name}
              cells={
                <span className="arrival-meeting-badge" data-badge={rowBlocked ? "off" : "saved"}>
                  {rowBlocked ? "BLOCKED" : "RUNNING"}
                </span>
              }
              trailing={
                rowBlocked ? (
                  <Button
                    variant="primary"
                    dense
                    onClick={() => openCoderSession(key)}
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
              cells={
                <>
                  {ev.project_name ? (
                    <>
                      <span className="arrival-meeting-room" data-testid="arrival-meeting-room">
                        ROOM &middot; {ev.project_name.toUpperCase()}
                      </span>
                      {/* HS-175 C5: Unlink beside the ROOM token -- a hover
                          verb at the desk width, visible at the phone width. */}
                      <span className="arrival-meeting-verbs">
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
      <Button
        variant="ghost"
        onClick={() => openSurfaceOr("dictate", "/dictation")}
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
