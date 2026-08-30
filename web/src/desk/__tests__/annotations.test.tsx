/** HS-153-04 -- Annotation popover + chips vitest.
 * Tests: chips render, remove button, selectionchange opens popover,
 * selection inside textarea does not open popover, MicButton present. */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import { useThreadStore, type ThreadMessage, type ThreadDetail, type DraftAnnotation } from "../threads";
import { ThreadPullout } from "../pullouts/ThreadPullout";
import { RuntimeBusProvider } from "../../runtime/RuntimeBus";

// Mock api
vi.mock("../../lib/api", () => ({
  apiFetch: vi.fn().mockResolvedValue({ relationships: [] }),
}));

// Mock MicButton
vi.mock("../components/MicButton", () => ({
  MicButton: ({ onText }: { onText: (t: string) => void }) => (
    <button data-testid="mic-button" onClick={() => onText("voice text")}>
      Mic
    </button>
  ),
}));

// Mock ModeTabs
vi.mock("../components/ModeTabs", () => ({
  ModeTabs: () => <div data-testid="mode-tabs">Modes</div>,
}));

// Mock store
vi.mock("../store", () => ({
  useDesk: Object.assign(
    (sel: (s: Record<string, unknown>) => unknown) =>
      sel({
        items: {
          meeting: [], note: [], artifact: [], decision: [], directory: [],
          people: [], thread: [], kb: [], recipe: [], workflow: [],
          workbench: [], chain: [], coder: [], game: [], layout: [],
          project: [], roadmap: [], story: [], repository: [], intelligence: [],
        },
        openPullout: () => {},
        refresh: () => Promise.resolve(),
      }),
    {
      getState: () => ({
        items: {},
        openPullout: () => {},
        refresh: () => Promise.resolve(),
      }),
    },
  ),
}));

// Stub WebSocket
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
    parts: [{ id: "p1", messageId: "msg-1", ordinal: 0, kind: "text", text: "Hello world from the assistant", sensitive: false }],
    ...overrides,
  };
}

function seedStore(messages: ThreadMessage[], drafts: DraftAnnotation[] = []) {
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
      token_in: 100,
      token_out: 50,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      last_turn_at: null,
    },
    messages,
    siblings: {},
    refs: [],
    draftAnnotations: drafts,
  };
  useThreadStore.setState({
    threads: { "t-1": detail },
    buffers: {},
    loading: {},
    draftAnnotations: { "t-1": drafts },
  });
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

describe("Annotation chips", () => {
  it("renders chips when draft annotations exist", () => {
    seedStore([makeMsg()], [
      {
        id: "ann-1",
        kind: "annotation",
        text: "The owner annotated: hello -- comment",
        ordinal: 0,
        sensitive: false,
        meta_json: { source: "owner", quote: "hello from the asst", comment: "my comment", anchor_message_id: "msg-1" },
      },
    ]);
    renderPullout();
    const chips = screen.getByTestId("annotation-chips");
    expect(chips).toBeTruthy();
    const chip = screen.getByTestId("annotation-chip");
    expect(chip).toBeTruthy();
  });

  it("renders no chips when no annotations", () => {
    seedStore([makeMsg()]);
    renderPullout();
    expect(screen.queryByTestId("annotation-chips")).toBeNull();
  });

  it("remove button present on chip", () => {
    seedStore([makeMsg()], [
      {
        id: "ann-1",
        kind: "annotation",
        text: "note",
        ordinal: 0,
        sensitive: false,
        meta_json: { source: "owner", quote: "quoted", comment: "c", anchor_message_id: "msg-1" },
      },
    ]);
    renderPullout();
    const removeBtn = screen.getByTestId("annotation-chip-remove");
    expect(removeBtn).toBeTruthy();
  });
});

describe("Annotation popover via selectionchange", () => {
  it("opens when selectionchange fires with a non-collapsed range inside an assistant text part", async () => {
    seedStore([makeMsg()]);
    const { container } = renderPullout();

    // Wait for the assistant row to render.
    const asstBody = container.querySelector(".thread-row-assistant .thread-row-body");
    expect(asstBody).toBeTruthy();

    // Find the message row element for closest() to work.
    const msgRow = container.querySelector("[data-message-id='msg-1']");
    expect(msgRow).toBeTruthy();

    // Create a mock text node inside the assistant body.
    // jsdom does not support real Range/Selection, so we mock getSelection.
    const textEl = asstBody!.querySelector(".surface-material") ?? asstBody!;

    const fakeRange = {
      commonAncestorContainer: textEl,
      getBoundingClientRect: () => ({ top: 100, left: 50, width: 80, bottom: 116, right: 130, height: 16, x: 50, y: 100, toJSON: () => ({}) }),
      cloneRange: () => fakeRange,
      collapse: () => {},
      setStart: () => {},
      setEnd: () => {},
    };

    const origGetSelection = window.getSelection;
    const fakeSelection = {
      isCollapsed: false,
      toString: () => "Hello world",
      getRangeAt: () => fakeRange,
      rangeCount: 1,
      removeAllRanges: () => {},
      addRange: () => {},
    };
    vi.stubGlobal("getSelection", () => fakeSelection);

    // Dispatch selectionchange (the component listens on document).
    await act(async () => {
      document.dispatchEvent(new Event("selectionchange"));
      // The handler debounces at 80ms.
      await new Promise((r) => setTimeout(r, 150));
    });

    // The popover should be visible.
    const popover = screen.queryByTestId("annotation-popover");
    expect(popover).toBeTruthy();
    expect(popover!.textContent).toContain("Hello world");

    // MicButton should be present inside the popover.
    const mic = popover!.querySelector("[data-testid='mic-button']");
    expect(mic).toBeTruthy();

    // Restore
    vi.stubGlobal("getSelection", origGetSelection);
  });

  it("does not open when active element is a textarea", async () => {
    seedStore([makeMsg()]);
    const { container } = renderPullout();

    const asstBody = container.querySelector(".thread-row-assistant .thread-row-body");
    expect(asstBody).toBeTruthy();
    const textEl = asstBody!.querySelector(".surface-material") ?? asstBody!;

    const fakeRange = {
      commonAncestorContainer: textEl,
      getBoundingClientRect: () => ({ top: 100, left: 50, width: 80, bottom: 116, right: 130, height: 16, x: 50, y: 100, toJSON: () => ({}) }),
      cloneRange: () => fakeRange,
      collapse: () => {},
      setStart: () => {},
      setEnd: () => {},
    };

    const origGetSelection = window.getSelection;
    vi.stubGlobal("getSelection", () => ({
      isCollapsed: false,
      toString: () => "Some text",
      getRangeAt: () => fakeRange,
      rangeCount: 1,
      removeAllRanges: () => {},
      addRange: () => {},
    }));

    // Focus a textarea so activeElement is a TEXTAREA.
    const textarea = container.querySelector("textarea");
    if (textarea) {
      textarea.focus();
    } else {
      // Create a temporary textarea and focus it.
      const tmp = document.createElement("textarea");
      document.body.appendChild(tmp);
      tmp.focus();
    }

    await act(async () => {
      document.dispatchEvent(new Event("selectionchange"));
      await new Promise((r) => setTimeout(r, 150));
    });

    // The popover should NOT appear.
    const popover = screen.queryByTestId("annotation-popover");
    expect(popover).toBeNull();

    // Clean up.
    vi.stubGlobal("getSelection", origGetSelection);
    const tmp = document.querySelector("textarea:not([data-testid])");
    if (tmp && !tmp.closest("[data-testid]")) tmp.remove();
  });
});
