// HS-135-04 — People is a single protected Desk application.  Its roster is
// a relationship projection, never a field of person tiles or a scorecard.
import { useCallback, useEffect, useMemo, useState } from "react";
import type { CoreProps } from "./core-types";
import { Button } from "../../components/signal/Signal";
import { ApiError, apiFetch, readableError } from "../../lib/api";
import { openSurfaceOr } from "../../desk/shell";
import { CycleGadget, EgressChip, PadGadget, StringGadget } from "../../desk/surface/gadgets";
import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
import {
  ConfirmVerb,
  SurfaceColumns,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceSplit,
  SurfaceState,
} from "../../desk/surface/Surface";
import { countToken } from "../../desk/surface";
import { renderHeroSlot } from "./core-layout";
import "./people.css";

type ReadinessState = "unconfigured" | "locked" | "key_unavailable" | "corrupt" | "unavailable" | "ready";
type Visibility = "shared_intent" | "leader_private";
type RelationshipKind = "direct_report" | "peer" | "extended";
type Lens = "now" | "prep" | "one-on-ones" | "context" | "history" | "info";

type Readiness = {
  readiness?: ReadinessState;
  state?: ReadinessState;
  store?: "encrypted" | "absent";
  sync?: "local_only";
  capture?: "notes_only";
};
type CalendarLink = { uid: string; source_id: string; label: string; linked_at?: string };
type UpcomingEvent = { id: string; uid: string; title: string; starts_at: string; ends_at: string; source_id: string; source_label?: string };
type Relationship = {
  id: string;
  display_name: string;
  relationship_kind?: string;
  role_context?: string | null;
  cadence?: string | null;
  next_one_on_one?: string | null;
  manager_commitment_count?: number;
  open_request_count?: number;
  project_refs?: string[];
  calendar_links?: CalendarLink[] | null;
  /* HS-150-02: owner aliases for the delegation lane. */
  owner_aliases?: string[] | null;
};
type AgendaItem = { id: string; body: string; visibility: Visibility; state: string; rolled_from_id?: string | null };
type Session = { id: string; occurred_at?: string; title?: string; agenda?: AgendaItem[] };
type GroundingNote = { id: string; topic?: string; body: string; visibility: Visibility; source?: string };
type CommitmentEvent = { event: string; state: string; at: string; source: string; rationale?: string; evidence?: Array<Record<string, unknown>> };
type Commitment = { id: string; body: string; due?: string | null; state?: string; history?: CommitmentEvent[]; execution_links?: Array<{ workbench_id: string; item_id: string }> };
type Workbench = { id: string; name: string };
type Project = { id: string; name: string; description?: string };
type ExecutionItem = { id: string; workbench_id: string; status: string; result?: string | null; result_artifact_id?: string | null; completed_at?: string | null };
type BriefActionItem = { id: string; task: string; owner: string | null; due: string | null };
type BriefDecision = { id: string; decision_text: string; rationale: string | null; lifecycle: string };
type BriefMeeting = { meeting_id: string; title: string | null; started_at: string; open_action_items: BriefActionItem[]; decisions: BriefDecision[] };
type WatchPR = { title: string; repo: string; pr_number: number; days_waiting: number; url: string; room_id: string; room_name: string };
type WatchAssignment = { summary: string; key: string; status: string; url: string; overdue: boolean; room_id: string; room_name: string };
type WatchSummary = { prs_waiting: WatchPR[]; oldest_waiting_days: number; open_assignments: WatchAssignment[] };
type BriefLastMeeting = { meeting_id: string; title: string | null; item_count: number; open_count: number };
type OneOnOneBrief = {
  relationship_id: string;
  display_name: string | null;
  open_commitments: Array<{ id: string; body: string; visibility: Visibility; state?: string; due?: string | null }>;
  agenda_items: Array<{ id: string; body: string; visibility: Visibility; state: string }>;
  grounding_note_count: number;
  linked_meetings: BriefMeeting[];
  unlinked_meeting_count: number;
  watch_summary?: WatchSummary;
  last_meeting?: BriefLastMeeting | null;
};
type RelationshipDetail = Relationship & {
  commitments?: Commitment[];
  requests?: Array<{ id: string; body: string; state: string }>;
  sessions?: Session[];
  notes?: GroundingNote[];
};

function stateOf(value: Readiness): ReadinessState {
  return value.state ?? value.readiness ?? "unconfigured";
}

function readinessFace(state: ReadinessState) {
  switch (state) {
    case "locked": return { label: "Locked", action: "Retry" };
    case "key_unavailable": return { label: "Key unavailable", action: "Recovery" };
    case "corrupt":
    case "unavailable": return { label: "Store unavailable", action: "Recovery" };
    default: return { label: "Not set up", action: "Set up" };
  }
}

function readinessForError(cause: unknown): Readiness {
  if (!(cause instanceof ApiError)) return { readiness: "corrupt" };
  const code = String(
    cause.payload && typeof cause.payload === "object"
      ? (cause.payload as Record<string, unknown>).detail ?? ""
      : "",
  );
  if (cause.status === 423 || code === "people_key_store_locked") return { readiness: "locked" };
  if (code.startsWith("people_key_")) return { readiness: "key_unavailable" };
  if (cause.status === 503 || code.startsWith("people_store_")) return { readiness: "unavailable" };
  return { readiness: "corrupt" };
}

/** A protected-plane failure means the encrypted DTOs must leave memory. */
function isProtectedFailure(cause: unknown): boolean {
  if (!(cause instanceof ApiError)) return false;
  if ([409, 423, 503].includes(cause.status)) return true;
  const code = String(
    cause.payload && typeof cause.payload === "object"
      ? (cause.payload as Record<string, unknown>).detail ?? ""
      : "",
  ).toLowerCase();
  return code.startsWith("people_store_") || code.startsWith("people_key_");
}

function facts() {
  return <><span className="people-fact">Encrypted</span><span className="people-fact">Local storage</span><span className="people-fact">Notes only</span></>;
}

export function PeopleCore({ hero, scope }: CoreProps) {
  const [readiness, setReadiness] = useState<Readiness>({ readiness: "unconfigured" });
  const [loading, setLoading] = useState(true);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<RelationshipDetail | null>(null);
  const [newName, setNewName] = useState("");
  const [newKind, setNewKind] = useState<RelationshipKind>("direct_report");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const requestedScope = scope?.startsWith("people:") ? scope.slice("people:".length) : null;
  const requestedRelationshipId = requestedScope?.includes(":") ? requestedScope.split(":")[0] : requestedScope;
  const requestedLens = requestedScope?.includes(":") ? requestedScope.split(":")[1] as Lens : null;

  const clearProtected = useCallback(() => {
    setRelationships([]);
    setSelectedId(null);
    setDetail(null);
    setNewName("");
  }, []);
  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const next = await apiFetch<Readiness>("/api/people/readiness");
      setReadiness(next);
      if (stateOf(next) !== "ready") { clearProtected(); return; }
      const list = await apiFetch<{ relationships?: Relationship[] }>("/api/people/relationships");
      setRelationships(list.relationships ?? []);
    } catch (cause) {
      clearProtected();
      setReadiness(readinessForError(cause));
      setError(readableError(cause));
    } finally { setLoading(false); }
  }, [clearProtected]);
  useEffect(() => { void load(); }, [load]);

  const unavailable = stateOf(readiness) !== "ready";
  const openSettings = () => openSurfaceOr("configure-settings", "/settings", "people-security");
  const recover = () => {
    if (stateOf(readiness) === "locked") { void load(); return; }
    if (stateOf(readiness) !== "unconfigured") { openSettings(); return; }
    void apiFetch("/api/people/setup", { method: "POST", json: {} })
      .then(() => load())
      .catch((cause) => protectedFailure(cause));
  };
  const select = async (id: string) => {
    setSelectedId(id); setDetail(null); setError("");
    try {
      const [relationship, sessions] = await Promise.all([
        apiFetch<{ relationship: Relationship }>(`/api/people/relationships/${encodeURIComponent(id)}`),
        apiFetch<{ one_on_ones: Session[] }>(`/api/people/relationships/${encodeURIComponent(id)}/one-on-ones`),
      ]);
      setDetail({ ...relationship.relationship, sessions: sessions.one_on_ones });
    } catch (cause) { protectedFailure(cause); }
  };
  useEffect(() => {
    if (
      stateOf(readiness) === "ready" &&
      requestedRelationshipId &&
      requestedRelationshipId !== selectedId &&
      relationships.some((relationship) => relationship.id === requestedRelationshipId)
    ) void select(requestedRelationshipId);
  }, [readiness, relationships, requestedRelationshipId, selectedId]); // selection is a response to the opaque Desk scope
  const createRelationship = async () => {
    const display_name = newName.trim(); if (!display_name) return;
    setBusy(true); setError("");
    try {
      const created = await apiFetch<{ relationship: Relationship }>("/api/people/relationships", { method: "POST", json: { display_name, relationship_kind: newKind } });
      setNewName(""); await load(); await select(created.relationship.id);
    } catch (cause) { protectedFailure(cause); } finally { setBusy(false); }
  };
  function protectedFailure(cause: unknown) {
    if (!isProtectedFailure(cause)) {
      setError(readableError(cause));
      return;
    }
    clearProtected();
    setReadiness(readinessForError(cause));
    setError(readableError(cause));
  }
  const selected = detail ?? relationships.find((row) => row.id === selectedId) ?? null;
  const verbs = unavailable ? null : <Button dense variant="primary" onClick={() => document.getElementById("people-new-relationship")?.focus()}>New relationship</Button>;

  if (loading) return <SurfaceState loading />;
  if (unavailable) {
    const face = readinessFace(stateOf(readiness));
    const isUnconfigured = stateOf(readiness) === "unconfigured";
    return <div className="people-joy-state" data-testid="people-joy-state">
      <div className="people-joy-lead">
        <Button variant="primary" onClick={recover} data-testid="people-joy-action">{isUnconfigured ? "Set up People" : face.action}</Button>
        <span className="people-joy-line">{isUnconfigured ? "Encrypted, local-only relationship context" : face.label}</span>
      </div>
      {error ? <span className="sr-only">{error}</span> : null}
    </div>;
  }
  return <div className="people-surface">
    {renderHeroSlot(hero, verbs, facts())}
    {error ? <SurfaceState error={error} onRetry={() => void load()} /> : null}
    <SurfaceSplit
      detailOpen={Boolean(selected)}
      main={<Roster relationships={relationships} selectedId={selectedId} newName={newName} setNewName={setNewName} newKind={newKind} setNewKind={setNewKind} busy={busy} onCreate={() => void createRelationship()} onSelect={(id) => void select(id)} />}
      detail={selected ? <RelationshipPane relationship={selected} initialLens={requestedLens} onRefresh={() => void select(selected.id)} onProtectedFailure={protectedFailure} onArchived={() => { clearProtected(); void load(); }} onBack={() => { setSelectedId(null); setDetail(null); }} /> : undefined}
    />
  </div>;
}

function Roster({ relationships, selectedId, newName, setNewName, newKind, setNewKind, busy, onCreate, onSelect }: {
  relationships: Relationship[]; selectedId: string | null; newName: string; setNewName(value: string): void; newKind: RelationshipKind; setNewKind(value: RelationshipKind): void; busy: boolean; onCreate(): void; onSelect(id: string): void;
}) {
  const ordered = useMemo(() => [...relationships].sort((a, b) => (Number(b.manager_commitment_count ?? 0) - Number(a.manager_commitment_count ?? 0)) || a.display_name.localeCompare(b.display_name)), [relationships]);
  return <SurfaceSection label="Relationships">
    <div className="people-new">
      <StringGadget mic={false} label="New relationship" value={newName} onChange={setNewName} placeholder="Name" inputProps={{ id: "people-new-relationship" }} onKeyDown={(event) => { if (event.key === "Enter") onCreate(); }} />
      <CycleGadget label="Relationship" value={newKind} onChange={(value) => setNewKind(value as RelationshipKind)} options={[{ value: "direct_report", label: "Direct report" }, { value: "peer", label: "Peer" }, { value: "extended", label: "Extended" }]} />
      <Button dense disabled={!newName.trim() || busy} loading={busy} onClick={onCreate}>Add</Button>
    </div>
    {!ordered.length ? <div className="people-empty-roster" data-testid="people-empty-roster"><p className="people-empty-lead">Add a relationship to start</p></div> : <SurfaceRows>{ordered.map((relationship) => <SurfaceRow key={relationship.id} selected={selectedId === relationship.id} title={relationship.display_name} detail={`${relationshipLabel(relationship.relationship_kind)}${relationship.next_one_on_one ? ` · ${relationship.next_one_on_one}` : ""}`} meta={relationship.manager_commitment_count ? `You owe ${relationship.manager_commitment_count}` : undefined} onOpen={() => onSelect(relationship.id)} />)}</SurfaceRows>}
  </SurfaceSection>;
}

/** HS-172-05: concern focus for Now wing opened from Prep summary rows. */
type NowConcern = "prs" | "assignments" | "commitments" | null;

function RelationshipPane({ relationship, initialLens, onRefresh, onProtectedFailure, onArchived, onBack }: { relationship: RelationshipDetail; initialLens?: Lens | null; onRefresh(): void; onProtectedFailure(cause: unknown): void; onArchived(): void; onBack(): void }) {
  const [lens, setLens] = useState<Lens>(initialLens || "now");
  const [upcomingEvents, setUpcomingEvents] = useState<UpcomingEvent[]>([]);
  const [nowConcern, setNowConcern] = useState<NowConcern>(null);
  const [prepBrief, setPrepBrief] = useState<OneOnOneBrief | null>(null);
  useEffect(() => {
    void apiFetch<{ upcoming?: UpcomingEvent[] }>("/api/door")
      .then((door) => {
        const events = (door.upcoming ?? []).filter(
          (item: Record<string, unknown>) => item.source === "calendar_event" && item.uid,
        ) as UpcomingEvent[];
        setUpcomingEvents(events);
      })
      .catch(() => setUpcomingEvents([]));
  }, [relationship.id]);
  const links = relationship.calendar_links ?? [];
  const linkedKeys = new Set(links.map((l) => `${l.uid}:${l.source_id}`));
  const nextLinked = upcomingEvents.find((ev) => linkedKeys.has(`${ev.uid}:${ev.source_id}`));
  const nextLabel = nextLinked ? shortWhen(nextLinked.starts_at) : null;
  const openConcern = useCallback((concern: NowConcern, brief: OneOnOneBrief) => {
    setPrepBrief(brief);
    setNowConcern(concern);
    setLens("now");
  }, []);
  const switchLens = useCallback((id: Lens) => {
    setLens(id);
    if (id !== "now") setNowConcern(null);
  }, []);
  return <div className="people-detail">
    <div className="people-detail-head"><Button dense variant="ghost" onClick={onBack}>Back</Button><strong>{relationship.display_name}</strong></div>
    {nextLabel ? <div className="people-next-header" data-testid="people-next-1on1">NEXT 1:1 &middot; {nextLabel}</div> : null}
    <div className="people-lenses" role="tablist" aria-label={`${relationship.display_name} lenses`}>
      {([['now', 'Now'], ['prep', 'Prep'], ['one-on-ones', '1:1s'], ['context', 'Context'], ['history', 'History'], ['info', 'Info']] as const).map(([id, label]) => <Button key={id} dense variant="ghost" role="tab" aria-selected={lens === id} onClick={() => switchLens(id)}>{label}</Button>)}
    </div>
    {lens === "now" ? <NowLens relationship={relationship} onRefresh={onRefresh} onProtectedFailure={onProtectedFailure} concern={nowConcern} prepBrief={prepBrief} /> : null}
    {lens === "prep" ? <PrepLens relationship={relationship} onProtectedFailure={onProtectedFailure} onOpenConcern={openConcern} /> : null}
    {lens === "one-on-ones" ? <OneOnOnes relationship={relationship} onRefresh={onRefresh} onProtectedFailure={onProtectedFailure} /> : null}
    {lens === "context" ? <ContextLens relationship={relationship} onRefresh={onRefresh} onProtectedFailure={onProtectedFailure} upcomingEvents={upcomingEvents} /> : null}
    {lens === "history" ? <HistoryLens relationship={relationship} /> : null}
    {lens === "info" ? <InfoLens relationship={relationship} onArchived={onArchived} onProtectedFailure={onProtectedFailure} /> : null}
  </div>;
}

function shortWhen(isoDate: string): string {
  try {
    const d = new Date(isoDate);
    if (Number.isNaN(d.getTime())) return "";
    const now = new Date();
    const diffMs = d.getTime() - now.getTime();
    const diffDays = Math.floor(diffMs / 86_400_000);
    const time = d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
    if (diffDays === 0) return `TODAY ${time}`;
    if (diffDays === 1) return `TOMORROW ${time}`;
    const day = d.toLocaleDateString(undefined, { weekday: "short" }).toUpperCase();
    return `${day} ${time}`;
  } catch { return ""; }
}

/** HS-172-05: build the `N PRS WAITING ON {name}` summary label.
 * If the name will not fit at 393, falls back to `N PRS WAITING`. */
export function prsSummaryLabel(count: number, displayName: string): string {
  const label = `${count} ${count === 1 ? "PR" : "PRS"} WAITING ON ${displayName.toUpperCase()}`;
  if (label.length > 30) return `${count} ${count === 1 ? "PR" : "PRS"} WAITING`;
  return label;
}

/** HS-172-05: cap inline reference tokens at three, then `+N`. */
export function capTokens(items: string[], max: number = 3): string {
  if (items.length === 0) return "";
  const shown = items.slice(0, max);
  const rest = items.length - max;
  const parts = shown.join(" · ");
  return rest > 0 ? `${parts} +${rest}` : parts;
}

/** HS-149-04 / HS-172-05: the Prep lens -- the 1:1 brief enrichment.
 * Display step = the person's name. Summary rows (absent at zero).
 * AGENDA section. Footer THIS DEVICE + PREPARED hh:mm. */
function PrepLens({ relationship, onProtectedFailure, onOpenConcern }: { relationship: RelationshipDetail; onProtectedFailure(cause: unknown): void; onOpenConcern(concern: NowConcern, brief: OneOnOneBrief): void }) {
  const [brief, setBrief] = useState<OneOnOneBrief | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [preparedAt] = useState(() => {
    const now = new Date();
    return now.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", hour12: false });
  });
  useEffect(() => {
    setLoading(true); setError("");
    void apiFetch<{ brief: OneOnOneBrief }>(`/api/people/relationships/${encodeURIComponent(relationship.id)}/brief`)
      .then((result) => setBrief(result.brief))
      .catch((cause) => {
        setBrief(null);
        if (typeof cause === "object" && cause !== null && "status" in cause && (cause as { status: number }).status === 503) {
          setError("People store locked");
        } else {
          onProtectedFailure(cause);
        }
      })
      .finally(() => setLoading(false));
  }, [relationship.id]);
  if (loading) return <SurfaceState loading />;
  if (error) return <SurfaceState error={error} data-testid="prep-locked" />;
  if (!brief) return <SurfaceState empty emptyLabel="Brief unavailable" />;

  const ws = brief.watch_summary;
  const prCount = ws?.prs_waiting?.length ?? 0;
  const assignCount = ws?.open_assignments?.length ?? 0;
  const overdueCommitments = brief.open_commitments.filter((c) => {
    if (!c.due) return false;
    try { return new Date(c.due) < new Date(); } catch { return false; }
  });
  const overdueCount = overdueCommitments.length;
  const lm = brief.last_meeting;
  const displayName = brief.display_name ?? relationship.display_name;
  const agendaCount = brief.agenda_items.length;

  // PR reference tokens: cap at 3 then +N
  const prNumbers = (ws?.prs_waiting ?? []).map((pr) => `#${pr.pr_number}`);
  const prTokenStr = capTokens(prNumbers);

  // Assignment keys
  const assignKeys = (ws?.open_assignments ?? []).map((a) => a.key).filter(Boolean);
  const assignTokenStr = capTokens(assignKeys);
  const anyOverdueAssignment = (ws?.open_assignments ?? []).some((a) => a.overdue);

  return <div data-testid="people-prep-lens" className="people-prep-enriched">
    {/* Display step: person's name */}
    <div className="people-prep-display" data-testid="prep-display-name">{displayName}</div>

    {/* Summary rows (each absent at zero -- UX-CANON A.8) */}
    <div className="people-prep-summary" data-testid="prep-summary-rows">
      {prCount > 0 ? (
        <div className="people-prep-row" data-testid="prep-prs-row">
          <div className="people-prep-row-main">
            <span className="people-prep-row-primary" data-testid="prep-prs-label">{prsSummaryLabel(prCount, displayName)}</span>
            <span className="people-prep-row-tokens">
              {ws?.oldest_waiting_days ? <span className="people-prep-token" data-warning={ws.oldest_waiting_days >= 3 || undefined} data-testid="prep-prs-days">{ws.oldest_waiting_days}+ DAYS</span> : null}
              {prTokenStr ? <span className="people-prep-token people-prep-token-muted" data-testid="prep-prs-numbers">{prTokenStr}</span> : null}
            </span>
            <span className="people-prep-row-spacer" />
            <Button dense variant="ghost" onClick={() => onOpenConcern("prs", brief)} data-testid="prep-prs-open">Open</Button>
          </div>
        </div>
      ) : null}

      {assignCount > 0 ? (
        <div className="people-prep-row" data-testid="prep-assignments-row">
          <div className="people-prep-row-main">
            <span className="people-prep-row-primary" data-testid="prep-assignments-label">{assignCount} {assignCount === 1 ? "ASSIGNMENT" : "ASSIGNMENTS"} OPEN</span>
            <span className="people-prep-row-tokens">
              {assignTokenStr ? <span className="people-prep-token people-prep-token-muted" data-testid="prep-assignments-keys">{assignTokenStr}</span> : null}
              {anyOverdueAssignment ? <span className="people-prep-token" data-warning="true" data-testid="prep-assignments-overdue">OVERDUE</span> : null}
            </span>
            <span className="people-prep-row-spacer" />
            <Button dense variant="ghost" onClick={() => onOpenConcern("assignments", brief)} data-testid="prep-assignments-open">Open</Button>
          </div>
        </div>
      ) : null}

      {overdueCount > 0 ? (
        <div className="people-prep-row" data-testid="prep-commitments-row">
          <div className="people-prep-row-main">
            <span className="people-prep-row-primary" data-testid="prep-commitments-label">{overdueCount} {overdueCount === 1 ? "COMMITMENT" : "COMMITMENTS"} OVERDUE</span>
            <span className="people-prep-row-tokens">
              {overdueCommitments[0] ? <span className="people-prep-token people-prep-token-muted">{overdueCommitments[0].body.length > 30 ? overdueCommitments[0].body.slice(0, 30) : overdueCommitments[0].body}</span> : null}
              {overdueCommitments[0]?.due ? <span className="people-prep-token" data-warning="true">BY {new Date(overdueCommitments[0].due).toLocaleDateString(undefined, { weekday: "short" }).toUpperCase()}</span> : null}
            </span>
            <span className="people-prep-row-spacer" />
            <Button dense variant="ghost" onClick={() => onOpenConcern("commitments", brief)} data-testid="prep-commitments-open">Open</Button>
          </div>
        </div>
      ) : null}

      {lm && lm.item_count > 0 ? (
        <div className="people-prep-row" data-testid="prep-meeting-row">
          <div className="people-prep-row-main">
            <span className="people-prep-row-primary">LAST MEETING</span>
            <span className="people-prep-row-tokens">
              <span className="people-prep-token people-prep-token-muted" data-testid="prep-meeting-items">{lm.item_count} {lm.item_count === 1 ? "ITEM" : "ITEMS"}</span>
              {lm.open_count > 0 ? <span className="people-prep-token people-prep-token-muted" data-testid="prep-meeting-open-count">{lm.open_count} OPEN</span> : null}
            </span>
            <span className="people-prep-row-spacer" />
            <Button dense variant="ghost" onClick={() => openSurfaceOr("review-meetings", "/history", lm.meeting_id)} data-testid="prep-meeting-open">Open</Button>
          </div>
        </div>
      ) : null}
    </div>

    {/* AGENDA section (unchanged from existing) */}
    {agendaCount > 0 ? (
      <div data-testid="prep-agenda">
        <SurfaceSection label={`Agenda ${agendaCount}`}>
          <SurfaceRows>{brief.agenda_items.map((item) => <SurfaceRow key={item.id} title={item.body} />)}</SurfaceRows>
        </SurfaceSection>
      </div>
    ) : null}

    {/* Footer: THIS DEVICE + PREPARED hh:mm */}
    <SurfaceFooter
      egress={<EgressChip label="THIS DEVICE" scope="local" />}
      receipt={<span className="people-prep-receipt" data-testid="prep-receipt">PREPARED {preparedAt}</span>}
    />
  </div>;
}

/** HS-149-03: the picker + linked series + unlink two-beat. In-world, no modal. */
function CalendarLinkSection({ relationship, onRefresh, onProtectedFailure, upcomingEvents }: { relationship: RelationshipDetail; onRefresh(): void; onProtectedFailure(cause: unknown): void; upcomingEvents: UpcomingEvent[] }) {
  const [pickerOpen, setPickerOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const links = relationship.calendar_links ?? [];
  const linkedKeys = new Set(links.map((l) => `${l.uid}:${l.source_id}`));
  // In-memory suggestion sort: display_name-containing rows first (case-insensitive, F10: never logged/persisted).
  const displayName = relationship.display_name;
  const available = upcomingEvents.filter((ev) => !linkedKeys.has(`${ev.uid}:${ev.source_id}`));
  const sorted = useMemo(() => {
    const lower = displayName.toLowerCase();
    const suggested: UpcomingEvent[] = [];
    const rest: UpcomingEvent[] = [];
    for (const ev of available) {
      if (ev.title.toLowerCase().includes(lower)) {
        suggested.push(ev);
      } else {
        rest.push(ev);
      }
    }
    return { suggested, rest, all: [...suggested, ...rest] };
  }, [available, displayName]);

  const linkEvent = async (ev: UpcomingEvent) => {
    setBusy(true);
    try {
      await apiFetch(`/api/people/relationships/${encodeURIComponent(relationship.id)}/calendar-links`, {
        method: "POST",
        json: { uid: ev.uid, source_id: ev.source_id, label: ev.title },
      });
      setPickerOpen(false);
      onRefresh();
    } catch (cause) { onProtectedFailure(cause); } finally { setBusy(false); }
  };
  const unlinkSeries = async (link: CalendarLink) => {
    setBusy(true);
    try {
      await apiFetch(`/api/people/relationships/${encodeURIComponent(relationship.id)}/calendar-links`, {
        method: "DELETE",
        json: { uid: link.uid, source_id: link.source_id },
      });
      onRefresh();
    } catch (cause) { onProtectedFailure(cause); } finally { setBusy(false); }
  };

  return <SurfaceSection label="Calendar series">
    {links.length ? <SurfaceRows>{links.map((link) => <SurfaceRow
      key={`${link.uid}:${link.source_id}`}
      title={link.label || "Linked series"}
      detail={link.linked_at ? `Linked ${new Date(link.linked_at).toLocaleDateString()}` : undefined}
      verbs={<ConfirmVerb label="Unlink" confirmLabel="Unlink?" busy={busy} onConfirm={() => void unlinkSeries(link)} />}
    />)}</SurfaceRows> : null}
    {pickerOpen ? (
      <div className="people-picker" data-testid="people-event-picker">
        {sorted.all.length ? <SurfaceRows>{sorted.all.map((ev) => {
          const isSuggested = sorted.suggested.includes(ev);
          return <SurfaceRow
            key={`${ev.uid}:${ev.source_id}:${ev.id}`}
            title={ev.title}
            detail={`${shortWhen(ev.starts_at)}${ev.source_label ? ` · ${ev.source_label}` : ""}`}
            meta={isSuggested ? "SUGGESTED" : undefined}
            onOpen={() => void linkEvent(ev)}
          />;
        })}</SurfaceRows> : <SurfaceState empty emptyLabel="No upcoming events" />}
        <Button dense variant="ghost" onClick={() => setPickerOpen(false)}>Cancel</Button>
      </div>
    ) : (
      <Button dense variant="ghost" disabled={busy} onClick={() => setPickerOpen(true)} data-testid="people-link-event">Link calendar event</Button>
    )}
  </SurfaceSection>;
}

/** HS-150-02: owner aliases section on the Context lens, mirroring CalendarLinkSection. */
function OwnerAliasSection({ relationship, onRefresh, onProtectedFailure }: { relationship: RelationshipDetail; onRefresh(): void; onProtectedFailure(cause: unknown): void }) {
  const [newAlias, setNewAlias] = useState("");
  const [busy, setBusy] = useState(false);
  const aliases = relationship.owner_aliases ?? [];

  const addAlias = async () => {
    const alias = newAlias.trim();
    if (!alias) return;
    setBusy(true);
    try {
      await apiFetch(`/api/people/relationships/${encodeURIComponent(relationship.id)}/owner-aliases`, {
        method: "POST",
        json: { alias },
      });
      setNewAlias("");
      onRefresh();
    } catch (cause) { onProtectedFailure(cause); } finally { setBusy(false); }
  };

  const removeAlias = async (alias: string) => {
    setBusy(true);
    try {
      await apiFetch(`/api/people/relationships/${encodeURIComponent(relationship.id)}/owner-aliases`, {
        method: "DELETE",
        json: { alias },
      });
      onRefresh();
    } catch (cause) { onProtectedFailure(cause); } finally { setBusy(false); }
  };

  return <div data-testid="people-owner-aliases"><SurfaceSection label="Owner aliases">
    {aliases.length ? <SurfaceRows>{aliases.map((alias) => <SurfaceRow
      key={alias}
      title={alias}
      verbs={<ConfirmVerb label="Remove" confirmLabel="Remove?" busy={busy} onConfirm={() => void removeAlias(alias)} />}
    />)}</SurfaceRows> : null}
    <div className="people-alias-add" data-testid="people-alias-add">
      <StringGadget mic={false} label="Owner alias" value={newAlias} onChange={setNewAlias} placeholder="Owner string" onKeyDown={(event: React.KeyboardEvent) => { if (event.key === "Enter") void addAlias(); }} />
      <Button dense disabled={!newAlias.trim() || busy} onClick={() => void addAlias()}>Add</Button>
    </div>
  </SurfaceSection></div>;
}

function ContextLens({ relationship, onRefresh, onProtectedFailure, upcomingEvents = [] }: { relationship: RelationshipDetail; onRefresh(): void; onProtectedFailure(cause: unknown): void; upcomingEvents?: UpcomingEvent[] }) {
  const [topic, setTopic] = useState(""); const [body, setBody] = useState(""); const [visibility, setVisibility] = useState<Visibility>("leader_private"); const [busy, setBusy] = useState(false); const [projects, setProjects] = useState<Project[]>([]); const [projectId, setProjectId] = useState("");
  useEffect(() => { void apiFetch<{ projects?: Project[] }>("/api/projects").then((result) => { const rows = result.projects ?? []; setProjects(rows); setProjectId((current) => current || rows[0]?.id || ""); }).catch(onProtectedFailure); }, [relationship.id]);
  const add = async () => { if (!body.trim()) return; setBusy(true); try { await apiFetch(`/api/people/relationships/${encodeURIComponent(relationship.id)}/notes`, { method: "POST", json: { topic: topic.trim(), body: body.trim(), visibility } }); setTopic(""); setBody(""); onRefresh(); } catch (cause) { onProtectedFailure(cause); } finally { setBusy(false); } };
  const linkProject = async () => { if (!projectId) return; try { await apiFetch(`/api/people/relationships/${encodeURIComponent(relationship.id)}/projects/${encodeURIComponent(projectId)}`, { method: "POST", json: {} }); onRefresh(); } catch (cause) { onProtectedFailure(cause); } };
  const unlinkProject = async (id: string) => { try { await apiFetch(`/api/people/relationships/${encodeURIComponent(relationship.id)}/projects/${encodeURIComponent(id)}`, { method: "DELETE" }); onRefresh(); } catch (cause) { onProtectedFailure(cause); } };
  const linkedProjects = projects.filter((project) => relationship.project_refs?.includes(project.id));
  return <>
    <CalendarLinkSection relationship={relationship} onRefresh={onRefresh} onProtectedFailure={onProtectedFailure} upcomingEvents={upcomingEvents} />
    <OwnerAliasSection relationship={relationship} onRefresh={onRefresh} onProtectedFailure={onProtectedFailure} />
    <SurfaceSection label="Projects"><div className="people-project-link"><CycleGadget label="Project" value={projectId} onChange={setProjectId} options={projects.map((project) => ({ value: project.id, label: project.name }))} /><Button dense disabled={!projectId || relationship.project_refs?.includes(projectId)} onClick={() => void linkProject()}>Link</Button></div>{linkedProjects.length ? <SurfaceRows>{linkedProjects.map((project) => <SurfaceRow key={project.id} title={project.name} detail={project.description} onOpen={() => openSurfaceOr("open-project-memory", "/project-memory", `project:${project.id}`)} verbs={<Button dense variant="ghost" onClick={() => void unlinkProject(project.id)}>Unlink</Button>} />)}</SurfaceRows> : <SurfaceState empty emptyLabel="No linked projects" />}</SurfaceSection>
    <SurfaceSection label="Grounding notes"><div className="people-context-add"><StringGadget mic={false} label="Topic" value={topic} onChange={setTopic} placeholder="Topic (optional)" /><PadGadget mic={false} label="Grounding note" value={body} onChange={setBody} placeholder="Context worth remembering" rows={3} /><CycleGadget label="Visibility" value={visibility} onChange={(value) => setVisibility(value as Visibility)} options={[{ value: "leader_private", label: "Leader private" }, { value: "shared_intent", label: "Shared" }]} /><Button dense disabled={!body.trim() || busy} onClick={() => void add()}>Add note</Button></div>{!(relationship.notes ?? []).length ? <SurfaceState empty emptyLabel="No grounding notes" /> : <SurfaceRows>{(relationship.notes ?? []).map((note) => <SurfaceRow key={note.id} title={note.topic || note.body} detail={note.topic ? note.body : undefined} meta={note.visibility === "leader_private" ? "Leader private" : "Shared"} />)}</SurfaceRows>}</SurfaceSection>
  </>;
}

function relationshipLabel(kind?: string): string {
  if (kind === "direct_report") return "Direct report";
  if (kind === "peer") return "Peer";
  if (kind === "extended") return "Extended relationship";
  return "Relationship";
}

function NowLens({ relationship, onRefresh, onProtectedFailure, concern, prepBrief }: { relationship: RelationshipDetail; onRefresh(): void; onProtectedFailure(cause: unknown): void; concern?: NowConcern; prepBrief?: OneOnOneBrief | null }) {
  const [request, setRequest] = useState(""); const [busy, setBusy] = useState(false); const [selectedCommitment, setSelectedCommitment] = useState<Commitment | null>(null);
  const createRequest = async () => { if (!request.trim()) return; setBusy(true); try { await apiFetch(`/api/people/relationships/${encodeURIComponent(relationship.id)}/requests`, { method: "POST", json: { body: request.trim(), visibility: "shared_intent", source: { kind: "manual" } } }); setRequest(""); onRefresh(); } catch (cause) { onProtectedFailure(cause); } finally { setBusy(false); } };
  const accept = async (id: string) => { try { await apiFetch(`/api/people/requests/${encodeURIComponent(id)}/accept`, { method: "POST", json: {} }); onRefresh(); } catch (cause) { onProtectedFailure(cause); } };

  // HS-172-05: when opened from a Prep summary row, show per-entity detail rows.
  // SurfaceLedgerRow with wrap: titles wrap to two lines, repo token below.
  if (concern && prepBrief) {
    const ws = prepBrief.watch_summary;
    const prTotal = ws?.prs_waiting?.length ?? 0;
    const assignTotal = ws?.open_assignments?.length ?? 0;
    const overdueList = prepBrief.open_commitments.filter((c) => { if (!c.due) return false; try { return new Date(c.due) < new Date(); } catch { return false; } });
    const overdueTotal = overdueList.length;
    return <div data-testid="people-now-concern">
      {concern === "prs" && ws && prTotal > 0 ? (
        <div data-testid="now-prs-detail">
        <SurfaceLedger count={`PRS WAITING ${prTotal}`} cols="room">
          {ws.prs_waiting.map((pr) => (
            <SurfaceLedgerRow
              key={`pr-${pr.pr_number}`}
              primary={<span className="surface-primary">{`#${pr.pr_number} · ${pr.title}`}</span>}
              wrap
              cells={
                <span className="people-now-caption">
                  <span className={pr.days_waiting >= 3 ? "people-now-caption-warning" : ""}>{pr.days_waiting} {pr.days_waiting === 1 ? "DAY" : "DAYS"}</span>
                  {pr.repo ? <> · <span>{pr.repo.toUpperCase()}</span></> : null}
                </span>
              }
              trailing={pr.url ? <Button dense variant="ghost" onClick={() => window.open(pr.url, "_blank", "noopener")}>Open</Button> : undefined}
              expands={false}
            />
          ))}
        </SurfaceLedger>
        </div>
      ) : null}
      {concern === "assignments" && ws && assignTotal > 0 ? (
        <div data-testid="now-assignments-detail">
        <SurfaceLedger count={`ASSIGNMENTS OPEN ${assignTotal}`} cols="room">
          {ws.open_assignments.map((a) => (
            <SurfaceLedgerRow
              key={a.key}
              primary={<span className="surface-primary">{`${a.key} · ${a.summary}`}</span>}
              wrap
              cells={
                <span className="people-now-caption">
                  <span>{a.status.toUpperCase()}</span>
                  {a.overdue ? <> · <span className="people-now-caption-warning">OVERDUE</span></> : null}
                </span>
              }
              trailing={a.url ? <Button dense variant="ghost" onClick={() => window.open(a.url, "_blank", "noopener")}>Open</Button> : undefined}
              expands={false}
            />
          ))}
        </SurfaceLedger>
        </div>
      ) : null}
      {concern === "commitments" && overdueTotal > 0 ? (
        <div data-testid="now-commitments-detail">
        <SurfaceLedger count={`COMMITMENTS OVERDUE ${overdueTotal}`} cols="room">
          {overdueList.map((c) => (
            <SurfaceLedgerRow
              key={c.id}
              primary={<span className="surface-primary">{c.body}</span>}
              wrap
              cells={
                <span className="people-now-caption">
                  {c.due ? <span className="people-now-caption-warning">BY {new Date(c.due).toLocaleDateString(undefined, { weekday: "short" }).toUpperCase()}</span> : null}
                  {c.due ? " · " : ""}<span className="people-now-caption-warning">OVERDUE</span>
                </span>
              }
              expands={false}
            />
          ))}
        </SurfaceLedger>
        </div>
      ) : null}
    </div>;
  }

  return <SurfaceColumns main={<>
    <SurfaceSection label="You owe"><SurfaceRows>{(relationship.commitments ?? []).length ? (relationship.commitments ?? []).map((item) => <SurfaceRow key={item.id} selected={selectedCommitment?.id === item.id} title={item.body} detail={item.due ?? undefined} meta={item.execution_links?.length ? "Workbench linked" : "Open"} onOpen={() => setSelectedCommitment(item)} />) : <SurfaceState empty emptyLabel="No commitments" />}</SurfaceRows>{selectedCommitment ? <CommitmentInspector commitment={selectedCommitment} onClose={() => setSelectedCommitment(null)} onRefresh={() => { onRefresh(); setSelectedCommitment(null); }} onProtectedFailure={onProtectedFailure} /> : null}</SurfaceSection>
    <SurfaceSection label="Open requests"><div className="people-new"><StringGadget mic={false} label="Request" value={request} onChange={setRequest} placeholder="Request" /><Button dense disabled={!request.trim() || busy} onClick={() => void createRequest()}>Add</Button></div><SurfaceRows>{(relationship.requests ?? []).filter((item) => item.state === "requested").map((item) => <SurfaceRow key={item.id} title={item.body} verbs={<Button dense onClick={() => void accept(item.id)}>Accept</Button>} />)}</SurfaceRows></SurfaceSection>
  </>} side={<SurfaceSection label="Next 1:1"><SurfaceState empty={!relationship.next_one_on_one} emptyLabel="No 1:1 planned">{relationship.next_one_on_one}</SurfaceState></SurfaceSection>} />;
}

function CommitmentInspector({ commitment, onClose, onRefresh, onProtectedFailure }: { commitment: Commitment; onClose(): void; onRefresh(): void; onProtectedFailure(cause: unknown): void }) {
  const [workbenches, setWorkbenches] = useState<Workbench[]>([]); const [workbenchId, setWorkbenchId] = useState(""); const [items, setItems] = useState<ExecutionItem[]>([]); const [rationale, setRationale] = useState(""); const [busy, setBusy] = useState(false);
  const load = useCallback(async () => {
    try {
      const [catalog, execution] = await Promise.all([
        apiFetch<{ workbenches?: Workbench[] }>("/api/workbenches"),
        apiFetch<{ items?: ExecutionItem[] }>(`/api/people/commitments/${encodeURIComponent(commitment.id)}/execution`),
      ]);
      const choices = catalog.workbenches ?? []; setWorkbenches(choices); setItems(execution.items ?? []); setWorkbenchId((current) => current || choices[0]?.id || "");
    } catch (cause) { onProtectedFailure(cause); }
  }, [commitment.id, onProtectedFailure]);
  useEffect(() => { void load(); }, [load]);
  const send = async () => { if (!workbenchId) return; setBusy(true); try { await apiFetch(`/api/people/commitments/${encodeURIComponent(commitment.id)}/workbench`, { method: "POST", json: { workbench_id: workbenchId } }); await load(); } catch (cause) { onProtectedFailure(cause); } finally { setBusy(false); } };
  const satisfy = async () => { setBusy(true); try { await apiFetch(`/api/people/commitments/${encodeURIComponent(commitment.id)}/satisfy`, { method: "POST", json: { rationale: rationale.trim() } }); onRefresh(); } catch (cause) { onProtectedFailure(cause); } finally { setBusy(false); } };
  const linked = items[0];
  return <div className="people-commitment-inspector"><div className="people-inspector-head"><strong>Commitment</strong><Button dense variant="ghost" onClick={onClose}>Close</Button></div><div className="people-commitment-body">{commitment.body}</div>{linked ? <SurfaceRows><SurfaceRow title={linked.result ? "Output ready" : "Workbench item"} detail={linked.result || `Status: ${linked.status}`} meta={linked.status} onOpen={() => openSurfaceOr("open-workbenches", "/workbenches", `workbench:${linked.workbench_id}`)} /></SurfaceRows> : <div className="people-delegate"><CycleGadget label="Workbench" value={workbenchId} onChange={setWorkbenchId} options={workbenches.map((workbench) => ({ value: workbench.id, label: workbench.name }))} /><Button dense disabled={!workbenchId || busy} onClick={() => void send()}>Send to Workbench</Button><span className="egress-badge is-cloud" title="Workbench model">Workbench model</span></div>}<div className="people-satisfy"><StringGadget mic={false} label="Satisfaction note" value={rationale} onChange={setRationale} placeholder="What fulfilled the commitment?" /><Button dense variant="primary" disabled={busy} onClick={() => void satisfy()}>Mark satisfied</Button></div></div>;
}

function HistoryLens({ relationship }: { relationship: RelationshipDetail }) {
  const commitments = relationship.commitments ?? [];
  const satisfied = commitments.filter((item) => item.state === "done").length;
  const evidence = commitments.filter((item) => item.history?.some((event) => Boolean(event.evidence?.length))).length;
  const events = commitments.flatMap((item) => (item.history ?? []).map((event) => ({ ...event, commitment: item.body }))).sort((a, b) => String(b.at).localeCompare(String(a.at)));
  const open = commitments.filter((item) => item.state === "open").length;
  return <><SurfaceSection label="Follow-through"><dl className="people-history-facts"><div><dt>Accepted</dt><dd>{countToken(commitments.length, "COMMITMENT") ?? "—"}</dd></div><div><dt>Satisfied</dt><dd>{countToken(satisfied, "DONE") ?? "—"}</dd></div><div><dt>Open</dt><dd>{countToken(open, "OPEN") ?? "—"}</dd></div><div><dt>With evidence</dt><dd>{countToken(evidence, "EVIDENCED") ?? "—"}</dd></div></dl></SurfaceSection><SurfaceSection label="Timeline">{events.length ? <SurfaceRows>{events.map((event, index) => <SurfaceRow key={`${event.at}-${index}`} title={event.commitment} detail={`${event.event}${event.rationale ? ` · ${event.rationale}` : ""}`} meta={event.at ? new Date(event.at).toLocaleDateString() : undefined} />)}</SurfaceRows> : <SurfaceState empty emptyLabel="No history" />}</SurfaceSection></>;
}

function OneOnOnes({ relationship, onRefresh, onProtectedFailure }: { relationship: RelationshipDetail; onRefresh(): void; onProtectedFailure(cause: unknown): void }) {
  const [draft, setDraft] = useState(""); const [visibility, setVisibility] = useState<Visibility>("shared_intent"); const [busy, setBusy] = useState(false);
  const session = relationship.sessions?.[0];
  const add = async () => { if (!draft.trim()) return; setBusy(true); try { const active = session ?? (await apiFetch<{ one_on_one: Session }>(`/api/people/relationships/${encodeURIComponent(relationship.id)}/one-on-ones`, { method: "POST", json: { visibility } })).one_on_one; await apiFetch(`/api/people/one-on-ones/${encodeURIComponent(active.id)}/agenda`, { method: "POST", json: { body: draft.trim(), visibility, state: "open", source: { kind: "manual" } } }); setDraft(""); onRefresh(); } catch (cause) { onProtectedFailure(cause); } finally { setBusy(false); } };
  const roll = async (item: AgendaItem) => { if (!session) return; try { await apiFetch(`/api/people/one-on-ones/${encodeURIComponent(session.id)}/agenda`, { method: "POST", json: { body: item.body, visibility: item.visibility, state: "open", rolled_from_id: item.id, source: { kind: "manual" } } }); onRefresh(); } catch (cause) { onProtectedFailure(cause); } };
  return <SurfaceSection label="1:1s"><div className="people-agenda-add"><PadGadget mic={false} label="Agenda item" value={draft} onChange={setDraft} placeholder="Agenda item" rows={2} /><CycleGadget label="Visibility" value={visibility} onChange={(value) => setVisibility(value as Visibility)} options={[{ value: "shared_intent", label: "Shared" }, { value: "leader_private", label: "Leader private" }]} /><Button dense disabled={!draft.trim() || busy} onClick={() => void add()}>Add</Button></div>{!session ? <SurfaceState empty emptyLabel="No 1:1s" /> : <SurfaceRows>{(session.agenda ?? []).map((item) => <SurfaceRow key={item.id} title={item.body} detail={item.visibility === "leader_private" ? "Leader private" : "Shared"} meta={item.state} verbs={<Button dense variant="ghost" onClick={() => void roll(item)}>Roll forward</Button>} />)}</SurfaceRows>}</SurfaceSection>;
}

function InfoLens({ relationship, onProtectedFailure, onArchived }: { relationship: RelationshipDetail; onProtectedFailure(cause: unknown): void; onArchived(): void }) {
  const archive = async () => { try { await apiFetch(`/api/people/relationships/${encodeURIComponent(relationship.id)}/archive`, { method: "POST", json: {} }); onArchived(); } catch (cause) { onProtectedFailure(cause); } };
  return <SurfaceSection label="Info"><dl className="people-info"><div><dt>Relationship</dt><dd>{relationshipLabel(relationship.relationship_kind)}</dd></div><div><dt>Role context</dt><dd>{relationship.role_context ?? "Not set"}</dd></div><div><dt>Cadence</dt><dd>{relationship.cadence ?? "Not set"}</dd></div><div><dt>Storage</dt><dd>Encrypted</dd></div><div><dt>Sync</dt><dd>This device only</dd></div><div><dt>Capture</dt><dd>Notes only</dd></div></dl><ConfirmVerb label="Archive" confirmLabel="Archive?" onConfirm={() => void archive()} /></SurfaceSection>;
}
