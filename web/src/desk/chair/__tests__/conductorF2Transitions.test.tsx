// Conductor F2 (Astra round 1 on #906, finding 5): rendered transitions with
// the window kept open. Fixtures from conductorF2.test.tsx.
// Conductor F2 (ratified boards K4a, K4c, K5a): on the Chair, the Door row
// wears the agent working on it; the AGENTS section lists every live session
// from `/api/coders/sessions` and names its item; the Needs you coder row
// carries the question, `CLAUDE CODE · WAITING · <age>`, the Project, and
// `Speak answer` (the face's one primary) and `Open`.
import { act, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../lib/api";
import { ChairHome } from "../ChairHome";
import { asHub } from "../../../test/hubNeedsYou";
import { useAgentFlights } from "../../agentFlights";

vi.mock("../../../lib/api", async (original) => ({
  ...await original<typeof import("../../../lib/api")>(),
  apiFetch: vi.fn(),
}));
vi.mock("../../shell", async (original) => ({
  ...await original<typeof import("../../shell")>(),
  openCoderSession: vi.fn(),
  openProjectRoom: vi.fn(),
}));
vi.mock("../../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../../components/MicButton", () => ({ MicButton: () => null }));
const bus = vi.hoisted(() => ({ handlers: new Map<string, Set<(frame: unknown) => void>>() }));
vi.mock("../../../runtime/RuntimeBus", () => {
  const value = {
    state: "connected",
    lastFrame: null,
    subscribe: (type: string, handler: (frame: unknown) => void) => {
      const set = bus.handlers.get(type) ?? new Set();
      set.add(handler);
      bus.handlers.set(type, set);
      return () => set.delete(handler);
    },
  };
  return { useRuntimeBus: () => value, useOptionalRuntimeBus: () => value, useRuntimeFrame: () => null };
});
function emit(type: string, data: unknown = {}) {
  for (const handler of bus.handlers.get(type) ?? []) handler({ type, data });
}

const TWO_MIN_AGO = new Date(Date.now() - 2 * 60 * 1000 - 5000).toISOString();
const QUESTION = "The runbook needs a rollback owner. Jordan or Avery?";

const FLIGHT_RUNBOOK = {
  origin_ref: "action:ai-runbook", kind: "action", id: "ai-runbook", title: "Write the rollback runbook",
  project_id: "p-ledger", project_name: "Payments ledger cutover", agent: "claude", state: "waiting",
  session_key: "claude:c1", pr: null, close: null, merged_at: null,
};
const FLIGHT_RECON = {
  ...FLIGHT_RUNBOOK, origin_ref: "decision:d-recon", kind: "decision", id: "d-recon",
  title: "Shard the reconciliation job", agent: "codex", state: "working", session_key: "codex:x1",
};

const SESSIONS = {
  sessions: [
    { session: { agent: "claude", session_id: "c1", state: "waiting", question: QUESTION, hook_event_name: "Notification",
      repo_root: "/h/dev/payments-ledger-runbook", updated_at: TWO_MIN_AGO }, flight: FLIGHT_RUNBOOK },
    { session: { agent: "codex", session_id: "x1", state: "working", repo_root: "/h/dev/payments-ledger-recon" }, flight: FLIGHT_RECON },
    { session: { agent: "claude", session_id: "solo", state: "working", repo_root: "/h/dev/scratch" } },
  ],
  flights: [FLIGHT_RUNBOOK, FLIGHT_RECON],
};

const CODER_ROW = {
  id: "coder:claude:c1", ref: "coder:claude:c1", projectId: "", projectName: "payments-ledger-runbook",
  title: QUESTION, why: "TO ANSWER", ageToken: TWO_MIN_AGO, since: TWO_MIN_AGO, dueAt: null,
  kind: "coder", source: "coder", verbHref: null, openRef: "coder:claude:c1", severity: "warning",
  sessionKey: "claude:c1", agent: "claude", question: QUESTION, waitKind: "answer",
  waitStartedAt: TWO_MIN_AGO, ageSeconds: 125,
};
const RUNBOOK_ROW = {
  id: "p-ledger:commitment:runbook", ref: "p-ledger:commitment:runbook", projectId: "p-ledger",
  projectName: "Payments ledger cutover", title: "Write the rollback runbook", why: "OWNER · UNKNOWN",
  ageToken: "", since: "2026-10-05T09:00:00", source: "commitment", verbHref: null, severity: "warning",
  kind: "action_item", actionItemId: "ai-runbook", unknowns: ["owner"],
};

let sessions: unknown = SESSIONS;

function wire() {
  vi.mocked(apiFetch).mockImplementation(asHub(async (path: string) => {
    const url = String(path);
    if (url === "/api/inference/assignments")
      return { schema: "InferenceAssignmentSummary@1", rows: [], task_overrides: [], issue_count: 0 };
    if (url.startsWith("/api/coders/sessions")) return sessions;
    if (url.startsWith("/api/desk/needs-you"))
      return { count: 2, projects: ["p-ledger"], items: [CODER_ROW, RUNBOOK_ROW], next: null, coverage: [], complete: true };
    if (url.startsWith("/api/door")) return { board: {}, counts: {}, upcoming: [], calendar_configured: false };
    return null;
  }));
}

const working = (s: Record<string, unknown>) => ({ ...s, flight: { ...(s as any).flight, state: "working" } });

describe("Conductor F2: transitions land on a mounted Chair", () => {
  beforeEach(() => {
    bus.handlers.clear();
    vi.mocked(apiFetch).mockReset();
    useAgentFlights.setState({ sessions: [], flights: [], loaded: false });
  });

  it("WORKING becomes WAITING on a coder frame; on merge + cleanup the session leaves AGENTS", async () => {
    const [runbook, recon, solo] = (SESSIONS.sessions as Array<Record<string, unknown>>);
    sessions = { sessions: [working(runbook), recon, solo], flights: [{ ...FLIGHT_RUNBOOK, state: "working" }, FLIGHT_RECON] };
    wire();
    render(<ChairHome />);
    const door = () => screen.getAllByTestId("arrival-needs-you-row").find((r) => r.textContent?.includes("Write the rollback runbook"))!;
    await waitFor(() => expect(within(door()).getByTestId("flight-chip").textContent).toContain("CLAUDE CODE · WORKING"));

    sessions = SESSIONS;   // the agent asked: waiting
    act(() => emit("intel_status", { state: "ready", scope: "coder" }));
    await waitFor(() => expect(within(door()).getByTestId("flight-chip").textContent).toContain("CLAUDE CODE · WAITING"));

    // The PR merged; the close waits for the owner (Secure): the session stays.
    const merged = { ...FLIGHT_RUNBOOK, state: "merged", close: "awaiting_confirm", pr: { number: 413, url: "u", state: "merged" } };
    sessions = { sessions: [{ ...runbook, flight: merged }, recon, solo], flights: [merged, FLIGHT_RECON] };
    act(() => emit("desk_changed"));
    await waitFor(() => expect(within(door()).getByTestId("flight-chip").textContent).toContain("PR #413 · MERGED"));
    expect(within(screen.getByTestId("arrival-agents")).getAllByTestId("arrival-agent-row")).toHaveLength(3);

    // Confirmed, closed and cleaned up: the session leaves AGENTS.
    const done = { ...merged, close: "closed", session_cleanup: "killed" };
    sessions = { sessions: [{ ...runbook, flight: done }, recon, solo], flights: [done, FLIGHT_RECON] };
    act(() => emit("desk_changed"));
    await waitFor(() => expect(within(screen.getByTestId("arrival-agents")).getAllByTestId("arrival-agent-row")).toHaveLength(2));
    expect(screen.getByTestId("arrival-agents").textContent).not.toContain("payments-ledger-runbook");
  });
});
