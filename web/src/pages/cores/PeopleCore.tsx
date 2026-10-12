// HS-135-04: People is a single protected Desk application.  Its roster is
// a relationship projection, never a field of person tiles or a scorecard.
import { wireDate } from "../../desk/surface/format";
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import type { CoreProps } from "./core-types";
import { Button } from "../../components/signal/Signal";
import { ApiError, apiFetch } from "../../lib/api";
import { plainFailure } from "../../desk/surface/plainFailure";
import { openSurfaceOr } from "../../desk/shell";
import { openSourceRef } from "../../desk/surface/citations";
import { PERSON_OPEN_EVENT, refOpener, type PersonOpenRequest } from "../../desk/openObject";
import { peekPersonLens, takePersonLens } from "../../desk/objectWindows";
import { composePeoplePrep, readPeoplePrep, type PeoplePrepData, type PrepCalendarEvent } from "../../desk/people/prepData";
import { announceTaskReturn, taskFocusPending } from "../../desk/returnToTask";
import { useOnDeskChanged } from "../../desk/useDeskChangedRefresh";
import { keepPlace, keptPlace, useDeskDraft } from "../../desk/deskMemory";
import { CycleGadget, EgressChip, PadGadget, StringGadget } from "../../desk/surface/gadgets";
import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
import {
  ConfirmVerb,

  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceSplit,
  SurfaceState,
} from "../../desk/surface/Surface";
import { countToken } from "../../desk/surface";
import { AppTile, Avatar, FigureStrip } from "../../desk/surface/kit";
import { renderHeroSlot } from "./core-layout";
import { useWindowTitle } from "../../desk/surface/title";
import "./people.css";
import { openProjectRoom } from "../../desk/shell";

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
  /** PHILO-17 (U09): what the person owes him, recorded by hand. */
  owed_to_you?: Array<{ id: string; body: string; visibility: Visibility; state?: string; due?: string | null }>;
  agenda_items: Array<{ id: string; body: string; visibility: Visibility; state: string }>;
  grounding_note_count: number;
  linked_meetings: BriefMeeting[];
  unlinked_meeting_count: number;
  watch_summary?: WatchSummary;
  last_meeting?: BriefLastMeeting | null;
};
type RelationshipDetail = Relationship & {
  commitments?: Commitment[];
  /** PHILO-17 (U09): commitments the person owes him (direction report_owes). */
  owed_to_you?: Commitment[];
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
    case "corrupt": return { label: "Store unavailable", action: "Recovery" };
    // PHILO-13-04: a store that is down comes back by itself; the verb tries
    // it again here instead of sending him to Settings (J3-07).
    case "unavailable": return { label: "Store unavailable", action: "Try again" };
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

/** PHILO-13-04 (A3): the store is down (503 / `people_store_*`). The
 * person and the unsent draft stay on the window; the failure is one row
 * with Try again (J3-06). The owner's Tenet 1: no over-engineering for safety. */
function isStoreOutage(cause: unknown): boolean {
  if (!(cause instanceof ApiError)) return false;
  const code = String(
    cause.payload && typeof cause.payload === "object"
      ? (cause.payload as Record<string, unknown>).detail ?? ""
      : "",
  ).toLowerCase();
  return cause.status === 503 || code.startsWith("people_store_");
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

/** PHILO-13-07 (B2) — the People window's place: the person it was on. */
const PEOPLE_PERSON_PLACE = "people/person";


export function PeopleCore({ hero, scope }: CoreProps) {
  const [readiness, setReadiness] = useState<Readiness>({ readiness: "unconfigured" });
  const [loading, setLoading] = useState(true);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<RelationshipDetail | null>(null);
  const [newName, setNewName] = useState("");
  const [newKind, setNewKind] = useState<RelationshipKind>("direct_report");
  // PHILO-17: a name already on the roster warns once; Add again adds it.
  const [duplicateWarned, setDuplicateWarned] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const requestedScope = scope?.startsWith("people:") ? scope.slice("people:".length) : null;
  // HS-200-14 (AC4): `people:project:<id>` scopes the roster to the people
  // linked to that Project; `people:<relationship>[:<lens>]` stays as it was.
  const requestedProjectId = requestedScope?.startsWith("project:") ? requestedScope.slice("project:".length) : null;
  const relationshipScope = requestedProjectId ? null : requestedScope;
  const requestedRelationshipId = relationshipScope?.includes(":") ? relationshipScope.split(":")[0] : relationshipScope;
  const requestedLens = relationshipScope?.includes(":") ? relationshipScope.split(":")[1] as Lens : null;
  const [projectFilter, setProjectFilter] = useState<string | null>(requestedProjectId);
  // PHILO-13-06 (Astra's pass): each explicit open is a request; a repeat
  // open with the same scope re-applies its lens (Prep → Now → Prep again).
  const [lensRequest, setLensRequest] = useState<{ lens: Lens; seq: number } | null>(null);
  useEffect(() => {
    const onOpen = (event: Event) => {
      const request = (event as CustomEvent<PersonOpenRequest>).detail;
      if (!request?.lens) return;
      setLensRequest({ lens: request.lens as Lens, seq: request.seq });
    };
    window.addEventListener(PERSON_OPEN_EVENT, onOpen);
    return () => window.removeEventListener(PERSON_OPEN_EVENT, onOpen);
  }, []);

  // PHILO-17 ALIVE: one way to add. Add person opens the add row at the
  // top of the roster (it is open on an empty roster).
  const [adding, setAdding] = useState(false);
  // PHILO-17 ALIVE: what each row says (next 1:1, owed both ways), read
  // from each person's own record. A failed read leaves the row plain.
  const [rowFacts, setRowFacts] = useState<Record<string, RowFacts>>({});
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
      setError(plainFailure("PEOPLE DID NOT LOAD", cause));
    } finally { setLoading(false); }
  }, [clearProtected]);
  useEffect(() => { void load(); }, [load]);
  // A write in another window (a commitment, a 1:1, an agent's write) shows
  // here with no reload. A quiet re-read: no loading state, the person stays
  // open, and the last read stays when it fails or the store is not ready.
  const followed = useRef({ ready: false, selectedId: null as string | null });
  const quietReads = useRef(0);
  followed.current = { ready: stateOf(readiness) === "ready", selectedId };
  useOnDeskChanged(() => {
    if (!followed.current.ready) return;
    // Only the newest quiet re-read lands; an older one that answers late is dropped.
    const order = ++quietReads.current;
    const newest = () => order === quietReads.current;
    void (async () => {
      try {
        const list = await apiFetch<{ relationships?: Relationship[] }>("/api/people/relationships");
        if (!newest()) return;
        setRelationships(list.relationships ?? []);
        const id = followed.current.selectedId;
        if (!id) return;
        const [relationship, sessions] = await Promise.all([
          apiFetch<{ relationship: Relationship }>(`/api/people/relationships/${encodeURIComponent(id)}`),
          apiFetch<{ one_on_ones: Session[] }>(`/api/people/relationships/${encodeURIComponent(id)}/one-on-ones`),
        ]);
        if (newest() && followed.current.selectedId === id) setDetail({ ...relationship.relationship, sessions: sessions.one_on_ones });
      } catch { /* the last read stays */ }
    })();
  });
  // HS-200-14 (AC4): the way back to the task. When this window was
  // opened from a Room verb (`rememberTaskFocus` on the way in), closing
  // it announces the return: the Room re-reads and focus lands back on
  // the verb the owner left -- and only then (the do-not-steal rule).
  useEffect(() => () => { if (taskFocusPending()) announceTaskReturn(); }, []);

  // The row facts are the roster's: read while no person is open (a
  // person's own read is the window's; the two never share a request).
  // Astra (PHILO-17 refit): ONE coalesced load: one in flight at a time,
  // run again only when the list of people changes (a bounded hub read
  // for these counts replaces this when the shared lane lands it).
  const personOpen = Boolean(selectedId || requestedRelationshipId);
  const rosterKey = relationships.map((row) => row.id).join("|");
  const factsRun = useRef<{ inFlight: boolean; doneKey: string | null; wantKey: string | null }>({ inFlight: false, doneKey: null, wantKey: null });
  const loadFacts = useCallback((key: string) => {
    const run = factsRun.current;
    run.wantKey = key;
    if (run.inFlight || run.doneKey === key) return;
    if (!key) { run.doneKey = key; setRowFacts({}); return; }
    run.inFlight = true;
    const ids = key.split("|");
    void Promise.all(ids.map(async (id) => {
      try {
        const read = await apiFetch<{ relationship: RelationshipDetail }>(`/api/people/relationships/${encodeURIComponent(id)}`);
        return [id, rowFactsOf(read.relationship)] as const;
      } catch {
        return null;
      }
    })).then((pairs) => {
      run.inFlight = false;
      run.doneKey = key;
      setRowFacts(Object.fromEntries(pairs.filter((pair): pair is readonly [string, RowFacts] => Boolean(pair))));
      if (run.wantKey !== null && run.wantKey !== key) loadFacts(run.wantKey);
    });
  }, []);
  useEffect(() => {
    if (personOpen) return;
    loadFacts(rosterKey);
  }, [rosterKey, personOpen, loadFacts]);
  const planOneOnOne = (id: string) => {
    setLensRequest((current) => ({ lens: "one-on-ones", seq: current ? current.seq + 1 : 1 }));
    void select(id);
  };

  const unavailable = stateOf(readiness) !== "ready";
  const openSettings = () => openSurfaceOr("configure-settings", "/settings", "people-security");
  const recover = () => {
    if (stateOf(readiness) === "locked" || stateOf(readiness) === "unavailable") { void load(); return; }
    if (stateOf(readiness) !== "unconfigured") { openSettings(); return; }
    void apiFetch("/api/people/setup", { method: "POST", json: {} })
      .then(() => load())
      .catch((cause) => protectedFailure(cause));
  };
  const select = async (id: string) => {
    // PHILO-13-04 fix round (Astra counsel P2): a standing failure leaves only
    // when this read lands; it is never cleared before the person is back.
    setSelectedId(id); setDetail(null);
    // PHILO-13-07 (B2): the person is this window's place; it returns after
    // a reload and a close.
    keepPlace(PEOPLE_PERSON_PLACE, id);
    try {
      const [relationship, sessions] = await Promise.all([
        apiFetch<{ relationship: Relationship }>(`/api/people/relationships/${encodeURIComponent(id)}`),
        apiFetch<{ one_on_ones: Session[] }>(`/api/people/relationships/${encodeURIComponent(id)}/one-on-ones`),
      ]);
      setDetail({ ...relationship.relationship, sessions: sessions.one_on_ones });
      setError("");
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
  // PHILO-13-07 (B2): with no person in the open request, the window comes
  // back on the person it was on (an explicit scope always wins).
  useEffect(() => {
    if (stateOf(readiness) !== "ready" || requestedRelationshipId || requestedProjectId || selectedId) return;
    const kept = keptPlace(PEOPLE_PERSON_PLACE);
    if (kept && relationships.some((relationship) => relationship.id === kept)) void select(kept);
  }, [readiness, relationships]); // once per roster read: Back clears the place
  const duplicate = sameName(relationships, newName);
  const duplicateShown = duplicate && duplicateWarned === nameKey(newName) ? duplicate : null;
  // PHILO-17: Add stays on the list with the cursor in Name, so three
  // reports are Name, Add three times. A quiet roster re-read (no loading
  // state) keeps the input on screen.
  const createRelationship = async () => {
    const display_name = newName.trim(); if (!display_name) return;
    if (duplicate && duplicateWarned !== nameKey(display_name)) { setDuplicateWarned(nameKey(display_name)); return; }
    setBusy(true); setError("");
    try {
      await apiFetch<{ relationship: Relationship }>("/api/people/relationships", { method: "POST", json: { display_name, relationship_kind: newKind } });
      setNewName(""); setDuplicateWarned("");
      const list = await apiFetch<{ relationships?: Relationship[] }>("/api/people/relationships");
      setRelationships(list.relationships ?? []);
    } catch (cause) { protectedFailure(cause); } finally {
      setBusy(false);
      document.getElementById("people-new-relationship")?.focus();
    }
  };
  function protectedFailure(cause: unknown) {
    if (isStoreOutage(cause) && (selectedId || relationships.length)) {
      setError(plainFailure("PEOPLE STORE", cause));
      return;
    }
    if (!isProtectedFailure(cause)) {
      setError(plainFailure("NOT DONE", cause));
      return;
    }
    clearProtected();
    setReadiness(readinessForError(cause));
    setError(plainFailure("PEOPLE STORE", cause));
  }
  const selected = detail ?? relationships.find((row) => row.id === selectedId) ?? null;
  // PHILO-17: the head verb names what it does; on a person's page it is gone.
  const addOpen = adding || !relationships.length;
  const verbs = unavailable || selected || addOpen ? null : <Button dense variant="primary" onClick={() => { setAdding(true); window.setTimeout(() => document.getElementById("people-new-relationship")?.focus(), 0); }}>Add person</Button>;

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
  // PHILO-13-04 (A3): the failure is ONE row in the window's status bar, which
  // stays on screen while he is down in a lens; the person and any unsent
  // draft stay under it (J3-06). Try again re-reads the person (or the
  // roster); the row leaves only when that read lands.
  const failureRow = error ? (
    <span className="people-failure" role="alert" data-testid="people-failure">
      <span className="people-failure-label">{error}</span>
      <Button dense variant="ghost" onClick={() => void (selectedId ? select(selectedId) : load())}>Try again</Button>
    </span>
  ) : null;
  // PHILO-17 ALIVE: the app tile and the one fact of the roster.
  const factList = Object.values(rowFacts);
  const owed = factList.reduce((sum, fact) => sum + fact.youOwe, 0);
  const owedToYou = factList.reduce((sum, fact) => sum + fact.owesYou, 0);
  const weekEnd = Date.now() + 7 * 86_400_000;
  const oneOnOnesThisWeek = factList.filter((fact) => {
    const at = fact.next ? wireDate(fact.next)?.getTime() ?? NaN : NaN;
    return Number.isFinite(at) && at <= weekEnd;
  }).length;
  const peopleHead = selected || !relationships.length ? null : (
    <div className="people-top" data-testid="people-headline">
      <AppTile sprite="people-ledger" hue={268} />
      <span className="surface-display">
        {relationships.length === 1 ? "1 person" : `${relationships.length} people`}
      </span>
      {/* The owed counts live once, in the This week strip under the roster. */}
      <span className="people-head-sp" />
      {verbs}
    </div>
  );
  return <div className="people-surface">
    {/* PHILO-17 REFIT: Add person sits in the roster's own head row (no
        empty band above it); a person's page has no head verb. */}
    {renderHeroSlot(hero, peopleHead ? null : verbs, failureRow)}
    {peopleHead}
    <SurfaceSplit
      detailOpen={Boolean(selected)}
      main={<Roster rowFacts={rowFacts} addOpen={addOpen} onCloseAdd={relationships.length ? () => setAdding(false) : undefined} onPlan={planOneOnOne} relationships={relationships} selectedId={selectedId} newName={newName} setNewName={setNewName} newKind={newKind} setNewKind={setNewKind} busy={busy} duplicateOf={duplicateShown?.display_name ?? null} onCreate={() => void createRelationship()} onSelect={(id) => void select(id)} projectFilter={projectFilter} onClearProjectFilter={() => setProjectFilter(null)} />}
      detail={selected ? <RelationshipPane relationship={selected} initialLens={requestedLens} lensRequest={lensRequest} onRefresh={() => void select(selected.id)} onProtectedFailure={protectedFailure} onArchived={() => { clearProtected(); void load(); }} onBack={() => { setSelectedId(null); setDetail(null); keepPlace(PEOPLE_PERSON_PLACE, ""); }} /> : undefined}
    />
    {selected ? null : <FigureStrip caption="This week" data-testid="people-week" figures={[
      { key: "one-on-ones", value: oneOnOnesThisWeek, label: oneOnOnesThisWeek === 1 ? "1:1 planned" : "1:1s planned", tone: "info" },
      { key: "you-owe", value: owed, label: "you owe", tone: "warn" },
      { key: "owed-to-you", value: owedToYou, label: "owed to you", tone: "ok" },
    ]} />}
    <SurfaceFooter egress={<span className="people-lock" title="Encrypted · Local storage · Notes only" data-testid="people-lock"><span aria-hidden="true">⚿</span> Encrypted</span>} />
  </div>;
}

function nameKey(name: string): string {
  return name.trim().replace(/\s+/g, " ").toLowerCase();
}

/** PHILO-17: the person already on the roster with this name, if any. */
function sameName(relationships: Relationship[], name: string): Relationship | null {
  const key = nameKey(name);
  return key ? relationships.find((row) => nameKey(row.display_name) === key) ?? null : null;
}

function Roster({ rowFacts = {}, addOpen = true, onCloseAdd, onPlan, relationships, selectedId, newName, setNewName, newKind, setNewKind, busy, duplicateOf = null, onCreate, onSelect, projectFilter = null, onClearProjectFilter }: {
  /** PHILO-17 ALIVE: what each row says, by relationship id. */
  rowFacts?: Record<string, RowFacts>;
  /** PHILO-17 ALIVE: the add row is open (Add person, or an empty roster). */
  addOpen?: boolean; onCloseAdd?(): void; onPlan?(id: string): void;
  relationships: Relationship[]; selectedId: string | null; newName: string; setNewName(value: string): void; newKind: RelationshipKind; setNewKind(value: RelationshipKind): void; busy: boolean; onCreate(): void; onSelect(id: string): void;
  /** PHILO-17: the name already on the roster; the next Add adds it again. */
  duplicateOf?: string | null;
  /** HS-200-14: the Project the roster is scoped to (`people:project:<id>`), or null for everyone. */
  projectFilter?: string | null; onClearProjectFilter?(): void;
}) {
  const scoped = useMemo(
    () => (projectFilter ? relationships.filter((r) => (r.project_refs ?? []).includes(projectFilter)) : relationships),
    [relationships, projectFilter],
  );
  const ordered = useMemo(() => [...scoped].sort((a, b) => (Number(b.manager_commitment_count ?? 0) - Number(a.manager_commitment_count ?? 0)) || a.display_name.localeCompare(b.display_name)), [scoped]);
  const scopedOut = projectFilter ? relationships.length - scoped.length : 0;
  return <SurfaceSection
    label={projectFilter ? countToken(ordered.length, "ON THIS PROJECT", "ON THIS PROJECT") ?? "THIS PROJECT" : "Relationships"}
    actions={projectFilter && scopedOut > 0 ? <Button dense variant="ghost" aria-label="Everyone: clear the Project scope" onClick={onClearProjectFilter} data-testid="people-roster-everyone">{countToken(scopedOut, "MORE", "MORE")} · Everyone</Button> : undefined}
  >
    {addOpen ? <div className="people-new" data-testid="people-add-row">
      <StringGadget label="Add person" value={newName} onChange={setNewName} placeholder="Name" inputProps={{ id: "people-new-relationship" }} onKeyDown={(event) => { if (event.key === "Enter") onCreate(); if (event.key === "Escape") onCloseAdd?.(); }} />
      <span className="people-role-pick" role="group" aria-label="Relationship">
        {ROLE_CHOICES.map((choice) => <Button key={choice.value} dense variant="ghost" className="people-role-choice" data-kind={choice.value} aria-pressed={newKind === choice.value} onClick={() => setNewKind(choice.value)}>{choice.label}</Button>)}
      </span>
      <Button dense variant="primary" disabled={!newName.trim() || busy} loading={busy} onClick={onCreate}>{duplicateOf ? "Add again" : "Add"}</Button>
      {onCloseAdd ? <Button dense variant="ghost" onClick={onCloseAdd}>Done</Button> : null}
    </div> : null}
    {duplicateOf ? <span className="surface-token people-duplicate" role="status" data-testid="people-duplicate">{duplicateOf} · Already here</span> : null}
    {!ordered.length ? <div className="people-empty-roster" data-testid="people-empty-roster">{projectFilter ? <span className="surface-token" data-testid="people-roster-none-linked">NO ONE LINKED YET</span> : <p className="people-empty-lead">Add a person to start</p>}</div> : <SurfaceRows>{ordered.map((relationship) => <PersonRow key={relationship.id} relationship={relationship} fact={rowFacts[relationship.id]} selected={selectedId === relationship.id} onSelect={onSelect} onPlan={onPlan} />)}</SurfaceRows>}
  </SurfaceSection>;
}

/** HS-172-05: concern focus for Now wing opened from Prep summary rows. */
type NowConcern = "prs" | "assignments" | "commitments" | null;

/** PHILO-17 (2b) — a person's own window (`pullout:people:<id>`): THAT
 *  person, on the RelationshipPane, not the People roster. A lens a door
 *  asks for comes in as a request (`PERSON_OPEN_EVENT`); a store that is
 *  not ready says so and offers its one verb, as the People window does. */
export function PersonWindowBody({ relationshipId, onClose }: { relationshipId: string; onClose?(): void }) {
  // The lens a door asked for before this window could hear it, once.
  const [initialLens] = useState<Lens | null>(() => peekPersonLens(relationshipId));
  useEffect(() => { takePersonLens(relationshipId); }, [relationshipId]);
  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const [detail, setDetail] = useState<RelationshipDetail | null>(null);
  const [error, setError] = useState("");
  const [lensRequest, setLensRequest] = useState<{ lens: Lens; seq: number } | null>(null);
  useWindowTitle(detail?.display_name ?? null, [detail?.display_name]);
  useEffect(() => {
    const onOpen = (event: Event) => {
      const request = (event as CustomEvent<PersonOpenRequest>).detail;
      if (request?.relationshipId !== relationshipId || !request.lens) return;
      takePersonLens(relationshipId);
      setLensRequest({ lens: request.lens as Lens, seq: request.seq });
    };
    window.addEventListener(PERSON_OPEN_EVENT, onOpen);
    return () => window.removeEventListener(PERSON_OPEN_EVENT, onOpen);
  }, [relationshipId]);
  const read = useCallback(async () => {
    try {
      const next = await apiFetch<Readiness>("/api/people/readiness");
      setReadiness(next);
      if (stateOf(next) !== "ready") { setDetail(null); return; }
      const [relationship, sessions] = await Promise.all([
        apiFetch<{ relationship: Relationship }>(`/api/people/relationships/${encodeURIComponent(relationshipId)}`),
        apiFetch<{ one_on_ones: Session[] }>(`/api/people/relationships/${encodeURIComponent(relationshipId)}/one-on-ones`),
      ]);
      setDetail({ ...relationship.relationship, sessions: sessions.one_on_ones });
      setError("");
    } catch (cause) {
      if (isProtectedFailure(cause) && !isStoreOutage(cause)) { setDetail(null); setReadiness(readinessForError(cause)); }
      setError(plainFailure(detail ? "PEOPLE STORE" : "PERSON DID NOT LOAD", cause));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [relationshipId]);
  useEffect(() => { void read(); }, [read]);
  // A write in another window shows here with no reload.
  useOnDeskChanged(() => { if (readiness && stateOf(readiness) === "ready") void read(); });
  const protectedFailure = (cause: unknown) => {
    if (isProtectedFailure(cause) && !isStoreOutage(cause)) { setDetail(null); setReadiness(readinessForError(cause)); }
    setError(plainFailure("NOT DONE", cause));
  };
  if (!readiness && !error) return <SurfaceState loading />;
  if (readiness && stateOf(readiness) !== "ready") {
    const face = readinessFace(stateOf(readiness));
    return <div className="people-joy-state" data-testid="people-joy-state">
      <div className="people-joy-lead">
        <Button variant="primary" onClick={() => openSurfaceOr("open-people", "/")} data-testid="people-joy-action">{face.action}</Button>
        <span className="people-joy-line">{face.label}</span>
      </div>
    </div>;
  }
  return <div className="people-surface" data-testid="person-window">
    {error ? (
      <span className="people-failure" role="alert" data-testid="people-failure">
        <span className="people-failure-label">{error}</span>
        <Button dense variant="ghost" onClick={() => void read()}>Try again</Button>
      </span>
    ) : null}
    {detail ? (
      <RelationshipPane relationship={detail} initialLens={initialLens} lensRequest={lensRequest}
        onRefresh={() => void read()} onProtectedFailure={protectedFailure}
        onArchived={() => { if (onClose) onClose(); else { setDetail(null); void read(); } }} />
    ) : null}
  </div>;
}

/** PHILO-17 REFIT: the person's tabs. Prep is the lead (the next 1:1, what
 *  to raise, owed both ways); Context, History and Info stay behind it.
 *  The old lenses `now` and `one-on-ones` land on Prep. */
type PaneLens = "prep" | "context" | "history" | "info";
function paneLens(lens: Lens | string | null | undefined): PaneLens | null {
  if (!lens) return null;
  if (lens === "context" || lens === "history" || lens === "info") return lens;
  return "prep";
}
const PANE_TABS: ReadonlyArray<readonly [PaneLens, string]> = [["prep", "Prep"], ["context", "Context"], ["history", "History"], ["info", "Info"]];
const PERSON_SPRITE = `${import.meta.env.BASE_URL || "/_built/"}desk/sprites/32/person.png`;

function openCount(items?: Array<{ state?: string }> | null): number {
  return (items ?? []).filter((item) => (item.state ?? "open") === "open").length;
}

/** PHILO-17 (2b): exported; a person's own window (`pullout:people:<id>`)
 *  hosts it. There the window's close is the way back, so no Back. */
export function RelationshipPane({ relationship, initialLens, lensRequest = null, onRefresh, onProtectedFailure, onArchived, onBack }: { relationship: RelationshipDetail; initialLens?: Lens | null; lensRequest?: { lens: Lens; seq: number } | null; onRefresh(): void; onProtectedFailure(cause: unknown): void; onArchived(): void; onBack?(): void }) {
  // PHILO-13-07 (B2): the tab is part of the place, kept per person.
  const lensPlace = `people/lens/${relationship.id}`;
  const [lens, setLensState] = useState<PaneLens>(() => paneLens(initialLens) ?? paneLens(keptPlace(lensPlace)) ?? "prep");
  const setLens = useCallback((next: PaneLens) => {
    setLensState(next);
    keepPlace(lensPlace, next === "prep" ? "" : next);
  }, [lensPlace]);
  // PHILO-13-06 (B1): a row that opens this person on a lens moves the open window to it.
  useEffect(() => { const next = paneLens(initialLens); if (next) setLens(next); }, [initialLens, setLens]);
  useEffect(() => { if (lensRequest) setLens(paneLens(lensRequest.lens) ?? "prep"); }, [lensRequest, setLens]);
  // The calendar picker (Context) reads the Door's upcoming events.
  const [upcomingEvents, setUpcomingEvents] = useState<UpcomingEvent[]>([]);
  const wantsCalendar = lens === "context";
  useEffect(() => {
    if (!wantsCalendar) return;
    let live = true;
    void apiFetch<{ upcoming?: UpcomingEvent[] }>("/api/door")
      .then((door) => {
        if (!live) return;
        setUpcomingEvents((door.upcoming ?? []).filter(
          (item: Record<string, unknown>) => item.source === "calendar_event" && item.uid,
        ) as UpcomingEvent[]);
      })
      .catch(() => { if (live) setUpcomingEvents([]); });
    return () => { live = false; };
  }, [relationship.id, wantsCalendar]);
  const youOwe = openCount(relationship.commitments);
  const owesYou = openCount(relationship.owed_to_you);
  return <div className="people-detail person-page">
    <header className="people-detail-head" data-testid="people-detail-head">
      {onBack ? <Button dense variant="ghost" onClick={onBack}>Back</Button> : null}
      <Avatar name={relationship.display_name} size="md" />
      <span className="people-who">
        <h2 className="people-name" data-testid="prep-display-name">{relationship.display_name}</h2>
        <span className="people-who-meta">
          <span className="people-role-chip" data-kind={relationship.relationship_kind ?? undefined}>{relationshipLabel(relationship.relationship_kind)}</span>
          {relationship.role_context ? <span>{relationship.role_context}</span> : null}
        </span>
      </span>
      <span className="people-head-sp" />
      {youOwe || owesYou ? <span className="people-strip" data-testid="people-owed-strip">
        {youOwe ? <span data-tone="warn"><b>{youOwe}</b> you owe</span> : null}
        {owesYou ? <span data-tone="ok"><b>{owesYou}</b> owed to you</span> : null}
      </span> : null}
    </header>
    <div className="people-lenses" role="tablist" aria-label={`${relationship.display_name} lenses`}>
      {PANE_TABS.map(([id, label]) => <Button key={id} dense variant="ghost" role="tab" aria-selected={lens === id} onClick={() => setLens(id)}>{label}</Button>)}
    </div>
    {lens === "prep" ? <PrepPane relationship={relationship} onRefresh={onRefresh} onProtectedFailure={onProtectedFailure} onPickCalendar={() => setLens("context")} /> : null}
    {lens === "context" ? <ContextLens relationship={relationship} onRefresh={onRefresh} onProtectedFailure={onProtectedFailure} upcomingEvents={upcomingEvents} /> : null}
    {lens === "history" ? <HistoryLens relationship={relationship} /> : null}
    {lens === "info" ? <InfoLens relationship={relationship} onArchived={onArchived} onProtectedFailure={onProtectedFailure} /> : null}
  </div>;
}

/** `in 50 min`, `in 2 h 05 min`, `now`; empty past a day. */
function untilWords(isoDate: string, now: number): string {
  const at = wireDate(isoDate)?.getTime();
  if (at === undefined || !Number.isFinite(at)) return "";
  const minutes = Math.ceil((at - now) / 60_000);
  if (minutes <= 0) return "now";
  if (minutes < 60) return `in ${minutes} min`;
  if (minutes < 24 * 60) return `in ${Math.floor(minutes / 60)} h ${String(minutes % 60).padStart(2, "0")} min`;
  return "";
}

function isOverdue(due?: string | null): boolean {
  if (!due) return false;
  const at = wireDate(due);
  if (!at) return false;
  const today = new Date(); today.setHours(0, 0, 0, 0);
  return at.getTime() < today.getTime();
}

/** PHILO-17 REFIT: one row of a plate: the words, one pill, one verb. */
function PlateRow({ title, onTitle, meta, verb, testId }: { title: string; onTitle?: () => void; meta?: ReactNode; verb?: ReactNode; testId?: string }) {
  return <li className="people-plate-row" data-testid={testId}>
    <span className="people-plate-text">
      {onTitle ? <Button variant="chrome" className="people-plate-title" onClick={onTitle}>{title}</Button> : <span className="people-plate-title">{title}</span>}
      {meta ? <span className="people-plate-meta">{meta}</span> : null}
    </span>
    {verb}
  </li>;
}

function DuePill({ due }: { due?: string | null }) {
  if (!due) return null;
  return isOverdue(due)
    ? <span className="people-pill" data-tone="danger">Overdue · BY {shortDay(due)}</span>
    : <span className="people-pill">BY {shortDay(due)}</span>;
}

/** HS-172-05: the rows behind a Prep concern (PRs, assignments, overdue). */
function ConcernDetail({ concern, brief }: { concern: Exclude<NowConcern, null>; brief: OneOnOneBrief }) {
  const ws = brief.watch_summary;
  if (concern === "prs" && ws?.prs_waiting?.length) return <div data-testid="now-prs-detail" className="people-concern">
    <SurfaceLedger count={`PRS WAITING ${ws.prs_waiting.length}`} cols="room">
      {ws.prs_waiting.map((pr) => <SurfaceLedgerRow key={`pr-${pr.pr_number}`} wrap expands={false}
        primary={<span className="surface-primary">{`#${pr.pr_number} · ${pr.title}`}</span>}
        cells={<span className="people-now-caption"><span className={pr.days_waiting >= 3 ? "people-now-caption-warning" : ""}>{pr.days_waiting} {pr.days_waiting === 1 ? "DAY" : "DAYS"}</span>{pr.repo ? <> · <span>{pr.repo.toUpperCase()}</span></> : null}</span>}
        trailing={pr.url ? <Button dense variant="ghost" onClick={() => window.open(pr.url, "_blank", "noopener")}>Open</Button> : undefined} />)}
    </SurfaceLedger>
  </div>;
  if (concern === "assignments" && ws?.open_assignments?.length) return <div data-testid="now-assignments-detail" className="people-concern">
    <SurfaceLedger count={`ASSIGNMENTS OPEN ${ws.open_assignments.length}`} cols="room">
      {ws.open_assignments.map((a) => <SurfaceLedgerRow key={a.key} wrap expands={false}
        primary={<span className="surface-primary">{`${a.key} · ${a.summary}`}</span>}
        cells={<span className="people-now-caption"><span>{a.status.toUpperCase()}</span>{a.overdue ? <> · <span className="people-now-caption-warning">OVERDUE</span></> : null}</span>}
        trailing={a.url ? <Button dense variant="ghost" onClick={() => window.open(a.url, "_blank", "noopener")}>Open</Button> : undefined} />)}
    </SurfaceLedger>
  </div>;
  return null;
}

/** PHILO-17 REFIT — Prep, the lead: the next 1:1 as the focus plate (when,
 *  what to raise, add to the agenda), then two plates: what he owes and
 *  what is owed to him, each with its add row. Every fact is the person's
 *  record or the hub's 1:1 brief (`/brief`, read-only). */
function PrepPane({ relationship, onRefresh, onProtectedFailure, onPickCalendar }: { relationship: RelationshipDetail; onRefresh(): void; onProtectedFailure(cause: unknown): void; onPickCalendar(): void }) {
  const [brief, setBrief] = useState<OneOnOneBrief | null>(null);
  const [failure, setFailure] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [concern, setConcern] = useState<NowConcern>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [selectedCommitment, setSelectedCommitment] = useState<Commitment | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const [preparedAt] = useState(() => new Date().toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", hour12: false }));
  // The person's record is re-read after each write; the brief follows it.
  useEffect(() => {
    let live = true;
    void apiFetch<{ brief: OneOnOneBrief }>(`/api/people/relationships/${encodeURIComponent(relationship.id)}/brief`)
      .then((result) => { if (live) { setBrief(result.brief); setFailure(""); } })
      .catch((cause) => {
        if (!live) return;
        if (isProtectedFailure(cause) && !isStoreOutage(cause)) { onProtectedFailure(cause); return; }
        setFailure(plainFailure("PREP DID NOT LOAD", cause));
      });
    return () => { live = false; };
  }, [relationship, attempt]); // eslint-disable-line react-hooks/exhaustive-deps
  // The countdown ticks; the words change in a fixed box.
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 30_000);
    return () => window.clearInterval(timer);
  }, []);
  const [agendaDraft, setAgendaDraft, forgetAgenda] = useDeskDraft(`people/1on1/${relationship.id}`);
  const [oweDraft, setOweDraft, forgetOwe] = useDeskDraft(`people/request/${relationship.id}`);
  const [owedDraft, setOwedDraft, forgetOwed] = useDeskDraft(`people/owed/${relationship.id}`);

  if (!brief && !failure) return <SurfaceState loading />;

  const base = `/api/people/relationships/${encodeURIComponent(relationship.id)}`;
  const run = async (key: string, work: () => Promise<unknown>, after?: () => void) => {
    setBusy(key);
    try { await work(); after?.(); onRefresh(); } catch (cause) { onProtectedFailure(cause); } finally { setBusy(null); }
  };
  const addAgenda = () => {
    const body = agendaDraft.trim(); if (!body) return;
    void run("agenda", async () => {
      const session = relationship.sessions?.[0] ?? (await apiFetch<{ one_on_one: Session }>(`${base}/one-on-ones`, { method: "POST", json: { visibility: "shared_intent" } })).one_on_one;
      await apiFetch(`/api/people/one-on-ones/${encodeURIComponent(session.id)}/agenda`, { method: "POST", json: { body, visibility: "shared_intent", state: "open", source: { kind: "manual" } } });
    }, forgetAgenda);
  };
  // What he owes: the hub's own path (a request he accepts becomes his commitment).
  const addOwe = () => {
    const body = oweDraft.trim(); if (!body) return;
    void run("owe", async () => {
      const made = await apiFetch<{ request: { id: string } }>(`${base}/requests`, { method: "POST", json: { body, visibility: "shared_intent", source: { kind: "manual" } } });
      await apiFetch(`/api/people/requests/${encodeURIComponent(made.request.id)}/accept`, { method: "POST", json: {} });
    }, forgetOwe);
  };
  const addOwed = () => {
    const body = owedDraft.trim(); if (!body) return;
    void run("owed", () => apiFetch(`${base}/owed`, { method: "POST", json: { body, visibility: "shared_intent" } }), forgetOwed);
  };
  const done = (id: string) => void run(`done:${id}`, () => apiFetch(`/api/people/commitments/${encodeURIComponent(id)}/transition`, { method: "POST", json: { verb: "done" } }));
  const accept = (id: string) => void run(`accept:${id}`, () => apiFetch(`/api/people/requests/${encodeURIComponent(id)}/accept`, { method: "POST", json: {} }));

  const prep = brief ? composePeoplePrep(brief) : null;
  const nextEvent = prep?.nextOneOnOne ?? null;
  const nextAt = relationship.next_one_on_one ?? nextEvent?.starts_at ?? null;
  const suggestions = !nextAt && prep ? prep.calendarLinkSuggestions : [];
  const lead: "link" | "agenda" = suggestions.length ? "link" : "agenda";
  const nextTitle = nextEvent?.title || (relationship.calendar_links ?? [])[0]?.label || "1:1";
  const until = nextAt ? untilWords(nextAt, now) : "";

  const ws = brief?.watch_summary;
  const prCount = ws?.prs_waiting?.length ?? 0;
  const assignCount = ws?.open_assignments?.length ?? 0;
  const youOweRows = (relationship.commitments ?? []).filter((item) => (item.state ?? "open") === "open");
  // The brief's open commitments name what is overdue (the 1:1 brief's read).
  const overdue = (brief?.open_commitments ?? []).filter((item) => isOverdue(item.due));
  const lm = brief?.last_meeting;
  const displayName = brief?.display_name ?? relationship.display_name;
  const toggle = (next: Exclude<NowConcern, null>) => setConcern((current) => (current === next ? null : next));
  const concernRows: ReactNode[] = [];
  if (brief && prCount) concernRows.push(<li key="prs" className="people-raise-row" data-testid="prep-prs-row">
    <span className="people-pill" data-tone={ws?.oldest_waiting_days && ws.oldest_waiting_days >= 3 ? "warn" : "info"} data-testid="prep-prs-label">{prsSummaryLabel(prCount, displayName)}</span>
    <span className="people-raise-tokens">
      {ws?.oldest_waiting_days ? <span className="people-prep-token" data-warning={ws.oldest_waiting_days >= 3 || undefined} data-testid="prep-prs-days">{ws.oldest_waiting_days}+ DAYS</span> : null}
      <span className="people-prep-token" data-testid="prep-prs-numbers">{capTokens((ws?.prs_waiting ?? []).map((pr) => `#${pr.pr_number}`))}</span>
    </span>
    <Button dense variant="ghost" onClick={() => toggle("prs")} aria-expanded={concern === "prs"} data-testid="prep-prs-open">{concern === "prs" ? "Hide" : "Show"}</Button>
  </li>);
  if (brief && assignCount) concernRows.push(<li key="assign" className="people-raise-row" data-testid="prep-assignments-row">
    <span className="people-pill" data-tone={(ws?.open_assignments ?? []).some((a) => a.overdue) ? "warn" : "info"} data-testid="prep-assignments-label">{assignCount} {assignCount === 1 ? "ASSIGNMENT" : "ASSIGNMENTS"} OPEN</span>
    <span className="people-raise-tokens">
      <span className="people-prep-token" data-testid="prep-assignments-keys">{capTokens((ws?.open_assignments ?? []).map((a) => a.key).filter(Boolean))}</span>
      {(ws?.open_assignments ?? []).some((a) => a.overdue) ? <span className="people-prep-token" data-warning="true" data-testid="prep-assignments-overdue">OVERDUE</span> : null}
    </span>
    <Button dense variant="ghost" onClick={() => toggle("assignments")} aria-expanded={concern === "assignments"} data-testid="prep-assignments-open">{concern === "assignments" ? "Hide" : "Show"}</Button>
  </li>);
  if (overdue.length) concernRows.push(<li key="overdue" className="people-raise-row" data-testid="prep-commitments-row">
    <span className="people-pill" data-tone="danger" data-testid="prep-commitments-label">{overdue.length} {overdue.length === 1 ? "COMMITMENT" : "COMMITMENTS"} OVERDUE</span>
    <span className="people-raise-tokens"><span className="people-prep-token">{overdue[0].body.length > 30 ? overdue[0].body.slice(0, 30) : overdue[0].body}</span></span>
  </li>);
  if (lm && lm.item_count > 0) concernRows.push(<li key="last" className="people-raise-row" data-testid="prep-meeting-row">
    <span className="people-pill">LAST MEETING</span>
    <span className="people-raise-tokens">
      <span className="people-prep-token" data-testid="prep-meeting-items">{lm.item_count} {lm.item_count === 1 ? "ITEM" : "ITEMS"}</span>
      {lm.open_count > 0 ? <span className="people-prep-token" data-testid="prep-meeting-open-count">{lm.open_count} OPEN</span> : null}
    </span>
    <Button dense variant="ghost" onClick={() => openSourceRef(`meeting:${lm.meeting_id}`)} data-testid="prep-meeting-open">Open meeting</Button>
  </li>);
  const agenda = prep?.agenda ?? [];
  const asked = (relationship.requests ?? []).filter((item) => item.state === "requested");
  const owedRows = (relationship.owed_to_you ?? []).filter((item) => (item.state ?? "open") === "open");
  const actions = prep?.openMeetingActions ?? [];

  return <div data-testid="people-prep-lens" className="people-prep">
    {failure ? <span className="people-failure" role="alert" data-testid="people-next-failure">
      <span className="people-failure-label">{failure}</span>
      <Button dense variant="ghost" onClick={() => setAttempt((n) => n + 1)}>Try again</Button>
    </span> : null}

    <section className="people-next" aria-label="Next 1:1" data-testid="people-next-plate">
      <header className="people-next-bar" data-testid={nextAt ? "people-next-1on1" : undefined}>
        <span className="people-next-label">NEXT 1:1</span>
        {nextAt ? <span className="people-next-sep" aria-hidden="true"> · </span> : null}
        <span className="people-next-when">{nextAt ? [shortWhen(nextAt), until].filter(Boolean).join(" · ") : brief ? "NOT PLANNED" : ""}</span>
      </header>
      <div className="people-next-body">
        {nextAt ? <div className="people-next-event">
          <span className="people-next-sprite" aria-hidden="true"><img src={PERSON_SPRITE} alt="" draggable={false} /></span>
          <span className="people-next-text">
            <span className="people-next-title">{nextTitle}</span>
            {nextEvent?.source_label ? <span className="people-plate-meta"><span>{nextEvent.source_label}</span></span> : null}
          </span>
        </div> : suggestions.length && prep ? <LinkSuggestions relationship={relationship} prep={prep} onLinked={onRefresh} onProtectedFailure={onProtectedFailure} testId="prep-link-suggestion" />
          : brief ? <div className="people-next-none"><span>No 1:1 planned</span><Button dense variant="ghost" onClick={onPickCalendar}>Pick from calendar</Button></div> : null}
        {prep?.projects.length ? <span className="people-plate-meta" data-testid="prep-projects">
          {prep.projects.map((project) => <Button key={project.id} variant="chrome" className="people-pill people-pill-link" data-tone="info" onClick={refOpener(`project:${project.id}`) ?? undefined}>{project.name}</Button>)}
        </span> : null}

        {concernRows.length || agenda.length ? <div className="people-raise" data-testid="prep-summary-rows">
          <span className="people-cap">TO RAISE</span>
          <ul className="people-raise-list">
            {concernRows}
            {agenda.map((item) => <li key={item.id} className="people-raise-row" data-testid="prep-agenda">
              <span className="people-raise-bead" aria-hidden="true" />
              <span className="people-raise-words">{item.body}</span>
              {item.rolled_from_id ? <span className="people-pill">Rolled</span> : null}
            </li>)}
          </ul>
          {concern && brief ? <ConcernDetail concern={concern} brief={brief} /> : null}
        </div> : null}

        <div className="people-add people-agenda-add">
          <StringGadget label="Add to the agenda" value={agendaDraft} onChange={setAgendaDraft} placeholder="What to raise" inputProps={{ id: `people-agenda-${relationship.id}` }} onKeyDown={(event) => { if (event.key === "Enter") addAgenda(); }} />
          <Button dense variant={lead === "agenda" ? "primary" : "secondary"} disabled={busy === "agenda"} loading={busy === "agenda"} onClick={() => { if (agendaDraft.trim()) addAgenda(); else document.getElementById(`people-agenda-${relationship.id}`)?.focus(); }} data-testid="people-add-agenda">Add to agenda</Button>
        </div>
      </div>
    </section>

    <div className="people-owe-grid">
      <section className="people-plate" data-testid="people-you-owe">
        <h3 className="people-cap">YOU OWE{youOweRows.length ? <b>{youOweRows.length}</b> : null}</h3>
        {youOweRows.length || asked.length ? <ul className="people-plate-rows" data-testid="prep-you-owe">
          {asked.map((item) => <PlateRow key={item.id} testId="people-asked" title={item.body}
            meta={<span className="people-pill" data-tone="info">Asked of you</span>}
            verb={<Button dense variant="ghost" loading={busy === `accept:${item.id}`} onClick={() => accept(item.id)}>Accept</Button>} />)}
          {youOweRows.map((item) => <PlateRow key={item.id} title={item.body}
            onTitle={() => setSelectedCommitment(item)}
            meta={item.due || item.execution_links?.length ? <>{item.due ? <DuePill due={item.due} /> : null}{item.execution_links?.length ? <span className="people-pill" data-tone="info">On a Workbench</span> : null}</> : undefined}
            verb={<Button dense variant="ghost" loading={busy === `done:${item.id}`} onClick={() => done(item.id)}>Done</Button>} />)}
        </ul> : null}
        {selectedCommitment ? <CommitmentInspector commitment={selectedCommitment} onClose={() => setSelectedCommitment(null)} onRefresh={() => { onRefresh(); setSelectedCommitment(null); }} onProtectedFailure={onProtectedFailure} /> : null}
        <div className="people-add">
          <StringGadget label="You owe" value={oweDraft} onChange={setOweDraft} placeholder="What you owe" onKeyDown={(event) => { if (event.key === "Enter") addOwe(); }} />
          <Button dense variant="ghost" disabled={!oweDraft.trim() || busy === "owe"} loading={busy === "owe"} onClick={addOwe}>Add</Button>
        </div>
      </section>

      <section className="people-plate" data-testid="people-they-owe">
        <h3 className="people-cap">THEY OWE YOU{owedRows.length + actions.length ? <b>{owedRows.length + actions.length}</b> : null}</h3>
        {owedRows.length || actions.length ? <ul className="people-plate-rows" data-testid="prep-owed">
          {owedRows.map((item) => <PlateRow key={item.id} title={item.body}
            meta={item.due ? <DuePill due={item.due} /> : undefined}
            verb={<Button dense variant="ghost" loading={busy === `done:${item.id}`} onClick={() => done(item.id)}>Done</Button>} />)}
          {actions.map((action) => <PlateRow key={action.id} title={action.task}
            onTitle={refOpener(`meeting:${action.meeting_id}`) ?? undefined}
            meta={<>{action.meeting_title ? <span>{action.meeting_title}</span> : null}{action.due ? <DuePill due={action.due} /> : null}</>} />)}
        </ul> : null}
        <div className="people-add">
          <StringGadget label="They owe you" value={owedDraft} onChange={setOwedDraft} placeholder="What they owe you" onKeyDown={(event) => { if (event.key === "Enter") addOwed(); }} />
          <Button dense variant="ghost" disabled={!owedDraft.trim() || busy === "owed"} loading={busy === "owed"} onClick={addOwed}>Add</Button>
        </div>
      </section>
    </div>

    <SurfaceFooter
      egress={<EgressChip label="THIS DEVICE" scope="local" />}
      receipt={<span className="people-prep-receipt" data-testid="prep-receipt">PREPARED {preparedAt}</span>}
    />
  </div>;
}
/** PHILO-17 ALIVE: what one roster row says, from the person's record. */
type RowFacts = { next: string | null; youOwe: number; owesYou: number };
function rowFactsOf(detail: RelationshipDetail): RowFacts {
  const open = (items?: Array<{ state?: string }> | null) => (items ?? []).filter((item) => (item.state ?? "open") === "open").length;
  return { next: detail.next_one_on_one ?? null, youOwe: open(detail.commitments), owesYou: open(detail.owed_to_you) };
}
const ROLE_CHOICES: Array<{ value: RelationshipKind; label: string }> = [
  { value: "direct_report", label: "Direct report" }, { value: "peer", label: "Peer" }, { value: "extended", label: "Extended" },
];
/** `Thu 10:00`, `Today 10:00`, `Oct 21 10:00`. */
function oneOnOneWhen(isoDate: string): string {
  const d = wireDate(isoDate);
  if (!d) return "";
  const startOf = (x: Date) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime();
  const days = Math.round((startOf(d) - startOf(new Date())) / 86_400_000);
  const time = d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", hour12: false });
  if (days === 0) return `Today ${time}`;
  if (days === 1) return `Tomorrow ${time}`;
  if (days > 1 && days < 7) return `${d.toLocaleDateString(undefined, { weekday: "short" })} ${time}`;
  return `${d.toLocaleDateString(undefined, { month: "short", day: "numeric" })} ${time}`;
}

/** PHILO-17 ALIVE: a roster row: the avatar, the name, the role chip, the
 *  next 1:1 (or Plan for a report with none), owed both ways as pills. */
function PersonRow({ relationship, fact, selected, onSelect, onPlan }: { relationship: Relationship; fact?: RowFacts; selected: boolean; onSelect(id: string): void; onPlan?(id: string): void }) {
  const report = (relationship.relationship_kind ?? "direct_report") === "direct_report";
  const next = fact?.next ?? relationship.next_one_on_one ?? null;
  const noOneOnOne = Boolean(fact) && !next && report;
  return <SurfaceRow
    selected={selected}
    glyph={<Avatar name={relationship.display_name} />}
    title={relationship.display_name}
    detail={<><span className="people-role-chip" data-kind={relationship.relationship_kind ?? undefined}>{relationshipLabel(relationship.relationship_kind)}</span>{next ? <span className="people-row-fact" data-testid="people-row-next">{`1:1 ${oneOnOneWhen(next)}`}</span> : noOneOnOne ? <span className="people-row-fact" data-quiet="" data-testid="people-row-next">No 1:1 planned</span> : null}</>}
    meta={fact && (fact.youOwe || fact.owesYou) ? <span className="people-row-pills">
      {fact.youOwe ? <span className="surface-token" data-chip data-tone="warn" data-plain="">{`You owe ${fact.youOwe}`}</span> : null}
      {fact.owesYou ? <span className="surface-token" data-chip data-tone="ok" data-plain="">{`Owes you ${fact.owesYou}`}</span> : null}
    </span> : undefined}
    verbs={noOneOnOne && onPlan ? <Button dense variant="ghost" onClick={() => onPlan(relationship.id)}>Plan</Button> : undefined}
    onOpen={() => onSelect(relationship.id)}
  />;
}

function shortWhen(isoDate: string): string {
  try {
    const d = wireDate(isoDate);
    if (!d) return "";
    const now = new Date();
    const startOf = (x: Date) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime(); // calendar days, not 24 h blocks
    const diffDays = Math.round((startOf(d) - startOf(now)) / 86_400_000);
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

/** A due date as a short day (`FRI`); never the raw ISO string. A date-only
 * value (`YYYY-MM-DD`, the `Set a date` producer's calendar day) stays that
 * calendar day in the desk's zone; `new Date("2026-10-06")` would read it as
 * UTC midnight and show the day before west of UTC. */
function shortDay(isoDate: string): string {
  const d = wireDate(isoDate);
  return !d ? isoDate : d.toLocaleDateString(undefined, { weekday: "short" }).toUpperCase();
}

/** The relationship's linked series, as one key: a change re-reads the brief. */
function linkKey(relationship: Relationship): string {
  return (relationship.calendar_links ?? []).map((l) => `${l.uid}:${l.source_id}`).join("|");
}

/** PHILO-13-09 (B4-W): a calendar event whose title holds the report's alias.
 * The custody rule: a suggestion never links by itself; his press on
 * `Link this 1:1` calls the existing calendar-links route. Withheld when empty. */
function LinkSuggestions({ relationship, prep, onLinked, onProtectedFailure, testId }: { relationship: RelationshipDetail; prep: PeoplePrepData; onLinked(): void; onProtectedFailure(cause: unknown): void; testId: string }) {
  const [busy, setBusy] = useState(false);
  const series = useMemo(() => {
    const seen = new Set<string>();
    return prep.calendarLinkSuggestions.filter((ev) => {
      const key = `${ev.uid}:${ev.source_id}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, [prep.calendarLinkSuggestions]);
  if (!series.length) return null;
  const link = async (ev: PrepCalendarEvent) => {
    setBusy(true);
    try {
      await apiFetch(`/api/people/relationships/${encodeURIComponent(relationship.id)}/calendar-links`, {
        method: "POST",
        json: { uid: ev.uid, source_id: ev.source_id, label: ev.title },
      });
      onLinked();
    } catch (cause) { onProtectedFailure(cause); } finally { setBusy(false); }
  };
  return <div data-testid={testId}>
    <SurfaceSection label="Next 1:1">
      <SurfaceRows>{series.map((ev) => <SurfaceRow
        key={`${ev.uid}:${ev.source_id}`}
        title={ev.title}
        detail={[shortWhen(ev.starts_at), ev.source_label].filter(Boolean).join(" · ")}
        verbs={<Button dense variant="primary" loading={busy} disabled={busy} onClick={() => void link(ev)}>Link this 1:1</Button>}
      />)}</SurfaceRows>
    </SurfaceSection>
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
      detail={link.linked_at ? `Linked ${wireDate(link.linked_at)?.toLocaleDateString() ?? ""}` : undefined}
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

  return <div data-testid="people-owner-aliases"><SurfaceSection label="Names in meeting notes">
    {aliases.length ? <SurfaceRows>{aliases.map((alias) => <SurfaceRow
      key={alias}
      title={alias}
      verbs={<ConfirmVerb label="Remove" confirmLabel="Remove?" busy={busy} onConfirm={() => void removeAlias(alias)} />}
    />)}</SurfaceRows> : null}
    <div className="people-alias-add" data-testid="people-alias-add">
      <StringGadget label="Name in meeting notes" value={newAlias} onChange={setNewAlias} placeholder="Name in meeting notes" onKeyDown={(event: React.KeyboardEvent) => { if (event.key === "Enter") void addAlias(); }} />
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
    <SurfaceSection label="Projects"><div className="people-project-link"><CycleGadget label="Project" value={projectId} onChange={setProjectId} options={projects.map((project) => ({ value: project.id, label: project.name }))} /><Button dense disabled={!projectId || relationship.project_refs?.includes(projectId)} onClick={() => void linkProject()}>Link</Button></div>{linkedProjects.length ? <SurfaceRows>{linkedProjects.map((project) => <SurfaceRow key={project.id} title={project.name} detail={project.description} onOpen={() => openProjectRoom(project.id)} verbs={<Button dense variant="ghost" onClick={() => void unlinkProject(project.id)}>Unlink</Button>} />)}</SurfaceRows> : <SurfaceState empty emptyLabel="No linked projects" />}</SurfaceSection>
    <SurfaceSection label="Notes"><div className="people-context-add"><StringGadget label="Topic" value={topic} onChange={setTopic} placeholder="Topic (optional)" /><PadGadget label="Note" value={body} onChange={setBody} placeholder="Context worth remembering" rows={3} /><CycleGadget label="Visibility" value={visibility} onChange={(value) => setVisibility(value as Visibility)} options={[{ value: "leader_private", label: "Leader private" }, { value: "shared_intent", label: "Shared" }]} /><Button dense disabled={!body.trim() || busy} onClick={() => void add()}>Add note</Button></div>{!(relationship.notes ?? []).length ? <SurfaceState empty emptyLabel="No notes" /> : <SurfaceRows>{(relationship.notes ?? []).map((note) => <SurfaceRow key={note.id} title={note.topic || note.body} detail={note.topic ? note.body : undefined} meta={note.visibility === "leader_private" ? "Leader private" : "Shared"} />)}</SurfaceRows>}</SurfaceSection>
  </>;
}

function relationshipLabel(kind?: string): string {
  if (kind === "direct_report") return "Direct report";
  if (kind === "peer") return "Peer";
  if (kind === "extended") return "Extended relationship";
  return "Relationship";
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
  return <div className="people-commitment-inspector"><div className="people-inspector-head"><strong>Commitment</strong><Button dense variant="ghost" onClick={onClose}>Close</Button></div><div className="people-commitment-body">{commitment.body}</div>{linked ? <SurfaceRows><SurfaceRow title={linked.result ? "Output ready" : "Workbench item"} detail={linked.result || `Status: ${linked.status}`} meta={linked.status} onOpen={() => openSurfaceOr("open-workbenches", "/workbenches", `workbench:${linked.workbench_id}`)} /></SurfaceRows> : <div className="people-delegate"><CycleGadget label="Workbench" value={workbenchId} onChange={setWorkbenchId} options={workbenches.map((workbench) => ({ value: workbench.id, label: workbench.name }))} /><Button dense disabled={!workbenchId || busy} onClick={() => void send()}>Send to Workbench</Button><span className="egress-badge is-cloud" title="Workbench model">Workbench model</span></div>}<div className="people-satisfy"><StringGadget label="Satisfaction note" value={rationale} onChange={setRationale} placeholder="What fulfilled the commitment?" /><Button dense variant="primary" disabled={busy} onClick={() => void satisfy()}>Mark satisfied</Button></div></div>;
}

function HistoryLens({ relationship }: { relationship: RelationshipDetail }) {
  const commitments = relationship.commitments ?? [];
  const satisfied = commitments.filter((item) => item.state === "done").length;
  const evidence = commitments.filter((item) => item.history?.some((event) => Boolean(event.evidence?.length))).length;
  const events = commitments.flatMap((item) => (item.history ?? []).map((event) => ({ ...event, commitment: item.body }))).sort((a, b) => String(b.at).localeCompare(String(a.at)));
  const open = commitments.filter((item) => item.state === "open").length;
  // PHILO-17 (UX-CANON: no counters of zero): a fact shows only with a value.
  const facts = ([
    ["Accepted", countToken(commitments.length, "COMMITMENT")],
    ["Satisfied", countToken(satisfied, "DONE")],
    ["Open", countToken(open, "OPEN")],
    ["With evidence", countToken(evidence, "EVIDENCED")],
  ] as Array<[string, string | null | undefined]>).filter((fact): fact is [string, string] => Boolean(fact[1]));
  return <>{facts.length ? <SurfaceSection label="Follow-through"><dl className="people-history-facts" data-testid="people-history-facts">{facts.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl></SurfaceSection> : null}<SurfaceSection label="Timeline">{events.length ? <SurfaceRows>{events.map((event, index) => <SurfaceRow key={`${event.at}-${index}`} title={event.commitment} detail={`${event.event}${event.rationale ? ` · ${event.rationale}` : ""}`} meta={event.at ? new Date(event.at).toLocaleDateString() : undefined} />)}</SurfaceRows> : <SurfaceState empty emptyLabel="No history" />}</SurfaceSection></>;
}

function InfoLens({ relationship, onProtectedFailure, onArchived }: { relationship: RelationshipDetail; onProtectedFailure(cause: unknown): void; onArchived(): void }) {
  const archive = async () => { try { await apiFetch(`/api/people/relationships/${encodeURIComponent(relationship.id)}/archive`, { method: "POST", json: {} }); onArchived(); } catch (cause) { onProtectedFailure(cause); } };
  return <SurfaceSection label="Info"><dl className="people-info"><div><dt>Relationship</dt><dd>{relationshipLabel(relationship.relationship_kind)}</dd></div>{relationship.role_context ? <div><dt>Role</dt><dd>{relationship.role_context}</dd></div> : null}{relationship.cadence ? <div><dt>Cadence</dt><dd>{relationship.cadence}</dd></div> : null}<div><dt>Storage</dt><dd>Encrypted</dd></div><div><dt>Sync</dt><dd>This device only</dd></div><div><dt>Capture</dt><dd>Notes only</dd></div></dl><ConfirmVerb label="Archive" confirmLabel="Archive?" onConfirm={() => void archive()} /></SurfaceSection>;
}
