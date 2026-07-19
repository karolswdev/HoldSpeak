// HS-100-09 — Agents opens on who needs you: blocked sessions render
// FIRST with an Answer verb; running follow; the canon word is agents.
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CompanionCore } from "../CompanionCore";

vi.mock("../../../lib/api", async (importOriginal) => {
  const mod = (await importOriginal()) as Record<string, unknown>;
  return {
    ...mod,
    apiFetch: vi.fn(async (url: string) => {
      if (url === "/api/recipes")
        return { recipes: [{ id: "r1", name: "Summarize like a PM" }] };
      if (url === "/api/coders/status")
        return {
          agent: {
            sessions: [
              {
                key: "claude:run-1",
                session: {
                  session_id: "run-1",
                  project: "holdspeak-mobile",
                  awaiting_response: false,
                },
              },
              {
                key: "claude:blocked-1",
                session: {
                  session_id: "blocked-1",
                  project: "holdspeak",
                  awaiting_response: true,
                  question: "Regenerate the schema snapshot?",
                },
              },
            ],
          },
        };
      return {};
    }),
  };
});

vi.mock("../../../desk/shell", () => ({
  openCoderSession: vi.fn(),
  openPersona: vi.fn(),
}));

describe("Agents (HS-100-09)", () => {
  it("renders blocked sessions before running, with the Answer verb", async () => {
    render(<CompanionCore />);
    const blockedHead = await screen.findByText("Blocked — needs your answer");
    await screen.findByText("holdspeak");
    const runningHead = screen.getByRole("heading", { name: "Running" });
    expect(
      blockedHead.compareDocumentPosition(runningHead) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(screen.getByRole("button", { name: "Answer" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Watch" })).toBeInTheDocument();
  });

  it("never says Personas", async () => {
    const { container } = render(<CompanionCore />);
    await screen.findByText("Blocked — needs your answer");
    expect(container.textContent).not.toMatch(/personas?/i);
  });
});
