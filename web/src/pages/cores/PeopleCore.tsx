// HS-135-04: People is a single protected Desk application.  Its roster is
// a relationship projection, never a field of person tiles or a scorecard.
import { PersonPages } from "../../desk/standingPages";
import { wireDate } from "../../desk/surface/format";
import { useCallback, useEffect, useId, useMemo, useRef, useState, type ReactNode } from "react";
import type { CoreProps } from "./core-types";
import { Button } from "../../components/signal/Signal";
import { ApiError, apiFetch } from "../../lib/api";
import { plainFailure } from "../../desk/surface/plainFailure";
import { openSurfaceOr } from "../../desk/shell";
import { openSourceRef } from "../../desk/surface/citations";
import { PERSON_OPEN_EVENT, openPerson, refOpener, type PersonOpenRequest } from "../../desk/openObject";
import { peekPersonLens, takePersonLens } from "../../desk/objectWindows";
import { composePeoplePrep, readPeoplePrep, type PeoplePrepData, type PrepCalendarEvent } from "../../desk/people/prepData";
import { announceTaskReturn, taskFocusPending } from "../../desk/returnToTask";
import { useOnDeskChanged } from "../../desk/useDeskChangedRefresh";
import { keepPlace, keptPlace, keptDraft, useDeskDraft } from "../../desk/deskMemory";
import { useDesk } from "../../desk/store";
import { useDeskWriteReceipt } from "../../desk/hooks/useWriteReceipt";
import { CycleGadget, PadGadget, StringGadget } from "../../desk/surface/gadgets";
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
  SurfaceWell,
} from "../../desk/surface/Surface";
import { Disclosure } from "../../desk/surface/patterns/Disclosure";
import { countToken } from "../../desk/surface";
import { Avatar, DotWord, Loading, StatusBar, ToolGlyph, Toolbar, countWords, hueOf, initialsOf } from "../../desk/surface/kit";
import { useWindowInterior } from "../../desk/surface/interior";
import { ObjectList, type ObjectListRow, type ObjectListSort } from "../../desk/surface/objects/ObjectList";
import { renderHeroSlot } from "./core-layout";
import { useOwnerName } from "../../desk/firstrun/ownerName";
import { nudgeText } from "../../desk/needs/NeedsDrawer";
import { NoteSendWells } from "../../desk/documentSendsLazy";
import { PeopleNotHere, PeopleReadFailed } from "../../desk/people/PeopleReadFailed";
import { useWindowTitle } from "../../desk/surface/title";
import "./people.css";
import { openProjectRoom } from "../../desk/shell";

type ReadinessState = "unconfigured" | "locked" | "key_unavailable" | "corrupt" | "unavailable" | "no_key_store" | "ready";
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
type CalendarRead = { loading: boolean; error: string; retry(): void };
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
  /** PHILO-17: `?counts=1` — open commitments each way. */
  you_owe_count?: number;
  owes_you_count?: number;
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
/** Betterment D7: the last 1:1 with the person (else the last meeting she was in). */
type BriefLastTime = {
  meeting_id: string; title: string | null; started_at: string; one_on_one: boolean;
  points: Array<{ id: string; task: string; owner: string | null; due: string | null; status: string | null }>;
  decisions: Array<{ id: string; decision_text: string; lifecycle: string }>;
};
/** Betterment D0/D7: his own meeting actions for this person ("I owe"). */
type BriefMyAction = { id: string; task: string; owner: string | null; due: string | null; due_said?: string | null; status?: string | null; meeting_id: string; meeting_title: string | null };
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
  last_time?: BriefLastTime | null;
  i_owe_meeting_actions?: BriefMyAction[];
  /** The brief's memory: plaintext desk excerpts on this person's projects. */
  memory?: { excerpts?: Array<{ ref: string; kind: string; title: string; text: string; project_id?: string }> } | null;
};
/** Betterment D6: a name his work mentions that no Person has yet
 *  (`GET /api/people/suggestions`, PeopleService.suggestions). */
type Suggestion = {
  key: string;
  name: string;
  said: string;
  relationship_kind: RelationshipKind;
  source: "meeting" | "1:1 series" | "jira";
  one_on_one: boolean;
  series: { uid: string; source_id: string; label: string; next_starts_at: string } | null;
  jira: boolean;
  meeting_count: number;
  promise_count: number;
  meetings: Array<{ id: string; title: string; started_at: string }>;
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
  // Betterment daily D8: no keychain on this Mac; not a failure to retry.
  if (code === "people_key_store_unavailable") return { readiness: "no_key_store" };
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

/** PHILO-17 (Astra MUST 4): the roster read carries each person's owed
 *  counts (one read of the open commitments on the hub). */
const ROSTER_READ = "/api/people/relationships?counts=1";

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
  // top of the roster.
  const [adding, setAdding] = useState(false);
  // Betterment D6: the people his work names that People does not hold.
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [suggestionBusy, setSuggestionBusy] = useState("");
  const readSuggestions = useCallback(async () => {
    try {
      const read = await apiFetch<{ suggestions?: Suggestion[] }>("/api/people/suggestions");
      setSuggestions(read.suggestions ?? []);
    } catch { /* the last read stays; the roster's own read names a failure */ }
  }, []);
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
      // Betterment D6: no Set up step. With no store yet the roster is
      // empty and the suggestions still come; the first Add makes the store.
      if (stateOf(next) === "unconfigured") { clearProtected(); void readSuggestions(); return; }
      if (stateOf(next) !== "ready") { clearProtected(); return; }
      const list = await apiFetch<{ relationships?: Relationship[] }>(ROSTER_READ);
      setRelationships(list.relationships ?? []);
      void readSuggestions();
    } catch (cause) {
      clearProtected();
      setReadiness(readinessForError(cause));
      setError(plainFailure("PEOPLE DID NOT LOAD", cause));
    } finally { setLoading(false); }
  }, [clearProtected, readSuggestions]);
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
        const list = await apiFetch<{ relationships?: Relationship[] }>(ROSTER_READ);
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

  // The row facts: the owed counts ride the roster read (`?counts=1`);
  // the next 1:1 is the Door's upcoming calendar events that carry a
  // person (ONE read for the whole roster, again only when the list of
  // people changes). Read while no person is open.
  const personOpen = Boolean(selectedId || requestedRelationshipId);
  const rosterKey = relationships.map((row) => row.id).join("|");
  const [nextByPerson, setNextByPerson] = useState<Record<string, RosterNext> | null>(null);
  // The roster whose next-1:1 read has ended (read or failed). Until it ends
  // the roster says it is reading: the Next 1:1 plate it adds lands above the
  // rows and reorders them (rows moved 153 px under load: the desk sweep).
  const [nextReadFor, setNextReadFor] = useState<string | null>(null);
  useEffect(() => {
    if (personOpen || !rosterKey) return;
    let live = true;
    void apiFetch<{ upcoming?: Array<Record<string, unknown>> }>("/api/door")
      .then((door) => { if (live) { setNextByPerson(nextOneOnOnes(door.upcoming ?? [])); setNextReadFor(rosterKey); } })
      .catch(() => { if (live) { setNextByPerson(null); setNextReadFor(rosterKey); } });
    return () => { live = false; };
  }, [rosterKey, personOpen]);
  const nextReading = !personOpen && Boolean(rosterKey) && nextReadFor !== rosterKey;
  const rowFacts = useMemo<Record<string, RowFacts>>(() => Object.fromEntries(relationships.map((row) => [row.id, {
    next: nextByPerson?.[row.id]?.startsAt ?? null,
    known: nextByPerson !== null,
    youOwe: Number(row.you_owe_count) || 0,
    owesYou: Number(row.owes_you_count) || 0,
  }])), [relationships, nextByPerson]);

  const unconfigured = stateOf(readiness) === "unconfigured";
  const unavailable = stateOf(readiness) !== "ready" && !unconfigured;
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
      const list = await apiFetch<{ relationships?: Relationship[] }>(ROSTER_READ);
      setRelationships(list.relationships ?? []);
    } catch (cause) { protectedFailure(cause); } finally {
      setBusy(false);
      document.getElementById("people-new-relationship")?.focus();
    }
  };
  // Betterment D6: Add makes the person in one press (the full name, the
  // kind, the spoken name and the 1:1 series ride along); Not a person
  // hides the name for good.
  const addSuggestion = async (suggestion: Suggestion) => {
    setSuggestionBusy(suggestion.key); setError("");
    try {
      await apiFetch("/api/people/suggestions/add", { method: "POST", json: { key: suggestion.key } });
      setSuggestions((rows) => rows.filter((row) => row.key !== suggestion.key));
      await load();
    } catch (cause) { protectedFailure(cause); } finally { setSuggestionBusy(""); }
  };
  const hideSuggestion = async (suggestion: Suggestion) => {
    setSuggestionBusy(suggestion.key); setError("");
    try {
      await apiFetch("/api/people/suggestions/hide", { method: "POST", json: { key: suggestion.key } });
      setSuggestions((rows) => rows.filter((row) => row.key !== suggestion.key));
    } catch (cause) { protectedFailure(cause); } finally { setSuggestionBusy(""); }
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
  // Window grammar (2026-10-24): the roster is a list view and a person is
  // sections under hairlines: both run edge to edge.
  useWindowInterior("list");
  const [rowSelected, setRowSelected] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<ObjectListSort>({ key: "next", dir: "asc" });
  const openAdd = () => { setAdding(true); window.setTimeout(() => document.getElementById("people-new-relationship")?.focus(), 0); };

  // W1-KIT: the first read shows the ghost rows of the list grammar; the
  // roster keeps its toolbar band (its verbs arrive with the roster).
  if (loading) return selectedId ? <Loading data-testid="people-loading" /> : <>
    <Toolbar label="People" />
    <Loading data-testid="people-loading" />
  </>;
  if (unavailable) {
    const state = stateOf(readiness);
    // Betterment daily D8: People cannot hold a key on this Mac: one line, no verb.
    if (state === "no_key_store") return <PeopleNotHere />;
    // Betterment D6: a People read that failed is one line in place.
    if (state === "unavailable" || state === "locked") return <PeopleReadFailed onRetry={() => void load()} detail={error} />;
    const face = readinessFace(state);
    return <div className="people-joy-state" data-testid="people-joy-state">
      <div className="people-joy-lead">
        <Button variant="primary" onClick={recover} data-testid="people-joy-action">{face.action}</Button>
        <span className="people-joy-line">{face.label}</span>
      </div>
      {error ? <span className="sr-only">{error}</span> : null}
    </div>;
  }
  // PHILO-13-04 (A3): the failure is ONE row that stays on screen while he
  // is down in a lens; the person and any unsent draft stay under it
  // (J3-06). Try again re-reads the person (or the roster); the row leaves
  // only when that read lands.
  const failureRow = error ? (
    <span className="people-failure" role="alert" data-testid="people-failure">
      <span className="people-failure-label">{error}</span>
      <Button dense variant="ghost" onClick={() => void (selectedId ? select(selectedId) : load())}>Try again</Button>
    </span>
  ) : null;

  // A person opened in place (a `people:<id>` scope, or the kept place).
  if (selected) {
    return <div className="people-surface">
      {renderHeroSlot(hero, null, failureRow)}
      <RelationshipPane relationship={selected} initialLens={requestedLens} lensRequest={lensRequest} onRefresh={() => void select(selected.id)} onProtectedFailure={protectedFailure} onArchived={() => { clearProtected(); void load(); }} onBack={() => { setSelectedId(null); setDetail(null); keepPlace(PEOPLE_PERSON_PLACE, ""); }} />
    </div>;
  }

  // The roster (window grammar): Toolbar [Add person] + search → the dense
  // list view (Name · Role · Next 1:1 · You owe), the names his meetings
  // carry as a second group under the people → the status bar (the count,
  // the next 1:1 in warm words, Encrypted; the selected row's verbs).
  const scoped = projectFilter ? relationships.filter((r) => (r.project_refs ?? []).includes(projectFilter)) : relationships;
  const scopedOut = projectFilter ? relationships.length - scoped.length : 0;
  const needle = nameKey(query);
  const shownPeople = needle ? scoped.filter((r) => nameKey(r.display_name).includes(needle)) : scoped;
  const shownSuggestions = projectFilter ? [] : needle ? suggestions.filter((s) => nameKey(s.name).includes(needle)) : suggestions;
  const weekEnd = Date.now() + 7 * 86_400_000;
  // The soonest 1:1 this week: the status bar's warm words; within a day its
  // Open prep is the bar's primary verb.
  const soonest = scoped
    .map((row) => ({ row, next: nextByPerson?.[row.id] }))
    .filter((x): x is { row: Relationship; next: RosterNext } => Boolean(x.next && (wireDate(x.next.startsAt)?.getTime() ?? Infinity) <= weekEnd))
    .sort((a, b) => (wireDate(a.next.startsAt)?.getTime() ?? 0) - (wireDate(b.next.startsAt)?.getTime() ?? 0))[0] ?? null;
  const soonestAt = soonest ? wireDate(soonest.next.startsAt)?.getTime() ?? Infinity : Infinity;
  const prepDue = Boolean(soonest) && soonestAt - Date.now() <= 86_400_000;
  const personRows: ObjectListRow[] = shownPeople.map((relationship) => {
    const fact = rowFacts[relationship.id];
    const report = (relationship.relationship_kind ?? "direct_report") === "direct_report";
    const next = fact?.next ?? relationship.next_one_on_one ?? null;
    const at = next ? wireDate(next)?.getTime() ?? Number.MAX_SAFE_INTEGER : Number.MAX_SAFE_INTEGER;
    const noOneOnOne = Boolean(fact?.known) && !next && report;
    return {
      id: relationship.id,
      kind: "person",
      name: relationship.display_name,
      avatar: { initials: initialsOf(relationship.display_name), hue: hueOf(relationship.display_name) },
      nameTestId: "people-row-name",
      cells: {
        role: relationshipLabel(relationship.relationship_kind),
        next: next ? `1:1 ${oneOnOneWhen(next)}` : noOneOnOne ? "None" : "",
        owe: fact?.youOwe ? String(fact.youOwe) : "",
      },
      sortValues: { next: at, owe: fact ? fact.youOwe : 0, role: relationshipLabel(relationship.relationship_kind) },
    };
  });
  // The hub ranks the names his work carries; the group keeps that order.
  const suggestionRows: ObjectListRow[] = shownSuggestions.map((row, index) => ({
    id: `suggestion:${row.key}`,
    kind: "person",
    name: row.name,
    avatar: { initials: initialsOf(row.name), hue: hueOf(row.name) },
    group: 1,
    cells: { role: "From your meetings", next: sentence(suggestionSource(row)), owe: "" },
    sortValues: { next: index, owe: index, role: String(index).padStart(4, "0") },
  }));
  const rows = [...personRows, ...suggestionRows];
  const byPerson = new Map(shownPeople.map((r) => [r.id, r]));
  const bySuggestion = new Map(shownSuggestions.map((s) => [`suggestion:${s.key}`, s]));
  const chosen = rowSelected && (byPerson.has(rowSelected) || bySuggestion.has(rowSelected)) ? rowSelected : null;
  const chosenPerson = chosen ? byPerson.get(chosen) ?? null : null;
  const chosenSuggestion = chosen ? bySuggestion.get(chosen) ?? null : null;
  const chosenNoOneOnOne = chosenPerson ? personRows.find((r) => r.id === chosenPerson.id)?.cells?.next === "None" : false;
  const selectionVerbs = chosenSuggestion ? <>
    <Button dense variant="secondary" loading={suggestionBusy === chosenSuggestion.key} disabled={Boolean(suggestionBusy)} onClick={() => void addSuggestion(chosenSuggestion)} aria-label={`Add ${chosenSuggestion.name}`} data-testid="people-suggestion-add"><ToolGlyph kind="new" />Add</Button>
    <Button dense variant="secondary" disabled={Boolean(suggestionBusy)} onClick={() => void hideSuggestion(chosenSuggestion)} aria-label={`${chosenSuggestion.name} is not a person`} data-testid="people-suggestion-hide">Not a person</Button>
  </> : chosenPerson ? <>
    <Button dense variant="secondary" onClick={() => openPerson(chosenPerson.id)} data-testid="people-open-selected">
      <ToolGlyph kind="open" />
      Open
    </Button>
    {chosenNoOneOnOne ? <Button dense variant="secondary" onClick={() => openPerson(chosenPerson.id, "prep")} data-testid="people-plan">Plan</Button> : null}
  </> : null;
  // W1-KIT: the status bar holds the selection's verbs only; Open prep (a
  // 1:1 within a day) is a plain toolbar verb beside Add person, the one
  // primary.
  const verbs = selectionVerbs;
  const everyone = projectFilter && scopedOut > 0 ? (
    <Button dense variant="secondary" aria-label="Everyone: clear the Project scope" onClick={() => setProjectFilter(null)} data-testid="people-roster-everyone">{`${scopedOut} more · Everyone`}</Button>
  ) : null;
  const toolbar = (
    <Toolbar label="People" data-testid="people-toolbar" trailing={<>
      {everyone}
      {relationships.length || suggestions.length ? <span className="people-search">
        <StringGadget label="Search people" value={query} onChange={setQuery} placeholder="Search people" />
      </span> : null}
    </>}>
      <Button dense variant="primary" onClick={openAdd} data-testid="people-add"><ToolGlyph kind="new" />Add person</Button>
      {prepDue && soonest ? <Button dense variant="secondary" onClick={() => openPerson(soonest.row.id, "prep")} data-testid="people-open-prep"><ToolGlyph kind="open" />Open prep</Button> : null}
    </Toolbar>
  );
  const firstName = (name: string) => name.trim().split(/\s+/)[0] || name;
  const empty = !relationships.length && !suggestions.length && !projectFilter && !adding;
  return <div className="people-surface people-roster" data-testid="people-roster">
    {renderHeroSlot(hero, null)}
    {toolbar}
    {failureRow}
    {nextReading ? <span hidden aria-busy="true" data-testid="people-next-reading" /> : null}
    {adding ? <div className="people-new" data-testid="people-add-row">
      <StringGadget label="Add person" value={newName} onChange={setNewName} placeholder="Name" inputProps={{ id: "people-new-relationship" }} onKeyDown={(event) => { if (event.key === "Enter") void createRelationship(); if (event.key === "Escape" && relationships.length) setAdding(false); }} />
      <span className="people-role-pick" role="group" aria-label="Relationship">
        {ROLE_CHOICES.map((choice) => <Button key={choice.value} dense variant="ghost" className="people-role-choice" data-kind={choice.value} aria-pressed={newKind === choice.value} onClick={() => setNewKind(choice.value)}>{choice.label}</Button>)}
      </span>
      <Button dense variant="primary" disabled={!newName.trim() || busy} loading={busy} onClick={() => void createRelationship()}>{duplicateShown ? "Add again" : "Add"}</Button>
      {relationships.length ? <Button dense variant="ghost" onClick={() => setAdding(false)}>Done</Button> : null}
      {duplicateShown ? <span className="people-duplicate" role="status" data-testid="people-duplicate">{duplicateShown.display_name} · Already here</span> : null}
    </div> : null}
    <WhoAreYou />
    {empty ? (
      <div className="people-empty" data-testid="people-empty-roster">
        <SurfaceState empty emptyLabel="People you meet appear here." emptyImage={PEOPLE_SPRITE} emptyKind="person"
          onAction={openAdd} actionLabel="Add person" />
      </div>
    ) : projectFilter && !scoped.length ? (
      <div className="people-empty" data-testid="people-roster-none-linked">
        <SurfaceState empty emptyLabel="No one linked yet" emptyImage={PEOPLE_SPRITE} emptyKind="person" />
      </div>
    ) : rows.length ? (
      <div className="people-list" data-testid="people-list">
        <ObjectList
          label="People"
          density="dense"
          rows={rows}
          columns={PEOPLE_COLUMNS.filter((column) => column.key === "name" || rows.some((row) => row.cells?.[column.key]))}
          sort={sort}
          onSort={(key: string) => setSort((current) => ({ key, dir: current.key === key && current.dir === "asc" ? "desc" : "asc" }))}
          selectedId={chosen}
          onSelect={setRowSelected}
          onOpen={(id) => { if (byPerson.has(id)) openPerson(id); else setRowSelected(id); }}
          rowProps={(row) => ({
            "data-testid": row.group ? "people-suggestion" : "people-row",
            "data-suggested": row.group ? "" : undefined,
            // DELIGHT 2 (small joys): a person's next 1:1 is in their own
            // teal (people.css), not grey; "None" and suggestions stay quiet.
            "data-next-one-on-one": !row.group && String(row.cells?.next ?? "").startsWith("1:1 ") ? "" : undefined,
          })}
        />
      </div>
    ) : null}
    <StatusBar
      data-testid="people-status"
      verbs={verbs}
      items={[
        { key: "count", testId: "people-count", text: projectFilter ? countWords(scoped.length, "on this project", "on this project") : countWords(relationships.length, "person", "people") },
        soonest ? { key: "next", lamp: prepDue ? "ask" as const : "info" as const, testId: "people-roster-next", text: `1:1 with ${firstName(soonest.row.display_name)} ${lowerDay(oneOnOneWhen(soonest.next.startsAt))}` } : null,
        { key: "suggested", lamp: "warn" as const, testId: "people-suggestions", text: projectFilter ? null : countWords(suggestions.length, "from your meetings", "from your meetings") },
        { key: "lock", lamp: "ok" as const, text: <span className="people-lock" title="Encrypted · Local storage · Notes only" data-testid="people-lock">Encrypted</span> },
      ]}
    />
  </div>;
}

const PEOPLE_SPRITE = `${import.meta.env.BASE_URL || "/_built/"}desk/sprites/people-ledger.png`;

// A column no row fills is not drawn (an empty column is a zero in
// another form, UX-CANON A.8).
const PEOPLE_COLUMNS = [
  { key: "name", word: "Name", track: "minmax(160px, 1.4fr)" },
  { key: "role", word: "Role", track: "minmax(170px, 0.8fr)" },
  { key: "next", word: "Next 1:1", track: "minmax(0, 1fr)" },
  { key: "owe", word: "You owe", track: "88px" },
] as const;

/** `Today 17:12` → `today 17:12` inside a sentence; a weekday stays. */
function lowerDay(words: string): string {
  return /^(Today|Tomorrow)\b/.test(words) ? words.charAt(0).toLowerCase() + words.slice(1) : words;
}

/** The first letter up (`named in Vendor sync` → `Named in Vendor sync`). */
function sentence(words: string): string {
  return words ? words.charAt(0).toUpperCase() + words.slice(1) : words;
}

/** Where a suggested name came from, in words. */
function suggestionSource(row: Suggestion): string {
  const parts: string[] = [];
  if (row.series) parts.push(row.series.next_starts_at ? `1:1 ${oneOnOneWhen(row.series.next_starts_at)}` : row.series.label || "1:1 series");
  else if (row.meetings[0]) parts.push(`named in ${row.meetings[0].title || "a meeting"}`);
  else if (row.jira) parts.push("assigned in Jira");
  if (row.promise_count) parts.push(row.promise_count === 1 ? "1 promise" : `${row.promise_count} promises`);
  return parts.join(" · ");
}

/** W1-TRUTH (atlas 2026-10-27): "Why does People ask my name?" His name
 *  belongs to Settings ▸ You. While it is not set, People says so ONCE: a
 *  quiet row with the one verb that opens Settings ▸ You; later visits
 *  show nothing. */
const NAME_ASKED_KEY = "hs.people.name-asked";

function nameAsked(): boolean {
  try { return window.localStorage.getItem(NAME_ASKED_KEY) === "1"; } catch { return false; }
}

function WhoAreYou() {
  const owner = useOwnerName();
  const [asked, setAsked] = useState(false);
  const [seen] = useState(nameAsked);
  useEffect(() => {
    if (seen || owner.loading || owner.readError || owner.isSet) return;
    setAsked(true);
    try { window.localStorage.setItem(NAME_ASKED_KEY, "1"); } catch { /* a private window asks again */ }
  }, [seen, owner.loading, owner.readError, owner.isSet]);
  if (!asked || owner.isSet) return null;
  return <div className="people-you-row" data-testid="people-who-are-you">
    <DotWord tone="warn">Your name is not set</DotWord>
    <Button dense variant="ghost" onClick={() => openSurfaceOr("configure-settings", "/settings", "owner")} data-testid="people-set-name">Set your name</Button>
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lensRequest, setLensRequest] = useState<{ lens: Lens; seq: number } | null>(null);
  useWindowTitle(detail?.display_name ?? null, [detail?.display_name]);
  useWindowInterior("list");
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
    setLoading(true);
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
    } finally {
      setLoading(false);
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
  if (loading && !detail) return <SurfaceState loading />;
  if (readiness && stateOf(readiness) !== "ready") {
    const face = readinessFace(stateOf(readiness));
    return <div className="people-joy-state" data-testid="people-joy-state">
      <div className="people-joy-lead">
        <Button variant="primary" onClick={() => openSurfaceOr("open-people", "/")} data-testid="people-joy-action">{face.action}</Button>
        <span className="people-joy-line">{face.label}</span>
      </div>
    </div>;
  }
  // Window grammar: the person window is the RelationshipPane with its
  // toolbar (Record meeting, Add note), a compact head, the prep's sections
  // edge to edge and the status bar (the next 1:1, Encrypted).
  return <div className="people-surface person-window" data-testid="person-window">
    {error ? (
      <span className="people-failure" role="alert" data-testid="people-failure">
        <span className="people-failure-label">{error}</span>
        <Button dense variant="ghost" onClick={() => void read()}>Try again</Button>
      </span>
    ) : null}
    {detail ? (
      <RelationshipPane relationship={detail} initialLens={initialLens} lensRequest={lensRequest} noteVerb
        /* Betterment Q11: What I owe her and What she owes me, first, from
           the desk's memory pages (no Ask). */
        lead={<PersonPages displayName={detail.display_name} />}
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
export function RelationshipPane({ relationship, initialLens, lensRequest = null, onRefresh, onProtectedFailure, onArchived, onBack, lead, noteVerb = false }: { relationship: RelationshipDetail; initialLens?: Lens | null; lensRequest?: { lens: Lens; seq: number } | null; onRefresh(): void; onProtectedFailure(cause: unknown): void; onArchived(): void; onBack?(): void;
  /** Material under the head (the person window's memory pages). */
  lead?: ReactNode;
  /** The person window: Add note sits on the toolbar (it opens Context's note well). */
  noteVerb?: boolean }) {
  // PHILO-13-07 (B2): the tab is part of the place, kept per person.
  const lensPlace = `people/lens/${relationship.id}`;
  const [lens, setLensState] = useState<PaneLens>(() => paneLens(initialLens) ?? paneLens(keptPlace(lensPlace)) ?? "prep");
  const setLens = useCallback((next: PaneLens) => {
    setLensState(next);
    keepPlace(lensPlace, next === "prep" ? "" : next);
  }, [lensPlace]);
  // PHILO-13-06 (B1): a row that opens this person on a lens moves the open window to it.
  // On mount the state's initializer already holds that lens: the first run only
  // keeps it. A mount run that set it again could land after his first tab press
  // and undo it (the -n 8 flake of peopleReopenLens, 2026-10-12).
  const firstLensRun = useRef(true);
  useEffect(() => {
    const first = firstLensRun.current;
    firstLensRun.current = false;
    const next = paneLens(initialLens);
    if (!next) return;
    if (first) keepPlace(lensPlace, next === "prep" ? "" : next);
    else setLens(next);
  }, [initialLens, setLens, lensPlace]);
  useEffect(() => { if (lensRequest) setLens(paneLens(lensRequest.lens) ?? "prep"); }, [lensRequest, setLens]);
  // The calendar picker (Context) reads the Door's upcoming events.
  const [upcomingEvents, setUpcomingEvents] = useState<UpcomingEvent[]>([]);
  const [calendarLoading, setCalendarLoading] = useState(lens === "context");
  const [calendarError, setCalendarError] = useState("");
  const [calendarAttempt, setCalendarAttempt] = useState(0);
  const [contextLinksOpen] = useState(false);
  const [prepRead, setPrepRead] = useState(false);
  const wantsCalendar = lens === "context";
  useEffect(() => {
    if (!wantsCalendar) return;
    let live = true;
    setCalendarLoading(true);
    setCalendarError("");
    void apiFetch<{ upcoming?: UpcomingEvent[] }>("/api/door")
      .then((door) => {
        if (!live) return;
        setUpcomingEvents((door.upcoming ?? []).filter(
          (item: Record<string, unknown>) => item.source === "calendar_event" && item.uid,
        ) as UpcomingEvent[]);
      })
      .catch((cause) => { if (live) setCalendarError(plainFailure("CALENDAR DID NOT LOAD", cause)); })
      .finally(() => { if (live) setCalendarLoading(false); });
    return () => { live = false; };
  }, [relationship.id, wantsCalendar, calendarAttempt]);
  const calendarRead: CalendarRead = { loading: calendarLoading, error: calendarError, retry: () => setCalendarAttempt((attempt) => attempt + 1) };
  const recordingState = useDesk((state) => state.recording);
  // The prep's read names the next 1:1 (the head's line, the toolbar's Record).
  const [next, setNext] = useState<PrepNext | null>(null);
  const [noteRequest, setNoteRequest] = useState(0);
  useEffect(() => { if (lens !== "context") setNoteRequest(0); }, [lens]);
  const nextWords = next?.at ? `1:1 ${oneOnOneWhen(next.at)}` : "";
  const record = next?.eventId && recordingState !== "recording" ? (
    <Button dense variant="primary" loading={recordingState === "busy"} disabled={recordingState !== "idle"}
      onClick={() => void useDesk.getState().startRecording({ calendarEventId: next.eventId! })}
      data-testid="prep-record-meeting"><ToolGlyph kind="record" />Record meeting</Button>
  ) : null;
  const addNote = noteVerb ? (
    <Button dense variant="secondary" onClick={() => { setLens("context"); setNoteRequest((n) => n + 1); }} data-testid="person-add-note">
      <ToolGlyph kind="new" />Add note
    </Button>
  ) : null;
  return <div className="people-detail person-page">
    {/* Window grammar: the window's verbs on a toolbar under the title bar. */}
    {onBack || record || addNote ? <Toolbar label={relationship.display_name} data-testid="person-toolbar">
      {onBack ? <Button dense variant="secondary" onClick={onBack}>Back</Button> : null}
      {record}
      {addNote}
    </Toolbar> : null}
    <header className="people-detail-head" data-testid="people-detail-head">
      <Avatar name={relationship.display_name} size="md" />
      <span className="people-who">
        <h2 className="people-name" data-testid="prep-display-name">{relationship.display_name}</h2>
        <span className="people-who-meta" data-testid="people-who-meta">
          {[relationshipLabel(relationship.relationship_kind), relationship.role_context, nextWords].filter(Boolean).join(" · ")}
        </span>
      </span>
    </header>
    {lead}
    {/* Betterment D7: the prep is the page; Context, History and Info are
        folds under it (one open at a time; a door that asks for one opens it). */}
    <PrepPane relationship={relationship} onRefresh={onRefresh} onProtectedFailure={onProtectedFailure} onRead={() => setPrepRead(true)} onNext={setNext} />
    {/* The folds wait for the prep's first read: drawn under a loading prep,
        they moved down when it landed (the desk sweep's still fence). */}
    {prepRead || lens !== "prep" ? <div className="people-folds" data-testid="people-folds">
      {PANE_TABS.filter(([id]) => id !== "prep").map(([id, label]) => <Disclosure key={id} label={label}
        open={lens === id} onOpenChange={(open) => setLens(open ? id : "prep")}>
        {lens === id && id === "context" ? <ContextLens key={relationship.id} relationship={relationship} onRefresh={onRefresh} onProtectedFailure={onProtectedFailure} upcomingEvents={upcomingEvents} calendarRead={calendarRead} initialLinksOpen={contextLinksOpen} noteRequest={noteRequest} noteVerbOutside={noteVerb} /> : null}
        {lens === id && id === "history" ? <HistoryLens relationship={relationship} /> : null}
        {lens === id && id === "info" ? <InfoLens relationship={relationship} onArchived={onArchived} onProtectedFailure={onProtectedFailure} /> : null}
      </Disclosure>)}
    </div> : null}
  </div>;
}

/** What the prep's read says of the next 1:1. */
type PrepNext = { at: string | null; eventId: string | null };

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

/** `Thu Oct 8` (the day a meeting was held). */
function dayLabel(isoDate: string): string {
  const d = wireDate(isoDate);
  return d ? d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" }) : "";
}

/** A memory kind in a plain word. */
function kindWord(kind: string): string {
  const k = String(kind || "").toLowerCase();
  if (k.includes("decision")) return "Decision";
  if (k.includes("meeting")) return "Meeting";
  if (k.includes("note")) return "Note";
  if (k.includes("item") || k.includes("action")) return "Action";
  if (k.includes("page")) return "Page";
  if (k.includes("update") || k.includes("send")) return "Update";
  return "Note";
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
  const day = shortDay(due);
  const words = `by ${day.charAt(0)}${day.slice(1).toLowerCase()}`;
  return isOverdue(due)
    ? <span className="people-state" data-tone="danger"><span className="kit-dot" data-tone="fail" aria-hidden="true" />{`Overdue · ${words}`}</span>
    : <span>{words}</span>;
}

/** HS-172-05: the rows behind a Prep concern (PRs, assignments, overdue). */
function ConcernDetail({ concern, brief }: { concern: Exclude<NowConcern, null>; brief: OneOnOneBrief }) {
  const ws = brief.watch_summary;
  if (concern === "prs" && ws?.prs_waiting?.length) return <div data-testid="now-prs-detail" className="people-concern">
    <SurfaceLedger count={`PRS WAITING ${ws.prs_waiting.length}`} cols="room">
      {ws.prs_waiting.map((pr) => <SurfaceLedgerRow key={`pr-${pr.pr_number}`} wrap expands={false}
        primary={<span className="surface-primary">{`#${pr.pr_number} · ${pr.title}`}</span>}
        cells={<span className="people-now-caption"><span className={pr.days_waiting >= 3 ? "people-now-caption-warning" : ""}>{pr.days_waiting} {pr.days_waiting === 1 ? "DAY" : "DAYS"}</span>{pr.repo ? <> · <span>{pr.repo.toUpperCase()}</span></> : null}</span>}
        trailing={pr.url ? <Button dense variant="ghost" onClick={() => window.open(pr.url, "_blank", "noopener")}>Open PR</Button> : undefined} />)}
    </SurfaceLedger>
  </div>;
  if (concern === "assignments" && ws?.open_assignments?.length) return <div data-testid="now-assignments-detail" className="people-concern">
    <SurfaceLedger count={`ASSIGNMENTS OPEN ${ws.open_assignments.length}`} cols="room">
      {ws.open_assignments.map((a) => <SurfaceLedgerRow key={a.key} wrap expands={false}
        primary={<span className="surface-primary">{`${a.key} · ${a.summary}`}</span>}
        cells={<span className="people-now-caption"><span>{a.status.toUpperCase()}</span>{a.overdue ? <> · <span className="people-now-caption-warning">OVERDUE</span></> : null}</span>}
        trailing={a.url ? <Button dense variant="ghost" onClick={() => window.open(a.url, "_blank", "noopener")}>Open issue</Button> : undefined} />)}
    </SurfaceLedger>
  </div>;
  return null;
}

/** PHILO-17 REFIT — Prep, the lead: the next 1:1 as the focus plate (when,
 *  what to raise, add to the agenda), then two plates: what he owes and
 *  what is owed to him, each with its add row. Every fact is the person's
 *  record or the hub's 1:1 brief (`/brief`, read-only). */
function PrepAddWell({ label, draft, onChange, onAdd, busy, actionLabel = "Add", testId }: {
  label: string; draft: string; onChange(value: string): void; onAdd(onSaved: () => void): void;
  busy: boolean; actionLabel?: string; testId?: string;
}) {
  const [open, setOpen] = useState(() => Boolean(draft));
  const inputId = useId();
  useEffect(() => {
    if (draft) setOpen(true);
  }, [draft]);
  const add = () => onAdd(() => setOpen(false));
  return open ? <SurfaceWell><div className="people-add">
    <StringGadget label={label} value={draft} onChange={onChange} inputProps={{ id: inputId }}
      onKeyDown={(event) => { if (event.key === "Enter" && !busy) add(); }} />
    <Button dense variant="secondary" disabled={!draft.trim() || busy} loading={busy} onClick={add} data-testid={testId}>{actionLabel}</Button>
    <Button dense variant="ghost" disabled={busy} onClick={() => setOpen(false)} aria-expanded={true}>Hide</Button>
  </div></SurfaceWell> : <Button dense variant="ghost" onClick={() => {
    setOpen(true);
    requestAnimationFrame(() => document.getElementById(inputId)?.focus());
  }} aria-expanded={false} data-testid={testId}>{actionLabel}</Button>;
}

/** Betterment D7: Nudge on a row she owes. It drafts the short message
 *  Needs you drafts (`nudgeText`), keeps it as a note and opens its Send
 *  well here; he presses Send (the egress rule). */
function PrepNudge({ task, person, due }: { task: string; person: string; due: string | null }) {
  const [note, setNote] = useState<{ id: string; title: string } | null>(null);
  const [failed, setFailed] = useState(false);
  const started = useRef(false);
  const text = nudgeText(task, person, due);
  useEffect(() => {
    if (started.current) return;
    started.current = true;
    const title = `Nudge: ${task}`;
    void (async () => {
      try {
        const made = await apiFetch<{ note?: { id?: string } }>("/api/notes", {
          method: "POST", json: { title, body_markdown: text, tags: ["nudge"] },
        });
        const id = String(made.note?.id ?? "");
        if (!id) { setFailed(true); return; }
        setNote({ id, title });
      } catch { setFailed(true); }
    })();
  }, [task, text]);
  return <div className="people-nudge" role="region" aria-label={`Nudge: ${task}`} data-testid="prep-nudge">
    <p className="people-nudge-text" data-testid="prep-nudge-text">{text}</p>
    {failed ? <SurfaceState error="The message was not prepared. Nothing was sent. Press Nudge to try again." />
      : note ? <NoteSendWells id={note.id} title={note.title} /> : <SurfaceState loading />}
  </div>;
}

function PrepPane({ relationship, onRefresh, onProtectedFailure, onRead, onNext }: { relationship: RelationshipDetail; onRefresh(): void; onProtectedFailure(cause: unknown): void; onRead?(): void; onNext?(next: PrepNext): void }) {
  const [brief, setBrief] = useState<OneOnOneBrief | null>(null);
  const [failure, setFailure] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [concern, setConcern] = useState<NowConcern>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const recordingState = useDesk((state) => state.recording);
  const { failure: recordingFailure, receipt: recordingReceipt } = useDeskWriteReceipt();
  const [selectedCommitment, setSelectedCommitment] = useState<{ commitment: Commitment; section: "you" | "they" } | null>(null);
  const commitmentOrigin = useRef<HTMLElement | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const [preparedAt] = useState(() => new Date().toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", hour12: false }));
  // The person's record is re-read after each write; the brief follows it.
  // A failed brief read is a state: it stays on screen until Try again (a
  // new `attempt`); a quiet re-read of the record never erases it
  // (peoplePrepB4: "a failed brief read is a named failure with Try again").
  const failedAt = useRef<{ attempt: number; id: string } | null>(null);
  useEffect(() => {
    if (failedAt.current?.attempt === attempt && failedAt.current.id === relationship.id) return;
    failedAt.current = null;
    let live = true;
    void apiFetch<{ brief: OneOnOneBrief }>(`/api/people/relationships/${encodeURIComponent(relationship.id)}/brief`)
      .then((result) => { if (live) { setBrief(result.brief ?? ({ open_commitments: [], agenda_items: [] } as unknown as OneOnOneBrief)); setFailure(""); } })
      .catch((cause) => {
        if (!live) return;
        if (isProtectedFailure(cause) && !isStoreOutage(cause)) { onProtectedFailure(cause); return; }
        failedAt.current = { attempt, id: relationship.id };
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
  // Betterment D7: Nudge on her row prepares a message; he presses Send.
  const [nudging, setNudging] = useState<{ id: string; task: string; due: string | null } | null>(null);
  const toggleNudge = (row: { id: string; task: string; due: string | null }) => setNudging((current) => (current?.id === row.id ? null : row));

  useEffect(() => { if (brief || failure) onRead?.(); }, [brief, failure, onRead]);
  useEffect(() => {
    const event = brief ? composePeoplePrep(brief).nextOneOnOne ?? null : null;
    onNext?.({ at: relationship.next_one_on_one ?? event?.starts_at ?? null, eventId: event?.id ?? null });
  }, [brief, relationship.next_one_on_one, onNext]);
  if (!brief && !failure) return <SurfaceState loading />;

  const base = `/api/people/relationships/${encodeURIComponent(relationship.id)}`;
  const inspectCommitment = (commitment: Commitment, section: "you" | "they") => {
    commitmentOrigin.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    setSelectedCommitment({ commitment, section });
  };
  const closeCommitment = () => {
    setSelectedCommitment(null);
    commitmentOrigin.current?.focus();
  };
  const run = async (key: string, work: () => Promise<unknown>, after?: () => void) => {
    setBusy(key);
    try { await work(); after?.(); onRefresh(); } catch (cause) { onProtectedFailure(cause); } finally { setBusy(null); }
  };
  const addAgenda = (onSaved?: () => void) => {
    const submitted = agendaDraft;
    const body = submitted.trim(); if (!body || busy === "agenda") return;
    void run("agenda", async () => {
      const session = relationship.sessions?.[0] ?? (await apiFetch<{ one_on_one: Session }>(`${base}/one-on-ones`, { method: "POST", json: { visibility: "shared_intent" } })).one_on_one;
      await apiFetch(`/api/people/one-on-ones/${encodeURIComponent(session.id)}/agenda`, { method: "POST", json: { body, visibility: "shared_intent", state: "open", source: { kind: "manual" } } });
    }, () => { if ((keptDraft(`people/1on1/${relationship.id}`) ?? "") === submitted) { forgetAgenda(); onSaved?.(); } });
  };
  // What he owes: the hub's own path (a request he accepts becomes his commitment).
  const addOwe = (onSaved?: () => void) => {
    const submitted = oweDraft;
    const body = submitted.trim(); if (!body || busy === "owe") return;
    void run("owe", async () => {
      const made = await apiFetch<{ request: { id: string } }>(`${base}/requests`, { method: "POST", json: { body, visibility: "shared_intent", source: { kind: "manual" } } });
      await apiFetch(`/api/people/requests/${encodeURIComponent(made.request.id)}/accept`, { method: "POST", json: {} });
    }, () => { if ((keptDraft(`people/request/${relationship.id}`) ?? "") === submitted) { forgetOwe(); onSaved?.(); } });
  };
  const addOwed = (onSaved?: () => void) => {
    const submitted = owedDraft;
    const body = submitted.trim(); if (!body || busy === "owed") return;
    void run("owed", () => apiFetch(`${base}/owed`, { method: "POST", json: { body, visibility: "shared_intent" } }),
      () => { if ((keptDraft(`people/owed/${relationship.id}`) ?? "") === submitted) { forgetOwed(); onSaved?.(); } });
  };
  const done = (id: string) => void run(`done:${id}`, () => apiFetch(`/api/people/commitments/${encodeURIComponent(id)}/transition`, { method: "POST", json: { verb: "done" } }));
  const completeAction = (id: string) => void run(`action-done:${id}`, () => apiFetch("/api/follow-through/complete", { method: "POST", json: { card_id: id, verb: "done", payload: {} } }));
  const removeAgenda = (id: string) => void run(`remove:${id}`, () => apiFetch(`/api/people/agenda/${encodeURIComponent(id)}/transition`, { method: "POST", json: { to: "removed" } }));
  const accept = (id: string) => void run(`accept:${id}`, () => apiFetch(`/api/people/requests/${encodeURIComponent(id)}/accept`, { method: "POST", json: {} }));

  const prep = brief ? composePeoplePrep(brief) : null;
  const nextEvent = prep?.nextOneOnOne ?? null;
  const nextAt = relationship.next_one_on_one ?? nextEvent?.starts_at ?? null;
  const suggestions = !nextAt && prep ? prep.calendarLinkSuggestions : [];
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
  if (brief && prCount) concernRows.push(<li key="prs" className="people-work-row" data-testid="prep-prs-row">
    <span className="people-pill" data-tone={ws?.oldest_waiting_days && ws.oldest_waiting_days >= 3 ? "warn" : "info"} data-testid="prep-prs-label">{prsSummaryLabel(prCount, displayName)}</span>
    <span className="people-raise-tokens">
      {ws?.oldest_waiting_days ? <span className="people-prep-token" data-warning={ws.oldest_waiting_days >= 3 || undefined} data-testid="prep-prs-days">{ws.oldest_waiting_days}+ DAYS</span> : null}
      <span className="people-prep-token" data-testid="prep-prs-numbers">{capTokens((ws?.prs_waiting ?? []).map((pr) => `#${pr.pr_number}`))}</span>
    </span>
    <Button dense variant="ghost" onClick={() => toggle("prs")} aria-expanded={concern === "prs"} data-testid="prep-prs-open">{concern === "prs" ? "Hide" : "Show"}</Button>
  </li>);
  if (brief && assignCount) concernRows.push(<li key="assign" className="people-work-row" data-testid="prep-assignments-row">
    <span className="people-pill" data-tone={(ws?.open_assignments ?? []).some((a) => a.overdue) ? "warn" : "info"} data-testid="prep-assignments-label">{assignCount} {assignCount === 1 ? "ASSIGNMENT" : "ASSIGNMENTS"} OPEN</span>
    <span className="people-raise-tokens">
      <span className="people-prep-token" data-testid="prep-assignments-keys">{capTokens((ws?.open_assignments ?? []).map((a) => a.key).filter(Boolean))}</span>
      {(ws?.open_assignments ?? []).some((a) => a.overdue) ? <span className="people-prep-token" data-warning="true" data-testid="prep-assignments-overdue">OVERDUE</span> : null}
    </span>
    <Button dense variant="ghost" onClick={() => toggle("assignments")} aria-expanded={concern === "assignments"} data-testid="prep-assignments-open">{concern === "assignments" ? "Hide" : "Show"}</Button>
  </li>);
  if (overdue.length) concernRows.push(<li key="overdue" className="people-work-row" data-testid="prep-commitments-row">
    <span className="people-pill" data-tone="danger" data-testid="prep-commitments-label">{overdue.length} {overdue.length === 1 ? "COMMITMENT" : "COMMITMENTS"} OVERDUE</span>
    <span className="people-raise-tokens"><span className="people-prep-token">{overdue[0].body.length > 30 ? overdue[0].body.slice(0, 30) : overdue[0].body}</span></span>
  </li>);
  const agenda = prep?.agenda ?? [];
  const asked = (relationship.requests ?? []).filter((item) => item.state === "requested");
  const owedRows = (relationship.owed_to_you ?? []).filter((item) => (item.state ?? "open") === "open");
  const actions = prep?.openMeetingActions ?? [];
  const myActions = (brief?.i_owe_meeting_actions ?? []).filter((a) => !["done", "dismissed", "completed"].includes(String(a.status ?? "")));
  const firstName = (displayName || "").trim().split(/\s+/)[0] || "They";
  // LAST TIME: the newest meeting of the linked 1:1 series (the brief's
  // linked_meetings, newest first), its decisions and open actions.
  // Betterment D7: the hub's Last time (the last 1:1 with her, else the
  // last meeting she was in) leads; the linked series is the fallback.
  const lastTime = brief?.last_time ?? null;
  const last = brief?.linked_meetings?.[0] ?? null;
  const lastId = lastTime?.meeting_id ?? last?.meeting_id ?? lm?.meeting_id ?? null;
  const lastTitle = lastTime ? (lastTime.one_on_one ? "1:1" : lastTime.title || "Meeting") : last?.title || lm?.title || "Meeting";
  const lastLines: Array<{ key: string; kind: "decision" | "action"; text: string; meta?: string | null }> = lastTime ? [
    ...lastTime.decisions.map((d) => ({ key: `d-${d.id}`, kind: "decision" as const, text: d.decision_text })),
    ...lastTime.points.map((a) => ({ key: `a-${a.id}`, kind: "action" as const, text: a.task, meta: [a.owner, a.status === "done" ? "Done" : null].filter(Boolean).join(" · ") || null })),
  ] : last ? [
    ...last.decisions.map((d) => ({ key: `d-${d.id}`, kind: "decision" as const, text: d.decision_text })),
    ...last.open_action_items.map((a) => ({ key: `a-${a.id}`, kind: "action" as const, text: a.task, meta: [a.owner, a.due ? `BY ${shortDay(a.due)}` : null].filter(Boolean).join(" · ") || null })),
  ] : [];
  const showLast = Boolean(lastId && (lastTime || lastLines.length || (lm && lm.item_count > 0)));
  const lastStarted = lastTime?.started_at ?? last?.started_at ?? null;
  const lastFacts = lastTime ? [
    lastTime.points.length ? (lastTime.points.length === 1 ? "1 point" : `${lastTime.points.length} points`) : null,
    lastTime.decisions.length ? (lastTime.decisions.length === 1 ? "1 decision" : `${lastTime.decisions.length} decisions`) : null,
  ].filter(Boolean).join(" · ") : "";
  // ON THE DESK: what the plaintext desk holds on this person's projects
  // (the brief's memory excerpts; its search words are the person's names).
  const excerpts = (brief?.memory?.excerpts ?? []).filter((e) => (e.title || e.text).trim());

  // Window grammar: sections in sentence case under a hairline, rows edge to
  // edge, no plates; the window's facts in the status bar.
  return <div data-testid="people-prep-lens" className="people-prep">
    {failure ? <span className="people-failure" role="alert" data-testid="people-next-failure">
      <span className="people-failure-label">{failure}</span>
      <Button dense variant="ghost" onClick={() => setAttempt((n) => n + 1)}>Try again</Button>
    </span> : null}

    <section className="people-section" aria-label="Agenda" data-testid="people-next-plate">
      <header className="people-section-head">
        <h3 className="people-section-cap">Agenda</h3>
        {nextAt ? <span className="people-section-fact" data-testid="people-next-1on1">{`Next 1:1 · ${[oneOnOneWhen(nextAt), until].filter(Boolean).join(" · ")}`}</span> : null}
      </header>
      {nextAt ? <div className="people-row people-next-event">
        <span className="people-row-glyph" aria-hidden="true"><img src={PERSON_SPRITE} alt="" draggable={false} /></span>
        <span className="people-row-words">{nextTitle}</span>
        {nextEvent?.source_label ? <span className="people-row-meta">{nextEvent.source_label}</span> : null}
      </div> : suggestions.length && prep ? <LinkSuggestions relationship={relationship} prep={prep} onLinked={onRefresh} onProtectedFailure={onProtectedFailure} testId="prep-link-suggestion" />
        : brief ? <div className="people-row people-next-none"><span className="people-row-meta">No 1:1 planned</span></div> : null}
      {prep?.projects.length ? <div className="people-row people-projects" data-testid="prep-projects">
        {prep.projects.map((project) => <Button key={project.id} variant="chrome" className="people-link" onClick={refOpener(`project:${project.id}`) ?? undefined}>{project.name}</Button>)}
      </div> : null}
      {brief ? <ol className="people-rows" data-testid="prep-to-raise">
        {agenda.map((item, index) => <li key={item.id} className="people-row people-raise-row" data-testid="prep-agenda">
          <span className="people-raise-n" aria-hidden="true">{index + 1}</span>
          <span className="people-raise-words">{item.body}</span>
          {item.rolled_from_id ? <span className="people-row-meta">Rolled</span> : null}
          <Button dense variant="ghost" className="people-raise-remove" aria-label={`Remove ${item.body}`} loading={busy === `remove:${item.id}`} onClick={() => removeAgenda(item.id)}>Remove</Button>
        </li>)}
      </ol> : null}
      <div className="people-row people-add-line">
        <PrepAddWell key={relationship.id} label="Add to the agenda" draft={agendaDraft} onChange={setAgendaDraft} onAdd={addAgenda} busy={busy === "agenda"} actionLabel="Add to agenda" testId="people-add-agenda" />
      </div>
    </section>

    {/* Betterment D7: what she owes me (with Nudge) and what I owe her,
        named with the person's name, side by side when there is room. */}
    <section className="people-section people-commitments" aria-label="Commitments">
      <header className="people-section-head"><h3 className="people-section-cap">Commitments</h3></header>
      <div className="people-owe-grid">
        <div className="people-owe" data-testid="people-they-owe">
          <h3 className="people-owe-cap">{`${firstName} owes me`}{owedRows.length + actions.length ? <b>{owedRows.length + actions.length}</b> : null}</h3>
          {owedRows.length || actions.length ? <ul className="people-rows" data-testid="prep-owed">
            {owedRows.map((item) => <PlateRow key={item.id} title={item.body}
              onTitle={() => inspectCommitment(item, "they")}
              meta={item.due ? <DuePill due={item.due} /> : undefined}
              verb={<span className="people-plate-verbs">
                <Button dense variant="ghost" aria-expanded={nudging?.id === item.id} onClick={() => toggleNudge({ id: item.id, task: item.body, due: item.due ?? null })}>Nudge</Button>
                <Button dense variant="ghost" loading={busy === `done:${item.id}`} onClick={() => done(item.id)}>Done</Button>
              </span>} />)}
            {actions.map((action) => {
              const sourceRef = action.source_ref || (action.meeting_id ? `meeting:${action.meeting_id}` : null);
              const sourceName = action.meeting_title
                ? `from ${action.meeting_title}`
                : action.source_type === "thought" ? "from Note" : action.source_type === "meeting" ? "from Meeting" : null;
              return <PlateRow key={action.id} title={action.task}
                onTitle={refOpener(sourceRef) ?? undefined}
                meta={<>{sourceName ? <span>{sourceName}</span> : null}{action.due ? <DuePill due={action.due} /> : null}</>}
                verb={<span className="people-plate-verbs">
                  <Button dense variant="ghost" aria-expanded={nudging?.id === action.id} onClick={() => toggleNudge({ id: action.id, task: action.task, due: action.due })}>Nudge</Button>
                  <Button dense variant="ghost" loading={busy === `action-done:${action.id}`} onClick={() => completeAction(action.id)}>Done</Button>
                </span>} />;
            })}
          </ul> : null}
          {nudging ? <PrepNudge key={nudging.id} task={nudging.task} person={displayName} due={nudging.due} /> : null}
          {selectedCommitment?.section === "they" ? <CommitmentInspector key={selectedCommitment.commitment.id} commitment={selectedCommitment.commitment} onClose={closeCommitment} onRefresh={() => { onRefresh(); setSelectedCommitment(null); }} onProtectedFailure={onProtectedFailure} /> : null}
          <div className="people-row people-add-line">
            <PrepAddWell key={relationship.id} label={`${firstName} owes me`} draft={owedDraft} onChange={setOwedDraft} onAdd={addOwed} busy={busy === "owed"} />
          </div>
        </div>

        <div className="people-owe" data-testid="people-you-owe">
          <h3 className="people-owe-cap">{`I owe ${firstName}`}{youOweRows.length + myActions.length ? <b>{youOweRows.length + myActions.length}</b> : null}</h3>
          {youOweRows.length || asked.length || myActions.length ? <ul className="people-rows" data-testid="prep-you-owe">
            {asked.map((item) => <PlateRow key={item.id} testId="people-asked" title={item.body}
              meta={<span className="people-state" data-tone="info"><span className="kit-dot" data-tone="info" aria-hidden="true" />Asked of you</span>}
              verb={<Button dense variant="ghost" loading={busy === `accept:${item.id}`} onClick={() => accept(item.id)}>Accept</Button>} />)}
            {youOweRows.map((item) => <PlateRow key={item.id} title={item.body}
              onTitle={() => inspectCommitment(item, "you")}
              meta={item.due || item.execution_links?.length ? <>{item.due ? <DuePill due={item.due} /> : null}{item.execution_links?.length ? <span>On an automation</span> : null}</> : undefined}
              verb={<Button dense variant="ghost" loading={busy === `done:${item.id}`} onClick={() => done(item.id)}>Done</Button>} />)}
            {myActions.map((action) => <PlateRow key={action.id} testId="prep-i-owe-action" title={action.task}
              onTitle={refOpener(action.meeting_id ? `meeting:${action.meeting_id}` : null) ?? undefined}
              meta={<>{action.meeting_title ? <span>{`from ${action.meeting_title}`}</span> : null}{action.due ? <DuePill due={action.due} /> : null}</>}
              verb={<Button dense variant="ghost" loading={busy === `action-done:${action.id}`} onClick={() => completeAction(action.id)}>Done</Button>} />)}
          </ul> : null}
          {selectedCommitment?.section === "you" ? <CommitmentInspector key={selectedCommitment.commitment.id} commitment={selectedCommitment.commitment} onClose={closeCommitment} onRefresh={() => { onRefresh(); setSelectedCommitment(null); }} onProtectedFailure={onProtectedFailure} /> : null}
          <div className="people-row people-add-line">
            <PrepAddWell key={relationship.id} label={`I owe ${firstName}`} draft={oweDraft} onChange={setOweDraft} onAdd={addOwe} busy={busy === "owe"} />
          </div>
        </div>
      </div>
    </section>

    {showLast && lastId ? <section className="people-section" aria-label="Last time" data-testid="prep-last">
      <header className="people-section-head">
        <h3 className="people-section-cap">Last time</h3>
        <span className="people-section-fact" data-testid="prep-meeting-row">
          <span className="people-plate-title" data-testid="prep-last-title">{lastStarted ? `${lastTitle} on ${dayLabel(lastStarted)}` : lastTitle}</span>
          {lastTime ? (lastFacts ? <span data-testid="prep-last-facts">{lastFacts}</span> : null) : lm && lm.item_count > 0 ? <span className="people-prep-token" data-testid="prep-meeting-items">{lm.item_count} {lm.item_count === 1 ? "ITEM" : "ITEMS"}</span> : null}
          {lm && lm.open_count > 0 ? <span className="people-prep-token" data-testid="prep-meeting-open-count">{lm.open_count} OPEN</span> : null}
          <Button dense variant="ghost" onClick={() => openSourceRef(`meeting:${lastId}`)} data-testid="prep-meeting-open">Open meeting</Button>
        </span>
      </header>
      {lastLines.length ? <ul className="people-rows">
        {lastLines.slice(0, 4).map((line) => <PlateRow key={line.key} title={line.text}
          meta={<><span className="people-state" data-tone={line.kind === "decision" ? "ok" : "info"}><span className="kit-dot" data-tone={line.kind === "decision" ? "ok" : "info"} aria-hidden="true" />{line.kind === "decision" ? "Decision" : "Action"}</span>{line.meta ? <span>{line.meta}</span> : null}</>} />)}
      </ul> : null}
      {lastLines.length > 4 ? <div className="people-row"><span className="people-row-meta">{`${lastLines.length - 4} more in the meeting`}</span></div> : null}
    </section> : null}

    {concernRows.length ? <section className="people-section" aria-label="Open work" data-testid="prep-summary-rows">
      <header className="people-section-head"><h3 className="people-section-cap">Open work</h3></header>
      <ul className="people-rows people-work-rows">{concernRows}</ul>
      {concern && brief ? <ConcernDetail concern={concern} brief={brief} /> : null}
    </section> : null}

    {excerpts.length ? <section className="people-section" aria-label="On the desk" data-testid="prep-memory">
      <header className="people-section-head"><h3 className="people-section-cap">On the desk</h3></header>
      <ul className="people-rows">
        {excerpts.slice(0, 4).map((e, index) => <PlateRow key={e.ref || `${e.kind}-${index}`} title={e.title || e.text}
          onTitle={e.ref ? () => openSourceRef(e.ref) : undefined}
          meta={<><span>{kindWord(e.kind)}</span>{e.title && e.text ? <span className="people-excerpt">{e.text}</span> : null}</>} />)}
      </ul>
    </section> : null}

    {/* The window's status bar: the next 1:1, Encrypted, when it was prepared. */}
    <StatusBar
      data-testid="person-status"
      items={[
        nextAt ? { key: "next", lamp: until ? "ask" as const : "info" as const, text: [`1:1 ${lowerDay(oneOnOneWhen(nextAt))}`, until].filter(Boolean).join(" · ") } : null,
        { key: "lock", lamp: "ok" as const, text: <span className="people-lock" title="Encrypted · Local storage · Notes only" data-testid="person-lock">Encrypted</span> },
        { key: "receipt", text: recordingFailure ? recordingReceipt : <span className="people-prep-receipt" data-testid="prep-receipt">{`Prepared ${preparedAt}`}</span> },
      ]}
    />
  </div>;
}
/** PHILO-17 ALIVE: what one roster row says, from the person's record. */
type RowFacts = { next: string | null; known: boolean; youOwe: number; owesYou: number };
type RosterNext = { startsAt: string; title: string };
/** Each person's soonest upcoming 1:1 from the Door's calendar rows. */
function nextOneOnOnes(upcoming: Array<Record<string, unknown>>): Record<string, RosterNext> {
  const out: Record<string, RosterNext> = {};
  const now = Date.now();
  for (const row of upcoming) {
    const id = String(row.person_relationship_id ?? "");
    const startsAt = String(row.starts_at ?? "");
    const at = wireDate(startsAt)?.getTime();
    if (!id || at === undefined || !Number.isFinite(at)) continue;
    const ends = wireDate(String(row.ends_at ?? ""))?.getTime() ?? at;
    if (ends < now) continue;
    const current = out[id] ? wireDate(out[id].startsAt)?.getTime() ?? Infinity : Infinity;
    if (at < current) out[id] = { startsAt, title: String(row.title || row.event_title || "1:1") };
  }
  return out;
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
function CalendarLinkSection({ relationship, onRefresh, onProtectedFailure, upcomingEvents, calendarRead }: { relationship: RelationshipDetail; onRefresh(): void; onProtectedFailure(cause: unknown): void; upcomingEvents: UpcomingEvent[]; calendarRead: CalendarRead }) {
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
        {calendarRead.loading ? <SurfaceState loading /> : calendarRead.error ? <SurfaceState error={calendarRead.error} onRetry={calendarRead.retry} /> : sorted.all.length ? <SurfaceRows>{sorted.all.map((ev) => {
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

function ContextLens({ relationship, onRefresh, onProtectedFailure, upcomingEvents = [], calendarRead, initialLinksOpen = false, noteRequest = 0, noteVerbOutside = false }: { relationship: RelationshipDetail; onRefresh(): void; onProtectedFailure(cause: unknown): void; upcomingEvents?: UpcomingEvent[]; calendarRead: CalendarRead; initialLinksOpen?: boolean; noteRequest?: number; noteVerbOutside?: boolean }) {
  const draftKey = `people/context/${relationship.id}`;
  const [topic, setTopic, forgetTopic] = useDeskDraft(`${draftKey}/topic`);
  const [body, setBody, forgetBody] = useDeskDraft(`${draftKey}/body`);
  const [draftVisibility, setVisibility, forgetVisibility] = useDeskDraft(`${draftKey}/visibility`);
  const visibility: Visibility = draftVisibility === "shared_intent" ? "shared_intent" : "leader_private";
  const [addingNote, setAddingNote] = useState(() => Boolean(topic || body || draftVisibility));
  // The toolbar's Add note (the person window) opens the well here.
  useEffect(() => { if (noteRequest) setAddingNote(true); }, [noteRequest]);
  const [busy, setBusy] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  useEffect(() => { void apiFetch<{ projects?: Project[] }>("/api/projects").then((result) => { const rows = result.projects ?? []; setProjects(rows); setProjectId((current) => current || rows[0]?.id || ""); }).catch(onProtectedFailure); }, [relationship.id]);
  const add = async () => {
    if (!body.trim() || busy) return;
    const submitted = { topic, body, draftVisibility };
    setBusy(true);
    try {
      await apiFetch(`/api/people/relationships/${encodeURIComponent(relationship.id)}/notes`, { method: "POST", json: { topic: topic.trim(), body: body.trim(), visibility } });
      // A newer note typed while this write was pending belongs to the next Add.
      if ((keptDraft(`${draftKey}/topic`) ?? "") === submitted.topic
          && (keptDraft(`${draftKey}/body`) ?? "") === submitted.body
          && (keptDraft(`${draftKey}/visibility`) ?? "") === submitted.draftVisibility) {
        forgetTopic(); forgetBody(); forgetVisibility(); setAddingNote(false);
      }
      onRefresh();
    } catch (cause) { onProtectedFailure(cause); } finally { setBusy(false); }
  };
  const linkProject = async () => { if (!projectId) return; try { await apiFetch(`/api/people/relationships/${encodeURIComponent(relationship.id)}/projects/${encodeURIComponent(projectId)}`, { method: "POST", json: {} }); onRefresh(); } catch (cause) { onProtectedFailure(cause); } };
  const unlinkProject = async (id: string) => { try { await apiFetch(`/api/people/relationships/${encodeURIComponent(relationship.id)}/projects/${encodeURIComponent(id)}`, { method: "DELETE" }); onRefresh(); } catch (cause) { onProtectedFailure(cause); } };
  const linkedProjects = projects.filter((project) => relationship.project_refs?.includes(project.id));
  return <>
    <SurfaceSection label="Notes" actions={!addingNote && !noteVerbOutside ? <Button dense onClick={() => setAddingNote(true)}>Add note</Button> : undefined}>
      {!(relationship.notes ?? []).length ? <SurfaceState empty emptyLabel="No notes" /> : <SurfaceLedger cols="room"><ul className="surface-ledger-rows">{(relationship.notes ?? []).map((note) => <SurfaceLedgerRow key={note.id} wrap primary={<span className="people-context-note">{note.topic ? <span className="people-context-note-topic">{note.topic}</span> : null}<span className="people-context-note-body">{note.body}</span></span>} cells={<span className="surface-token">{note.visibility === "leader_private" ? "Leader private" : "Shared"}</span>} />)}</ul></SurfaceLedger>}
      {addingNote ? <SurfaceWell head="Add note"><div className="people-context-add"><StringGadget label="Topic" value={topic} onChange={setTopic} placeholder="Topic (optional)" /><PadGadget label="Note" value={body} onChange={setBody} placeholder="Context worth remembering" rows={3} /><CycleGadget label="Visibility" value={visibility} onChange={setVisibility} options={[{ value: "leader_private", label: "Leader private" }, { value: "shared_intent", label: "Shared" }]} /><Button dense variant="ghost" onClick={() => setAddingNote(false)}>Close</Button><Button dense variant="primary" disabled={!body.trim() || busy} loading={busy} onClick={() => void add()}>Add note</Button></div></SurfaceWell> : null}
    </SurfaceSection>
    <SurfaceSection label="Projects">{linkedProjects.length ? <SurfaceRows>{linkedProjects.map((project) => <SurfaceRow key={project.id} title={project.name} detail={project.description} onOpen={() => openProjectRoom(project.id)} />)}</SurfaceRows> : <SurfaceState empty emptyLabel="No linked projects" />}</SurfaceSection>
    <Disclosure label="Links" defaultOpen={initialLinksOpen}>
      <SurfaceSection label="Projects"><div className="people-project-link"><CycleGadget label="Project" value={projectId} onChange={setProjectId} options={projects.map((project) => ({ value: project.id, label: project.name }))} /><Button dense disabled={!projectId || relationship.project_refs?.includes(projectId)} onClick={() => void linkProject()}>Link</Button></div>{linkedProjects.length ? <SurfaceRows>{linkedProjects.map((project) => <SurfaceRow key={project.id} title={project.name} verbs={<Button dense variant="ghost" onClick={() => void unlinkProject(project.id)}>Unlink</Button>} />)}</SurfaceRows> : null}</SurfaceSection>
      <CalendarLinkSection relationship={relationship} onRefresh={onRefresh} onProtectedFailure={onProtectedFailure} upcomingEvents={upcomingEvents} calendarRead={calendarRead} />
      <OwnerAliasSection relationship={relationship} onRefresh={onRefresh} onProtectedFailure={onProtectedFailure} />
    </Disclosure>
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
  return <div className="people-commitment-inspector"><div className="people-inspector-head"><strong>Commitment</strong><Button dense variant="ghost" onClick={onClose}>Close</Button></div><div className="people-commitment-body">{commitment.body}</div>{linked ? <SurfaceRows><SurfaceRow title={linked.result ? "Output ready" : "Automation item"} detail={linked.result || `Status: ${linked.status}`} meta={linked.status} onOpen={() => openSurfaceOr("open-workbenches", "/workbenches", `workbench:${linked.workbench_id}`)} /></SurfaceRows> : <div className="people-delegate"><CycleGadget label="Automation" value={workbenchId} onChange={setWorkbenchId} options={workbenches.map((workbench) => ({ value: workbench.id, label: workbench.name }))} /><Button dense disabled={!workbenchId || busy} onClick={() => void send()}>Send to automation</Button></div>}<div className="people-satisfy"><StringGadget label="Satisfaction note" value={rationale} onChange={setRationale} placeholder="What fulfilled the commitment?" /><Button dense variant="primary" disabled={busy} onClick={() => void satisfy()}>Mark satisfied</Button></div></div>;
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
