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

    // Setup stays folded; the missing agent and its action stay visible.
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /Run.*Bind an agent first/ })).toBeInTheDocument(),
    );

    const runButton = screen.getByRole("button", {
      name: /Run.*Bind an agent first/,
    });
    expect(runButton).toBeDisabled();
    await waitFor(() => expect(screen.getByText("No agent", { exact: true })).toBeVisible());
    expect(screen.getByRole("button", { name: "Choose agent" })).toBeVisible();
    expect(screen.queryByLabelText("Search agents")).toBeNull();
  });

  it("Run button is enabled when an agent is bound", async () => {
    mockHub({
      recipeId: "r1",
      recipes: [{ id: "r1", name: "My Agent", avatar: "", role: "" }],
    });
    render(<WorkbenchWindow workbenchId="wb1" />);

    await waitFor(() => {
      const runButton = screen.getByRole("button", { name: /Run this automation/ });
      expect(runButton).toBeEnabled();
    });

    const runButton = screen.getByRole("button", {
      name: /Run this automation/,
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

  it("shows no 'No agents yet' and no 'New Agent' when no agents exist (Betterment A4: personas are retired)", async () => {
    mockHub({ recipeId: null, recipes: [] });
    render(<WorkbenchWindow workbenchId="wb1" />);

    fireEvent.click(await screen.findByRole("button", { name: "Choose agent" }));
    await screen.findByRole("textbox", { name: "Search agents" });
    expect(screen.queryByText("No agents yet")).toBeNull();
    expect(screen.queryByText("New Agent")).toBeNull();
  });

  it("shows 'No agents match' when search filters all agents", async () => {
    mockHub({
      recipeId: null,
      recipes: [{ id: "r1", name: "Test Agent", avatar: "", role: "" }],
    });
    render(<WorkbenchWindow workbenchId="wb1" />);

    fireEvent.click(await screen.findByRole("button", { name: "Choose agent" }));
    // Configuration is requested before its agent list appears.
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
  const NO_ENGINE = { status: 409, body: { error: "No engine is set for this automation.", code: "no_assignment" } };
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

  it("offers the same engine repair from empty Runs without submitting a known refusal", async () => {
    const calls = mockHub({ recipeId: "r1", recipes: AGENT, engineStatus: "no_assignment" });
    render(<WorkbenchWindow workbenchId="wb1" />);
    await screen.findByTestId("wb-no-engine");
    fireEvent.click(screen.getByRole("tab", { name: "Runs" }));
    expect(screen.queryByRole("button", { name: "Run now" })).toBeNull();
    expect(screen.getByRole("button", { name: "Choose engine" })).toBeInTheDocument();
    expect(calls.mock.calls.filter(([input, init]) => String(input).endsWith("/run") && init?.method === "POST")).toHaveLength(0);
  });

  it("folds the bound agent roster while keeping its identity and engine controls visible", async () => {
    mockHub({ recipeId: "r1", recipes: AGENT, engineStatus: "assigned" });
    render(<WorkbenchWindow workbenchId="wb1" />);
    fireEvent.click(await screen.findByRole("button", { name: "Configure" }));
    const group = screen.getByRole("region", { name: "Agent" });
    expect(group).toHaveAttribute("data-material", "inset");
    const roster = group.querySelector("details")!;
    expect(roster).not.toHaveAttribute("open");
    expect(group.querySelector(".wb-config-current-agent strong")).toHaveTextContent("Agent");
    await waitFor(() => expect(group.querySelector(".wb-config-current-agent strong")).toBeVisible());
    expect(screen.getByRole("region", { name: "Engines" })).toHaveAttribute("data-material", "inset");
    fireEvent.click(within(group).getByText("Choose agent", { exact: true }));
    expect(roster).toHaveAttribute("open");
    expect(screen.getByLabelText("Search agents")).toBeVisible();
  });

  it("offers Run when the engine is assigned on THIS workbench only (subject scope)", async () => {
    mockHub({ recipeId: "r1", recipes: AGENT, engineStatus: "assigned", engineSource: "subject" });
    const fetchMock = vi.mocked(fetch);
    render(<WorkbenchWindow workbenchId="wb1" />);
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Run this automation now" })).not.toBeDisabled(),
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
    const run = await screen.findByRole("button", { name: "Run this automation now" });
    await waitFor(() => expect(run).not.toBeDisabled());
    await act(async () => { fireEvent.click(run); });
    await screen.findByTestId("wb-no-engine");
    expect(door()).toBeTruthy();
    expect(screen.getByRole("button", { name: "Run: No engine" })).toBeDisabled();
    expect(container.textContent).not.toMatch(/HTTP \d+/);
    expect(container.textContent).not.toContain("Could not start the run");
  });

  it("500, then Retry answered by the named 409: the receipt clears and the door shows", async () => {
    mockHub({
      recipeId: "r1", recipes: AGENT,
      runAnswers: [{ status: 500, body: { error: "boom" } }, NO_ENGINE],
    });
    const { container } = render(<WorkbenchWindow workbenchId="wb1" />);
    const run = await screen.findByRole("button", { name: "Run this automation now" });
    await waitFor(() => expect(run).not.toBeDisabled());
    await act(async () => { fireEvent.click(run); });
    expect((await screen.findByText("Could not start the run"))).toBeTruthy();
    expect(screen.queryByTestId("wb-no-engine")).toBeNull();
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Try again" })); });
    await screen.findByTestId("wb-no-engine");
    expect(door()).toBeTruthy();
    expect(container.textContent).not.toMatch(/HTTP \d+/);
    expect(container.textContent).not.toContain("Could not start the run");
    expect(screen.getByRole("button", { name: "Run: No engine" })).toBeDisabled();
  });
});

// Recorded from the real WorkbenchRunner/WorkbenchService on an isolated DB by
// test_grounding_source_restoration_reruns_same_item_with_exact_source. The
// failed attempt made zero provider calls; Re-run's producer retained the same
// item, instruction, explicit source and context. No model result is replayed.
const groundingRetryRecording = {"failed":{"id":"wb-5af249dd93","name":"Runner","recipe_id":"recipe-5af249dd93","profile_id":"profile-5af249dd93","resolver_profile_id":null,"schedule":null,"schedule_enabled":false,"schedule_revision":1,"item_order":[],"created_at":"2026-10-17T06:42:41Z","last_modified":"2026-10-17T06:42:41Z","deleted":false,"items":[{"id":"item-1","workbench_id":"wb-5af249dd93","title":"Item 1","body":"input 1","priority":3,"status":"failed","grounding":{"refs":["note:restored-source"]},"context":{"origin":"owner-instruction","project_id":"architecture-review"},"result":"Source unavailable · note:restored-source","result_artifact_id":null,"result_egress":null,"mint_attempted":false,"tokens_consumed":0,"created_at":"2026-10-17T06:42:41Z","last_modified":"2026-10-17T06:42:42.043721+00:00","claimed_at":"2026-10-17T06:42:42.043401+00:00","completed_at":"2026-10-17T06:42:42.043721+00:00","parked":false}],"item_count":1,"pending_count":0,"last_run":{"id":"wbrun_edfd91d1084f","workbench_id":"wb-5af249dd93","started_at":"2026-10-17T06:42:42.043097+00:00","completed_at":"2026-10-17T06:42:42.057525+00:00","items_attempted":1,"items_completed":0,"items_failed":1,"mint_failures":0,"total_tokens":0,"egress_boundary":"","model":"","constitutional_context_revision":0,"constitutional_context_hash":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","skills_injected":[],"status":"completed"},"assignment_summary":{"status":"assigned","source":"subject","chain":["Profile"],"repair":null}},"reset":{"id":"item-1","workbench_id":"wb-5af249dd93","title":"Item 1","body":"input 1","priority":3,"status":"pending","grounding":{"refs":["note:restored-source"]},"context":{"origin":"owner-instruction","project_id":"architecture-review"},"result":null,"result_artifact_id":null,"result_egress":null,"mint_attempted":false,"tokens_consumed":0,"created_at":"2026-10-17T06:42:41Z","last_modified":"2026-10-17T06:42:42Z","claimed_at":"2026-10-17T06:42:42.043401+00:00","completed_at":null,"parked":false},"pending":{"id":"wb-5af249dd93","name":"Runner","recipe_id":"recipe-5af249dd93","profile_id":"profile-5af249dd93","resolver_profile_id":null,"schedule":null,"schedule_enabled":false,"schedule_revision":1,"item_order":[],"created_at":"2026-10-17T06:42:41Z","last_modified":"2026-10-17T06:42:41Z","deleted":false,"items":[{"id":"item-1","workbench_id":"wb-5af249dd93","title":"Item 1","body":"input 1","priority":3,"status":"pending","grounding":{"refs":["note:restored-source"]},"context":{"origin":"owner-instruction","project_id":"architecture-review"},"result":null,"result_artifact_id":null,"result_egress":null,"mint_attempted":false,"tokens_consumed":0,"created_at":"2026-10-17T06:42:41Z","last_modified":"2026-10-17T06:42:42Z","claimed_at":"2026-10-17T06:42:42.043401+00:00","completed_at":null,"parked":false}],"item_count":1,"pending_count":1,"last_run":{"id":"wbrun_edfd91d1084f","workbench_id":"wb-5af249dd93","started_at":"2026-10-17T06:42:42.043097+00:00","completed_at":"2026-10-17T06:42:42.057525+00:00","items_attempted":1,"items_completed":0,"items_failed":1,"mint_failures":0,"total_tokens":0,"egress_boundary":"","model":"","constitutional_context_revision":0,"constitutional_context_hash":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","skills_injected":[],"status":"completed"},"assignment_summary":{"status":"assigned","source":"subject","chain":["Profile"],"repair":null}}};

describe("Workbench required source recovery", () => {
  beforeEach(() => { localStorage.clear(); mocks.listeners.clear(); });
  afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks(); });

  it("renders the actual missing source and Re-run queues the same grounded instruction and runs it", async () => {
    let snapshot: typeof groundingRetryRecording.failed | typeof groundingRetryRecording.pending =
      structuredClone(groundingRetryRecording.failed);
    const bench = snapshot.id;
    const original = snapshot.items[0];
    const calls = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const path = new URL(String(input), "http://test").pathname;
      const json = (body: unknown) => new Response(JSON.stringify(body), {
        headers: { "content-type": "application/json" },
      });
      if (path === `/api/workbenches/${bench}/items/${original.id}` && init?.method === "PUT") {
        expect(JSON.parse(String(init.body))).toEqual({
          status: "pending", result: null, result_egress: null, tokens_consumed: 0, completed_at: null,
        });
        snapshot = structuredClone(groundingRetryRecording.pending);
        return json({ item: groundingRetryRecording.reset });
      }
      if (path === `/api/workbenches/${bench}`) return json({ workbench: snapshot });
      if (path.endsWith("/runs")) return json({ runs: [] });
      if (path.endsWith("/memory")) return json({ entries: [] });
      if (path.startsWith("/api/skills")) return json({ skills: [] });
      return json({});
    });
    vi.stubGlobal("fetch", calls);
    useDesk.setState({
      items: { ...EMPTY_ITEMS,
        workbench: [{ kind: "workbench", id: bench, name: snapshot.name } as never],
        recipe: [{ kind: "recipe", id: snapshot.recipe_id, name: "Runner" } as never],
      },
      inferenceTargets: [], profiles: [],
    });
    const { container } = render(<WorkbenchWindow workbenchId={bench} />);
    fireEvent.click((await screen.findByText(original.title)).closest("button")!);
    await screen.findByRole("button", { name: "Re-run" });
    expect(container.querySelector(".wb-card-result-body")).toHaveTextContent(original.result);
    expect(screen.getByRole("textbox", { name: "Item body" })).toHaveValue(original.body);
    expect(screen.queryByRole("button", { name: "Open artifact" })).toBeNull();
    expect(screen.queryByText("Review needed")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Re-run" }));
    await waitFor(() => expect(screen.queryByRole("button", { name: "Re-run" })).toBeNull());
    expect(screen.getByRole("textbox", { name: "Item body" })).toHaveValue(original.body);
    expect(screen.getByText("NEEDS REVIEW")).toBeInTheDocument();
    expect(snapshot.items[0].id).toBe(original.id);
    expect(snapshot.items[0].grounding).toEqual(original.grounding);
    expect(snapshot.items[0].context).toEqual(original.context);
    expect(calls.mock.calls.filter(([, init]) => init?.method === "PUT")).toHaveLength(1);
    // Re-run runs it (recon step 17): after the PUT, one run of exactly this item.
    await waitFor(() => expect(calls.mock.calls.filter(([, init]) => init?.method === "POST")).toHaveLength(1));
    const [runUrl, runInit] = calls.mock.calls.find(([, init]) => init?.method === "POST")!;
    expect(new URL(String(runUrl), "http://test").pathname).toBe(`/api/workbenches/${bench}/run`);
    expect(JSON.parse(String(runInit!.body))).toEqual({ item_ids: [original.id] });
  });
});
