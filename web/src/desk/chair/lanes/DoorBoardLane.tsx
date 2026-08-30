import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch, newDeliveryId, readableError } from "../../../lib/api";
import { openIntelligence } from "../../intelligenceNavigation";
import { useWriteReceipt } from "../../hooks/useWriteReceipt";
import { StringGadget } from "../../surface/gadgets";
import { SurfaceSection, SurfaceState } from "../../surface/Surface";
import { openSurfaceOr } from "../../shell";
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
  /* HS-150-02: person projection for mapped owner strings (only-when-present). */
  person_label?: string;
  person_relationship_id?: string;
  delegated_at?: string | null;
  created_at?: string | null;
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
  /* HS-146-04: rail provenance fields projected by _calendar_event_item. */
  source_id?: string;
  source_label?: string;
  /* HS-147-01: present when an event-linked schedule exists. */
  armed_schedule_id?: string;
  /* HS-149-03: series uid for the picker/link flow. */
  uid?: string;
  /* HS-149-03: person label for linked calendar series (only-when-present). */
  person_label?: string;
  /* HS-149-04: relationship ID for the PREP affordance (only-when-present). */
  person_relationship_id?: string;
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
  calendar_configured: boolean;
  /** HS-149-01 L2: the People store readiness state. Absent when no People projection is wired. */
  people_store_state?: string;
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

/** HS-150-02: staleness from delegated_at ?? created_at. Fewest words, mono. */
function stalenessLabel(card: DoorCard): string | null {
  const ts = card.delegated_at || card.created_at;
  if (!ts) return null;
  const then = new Date(ts).getTime();
  if (!Number.isFinite(then)) return null;
  const days = Math.max(0, Math.floor((Date.now() - then) / 86_400_000));
  return `waiting ${days}d`;
}

/** HS-150-02: reserved owner strings that never show the map affordance. */
const RESERVED_OWNERS = new Set(["me", "remote", "you"]);
function isReservedOwner(owner: string): boolean {
  return RESERVED_OWNERS.has(owner.toLowerCase());
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
    // HS-150-02: mapped cards render a person chip; show raw owner only for unmapped.
    card.person_label ? "" : (card.owner ? `owner ${card.owner}` : ""),
    dueLabel(card.due) ?? "",
    typeof card.stale_score === "number" ? `age ${card.stale_score}` : "",
  ].filter(Boolean);
}

/** HS-145-01: pure scroll-hint state from viewport geometry. */
export type ScrollHint = "none" | "right" | "left" | "both";

export function computeScrollHint(
  scrollLeft: number,
  scrollWidth: number,
  clientWidth: number,
): ScrollHint {
  if (scrollWidth <= clientWidth) return "none";
  const atLeft = scrollLeft <= 0;
  // The 20px tolerance absorbs scrollbar-gutter: stable both-edges
  // which reduces the effective scrollable range by the gutter width.
  const atRight = scrollLeft + clientWidth >= scrollWidth - 20;
  if (atLeft && atRight) return "none";
  if (atLeft) return "right";
  if (atRight) return "left";
  return "both";
}

/** HS-149-01 L2: map the People store state to PeopleCore's gate vocabulary. */
function peopleStateLabel(state: string | undefined): string | null {
  if (!state || state === "ready") return null;
  switch (state) {
    case "locked": return "People store locked";
    case "key_unavailable": return "People key unavailable";
    case "corrupt": return "People store unavailable";
    case "unavailable": return "People store unavailable";
    case "unconfigured": return "People not set up";
    default: return "People store unavailable";
  }
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

/** HS-146-04: true when the upcoming list spans >1 distinct calendar source. */
function hasMultipleSources(upcoming: DoorUpcomingItem[]): boolean {
  const ids = new Set<string>();
  for (const item of upcoming) {
    if (item.source === "calendar_event" && item.source_id) {
      ids.add(item.source_id);
      if (ids.size > 1) return true;
    }
  }
  return false;
}

/** HS-147-02: refusal code to human-readable, fewest words. */
function refusalLabel(code: string): string {
  if (code === "event_already_armed" || code === "conflict") return "ALREADY ARMED";
  if (code === "event_already_ended") return "EVENT ENDED";
  if (code === "not_found") return "EVENT NOT FOUND";
  return code.toUpperCase().replace(/_/g, " ");
}

/** HS-147-02: extract the refusal code from an ApiError payload. */
function refusalCode(error: unknown): string {
  if (error && typeof error === "object" && "payload" in error) {
    const payload = (error as { payload: unknown }).payload;
    if (payload && typeof payload === "object" && "code" in payload) {
      const code = (payload as { code: unknown }).code;
      if (typeof code === "string" && code) return code;
    }
  }
  return "request_failed";
}

/** HS-147-02: per-row arm/cancel state for the upcoming rail. */
function UpcomingRowActions({ item, onReload }: { item: DoorUpcomingItem; onReload: () => void }) {
  const [busy, setBusy] = useState(false);
  const [refusal, setRefusal] = useState<string | null>(null);
  const [confirmCancel, setConfirmCancel] = useState(false);

  const arm = async () => {
    setBusy(true);
    setRefusal(null);
    try {
      await apiFetch("/api/scheduled-recordings", {
        method: "POST",
        json: { calendar_event_id: item.id },
      });
      // Success: the store's scheduledRecordings list change triggers
      // DoorBoardLane.tsx:339-345 re-fetch, which repopulates armed_schedule_id.
      await useDesk.getState().loadSchedules();
      onReload();
    } catch (err) {
      setRefusal(refusalLabel(refusalCode(err)));
    } finally {
      setBusy(false);
    }
  };

  const cancel = async () => {
    if (!item.armed_schedule_id) return;
    setBusy(true);
    setRefusal(null);
    try {
      // DELETE removes the idle event-linked one-shot schedule entirely.
      // POST /{id}/cancel is for actively-arming countdowns; DELETE is the
      // correct authority for disarming an idle linked schedule.
      await apiFetch(`/api/scheduled-recordings/${encodeURIComponent(item.armed_schedule_id)}`, {
        method: "DELETE",
      });
      setConfirmCancel(false);
      await useDesk.getState().loadSchedules();
      onReload();
    } catch (err) {
      setRefusal(refusalLabel(refusalCode(err)));
      setConfirmCancel(false);
    } finally {
      setBusy(false);
    }
  };

  if (item.source !== "calendar_event") return null;

  // Armed state: ARMED chip + CANCEL? two-beat verb.
  if (item.armed_schedule_id) {
    return (
      <span className="door-upcoming-arm-actions" data-testid="door-arm-actions">
        <span className="door-upcoming-armed-chip" data-testid="door-armed-chip">ARMED</span>
        {confirmCancel ? (
          <Button
            dense
            variant="danger"
            loading={busy}
            disabled={busy}
            data-testid="door-cancel-confirm"
            onClick={() => void cancel()}
          >
            Cancel
          </Button>
        ) : (
          <Button
            dense
            variant="ghost"
            disabled={busy}
            data-testid="door-cancel-prompt"
            onClick={() => setConfirmCancel(true)}
          >
            Cancel?
          </Button>
        )}
        {refusal ? <span className="door-upcoming-refusal" data-testid="door-arm-refusal">{refusal}</span> : null}
      </span>
    );
  }

  // Unarmed: RECORD THIS button + PREP (F8: only when person_label is present).
  return (
    <span className="door-upcoming-arm-actions" data-testid="door-arm-actions">
      <Button
        dense
        variant="ghost"
        loading={busy}
        disabled={busy}
        data-testid="door-record-this"
        onClick={() => void arm()}
      >
        Record this
      </Button>
      {item.person_label && item.person_relationship_id ? (
        <Button
          dense
          variant="ghost"
          data-testid="door-prep"
          onClick={() => openSurfaceOr("open-people", "/", `people:${item.person_relationship_id}:prep`)}
        >
          Prep
        </Button>
      ) : null}
      {refusal ? <span className="door-upcoming-refusal" data-testid="door-arm-refusal">{refusal}</span> : null}
    </span>
  );
}

function UpcomingRail({ upcoming, calendarConfigured, onReload }: { upcoming: DoorUpcomingItem[]; calendarConfigured: boolean; onReload: () => void }) {
  const showChips = hasMultipleSources(upcoming);
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
                {/* HS-147-02: arm/cancel verb on EVENT rows. */}
                <UpcomingRowActions item={item} onReload={onReload} />
                {/* HS-146-04: provenance chip on EVENT rows when >1 source. */}
                {showChips && item.source === "calendar_event" && item.source_label ? (
                  <span className="door-upcoming-provenance">{item.source_label.toUpperCase()}</span>
                ) : null}
                {/* HS-149-03: quiet mono person chip on linked EVENT rows. */}
                {item.person_label ? (
                  <span className="door-upcoming-person" data-testid="door-person-chip">{item.person_label}</span>
                ) : null}
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
      ) : !calendarConfigured ? (
        <div className="door-upcoming-empty door-upcoming-empty--connect">
          <span>No calendar connected.</span>
          <Button dense variant="ghost" onClick={() => useDesk.getState().openSurfaceWindow("configure-settings", "meetings")}>
            Connect calendar
          </Button>
        </div>
      ) : (
        <div className="door-upcoming-empty">No future time scheduled.</div>
      )}
    </section>
  );
}

/** HS-150-02: header chip row for person filter (one per mapped person + EVERYONE). */
type PickerRelationship = { id: string; display_name: string };

function PersonChipRow({ cards, selectedPersonId, onSelect }: {
  cards: DoorCard[];
  selectedPersonId: string | null;
  onSelect: (personId: string | null) => void;
}) {
  const people = new Map<string, string>();
  for (const card of cards) {
    if (card.person_relationship_id && card.person_label) {
      people.set(card.person_relationship_id, card.person_label);
    }
  }
  if (people.size === 0) return null;
  return (
    <div className="door-person-chips" data-testid="door-person-chip-row">
      <button
        type="button"
        className={`door-person-chip-btn${!selectedPersonId ? " door-person-chip-active" : ""}`}
        onClick={() => onSelect(null)}
        data-testid="door-filter-everyone"
      >
        Everyone
      </button>
      {Array.from(people).map(([id, label]) => (
        <button
          key={id}
          type="button"
          className={`door-person-chip-btn${selectedPersonId === id ? " door-person-chip-active" : ""}`}
          onClick={() => onSelect(selectedPersonId === id ? null : id)}
          data-testid="door-filter-person"
        >
          {label}
        </button>
      ))}
    </div>
  );
}

/** HS-150-02: in-card map affordance -- picker of relationships, suggestion-first. */
function MapPicker({
  ownerString,
  onMapped,
  onCancel,
}: {
  ownerString: string;
  onMapped: () => void;
  onCancel: () => void;
}) {
  const [relationships, setRelationships] = useState<PickerRelationship[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    apiFetch<{ relationships?: PickerRelationship[] }>("/api/people/relationships")
      .then((data) => { setRelationships(data.relationships ?? []); setLoading(false); })
      .catch(() => { setLoading(false); setError("Could not load relationships"); });
  }, []);

  const map = async (relId: string) => {
    setBusy(true);
    setError("");
    try {
      await apiFetch(`/api/people/relationships/${encodeURIComponent(relId)}/owner-aliases`, {
        method: "POST",
        json: { alias: ownerString },
      });
      onMapped();
    } catch (cause) {
      setError(readableError(cause));
      setBusy(false);
    }
  };

  const folded = ownerString.toLowerCase();
  const sorted = [...relationships].sort((a, b) => {
    const aMatch = a.display_name.toLowerCase().includes(folded) || folded.includes(a.display_name.toLowerCase());
    const bMatch = b.display_name.toLowerCase().includes(folded) || folded.includes(b.display_name.toLowerCase());
    if (aMatch && !bMatch) return -1;
    if (!aMatch && bMatch) return 1;
    return a.display_name.localeCompare(b.display_name);
  });

  if (loading) return <div className="door-card-map-picker" data-testid="door-card-map-picker">Loading</div>;

  return (
    <div className="door-card-map-picker" data-testid="door-card-map-picker">
      {error ? <span className="door-card-map-error">{error}</span> : null}
      {sorted.length ? sorted.map((rel) => {
        const isSuggested = rel.display_name.toLowerCase().includes(folded) || folded.includes(rel.display_name.toLowerCase());
        return (
          <button
            key={rel.id}
            type="button"
            className="door-card-map-option"
            disabled={busy}
            onClick={() => void map(rel.id)}
            data-testid="door-card-map-option"
          >
            {rel.display_name}{isSuggested ? " (suggested)" : ""}
          </button>
        );
      }) : <span className="door-card-map-empty">No relationships</span>}
      <Button dense variant="ghost" onClick={onCancel}>Cancel</Button>
    </div>
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
  /* HS-150-02: person filter + map affordance state. */
  const [filterPersonId, setFilterPersonId] = useState<string | null>(null);
  const [mappingCardId, setMappingCardId] = useState<string | null>(null);
  /* HS-145-01: scroll-hint listener on the populated viewport. */
  const viewportRef = useRef<HTMLDivElement>(null);

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

  useEffect(() => {
    const el = viewportRef.current;
    if (!el) return;
    const wrap = el.parentElement;
    if (!wrap) return;
    let raf = 0;
    const update = () => {
      raf = 0;
      const hint = computeScrollHint(el.scrollLeft, el.scrollWidth, el.clientWidth);
      if (wrap.dataset.scrollHint !== hint) wrap.dataset.scrollHint = hint;
    };
    const schedule = () => { if (!raf) raf = requestAnimationFrame(update); };
    update();
    el.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    return () => {
      if (raf) cancelAnimationFrame(raf);
      el.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
    };
  });

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
      {/* HS-149-01 L2: quiet named line when People store is not ready. */}
      {peopleStateLabel(projection.people_store_state) ? (
        <div className="door-board-people-state" data-testid="door-people-state">{peopleStateLabel(projection.people_store_state)}</div>
      ) : null}
      {/* HS-150-02: header person chips for filter. */}
      <PersonChipRow cards={cards} selectedPersonId={filterPersonId} onSelect={setFilterPersonId} />
      {cards.length ? (
        <div className="door-board-hint-wrap">
        <div ref={viewportRef} className="door-board-viewport" tabIndex={0} aria-label="Door board, scroll horizontally for all columns">
          <div className="door-board-grid">
          {COLUMNS.map(({ id, label, count }) => {
            const columnCards = (projection.board[id] ?? []).filter(
              (card) => !filterPersonId || card.person_relationship_id === filterPersonId,
            );
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
                    const peopleReady = projection.people_store_state === "ready";
                    const showMap = peopleReady && card.owner && !card.person_label && !isReservedOwner(card.owner);
                    const isMapping = mappingCardId === card.id;
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
                        {/* HS-150-02: person chip for mapped owner (click filters). */}
                        {card.person_label ? (
                          <div className="door-card-person" data-testid="door-card-person-chip">
                            <button
                              type="button"
                              className="door-card-person-btn"
                              onClick={() => setFilterPersonId(card.person_relationship_id || null)}
                            >
                              {card.person_label}
                            </button>
                            {stalenessLabel(card) ? <span className="door-card-staleness" data-testid="door-card-staleness">{stalenessLabel(card)}</span> : null}
                          </div>
                        ) : null}
                        {verbs.length || showMap ? (
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
                            {/* HS-150-02: map affordance on unmapped non-reserved owners. */}
                            {showMap ? (
                              <div className="door-card-action">
                                {isMapping ? (
                                  <MapPicker
                                    ownerString={card.owner!}
                                    onMapped={() => { setMappingCardId(null); void reload(); }}
                                    onCancel={() => setMappingCardId(null)}
                                  />
                                ) : (
                                  <Button
                                    dense
                                    variant="ghost"
                                    data-testid="door-card-map-btn"
                                    onClick={() => setMappingCardId(card.id)}
                                  >
                                    map&hellip;
                                  </Button>
                                )}
                              </div>
                            ) : null}
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
        </div>
      ) : <SurfaceState empty emptyLabel="Door clear" />}
      <UpcomingRail upcoming={projection.upcoming} calendarConfigured={projection.calendar_configured} onReload={() => void reload()} />
    </SurfaceSection>
  );
}
