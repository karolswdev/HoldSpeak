/** HS-151-06 / HS-153-02 — ThreadComposer tests: keys, chips, verb filter,
 * Send/Stop, mic never sends, two-stage slash completion, R3 line-start rule,
 * completeSlash pure function, verb registry mapping. */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { act, render, screen, fireEvent, waitFor } from "@testing-library/react";
import { clearThreadComposerDraft, useThreadComposerDrafts } from "../threadComposerDrafts";
import {
  ThreadComposer,
  InlineEditor,
  filterSlashCommands,
  completeSlash,
  isSlashAtLineStart,
  THREAD_SLASH_COMMANDS,
  type ThreadComposerProps,
  type SlashCompletionContext,
} from "../components/ThreadComposer";
import {
  filterItems,
  itemToRef,
  directoryToItem,
  type AutocompleteItem,
} from "../components/InletAutocomplete";
import composerCss from "../pullouts/thread-pullout.css?raw";
// ── mock dependencies ──────────────────────────────────────────────

vi.mock("../../lib/api", () => ({
  apiFetch: vi.fn().mockResolvedValue({ relationships: [] }),
}));

vi.mock("../store", () => ({
  useDesk: Object.assign(
    (sel: (s: Record<string, unknown>) => unknown) =>
      sel({
        items: {
          meeting: [{ id: "m1", title: "Standup" }],
          note: [{ id: "n1", title: "Design notes" }],
          artifact: [{ id: "a1", title: "RFC v2" }],
          decision: [{ id: "d1", title: "Use Vite" }],
          directory: [],
          people: [],
          thread: [],
          kb: [],
          recipe: [],
          workflow: [],
          workbench: [],
          chain: [],
          coder: [],
          game: [],
          layout: [],
          project: [],
          roadmap: [],
          story: [],
          repository: [],
          intelligence: [],
        },
      }),
    { getState: () => ({ items: {} }) },
  ),
}));

vi.mock("../tools", () => ({
  KIND_GLYPH: {
    note: "N",
    decision: "D",
    meeting: "M",
    artifact: "A",
    person: "P",
    zone: "Z",
    thread: "T",
  },
  KIND_LABEL: {},
  DESK_TOOLS: [
    { href: "/dictation", label: "Speak", description: "Voice typing.", glyph: "V", action: "dictate", group: "app" },
    { href: "/ask", label: "Ask AI", description: "Ask.", glyph: "A", action: "ask", group: "app" },
  ],
}));

// The mic keeps the real component's `desk-mic` class: it is the transport
// instrument (Signal.tsx's TransportKey duty), not a verb, so the raw-button
// assertion below excludes it by the same class production renders.
vi.mock("../components/MicButton", () => ({
  MicButton: ({ onText }: { onText: (t: string) => void }) => (
    <button className="desk-mic" data-testid="mic-button" onClick={() => onText("hello from mic")}>
      Mic
    </button>
  ),
}));

vi.mock("../surface/Surface", () => ({
  SurfaceRows: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
  SurfaceRow: ({
    title,
    onOpen,
    selected,
  }: {
    title: string;
    onOpen: () => void;
    selected: boolean;
    detail?: string;
    glyph?: React.ReactNode;
    id?: string;
    role?: string;
    ariaSelected?: boolean;
  }) => (
    <div
      data-testid={`surface-row-${title}`}
      data-selected={selected || undefined}
      onClick={onOpen}
    >
      {title}
    </div>
  ),
}));

// ── helpers ────────────────────────────────────────────────────────

beforeEach(() => {
  useThreadComposerDrafts.setState({ drafts: {} });
  // HS-200-41 AC4 — the draft store is sessionStorage-backed; without this a
  // draft written by one test would rehydrate into the next.
  window.sessionStorage.clear();
  Object.defineProperty(HTMLElement.prototype, "scrollIntoView", { configurable: true, value: vi.fn() });
});

const DRAFT_KEY = "hs.threadComposerDrafts";

function renderComposer(overrides: Partial<ThreadComposerProps> = {}) {
  const props: ThreadComposerProps = {
    threadId: "t-1",
    onSend: vi.fn(),
    onStop: vi.fn(),
    onKeep: vi.fn(),
    onFork: vi.fn(),
    onNewThread: vi.fn(),
    streaming: false,
    lastAssistantId: "ast-1",
    ...overrides,
  };
  return { ...render(<ThreadComposer {...props} />), props };
}

// ── unit tests: completeSlash (pure function) ───────────────────────

const CTX: SlashCompletionContext = {
  modes: [
    { id: "hs-seed-mode-desk", name: "Desk" },
    { id: "hs-seed-mode-chase", name: "Chase" },
    { id: "hs-seed-mode-draft", name: "Draft" },
    { id: "hs-seed-mode-plan", name: "Plan" },
  ],
  prompts: [
    { id: "p1", title: "Weekly update", body: "Summarize this week." },
    { id: "p2", title: "1:1 prep", body: "Prepare for 1:1." },
  ],
  guardrails: [
    { id: "g1", title: "Effect guard" },
  ],
};

describe("completeSlash (pure)", () => {
  it("returns command completions for /", () => {
    const result = completeSlash("/", 1, CTX);
    expect(result).not.toBeNull();
    expect(result!.stage).toBe("command");
    expect(result!.items.length).toBe(THREAD_SLASH_COMMANDS.length);
  });

  it("filters commands: /mo -> mode", () => {
    const result = completeSlash("/mo", 3, CTX);
    expect(result).not.toBeNull();
    expect(result!.stage).toBe("command");
    expect(result!.items.map((i) => i.id)).toContain("mode");
    expect(result!.items.map((i) => i.id)).not.toContain("keep");
  });

  it("returns mode arguments for /mode d", () => {
    const result = completeSlash("/mode d", 7, CTX);
    expect(result).not.toBeNull();
    expect(result!.stage).toBe("argument");
    expect(result!.command?.id).toBe("mode");
    const labels = result!.items.map((i) => i.label);
    expect(labels).toContain("Desk");
    expect(labels).toContain("Draft");
    expect(labels).not.toContain("Chase");
    expect(labels).not.toContain("Plan");
  });

  it("returns all modes for /mode (empty arg)", () => {
    const result = completeSlash("/mode ", 6, CTX);
    expect(result).not.toBeNull();
    expect(result!.stage).toBe("argument");
    expect(result!.items.length).toBe(4);
  });

  it("returns prompt arguments for /prompt w", () => {
    const result = completeSlash("/prompt w", 9, CTX);
    expect(result).not.toBeNull();
    expect(result!.stage).toBe("argument");
    expect(result!.command?.id).toBe("prompt");
    const labels = result!.items.map((i) => i.label);
    expect(labels).toContain("Weekly update");
    expect(labels).not.toContain("1:1 prep");
  });

  it("returns prompt arguments for /prompt (empty arg)", () => {
    const result = completeSlash("/prompt ", 8, CTX);
    expect(result).not.toBeNull();
    expect(result!.stage).toBe("argument");
    expect(result!.items.length).toBe(2);
  });

  it("returns null for mid-line /", () => {
    const result = completeSlash("hello /mode", 11, CTX);
    expect(result).toBeNull();
  });

  it("returns completions for / at start of second line", () => {
    const text = "first line\n/mo";
    const result = completeSlash(text, text.length, CTX);
    expect(result).not.toBeNull();
    expect(result!.stage).toBe("command");
    expect(result!.items.map((i) => i.id)).toContain("mode");
  });

  it("returns null for commands without hasArg when followed by space", () => {
    const result = completeSlash("/tools ", 7, CTX);
    expect(result).toBeNull();
  });

  it("returns guardrail arguments for /guardrail e", () => {
    const result = completeSlash("/guardrail e", 12, CTX);
    expect(result).not.toBeNull();
    expect(result!.stage).toBe("argument");
    expect(result!.command?.id).toBe("guardrail");
    expect(result!.items.map((i) => i.label)).toContain("Effect guard");
  });

  it("returns guardrail arguments for /guardrail on e (S2)", () => {
    const result = completeSlash("/guardrail on e", 15, CTX);
    expect(result).not.toBeNull();
    expect(result!.stage).toBe("argument");
    expect(result!.command?.id).toBe("guardrail");
  });

  it("returns guardrail arguments for /guardrail off e (S2)", () => {
    const result = completeSlash("/guardrail off e", 16, CTX);
    expect(result).not.toBeNull();
    expect(result!.stage).toBe("argument");
    expect(result!.command?.id).toBe("guardrail");
  });
});

describe("isSlashAtLineStart", () => {
  it("true for / at start of text", () => {
    expect(isSlashAtLineStart("/mode", 1)).toBe(true);
  });

  it("true for / at start of second line", () => {
    expect(isSlashAtLineStart("hello\n/mode", 7)).toBe(true);
  });

  it("false for mid-line /", () => {
    expect(isSlashAtLineStart("hello /mode", 7)).toBe(false);
  });
});

// ── unit tests: filterSlashCommands (backward compat) ──────────────

describe("filterSlashCommands", () => {
  it("returns all commands for empty query", () => {
    expect(filterSlashCommands("")).toHaveLength(THREAD_SLASH_COMMANDS.length);
  });

  it("filters by id prefix", () => {
    const matches = filterSlashCommands("ke");
    expect(matches).toHaveLength(1);
    expect(matches[0].id).toBe("keep");
  });

  it("filters by label content", () => {
    const matches = filterSlashCommands("note");
    expect(matches).toHaveLength(1);
    expect(matches[0].id).toBe("keep");
  });

  it("returns empty for no match", () => {
    expect(filterSlashCommands("zzz")).toHaveLength(0);
  });
});

// ── verb id well-formedness ─────────────────────────────────────────

describe("slash command verb ids", () => {
  it("every THREAD_SLASH_COMMANDS entry has a non-empty verbId starting with thread.", () => {
    for (const cmd of THREAD_SLASH_COMMANDS) {
      expect(cmd.verbId).toBeTruthy();
      expect(cmd.verbId.startsWith("thread."), `/${cmd.id} verbId should start with thread., got ${cmd.verbId}`).toBe(true);
    }
  });

  it("all verb ids are unique", () => {
    const ids = THREAD_SLASH_COMMANDS.map((c) => c.verbId);
    expect(new Set(ids).size).toBe(ids.length);
  });
});

// ── unit tests: filterItems (generic autocomplete) ──────────────────

describe("filterItems", () => {
  const items: AutocompleteItem[] = [
    { id: "m1", kind: "meeting", name: "Standup", nameNormalized: "standup" },
    { id: "n1", kind: "note", name: "Design notes", nameNormalized: "design notes" },
    { id: "d1", kind: "decision", name: "Use Vite", nameNormalized: "use vite" },
    { id: "p1", kind: "person", name: "Ewa", nameNormalized: "ewa" },
  ];

  it("filters by prefix", () => {
    const matches = filterItems("sta", items);
    expect(matches).toHaveLength(1);
    expect(matches[0].name).toBe("Standup");
  });

  it("empty query returns all (up to 8)", () => {
    expect(filterItems("", items)).toHaveLength(4);
  });

  it("results are sorted alphabetically", () => {
    const matches = filterItems("", items);
    const names = matches.map((m) => m.name);
    expect(names).toEqual([...names].sort());
  });

  it("returns max 8", () => {
    const many = Array.from({ length: 20 }, (_, i) => ({
      id: `x${i}`,
      kind: "note",
      name: `Note ${i}`,
      nameNormalized: `note ${i}`,
    }));
    expect(filterItems("note", many)).toHaveLength(8);
  });
});

// ── unit tests: itemToRef ───────────────────────────────────────────

describe("itemToRef", () => {
  it("builds a ResolvedRef from an AutocompleteItem", () => {
    const ref = itemToRef({
      id: "m1",
      kind: "meeting",
      name: "Standup",
      nameNormalized: "standup",
    });
    expect(ref).toEqual({
      name: "Standup",
      id: "m1",
      ref: "meeting:m1",
      kind: "meeting",
    });
  });
});

// ── unit tests: directoryToItem ─────────────────────────────────────

describe("directoryToItem", () => {
  it("converts Directory to AutocompleteItem", () => {
    const item = directoryToItem({
      kind: "directory",
      id: "dir1",
      name: "Research",
      nameNormalized: "research",
      parentId: null,
      memberIds: ["a", "b"],
      createdAt: "2026-01-01",
    });
    expect(item.kind).toBe("zone");
    expect(item.name).toBe("Research");
    expect(item.detail).toBe("2 items");
  });
});

// ── component tests ─────────────────────────────────────────────────

describe("ThreadComposer", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders textarea, mic, and send button", () => {
    renderComposer();
    expect(screen.getByTestId("composer-input")).toBeInTheDocument();
    expect(screen.getByTestId("mic-button")).toBeInTheDocument();
    expect(screen.getByTestId("composer-send")).toBeInTheDocument();
  });

  it("retains unsent text and references across window remounts, separately for each Thread", () => {
    const first = renderComposer();
    const input = screen.getByTestId("composer-input");
    fireEvent.change(input, { target: { value: "@De" } });
    fireEvent.click(screen.getByTestId("surface-row-Design notes"));
    fireEvent.change(input, { target: { value: "My draft before changing rooms" } });
    first.unmount();
    const other = renderComposer({ threadId: "t-2" });
    expect(screen.getByTestId("composer-input")).toHaveValue("");
    expect(screen.queryByTestId("ref-chip-note")).not.toBeInTheDocument();
    other.unmount();
    renderComposer();
    expect(screen.getByTestId("composer-input")).toHaveValue("My draft before changing rooms");
    expect(screen.getByTestId("ref-chip-note")).toHaveTextContent("Design notes");
  });

  it.each([true, false])("settles an in-flight send after the window remounts: accepted=%s", async (accepted) => {
    let finish!: (accepted: boolean) => void;
    const onSend = vi.fn(() => new Promise<boolean>((resolve) => { finish = resolve; }));
    const first = renderComposer({ onSend });
    fireEvent.change(screen.getByTestId("composer-input"), { target: { value: "Keep this across rooms" } });
    fireEvent.click(screen.getByTestId("composer-send"));
    first.unmount();
    renderComposer({ onSend });
    expect(screen.getByTestId("composer-input")).toHaveValue("Keep this across rooms");
    expect(screen.getByTestId("composer-send")).toBeDisabled();
    expect(onSend).toHaveBeenCalledOnce();
    await act(async () => finish(accepted));
    expect(screen.getByTestId("composer-input")).toHaveValue(accepted ? "" : "Keep this across rooms");
    expect(screen.getByTestId("composer-input")).not.toBeDisabled();
  });

  // ── HS-200-41 AC4: the draft survives a reload and a crash restore ──

  it("writes the draft to sessionStorage, and to no durable disk store", () => {
    const durableWrite = vi.spyOn(window.localStorage, "setItem");
    renderComposer();
    const input = screen.getByTestId("composer-input");
    fireEvent.change(input, { target: { value: "@De" } });
    fireEvent.click(screen.getByTestId("surface-row-Design notes"));
    fireEvent.change(input, { target: { value: "Half-written question" } });

    const stored = JSON.parse(window.sessionStorage.getItem(DRAFT_KEY) as string);
    expect(stored["t-1"].text).toBe("Half-written question");
    expect(stored["t-1"].chips).toEqual([
      { ref: { name: "Design notes", id: "n1", ref: "note:n1", kind: "note" } },
    ]);
    expect(
      durableWrite.mock.calls.filter(([key]) => String(key).includes("threadComposerDraft")),
    ).toEqual([]);
    expect(window.localStorage.getItem(DRAFT_KEY)).toBeNull();
    durableWrite.mockRestore();
  });

  it("erases the stored draft once the hub accepts the message", async () => {
    let finish!: (accepted: boolean) => void;
    renderComposer({ onSend: vi.fn(() => new Promise<boolean>((resolve) => { finish = resolve; })) });
    const input = screen.getByTestId("composer-input");
    fireEvent.change(input, { target: { value: "Sent and gone" } });
    fireEvent.keyDown(input, { key: "Enter" });
    // An in-flight send is browser state, never custody: it is not persisted.
    expect(JSON.parse(window.sessionStorage.getItem(DRAFT_KEY) as string)["t-1"]).toEqual({
      text: "Sent and gone",
      chips: [],
      sending: false,
    });
    await act(async () => finish(true));
    expect(window.sessionStorage.getItem(DRAFT_KEY)).toBeNull();
  });

  it("clears the stored draft when the Thread closes", () => {
    renderComposer();
    fireEvent.change(screen.getByTestId("composer-input"), { target: { value: "Gone with the window" } });
    expect(window.sessionStorage.getItem(DRAFT_KEY)).toContain("Gone with the window");
    // threads.ts removeThread() calls this eraser when a Thread closes.
    act(() => clearThreadComposerDraft("t-1"));
    expect(window.sessionStorage.getItem(DRAFT_KEY)).toBeNull();
  });

  it("restores an unsent draft after a reload, carrying no stale sending state", async () => {
    const chip = { ref: { name: "Design notes", id: "n1", ref: "note:n1", kind: "note" } };
    // The crash-restore shape: the tab died mid-send, so `sending` was true.
    window.sessionStorage.setItem(
      DRAFT_KEY,
      JSON.stringify({ "t-1": { text: "Half-written question", chips: [chip], sending: true } }),
    );
    vi.resetModules();
    const reloaded = await import("../threadComposerDrafts");
    const restored = reloaded.useThreadComposerDrafts.getState().drafts;
    expect(restored["t-1"]).toEqual({ text: "Half-written question", chips: [chip], sending: false });

    useThreadComposerDrafts.setState({ drafts: restored });
    renderComposer();
    expect(screen.getByTestId("composer-input")).toHaveValue("Half-written question");
    expect(screen.getByTestId("composer-input")).not.toBeDisabled();
    expect(screen.getByTestId("composer-send")).not.toBeDisabled();
    expect(screen.getByTestId("ref-chip-note")).toHaveTextContent("Design notes");
  });

  it("drops unreadable stored drafts instead of failing the reload", async () => {
    window.sessionStorage.setItem(DRAFT_KEY, "{not json");
    vi.resetModules();
    const reloaded = await import("../threadComposerDrafts");
    expect(reloaded.useThreadComposerDrafts.getState().drafts).toEqual({});
  });

  it("still types when the browser refuses storage", async () => {
    const read = vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new DOMException("SecurityError");
    });
    const write = vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new DOMException("QuotaExceededError");
    });
    try {
      vi.resetModules();
      const reloaded = await import("../threadComposerDrafts");
      expect(reloaded.useThreadComposerDrafts.getState().drafts).toEqual({});

      renderComposer();
      const input = screen.getByTestId("composer-input");
      fireEvent.change(input, { target: { value: "Typed with storage refused" } });
      expect(input).toHaveValue("Typed with storage refused");
      expect(screen.getByTestId("composer-send")).not.toBeDisabled();
    } finally {
      read.mockRestore();
      write.mockRestore();
    }
  });

  // ── HS-200-41 AC5: every verb is the library Button ─────────────────

  it.each([false, true])("draws every verb as the library Button: streaming=%s", (streaming) => {
    renderComposer({ streaming });
    const input = screen.getByTestId("composer-input");
    fireEvent.change(input, { target: { value: "@De" } });
    fireEvent.click(screen.getByTestId("surface-row-Design notes"));
    fireEvent.change(input, { target: { value: "A question with an attachment" } });
    expect(screen.getByTestId(streaming ? "composer-stop" : "composer-send")).toHaveClass("btn");

    const composer = screen.getByTestId("thread-composer");
    // The mic is the transport instrument, not a verb; every other button in
    // the composer must carry the library's `btn` face.
    const raw = Array.from(composer.querySelectorAll("button")).filter(
      (el) => !el.classList.contains("btn") && !el.classList.contains("desk-mic"),
    );
    expect(raw.map((el) => el.outerHTML)).toEqual([]);
  });

  it("draws a refused Send as disabled, not merely marks it disabled", () => {
    renderComposer();
    const send = screen.getByTestId("composer-send");
    expect(send).toBeDisabled();
    // D-R1 — Send keeps the chip face; the swap is canon, not appearance.
    expect(send).toHaveClass("btn", "desk-chip");

    // D-R2 — jsdom applies no stylesheet, so the face is proved against the
    // sheet that owns this surface (the editorFootGrip.test.ts precedent).
    // `.desk-next .desk-chip` (chrome-menus.css) has no disabled rule and
    // outranks the library's, so without this the refused verb looks live.
    const rule = composerCss.slice(composerCss.indexOf(".thread-composer-row .desk-chip:disabled"));
    const selectors = rule.split("{")[0] ?? "";
    const block = rule.split("{")[1]?.split("}")[0] ?? "";
    // The chip's own :hover outranks a bare :disabled rule, so the refused
    // verb must stay refused under the pointer too.
    expect(selectors).toContain(".thread-composer-row .desk-chip:disabled:hover");
    expect(selectors).toContain(".thread-inline-editor-actions .desk-chip:disabled");
    expect(block).toContain("var(--disabled-bg)");
    expect(block).toContain("var(--disabled-fg)");
    expect(block).toContain("var(--disabled-border)");
  });

  it("keeps the library's hover and press grammar off the ref-chip remove verb", () => {
    // D-R3 — the swap must not add a hover background or a press settle the
    // chip never had; the focus ring `all: unset` had killed does stay.
    const hover = composerCss
      .split(".thread-ref-chip .thread-ref-chip-remove:hover")[1]
      ?.split("}")[0] ?? "";
    expect(hover).toContain("background: none");
    const press = composerCss
      .split(".thread-ref-chip .thread-ref-chip-remove:active:not(:disabled)")[1]
      ?.split("}")[0] ?? "";
    expect(press).toContain("transform: none");
    expect(composerCss).not.toContain(".thread-ref-chip-remove:focus-visible");
  });

  it("Enter sends the message", () => {
    const { props } = renderComposer();
    const input = screen.getByTestId("composer-input") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "hello world" } });
    fireEvent.keyDown(input, { key: "Enter", shiftKey: false });
    expect(props.onSend).toHaveBeenCalledWith("hello world", []);
  });

  it("keeps the draft until the hub accepts it and blocks duplicate sends", async () => {
    let finish!: (accepted: boolean) => void;
    renderComposer({ onSend: vi.fn(() => new Promise<boolean>((resolve) => { finish = resolve; })) });
    const input = screen.getByTestId("composer-input");
    fireEvent.change(input, { target: { value: "Remember my exact words" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(input).toHaveValue("Remember my exact words");
    expect(screen.getByTestId("composer-send")).toBeDisabled();
    await act(async () => finish(true));
    expect(input).toHaveValue("");
  });

  it.each([false, new Error("Connection lost")])("preserves the draft after an unconfirmed send: %s", async (failure) => {
    renderComposer({ onSend: vi.fn(async () => { if (failure instanceof Error) throw failure; return failure; }) });
    const input = screen.getByTestId("composer-input");
    fireEvent.change(input, { target: { value: "Do not lose this prompt" } });
    fireEvent.keyDown(input, { key: "Enter" });
    await waitFor(() => expect(screen.getByTestId("composer-send")).not.toBeDisabled());
    expect(input).toHaveValue("Do not lose this prompt");
  });

  it("Shift+Enter does NOT send (inserts newline)", () => {
    const { props } = renderComposer();
    const input = screen.getByTestId("composer-input") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "hello" } });
    fireEvent.keyDown(input, { key: "Enter", shiftKey: true });
    expect(props.onSend).not.toHaveBeenCalled();
  });

  it("Esc during streaming calls onStop", () => {
    const { props } = renderComposer({ streaming: true });
    const input = screen.getByTestId("composer-input") as HTMLTextAreaElement;
    fireEvent.keyDown(input, { key: "Escape" });
    expect(props.onStop).toHaveBeenCalled();
  });

  it("shows Stop button when streaming", () => {
    renderComposer({ streaming: true });
    expect(screen.getByTestId("composer-stop")).toBeInTheDocument();
    expect(screen.queryByTestId("composer-send")).not.toBeInTheDocument();
  });

  it("shows Send button when not streaming", () => {
    renderComposer({ streaming: false });
    expect(screen.getByTestId("composer-send")).toBeInTheDocument();
    expect(screen.queryByTestId("composer-stop")).not.toBeInTheDocument();
  });

  it("mic text lands in the field but NEVER sends", () => {
    const { props } = renderComposer();
    const mic = screen.getByTestId("mic-button");
    fireEvent.click(mic);
    // Mic text should be in the textarea
    const input = screen.getByTestId("composer-input") as HTMLTextAreaElement;
    expect(input.value).toBe("hello from mic");
    // But onSend should NOT have been called
    expect(props.onSend).not.toHaveBeenCalled();
  });

  it("empty draft disables Send", () => {
    renderComposer();
    const send = screen.getByTestId("composer-send");
    expect(send).toBeDisabled();
  });

  it("non-empty draft enables Send", () => {
    renderComposer();
    const input = screen.getByTestId("composer-input") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "msg" } });
    const send = screen.getByTestId("composer-send");
    expect(send).not.toBeDisabled();
  });

  it("Enter with streaming calls onStop, not onSend", () => {
    const { props } = renderComposer({ streaming: true });
    const input = screen.getByTestId("composer-input") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "hello" } });
    fireEvent.keyDown(input, { key: "Enter", shiftKey: false });
    expect(props.onStop).toHaveBeenCalled();
    expect(props.onSend).not.toHaveBeenCalled();
  });
});

// ── InlineEditor tests ──────────────────────────────────────────────

describe("InlineEditor", () => {
  it("renders with initial text", () => {
    render(
      <InlineEditor
        initialText="original"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    const input = screen.getByTestId("inline-editor-input") as HTMLTextAreaElement;
    expect(input.value).toBe("original");
  });

  it("Enter confirms with the edited text", () => {
    const onConfirm = vi.fn();
    render(
      <InlineEditor
        initialText="original"
        onConfirm={onConfirm}
        onCancel={vi.fn()}
      />,
    );
    const input = screen.getByTestId("inline-editor-input") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "edited" } });
    fireEvent.keyDown(input, { key: "Enter", shiftKey: false });
    expect(onConfirm).toHaveBeenCalledWith("edited");
  });

  it("Escape cancels without confirming", () => {
    const onCancel = vi.fn();
    const onConfirm = vi.fn();
    render(
      <InlineEditor
        initialText="original"
        onConfirm={onConfirm}
        onCancel={onCancel}
      />,
    );
    const input = screen.getByTestId("inline-editor-input") as HTMLTextAreaElement;
    fireEvent.keyDown(input, { key: "Escape" });
    expect(onCancel).toHaveBeenCalled();
    expect(onConfirm).not.toHaveBeenCalled();
  });

  // HS-200-41 AC5 — Send and Cancel are the library Button, not raw markup.
  it("draws every verb as the library Button", () => {
    render(
      <InlineEditor initialText="original" onConfirm={vi.fn()} onCancel={vi.fn()} />,
    );
    const editor = screen.getByTestId("inline-editor");
    const raw = Array.from(editor.querySelectorAll("button")).filter(
      (el) => !el.classList.contains("btn") && !el.classList.contains("desk-mic"),
    );
    expect(raw.map((el) => el.outerHTML)).toEqual([]);
    // D-R1 — the swap is canon only: both verbs keep the chip face they had.
    expect(screen.getByText("Send")).toHaveClass("desk-chip");
    expect(screen.getByText("Cancel")).toHaveClass("desk-chip", "quiet");
  });
});

// ── slash command verb filter integration ───────────────────────────

describe("slash command palette via composer", () => {
  it("typing / shows slash palette", () => {
    renderComposer();
    const input = screen.getByTestId("composer-input") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "/" } });
    expect(screen.getByTestId("slash-palette")).toBeInTheDocument();
  });

  it("typing /ke filters to keep", () => {
    renderComposer();
    const input = screen.getByTestId("composer-input") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "/ke" } });
    // Should show the keep command
    expect(screen.getByTestId("surface-row-/keep")).toBeInTheDocument();
    expect(screen.queryByTestId("surface-row-/fork")).not.toBeInTheDocument();
  });

  it("/stop runs onStop", () => {
    const { props } = renderComposer();
    const input = screen.getByTestId("composer-input") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "/stop" } });
    // Select via Enter
    fireEvent.keyDown(input, { key: "Enter" });
    expect(props.onStop).toHaveBeenCalled();
  });

  it("/new runs onNewThread", () => {
    const { props } = renderComposer();
    const input = screen.getByTestId("composer-input") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "/new" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(props.onNewThread).toHaveBeenCalled();
  });

  it("mid-line / does NOT open slash palette", () => {
    renderComposer();
    const input = screen.getByTestId("composer-input") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "hello /mode" } });
    expect(screen.queryByTestId("slash-palette")).not.toBeInTheDocument();
  });

  it("Esc closes slash palette", () => {
    renderComposer();
    const input = screen.getByTestId("composer-input") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "/" } });
    expect(screen.getByTestId("slash-palette")).toBeInTheDocument();
    fireEvent.keyDown(input, { key: "Escape" });
    expect(screen.queryByTestId("slash-palette")).not.toBeInTheDocument();
  });

  it("/tools shows system row about palette", () => {
    renderComposer({ currentMode: { id: "m1", name: "Chase" } });
    const input = screen.getByTestId("composer-input") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "/tools" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(screen.getByTestId("thread-system-row")).toBeInTheDocument();
    expect(screen.getByTestId("thread-system-row").textContent).toContain("Chase");
  });

  it("/compact fires the compact API and shows system row", () => {
    renderComposer();
    const input = screen.getByTestId("composer-input") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "/compact" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(screen.getByTestId("thread-system-row")).toBeInTheDocument();
    expect(screen.getByTestId("thread-system-row").textContent).toContain("Compacting");
  });

});
