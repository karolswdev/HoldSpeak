/* The first-run Agents card (the Conductor canvas K1a/K1b/K1c), with the
 * hub faked in the shape of the K1 onboarding routes
 * (GET /api/onboarding/agents, POST /api/onboarding/agents/use). */
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));

vi.mock("../../../lib/api", async (importOriginal) => ({
  ApiError: (await importOriginal<typeof import("../../../lib/api")>()).ApiError,
  apiFetch: mocks.apiFetch,
  readableError: (error: unknown) => (error instanceof Error ? error.message : "Request failed"),
}));

import { ApiError } from "../../../lib/api";
import { AgentsCard, codeWords } from "../AgentsCard";
import { useAgentsStep, type AgentRow, type AgentsDetect } from "../agentsStep";

function agent(id: "claude" | "codex", patch: Partial<AgentRow> = {}): AgentRow {
  return {
    id,
    label: id === "claude" ? "Claude Code" : "Codex",
    installed: true,
    path: `/opt/bin/${id}`,
    version: id === "claude" ? "2.1.4" : "0.46.0",
    hooks: "missing",
    signed_in: "yes",
    ready: false,
    verb: "Use it",
    ...patch,
  };
}

function detect(agents: AgentRow[], tmux = true): AgentsDetect {
  return {
    agents,
    tmux: { installed: tmux, path: tmux ? "/opt/bin/tmux" : null, version: tmux ? "3.5a" : null, install_hint: tmux ? null : "brew install tmux" },
  };
}

function Harness() {
  const step = useAgentsStep();
  return <AgentsCard step={step} lit={false} />;
}

let state: AgentsDetect;

beforeEach(() => {
  mocks.apiFetch.mockReset();
  mocks.apiFetch.mockImplementation(async (path: string, init?: { method?: string; json?: { agent: string } }) => {
    if (path === "/api/onboarding/agents") return state;
    if (path === "/api/onboarding/agents/use" && init?.method === "POST") {
      const id = init.json?.agent;
      state = { ...state, agents: state.agents.map((row) => (row.id === id ? { ...row, hooks: "installed", ready: true } : row)) };
      return { operation_id: `op-${id}`, receipt: { state: "succeeded" } };
    }
    throw new Error(`unexpected ${path}`);
  });
});

afterEach(cleanup);

describe("the Agents card", () => {
  it("K1a: rows with the version and the three lamps, a tmux row, one Install hooks on THIS DEVICE", async () => {
    state = detect([agent("claude"), agent("codex")]);
    render(<Harness />);
    const card = await screen.findByTestId("firstrun-agents");
    await within(card).findByText("2 FOUND");
    const claude = within(card).getAllByTestId("firstrun-agent-row").find((r) => r.dataset.agent === "claude")!;
    expect(claude.textContent).toContain("CLAUDE 2.1.4");
    expect(within(claude).getByRole("status", { name: "INSTALLED" })).toBeTruthy();
    expect(within(claude).getByRole("status", { name: "SIGNED IN" })).toBeTruthy();
    expect(within(claude).getByRole("status", { name: "HOOKS" }).getAttribute("data-state")).toBe("idle");
    const tmux = within(card).getAllByTestId("firstrun-agent-row").find((r) => r.dataset.agent === "tmux")!;
    expect(tmux.textContent).toContain("TMUX 3.5A");
    expect(within(card).getByText("THIS DEVICE")).toBeTruthy();
    expect(within(card).getByRole("button", { name: "Install hooks: Claude Code and Codex" })).toBeTruthy();
    expect(within(card).queryByText("Check again")).toBeNull();
  });

  it("unknown sign-in is its own token, never a false no; broken hooks show as broken", async () => {
    state = detect([agent("claude", { signed_in: "unknown", hooks: "broken" }), agent("codex", { hooks: "installed", ready: true })]);
    render(<Harness />);
    const card = await screen.findByTestId("firstrun-agents");
    await within(card).findByText("SIGN-IN UNKNOWN");
    expect(within(card).getByRole("status", { name: "HOOKS BROKEN" }).getAttribute("data-state")).toBe("failure");
    // Only the agent that lacks its hooks is installed by the press.
    expect(within(card).getByRole("button", { name: "Install hooks: Claude Code" })).toBeTruthy();
  });

  it("K1b: Install hooks runs the admitted install per agent, reads again, and folds to the receipt", async () => {
    state = detect([agent("claude"), agent("codex")]);
    render(<Harness />);
    const card = await screen.findByTestId("firstrun-agents");
    fireEvent.click(await within(card).findByRole("button", { name: /^Install hooks/ }));
    await within(card).findByTestId("firstrun-agents-receipt");
    const posts = mocks.apiFetch.mock.calls.filter(([, init]) => init?.method === "POST").map(([, init]) => init.json.agent);
    expect(posts).toEqual(["claude", "codex"]);
    expect(within(card).getByText("2 AGENTS READY")).toBeTruthy();
    const receipt = within(card).getByTestId("firstrun-agents-receipt").textContent ?? "";
    expect(receipt).toContain("CLAUDE CODE · HOOKS IN");
    expect(receipt).toContain("CODEX · HOOKS IN");
    expect(receipt).toContain("TMUX 3.5A");
    expect(within(card).queryByTestId("firstrun-agent-row")).toBeNull();
  });

  it("a refused install is a named token (no prose), and the rows stay", async () => {
    state = detect([agent("claude")]);
    mocks.apiFetch.mockImplementation(async (path: string, init?: { method?: string }) => {
      if (path === "/api/onboarding/agents") return state;
      if (init?.method === "POST") throw new ApiError(409, "x", { code: "agent_settings_unreadable", operation_id: "op-1" });
      throw new Error(path);
    });
    render(<Harness />);
    const card = await screen.findByTestId("firstrun-agents");
    fireEvent.click(await within(card).findByRole("button", { name: /^Install hooks/ }));
    const refused = await within(card).findByTestId("firstrun-agents-refused");
    expect(refused.textContent).toContain("HOOKS NOT IN");
    expect(refused.textContent).toContain("CLAUDE CODE · AGENT SETTINGS UNREADABLE");
    expect(refused.textContent).not.toContain("_");
  });

  it("K1c: nothing installed: NOT INSTALLED tokens, Copy install per agent, Check again reads again", async () => {
    state = detect([agent("claude", { installed: false, path: null, verb: null }), agent("codex", { installed: false, path: null, verb: null })], false);
    const writeText = vi.fn(async () => undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    render(<Harness />);
    const card = await screen.findByTestId("firstrun-agents");
    await within(card).findByText("NO AGENT FOUND");
    expect(within(card).getByText("CLAUDE NOT INSTALLED")).toBeTruthy();
    expect(within(card).getByText("CODEX NOT INSTALLED")).toBeTruthy();
    expect(within(card).getByText("TMUX NOT INSTALLED")).toBeTruthy();
    expect(within(card).queryByText("Install hooks")).toBeNull();
    fireEvent.click(within(card).getByRole("button", { name: "Copy install: Claude Code" }));
    await waitFor(() => expect(writeText).toHaveBeenCalledWith("npm install -g @anthropic-ai/claude-code"));
    const reads = mocks.apiFetch.mock.calls.length;
    fireEvent.click(within(card).getByTestId("firstrun-agents-check"));
    await waitFor(() => expect(mocks.apiFetch.mock.calls.length).toBe(reads + 1));
  });

  it("codeWords never leaves snake_case on a face", () => {
    expect(codeWords("agent_settings_path_changed")).toBe("AGENT SETTINGS PATH CHANGED");
  });
});
