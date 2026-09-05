// HS-169-03 — the Room rebuilt to the ratified canvas.
// Four questions: What needs me now? What am I watching? What changed
// since I last looked? What did we decide and what do I owe people?
// Two wings: ROOM · HISTORY. Ask well at the foot. No counters of zero,
// no REV, no raw field names, the name said once.
import React, { useEffect, useRef, useState, useMemo, useCallback, useReducer } from "react";
import {
  countLabel,
  SurfaceFooter,
  SurfaceSection,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceStream,
  SurfaceStreamDay,
  SurfaceStreamEntry,
  SurfaceWell,
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
  NudgeCardAction,
} from "./model";
import { lifecycleLabel, resolveHealthRows, nudgeCardReducer, formatDays } from "./model";
import { StringGadget } from "../../desk/surface/gadgets";
import { egressFor, egressForEvent, receiptLabel } from "../../desk/surface/egress";
import { useProjectRoomController } from "./useProjectRoomController";
import { useReviewController } from "./review/useReviewController";
import { ReviewPosture } from "./review/ReviewPosture";
import { useUpdateController } from "./update/useUpdateController";
import { UpdatePosture } from "./update/UpdatePosture";
import { useStewardController } from "./steward/useStewardController";
import { StewardPosture } from "./steward/StewardPosture";
import * as api from "./api";
import { RoomPeopleSection, monogram } from "./RoomPeopleSection";
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
  confluence: "C",
  meeting: "MTG",
  proposal: "MTG",
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

/** Format a due date as a short day name (FRI) when within ~7 days, else MMM DD. */
function formatDueShort(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
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
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
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
              ? (target.daysLeft ? `OVERDUE BY ${Math.abs(target.daysLeft)} DAYS` : "OVERDUE TODAY")
              : `TARGET ${formatTargetDate(target.targetAt)}${target.daysLeft ? ` · ${target.daysLeft} DAYS` : " · TODAY"}`
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

/* ── HS-173: HEALTH section ── */

function healthToneToState(tone: "green" | "amber" | "red"): "success" | "warning" | "failure" {
  if (tone === "red") return "failure";
  if (tone === "amber") return "warning";
  return "success";
}

function HealthSection({ room }: { room: RoomSnapshot }) {
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
}: {
  person: RoomHealthPerson | undefined;
  needsYouItem: RoomNeedsYouItem;
  nudgeItem: api.NudgeItem | undefined;
  onReload: () => void;
  onSent?: () => void;
}) {
  const displayName = person?.displayName || needsYouItem.title;
  // Bind PR from the nudge step (the wire's authoritative source)
  const prNumber = nudgeItem?.pr_number ?? person?.prs?.[0]?.number ?? 0;
  const prTitle = nudgeItem?.pr_title ?? person?.prs?.[0]?.title ?? "";
  const prUrl = nudgeItem?.pr_url ?? person?.prs?.[0]?.url ?? "";
  const stepId = nudgeItem?.step_id ?? person?.nudge?.stepId ?? "";
  const waitDays = Math.round(person?.medianDays || needsYouItem.medianDays || 1);
  const defaultText = nudgeItem?.comment_text
    || person?.nudge?.text
    || `This PR has been waiting for review for ${waitDays} days. Flagged by HoldSpeak.`;

  // The card starts open (it mounts when the user clicks Nudge)
  const [card, dispatch] = useReducer(nudgeCardReducer, { phase: "open", text: defaultText, busy: false } as NudgeCardState);

  const handleSend = async () => {
    if (card.phase !== "open" && card.phase !== "failed") return;
    if (!stepId) return;
    dispatch({ type: "sending" });
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
      } else {
        dispatch({ type: "failed", reason: String(result.message || "Send failed") });
      }
    } catch (err) {
      dispatch({ type: "failed", reason: String(err) });
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
        lead={<StateChip state="success" label="" icon={"●"} />}
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
  const sentDate = new Date(nudge.sentAt);
  if (Number.isNaN(sentDate.getTime())) return null;
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
}: {
  item: RoomNeedsYouItem;
  proposal: RoomProposalItem | undefined;
  ctrl: ReturnType<typeof useProjectRoomController>;
  isNewest: boolean;
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
    const dateStr = formatMMDD(createdAt);
    captionParts.push(`from ${meetingTitle}${dateStr ? ` ${dateStr}` : ""}`);
  }

  return (
    <SurfaceLedgerRow
      data-testid="proposal-row"
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

  // Build a lookup from proposalId to the full proposal data
  const proposalMap = new Map<string, RoomProposalItem>();
  for (const p of ctrl.proposals) proposalMap.set(p.id, p);

  // Find the newest proposal for the accent frame
  const newestProposalId = items
    .filter((it) => it.proposalId)
    .sort((a, b) => (b.createdAt || b.since || "").localeCompare(a.createdAt || a.since || ""))
    [0]?.proposalId || "";

  return (
    <SurfaceSection label={`NEEDS YOU ${count}`} actions={reviewAction}>
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
                      person={person}
                      needsYouItem={item}
                      nudgeItem={matchedNudge}
                      onReload={() => { setOpenNudge(null); void ctrl.load(); }}
                      onSent={() => setSentNudgeRelIds((prev) => new Set([...prev, relId]))}
                    />
                  ) : null}
                </React.Fragment>
              );
            }
            return (
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
            );
          })}
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
                    loading={busyWatch === src.watchIds[0]}
                    onClick={() => {
                      if (src.state === "paused") void handleResume(src.watchIds);
                      else void handlePause(src.watchIds);
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
                  {src.host ? <EgressChip label={src.host} scope="cloud" title={src.host} /> : null}
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
            return (
              <SurfaceLedgerRow
                key={item.id}
                lead={<StateChip state="success" label="" icon={"●"} />}
                primary={<span className="surface-primary">{label}</span>}
                wrap
                expands={false}
                data-testid="receipt-row"
                cells={
                  <>
                    {item.outcome && item.outcome !== "ok" ? (
                      <span className="surface-token">{item.outcome.toUpperCase()}</span>
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
                <SurfaceLedgerRow
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
                      <span className="surface-token room-confirmed-token" data-testid="confirmed-state">
                        CONFIRMED {confirmedTime}
                      </span>
                      {wasParts.map((w, wi) => (
                        <span key={wi} className="surface-token room-was-token">{w}</span>
                      ))}
                    </>
                  }
                  trailing={
                    <Button dense variant="ghost" onClick={() => openPrimitive(`decision:${dec.id}`)}>Open</Button>
                  }
                />
              );
            }

            return (
              <SurfaceLedgerRow
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
                  ) : (
                    <Button dense variant="ghost" onClick={() => openPrimitive(`decision:${dec.id}`)}>Open</Button>
                  )
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
  const targets = useDesk((s) => s.inferenceTargets);
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
  }, [projectId, targets]);
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
        <input // UX-CANON: needs redesign (HS-170-04)
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

  // S-1: footer receipt omits zero parts — "Nothing today" / "Nothing this week"
  const historyReceipt = (() => {
    const { todayCount: t, weekCount: w } = historyCounts;
    if (t === 0 && w === 0) return "NOTHING THIS WEEK";
    if (t === 0) return `NOTHING TODAY · ${w} THIS WEEK`;
    if (w === 0) return `${t} TODAY · NOTHING THIS WEEK`;
    return `${t} TODAY · ${w} THIS WEEK`;
  })();
  const footerReceipt = ctrl.view === "history" ? (
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
        <div className="room-body" data-testid="room-body">
          {ctrl.view === "room" ? (
            <>
              <div className="room-section-rise" style={{ animationDelay: "0ms" }}>
                <RoomHead room={ctrl.room} ctrl={ctrl} updateCtrl={updateCtrl} />
              </div>
              <div className="room-section-rise" style={{ animationDelay: "20ms" }}>
                <HealthSection room={ctrl.room} />
              </div>
              <div className="room-section-rise" style={{ animationDelay: "40ms" }}>
                <NeedsYouSection room={ctrl.room} ctrl={ctrl} reviewCtrl={reviewCtrl} pendingCount={pendingCount} />
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
