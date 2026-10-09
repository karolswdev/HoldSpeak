// HS-169-03 — the Room rebuilt to the ratified canvas.
// Four questions: What needs me now? What am I watching? What changed
// since I last looked? What did we decide and what do I owe people?
// Two wings: ROOM · HISTORY. Ask well at the foot. No counters of zero,
// no REV, no raw field names, the name said once.
import { HandRowVerb } from "../../desk/components/HandRowVerb";
import { wireDate } from "../../desk/surface/format";
import React, { useEffect, useRef, useState, useMemo, useCallback, useReducer } from "react";
import {
  countLabel,
  SurfaceFooter,
  SurfaceSection,
  SurfaceRows,
  SurfaceRow,
  SurfaceState,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceStream,
  SurfaceStreamDay,
  SurfaceStreamEntry,
  SurfaceWell,
  ConfirmVerb,
  EgressChip,
  StateChip,
  TaskResume,
  TaskResumeList,
  humanTime,
  streamDayLabel,
  MicButton,
  groundedMatchCount,
  CitationChips,
  sourceLabel,
  Material,
} from "../../desk/surface";
import { useWindowTitle } from "../../desk/surface/title";
import { Button } from "../../components/signal/Signal";
import {
  getAssignmentEditor,
} from "../../pages/cores/assignmentExperience";
import {
  runAsk,
  saveAskTask,
  listUnfinishedAsks,
  resumeAskTask,
  discardAskTask,
  stopAskTask,
  type AskRunResult,
  type AskTask,
} from "../../desk/ask";
import { onReturnToTask, rememberTaskFocus } from "../../desk/returnToTask";
import { useOnDeskChanged } from "../../desk/useDeskChangedRefresh";
import { StandingPagesSection, useStandingPages } from "../../desk/standingPages";
import { apiFetch } from "../../lib/api";
import type { InferenceTarget } from "../../desk/api";
import { openPrimitive, openSurfaceOr } from "../../desk/shell";
import { ROOM_AT_EVENT, ROOM_PROPOSAL_EVENT, ROOM_UPDATES_EVENT, refOpener, takeRoomAtRequest, takeRoomProposalRequest, takeRoomUpdatesRequest } from "../../desk/openObject";
import { useDesk } from "../../desk/store";
import type { CoreProps } from "../../pages/cores/core-types";
import type {
  RoomSnapshot,
  RoomHealthData,
  RoomTargetData,
  RoomSourceItem,
  RoomChangeRow,
  RoomReviewData,
  RoomNeedsYouItem,
  RoomProposalItem,
  RoomSuggestedSourceItem,
  RoomHealthPerson,
  NudgeCardState,
  NudgeLocal,
  NudgeCardAction,
} from "./model";
import { lifecycleLabel, roomHealthWord, resolveHealthRows, nudgeCardReducer, initialNudgeCard, formatDays, healthReasonWords, needsYouWhyWords } from "./model";
import { StringGadget, CycleGadget } from "../../desk/surface/gadgets";
import { egressFor, egressForEvent, receiptFace, receiptLabel, refusalWord } from "../../desk/surface/egress";
import { useProjectRoomController } from "./useProjectRoomController";
import { useReviewController } from "./review/useReviewController";
import { ReviewPosture } from "./review/ReviewPosture";
import { useUpdateController } from "./update/useUpdateController";
import { UpdatePosture } from "./update/UpdatePosture";
import { useStewardController } from "./steward/useStewardController";
import { StewardPosture } from "./steward/StewardPosture";
import { pluralize } from "./steward/model";
import { usePrepareController, type PrepareController } from "./prepare/usePrepareController";
import { PreparePosture, RESULT_OPTIONS } from "./prepare/PreparePosture";
import { coverageToken, clockToken } from "./prepare/model";
import * as api from "./api";
import { RoomPeopleSection, monogram } from "./RoomPeopleSection";
import "./project-room.css";
import { RecallFace } from "./recall/RecallFace";
import { DecisionRecordPreparedChip, DecisionRecordSendWells } from "../../desk/documentSendsLazy";
import { fetchUpdates } from "./update/api";
import { Unreadable } from "../../desk/surface/send";
import { retryRoomLink, useRoomSendLink } from "../../desk/windowSend";
import { flightForItem, isInFlight, mergeReceipt, useAgentFlights, useAgentFlightsLive } from "../../desk/agentFlights";
import { FlightChip, FlightVerbs } from "../../desk/components/AgentFlight";

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
  confluence: "C",
  meeting: "MTG",
  proposal: "MTG",
  delta: "◇",
  room: "▣",
};

export function emblemFor(source: string): string {
  const key = source.toLowerCase();
  return PROVIDER_EMBLEM[key] || source.slice(0, 2).toUpperCase();
}

/* ── time formatting ── */

function formatReadAt(iso: string | null): string {
  if (!iso) return "";
  const d = wireDate(iso);
  if (!d) return "";
  const days = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${days[d.getDay()]} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function formatTimeShort(iso: string | null): string {
  if (!iso) return "";
  const d = wireDate(iso);
  if (!d) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function formatTargetDate(iso: string): string {
  const d = wireDate(iso);
  if (!d) return iso;
  const months = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"];
  return `${months[d.getMonth()]} ${d.getDate()}`;
}

/** Format a due date as a short day name (FRI) when within ~7 days, else MMM DD. */
function formatDueShort(iso: string): string {
  const d = wireDate(iso);
  if (!d) return iso;
  const days = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
  const now = new Date();
  const diffMs = d.getTime() - now.getTime();
  const diffDays = Math.abs(diffMs) / 86_400_000;
  if (diffDays <= 7) return days[d.getDay()];
  const months = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"];
  return `${months[d.getMonth()]} ${d.getDate()}`;
}

/** Local-time YYYY-MM-DD (same derivation as streamDayLabel's sameDay). */
function localDateStr(d: Date): string {
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

/** PHILO-15 B69: the Room head's one source word, from the hub's freshness
 *  states (the rule Needs you reads): `STALE · CHECKED 10H AGO`, `QUIET UNTIL
 *  08:00`, else `CHECKED <age>`. Null with no checked source. */
export function sourcesWord(items: RoomSourceItem[], quietUntil?: string | null): { word: string; stale: boolean } | null {
  const checked = maxCheckedAt(items);
  if (items.some((i) => i.freshness === "stale")) {
    return { word: checked ? `STALE · CHECKED ${humanTime(checked)}` : "STALE", stale: true };
  }
  if (quietUntil && items.some((i) => i.freshness === "quiet")) {
    return { word: `QUIET UNTIL ${formatTimeShort(quietUntil)}`, stale: false };
  }
  return checked ? { word: `CHECKED ${humanTime(checked)}`, stale: false } : null;
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

/* ── proposal date formatting ── */

function formatMMDD(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = wireDate(iso);
  if (!d) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
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
  unread,
}: {
  count: number;
  isAccent: boolean;
  /** A Room read failed: the Room cannot say it is clear. */
  unread: boolean;
}) {
  return (
    <span
      className="surface-display room-headline"
      data-testid="room-headline"
      data-accent={isAccent || undefined}
    >
      {/* PHILO-13-03 (canvas C1-4a): a Room counts its own open items, a
          narrower set than the Desk's one "needs you" number. */}
      {count > 0 ? `${count} open here` : unread ? "Not all read" : "Clear here"}
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
  const healthWord = roomHealthWord(room);
  const target = room.target.state === "ok" ? (room.target as RoomTargetData & { state: "ok" }) : null;
  const needsYouCount = room.needsYou.state === "ok" ? room.needsYou.count : 0;
  const sources = room.sources.state === "ok" ? room.sources.items : [];
  const sourceWord = sourcesWord(sources, room.sources.state === "ok" ? room.sources.quietUntil : null);

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
      <RoomHeadline
        count={needsYouCount}
        isAccent={needsYouCount > 0}
        // PHILO-15 B69: a STALE source is not read: never "Clear here".
        unread={room.health.state === "degraded" || room.needsYou.state === "degraded" || Boolean(sourceWord?.stale)}
      />
      {showOutcome ? (
        <p className="room-head-outcome surface-primary" data-testid="room-head-outcome">
          {room.project.outcomeText || room.project.name}
        </p>
      ) : null}
      <div className="room-head-chips" data-testid="room-head-chips">
        {healthWord ? (
          // PHILO-15 lane 12 (B25): an empty Project reads NEW (no health
          // claim with nothing to judge).
          <StateChip
            state={healthWord.tone === "fail" ? "failure" : healthWord.tone === "info" ? "idle" : "success"}
            label={healthWord.word}
            icon={healthWord.tone === "info" ? "○" : "●"}
            data-testid="room-health-word"
          />
        ) : null}
        {health?.reason ? (
          <span className="surface-token room-chip-faint" data-testid="room-health-reason">{healthReasonWords(health)}</span>
        ) : null}
        {target?.targetAt ? (
          <span
            className="surface-token"
            data-testid="room-target-chip"
            data-tone={target.passed ? "danger" : undefined}
          >
            {/* HS-200-16: one day is a day.  Both branches count through the
                tree's existing honest-pluralization helper (steward/model.ts),
                the same rule `_count_unit` applies on the backend. */}
            {target.passed
              ? (target.daysLeft
                  ? `OVERDUE BY ${pluralize(Math.abs(target.daysLeft), "DAY", "DAYS")}`
                  : "OVERDUE TODAY")
              : `TARGET ${formatTargetDate(target.targetAt)}${target.daysLeft ? ` · ${pluralize(target.daysLeft, "DAY", "DAYS")}` : " · TODAY"}`
            }
          </span>
        ) : null}
        {sourceWord ? (
          <span className="surface-token room-chip-faint" data-testid="room-sources-word"
            data-tone={sourceWord.stale ? "warn" : undefined}>{sourceWord.word}</span>
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

/* ── HS-173: HEALTH section ── */

function healthToneToState(tone: "green" | "amber" | "red"): "success" | "warning" | "failure" {
  if (tone === "red") return "failure";
  if (tone === "amber") return "warning";
  return "success";
}

function HealthSection({ room, onRetry }: { room: RoomSnapshot; onRetry: () => void }) {
  // A failed health read is named, with Retry. It is never drawn as "no
  // health rows" (the same species as ITEMS UNAVAILABLE).
  if (room.health.state === "degraded") {
    return (
      <SurfaceSection
        label="HEALTH"
        actions={
          <Button dense variant="ghost" onClick={onRetry} data-testid="health-retry">
            Retry
          </Button>
        }
      >
        <span data-testid="health-not-read">
          <StateChip state="unreachable" label="HEALTH NOT READ" />
        </span>
      </SurfaceSection>
    );
  }
  const health = room.health.state === "ok"
    ? (room.health as RoomHealthData & { state: "ok" }) : null;
  if (!health?.signals) return null;

  const rows = resolveHealthRows(health.signals, health.mergeQueueDepth);
  if (rows.length === 0) return null;

  // CHECKED N MIN AGO on the section caption (addendum P2-8: one token, not per row)
  const checkedToken = health.checkedAt ? `CHECKED ${humanTime(health.checkedAt)}` : null;

  return (
    <SurfaceSection
      label="HEALTH"
      actions={checkedToken ? (
        <span className="surface-token room-chip-faint" data-testid="health-checked">{checkedToken}</span>
      ) : undefined}
    >
      <SurfaceLedger count="" cols="room">
        <ul className="surface-ledger-rows room-health-rows">
          {rows.map((row) => (
            <SurfaceLedgerRow
              key={row.key}
              data-testid={`health-row-${row.key}`}
              lead={<StateChip state={healthToneToState(row.tone)} label="" icon={"●"} />}
              primary={<span className="surface-primary room-health-label">{row.label}</span>}
              wrap
              cells={
                <>
                  {row.tokens.map((tok, ti) => (
                    <span key={ti} className="surface-token" data-testid={`health-token-${row.key}-${ti}`}>
                      {ti > 0 ? " · " : ""}{tok}
                    </span>
                  ))}
                </>
              }
            />
          ))}
        </ul>
      </SurfaceLedger>
    </SurfaceSection>
  );
}

/* ── HS-173-04: Nudge card (inline under a bottleneck row) ── */

function NudgeCard({
  person,
  needsYouItem,
  nudgeItem,
  onReload,
  onSent,
  persistedState,
  local,
  onLocal,
}: {
  person: RoomHealthPerson | undefined;
  needsYouItem: RoomNeedsYouItem;
  nudgeItem: api.NudgeItem | undefined;
  onReload: () => void;
  onSent?: () => void;
  /** The step's persisted state (the wire). */
  persistedState?: string | null;
  /** The Room's own state of a Send it pressed (outlives this card: the card can close mid-send). */
  local?: NudgeLocal;
  onLocal?: (next: NudgeLocal) => void;
}) {
  const displayName = person?.displayName || needsYouItem.title;
  // Bind PR from the nudge step (the wire's authoritative source)
  const prNumber = nudgeItem?.pr_number ?? person?.nudge?.prNumber ?? person?.prs?.[0]?.number ?? 0;
  const prTitle = nudgeItem?.pr_title ?? person?.prs?.[0]?.title ?? "";
  const prUrl = nudgeItem?.pr_url ?? person?.prs?.[0]?.url ?? "";
  const stepId = nudgeItem?.step_id ?? person?.nudge?.stepId ?? "";
  const waitDays = Math.round(person?.medianDays || needsYouItem.medianDays || 1);
  const defaultText = nudgeItem?.comment_text
    || person?.nudge?.text
    || `This PR has been waiting for review for ${waitDays} days. Flagged by HoldSpeak.`;

  // PHILO-10-02: the card starts from the step's persisted state, never blindly open.
  // The parent keys this card by the live state, so a late answer re-seeds the CURRENT card.
  const [card, dispatch] = useReducer(nudgeCardReducer, initialNudgeCard(
    local?.state ?? persistedState, defaultText, prNumber,
    { displayName, sentAt: local?.sentAt, reason: local?.reason, text: local?.text }));

  const handleSend = async () => {
    if (card.phase !== "open" && card.phase !== "failed") return;
    if (card.phase === "open" && card.busy) return;
    if (!stepId) return;
    dispatch({ type: "sending" });
    const submitted = card.text;
    onLocal?.({ state: "pending", text: submitted });
    try {
      const result = await api.sendNudge(stepId, card.text);
      if (result.success) {
        const sentAt = typeof result.sent_at === "string"
          ? result.sent_at : new Date().toISOString();
        dispatch({
          type: "sent",
          displayName,
          prNumber,
          sentAt,
        });
        // The receipt row stays visible; notify parent for cooldown token.
        onSent?.();
        onLocal?.({ state: "sent", sentAt });
      } else if (result.outcome === "unknown") {
        // PHILO-10-02 (F4): not known to be posted, not known to be lost.
        dispatch({ type: "unknown", prNumber });
        onLocal?.({ state: "unknown" });
      } else {
        const reason = String(result.message || "Send failed");
        dispatch({ type: "failed", reason });
        onLocal?.({ state: "failed", reason, text: submitted });
      }
    } catch (err) {
      dispatch({ type: "failed", reason: String(err) });
      onLocal?.({ state: "failed", reason: String(err), text: submitted });
    }
  };

  const handleDismiss = async () => {
    if (stepId) {
      try { await api.dismissNudge(stepId); } catch { /* non-fatal */ }
    }
    dispatch({ type: "dismiss" });
    onReload();
  };

  // Receipt row (after Send)
  if (card.phase === "sent") {
    return (
      <SurfaceLedgerRow
        data-testid="nudge-receipt-row"
        lead={<StateChip state="success" label="" icon={"●"} wordless />}
        primary={<span className="surface-primary">SENT</span>}
        wrap
        cells={
          <>
            <span className="room-nudge-receipt-name">{displayName}</span>
            {prNumber ? (
              <span className="surface-token">
                {prUrl ? (
                  <a href={prUrl} target="_blank" rel="noopener noreferrer" className="room-nudge-pr-link">#{prNumber}</a>
                ) : `#${prNumber}`}
              </span>
            ) : null}
            <span className="surface-token">{formatTimeShort(card.sentAt)}</span>
            <EgressChip label="GITHUB.COM" scope="cloud" />
          </>
        }
      />
    );
  }

  // PHILO-10-02 (F4): the result is unknown -- no Send verb; check the pull request.
  if (card.phase === "unknown") {
    return (
      <SurfaceLedgerRow
        data-testid="nudge-unknown-row"
        lead={<StateChip state="warning" label="" icon={"●"} wordless />}
        primary={<span className="surface-primary">RESULT UNKNOWN</span>}
        wrap
        cells={
          <>
            <span className="room-nudge-receipt-name">{displayName}</span>
            <span className="surface-token">
              {prUrl ? (
                <a href={prUrl} target="_blank" rel="noopener noreferrer" className="room-nudge-pr-link">CHECK #{card.prNumber}</a>
              ) : `CHECK #${card.prNumber}`}
            </span>
            <EgressChip label="GITHUB.COM" scope="cloud" />
          </>
        }
      />
    );
  }

  // Nudge card (open / failed state)
  if (card.phase === "open" || card.phase === "failed") {
    return (
      <li className="surface-ledger-row room-nudge-card-row" data-testid="nudge-card" data-open>
        <SurfaceWell>
          <div className="room-nudge-card-who surface-primary" data-testid="nudge-card-who">{displayName}</div>
          {prNumber ? (
            <div className="room-nudge-card-pr">
              <a href={prUrl || "#"} target="_blank" rel="noopener noreferrer" className="surface-token room-nudge-pr-link" data-testid="nudge-card-pr">
                #{prNumber} · {prTitle}
              </a>
            </div>
          ) : null}
          {person?.prs && person.prs.length > 1 ? (
            <div className="room-nudge-pr-list" data-testid="nudge-card-pr-list">
              {person.prs.map((pr) => (
                <div key={pr.number} className="room-nudge-pr-item">
                  <a href={pr.url || "#"} target="_blank" rel="noopener noreferrer" className="surface-token room-nudge-pr-link">
                    #{pr.number} · {pr.title}
                  </a>
                </div>
              ))}
            </div>
          ) : null}
          <div className="room-nudge-card-text" data-testid="nudge-card-text">
            <StringGadget
              label="Comment"
              value={card.text}
              onChange={(v) => dispatch({ type: "setText", text: v })}
            />
          </div>
          {card.phase === "failed" ? (
            <div className="room-nudge-card-error">
              <StateChip state="failure" label="FAILED" icon={"●"} />
              <span className="surface-token">{card.reason}</span>
            </div>
          ) : null}
          <div className="room-nudge-card-footer">
            <EgressChip label="GITHUB.COM" scope="cloud" data-testid="nudge-card-egress" />
            <span className="room-nudge-card-verbs">
              <Button dense variant="primary" loading={card.phase === "open" && card.busy} onClick={() => void handleSend()} data-testid="nudge-send">
                Send
              </Button>
              <Button dense variant="ghost" onClick={() => void handleDismiss()} data-testid="nudge-dismiss">
                Dismiss
              </Button>
            </span>
          </div>
        </SurfaceWell>
      </li>
    );
  }

  // Closed — render as the bottleneck row's trailing verb
  return null;
}

/* ── HS-173: nudge cooling token (NUDGED N D AGO / NUDGED JUST NOW) ── */

export function nudgeCooldownToken(nudge: RoomHealthPerson["nudge"]): string | null {
  if (!nudge || nudge.state !== "sent" || !nudge.sentAt) return null;
  const sentDate = wireDate(nudge.sentAt);
  if (!sentDate) return null;
  const diffMs = Date.now() - sentDate.getTime();
  const diffDays = diffMs / 86_400_000;
  if (diffDays > 7) return null; // past cooldown
  if (diffDays < 1 / 24) return "NUDGED JUST NOW"; // under 1 hour
  if (diffDays < 1) return `NUDGED ${Math.max(1, Math.round(diffDays * 24))} H AGO`; // hours under a day
  return `NUDGED ${Math.max(1, Math.round(diffDays))} D AGO`;
}

/* ── HS-172-03: Proposal row sub-component ── */

function ProposalRow({
  item,
  proposal,
  ctrl,
  isNewest,
  selected = false,
}: {
  item: RoomNeedsYouItem;
  proposal: RoomProposalItem | undefined;
  ctrl: ReturnType<typeof useProjectRoomController>;
  isNewest: boolean;
  selected?: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState("");
  const [editOwner, setEditOwner] = useState("");
  const [editDue, setEditDue] = useState("");

  const proposalId = item.proposalId || "";
  const kind = item.proposalKind || "action";
  const prefix = kind === "decision" ? "Decide:" : "Confirm:";
  const host = item.host || proposal?.modelHost || "";

  // Caption: BY FRI · from Standup 09-05 · MAREK + EgressChip
  const dueHint = proposal?.dueHint || item.dueHint;
  const meetingTitle = item.meetingTitle || "";
  const meetingStartedAt = item.meetingStartedAt || "";
  const createdAt = proposal?.createdAt || item.createdAt || "";
  const speaker = proposal?.speakerLabel || item.speakerLabel || "";
  const ownerHint = proposal?.ownerHint || item.ownerHint || "";

  const openEdit = () => {
    setEditText(proposal?.text || item.title);
    setEditOwner(ownerHint || "");
    setEditDue(dueHint || "");
    setEditing(true);
  };

  const handleSaveConfirm = () => {
    const edits: { text?: string; owner?: string; due?: string } = {};
    const origText = proposal?.originalText || proposal?.text || item.title;
    if (editText && editText !== origText) edits.text = editText;
    if (editOwner) edits.owner = editOwner;
    if (editDue) edits.due = editDue;
    void ctrl.handleConfirmProposal(proposalId, edits);
    setEditing(false);
  };

  const cancelEdit = () => setEditing(false);

  if (editing) {
    // Board: RoomProposalEdit — text StringGadget + OWNER + DUE + was: caption + Save & confirm + Cancel
    const origText = proposal?.originalText || proposal?.text || item.title;
    const origDue = proposal?.dueHint || item.dueHint || "";
    const wasCaption = `WAS: ${origText.toUpperCase()}${origDue ? ` · BY ${origDue.toUpperCase()}` : ""}`;

    return (
      <li className={`surface-ledger-row room-proposal-edit-row${isNewest ? " room-needs-you-new" : ""}`} data-testid="proposal-edit-row" data-open>
        <div className="surface-ledger-line room-proposal-edit-line">
          <span className="surface-ledger-lead">MTG</span>
          <span className="surface-ledger-primary">
            <span className="surface-primary" data-testid="proposal-edit-text">{item.title}</span>
          </span>
        </div>
        <div className="surface-ledger-open room-proposal-edit-well" data-testid="proposal-edit-well">
          <div className="room-proposal-edit-fields">
            <StringGadget label="Text" value={editText} onChange={setEditText} autoFocus />
            <label className="room-proposal-edit-label">
              <span className="room-proposal-edit-label-text">OWNER</span>
              <StringGadget label="Owner" value={editOwner} onChange={setEditOwner} placeholder="Owner" />
            </label>
            <label className="room-proposal-edit-label">
              <span className="room-proposal-edit-label-text">DUE</span>
              <StringGadget label="Due" value={editDue} onChange={setEditDue} placeholder="Due" />
            </label>
          </div>
          <p className="room-proposal-was-caption" data-testid="proposal-was-caption">{wasCaption}</p>
          <div className="room-proposal-edit-verbs">
            <Button dense variant="primary" loading={ctrl.proposalBusy === proposalId} onClick={handleSaveConfirm} data-testid="proposal-save-confirm">
              Save & confirm
            </Button>
            <Button dense variant="ghost" onClick={cancelEdit} data-testid="proposal-cancel-edit">
              Cancel
            </Button>
          </div>
        </div>
      </li>
    );
  }

  // Caption parts
  const captionParts: string[] = [];
  if (dueHint) captionParts.push(`BY ${dueHint.toUpperCase()}`);
  if (meetingTitle) {
    // HS-200-16: the date belongs to the MEETING this came from, not to the
    // moment the proposal row was written.  They agree on a same-day desk and
    // disagree the next morning; the caption said `from <meeting> <today>`
    // while the review wing and recall both said the meeting's own day.
    const dateStr = formatMMDD(meetingStartedAt || createdAt);
    captionParts.push(`from ${meetingTitle}${dateStr ? ` ${dateStr}` : ""}`);
  }

  return (
    <SurfaceLedgerRow
      data-testid="proposal-row"
      selected={selected}
      lead="MTG"
      primary={
        <span className="surface-primary room-proposal-text" data-testid="proposal-primary">
          <span className="room-proposal-prefix" data-proposal-kind={kind}>{prefix}</span>
          {" "}{item.title}
        </span>
      }
      wrap
      cells={
        <>
          {captionParts.length > 0 ? (
            <span className="room-proposal-caption" data-testid="proposal-caption">
              {captionParts.join(" · ")}
            </span>
          ) : null}
          {speaker ? (
            <span className="room-proposal-caption room-proposal-speaker">{speaker.toUpperCase()}</span>
          ) : null}
          {host ? (
            <EgressChip label={egressFor(host).label} scope={egressFor(host).scope} />
          ) : null}
        </>
      }
      trailing={
        <span className="room-proposal-verbs" data-testid="proposal-verbs">
          <Button dense variant="primary" loading={ctrl.proposalBusy === proposalId} onClick={() => void ctrl.handleConfirmProposal(proposalId)} data-testid="proposal-confirm">
            Confirm
          </Button>
          <Button dense variant="ghost" onClick={openEdit} data-testid="proposal-edit">
            Edit
          </Button>
          <Button dense variant="ghost" onClick={() => void ctrl.handleDismissProposal(proposalId)} data-testid="proposal-dismiss">
            Dismiss
          </Button>
        </span>
      }
    />
  );
}

/* ── OPEN HERE section (PHILO-13-03: was NEEDS YOU) ── */

function NeedsYouSection({
  room,
  ctrl,
  reviewCtrl,
  pendingCount,
  selectedProposalId = "",
}: {
  room: RoomSnapshot;
  ctrl: ReturnType<typeof useProjectRoomController>;
  reviewCtrl: ReturnType<typeof useReviewController>;
  pendingCount: number;
  selectedProposalId?: string;
}) {
  if (room.needsYou.state !== "ok") return null;
  const { items, count } = room.needsYou;

  const nextCheck = room.sources.state === "ok" ? room.sources.nextCheckAt : null;
  // PHILO-15 B69: while quiet hours hold the sweep, the next check is the quiet end.
  const quietUntil = room.sources.state === "ok" ? room.sources.quietUntil : null;
  const nextWords = quietUntil
    ? ` · quiet until ${formatTimeShort(quietUntil)}`
    : nextCheck ? ` · next check ${formatTimeShort(nextCheck)}` : "";

  // HS-173: build a map of relationship_id -> health person for nudge state
  const health = room.health.state === "ok"
    ? (room.health as RoomHealthData & { state: "ok" }) : null;
  const peopleMap = useMemo(() => {
    const m = new Map<string, RoomHealthPerson>();
    if (health?.people) {
      for (const p of health.people) {
        if (p.relationshipId) m.set(p.relationshipId, p);
      }
    }
    return m;
  }, [health?.people]);

  // HS-173-04: build a map of reviewer_login -> nudge item from the controller
  const nudgeMap = useMemo(() => {
    const m = new Map<string, api.NudgeItem>();
    for (const n of ctrl.nudges) {
      if (n.reviewer_login) m.set(n.reviewer_login.toLowerCase(), n);
    }
    return m;
  }, [ctrl.nudges]);

  // HS-173: track which nudge cards are open (by relationship_id)
  const [openNudge, setOpenNudge] = useState<string | null>(null);

  // HS-173-04: track locally sent nudges so the row shows NUDGED JUST NOW
  // immediately without waiting for a reload.
  const [sentNudgeRelIds, setSentNudgeRelIds] = useState<Set<string>>(new Set());
  // PHILO-10-02: the Room's own state of each Send it pressed (pending, unknown, failed, sent)
  // survives closing and reopening the card, and a late answer reaches the current card.
  const [localNudges, setLocalNudges] = useState<Record<string, NudgeLocal>>({});
  // Conductor F2 (K4b): each row wears its agent where it lives.
  const flights = useAgentFlights((s) => s.flights);

  const reviewAction = pendingCount > 0 ? (
    <Button dense variant="ghost" loading={reviewCtrl.loading} onClick={() => void reviewCtrl.enterReview()} data-testid="review-verb" data-verb="review">
      Review {pendingCount}
    </Button>
  ) : undefined;

  if (items.length === 0) {
    return (
      <SurfaceSection label="OPEN HERE" actions={reviewAction}>
        <p className="room-empty-line" data-testid="needs-you-empty">
          {room.health.state === "degraded" ? "Not all read" : "Nothing open"}{nextWords}
        </p>
      </SurfaceSection>
    );
  }

  // Build a lookup from proposalId to the full proposal data
  const proposalMap = new Map<string, RoomProposalItem>();
  for (const p of ctrl.proposals) proposalMap.set(p.id, p);

  // Find the newest proposal for the accent frame
  const newestProposalId = items
    .filter((it) => it.proposalId)
    .sort((a, b) => (b.createdAt || b.since || "").localeCompare(a.createdAt || a.since || ""))
    [0]?.proposalId || "";

  return (
    <SurfaceSection label={`OPEN HERE ${count}`} actions={reviewAction}>
      <SurfaceLedger count="" cols="room">
        <ul className="surface-ledger-rows">
          {items.map((item, i) => {
            if (item.proposalId) {
              return (
                <ProposalRow
                  key={`prop-${item.proposalId}`}
                  item={item}
                  proposal={proposalMap.get(item.proposalId)}
                  ctrl={ctrl}
                  isNewest={item.proposalId === newestProposalId}
                  selected={item.proposalId === selectedProposalId}
                />
              );
            }
            // HS-173: bottleneck rows
            if (item.kind === "review_bottleneck") {
              const relId = item.relationshipId || "";
              const person = relId ? peopleMap.get(relId) : undefined;
              const login = person?.login || "";
              const matchedNudge = login ? nudgeMap.get(login.toLowerCase()) : undefined;
              const mono = monogram(item.title);
              const cooldown = sentNudgeRelIds.has(relId)
                ? "NUDGED JUST NOW"
                : (person ? nudgeCooldownToken(person.nudge) : null);
              const hasNudgeStep = !!(matchedNudge?.step_id || person?.nudge?.stepId);
              const isNudgeOpen = openNudge === relId;

              // Build why from structured fields (correct plurals + day format)
              const md = item.medianDays ?? person?.medianDays ?? 0;
              const pc = item.prCount ?? person?.count ?? 0;
              const whyText = `REVIEW BOTTLENECK · ${formatDays(md)} D MEDIAN · ${pc} ${pc === 1 ? "PR" : "PRS"} WAITING`;

              return (
                <React.Fragment key={`bottleneck-${relId}-${i}`}>
                  <SurfaceLedgerRow
                    data-testid="bottleneck-row"
                    lead={mono}
                    primary={<span className="surface-primary">{item.title}</span>}
                    wrap
                    cells={
                      <span
                        className="surface-token room-why-token"
                        data-testid="bottleneck-why"
                      >
                        {whyText}
                      </span>
                    }
                    trailing={
                      <span className="room-bottleneck-verbs">
                        {cooldown ? (
                          <span className="surface-token room-nudge-cooldown" data-testid="nudge-cooldown">{cooldown}</span>
                        ) : hasNudgeStep ? (
                          <Button dense variant="ghost" onClick={() => setOpenNudge(isNudgeOpen ? null : relId)} data-testid="nudge-verb">
                            Nudge
                          </Button>
                        ) : null}
                        <Button
                          dense
                          variant="ghost"
                          onClick={() => openSurfaceOr("open-people", "/", `people:${relId}`)}
                          data-testid="bottleneck-open"
                        >
                          Open
                        </Button>
                      </span>
                    }
                  />
                  {isNudgeOpen ? (
                    <NudgeCard
                      key={`${relId}:${localNudges[relId]?.state ?? person?.nudge?.state ?? matchedNudge?.state ?? ""}`}
                      person={person}
                      needsYouItem={item}
                      nudgeItem={matchedNudge}
                      onReload={() => { setOpenNudge(null); void ctrl.load(); }}
                      onSent={() => setSentNudgeRelIds((prev) => new Set([...prev, relId]))}
                      persistedState={person?.nudge?.state ?? matchedNudge?.state}
                      local={localNudges[relId]}
                      onLocal={(next) => setLocalNudges((prev) => ({ ...prev, [relId]: next }))}
                    />
                  ) : null}
                </React.Fragment>
              );
            }
            const flight = flightForItem(flights, item);
            return (
              <SurfaceLedgerRow
                key={`${item.source}-${item.title}-${i}`}
                data-testid="needs-you-row"
                lead={emblemFor(item.source)}
                primary={<span className="surface-primary">{item.title}</span>}
                wrap
                cells={
                  <span className="room-why-cells">
                    <span
                      className="surface-token room-why-token"
                      style={{ color: severityColor(item.severity) }}
                      data-tone={severityTone(item.severity)}
                      data-testid="needs-you-why"
                    >
                      {needsYouWhyWords(item)}
                    </span>
                    <FlightChip flight={flight} />
                  </span>
                }
                trailing={<>
                  {/* Conductor F2: an item in flight shows its flight and its
                      verb; Hand to agent (Conductor K2e) only on an item no
                      agent holds, before the row's Open, as drawn. */}
                  {isInFlight(flight)
                    ? <FlightVerbs flight={flight} title={item.title} />
                    : <HandRowVerb item={{ title: item.title, source: item.source, actionItemId: item.actionItemId, projectId: ctrl.projectId, kind: item.kind, watchId: item.watchId, entityId: item.entityId, url: item.url }} />}
                  {item.verb === "decide" ? (
                    <Button dense variant="ghost" onClick={() => {
                      if (item.url) window.open(item.url, "_blank", "noopener");
                    }}>Decide</Button>
                  ) : item.url ? (
                    <Button dense variant="ghost" onClick={() => window.open(item.url!, "_blank", "noopener")}>Open</Button>
                  ) : item.actionItemId ? (
                    /* A meeting's open action: Open lands on its card in
                       Follow-through, where the owner and the date are set
                       (review of #789: the row had no control). */
                    <Button
                      dense
                      variant="ghost"
                      data-testid="needs-you-open-action"
                      onClick={() => refOpener(`action_item:${item.actionItemId}`)?.()}
                    >
                      Open
                    </Button>
                  ) : null}
                </>}
              />
            );
          })}
        </ul>
      </SurfaceLedger>
    </SurfaceSection>
  );
}

/* ── ITEMS section (PHILO-9-03, the Q3 ruling; the ratified items canvas) ──
 * The project's milestones and risks (and any other item), read from the
 * existing `GET /api/projects/{id}/items`. No Add control: items enter by
 * owner-authenticated MCP (`project.item.create`). No verbs on a row.
 * Order: late milestones first (most late first), then open risks (by
 * severity), then planned milestones by date, then missed, then the closed
 * rest. Zero items (the read succeeded): the section is omitted. A failed
 * read is ITEMS UNAVAILABLE with Retry, never empty. */

type ItemRow = {
  id: string;
  item_type: string;
  title: string;
  lifecycle: string;
  severity: string | null;
  due_at: string | null;
  details_json: string | null;
};

const ITEM_MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];

function dayNumber(ymd: string): number {
  const [y, m, d] = ymd.slice(0, 10).split("-").map(Number);
  return Math.round(new Date(y, m - 1, d).getTime() / 86_400_000);
}
function todayNumber(): number {
  const n = new Date();
  return Math.round(new Date(n.getFullYear(), n.getMonth(), n.getDate()).getTime() / 86_400_000);
}
function dueWord(ymd: string): string {
  const [, m, d] = ymd.slice(0, 10).split("-").map(Number);
  return `DUE ${ITEM_MONTHS[m - 1]} ${d}`;
}
/** Days late for a planned milestone past its date; 0 otherwise. */
function daysLate(item: ItemRow): number {
  if (item.item_type !== "milestone" || item.lifecycle !== "planned" || !item.due_at) return 0;
  return Math.max(0, todayNumber() - dayNumber(item.due_at));
}
const CLOSED = new Set(["reached", "missed", "dropped", "mitigated", "accepted", "closed", "resolved", "retired", "done"]);
const SEVERITY_ORDER: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };

function itemRank(item: ItemRow): [number, number] {
  const late = daysLate(item);
  if (late > 0) return [0, -late];
  if (item.lifecycle === "missed") return [3, 0];
  if (CLOSED.has(item.lifecycle)) return [4, 0];
  if (item.item_type === "risk") return [1, SEVERITY_ORDER[item.severity ?? ""] ?? 9];
  return [2, item.due_at ? dayNumber(item.due_at) : Number.MAX_SAFE_INTEGER];
}

function ItemCells({ item }: { item: ItemRow }) {
  const late = daysLate(item);
  let details: Record<string, unknown> = {};
  try { details = item.details_json ? JSON.parse(item.details_json) : {}; } catch { details = {}; }
  const tokens: { text: string; tone?: string }[] = [{ text: item.item_type.toUpperCase() }];
  if (item.item_type === "risk") {
    if (details.likelihood) tokens.push({ text: `LIKELIHOOD ${String(details.likelihood).toUpperCase()}` });
    if (details.impact) tokens.push({ text: `IMPACT ${String(details.impact).toUpperCase()}` });
  }
  if (item.due_at) tokens.push({ text: dueWord(item.due_at) });
  if (late > 0) tokens.push({ text: `${pluralize(late, "DAY", "DAYS")} LATE`, tone: "danger" });
  else if (item.lifecycle !== "planned" && item.lifecycle !== "open") tokens.push({ text: item.lifecycle.toUpperCase(), tone: item.lifecycle === "missed" ? "danger" : undefined });
  return (
    <>
      {tokens.map((t, i) => (
        <span key={i} className="surface-token" data-chip data-tone={t.tone} data-testid="item-token">
          {t.text}
        </span>
      ))}
    </>
  );
}

function itemLead(item: ItemRow) {
  if (daysLate(item) > 0) return <StateChip state="failure" label="" icon="●" wordless />;
  // Missed is a failure, dropped is idle; only a reached or resolved item
  // earns the success check (Codex Astra canvases r1 F7).
  if (item.lifecycle === "missed") return <StateChip state="failure" label="" icon="✗" wordless />;
  if (item.lifecycle === "dropped") return <StateChip state="idle" label="" icon="—" />;
  if (CLOSED.has(item.lifecycle)) return <StateChip state="success" label="" icon="✓" wordless />;
  if (item.item_type === "risk") return <StateChip state="warning" label="" icon="⚠" wordless />;
  return <StateChip state="idle" label="" icon="○" />;
}

function ItemsSection({ projectId, revision }: { projectId: string; revision: number }) {
  const [items, setItems] = useState<ItemRow[] | null>(null);
  // A failed read is UNAVAILABLE, never empty (Codex Astra canvases r1 F7).
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let live = true;
    apiFetch<{ items: ItemRow[] }>(`/api/projects/${encodeURIComponent(projectId)}/items?limit=200`)
      .then((r) => { if (live) { setFailed(false); setItems(r.items ?? []); } })
      .catch(() => { if (live) { setFailed(true); setItems(null); } });
    return () => { live = false; };
  }, [projectId, revision, attempt]);
  if (failed) {
    return (
      <SurfaceSection
        label="ITEMS"
        actions={
          <Button dense variant="ghost" onClick={() => setAttempt((n) => n + 1)} data-testid="items-retry">
            Retry
          </Button>
        }
      >
        <span data-testid="items-unavailable">
          <StateChip state="unreachable" label="ITEMS UNAVAILABLE" />
        </span>
      </SurfaceSection>
    );
  }
  if (items === null) return null;
  if (items.length === 0) return null;
  const sorted = [...items].sort((a, b) => {
    const [ra, sa] = itemRank(a);
    const [rb, sb] = itemRank(b);
    return ra - rb || sa - sb || a.title.localeCompare(b.title);
  });
  return (
    <SurfaceSection label={countLabel("ITEMS", items.length)}>
      <SurfaceLedger count="" cols="room">
        <ul className="surface-ledger-rows" data-testid="items-section">
          {sorted.map((item) => (
            <SurfaceLedgerRow
              key={item.id}
              data-testid="item-row"
              expands={false}
              wrap
              lead={itemLead(item)}
              primary={<span className="surface-primary">{item.title}</span>}
              cells={<ItemCells item={item} />}
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
  ctrl,
}: {
  room: RoomSnapshot;
  onReload: () => void;
  stewardCtrl: ReturnType<typeof useStewardController>;
  ctrl: ReturnType<typeof useProjectRoomController>;
}) {
  const [busyWatch, setBusyWatch] = useState<string>("");

  if (room.sources.state !== "ok") return null;
  const { items, count } = room.sources;

  // HS-169-04: act on every watchId in the merged row.
  const handlePause = async (watchIds: string[]) => {
    setBusyWatch(watchIds[0]);
    try { await Promise.all(watchIds.map(api.pauseWatch)); onReload(); }
    catch { /* non-fatal */ }
    finally { setBusyWatch(""); }
  };

  const handleResume = async (watchIds: string[]) => {
    setBusyWatch(watchIds[0]);
    try { await Promise.all(watchIds.map(api.resumeWatch)); onReload(); }
    catch { /* non-fatal */ }
    finally { setBusyWatch(""); }
  };

  const handleRetire = async (watchIds: string[]) => {
    setBusyWatch(watchIds[0]);
    try { await Promise.all(watchIds.map(api.retireWatch)); onReload(); }
    catch { /* non-fatal */ }
    finally { setBusyWatch(""); }
  };

  const sorted = [...items].sort((a, b) => {
    const order = { live: 0, paused: 1, cant_check: 2 } as Record<string, number>;
    const aOrder = a.suggested ? 3 : (order[a.state] ?? 1);
    const bOrder = b.suggested ? 3 : (order[b.state] ?? 1);
    return aOrder - bOrder;
  });

  // HS-172-06: suggested sources sit ABOVE existing sources
  const suggestions = ctrl.suggestedSources;

  // SOURCES N counts accepted sources only (F9 ruling); count absent at zero
  const acceptedCount = items.filter((s) => !s.suggested).length;

  return (
    <SurfaceSection
      label={acceptedCount > 0 ? `SOURCES ${acceptedCount}` : "SOURCES"}
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
          {/* HS-172-06: suggested sources sit above existing */}
          {suggestions.map((sug) => {
            // Resolve meeting title from the needs-you items or proposals
            const mtgItem = room.needsYou.state === "ok"
              ? room.needsYou.items.find((it) => it.meetingTitle)
              : undefined;
            const sugMeetingTitle = mtgItem?.meetingTitle || "";
            return (
            <SurfaceLedgerRow
              key={`sug-${sug.id}`}
              data-testid="suggested-source-row"
              lead={emblemFor(sug.provider)}
              primary={<span className="surface-primary" data-testid="suggested-ref">{sug.reference}</span>}
              wrap
              cells={
                <span className="surface-token room-chip-faint" data-testid="suggested-caption">
                  {`SUGGESTED · FROM ${sugMeetingTitle ? sugMeetingTitle.toUpperCase() : "MEETING"} ${formatMMDD(sug.createdAt)}`}
                </span>
              }
              trailing={
                <span className="room-suggestion-verbs" data-testid="suggested-verbs">
                  <Button dense variant="primary" loading={ctrl.suggestionBusy === sug.reference} onClick={() => void ctrl.handleAddSuggestion(sug.reference)} data-testid="suggested-add">
                    Add
                  </Button>
                  <Button dense variant="ghost" onClick={() => void ctrl.handleDismissSuggestion(sug.reference)} data-testid="suggested-dismiss">
                    Dismiss
                  </Button>
                </span>
              }
            />
            );
          })}
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
                    <>
                      {/* S-3 / HS-169-07 park candidate: the design names "Fix"
                          (opens Adjust) beside "Remove".  Adjust is withheld in
                          this phase; "Fix" will arrive with the extracted
                          AdjustWell component (PUT /api/watches/{id}/rules). */}
                      <ConfirmVerb
                        label="Remove"
                        confirmLabel="Remove?"
                        busy={busyWatch === src.watchIds[0]}
                        onConfirm={() => void handleRetire(src.watchIds)}
                      />
                    </>
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
              // PHILO-9-03 (F15, UX-CANON A.11): this Add had no action -- a
              // verb that does nothing is a lie. The hub's source read never
              // sets `suggested` (project_service.py: every source item is
              // `suggested: False`); a suggestion is added from the SUGGESTED
              // rows above (Add / Dismiss, wired). The verb is withheld.
              return (
                <SurfaceLedgerRow
                  key={src.watchId}
                  lead={emblemFor(src.provider)}
                  primary={<span className="surface-primary">{src.scope}</span>}
                  wrap
                  cells={<span className="surface-token room-chip-faint">SUGGESTED</span>}
                  data-testid="source-suggested-row"
                />
              );
            }

            /* LINE 1: emblem . scope (primary) . [gap] . tokens left-aligned . [spacer] . verbs
               LINE 2: checked + host, starting at the scope's left edge.
               The tokens sit INSIDE the primary slot so they follow the scope
               inline, not right-aligned as cells.
               HS-175-04: meeting rows use the same grammar — one grammar for
               all source rows. CHECKED/NEVER chip replaces "checked N ago"
               when no egress host (the meeting source is local-only). */
            const isMeeting = src.provider === "meeting";
            return (
              <SurfaceLedgerRow
                key={src.watchId}
                lead={emblemFor(src.provider)}
                data-testid={isMeeting ? "source-meeting-row" : undefined}
                primary={
                  <span className="room-source-primary">
                    <span className="surface-primary" data-testid="source-scope">{src.scope}</span>
                    {src.tokens.map((tok, ti) => (
                      <span key={ti} className="surface-token room-source-tok" data-testid={isMeeting ? "source-meeting-token" : undefined}>
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
                    loading={busyWatch === src.watchIds[0]}
                    onClick={() => {
                      if (src.state === "paused") void handleResume(src.watchIds);
                      else void handlePause(src.watchIds);
                    }}
                    data-testid={isMeeting ? "source-meeting-verb" : undefined}
                  >
                    {src.state === "paused" ? "Resume" : "Pause"}
                  </Button>
                }
              >
                <div className="room-source-line2">
                  {/* HS-175 counsel C7(b): a paused Watch SAYS so (idle chip)
                      beside its Resume verb -- one grammar for MTG / GH / J. */}
                  {src.state === "paused" ? (
                    <span data-testid="source-paused"><StateChip state="idle" label="PAUSED" /></span>
                  ) : null}
                  {/* PHILO-15 B69: the source's one state, the one Needs you shows. */}
                  {src.freshness === "stale" ? (
                    <span data-testid="source-freshness"><StateChip state="warning" label="STALE" /></span>
                  ) : src.freshness === "quiet" && src.quietUntil ? (
                    <span data-testid="source-freshness">
                      <StateChip state="idle" label={`QUIET UNTIL ${formatTimeShort(src.quietUntil)}`} />
                    </span>
                  ) : null}
                  {isMeeting ? (
                    <span data-testid="source-meeting-checked">
                      {src.checkedAt ? (
                        <StateChip state="success" label={`CHECKED ${formatTimeShort(src.checkedAt)}`} icon={"●"} />
                      ) : (
                        <StateChip state="idle" label="NEVER" />
                      )}
                    </span>
                  ) : (
                    <>
                      {src.checkedAt ? (
                        <span className="room-source-checked">checked {humanTime(src.checkedAt)}</span>
                      ) : null}
                      {src.host ? <EgressChip label={src.host} scope="cloud" title={src.host} /> : null}
                    </>
                  )}
                </div>
              </SurfaceLedgerRow>
            );
          })}
        </ul>
      </SurfaceLedger>
    </SurfaceSection>
  );
}

/* ── RECEIPTS section (HS-174-04: pipeline event receipts with origin badge) ── */

function ReceiptsSection({ room }: { room: RoomSnapshot }) {
  if (room.receipts.state !== "ok") return null;
  const { items } = room.receipts;
  if (items.length === 0) return null;

  return (
    <SurfaceSection label={countLabel("RECEIPTS", items.length)}>
      <SurfaceLedger count="" cols="room">
        <ul className="surface-ledger-rows">
          {items.map((item) => {
            const egress = egressForEvent({ origin: item.origin, caller: item.caller });
            const label = receiptLabel({ op: item.op, title: item.title, outcome: item.outcome });
            // PHILO-9-03 (Codex Astra r1 finding 1): the row says what
            // happened -- a refused write is ✗ REFUSED + the plain reason,
            // never a success chip.
            const face = receiptFace(item.outcome);
            return (
              <SurfaceLedgerRow
                key={item.id}
                lead={<StateChip state={face.state} label="" icon={face.icon} wordless={Boolean(face.word)} />}
                primary={
                  <span className="surface-primary" data-outcome={item.outcome || "ok"} data-code={item.reason ?? undefined}>
                    {label}
                  </span>
                }
                wrap
                expands={false}
                data-testid="receipt-row"
                cells={
                  <>
                    {face.word ? (
                      <span data-testid="receipt-outcome"><StateChip state={face.state} label={face.word} /></span>
                    ) : null}
                    {face.word && item.reason ? (
                      <span className="surface-token" data-chip data-testid="receipt-reason">{refusalWord(item.reason)}</span>
                    ) : null}
                    {egress.label ? (
                      <EgressChip label={egress.label} scope={egress.scope} data-testid="receipt-egress" />
                    ) : null}
                    {item.timestamp ? (
                      <span className="surface-token" data-muted>{humanTime(item.timestamp)}</span>
                    ) : null}
                  </>
                }
              />
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
          {/* S-2: the design's line is "GitHub · 2 opened · 1 merged" */}
          <p className="room-since-group-head surface-primary">
            {group.source}{group.summary ? ` · ${group.summary}` : ""}
          </p>
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

/** PHILO-11-05a (canvas B4, B4b): a decision row is a decision RECORD
 *  (design 6a), also when it is marked `source="meeting"`. The row unfolds
 *  in place and holds the record's SEND well (the seat); it carries
 *  PREPARED ×K when a send waits. Its `Open` opened nothing for a record
 *  (G1, ledgered), so it is withheld; a row with a real URL keeps its Open. */
function RoomDecisionRow({ dec, cells, ...rest }: React.ComponentProps<typeof SurfaceLedgerRow> & {
  dec: { id: string; text: string; kind?: string };
}) {
  const [open, setOpen] = useState(false);
  // PHILO-15 08 (Astra #983 r2): a confirmed ACTION's record is the anchor
  // of its commitment, not a decision: it reads "Action:", says ACTION, and
  // carries no decision Send well.
  if (dec.kind === "action") {
    return (
      <SurfaceLedgerRow {...rest} lineLabel={`Action: ${dec.text}`}
        cells={<><span className="surface-token" data-testid="room-row-kind">ACTION</span>{cells}</>} />
    );
  }
  return (
    <SurfaceLedgerRow {...rest} open={open} onToggle={() => setOpen((o) => !o)}
      lineLabel={`Decision: ${dec.text}`}
      cells={<>{cells}<DecisionRecordPreparedChip id={dec.id} /></>}>
      {open ? <DecisionRecordSendWells id={dec.id} text={dec.text} /> : null}
    </SurfaceLedgerRow>
  );
}

function DecisionsCommitmentsSection({ room }: { room: RoomSnapshot }) {
  const decisionItems = room.decisions.state === "ok" ? room.decisions.items : [];
  const commitmentItems = room.commitments.state === "ok" ? room.commitments.items : [];

  // HS-172-03: fold commitments into their decision row when the decision
  // carries a commitmentId that matches a commitment's id. The merged row
  // shows OWNER + BY DUE + CONFIRMED; the commitment is not listed separately.
  const foldedCommitmentIds = new Set<string>();
  const commitmentById = new Map(commitmentItems.map((c) => [c.id, c]));
  for (const dec of decisionItems) {
    if (dec.commitmentId && commitmentById.has(dec.commitmentId)) {
      foldedCommitmentIds.add(dec.commitmentId);
    }
  }
  const unfoldedCommitments = commitmentItems.filter((c) => !foldedCommitmentIds.has(c.id));

  const total = decisionItems.length + unfoldedCommitments.length;
  if (total === 0) return null;

  return (
    <SurfaceSection label={`DECISIONS & COMMITMENTS ${total}`}>
      <SurfaceLedger count="" cols="room">
        <ul className="surface-ledger-rows">
          {decisionItems.map((dec) => {
            // HS-172-03: proposal-derived decisions carry source=meeting
            const isProposal = dec.source === "meeting";
            const confirmedTime = dec.confirmedAt ? formatTimeShort(dec.confirmedAt) : "";
            const foldedCommitment = dec.commitmentId ? commitmentById.get(dec.commitmentId) : undefined;

            // Build WAS tokens from changed fields only (F5 ruling)
            const wasParts: string[] = [];
            if (dec.was) {
              if (dec.was.text) {
                const truncated = dec.was.text.length > 40
                  ? `${dec.was.text.slice(0, 40)}...`
                  : dec.was.text;
                wasParts.push(`WAS "${truncated}"`);
              }
              if (dec.was.due) wasParts.push(`WAS BY ${dec.was.due.toUpperCase()}`);
              if (dec.was.owner) wasParts.push(`WAS ${dec.was.owner}`);
            }

            if (isProposal) {
              // Merged caption: OWNER MAREK · BY FRI · CONFIRMED 09:15 + WAS tokens
              const ownerName = foldedCommitment?.owner;
              const dueDateRaw = foldedCommitment?.dueAt;
              // Format due as short day name (FRI) when within ~7 days, else date
              const dueLabel = dueDateRaw ? formatDueShort(dueDateRaw) : "";

              return (
                <RoomDecisionRow
                  dec={dec}
                  key={`dec-${dec.id}`}
                  data-testid="decision-row"
                  lead="MTG"
                  primary={<span className="surface-primary">{dec.text}</span>}
                  wrap
                  cells={
                    <>
                      {ownerName ? (
                        <span className="surface-token">OWNER {ownerName.toUpperCase()}</span>
                      ) : null}
                      {dueLabel ? (
                        <span className="surface-token">BY {dueLabel.toUpperCase()}</span>
                      ) : null}
                      {dec.done ? (
                        // PHILO-15 B70: a done action reads DONE, not CONFIRMED.
                        <span className="surface-token room-confirmed-token" data-testid="done-state">
                          {dec.doneAt ? `DONE · ${formatTimeShort(dec.doneAt)}` : "DONE"}
                        </span>
                      ) : (
                        <span className="surface-token room-confirmed-token" data-testid="confirmed-state">
                          CONFIRMED {confirmedTime}
                        </span>
                      )}
                      {wasParts.map((w, wi) => (
                        <span key={wi} className="surface-token room-was-token">{w}</span>
                      ))}
                    </>
                  }
                />
              );
            }

            return (
              <RoomDecisionRow
                dec={dec}
                key={`dec-${dec.id}`}
                data-testid="decision-row"
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
                  ) : undefined
                }
              />
            );
          })}
          {unfoldedCommitments.map((c) => (
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

/** Resolve the model host label for the ask well's egress chip.
 *  Article III: the chip names the HOST at the point of decision.
 *  1. Reads the assignment to find the profile_id.
 *  2. Looks up the InferenceTarget with that profile_id in the desk store
 *     to find the endpoint URL (the host the Settings face shows).
 *  3. Falls back to the boundary label (LOCAL/CLOUD) only when no host exists.
 *  4. NOT SET when unassigned. */
function useModelLabel(projectId: string): { host: string; scope: "local" | "cloud" | undefined } {
  const [host, setHost] = useState("NOT SET");
  const [scope, setScope] = useState<"local" | "cloud" | undefined>(undefined);
  const deskTargets = useDesk((s) => s.inferenceTargets);
  // HS-200-41 — the defect on this very seam. The hook used to re-read only
  // on `[projectId, targets]`, and `inferenceTargets` moves only when the
  // whole desk calls `refresh()`. So the owner pressed `Choose`, assigned a
  // model, came back — and the chip still read `MODEL · NOT SET`. That is
  // the STATE half of return-to-task failing on the surface this story
  // sends him back to, so it is fixed here, on the same subscription.
  const [freshTargets, setFreshTargets] = useState<InferenceTarget[] | null>(null);
  const [reread, setReread] = useState(0);
  const targets = freshTargets ?? deskTargets;
  useEffect(
    () =>
      onReturnToTask(() => {
        void apiFetch<{ targets?: InferenceTarget[] }>("/api/inference-targets")
          .then((r) => setFreshTargets(r.targets ?? []))
          .catch(() => { /* the assignment re-read below still runs */ });
        setReread((n) => n + 1);
      }),
    [],
  );
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
        // Look up the InferenceTarget by profile_id for the real host.
        const target = targets.find((t) => t.profile_id === entry.profile_id);
        // Extract hostname from the endpoint URL, or use node, or fall back to boundary.
        let resolvedHost = "";
        if (target?.endpoint) {
          try {
            resolvedHost = new URL(target.endpoint).host;
          } catch {
            resolvedHost = target.endpoint;
          }
        } else if (target?.node) {
          resolvedHost = target.node;
        }
        // Determine scope from the target's boundary or kind.
        const boundary = target?.boundary || entry.boundary || "";
        const isLocal = boundary === "same_device" || boundary === "private_network";
        setHost(resolvedHost || boundaryToLabel(boundary) || entry.label || "Assigned");
        setScope(isLocal ? "local" : "cloud");
      } else {
        setHost("NOT SET");
        setScope(undefined);
      }
    }).catch(() => { /* non-fatal */ });
    return () => { cancelled = true; };
  }, [projectId, targets, reread]);
  return { host, scope };
}

function boundaryToLabel(boundary: string): string {
  switch (boundary) {
    case "same_device": return "LOCAL";
    case "private_network": return "LAN";
    case "paired_device": return "PAIRED";
    case "private_mesh": return "MESH";
    case "external_service": return "CLOUD";
    default: return "";
  }
}

/** The Room's ask, as ONE controller.
 *
 *  HS-200-41 F5: the unfinished list and the ask well are TWO faces over one
 *  state. They used to be one component, which put a ledger inside the
 *  composer's sticky foot — five rows and the Room was gone behind them. The
 *  state lives here so the list can sit in the body as its own section, where
 *  the design's posture-6 grammar puts it, while the well stays sticky. */
export function useRoomAsk(projectId: string, projectName: string) {
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState<AskRunResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  // The ask no longer dies with the tab. The words are written to
  // `project_ask_tasks` BEFORE the run goes out (ruling B3), so a restart, a
  // crash or a trip to Settings finds them again.
  const [unfinished, setUnfinished] = useState<AskTask[]>([]);
  const [working, setWorking] = useState<{ id: string; verb: "resume" | "discard" } | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const loadUnfinished = useCallback(async () => {
    if (!projectId) return;
    const page = await listUnfinishedAsks({ projectId, limit: 5 });
    setUnfinished(page.items);
  }, [projectId]);

  useEffect(() => { void loadUnfinished(); }, [loadUnfinished]);
  // The generalisation the design's D3 called MISSING: the Room's ask well
  // subscribes to return-to-task like every other face holding unfinished
  // work, so readiness and the saved row re-read WITHOUT a reload.
  useEffect(() => onReturnToTask(() => { void loadUnfinished(); }), [loadUnfinished]);

  const ask = async () => {
    const purpose = prompt.trim();
    if (!purpose || busy) return;
    setBusy(true);
    setError("");
    const grounding = {
      meeting_ids: [],
      artifact_ids: [],
      refs: [`project:${projectId}`],
      expand: "summary" as const,
    };
    // Save FIRST: the row and its invocation identity exist before anything
    // is dispatched, so an answer that lands after the tab is gone can be
    // claimed instead of paid for twice (ruling B3). A refusal here does not
    // block the work — durability is the bonus, never the gate.
    const task = await saveAskTask(projectId, {
      purpose,
      lens: "Project",
      grounding,
    });
    const answer = await runAsk({
      prompt: purpose,
      lens: "Project",
      context: [
        { id: projectId, kind: "project", ref: `project:${projectId}`, title: projectName },
      ],
      grounding,
      ...(task ? { invocationId: task.invocationId } : {}),
    });
    setBusy(false);
    if (!answer.ok) {
      // Record WHY it stopped, from the hub's own refusal CODE — never its
      // sentence (ruling B5). The server resolves the token against its live
      // placement and quotes the engine itself; nothing written here reaches
      // the row. The ask stays unfinished and fully resumable either way.
      let recorded = false;
      if (task && answer.refusalCode) {
        recorded = (await stopAskTask(task.id, answer.refusalCode)).ok;
      }
      // F6: the failure is said ONCE. When it landed on a row, the row says
      // it — in the engine's own words, beside the verb that acts on it. The
      // inline line survives only for a failure that reached no row at all
      // (no saved row, or a transport failure the hub never coded), where it
      // is the only thing that can speak.
      if (!recorded) setError(answer.output);
      void loadUnfinished();
      return;
    }
    setResult(answer);
    // Settle the record against the answer the run just wrote. The resume
    // route reads `ask_results` first, finds it, marks the task accepted and
    // dispatches NOTHING — there is no separate accept route, and minting a
    // second identity to settle one is the double-spend B3 forbids.
    if (task) await resumeAskTask(task.id);
    void loadUnfinished();
  };

  const resume = async (task: AskTask) => {
    setWorking({ id: task.id, verb: "resume" });
    setError("");
    const outcome = await resumeAskTask(task.id);
    setWorking(null);
    if (!outcome.ok) { setError(outcome.error); return; }
    setPrompt(task.purpose);
    if (outcome.answer) setResult(outcome.answer);
    await loadUnfinished();
    inputRef.current?.focus();
  };

  const discard = async (task: AskTask) => {
    setWorking({ id: task.id, verb: "discard" });
    await discardAskTask(task.id);
    setWorking(null);
    await loadUnfinished();
  };

  return {
    prompt, setPrompt, result, busy, error, unfinished, working,
    inputRef, ask, resume, discard,
  };
}

export type RoomAsk = ReturnType<typeof useRoomAsk>;

/** UNFINISHED — the saved work, in the Room BODY as its own section.
 *
 *  F5: this used to render inside `.room-ask-container`, which is
 *  `position: sticky; bottom: 0`. A ledger does not belong in a composer's
 *  foot: at five rows it covered every other section and the Room was a wall
 *  of unfinished asks over dead space. */
function RoomUnfinishedSection({ ask }: { ask: RoomAsk }) {
  const { unfinished, working } = ask;
  if (unfinished.length === 0) return null;
  // The ratified board draws UNFINISHED 1 — ONE row, one filled primary. It
  // never showed a list. Five filled primaries is no lead at all, so the
  // filled verb survives only while the board's case holds; beyond it every
  // row draws the quiet verb. Flagged to the owner as a board question.
  const lead = unfinished.length === 1;
  return (
    <SurfaceSection label={countLabel("UNFINISHED", unfinished.length)}>
      <TaskResumeList data-testid="room-unfinished">
        {unfinished.map((task) => (
          <TaskResume
            key={task.id}
            data-testid={`room-unfinished-${task.id}`}
            purpose={task.purpose}
            state={task.state}
            savedAt={task.savedAt}
            settledAt={task.settledAt}
            recipe={task.recipeKey}
            stoppedReason={task.stoppedReason}
            stoppedCode={task.stoppedCode}
            custody={task.custody}
            primary={lead}
            busy={working?.id === task.id && working.verb === "resume"}
            onVerb={() => void ask.resume(task)}
            onDiscard={() => void ask.discard(task)}
            discardBusy={working?.id === task.id && working.verb === "discard"}
          />
        ))}
      </TaskResumeList>
    </SurfaceSection>
  );
}

/** BRIEFS — the kept preparation briefs, attached to this Project (HS-200-11
 *  AC4).  Absent at zero (A.8). */
function RoomBriefsSection({ prepare }: { prepare: PrepareController }) {
  const { kept } = prepare;
  if (kept.length === 0) return null;
  return (
    <SurfaceSection label={countLabel("BRIEFS", kept.length)}>
      <SurfaceLedger count="" cols="room">
        <ul className="surface-ledger-rows" data-testid="room-briefs">
          {kept.map((brief) => {
            const coverage = coverageToken(brief.manifest.coverage);
            const keptAt = clockToken("KEPT", brief.keptAt);
            return (
              <SurfaceLedgerRow
                key={brief.id}
                data-testid="room-brief-row"
                lead={<span className="prepare-emblem" aria-hidden="true">BRF</span>}
                primary={<span className="surface-primary">{brief.purpose}</span>}
                cells={
                  <span className="prepare-source-cells">
                    {keptAt ? <span className="surface-token" data-chip>{keptAt}</span> : null}
                    {coverage ? (
                      <StateChip state={brief.manifest.coverage.complete ? "success" : "warning"} label={coverage} />
                    ) : null}
                  </span>
                }
                trailing={
                  <Button dense variant="ghost" aria-label={`Open: ${brief.purpose}`} data-testid="room-brief-open" onClick={() => void prepare.openBrief(brief)}>
                    Open
                  </Button>
                }
                wrap
                open
                expands={false}
              />
            );
          })}
        </ul>
      </SurfaceLedger>
    </SurfaceSection>
  );
}

/** The Room's ask (Phase 16: the kit's AskWell: the sunken paper well with
 *  the mic on its right edge, the model's egress chip beside it). The
 *  Room window on the desk (the Project's drawer) draws the same well. */
export function RoomAskWell({
  ask,
  projectId,
  onOpenRef,
  onPrepare,
}: {
  ask: RoomAsk;
  projectId: string;
  onOpenRef: (ref: string) => void;
  /** HS-200-11: `Result → Preparation brief` hands the words to the Prepare
   *  posture; nothing here requires a calendar (AC1). */
  onPrepare?: (purpose: string) => void;
}) {
  const { prompt, setPrompt, result, error, inputRef } = ask;
  const receipt = result?.groundingReceipt;
  const groundedCount = groundedMatchCount(receipt ?? null);
  const modelLabel = useModelLabel(projectId);

  return (
    <div className="room-ask-section" data-testid="room-ask-well">
      {result ? (
        <div className="surface-aerogel room-ask-answer" data-testid="room-ask-answer">
          <Material>{result.output}</Material>
          {receipt && groundedCount > 0 ? (
            <p className="desk-ask-grounded">
              GROUNDED ON {groundedCount} OF {receipt.matchedCount}
            </p>
          ) : null}
          <CitationChips refs={receipt?.sourceRefs || []} onOpen={onOpenRef} />
        </div>
      ) : null}
      {error ? <p className="room-ask-error">{error}</p> : null}
      <div className="room-ask-well" data-testid="room-ask-input-well">
        {/* Phase 16 (the interior kit, §11 "AskWell"): the library string
            well (sunken paper, the mic on its right edge) replaces the raw
            input HS-170-04 left for a redesign. */}
        <StringGadget
          label="Ask this project"
          value={prompt}
          onChange={setPrompt}
          placeholder="Ask this project…"
          micLabel="Speak to ask this project"
          micDraftScope={`project-ask-${projectId}`}
          inputRef={inputRef}
          inputProps={{ className: "room-ask-input" }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void ask.ask();
            }
          }}
        />
        {onPrepare ? (
          <span className="room-ask-result" data-testid="room-ask-result">
            <CycleGadget
              label="Result"
              value="answer"
              options={RESULT_OPTIONS}
              onChange={(next) => { if (next === "brief") onPrepare(prompt); }}
            />
          </span>
        ) : null}
        {/* Condition 8: NOT SET = idle/muted tone (no scope), assigned = scope from assignment */}
        {modelLabel.host === "NOT SET" ? (
          <span className="room-ask-model-chip">
            <EgressChip label="MODEL · NOT SET" className="room-egress-idle" title="No model assigned" />
            <Button
              dense
              variant="ghost"
              onClick={() => {
                // The verb he leaves is `Choose`, but `Choose` is GONE once a
                // model is set — so the place to come back to is the well he
                // was typing in, with his words still in it (design D2(a)).
                rememberTaskFocus(inputRef.current);
                openSurfaceOr("configure-runs-on", "/settings", "models");
              }}
            >
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
        <Button dense variant="ghost" className="room-ask-submit-hidden" aria-label="Submit" onClick={() => void ask.ask()} tabIndex={-1}>
          Submit
        </Button>
      </div>
    </div>
  );
}

/* ── Desk memory: the recall face (HS-200-13) lives in ./recall ── */

/* ── HISTORY wing ── */

interface HistoryEntry {
  id: string;
  kind: string;
  phrase: string;
  time: string;
  source: string;
  occurredAt: string;
  targetRef: string | null;
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
    targetRef: c.targetRef ?? null,
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
        count={todayCount > 0 ? `${todayCount} today` : "Nothing today"}
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
              <input // UX-CANON: needs redesign (HS-170-04)
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
              <HistoryEntryRow key={entry.id} entry={entry} />
            ))}
          </SurfaceStreamDay>
        ))}
      </SurfaceStream>
    </div>
  );
}

/** PHILO-13-06 (B1): an activity row opens the object it touched; a row
 *  about the Room itself names nothing to open and draws no verb. */
function HistoryEntryRow({ entry }: { entry: HistoryEntry }) {
  // A change to the Room itself (`project:<id>`) opens what is already open.
  const open = entry.targetRef?.startsWith("project:") ? null : refOpener(entry.targetRef);
  return (
    <SurfaceStreamEntry
      when={entry.time}
      dense
      verbs={open ? (
        <Button dense variant="ghost" onClick={open} aria-label={`Open: ${entry.phrase}`} data-testid="history-entry-open">
          Open
        </Button>
      ) : undefined}
    >
      <span data-testid="history-entry">{entry.phrase}</span>
    </SurfaceStreamEntry>
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
  useAgentFlightsLive();
  const agentFlights = useAgentFlights((s) => s.flights);
  const loading = ctrl.loadStatus === "loading";
  // A write in another window (a meeting filed, an update published, an
  // agent's write) shows in this Room with no reload.
  useOnDeskChanged(() => { void ctrl.load(true); });

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

  // PHILO-13-15 (C5): the Room link { projectId, updateId, destinationId }
  // from `Send to ▸`: the linked update opens in the Update posture (also
  // when the Room is open on another update), its well picked. A failed
  // latest-update read opens the SEND well with the failure and Retry (P8).
  const { openUpdate } = updateCtrl;
  const openLinkedUpdate = useCallback(async (updateId: string) => {
    if (!ctrl.projectId) return false;
    // A failed read rejects: the link shows the failure with Retry (windowSend.tsx).
    const u = (await fetchUpdates(ctrl.projectId)).find((x) => x.id === updateId);
    if (!u) return false;
    openUpdate(u);
    return true;
  }, [ctrl.projectId, openUpdate]);
  const sendFailed = useRoomSendLink(ctrl.projectId, openLinkedUpdate);

  // PHILO-13-14 (C4): the palette's `Draft update for <project>` opens this
  // Room in its Update posture, as the `Draft update` Button does.
  const { enterUpdates } = updateCtrl;
  useEffect(() => {
    const projectId = ctrl.projectId;
    if (!projectId) return;
    const take = () => { if (takeRoomUpdatesRequest(projectId)) void enterUpdates(); };
    take();
    window.addEventListener(ROOM_UPDATES_EVENT, take);
    return () => window.removeEventListener(ROOM_UPDATES_EVENT, take);
  }, [ctrl.projectId, enterUpdates]);
  // Phase 16: the Room window's History and Steward verbs (the drawer's
  // FilterBar and Sources section) open this Room AT that place.
  const { enterSteward } = stewardCtrl;
  const { setView } = ctrl;
  useEffect(() => {
    const projectId = ctrl.projectId;
    if (!projectId) return;
    const take = () => {
      const place = takeRoomAtRequest(projectId);
      if (place === "history") setView("history");
      else if (place === "steward") void enterSteward();
    };
    take();
    window.addEventListener(ROOM_AT_EVENT, take);
    return () => window.removeEventListener(ROOM_AT_EVENT, take);
  }, [ctrl.projectId, enterSteward, setView]);
  // PHILO-14 A2b: a proposal row elsewhere (Needs you) opens this Room with
  // that proposal selected in OPEN HERE. `seq` counts the requests, so the
  // same proposal asked for again is revealed again (A5b, Astra r1).
  const [proposalRequest, setProposalRequest] = useState({ id: "", seq: 0 });
  const selectedProposalId = proposalRequest.id;
  const sendFailure = sendFailed && ctrl.projectId ? (
    <div data-send="well" data-testid="send-well" data-doc={`project:${ctrl.projectId}`} role="group"
      aria-label="Send the latest update">
      <SurfaceSection label="SEND">
        <Unreadable what="LATEST UPDATE" testid="room-latest-unreadable"
          onRetry={() => retryRoomLink(ctrl.projectId as string)} />
      </SurfaceSection>
    </div>
  ) : null;

  // HS-200-41 — one controller, two faces: UNFINISHED sits in the body as a
  // section, the well stays sticky at the foot (F5).
  const askCtrl = useRoomAsk(ctrl.projectId, ctrl.projectName);
  const standingPages = useStandingPages("project", ctrl.projectId);

  // HS-200-11 — the Prepare posture: one manual preparation path over the
  // Room's read sources, its carried decisions and its open commitments.
  const prepareCtrl = usePrepareController(ctrl.projectId, () => void ctrl.load());

  // PHILO-14 A5b (Astra r1 on #965): a proposal request REVEALS the
  // proposal, whatever the Room shows. Every posture (Review, Update,
  // Steward, Prepare) closes the way its own Close does, except Update,
  // which steps aside with no write (a kept Update place is not restored
  // over the request), the Room goes to its ROOM wing (not History),
  // and the selected row scrolls into view.
  const revealProposal = useRef<(id: string) => void>(() => undefined);
  revealProposal.current = (id: string) => {
    if (reviewCtrl.posture !== "off") reviewCtrl.exitReview();
    // The Update posture steps aside and NEVER writes (Muad'Dib's ruling on
    // Astra r2): its text, kept draft and failure stay; Draft update brings
    // the editor back. Always: it also forgets a kept Update place that a
    // just-mounted Room is still restoring (393 opens a fresh Room window).
    updateCtrl.stepAside();
    if (stewardCtrl.posture !== "off") stewardCtrl.exitSteward();
    if (prepareCtrl.posture !== "off") prepareCtrl.exit();
    if (ctrl.view !== "room") ctrl.setView("room");
    setProposalRequest((prev) => ({ id, seq: prev.seq + 1 }));
  };
  useEffect(() => {
    const projectId = ctrl.projectId;
    if (!projectId) return;
    const take = () => {
      const proposal = takeRoomProposalRequest(projectId);
      if (proposal) revealProposal.current(proposal);
    };
    take();
    window.addEventListener(ROOM_PROPOSAL_EVENT, take);
    return () => window.removeEventListener(ROOM_PROPOSAL_EVENT, take);
  }, [ctrl.projectId]);
  const roomBodyRef = useRef<HTMLDivElement>(null);
  const revealedSeq = useRef(0);
  // Once per request: when the row is drawn (the wing switch and a posture's
  // close render first), it scrolls into view; a later re-read never pulls
  // the owner back to it.
  useEffect(() => {
    if (!proposalRequest.seq || revealedSeq.current === proposalRequest.seq) return;
    const row = roomBodyRef.current?.querySelector<HTMLElement>(
      "[data-testid=proposal-row][data-selected]",
    );
    if (!row) return;
    revealedSeq.current = proposalRequest.seq;
    row.scrollIntoView?.({ block: "center" });
  });

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

  // The unscoped surface is Desk memory: the recall face (HS-200-13,
  // posture 5) -- CURRENT / SUPERSEDED / OWED over one query, never a
  // dead empty state.
  // HS-200-11's `q:<sentence>` scope (`Find support` opens Desk memory WITH
  // the sentence, searched; counsel P1-5) reaches the recall face here.
  if (!ctrl.projectId)
    return <RecallFace initialQuery={scope?.startsWith("q:") ? scope.slice("q:".length).trim() : ""} />;

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
        {sendFailure}
        <UpdatePosture ctrl={updateCtrl} />
      </>
    );
  }

  if (stewardCtrl.posture !== "off") {
    return (
      <>
        {hero ? hero(<Button dense variant="ghost" onClick={handleRefresh}>Refresh</Button>) : null}
        <StewardPosture
          ctrl={stewardCtrl}
          onOpenReview={(reviewId: string) => {
            stewardCtrl.exitSteward();
            void reviewCtrl.enterReview(reviewId);
          }}
        />
      </>
    );
  }

  if (prepareCtrl.posture !== "off") {
    return (
      <>
        {hero ? hero(<Button dense variant="ghost" onClick={handleRefresh}>Refresh</Button>) : null}
        <div className="room-body" data-testid="room-body">
          <PreparePosture
            ctrl={prepareCtrl}
            projectName={ctrl.projectName}
            onOpenRef={ctrl.openProjectRef}
            onResultChange={(purpose) => {
              // `Result → Answer` walks back to the Room well with his words.
              askCtrl.setPrompt(purpose);
              prepareCtrl.exit();
            }}
          />
        </div>
      </>
    );
  }

  const readReceipt = ctrl.readAt ? `READ ${formatTimeShort(ctrl.readAt)}` : "";
  const nextCheck = ctrl.room?.sources.state === "ok" ? ctrl.room.sources.nextCheckAt : null;

  // S-1: footer receipt omits zero parts — "Nothing today" / "Nothing this week"
  const historyReceipt = (() => {
    const { todayCount: t, weekCount: w } = historyCounts;
    if (t === 0 && w === 0) return "NOTHING THIS WEEK";
    if (t === 0) return `NOTHING TODAY · ${w} THIS WEEK`;
    if (w === 0) return `${t} TODAY · NOTHING THIS WEEK`;
    return `${t} TODAY · ${w} THIS WEEK`;
  })();
  // Conductor F2 (K6): a commitment an agent's merged PR closed names
  // itself on the receipt line (K4's follow-through: the PR, the close).
  const merged = mergeReceipt(agentFlights, ctrl.projectId);
  const footerReceipt = ctrl.view !== "history" && merged ? (
    <span className="surface-footer-receipt-line" data-tone="ok" data-wrap role="status" data-testid="room-merge-receipt">
      {/* PHILO-15 B51/B52: the PR by its own title and number (the item's
          title only when the hub has not read the PR's yet). */}
      {`DONE · ${merged.pr?.title || merged.title} · PR #${merged.pr?.number ?? ""} MERGED · ${formatTimeShort(merged.mergedAt ?? "")}`}
    </span>
  ) : ctrl.view === "history" ? (
    <span className="surface-footer-receipt-line" role="status" data-testid="room-footer-receipt">
      {historyReceipt}
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
        <div className="room-body" data-testid="room-body" ref={roomBodyRef}>
          {sendFailure}
          {ctrl.view === "room" ? (
            <>
              <div className="room-section-rise" style={{ animationDelay: "0ms" }}>
                <RoomHead room={ctrl.room} ctrl={ctrl} updateCtrl={updateCtrl} />
              </div>
              {/* Memory on the Desk (canvas section 2, option B): the
                  project's standing pages sit under the head, as ratified. */}
              {standingPages.length ? (
                <div className="room-section-rise" style={{ animationDelay: "10ms" }}>
                  <StandingPagesSection pages={standingPages} />
                </div>
              ) : null}
              <div className="room-section-rise" style={{ animationDelay: "20ms" }}>
                <HealthSection room={ctrl.room} onRetry={handleRefresh} />
              </div>
              <div className="room-section-rise" style={{ animationDelay: "40ms" }}>
                <NeedsYouSection
                  room={ctrl.room}
                  ctrl={ctrl}
                  reviewCtrl={reviewCtrl}
                  selectedProposalId={selectedProposalId}
                  pendingCount={pendingCount}
                />
              </div>
              {/* PHILO-9-03 (the Q3 ruling, the ratified items canvas): ITEMS sits
                  right after NEEDS YOU -- the plan he reads after what needs him. */}
              <div className="room-section-rise" style={{ animationDelay: "50ms" }} data-section="items">
                <ItemsSection projectId={ctrl.projectId} revision={ctrl.room.revision} />
              </div>
              {/* HS-200-41 F5: the saved work is a SECTION in the body, and it
                  sits HERE — directly after NEEDS YOU. Unfinished work IS
                  attention, so it belongs in the reading path next to the
                  Room's first question; the design's posture-6 grammar makes
                  resuming work a peer of repair, not a footnote under SINCE
                  CREATED. Filed last it was also the section the sticky foot
                  reached, so the one row he came back for opened underneath
                  the composer with its verb hidden. */}
              <div className="room-section-rise" style={{ animationDelay: "60ms" }}>
                <RoomUnfinishedSection ask={askCtrl} />
              </div>
              <div className="room-section-rise" style={{ animationDelay: "80ms" }}>
                <SourcesSection room={ctrl.room} onReload={() => void ctrl.load()} stewardCtrl={stewardCtrl} ctrl={ctrl} />
              </div>
              <div className="room-section-rise" style={{ animationDelay: "100ms" }}>
                <RoomPeopleSection projectId={ctrl.projectId} />
              </div>
              <div className="room-section-rise" style={{ animationDelay: "110ms" }}>
                <ReceiptsSection room={ctrl.room} />
              </div>
              <div className="room-section-rise" style={{ animationDelay: "120ms" }}>
                <SinceYouLookedSection room={ctrl.room} />
              </div>
              <div className="room-section-rise" style={{ animationDelay: "160ms" }}>
                <DecisionsCommitmentsSection room={ctrl.room} />
              </div>
              <div className="room-section-rise" style={{ animationDelay: "180ms" }}>
                <RoomBriefsSection prepare={prepareCtrl} />
              </div>
              {/* Condition 7: ask well sticky at the foot of a wide window; in the
                  flow at a narrow one (PHILO-9-03 F10, project-room.css). */}
              <div className="room-section-rise room-ask-container" style={{ animationDelay: "200ms" }}>
                <RoomAskWell
                  ask={askCtrl}
                  projectId={ctrl.projectId}
                  onOpenRef={ctrl.openProjectRef}
                  onPrepare={(purpose) => prepareCtrl.enterPrepare(purpose)}
                />
              </div>
            </>
          ) : (
            <HistoryWing room={ctrl.room} todayCount={historyCounts.todayCount} weekCount={historyCounts.weekCount} />
          )}
        </div>
      ) : loading ? (
        <div className="room-loading"><p className="room-empty-line">Loading…</p></div>
      ) : ctrl.error ? (
        // PHILO-13-04 ledger, paid in B1: a plain failure name and Try again,
        // never the hub's own text (plainFailure in the controller).
        <div className="room-error" role="alert" data-testid="room-load-failed">
          <span className="surface-token" data-chip>{ctrl.error}</span>
          <Button dense variant="primary" onClick={handleRefresh} data-testid="room-load-retry">Try again</Button>
        </div>
      ) : null}
      <SurfaceFooter
        receipt={footerReceipt}
        verbs={
          <>
            {ctrl.view !== "history" && merged ? (
              <FlightVerbs flight={merged} title={merged.pr?.title || merged.title} />
            ) : null}
            <Button dense variant="ghost" onClick={handleRefresh} data-testid="room-refresh">Refresh</Button>
          </>
        }
      />
    </>
  );
}
