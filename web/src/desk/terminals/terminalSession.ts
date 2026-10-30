import { createStore, type StoreApi } from "zustand/vanilla";
import { armTerminal, disarmTerminal, readTerminalSubscription, sendTerminalCommand } from "./api";
import { decodeTerminalInput, normalizeTerminalKeys } from "./input";
import type {
  TerminalDescriptor,
  TerminalKey,
  TerminalPaneGeometry,
  TerminalReceipt,
  TerminalSessionState,
  TerminalStatus,
} from "./types";

export const TERMINAL_FOCUSED_POLL_MS = 350;
export const TERMINAL_VISIBLE_POLL_MS = 1_200;
export const TERMINAL_INPUT_BATCH_MS = 30;

// eslint-disable-next-line no-control-regex
const ANSI = /\u001b\[[0-9;?]*[ -/]*[@-~]|\u001b\][\s\S]*?(?:\u0007|\u001b\\)|\u001b[@-Z\\-_]/g;
const RAW_MAX_CHARS = 256_000;

function toLines(raw: string): string[] {
  return raw.replace(ANSI, "").replace(/\r/g, "").split("\n");
}

function capRaw(raw: string): string {
  return raw.length > RAW_MAX_CHARS ? raw.slice(-RAW_MAX_CHARS) : raw;
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
          schedule(atLifecycle);
        }
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
        commandError = null;
        set({ status: "loading", error: null });
        void poll(lifecycle);
      },
      stop() {
        lifecycle += 1;
        running = false;
        commandError = null;
        clearTimer();
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
        if (!activity.visible) clearTimer();
        else if (running) void poll(lifecycle);
      },
      async enableTyping() {
        if (!running || !["live", "not_modified"].includes(get().status)) return false;
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
        if (wasEnabled) await disarmTerminal(controllerDescriptor);
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
        if (!keys.length || !get().canType) return false;
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
