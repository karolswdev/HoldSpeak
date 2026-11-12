// Parked 2026-11-11: Open owns the Needs you selection and its inspector verbs.
// @ts-nocheck
// Needs you: his own rows (proposals to Confirm, what he owes, what waits on
// his review, a review bottleneck with its Nudge, a matched meeting to file).
import React, { useMemo, useState } from "react";
import { StateChip, SurfaceLedger, SurfaceLedgerRow, SurfaceSection, SurfaceState } from "../../../desk/surface";
import { StringGadget } from "../../../desk/surface/gadgets";
import { Token } from "../../../desk/surface/Token";
import { wireDate } from "../../../desk/surface/format";
import { openSurfaceOr } from "../../../desk/shell";
import { refOpener } from "../../../desk/openObject";
import { flightForItem, isInFlight, useAgentFlights } from "../../../desk/agentFlights";
import { FlightChip, FlightVerbs } from "../../../desk/components/AgentFlight";
import { HandRowVerb } from "../../../desk/components/HandRowVerb";
import { RunAsProgramVerb } from "../../../desk/programs/RunAsProgram";
import { Button } from "../../../components/signal/Signal";
import type {
  NudgeLocal, RoomHealthData, RoomHealthPerson, RoomNeedsYouItem, RoomProposalItem, RoomSnapshot,
} from "../model";
import { formatDays, needsYouWhyWords, whyFaceWords } from "../model";
import { isMine } from "../now/model";
import * as api from "../api";
import { monogram } from "../RoomPeopleSection";
import { NudgeCard } from "../NudgeCard";
import type { useProjectRoomController } from "../useProjectRoomController";
import type { useReviewController } from "../review/useReviewController";
import { RowSprite } from "./rows";
import { formatDueShort, formatMMDD, severityColor, severityTone } from "./format";

/** A Needs you row's why, in quiet words; a late milestone's lateness is
 *  the one red word. */
function WhyWords({ words, alert }: { words: string; alert: boolean }) {
  const split = alert ? words.lastIndexOf(" · ") : -1;
  if (split < 0) return <>{words}</>;
  return <>{words.slice(0, split + 3)}<span className="room-why-alert">{words.slice(split + 3)}</span></>;
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
  const [failure, setFailure] = useState("");
  const [accepted, setAccepted] = useState<{ text: string; owner: string; due: string } | null>(null);

  const proposalId = item.proposalId || "";
  const kind = item.proposalKind || "action";
  const prefix = kind === "decision" ? "Decide:" : "Confirm:";
  // Caption: BY FRI · from Standup 09-05 · MAREK (no host chip: owner
  // ruling 2026-10-25)
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

  const confirm = async (edits?: { text?: string; owner?: string; due?: string }) => {
    setFailure("");
    const result = await ctrl.handleConfirmProposal(proposalId, edits);
    if (!result.ok) setFailure(result.error);
    else setAccepted({ text: edits?.text ?? proposal?.text ?? item.title, owner: edits?.owner ?? ownerHint, due: edits?.due ?? dueHint ?? "" });
    return result.ok;
  };

  const handleSaveConfirm = async () => {
    const edits: { text?: string; owner?: string; due?: string } = {};
    const origText = proposal?.originalText || proposal?.text || item.title;
    if (editText && editText !== origText) edits.text = editText;
    if (editOwner) edits.owner = editOwner;
    if (editDue) edits.due = editDue;
    if (await confirm(edits)) setEditing(false);
  };

  const cancelEdit = () => setEditing(false);

  // A successful write remains successful while its follow-up read recovers.
  if (accepted) return <SurfaceLedgerRow data-testid="proposal-accepted" lead="MTG" wrap primary={accepted.text} cells={<>{accepted.owner ? <Token className="surface-token">{accepted.owner}</Token> : null}{accepted.due ? <Token className="surface-token">BY {formatDueShort(accepted.due)}</Token> : null}<StateChip state="success" label="Confirmed" /></>} />;

  if (editing) {
    // Board: RoomProposalEdit — text StringGadget + Owner + Due + Was: caption + Save & confirm + Cancel
    const origText = proposal?.originalText || proposal?.text || item.title;
    const origDue = proposal?.dueHint || item.dueHint || "";
    const wasCaption = `Was: ${origText}${origDue ? ` · by ${origDue}` : ""}`;

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
            <StringGadget label="Text" value={editText} onChange={setEditText} disabled={ctrl.proposalBusy === proposalId} autoFocus />
            <label className="room-proposal-edit-label">
              <span className="room-proposal-edit-label-text">Owner</span>
              <StringGadget label="Owner" value={editOwner} onChange={setEditOwner} placeholder="Owner" disabled={ctrl.proposalBusy === proposalId} />
            </label>
            <label className="room-proposal-edit-label">
              <span className="room-proposal-edit-label-text">Due</span>
              <StringGadget label="Due" value={editDue} onChange={setEditDue} placeholder="Due" disabled={ctrl.proposalBusy === proposalId} />
            </label>
          </div>
          <p className="room-proposal-was-caption" data-testid="proposal-was-caption">{wasCaption}</p>
          {failure ? <SurfaceState error={failure} /> : null}
          <div className="room-proposal-edit-verbs">
            <Button dense variant="primary" loading={ctrl.proposalBusy === proposalId} disabled={ctrl.proposalBusy === proposalId} onClick={() => void handleSaveConfirm()} data-testid="proposal-save-confirm">
              {failure ? "Try again" : "Save & confirm"}
            </Button>
            <Button dense variant="ghost" disabled={ctrl.proposalBusy === proposalId} onClick={cancelEdit} data-testid="proposal-cancel-edit">
              Cancel
            </Button>
          </div>
        </div>
      </li>
    );
  }

  // Caption parts
  const captionParts: string[] = [];
  if (dueHint) captionParts.push(`By ${dueHint}`);
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
        /* PHILO-17 refit: the title press edits the proposal (one row,
           Confirm and a quiet Dismiss). */
        <Button variant="chrome" className="room-proposal-title" onClick={openEdit}
          aria-label={`Edit: ${item.title}`} data-testid="proposal-edit">
          <span className="surface-primary room-proposal-text" data-testid="proposal-primary">
            <span className="room-proposal-prefix" data-proposal-kind={kind}>{prefix}</span>
            {" "}{item.title}
          </span>
        </Button>
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
            <span className="room-proposal-caption room-proposal-speaker">{speaker}</span>
          ) : null}
          {failure ? <Token className="surface-token" role="alert">{failure}</Token> : null}
        </>
      }
      trailing={
        <span className="room-proposal-verbs" data-testid="proposal-verbs">
          <Button dense variant="secondary" loading={ctrl.proposalBusy === proposalId} disabled={ctrl.proposalBusy === proposalId} onClick={() => void confirm()} data-testid="proposal-confirm">
            {failure ? "Try again" : "Confirm"}
          </Button>
          <Button dense variant="ghost" onClick={() => void ctrl.handleDismissProposal(proposalId)} data-testid="proposal-dismiss">
            Dismiss
          </Button>
        </span>
      }
    />
  );
}

/* ── NEEDS YOU (Betterment P3: his own rows; was OPEN HERE) ── */

export function NeedsYouSection({
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
  // Betterment P3: Needs you holds his own rows only (proposals to Confirm,
  // what he owes, what waits on his review); what others owe is Waiting on.
  const items = room.needsYou.items.filter(isMine);

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
  // Betterment P5: one producer-matched meeting can be filed from its row.
  const [meetingBusy, setMeetingBusy] = useState<string | null>(null);
  // Conductor F2 (K4b): each row wears its agent where it lives.
  const flights = useAgentFlights((s) => s.flights);

  const reviewAction = pendingCount > 0 ? (
    <Button dense variant="ghost" loading={reviewCtrl.loading} onClick={() => void reviewCtrl.enterReview()} data-testid="review-verb" data-verb="review">
      Review {pendingCount}
    </Button>
  ) : undefined;

  // Absent when empty (no counters of zero); a Review still has its verb.
  if (items.length === 0) {
    return reviewAction ? <SurfaceSection label="Needs you" actions={reviewAction} /> : null;
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
    // No count: "needs you" with a number is the desk's one number
    // (PHILO-13-03); the project's filter says the rows themselves.
    <SurfaceSection label="Needs you" actions={reviewAction} data-testid="room-needs-you">
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
            if (item.kind === "meeting_match" && item.meetingId) {
              const meetingId = item.meetingId;
              return (
                <SurfaceLedgerRow
                  key={`meeting-match-${meetingId}`}
                  data-testid="meeting-match-row"
                  lead={<RowSprite source="meeting" kind="meeting_match" />}
                  primary={<span className="surface-primary">{item.title}</span>}
                  wrap
                  cells={item.meetingTitle ? (
                    <Token className="surface-token" data-testid="meeting-match-title">{item.meetingTitle}</Token>
                  ) : undefined}
                  trailing={
                    <Button
                      dense
                      variant="ghost"
                      loading={meetingBusy === meetingId}
                      disabled={meetingBusy === meetingId}
                      data-testid="meeting-match-add"
                      onClick={() => {
                        setMeetingBusy(meetingId);
                        void api.associateMeeting(ctrl.projectId, meetingId)
                          .then(() => ctrl.load())
                          .finally(() => setMeetingBusy(null));
                      }}
                    >
                      Add
                    </Button>
                  }
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
              // A nudge has a real place only when the producer named the PR.
              // Keep the verb out of rows whose destination is unreadable or absent.
              const hasDestination = Boolean(
                matchedNudge?.pr_url
                || person?.prs?.some((pr) => pr.url)
                // A persisted result can retain only the PR number; it is
                // still the place to inspect an indeterminate send.
                || person?.nudge?.prNumber,
              );
              const hasNudgeStep = Boolean((matchedNudge?.step_id || person?.nudge?.stepId) && hasDestination);
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
                      <Token
                        className="surface-token room-why-token"
                        data-testid="bottleneck-why"
                      >
                        {whyFaceWords(whyText)}
                      </Token>
                    }
                    trailing={
                      <span className="room-bottleneck-verbs">
                        {cooldown ? (
                          <Token className="surface-token room-nudge-cooldown" data-testid="nudge-cooldown">{whyFaceWords(cooldown)}</Token>
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
                lead={<RowSprite source={item.source} kind={item.kind} />}
                primary={<span className="surface-primary" title={item.title}>{item.title}</span>}
                wrap
                cells={
                  <span className="room-why-cells">
                    <Token
                      className="surface-token room-why-token"
                      style={{ color: severityColor(item.severity) }}
                      data-tone={severityTone(item.severity)}
                      data-testid="needs-you-why"
                    >
                      <WhyWords words={whyFaceWords(needsYouWhyWords(item))} alert={(item.source === "item" && item.kind === "milestone") || severityTone(item.severity) === "danger"} />
                    </Token>
                    <FlightChip flight={flight} />
                  </span>
                }
                trailing={<>
                  {/* Conductor F2: an item in flight shows its flight and its
                      verb; Hand to coder (Conductor K2e) only on an item no
                      agent holds, before the row's Open, as drawn. */}
                  {isInFlight(flight)
                    ? <FlightVerbs flight={flight} title={item.title} />
                    : <HandRowVerb item={{ title: item.title, source: item.source, actionItemId: item.actionItemId, projectId: ctrl.projectId, kind: item.kind, watchId: item.watchId, entityId: item.entityId, url: item.url }} />}
                  {/* JRN13: an action of the Project can become a Program. */}
                  {item.actionItemId && !isInFlight(flight)
                    ? <RunAsProgramVerb actionId={item.actionItemId} projectId={ctrl.projectId} title={item.title} /> : null}
                  {item.verb === "decide" ? (
                    <Button dense variant="ghost" onClick={() => {
                      if (item.url) window.open(item.url, "_blank", "noopener");
                    }}>Decide</Button>
                  ) : item.url ? (
                    <Button dense variant="ghost" onClick={() => window.open(item.url!, "_blank", "noopener")}>Open source</Button>
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
