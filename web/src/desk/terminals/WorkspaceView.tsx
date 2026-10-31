import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { ApiError, apiFetch, readableError } from "../../lib/api";
import { agentWord, flightLabel, reviewResult, useAgentFlights } from "../agentFlights";
import { aboutTarget, askAboutRef, askableKind, type AboutChip } from "../askAbout";
import { handRefOf, openHand } from "../agentHand";
import { MicButton } from "../components/MicButton";
import { WorkMenu, type WorkMenuEntry } from "../components/DeskMenu";
import { DeskEditor, type DeskEditorHandle } from "../components/DeskEditor";
import { RepositoryBrowserView } from "../components/RepositoryBrowserView";
import { useRepositoryBrowser } from "../components/RepositoryBrowserController";
import {
  fetchDiff,
  fetchFileRecord,
  fetchStatus,
  fetchTree,
  stageFiles,
  commit,
  writeFile,
  registerRepository,
  type RepoChange,
  type RepoStatus,
} from "../repository";
import { openAgentLane, openProjectRoom } from "../shell";
import { openRef } from "../openObject";
import { useDesk } from "../store";
import { objectByRef } from "../world";
import { normalizeRef } from "../screen/compose";
import { refreshTerminalInventory } from "./windows";
import { setWorkspaceSelection } from "./workspaceSelection";
import { readWorkspaceFileDraft, writeWorkspaceFileDraft } from "./workspaceDrafts";
import { capturedWorkspaceFileContent } from "./workspaceHandoff";
import {
  ActionNotice,
  CheckGadget,
  SurfaceRows,
  SurfaceRow,
  SurfaceState,
  SurfaceWell,
  ScrollHint,
  StringGadget,
} from "../surface";
import type { TerminalContext, TerminalDescriptor } from "./types";
import type { WorkspaceFace } from "./workspaceSelection";
import type { WorkspaceHandoffContext, WorkspaceHandoffPreparation } from "./workspaceHandoff";

interface WorkspaceViewProps {
  descriptor: TerminalDescriptor | null;
  face: WorkspaceFace;
  onChanges(): void;
  selectedProjectId: string | null;
  selectedProjectName: string | null;
  onRepositoryBound?(): void;
  onPrepareFileHandoff?(preparation: WorkspaceHandoffPreparation): void;
}

function fact(label: string, value: ReactNode) {
  return <SurfaceRow key={label} title={label} detail={value} />;
}

function contextWord(context: TerminalContext): string {
  if (context.status === "bound") return "Bound workspace";
  if (context.status === "worktree") return "Worktree only";
  if (context.status === "unavailable") return "Context unavailable";
  return "Unbound shell";
}

function originRef(origin: unknown): string | null {
  if (typeof origin === "string" && origin.includes(":")) return origin;
  if (!origin || typeof origin !== "object") return null;
  const row = origin as { kind?: unknown; id?: unknown };
  return typeof row.kind === "string" && typeof row.id === "string" ? `${row.kind}:${row.id}` : null;
}

type ResourceRow = { ref: string; title: string; unavailable?: boolean };

function resourceAboutTarget(ref: string, title: string): AboutChip | null {
  const known = aboutTarget(ref);
  if (known) return known;
  const [kind, ...rest] = ref.split(":");
  const id = rest.join(":");
  if (!id || !askableKind(kind) || !["note", "decision", "meeting"].includes(kind)) return null;
  return { id, kind, title: title.trim() || id, ref };
}

function ResourceAction({ resource, projectId, onOpen }: { resource: ResourceRow; projectId: string | null; onOpen(): void }) {
  const [menu, setMenu] = useState<{ x: number; y: number } | null>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const ref = normalizeRef(resource.ref);
  const openLabel = ref.startsWith("repository:") ? "Open files" : `Open ${resourceKind(ref).toLowerCase()}`;
  const about = resourceAboutTarget(ref, resource.title);
  const hand = handRefOf(ref);
  if (resource.unavailable) return <Button dense variant="ghost" onClick={onOpen}>Retry</Button>;
  const entries: WorkMenuEntry[] = [
    ...(about ? [{ type: "item" as const, id: "ask", label: "Ask about this", onSelect: () => {
      if (!askAboutRef(ref)) useDesk.getState().askAbout([about]);
      setMenu(null);
    } }] : []),
    ...(hand ? [{ type: "item" as const, id: "hand", label: "Hand to an agent", onSelect: () => { openHand({ ...hand, title: resource.title, projectId }); setMenu(null); } }] : []),
  ];
  if (!entries.length) return <Button dense variant="ghost" onClick={onOpen}>{openLabel}</Button>;
  return <>
    <span className="terminals-resource-actions">
      <Button dense variant="ghost" onClick={onOpen}>{openLabel}</Button>
      <Button
        ref={buttonRef}
        dense
        variant="ghost"
        aria-haspopup="menu"
        aria-expanded={Boolean(menu)}
        onClick={() => {
          const rect = buttonRef.current?.getBoundingClientRect();
          if (rect) setMenu({ x: rect.left, y: rect.bottom });
        }}
      >More</Button>
    </span>
    {menu ? <WorkMenu label={`Actions for ${resource.title}`} x={menu.x} y={menu.y} opener={buttonRef.current} autoFocus entries={entries} onClose={() => setMenu(null)} /> : null}
  </>;
}

function resourceKind(ref: string): string {
  const kind = normalizeRef(ref).split(":", 1)[0];
  return kind ? kind[0].toUpperCase() + kind.slice(1) : "Resource";
}

function ContextView({ descriptor, selectedProjectId, selectedProjectName, onRepositoryBound }: { descriptor: TerminalDescriptor; selectedProjectId: string | null; selectedProjectName: string | null; onRepositoryBound?: () => void }) {
  const context = descriptor.context;
  const briefRef = originRef(context.launch?.origin_ref);
  const alive = useRef(true);
  const descriptorIdRef = useRef(descriptor.id);
  descriptorIdRef.current = descriptor.id;
  const flights = useAgentFlights((state) => state.flights);
  const sessions = useAgentFlights((state) => state.sessions);
  const flight = context.launch ? flights.find((row) => row.launchId === context.launch?.id) ?? null : null;
  const session = context.launch ? sessions.find((row) => row.flight?.launchId === context.launch?.id) ?? null : null;
  const items = useDesk((state) => state.items);
  const [resources, setResources] = useState<ResourceRow[]>([]);
  const [resourcesError, setResourcesError] = useState<string | null>(null);
  const [resourceReadNonce, setResourceReadNonce] = useState(0);
  const [brief, setBrief] = useState<{ title: string; body: string } | null>(null);
  const [binding, setBinding] = useState(false);
  const [repositoryPath, setRepositoryPath] = useState(descriptor.current_path ?? "");
  const [registering, setRegistering] = useState(false);
  const [registerError, setRegisterError] = useState<string | null>(null);
  const [registered, setRegistered] = useState<string | null>(null);
  const bindingReceiptKey = context.source && selectedProjectId
    ? `terminal-workspace-binding:${context.source.id}:${selectedProjectId}`
    : "";
  const bindingReceipt = useDesk((state) => bindingReceiptKey ? state.drafts[bindingReceiptKey] ?? null : null);
  const setDeskDraft = useDesk((state) => state.setDraft);
  useEffect(() => {
    alive.current = true;
    return () => { alive.current = false; };
  }, []);
  useEffect(() => {
    setRepositoryPath(descriptor.current_path ?? "");
    setRegisterError(null);
    setRegistered(null);
    setRegistering(false);
  }, [descriptor.id, descriptor.current_path]);
  useEffect(() => {
    let alive = true;
    setResources([]);
    setResourcesError(null);
    if (!context.project) return () => { alive = false; };
    void apiFetch<{ resources?: Array<Record<string, unknown>> }>(`/api/projects/${encodeURIComponent(context.project.id)}/resources`)
      .then((answer) => {
        if (!alive) return;
        const refs = (answer.resources ?? []).map((resource) => String(resource.resource_ref ?? resource.ref ?? ""))
          .filter((ref) => ref.includes(":"));
        void Promise.all(refs.map(async (ref) => {
          const normalized = normalizeRef(ref);
          if (normalized === `repository:${context.source?.id ?? ""}`) return { ref, title: context.source?.name ?? "Repository" };
          const object = objectByRef(items, normalized);
          if (object && object.title.trim() && object.title.trim() !== normalized.slice(normalized.indexOf(":") + 1))
            return { ref, title: object.title };
          if (!normalized.startsWith("note:")) return { ref, title: `${resourceKind(ref)} · Not read`, unavailable: true };
          try {
            const note = await apiFetch<{ note?: { title?: string } }>(`/api/notes/${encodeURIComponent(normalized.slice("note:".length))}`);
            return note.note?.title ? { ref, title: note.note.title } : { ref, title: "Note · Not read", unavailable: true };
          } catch {
            return { ref, title: "Note · Not read", unavailable: true };
          }
        })).then((resolved) => {
          if (alive) setResources(resolved);
        });
      })
      .catch((error: unknown) => {
        if (alive) setResourcesError(error instanceof Error ? error.message : "Project resources unavailable");
      });
    return () => { alive = false; };
  }, [context.project?.id, context.source?.id, context.source?.name, items, resourceReadNonce]);
  useEffect(() => {
    if (context.launch) void useAgentFlights.getState().load();
  }, [context.launch?.id]);
  useEffect(() => {
    let alive = true;
    const ref = briefRef;
    const indexed = ref ? objectByRef(items, normalizeRef(ref)) : null;
    const indexedBody = indexed && "bodyMarkdown" in indexed.ref ? String(indexed.ref.bodyMarkdown ?? "") : "";
    setBrief(null);
    if (indexed) setBrief({ title: indexed.title, body: indexedBody });
    if (!ref?.startsWith("note:")) return () => { alive = false; };
    void apiFetch<{ note?: { title?: string; body_markdown?: string } }>(`/api/notes/${encodeURIComponent(ref.slice("note:".length))}`)
      .then((answer) => {
        if (!alive) return;
        setBrief({ title: String(answer.note?.title ?? indexed?.title ?? "Brief"), body: String(answer.note?.body_markdown ?? indexedBody) });
      })
      .catch(() => undefined);
    return () => { alive = false; };
  }, [briefRef, items]);
  const openProject = () => context.project && openProjectRoom(context.project.id);
  const openLaunch = () => context.launch && openAgentLane(context.launch.id);
  const openProgram = () => { if (context.program) openRef(`program:${context.program.id}`); };
  const openOrigin = () => { const ref = originRef(context.launch?.origin_ref); if (ref) openRef(ref); };
  const openResource = (ref: string) => {
    if (normalizeRef(ref) === `repository:${context.source?.id ?? ""}`) {
      setWorkspaceSelection({ sessionId: descriptor.id, face: "files" });
      useDesk.getState().openSurfaceWindow("open-terminals");
      return;
    }
    openRef(ref);
  };
  const bindRepository = async () => {
    const projectId = selectedProjectId;
    const sourceId = context.source?.id;
    if (!projectId || !sourceId || binding) return;
    const receiptProjectId = projectId;
    const receiptSourceId = sourceId;
    setBinding(true);
    try {
      await apiFetch(`/api/projects/${encodeURIComponent(receiptProjectId)}/resources/${encodeURIComponent(`repository:${receiptSourceId}`)}`, { method: "PUT", json: {} });
      if (!alive.current) return;
      if (bindingReceiptKey === `terminal-workspace-binding:${receiptSourceId}:${receiptProjectId}`)
        setDeskDraft(bindingReceiptKey, "Repository added to project");
      onRepositoryBound?.();
      void refreshTerminalInventory();
    } catch (error) {
      if (!alive.current) return;
      if (bindingReceiptKey === `terminal-workspace-binding:${receiptSourceId}:${receiptProjectId}`)
        setDeskDraft(bindingReceiptKey, error instanceof Error ? error.message : "Repository was not added");
    } finally { setBinding(false); }
  };
  const registerFolder = async () => {
    const capturedDescriptorId = descriptor.id;
    const capturedPath = repositoryPath.trim();
    if (!capturedPath || registering) return;
    setRegistering(true);
    setRegisterError(null);
    setRegistered(null);
    try {
      await registerRepository({ path: capturedPath });
      if (!alive.current) return;
      void refreshTerminalInventory();
      if (descriptorIdRef.current !== capturedDescriptorId) return;
      setRegistered("Folder registered");
    } catch (error) {
      if (!alive.current || descriptorIdRef.current !== capturedDescriptorId) return;
      setRegisterError(readableError(error));
    } finally {
      if (alive.current && descriptorIdRef.current === capturedDescriptorId) setRegistering(false);
    }
  };
  const stateWords = flight ? (flightLabel(flight) ?? agentWord(flight.agent)) : context.launch ? "Open agent" : null;
  const needsWords = session?.question || (session?.blocked ? "Needs you" : flight?.state === "waiting" ? "Waiting for your answer" : null);
  const review = flight?.review ? reviewResult(flight.review) : null;
  const remainingFindings = review ? review.findingsLeft.reduce((count) => count + 1, 0) : 0;
  const reviewWords = flight?.review
    ? review ? (remainingFindings > 0 ? `${remainingFindings} findings left` : "Review complete") : "Review in progress"
    : null;
  const briefTitle = brief?.title || flight?.title || null;
  const toolsWords = context.mcp?.status === "configured"
    ? `Configured${context.mcp.server ? ` · ${context.mcp.server}` : ""}${context.mcp.read_only ? " · read only" : ""}`
    : null;
  const registrationPanel = !context.source && descriptor.current_path ? <SurfaceWell head={<span>Register workspace folder</span>}>
    <SurfaceRows>{fact("State", "Unbound shell")}</SurfaceRows>
    <div className="terminals-workspace-actions">
      <StringGadget label="Repository folder" value={repositoryPath} onChange={setRepositoryPath} placeholder="A repository folder on this Mac" disabled={registering} />
      <Button dense variant="secondary" loading={registering} disabled={!repositoryPath.trim() || registering} onClick={() => void registerFolder()}>Register folder</Button>
    </div>
    {registerError ? <ActionNotice tone="danger" role="alert">{registerError}</ActionNotice> : null}
    {registered ? <ActionNotice tone="ok">{registered}</ActionNotice> : null}
  </SurfaceWell> : null;
  const bindingPanel = context.source && !context.project ? <SurfaceWell head={<span>Project binding</span>}>
    <div className="terminals-workspace-actions">
      {selectedProjectId
        ? <><span>Use {context.source.name} in {selectedProjectName || "this project"}</span><Button dense variant="secondary" loading={binding} disabled={binding} onClick={() => void bindRepository()}>Use repository in project</Button></>
        : <span>Choose a Project above to file {context.source.name}.</span>}
    </div>
    {bindingReceipt ? <ActionNotice tone={bindingReceipt === "Repository added to project" ? "ok" : "danger"}>{bindingReceipt}</ActionNotice> : null}
  </SurfaceWell> : null;
  const resourcesPanel = context.project ? <SurfaceWell head={<span>Project notes and resources</span>}>
    {resourcesError ? <ActionNotice tone="danger">{resourcesError} <Button dense variant="ghost" onClick={() => { setResourcesError(null); setResourceReadNonce((value) => value + 1); }}>Retry</Button></ActionNotice> : null}
    {resources.length ? <SurfaceRows>{resources.map((resource) => <SurfaceRow key={resource.ref} title={resource.title} verbs={resource.unavailable
      ? <Button dense variant="ghost" onClick={() => { setResourcesError(null); setResourceReadNonce((value) => value + 1); }}>Retry</Button>
      : normalizeRef(resource.ref) === `repository:${context.source?.id ?? ""}`
        ? <Button dense variant="ghost" onClick={() => openResource(resource.ref)}>Files</Button>
        : <ResourceAction resource={resource} projectId={context.project?.id ?? selectedProjectId} onOpen={() => openResource(resource.ref)} />} />)}</SurfaceRows> : resourcesError ? null : <span className="quiet">No project resources</span>}
  </SurfaceWell> : null;
  if (context.status === "unavailable") return <div className="terminals-workspace-context" data-testid="terminal-workspace-context">
    <SurfaceState error="Context unavailable. Session stays open. Retry inventory." onRetry={() => void refreshTerminalInventory()} retryLabel="Retry" />
  </div>;
  if (context.status === "unbound") return <div className="terminals-workspace-context" data-testid="terminal-workspace-context">
    <SurfaceState empty={false}>{registrationPanel ?? <SurfaceWell head={<span>Unbound shell</span>}><SurfaceRows>{fact("State", "Folder not available")}</SurfaceRows></SurfaceWell>}</SurfaceState>
  </div>;
  if (context.status === "worktree") return <div className="terminals-workspace-context" data-testid="terminal-workspace-context">
    <SurfaceState empty={false}>
      <SurfaceWell head={<span>Worktree only</span>}>
        <SurfaceRows>
          {context.source ? fact("Source", context.source.name) : null}
          {context.worktree?.branch ? fact("Branch", context.worktree.branch) : null}
        </SurfaceRows>
      </SurfaceWell>
      {bindingPanel}
    </SurfaceState>
  </div>;
  return <div className="terminals-workspace-context" data-testid="terminal-workspace-context">
    <SurfaceState empty={false}>
      <SurfaceWell head={<span>Bound workspace</span>}>
        <SurfaceRows>
          {context.project ? fact("Project", <Button dense variant="ghost" onClick={openProject}>{context.project.name}</Button>) : null}
          {context.source ? fact("Source", context.source.name) : null}
          {context.worktree?.branch ? fact("Branch", context.worktree.branch) : null}
          {briefTitle ? fact("Brief", originRef(context.launch?.origin_ref) ? <Button dense variant="ghost" onClick={openOrigin}>{briefTitle}</Button> : briefTitle) : null}
          {context.launch && stateWords ? fact("Agent", <Button dense variant="ghost" onClick={openLaunch}>{stateWords}</Button>) : null}
          {needsWords ? fact("Needs you", needsWords) : null}
          {reviewWords ? fact("Review", reviewWords) : null}
          {context.program ? fact("Program", <Button dense variant="ghost" onClick={openProgram}>{context.program.title}{context.program.step_ordinal != null ? ` · Step ${context.program.step_ordinal}` : ""}</Button>) : null}
          {toolsWords ? fact("HoldSpeak tools", toolsWords) : null}
        </SurfaceRows>
      </SurfaceWell>
      {brief?.body ? <SurfaceWell head={<span>Brief</span>}><p className="terminals-workspace-brief">{brief.body.slice(0, 600)}</p></SurfaceWell> : null}
      {resourcesPanel}
    </SurfaceState>
  </div>;
}

function ChangesView({ repositoryId, worktreeId }: { repositoryId: string; worktreeId?: string | null }) {
  const alive = useRef(true);
  const generation = useRef(0);
  const [status, setStatus] = useState<RepoStatus | null>(null);
  const [diff, setDiff] = useState<{ text: string; truncated: boolean } | null>(null);
  const [stagedDiff, setStagedDiff] = useState<{ text: string; truncated: boolean } | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryAction, setRetryAction] = useState<"refresh" | "stage" | "commit">("refresh");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [receipt, setReceipt] = useState<string | null>(null);
  const commitDraftKey = `terminal-workspace-commit:${repositoryId}:${worktreeId ?? ""}`;
  const message = useDesk((state) => state.drafts[commitDraftKey] ?? "");
  const setDeskDraft = useDesk((state) => state.setDraft);
  const scope = useMemo(() => worktreeId ? { worktreeId } : undefined, [worktreeId]);
  const refresh = async () => {
    const request = ++generation.current;
    setRetryAction("refresh");
    setBusy(true); setError(null);
    try {
      const [nextStatus, nextDiff, nextStagedDiff] = await Promise.all([
        fetchStatus(repositoryId, scope),
        fetchDiff(repositoryId, scope),
        fetchDiff(repositoryId, { ...scope, staged: true }),
      ]);
      if (!alive.current || request !== generation.current) return;
      setStatus(nextStatus);
      setDiff({ text: nextDiff.diff, truncated: nextDiff.truncated });
      setStagedDiff({ text: nextStagedDiff.diff, truncated: nextStagedDiff.truncated });
    } catch (caught) {
      if (!alive.current || request !== generation.current) return;
      setError(caught instanceof Error ? caught.message : "Changes are unavailable");
    } finally { if (alive.current && request === generation.current) setBusy(false); }
  };
  useEffect(() => {
    alive.current = true;
    void refresh();
    return () => { alive.current = false; generation.current += 1; };
  }, [repositoryId, worktreeId]);
  const changes: RepoChange[] = status?.changes ?? [];
  const stagedChanges = changes.filter((change) => {
    const index = change.index_status.trim();
    return Boolean(index && index !== "?");
  });
  const workingDiff = Boolean(diff?.text);
  const stagedDiffText = Boolean(stagedDiff?.text);
  const changeWords = (change: RepoChange): string => {
    const index = change.index_status.trim();
    const worktree = change.worktree_status.trim();
    const codes = `${index}${worktree}`;
    if (codes.includes("R")) return "Renamed";
    if (codes.includes("D")) return "Deleted";
    if (codes.includes("?")) return "New file";
    if (index && worktree) return "Staged and changed again";
    if (codes.includes("A")) return "New file";
    if (index) return "Staged";
    if (worktree) return "Changed";
    return "Changed";
  };
  const toggle = (path: string) => setSelected((current) => {
    const next = new Set(current);
    if (next.has(path)) next.delete(path); else next.add(path);
    return next;
  });
  const stage = async () => {
    if (!selected.size) return;
    const capturedPaths = [...selected];
    const request = ++generation.current;
    setBusy(true); setError(null);
    try {
      await stageFiles(repositoryId, capturedPaths, scope);
      if (!alive.current || request !== generation.current) return;
      setSelected(new Set());
      const stagedCount = capturedPaths.reduce((count) => count + 1, 0);
      setReceipt(`${stagedCount} ${stagedCount === 1 ? "file" : "files"} staged`);
      await refresh();
    } catch (caught) {
      if (!alive.current || request !== generation.current) return;
      setRetryAction("stage");
      const reason = caught instanceof Error && caught.message ? ` · ${caught.message}` : "";
      setError(`Could not stage selected files. Your selection stays here. Retry Stage in Changes.${reason}`);
      setBusy(false);
    }
  };
  const commitSelected = async () => {
    const capturedDraft = message;
    const capturedMessage = capturedDraft.trim();
    if (!capturedMessage || !stagedChanges.length) return;
    setBusy(true); setError(null);
    try {
      await commit(repositoryId, capturedMessage, scope);
      if (!alive.current) return;
      if (useDesk.getState().drafts[commitDraftKey] === capturedDraft) setDeskDraft(commitDraftKey, null);
      setReceipt("Changes committed");
      await refresh();
    } catch (caught) {
      if (!alive.current) return;
      setRetryAction("commit");
      const reason = caught instanceof Error && caught.message ? ` · ${caught.message}` : "";
      setError(`Could not commit changes. Your staged changes and commit message stay here. Retry Commit in Changes.${reason}`);
      setBusy(false);
    }
  };
  if (busy && !status) return <SurfaceState loading />;
  if (error && !status) return <SurfaceState error={error} onRetry={() => void refresh()} />;
  return <div className="terminals-workspace-changes" data-testid="terminal-workspace-changes">
    {error ? <ActionNotice tone="danger" role="alert">{error} <Button dense variant="ghost" onClick={() => void (retryAction === "stage" ? stage() : retryAction === "commit" ? commitSelected() : refresh())}>Retry</Button></ActionNotice> : null}
    {receipt ? <ActionNotice tone="ok">{receipt}</ActionNotice> : null}
    <SurfaceRows>
      {changes.length ? changes.map((change) => <SurfaceRow
        key={change.path}
        title={<span className="terminals-change-choice"><CheckGadget label={`Select ${change.path} for Git`} checked={selected.has(change.path)} disabled={busy} onChange={() => toggle(change.path)} /> {change.path}</span>}
        detail={changeWords(change)}
      />) : <SurfaceRow title="No changed files" detail={status?.branch ? `On ${status.branch}` : "The worktree is clean"} quiet />}
    </SurfaceRows>
    {workingDiff || !stagedDiffText ? <SurfaceWell head={<span>Working tree diff{diff?.truncated ? " · shortened" : ""}</span>}>
      <pre className="terminals-workspace-diff">{diff?.text || "No changes"}</pre>
    </SurfaceWell> : null}
    {stagedDiffText ? <SurfaceWell head={<span>Staged diff{stagedDiff?.truncated ? " · shortened" : ""}</span>}>
      <pre className="terminals-workspace-diff">{stagedDiff?.text}</pre>
    </SurfaceWell> : null}
    <div className="terminals-workspace-actions">
      <Button dense variant="secondary" disabled={!selected.size || busy} onClick={() => void stage()}>Stage {selected.size || ""}</Button>
      <StringGadget label="Commit message" value={message} onChange={(value) => setDeskDraft(commitDraftKey, value)} placeholder="Commit message" disabled={busy} />
      <Button dense disabled={!message.trim() || !stagedChanges.length || busy} onClick={() => void commitSelected()}>Commit</Button>
    </div>
  </div>;
}

function FilesView({ repositoryId, worktreeId, project, source, worktree, onChanges, onPrepareFileHandoff }: {
  repositoryId: string;
  worktreeId?: string | null;
  project: WorkspaceHandoffContext["project"];
  source: WorkspaceHandoffContext["source"];
  worktree: WorkspaceHandoffContext["worktree"];
  onChanges(): void;
  onPrepareFileHandoff?: (preparation: WorkspaceHandoffPreparation) => void;
}) {
  const alive = useRef(true);
  const hashes = useRef(new Map<string, string | null>());
  const readHashes = useRef(new Map<string, { content: string; sha256: string | null }>());
  const previewRef = useRef<HTMLPreElement>(null);
  const editorRef = useRef<DeskEditorHandle | null>(null);
  const currentFileKeyRef = useRef("");
  const inspectionGenerationRef = useRef(0);
  const [editing, setEditing] = useState(false);
  const [draftValue, setDraftValue] = useState("");
  const [saving, setSaving] = useState(false);
  const [readingLatest, setReadingLatest] = useState(false);
  const [latestDisk, setLatestDisk] = useState<{ content: string; sha256: string | null } | null>(null);
  const [conflictNeedsReadLatest, setConflictNeedsReadLatest] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);
  const scope = useMemo(() => worktreeId ? { worktreeId } : undefined, [worktreeId]);
  const fileDraftKey = (path: string) => `terminal-workspace:${repositoryId}:${worktreeId ?? ""}:${path}`;
  const adapter = useMemo(() => ({
    tree: (path: string) => fetchTree(repositoryId, path, scope),
    file: async (path: string) => {
      const answer = await fetchFileRecord(repositoryId, path, scope);
      const retained = readWorkspaceFileDraft(useDesk.getState().drafts[fileDraftKey(path)]);
      // The controller owns stale-read acceptance. Keep the bytes with the
      // hash so a late answer can never lend its revision to newer inspection
      // text at prepare time.
      readHashes.current.set(path, { content: answer.content, sha256: answer.sha256 });
      hashes.current.set(path, retained ? retained.baseSha256 : answer.sha256);
      return answer.content;
    },
  }), [repositoryId, scope]);
  const browser = useRepositoryBrowser(adapter);
  const inspection = browser.entry.inspection;
  const draftKey = inspection ? `terminal-workspace:${repositoryId}:${worktreeId ?? ""}:${inspection.path}` : "";
  if (currentFileKeyRef.current !== draftKey) {
    currentFileKeyRef.current = draftKey;
    inspectionGenerationRef.current += 1;
  }
  const rawDraft = useDesk((state) => draftKey ? state.drafts[draftKey] ?? null : null);
  const retainedDraft = readWorkspaceFileDraft(rawDraft);
  const setDeskDraft = useDesk((state) => state.setDraft);
  useEffect(() => {
    if (!inspection) return;
    setDraftValue(retainedDraft?.text ?? inspection.content);
  }, [inspection?.path, inspection?.content, rawDraft, draftKey]);
  useEffect(() => {
    setEditing(false);
    setSaving(false);
    setReadingLatest(false);
    setLatestDisk(null);
    setConflictNeedsReadLatest(false);
    setSaveError(null);
    setSaved(null);
  }, [draftKey]);
  useEffect(() => {
    alive.current = true;
    return () => { alive.current = false; };
  }, []);
  const voiceDraftKey = inspection ? `terminal-workspace-voice:${draftKey}` : "";
  const retainedVoice = useDesk((state) => voiceDraftKey ? state.drafts[voiceDraftKey] ?? "" : "");
  const keepVoice = (text: string) => {
    if (!voiceDraftKey || !text.trim()) return;
    const prior = useDesk.getState().drafts[voiceDraftKey] ?? "";
    useDesk.getState().setDraft(voiceDraftKey, prior ? `${prior}\n\n${text.trim()}` : text.trim());
  };
  const bindVoice = () => {
    const capturedKey = currentFileKeyRef.current;
    const target = editorRef.current?.captureVoiceTarget() ?? null;
    return (text: string) => {
      if (editorRef.current && target && currentFileKeyRef.current === capturedKey && editorRef.current.insertAtCapturedTarget(target, text)) return;
      keepVoice(text);
    };
  };
  const insertRetainedVoice = () => {
    if (!retainedVoice || !voiceDraftKey) return;
    const capturedKey = currentFileKeyRef.current;
    const editor = editorRef.current;
    const target = editor?.captureVoiceTarget() ?? null;
    const inserted = Boolean(editor && target && currentFileKeyRef.current === capturedKey
      && editor.insertAtCapturedTarget(target, retainedVoice, { focus: true }));
    if (inserted) useDesk.getState().setDraft(voiceDraftKey, null);
  };
  const readLatestFile = async () => {
    const current = browser.entry.inspection;
    if (!current || readingLatest) return;
    const capturedPath = current.path;
    const capturedDraftKey = draftKey;
    const capturedGeneration = inspectionGenerationRef.current;
    setReadingLatest(true);
    setLatestDisk(null);
    setSaveError(null);
    setConflictNeedsReadLatest(true);
    try {
      const latest = await fetchFileRecord(repositoryId, capturedPath, scope);
      if (!alive.current || currentFileKeyRef.current !== capturedDraftKey || inspectionGenerationRef.current !== capturedGeneration) return;
      setLatestDisk({ content: latest.content, sha256: latest.sha256 });
      setConflictNeedsReadLatest(false);
    } catch (caught) {
      if (!alive.current || currentFileKeyRef.current !== capturedDraftKey || inspectionGenerationRef.current !== capturedGeneration) return;
      const reason = caught instanceof Error && caught.message ? ` · ${caught.message}` : "";
      setSaveError(`Could not read latest file in this worktree. Your edit stays in Files. Retry Read latest.${reason}`);
      setConflictNeedsReadLatest(true);
    } finally {
      if (alive.current && currentFileKeyRef.current === capturedDraftKey && inspectionGenerationRef.current === capturedGeneration)
        setReadingLatest(false);
    }
  };
  const save = async () => {
    if (!inspection || saving) return;
    const capturedPath = inspection.path;
    const capturedDraftKey = draftKey;
    const capturedGeneration = inspectionGenerationRef.current;
    const capturedText = draftValue;
    const reviewedSha256 = latestDisk?.sha256 ?? null;
    const hasReview = latestDisk !== null;
    const capturedBaseSha256 = reviewedSha256 ?? hashes.current.get(capturedPath) ?? null;
    setSaving(true); setSaveError(null); setSaved(null);
    setConflictNeedsReadLatest(false);
    if (hasReview) {
      hashes.current.set(capturedPath, capturedBaseSha256);
      setDeskDraft(capturedDraftKey, writeWorkspaceFileDraft({ text: capturedText, baseSha256: capturedBaseSha256 }));
      setLatestDisk(null);
    }
    try {
      const answer = await writeFile(repositoryId, capturedPath, capturedText, { ...scope, expectedSha256: capturedBaseSha256 });
      if (!alive.current) return;
      const next = answer && typeof answer === "object" && "sha256" in answer && typeof answer.sha256 === "string" ? answer.sha256 : null;
      if (browser.entry.inspection?.path !== capturedPath || currentFileKeyRef.current !== capturedDraftKey || inspectionGenerationRef.current !== capturedGeneration) return;
      hashes.current.set(capturedPath, next);
      setLatestDisk(null);
      if (useDesk.getState().drafts[capturedDraftKey] === writeWorkspaceFileDraft({ text: capturedText, baseSha256: capturedBaseSha256 }))
        useDesk.getState().setDraft(capturedDraftKey, null);
      setSaved("File saved");
      setEditing(false);
      browser.refresh();
    } catch (caught) {
      if (!alive.current || currentFileKeyRef.current !== capturedDraftKey || inspectionGenerationRef.current !== capturedGeneration) return;
      if (caught instanceof ApiError && caught.status === 409 && caught.message.includes("file changed before write")) {
        setLatestDisk(null);
        setConflictNeedsReadLatest(true);
        setSaveError("File changed in this worktree. Your edit stays in Files. Read latest, then Save reviewed edit.");
        return;
      }
      const reason = caught instanceof Error && caught.message ? ` · ${caught.message}` : "";
      setSaveError(`Could not save file. Your edit stays in Files. Retry Save in Files.${reason}`);
    } finally {
      if (alive.current && currentFileKeyRef.current === capturedDraftKey && inspectionGenerationRef.current === capturedGeneration)
        setSaving(false);
    }
  };
  const renderInspection = (current: NonNullable<typeof inspection>) => <SurfaceWell head={<span className="repo-browser-file-path">{current.path}</span>}>
    <div className="terminals-file-editor" data-testid="terminal-file-editor">
      <div className="terminals-file-editor-head">
        <span>{editing ? "Editing" : current.retained ? "Retained draft" : "Read only"}</span>
        {editing ? <MicButton label="Speak into file" draftScope={`terminal-workspace-voice-audio:${draftKey}`} bindText={bindVoice} onText={keepVoice} /> : null}
        {!editing && onPrepareFileHandoff ? <Button dense variant="ghost" data-testid="terminal-file-prepare-agent" onClick={() => {
          const read = readHashes.current.get(current.path);
          const freshRead = !current.retained && read?.content === current.content;
          const words = freshRead ? `Review ${current.path}` : `Review ${current.path} (read copy retained)`;
          onPrepareFileHandoff({
            words,
            context: {
              project,
              source,
              worktree,
              file: {
                path: current.path,
                content: freshRead ? capturedWorkspaceFileContent(current.content).text : null,
                revision: freshRead ? read?.sha256 ?? null : null,
              },
            },
          });
        }}>Prepare agent</Button> : null}
        {!editing && hashes.current.get(current.path) ? <Button dense variant="secondary" data-testid="terminal-file-edit" onClick={() => setEditing(true)}>Edit file</Button> : null}
      </div>
      {editing && retainedVoice ? <ActionNotice tone="info">Voice kept for this file <Button dense variant="ghost" onClick={insertRetainedVoice}>Insert</Button></ActionNotice> : null}
      {!editing && !hashes.current.get(current.path) ? <ActionNotice tone="info">Revision unavailable; draft stays. Refresh the worktree. <Button dense variant="ghost" onClick={browser.refresh}>Refresh</Button></ActionNotice> : null}
      {editing ? <>
        <DeskEditor ref={editorRef} value={draftValue} onChange={(value) => { const baseSha256 = hashes.current.get(current.path) ?? null; setDraftValue(value); setDeskDraft(draftKey, writeWorkspaceFileDraft({ text: value, baseSha256 })); }} editable={!saving} ariaLabel={`Edit ${current.path}`} showToolbar={false} lineWrapping={false} minHeight="calc(var(--desk-surface-row-h) * 5)" />
        {latestDisk ? <SurfaceWell head={<span>Latest on disk</span>}>
          <ScrollHint axis="y" scrollRef={previewRef}><pre className="terminals-workspace-diff" data-testid="terminal-latest-disk">{latestDisk.content}</pre></ScrollHint>
          <div className="terminals-workspace-actions">
            <span className="quiet">Latest revision loaded. Your edit stays here.</span>
            <Button dense variant="ghost" loading={readingLatest} disabled={readingLatest || saving} onClick={() => void readLatestFile()}>Read latest</Button>
          </div>
        </SurfaceWell> : null}
        <div className="terminals-workspace-actions">
          <Button dense variant="ghost" disabled={saving} onClick={() => { setEditing(false); setDraftValue(current.content); setDeskDraft(draftKey, null); hashes.current.delete(current.path); browser.refresh(); }}>Cancel</Button>
          <Button dense variant="primary" loading={saving} disabled={saving || conflictNeedsReadLatest} onClick={() => void save()}>{latestDisk ? "Save reviewed edit" : "Save file"}</Button>
        </div>
      </> : <ScrollHint axis="y" scrollRef={previewRef}>
        <pre ref={previewRef} className="repo-browser-file-content" data-testid="repo-file-content">{current.content}</pre>
      </ScrollHint>}
    </div>
  </SurfaceWell>;
  return <div className="terminals-workspace-files" data-testid="terminal-workspace-files">
    <div className="terminals-workspace-subtoolbar">
      <span>Files</span>
      <Button dense variant="ghost" onClick={onChanges}>Changes</Button>
    </div>
    {saveError ? <ActionNotice tone="danger" role="alert">{saveError} {conflictNeedsReadLatest
      ? <Button dense variant="ghost" loading={readingLatest} disabled={readingLatest || saving} onClick={() => void readLatestFile()}>Read latest</Button>
      : <Button dense variant="ghost" onClick={() => void save()}>Retry Save</Button>}</ActionNotice> : null}
    {saved ? <ActionNotice tone="ok">{saved}</ActionNotice> : null}
    <RepositoryBrowserView browser={browser} renderInspection={renderInspection} />
  </div>;
}

export function WorkspaceView({ descriptor, face, onChanges, selectedProjectId, selectedProjectName, onRepositoryBound, onPrepareFileHandoff }: WorkspaceViewProps) {
  if (face === "sessions") return null;
  if (!descriptor) return <SurfaceState empty emptyLabel="Choose a terminal session" emptyHint="Select a session to inspect its files and context." />;
  const context = descriptor.context;
  const repositoryId = context.source?.id ?? null;
  const worktreeId = context.worktree?.id ?? null;
  const workspaceReady = Boolean(repositoryId && worktreeId);
  return <section className="terminals-workspace" aria-label="Terminal workspace" data-testid="terminal-workspace">
    {!workspaceReady && face !== "context" ? <SurfaceState empty emptyLabel="No registered worktree" emptyHint="This terminal is live, but it has no source and worktree record." /> : null}
    {face === "files" && repositoryId && worktreeId ? <FilesView
      key={`${repositoryId}:${worktreeId}`}
      repositoryId={repositoryId}
      worktreeId={worktreeId}
      project={context.project}
      source={context.source ? { id: context.source.id, title: context.source.name } : null}
      worktree={context.worktree ? { id: context.worktree.id, branch: context.worktree.branch } : null}
      onChanges={onChanges}
      onPrepareFileHandoff={onPrepareFileHandoff}
    /> : null}
    {face === "changes" && repositoryId && worktreeId ? <ChangesView key={`${repositoryId}:${worktreeId}`} repositoryId={repositoryId} worktreeId={worktreeId} /> : null}
    {face === "context" ? <ContextView descriptor={descriptor} selectedProjectId={selectedProjectId} selectedProjectName={selectedProjectName} onRepositoryBound={onRepositoryBound} /> : null}
  </section>;
}
