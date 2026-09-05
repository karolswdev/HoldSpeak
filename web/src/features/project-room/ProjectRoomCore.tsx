// HS-169-03 — the Room rebuilt to the ratified canvas.
// Four questions: What needs me now? What am I watching? What changed
// since I last looked? What did we decide and what do I owe people?
// Two wings: ROOM · HISTORY. Ask well at the foot. No counters of zero,
// no REV, no raw field names, the name said once.
import { useEffect, useRef, useState, useMemo, useCallback } from "react";
import {
  SurfaceFooter,
  SurfaceSection,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceStream,
  SurfaceStreamDay,
  SurfaceStreamEntry,
  ConfirmVerb,
  EgressChip,
  StateChip,
  humanTime,
  streamDayLabel,
  MicButton,
  groundedMatchCount,
  CitationChips,
  Material,
} from "../../desk/surface";
import { useWindowTitle } from "../../desk/surface/title";
import { Button } from "../../components/signal/Signal";
import {
  getAssignmentEditor,
} from "../../pages/cores/assignmentExperience";
import { runAsk, type AskRunResult } from "../../desk/ask";
import { openPrimitive, openSurfaceOr } from "../../desk/shell";
import type { CoreProps } from "../../pages/cores/core-types";
import type {
  RoomSnapshot,
  RoomHealthData,
  RoomTargetData,
  RoomSourceItem,
  RoomChangeRow,
  RoomReviewData,
} from "./model";
import { lifecycleLabel } from "./model";
import { useProjectRoomController } from "./useProjectRoomController";
import { useReviewController } from "./review/useReviewController";
import { ReviewPosture } from "./review/ReviewPosture";
import { useUpdateController } from "./update/useUpdateController";
import { UpdatePosture } from "./update/UpdatePosture";
import { useStewardController } from "./steward/useStewardController";
import { StewardPosture } from "./steward/StewardPosture";
import * as api from "./api";
import "./project-room.css";

/* ── sub-components (kept for backward-compat re-exports) ── */

const PROMOTION_TYPES = [
  ["adr", "ADR"],
  ["note", "NOTE"],
  ["decision_announcement", "ANNC"],
] as const;

export function LifecycleChip({ row }: { row: Record<string, unknown> }) {
  const lifecycle = String(row.lifecycle || "recorded");
  const tone =
    lifecycle === "accepted"
      ? "ok"
      : lifecycle === "rejected"
        ? "danger"
        : undefined;
  return (
    <span className="surface-token" data-tone={tone}>
      {lifecycleLabel(row)}
    </span>
  );
}

export function DecisionPromotionSlot({
  decision,
  onOpenArtifact,
}: {
  decision: Record<string, unknown>;
  onOpenArtifact?(artifactId: string): void;
}) {
  if (String(decision.lifecycle) !== "accepted") return null;
  return null;
}

/* ── provider emblems ── */

const PROVIDER_EMBLEM: Record<string, string> = {
  github: "GH",
  jira: "J",
  meeting: "▣",
  delta: "◇",
  room: "▣",
};

function emblemFor(source: string): string {
  const key = source.toLowerCase();
  return PROVIDER_EMBLEM[key] || source.slice(0, 2).toUpperCase();
}

/* ── time formatting ── */

function formatReadAt(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const days = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${days[d.getDay()]} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function formatTimeShort(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function formatTargetDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const months = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"];
  return `${months[d.getMonth()]} ${d.getDate()}`;
}

/** Local-time YYYY-MM-DD (same derivation as streamDayLabel's sameDay). */
function localDateStr(d: Date): string {
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function maxCheckedAt(items: RoomSourceItem[]): string | null {
  let best: string | null = null;
  for (const item of items) {
    if (item.checkedAt && (!best || item.checkedAt > best)) {
      best = item.checkedAt;
    }
  }
  return best;
}

/* ── severity ── */

function severityTone(severity: string): string | undefined {
  if (severity === "danger") return "danger";
  if (severity === "warning") return "warn";
  return undefined;
}

function severityColor(severity: string): string {
  if (severity === "danger") return "#f87171";
  if (severity === "warning") return "#fbbf24";
  return "var(--text-muted)";
}

/* ── HISTORY: kind->phrase map ── */

const KIND_PHRASE_MAP: Record<string, string> = {
  "project.created": "Created",
  "project.updated": "Updated",
  "project.archived": "Archived",
  "project.restored": "Restored",
  "project.resource.linked": "Resource linked",
  "project.resource.unlinked": "Resource unlinked",
  "item.created": "Item created",
  "item.updated": "Item updated",
  "item.deleted": "Item deleted",
  "watch.activated": "Watch activated",
  "watch.paused": "Watch paused",
  "watch.retired": "Watch retired",
  "watch.evaluated": "Check completed",
  "update.drafted": "Update drafted",
  "update.published": "Update published",
  "steward.run": "Steward ran",
  "review.opened": "Review opened",
  "review.accepted": "Review accepted",
  "decision.recorded": "Decided",
  "decision.accepted": "Decision accepted",
};

export function kindToPhrase(kind: string): string {
  if (KIND_PHRASE_MAP[kind]) return KIND_PHRASE_MAP[kind];
  const last = kind.split(".").pop() || kind;
  return last.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
}

/* ── the Room headline ── */

function RoomHeadline({
  count,
  isAccent,
}: {
  count: number;
  isAccent: boolean;
}) {
  return (
    <span
      className="surface-display room-headline"
      data-testid="room-headline"
      data-accent={isAccent || undefined}
    >
      {count > 0 ? `${count} need you` : "Nothing needs you"}
    </span>
  );
}

/* ── the Room head ── */

function RoomHead({
  room,
  ctrl,
  updateCtrl,
}: {
  room: RoomSnapshot;
  ctrl: ReturnType<typeof useProjectRoomController>;
  updateCtrl: ReturnType<typeof useUpdateController>;
}) {
  const health = room.health.state === "ok" ? (room.health as RoomHealthData & { state: "ok" }) : null;
  const target = room.target.state === "ok" ? (room.target as RoomTargetData & { state: "ok" }) : null;
  const needsYouCount = room.needsYou.state === "ok" ? room.needsYou.count : 0;
  const sources = room.sources.state === "ok" ? room.sources.items : [];
  const checked = maxCheckedAt(sources);

  const nameRef = useRef<HTMLSpanElement>(null);
  const [showOutcome, setShowOutcome] = useState(false);
  useEffect(() => {
    const el = nameRef.current;
    if (!el) return;
    const check = () => {
      const overflows = el.scrollWidth > el.clientWidth;
      const outcome = room.project.outcomeText || room.project.name;
      setShowOutcome(overflows || outcome.length > 80);
    };
    check();
    const ro = new ResizeObserver(check);
    ro.observe(el);
    return () => ro.disconnect();
  }, [room.project.name, room.project.outcomeText]);

  return (
    <div className="room-head" data-testid="room-head">
      <span ref={nameRef} className="room-head-name-measure" aria-hidden="true">
        {room.project.name}
      </span>
      <RoomHeadline count={needsYouCount} isAccent={needsYouCount > 0} />
      {showOutcome ? (
        <p className="room-head-outcome surface-primary" data-testid="room-head-outcome">
          {room.project.outcomeText || room.project.name}
        </p>
      ) : null}
      <div className="room-head-chips" data-testid="room-head-chips">
        {health ? (
          <StateChip
            state={health.assessment === "at_risk" ? "failure" : "success"}
            label={health.assessment === "at_risk" ? "AT RISK" : "ON TRACK"}
            icon={"●"}
          />
        ) : null}
        {health?.reason ? (
          <span className="surface-token room-chip-faint">{health.reason}</span>
        ) : null}
        {target?.targetAt ? (
          <span
            className="surface-token"
            data-testid="room-target-chip"
            data-tone={target.passed ? "danger" : undefined}
          >
            {target.passed
              ? `OVERDUE BY ${Math.abs(target.daysLeft ?? 0)} DAYS`
              : `TARGET ${formatTargetDate(target.targetAt)} · ${target.daysLeft} DAYS`
            }
          </span>
        ) : null}
        {checked ? (
          <span className="surface-token room-chip-faint">CHECKED {humanTime(checked)}</span>
        ) : null}
        {room.project.isArchived ? (
          <StateChip state="failure" label="ARCHIVED" icon={"●"} />
        ) : null}
        <span className="room-head-trailing">
          <Button
            dense
            variant="primary"
            loading={updateCtrl.loading}
            onClick={() => void updateCtrl.enterUpdates()}
            data-testid="updates-verb"
          >
            Draft update
          </Button>
        </span>
      </div>
    </div>
  );
}

/* ── NEEDS YOU section ── */

function NeedsYouSection({
  room,
  ctrl,
  reviewCtrl,
  pendingCount,
}: {
  room: RoomSnapshot;
  ctrl: ReturnType<typeof useProjectRoomController>;
  reviewCtrl: ReturnType<typeof useReviewController>;
  pendingCount: number;
}) {
  if (room.needsYou.state !== "ok") return null;
  const { items, count } = room.needsYou;

  const nextCheck = room.sources.state === "ok" ? room.sources.nextCheckAt : null;

  const reviewAction = pendingCount > 0 ? (
    <Button dense variant="ghost" loading={reviewCtrl.loading} onClick={() => void reviewCtrl.enterReview()} data-testid="review-verb" data-verb="review">
      Review {pendingCount}
    </Button>
  ) : undefined;

  if (items.length === 0) {
    return (
      <SurfaceSection label="NEEDS YOU" actions={reviewAction}>
        <p className="room-empty-line" data-testid="needs-you-empty">
          Nothing needs you{nextCheck ? ` · next check ${formatTimeShort(nextCheck)}` : ""}
        </p>
      </SurfaceSection>
    );
  }

  return (
    <SurfaceSection label={`NEEDS YOU ${count}`} actions={reviewAction}>
      <SurfaceLedger count="" cols="room">
        <ul className="surface-ledger-rows">
          {items.map((item, i) => (
            <SurfaceLedgerRow
              key={`${item.source}-${item.title}-${i}`}
              data-testid="needs-you-row"
              lead={emblemFor(item.source)}
              primary={<span className="surface-primary">{item.title}</span>}
              wrap
              cells={
                <span
                  className="surface-token room-why-token"
                  style={{ color: severityColor(item.severity) }}
                  data-tone={severityTone(item.severity)}
                  data-testid="needs-you-why"
                >
                  {item.why}
                </span>
              }
              trailing={
                item.verb === "decide" ? (
                  <Button dense variant="ghost" onClick={() => {
                    if (item.url) window.open(item.url, "_blank", "noopener");
                  }}>Decide</Button>
                ) : item.url ? (
                  <Button dense variant="ghost" onClick={() => window.open(item.url!, "_blank", "noopener")}>Open</Button>
                ) : null
              }
            />
          ))}
        </ul>
      </SurfaceLedger>
    </SurfaceSection>
  );
}

/* ── SOURCES section ── */

function SourcesSection({
  room,
  onReload,
  stewardCtrl,
}: {
  room: RoomSnapshot;
  onReload: () => void;
  stewardCtrl: ReturnType<typeof useStewardController>;
}) {
  const [busyWatch, setBusyWatch] = useState<string>("");

  if (room.sources.state !== "ok") return null;
  const { items, count } = room.sources;

  const handlePause = async (watchId: string) => {
    setBusyWatch(watchId);
    try { await api.pauseWatch(watchId); onReload(); }
    catch { /* non-fatal */ }
    finally { setBusyWatch(""); }
  };

  const handleResume = async (watchId: string) => {
    setBusyWatch(watchId);
    try { await api.resumeWatch(watchId); onReload(); }
    catch { /* non-fatal */ }
    finally { setBusyWatch(""); }
  };

  const handleRetire = async (watchId: string) => {
    setBusyWatch(watchId);
    try { await api.retireWatch(watchId); onReload(); }
    catch { /* non-fatal */ }
    finally { setBusyWatch(""); }
  };

  const sorted = [...items].sort((a, b) => {
    const order = { live: 0, paused: 1, cant_check: 2 } as Record<string, number>;
    const aOrder = a.suggested ? 3 : (order[a.state] ?? 1);
    const bOrder = b.suggested ? 3 : (order[b.state] ?? 1);
    return aOrder - bOrder;
  });

  return (
    <SurfaceSection
      label={`SOURCES ${count}`}
      actions={
        /* HS-169-07 park candidate: the steward's settings live under the
           sources (D4/D5).  Until per-source Adjust exists, this ghost verb
           is the honest interim entry point to the StewardPosture. */
        <Button dense variant="ghost" loading={stewardCtrl.loading} onClick={() => void stewardCtrl.enterSteward()} data-testid="steward-verb" data-verb="steward">
          Steward
        </Button>
      }
    >
      <SurfaceLedger count="" cols="room">
        <ul className="surface-ledger-rows">
          {sorted.map((src) => {
            if (src.state === "cant_check") {
              return (
                <SurfaceLedgerRow
                  key={src.watchId}
                  lead={emblemFor(src.provider)}
                  primary={<span className="surface-primary">{src.scope}</span>}
                  wrap
                  open
                  expands={false}
                  cells={<StateChip state="warning" label="CAN'T CHECK" />}
                  trailing={
                    <ConfirmVerb
                      label="Remove"
                      confirmLabel="Remove?"
                      busy={busyWatch === src.watchId}
                      onConfirm={() => void handleRetire(src.watchId)}
                    />
                  }
                >
                  {src.plainReason ? (
                    <div className="room-source-line2">
                      <span className="room-source-reason">{src.plainReason}</span>
                    </div>
                  ) : null}
                </SurfaceLedgerRow>
              );
            }

            if (src.suggested) {
              return (
                <SurfaceLedgerRow
                  key={src.watchId}
                  lead={emblemFor(src.provider)}
                  primary={<span className="surface-primary">{src.scope}</span>}
                  wrap
                  cells={<span className="surface-token room-chip-faint">SUGGESTED</span>}
                  trailing={<Button dense variant="ghost">Add</Button>}
                />
              );
            }

            /* LINE 1: emblem . scope (primary) . [gap] . tokens left-aligned . [spacer] . verbs
               LINE 2: checked + host, starting at the scope's left edge.
               The tokens sit INSIDE the primary slot so they follow the scope
               inline, not right-aligned as cells. */
            return (
              <SurfaceLedgerRow
                key={src.watchId}
                lead={emblemFor(src.provider)}
                primary={
                  <span className="room-source-primary">
                    <span className="surface-primary" data-testid="source-scope">{src.scope}</span>
                    {src.tokens.map((tok, ti) => (
                      <span key={ti} className="surface-token room-source-tok">
                        {ti > 0 ? " · " : ""}{tok}
                      </span>
                    ))}
                  </span>
                }
                wrap
                open
                expands={false}
                trailing={
                  <Button
                    dense
                    variant="ghost"
                    loading={busyWatch === src.watchId}
                    onClick={() => {
                      if (src.state === "paused") void handleResume(src.watchId);
                      else void handlePause(src.watchId);
                    }}
                  >
                    {src.state === "paused" ? "Resume" : "Pause"}
                  </Button>
                }
              >
                <div className="room-source-line2">
                  {src.checkedAt ? (
                    <span className="room-source-checked">checked {humanTime(src.checkedAt)}</span>
                  ) : null}
                  <EgressChip label={src.host} scope="cloud" title={src.host} />
                </div>
              </SurfaceLedgerRow>
            );
          })}
        </ul>
      </SurfaceLedger>
    </SurfaceSection>
  );
}

/* ── SINCE YOU LOOKED section ── */

function SinceYouLookedSection({ room }: { room: RoomSnapshot }) {
  if (room.sinceRead.state !== "ok") return null;
  const { readAt, groups } = room.sinceRead;
  const caption = readAt ? "SINCE YOU LOOKED" : "SINCE CREATED";
  const readLabel = readAt ? formatReadAt(readAt) : null;

  if (groups.length === 0) {
    return (
      <SurfaceSection
        label={caption}
        actions={readLabel ? <span className="surface-token room-chip-faint">{readLabel}</span> : undefined}
      >
        <p className="room-empty-line" data-testid="since-read-empty">
          {readAt ? `Nothing since ${formatTimeShort(readAt)}` : "Created just now"}
        </p>
      </SurfaceSection>
    );
  }

  return (
    <SurfaceSection
      label={caption}
      actions={readLabel ? <span className="surface-token room-chip-faint">{readLabel}</span> : undefined}
    >
      {groups.map((group, gi) => (
        <div key={gi} className="room-since-group" data-testid="since-read-group">
          <p className="room-since-group-head surface-primary">{group.summary}</p>
          <ul className="room-since-entries">
            {group.entries.map((entry, ei) => (
              <li key={ei} className="room-since-entry">
                <span className="room-since-phrase">{entry.phrase}</span>
                {entry.at ? (
                  <span className="room-since-time">{" · "}{humanTime(entry.at)}</span>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </SurfaceSection>
  );
}

/* ── DECISIONS & COMMITMENTS section ── */

function DecisionsCommitmentsSection({ room }: { room: RoomSnapshot }) {
  const decisionItems = room.decisions.state === "ok" ? room.decisions.items : [];
  const commitmentItems = room.commitments.state === "ok" ? room.commitments.items : [];
  if (decisionItems.length === 0 && commitmentItems.length === 0) return null;
  const total = decisionItems.length + commitmentItems.length;

  return (
    <SurfaceSection label={`DECISIONS & COMMITMENTS ${total}`}>
      <SurfaceLedger count="" cols="room">
        <ul className="surface-ledger-rows">
          {decisionItems.map((dec) => (
            <SurfaceLedgerRow
              key={`dec-${dec.id}`}
              primary={
                <>
                  <span className="room-dc-verb">Decided</span>
                  {" · "}{dec.text}{" · "}{humanTime(dec.at)}
                </>
              }
              wrap
              trailing={
                dec.url ? (
                  <Button dense variant="ghost" onClick={() => window.open(dec.url!, "_blank", "noopener")}>Open</Button>
                ) : (
                  <Button dense variant="ghost" onClick={() => openPrimitive(`decision:${dec.id}`)}>Open</Button>
                )
              }
            />
          ))}
          {commitmentItems.map((c) => (
            <SurfaceLedgerRow
              key={`com-${c.id}`}
              primary={
                <>
                  <span className="room-dc-verb">You owe</span>
                  {" · "}{c.text}
                  {c.dueAt ? <>{" · by "}{humanTime(c.dueAt)}</> : null}
                </>
              }
              wrap
              trailing={
                <Button dense variant="ghost" onClick={() => openPrimitive(`commitment:${c.id}`)}>Open</Button>
              }
            />
          ))}
        </ul>
      </SurfaceLedger>
    </SurfaceSection>
  );
}

/* ── Ask well ── */

function useModelLabel(projectId: string): { host: string; scope: "local" | "cloud" | undefined } {
  const [host, setHost] = useState("NOT SET");
  const [scope, setScope] = useState<"local" | "cloud" | undefined>(undefined);
  useEffect(() => {
    if (!projectId) return;
    let cancelled = false;
    getAssignmentEditor(
      { kind: "subject", subject_kind: "project", subject_id: projectId, capability_id: "ask.answer" },
      "ask.answer",
    ).then((editor) => {
      if (cancelled) return;
      const eff = editor.effective;
      if (eff.status === "assigned" && eff.assignment?.entries?.length) {
        const entry = eff.assignment.entries[0];
        setHost(entry.boundary || entry.label || "Assigned");
        setScope(entry.boundary?.includes("local") || entry.boundary?.includes("192.168") ? "local" : "cloud");
      } else {
        setHost("NOT SET");
        setScope(undefined);
      }
    }).catch(() => { /* non-fatal */ });
    return () => { cancelled = true; };
  }, [projectId]);
  return { host, scope };
}

function RoomAskWell({
  projectId,
  projectName,
  onOpenRef,
}: {
  projectId: string;
  projectName: string;
  onOpenRef: (ref: string) => void;
}) {
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState<AskRunResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const receipt = result?.groundingReceipt;
  const groundedCount = groundedMatchCount(receipt ?? null);
  const modelLabel = useModelLabel(projectId);

  const ask = async () => {
    if (!prompt.trim() || busy) return;
    setBusy(true);
    setError("");
    const answer = await runAsk({
      prompt: prompt.trim(),
      lens: "Project",
      context: [
        { id: projectId, kind: "project", ref: `project:${projectId}`, title: projectName },
      ],
      grounding: {
        meeting_ids: [],
        artifact_ids: [],
        refs: [`project:${projectId}`],
        expand: "summary",
      },
    });
    setBusy(false);
    if (!answer.ok) { setError(answer.output); return; }
    setResult(answer);
  };

  return (
    <div className="room-ask-section" data-testid="room-ask-well">
      {result ? (
        <div className="surface-aerogel room-ask-answer" data-testid="room-ask-answer">
          <Material>{result.output}</Material>
          {receipt ? (
            <p className="desk-ask-grounded">
              GROUNDED ON {groundedCount} OF {receipt.matchedCount}
            </p>
          ) : null}
          <CitationChips refs={receipt?.sourceRefs || []} onOpen={onOpenRef} />
        </div>
      ) : null}
      {error ? <p className="room-ask-error">{error}</p> : null}
      <div className="room-ask-well" data-testid="room-ask-input-well">
        <input
          type="text"
          className="room-ask-input"
          aria-label="Ask this project"
          value={prompt}
          placeholder="Ask this project…"
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void ask();
            }
          }}
        />
        <MicButton
          draftScope={`project-ask-${projectId}`}
          onText={(text) => setPrompt((v) => (v ? `${v} ${text}` : text))}
        />
        {/* Condition 8: NOT SET = idle/muted tone (no scope), assigned = scope from assignment */}
        {modelLabel.host === "NOT SET" ? (
          <span className="room-ask-model-chip">
            <EgressChip label="MODEL · NOT SET" className="room-egress-idle" title="No model assigned" />
            <Button dense variant="ghost" onClick={() => openSurfaceOr("configure-runs-on", "/settings", "models")}>
              Choose
            </Button>
          </span>
        ) : (
          <EgressChip
            label={`MODEL · ${modelLabel.host}`}
            scope={modelLabel.scope}
            title={`Model: ${modelLabel.host}`}
          />
        )}
        {/* Condition 1: no raw <button>; visually-hidden submit for a11y */}
        <Button dense variant="ghost" className="room-ask-submit-hidden" aria-label="Submit" onClick={() => void ask()} tabIndex={-1}>
          Submit
        </Button>
      </div>
    </div>
  );
}

/* ── HISTORY wing ── */

interface HistoryEntry {
  id: string;
  kind: string;
  phrase: string;
  time: string;
  source: string;
  occurredAt: string;
}

const HISTORY_FILTERS = [
  { field: "source", value: "ALL" },
  { field: "source", value: "GITHUB" },
  { field: "source", value: "JIRA" },
  { field: "source", value: "ROOM" },
];

function changeToHistoryEntry(c: RoomChangeRow): HistoryEntry {
  const phrase = kindToPhrase(c.kind);
  let source = "ROOM";
  if (c.kind.startsWith("github.") || c.kind.startsWith("pr.") || c.kind.startsWith("ci.")) source = "GITHUB";
  else if (c.kind.startsWith("jira.")) source = "JIRA";
  return {
    id: c.id, kind: c.kind,
    phrase: c.label || phrase,
    time: c.occurredAt ? formatTimeShort(c.occurredAt) : "",
    source,
    occurredAt: c.occurredAt || "",
  };
}

function groupByDay(entries: HistoryEntry[]): { label: string; date: string; entries: HistoryEntry[] }[] {
  const groups: { label: string; date: string; entries: HistoryEntry[] }[] = [];
  for (const entry of entries) {
    const d = new Date(entry.occurredAt);
    const dateStr = localDateStr(d);
    const last = groups[groups.length - 1];
    if (last && last.date === dateStr) {
      last.entries.push(entry);
    } else {
      groups.push({ label: streamDayLabel(d), date: dateStr, entries: [entry] });
    }
  }
  return groups;
}

function HistoryWing({
  room,
  todayCount,
  weekCount,
}: {
  room: RoomSnapshot;
  todayCount: number;
  weekCount: number;
}) {
  const changes = room.changes.state === "ok" ? room.changes.recent : [];
  const allEntries = useMemo(() => changes.map(changeToHistoryEntry), [changes]);

  const [sourceFilter, setSourceFilter] = useState("ALL");

  const filtered = useMemo(() => {
    if (sourceFilter === "ALL") return allEntries;
    return allEntries.filter((e) => e.source === sourceFilter);
  }, [allEntries, sourceFilter]);

  const [searchQuery, setSearchQuery] = useState("");
  const searchFiltered = useMemo(() => {
    if (!searchQuery.trim()) return filtered;
    const q = searchQuery.toLowerCase();
    return filtered.filter((e) => e.phrase.toLowerCase().includes(q));
  }, [filtered, searchQuery]);

  const days = useMemo(() => groupByDay(searchFiltered), [searchFiltered]);

  return (
    <div className="room-history" data-testid="room-history">
      <SurfaceStream
        count={todayCount > 0 ? `${todayCount} today` : "0 today"}
        controls={
          <div className="room-history-controls">
            {/* Condition 1: library Button, not raw <button>; flat filter via data-filter + CSS */}
            <span className="room-history-filters" role="group" aria-label="Source filter">
              {HISTORY_FILTERS.map((f) => (
                <Button
                  key={f.value}
                  dense
                  variant="ghost"
                  className="room-filter-token"
                  data-filter-active={sourceFilter === f.value || undefined}
                  onClick={() => setSourceFilter(f.value)}
                  aria-pressed={sourceFilter === f.value}
                >
                  {f.value}
                </Button>
              ))}
            </span>
            <div className="room-history-search">
              <input
                type="search"
                aria-label="Search history"
                placeholder="Search history…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <MicButton
                draftScope="room-history-search"
                onText={(text) => setSearchQuery((v) => (v ? `${v} ${text}` : text))}
              />
            </div>
          </div>
        }
      >
        {days.map((day) => (
          <SurfaceStreamDay key={day.label} label={day.label}>
            {day.entries.map((entry) => (
              <SurfaceStreamEntry key={entry.id} when={entry.time} dense>
                <span data-testid="history-entry">{entry.phrase}</span>
              </SurfaceStreamEntry>
            ))}
          </SurfaceStreamDay>
        ))}
      </SurfaceStream>
    </div>
  );
}

/* ── History count helper (shared between footer and HistoryWing) ── */

function computeHistoryCounts(changes: RoomChangeRow[]): { todayCount: number; weekCount: number } {
  const entries = changes.map(changeToHistoryEntry);
  const todayStr = localDateStr(new Date());
  const weekAgo = new Date(Date.now() - 7 * 86_400_000);
  const todayCount = entries.filter((e) => {
    const d = new Date(e.occurredAt);
    return localDateStr(d) === todayStr;
  }).length;
  const weekCount = entries.filter((e) => {
    const d = new Date(e.occurredAt);
    return d >= weekAgo;
  }).length;
  return { todayCount, weekCount };
}

/* ── main core ── */

export function ProjectRoomCore({ hero, scope, scopeLabel }: CoreProps) {
  const ctrl = useProjectRoomController(scope, scopeLabel);
  const loading = ctrl.loadStatus === "loading";

  const reviewData: RoomReviewData | null =
    ctrl.room?.review.state === "ok"
      ? (ctrl.room.review as RoomReviewData & { state: "ok" })
      : null;

  const reviewCtrl = useReviewController(
    ctrl.projectId, reviewData, () => void ctrl.load(),
  );

  const updateCtrl = useUpdateController(
    ctrl.projectId, () => void ctrl.load(),
  );

  const stewardCtrl = useStewardController(
    ctrl.projectId, () => void ctrl.load(),
  );

  const runtimeTitle =
    ctrl.loadStatus === "ready" && ctrl.projectName !== "Project"
      ? ctrl.projectName : null;
  useWindowTitle(runtimeTitle, [runtimeTitle]);

  const readPosted = useRef(false);
  useEffect(() => {
    if (ctrl.loadStatus === "ready" && ctrl.room && !readPosted.current) {
      readPosted.current = true;
      void ctrl.postRead();
    }
  }, [ctrl.loadStatus]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleRefresh = useCallback(() => {
    readPosted.current = false;
    void ctrl.load().then(() => void ctrl.postRead());
  }, [ctrl]); // eslint-disable-line react-hooks/exhaustive-deps

  const pendingCount = reviewData?.pendingCount ?? 0;

  // Condition 2: history counts computed here, shared with HistoryWing and footer.
  const historyCounts = useMemo(() => {
    if (!ctrl.room || ctrl.room.changes.state !== "ok") return { todayCount: 0, weekCount: 0 };
    return computeHistoryCounts(ctrl.room.changes.recent);
  }, [ctrl.room]);

  if (!ctrl.projectId)
    return (
      <div className="room-empty-state">
        <p className="room-empty-line">Open a Project</p>
      </div>
    );

  // Posture routing: Review > Update > Steward > Room
  if (reviewCtrl.posture === "active") {
    return (
      <>
        {hero ? hero(<Button dense variant="ghost" onClick={handleRefresh}>Refresh</Button>) : null}
        <ReviewPosture ctrl={reviewCtrl} />
      </>
    );
  }

  if (updateCtrl.posture !== "off") {
    return (
      <>
        {hero ? hero(<Button dense variant="ghost" onClick={handleRefresh}>Refresh</Button>) : null}
        <UpdatePosture ctrl={updateCtrl} />
      </>
    );
  }

  if (stewardCtrl.posture !== "off") {
    return (
      <>
        {hero ? hero(<Button dense variant="ghost" onClick={handleRefresh}>Refresh</Button>) : null}
        <StewardPosture ctrl={stewardCtrl} />
      </>
    );
  }

  const readReceipt = ctrl.readAt ? `READ ${formatTimeShort(ctrl.readAt)}` : "";
  const nextCheck = ctrl.room?.sources.state === "ok" ? ctrl.room.sources.nextCheckAt : null;

  // Condition 2: footer receipt switches on wing — ROOM: READ+NEXT CHECK; HISTORY: N TODAY · M THIS WEEK
  const footerReceipt = ctrl.view === "history" ? (
    <span className="surface-footer-receipt-line" role="status" data-testid="room-footer-receipt">
      {historyCounts.todayCount} TODAY {" · "} {historyCounts.weekCount} THIS WEEK
    </span>
  ) : (
    <span className="surface-footer-receipt-line" role="status" data-testid="room-footer-receipt">
      {readReceipt}
      {readReceipt && nextCheck ? " · " : ""}
      {nextCheck ? `NEXT CHECK ${formatTimeShort(nextCheck)}` : ""}
    </span>
  );

  return (
    <>
      {hero ? hero(<Button dense variant="ghost" onClick={handleRefresh}>Refresh</Button>) : null}
      {ctrl.room ? (
        <div className="room-body" data-testid="room-body">
          {ctrl.view === "room" ? (
            <>
              <div className="room-section-rise" style={{ animationDelay: "0ms" }}>
                <RoomHead room={ctrl.room} ctrl={ctrl} updateCtrl={updateCtrl} />
              </div>
              <div className="room-section-rise" style={{ animationDelay: "40ms" }}>
                <NeedsYouSection room={ctrl.room} ctrl={ctrl} reviewCtrl={reviewCtrl} pendingCount={pendingCount} />
              </div>
              <div className="room-section-rise" style={{ animationDelay: "80ms" }}>
                <SourcesSection room={ctrl.room} onReload={() => void ctrl.load()} stewardCtrl={stewardCtrl} />
              </div>
              <div className="room-section-rise" style={{ animationDelay: "120ms" }}>
                <SinceYouLookedSection room={ctrl.room} />
              </div>
              <div className="room-section-rise" style={{ animationDelay: "160ms" }}>
                <DecisionsCommitmentsSection room={ctrl.room} />
              </div>
              {/* Condition 7: ask well sticky at the foot at ALL widths */}
              <div className="room-section-rise room-ask-container" style={{ animationDelay: "200ms" }}>
                <RoomAskWell projectId={ctrl.projectId} projectName={ctrl.projectName} onOpenRef={ctrl.openProjectRef} />
              </div>
            </>
          ) : (
            <HistoryWing room={ctrl.room} todayCount={historyCounts.todayCount} weekCount={historyCounts.weekCount} />
          )}
        </div>
      ) : loading ? (
        <div className="room-loading"><p className="room-empty-line">Loading…</p></div>
      ) : ctrl.error ? (
        <div className="room-error"><p className="room-empty-line">{ctrl.error}</p></div>
      ) : null}
      <SurfaceFooter
        receipt={footerReceipt}
        verbs={
          <Button dense variant="ghost" onClick={handleRefresh} data-testid="room-refresh">Refresh</Button>
        }
      />
    </>
  );
}
