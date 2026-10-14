/** HS-151-05 — ThreadPullout rendering tests: rows render streaming, done,
 * error, crashed+Retry, sibling picker. */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import * as threads from "../threads";
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
afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
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
      mode: null,
      call_mode: 0,
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

describe("ThreadPullout title", () => {
  beforeEach(() => {
    seedStore([]);
    vi.spyOn(useThreadStore.getState(), "loadThread").mockResolvedValue(undefined);
  });

  it("names the thread only in its window and keeps a library Rename action", () => {
    const detail = useThreadStore.getState().threads["t-1"];
    detail.thread.mode = { id: "hs-seed-mode-desk", name: "Desk", avatar: "#666" };
    const { container } = renderPullout();
    expect(screen.queryByText("Test Thread")).toBeNull();
    expect(screen.getByRole("button", { name: "Rename thread" }).classList.contains("btn")).toBe(true);
    expect(container.querySelector(".thread-mode-badge")).toBeNull();
  });

  it("opens the current title and mic; Escape restores Rename focus without a write", async () => {
    const patch = vi.spyOn(threads, "patchThread");
    renderPullout();
    fireEvent.click(screen.getByRole("button", { name: "Rename thread" }));
    const input = screen.getByRole("textbox", { name: "Thread title" });
    expect((input as HTMLInputElement).value).toBe("Test Thread");
    expect(document.activeElement).toBe(input);
    expect(screen.getByRole("button", { name: /^Speak thread title/ })).toBeTruthy();
    fireEvent.change(input, { target: { value: "Discard this" } });
    fireEvent.keyDown(input, { key: "Escape" });
    await waitFor(() => expect(document.activeElement).toBe(screen.getByRole("button", { name: "Rename thread" })));
    expect(patch).not.toHaveBeenCalled();
  });

  it("Enter commits the title and restores Rename focus", async () => {
    const patch = vi.spyOn(threads, "patchThread").mockResolvedValue(useThreadStore.getState().threads["t-1"].thread);
    renderPullout();
    fireEvent.click(screen.getByRole("button", { name: "Rename thread" }));
    const input = screen.getByRole("textbox", { name: "Thread title" });
    fireEvent.change(input, { target: { value: "Architecture review" } });
    fireEvent.keyDown(input, { key: "Enter" });
    await waitFor(() => expect(patch).toHaveBeenCalledExactlyOnceWith("t-1", { title: "Architecture review" }));
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Rename thread" }));
  });
});

describe("ThreadPullout rows", () => {
  it("renders a done assistant row with text through Material", () => {
    seedStore([makeMsg()]);
    renderPullout();
    expect(screen.getByText("Hello")).toBeTruthy();
  });

  it.each(["", " late suffix"])("keeps saved streaming text when live buffer is incomplete: %s", (text) => {
    seedStore([makeMsg({ streaming: true, completedAt: null })]);
    if (text) useThreadStore.setState({ buffers: {
      "msg-1": { messageId: "msg-1", highSeq: 4, parts: new Map([[0, { kind: "text", text }]]) },
    } });
    renderPullout();
    expect(screen.getByText("Hello")).toBeTruthy();
  });

  it("shows live text that extends the saved answer", () => {
    seedStore([makeMsg({ streaming: true, completedAt: null })]);
    useThreadStore.setState({ buffers: {
      "msg-1": { messageId: "msg-1", highSeq: 4, parts: new Map([[0, { kind: "text", text: "Hello from the live answer" }]]) },
    } });
    renderPullout();
    expect(screen.getByText("Hello from the live answer")).toBeTruthy();
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

  it("renders the last turn's receipt short-id in the footer", () => {
    // Owner pick 2026-10-05 (route in footer): the receipt rides the
    // footer's last-turn route, not the row.
    seedStore([makeMsg({ receiptId: "rcpt-12345678abcdef0123456789abcdef", egressReceiptId: "rcpt-12345678abcdef0123456789abcdef", egressScope: "local" })]);
    const { container } = renderPullout();
    expect(container.querySelector(".thread-route-footer")!.textContent).toContain("RECEIPT ··cdef");
    expect(container.querySelector(".thread-row-receipt")).toBeNull();
  });

  it("renders token counts in the head", () => {
    seedStore([makeMsg()]);
    renderPullout();
    expect(screen.getByText(/IN 100/)).toBeTruthy();
  });

  it("done row shows its egress lamp; the footer shows receipt and model", () => {
    seedStore([
      makeMsg({
        receiptId: "rcpt-aabbccdd11223344",
        egressReceiptId: "rcpt-aabbccdd11223344",
        // Server stores boundary name (same_device), not abstract scope (local).
        egressScope: "same_device",
        modelId: "hs151-fake-model",
        parts: [{ id: "p1", messageId: "msg-1", ordinal: 0, kind: "text", text: "Answer", sensitive: false }],
      }),
    ]);
    const { container } = renderPullout();
    // Egress lamp on the row: boundaryEgressLamp("same_device") => "LOCAL".
    const lampEl = container.querySelector(".thread-row-head .gadget-lamp");
    expect(lampEl).toBeTruthy();
    expect(lampEl!.textContent).toContain("LOCAL");
    // The row is ASSISTANT; the model and the receipt ride the footer once.
    expect(container.querySelector(".thread-row-label")!.textContent).toBe("ASSISTANT");
    expect(container.querySelector(".thread-route-footer")!.textContent).toContain(
      "LAST TURN · hs151-fake-model · RECEIPT ··3344",
    );
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

  it("hydrates a persisted deny as primary and focused", () => {
    seedStore([
      makeMsg({
        id: "asst-guardrail",
        parts: [{
          id: "p-tool-call",
          messageId: "asst-guardrail",
          ordinal: 0,
          kind: "tool_call",
          text: "",
          sensitive: false,
          metaJson: {
            id: "call-guardrail",
            name: "people.commitment.transition",
            arguments: "{}",
            class: "effect_proposal",
            state: "awaiting_decision",
            default_decision: "deny",
          },
        }],
      }),
    ]);
    useThreadStore.getState().hydrateToolRows("t-1");

    renderPullout();

    const deny = screen.getByTestId("deny");
    expect(screen.getByTestId("decision-box")).toHaveAttribute("data-default-decision", "deny");
    expect(deny.classList.contains("btn--primary")).toBe(true);
    expect(deny).toHaveFocus();
  });
});
