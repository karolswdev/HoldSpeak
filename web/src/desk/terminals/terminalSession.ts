import { createStore, type StoreApi } from "zustand/vanilla";
import { armTerminal, disarmTerminal, readTerminalLive, readTerminalSubscription, resizeTerminal, sendTerminalCommand } from "./api";
import { decodeTerminalInput, normalizeTerminalKeys } from "./input";
import type {
  TerminalDescriptor,
  TerminalKey,
  TerminalPaneGeometry,
  TerminalReceipt,
  TerminalDimensions,
  TerminalOutputFrame,
  TerminalOutputSource,
  TerminalResizeState,
  TerminalSessionState,
  TerminalStatus,
} from "./types";

export const TERMINAL_FOCUSED_POLL_MS = 350;
export const TERMINAL_VISIBLE_POLL_MS = 1_200;
export const TERMINAL_INPUT_BATCH_MS = 30;
export const TERMINAL_LIVE_RECONNECT_MS = 250;
export const TERMINAL_LIVE_RECONNECT_MAX_MS = 5_000;
export const TERMINAL_LIVE_HEADER_TIMEOUT_MS = 10_000;
export const TERMINAL_LIVE_IDLE_TIMEOUT_MS = 30_000;

// eslint-disable-next-line no-control-regex
const ANSI = /\u001b\[[0-9;?]*[ -/]*[@-~]|\u001b\][\s\S]*?(?:\u0007|\u001b\\)|\u001b[@-Z\\-_]/g;
const RAW_MAX_CHARS = 256_000;

function toLines(raw: string): string[] {
  return raw.replace(ANSI, "").replace(/\r/g, "").split("\n");
}

function capRaw(raw: string): string {
  return raw.length > RAW_MAX_CHARS ? raw.slice(-RAW_MAX_CHARS) : raw;
}

function createOutputSource(): { source: TerminalOutputSource; emit(frame: TerminalOutputFrame): void; setResync(handler: () => void): void; markResync(): void } {
  let current: TerminalOutputFrame | null = null;
  let snapshot: TerminalOutputFrame | null = null;
  const backlog: TerminalOutputFrame[] = [];
  let backlogBytes = 0;
  let requestResync: () => void = () => undefined;
  const listeners = new Set<(frame: TerminalOutputFrame) => void>();
  const resyncListeners = new Set<() => void>();
  return {
    source: {
      subscribe(listener) {
        listeners.add(listener);
        return () => listeners.delete(listener);
      },
      subscribeResync(listener) {
        resyncListeners.add(listener);
        return () => resyncListeners.delete(listener);
      },
      current: () => current,
      replay: (afterSequence = 0) => {
        const first = backlog[0];
        if (first && first.sequence > afterSequence + 1) return null;
        return backlog.filter((frame) => frame.sequence > afterSequence);
      },
      snapshot: () => snapshot,
      requestResync: () => requestResync(),
    },
    emit(frame) {
      current = frame;
      if (frame.kind === "snapshot" || frame.kind === "resync") {
        snapshot = frame;
        backlog.length = 0;
        backlogBytes = 0;
      }
      backlog.push(frame);
      backlogBytes += frame.data.byteLength;
      while (backlog.length > 512 || backlogBytes > 512 * 1024) {
        const removed = backlog.shift();
        if (removed) backlogBytes -= removed.data.byteLength;
      }
      for (const listener of [...listeners]) listener(frame);
    },
    setResync(handler) { requestResync = handler; },
    markResync() { for (const listener of [...resyncListeners]) listener(); },
  };
}

function decodeBase64(value: string): Uint8Array | null {
  if (!value) return new Uint8Array();
  if (!/^[A-Za-z0-9+/]*={0,2}$/.test(value) || value.length % 4 === 1) return null;
  try {
    const binary = atob(value);
    const bytes = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
    return bytes;
  } catch {
    return null;
  }
}

function frameBytes(value: unknown, encoding: unknown): Uint8Array | null {
  if (typeof value !== "string") return null;
  return encoding === "base64" ? decodeBase64(value) : new TextEncoder().encode(value);
}

function dimensionsEqual(left: TerminalDimensions | null, right: TerminalDimensions | null): boolean {
  return Boolean(left && right && left.cols === right.cols && left.rows === right.rows);
}

function paneGeometry(value: unknown): TerminalPaneGeometry | null {
  if (!value || typeof value !== "object") return null;
  const row = value as Record<string, unknown>;
  const width = Number(row.width);
  const height = Number(row.height);
  if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) return null;
  return {
    width,
    height,
    cursorX: Number(row.cursorX ?? row.cursor_x) || 0,
    cursorY: Number(row.cursorY ?? row.cursor_y) || 0,
  };
}

function statusFromResponse(status: string, responseStatus: number): TerminalStatus {
  if (responseStatus === 401) return "unauthorized";
  if (responseStatus === 404) return "target_gone";
  if (responseStatus === 409) return "generation_mismatch";
  if (["snapshot", "deltas", "not_modified"].includes(status)) return status as TerminalStatus;
  if (status === "resync_required") return "resyncing";
  if (["stream_unavailable", "target_gone", "generation_mismatch", "unauthorized", "tmux_absent"].includes(status)) return status as TerminalStatus;
  return responseStatus >= 400 ? "error" : "live";
}

type PendingItem =
  | { kind: "keys"; keys: TerminalKey[]; target: string; queueEpoch: number; resolve?: (ok: boolean) => void }
  | { kind: "text"; text: string; submit: boolean; target: string; queueEpoch: number; resolve?: (ok: boolean) => void };

function targetKey(descriptor: TerminalDescriptor): string {
  return `${descriptor.target.node_id}|${descriptor.target.target_id}|${descriptor.target.target_generation}`;
}

/** Create an independent controller for one terminal descriptor.
 *
 * The returned vanilla StoreApi is intentionally local to this descriptor.
 * React consumers can use `useStore(session, selector)` and non-React callers
 * can use `getState()`; there is no global current terminal selection.
 */
export function createTerminalSession(
  descriptor: TerminalDescriptor,
  options: { mode?: "poll" | "live" } = {},
): StoreApi<TerminalSessionState> {
  const controllerDescriptor: TerminalDescriptor = {
    ...descriptor,
    target: { ...descriptor.target },
  };
  Object.freeze(controllerDescriptor.target);
  Object.freeze(controllerDescriptor);
  const immutableKey = targetKey(controllerDescriptor);
  let running = false;
  let lifecycle = 0;
  let timer: ReturnType<typeof setTimeout> | null = null;
  let pollEpoch: number | null = null;
  let refreshRequested = false;
  let pending: PendingItem[] = [];
  let batchTimer: ReturnType<typeof setTimeout> | null = null;
  let sendEpoch: number | null = null;
  let queueEpoch = 0;
  let typingTimer: ReturnType<typeof setTimeout> | null = null;
  let activity = { focused: false, visible: true };
  // A command refusal is an operator-visible fact, not a transient poll
  // status. Successful screen reads may recover the connection, but must not
  // erase the last "not sent" reason until the operator tries new input or
  // explicitly disarms/re-arms the controller.
  let commandError: string | null = null;
  const mode = options.mode ?? "poll";
  const output = createOutputSource();
  let liveAbort: AbortController | null = null;
  let liveIdleTimer: ReturnType<typeof setTimeout> | null = null;
  let liveReconnect: ReturnType<typeof setTimeout> | null = null;
  let liveStreamId: string | null = null;
  let liveSequence = 0;
  let liveBackoff = TERMINAL_LIVE_RECONNECT_MS;
  let liveRebindRefused = false;
  let liveReconnectWanted = false;
  let liveResyncPending = false;
  let liveForceSnapshot = false;
  let resizeDesired: TerminalDimensions | null = null;
  let resizeInFlight: TerminalDimensions | null = null;

  const clearTimer = () => {
    if (timer !== null) clearTimeout(timer);
    timer = null;
  };
  const clearBatch = () => {
    if (batchTimer !== null) clearTimeout(batchTimer);
    batchTimer = null;
  };
  const clearTypingTimer = () => {
    if (typingTimer !== null) clearTimeout(typingTimer);
    typingTimer = null;
  };
  const clearLiveReconnect = () => {
    if (liveReconnect !== null) clearTimeout(liveReconnect);
    liveReconnect = null;
  };
  const abortLive = () => {
    if (liveIdleTimer !== null) clearTimeout(liveIdleTimer);
    liveIdleTimer = null;
    liveAbort?.abort();
    liveAbort = null;
  };
  const resolveItems = (items: PendingItem[], ok: boolean) => {
    for (const item of items) item.resolve?.(ok);
  };
  const cancelPending = () => {
    resolveItems(pending, false);
    pending = [];
    clearBatch();
  };
  const invalidateInputQueue = () => {
    queueEpoch += 1;
    cancelPending();
  };

  const store = createStore<TerminalSessionState>((set, get) => {
    const schedule = (atLifecycle: number) => {
      clearTimer();
      if (!running || atLifecycle !== lifecycle || !activity.visible) return;
      timer = setTimeout(() => {
        timer = null;
        if (atLifecycle === lifecycle) void poll(atLifecycle);
      }, activity.focused ? TERMINAL_FOCUSED_POLL_MS : TERMINAL_VISIBLE_POLL_MS);
    };

    const poll = async (atLifecycle = lifecycle): Promise<void> => {
      if (!running || atLifecycle !== lifecycle || !activity.visible || pollEpoch === atLifecycle) return;
      pollEpoch = atLifecycle;
      const sequenceAtRead = get().sequence;
      const hashAtRead = get().hash;
      set({ status: get().status === "idle" ? "loading" : get().status });
      try {
        const { response, body } = await readTerminalSubscription(
          controllerDescriptor.target,
          sequenceAtRead,
          hashAtRead,
        );
        // Descriptor and target are immutable, but stopped controllers can
        // still have a response in flight. Never paint after stop.
        if (!running || atLifecycle !== lifecycle) return;
        const wireStatus = String(body.status || "");
        const status = statusFromResponse(wireStatus, response.status);
        if (!response.ok || ["target_gone", "generation_mismatch", "unauthorized", "stream_unavailable", "tmux_absent"].includes(status)) {
          invalidateInputQueue();
          clearTypingTimer();
          set({ status, error: body.detail || wireStatus || `HTTP ${response.status}`, raw: null, lines: [], pane: null, canType: false });
          return;
        }
        if (wireStatus === "not_modified") {
          set({ status: "live", pane: paneGeometry(body.pane) || get().pane, error: commandError });
          return;
        }
        if (wireStatus === "snapshot" || wireStatus === "resync_required") {
          const raw = typeof body.raw === "string" ? body.raw : typeof body.content === "string" ? body.content : "";
          set({
            status: wireStatus === "resync_required" ? "resyncing" : "live",
            raw: capRaw(raw),
            lines: Array.isArray(body.lines) ? body.lines.map(String) : toLines(raw),
            pane: paneGeometry(body.pane),
            sequence: Number(body.sequence || 0),
            hash: typeof body.hash === "string" ? body.hash : null,
            changedAt: Date.now(),
            error: commandError,
          });
          return;
        }
        if (wireStatus === "deltas") {
          let raw = get().raw || "";
          let changed = false;
          let sequence = get().sequence;
          for (const delta of body.deltas || []) {
            const data = typeof delta.raw === "string"
              ? delta.raw
              : typeof delta.content === "string" ? delta.content : String(delta.data || "");
            const replace = Boolean(delta.replace) || ["replace", "screen", "snapshot", "full"].includes(
              String(delta.kind || delta.mode || delta.type || "").toLowerCase(),
            );
            raw = replace ? data : raw + data;
            sequence = Number(delta.sequence || sequence);
            changed = true;
          }
          set({
            status: "live",
            raw: capRaw(raw),
            lines: toLines(capRaw(raw)),
            pane: paneGeometry(body.pane) || get().pane,
            sequence: Number(body.sequence || sequence),
            hash: typeof body.hash === "string" ? body.hash : get().hash,
            changedAt: changed ? Date.now() : get().changedAt,
            error: commandError,
          });
          return;
        }
        if (wireStatus && wireStatus !== "live") {
          invalidateInputQueue();
          clearTypingTimer();
          set({ status: statusFromResponse(wireStatus, response.status), error: body.detail || wireStatus, canType: false });
        } else {
          set({ status: "live", error: commandError });
        }
      } catch {
        if (running && atLifecycle === lifecycle) {
          invalidateInputQueue();
          clearTypingTimer();
          set({ status: "unreachable", error: "hub unreachable", canType: false });
        }
      } finally {
        if (pollEpoch === atLifecycle) {
          pollEpoch = null;
          const followUp = refreshRequested;
          refreshRequested = false;
          if (followUp && running && atLifecycle === lifecycle && activity.visible) {
            clearTimer();
            void poll(atLifecycle);
            return;
          }
          schedule(atLifecycle);
        }
      }
    };

    const requestPromptRead = (atLifecycle = lifecycle) => {
      if (!running || atLifecycle !== lifecycle || !activity.visible) return;
      if (pollEpoch === atLifecycle) {
        refreshRequested = true;
        return;
      }
      clearTimer();
      void poll(atLifecycle);
    };

    const scheduleLiveReconnect = (atLifecycle: number) => {
      clearLiveReconnect();
      if (mode !== "live" || !running || atLifecycle !== lifecycle || !activity.visible || liveRebindRefused) return;
      const delay = liveBackoff;
      liveBackoff = Math.min(TERMINAL_LIVE_RECONNECT_MAX_MS, Math.max(TERMINAL_LIVE_RECONNECT_MS, liveBackoff * 2));
      liveReconnect = setTimeout(() => {
        liveReconnect = null;
        if (running && atLifecycle === lifecycle && activity.visible) void readLive(atLifecycle);
      }, delay);
    };

    output.setResync(() => {
      if (mode !== "live" || !running || !activity.visible) return;
      liveResyncPending = true;
      liveForceSnapshot = true;
      liveReconnectWanted = true;
      output.markResync();
      set({ status: "resyncing", error: "Terminal replay expired; resyncing" });
      abortLive();
    });

    const handleLiveFrame = (value: unknown, atLifecycle: number): boolean => {
      if (!running || atLifecycle !== lifecycle || liveRebindRefused) return false;
      const row = value && typeof value === "object" ? value as Record<string, unknown> : {};
      const wireStatus = String(row.status ?? row.type ?? "").toLowerCase();
      // A typed absence is authoritative even when it repeats the last output
      // cursor or arrives under a new stream id. Sequence/epoch handling is
      // only for data-bearing frames.
      if (["target_gone", "generation_mismatch", "unauthorized", "tmux_absent", "stream_unavailable"].includes(wireStatus)) {
        if (wireStatus !== "stream_unavailable") liveRebindRefused = true;
        invalidateInputQueue();
        clearTypingTimer();
        set({
          status: statusFromResponse(wireStatus, wireStatus === "unauthorized" ? 401 : wireStatus === "target_gone" ? 404 : wireStatus === "generation_mismatch" ? 409 : 503),
          error: String(row.detail || wireStatus),
          raw: null,
          lines: [],
          pane: null,
          canType: false,
        });
        return false;
      }
      const rowStreamId = typeof row.stream_id === "string" ? row.stream_id : null;
      const newStreamEpoch = Boolean(rowStreamId && liveStreamId && rowStreamId !== liveStreamId);
      if (rowStreamId) {
        liveStreamId = rowStreamId;
        if (newStreamEpoch && wireStatus !== "snapshot" && wireStatus !== "resync_required") {
          set({ status: "resyncing", error: "Terminal stream resumed; waiting for snapshot" });
          liveForceSnapshot = true;
          liveReconnectWanted = true;
          abortLive();
          return false;
        }
        if (newStreamEpoch) liveSequence = 0;
      }
      const sequence = Number(row.sequence);
      const orderedFrame = ["snapshot", "resync_required", "heartbeat", "output", "data", "live"].includes(wireStatus);
      if (orderedFrame && Number.isFinite(sequence) && sequence > 0) {
        if (liveSequence > 0 && sequence > liveSequence + 1 && wireStatus !== "snapshot" && wireStatus !== "resync_required") {
          set({ status: "resyncing", error: "Output gap; resyncing terminal" });
          liveForceSnapshot = true;
          liveReconnectWanted = true;
          abortLive();
          return false;
        }
        if (sequence <= liveSequence && wireStatus !== "snapshot" && wireStatus !== "resync_required") return true;
      }
      const pane = paneGeometry(row.pane);
      if (wireStatus === "heartbeat") {
        if (sequence > liveSequence) liveSequence = sequence;
        set({ status: "live", error: commandError, pane: pane || get().pane });
        return true;
      }
      const rawData = row.data ?? row.content ?? row.raw;
      if (wireStatus === "resync_required" && rawData == null) {
        liveResyncPending = true;
        output.markResync();
        set({ status: "resyncing", error: "Terminal output resync required" });
        return true;
      }
      const data = frameBytes(rawData, row.encoding);
      if (!data || ((wireStatus === "snapshot" || wireStatus === "output" || wireStatus === "data" || wireStatus === "live") && rawData == null)) {
        liveResyncPending = true;
        liveForceSnapshot = true;
        liveReconnectWanted = true;
        set({ status: "resyncing", error: "Invalid terminal stream bytes" });
        abortLive();
        return false;
      }
      const sequenceValue = Number.isFinite(sequence) && sequence > 0 ? sequence : liveSequence + 1;
      if (wireStatus === "resync_required" && data.byteLength === 0) {
        liveResyncPending = true;
        set({ status: "resyncing", error: "Terminal output resync required" });
        return true;
      }
      if (liveResyncPending && wireStatus !== "snapshot" && wireStatus !== "resync_required") {
        set({ status: "resyncing", error: "Waiting for terminal snapshot" });
        liveReconnectWanted = true;
        abortLive();
        return false;
      }
      if (wireStatus === "snapshot" || wireStatus === "resync_required") {
        if (wireStatus === "snapshot") liveForceSnapshot = false;
        liveResyncPending = false;
        liveSequence = sequenceValue;
        const text = new TextDecoder().decode(data);
        output.emit({ kind: wireStatus === "resync_required" ? "resync" : "snapshot", data, sequence: liveSequence, pane, streamId: liveStreamId });
        set({
          status: wireStatus === "resync_required" ? "resyncing" : "live",
          raw: capRaw(text),
          lines: toLines(text),
          pane: pane || get().pane,
          sequence: liveSequence,
          hash: null,
          changedAt: Date.now(),
          error: commandError,
        });
        return true;
      }
      if (wireStatus === "output" || wireStatus === "data" || wireStatus === "live") {
        if (sequenceValue > liveSequence + 1 && liveSequence > 0) {
          set({ status: "resyncing", error: "Output gap; resyncing terminal" });
          liveForceSnapshot = true;
          liveReconnectWanted = true;
          abortLive();
          return false;
        }
        liveSequence = sequenceValue;
        output.emit({ kind: "output", data, sequence: liveSequence, pane, streamId: liveStreamId });
        set({ status: "live", sequence: liveSequence, pane: pane || get().pane, changedAt: Date.now(), error: commandError });
        return true;
      }
      if (wireStatus) set({ status: "live", error: commandError });
      return true;
    };

    const readLive = async (atLifecycle = lifecycle): Promise<void> => {
      if (mode !== "live" || !running || atLifecycle !== lifecycle || !activity.visible || liveAbort || liveRebindRefused) return;
      const abortController = new AbortController();
      liveAbort = abortController;
      let headerTimer: ReturnType<typeof setTimeout> | null = null;
      const armIdleDeadline = () => {
        if (liveIdleTimer !== null) clearTimeout(liveIdleTimer);
        liveIdleTimer = setTimeout(() => {
          if (liveAbort !== abortController || !running || atLifecycle !== lifecycle) return;
          liveReconnectWanted = true;
          set({ status: "stream_unavailable", error: "Terminal stream idle" });
          abortController.abort();
        }, TERMINAL_LIVE_IDLE_TIMEOUT_MS);
      };
      try {
        const response = await Promise.race([
          readTerminalLive(
            controllerDescriptor.target,
            liveForceSnapshot ? null : liveStreamId,
            liveForceSnapshot ? 0 : liveSequence,
            abortController.signal,
          ),
          new Promise<Response>((_, reject) => {
            headerTimer = setTimeout(() => {
              liveReconnectWanted = true;
              set({ status: "stream_unavailable", error: "Terminal stream header timeout" });
              abortController.abort();
              reject(new Error("Terminal stream header timeout"));
            }, TERMINAL_LIVE_HEADER_TIMEOUT_MS);
          }),
        ]);
        if (headerTimer !== null) clearTimeout(headerTimer);
        headerTimer = null;
        if (!running || atLifecycle !== lifecycle || abortController.signal.aborted) return;
        if (!response.ok || !response.body) {
          let errorBodyTimer: ReturnType<typeof setTimeout> | null = null;
          const body = await Promise.race([
            response.json().catch(() => ({})),
            new Promise<Record<string, unknown>>((resolve) => {
              errorBodyTimer = setTimeout(() => resolve({}), 2_000);
            }),
          ]) as Record<string, unknown>;
          if (errorBodyTimer !== null) clearTimeout(errorBodyTimer);
          if (!running || atLifecycle !== lifecycle || abortController.signal.aborted) return;
          const bodyStatus = String(body.status || "");
          const wireStatus = bodyStatus || (
            response.status === 401 ? "unauthorized"
              : response.status === 404 ? "target_gone"
                : response.status === 409 ? "generation_mismatch"
                  : "stream_unavailable"
          );
          if (["target_gone", "generation_mismatch", "unauthorized", "tmux_absent"].includes(wireStatus)) liveRebindRefused = true;
          invalidateInputQueue();
          clearTypingTimer();
          set({
            status: statusFromResponse(wireStatus, response.status),
            error: String(body.detail || body.error || wireStatus),
            raw: null,
            lines: [],
            pane: null,
            canType: false,
          });
          return;
        }
        liveBackoff = TERMINAL_LIVE_RECONNECT_MS;
        set({ status: liveSequence ? "live" : "loading", error: commandError });
        armIdleDeadline();
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let stopReading = false;
        while (!abortController.signal.aborted && running && atLifecycle === lifecycle && !stopReading) {
          const chunk = await reader.read();
          if (chunk.done) break;
          armIdleDeadline();
          buffer += decoder.decode(chunk.value, { stream: true });
          let newline = buffer.indexOf("\n");
          while (newline >= 0) {
            const line = buffer.slice(0, newline).trim();
            buffer = buffer.slice(newline + 1);
            if (line) {
              try {
                if (!handleLiveFrame(JSON.parse(line), atLifecycle)) {
                  stopReading = true;
                  void reader.cancel().catch(() => {});
                  break;
                }
              } catch {
                liveResyncPending = true;
                liveForceSnapshot = true;
                liveReconnectWanted = true;
                set({ status: "resyncing", error: "Invalid terminal stream frame" });
                abortLive();
                stopReading = true;
                void reader.cancel().catch(() => {});
                break;
              }
            }
            newline = buffer.indexOf("\n");
          }
        }
        buffer += decoder.decode();
        if (!stopReading && !abortController.signal.aborted && buffer.trim()) {
          try { handleLiveFrame(JSON.parse(buffer.trim()), atLifecycle); } catch {
            liveResyncPending = true;
            liveReconnectWanted = true;
            set({ status: "resyncing", error: "Invalid terminal stream frame" });
            abortLive();
          }
        }
      } catch (error) {
        if (!abortController.signal.aborted && running && atLifecycle === lifecycle) {
          set({ status: "stream_unavailable", error: error instanceof Error ? error.message : "Terminal stream unavailable" });
        }
      } finally {
        if (headerTimer !== null) clearTimeout(headerTimer);
        if (liveIdleTimer !== null) clearTimeout(liveIdleTimer);
        liveIdleTimer = null;
        if (liveAbort === abortController) liveAbort = null;
        const reconnect = liveReconnectWanted || !abortController.signal.aborted;
        liveReconnectWanted = false;
        if (running && atLifecycle === lifecycle && activity.visible && reconnect && !liveRebindRefused) {
          scheduleLiveReconnect(atLifecycle);
        }
      }
    };

    const sendResize = async (atLifecycle = lifecycle): Promise<boolean> => {
      if (mode !== "live" || !running || atLifecycle !== lifecycle || !activity.visible || !activity.focused || !get().canType || resizeInFlight || !resizeDesired) return false;
      const captured = resizeDesired;
      resizeInFlight = captured;
      set({ resize: { ...get().resize, busy: true, error: null } });
      try {
        const result = await resizeTerminal(controllerDescriptor, captured);
        if (!running || atLifecycle !== lifecycle) return false;
        // A newer local fit wins. Do not let an older ACK overwrite it.
        if (!dimensionsEqual(captured, resizeDesired)) return result.ok;
        if (result.ok && dimensionsEqual(result.dimensions, captured)) {
          const currentPane = get().pane;
          set({
            resize: { desired: captured, acknowledged: result.dimensions, busy: false, error: null },
            pane: currentPane
              ? { ...currentPane, width: result.dimensions.cols, height: result.dimensions.rows }
              : { width: result.dimensions.cols, height: result.dimensions.rows, cursorX: 0, cursorY: 0 },
          });
        } else {
          set({ resize: { ...get().resize, busy: false, error: result.ok ? "Resize was not acknowledged at the requested size" : result.error }, canType: !result.ok && result.revoke ? false : get().canType });
        }
        return result.ok && dimensionsEqual(result.dimensions, captured);
      } finally {
        if (dimensionsEqual(resizeInFlight, captured)) resizeInFlight = null;
        if (running && atLifecycle === lifecycle && activity.visible && activity.focused && get().canType && resizeDesired && !dimensionsEqual(resizeDesired, captured) && !resizeInFlight) void sendResize(atLifecycle);
      }
    };

    const deliver = async (items: PendingItem[], atLifecycle = lifecycle): Promise<void> => {
      if (!items.length || sendEpoch === atLifecycle || !running || atLifecycle !== lifecycle) return;
      sendEpoch = atLifecycle;
      set({ busy: true, error: null });
      let succeeded = false;
      const itemQueueEpoch = items[0].queueEpoch;
      try {
        const item = items[0];
        const out = item.kind === "keys"
          ? await sendTerminalCommand(controllerDescriptor, "terminal.keys", {
            keys: items.flatMap((candidate) => candidate.kind === "keys" ? candidate.keys : []),
          })
          : await sendTerminalCommand(controllerDescriptor, "terminal.text", {
            text: items.flatMap((candidate) => candidate.kind === "text" ? [candidate.text] : []).join(""),
            submit: item.submit,
          });
        if (!running || atLifecycle !== lifecycle || itemQueueEpoch !== queueEpoch) return;
        if (out.ok) {
          succeeded = true;
          commandError = null;
          set({ busy: false, receipt: out.receipt, error: null });
        } else {
          // A refusal, failed effect or unknown transport outcome is not safe
          // to replay. Keep the reason, cancel everything still unsent.
          commandError = out.error;
          invalidateInputQueue();
          if (out.revoke) clearTypingTimer();
          set({ busy: false, error: out.error, receipt: out.receipt || null, canType: out.revoke ? false : get().canType });
        }
      } finally {
        if (sendEpoch === atLifecycle) {
          sendEpoch = null;
        }
        if (succeeded && running && atLifecycle === lifecycle && itemQueueEpoch === queueEpoch) {
          // Drop only the batch that was captured for this send. Newer input
          // remains queued and can never be cleared by an older response.
          const captured = new Set(items);
          pending = pending.filter((candidate) => !captured.has(candidate));
          resolveItems(items, true);
          if (!pending.length) requestPromptRead(atLifecycle);
        }
        if (running && atLifecycle === lifecycle && sendEpoch === null && pending.length) {
          const firstKind = pending[0].kind;
          const firstSubmit = firstKind === "text" ? pending[0].submit : undefined;
          const nextBatch: PendingItem[] = [];
          for (const candidate of pending) {
            if (candidate.kind !== firstKind) break;
            if (candidate.kind === "text" && candidate.submit !== firstSubmit) break;
            nextBatch.push(candidate);
          }
          void deliver(nextBatch, atLifecycle);
        }
        if (atLifecycle === lifecycle) set({ busy: sendEpoch === atLifecycle || pending.length > 0 });
      }
    };

    const enqueue = (item: PendingItem): boolean => {
      if (!running || !get().canType) return false;
      pending.push(item);
      commandError = null;
      if (batchTimer === null) {
        batchTimer = setTimeout(() => {
          batchTimer = null;
          if (pending.length && sendEpoch !== lifecycle) {
            const firstKind = pending[0].kind;
            const firstSubmit = firstKind === "text" ? pending[0].submit : undefined;
            const batch: PendingItem[] = [];
            for (const candidate of pending) {
              if (candidate.kind !== firstKind) break;
              if (candidate.kind === "text" && candidate.submit !== firstSubmit) break;
              batch.push(candidate);
            }
            void deliver(batch, lifecycle);
          }
        }, TERMINAL_INPUT_BATCH_MS);
      }
      set({ busy: true, error: null });
      return true;
    };

    return {
      descriptor: controllerDescriptor,
      output: mode === "live" ? output.source : null,
      live: mode === "live",
      resize: { desired: null, acknowledged: null, busy: false, error: null },
      status: "idle",
      raw: null,
      lines: [],
      pane: null,
      canType: false,
      busy: false,
      error: null,
      receipt: null,
      sequence: 0,
      hash: null,
      changedAt: null,
      focused: false,
      visible: true,
      start() {
        if (running) return;
        lifecycle += 1;
        running = true;
        refreshRequested = false;
        commandError = null;
        liveResyncPending = false;
        liveForceSnapshot = false;
        set({ status: "loading", error: null });
        if (mode === "live") void readLive(lifecycle);
        else void poll(lifecycle);
      },
      stop() {
        lifecycle += 1;
        running = false;
        refreshRequested = false;
        commandError = null;
        liveResyncPending = false;
        liveForceSnapshot = false;
        clearTimer();
        clearLiveReconnect();
        liveReconnectWanted = false;
        abortLive();
        clearTypingTimer();
        invalidateInputQueue();
        const shouldDisarm = get().canType;
        set({ status: "idle", busy: false, canType: false });
        if (shouldDisarm) void disarmTerminal(controllerDescriptor);
      },
      setActivity(next) {
        const nextActivity = { focused: Boolean(next.focused), visible: Boolean(next.visible) };
        if (activity.focused === nextActivity.focused && activity.visible === nextActivity.visible) return;
        activity = nextActivity;
        set(activity);
        if (!activity.visible) {
          clearTimer();
          refreshRequested = false;
          clearLiveReconnect();
          liveReconnectWanted = false;
          if (mode === "live") abortLive();
        } else if (running) {
          if (mode === "live") {
            if (!liveAbort && liveReconnect === null) void readLive(lifecycle);
          }
          else void poll(lifecycle);
        }
      },
      setHostGeometry(next) {
        const dimensions = { cols: Math.max(1, Math.floor(next.cols)), rows: Math.max(1, Math.floor(next.rows)) };
        if (mode !== "live" || !activity.visible || !activity.focused || !get().canType) return;
        resizeDesired = dimensions;
        const current = get().resize;
        if (dimensionsEqual(current.desired, dimensions) && (current.busy || dimensionsEqual(current.acknowledged, dimensions))) return;
        set({ resize: { ...current, desired: dimensions, error: null } });
        void sendResize(lifecycle);
      },
      async retryResize() {
        if (!resizeDesired || !activity.visible || !activity.focused || !get().canType) return false;
        set({ resize: { ...get().resize, busy: false, error: null } });
        return sendResize(lifecycle);
      },
      async enableTyping() {
        if (!running || !["live", "not_modified", "loading", "resyncing"].includes(get().status)) return false;
        const atLifecycle = lifecycle;
        commandError = null;
        set({ error: null });
        const result = await armTerminal(controllerDescriptor);
        if (!running || atLifecycle !== lifecycle) return false;
        if (result.ok) {
          set({ canType: true, error: null });
          clearTypingTimer();
          if (result.expiresInSeconds && result.expiresInSeconds > 0) {
            const atLifecycle = lifecycle;
            typingTimer = setTimeout(() => {
              if (!running || atLifecycle !== lifecycle) return;
              invalidateInputQueue();
              commandError = "Typing grant expired";
              set({ canType: false, busy: sendEpoch === atLifecycle, error: commandError });
              void disarmTerminal(controllerDescriptor);
            }, result.expiresInSeconds * 1_000);
          }
          return true;
        }
        commandError = result.error;
        set({ canType: false, error: result.error });
        return false;
      },
      async disableTyping() {
        clearTypingTimer();
        invalidateInputQueue();
        commandError = null;
        const wasEnabled = get().canType;
        set({ canType: false, busy: sendEpoch === lifecycle, error: null });
        if (wasEnabled) {
          const result = await disarmTerminal(controllerDescriptor);
          if (!result.ok) {
            commandError = `Disarm failed: ${result.error}`;
            set({ error: commandError });
          }
        }
      },
      sendData(data) {
        if (!activity.focused || !get().canType) return false;
        const decoded = decodeTerminalInput(data);
        if (decoded.rejected) {
          commandError = `Unsupported key sequence: ${JSON.stringify(decoded.rejected)}`;
          set({ error: commandError });
          return false;
        }
        let accepted = false;
        for (const operation of decoded.operations) {
          if (operation.kind === "text") {
            // Ordinary xterm printables travel as one literal keys item. This
            // preserves a natural standalone space (the text endpoint quite
            // correctly refuses whitespace-only messages). Bracketed paste,
            // multiline text and large text retain the text transport's paste
            // discipline and never turn a pasted LF into Enter.
            const useTextTransport = operation.text.trim() !== "" && (
              Boolean(operation.paste)
              || operation.text.includes("\n")
              || operation.text.length > 200
            );
            accepted = (useTextTransport
              ? enqueue({ kind: "text", text: operation.text, submit: false, target: immutableKey, queueEpoch })
              : enqueue({ kind: "keys", keys: [{ literal: operation.text }], target: immutableKey, queueEpoch })) || accepted;
          } else accepted = enqueue({ kind: "keys", keys: operation.keys, target: immutableKey, queueEpoch }) || accepted;
        }
        return accepted;
      },
      async sendText(text, submit = false) {
        if (!text || !get().canType) return false;
        return new Promise<boolean>((resolve) => {
          if (!enqueue({ kind: "text", text, submit, target: immutableKey, queueEpoch, resolve })) resolve(false);
        });
      },
      async sendKeys(keys, _label) {
        if (!keys.length) return false;
        if (!get().canType) {
          commandError = "Press Type first";
          set({ error: commandError });
          return false;
        }
        const normalized = normalizeTerminalKeys(keys);
        if (normalized.rejected) {
          commandError = `Unsupported key: ${normalized.rejected}`;
          set({ error: commandError });
          return false;
        }
        return new Promise<boolean>((resolve) => {
          if (!enqueue({ kind: "keys", keys: normalized.keys, target: immutableKey, queueEpoch, resolve })) resolve(false);
        });
      },
    };
  });
  return store;
}
