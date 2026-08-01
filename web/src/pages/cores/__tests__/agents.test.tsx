// HS-100-09 — Agents opens on who needs you: blocked sessions render
// FIRST with an Answer verb; running follow; the canon word is agents.
// HS-111-04 — the surface is the crew board (one SurfaceLedger); the
// locked semantics survive the rerender: blocked-before-running, the
// Answer verb, and "Personas" never returns.
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

describe("Agents (HS-100-09 / HS-111-04)", () => {
  it("renders blocked sessions before running, with the Answer verb", async () => {
    render(<CompanionCore />);
    const blockedRow = await screen.findByText("holdspeak");
    const runningRow = screen.getByText("holdspeak-mobile");
    // Blocked-first is the pinned ordering contract.
    expect(
      blockedRow.compareDocumentPosition(runningRow) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    // The blocked row opens in place with its question and the Answer verb.
    expect(
      screen.getByText("Regenerate the schema snapshot?", {
        selector: "pre",
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Answer" })).toBeInTheDocument();
    // The board head counts the crew honestly.
    expect(
      screen.getByText("CREW 1 · SESSIONS 2 · BLOCKED 1"),
    ).toBeInTheDocument();
  });

  it("never says Personas", async () => {
    const { container } = render(<CompanionCore />);
    await screen.findByText("holdspeak");
    expect(container.textContent).not.toMatch(/personas?/i);
  });
});
