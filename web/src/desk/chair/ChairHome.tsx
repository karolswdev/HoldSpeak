// HS-170-04 -- ChairHome: THE ARRIVAL.
// The Tuesday face: one display headline, sections only when populated,
// every verb the library Button, no counters of zero, no sentences.
// The lane vocabulary is PARKED; the arrival composes directly from
// the surface library and the needs-you wire.

import { useCallback, useEffect, useMemo, useState } from "react";
import { Chair } from "./Chair";
import { FirstWords } from "../components/FirstWords";
import { useDesk } from "../store";
import { openSurface, openSurfaceOr, openCoderSession } from "../shell";
import { apiFetch } from "../../lib/api";
import { Button } from "../../components/signal/Signal";
import { MicButton } from "../components/MicButton";
import { intelBadge } from "./intelBadge";
import { labelFor, supportsDoorVerb, commandForDoorVerb } from "./doorVerbs";
import {
  SurfaceSection,
  SurfaceLedger,
  SurfaceLedgerRow,
  EgressChip,
  StateChip,
  countLabel,
  countToken,
} from "../surface";
import { openIntelligence } from "../intelligenceNavigation";
import { unfinishedThoughts, type UnfinishedThought } from "../thoughts";
import type { Meeting } from "../../lib/primitives";

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
}

interface NeedsYouPayload {
  count: number;
  mutedCount?: number;
  projects: string[];
  items: NeedsYouItem[];
  next: { label: string; at: string } | null;
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

interface DoorProjection {
  board: Record<string, DoorCard[]>;
  counts: Record<string, number>;
  upcoming: Array<{ id: string; source: string; title: string; starts_at: string }>;
  calendar_configured: boolean;
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
  return `${Math.round(seconds / 60)} MIN`;
}

/** Source emblem token: GH for github, J for jira, MTG for proposals, etc. */
function sourceEmblem(source: string): string {
  const s = source.toLowerCase();
  if (s === "github") return "GH";
  if (s === "jira") return "J";
  if (s === "delta") return "D";
  if (s === "proposal") return "MTG";
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
      why = "NOW";
      severity = "warning";
    } else if (column === "waiting") {
      why = card.owner ? `WAITING ON ${card.owner.toUpperCase()}` : "WAITING";
      severity = "info";
    } else if (column === "unassigned") {
      why = "UNASSIGNED";
      severity = "warning";
    }
    return {
      projectId: "",
      projectName: "",
      ref: card.id,
      title: card.title || card.text || "Untitled",
      why,
      ageToken: "",
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

/** Headline for the arrival — zero = "Nothing needs you" (UX-CANON A8). */
function headlineFor(count: number, projectCount: number): string {
  if (count <= 0) return "Nothing needs you";
  const n = String(count);
  if (projectCount > 0) {
    const p = projectCount === 1 ? "project" : "projects";
    return n + " need you across " + String(projectCount) + " " + p;
  }
  return n + " need you";
}

/** Format NEXT line from the payload. */
function nextLine(next: NeedsYouPayload["next"]): string | null {
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
  return parts.join(" · ");
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
  const [needsYou, setNeedsYou] = useState<NeedsYouPayload | null>(null);
  useEffect(() => {
    void apiFetch<NeedsYouPayload>("/api/desk/needs-you").then(setNeedsYou).catch(() => null);
  }, []);

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
    } catch { /* stays */ }
    finally { setGenerating(false); }
  };

  // ── merge door items into needs-you ──
  const doorItems = useMemo(() => {
    if (!door) return [];
    const board = door.board ?? {};
    // Order: overdue first, then now, then waiting, then unassigned.
    // Active items do not appear.
    return [
      ...doorCardsToItems("overdue", board.overdue ?? []),
      ...doorCardsToItems("now", board.now ?? []),
      ...doorCardsToItems("waiting", board.waiting ?? []),
      ...doorCardsToItems("unassigned", board.unassigned ?? []),
    ];
  }, [door]);

  const roomItems = needsYou?.items ?? [];
  // HS-171: separate muted from unmuted; muted render dimmed at the end.
  const { unmutedItems, mutedItems } = useMemo(() => {
    const SEV: Record<string, number> = { danger: 0, warning: 1, info: 2 };
    const merged = [...doorItems, ...roomItems];
    merged.sort((a, b) => (SEV[a.severity] ?? 2) - (SEV[b.severity] ?? 2));
    const unmuted: NeedsYouItem[] = [];
    const muted: NeedsYouItem[] = [];
    for (const item of merged) {
      if (item.muted) muted.push(item);
      else unmuted.push(item);
    }
    return { unmutedItems: unmuted, mutedItems: muted };
  }, [doorItems, roomItems]);

  // ── headline: uses the wire's count (excludes muted) + door items ──
  const count = (needsYou?.count ?? 0) + doorItems.length;
  const projectCount = needsYou?.projects?.length ?? 0;
  const hasProjects = projectCount > 0;
  const headline = headlineFor(count, projectCount);
  const headlineAccent = count > 0;
  const mutedCount = mutedItems.length > 0 ? mutedItems.length : 0;

  // ── NEXT line: prefer door upcoming (schedule/calendar), fall back to rooms ──
  const doorNext = door?.upcoming?.[0];
  const nextPayload = doorNext
    ? { label: doorNext.title, at: doorNext.starts_at }
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
    } catch { /* row stays */ }
    finally { setBusyBriefId(null); }
  };

  // ── intel run (S-2: response carries host for the egress chip) ──
  const [runningIntel, setRunningIntel] = useState<string | null>(null);
  const [intelReceipt, setIntelReceipt] = useState<{ meetingId: string; host: string } | null>(null);
  const runIntelligence = async (meetingId: string) => {
    setRunningIntel(meetingId);
    setIntelReceipt(null);
    try {
      const result = await apiFetch<{ jobId: string; state: string; host: string }>(
        `/api/meetings/${encodeURIComponent(meetingId)}/intelligence/run`,
        { method: "POST" },
      );
      setIntelReceipt({ meetingId, host: result.host || "THIS DEVICE" });
      void useDesk.getState().refresh();
    } catch { /* receipt stays */ }
    finally { setRunningIntel(null); }
  };

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
        ) : !calendarConfigured ? (
          <p className="arrival-next" data-testid="arrival-no-calendar">
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
          </p>
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

      {/* ── Needs You (unmuted) ── */}
      {unmutedItems.length > 0 ? (
        <div data-testid="arrival-needs-you">
          <NeedsYouSection
            items={unmutedItems}
            count={count}
            multipleProjects={hasProjects}
            onProposalConfirm={handleProposalConfirm}
          />
        </div>
      ) : null}

      {/* ── Muted (dimmed, under a MUTED caption; A8: count pre-extracted) ── */}
      {mutedCount > 0 ? (
        <div data-testid="arrival-muted" className="arrival-muted-section">
          <NeedsYouSection
            items={mutedItems}
            count={mutedCount}
            multipleProjects={hasProjects}
            muted
            onProposalConfirm={handleProposalConfirm}
          />
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
  count,
  multipleProjects,
  muted = false,
  onProposalConfirm,
}: {
  items: NeedsYouItem[];
  count: number;
  multipleProjects: boolean;
  muted?: boolean;
  onProposalConfirm?: (proposalId: string) => void;
}) {
  return (
    <SurfaceSection label={countLabel(muted ? "MUTED" : "NEEDS YOU", count)}>
      <SurfaceLedger count={null} cols="room">
        {items.map((item, i) => {
          const ext = item as NeedsYouItem & { _isDoor?: boolean; _isUnassigned?: boolean; _doorCard?: DoorCard };
          const isDoor = ext._isDoor === true;
          const isUnassigned = ext._isUnassigned === true;
          const isProposal = Boolean(item.proposalId);
          const emblem = isDoor ? doorEmblem(item.source) : sourceEmblem(item.source);
          const proposalPrefix = isProposal
            ? (item.proposalKind === "decision" ? "Decide:" : "Confirm:")
            : null;
          return (
            <SurfaceLedgerRow
              key={`${item.projectId || "door"}-${item.ref || item.proposalId}-${i}`}
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
                <span className="arrival-needs-you-meta">
                  <span
                    className="arrival-why-token"
                    data-tone={isProposal ? undefined : whySeverityTone(item.severity)}
                    data-testid="arrival-why"
                  >
                    {item.why}
                  </span>
                  {muted ? (
                    <span className="arrival-project-token">MUTED</span>
                  ) : null}
                  {multipleProjects && item.projectName ? (
                    <span className="arrival-project-token">{item.projectName}</span>
                  ) : null}
                </span>
              }
              trailing={
                <NeedsYouRowVerbs
                  item={item}
                  isDoor={isDoor}
                  isUnassigned={isUnassigned}
                  doorCard={ext._doorCard}
                  onProposalConfirm={onProposalConfirm}
                />
              }
              wrap
              expands={false}
              data-testid={isProposal ? "arrival-proposal-row" : "arrival-needs-you-row"}
            />
          );
        })}
      </SurfaceLedger>
    </SurfaceSection>
  );
}

/** Verb buttons for a NEEDS YOU row: door lawful verb (primary dense) + Open (ghost),
 *  or proposal Confirm + Open, or "Name an owner" for unassigned, or external Open. */
function NeedsYouRowVerbs({
  item,
  isDoor,
  isUnassigned,
  doorCard,
  onProposalConfirm,
}: {
  item: NeedsYouItem;
  isDoor: boolean;
  isUnassigned: boolean;
  doorCard?: DoorCard;
  onProposalConfirm?: (proposalId: string) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  if (isUnassigned) {
    return (
      <Button
        variant="ghost"
        dense
        onClick={() => {
          if (doorCard?.open_ref) useDesk.getState().openPullout(doorCard.open_ref);
        }}
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
      } catch { /* row stays */ }
      finally { setBusy(false); }
    };
    if (done) return null;
    return (
      <>
        <Button
          variant="primary"
          dense
          disabled={busy}
          onClick={() => void confirmProposal()}
          data-testid="arrival-proposal-confirm"
        >
          {busy ? "..." : "Confirm"}
        </Button>
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
          data-testid="arrival-proposal-open"
        >
          Open
        </Button>
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
      } catch { /* receipt stays */ }
      finally { setBusy(false); }
    };

    if (done) return null;
    return (
      <>
        {firstVerb ? (
          <Button
            variant="primary"
            dense
            disabled={busy}
            onClick={() => void fireVerb()}
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
        variant="ghost"
        dense
        onClick={() => window.open(item.verbHref!, "_blank", "noopener")}
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

function MeetingsSection({
  meetings,
  runningIntel,
  intelReceipt,
  onRunIntel,
}: {
  meetings: Meeting[];
  runningIntel: string | null;
  intelReceipt: { meetingId: string; host: string } | null;
  onRunIntel: (id: string) => void;
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
          const badge = receipt ? "QUEUED" : intelBadge(m.intelStatus);
          const hasTranscript = m.transcriptWords != null && m.transcriptWords > 0;
          const isOff = badge === "OFF";
          const isComplete = badge === "RAN" || badge === "SAVED";
          return (
            <SurfaceLedgerRow
              key={m.id}
              time={ledgerDate(m.startedAt)}
              primary={m.title || "Untitled meeting"}
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
                      data-badge={badge.toLowerCase()}
                      data-testid="arrival-meeting-badge"
                    >
                      {badge}
                    </span>
                  )}
                  {receipt ? (
                    <EgressChip
                      label={receipt.host === "local" ? "THIS DEVICE" : receipt.host}
                      scope={receipt.host === "local" ? "local" : "cloud"}
                    />
                  ) : null}
                </>
              }
              trailing={
                isOff && hasTranscript ? (
                  <Button
                    variant="primary"
                    dense
                    disabled={runningIntel === m.id}
                    onClick={() => onRunIntel(m.id)}
                    data-testid="arrival-run-intel"
                  >
                    {runningIntel === m.id ? "Running..." : "Run intelligence"}
                  </Button>
                ) : isComplete ? (
                  <Button
                    variant="ghost"
                    dense
                    onClick={() =>
                      openSurfaceOr("review-meetings", "/meetings", m.id)
                    }
                  >
                    Open
                  </Button>
                ) : null
              }
              onToggle={() =>
                openSurfaceOr("review-meetings", "/meetings", m.id)
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
        Develop a thought
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
