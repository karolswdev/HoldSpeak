/** HS-135-15 — workbench creation operates: Run ghosting, AGENT empty state. */
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../../api";
import { useDesk } from "../../store";

type Frame = { type: string; data: unknown };

const mocks = vi.hoisted(() => ({
  listeners: new Map<string, Set<(frame: Frame) => void>>(),
}));

vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    lastFrame: null,
    subscribe: (type: string, listener: (frame: Frame) => void) => {
      const set =
        mocks.listeners.get(type) ?? new Set<(frame: Frame) => void>();
      set.add(listener);
      mocks.listeners.set(type, set);
      return () => set.delete(listener);
    },
  }),
  useRuntimeFrame: () => null,
}));

import { WorkbenchWindow } from "../WorkbenchWindow";

function mockHub(opts: {
  recipeId?: string | null;
  recipes?: Array<{ id: string; name: string; avatar: string; role: string }>;
  /** `assignment_summary.status` on the detail (resolved for THIS workbench by
   *  the hub, runner precedence); omitted = the detail carries no summary. */
  engineStatus?: "assigned" | "no_assignment";
  engineSource?: string | null;
  /** The hub's answers to successive POST /run calls (the last one repeats). */
  runAnswers?: Array<{ status: number; body: unknown }>;
  items?: Array<{ id: string; title: string }>;
} = {}) {
  const { recipeId = null, recipes = [], engineStatus, engineSource = null, runAnswers, items = [] } = opts;
  const live = items.map((i) => ({ ...i, body: "", status: "pending", priority: 3, result: null, parked: false }));
  const wb = () => ({
    id: "wb1",
    name: "Test WB",
    recipe_id: recipeId,
    profile_id: null,
    resolver_profile_id: null,
    schedule: null,
    schedule_enabled: false,
    items: live.filter((i) => !i.parked),
    last_run: null,
    ...(engineStatus
      ? { assignment_summary: { status: engineStatus, source: engineSource, chain: engineStatus === "assigned" ? ["Qwen3"] : [], repair: null } }
      : {}),
  });
  let runCalls = 0;
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const json = (body: unknown, status = 200) =>
      new Response(JSON.stringify(body), {
        status,
        headers: { "content-type": "application/json" },
      });
    if (/\/api\/workbenches\/wb1\/run$/.test(url) && runAnswers) {
      const answer = runAnswers[Math.min(runCalls, runAnswers.length - 1)];
      runCalls += 1;
      return json(answer.body, answer.status);
    }
    const park = url.match(/\/api\/workbenches\/wb1\/items\/([^/]+)$/);
    if (park && init?.method === "DELETE") {
      const it = live.find((i) => i.id === park[1]);
      if (it) it.parked = true;
      return json({ success: true, parked: park[1] });
    }
    if (/\/runs$/.test(url)) return json({ runs: [] });
    if (/\/memory$/.test(url)) return json({ entries: [] });
    if (/\/api\/skills/.test(url)) return json({ skills: [] });
    if (/\/api\/workbenches\/wb1\?parked=true$/.test(url))
      return json({ workbench: { ...wb(), items: live.filter((i) => i.parked) } });
    if (/\/api\/workbenches\/wb1$/.test(url)) return json({ workbench: wb() });
    return json({});
  });
  vi.stubGlobal("fetch", fetchMock);
  useDesk.setState({
    items: {
      ...EMPTY_ITEMS,
      workbench: [
        { kind: "workbench", id: "wb1", name: "Test WB" } as never,
      ],
      recipe: recipes.map((r) => ({ ...r, kind: "recipe" })) as never[],
    },
    inferenceTargets: [],
    profiles: [],
  });
  return fetchMock;
}

describe("HS-135-15 Run button ghosting", () => {
  beforeEach(() => {
    localStorage.clear();
    mocks.listeners.clear();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("Run button is disabled with visible reason when no agent is bound", async () => {
    mockHub({ recipeId: null });
    render(<WorkbenchWindow workbenchId="wb1" />);

    // Wait for the config panel to load (it auto-opens when no agent)
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /Run.*Bind an agent first/ })).toBeInTheDocument(),
    );

    const runButton = screen.getByRole("button", {
      name: /Run.*Bind an agent first/,
    });
    expect(runButton).toBeDisabled();
    // The visible reason label should be present
    expect(runButton.textContent).toContain("Bind an agent first");
  });

  it("Run button is enabled when an agent is bound", async () => {
    mockHub({
      recipeId: "r1",
      recipes: [{ id: "r1", name: "My Agent", avatar: "", role: "" }],
    });
    render(<WorkbenchWindow workbenchId="wb1" />);

    await waitFor(() => {
      const runButton = screen.getByRole("button", { name: /Run this workbench/ });
      expect(runButton).toBeEnabled();
    });

    const runButton = screen.getByRole("button", {
      name: /Run this workbench/,
    });
    expect(runButton.textContent).not.toContain("Bind an agent");
  });
});

describe("HS-135-15 AGENT section empty vs filtered labels", () => {
  beforeEach(() => {
    localStorage.clear();
    mocks.listeners.clear();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("shows 'No agents yet' with create affordance when no agents exist", async () => {
    mockHub({ recipeId: null, recipes: [] });
    render(<WorkbenchWindow workbenchId="wb1" />);

    // The config panel auto-opens when no agent is bound
    await waitFor(() =>
      expect(screen.getByText("No agents yet")).toBeInTheDocument(),
    );

    // Should show a "New Agent" create affordance
    expect(screen.getByText("New Agent")).toBeInTheDocument();
  });

  it("shows 'No agents match' when search filters all agents", async () => {
    mockHub({
      recipeId: null,
      recipes: [{ id: "r1", name: "Test Agent", avatar: "", role: "" }],
    });
    render(<WorkbenchWindow workbenchId="wb1" />);

    // Wait for config panel with the agent listed
    await waitFor(() =>
      expect(screen.getByText("Test Agent")).toBeInTheDocument(),
    );

    // Type a search that matches nothing
    const searchInput = screen.getByPlaceholderText("SEARCH AGENTS");
    await act(async () => {
      searchInput.focus();
      // Simulate typing a non-matching query
      const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype,
        "value",
      )?.set;
      nativeInputValueSetter?.call(searchInput, "zzz_no_match");
      searchInput.dispatchEvent(new Event("input", { bubbles: true }));
    });

    await waitFor(() =>
      expect(screen.getByText("No agents match")).toBeInTheDocument(),
    );
  });
});

// Inventory 2026-10-03: Run was live with no engine; the press gave
// "RUN FAILED · HTTP 500" and the hub's reason never reached the face.
// PR #779 review (Astra): the fact is the assignment resolved for THIS
// workbench; the door stays reachable under a Park receipt; Retry handles
// the named refusal too.
describe("Run with no engine", () => {
  const AGENT = [{ id: "r1", name: "Agent", avatar: "", role: "" }];
  const NO_ENGINE = { status: 409, body: { error: "No engine is set for this workbench.", code: "no_assignment" } };
  beforeEach(() => {
    localStorage.clear();
    mocks.listeners.clear();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });
  const door = () => within(screen.getByTestId("wb-no-engine")).getByRole("button", { name: "Choose an engine" });

  it("does not offer Run and shows the Choose an engine door", async () => {
    mockHub({ recipeId: "r1", recipes: AGENT, engineStatus: "no_assignment" });
    render(<WorkbenchWindow workbenchId="wb1" />);
    await screen.findByTestId("wb-no-engine");
    expect(door()).toBeTruthy();
    expect(screen.getByText("No engine", { selector: "*:not(small)" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Run: No engine" })).toBeDisabled();
  });

  it("offers Run when the engine is assigned on THIS workbench only (subject scope)", async () => {
    mockHub({ recipeId: "r1", recipes: AGENT, engineStatus: "assigned", engineSource: "subject" });
    const fetchMock = vi.mocked(fetch);
    render(<WorkbenchWindow workbenchId="wb1" />);
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Run this workbench now" })).not.toBeDisabled(),
    );
    expect(screen.queryByTestId("wb-no-engine")).toBeNull();
    // The window does not ask the subject-blind assignment editor.
    expect(fetchMock.mock.calls.some(([input]) => String(input).includes("/api/inference/assignments/editor"))).toBe(false);
  });

  it("keeps the door reachable while a Park receipt stands", async () => {
    mockHub({
      recipeId: "r1", recipes: AGENT, engineStatus: "no_assignment",
      items: [{ id: "i1", title: "First item" }, { id: "i2", title: "Second item" }],
    });
    render(<WorkbenchWindow workbenchId="wb1" />);
    const head = await screen.findByText("First item");
    fireEvent.click(head.closest("button")!);
    fireEvent.click(await screen.findByRole("button", { name: "Park" }));
    const receipt = await screen.findByTestId("wb-park-receipt");
    expect(within(receipt).getByRole("button", { name: "Restore" })).toBeTruthy();
    // The receipt holds the slot; the repair door is still on the face.
    expect(door()).toBeTruthy();
    expect(screen.getByRole("button", { name: "Run: No engine" })).toBeDisabled();
  });

  it("a named 409 from the hub reads as NO ENGINE with the door, never as HTTP", async () => {
    // The detail carries no summary, so Run is live; the hub then refuses by name.
    mockHub({ recipeId: "r1", recipes: AGENT, runAnswers: [NO_ENGINE] });
    const { container } = render(<WorkbenchWindow workbenchId="wb1" />);
    const run = await screen.findByRole("button", { name: "Run this workbench now" });
    await waitFor(() => expect(run).not.toBeDisabled());
    await act(async () => { fireEvent.click(run); });
    await screen.findByTestId("wb-no-engine");
    expect(door()).toBeTruthy();
    expect(screen.getByRole("button", { name: "Run: No engine" })).toBeDisabled();
    expect(container.textContent).not.toMatch(/HTTP \d+/);
    expect(container.textContent).not.toContain("RUN FAILED");
  });

  it("500, then Retry answered by the named 409: the receipt clears and the door shows", async () => {
    mockHub({
      recipeId: "r1", recipes: AGENT,
      runAnswers: [{ status: 500, body: { error: "boom" } }, NO_ENGINE],
    });
    const { container } = render(<WorkbenchWindow workbenchId="wb1" />);
    const run = await screen.findByRole("button", { name: "Run this workbench now" });
    await waitFor(() => expect(run).not.toBeDisabled());
    await act(async () => { fireEvent.click(run); });
    expect((await screen.findByText("RUN FAILED · HTTP 500"))).toBeTruthy();
    expect(screen.queryByTestId("wb-no-engine")).toBeNull();
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Retry" })); });
    await screen.findByTestId("wb-no-engine");
    expect(door()).toBeTruthy();
    expect(container.textContent).not.toMatch(/HTTP \d+/);
    expect(container.textContent).not.toContain("RUN FAILED");
    expect(screen.getByRole("button", { name: "Run: No engine" })).toBeDisabled();
  });
});
