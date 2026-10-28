// Betterment E2 — Found on this Mac, one-press Add, and an agent engine's
// Spend limit per run, on the hub's own recorded answers.
//
// The answers come from `scripts/record_engines_fixture.py` (the real hub
// through TestClient, isolated HOME, the fake `claude`/`codex` of
// tests/fixtures/fake_agent_cli.py first on PATH). Only `apiFetch` is
// mocked: a GET replays the current step's answer; the connect POST checks
// the body the face sent and moves to the next recorded step. The hub half
// (detect, connect, cost, sign-in) is tests/integration/test_desk_engines.py.

import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../lib/api";
import { recordedGet, type Gets } from "../../../test/recordedHub";
import recorded from "./fixtures/engines.recorded.json";

vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: vi.fn(),
}));
// The speech row and Meaning search have their own tests; here only the
// Engines reads move.
vi.mock("../../concierge/MeaningSearchRow", () => ({ MeaningSearchRow: () => null }));
vi.mock("../../../desk/firstrun/SpeechSetup", () => ({
  useSpeechSetup: () => ({ notSetUp: false, ready: true, ai: { read: { kind: "ok" } } }),
  SpeechSetup: () => null,
}));
vi.mock("../../../desk/shell", () => ({ openSurfaceOr: vi.fn() }));

import { RunsOnCore } from "../RunsOnCore";

type Step = { name: string; gets: Gets; post?: string; body?: Record<string, unknown>; answer?: unknown };
const STEPS = recorded.claude.steps as Step[];
const step = (name: string) => STEPS.find((s) => s.name === name)!;

/** The hub, one recorded step at a time. */
function hub(start: Gets, posts: Record<string, Step> = {}) {
  let gets = start;
  const sent: Array<Record<string, unknown>> = [];
  vi.mocked(apiFetch).mockImplementation(async (path: string, init?: { method?: string; json?: unknown }) => {
    // E5's row editors were not recorded for this desk: the rows read NOT READ.
    if (path === "/api/inference/assignments/editor") throw new Error("not recorded");
    if (init?.method === "POST") {
      const draft = ((init.json ?? {}) as { draft?: Record<string, unknown> }).draft ?? {};
      sent.push(draft);
      const next = posts[String(draft.spend_limit_usd != null ? "limit" : "add")];
      if (!next || path !== next.post) throw new Error(`unrecorded POST ${path}`);
      gets = next.gets;
      return structuredClone(next.answer) as never;
    }
    return recordedGet(gets, String(path).split("?")[0]) as never;
  });
  return sent;
}

function width(px: number) {
  return vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockReturnValue({
    width: px, height: 800, top: 0, left: 0, right: px, bottom: 800, x: 0, y: 0, toJSON: () => ({}),
  });
}

// Window grammar (2026-10-24): an engine is a row of the dense engine list;
// the selected row's verbs and egress chip are in the status bar.
const ROW = "runson-engine-agent-claude";
const status = () => document.querySelector(".kit-statusbar") as HTMLElement;
/** Select one engine row (a press on its name). */
function pick(testId: string) {
  const row = screen.getByTestId(testId);
  fireEvent.click(row.querySelector(".object-list-open") as HTMLElement);
  return row;
}

beforeEach(() => {
  vi.mocked(apiFetch).mockReset();
});
afterEach(() => {
  vi.restoreAllMocks();
});

describe("Engines — Found on this Mac (Betterment E2)", () => {
  it.each([1440, 393])("at %i a signed-in Claude Code is found; Add makes it READY with the ANTHROPIC chip", async (px) => {
    width(px);
    const sent = hub(step("found").gets, { add: step("add") });
    render(<RunsOnCore />);

    const found = await screen.findByTestId("runson-found-engines");
    expect(found.textContent).toBe("1 found on this Mac");
    const plate = within(screen.getByTestId("runson-engines")).getByTestId("runson-engine-agent:found:claude");
    expect(plate.querySelector(".object-list-name-word")?.textContent).toBe("Claude Code · signed in");
    expect(within(plate).getByTestId("runson-engine-state-agent:found:claude").textContent).toBe("Found");
    expect(within(plate).getByText("Cloud")).toBeTruthy();
    // The selected row's egress chip and its verb are in the status bar.
    pick("runson-engine-agent:found:claude");
    expect(plate.getAttribute("aria-selected")).toBe("true");
    expect(within(status()).getByText("Anthropic")).toBeTruthy();

    await act(async () => {
      fireEvent.click(within(status()).getByRole("button", { name: "Add" }));
    });
    expect(sent).toHaveLength(1);
    expect(sent[0]).toMatchObject({ preset: "claude", profile_id: "agent-claude", expected_profile_revision: 0 });
    expect(sent[0]).not.toHaveProperty("spend_limit_usd");

    await waitFor(() => expect(screen.queryByTestId("runson-found-engines")).toBeNull());
    const engine = await within(screen.getByTestId("runson-engines")).findByTestId(ROW);
    pick(ROW);
    expect(engine.querySelector(".object-list-name-word")?.textContent).toBe("Claude Code");
    expect(within(engine).getByTestId("runson-engine-state-agent-claude").textContent).toBe("Ready");
    expect(within(status()).getByText("Anthropic")).toBeTruthy();
    expect(engine.textContent).not.toContain("Not signed in");
    expect(screen.getByTestId("runson-receipt").textContent).toMatch(/^Added at \d\d:\d\d · Claude Code$/);
  });

  it("with no agent CLI on this Mac the section is absent", async () => {
    hub(recorded.nothingFound.gets as Gets);
    render(<RunsOnCore />);
    await waitFor(() => expect(screen.getByTestId("runson-root").getAttribute("aria-busy")).toBeNull());
    expect(screen.queryByTestId("runson-found-engines")).toBeNull();
    expect(screen.queryByText(/Found on this Mac/)).toBeNull();
  });
});

describe("Engines — the empty list (DELIGHT 2)", () => {
  it("no engine is the engine object, one line and Add an engine, which opens the kinds", async () => {
    // The recorded fresh desk, with its one migrated speech engine unbound
    // the way the hub records every other unassigned job (no engine at all).
    const gets = structuredClone(recorded.nothingFound.gets) as unknown as Gets;
    const answer = gets["/api/inference/assignments"] as { task_overrides: Array<{ id: string; effective: Record<string, unknown> }> };
    const unassigned = answer.task_overrides.find((task) => task.effective.assignment == null)!.effective;
    for (const task of answer.task_overrides)
      if (task.effective.assignment != null) task.effective = { ...unassigned, capability_id: task.id };
    hub(gets);
    render(<RunsOnCore />);
    const empty = await screen.findByTestId("runson-engines-empty");
    const object = empty.querySelector('.surface-state[data-object="engine"]') as HTMLElement;
    expect(object.querySelector(".surface-state-sprite")?.getAttribute("src")).toMatch(/cartridge\.png$/);
    expect(object.querySelector(".surface-state-line")?.textContent).toBe("No engine yet");
    expect(object.textContent).not.toMatch(/\b0\b/);
    fireEvent.click(within(object).getByRole("button", { name: "Add an engine" }));
    expect(await screen.findByTestId("runson-add-kinds")).toBeInTheDocument();
    // The kinds are open: the empty state offers no second Add.
    expect(within(object).queryByRole("button", { name: "Add an engine" })).toBeNull();
  });
});

describe("Engines — pi on his LAN model (Betterment E7)", () => {
  const PI = (recorded as unknown as { pi: { steps: Step[] } }).pi.steps;
  const piStep = (name: string) => PI.find((s) => s.name === name)!;

  it.each([1440, 393])("at %i pi is found with his LAN box as its egress; Add keeps it on his network", async (px) => {
    width(px);
    const sent = hub(piStep("found").gets, { add: piStep("add") });
    render(<RunsOnCore />);
    await screen.findByTestId("runson-found-engines");
    const plate = pick("runson-engine-agent:found:pi");
    // pi's own config sends its model to 192.168.1.43: a LAN chip, never a vendor's cloud.
    expect(within(plate).getByText("LAN")).toBeTruthy();
    expect(within(status()).getByText("192.168.1.43 · LAN")).toBeTruthy();
    await act(async () => {
      fireEvent.click(within(status()).getByRole("button", { name: "Add" }));
    });
    expect(sent[0]).toMatchObject({ preset: "pi" });
    await within(screen.getByTestId("runson-engines")).findByTestId("runson-engine-agent-pi");
    pick("runson-engine-agent-pi");
    expect(within(status()).getByText("192.168.1.43 · LAN")).toBeTruthy();
  });
});

describe("Engines — an agent engine's Spend limit per run (Betterment E2)", () => {
  it("unfolds to No limit and the week's cost; Save sends the limit and the row shows it", async () => {
    width(1440);
    const sent = hub(step("spent").gets, { limit: step("limit") });
    render(<RunsOnCore />);
    await screen.findByTestId(ROW);
    pick(ROW);
    fireEvent.click(within(status()).getByRole("button", { name: "Spend" }));

    const detail = screen.getByTestId("runson-inspector-spend-agent-claude");
    const field = within(detail).getByLabelText("Spend limit per run") as HTMLInputElement;
    expect(field.value).toBe("");
    expect(field.placeholder).toBe("No limit");
    expect(within(detail).getByTestId("runson-agent-cost-agent-claude").textContent).toBe("Today $0.02 · this week $0.02");
    expect(within(detail).queryByRole("button", { name: "No limit" })).toBeNull();

    fireEvent.change(field, { target: { value: "0.5" } });
    await act(async () => {
      fireEvent.click(within(detail).getByRole("button", { name: "Save" }));
    });
    expect(sent).toEqual([
      expect.objectContaining({
        preset: "claude", profile_id: "agent-claude", expected_profile_revision: 1,
        label: "Claude Code", model: "default", spend_limit_usd: 0.5,
      }),
    ]);
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toBe("Spend limit $0.50 per run · Claude Code"));
    const inspector = () => screen.getByTestId("runson-inspector-spend-agent-claude");
    await waitFor(() => expect(within(inspector()).getByRole("button", { name: "No limit" })).toBeTruthy());
    expect((within(inspector()).getByLabelText("Spend limit per run") as HTMLInputElement).value).toBe("0.50");
  });

  it("an amount out of range is refused in words, with no write", async () => {
    width(1440);
    const sent = hub(step("spent").gets);
    render(<RunsOnCore />);
    await screen.findByTestId(ROW);
    pick(ROW);
    fireEvent.click(within(status()).getByRole("button", { name: "Spend" }));
    const engine = screen.getByTestId("runson-inspector-spend-agent-claude");
    fireEvent.change(within(engine).getByLabelText("Spend limit per run"), { target: { value: "0" } });
    fireEvent.click(within(engine).getByRole("button", { name: "Save" }));
    expect(within(engine).getByTestId("runson-agent-spend-invalid").textContent).toContain("More than $0, up to $1000");
    expect(sent).toEqual([]);
  });

  it("Codex says it cannot limit spend and reports no cost", async () => {
    width(1440);
    hub(recorded.codex.gets as Gets);
    render(<RunsOnCore />);
    await screen.findByTestId("runson-engine-agent-codex");
    pick("runson-engine-agent-codex");
    expect(within(status()).getByText("Openai")).toBeTruthy();
    fireEvent.click(within(status()).getByRole("button", { name: "Spend" }));
    const engine = screen.getByTestId("runson-inspector-spend-agent-codex");
    expect(within(engine).queryByLabelText("Spend limit per run")).toBeNull();
    expect(within(engine).getByTestId("runson-agent-no-limit-agent-codex").textContent).toBe("No spend limit in Codex");
    expect(within(engine).getByTestId("runson-agent-cost-agent-codex").textContent).toBe("Codex reports no cost");
  });

  it("a run that said it has no sign-in shows NOT SIGNED IN on the row", async () => {
    width(1440);
    hub(step("signedOut").gets);
    render(<RunsOnCore />);
    await screen.findByTestId(ROW);
    await waitFor(() => expect(screen.getByTestId("runson-engine-state-agent-claude").textContent).toBe("Not signed in"));
    expect(screen.getByTestId("runson-engine-state-agent-claude").getAttribute("data-tone")).not.toBe("ok");
  });
});

/* ── Betterment E3: the model picker, one engine for each model ── */

type ThreeStep = { name: string; gets?: Gets; post?: string; body?: Record<string, unknown>; answer?: unknown };
const THREE = (recorded as unknown as { threeModels: { steps: ThreeStep[] } }).threeModels.steps;
const three = (name: string) => THREE.find((s) => s.name === name)!;
const STUB_URL = "http://127.0.0.1:8099/v1";

/** The hub of `threeModels`: the Check answer, then one recorded define per model. */
function threeHub(check: unknown = three("check").answer) {
  let gets = three("open").gets!;
  const defined: Array<Record<string, unknown>> = [];
  vi.mocked(apiFetch).mockImplementation(async (path: string, init?: { method?: string; json?: unknown }) => {
    if (path === "/api/inference/assignments/editor") throw new Error("not recorded");
    if (init?.method === "POST" && path === "/api/setup/discover-models") return structuredClone(check) as never;
    if (init?.method === "POST") {
      const draft = ((init.json ?? {}) as { draft?: Record<string, unknown> }).draft ?? {};
      defined.push(draft);
      const next = three(String(draft.model));
      if (!next || path !== next.post) throw new Error(`unrecorded POST ${path} ${String(draft.model)}`);
      gets = next.gets!;
      return structuredClone(next.answer) as never;
    }
    return recordedGet(gets, String(path).split("?")[0]) as never;
  });
  return defined;
}

async function checkStub() {
  render(<RunsOnCore />);
  fireEvent.click(await screen.findByTestId("concierge-add-engine"));
  // Betterment E4: a server on his network is one of the five kinds.
  fireEvent.click(screen.getByTestId("runson-kind-lan"));
  fireEvent.change(screen.getByLabelText("Server address"), { target: { value: STUB_URL } });
  await act(async () => {
    fireEvent.click(screen.getByTestId("concierge-add-check"));
  });
  return screen.findByTestId("concierge-add-picker");
}

const row = (model: string) =>
  screen.getAllByTestId("concierge-add-pick").find((r) => r.getAttribute("data-model") === model)!;

describe("Engines — the model picker (Betterment E3)", () => {
  it.each([1440, 393])("at %i Check lists all three models, picks none, and two of them become two engines", async (px) => {
    width(px);
    const defined = threeHub();
    const picker = await checkStub();

    // All three, in the server's order; nothing is picked for him.
    expect(within(picker).getAllByTestId("concierge-add-pick").map((r) => r.getAttribute("data-model"))).toEqual([
      "alpha-7b", "beta-13b", "gamma-3b",
    ]);
    expect(within(picker).getAllByRole("button", { name: "Use" })).toHaveLength(3);
    expect(within(picker).queryByText("Added")).toBeNull();
    expect(defined).toEqual([]);
    // The context the server said it runs; a model that did not say shows none.
    expect(row("alpha-7b").textContent).toContain("49,152 tokens");
    expect(row("gamma-3b").textContent).not.toContain("Tokens");
    // Three models need no search field.
    expect(screen.queryByTestId("concierge-add-search")).toBeNull();

    await act(async () => {
      fireEvent.click(within(row("alpha-7b")).getByRole("button", { name: "Use" }));
    });
    await waitFor(() => expect(within(row("alpha-7b")).getByText("Added")).toBeTruthy());
    await act(async () => {
      fireEvent.click(within(row("gamma-3b")).getByRole("button", { name: "Use" }));
    });
    await waitFor(() => expect(within(row("gamma-3b")).getByText("Added")).toBeTruthy());

    // One engine for each model: the id is host + model, and the context goes with it.
    expect(defined).toEqual([
      expect.objectContaining({ profile_id: "engine-127-0-0-1-8099-alpha-7b", model: "alpha-7b", context_tokens: 49152, endpoint: STUB_URL }),
      expect.objectContaining({ profile_id: "engine-127-0-0-1-8099-gamma-3b", model: "gamma-3b", context_tokens: null, endpoint: STUB_URL }),
    ]);
    expect(within(row("beta-13b")).getByRole("button", { name: "Use" })).toBeTruthy();
    expect(screen.getByTestId("runson-receipt").textContent).toMatch(/^Added at \d\d:\d\d · gamma-3b · 127\.0\.0\.1:8099$/);
    // Both are in Your engines (Betterment E5: one list at both widths).
    const board = screen.getByTestId("runson-engines");
    expect(await within(board).findByTestId("runson-engine-engine-127-0-0-1-8099-alpha-7b")).toBeTruthy();
    expect(within(board).getByTestId("runson-engine-engine-127-0-0-1-8099-gamma-3b")).toBeTruthy();
  });

  it("a long list has a search field that narrows it", async () => {
    // The recorded answer with more names: the search is the face's own filter.
    const answer = structuredClone(three("check").answer) as { models: string[] };
    answer.models = [...answer.models, "delta-1b", "epsilon-2b", "zeta-4b", "eta-8b"];
    threeHub(answer);
    await checkStub();
    const search = within(screen.getByTestId("concierge-add-search")).getByLabelText("Find a model");
    fireEvent.change(search, { target: { value: "ETA" } });
    expect(screen.getAllByTestId("concierge-add-pick").map((r) => r.getAttribute("data-model"))).toEqual([
      "beta-13b", "zeta-4b", "eta-8b",
    ]);
    fireEvent.change(search, { target: { value: "nothing-like-this" } });
    expect(screen.queryAllByTestId("concierge-add-pick")).toHaveLength(0);
    expect(screen.getByTestId("concierge-add-no-match").textContent).toBe("No model matches");
  });
});

/* ── Betterment E4: Add an engine, by kind ── */

type OrStep = { name: string; gets?: Gets; post?: string; body?: Record<string, unknown>; answer?: unknown };
const OR = (recorded as unknown as { openRouter: { steps: OrStep[] } }).openRouter.steps;
const orStep = (name: string) => OR.find((s) => s.name === name)!;
const OPENROUTER = "https://openrouter.ai/api/v1";
const OR_KEY = "sk-or-stub-key";
const CHOSEN = "qwen/qwen3.5-35b-a3b";

/** The hub of `openRouter`: the open reads, the Check, and the recorded Use. */
function orHub() {
  const sent: Array<{ path: string; json: Record<string, unknown> }> = [];
  vi.mocked(apiFetch).mockImplementation(async (path: string, init?: { method?: string; json?: unknown }) => {
    // The list's Used for column reads the row editors on open; not recorded here.
    if (path === "/api/inference/assignments/editor") throw new Error("not recorded");
    if (init?.method === "POST") {
      const json = (init.json ?? {}) as Record<string, unknown>;
      sent.push({ path, json });
      if (path === "/api/setup/discover-models") return structuredClone(orStep("check").answer) as never;
      const draft = (json.draft ?? {}) as Record<string, unknown>;
      const next = orStep(String(draft.model));
      if (!next || path !== next.post) throw new Error(`unrecorded POST ${path}`);
      return structuredClone(next.answer) as never;
    }
    return recordedGet(orStep("open").gets!, String(path).split("?")[0]) as never;
  });
  return sent;
}

/** Count the presses he makes (a paste is not a press). */
function press(counter: { n: number }, el: HTMLElement) {
  counter.n += 1;
  fireEvent.click(el);
}

describe("Engines — Add an engine, by kind (Betterment E4)", () => {
  it.each([1440, 393])("at %i OpenRouter with a chosen model takes 5 presses and one paste, with no address typed", async (px) => {
    width(px);
    const sent = orHub();
    const presses = { n: 0 };
    render(<RunsOnCore />);

    press(presses, await screen.findByTestId("concierge-add-engine"));
    const kinds = screen.getByTestId("runson-add-kinds");
    expect(within(kinds).getAllByRole("button", { pressed: false }).map((b) => b.querySelector(".runson-kind-name")?.textContent))
      .toEqual(["An agent on this Mac", "A service", "A server on my network", "A model on this Mac", "Another HoldSpeak"]);
    press(presses, within(kinds).getByTestId("runson-kind-service"));
    expect(["OpenRouter", "OpenAI", "Anthropic", "Gemini"].map((name) => within(kinds).getByRole("button", { name }))).toHaveLength(4);
    press(presses, within(kinds).getByRole("button", { name: "OpenRouter" }));

    // No address to know: the tile carries it, and the chip names the host.
    expect(screen.queryByLabelText("Server address")).toBeNull();
    expect(screen.queryByTestId("concierge-add-my-server")).toBeNull();
    expect(within(screen.getByTestId("concierge-add-egress")).getByText("OPENROUTER.AI")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("OpenRouter key"), { target: { value: OR_KEY } });
    await act(async () => {
      press(presses, screen.getByTestId("concierge-add-check"));
    });
    expect(sent[0]).toEqual({ path: "/api/setup/discover-models", json: { base_url: OPENROUTER, api_key: OR_KEY, check_tools: true } });

    // The catalog presets the service serves are on top, with their short name.
    const picker = await screen.findByTestId("concierge-add-picker");
    const rows = within(picker).getAllByTestId("concierge-add-pick");
    expect(rows.map((r) => r.getAttribute("data-model"))).toEqual(["qwen/qwen3-8b", CHOSEN, "anthropic/claude-x"]);
    expect(rows.map((r) => r.hasAttribute("data-preset"))).toEqual([true, true, false]);
    expect(rows[1].textContent).toContain("Balanced Qwen");
    expect(within(picker).queryByText("Added")).toBeNull();

    await act(async () => {
      press(presses, within(rows[1]).getByRole("button", { name: "Use" }));
    });
    await waitFor(() => expect(within(row(CHOSEN)).getByText("Added")).toBeTruthy());
    expect(presses.n).toBe(5);
    expect(sent[1].path).toBe("/api/inference/model-library/define-endpoint");
    expect(sent[1].json).toEqual({
      draft: expect.objectContaining({
        profile_id: "engine-openrouter-ai-qwen-qwen3-5-35b-a3b", label: "OpenRouter", provider_family: "openai_compatible",
        model: CHOSEN, endpoint: OPENROUTER, requires_key: true, context_tokens: 262144,
      }),
      secret: { value: OR_KEY },
    });
    // The draft the hub recorded for this Use, but for its request id.
    const { request_id: _id, ...recordedDraft } = orStep(CHOSEN).body!;
    expect(sent[1].json.draft).toMatchObject(recordedDraft);
    expect(screen.getByTestId("runson-receipt").textContent).toMatch(/^Added at \d\d:\d\d · qwen\/qwen3\.5-35b-a3b · openrouter\.ai$/);
  });

  it("Anthropic is a working service tile, never a NOT SUPPORTED YET dead end", async () => {
    width(1440);
    const sent = orHub();
    render(<RunsOnCore />);
    fireEvent.click(await screen.findByTestId("concierge-add-engine"));
    fireEvent.click(screen.getByTestId("runson-kind-service"));
    fireEvent.click(screen.getByRole("button", { name: "Anthropic" }));
    expect(within(screen.getByTestId("concierge-add-egress")).getByText("API.ANTHROPIC.COM")).toBeTruthy();
    expect(screen.getByLabelText("Anthropic key")).toBeTruthy();
    expect(screen.getByTestId("runson-root").textContent).not.toMatch(/NOT SUPPORTED/);
    fireEvent.change(screen.getByLabelText("Anthropic key"), { target: { value: "sk-ant" } });
    await act(async () => {
      fireEvent.click(screen.getByTestId("concierge-add-check"));
    });
    expect(sent[0].json).toMatchObject({ base_url: "https://api.anthropic.com/v1", api_key: "sk-ant" });
  });

  it("an agent on this Mac: Add for the one found, one install line for the one missing", async () => {
    width(1440);
    const sent = hub(step("found").gets, { add: step("add") });
    render(<RunsOnCore />);
    fireEvent.click(await screen.findByTestId("concierge-add-engine"));
    fireEvent.click(screen.getByTestId("runson-kind-agent"));
    const codex = screen.getByTestId("runson-agent-tile-codex");
    expect(within(codex).getByTestId("runson-agent-install-codex").textContent).toBe("npm install -g @openai/codex");
    expect(within(codex).queryByRole("button")).toBeNull();
    const claude = screen.getByTestId("runson-agent-tile-claude");
    expect(within(claude).getByText("ANTHROPIC")).toBeTruthy();
    await act(async () => {
      fireEvent.click(within(claude).getByRole("button", { name: "Add" }));
    });
    expect(sent).toEqual([expect.objectContaining({ preset: "claude", profile_id: "agent-claude" })]);
  });

  it("a server on my network keeps the address row and Find on LAN; Close folds the kinds away", async () => {
    width(1440);
    orHub();
    render(<RunsOnCore />);
    fireEvent.click(await screen.findByTestId("concierge-add-engine"));
    fireEvent.click(screen.getByTestId("runson-kind-lan"));
    expect(screen.getByLabelText("Server address")).toBeTruthy();
    expect(within(screen.getByTestId("runson-add-kinds")).getByTestId("runson-kind-find-lan")).toBeTruthy();
    fireEvent.click(screen.getByTestId("runson-kind-local"));
    expect(screen.getByTestId("runson-local-models")).toBeTruthy();
    fireEvent.click(screen.getByTestId("runson-add-close"));
    expect(screen.queryByTestId("runson-add-kinds")).toBeNull();
    expect(screen.getByTestId("concierge-add-engine")).toBeTruthy();
  });
});

/* ── Betterment E5: What runs where ── */

import { WHAT_ROWS } from "../whatRows";

type WhatStep = { name: string; gets?: Gets; editors?: Record<string, unknown>; post?: string; body?: Record<string, unknown>; answer?: unknown };
const WHAT = (recorded as unknown as { whatRunsWhere: { steps: WhatStep[] } }).whatRunsWhere.steps;
const whatStep = (name: string) => WHAT.find((s) => s.name === name)!;
const rowOfScope = (scope: unknown) => WHAT_ROWS.find((r) => JSON.stringify(r.scope) === JSON.stringify(scope))!;

/** The hub of `whatRunsWhere`: reads and editor answers of the current step;
 *  a set moves to the step recorded for that row. */
function whatHub() {
  let at = whatStep("open");
  const sent: Array<{ path: string; json: Record<string, unknown> }> = [];
  vi.mocked(apiFetch).mockImplementation(async (path: string, init?: { method?: string; json?: unknown }) => {
    const json = (init?.json ?? {}) as Record<string, unknown>;
    if (path === "/api/inference/assignments/editor") return structuredClone(at.editors![rowOfScope(json.scope).id]) as never;
    if (init?.method === "POST") {
      sent.push({ path, json });
      if (path === "/api/concierge/probe") return structuredClone(whatStep("tryAnswers").answer) as never;
      const next = whatStep(rowOfScope(json.scope).id);
      if (!next || path !== next.post) throw new Error(`unrecorded POST ${path}`);
      at = next;
      return structuredClone(next.answer) as never;
    }
    return recordedGet(at.gets!, String(path).split("?")[0]) as never;
  });
  return sent;
}

const whatRow = (id: string) => screen.getByTestId(`runson-what-${id}`);

describe("Engines — What runs where (Betterment E5)", () => {
  it.each([1440, 393])("at %i Meeting summaries and Answers each take 2 presses; an inheriting row reads Everything else", async (px) => {
    width(px);
    const sent = whatHub();
    render(<RunsOnCore />);
    await screen.findByTestId("runson-what");
    // The drag switchboard is parked behind Builder tools.
    expect(screen.queryByTestId("runson-assignments")).toBeNull();
    await waitFor(() => expect(within(whatRow("summaries")).getByTestId("runson-what-pick-summaries").textContent).toContain("Everything else"));
    expect(within(whatRow("automations")).getByTestId("runson-what-pick-automations").textContent).toContain("Everything else");

    // Meeting summaries → the stub server: two presses.
    fireEvent.click(within(whatRow("summaries")).getByTestId("runson-what-pick-summaries"));
    await act(async () => {
      fireEvent.click(within(whatRow("summaries")).getByTestId("runson-what-option-summaries-engine-stub"));
    });
    expect(sent[0]).toEqual({ path: "/api/inference/assignments/set", json: expect.objectContaining({
      scope: { kind: "capability", capability_id: "meeting.deferred_analysis" },
      expected_revision: 0,
      entries: [{ profile_id: "engine-stub", profile_revision: 1 }],
    }) });
    await waitFor(() => expect(within(whatRow("summaries")).getByTestId("runson-what-pick-summaries").textContent).not.toContain("Everything else"));
    expect(screen.getByTestId("runson-receipt").textContent).toMatch(/^Set at \d\d:\d\d · Meeting summaries → stub fallback$/);

    // Answers → Claude Code: two presses.
    fireEvent.click(within(whatRow("answers")).getByTestId("runson-what-pick-answers"));
    await act(async () => {
      fireEvent.click(within(whatRow("answers")).getByTestId("runson-what-option-answers-agent-claude"));
    });
    expect(sent[1].json).toMatchObject({ scope: { kind: "capability", capability_id: "ask.answer" }, entries: [{ profile_id: "agent-claude", profile_revision: 1 }] });
    await waitFor(() => expect(within(whatRow("answers")).getByTestId("runson-what-pick-answers").textContent).toContain("Claude Code"));
    expect(within(whatRow("answers")).getByText("Anthropic")).toBeTruthy();
    expect(screen.getByTestId("runson-undo")).toBeTruthy();
  });

  it("Speech to text lists no agent and no chat server; Everything else lists no speech engine", async () => {
    width(1440);
    whatHub();
    render(<RunsOnCore />);
    await screen.findByTestId("runson-what");
    fireEvent.click(await screen.findByTestId("runson-what-more"));
    await waitFor(() => expect(within(whatRow("speech")).getByTestId("runson-what-pick-speech").hasAttribute("disabled")).toBe(false));
    fireEvent.click(within(whatRow("speech")).getByTestId("runson-what-pick-speech"));
    const options = within(whatRow("speech")).getByTestId("runson-what-options-speech");
    expect(within(options).queryByTestId("runson-what-option-speech-agent-claude")).toBeNull();
    expect(within(options).queryByTestId("runson-what-option-speech-engine-stub")).toBeNull();
    // Betterment setup ST1: speech never follows Everything else (the hub
    // reads no_assignment), so its clear option does not say it does.
    expect(within(options).getByTestId("runson-what-option-speech-default").textContent).toBe("No engine");
    expect(within(options).queryByText("Everything else")).toBeNull();
    fireEvent.click(within(whatRow("default")).getByTestId("runson-what-pick-default"));
    const defaults = within(whatRow("default")).getByTestId("runson-what-options-default");
    expect(within(defaults).getAllByRole("button").map((b) => b.getAttribute("data-testid"))).toEqual([
      "runson-what-option-default-agent-claude", "runson-what-option-default-engine-stub",
    ]);
  });

  it("Try it under Answers shows the answer in words under the row", async () => {
    width(1440);
    const sent = whatHub();
    render(<RunsOnCore />);
    await screen.findByTestId("runson-what");
    fireEvent.click(await within(whatRow("answers")).findByTestId("runson-what-pick-answers"));
    await act(async () => {
      fireEvent.click(within(whatRow("answers")).getByTestId("runson-what-option-answers-agent-claude"));
    });
    await waitFor(() => expect(within(whatRow("answers")).getByTestId("runson-what-pick-answers").textContent).toContain("Claude Code"));
    await act(async () => {
      fireEvent.click(within(whatRow("answers")).getByTestId("runson-what-try-answers"));
    });
    const probe = sent.find((s) => s.path === "/api/concierge/probe")!;
    expect(probe.json).toMatchObject({ task: true, capabilityId: "ask.answer", confirmOffMachine: true, expectedProfileIds: ["agent-claude"] });
    await waitFor(() => expect(screen.getByTestId("runson-what-state-answers").textContent).toMatch(/^Completed · /));
    expect(screen.getByTestId("runson-what-output-answers").textContent).toBeTruthy();
  });

  it("Try it runs each row's own sample: Automations, Live meeting notes and Thread have one; Thoughts, Drafts and Speech have none", async () => {
    width(1440);
    const sent = whatHub();
    render(<RunsOnCore />);
    await screen.findByTestId("runson-what");
    fireEvent.click(await screen.findByTestId("runson-what-more"));
    await waitFor(() => expect(within(whatRow("automations")).getByTestId("runson-what-try-automations")).toBeTruthy());
    for (const id of ["live", "thread"]) expect(within(whatRow(id)).getByTestId(`runson-what-try-${id}`)).toBeTruthy();
    for (const id of ["thoughts", "drafts", "speech"]) expect(within(whatRow(id)).queryByTestId(`runson-what-try-${id}`)).toBeNull();
    for (const [id, capability] of [["automations", "workbench.item"], ["live", "meeting.live_analysis"], ["thread", "chat.turn"]]) {
      await act(async () => {
        fireEvent.click(within(whatRow(id)).getByTestId(`runson-what-try-${id}`));
      });
      expect(sent.filter((s) => s.path === "/api/concierge/probe").pop()!.json).toMatchObject({ task: true, capabilityId: capability });
      await waitFor(() => expect(screen.getByTestId(`runson-what-state-${id}`).textContent).toMatch(/^Completed · /));
    }
  });

  it("Undo in the foot writes the row back", async () => {
    width(1440);
    const sent = whatHub();
    render(<RunsOnCore />);
    await screen.findByTestId("runson-what");
    fireEvent.click(await within(whatRow("summaries")).findByTestId("runson-what-pick-summaries"));
    await act(async () => {
      fireEvent.click(within(whatRow("summaries")).getByTestId("runson-what-option-summaries-engine-stub"));
    });
    // The recorded hub has no Undo answer: the clear it sends is the proof.
    vi.mocked(apiFetch).mockImplementationOnce(async (path: string, init?: { json?: unknown }) => {
      sent.push({ path, json: (init?.json ?? {}) as Record<string, unknown> });
      return { revision: 2 } as never;
    });
    await act(async () => {
      fireEvent.click(screen.getByTestId("runson-undo"));
    });
    expect(sent[sent.length - 1]).toEqual({ path: "/api/inference/assignments/clear", json: expect.objectContaining({
      scope: { kind: "capability", capability_id: "meeting.deferred_analysis" },
      capability_id: "meeting.deferred_analysis",
      expected_revision: 1,
    }) });
  });
});
