/** HS-151-05 — Thread store tests: delta application by seq, dedup,
 * out-of-order drop, crash rule, reconnect reconcile. */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  useThreadStore,
  isCrashed,
  CRASH_TIMEOUT_MS,
  type ThreadMessage,
  type ThreadDeltaPayload,
  type ThreadTurnStartedPayload,
  type ThreadTurnDonePayload,
  type ThreadDetail,
} from "../threads";

function makeMessage(overrides: Partial<ThreadMessage> = {}): ThreadMessage {
  return {
    id: "msg-1",
    threadId: "t-1",
    parentId: null,
    role: "assistant",
    streaming: false,
    operationId: null,
    receiptId: null,
    egressScope: null,
    egressHost: null,
    modelId: null,
    statsJson: null,
    errorJson: null,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    completedAt: null,
    abortedAt: null,
    parts: [],
    ...overrides,
  };
}

function seedThread(threadId: string, messages: ThreadMessage[] = []): void {
  useThreadStore.setState({
    threads: {
      [threadId]: {
        thread: {
          id: threadId,
          title: "Test",
          recipe_id: null,
          profile_override: null,
          directory_id: null,
          parent_thread_id: null,
          status_line: null,
          token_in: 0,
          token_out: 0,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          last_turn_at: null,
        },
        messages,
        siblings: {},
        refs: [],
        draftAnnotations: [],
      },
    },
    buffers: {},
    loading: {},
  });
}

beforeEach(() => {
  useThreadStore.setState({
    threads: {},
    buffers: {},
    loading: {},
  });
});

describe("delta application", () => {
  it("applies deltas by seq in order", () => {
    seedThread("t-1", [makeMessage({ id: "msg-1", streaming: true })]);
    const { applyTurnStarted, applyDelta, getBufferText } =
      useThreadStore.getState();

    applyTurnStarted({
      thread_id: "t-1",
      message_id: "msg-2",
      user_message_id: "u-1",
      model_id: "test",
      egress: null,
    });

    // msg-2 gets a buffer from turn_started, but msg-1 exists already —
    // create a buffer for msg-1 to test delta application on it.
    useThreadStore.setState((s) => ({
      buffers: {
        ...s.buffers,
        "msg-1": { messageId: "msg-1", parts: new Map(), highSeq: -1 },
      },
    }));

    const ok1 = applyDelta({
      thread_id: "t-1",
      message_id: "msg-1",
      ordinal: 0,
      kind: "text",
      text: "Hello",
      seq: 0,
    });
    expect(ok1).toBe(true);

    const ok2 = applyDelta({
      thread_id: "t-1",
      message_id: "msg-1",
      ordinal: 0,
      kind: "text",
      text: " world",
      seq: 1,
    });
    expect(ok2).toBe(true);

    expect(getBufferText("msg-1")).toBe("Hello world");
  });

  it("drops duplicate seq", () => {
    seedThread("t-1", [makeMessage({ id: "msg-1", streaming: true })]);
    const { applyDelta } = useThreadStore.getState();

    useThreadStore.setState((s) => ({
      buffers: {
        ...s.buffers,
        "msg-1": { messageId: "msg-1", parts: new Map(), highSeq: -1 },
      },
    }));

    applyDelta({
      thread_id: "t-1",
      message_id: "msg-1",
      ordinal: 0,
      kind: "text",
      text: "A",
      seq: 0,
    });

    // Same seq — should be dropped.
    const dropped = applyDelta({
      thread_id: "t-1",
      message_id: "msg-1",
      ordinal: 0,
      kind: "text",
      text: "B",
      seq: 0,
    });
    expect(dropped).toBe(false);

    expect(useThreadStore.getState().getBufferText("msg-1")).toBe("A");
  });

  it("drops out-of-order (lower seq than highSeq)", () => {
    seedThread("t-1", [makeMessage({ id: "msg-1", streaming: true })]);
    const { applyDelta } = useThreadStore.getState();

    useThreadStore.setState((s) => ({
      buffers: {
        ...s.buffers,
        "msg-1": { messageId: "msg-1", parts: new Map(), highSeq: 5 },
      },
    }));

    const dropped = applyDelta({
      thread_id: "t-1",
      message_id: "msg-1",
      ordinal: 0,
      kind: "text",
      text: "stale",
      seq: 3,
    });
    expect(dropped).toBe(false);
  });

  it("ignores deltas for unknown messages (no buffer)", () => {
    seedThread("t-1");
    const { applyDelta } = useThreadStore.getState();

    const result = applyDelta({
      thread_id: "t-1",
      message_id: "unknown-msg",
      ordinal: 0,
      kind: "text",
      text: "ignored",
      seq: 0,
    });
    expect(result).toBe(false);
  });
});

describe("crash rule", () => {
  it("streaming=true + updatedAt older than CRASH_TIMEOUT_MS = crashed", () => {
    const old = new Date(Date.now() - CRASH_TIMEOUT_MS - 1000).toISOString();
    expect(
      isCrashed(makeMessage({ streaming: true, updatedAt: old })),
    ).toBe(true);
  });

  it("streaming=true + updatedAt recent = not crashed", () => {
    const recent = new Date().toISOString();
    expect(
      isCrashed(makeMessage({ streaming: true, updatedAt: recent })),
    ).toBe(false);
  });

  it("streaming=false = not crashed regardless of age", () => {
    const old = new Date(Date.now() - CRASH_TIMEOUT_MS - 5000).toISOString();
    expect(
      isCrashed(makeMessage({ streaming: false, updatedAt: old })),
    ).toBe(false);
  });
});

describe("turn lifecycle", () => {
  it("applyTurnStarted creates a message stub with streaming=true", () => {
    seedThread("t-1");

    useThreadStore.getState().applyTurnStarted({
      thread_id: "t-1",
      message_id: "msg-a",
      user_message_id: "u-1",
      model_id: "qwen",
      egress: "local",
    });

    const detail = useThreadStore.getState().threads["t-1"];
    const msg = detail.messages.find((m) => m.id === "msg-a");
    expect(msg).toBeDefined();
    expect(msg!.streaming).toBe(true);
    expect(msg!.modelId).toBe("qwen");
    expect(msg!.egressScope).toBe("local");
    expect(useThreadStore.getState().buffers["msg-a"]).toBeDefined();
  });

  it("applyTurnDone finalizes message, clears buffer, sets receipt", () => {
    seedThread("t-1", [makeMessage({ id: "msg-a", streaming: true })]);

    // Seed a buffer with some content.
    useThreadStore.setState((s) => ({
      buffers: {
        ...s.buffers,
        "msg-a": {
          messageId: "msg-a",
          parts: new Map([[0, { kind: "text" as const, text: "Done content" }]]),
          highSeq: 5,
        },
      },
    }));

    useThreadStore.getState().applyTurnDone({
      thread_id: "t-1",
      message_id: "msg-a",
      receipt_id: "rcpt-12345678abcdef",
      outcome: "succeeded",
      egress: "local",
      stats: { prompt_tokens: 100, completion_tokens: 50 },
    });

    const detail = useThreadStore.getState().threads["t-1"];
    const msg = detail.messages.find((m) => m.id === "msg-a");
    expect(msg!.streaming).toBe(false);
    expect(msg!.receiptId).toBe("rcpt-12345678abcdef");
    expect(msg!.parts).toHaveLength(1);
    expect(msg!.parts[0].text).toBe("Done content");
    expect(useThreadStore.getState().buffers["msg-a"]).toBeUndefined();
  });
});

describe("crash rule with epoch timestamps", () => {
  it("handles epoch-second timestamps from the server correctly", () => {
    // The server returns epoch seconds (e.g. 1725000000.123), not ISO strings.
    // wireTimestamp converts them to ISO; isCrashed must compare correctly.
    const nowEpoch = Date.now() / 1000;
    const recentIso = new Date((nowEpoch - 2) * 1000).toISOString();
    const oldIso = new Date((nowEpoch - CRASH_TIMEOUT_MS / 1000 - 5) * 1000).toISOString();

    expect(isCrashed(makeMessage({ streaming: true, updatedAt: recentIso }))).toBe(false);
    expect(isCrashed(makeMessage({ streaming: true, updatedAt: oldIso }))).toBe(true);
  });
});

describe("missing detail on mount", () => {
  it("renders without a thread in store, then hydrates after loadThread", async () => {
    // Initially the store has no thread for "t-new".
    expect(useThreadStore.getState().threads["t-new"]).toBeUndefined();
    expect(useThreadStore.getState().loading["t-new"]).toBeUndefined();

    // Mock the server returning a flat thread response.
    vi.stubGlobal("fetch", () =>
      Promise.resolve(
        new Response(
          JSON.stringify({
            id: "t-new",
            title: "Hydrated Thread",
            recipe_id: null,
            profile_override: null,
            directory_id: null,
            parent_thread_id: null,
            status_line: null,
            token_in: 5,
            token_out: 10,
            created_at: Date.now() / 1000,
            updated_at: Date.now() / 1000,
            last_turn_at: null,
            messages: [
              {
                id: "m1",
                role: "user",
                parent_id: null,
                streaming: 0,
                receipt_id: null,
                egress_scope: null,
                model_id: null,
                parts: [{ id: "p1", kind: "text", text: "hello", ordinal: 0, sensitive: 0 }],
                created_at: Date.now() / 1000,
                updated_at: Date.now() / 1000,
                completed_at: null,
                aborted_at: null,
              },
            ],
            refs: [],
            siblings: {},
          }),
          { headers: { "content-type": "application/json" } },
        ),
      ),
    );

    await useThreadStore.getState().loadThread("t-new");

    const detail = useThreadStore.getState().threads["t-new"];
    expect(detail).toBeDefined();
    expect(detail.thread.title).toBe("Hydrated Thread");
    expect(detail.thread.token_in).toBe(5);
    expect(detail.messages).toHaveLength(1);
    expect(detail.messages[0].parts[0].text).toBe("hello");
    // Timestamps should be ISO strings, not raw epoch numbers.
    expect(detail.thread.created_at).toMatch(/^\d{4}-\d{2}-\d{2}T/);

    vi.unstubAllGlobals();
  });
});

describe("reconnect reconcile", () => {
  it("reconcile reloads the thread from the API", async () => {
    const mockDetail: ThreadDetail = {
      thread: {
        id: "t-1",
        title: "Reconciled",
        recipe_id: null,
        profile_override: null,
        directory_id: null,
        parent_thread_id: null,
        status_line: null,
        token_in: 10,
        token_out: 20,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        last_turn_at: null,
      },
      messages: [],
      siblings: {},
      refs: [],
    };

    // The server returns a FLAT response: thread fields at root, plus
    // messages/siblings/refs arrays mixed in.
    vi.stubGlobal("fetch", () =>
      Promise.resolve(
        new Response(
          JSON.stringify({
            id: "t-1",
            title: "Reconciled",
            recipe_id: null,
            profile_override: null,
            directory_id: null,
            parent_thread_id: null,
            status_line: null,
            token_in: 10,
            token_out: 20,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            last_turn_at: null,
            messages: [],
            refs: [],
            siblings: {},
          }),
          { headers: { "content-type": "application/json" } },
        ),
      ),
    );

    seedThread("t-1");
    await useThreadStore.getState().reconcile("t-1");
    expect(useThreadStore.getState().threads["t-1"].thread.title).toBe("Reconciled");

    vi.unstubAllGlobals();
  });
});
