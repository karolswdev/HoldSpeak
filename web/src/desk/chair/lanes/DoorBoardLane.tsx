import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch, newDeliveryId, readableError } from "../../../lib/api";
import { openIntelligence } from "../../intelligenceNavigation";
import { useWriteReceipt } from "../../hooks/useWriteReceipt";
import { StringGadget } from "../../surface/gadgets";
import { SurfaceSection, SurfaceState } from "../../surface/Surface";
import { useDesk } from "../../store";
import type { LaneProps } from "../laneContract";
import { upcomingTimeLabel } from "./upcomingTime";

type DoorColumnId = "overdue" | "now" | "waiting" | "unassigned" | "active";
type DoorVerbArguments = Record<string, string | number | null | undefined>;

export type DoorVerb = {
  name: string;
  arguments: DoorVerbArguments;
  required_arguments?: string[];
};

export type DoorCard = {
  id: string;
  source: string;
  target_ref: string;
  open_ref?: string;
  title?: string;
  text?: string;
  body_preview?: string;
  owner?: string | null;
  due?: string | null;
  stale_score?: number | null;
  continuity_state?: string;
  updated_at?: string;
  filing_status?: string;
  lawful_verbs?: DoorVerb[];
};

export type DoorUpcomingItem = {
  id: string;
  source: "calendar_event" | "scheduled_recording";
  target_ref: string;
  title: string;
  starts_at: string;
  ends_at: string;
  location: string | null;
  meeting_url: string | null;
  state: string;
};

export type DoorProjection = {
  board: Record<DoorColumnId, DoorCard[]>;
  counts: {
    overdue: number;
    now: number;
    waiting: number;
    active: number;
    upcoming_today: number;
  };
  upcoming: DoorUpcomingItem[];
};

type Command = { endpoint: string; body?: Record<string, unknown> };
type ActionPayload = { until?: string; to?: string };

const COLUMNS: Array<{ id: DoorColumnId; label: string; count?: keyof DoorProjection["counts"] }> = [
  { id: "overdue", label: "Overdue", count: "overdue" },
  { id: "now", label: "Now", count: "now" },
  { id: "waiting", label: "Waiting", count: "waiting" },
  // The aggregate does not project an unassigned count; inventing one would be false.
  { id: "unassigned", label: "Unassigned" },
  { id: "active", label: "Active", count: "active" },
];

function text(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function labelFor(verb: DoorVerb): string {
  if (verb.name === "follow_through.complete") {
    return text(verb.arguments.verb).replace(/^./, (letter) => letter.toUpperCase());
  }
  if (verb.name === "cadence.set_status") {
    return text(verb.arguments.status) === "killed" ? "Kill" : "Close";
  }
  if (verb.name === "thought.complete") return "Complete";
  if (verb.name === "people.commitment.transition") {
    return text(verb.arguments.verb).replace(/^./, (letter) => letter.toUpperCase());
  }
  return "";
}

function supportsDoorVerb(verb: DoorVerb): boolean {
  return [
    "follow_through.complete",
    "cadence.set_status",
    "thought.complete",
    "people.commitment.transition",
  ].includes(verb.name);
}

function requiredPayload(verb: DoorVerb): "until" | "to" | null {
  const needs = verb.required_arguments ?? [];
  if (needs.includes("payload.until")) return "until";
  if (needs.includes("payload.to")) return "to";
  return null;
}

/** Fixed HTTP adapter table. Door descriptors name capabilities, never URLs. */
export function commandForDoorVerb(verb: DoorVerb, payload: ActionPayload = {}): Command | null {
  const args = verb.arguments;
  if (verb.name === "follow_through.complete") {
    const cardId = text(args.card_id);
    const action = text(args.verb);
    if (!cardId || !action) return null;
    if (action === "snooze" && !payload.until?.trim()) return null;
    if (action === "delegate" && !payload.to?.trim()) return null;
    const writePayload = action === "snooze"
      ? { until: payload.until?.trim() }
      : action === "delegate"
        ? { to: payload.to?.trim() }
        : {};
    return {
      endpoint: "/api/follow-through/complete",
      body: { card_id: cardId, verb: action, payload: writePayload },
    };
  }
  if (verb.name === "cadence.set_status") {
    const loopId = text(args.loop_id);
    const status = text(args.status);
    if (!loopId || !["closed", "killed"].includes(status)) return null;
    return { endpoint: `/api/cadence/loops/${encodeURIComponent(loopId)}/${status === "closed" ? "close" : "kill"}` };
  }
  if (verb.name === "thought.complete") {
    const thoughtId = text(args.thought_id);
    const aggregateRevision = args.expected_aggregate_revision;
    const lifecycleRevision = args.expected_lifecycle_revision;
    if (!thoughtId || typeof aggregateRevision !== "number" || typeof lifecycleRevision !== "number") return null;
    return {
      endpoint: `/api/thoughts/${encodeURIComponent(thoughtId)}/complete`,
      body: {
        request_id: newDeliveryId(),
        expected_aggregate_revision: aggregateRevision,
        expected_lifecycle_revision: lifecycleRevision,
      },
    };
  }
  if (verb.name === "people.commitment.transition") {
    const commitmentId = text(args.commitment_id);
    const action = text(args.verb);
    if (!commitmentId || !["done", "dismiss"].includes(action)) return null;
    return {
      endpoint: `/api/people/commitments/${encodeURIComponent(commitmentId)}/transition`,
      body: { verb: action },
    };
  }
  return null;
}

function titleFor(card: DoorCard): string {
  return card.title?.trim() || card.text?.trim() || "Untitled";
}

function sourceLabel(source: string): string {
  return source.replace(/[_-]+/g, " ");
}

function dueLabel(due: string | null | undefined): string | null {
  if (!due) return null;
  const date = new Date(`${due.slice(0, 10)}T00:00:00`);
  if (Number.isNaN(date.getTime())) return due;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const days = Math.round((date.getTime() - today.getTime()) / 86_400_000);
  if (days === 0) return "due today";
  if (days < 0) return `overdue ${Math.abs(days)}d`;
  return `due ${days}d`;
}

function updatedLabel(value: string | undefined): string | null {
  if (!value) return null;
  const then = new Date(value).getTime();
  if (!Number.isFinite(then)) return "updated recently";
  const minutes = Math.max(0, Math.floor((Date.now() - then) / 60_000));
  if (minutes < 1) return "updated now";
  if (minutes < 60) return `updated ${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `updated ${hours}h`;
  return `updated ${Math.floor(hours / 24)}d`;
}

function cardFacts(card: DoorCard): string[] {
  if (card.source === "thought") {
    return [
      sourceLabel(card.source),
      card.continuity_state?.replace(/_/g, " ") ?? "",
      updatedLabel(card.updated_at) ?? "",
    ].filter(Boolean);
  }
  return [
    sourceLabel(card.source),
    card.owner ? `owner ${card.owner}` : "",
    dueLabel(card.due) ?? "",
    typeof card.stale_score === "number" ? `age ${card.stale_score}` : "",
  ].filter(Boolean);
}

function headline(counts: DoorProjection["counts"]): string {
  return [
    counts.overdue ? `${counts.overdue} overdue` : "",
    counts.now ? `${counts.now} now` : "",
    counts.waiting ? `${counts.waiting} waiting` : "",
    counts.active ? `${counts.active} active` : "",
  ].filter(Boolean).join(" · ");
}

function upcomingKind(item: DoorUpcomingItem): string {
  return item.source === "calendar_event" ? "EVENT" : "SCHEDULED RECORDING";
}

function upcomingTitle(item: DoorUpcomingItem): string {
  return item.title.trim() || (item.source === "calendar_event" ? "Untitled event" : "Untitled scheduled recording");
}

function UpcomingRail({ upcoming }: { upcoming: DoorUpcomingItem[] }) {
  return (
    <section className="door-upcoming-rail" aria-labelledby="door-upcoming-title">
      <header className="door-upcoming-head">
        <h3 id="door-upcoming-title">UPCOMING</h3>
        <Button dense variant="ghost" onClick={() => useDesk.getState().openScheduleCreate()}>
          Schedule recording
        </Button>
      </header>
      {upcoming.length ? (
        <ol className="door-upcoming-list">
          {upcoming.map((item) => {
            const time = upcomingTimeLabel(item.starts_at);
            return (
              <li className="door-upcoming-row" key={`${item.source}:${item.id}`} data-upcoming-source={item.source}>
                <span className="door-upcoming-kind">{upcomingKind(item)}</span>
                <strong>{upcomingTitle(item)}</strong>
                {time ? <span className="door-upcoming-time">STARTS {time}</span> : null}
                {item.location ? <span className="door-upcoming-detail">{item.location}</span> : null}
                {item.meeting_url ? (
                  <a className="door-upcoming-link" href={item.meeting_url} target="_blank" rel="noreferrer">
                    Meeting link
                  </a>
                ) : null}
              </li>
            );
          })}
        </ol>
      ) : (
        <div className="door-upcoming-empty">No future time scheduled.</div>
      )}
    </section>
  );
}

export function DoorBoardLane({ onOpenInWindow }: LaneProps) {
  const deskUpdatedAt = useDesk((state) => state.updatedAt);
  // The schedule slice remains its own writer. This is only a post-save
  // invalidation signal for the aggregate that owns the visible rail.
  const scheduledRecordings = useDesk((state) => state.scheduledRecordings);
  const sawScheduleList = useRef(false);
  const [projection, setProjection] = useState<DoorProjection | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [busyCardId, setBusyCardId] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<{ cardId: string; verbIndex: number } | null>(null);
  const [payloadValue, setPayloadValue] = useState("");
  const { attempt, receipt } = useWriteReceipt();

  const reload = useCallback(async () => {
    setLoading(true);
    setLoadError("");
    try {
      setProjection(await apiFetch<DoorProjection>("/api/door"));
    } catch (cause) {
      setLoadError(readableError(cause));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload, deskUpdatedAt]);

  useEffect(() => {
    if (!sawScheduleList.current) {
      sawScheduleList.current = true;
      return;
    }
    void reload();
  }, [reload, scheduledRecordings]);

  const dispatch = async (card: DoorCard, verb: DoorVerb, payload: ActionPayload = {}) => {
    const command = commandForDoorVerb(verb, payload);
    if (!command || busyCardId) return;
    setBusyCardId(card.id);
    const result = await attempt(labelFor(verb), () => apiFetch(command.endpoint, {
      method: "POST",
      ...(command.body ? { json: command.body } : {}),
    }));
    if (result.ok) {
      setExpanded(null);
      setPayloadValue("");
      await reload();
    }
    setBusyCardId(null);
  };

  // Door owns its loading/refusal seat too: leaving a bare SurfaceState outside
  // the named lane hid both the source of a failed read and the re-homed Brief
  // capability. Keep every initial state in the same Chair material.
  if (loading && !projection) {
    return (
      <SurfaceSection
        label="DOOR"
        actions={<Button dense variant="ghost" onClick={() => openIntelligence({ view: "brief" })}>Brief</Button>}
        className="door-board-section"
      >
        <SurfaceState loading />
      </SurfaceSection>
    );
  }
  if (loadError && !projection) {
    return (
      <SurfaceSection
        label="DOOR"
        actions={<Button dense variant="ghost" onClick={() => openIntelligence({ view: "brief" })}>Brief</Button>}
        className="door-board-section"
      >
        <SurfaceState error={loadError} onRetry={() => void reload()} />
      </SurfaceSection>
    );
  }
  if (!projection) return null;

  const cards = COLUMNS.flatMap(({ id }) => projection.board[id] ?? []);

  return (
    <SurfaceSection
      label="DOOR"
      className="door-board-section"
      actions={<Button dense variant="ghost" onClick={() => openIntelligence({ view: "brief" })}>Brief</Button>}
    >
      <div className="door-board-summary" aria-live="polite">
        {headline(projection.counts)}
      </div>
      {receipt ? <div className="door-board-receipt">{receipt}</div> : null}
      {loadError ? <SurfaceState error={loadError} onRetry={() => void reload()} /> : null}
      {cards.length ? (
        <div className="door-board-viewport" tabIndex={0} aria-label="Door board, scroll horizontally for all columns">
          <div className="door-board-grid">
          {COLUMNS.map(({ id, label, count }) => {
            const columnCards = projection.board[id] ?? [];
            const displayedCount = count ? projection.counts[count] : null;
            return (
              <section key={id} className="door-board-column" aria-labelledby={`door-column-${id}`}>
                <header className="door-board-column-head">
                  <h4 id={`door-column-${id}`}>{label}</h4>
                  {displayedCount !== null ? (
                    <span aria-label={`${displayedCount} ${label.toLowerCase()} items`}>{displayedCount}</span>
                  ) : null}
                </header>
                <div className="door-board-cards">
                  {columnCards.length ? columnCards.map((card) => {
                    const verbs = (card.lawful_verbs ?? []).filter(supportsDoorVerb);
                    return (
                      <article className="door-card" key={card.id}>
                        <button
                          type="button"
                          className="door-card-open"
                          onClick={() => onOpenInWindow(card.open_ref ?? card.target_ref)}
                        >
                          <strong>{titleFor(card)}</strong>
                          {card.body_preview ? <span>{card.body_preview}</span> : null}
                          <small>{cardFacts(card).join(" · ")}</small>
                        </button>
                        {verbs.length ? (
                          <div className="door-card-actions" aria-label={`Actions for ${titleFor(card)}`}>
                            {verbs.map((verb, index) => {
                              const required = requiredPayload(verb);
                              const isExpanded = expanded?.cardId === card.id && expanded.verbIndex === index;
                              const disabled = busyCardId !== null;
                              return (
                                <div className="door-card-action" key={`${verb.name}-${index}`}>
                                  <Button
                                    dense
                                    variant="ghost"
                                    disabled={disabled}
                                    loading={busyCardId === card.id && !required}
                                    onClick={() => {
                                      if (required) {
                                        setExpanded(isExpanded ? null : { cardId: card.id, verbIndex: index });
                                        setPayloadValue("");
                                      } else {
                                        void dispatch(card, verb);
                                      }
                                    }}
                                  >
                                    {labelFor(verb)}
                                  </Button>
                                  {required && isExpanded ? (
                                    <div className="door-card-action-seat">
                                      <StringGadget
                                        label={required === "until" ? "Until" : "Delegate to"}
                                        value={payloadValue}
                                        onChange={setPayloadValue}
                                        placeholder={required === "until" ? "2026-08-28" : "Name"}
                                      />
                                      <Button
                                        dense
                                        variant="primary"
                                        disabled={!payloadValue.trim() || busyCardId !== null}
                                        loading={busyCardId === card.id}
                                        onClick={() => void dispatch(card, verb, required === "until" ? { until: payloadValue } : { to: payloadValue })}
                                      >
                                        Apply
                                      </Button>
                                    </div>
                                  ) : null}
                                </div>
                              );
                            })}
                          </div>
                        ) : null}
                      </article>
                    );
                  }) : <div className="door-board-column-empty">Clear</div>}
                </div>
              </section>
            );
          })}
          </div>
        </div>
      ) : <SurfaceState empty emptyLabel="Door clear" />}
      <UpcomingRail upcoming={projection.upcoming} />
    </SurfaceSection>
  );
}
