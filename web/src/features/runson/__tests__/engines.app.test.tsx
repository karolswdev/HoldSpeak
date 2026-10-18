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

const PLATE = "switchboard-engine-agent-claude";

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
    expect(within(found).getByTestId("switchboard-found-cap").textContent).toBe("Found on this Mac · 1");
    const plate = within(found).getByTestId("switchboard-engine-agent:found:claude");
    expect(within(plate).getByText("Claude Code · signed in")).toBeTruthy();
    expect(plate.querySelector(".switchboard-emblem")?.textContent).toBe("CLI");
    expect(within(plate).getByText("ANTHROPIC")).toBeTruthy();

    await act(async () => {
      fireEvent.click(within(plate).getByRole("button", { name: "Add" }));
    });
    expect(sent).toHaveLength(1);
    expect(sent[0]).toMatchObject({ preset: "claude", profile_id: "agent-claude", expected_profile_revision: 0 });
    expect(sent[0]).not.toHaveProperty("spend_limit_usd");

    await waitFor(() => expect(screen.queryByTestId("runson-found-engines")).toBeNull());
    const engine = await within(screen.getByTestId("runson-assignments")).findByTestId(PLATE);
    expect(within(engine).getByText("Claude Code")).toBeTruthy();
    expect(within(engine).getByTestId("switchboard-lamp-agent-claude").getAttribute("data-lamp")).toBe("ok");
    expect(within(engine).getByText("ANTHROPIC")).toBeTruthy();
    expect(engine.textContent).not.toContain("NOT SIGNED IN");
    expect(screen.getByTestId("runson-receipt").textContent).toMatch(/^ADDED \d\d:\d\d · Claude Code$/);
  });

  it("with no agent CLI on this Mac the section is absent", async () => {
    hub(recorded.nothingFound.gets as Gets);
    render(<RunsOnCore />);
    await waitFor(() => expect(screen.getByTestId("runson-root").getAttribute("aria-busy")).toBeNull());
    expect(screen.queryByTestId("runson-found-engines")).toBeNull();
    expect(screen.queryByText(/Found on this Mac/)).toBeNull();
  });
});

describe("Engines — an agent engine's Spend limit per run (Betterment E2)", () => {
  it("unfolds to No limit and the week's cost; Save sends the limit and the row shows it", async () => {
    width(1440);
    const sent = hub(step("spent").gets, { limit: step("limit") });
    render(<RunsOnCore />);
    const engine = await screen.findByTestId(PLATE);
    fireEvent.click(within(engine).getByRole("button", { name: "Spend" }));

    const detail = within(engine).getByTestId("switchboard-detail-agent-claude");
    const field = within(detail).getByLabelText("Spend limit per run") as HTMLInputElement;
    expect(field.value).toBe("");
    expect(field.placeholder).toBe("No limit");
    expect(within(detail).getByTestId("runson-agent-cost-agent-claude").textContent).toBe("TODAY $0.02 · THIS WEEK $0.02");
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
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toBe("SPEND LIMIT $0.50 PER RUN · Claude Code"));
    await waitFor(() => expect(within(screen.getByTestId(PLATE)).getByRole("button", { name: "No limit" })).toBeTruthy());
    expect((within(screen.getByTestId(PLATE)).getByLabelText("Spend limit per run") as HTMLInputElement).value).toBe("0.50");
  });

  it("an amount out of range is refused in words, with no write", async () => {
    width(1440);
    const sent = hub(step("spent").gets);
    render(<RunsOnCore />);
    const engine = await screen.findByTestId(PLATE);
    fireEvent.click(within(engine).getByRole("button", { name: "Spend" }));
    fireEvent.change(within(engine).getByLabelText("Spend limit per run"), { target: { value: "0" } });
    fireEvent.click(within(engine).getByRole("button", { name: "Save" }));
    expect(within(engine).getByTestId("runson-agent-spend-invalid").textContent).toContain("MORE THAN $0, UP TO $1000");
    expect(sent).toEqual([]);
  });

  it("Codex says it cannot limit spend and reports no cost", async () => {
    width(1440);
    hub(recorded.codex.gets as Gets);
    render(<RunsOnCore />);
    const engine = await screen.findByTestId("switchboard-engine-agent-codex");
    expect(within(engine).getByText("OPENAI")).toBeTruthy();
    fireEvent.click(within(engine).getByRole("button", { name: "Spend" }));
    expect(within(engine).queryByLabelText("Spend limit per run")).toBeNull();
    expect(within(engine).getByTestId("runson-agent-no-limit-agent-codex").textContent).toBe("CODEX CAN'T LIMIT SPEND");
    expect(within(engine).getByTestId("runson-agent-cost-agent-codex").textContent).toBe("CODEX REPORTS NO COST");
  });

  it("a run that said it has no sign-in shows NOT SIGNED IN on the row", async () => {
    width(1440);
    hub(step("signedOut").gets);
    render(<RunsOnCore />);
    const engine = await screen.findByTestId(PLATE);
    await waitFor(() => expect(engine.textContent).toContain("NOT SIGNED IN"));
    expect(within(engine).getByTestId("switchboard-lamp-agent-claude").getAttribute("data-lamp")).not.toBe("ok");
  });
});
