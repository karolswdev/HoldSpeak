import { useEffect, useReducer } from "react";
import { wireDate } from "../../desk/surface/format";
import {
  SurfaceLedgerRow,
  SurfaceWell,
  EgressChip,
  StateChip,
} from "../../desk/surface";
import { Button } from "../../components/signal/Signal";
import { StringGadget } from "../../desk/surface/gadgets";
import { SendWells, pickDestination, type DocRef } from "../../desk/surface/send";
import type { RoomHealthPerson, RoomNeedsYouItem, RoomNudgeDestination, NudgeLocal } from "./model";
import { nudgeCardReducer, initialNudgeCard } from "./model";
import * as api from "./api";
import { Token } from "../../desk/surface/Token";

function formatTimeShort(iso: string | null): string {
  if (!iso) return "";
  const date = wireDate(iso);
  if (!date) return "";
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

/* ── HS-173-04: Nudge card (inline under a bottleneck row) ── */

export function NudgeCard({
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
              <Token className="surface-token">
                {prUrl ? (
                  <a href={prUrl} target="_blank" rel="noopener noreferrer" className="room-nudge-pr-link">#{prNumber}</a>
                ) : `#${prNumber}`}
              </Token>
            ) : null}
            <Token className="surface-token">{formatTimeShort(card.sentAt)}</Token>
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
            <Token className="surface-token">
              {prUrl ? (
                <a href={prUrl} target="_blank" rel="noopener noreferrer" className="room-nudge-pr-link">CHECK #{card.prNumber}</a>
              ) : `CHECK #${card.prNumber}`}
            </Token>
          </>
        }
      />
    );
  }

  // Nudge card (open / failed state)
  if (card.phase === "open" || card.phase === "failed") {
    return (
      <li className="surface-ledger-row room-nudge-card-row" data-testid="nudge-card" data-send="well" data-open>
        <SurfaceWell>
          <StateChip state="active" label="NUDGE READY" />
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
              <Token className="surface-token">{card.reason}</Token>
            </div>
          ) : null}
          <div className="room-nudge-card-footer">
            {/* The preview before Send: it names where the comment goes. */}
            <EgressChip label="github.com" scope="cloud" data-testid="nudge-card-egress" />
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

/** P6 generic Nudge: the document and exact destination come from the Room
 * producer.  SendWells owns preview, prepare, and the owner-only Send press. */
export function GenericNudgeCard({ nudge }: { nudge: RoomNudgeDestination }) {
  const doc: DocRef = {
    ref: nudge.documentRef,
    title: nudge.title,
    label: "NUDGE",
  };
  useEffect(() => {
    pickDestination(nudge.documentRef, nudge.destinationId);
  }, [nudge.documentRef, nudge.destinationId]);
  return (
    <li className="surface-ledger-row room-nudge-card-row" data-testid="generic-nudge-card" data-open>
      <SendWells
        doc={doc}
        destinationIds={[nudge.destinationId]}
        head={<StateChip state="active" label="NUDGE READY" />}
      />
    </li>
  );
}
