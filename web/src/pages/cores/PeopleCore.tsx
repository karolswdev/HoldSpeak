// HS-135-04 — People is a single protected Desk application.  Its roster is
// a relationship projection, never a field of person tiles or a scorecard.
import { useCallback, useEffect, useMemo, useState } from "react";
import type { CoreProps } from "./core-types";
import { Button } from "../../components/signal/Signal";
import { ApiError, apiFetch, readableError } from "../../lib/api";
import { openSurfaceOr } from "../../desk/shell";
import { spriteUrl } from "../../desk/sprites";
import { CycleGadget, PadGadget, StringGadget } from "../../desk/surface/gadgets";
import {
  ConfirmVerb,
  SurfaceColumns,
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceSplit,
  SurfaceState,
} from "../../desk/surface/Surface";
import { renderHeroSlot } from "./core-layout";
import "./people.css";

type ReadinessState = "unconfigured" | "locked" | "key_unavailable" | "corrupt" | "unavailable" | "ready";
type Visibility = "shared_intent" | "leader_private";
type RelationshipKind = "direct_report" | "peer" | "extended";
type Lens = "now" | "one-on-ones" | "context" | "history" | "info";

type Readiness = {
  readiness?: ReadinessState;
  state?: ReadinessState;
  store?: "encrypted" | "absent";
  sync?: "local_only";
  capture?: "notes_only";
};
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
};
type AgendaItem = { id: string; body: string; visibility: Visibility; state: string; rolled_from_id?: string | null };
type Session = { id: string; occurred_at?: string; title?: string; agenda?: AgendaItem[] };
type GroundingNote = { id: string; topic?: string; body: string; visibility: Visibility; source?: string };
type CommitmentEvent = { event: string; state: string; at: string; source: string; rationale?: string; evidence?: Array<Record<string, unknown>> };
type Commitment = { id: string; body: string; due?: string | null; state?: string; history?: CommitmentEvent[]; execution_links?: Array<{ workbench_id: string; item_id: string }> };
type Workbench = { id: string; name: string };
type Project = { id: string; name: string; description?: string };
type ExecutionItem = { id: string; workbench_id: string; status: string; result?: string | null; result_artifact_id?: string | null; completed_at?: string | null };
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
  const requestedRelationshipId = scope?.startsWith("people:")
    ? scope.slice("people:".length)
    : null;

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
    return <SurfaceState empty emptyLabel={face.label} onAction={recover} actionLabel={face.action}>{error ? <span className="sr-only">{error}</span> : null}</SurfaceState>;
  }
  return <>
    {renderHeroSlot(hero, verbs, facts())}
    {error ? <SurfaceState error={error} onRetry={() => void load()} /> : null}
    <SurfaceSplit
      detailOpen={Boolean(selected)}
      main={<Roster relationships={relationships} selectedId={selectedId} newName={newName} setNewName={setNewName} newKind={newKind} setNewKind={setNewKind} busy={busy} onCreate={() => void createRelationship()} onSelect={(id) => void select(id)} />}
      detail={selected ? <RelationshipPane relationship={selected} onRefresh={() => void select(selected.id)} onProtectedFailure={protectedFailure} onArchived={() => { clearProtected(); void load(); }} onBack={() => { setSelectedId(null); setDetail(null); }} /> : undefined}
    />
  </>;
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
    {!ordered.length ? <SurfaceState empty emptyLabel="No relationships" emptyImage={spriteUrl("people", "people")} /> : <SurfaceRows>{ordered.map((relationship) => <SurfaceRow key={relationship.id} selected={selectedId === relationship.id} title={relationship.display_name} detail={`${relationshipLabel(relationship.relationship_kind)}${relationship.next_one_on_one ? ` · ${relationship.next_one_on_one}` : ""}`} meta={relationship.manager_commitment_count ? `You owe ${relationship.manager_commitment_count}` : undefined} onOpen={() => onSelect(relationship.id)} />)}</SurfaceRows>}
  </SurfaceSection>;
}

function RelationshipPane({ relationship, onRefresh, onProtectedFailure, onArchived, onBack }: { relationship: RelationshipDetail; onRefresh(): void; onProtectedFailure(cause: unknown): void; onArchived(): void; onBack(): void }) {
  const [lens, setLens] = useState<Lens>("now");
  return <div className="people-detail">
    <div className="people-detail-head"><Button dense variant="ghost" onClick={onBack}>Back</Button><strong>{relationship.display_name}</strong></div>
    <div className="people-lenses" role="tablist" aria-label={`${relationship.display_name} lenses`}>
      {([['now', 'Now'], ['one-on-ones', '1:1s'], ['context', 'Context'], ['history', 'History'], ['info', 'Info']] as const).map(([id, label]) => <button key={id} type="button" role="tab" aria-selected={lens === id} onClick={() => setLens(id)}>{label}</button>)}
    </div>
    {lens === "now" ? <NowLens relationship={relationship} onRefresh={onRefresh} onProtectedFailure={onProtectedFailure} /> : null}
    {lens === "one-on-ones" ? <OneOnOnes relationship={relationship} onRefresh={onRefresh} onProtectedFailure={onProtectedFailure} /> : null}
    {lens === "context" ? <ContextLens relationship={relationship} onRefresh={onRefresh} onProtectedFailure={onProtectedFailure} /> : null}
    {lens === "history" ? <HistoryLens relationship={relationship} /> : null}
    {lens === "info" ? <InfoLens relationship={relationship} onArchived={onArchived} onProtectedFailure={onProtectedFailure} /> : null}
  </div>;
}

function ContextLens({ relationship, onRefresh, onProtectedFailure }: { relationship: RelationshipDetail; onRefresh(): void; onProtectedFailure(cause: unknown): void }) {
  const [topic, setTopic] = useState(""); const [body, setBody] = useState(""); const [visibility, setVisibility] = useState<Visibility>("leader_private"); const [busy, setBusy] = useState(false); const [projects, setProjects] = useState<Project[]>([]); const [projectId, setProjectId] = useState("");
  useEffect(() => { void apiFetch<{ projects?: Project[] }>("/api/projects").then((result) => { const rows = result.projects ?? []; setProjects(rows); setProjectId((current) => current || rows[0]?.id || ""); }).catch(onProtectedFailure); }, [relationship.id]);
  const add = async () => { if (!body.trim()) return; setBusy(true); try { await apiFetch(`/api/people/relationships/${encodeURIComponent(relationship.id)}/notes`, { method: "POST", json: { topic: topic.trim(), body: body.trim(), visibility } }); setTopic(""); setBody(""); onRefresh(); } catch (cause) { onProtectedFailure(cause); } finally { setBusy(false); } };
  const linkProject = async () => { if (!projectId) return; try { await apiFetch(`/api/people/relationships/${encodeURIComponent(relationship.id)}/projects/${encodeURIComponent(projectId)}`, { method: "POST", json: {} }); onRefresh(); } catch (cause) { onProtectedFailure(cause); } };
  const unlinkProject = async (id: string) => { try { await apiFetch(`/api/people/relationships/${encodeURIComponent(relationship.id)}/projects/${encodeURIComponent(id)}`, { method: "DELETE" }); onRefresh(); } catch (cause) { onProtectedFailure(cause); } };
  const linkedProjects = projects.filter((project) => relationship.project_refs?.includes(project.id));
  return <><SurfaceSection label="Projects"><div className="people-project-link"><CycleGadget label="Project" value={projectId} onChange={setProjectId} options={projects.map((project) => ({ value: project.id, label: project.name }))} /><Button dense disabled={!projectId || relationship.project_refs?.includes(projectId)} onClick={() => void linkProject()}>Link</Button></div>{linkedProjects.length ? <SurfaceRows>{linkedProjects.map((project) => <SurfaceRow key={project.id} title={project.name} detail={project.description} onOpen={() => openSurfaceOr("open-project-memory", "/project-memory", `project:${project.id}`)} verbs={<Button dense variant="ghost" onClick={() => void unlinkProject(project.id)}>Unlink</Button>} />)}</SurfaceRows> : <SurfaceState empty emptyLabel="No linked projects" />}</SurfaceSection><SurfaceSection label="Grounding notes"><div className="people-context-add"><StringGadget mic={false} label="Topic" value={topic} onChange={setTopic} placeholder="Topic (optional)" /><PadGadget mic={false} label="Grounding note" value={body} onChange={setBody} placeholder="Context worth remembering" rows={3} /><CycleGadget label="Visibility" value={visibility} onChange={(value) => setVisibility(value as Visibility)} options={[{ value: "leader_private", label: "Leader private" }, { value: "shared_intent", label: "Shared" }]} /><Button dense disabled={!body.trim() || busy} onClick={() => void add()}>Add note</Button></div>{!(relationship.notes ?? []).length ? <SurfaceState empty emptyLabel="No grounding notes" /> : <SurfaceRows>{(relationship.notes ?? []).map((note) => <SurfaceRow key={note.id} title={note.topic || note.body} detail={note.topic ? note.body : undefined} meta={note.visibility === "leader_private" ? "Leader private" : "Shared"} />)}</SurfaceRows>}</SurfaceSection></>;
}

function relationshipLabel(kind?: string): string {
  if (kind === "direct_report") return "Direct report";
  if (kind === "peer") return "Peer";
  if (kind === "extended") return "Extended relationship";
  return "Relationship";
}

function NowLens({ relationship, onRefresh, onProtectedFailure }: { relationship: RelationshipDetail; onRefresh(): void; onProtectedFailure(cause: unknown): void }) {
  const [request, setRequest] = useState(""); const [busy, setBusy] = useState(false); const [selectedCommitment, setSelectedCommitment] = useState<Commitment | null>(null);
  const createRequest = async () => { if (!request.trim()) return; setBusy(true); try { await apiFetch(`/api/people/relationships/${encodeURIComponent(relationship.id)}/requests`, { method: "POST", json: { body: request.trim(), visibility: "shared_intent", source: { kind: "manual" } } }); setRequest(""); onRefresh(); } catch (cause) { onProtectedFailure(cause); } finally { setBusy(false); } };
  const accept = async (id: string) => { try { await apiFetch(`/api/people/requests/${encodeURIComponent(id)}/accept`, { method: "POST", json: {} }); onRefresh(); } catch (cause) { onProtectedFailure(cause); } };
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
  return <><SurfaceSection label="Follow-through"><dl className="people-history-facts"><div><dt>Accepted</dt><dd>{commitments.length}</dd></div><div><dt>Satisfied</dt><dd>{satisfied}</dd></div><div><dt>Open</dt><dd>{commitments.filter((item) => item.state === "open").length}</dd></div><div><dt>With evidence</dt><dd>{evidence}</dd></div></dl></SurfaceSection><SurfaceSection label="Timeline">{events.length ? <SurfaceRows>{events.map((event, index) => <SurfaceRow key={`${event.at}-${index}`} title={event.commitment} detail={`${event.event}${event.rationale ? ` · ${event.rationale}` : ""}`} meta={event.at ? new Date(event.at).toLocaleDateString() : undefined} />)}</SurfaceRows> : <SurfaceState empty emptyLabel="No history" />}</SurfaceSection></>;
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
