/* A person: one ledger, one composer. Links edit in place from the mast. */
import { useEffect, useRef, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { ConfirmVerb, CycleGadget, Mast, Spine, SurfaceRow, SurfaceRows, SurfaceSection } from "../../desk/surface";
import { ShowMe } from "../../desk/walk/ShowMe";
import { useDesk } from "../../desk/store";
import * as hub from "../../desk/people/api";
import { failureTitle } from "../../desk/surface/plainFailure";
import { CalendarLinkSection, OwnerAliasSection } from "./PeopleLinks";
import { PeopleLedger } from "./PeopleLedger";
import { dayLabel, isOverdue, lowerDay, oneOnOneWhen, relationshipLabel, type CalendarRead, type Commitment, type Lens, type PrepNext, type Project, type RelationshipDetail, type UpcomingEvent } from "./peopleModel";

function personSpine(relationship: RelationshipDetail) {
  const all = [...(relationship.owed_to_you ?? []), ...(relationship.commitments ?? [])];
  const open = (rows: Commitment[]) => rows.filter((row) => (row.state ?? "open") === "open" && !isOverdue(row.due)).length;
  const brass = open(relationship.owed_to_you ?? []);
  const steel = open(relationship.commitments ?? []);
  const coral = all.filter((row) => (row.state ?? "open") === "open" && isOverdue(row.due)).length;
  const moss = all.filter((row) => row.state === "done").length;
  return { words: [brass ? `${brass} owed to you` : "", steel ? `${steel} you owe` : "", coral ? `${coral} overdue` : "", moss ? `${moss} done` : ""].filter(Boolean).join(", "), segments: [
    { tone: "brass" as const, share: brass }, { tone: "steel" as const, share: steel },
    { tone: "coral" as const, share: coral }, { tone: "moss" as const, share: moss },
  ] };
}

export function RelationshipPane({ relationship, initialLens, lensRequest, onRefresh, onProtectedFailure, onArchived, onBack, lead }: {
  relationship: RelationshipDetail; initialLens?: Lens | null; lensRequest?: { lens: Lens; seq: number } | null;
  onRefresh(): void; onProtectedFailure(cause: unknown, mayHaveSaved?: boolean): void; onArchived(): void;
  onBack?(): void; lead?: ReactNode;
}) {
  const [links, setLinks] = useState(initialLens === "info");
  const [composerRequest, setComposerRequest] = useState(initialLens === "context" ? 1 : 0);
  const [next, setNext] = useState<PrepNext | null>(null);
  const ledger = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (lensRequest?.lens === "context") setComposerRequest((n) => n + 1);
    else if (lensRequest?.lens === "info") setLinks(true);
    else if (lensRequest) { setLinks(false); ledger.current?.scrollIntoView?.({ block: "start" }); }
  }, [lensRequest]);
  const projects = useDesk((state) => state.projects);
  const spine = personSpine(relationship);
  const facts = [relationshipLabel(relationship.relationship_kind), relationship.role_context, relationship.cadence,
    next?.last ? `last 1:1 ${dayLabel(next.last)}` : "", next?.at ? `next 1:1 ${lowerDay(oneOnOneWhen(next.at))}` : "",
    ...projects.filter((project) => relationship.project_refs?.includes(project.id)).map((project) => project.name),
  ].filter(Boolean).join(" · ");
  return <div className="people-person" data-testid="people-person">
    <Mast kind="person" id={relationship.id} className="people-detail-head" data-testid="people-detail-head"
      title={<span className="people-name" data-testid="prep-display-name">{relationship.display_name}</span>}
      facts={<span data-testid="people-who-meta">{facts}</span>}>
      {onBack ? <Button variant="secondary" className="people-back" onClick={onBack}>Back</Button> : null}
      <Button variant="secondary" onClick={() => setComposerRequest((n) => n + 1)} data-testid="person-add-note">Note</Button>
      <Button variant="ghost" aria-expanded={links} onClick={() => setLinks(!links)} data-testid="person-link-project">{links ? "Close links" : "Links"}</Button>
      <ShowMe app="surface-people" />
    </Mast>
    <Spine className="people-spine" segments={spine.segments} label={spine.words || undefined} data-testid="people-spine" />
    {links ? <PersonLinks relationship={relationship} onRefresh={onRefresh} onProtectedFailure={onProtectedFailure} onArchived={onArchived} /> : null}
    {lead}
    <div ref={ledger} className="people-ledger-body"><PeopleLedger key={relationship.id} relationship={relationship} onRefresh={onRefresh}
      onProtectedFailure={onProtectedFailure} onNext={setNext} composerRequest={composerRequest} /></div>
  </div>;
}

function PersonLinks({ relationship, onRefresh, onProtectedFailure, onArchived }: {
  relationship: RelationshipDetail; onRefresh(): void; onProtectedFailure(cause: unknown): void; onArchived(): void;
}) {
  const [events, setEvents] = useState<UpcomingEvent[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [title, setTitle] = useState("");
  useEffect(() => {
    let live = true;
    setLoading(true); setError("");
    void hub.readUpcoming<UpcomingEvent>().then((answer) => {
      if (live) setEvents((answer.upcoming ?? []).filter((row) => row.uid && row.source === "calendar_event"));
    }).catch((cause) => { if (live) { setError("Could not load the calendar · Nothing changed · Try again"); setTitle(failureTitle(cause)); } })
      .finally(() => { if (live) setLoading(false); });
    void hub.readProjects<Project>().then((answer) => {
      if (live) { setProjects(answer.projects ?? []); setProjectId((id) => id || answer.projects?.[0]?.id || ""); }
    }).catch((cause) => { if (live) onProtectedFailure(cause); });
    return () => { live = false; };
  }, [relationship.id, attempt]); // eslint-disable-line react-hooks/exhaustive-deps
  const act = async (work: () => Promise<unknown>) => {
    try { await work(); onRefresh(); } catch (cause) { onProtectedFailure(cause); }
  };
  const calendarRead: CalendarRead = { loading, error, title, retry: () => setAttempt((n) => n + 1) };
  return <section className="people-links" aria-label="Links" data-testid="people-links">
    <SurfaceSection label="Projects"><div className="people-project-link">
      <CycleGadget label="Project" value={projectId} onChange={setProjectId} options={projects.map((project) => ({ value: project.id, label: project.name }))} />
      <Button dense disabled={!projectId || relationship.project_refs?.includes(projectId)} onClick={() => void act(() => hub.linkProject(relationship.id, projectId))}>Link</Button>
    </div><SurfaceRows>{projects.filter((project) => relationship.project_refs?.includes(project.id)).map((project) => <SurfaceRow key={project.id} title={project.name}
      verbs={<Button dense variant="ghost" onClick={() => void act(() => hub.unlinkProject(relationship.id, project.id))}>Unlink</Button>} />)}</SurfaceRows></SurfaceSection>
    <CalendarLinkSection relationship={relationship} onRefresh={onRefresh} onProtectedFailure={onProtectedFailure} upcomingEvents={events} calendarRead={calendarRead} />
    <OwnerAliasSection relationship={relationship} onRefresh={onRefresh} onProtectedFailure={onProtectedFailure} />
    <ConfirmVerb targetId={relationship.id} label="Archive person" confirmLabel="Archive?" onConfirm={() => {
      void hub.archivePerson(relationship.id).then(onArchived).catch(onProtectedFailure);
    }} />
  </section>;
}
