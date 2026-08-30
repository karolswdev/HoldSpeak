/** HS-151-06 / HS-153-02 — ThreadComposer tests: keys, chips, verb filter,
 * Send/Stop, mic never sends, two-stage slash completion, R3 line-start rule,
 * completeSlash pure function, verb registry mapping. */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
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

vi.mock("../components/MicButton", () => ({
  MicButton: ({ onText }: { onText: (t: string) => void }) => (
    <button data-testid="mic-button" onClick={() => onText("hello from mic")}>
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

function renderComposer(overrides: Partial<ThreadComposerProps> = {}) {
  const props: ThreadComposerProps = {
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

  it("Enter sends the message", () => {
    const { props } = renderComposer();
    const input = screen.getByTestId("composer-input") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "hello world" } });
    fireEvent.keyDown(input, { key: "Enter", shiftKey: false });
    expect(props.onSend).toHaveBeenCalledWith("hello world", []);
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

  it("/compact shows not-yet system row", () => {
    renderComposer();
    const input = screen.getByTestId("composer-input") as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "/compact" } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(screen.getByTestId("thread-system-row")).toBeInTheDocument();
    expect(screen.getByTestId("thread-system-row").textContent).toContain("not yet");
  });
});
