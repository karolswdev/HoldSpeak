/* People readiness surrounds the shared roster; person reads and writes are app slots. */
import { useCallback, useEffect, useRef, useState } from "react";
import { ActionNotice, StatusBar, ListApp, useListApp, StringGadget, SurfaceState, countWords, PreferencePane, PaneInspector, InspectorForm, InspectorFacts, GadgetRow, CycleGadget, type ListVerb } from "../../desk/surface";
import { useGuideView } from "../../desk/walk/viewState";
import { wireDate } from "../../desk/surface/format";
import type { CoreProps } from "./core-types";
import * as hub from "../../desk/people/api";
import { failureTitle } from "../../desk/surface/plainFailure";
import { openSurfaceOr } from "../../desk/shell";
import { openPerson, PERSON_OPEN_EVENT, type PersonOpenRequest } from "../../desk/openObject";
import { peekPersonLens, takePersonLens } from "../../desk/objectWindows";
import { announceTaskReturn, taskFocusPending } from "../../desk/returnToTask";
import { PEOPLE_CHANGE_KINDS, useOnDeskChanged } from "../../desk/useDeskChangedRefresh";
import { keepPlace, keptPlace } from "../../desk/deskMemory";
import { useWindowInterior } from "../../desk/surface/interior";
import { useWindowTitle } from "../../desk/surface/title";
import { RelationshipKind, Lens, Readiness, Relationship, Suggestion, RelationshipDetail, stateOf, readinessForError, isStoreOutage, isProtectedFailure, isAuthOrKeyFailure, PEOPLE_PERSON_PLACE, readWhole, RosterNext, nextOneOnOnes, ROLE_CHOICES, oneOnOneWhen, lowerDay, sentence, relationshipLabel } from "./peopleModel";
import { RelationshipPane } from "./PeoplePerson";
export { RelationshipPane } from "./PeoplePerson";
export { prsSummaryLabel, capTokens } from "./peopleModel";

type PersonRow = { id: string; person: Relationship; suggestion?: never } | { id: string; suggestion: Suggestion; person?: never };
async function readPeople(previousSuggestions: Suggestion[]) {
  try {
    const readiness = await hub.readReadiness<Readiness>();
    const state = stateOf(readiness);
    if (state !== "ready" && state !== "unconfigured") return { rows: [] as PersonRow[], readiness };
    const roster = state === "ready" ? await hub.readRoster<Relationship>() : { relationships: [] };
    // Suggestions are optional; their read cannot turn a roster into a refusal.
    const suggested = await hub.readSuggestions<Suggestion>().catch(() => ({ suggestions: previousSuggestions }));
    const rows: PersonRow[] = [
      ...(roster.relationships ?? []).map(person => ({ id: person.id, person })),
      ...(suggested.suggestions ?? []).map(suggestion => ({ id: `suggestion:${suggestion.key}`, suggestion })),
    ];
    return { rows, readiness };
  } catch (cause) {
    if (isProtectedFailure(cause) || isAuthOrKeyFailure(cause)) return { rows: [] as PersonRow[], readiness: readinessForError(cause) };
    throw cause;
  }
}

export function PeopleCore({ scope }: CoreProps) {
  const requestedScope = scope?.startsWith("people:") ? scope.slice("people:".length) : null;
  const requestedProjectId = requestedScope?.startsWith("project:") ? requestedScope.slice("project:".length) : null;
  const requestedId = requestedProjectId ? null : requestedScope?.split(":")[0];
  const [projectFilter, setProjectFilter] = useState<string | null>(requestedProjectId);
  const lastSuggestions = useRef<Suggestion[]>([]);
  const read = useCallback(() => readPeople(lastSuggestions.current), []);
  const app = useListApp({ read, keyOf: row => row.id,
    initialPicked: requestedId || (requestedProjectId ? null : keptPlace(PEOPLE_PERSON_PLACE)),
    search: (row, query) => (!projectFilter || Boolean(row.person?.project_refs?.includes(projectFilter))) && nameKey(row.person?.display_name ?? row.suggestion!.name).includes(nameKey(query)),
  });
  const relationships = app.rows.flatMap(row => row.person ? [row.person] : []);
  const suggestions = app.rows.flatMap(row => row.suggestion ? [row.suggestion] : []);
  useEffect(() => { lastSuggestions.current = suggestions; }, [app.page]);
  const selectedId = app.selected?.person?.id ?? null;
  const [refusal, setRefusal] = useState<Readiness | null>(null);
  const readiness = refusal ?? app.page?.readiness ?? { readiness: "unconfigured" };
  const unconfigured = stateOf(readiness) === "unconfigured";
  const unavailable = stateOf(readiness) !== "ready" && !unconfigured;
  const [detail, setDetail] = useState<RelationshipDetail | null>(null);
  const [detailAttempt, retryDetail] = useState(0);
  const [newName, setNewName] = useState("");
  const [newKind, setNewKind] = useState<RelationshipKind>("direct_report");
  const [duplicateWarned, setDuplicateWarned] = useState("");
  const [adding, setAdding] = useState(false);
  const [busy, setBusy] = useState(false);
  const [suggestionBusy, setSuggestionBusy] = useState("");
  const [error, setError] = useState("");
  const [errorTitle, setErrorTitle] = useState("");
  const reload = async () => { setRefusal(null); await app.reload(); };
  const clearProtected = () => {
    app.rows.forEach(row => app.drop(row.id)); app.setPicked(null); setDetail(null); setNewName("");
  };
  function protectedFailure(cause: unknown, mayHaveSaved = false) {
    if (mayHaveSaved || isAuthOrKeyFailure(cause)) {
      clearProtected(); setRefusal(readinessForError(cause));
    }
    setError(mayHaveSaved ? "Could not read the people store · A promise may be saved · Check again when the store is back" : "Could not do that · Nothing changed · Try again");
    setErrorTitle(failureTitle(cause));
  }
  // The kit owns selected identity. Only this person's independent detail read lives here.
  useEffect(() => {
    if (!selectedId || unavailable) { setDetail(null); return; }
    let live = true;
    setDetail(current => current?.id === selectedId ? current : null);
    void readWhole(selectedId).then(whole => {
      if (live && whole.id === selectedId) { setDetail(whole); setError(""); }
    }).catch(cause => { if (live) protectedFailure(cause); });
    return () => { live = false; };
  }, [selectedId, app.page, detailAttempt, unavailable]); // domain detail follows the acknowledged roster
  useEffect(() => { if (!app.loading) keepPlace(PEOPLE_PERSON_PLACE, selectedId ?? ""); }, [app.loading, selectedId]);
  useEffect(() => { if (requestedId) app.setPicked(requestedId); }, [requestedId]);
  useOnDeskChanged(() => { if (stateOf(readiness) === "ready") void app.reload(); });
  useEffect(() => () => { if (taskFocusPending()) announceTaskReturn(); }, []);
  useGuideView(() => ({ detail, adding }), saved => { setDetail(saved.detail); setAdding(saved.adding); }, () => setAdding(false), 1);
  const rosterKey = relationships.map(row => row.id).join("|");
  const [nextByPerson, setNextByPerson] = useState<Record<string, RosterNext> | null>(null);
  const [nextReadFor, setNextReadFor] = useState<string | null>(null);
  useEffect(() => {
    if (!rosterKey) return;
    let live = true;
    void hub.readUpcoming<Record<string, unknown>>()
      .then(door => { if (live) { setNextByPerson(nextOneOnOnes(door.upcoming ?? [])); setNextReadFor(rosterKey); } })
      .catch(() => { if (live) { setNextByPerson(null); setNextReadFor(rosterKey); } });
    return () => { live = false; };
  }, [rosterKey]);
  const recover = () => {
    if (["locked", "unavailable"].includes(stateOf(readiness))) { void reload(); return; }
    openSurfaceOr("configure-settings", "/settings", "people-security");
  };
  const duplicate = sameName(relationships, newName);
  const duplicateShown = duplicate && duplicateWarned === nameKey(newName) ? duplicate : null;
  const createRelationship = async () => {
    const display_name = newName.trim(); if (!display_name || busy) return;
    if (duplicate && duplicateWarned !== nameKey(display_name)) { setDuplicateWarned(nameKey(display_name)); return; }
    setBusy(true); setError("");
    try {
      await hub.createPerson(display_name, newKind);
      setNewName(""); setDuplicateWarned(""); await reload();
    } catch (cause) { protectedFailure(cause); }
    finally { setBusy(false); document.getElementById("people-new-relationship")?.focus(); }
  };
  const changeSuggestion = async (suggestion: Suggestion, hide: boolean) => {
    setSuggestionBusy(suggestion.key); setError("");
    try {
      if (hide) await hub.hideSuggestion(suggestion.key); else await hub.addSuggestion(suggestion.key);
      app.drop(`suggestion:${suggestion.key}`);
      if (!hide) await reload();
    } catch (cause) { protectedFailure(cause); } finally { setSuggestionBusy(""); }
  };
  if (!app.page && app.loading) return <SurfaceState loading data-testid="people-loading" />;
  if (!app.page && app.error) return <PeopleState state="unavailable" error={app.error} retry={() => void reload()} recover={recover} />;
  if (unavailable) return <PeopleState state={stateOf(readiness)} error={error} retry={() => void reload()} recover={recover} />;
  const selectedDetail = detail?.id === selectedId ? detail : null;
  const selected = selectedDetail ?? app.selected?.person;
  const suggestion = app.selected?.suggestion;
  const scoped = projectFilter ? relationships.filter(row => row.project_refs?.includes(projectFilter)) : relationships;
  const scopedOut = relationships.length - scoped.length;
  const soonest = scoped.map(row => ({ row, next: nextByPerson?.[row.id] }))
    .filter((x): x is { row: Relationship; next: RosterNext } => Boolean(x.next && (wireDate(x.next.startsAt)?.getTime() ?? Infinity) <= Date.now() + 7 * 86_400_000))
    .sort((a,b) => (wireDate(a.next.startsAt)?.getTime() ?? 0) - (wireDate(b.next.startsAt)?.getTime() ?? 0))[0];
  const personSelected = (row: {kind: string} | null) => row?.kind === "person";
  const selectedSuggestion = (id?: string) => suggestions.find(item => `suggestion:${item.key}` === id);
  const verbs: ListVerb[] = [
    {id:"add-person",label:"Add person",key:"n",run:() => { setAdding(true); window.setTimeout(() => document.getElementById("people-new-relationship")?.focus(),0); }},
    {id:"open",label:"Open",key:"Enter",enabled:personSelected,run:row => { if (row) openPerson(row.id); }},
    {id:"prep",label:"Prep 1:1",key:"p",enabled:personSelected,run:row => { if (row) openPerson(row.id,"prep"); }},
    ...(suggestions.length ? [
      {id:"add-suggestion",label:"Add from meetings",key:"a",enabled:row => row?.kind === "suggestion" && !suggestionBusy,run:row => { const item = selectedSuggestion(row?.id); if (item) void changeSuggestion(item,false); }},
      {id:"hide-suggestion",label:"Hide",key:"Delete",enabled:row => row?.kind === "suggestion" && !suggestionBusy,run:row => { const item = selectedSuggestion(row?.id); if (item) void changeSuggestion(item,true); }},
    ] as ListVerb[] : []),
    ...(projectFilter && scopedOut ? [{id:"everyone",label:`${scopedOut} more · Everyone`,run:() => setProjectFilter(null)}] : []),
  ];
  const selectedNext = selected ? nextByPerson?.[selected.id]?.startsAt ?? selected.next_one_on_one : null;
  const failureRow = error ? <ActionNotice tone="danger" role="alert">{adding ? "Person could not be added; the name is kept." : "People could not be read; the last view is kept, try again."}</ActionNotice> : null;
  return <ListApp app={{...app,loading:app.loading && !app.page}} label="People"
    ids={{windowTestId:"people-roster",listTestId:"people-list",paneTestId:"people-summary",toolbarTestId:"people-toolbar",statusTestId:"people-status",loadingTestId:"people-loading"}}
    words={{find:"Find a person",empty:projectFilter ? "No one linked yet" : "People you meet appear here.",noMatch:"No names match",select:"Select a person"}}
    row={row => {
      const person = row.person, next = person && (nextByPerson?.[person.id]?.startsAt ?? person.next_one_on_one);
      return {id:row.id,kind:person ? "person" : "suggestion",name:person?.display_name ?? row.suggestion!.name,nameTestId:person ? "people-row-name" : undefined,
        cells:{relationship:person ? relationshipLabel(person.relationship_kind) : "From meetings",next:next ? oneOnOneWhen(next) : "",open:person ? [person.you_owe_count ? `${person.you_owe_count} you owe` : "",person.owes_you_count ? `${person.owes_you_count} owed to you` : ""].filter(Boolean).join(" · ") : ""}};
    }}
    list={{verbs,defaultVerb:"open",columns:[
      {key:"name",word:"Name",priority:100,track:"minmax(0, 1.2fr)"}, {key:"relationship",word:"Relationship",priority:10,track:"minmax(0, 1fr)"},
      {key:"next",word:"Next 1:1",priority:30,track:"minmax(0, 1fr)"}, {key:"open",word:"Open with them",priority:20,track:"minmax(0, 1.4fr)"},
    ],rowProps:row => ({"data-testid":row.kind === "suggestion" ? "people-suggestion" : "people-row","data-person":row.id})}}
    pane={() => adding || selected || suggestion || error ? <>{adding ? <PaneInspector label="New person"><InspectorForm testId="people-add-row"
      completion={{cancel:() => setAdding(false),primary:{label:error ? "Try again" : duplicateShown ? "Add again" : "Add",disabled:!newName.trim() || busy,busy,run:() => void createRelationship()}}}
      notice={failureRow ?? (duplicateShown ? <span role="status" data-testid="people-duplicate">{duplicateShown.display_name} · Already here</span> : null)}>
      <GadgetRow label="Name"><StringGadget label="Add person" value={newName} onChange={setNewName} placeholder="Name" inputProps={{id:"people-new-relationship"}} onKeyDown={event => {if (event.key === "Enter") void createRelationship();}} /></GadgetRow>
      <GadgetRow label="Relationship"><CycleGadget label="Relationship" value={newKind} options={ROLE_CHOICES} onChange={value => setNewKind(value as RelationshipKind)} /></GadgetRow>
    </InspectorForm></PaneInspector> : selected ? <InspectorFacts data-feedback-redact="true" name={selected.display_name} nameTestId="people-summary-name" notice={error ? <ActionNotice tone="danger" role="alert" action={{label:"Try again",onClick:()=>retryDetail(n=>n+1)}}>People could not be read; the last view is kept, try again.</ActionNotice> : undefined} rows={[
      {label:"Relationship",value:relationshipLabel(selected.relationship_kind)}, {label:"Next 1:1",value:selectedNext ? oneOnOneWhen(selectedNext) : ""},
      ...(!selectedDetail ? [{label:"Commitments",value:error ? "Commitments not read" : "Reading commitments…"}] : [
        ...(selectedDetail.commitments ?? []).filter(item => ["open","in_progress"].includes(item.state ?? "open")).map(item => ({key:item.id,label:"You owe",value:item.body})),
        ...(selectedDetail.owed_to_you ?? []).filter(item => ["open","in_progress"].includes(item.state ?? "open")).map(item => ({key:item.id,label:"Owed to you",value:item.body})),
        ...(![...(selectedDetail.commitments ?? []),...(selectedDetail.owed_to_you ?? [])].some(item => ["open","in_progress"].includes(item.state ?? "open")) ? [{label:"Commitments",value:"No open commitments"}] : []),
      ]),
    ]} /> : suggestion ? <InspectorFacts name={suggestion.name} rows={[{label:"From",value:sentence(suggestionSource(suggestion))}]} /> : null}</> : null}
    status={[
      {key:"count",testId:"people-count",text:projectFilter ? countWords(scoped.length,"on this project","on this project") : countWords(relationships.length,"person","people")},
      soonest ? {key:"next",testId:"people-roster-next",text:`1:1 with ${soonest.row.display_name.trim().split(/\s+/)[0]} ${lowerDay(oneOnOneWhen(soonest.next.startsAt))}`} : null,
      {key:"suggested",testId:"people-suggestions",text:projectFilter ? null : countWords(suggestions.length,"from your meetings","from your meetings")},
      error ? {key:"failure",lamp:"fail",text:adding ? "Person not saved" : "People read failed"} : null,
    ]}>
    {rosterKey && nextReadFor !== rosterKey ? <span hidden aria-busy="true" data-testid="people-next-reading" /> : null}

  </ListApp>;
}

function PeopleState({state,error,retry,recover}: {state:ReturnType<typeof stateOf>;error?:string;retry():void;recover():void}) {
  const line=state==="no_key_store"?"People is not set up on this Mac.":state==="locked"?"People is locked.":state==="key_unavailable"?"Key unavailable.":state==="corrupt"?"People store is unavailable; nothing changed, open Settings.":"People could not be read; nothing changed, try again.";
  const recovery=state==="key_unavailable"||state==="corrupt";
  return <PreferencePane label="People state" testId={state==="no_key_store"?"people-not-here":recovery?"people-joy-state":"people-read-failed"}>
    <SurfaceState error={line} errorTitle={error} onRetry={state==="no_key_store"?undefined:recovery?recover:retry} retryLabel={recovery?"Recovery":"Try again"}/>
    <StatusBar data-testid="people-status" items={[{key:"failure",lamp:"fail",text:state==="unavailable"?"People read failed":state==="corrupt"?"People store unavailable":line}]}/>
  </PreferencePane>;
}

function suggestionSource(row: Suggestion): string {
  const parts: string[] = [];
  if (row.series) parts.push(row.series.next_starts_at ? `1:1 ${oneOnOneWhen(row.series.next_starts_at)}` : row.series.label || "1:1 series");
  else if (row.meetings[0]) parts.push(`named in ${row.meetings[0].title || "a meeting"}`);
  else if (row.jira) parts.push("assigned in Jira");
  if (row.promise_count) parts.push(row.promise_count === 1 ? "1 promise" : `${row.promise_count} promises`);
  return parts.join(" · ");
}
function nameKey(name: string): string { return name.trim().replace(/\s+/g," ").toLowerCase(); }
function sameName(relationships: Relationship[], name: string): Relationship | null {
  const key = nameKey(name); return key ? relationships.find(row => nameKey(row.display_name) === key) ?? null : null;
}

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
      if (isAuthOrKeyFailure(cause)) { setDetail(null); setReadiness(readinessForError(cause)); }
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
    if (isAuthOrKeyFailure(cause)) { setDetail(null); setReadiness(readinessForError(cause)); }
    setError("Could not do that · Nothing changed · Try again"); setErrorTitle(failureTitle(cause));
  };
  if (loading && !detail) return <SurfaceState loading />;
  if (readiness && stateOf(readiness) !== "ready") return <PeopleState state={stateOf(readiness)} error={error} retry={() => void read()} recover={() => openSurfaceOr("configure-settings","/settings","people-security")} />;
  if (!detail) return <PeopleState state="unavailable" error={error} retry={() => void read()} recover={() => void read()} />;
  return <PreferencePane label={detail.display_name} testId="person-window">
    <RelationshipPane relationship={detail} initialLens={initialLens} lensRequest={lensRequest} issue={error}
      onRefresh={() => void read()} onProtectedFailure={protectedFailure}
      onArchived={() => { if (onClose) onClose(); else { setDetail(null); void read(); } }} />
  </PreferencePane>;
}
