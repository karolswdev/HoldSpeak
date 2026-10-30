import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { Button } from "../../components/signal/Signal";
import { apiRequest } from "../../lib/api";
import { StartAgent } from "../conductor/StartAgent";
import { useConductor } from "../conductor/store";
import { DotWord, StatusBar, StringGadget, SurfaceState, ToolGlyph, Toolbar } from "../surface";
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

function TerminalRow({
  descriptor,
  open,
  onOpen,
}: {
  descriptor: TerminalDescriptor;
  open: boolean;
  onOpen(): void;
}) {
  const state = descriptor.state.trim().toLowerCase();
  const tone = state === "waiting" || state === "awaiting_response" || state === "needs_you"
    ? "warn" as const
    : state === "done" || state === "checked"
      ? "ok" as const
      : state === "live" || state === "working"
        ? "info" as const
        : "idle" as const;
  return (
    <li className="terminals-row" data-testid={`terminal-row-${descriptor.id}`}>
      <span className="terminals-row-glyph" aria-hidden="true"><ToolGlyph kind="engine" /></span>
      <span className="terminals-row-copy">
        <strong>{descriptor.label || descriptor.session || "Terminal"}</strong>
        <span className="kit-listrow-meta">
          {[descriptor.agent !== "pane" ? descriptor.agent : "Shell", descriptor.command].filter(Boolean).join(" · ")}
          {descriptor.current_path ? <><span aria-hidden="true"> · </span><span className="terminals-row-path">{descriptor.current_path}</span></> : null}
        </span>
      </span>
      <DotWord className="terminals-row-state" tone={tone} live={tone === "info"} title={descriptor.state}>
        {stateWord(descriptor)}
      </DotWord>
      <Button
        dense
        variant={open ? "secondary" : "ghost"}
        onClick={onOpen}
        data-testid={`terminal-open-${descriptor.id}`}
      >
        {open ? "Focus" : "Open"}
      </Button>
    </li>
  );
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

function NewShell({ onCreated }: { onCreated(descriptorId?: string): void }) {
  const [name, setName] = useState("");
  const [cwd, setCwd] = useState("");
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
      setName("");
      setCwd("");
      onCreated(descriptor?.id);
    } catch (caught) {
      setBusy(false);
      setError(caught instanceof Error ? caught.message : "The shell was not started.");
      return;
    }
  };
  return (
    <div className="terminals-new-shell" data-testid="terminal-new-shell">
      <StringGadget label="Shell name" value={name} onChange={setName} placeholder="Name this shell" />
      <StringGadget label="Folder (optional)" value={cwd} onChange={setCwd} placeholder="Local folder" />
      {error ? <p className="terminals-inline-error" role="alert">{error}</p> : null}
      <Button variant="primary" loading={busy} disabled={!name.trim() || busy} onClick={() => void spawn()}>
        <ToolGlyph kind="new" />
        Create shell
      </Button>
    </div>
  );
}

export function TerminalsCore() {
  const inventory = useTerminalInventory();
  const terminalWindows = useDesk((state) => state.terminalWindows);
  const [query, setQuery] = useState("");
  const [newShell, setNewShell] = useState(false);
  const [startingAgent, setStartingAgent] = useState(false);
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

  return (
    <div className="terminals-core" data-testid="terminals-inventory" data-interior="list">
      <Toolbar label="Terminals" data-testid="terminals-toolbar">
        <Button variant="primary" dense onClick={() => setNewShell((value) => !value)} data-testid="terminal-new">
          <ToolGlyph kind="new" />
          New terminal
        </Button>
        <Button variant={startingAgent ? "secondary" : "ghost"} dense onClick={() => setStartingAgent((value) => !value)} data-testid="terminal-start-agent">
          <ToolGlyph kind="run" />
          Start an agent
        </Button>
        <Button variant="ghost" dense onClick={refresh} data-testid="terminal-refresh">
          <ToolGlyph kind="retry" />
          Refresh
        </Button>
        <Button variant="ghost" dense disabled={terminalWindows.length < 2} onClick={tileTerminals} data-testid="terminal-tile">
          Tile terminals
        </Button>
      </Toolbar>

      <div className="terminals-search">
        <StringGadget label="Find a session or folder" value={query} onChange={setQuery} placeholder="Find a session or folder" />
      </div>

      {newShell ? <NewShell onCreated={(descriptorId) => {
        setNewShell(false);
        if (descriptorId) useDesk.getState().openTerminalWindow(descriptorId);
        refresh();
      }} /> : null}
      {startingAgent ? (
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
      ) : null}

      <div className="terminals-list" role="region" aria-label="Terminal sessions">
        {inventoryLoading && !inventory.sessions.length ? <SurfaceState loading /> : null}
        {inventory.status === "error" ? <SurfaceState error={inventoryFailure(inventory.status, inventory.detail)} onRetry={refresh} retryLabel="Retry" /> : null}
        {inventory.status === "tmux_absent" ? <SurfaceState error={inventoryFailure(inventory.status, inventory.detail)} onRetry={refresh} retryLabel="Retry" /> : null}
        {inventory.status !== "error" && inventory.status !== "tmux_absent" && !rows.length && !inventoryLoading ? (
          <SurfaceState empty emptyLabel={queryText ? "No matching terminals" : "No terminal sessions"} emptyHint="Create a shell or start an agent to see it here." />
        ) : null}
        {groups.map(([group, descriptors]) => (
          <section className="terminals-group" key={group} aria-label={group}>
            <h3>{group}</h3>
            <ul>
              {descriptors.map((descriptor) => (
                <TerminalRow key={descriptor.id} descriptor={descriptor} open={openIds.has(descriptor.id)} onOpen={() => openTerminal(descriptor)} />
              ))}
            </ul>
          </section>
        ))}
      </div>
      <StatusBar items={[{ lamp: inventory.status === "ok" ? "ok" : inventoryLoading ? "info" : "warn", text: inventory.status === "ok" ? `${rows.length} terminal${rows.length === 1 ? "" : "s"}` : inventoryLoading ? "Connecting" : inventory.detail || inventory.status }]}
        trailing={terminalWindows.length ? `${terminalWindows.length} open` : undefined} />
    </div>
  );
}

export { terminalWindowId };
