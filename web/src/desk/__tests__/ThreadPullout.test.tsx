/** HS-151-05 — ThreadPullout rendering tests: rows render streaming, done,
 * error, crashed+Retry, sibling picker. */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { useThreadStore, type ThreadMessage, type ThreadDetail } from "../threads";
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
afterEach(() => vi.unstubAllGlobals());

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
    draftAnnotations: [],
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

describe("ThreadPullout rows", () => {
  it("renders a done assistant row with text through Material", () => {
    seedStore([makeMsg()]);
    renderPullout();
    expect(screen.getByText("Hello")).toBeTruthy();
  });

  it("renders a user row with YOU label", () => {
    seedStore([
      makeMsg({
        id: "u-1",
        role: "user",
        parts: [{ id: "p1", messageId: "u-1", ordinal: 0, kind: "text", text: "My question", sensitive: false }],
      }),
    ]);
    renderPullout();
    expect(screen.getByText("YOU")).toBeTruthy();
    expect(screen.getByText("My question")).toBeTruthy();
  });

  it("renders error row in-flow", () => {
    seedStore([
      makeMsg({
        errorJson: { error: "Provider unreachable" },
        parts: [],
      }),
    ]);
    renderPullout();
    expect(screen.getByText("Provider unreachable")).toBeTruthy();
  });

  it("renders CRASHED + Retry when streaming older than threshold", () => {
    const old = new Date(Date.now() - 20_000).toISOString();
    seedStore([
      makeMsg({
        streaming: true,
        updatedAt: old,
        completedAt: null,
        parts: [],
      }),
    ]);
    renderPullout();
    expect(screen.getByText("CRASHED")).toBeTruthy();
    expect(screen.getByText("Retry")).toBeTruthy();
  });

  it("renders sibling picker with n/m format", () => {
    // Server returns { message_id: [position(1-based), total] }.
    seedStore(
      [
        makeMsg({ id: "msg-a", parentId: "root" }),
      ],
      { "msg-a": ["1", "3"] },
    );
    renderPullout();
    // Should show the sibling count for the message.
    expect(screen.getByText("1/3")).toBeTruthy();
  });

  it("renders receipt short-id for assistant row with receiptId", () => {
    seedStore([makeMsg({ receiptId: "rcpt-12345678abcdef0123456789abcdef" })]);
    renderPullout();
    // Receipt renders as "receipt ····" + last 4 chars.
    expect(screen.getByText(/cdef/)).toBeTruthy();
  });

  it("renders token counts in the head", () => {
    seedStore([makeMsg()]);
    renderPullout();
    expect(screen.getByText(/IN 100/)).toBeTruthy();
  });

  it("done row shows receipt, egress lamp, and model id", () => {
    seedStore([
      makeMsg({
        receiptId: "rcpt-aabbccdd11223344",
        // Server stores boundary name (same_device), not abstract scope (local).
        egressScope: "same_device",
        modelId: "hs151-fake-model",
        parts: [{ id: "p1", messageId: "msg-1", ordinal: 0, kind: "text", text: "Answer", sensitive: false }],
      }),
    ]);
    const { container } = renderPullout();
    // Receipt short-id (last 4 chars) rendered inside receipt span.
    const receiptEl = container.querySelector(".thread-row-receipt");
    expect(receiptEl).toBeTruthy();
    expect(receiptEl!.textContent).toContain("3344");
    // Egress lamp: boundaryEgressLamp("same_device") => "LOCAL".
    const lampEl = container.querySelector(".gadget-lamp");
    expect(lampEl).toBeTruthy();
    expect(lampEl!.textContent).toContain("LOCAL");
    // Model id as the row label.
    expect(screen.getByText("hs151-fake-model")).toBeTruthy();
  });

  it("CRASHED row renders even with zero parts", () => {
    const old = new Date(Date.now() - 30_000).toISOString();
    seedStore([
      makeMsg({
        id: "u-1",
        role: "user",
        parts: [{ id: "p1", messageId: "u-1", ordinal: 0, kind: "text", text: "What crashed?", sensitive: false }],
      }),
      makeMsg({
        id: "asst-1",
        streaming: true,
        updatedAt: old,
        completedAt: null,
        parts: [],
      }),
    ]);
    renderPullout();
    // Both the user row and the crashed assistant row must render.
    expect(screen.getByText("YOU")).toBeTruthy();
    expect(screen.getByText("CRASHED")).toBeTruthy();
    expect(screen.getByText("Retry")).toBeTruthy();
  });

  it("error row shows named reason from errorJson", () => {
    seedStore([
      makeMsg({
        errorJson: { error: "Provider unreachable: fake engine error" },
        parts: [],
        completedAt: new Date().toISOString(),
      }),
    ]);
    renderPullout();
    expect(screen.getByText("Provider unreachable: fake engine error")).toBeTruthy();
  });
});
