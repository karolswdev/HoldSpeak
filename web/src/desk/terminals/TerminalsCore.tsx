import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { Button } from "../../components/signal/Signal";
import { apiFetch, apiRequest } from "../../lib/api";
import { StartAgent } from "../conductor/StartAgent";
import { useAgentFlights } from "../agentFlights";
import { ActionNotice, CycleGadget, ListDay, ListRow, ListView, StatusBar, StringGadget, SurfaceState, SurfaceWings, ToolGlyph, Toolbar, ToolbarFold, countWords, useWindowInterior, useWindowWings } from "../surface";
import { useDesk } from "../store";
import { gatherFront } from "../compositor/useCompositor";
import {
  refreshTerminalInventory,
  subscribeTerminalInventory,
  terminalInventorySnapshot,
  terminalWindowId,
  type TerminalInventoryState,
} from "./windows";
import type { TerminalDescriptor } from "./types";
import { WorkspaceView } from "./WorkspaceView";
import { WorkspaceOverview } from "./WorkspaceOverview";
import type { WorkspaceHandoffPreparation } from "./workspaceHandoff";
import {
  queueWorkspaceLaunch,
  bumpWorkspaceRequestEpoch,
  cancelWorkspaceLaunch,
  resolveWorkspaceLaunch,
  selectWorkspaceFace,
  selectWorkspaceSession,
  setWorkspaceSelection,
  setWorkspaceSelectionQuiet,
  subscribeWorkspaceSelection,
  workspaceSelectionSnapshot,
  type WorkspaceFace,
} from "./workspaceSelection";
import "./terminals.css";

function useTerminalInventory() {
  const state = useSyncExternalStore(
    subscribeTerminalInventory,
    terminalInventorySnapshot,
    terminalInventorySnapshot,
  );
  useEffect(() => { void refreshTerminalInventory(); }, []);
  return state;
}

function stateWord(descriptor: TerminalDescriptor): string {
  const state = descriptor.state.trim().toLowerCase();
  if (!state || state === "live" || state === "working") return "Live";
  if (state === "waiting" || state === "awaiting_response" || state === "needs_you") return "Needs you";
  if (state === "done" || state === "checked") return "Done";
  return state.replaceAll("_", " ");
}

function contextOriginRef(value: unknown): string | null {
  if (typeof value === "string" && value.includes(":")) return value;
  if (!value || typeof value !== "object") return null;
  const row = value as { kind?: unknown; id?: unknown };
  return typeof row.kind === "string" && typeof row.id === "string" ? `${row.kind}:${row.id}` : null;
}

const terminalInventoryError = "Cannot read terminals. Open views kept. Press Retry.";
const terminalTmuxAbsent = "Terminal inventory unavailable. Open views kept. Press Retry.";

function inventoryFailure(status: TerminalInventoryState["status"], detail: string | null): string {
  const message = status === "tmux_absent" ? terminalTmuxAbsent : terminalInventoryError;
  return detail ? `${message} · ${detail}` : message;
}

function tileTerminals(): void {
  const windows = useDesk.getState().terminalWindows;
  if (windows.length < 2) return;
  // The compositor's Room gather is the existing OS arrangement method. Bring
  // one terminal front first so the room is terminals; non-terminal windows
  // keep their geometry and are not part of the gathered group.
  useDesk.getState().focusPanel(terminalWindowId(windows[windows.length - 1].id));
  gatherFront();
}

function terminalRowState(descriptor: TerminalDescriptor) {
  const state = descriptor.state.trim().toLowerCase();
  const tone = state === "waiting" || state === "awaiting_response" || state === "needs_you"
    ? "warn" as const
    : state === "done" || state === "checked"
      ? "ok" as const
      : state === "live" || state === "working"
        ? "info" as const
        : "idle" as const;
  return { word: stateWord(descriptor), tone, live: tone === "info" };
}

function TerminalRow({
  descriptor,
  open,
  selected,
  onOpen,
}: {
  descriptor: TerminalDescriptor;
  open: boolean;
  selected: boolean;
  onOpen(): void;
}) {
  const rowState = terminalRowState(descriptor);
  return <ListRow
    glyph={<ToolGlyph kind="engine" />}
    name={descriptor.label || descriptor.session || "Terminal"}
    meta={[descriptor.agent !== "pane" ? descriptor.agent : "Shell", descriptor.command].filter(Boolean).join(" · ")}
    state={{ word: rowState.word, tone: rowState.tone, live: rowState.live }}
    selected={selected}
    onOpen={onOpen}
    openLabel={`${open ? "Focus" : "Open"}: ${descriptor.label || descriptor.session || "Terminal"}`}
    openTestId={`terminal-open-${descriptor.id}`}
    data-testid={`terminal-row-${descriptor.id}`}
  />;
}

interface SpawnShellAnswer {
  status?: string;
  detail?: string;
  pane_id?: string;
}

async function spawnShell(name: string, cwd: string): Promise<SpawnShellAnswer> {
  const response = await apiRequest("/api/coders/factory/spawn", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ name, ...(cwd ? { cwd } : {}) }),
  });
  const body = await response.json().catch(() => ({})) as SpawnShellAnswer;
  if (!response.ok || body.status !== "spawned")
    throw new Error(body.detail || body.status || `HTTP ${response.status}`);
  return body;
}

function NewShell({
  name,
  cwd,
  onNameChange,
  onCwdChange,
  onCreated,
  onCancel,
}: {
  name: string;
  cwd: string;
  onNameChange(next: string): void;
  onCwdChange(next: string): void;
  onCreated(descriptorId?: string): void;
  onCancel(): void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const spawn = async () => {
    const clean = name.trim();
    if (!clean || busy) return;
    setBusy(true);
    setError(null);
    try {
      const answer = await spawnShell(clean, cwd.trim());
      await refreshTerminalInventory();
      const sessions = terminalInventorySnapshot().sessions;
      const descriptor = answer.pane_id
        ? sessions.find((row) => row.pane_id === answer.pane_id)
        : sessions.find((row) => row.session === clean);
      setBusy(false);
      onCreated(descriptor?.id);
    } catch (caught) {
      setBusy(false);
      setError(caught instanceof Error ? caught.message : "The shell was not started.");
      return;
    }
  };
  return (
    <div className="terminals-new-shell" data-testid="terminal-new-shell">
      <StringGadget label="Shell name" value={name} onChange={onNameChange} placeholder="Name this shell" />
      <StringGadget label="Folder (optional)" value={cwd} onChange={onCwdChange} placeholder="Local folder" />
      {error ? <p className="terminals-inline-error" role="alert">{error}</p> : null}
      <div className="terminals-form-verbs">
        <Button dense variant="ghost" disabled={busy} onClick={onCancel}>Cancel</Button>
        <Button dense variant="primary" loading={busy} disabled={!name.trim() || busy} onClick={() => void spawn()}>
          <ToolGlyph kind="new" />
          Create shell
        </Button>
      </div>
    </div>
  );
}

export function TerminalsCore() {
  useWindowInterior("list");
  const inventory = useTerminalInventory();
  const terminalWindows = useDesk((state) => state.terminalWindows);
  const [query, setQuery] = useState("");
  const [newShell, setNewShell] = useState(false);
  const [startingAgent, setStartingAgent] = useState(false);
  const [newShellName, setNewShellName] = useState("");
  const [newShellCwd, setNewShellCwd] = useState("");
  const [agentPreparation, setAgentPreparation] = useState<WorkspaceHandoffPreparation | null>(null);
  const [projectOptions, setProjectOptions] = useState<Array<{ value: string; label: string }>>([]);
  const [projectRepositoryIds, setProjectRepositoryIds] = useState<Set<string>>(new Set());
  const [projectResourceRevision, setProjectResourceRevision] = useState(0);
  const [handoffTimedOut, setHandoffTimedOut] = useState<Record<string, boolean>>({});
  const [pendingRetry, setPendingRetry] = useState(0);
  const selection = useSyncExternalStore(subscribeWorkspaceSelection, workspaceSelectionSnapshot, workspaceSelectionSnapshot);
  const flights = useAgentFlights((state) => state.flights);
  useEffect(() => {
    let alive = true;
    void apiFetch<{ projects?: Array<Record<string, unknown>> }>("/api/projects")
      .then((answer) => {
        if (!alive) return;
        setProjectOptions((answer.projects ?? []).filter((project) => project.archived !== true).map((project) => ({ value: String(project.id ?? ""), label: String(project.name ?? project.id ?? "Project") })).filter((project) => project.value));
      })
      .catch(() => { if (alive) setProjectOptions([]); });
    return () => { alive = false; };
  }, []);
  useEffect(() => {
    let alive = true;
    setProjectRepositoryIds(new Set());
    if (!selection.projectId) return () => { alive = false; };
    void apiFetch<{ resources?: Array<Record<string, unknown>> }>(`/api/projects/${encodeURIComponent(selection.projectId)}/resources`)
      .then((answer) => {
        if (!alive) return;
        const ids = (answer.resources ?? []).map((resource) => String(resource.resource_ref ?? resource.ref ?? ""))
          .filter((ref) => ref.startsWith("repository:"))
          .map((ref) => ref.slice("repository:".length));
        setProjectRepositoryIds(new Set(ids));
      })
      .catch(() => { if (alive) setProjectRepositoryIds(new Set()); });
    return () => { alive = false; };
  }, [selection.projectId, projectResourceRevision]);
  const queryText = query.trim().toLowerCase();
  const rows = useMemo(() => inventory.sessions.filter((descriptor) => {
    if (selection.projectId) {
      const boundToProject = descriptor.context.project?.id === selection.projectId;
      const filedSource = !descriptor.context.project && Boolean(descriptor.context.source?.id && projectRepositoryIds.has(descriptor.context.source.id));
      if (!boundToProject && !filedSource) return false;
    }
    if (!queryText) return true;
    return [descriptor.label, descriptor.session, descriptor.agent, descriptor.command, descriptor.current_path]
      .some((value) => value.toLowerCase().includes(queryText));
  }), [inventory.sessions, projectRepositoryIds, queryText, selection.projectId]);
  const openIds = useMemo(() => new Set(terminalWindows.map((window) => window.id)), [terminalWindows]);
  const groups = useMemo(() => {
    const grouped = new Map<string, TerminalDescriptor[]>();
    for (const descriptor of rows) {
      const key = descriptor.current_path || "Local shells";
      grouped.set(key, [...(grouped.get(key) ?? []), descriptor]);
    }
    return [...grouped.entries()];
  }, [rows]);

  const openTerminal = (descriptor: TerminalDescriptor) => {
    selectWorkspaceSession(descriptor, selection.face);
    useDesk.getState().openTerminalWindow(descriptor.id);
  };
  const selectedDescriptor = inventory.sessions.find((descriptor) => descriptor.id === selection.sessionId) ?? null;
  useWindowWings(
    <SurfaceWings
      wings={[{ id: "sessions", label: "Sessions" }, { id: "files", label: "Files" }, { id: "context", label: "Context" }]}
      active={selection.face === "changes" ? "files" : selection.face}
      onChange={(face) => selectWorkspaceFace(face as WorkspaceFace)}
    />,
    [selection.face],
  );
  const projects = useMemo(() => {
    const found = new Map<string, string>();
    projectOptions.forEach((project) => found.set(project.value, project.label));
    inventory.sessions.forEach((descriptor) => {
      if (descriptor.context.project) found.set(descriptor.context.project.id, descriptor.context.project.name);
    });
    return [...found.entries()].map(([value, label]) => ({ value, label }));
  }, [inventory.sessions, projectOptions]);
  const selectedProjectName = projects.find((project) => project.value === selection.projectId)?.label ?? null;
  const changeProject = (value: string) => {
    const nextProjectId = value === "all" ? null : value;
    const selected = selection.sessionId
      ? inventory.sessions.find((descriptor) => descriptor.id === selection.sessionId) ?? null
      : null;
    const selectedBoundProject = selected?.context.project?.id ?? null;
    // An unbound shell stays selected while the Project picker changes: that
    // picker is the filing target. A bound agent belongs to its authoritative
    // Project, so do not leave its checkout under a different Project label.
    if (nextProjectId && selectedBoundProject && selectedBoundProject !== nextProjectId) {
      setWorkspaceSelection({ projectId: nextProjectId, sessionId: null, face: "sessions" });
      return;
    }
    setWorkspaceSelection({ projectId: nextProjectId });
  };
  const sessionOptions = useMemo(() => {
    const options = rows.map((descriptor) => ({ value: descriptor.id, label: descriptor.label || descriptor.session || "Terminal" }));
    if (selectedDescriptor && !options.some((option) => option.value === selectedDescriptor.id))
      options.push({ value: selectedDescriptor.id, label: selectedDescriptor.label || selectedDescriptor.session || "Terminal" });
    return [{ value: "none", label: "Choose a session" }, ...options];
  }, [rows, selectedDescriptor]);
  useEffect(() => {
    selection.pendingHandoffs.forEach((pending) => {
      const pendingFlight = pending.kind === "queue" ? flights.find((flight) => flight.queueId === pending.id) : null;
      const launchId = pendingFlight?.launchId ?? (pending.kind === "launch" ? pending.id : null);
      const directMatch = launchId
        ? inventory.sessions.find((descriptor) => descriptor.context.launch?.id === launchId)
        : null;
      const originMatches = pending.kind === "queue" && pending.originRef && pending.projectId
        ? inventory.sessions.filter((descriptor) => descriptor.context.project?.id === pending.projectId
          && contextOriginRef(descriptor.context.launch?.origin_ref) === pending.originRef)
        : [];
      // Queued flights can lose their queue_id when the hub projects the
      // admitted launch. Join only on the captured Note + Project and only
      // when that producer-backed join is unique; never guess by cwd/name.
      const match = directMatch ?? (originMatches.length === 1 ? originMatches[0] : null);
      if (!match) return;
      const currentSelection = workspaceSelectionSnapshot();
      const before = currentSelection.pendingHandoffs.some((handoff) => handoff.id === pending.id);
      const ownsArrival = currentSelection.pendingHandoffs.find((handoff) => handoff.id === pending.id)?.epoch === currentSelection.requestEpoch;
      resolveWorkspaceLaunch(pending.id, match);
      if (before && ownsArrival) useDesk.getState().openTerminalWindow(match.id);
    });
  }, [flights, inventory.sessions, selection.pendingHandoffs]);
  useEffect(() => {
    if (!selection.pendingHandoffs.length) return;
    let active = true;
    let attempts = 0;
    let timer: number | null = null;
    const poll = () => {
      if (!active || !workspaceSelectionSnapshot().pendingHandoffs.length) return;
      if (attempts >= 20) {
        setHandoffTimedOut((current) => Object.fromEntries(workspaceSelectionSnapshot().pendingHandoffs.map((handoff) => [handoff.id, current[handoff.id] ?? true])));
        return;
      }
      attempts += 1;
      void refreshTerminalInventory();
      void useAgentFlights.getState().load();
      timer = window.setTimeout(poll, 1000);
    };
    poll();
    return () => { active = false; if (timer != null) window.clearTimeout(timer); };
  }, [selection.pendingHandoffs.length, pendingRetry]);
  const refresh = () => {
    void refreshTerminalInventory();
    if (selection.pendingHandoffs.length) {
      setHandoffTimedOut((current) => Object.fromEntries(selection.pendingHandoffs.map((handoff) => [handoff.id, false])));
      setPendingRetry((current) => current + 1);
      void useAgentFlights.getState().load();
    }
  };
  const inventoryLoading = inventory.status === "idle" || inventory.status === "loading";

  const formOpen = newShell || startingAgent;
  const secondaryActions = [
    { key: "refresh", label: "Refresh", glyph: "retry" as const, onSelect: refresh, testId: "terminal-refresh" },
    ...(terminalWindows.length > 1 ? [{ key: "tile", label: "Tile terminals", onSelect: tileTerminals, testId: "terminal-tile" }] : []),
  ];
  const inventoryStatusText = inventory.status === "ok"
    ? countWords(rows.length, "terminal")
    : inventoryLoading
      ? "Connecting"
      : inventory.status === "tmux_absent"
        ? "Terminal inventory unavailable"
        : "Cannot read terminals";
  const inventoryStatus = inventory.status === "ok" ? "ok" as const : inventoryLoading ? "info" as const : "warn" as const;

  return (
    <div className="terminals-core" data-testid="terminals-inventory" data-interior="list">
      <Toolbar label="Terminals" data-testid="terminals-toolbar">
        <Button
          variant={selectedDescriptor ? "secondary" : "primary"}
          dense
          onClick={() => {
            bumpWorkspaceRequestEpoch();
            setAgentPreparation(null);
            setNewShell((value) => !value);
            setStartingAgent(false);
          }}
          data-testid="terminal-new"
        >
          <ToolGlyph kind="new" />
          New terminal
        </Button>
        <Button
          variant={startingAgent ? "secondary" : "ghost"}
          dense
          onClick={() => {
            bumpWorkspaceRequestEpoch();
            setAgentPreparation(null);
            setStartingAgent((value) => !value);
            setNewShell(false);
          }}
          data-testid="terminal-start-agent"
        >
          <ToolGlyph kind="run" />
          Start an agent
        </Button>
        <ToolbarFold label="More" foldAt="medium" verbs={secondaryActions} data-testid="terminal-more" />
        {!formOpen && projects.length ? <CycleGadget label="Project" value={selection.projectId ?? "all"} options={[{ value: "all", label: "All projects" }, ...projects]} onChange={changeProject} /> : null}
        {!formOpen && selection.face !== "sessions" ? <CycleGadget label="Session" value={selection.sessionId ?? "none"} options={sessionOptions} onChange={(value) => { const descriptor = inventory.sessions.find((row) => row.id === value); if (descriptor) selectWorkspaceSession(descriptor, selection.face); }} data-testid="terminal-session-select" /> : null}
      </Toolbar>

      {formOpen ? (
        newShell ? <NewShell
          name={newShellName}
          cwd={newShellCwd}
          onNameChange={setNewShellName}
          onCwdChange={setNewShellCwd}
          onCancel={() => setNewShell(false)}
          onCreated={(descriptorId) => {
            setNewShell(false);
            setNewShellName("");
            setNewShellCwd("");
            if (descriptorId) useDesk.getState().openTerminalWindow(descriptorId);
            refresh();
          }}
        /> : (
          <>
          <div className="terminals-start-agent">
            <StartAgent
              initialProjectId={agentPreparation ? agentPreparation.context.project?.id ?? null : selection.projectId}
              preparation={agentPreparation}
              onCancel={() => { bumpWorkspaceRequestEpoch(); setStartingAgent(false); }}
              onStarting={() => workspaceSelectionSnapshot().requestEpoch}
              onStarted={(row, started) => {
                const requestEpoch = started?.requestEpoch ?? workspaceSelectionSnapshot().requestEpoch;
                const ownsStart = workspaceSelectionSnapshot().requestEpoch === requestEpoch;
                if (ownsStart) setStartingAgent(false);
                if (ownsStart) setAgentPreparation(null);
                const prefix = row?.split(":", 1)[0];
                const id = row?.slice(prefix ? prefix.length + 1 : 0) ?? "";
                const startedProject = started?.projectId ?? selection.projectId;
                if (row && id) {
                  setHandoffTimedOut((current) => ({ ...current, [id]: false }));
                  if (ownsStart)
                    setWorkspaceSelectionQuiet({ projectId: startedProject, sessionId: null, face: "sessions" });
                  queueWorkspaceLaunch(id, startedProject, prefix === "queue" ? "queue" : "launch", requestEpoch,
                    started?.noteId ? `note:${started.noteId}` : null);
                }
                refresh();
              }}
            />
          </div>
          </>
        )
      ) : selection.face === "sessions" ? <>
      <div className="terminals-search">
        <StringGadget label="Find a session or folder" value={query} onChange={setQuery} placeholder="Find a session or folder" />
      </div>
      {selection.pendingHandoffs.map((pending) => <ActionNotice key={`${pending.kind}:${pending.id}`} tone="info" data-testid={`terminal-handoff-pending-${pending.id}`}>
        <span>{handoffTimedOut[pending.id] ? "Still waiting · Check again" : pending.kind === "queue" ? "Agent queued · waiting for its terminal" : "Agent starting · waiting for its terminal"}</span>
        <Button dense variant="ghost" onClick={refresh}>Check again</Button>
        <Button dense variant="ghost" onClick={() => cancelWorkspaceLaunch(pending.id)}>Stop waiting</Button>
      </ActionNotice>)}

      {selectedDescriptor ? <WorkspaceOverview
        descriptor={selectedDescriptor}
        selectedProjectName={selectedProjectName}
        onOpenTerminal={() => openTerminal(selectedDescriptor)}
      /> : null}
      <div className="terminals-list" role="region" aria-label="Terminal sessions">
        {inventoryLoading && !inventory.sessions.length ? <SurfaceState loading /> : null}
        {inventory.status === "error" ? <SurfaceState error={inventoryFailure(inventory.status, inventory.detail)} onRetry={refresh} retryLabel="Retry" /> : null}
        {inventory.status === "tmux_absent" ? <SurfaceState error={inventoryFailure(inventory.status, inventory.detail)} onRetry={refresh} retryLabel="Retry" /> : null}
        {inventory.status !== "error" && inventory.status !== "tmux_absent" && !rows.length && !inventoryLoading ? (
          <SurfaceState
            empty
            emptyLabel={queryText ? "No matching terminals" : selection.projectId ? `No sessions in ${selectedProjectName || "this project"}` : "No terminal sessions"}
            emptyHint={queryText ? undefined : "Create a shell or start an agent to see it here."}
          />
        ) : null}
        {groups.length ? (
          <ListView label="Terminal sessions">
            {groups.map(([group, descriptors]) => (
              <div className="terminals-group" key={group} title={group} data-folder-path={group}>
                <ListDay label={group === "Local shells" ? group : group.split(/[\\/]/).filter(Boolean).pop() || group}>
                  {descriptors.map((descriptor) => (
                    <TerminalRow key={descriptor.id} descriptor={descriptor} open={openIds.has(descriptor.id)} selected={selection.sessionId === descriptor.id} onOpen={() => openTerminal(descriptor)} />
                  ))}
                </ListDay>
              </div>
            ))}
          </ListView>
        ) : null}
      </div>
      </> : <>
      {selection.pendingHandoffs.map((pending) => <ActionNotice key={`${pending.kind}:${pending.id}`} tone="info" data-testid={`terminal-handoff-pending-${pending.id}`}>
        <span>{handoffTimedOut[pending.id] ? "Still waiting · Check again" : pending.kind === "queue" ? "Agent queued · waiting for its terminal" : "Agent starting · waiting for its terminal"}</span>
        <Button dense variant="ghost" onClick={refresh}>Check again</Button>
        <Button dense variant="ghost" onClick={() => cancelWorkspaceLaunch(pending.id)}>Stop waiting</Button>
      </ActionNotice>)}
      <div className="terminals-workspace-head" data-testid="terminal-workspace-head">
        {selectedDescriptor ? <span className="terminals-workspace-selected">{selectedDescriptor.label}</span> : <span className="terminals-workspace-selected">No session selected</span>}
      </div>
      </>}
      {selection.face !== "sessions" ? (
        <div className="terminals-workspace-return-target" hidden={formOpen} aria-hidden={formOpen ? "true" : undefined}>
          <WorkspaceView
            descriptor={selectedDescriptor}
            face={selection.face}
            onChanges={() => selectWorkspaceFace("changes")}
            selectedProjectId={selection.projectId}
            selectedProjectName={selectedProjectName}
            onRepositoryBound={() => setProjectResourceRevision((revision) => revision + 1)}
            onPrepareFileHandoff={(preparation) => {
              bumpWorkspaceRequestEpoch();
              setAgentPreparation(preparation);
              setStartingAgent(true);
              setNewShell(false);
            }}
          />
        </div>
      ) : null}
      <StatusBar
        items={[inventoryStatusText ? { lamp: inventoryStatus, text: inventoryStatusText } : null]}
        trailing={terminalWindows.length ? `${terminalWindows.length} open` : undefined}
      />
    </div>
  );
}

export { terminalWindowId };
