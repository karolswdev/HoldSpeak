// HS-104-02 — held tool calls on the shade: the redacted preview,
// Approve and Deny verbs, the deny reason edited in place (no modal).
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SystemShade } from "../SystemShade";

const { decide } = vi.hoisted(() => ({
  decide: vi.fn().mockResolvedValue(undefined),
}));

vi.mock("../../gate", async (importOriginal) => {
  const original = await importOriginal<typeof import("../../gate")>();
  const state = {
    held: [
      {
        id: "toolu_1",
        session_key: "claude:s1",
        agent: "claude",
        tool: "Bash",
        args_sha256: "a".repeat(64),
        args_head: '{"command":"rm -rf build"}',
        cwd: "/tmp/repo",
        created_at: Date.now() / 1000 - 12,
        expires_at: Date.now() / 1000 + 200,
        state: "held",
        decided_by: null,
        decided_at: null,
        reason: null,
      },
    ],
    loaded: true,
    error: null,
    refresh: vi.fn().mockResolvedValue(undefined),
    decide,
  };
  const useGate = Object.assign(() => state, {
    getState: () => state,
  });
  return { ...original, useGate };
});

vi.mock("../../projections", () => ({
  useProjections: () => ({
    projections: [],
    counts: { needs_attention: 0, receipts: 0 },
    refresh: vi.fn().mockResolvedValue(undefined),
    present: vi.fn(),
  }),
}));

vi.mock("../../../lib/api", () => ({
  apiFetch: vi.fn().mockResolvedValue({ items: [] }),
}));

describe("SystemShade gate cards (HS-104-02)", () => {
  it("renders the held call with its redacted preview and Approve lands the decision", () => {
    render(<SystemShade open onClose={vi.fn()} onOpenMemory={vi.fn()} />);
    expect(screen.getByText("Bash held · claude:s1")).toBeTruthy();
    expect(screen.getByText('{"command":"rm -rf build"}')).toBeTruthy();
    expect(screen.queryByText("Nothing needs you")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Approve" }));
    expect(decide).toHaveBeenCalledWith("toolu_1", "approved");
  });

  it("Deny reveals the in-place reason line and sends it verbatim", () => {
    render(<SystemShade open onClose={vi.fn()} onOpenMemory={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: "Deny" }));
    const input = screen.getByPlaceholderText("Reason for the agent, one line");
    fireEvent.change(input, { target: { value: "use the staging bucket" } });
    fireEvent.click(screen.getByRole("button", { name: "Send deny" }));
    expect(decide).toHaveBeenCalledWith("toolu_1", "denied", "use the staging bucket");
  });
});
