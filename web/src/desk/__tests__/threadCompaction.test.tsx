/** HS-153-05 — Compaction cut marker, fold, compact_failed row, and Door card thread chip. */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { useThreadStore, type ThreadMessage, type ThreadDetail } from "../threads";
import { ThreadPullout } from "../pullouts/ThreadPullout";
import { RuntimeBusProvider } from "../../runtime/RuntimeBus";

// Mock WebSocket so RuntimeBusProvider does not connect.
beforeEach(() => {
  vi.stubGlobal("WebSocket", class {
    addEventListener() {}
    removeEventListener() {}
    close() {}
    send() {}
    readyState = 3;
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

describe("compaction cut marker", () => {
  it("renders the cut marker for a compaction system message", () => {
    seedStore([
      makeMsg({ id: "u1", role: "user", parts: [{ id: "pu1", messageId: "u1", ordinal: 0, kind: "text", text: "hi", sensitive: false }] }),
      makeMsg({ id: "a1", role: "assistant", parts: [{ id: "pa1", messageId: "a1", ordinal: 0, kind: "text", text: "hello", sensitive: false }] }),
      makeMsg({
        id: "cut1",
        role: "system",
        statsJson: { compaction: true, cut_at: "u1", count: 2 },
        parts: [{ id: "pcut1", messageId: "cut1", ordinal: 0, kind: "text", text: "Summary of earlier messages", sensitive: false }],
      }),
      makeMsg({ id: "u2", role: "user", parts: [{ id: "pu2", messageId: "u2", ordinal: 0, kind: "text", text: "next", sensitive: false }] }),
    ]);
    renderPullout();
    const marker = screen.getByTestId("compact-cut-marker");
    expect(marker).toBeTruthy();
    expect(marker.textContent).toContain("compacted");
    expect(marker.textContent).toContain("2 messages");
  });

  it("folds messages before the cut behind a toggle", () => {
    seedStore([
      makeMsg({ id: "u1", role: "user", parts: [{ id: "pu1", messageId: "u1", ordinal: 0, kind: "text", text: "early question", sensitive: false }] }),
      makeMsg({ id: "a1", role: "assistant", parts: [{ id: "pa1", messageId: "a1", ordinal: 0, kind: "text", text: "early answer", sensitive: false }] }),
      makeMsg({
        id: "cut1",
        role: "system",
        statsJson: { compaction: true, cut_at: "u1", count: 2 },
        parts: [{ id: "pcut1", messageId: "cut1", ordinal: 0, kind: "text", text: "Summary", sensitive: false }],
      }),
      makeMsg({ id: "u2", role: "user", parts: [{ id: "pu2", messageId: "u2", ordinal: 0, kind: "text", text: "after cut", sensitive: false }] }),
    ]);
    renderPullout();

    const fold = screen.getByTestId("earlier-messages-fold");
    expect(fold).toBeTruthy();
    // The toggle should say "2 earlier messages"
    const toggle = fold.querySelector(".thread-earlier-toggle")!;
    expect(toggle.textContent).toContain("2 earlier");

    // Earlier messages not visible initially
    expect(screen.queryByText("early question")).toBeNull();

    // Click to expand
    fireEvent.click(toggle);
    expect(screen.getByText("early question")).toBeTruthy();
    expect(screen.getByText("early answer")).toBeTruthy();
  });

  it("does not render fold when no compaction row exists", () => {
    seedStore([
      makeMsg({ id: "u1", role: "user", parts: [{ id: "pu1", messageId: "u1", ordinal: 0, kind: "text", text: "hi", sensitive: false }] }),
      makeMsg({ id: "a1", role: "assistant", parts: [{ id: "pa1", messageId: "a1", ordinal: 0, kind: "text", text: "hello", sensitive: false }] }),
    ]);
    renderPullout();
    expect(screen.queryByTestId("earlier-messages-fold")).toBeNull();
    expect(screen.queryByTestId("compact-cut-marker")).toBeNull();
  });

  it("shows RAW fold with the summary text", () => {
    seedStore([
      makeMsg({
        id: "cut1",
        role: "system",
        statsJson: { compaction: true, cut_at: "u1", count: 3 },
        parts: [{ id: "pcut1", messageId: "cut1", ordinal: 0, kind: "text", text: "The user asked about X and I replied with Y", sensitive: false }],
      }),
    ]);
    renderPullout();
    const marker = screen.getByTestId("compact-cut-marker");
    const rawToggle = marker.querySelector(".thread-raw-toggle");
    expect(rawToggle).toBeTruthy();
    expect(rawToggle!.textContent).toContain("RAW");
    // The summary text is inside a <pre> inside a <details>
    const pre = marker.querySelector(".thread-raw-content");
    expect(pre).toBeTruthy();
    expect(pre!.textContent).toContain("The user asked about X");
  });
});

describe("compact_failed row", () => {
  it("renders a compact_failed warning row", () => {
    seedStore([
      makeMsg({ id: "u1", role: "user", parts: [{ id: "pu1", messageId: "u1", ordinal: 0, kind: "text", text: "hi", sensitive: false }] }),
      makeMsg({
        id: "fail1",
        role: "system",
        statsJson: { compact_failed: true },
        parts: [{ id: "pfail1", messageId: "fail1", ordinal: 0, kind: "text", text: "Engine timeout", sensitive: false }],
      }),
    ]);
    renderPullout();
    const failRow = screen.getByTestId("compact-failed-row");
    expect(failRow).toBeTruthy();
    expect(failRow.textContent).toContain("compact failed");
    expect(failRow.textContent).toContain("Engine timeout");
  });
});

// Door card thread provenance chip is tested in DoorBoardLane.test.tsx
// alongside the existing HS-146-04 provenance chip tests — see the
// "thread provenance chip" describe block added below.
