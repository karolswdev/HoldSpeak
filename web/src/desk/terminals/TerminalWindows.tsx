import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import { flushSync } from "react-dom";
import type { StoreApi } from "zustand/vanilla";
import { Button } from "../../components/signal/Signal";
import { PaneWell, StatusBar, StringGadget, ToolGlyph, Toolbar, ToolbarFold } from "../surface";
import { DeskWindowFrame } from "../components/DeskWindow";
import { useFrontWindowId } from "../components/window/windowRegistry";
import { useDesk } from "../store";
import { useCompactViewport } from "../useCompactViewport";
import { AGENT_CHANGE_KINDS, useOnCoderFrame, useOnDeskChanged } from "../useDeskChangedRefresh";
import { createTerminalSession } from "./terminalSession";
import type { TerminalDescriptor, TerminalKey, TerminalSessionState } from "./types";
import { selectWorkspaceSession } from "./workspaceSelection";
import {
  refreshTerminalInventory,
  terminalDescriptorId,
  terminalInventorySnapshot,
  subscribeTerminalInventory,
  TERMINALS_WINDOW_ID,
  terminalWindowId,
  type TerminalInventoryState,
} from "./windows";
import "./terminals.css";

const EMPTY_SESSION: TerminalSessionState | null = null;

function useTerminalInventory(hasOpenWindows: boolean, inventoryOpen: boolean) {
  const snapshot = useSyncExternalStore(
    subscribeTerminalInventory,
    terminalInventorySnapshot,
    terminalInventorySnapshot,
  );
  const refreshWhenOpen = () => {
    if (hasOpenWindows || inventoryOpen) void refreshTerminalInventory();
  };
  // TerminalWindows is the one desk-level owner of live inventory refreshes.
  // The terminal frames themselves only consume this projection; they do not
  // create one bus subscription per controller.
  useOnCoderFrame(refreshWhenOpen);
  useOnDeskChanged(refreshWhenOpen, AGENT_CHANGE_KINDS);
  useEffect(() => {
    // Restored terminal frames may be the only mounted terminal surface after
    // reload. They must hydrate their own inventory instead of relying on the
    // inventory app having been opened first.
    if ((hasOpenWindows || inventoryOpen) && snapshot.status === "idle") void refreshTerminalInventory();
  }, [hasOpenWindows, inventoryOpen, snapshot.status]);
  return snapshot;
}

function useSession(descriptor: TerminalDescriptor | null): TerminalSessionState | null {
  const key = descriptor
    ? `${descriptor.id}|${descriptor.target.node_id}|${descriptor.target.target_id}|${descriptor.target.target_generation}`
    : "";
  const store = useMemo<StoreApi<TerminalSessionState> | null>(
    () => descriptor ? createTerminalSession(descriptor) : null,
    [key],
  );
  const snapshot = useSyncExternalStore(
    store?.subscribe ?? (() => () => undefined),
    store?.getState ?? (() => EMPTY_SESSION),
    store?.getState ?? (() => EMPTY_SESSION),
  );
  useEffect(() => {
    if (!store) return;
    store.getState().start();
    return () => store.getState().stop();
  }, [store]);
  return snapshot;
}

function statusWords(session: TerminalSessionState | null): string {
  if (!session) return "Not connected";
  if (session.error) {
    const disconnected = ["error", "unreachable", "unauthorized", "target_gone", "generation_mismatch", "stream_unavailable", "tmux_absent"].includes(session.status);
    const posture = disconnected ? "Not connected" : session.canType ? "Not sent" : "View only";
    return `${posture} · ${session.error}`;
  }
  if (session.receipt) return "Sent";
  if (session.canType) return "Typing enabled";
  if (session.status === "live" || session.status === "not_modified") return "Live · View only";
  if (session.status === "loading") return "Connecting";
  if (session.status === "target_gone" || session.status === "generation_mismatch") return "Not connected";
  return session.status.replaceAll("_", " ");
}

function keyLabel(key: TerminalKey): string {
  return typeof key === "string" ? key : key.literal;
}

function keyFace(key: TerminalKey): string {
  return keyLabel(key) === "C-c" ? "Ctrl-C" : keyLabel(key);
}

const terminalInventoryError = "Cannot read terminals. Draft kept. Open Terminals and press Refresh.";
const terminalTmuxAbsent = "Terminal inventory unavailable. Draft kept. Open Terminals and press Refresh.";
const terminalDescriptorAbsent = "Terminal ended or was removed. Draft kept. Open Terminals and press Refresh.";

function withTerminalDetail(message: string, detail: string | null): string {
  return detail ? `${message} · ${detail}` : message;
}

function TerminalWindow({
  descriptor,
  id,
  inventory,
}: {
  descriptor: TerminalDescriptor | null;
  id: string;
  inventory: TerminalInventoryState;
}) {
  const descriptorId = terminalDescriptorId(id) ?? id.slice("terminal:".length);
  const session = useSession(descriptor);
  const frontWindow = useFrontWindowId();
  const compact = useCompactViewport();
  const minimized = useDesk((state) => state.panelMin.includes(id));
  const [focusSignal, setFocusSignal] = useState(0);
  const [findOpen, setFindOpen] = useState(false);
  const [typingPending, setTypingPending] = useState(false);
  const draftKey = `terminal:${descriptorId}`;
  const draft = useDesk((state) => state.drafts[draftKey] ?? "");
  const setDraft = useDesk((state) => state.setDraft);
  const [messageOpen, setMessageOpen] = useState(() => Boolean(draft.trim()));
  const close = () => useDesk.getState().closeTerminalWindow(descriptorId);
  const backToInventory = () => useDesk.getState().openSurfaceWindow("open-terminals");
  const openWorkspace = () => {
    if (!descriptor) return;
    selectWorkspaceSession(descriptor, "files");
    useDesk.getState().openSurfaceWindow("open-terminals");
  };
  const sendText = async () => {
    if (!session || !draft.trim()) return;
    const capturedDraft = draft;
    const ok = await session.sendText(capturedDraft, true);
    if (ok && useDesk.getState().drafts[draftKey] === capturedDraft) setDraft(draftKey, null);
  };
  const focusTerminal = () => {
    flushSync(() => setFocusSignal((value) => value + 1));
  };
  const toggleTyping = async () => {
    if (!session || typingPending) return;
    if (!session.canType) {
      // The operator's Type press owns focus. Flush the signal before asking
      // the hub for its scoped grant so a delayed ACK can never move focus.
      focusTerminal();
    }
    setTypingPending(true);
    try {
      if (session.canType) await session.disableTyping();
      else await session.enableTyping();
    } finally {
      setTypingPending(false);
    }
  };
  useEffect(() => {
    // A draft recovered from the Desk is an explicit request to show Message.
    // Hiding the disclosure never discards it, so it remains available when
    // this window is restored or the user opens Message again.
    if (draft.trim()) setMessageOpen(true);
  }, [draft]);
  const keys: TerminalKey[] = ["C-c", "Escape", "Tab", "Up", "Down", "Left", "Right", "Enter"];
  const title = descriptor ? `${descriptor.agent !== "pane" ? descriptor.agent : "Shell"} · ${descriptor.label}` : `Terminal · ${descriptorId}`;
  const live = Boolean(session && ["live", "not_modified", "resyncing"].includes(session.status));
  const typingActionDisabled = typingPending
    || !session
    || (!session.canType && !["live", "not_modified"].includes(session.status));
  const setActivity = session?.setActivity;
  const absence = session?.error
    ? `Terminal unavailable · ${session.error}`
    : session?.status === "loading"
      ? "Connecting to terminal…"
      : inventory.status === "idle" || inventory.status === "loading"
        ? "Connecting to terminal inventory…"
        : inventory.status === "error"
          ? withTerminalDetail(terminalInventoryError, inventory.detail)
          : inventory.status === "tmux_absent"
            ? withTerminalDetail(terminalTmuxAbsent, inventory.detail)
            : descriptor
              ? "Terminal unavailable"
              : terminalDescriptorAbsent;
  useEffect(() => {
    if (!setActivity || typeof document === "undefined") return;
    const update = () => setActivity({
      focused: frontWindow === id && !minimized && document.activeElement instanceof HTMLElement
        && document.activeElement.closest(".terminal-well-screen") !== null
        && document.activeElement.closest(".terminals-window")?.id === id,
      visible: !minimized && document.visibilityState !== "hidden" && (!compact || frontWindow === id),
    });
    const onVisibility = () => update();
    document.addEventListener("visibilitychange", onVisibility);
    update();
    return () => document.removeEventListener("visibilitychange", onVisibility);
  }, [compact, frontWindow, id, minimized, setActivity]);
  return (
    <DeskWindowFrame
      id={id}
      title={title}
      label={title}
      glyph="▥"
      className="desk-pullout terminals-window"
      minW={440}
      minH={300}
      defaultW={700}
      defaultH={560}
      room="terminals"
      open
      unmountOnMinimize
      escapeCloses={false}
      onClose={close}
      onBack={() => { close(); backToInventory(); }}
    >
      <div
        className="desk-pullout-body terminals-window-body"
        data-interior="editor"
        data-testid={`terminal-window-${descriptorId}`}
        onFocusCapture={(event) => {
          const target = event.target as HTMLElement;
          session?.setActivity({ focused: Boolean(target.closest(".terminal-well-screen")), visible: true });
        }}
        onBlurCapture={() => {
          const active = document.activeElement;
          session?.setActivity({ focused: active instanceof HTMLElement && Boolean(active.closest(".terminal-well-screen")), visible: true });
        }}
        onPointerDown={() => useDesk.getState().focusPanel(id)}
      >
        <Toolbar label="Terminal controls" data-testid="terminal-toolbar">
          <Button
            dense
            variant={session?.canType ? "secondary" : "ghost"}
            loading={typingPending}
            disabled={typingActionDisabled}
            onClick={() => void toggleTyping()}
            data-testid="terminal-enable-typing"
          >
            {session?.canType ? "View only" : "Type"}
          </Button>
          <ToolbarFold
            label="Keys"
            foldAt="medium"
            verbs={keys.map((key) => ({
              key: `key-${keyLabel(key)}`,
              label: keyFace(key),
              onSelect: () => { void session?.sendKeys([key], keyLabel(key)); },
            }))}
          />
          <Button
            dense
            variant={findOpen ? "secondary" : "ghost"}
            aria-pressed={findOpen}
            onClick={() => {
              if (findOpen) focusTerminal();
              setFindOpen((open) => !open);
            }}
            data-testid="terminal-find"
          >
            Find
          </Button>
          <Button
            dense
            variant={messageOpen ? "secondary" : "ghost"}
            aria-expanded={messageOpen}
            aria-controls={`terminal-composer-${descriptorId}`}
            onClick={() => {
              if (messageOpen) focusTerminal();
              setMessageOpen((open) => !open);
            }}
            data-testid="terminal-message-toggle"
          >
            Message
          </Button>
          <Button dense variant="ghost" disabled={!descriptor} onClick={openWorkspace} data-testid="terminal-workspace">
            Workspace
          </Button>
          <span className="terminals-toolbar-spacer" />
          {descriptor ? <span className="terminals-toolbar-path" title={descriptor.current_path}>{descriptor.current_path || descriptor.session}</span> : null}
        </Toolbar>
        <div className="terminals-screen" onClick={() => setFocusSignal((value) => value + 1)}>
          <PaneWell
            live={live}
            lines={session?.lines ?? []}
            raw={session?.raw}
            pane={session?.pane}
            changedAt={session?.changedAt}
            header={findOpen ? "find" : "none"}
            absence={absence}
            onData={(data) => session?.sendData(data)}
            copyOnSelect={false}
            inputEnabled={Boolean(session?.canType)}
            focusSignal={focusSignal || undefined}
            onFocus={() => session?.setActivity({ focused: true, visible: true })}
          />
        </div>
        {messageOpen ? (
          <div className="terminals-composer" id={`terminal-composer-${descriptorId}`} data-testid="terminal-composer">
            <StringGadget label="Message" value={draft} onChange={(value) => setDraft(draftKey, value)} placeholder="Say or type a message" />
            <Button dense variant="secondary" disabled={!draft.trim() || !session?.canType || session.busy} loading={session?.busy} onClick={() => void sendText()}>
              Send
            </Button>
          </div>
        ) : null}
        <StatusBar
          data-testid="terminal-status"
          items={[{
            lamp: session?.error ? "warn" : session?.canType || live ? "ok" : "info",
            text: statusWords(session),
          }]}
          trailing={descriptor ? `${descriptor.agent !== "pane" ? descriptor.agent : "Shell"} · ${descriptor.session}` : undefined}
        />
      </div>
    </DeskWindowFrame>
  );
}

export function TerminalWindows() {
  const terminalWindows = useDesk((state) => state.terminalWindows);
  const inventoryOpen = useDesk((state) => Boolean(state.windowsById[TERMINALS_WINDOW_ID]));
  const inventory = useTerminalInventory(terminalWindows.length > 0, inventoryOpen);
  const descriptorById = useMemo(() => new Map(inventory.sessions.map((session) => [session.id, session])), [inventory.sessions]);
  return (
    <>
      {terminalWindows.map((window) => (
        <TerminalWindow
          key={window.id}
          id={terminalWindowId(window.id)}
          descriptor={descriptorById.get(window.id) ?? null}
          inventory={inventory}
        />
      ))}
    </>
  );
}
