// HS-100-09 — agents open on who needs you: blocked sessions render FIRST
// with an Answer verb; running follow; the canon word is agents.
// PHILO-14 C4: re-anchored. The Agents application (CompanionCore) is
// PARKED; agents live in the Conductor drawer, so these locked semantics
// are proved on the Conductor window: blocked-before-running, the Answer
// verb, and "Personas" never returns.
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ConductorWindow } from "../../../desk/conductor/ConductorWindow";
import { __resetConductor } from "../../../desk/conductor/store";
import { useAgentFlights } from "../../../desk/agentFlights";
import { openCoderSession } from "../../../desk/shell";

vi.mock("../../../lib/api", async (importOriginal) => {
  const mod = (await importOriginal()) as Record<string, unknown>;
  return {
    ...mod,
    apiFetch: vi.fn(async (url: string) => {
      if (url === "/api/onboarding/agents") return { agents: [], tmux: { installed: true, path: null, install_hint: null } };
      // Conductor F2: the roster reads every live session (the sessions route).
      if (url === "/api/coders/sessions?include_ended=false")
        return {
          sessions: [
            {
              session: {
                agent: "claude",
                session_id: "run-1",
                project_name: "holdspeak-mobile",
                state: "working",
                awaiting_response: false,
              },
            },
            {
              session: {
                agent: "claude",
                session_id: "blocked-1",
                project_name: "holdspeak",
                state: "waiting",
                awaiting_response: true,
                question: "Regenerate the schema snapshot?",
              },
            },
          ],
          flights: [],
        };
      return {};
    }),
  };
});

vi.mock("../../../desk/shell", async (importOriginal) => ({
  ...((await importOriginal()) as Record<string, unknown>),
  openCoderSession: vi.fn(),
  openAgentLane: vi.fn(),
}));
vi.mock("../../../runtime/RuntimeBus", () => {
  const value = { state: "connected", lastFrame: null, subscribe: () => () => undefined };
  return { useRuntimeBus: () => value, useOptionalRuntimeBus: () => value, useRuntimeFrame: () => null };
});

beforeEach(() => {
  __resetConductor();
  useAgentFlights.setState({ sessions: [], flights: [], loaded: false });
});

describe("Agents in the Conductor (HS-100-09, re-anchored by PHILO-14 C4)", () => {
  it("renders blocked sessions before running, with the Answer verb", async () => {
    render(<ConductorWindow />);
    const blocked = await screen.findByRole("button", { name: /^Claude Code: holdspeak, AGENT, ASKS/ });
    const running = screen.getByRole("button", { name: /^Claude Code: holdspeak-mobile, AGENT, WORKS/ });
    // Blocked-first is the pinned ordering contract.
    expect(blocked.compareDocumentPosition(running) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    // The blocked agent's verb is Answer: it opens the session's answer well.
    fireEvent.click(blocked);
    fireEvent.click(screen.getByRole("button", { name: "Answer" }));
    expect(openCoderSession).toHaveBeenCalledWith("claude:blocked-1", { answer: true });
    // The head counts honestly: one at work, one asks.
    const head = screen.getByTestId("conductor-head").textContent ?? "";
    expect(head).toContain("1 AT WORK");
    expect(head).toContain("1 ASK");
  });

  it("never says Personas", async () => {
    const { container } = render(<ConductorWindow />);
    await screen.findByRole("button", { name: /^Claude Code: holdspeak, AGENT/ });
    expect(container.textContent).not.toMatch(/personas?/i);
  });
});
