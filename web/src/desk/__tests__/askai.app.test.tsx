/** Ask AI (the thread window): the face half of the browser walks the test
 * diet moved (2026-10-11). The real ThreadPullout with the real thread store;
 * only fetch is mocked, with the hub's real response shapes:
 *   POST /api/threads/{id}/turns  -> 201 {thread_id, user_message_id, assistant_message_id}
 *     (holdspeak/services/thread_service.py start_turn; routes/threads.py api_start_turn)
 *   POST /api/threads/{id}/abort  -> {aborted: true, message_id}
 *     (holdspeak/services/thread_service.py ThreadService.abort)
 *   POST /api/threads/{id}/decide -> {call_id, decision, always, state}
 *     (holdspeak/web/routes/threads.py api_decide_tool)
 * The hub half (the route writes the policy, the re-dispatch, the denied
 * result) is in tests/unit/test_desk_ask_ai.py. */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useThreadStore, type ThreadDetail, type ThreadMessage, type ToolRow } from "../threads";
import { ThreadPullout } from "../pullouts/ThreadPullout";
import { RuntimeBusProvider } from "../../runtime/RuntimeBus";

type Call = { url: string; method: string; body: unknown };
let calls: Call[] = [];

function hub(routes: Record<string, { status?: number; body: unknown }>) {
  calls = [];
  vi.stubGlobal("fetch", vi.fn((input: string, init: RequestInit = {}) => {
    const url = String(input);
    const method = String(init.method ?? "GET");
    calls.push({ url, method, body: init.body ? JSON.parse(String(init.body)) : undefined });
    const hit = Object.entries(routes).find(([key]) => `${method} ${url}`.endsWith(key));
    // Any other request fails like a closed hub (the other suites' default).
    if (!hit) return Promise.reject(new TypeError("no hub in this test"));
    const { status = 200, body } = hit[1];
    return Promise.resolve({
      ok: status < 400, status,
      headers: { get: () => "application/json" },
      json: () => Promise.resolve(body),
      text: () => Promise.resolve(JSON.stringify(body)),
    });
  }));
}

beforeEach(() => {
  vi.stubGlobal("WebSocket", class {
    addEventListener() {}
    removeEventListener() {}
    close() {}
    send() {}
    readyState = 3;
  });
});
afterEach(() => {
  vi.unstubAllGlobals();
  useThreadStore.setState({ threads: {}, buffers: {}, loading: {}, toolRows: {}, statusLines: {} });
});

const now = () => new Date().toISOString();

function msg(over: Partial<ThreadMessage> = {}): ThreadMessage {
  return {
    id: "msg-1", threadId: "t-1", parentId: null, role: "assistant", streaming: false,
    operationId: null, receiptId: null, egressScope: null, egressHost: null, modelId: null,
    statsJson: null, errorJson: null, createdAt: now(), updatedAt: now(), completedAt: now(),
    abortedAt: null,
    parts: [{ id: "p1", messageId: "msg-1", ordinal: 0, kind: "text", text: "Hello", sensitive: false }],
    ...over,
  };
}

function seed(messages: ThreadMessage[]) {
  const detail: ThreadDetail = {
    thread: {
      id: "t-1", title: "Abort Test", recipe_id: null, profile_override: null, directory_id: null,
      parent_thread_id: null, status_line: null, mode: null, call_mode: 0, token_in: 0, token_out: 0,
      created_at: now(), updated_at: now(), last_turn_at: null,
    },
    messages, siblings: {}, refs: [], draftAnnotations: [],
  };
  useThreadStore.setState({ threads: { "t-1": detail }, buffers: {}, loading: {} });
}

function renderThread() {
  return render(
    <RuntimeBusProvider>
      <ThreadPullout
        object={{ kind: "thread", id: "t-1", title: "Abort Test", ref: { kind: "thread", id: "t-1", title: "Abort Test" } as any }}
        onClose={() => {}}
      />
    </RuntimeBusProvider>,
  );
}

describe("Ask AI: Send, Stop, Send", () => {
  it("Send flips to Stop while the turn streams; Stop aborts and Send comes back", async () => {
    // replaces: tests/e2e/test_hs151_thread_glass.py::test_abort_mid_stream_flips_send_stop_send
    hub({
      "POST /api/threads/t-1/turns": { status: 201, body: { thread_id: "t-1", user_message_id: "u-9", assistant_message_id: "a-9" } },
      "POST /api/threads/t-1/abort": { body: { aborted: true, message_id: "a-9" } },
    });
    seed([]);
    renderThread();
    fireEvent.change(screen.getByTestId("composer-input"), { target: { value: "This will be aborted" } });
    fireEvent.click(screen.getByTestId("composer-send"));

    // The accepted turn streams: the verb is Stop.
    await waitFor(() => expect(screen.getByTestId("composer-stop")).toBeInTheDocument());
    expect(screen.queryByTestId("composer-send")).not.toBeInTheDocument();
    expect(calls.find((c) => c.url.endsWith("/api/threads/t-1/turns"))?.body).toEqual({ text: "This will be aborted" });

    fireEvent.click(screen.getByTestId("composer-stop"));
    await waitFor(() => expect(screen.getByTestId("composer-send")).toBeInTheDocument());
    expect(screen.queryByTestId("composer-stop")).not.toBeInTheDocument();
    expect(calls.some((c) => c.method === "POST" && c.url.endsWith("/api/threads/t-1/abort"))).toBe(true);
    const aborted = useThreadStore.getState().threads["t-1"].messages.find((m) => m.id === "a-9")!;
    expect(aborted.streaming).toBe(false);
    expect(aborted.abortedAt).toBeTruthy();
  });
});

describe("Ask AI: the decision box sends the owner's decision", () => {
  const held: ToolRow = {
    callId: "glass-call-1", messageId: "msg-1", name: "desk.create", toolClass: "effect_proposal",
    argsHead: '{"kind":"notes"}', state: "awaiting_decision", decisionRequired: true,
  };

  function withRow(row: ToolRow, decide: Record<string, unknown>) {
    hub({ "POST /api/threads/t-1/decide": { body: decide } });
    seed([msg()]);
    useThreadStore.setState({ toolRows: { "t-1": { [row.callId]: row } } });
    return renderThread();
  }

  const rowState = () => screen.getByTestId("tool-row").getAttribute("data-tool-state");
  const decideBody = () => calls.find((c) => c.url.endsWith("/api/threads/t-1/decide"))?.body;

  it("Allow once sends approve and the row leaves the held state", async () => {
    // replaces: tests/e2e/test_hs152_hands_glass.py::test_allow_once_decision_box_to_receipted
    withRow(held, { call_id: "glass-call-1", decision: "approve", always: false, state: "admitted" });
    fireEvent.click(screen.getByTestId("allow-once"));
    await waitFor(() => expect(decideBody()).toEqual({ call_id: "glass-call-1", decision: "approve" }));
    expect(rowState()).toBe("running");
    expect(screen.queryByTestId("decision-box")).toBeNull();
  });

  it("Allow always sends always: true", async () => {
    // replaces: tests/e2e/test_hs152_hands_glass.py::test_allow_always_auto_admit (the press)
    withRow(held, { call_id: "glass-call-1", decision: "approve", always: true, state: "admitted" });
    fireEvent.click(screen.getByTestId("allow-always"));
    await waitFor(() => expect(decideBody()).toEqual({ call_id: "glass-call-1", decision: "approve", always: true }));
    expect(rowState()).toBe("running");
  });

  it("Deny sends deny and the row is denied", async () => {
    // replaces: tests/e2e/test_hs152_hands_glass.py::test_deny_shows_tool_denied_row
    withRow(held, { call_id: "glass-call-1", decision: "deny", always: false, state: "denied" });
    fireEvent.click(screen.getByTestId("deny"));
    await waitFor(() => expect(decideBody()).toEqual({ call_id: "glass-call-1", decision: "deny" }));
    expect(rowState()).toBe("denied");
  });

  const asking: ToolRow = {
    ...held, callId: "glass-elicit-1", name: "desk.list", toolClass: "evidence_read", state: "elicitation",
    elicitation: {
      type: "object", prompt: "Pick a fruit",
      properties: { name: { type: "string", title: "Name" } }, required: ["name"],
    },
  };

  it("an elicitation Submit sends the answer the owner typed", async () => {
    // replaces: tests/e2e/test_hs152_hands_glass.py::test_elicitation_form_submit_and_decline (Submit)
    withRow(asking, { call_id: "glass-elicit-1", decision: "approve", always: false, state: "admitted" });
    fireEvent.change(screen.getByRole("textbox", { name: "Name" }), { target: { value: "Apple" } });
    fireEvent.click(screen.getByTestId("elicitation-submit"));
    await waitFor(() => expect(decideBody()).toEqual({ call_id: "glass-elicit-1", decision: "approve", answer: { name: "Apple" } }));
    expect(rowState()).toBe("running");
  });

  it("an elicitation Decline sends deny and the row is denied", async () => {
    // replaces: tests/e2e/test_hs152_hands_glass.py::test_elicitation_form_submit_and_decline (Decline)
    withRow(asking, { call_id: "glass-elicit-1", decision: "deny", always: false, state: "denied" });
    fireEvent.click(screen.getByTestId("elicitation-decline"));
    await waitFor(() => expect(decideBody()).toEqual({ call_id: "glass-elicit-1", decision: "deny" }));
    expect(rowState()).toBe("denied");
  });
});
