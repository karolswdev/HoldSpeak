/** HS-135-15 — workbench creation operates: Run ghosting, AGENT empty state. */
import { act, render, screen, waitFor } from "@testing-library/react";
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
} = {}) {
  const { recipeId = null, recipes = [] } = opts;
  const wb = {
    id: "wb1",
    name: "Test WB",
    recipe_id: recipeId,
    profile_id: null,
    resolver_profile_id: null,
    schedule: null,
    schedule_enabled: false,
    items: [],
    last_run: null,
  };
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    const json = (body: unknown) =>
      new Response(JSON.stringify(body), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    if (/\/runs$/.test(url)) return json({ runs: [] });
    if (/\/memory$/.test(url)) return json({ entries: [] });
    if (/\/api\/skills/.test(url)) return json({ skills: [] });
    if (/\/api\/workbenches\/wb1$/.test(url)) return json({ workbench: wb });
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
