// Parked: the roster now uses the kit selection list and a plain summary.
/* The People roster and person-window hosts; the selected person is one ledger. */
import { StringGadget, SurfaceState, DotWord, StatusBar, countWords } from "../../desk/surface";

import { PersonPages } from "../../desk/standingPages";
import { wireDate } from "../../desk/surface/format";
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import type { CoreProps } from "./core-types";
import { Button } from "../../components/signal/Signal";
import * as hub from "../../desk/people/api";
import { failureTitle } from "../../desk/surface/plainFailure";
import { openSurfaceOr } from "../../desk/shell";
import { PERSON_OPEN_EVENT, type PersonOpenRequest } from "../../desk/openObject";
import { peekPersonLens, takePersonLens } from "../../desk/objectWindows";
import { announceTaskReturn, taskFocusPending } from "../../desk/returnToTask";
import { PEOPLE_CHANGE_KINDS, useOnDeskChanged } from "../../desk/useDeskChangedRefresh";
import { keepPlace, keptPlace } from "../../desk/deskMemory";
import { useWindowInterior } from "../../desk/surface/interior";
import { renderHeroSlot } from "./core-layout";
import { useOwnerName } from "../../desk/firstrun/ownerName";
import { useOwnerWriter } from "./settings/writer";
import { PeopleNotHere, PeopleReadFailed } from "../../desk/people/PeopleReadFailed";
import { PeopleRail, type RailPerson } from "../../desk/people/PeopleRail";
import { useWindowTitle } from "../../desk/surface/title";
import "./people.css";
import { RelationshipKind, Lens, Readiness, Relationship, Suggestion, RelationshipDetail, stateOf, readinessFace, readinessForError, isStoreOutage, isProtectedFailure, PEOPLE_PERSON_PLACE, readWhole, RosterNext, nextOneOnOnes, ROLE_CHOICES, oneOnOneWhen, lowerDay, sentence, relationshipLabel } from "./peopleModel";
import { RelationshipPane } from "./PeoplePerson";
export { RelationshipPane } from "./PeoplePerson";
export { prsSummaryLabel, capTokens } from "./peopleModel";
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
  const [errorTitle, setErrorTitle] = useState("");
  const [busy, setBusy] = useState(false);
  const requestedScope = scope?.startsWith("people:") ? scope.slice("people:".length) : null;
  // HS-200-14 (AC4): `people:project:<id>` scopes the rail to the people
  // linked to that Project; `people:<relationship>[:<lens>]` picks a person.
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

  // PHILO-17 ALIVE: one way to add. Add person opens the add row on the rail.
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
  // HS-S33: only the newest person read may land (a late read of the
  // person he left never draws over the one he is on).
  const selectSeq = useRef(0);
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
    const display_name = newName.trim(); if (!display_name) return;
    if (duplicate && duplicateWarned !== nameKey(display_name)) { setDuplicateWarned(nameKey(display_name)); return; }
    setBusy(true); setError("");
    try {
      await hub.createPerson(display_name, newKind);
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
    if (state === "no_key_store") return <PeopleNotHere />;
    // Betterment D6: a People read that failed is one line in place.
    if (state === "unavailable" || state === "locked") return <PeopleReadFailed onRetry={() => void load()} detail={error} />;
    const face = readinessFace(state);
    return <div className="people-joy-state" data-testid="people-joy-state">
      <Button variant="primary" onClick={recover} data-testid="people-joy-action">{face.action}</Button>
      <span className="people-joy-line">{face.label}</span>
      {error ? <span className="sr-only">{error}</span> : null}
    </div>;
  }
  // PHILO-13-04 (A3): the failure is ONE row that stays on screen while he
  // is down in a fold; the person and any unsent draft stay under it
  // (J3-06). Try again re-reads the person (or the roster).
  const failureRow = error ? (
    <span className="people-failure" role="alert" data-testid="people-failure">
      <span className="people-failure-label" title={errorTitle || undefined}>{error}</span>
      <Button dense variant="ghost" onClick={() => void (selectedId ? select(selectedId) : load())}>Try again</Button>
    </span>
  ) : null;

  const scoped = projectFilter ? relationships.filter((r) => (r.project_refs ?? []).includes(projectFilter)) : relationships;
  const scopedOut = projectFilter ? relationships.length - scoped.length : 0;
  const needle = nameKey(query);
  const shownPeople = needle ? scoped.filter((r) => nameKey(r.display_name).includes(needle)) : scoped;
  const shownSuggestions = projectFilter ? [] : needle ? suggestions.filter((s) => nameKey(s.name).includes(needle)) : suggestions;
  // The soonest 1:1 this week: the status bar's warm words; within a day its
  // Open prep is the pane's verb.
  const weekEnd = Date.now() + 7 * 86_400_000;
  const soonest = scoped
    .map((row) => ({ row, next: nextByPerson?.[row.id] }))
    .filter((x): x is { row: Relationship; next: RosterNext } => Boolean(x.next && (wireDate(x.next.startsAt)?.getTime() ?? Infinity) <= weekEnd))
    .sort((a, b) => (wireDate(a.next.startsAt)?.getTime() ?? 0) - (wireDate(b.next.startsAt)?.getTime() ?? 0))[0] ?? null;
  const prepDue = Boolean(soonest) && (wireDate(soonest!.next.startsAt)?.getTime() ?? Infinity) - Date.now() <= 86_400_000;
  const railPeople: RailPerson[] = shownPeople.map((relationship) => {
    const next = nextByPerson?.[relationship.id]?.startsAt ?? relationship.next_one_on_one ?? null;
    return {
      id: relationship.id, name: relationship.display_name, role: relationshipLabel(relationship.relationship_kind),
      next: next ? `1:1 ${oneOnOneWhen(next)}` : "",
      youOwe: Number(relationship.you_owe_count) || 0, owesYou: Number(relationship.owes_you_count) || 0,
      overdue: Number(relationship.overdue_count) || 0, done: Number(relationship.done_count) || 0,
    };
  });
  const suggestion = pickedSuggestion ? shownSuggestions.find((s) => `suggestion:${s.key}` === pickedSuggestion) ?? null : null;
  const firstName = (name: string) => name.trim().split(/\s+/)[0] || name;
  const empty = !relationships.length && !suggestions.length && !projectFilter && !adding;

  // The pane: the picked person, a picked suggestion's plate, or the soonest 1:1.
  let pane: ReactNode;
  if (selected) {
    pane = <RelationshipPane relationship={selected} initialLens={requestedLens} lensRequest={lensRequest} onRefresh={() => void select(selected.id)} onProtectedFailure={protectedFailure} onArchived={() => { clearProtected(); void load(); }} onBack={back} />;
  } else if (empty) {
    pane = <div className="people-empty" data-testid="people-empty-roster">
      <SurfaceState empty emptyLabel="People you meet appear here." emptyImage={PEOPLE_SPRITE} emptyKind="person" onAction={openAdd} actionLabel="Add person" />
    </div>;
  } else if (projectFilter && !scoped.length) {
    pane = <div className="people-empty" data-testid="people-roster-none-linked">
      <SurfaceState empty emptyLabel="No one linked yet" emptyImage={PEOPLE_SPRITE} emptyKind="person" />
    </div>;
  } else if (suggestion) {
    pane = <NowPlate eyebrow="From your meetings" tone="brass" title={suggestion.name} facts={sentence(suggestionSource(suggestion))}>
      <Button variant="primary" loading={suggestionBusy === suggestion.key} disabled={Boolean(suggestionBusy)} onClick={() => void addSuggestion(suggestion)} aria-label={`Add ${suggestion.name}`} data-testid="people-suggestion-add">Add</Button>
      <Button variant="secondary" disabled={Boolean(suggestionBusy)} onClick={() => void hideSuggestion(suggestion)} aria-label={`Hide ${suggestion.name}`} data-testid="people-suggestion-hide">Hide</Button>
    </NowPlate>;
  } else if (soonest) {
    pane = <NowPlate eyebrow="Next 1:1" tone="steel" title={soonest.row.display_name} facts={oneOnOneWhen(soonest.next.startsAt)}>
      <Button variant={prepDue ? "primary" : "secondary"} onClick={() => void select(soonest.row.id)} data-testid={prepDue ? "people-open-prep" : "people-open-soonest"}>Open prep</Button>
    </NowPlate>;
  } else {
    pane = <SurfaceState empty emptyLabel={countWords(scoped.length, "person", "people") ?? ""} emptyImage={PEOPLE_SPRITE} emptyKind="person" />;
  }
  const head = <>
    {adding ? <div className="people-new" data-testid="people-add-row">
      <StringGadget label="Add person" value={newName} onChange={setNewName} placeholder="Name" inputProps={{ id: "people-new-relationship" }} onKeyDown={(event) => { if (event.key === "Enter") void createRelationship(); if (event.key === "Escape" && relationships.length) setAdding(false); }} />
      <span className="people-role-pick" role="group" aria-label="Relationship">
        {ROLE_CHOICES.map((choice) => <Button key={choice.value} dense variant="ghost" className="people-role-choice" data-kind={choice.value} aria-pressed={newKind === choice.value} onClick={() => setNewKind(choice.value)}>{choice.label}</Button>)}
      </span>
      <span className="people-new-verbs">
        <Button dense variant="primary" disabled={!newName.trim() || busy} loading={busy} onClick={() => void createRelationship()}>{duplicateShown ? "Add again" : "Add"}</Button>
        {relationships.length ? <Button dense variant="ghost" onClick={() => setAdding(false)}>Done</Button> : null}
      </span>
      {duplicateShown ? <span className="people-duplicate" role="status" data-testid="people-duplicate">{duplicateShown.display_name} · Already here</span> : null}
    </div> : null}
    {projectFilter && scopedOut > 0 ? (
      <Button dense variant="secondary" className="people-everyone" aria-label="Everyone: clear the Project scope" onClick={() => setProjectFilter(null)} data-testid="people-roster-everyone">{`${scopedOut} more · Everyone`}</Button>
    ) : null}
  </>;
  return <div className="people-surface people-frame" data-testid="people-roster" data-picked={selected ? "" : undefined}>
    {renderHeroSlot(hero, null)}
    {nextReading ? <span hidden aria-busy="true" data-testid="people-next-reading" /> : null}
    <div className="people-body surface-rail-layout">
      {empty ? null : <PeopleRail people={railPeople} suggestions={shownSuggestions.map((s) => ({ key: s.key, name: s.name, source: sentence(suggestionSource(s)) }))}
        picked={selected ? selected.id : pickedSuggestion} query={query} onQuery={setQuery} adding={adding}
        searchable={Boolean(relationships.length || suggestions.length)} head={head}
        onBack={() => { back(); setPickedSuggestion(null); }}
        onPick={(id) => { if (id.startsWith("suggestion:")) { back(); setPickedSuggestion(id); } else void select(id); }} onAdd={() => (adding ? setAdding(false) : openAdd())} />}
      <div className="people-pane" data-testid="people-pane">
        {failureRow}
        {selected ? null : <WhoAreYou />}
        {pane}
      </div>
    </div>
    {selected ? null : <StatusBar
      data-testid="people-status"
      items={[
        { key: "count", testId: "people-count", text: projectFilter ? countWords(scoped.length, "on this project", "on this project") : countWords(relationships.length, "person", "people") },
        soonest ? { key: "next", lamp: prepDue ? "ask" as const : "info" as const, testId: "people-roster-next", text: `1:1 with ${firstName(soonest.row.display_name)} ${lowerDay(oneOnOneWhen(soonest.next.startsAt))}` } : null,
        { key: "suggested", lamp: "warn" as const, testId: "people-suggestions", text: projectFilter ? null : countWords(suggestions.length, "from your meetings", "from your meetings") },
        { key: "lock", lamp: "ok" as const, text: <span className="people-lock" title="Encrypted · Local storage · Notes only" data-testid="people-lock">Encrypted</span> },
      ]}
    />}
  </div>;
}

/** The plate (the language, 2026-11-08): the one raised thing of the face,
 *  the thing that matters now, with its verb. */
function NowPlate({ eyebrow, tone, title, facts, children }: { eyebrow: string; tone: "brass" | "steel" | "coral"; title: ReactNode; facts?: ReactNode; children?: ReactNode }) {
  return <section className="people-now" data-tone={tone} aria-label={eyebrow} data-testid="people-plate">
    <span className="people-now-eyebrow">{eyebrow}</span>
    <h3 className="people-now-title">{title}</h3>
    {facts ? <p className="people-now-facts">{facts}</p> : null}
    {children ? <div className="people-now-verbs">{children}</div> : null}
  </section>;
}

const PEOPLE_SPRITE = `${import.meta.env.BASE_URL || "/_built/"}desk/sprites/people-ledger.png`;

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
  const owner = useOwnerName(useOwnerWriter());
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
