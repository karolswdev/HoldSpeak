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
import {
  SurfaceSection,
  SurfaceLedger,
  SurfaceLedgerRow,
  EgressChip,
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
}

interface NeedsYouPayload {
  count: number;
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

/** Source emblem token: GH for github, J for jira, etc. */
function sourceEmblem(source: string): string {
  const s = source.toLowerCase();
  if (s === "github") return "GH";
  if (s === "jira") return "J";
  if (s === "delta") return "D";
  return s.slice(0, 2).toUpperCase();
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
  // ── needs-you wire ──
  const [needsYou, setNeedsYou] = useState<NeedsYouPayload | null>(null);
  useEffect(() => {
    void apiFetch<NeedsYouPayload>("/api/desk/needs-you").then(setNeedsYou).catch(() => null);
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

  // ── headline ──
  const count = needsYou?.count ?? 0;
  const projectCount = needsYou?.projects?.length ?? 0;
  const headline =
    count > 0
      ? `${count} need you across ${projectCount} ${projectCount === 1 ? "project" : "projects"}`
      : "Nothing needs you";
  const headlineAccent = count > 0;
  const next = needsYou ? nextLine(needsYou.next) : null;

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

  const multipleProjects = projectCount > 1;

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
      </div>

      {/* ── Needs You ── */}
      {count > 0 && needsYou ? (
        <div data-testid="arrival-needs-you">
          <NeedsYouSection
            items={needsYou.items}
            count={count}
            multipleProjects={multipleProjects}
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
}: {
  items: NeedsYouItem[];
  count: number;
  multipleProjects: boolean;
}) {
  return (
    <SurfaceSection label={countLabel("NEEDS YOU", count)}>
      <SurfaceLedger count={null} cols="room">
        {items.map((item, i) => (
          <SurfaceLedgerRow
            key={`${item.projectId}-${item.ref}-${i}`}
            lead={
              <span className="arrival-source-emblem" data-testid="arrival-source-emblem">
                {sourceEmblem(item.source)}
              </span>
            }
            primary={item.title}
            cells={
              <span className="arrival-needs-you-meta">
                <span
                  className="arrival-why-token"
                  data-tone={whySeverityTone(item.severity)}
                  data-testid="arrival-why"
                >
                  {item.why}
                </span>
                {multipleProjects ? (
                  <span className="arrival-project-token">{item.projectName}</span>
                ) : null}
              </span>
            }
            trailing={
              item.verbHref ? (
                <Button
                  variant="ghost"
                  dense
                  onClick={() => {
                    if (item.verbHref) window.open(item.verbHref, "_blank", "noopener");
                  }}
                >
                  Open
                </Button>
              ) : null
            }
            wrap
            expands={false}
            data-testid="arrival-needs-you-row"
          />
        ))}
      </SurfaceLedger>
    </SurfaceSection>
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
          const isSaved = badge === "SAVED";
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
                  <span
                    className="arrival-meeting-badge"
                    data-badge={badge.toLowerCase()}
                    data-testid="arrival-meeting-badge"
                  >
                    {badge}
                  </span>
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
                ) : isSaved ? (
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
    </footer>
  );
}
