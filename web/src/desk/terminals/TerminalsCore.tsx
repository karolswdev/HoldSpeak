import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { Button } from "../../components/signal/Signal";
import { apiRequest } from "../../lib/api";
import { StartAgent } from "../conductor/StartAgent";
import { useConductor } from "../conductor/store";
import { ListDay, ListRow, ListView, StatusBar, StringGadget, SurfaceState, ToolGlyph, Toolbar, ToolbarFold, countWords, useWindowInterior } from "../surface";
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
  onOpen,
}: {
  descriptor: TerminalDescriptor;
  open: boolean;
  onOpen(): void;
}) {
  const rowState = terminalRowState(descriptor);
  return <ListRow
    glyph={<ToolGlyph kind="engine" />}
    name={descriptor.label || descriptor.session || "Terminal"}
    meta={[descriptor.agent !== "pane" ? descriptor.agent : "Shell", descriptor.command].filter(Boolean).join(" · ")}
    state={{ word: rowState.word, tone: rowState.tone, live: rowState.live }}
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
      const descriptor = terminalInventorySnapshot().sessions.find((row) =>
        row.session === clean || row.label.includes(clean) || row.pane_id === answer.pane_id,
      );
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
  const queryText = query.trim().toLowerCase();
  const rows = useMemo(() => inventory.sessions.filter((descriptor) => {
    if (!queryText) return true;
    return [descriptor.label, descriptor.session, descriptor.agent, descriptor.command, descriptor.current_path]
      .some((value) => value.toLowerCase().includes(queryText));
  }), [inventory.sessions, queryText]);
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
    useDesk.getState().openTerminalWindow(descriptor.id);
  };
  const refresh = () => { void refreshTerminalInventory(); };
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
          variant="primary"
          dense
          onClick={() => {
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
            setStartingAgent((value) => !value);
            setNewShell(false);
          }}
          data-testid="terminal-start-agent"
        >
          <ToolGlyph kind="run" />
          Start an agent
        </Button>
        <ToolbarFold label="More" foldAt="medium" verbs={secondaryActions} data-testid="terminal-more" />
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
          <div className="terminals-start-agent">
            <StartAgent
              onCancel={() => setStartingAgent(false)}
              onStarted={(row) => {
                setStartingAgent(false);
                if (row) useConductor.getState().openWindow(null, row);
                void useConductor.getState().readFlights();
                refresh();
              }}
            />
          </div>
        )
      ) : <>
      <div className="terminals-search">
        <StringGadget label="Find a session or folder" value={query} onChange={setQuery} placeholder="Find a session or folder" />
      </div>

      <div className="terminals-list" role="region" aria-label="Terminal sessions">
        {inventoryLoading && !inventory.sessions.length ? <SurfaceState loading /> : null}
        {inventory.status === "error" ? <SurfaceState error={inventoryFailure(inventory.status, inventory.detail)} onRetry={refresh} retryLabel="Retry" /> : null}
        {inventory.status === "tmux_absent" ? <SurfaceState error={inventoryFailure(inventory.status, inventory.detail)} onRetry={refresh} retryLabel="Retry" /> : null}
        {inventory.status !== "error" && inventory.status !== "tmux_absent" && !rows.length && !inventoryLoading ? (
          <SurfaceState
            empty
            emptyLabel={queryText ? "No matching terminals" : "No terminal sessions"}
            emptyHint={queryText ? undefined : "Create a shell or start an agent to see it here."}
          />
        ) : null}
        {groups.length ? (
          <ListView label="Terminal sessions">
            {groups.map(([group, descriptors]) => (
              <div className="terminals-group" key={group} title={group} data-folder-path={group}>
                <ListDay label={group === "Local shells" ? group : group.split(/[\\/]/).filter(Boolean).pop() || group}>
                  {descriptors.map((descriptor) => (
                    <TerminalRow key={descriptor.id} descriptor={descriptor} open={openIds.has(descriptor.id)} onOpen={() => openTerminal(descriptor)} />
                  ))}
                </ListDay>
              </div>
            ))}
          </ListView>
        ) : null}
      </div>
      </>}
      <StatusBar
        items={[inventoryStatusText ? { lamp: inventoryStatus, text: inventoryStatusText } : null]}
        trailing={terminalWindows.length ? `${terminalWindows.length} open` : undefined}
      />
    </div>
  );
}

export { terminalWindowId };
