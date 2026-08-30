/** HS-152-04 — Thread tool row tests: store reducers (frames -> rows,
 * decide optimistic/reconcile, hydrate from parts) and ThreadPullout
 * tool row rendering (decision box, elicitation form, keyboard reach). */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import {
  useThreadStore,
  type ThreadMessage,
  type ThreadDetail,
  type ThreadToolPendingPayload,
  type ThreadToolResultPayload,
  type ThreadStatusLinePayload,
  type ToolRow,
} from "../threads";
import { ThreadPullout } from "../pullouts/ThreadPullout";
import { RuntimeBusProvider } from "../../runtime/RuntimeBus";

// Mock the WebSocket so RuntimeBusProvider does not connect.
beforeEach(() => {
  vi.stubGlobal("WebSocket", class {
    addEventListener() {}
    removeEventListener() {}
    close() {}
    send() {}
    readyState = 3; // CLOSED
  });
});
afterEach(() => {
  vi.unstubAllGlobals();
  useThreadStore.setState({
    threads: {},
    buffers: {},
    loading: {},
    focusMessageId: null,
    toolRows: {},
    statusLines: {},
  });
});

function makeMsg(overrides: Partial<ThreadMessage> = {}): ThreadMessage {
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
    completedAt: new Date().toISOString(),
    abortedAt: null,
    parts: [{ id: "p1", messageId: "msg-1", ordinal: 0, kind: "text", text: "Hello", sensitive: false }],
    ...overrides,
  };
}

function seedStore(messages: ThreadMessage[], siblings: Record<string, string[]> = {}) {
  const detail: ThreadDetail = {
    thread: {
      id: "t-1",
      title: "Test Thread",
      recipe_id: null,
      profile_override: null,
      directory_id: null,
      parent_thread_id: null,
      status_line: null,
      token_in: 100,
      token_out: 50,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      last_turn_at: null,
    },
    messages,
    siblings,
    refs: [],
  };
  useThreadStore.setState({ threads: { "t-1": detail }, buffers: {}, loading: {} });
}

function renderPullout() {
  return render(
    <RuntimeBusProvider>
      <ThreadPullout
        object={{
          kind: "thread",
          id: "t-1",
          title: "Test Thread",
          ref: {
            kind: "thread",
            id: "t-1",
            title: "Test Thread",
            tokenIn: 100,
            tokenOut: 50,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          } as any,
        }}
        onClose={() => {}}
      />
    </RuntimeBusProvider>,
  );
}

// ── Store reducer tests ────────────────────────────────────────────

describe("ThreadStore tool row reducers", () => {
  it("applyToolPending creates a tool row keyed by call_id", () => {
    const payload: ThreadToolPendingPayload = {
      thread_id: "t-1",
      message_id: "msg-1",
      call_id: "call-1",
      name: "desk.create",
      args_head: '{"kind":"note"}',
      class: "effect_proposal",
      decision_required: true,
    };
    useThreadStore.getState().applyToolPending(payload);
    const row = useThreadStore.getState().toolRows["t-1"]?.["call-1"];
    expect(row).toBeTruthy();
    expect(row!.state).toBe("awaiting_decision");
    expect(row!.name).toBe("desk.create");
    expect(row!.toolClass).toBe("effect_proposal");
    expect(row!.decisionRequired).toBe(true);
  });

  it("applyToolPending with elicitation sets state to elicitation", () => {
    const payload: ThreadToolPendingPayload = {
      thread_id: "t-1",
      message_id: "msg-1",
      call_id: "call-e",
      name: "some.tool",
      args_head: "{}",
      class: "evidence_read",
      decision_required: true,
      elicitation: { type: "object", properties: { name: { type: "string" } } },
    };
    useThreadStore.getState().applyToolPending(payload);
    const row = useThreadStore.getState().toolRows["t-1"]?.["call-e"];
    expect(row!.state).toBe("elicitation");
    expect(row!.elicitation).toBeTruthy();
  });

  it("applyToolPending without decision_required sets state to pending", () => {
    const payload: ThreadToolPendingPayload = {
      thread_id: "t-1",
      message_id: "msg-1",
      call_id: "call-p",
      name: "desk.list",
      args_head: "{}",
      class: "evidence_read",
      decision_required: false,
    };
    useThreadStore.getState().applyToolPending(payload);
    const row = useThreadStore.getState().toolRows["t-1"]?.["call-p"];
    expect(row!.state).toBe("pending");
  });

  it("applyToolResult updates a pending row to receipted", () => {
    // First create the pending row
    useThreadStore.getState().applyToolPending({
      thread_id: "t-1",
      message_id: "msg-1",
      call_id: "call-r",
      name: "desk.list",
      args_head: "{}",
      class: "evidence_read",
      decision_required: false,
    });

    // Now apply the result
    useThreadStore.getState().applyToolResult({
      thread_id: "t-1",
      message_id: "msg-1",
      call_id: "call-r",
      name: "desk.list",
      receipt_id: "tr-abc123def456",
      outcome: "succeeded",
      kind: "data",
      summary: '{"items":[]}',
      sensitive: false,
    });

    const row = useThreadStore.getState().toolRows["t-1"]?.["call-r"];
    expect(row!.state).toBe("receipted");
    expect(row!.receiptId).toBe("tr-abc123def456");
    expect(row!.outcome).toBe("succeeded");
  });

  it("applyToolResult with tool_denied sets state to denied", () => {
    useThreadStore.getState().applyToolPending({
      thread_id: "t-1",
      message_id: "msg-1",
      call_id: "call-d",
      name: "desk.create",
      args_head: "{}",
      class: "effect_proposal",
      decision_required: true,
    });

    useThreadStore.getState().applyToolResult({
      thread_id: "t-1",
      message_id: "msg-1",
      call_id: "call-d",
      name: "desk.create",
      receipt_id: "",
      outcome: "failed",
      kind: "tool_denied",
      summary: "",
      sensitive: false,
    });

    const row = useThreadStore.getState().toolRows["t-1"]?.["call-d"];
    expect(row!.state).toBe("denied");
    expect(row!.error).toBe("tool_denied");
  });

  it("applyToolResult with tool_execution_failed sets state to failed", () => {
    useThreadStore.getState().applyToolPending({
      thread_id: "t-1",
      message_id: "msg-1",
      call_id: "call-f",
      name: "desk.create",
      args_head: "{}",
      class: "effect_proposal",
      decision_required: false,
    });

    useThreadStore.getState().applyToolResult({
      thread_id: "t-1",
      message_id: "msg-1",
      call_id: "call-f",
      name: "desk.create",
      receipt_id: "",
      outcome: "failed",
      kind: "tool_execution_failed",
      summary: "Something broke",
      sensitive: false,
    });

    const row = useThreadStore.getState().toolRows["t-1"]?.["call-f"];
    expect(row!.state).toBe("failed");
    expect(row!.error).toBe("tool_execution_failed");
  });

  it("decideOptimistic flips state to running on approve", () => {
    useThreadStore.getState().applyToolPending({
      thread_id: "t-1",
      message_id: "msg-1",
      call_id: "call-o",
      name: "desk.create",
      args_head: "{}",
      class: "effect_proposal",
      decision_required: true,
    });

    useThreadStore.getState().decideOptimistic("t-1", "call-o", "approve");
    const row = useThreadStore.getState().toolRows["t-1"]?.["call-o"];
    expect(row!.state).toBe("running");
  });

  it("decideOptimistic flips state to denied on deny", () => {
    useThreadStore.getState().applyToolPending({
      thread_id: "t-1",
      message_id: "msg-1",
      call_id: "call-od",
      name: "desk.create",
      args_head: "{}",
      class: "effect_proposal",
      decision_required: true,
    });

    useThreadStore.getState().decideOptimistic("t-1", "call-od", "deny");
    const row = useThreadStore.getState().toolRows["t-1"]?.["call-od"];
    expect(row!.state).toBe("denied");
  });

  it("applyStatusLine sets the live status line for a thread", () => {
    useThreadStore.getState().applyStatusLine({
      thread_id: "t-1",
      text: "Running desk.create...",
    });
    expect(useThreadStore.getState().statusLines["t-1"]).toBe("Running desk.create...");
  });

  it("hydrateToolRows reconstructs tool rows from persisted parts", () => {
    seedStore([
      makeMsg({
        id: "asst-1",
        role: "assistant",
        parts: [
          {
            id: "p-tc",
            messageId: "asst-1",
            ordinal: 0,
            kind: "tool_call",
            text: "",
            sensitive: false,
            metaJson: {
              id: "call-h",
              name: "desk.list",
              arguments: "{}",
              class: "evidence_read",
              state: "admitted",
            },
          },
          {
            id: "p-text",
            messageId: "asst-1",
            ordinal: 1,
            kind: "text",
            text: "Some text",
            sensitive: false,
          },
        ],
      }),
      makeMsg({
        id: "tool-1",
        role: "tool",
        parentId: "asst-1",
        parts: [
          {
            id: "p-tr",
            messageId: "tool-1",
            ordinal: 0,
            kind: "text",
            text: '{"items":[]}',
            sensitive: false,
            toolCallId: "call-h",
            metaJson: { kind: "data", receipt_id: "tr-hydrate123" },
          },
        ],
      }),
    ]);

    useThreadStore.getState().hydrateToolRows("t-1");
    const row = useThreadStore.getState().toolRows["t-1"]?.["call-h"];
    expect(row).toBeTruthy();
    expect(row!.state).toBe("receipted");
    expect(row!.receiptId).toBe("tr-hydrate123");
    expect(row!.name).toBe("desk.list");
  });

  it("hydrateToolRows: awaiting_decision when no result exists", () => {
    seedStore([
      makeMsg({
        id: "asst-2",
        role: "assistant",
        parts: [
          {
            id: "p-tc2",
            messageId: "asst-2",
            ordinal: 0,
            kind: "tool_call",
            text: "",
            sensitive: false,
            metaJson: {
              id: "call-h2",
              name: "desk.create",
              arguments: '{"kind":"note"}',
              class: "effect_proposal",
              state: "awaiting_decision",
            },
          },
        ],
      }),
    ]);

    useThreadStore.getState().hydrateToolRows("t-1");
    const row = useThreadStore.getState().toolRows["t-1"]?.["call-h2"];
    expect(row).toBeTruthy();
    expect(row!.state).toBe("awaiting_decision");
    expect(row!.decisionRequired).toBe(true);
  });
});

// ── Pullout rendering tests ────────────────────────────────────────

describe("ThreadPullout tool rows", () => {
  it("renders a decision box with Allow once / Allow always / Deny", () => {
    seedStore([makeMsg()]);
    // Seed a tool row in awaiting_decision
    useThreadStore.setState({
      toolRows: {
        "t-1": {
          "call-ui": {
            callId: "call-ui",
            messageId: "msg-1",
            name: "desk.create",
            toolClass: "effect_proposal",
            argsHead: '{"kind":"note"}',
            state: "awaiting_decision",
            decisionRequired: true,
          },
        },
      },
    });
    renderPullout();

    const box = screen.getByTestId("decision-box");
    expect(box).toBeTruthy();
    expect(screen.getByTestId("allow-once")).toBeTruthy();
    expect(screen.getByTestId("allow-always")).toBeTruthy();
    expect(screen.getByTestId("deny")).toBeTruthy();
  });

  it("keyboard: Tab reaches all three decision verbs", () => {
    seedStore([makeMsg()]);
    useThreadStore.setState({
      toolRows: {
        "t-1": {
          "call-kb": {
            callId: "call-kb",
            messageId: "msg-1",
            name: "desk.create",
            toolClass: "effect_proposal",
            argsHead: "{}",
            state: "awaiting_decision",
            decisionRequired: true,
          },
        },
      },
    });
    renderPullout();

    const allowOnce = screen.getByTestId("allow-once");
    const allowAlways = screen.getByTestId("allow-always");
    const deny = screen.getByTestId("deny");

    // All buttons should be focusable (type="button", not disabled)
    expect(allowOnce.tagName).toBe("BUTTON");
    expect(allowAlways.tagName).toBe("BUTTON");
    expect(deny.tagName).toBe("BUTTON");
    expect(allowOnce.hasAttribute("disabled")).toBe(false);
    expect(allowAlways.hasAttribute("disabled")).toBe(false);
    expect(deny.hasAttribute("disabled")).toBe(false);
  });

  it("renders receipted row with short-id and outcome", () => {
    seedStore([makeMsg()]);
    useThreadStore.setState({
      toolRows: {
        "t-1": {
          "call-rc": {
            callId: "call-rc",
            messageId: "msg-1",
            name: "desk.list",
            toolClass: "evidence_read",
            argsHead: "{}",
            state: "receipted",
            decisionRequired: false,
            receiptId: "tr-abcd1234efgh",
            outcome: "succeeded",
            kind: "data",
          },
        },
      },
    });
    renderPullout();

    const toolRow = screen.getByTestId("tool-row");
    expect(toolRow).toBeTruthy();
    expect(toolRow.textContent).toContain("efgh");
    expect(toolRow.textContent).toContain("DONE");
  });

  it("renders denied row with error code", () => {
    seedStore([makeMsg()]);
    useThreadStore.setState({
      toolRows: {
        "t-1": {
          "call-dn": {
            callId: "call-dn",
            messageId: "msg-1",
            name: "desk.create",
            toolClass: "effect_proposal",
            argsHead: "{}",
            state: "denied",
            decisionRequired: false,
            error: "tool_denied",
          },
        },
      },
    });
    renderPullout();

    const toolRow = screen.getByTestId("tool-row");
    expect(toolRow.textContent).toContain("DENIED");
    expect(toolRow.textContent).toContain("tool_denied");
  });

  it("renders People badge for sensitive tool results", () => {
    seedStore([makeMsg()]);
    useThreadStore.setState({
      toolRows: {
        "t-1": {
          "call-ppl": {
            callId: "call-ppl",
            messageId: "msg-1",
            name: "people.readiness",
            toolClass: "evidence_read",
            argsHead: "{}",
            state: "receipted",
            decisionRequired: false,
            receiptId: "tr-people1234",
            outcome: "succeeded",
            kind: "data",
            sensitive: true,
          },
        },
      },
    });
    renderPullout();

    expect(screen.getByTestId("people-badge")).toBeTruthy();
    expect(screen.getByTestId("people-badge").textContent).toBe("PEOPLE");
  });

  it("renders elicitation form with Submit / Decline", () => {
    seedStore([makeMsg()]);
    useThreadStore.setState({
      toolRows: {
        "t-1": {
          "call-el": {
            callId: "call-el",
            messageId: "msg-1",
            name: "some.tool",
            toolClass: "evidence_read",
            argsHead: "{}",
            state: "elicitation",
            decisionRequired: true,
            elicitation: {
              type: "object",
              prompt: "Pick a name",
              properties: {
                name: { type: "string", title: "Name" },
              },
              required: ["name"],
            },
          },
        },
      },
    });
    renderPullout();

    expect(screen.getByTestId("elicitation-form")).toBeTruthy();
    expect(screen.getByTestId("elicitation-submit")).toBeTruthy();
    expect(screen.getByTestId("elicitation-decline")).toBeTruthy();
    expect(screen.getByText("Pick a name")).toBeTruthy();
  });

  it("renders class glyph for tool row", () => {
    seedStore([makeMsg()]);
    useThreadStore.setState({
      toolRows: {
        "t-1": {
          "call-gl": {
            callId: "call-gl",
            messageId: "msg-1",
            name: "desk.create",
            toolClass: "effect_proposal",
            argsHead: "{}",
            state: "pending",
            decisionRequired: false,
          },
        },
      },
    });
    const { container } = renderPullout();

    const glyph = container.querySelector(".thread-tool-class-glyph");
    expect(glyph).toBeTruthy();
    expect(glyph!.textContent).toBe("E");
  });

  it("renders failed row with error code", () => {
    seedStore([makeMsg()]);
    useThreadStore.setState({
      toolRows: {
        "t-1": {
          "call-fail": {
            callId: "call-fail",
            messageId: "msg-1",
            name: "desk.create",
            toolClass: "effect_proposal",
            argsHead: "{}",
            state: "failed",
            decisionRequired: false,
            error: "tool_execution_failed",
          },
        },
      },
    });
    renderPullout();

    const toolRow = screen.getByTestId("tool-row");
    expect(toolRow.textContent).toContain("FAILED");
    expect(toolRow.textContent).toContain("tool_execution_failed");
  });
});
