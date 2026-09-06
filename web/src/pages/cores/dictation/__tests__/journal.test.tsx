// HS-176-03 — the Journal wing as a stream: row grammar, the filter tokens,
// the two empty states, `Clear`'s presence rule, the bus prepend + dedupe,
// and the `before=` page.
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { Journal, journalDayLabel, journalUrl, landedLabel, sourceBadge } from "../Journal";

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
  listeners: new Map<string, (frame: { type: string; data: unknown }) => void>(),
}));

vi.mock("../../../../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  readableError: (e: unknown) => (e instanceof Error ? e.message : "failed"),
}));

// `useRuntimeBus` throws outside its provider (RuntimeBus.tsx:106-111); the
// LiveCore.test.tsx pattern is to mock the module and drive the frames.
vi.mock("../../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    lastFrame: null,
    subscribe: (type: string, listener: (frame: { type: string; data: unknown }) => void) => {
      mocks.listeners.set(type, listener);
      return () => mocks.listeners.delete(type);
    },
  }),
}));

function push(data: Record<string, unknown>) {
  const listener = mocks.listeners.get("dictation.journal.entry");
  if (!listener) throw new Error("the Journal never subscribed to the bus");
  act(() => listener({ type: "dictation.journal.entry", data }));
}

const READINESS = {
  target: {
    overrides: [
      { id: "claude_code", label: "Claude Code" },
      { id: "terminal_shell", label: "Terminal shell" },
    ],
  },
};

function row(over: Record<string, unknown> = {}) {
  return {
    id: 5,
    created_at: new Date().toISOString(),
    source: "dictation",
    transcript: "Ship the Q4 platform in October",
    final_text: "Ship the Q4 platform in October",
    total_ms: 38,
    target_profile: "claude_code",
    corrections_applied: [],
    taught_from: false,
    ...over,
  };
}

/** Route every URL the wing reads; `journal` is a function of the URL. */
function wire(journal: (url: string) => unknown) {
  mocks.apiFetch.mockImplementation((url: string) => {
    if (url.startsWith("/api/dictation/readiness")) return Promise.resolve(READINESS);
    if (url.startsWith("/api/dictation/journal")) return Promise.resolve(journal(url));
    return Promise.resolve({});
  });
}

function journalUrls(): string[] {
  return mocks.apiFetch.mock.calls
    .map((call: unknown[]) => String(call[0]))
    .filter((url) => url.startsWith("/api/dictation/journal"));
}

beforeEach(() => {
  vi.clearAllMocks();
  mocks.listeners.clear();
});

describe("the Journal row grammar", () => {
  it("draws LANDED IN <label>, N MS, the source badge, and the APPLIED chip only where a rule fired", async () => {
    wire(() => ({
      count: 2,
      items: [
        row({ id: 9, corrections_applied: [3] }),
        row({
          id: 8,
          transcript: "Tail the steward log",
          target_profile: "terminal_shell",
          total_ms: 47,
          source: "hotkey",
        }),
      ],
    }));
    const { container } = render(<Journal />);

    await screen.findByText("Ship the Q4 platform in October");
    expect(screen.getByText("LANDED IN CLAUDE CODE")).toBeInTheDocument();
    expect(screen.getByText("LANDED IN TERMINAL SHELL")).toBeInTheDocument();
    expect(screen.getByText("38 MS")).toBeInTheDocument();
    expect(screen.getByText("47 MS")).toBeInTheDocument();
    // Human source badges — never the wire's `dry_run`/snake_case. Scoped to
    // the trailing slot: the filter strip carries the same words.
    const badges = Array.from(
      container.querySelectorAll(".surface-ledger-trailing"),
    ).map((n) => n.textContent);
    expect(badges).toEqual(["DICTATION", "HOTKEY"]);

    // APPLIED carries NO count and appears only on the row that stored ids.
    const applied = screen.getAllByText("APPLIED");
    expect(applied).toHaveLength(1);
    expect(applied[0].textContent).toBe("APPLIED");
    expect(applied[0]).toHaveAttribute("data-tone", "ok");

    // The APPLIED/TAUGHT slot is present on EVERY row, so an empty one never
    // moves its neighbours.
    expect(container.querySelectorAll(".journal-mark")).toHaveLength(2);
  });

  it("draws TAUGHT only on the row he taught FROM, and never renders from `learning`", async () => {
    wire(() => ({
      count: 2,
      items: [
        row({ id: 9, taught_from: true, transcript: "Ship the queue for platform" }),
        row({
          id: 8,
          transcript: "Draft the release note",
          // The retired read-time signals: they must paint nothing (R2).
          learning: { matched: true, similar: 4 },
          best_correction_signal: { similar: 4 },
        }),
      ],
    }));
    render(<Journal />);

    await screen.findByText("Ship the queue for platform");
    const taught = screen.getAllByText("TAUGHT");
    expect(taught).toHaveLength(1);
    expect(taught[0].textContent).toBe("TAUGHT");
    expect(screen.queryByText(/SIMILAR/)).toBeNull();
  });

  it("keeps every verb on the opened row and tokenises the replay preview", async () => {
    wire((url) =>
      url.includes("replay")
        ? { after: { final_text: "" } }
        : { count: 1, items: [row({ id: 9 })] },
    );
    mocks.apiFetch.mockImplementation((url: string) => {
      if (url.startsWith("/api/dictation/readiness")) return Promise.resolve(READINESS);
      if (url.includes("/replay")) return Promise.resolve({ after: { final_text: "" } });
      if (url.startsWith("/api/dictation/journal"))
        return Promise.resolve({ count: 1, items: [row({ id: 9 })] });
      return Promise.resolve({});
    });
    render(<Journal />);

    const line = await screen.findByText("Ship the Q4 platform in October");
    fireEvent.click(line.closest("button")!);

    // The 175 law: a replacing face keeps its verbs.
    expect(screen.getByRole("button", { name: "Replay" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copy" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Replay" }));
    // Tokens, not the two sentences the old face carried (rule A.3).
    expect(await screen.findByText("REPLAY · PREVIEW")).toBeInTheDocument();
    expect(screen.getByText("NO TEXT")).toBeInTheDocument();
    expect(screen.queryByText(/preview only/)).toBeNull();
    expect(screen.queryByText(/completed without text/)).toBeNull();
  });
});

describe("the Journal's filter tokens", () => {
  it("drives the route's `source` param, with ALL sending none", async () => {
    wire(() => ({ count: 1, items: [row({ id: 9 })] }));
    render(<Journal />);
    await screen.findByText("Ship the Q4 platform in October");

    expect(journalUrls()[0]).toBe("/api/dictation/journal?limit=50");

    fireEvent.click(screen.getByRole("button", { name: "BROWSER" }));
    await waitFor(() =>
      expect(journalUrls()).toContain("/api/dictation/journal?limit=50&source=browser"),
    );

    fireEvent.click(screen.getByRole("button", { name: "ALL" }));
    await waitFor(() =>
      expect(journalUrls().filter((u) => u === "/api/dictation/journal?limit=50")).toHaveLength(2),
    );
  });

  it("renders the tokens over an empty stream (no sparse rule)", async () => {
    wire(() => ({ count: 0, items: [] }));
    render(<Journal />);
    await screen.findByText("NOTHING SPOKEN");
    for (const label of ["ALL", "DICTATION", "BROWSER", "HOTKEY"])
      expect(screen.getByRole("button", { name: label })).toBeInTheDocument();
  });
});

describe("the Journal's two empty states and Clear", () => {
  it("reads NOTHING SPOKEN with no Clear when nothing was ever spoken", async () => {
    wire(() => ({ count: 0, items: [] }));
    render(<Journal />);
    await screen.findByText("NOTHING SPOKEN");
    expect(screen.queryByText("NOTHING MATCHES")).toBeNull();
    // A verb that does nothing is a lie (A.11).
    expect(screen.queryByRole("button", { name: "Clear" })).toBeNull();
  });

  it("reads NOTHING MATCHES on a search miss, with Clear present", async () => {
    wire(() => ({ count: 1, items: [row({ id: 9 })] }));
    render(<Journal />);
    await screen.findByText("Ship the Q4 platform in October");
    expect(screen.getByRole("button", { name: "Clear" })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Search the journal"), {
      target: { value: "zzz nothing" },
    });
    expect(await screen.findByText("NOTHING MATCHES")).toBeInTheDocument();
    expect(screen.queryByText("NOTHING SPOKEN")).toBeNull();
    expect(screen.getByRole("button", { name: "Clear" })).toBeInTheDocument();
  });

  it("searches final_text as well as the transcript", async () => {
    wire(() => ({
      count: 1,
      items: [row({ id: 9, transcript: "postgress migration", final_text: "PostgreSQL migration" })],
    }));
    render(<Journal />);
    await screen.findByText("postgress migration");
    fireEvent.change(screen.getByLabelText("Search the journal"), {
      target: { value: "PostgreSQL" },
    });
    expect(screen.getByText("postgress migration")).toBeInTheDocument();
    expect(screen.queryByText("NOTHING MATCHES")).toBeNull();
  });
});

describe("the Journal's live push", () => {
  it("prepends a pushed entry and never doubles one already loaded", async () => {
    wire(() => ({ count: 1, items: [row({ id: 9 })] }));
    const { container } = render(<Journal />);
    await screen.findByText("Ship the Q4 platform in October");

    push({
      id: 10,
      created_at: new Date().toISOString(),
      source: "hotkey",
      transcript: "Move the design review to Thursday",
      final_text: "Move the design review to Thursday",
      total_ms: 33,
      corrections_applied: [],
      taught_from: false,
      target_profile: "editor",
    });
    expect(await screen.findByText("Move the design review to Thursday")).toBeInTheDocument();
    const primaries = () =>
      Array.from(container.querySelectorAll(".surface-ledger-primary")).map(
        (n) => n.textContent,
      );
    expect(primaries()[0]).toBe("Move the design review to Thursday");

    // The same id again (a frame racing the read) must not double the row.
    push({ id: 10, transcript: "Move the design review to Thursday", source: "hotkey" });
    push({ id: 9, transcript: "Ship the Q4 platform in October", source: "dictation" });
    expect(primaries()).toHaveLength(2);
  });
});

describe("the Journal's scroll-to-load", () => {
  it("pages with before=<oldest id> and appends the older rows", async () => {
    const observers: Array<() => void> = [];
    class ObserverStub {
      constructor(private cb: (entries: { isIntersecting: boolean }[]) => void) {
        observers.push(() => this.cb([{ isIntersecting: true }]));
      }
      observe() {}
      disconnect() {}
      unobserve() {}
    }
    vi.stubGlobal("IntersectionObserver", ObserverStub);

    const first = Array.from({ length: 50 }, (_, i) =>
      row({ id: 100 - i, transcript: `line ${100 - i}` }),
    );
    mocks.apiFetch.mockImplementation((url: string) => {
      if (url.startsWith("/api/dictation/readiness")) return Promise.resolve(READINESS);
      if (url.includes("before=51"))
        return Promise.resolve({ count: 51, items: [row({ id: 49, transcript: "line 49" })] });
      return Promise.resolve({ count: 51, items: first });
    });

    render(<Journal />);
    await screen.findByText("line 100");
    expect(screen.queryByText("line 49")).toBeNull();

    // The sentinel comes into view. Retried, because the page's own effects
    // may still be settling under a loaded machine; `paging` and the id dedupe
    // make a repeat call a no-op.
    await waitFor(
      async () => {
        await act(async () => {
          observers.at(-1)?.();
        });
        expect(journalUrls()).toContain("/api/dictation/journal?limit=50&before=51");
      },
      { timeout: 5000 },
    );
    expect(
      await screen.findByText("line 49", undefined, { timeout: 5000 }),
    ).toBeInTheDocument();
    // The whole history is never refetched — the first page stands.
    expect(screen.getByText("line 100")).toBeInTheDocument();
    vi.unstubAllGlobals();
  });
});

describe("the Journal's pure grammar", () => {
  it("builds the route's URL", () => {
    expect(journalUrl("")).toBe("/api/dictation/journal?limit=50");
    expect(journalUrl("hotkey")).toBe("/api/dictation/journal?limit=50&source=hotkey");
    expect(journalUrl("", 12)).toBe("/api/dictation/journal?limit=50&before=12");
  });

  it("renders labels, never raw ids", () => {
    const labels = { claude_code: "Claude Code" };
    expect(landedLabel({ target_profile: "claude_code" }, labels)).toBe("CLAUDE CODE");
    expect(landedLabel({ target_profile: "terminal_shell" }, {})).toBe("TERMINAL SHELL");
    expect(landedLabel({ source: "dry_run" }, labels)).toBe("DRY RUN");
    expect(landedLabel({}, labels)).toBe("");
    expect(sourceBadge("dry_run")).toBe("DRY RUN");
    expect(sourceBadge("dictation")).toBe("DICTATION");
    expect(sourceBadge("")).toBe("");
  });

  it("bands the days TODAY / YESTERDAY / the date", () => {
    const now = new Date("2026-09-06T12:00:00");
    expect(journalDayLabel(new Date("2026-09-06T09:00:00"), now)).toBe("TODAY");
    expect(journalDayLabel(new Date("2026-09-05T17:00:00"), now)).toBe("YESTERDAY");
    expect(journalDayLabel(new Date("2026-09-01T17:00:00"), now)).not.toMatch(/TODAY|YESTERDAY/);
    expect(journalDayLabel(null)).toBe("UNDATED");
  });
});
