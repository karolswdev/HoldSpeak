// PHILO-14 A5 (Astra r2 on #935): the shade is an approval surface too. It
// shows the held command before any decision; a call the hub cannot show
// whole (the 198-char producer case, `db.gate.command_view`) reads
// `<head>… +90 CHARS` and offers Deny only, never Approve.
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SystemShade } from "../SystemShade";

const { CUT_HEAD } = vi.hoisted(() => ({ CUT_HEAD: "psql -h staging-ledger -U ops -d payments -c 'select count(*) from entries where ledger_id = 777777777777777" }));

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
        args_head: `{"command":"${CUT_HEAD}`,
        args_shown: CUT_HEAD,
        args_cut: true,
        args_hidden: 90,
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

describe("SystemShade: a cut held call (PHILO-14 A5)", () => {
  it("shows the command with `… +90 CHARS` and offers Deny only", () => {
    render(<SystemShade open onClose={vi.fn()} onOpenMemory={vi.fn()} />);
    expect(screen.getByTestId("shade-gate-command").textContent).toBe(`${CUT_HEAD}… +90 CHARS`);
    expect(screen.queryByRole("button", { name: "Approve" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Deny" }));
    fireEvent.click(screen.getByRole("button", { name: "Send deny" }));
    expect(decide).toHaveBeenCalledWith("toolu_1", "denied", "");
  });
});
