// Needs you and the system shade on the hub's OWN answers (the test diet,
// 2026-10-11). The answers under ./wire were captured on a real hub where an
// agent's own credential held two calls outside its worktree through the real
// gate route (`ls /etc`, and a 198-char call the hook cut), and are fenced
// against the hub's shape on every run by
// tests/integration/test_desk_agents_wire.py. Only apiFetch is a double; the
// drawer, the shade, the gate store and the needs-you reader are the real ones.
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { hubWire } from "./wire/hubWire";

const api = vi.hoisted(() => ({ fetch: vi.fn() }));
vi.mock("../../lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../lib/api")>()),
  apiFetch: api.fetch,
}));
vi.mock("../shell", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../shell")>()),
  openCoderSession: vi.fn(),
  openSurfaceOr: vi.fn(),
}));
vi.mock("../components/MicButton", () => ({ MicButton: () => null }));

import { openCoderSession } from "../shell";
import { useAgentFlights } from "../agentFlights";
import { NeedsDrawer } from "../needs/NeedsDrawer";
import { SystemShade } from "../components/SystemShade";
import { useGate } from "../gate";

const NEEDS = hubWire("needs-you.gate");
const HELD = hubWire("gate-proposals.held");
const LONG_CMD = (() => {
  const base = "psql -h staging-ledger -U ops -d payments -c 'select count(*) from entries where ledger_id = ";
  return base + "7".repeat(198 - base.length - 1) + "'";
})();

let decided: Array<{ url: string; json: unknown }> = [];

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date(NEEDS.captured_at));
  decided = [];
  vi.mocked(openCoderSession).mockClear();
  (globalThis as { __resetNeedsYou?: () => void }).__resetNeedsYou?.();
  useAgentFlights.setState({ flights: [], sessions: [], loaded: true } as never);
  api.fetch.mockReset();
  api.fetch.mockImplementation(async (url: string, init?: { json?: unknown }) => {
    const path = String(url);
    if (path.startsWith("/api/desk/needs-you")) return NEEDS.wire;
    if (path.startsWith("/api/gate/proposals?state=held")) return HELD.wire;
    if (path.endsWith("/decide")) {
      decided.push({ url: path, json: init?.json });
      return { state: (init?.json as { decision?: string })?.decision };
    }
    if (path === "/api/door") return hubWire("door.empty").wire;
    if (path.startsWith("/api/desk/projections")) return hubWire("desk-projections.attention").wire;
    if (path === "/api/dictation/corrections") return hubWire("dictation-corrections.empty").wire;
    if (path === "/api/brief/latest") return hubWire("brief-latest.empty").wire;
    throw new Error(`no captured hub answer for ${path}`);
  });
});
afterEach(() => {
  vi.useRealTimers();
});

function rowWith(text: string): HTMLElement {
  const rows = [...document.querySelectorAll<HTMLElement>("[data-testid='needs-drawer'] [data-testid='needs-row']")];
  const hit = rows.find((li) => (li.textContent ?? "").includes(text));
  if (!hit) throw new Error(`no row with ${text}`);
  return hit;
}

describe("a held call on Needs you (Conductor R1, PHILO-14 A5)", () => {
  /** replaces: tests/e2e/test_conductor_r1_gate_row_glass.py::test_a_held_call_row_opens_the_shade_and_approve_and_deny_decide_it */
  it("the row says why it waits, the whole command, HELD CALL; Approve and Deny decide the real proposal", async () => {
    render(<NeedsDrawer />);
    await waitFor(() => expect(rowWith("ls /etc")).toBeTruthy());
    const row = rowWith("ls /etc");
    expect(row.querySelector(".needs-row-fact")?.textContent).toBe("OUTSIDE THE WORKTREE\nls /etc");
    expect(row.querySelector(".needs-row-lamp")?.textContent).toContain("HELD CALL");
    fireEvent.click(row.querySelector("[data-verb='approve']")!);
    await waitFor(() => expect(decided).toContainEqual(expect.objectContaining({
      url: "/api/gate/proposals/toolu_glass_approve/decide", json: expect.objectContaining({ decision: "approved" }),
    })));
    fireEvent.click(rowWith("ls /etc").querySelector("[data-verb='deny']")!);
    await waitFor(() => expect(decided.some((d) => (d.json as { decision?: string })?.decision === "denied")).toBe(true));
  });

  /** replaces: tests/e2e/test_conductor_r1_gate_row_glass.py::test_a_held_call_row_opens_the_shade_and_approve_and_deny_decide_it (the cut call) */
  it("a cut call reads `… +90 CHARS` and CUT · APPROVE IN RAW, with Deny and Open, never Approve", async () => {
    render(<NeedsDrawer />);
    await waitFor(() => expect(rowWith("psql -h staging-ledger")).toBeTruthy());
    const row = rowWith("psql -h staging-ledger");
    const [reason, fact] = (row.querySelector(".needs-row-fact")?.textContent ?? "").split("\n");
    expect(reason).toBe("OUTSIDE THE WORKTREE");
    expect(fact.endsWith("… +90 CHARS")).toBe(true);
    expect(LONG_CMD.startsWith(fact.replace(/… \+90 CHARS$/, ""))).toBe(true);
    expect(row.querySelector(".needs-row-lamp")?.textContent).toContain("CUT · APPROVE IN RAW");
    expect(row.querySelector("[data-verb='approve']")).toBeNull();
    expect(row.querySelectorAll("[data-verb='deny']")).toHaveLength(1);
    expect(row.querySelectorAll("[data-verb='open']")).toHaveLength(1);
    // PHILO-15 20 (B63): Open opens the lane on Raw, where the cut call is approved.
    fireEvent.click(row.querySelector("[data-verb='open']")!);
    expect(openCoderSession).toHaveBeenCalledWith("claude:glass-r1", { raw: true });
  });

  /** replaces: tests/e2e/test_conductor_r1_gate_row_glass.py::test_a_held_call_row_opens_the_shade_and_approve_and_deny_decide_it (the shade) */
  it("the shade shows the cut call `… +90 CHARS` with Deny only", async () => {
    render(<SystemShade open onClose={vi.fn()} onOpenMemory={vi.fn()} />);
    await waitFor(() => expect(useGate.getState().held.length).toBe(2));
    const cards = [...document.querySelectorAll<HTMLElement>(".desk-gate-item")];
    const cut = cards.find((card) => (card.textContent ?? "").includes("psql -h staging-ledger"))!;
    expect(cut).toBeTruthy();
    expect(within(cut).getByTestId("shade-gate-command").textContent?.endsWith("… +90 CHARS")).toBe(true);
    expect(within(cut).queryByRole("button", { name: "Approve" })).toBeNull();
    expect(within(cut).getAllByRole("button", { name: "Deny" })).toHaveLength(1);
  });
});
