/* People is a selection list; the person editor keeps its own window. */
import { StringGadget, SurfaceState, StatusBar, countWords, PreferencePane, ListPane, PaneActions, PaneInspector, InspectorForm, InspectorFacts, GadgetRow, CycleGadget, type ListVerb } from "../../desk/surface";

import { PersonPages } from "../../desk/standingPages";
import { wireDate } from "../../desk/surface/format";
import { useCallback, useEffect, useRef, useState } from "react";
import type { CoreProps } from "./core-types";
import { Button } from "../../components/signal/Signal";
import * as hub from "../../desk/people/api";
import { failureTitle } from "../../desk/surface/plainFailure";
import { openSurfaceOr } from "../../desk/shell";
import { openPerson, PERSON_OPEN_EVENT, type PersonOpenRequest } from "../../desk/openObject";
import { peekPersonLens, takePersonLens } from "../../desk/objectWindows";
import { announceTaskReturn, taskFocusPending } from "../../desk/returnToTask";
import { PEOPLE_CHANGE_KINDS, useOnDeskChanged } from "../../desk/useDeskChangedRefresh";
import { keepPlace, keptPlace } from "../../desk/deskMemory";
import { useWindowInterior } from "../../desk/surface/interior";
import { PeopleNotHere, PeopleReadFailed } from "../../desk/people/PeopleReadFailed";
import { PeopleRail, type RailPerson } from "../../desk/people/PeopleRail";
import { useWindowTitle } from "../../desk/surface/title";
import "./people.css";
import { RelationshipKind, Lens, Readiness, Relationship, Suggestion, RelationshipDetail, stateOf, readinessFace, readinessForError, isStoreOutage, isProtectedFailure, PEOPLE_PERSON_PLACE, readWhole, RosterNext, nextOneOnOnes, ROLE_CHOICES, oneOnOneWhen, lowerDay, sentence, relationshipLabel } from "./peopleModel";
import { RelationshipPane } from "./PeoplePerson";
export { RelationshipPane } from "./PeoplePerson";
export { prsSummaryLabel, capTokens } from "./peopleModel";
export function PeopleCore({ scope }: CoreProps) {
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
  const [errorTitle, setErrorTitle] = useState("");
  const [busy, setBusy] = useState(false);
  const requestedScope = scope?.startsWith("people:") ? scope.slice("people:".length) : null;
  // HS-200-14 (AC4): `people:project:<id>` scopes the rail to the people
  // linked to that Project; `people:<relationship>[:<lens>]` picks a person.
  const requestedProjectId = requestedScope?.startsWith("project:") ? requestedScope.slice("project:".length) : null;
  const relationshipScope = requestedProjectId ? null : requestedScope;
  const requestedRelationshipId = relationshipScope?.includes(":") ? relationshipScope.split(":")[0] : relationshipScope;
  const [projectFilter, setProjectFilter] = useState<string | null>(requestedProjectId);

  // Add person opens the shared inspector below the list.
  const [adding, setAdding] = useState(false);
  // Betterment D6: the people his work names that People does not hold.
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [suggestionBusy, setSuggestionBusy] = useState("");
  const readSuggestions = useCallback(async () => {
    try {
      const read = await hub.readSuggestions<Suggestion>();
      setSuggestions(read.suggestions ?? []);
    } catch { /* the last read stays; the roster's own read names a failure */ }
  }, []);
  const selectSeq = useRef(0);
  const clearProtected = useCallback(() => {
    selectSeq.current += 1;
    setRelationships([]);
    setSelectedId(null);
    setDetail(null);
    setNewName("");
  }, []);
  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const next = await hub.readReadiness<Readiness>();
      setReadiness(next);
      // Betterment D6: no Set up step. With no store yet the roster is
      // empty and the suggestions still come; the first Add makes the store.
      if (stateOf(next) === "unconfigured") { clearProtected(); void readSuggestions(); return; }
      if (stateOf(next) !== "ready") { clearProtected(); return; }
      const list = await hub.readRoster<Relationship>();
      setRelationships(list.relationships ?? []);
      void readSuggestions();
    } catch (cause) {
      clearProtected();
      setReadiness(readinessForError(cause));
      setError("Could not load people · Nothing changed · Try again"); setErrorTitle(failureTitle(cause));
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
        const list = await hub.readRoster<Relationship>();
        if (!newest()) return;
        setRelationships(list.relationships ?? []);
        const id = followed.current.selectedId;
        if (!id) return;
        const whole = await readWhole(id);
        if (newest() && followed.current.selectedId === id) setDetail(whole);
      } catch { /* the last read stays */ }
    })();
  });
  // HS-200-14 (AC4): the way back to the task. When this window was
  // opened from a Room verb (`rememberTaskFocus` on the way in), closing
  // it announces the return: the Room re-reads and focus lands back on
  // the verb the owner left -- and only then (the do-not-steal rule).
  useEffect(() => () => { if (taskFocusPending()) announceTaskReturn(); }, []);

  // The rail's facts: the owed counts ride the roster read (`?counts=1`);
  // the next 1:1 is the Door's upcoming calendar events that carry a
  // person (ONE read for the whole roster, again when the list changes).
  const rosterKey = relationships.map((row) => row.id).join("|");
  const [nextByPerson, setNextByPerson] = useState<Record<string, RosterNext> | null>(null);
  // The roster whose next-1:1 read has ended (read or failed). Until it ends
  // the rail says it is reading (the desk sweep's still fence).
  const [nextReadFor, setNextReadFor] = useState<string | null>(null);
  useEffect(() => {
    if (!rosterKey) return;
    let live = true;
    void hub.readUpcoming<Record<string, unknown>>()
      .then((door) => { if (live) { setNextByPerson(nextOneOnOnes(door.upcoming ?? [])); setNextReadFor(rosterKey); } })
      .catch(() => { if (live) { setNextByPerson(null); setNextReadFor(rosterKey); } });
    return () => { live = false; };
  }, [rosterKey]);
  const nextReading = Boolean(rosterKey) && nextReadFor !== rosterKey;

  const unconfigured = stateOf(readiness) === "unconfigured";
  const unavailable = stateOf(readiness) !== "ready" && !unconfigured;
  const openSettings = () => openSurfaceOr("configure-settings", "/settings", "people-security");
  const recover = () => {
    if (stateOf(readiness) === "locked" || stateOf(readiness) === "unavailable") { void load(); return; }
    if (stateOf(readiness) !== "unconfigured") { openSettings(); return; }
    void hub.setupPeople().then(() => load()).catch((cause) => protectedFailure(cause));
  };
  // Only the newest selection read may land.
  const select = async (id: string) => {
    // PHILO-13-04 fix round (Astra counsel P2): a standing failure leaves only
    // when this read lands; it is never cleared before the person is back.
    const mine = ++selectSeq.current;
    setSelectedId(id); setDetail(null); setPickedSuggestion(null);
    // PHILO-13-07 (B2): the person is this window's place; it returns after
    // a reload and a close.
    keepPlace(PEOPLE_PERSON_PLACE, id);
    try {
      const whole = await readWhole(id);
      if (selectSeq.current !== mine || whole.id !== id) return;
      setDetail(whole);
      setError("");
    } catch (cause) { if (selectSeq.current === mine) protectedFailure(cause); }
  };
  const back = () => { selectSeq.current += 1; setSelectedId(null); setDetail(null); keepPlace(PEOPLE_PERSON_PLACE, ""); };
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
  // PHILO-17: Add stays on the rail with the cursor in Name, so three
  // reports are Name, Add three times. A quiet roster re-read (no loading
  // state) keeps the input on screen.
  const createRelationship = async () => {
    const display_name = newName.trim(); if (!display_name || busy) return;
    if (duplicate && duplicateWarned !== nameKey(display_name)) { setDuplicateWarned(nameKey(display_name)); return; }
    setBusy(true); setError("");
    try {
      await hub.createPerson(display_name, newKind);
      if (unconfigured) setReadiness({ readiness: "ready", store: "encrypted" });
      setNewName(""); setDuplicateWarned("");
      const list = await hub.readRoster<Relationship>();
      setRelationships(list.relationships ?? []);
    } catch (cause) { protectedFailure(cause); } finally {
      setBusy(false);
      document.getElementById("people-new-relationship")?.focus();
    }
  };
  // Betterment D6: Add makes the person in one press (the full name, the
  // kind, the spoken name and the 1:1 series ride along); Hide takes the
  // name off for good.
  const [pickedSuggestion, setPickedSuggestion] = useState<string | null>(null);
  const addSuggestion = async (suggestion: Suggestion) => {
    setSuggestionBusy(suggestion.key); setError("");
    try {
      await hub.addSuggestion(suggestion.key);
      setSuggestions((rows) => rows.filter((row) => row.key !== suggestion.key));
      await load();
    } catch (cause) { protectedFailure(cause); } finally { setSuggestionBusy(""); }
  };
  const hideSuggestion = async (suggestion: Suggestion) => {
    setSuggestionBusy(suggestion.key); setError("");
    try {
      await hub.hideSuggestion(suggestion.key);
      setSuggestions((rows) => rows.filter((row) => row.key !== suggestion.key));
    } catch (cause) { protectedFailure(cause); } finally { setSuggestionBusy(""); }
  };
  function protectedFailure(cause: unknown, mayHaveSaved = false) {
    if (mayHaveSaved) {
      // HS-S33: an Add whose write may have landed lost its owner or key.
      clearProtected(); setReadiness(readinessForError(cause));
      setError("Could not read the people store · A promise may be saved · Check again when the store is back"); setErrorTitle(failureTitle(cause));
      return;
    }
    if (isStoreOutage(cause) && (selectedId || relationships.length)) {
      setError("Could not read the people store · What is on screen stays · Try again"); setErrorTitle(failureTitle(cause));
      return;
    }
    if (!isProtectedFailure(cause)) {
      setError("Could not do that · Nothing changed · Try again"); setErrorTitle(failureTitle(cause));
      return;
    }
    clearProtected();
    setReadiness(readinessForError(cause));
    setError("Could not read the people store · Nothing changed · Try again"); setErrorTitle(failureTitle(cause));
  }
  const selected = detail ?? relationships.find((row) => row.id === selectedId) ?? null;
  useWindowInterior("list");
  const [query, setQuery] = useState("");
  const openAdd = () => { setAdding(true); window.setTimeout(() => document.getElementById("people-new-relationship")?.focus(), 0); };

  if (loading) return <SurfaceState loading data-testid="people-loading" />;
  if (unavailable) {
    const state = stateOf(readiness);
    // Betterment daily D8: People cannot hold a key on this Mac: one line, no verb.
    if (state === "no_key_store") return <PreferencePane label="People state"><PeopleNotHere /></PreferencePane>;
    // Betterment D6: a People read that failed is one line in place.
    if (state === "unavailable" || state === "locked") return <PreferencePane label="People state"><PeopleReadFailed onRetry={() => void load()} detail={error} /></PreferencePane>;
    const face = readinessFace(state);
    return <PreferencePane label="People state"><div data-testid="people-joy-state"><PaneActions>
      <Button variant="primary" onClick={recover} data-testid="people-joy-action">{face.action}</Button>
      <span>{face.label}</span>
      {error ? <span className="sr-only">{error}</span> : null}
    </PaneActions></div></PreferencePane>;
  }
  // PHILO-13-04 (A3): the failure is ONE row that stays on screen while he
  // is down in a fold; the person and any unsent draft stay under it
  // (J3-06). Try again re-reads the person (or the roster).
  const failureRow = error ? (
    <div role="alert" data-testid="people-failure"><PaneActions>
      <span title={errorTitle || undefined}>{adding && newName.trim() ? "Person could not be added · Name kept · Try again" : "People could not be read · Last view kept · Try again"}</span>
      <span className="sr-only">{error}</span>
      <Button dense variant="ghost" onClick={() => void (adding && newName.trim() ? createRelationship() : selectedId && !adding ? select(selectedId) : load())}>Try again</Button>
    </PaneActions></div>
  ) : null;

  const scoped = projectFilter ? relationships.filter((r) => (r.project_refs ?? []).includes(projectFilter)) : relationships;
  const scopedOut = projectFilter ? relationships.length - scoped.length : 0;
  const needle = nameKey(query);
  const shownPeople = needle ? scoped.filter((r) => nameKey(r.display_name).includes(needle)) : scoped;
  const shownSuggestions = projectFilter ? [] : needle ? suggestions.filter((s) => nameKey(s.name).includes(needle)) : suggestions;
  // The soonest 1:1 this week stays in the status bar.
  const weekEnd = Date.now() + 7 * 86_400_000;
  const soonest = scoped
    .map((row) => ({ row, next: nextByPerson?.[row.id] }))
    .filter((x): x is { row: Relationship; next: RosterNext } => Boolean(x.next && (wireDate(x.next.startsAt)?.getTime() ?? Infinity) <= weekEnd))
    .sort((a, b) => (wireDate(a.next.startsAt)?.getTime() ?? 0) - (wireDate(b.next.startsAt)?.getTime() ?? 0))[0] ?? null;
  const railPeople: RailPerson[] = shownPeople.map((relationship) => {
    const next = nextByPerson?.[relationship.id]?.startsAt ?? relationship.next_one_on_one ?? null;
    return {
      id: relationship.id, name: relationship.display_name, role: relationshipLabel(relationship.relationship_kind),
      next: next ? oneOnOneWhen(next) : "",
      youOwe: Number(relationship.you_owe_count) || 0, owesYou: Number(relationship.owes_you_count) || 0,
    };
  });
  const suggestion = pickedSuggestion ? shownSuggestions.find((s) => `suggestion:${s.key}` === pickedSuggestion) ?? null : null;
  const firstName = (name: string) => name.trim().split(/\s+/)[0] || name;
  const empty = !relationships.length && !suggestions.length && !projectFilter && !adding;

  const selectedNext = selected ? nextByPerson?.[selected.id]?.startsAt ?? selected.next_one_on_one : null;
  const personSelected = (row: { kind: string } | null) => row?.kind === "person";
  const picked = selectedId ?? pickedSuggestion;
  const selectedSuggestion = (id: string | undefined) => suggestions.find((item) => `suggestion:${item.key}` === id);
  const verbs: ListVerb[] = [
    { id: "add-person", label: "Add person", key: "n", run: openAdd },
    { id: "open", label: "Open", key: "Enter", enabled: personSelected, run: (row) => { if (row) openPerson(row.id); } },
    { id: "prep", label: "Prep 1:1", key: "p", enabled: personSelected, run: (row) => { if (row) openPerson(row.id, "prep"); } },
    ...(suggestions.length ? [{ id: "add-suggestion", label: "Add from meetings", key: "a", enabled: (row) => row?.kind === "suggestion" && !suggestionBusy, run: (row) => { const item = selectedSuggestion(row?.id); if (item) void addSuggestion(item); } },
    { id: "hide-suggestion", label: "Hide", key: "Delete", enabled: (row) => row?.kind === "suggestion" && !suggestionBusy, run: (row) => { const item = selectedSuggestion(row?.id); if (item) void hideSuggestion(item); } },
    ] as ListVerb[] : []),
    ...(projectFilter && scopedOut ? [{ id: "everyone", label: `${scopedOut} more · Everyone`, run: () => setProjectFilter(null) }] : []),
  ];
  return <PreferencePane label="People" testId="people-roster">
    {nextReading ? <span hidden aria-busy="true" data-testid="people-next-reading" /> : null}
    <ListPane label="Selected person" previewTestId="people-summary" list={<>
      <PeopleRail people={railPeople} suggestions={shownSuggestions.map((s) => ({ key: s.key, name: s.name, source: sentence(suggestionSource(s)) }))}
      picked={picked} query={query} onQuery={(value) => { setQuery(value); back(); setPickedSuggestion(null); }} verbs={verbs}
      onPick={(id) => { if (id.startsWith("suggestion:")) { back(); setPickedSuggestion(id); } else if (id !== selectedId) void select(id); }} />
    {failureRow}
    </>}>
    {adding ? <PaneInspector label="New person">
      <InspectorForm testId="people-add-row" completion={{ cancel: () => setAdding(false), primary: { label: duplicateShown ? "Add again" : "Add", disabled: !newName.trim() || busy, busy, run: () => void createRelationship() } }} notice={duplicateShown ? <span role="status" data-testid="people-duplicate">{duplicateShown.display_name} · Already here</span> : null}>
        <GadgetRow label="Name"><StringGadget label="Add person" value={newName} onChange={setNewName} placeholder="Name" inputProps={{ id: "people-new-relationship" }} onKeyDown={(event) => { if (event.key === "Enter") void createRelationship(); if (event.key === "Escape") setAdding(false); }} /></GadgetRow>
        <GadgetRow label="Relationship"><CycleGadget label="Relationship" value={newKind} options={ROLE_CHOICES} onChange={(value) => setNewKind(value as RelationshipKind)} /></GadgetRow>
      </InspectorForm>
    </PaneInspector> : <>
      {selected ? <InspectorFacts name={selected.display_name} nameTestId="people-summary-name" rows={[
        {label: "Relationship", value: relationshipLabel(selected.relationship_kind)},
        {label: "Next 1:1", value: selectedNext ? oneOnOneWhen(selectedNext) : ""},
        ...(!detail ? [{label: "Commitments", value: error ? "Commitments not read" : "Reading commitments…"}] : [
          ...(detail.commitments ?? []).filter(item => (item.state ?? "open") === "open" || item.state === "in_progress").map(item => ({key: item.id, label: "You owe", value: item.body})),
          ...(detail.owed_to_you ?? []).filter(item => (item.state ?? "open") === "open" || item.state === "in_progress").map(item => ({key: item.id, label: "Owed to you", value: item.body})),
          ...(![...(detail.commitments ?? []), ...(detail.owed_to_you ?? [])].some(item => (item.state ?? "open") === "open" || item.state === "in_progress") ? [{label: "Commitments", value: "No open commitments"}] : []),
        ]),
      ]} /> : suggestion ? <InspectorFacts name={suggestion.name} rows={[{label:"Name",value:suggestion.name},{label:"From",value:sentence(suggestionSource(suggestion))}]} />
        : <span data-testid={empty ? "people-empty-roster" : projectFilter && !scoped.length ? "people-roster-none-linked" : undefined}>{empty ? "People you meet appear here." : projectFilter && !scoped.length ? "No one linked yet" : needle && !shownPeople.length && !shownSuggestions.length ? "No names match" : "Select a person"}</span>}
    </>}
    </ListPane>
    <StatusBar data-testid="people-status" items={[
      { key: "count", testId: "people-count", text: projectFilter ? countWords(scoped.length, "on this project", "on this project") : countWords(relationships.length, "person", "people") },
      soonest ? { key: "next", testId: "people-roster-next", text: `1:1 with ${firstName(soonest.row.display_name)} ${lowerDay(oneOnOneWhen(soonest.next.startsAt))}` } : null,
      { key: "suggested", testId: "people-suggestions", text: projectFilter ? null : countWords(suggestions.length, "from your meetings", "from your meetings") },
    ]} />
  </PreferencePane>;
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
  const [errorTitle, setErrorTitle] = useState("");
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
      const next = await hub.readReadiness<Readiness>();
      setReadiness(next);
      if (stateOf(next) !== "ready") { setDetail(null); return; }
      setDetail(await readWhole(relationshipId));
      setError("");
    } catch (cause) {
      if (isProtectedFailure(cause) && !isStoreOutage(cause)) { setDetail(null); setReadiness(readinessForError(cause)); }
      setError(detail ? "Could not read the people store · What is on screen stays · Try again" : "Could not load this person · Nothing changed · Try again"); setErrorTitle(failureTitle(cause));
    } finally {
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [relationshipId]);
  useEffect(() => { void read(); }, [read]);
  // A write in another window shows here with no reload.
  useOnDeskChanged(() => { if (readiness && stateOf(readiness) === "ready") void read(); }, [
    ...PEOPLE_CHANGE_KINDS, "calendar", "calendar_event",
  ]);
  const protectedFailure = (cause: unknown, mayHaveSaved = false) => {
    if (mayHaveSaved) {
      // HS-S33: an Add whose write may have landed lost its owner or key.
      setDetail(null); setReadiness(readinessForError(cause));
      setError("Could not read the people store · A promise may be saved · Check again when the store is back"); setErrorTitle(failureTitle(cause));
      return;
    }
    if (isProtectedFailure(cause) && !isStoreOutage(cause)) { setDetail(null); setReadiness(readinessForError(cause)); }
    setError("Could not do that · Nothing changed · Try again"); setErrorTitle(failureTitle(cause));
  };
  if (loading && !detail) return <SurfaceState loading />;
  if (readiness && stateOf(readiness) !== "ready") {
    const face = readinessFace(stateOf(readiness));
    return <div className="people-joy-state" data-testid="people-joy-state">
      <Button variant="primary" onClick={() => openSurfaceOr("open-people", "/")} data-testid="people-joy-action">{face.action}</Button>
      <span className="people-joy-line">{face.label}</span>
    </div>;
  }
  // The person window is the RelationshipPane: the mast, the plate, the
  // ledger, the folds and the status bar (the next 1:1, Encrypted).
  return <div className="people-surface person-window" data-testid="person-window">
    {error ? (
      <span className="people-failure" role="alert" data-testid="people-failure">
        <span className="people-failure-label" title={errorTitle || undefined}>{error}</span>
        <Button dense variant="ghost" onClick={() => void read()}>Try again</Button>
      </span>
    ) : null}
    {detail ? (
      <RelationshipPane relationship={detail} initialLens={initialLens} lensRequest={lensRequest}
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
