import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../lib/api";
import { openPerson } from "../../../desk/openObject";
import { __resetSurfaces, openProjectRoom, openSurfaceOr } from "../../../desk/shell";
import { useDesk } from "../../../desk/store";
import { MemoryCore } from "../MemoryCore";
import { clearEngineCache } from "../../../desk/hooks/useEngine";
import TOOLS from "../../../test/wire/ask.tools.wire.json";

vi.mock("../../../lib/api", async (original) => ({
  ...await original<typeof import("../../../lib/api")>(),
  apiFetch: vi.fn(),
}));

vi.mock("../../../desk/shell", async (original) => ({
  ...await original<typeof import("../../../desk/shell")>(),
  openPerson: vi.fn(),
  openProjectRoom: vi.fn(),
  openSurfaceOr: vi.fn(),
}));

vi.mock("../../../desk/openObject", async (original) => ({
  ...await original<typeof import("../../../desk/openObject")>(),
  openPerson: vi.fn(),
}));

const source = { ref: "meeting:mira-1on1", token: "1:1 WITH MIRA", opens: true };
const pages = {
  pages: [
    {
      slug: "what-i-owe", question: "What do I owe?",
      sentences: [{ text: "You owe Mira feedback by Friday.", refs: [source] }],
      built_at: "2026-10-19T09:10:00Z", stale: false, new_sources: 0, model: "pages", boundary: "local",
    },
    {
      slug: "what-changed-this-week", question: "What changed this week?",
      sentences: [{ text: "The cutover review moved to Friday.", refs: [source] }],
      built_at: "2026-10-19T09:10:00Z", stale: false, new_sources: 0, model: "pages", boundary: "local",
    },
  ],
};
const beliefs = {
  current: [], superseded: [], disputed: [], owed: [], meetings: [], briefs: [], also: [], remembered: 1,
  query: "", recent: true, filter: "all", searched_at: "2026-10-19T09:10:00Z", projects_searched: 0,
  beliefs: [
    {
      id: "belief-mira", kind: "belief", text: "Mira owns the cutover review.", state: "current",
      proof_count: 1, source_count: 1, seen: "10-19", since: "", project: null,
      evidence: [source], history: [],
    },
    {
      id: "belief-other", kind: "belief", text: "Theo owns the on-call handbook.", state: "current",
      proof_count: 1, source_count: 1, seen: "10-19", since: "", project: null,
      evidence: [{ ref: "note:theo", token: "NOTE THEO", opens: true }], history: [],
    },
  ],
};

beforeEach(() => {
  const realAskQuestion = useDesk.getState().askQuestion;
  const askQuestion = vi.fn((question: string) => realAskQuestion(question));
  useDesk.setState({
    windowsById: {},
    items: { ...useDesk.getState().items },
    projects: [],
    inferenceTargets: [],
    askOpen: false,
    askThread: null,
    askQuestion,
  });
  vi.mocked(apiFetch).mockImplementation(async (url) => {
    if (String(url).startsWith("/api/memory/pages")) return pages;
    if (String(url).startsWith("/api/memory/recall")) return beliefs;
    if (url === "/api/projects") return { projects: [{ id: "p1", name: "Ledger" }] };
    if (url === "/api/people/relationships?counts=1") return { relationships: [{ id: "r1", display_name: "Mira Kovacs" }] };
    if (url === "/api/inference/assignments") return {};
    return {};
  });
});

afterEach(() => {
  __resetSurfaces();
  vi.clearAllMocks();
});

describe("Q12 Memory", () => {
  it("opens on desk answers, shows Why sources, and links projects and people", async () => {
    useDesk.setState({
      askThread: {
        threadId: null,
        nonce: 3,
        about: [
          { id: "p1", kind: "project", title: "Ledger", ref: "project:p1" },
          { id: "r1", kind: "person", title: "Mira Kovacs", ref: "person:r1" },
        ],
      },
      selectedIds: ["note:scoped"],
    });
    render(<MemoryCore />);
    const home = await screen.findByTestId("memory-home");
    expect((await within(home).findAllByTestId("standing-page")).map((page) => page.getAttribute("aria-label"))).toEqual([
      "What I owe", "What changed this week",
    ]);
    expect(within(home).queryByText("Recent work")).toBeNull();

    fireEvent.click(within(home).getAllByRole("button", { name: "Why" })[0]);
    expect(within(home).getByTestId("memory-belief").textContent).toContain("Mira owns the cutover review.");
    expect(within(home).getByTestId("memory-belief").textContent).not.toContain("Theo owns the on-call handbook.");
    expect(within(home).getAllByRole("button", { name: "Open the source: 1:1 With Mira" }).length).toBeGreaterThan(0);

    // The links are list views: a programmatic press selects (Open in the
    // status bar); one pointer press opens (W1-KIT).
    fireEvent.click(within(home).getByRole("button", { name: "Ledger" }));
    fireEvent.click(screen.getByTestId("memory-open-selected"));
    expect(vi.mocked(openProjectRoom)).toHaveBeenCalledWith("p1");
    fireEvent.click(within(home).getByRole("button", { name: "Mira Kovacs" }), { detail: 1 });
    expect(vi.mocked(openPerson)).toHaveBeenCalledWith("r1");
    expect(screen.getByTestId("memory-written").textContent).toMatch(/^Written /);
    expect(screen.getByTestId("memory-status").textContent).toContain("1 project");
    expect(screen.getByTestId("memory-status").textContent).toContain("1 person");

    fireEvent.change(within(home).getByRole("searchbox", { name: "Find or ask your desk" }), { target: { value: "what changed?" } });
    fireEvent.click(within(home).getByRole("button", { name: "Ask" }));
    expect(useDesk.getState().askQuestion).toHaveBeenCalledWith("what changed?");
    expect(useDesk.getState().askThread?.about).toBeUndefined();
    expect(useDesk.getState().selectedIds).toEqual([]);
    expect(vi.mocked(openSurfaceOr)).not.toHaveBeenCalled();
  });

  it("keeps a project link when the People directory read is unavailable", async () => {
    vi.mocked(apiFetch).mockImplementation(async (url) => {
      if (String(url).startsWith("/api/memory/pages")) return pages;
      if (String(url).startsWith("/api/memory/recall")) return { beliefs: [] };
      if (url === "/api/projects") return { projects: [{ id: "p1", name: "Ledger" }] };
      if (url === "/api/people/relationships?counts=1") throw new Error("people unavailable");
      if (url === "/api/inference/assignments") return {};
      return {};
    });
    render(<MemoryCore />);
    expect(await screen.findByRole("button", { name: "Ledger" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Mira Kovacs" })).toBeNull();
  });

  it.each(["/api/memory/pages", "/api/projects", "/api/memory/recall"])(
    "keeps the lower controls out until the first %s read settles", async (held) => {
      const original = vi.mocked(apiFetch).getMockImplementation()!;
      let release!: (value: unknown) => void;
      const pending = new Promise((resolve) => { release = resolve; });
      vi.mocked(apiFetch).mockImplementation((url, init) =>
        String(url).startsWith(held) ? pending : original(url, init));
      render(<MemoryCore />);
      expect(screen.getByRole("searchbox", { name: "Find or ask your desk" })).toBeTruthy();
      expect(screen.queryByTestId("memory-projects")).toBeNull();
      expect(screen.queryByTestId("memory-status")).toBeNull();
      release(held === "/api/memory/pages" ? pages : held === "/api/projects"
        ? { projects: [{ id: "p1", name: "Ledger" }] } : beliefs);
      expect(await screen.findByTestId("memory-projects")).toBeTruthy();
      expect(screen.getAllByTestId("standing-page")).toHaveLength(2);
      expect(screen.getByRole("button", { name: "Ledger" })).toBeTruthy();
    },
  );

  it("names a project's open count and meetings, and a person's role and what you owe, as quiet meta", async () => {
    vi.mocked(apiFetch).mockImplementation(async (url) => {
      if (String(url).startsWith("/api/memory/pages")) return { pages: [] };
      if (String(url).startsWith("/api/memory/recall")) return { beliefs: [] };
      if (url === "/api/projects") return { projects: [{ id: "p1", name: "Ledger", meeting_count: 3 }] };
      if (url === "/api/people/relationships?counts=1") {
        return { relationships: [{ id: "r1", display_name: "Mira Kovacs", relationship_kind: "direct_report", you_owe_count: 2 }] };
      }
      if (url === "/api/inference/assignments") return {};
      return {};
    });
    render(<MemoryCore />);
    const projects = await screen.findByTestId("memory-projects");
    expect(within(projects).getByRole("button", { name: "Ledger, 3 meetings" })).toBeTruthy();
    const people = screen.getByTestId("memory-people");
    expect(within(people).getByRole("button", { name: "Mira Kovacs, Direct report · You owe 2" })).toBeTruthy();
    expect(within(people).getByText("MK")).toBeTruthy();
  });

  it("shows one empty message and the background engine picker when no page exists", async () => {
    vi.mocked(apiFetch).mockImplementation(async (url) => {
      if (String(url).startsWith("/api/memory/pages")) return { pages: [] };
      if (String(url).startsWith("/api/memory/recall")) return { beliefs: [] };
      if (url === "/api/inference/assignments") return {};
      return {};
    });
    render(<MemoryCore />);
    const empty = await screen.findByTestId("memory-empty");
    expect(empty.textContent).toBe("Desk pages not written yet");
    expect(screen.getAllByText("Desk pages not written yet")).toHaveLength(1);
    expect(screen.getByTestId("memory-pages-line").textContent).toContain("No engine writes the desk pages");
    // DELIGHT 2: no project and no person yet is the memory object and one line.
    const nothing = screen.getByTestId("memory-nothing");
    expect(nothing.querySelector('.surface-state[data-object="memory"] .surface-state-sprite')?.getAttribute("src")).toMatch(/memory\.png$/);
    expect(nothing.textContent).toBe("No projects or people yet");
    // No RAW fold on this face (debug hides behind RAW on the desk floor).
    expect(screen.queryByRole("button", { name: /^RAW$/ })).toBeNull();
    fireEvent.click(within(screen.getByTestId("memory-pages-line")).getByRole("button", { name: "Choose engine" }));
    await waitFor(() => expect(vi.mocked(openSurfaceOr)).toHaveBeenCalledWith("open-concierge", "/models", "background"));
  });

  it("pass 2: one engine truth — Ask has an engine, nothing writes the pages: the toolbar and the line both say no engine", async () => {
    // The recorded summary has ask.answer assigned and memory.page not:
    // the atlas's "● Studio engine" over "No engine writes the desk pages".
    clearEngineCache();
    vi.mocked(apiFetch).mockImplementation(async (url) => {
      if (String(url).startsWith("/api/memory/pages")) return { pages: [] };
      if (String(url).startsWith("/api/memory/recall")) return { beliefs: [] };
      if (url === "/api/inference/assignments") return TOOLS.assignments;
      return {};
    });
    render(<MemoryCore />);
    const line = await screen.findByTestId("memory-pages-line");
    expect(line.textContent).toContain("No engine writes the desk pages");
    const engine = within(screen.getByTestId("memory-toolbar")).getByTestId("engine-line");
    await waitFor(() => expect(engine).toHaveAttribute("data-state", "none"));
    expect(engine).toHaveTextContent("No engine");
    expect(engine).not.toHaveTextContent("Glass Lan");
    fireEvent.click(engine);
    await waitFor(() => expect(vi.mocked(openSurfaceOr)).toHaveBeenCalledWith("open-concierge", "/models", "background"));
    clearEngineCache();
  });

  it("W2: the composer field finds as it is typed: names, then what the desk remembers, as name · kind · date rows", async () => {
    vi.mocked(apiFetch).mockImplementation(async (url) => {
      if (String(url).startsWith("/api/memory/pages")) return pages;
      if (String(url).startsWith("/api/memory/recall?query=")) {
        return {
          ...beliefs, query: "ledger", recent: false, beliefs: [],
          current: [{ id: "d1", ref: "decision:d1", text: "Freeze the ledger on Nov 5", decided_at: "2026-10-20T10:00:00Z",
            rationale: "", lifecycle: "accepted", state: "current", dec_token: "", axes: [], support: "", acceptance: "",
            successor: null, predecessor_id: null, supersession_reason: null, dispute_reason: null, project: null,
            source: null, carried: false, commitment_ids: [] }],
          meetings: [{ kind: "calendar_event", source_ref: "meeting:m1", title: "Ledger sync", snippet: "", occurred_at: "2026-10-21T10:00:00Z" }],
        };
      }
      if (String(url).startsWith("/api/memory/recall")) return beliefs;
      if (url === "/api/projects") return { projects: [{ id: "p1", name: "Ledger" }] };
      if (url === "/api/people/relationships?counts=1") return { relationships: [{ id: "r1", display_name: "Mira Kovacs" }] };
      if (url === "/api/inference/assignments") return {};
      return {};
    });
    render(<MemoryCore />);
    const home = await screen.findByTestId("memory-home");
    await within(home).findByTestId("memory-projects");
    // One field: the Ask composer row over the whole desk, with Ask ⏎.
    const toolbar = screen.getByTestId("memory-toolbar");
    expect(toolbar.textContent).toContain("My whole desk");
    expect(within(toolbar).getByRole("button", { name: "Ask" })).toBeDisabled();
    fireEvent.change(within(home).getByRole("searchbox", { name: "Find or ask your desk" }), { target: { value: "ledger" } });
    const found = await screen.findByTestId("memory-found");
    await waitFor(() => expect(within(found).getByRole("button", { name: /Freeze the ledger on Nov 5, Decision · Oct 20/ })).toBeTruthy());
    expect(within(found).getByRole("button", { name: "Ledger, Project" })).toBeTruthy();
    expect(within(found).getByRole("button", { name: /Ledger sync, Calendar · Oct 21/ })).toBeTruthy();
    expect(screen.queryByTestId("memory-people")).toBeNull();
    expect(screen.getByTestId("memory-found-count").textContent).toBe("3 found");
  });
});
