import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../lib/api";
import { openPerson } from "../../../desk/openObject";
import { __resetSurfaces, openProjectRoom, openSurfaceOr } from "../../../desk/shell";
import { useDesk } from "../../../desk/store";
import { MemoryCore } from "../MemoryCore";

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
    if (url === "/api/people/relationships") return { relationships: [{ id: "r1", display_name: "Mira Kovacs" }] };
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
    expect(within(home).getAllByRole("button", { name: "Open the source: 1:1 WITH MIRA" }).length).toBeGreaterThan(0);

    fireEvent.click(within(home).getByRole("button", { name: "Ledger" }));
    fireEvent.click(within(home).getByRole("button", { name: "Mira Kovacs" }));
    expect(vi.mocked(openProjectRoom)).toHaveBeenCalledWith("p1");
    expect(vi.mocked(openPerson)).toHaveBeenCalledWith("r1");

    fireEvent.change(within(home).getByRole("searchbox", { name: "Ask your desk" }), { target: { value: "what changed?" } });
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
      if (url === "/api/people/relationships") throw new Error("people unavailable");
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
      expect(screen.getByRole("searchbox", { name: "Ask your desk" })).toBeTruthy();
      expect(screen.queryByRole("button", { name: "RAW", exact: true })).toBeNull();
      release(held === "/api/memory/pages" ? pages : held === "/api/projects"
        ? { projects: [{ id: "p1", name: "Ledger" }] } : beliefs);
      expect(await screen.findByRole("button", { name: "RAW", exact: true })).toBeTruthy();
      expect(screen.getAllByTestId("standing-page")).toHaveLength(2);
      expect(screen.getByRole("button", { name: "Ledger" })).toBeTruthy();
    },
  );

  it("shows one empty message and the background engine picker when no page exists", async () => {
    vi.mocked(apiFetch).mockImplementation(async (url) => {
      if (String(url).startsWith("/api/memory/pages")) return { pages: [] };
      if (String(url).startsWith("/api/memory/recall")) return { beliefs: [] };
      if (url === "/api/inference/assignments") return {};
      return {};
    });
    render(<MemoryCore />);
    const empty = await screen.findByTestId("memory-empty");
    expect(empty.textContent).toContain("Not written yet.");
    expect(screen.getAllByText("Not written yet.")).toHaveLength(1);
    fireEvent.click(within(empty).getByRole("button", { name: "Choose engine" }));
    await waitFor(() => expect(vi.mocked(openSurfaceOr)).toHaveBeenCalledWith("open-concierge", "/models", "background"));
  });
});
