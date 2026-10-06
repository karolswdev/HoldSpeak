// Conductor F2 (ratified boards K4a, K4c, K5a): on the Chair, the Door row
// wears the agent working on it; the AGENTS section lists every live session
// from `/api/coders/sessions` and names its item; the Needs you coder row
// carries the question, `CLAUDE CODE · WAITING · <age>`, the Project, and
// `Speak answer` (the face's one primary) and `Open`.
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../lib/api";
import { ChairHome } from "../ChairHome";
import { asHub } from "../../../test/hubNeedsYou";
import { useAgentFlights } from "../../agentFlights";
import { openCoderSession } from "../../shell";

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
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));

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

function wire() {
  vi.mocked(apiFetch).mockImplementation(asHub(async (path: string) => {
    const url = String(path);
    if (url === "/api/inference/assignments")
      return { schema: "InferenceAssignmentSummary@1", rows: [], task_overrides: [], issue_count: 0 };
    if (url.startsWith("/api/coders/sessions")) return SESSIONS;
    if (url.startsWith("/api/desk/needs-you"))
      return { count: 2, projects: ["p-ledger"], items: [CODER_ROW, RUNBOOK_ROW], next: null, coverage: [], complete: true };
    if (url.startsWith("/api/door")) return { board: {}, counts: {}, upcoming: [], calendar_configured: false };
    return null;
  }));
}

describe("Conductor F2 on the Chair", () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset();
    vi.mocked(openCoderSession).mockReset();
    useAgentFlights.setState({ sessions: [], flights: [], loaded: false });
    wire();
  });

  it("K5a: the coder row: question, agent and age, Project, Speak answer as the one primary, Open", async () => {
    render(<ChairHome />);
    const row = await screen.findByTestId("arrival-coder-row");
    expect(within(row).getByTestId("arrival-coder-question").textContent).toBe(QUESTION);
    expect(within(row).getByTestId("arrival-source-emblem").textContent).toBe("CC");
    expect(within(row).getByTestId("arrival-why").textContent).toBe("CLAUDE CODE · WAITING · 2 MIN");
    await waitFor(() => expect(within(row).getByTestId("arrival-project").textContent).toContain("PAYMENTS LEDGER CUTOVER"));
    const speak = within(row).getByRole("button", { name: "Speak answer: Claude Code" });
    expect(speak.className).toMatch(/primary/);
    fireEvent.click(speak);
    expect(openCoderSession).toHaveBeenCalledWith("claude:c1", { answer: true });
    fireEvent.click(within(row).getByRole("button", { name: "Open: Claude Code session" }));
    expect(openCoderSession).toHaveBeenLastCalledWith("claude:c1");
  });

  it("K4a: the Door row wears CLAUDE CODE · WAITING and Session", async () => {
    render(<ChairHome />);
    await waitFor(() => expect(screen.getAllByTestId("flight-chip").length).toBeGreaterThan(0));
    const row = screen.getAllByTestId("arrival-needs-you-row").find((r) => r.textContent?.includes("Write the rollback runbook"))!;
    expect(within(row).getByTestId("flight-chip").textContent).toContain("CLAUDE CODE · WAITING");
    fireEvent.click(within(row).getByRole("button", { name: "Open session: Write the rollback runbook" }));
    expect(openCoderSession).toHaveBeenCalledWith("claude:c1");
  });

  it("K4c: AGENTS lists every live session; a handed one names its item", async () => {
    render(<ChairHome />);
    const section = await screen.findByTestId("arrival-agents");
    const rows = within(section).getAllByTestId("arrival-agent-row");
    expect(rows.map((r) => r.querySelector(".surface-ledger-primary")?.textContent)).toEqual([
      "payments-ledger-runbook", "payments-ledger-recon", "scratch",
    ]);
    expect(within(rows[0]).getByTestId("arrival-agent-origin").textContent).toBe("↳ Write the rollback runbook");
    expect(within(rows[0]).getByRole("status").textContent).toContain("CLAUDE CODE · WAITING");
    expect(within(rows[1]).getByTestId("arrival-agent-origin").textContent).toBe("↳ Shard the reconciliation job");
    expect(within(rows[1]).getByRole("status").textContent).toContain("CODEX · WORKING");
    // A session no one handed an item keeps its plain badge.
    expect(within(rows[2]).queryByTestId("arrival-agent-origin")).toBeNull();
    expect(rows[2].textContent).toContain("RUNNING");
    fireEvent.click(within(rows[0]).getByRole("button", { name: "Answer" }));
    expect(openCoderSession).toHaveBeenCalledWith("claude:c1", { answer: true });
  });
});
