// One face per agent (2026-11-08): the lane window folded into the Agents
// pane. These are the lane's behaviours (PHILO-14 C2, PHILO-15 B46/B63/B67,
// W4) proven on the pane, on the same lane answers the lane window read:
// the held plate (Allow / Deny, a refusal and its Retry), a cut call read
// whole in the terminal, Tell it with its queued receipts and Take back, the
// PR row, the files fold, the check log, the unread parts, Stop, the
// terminal in the pane, and the ledger (report sections, tool rows, the
// brief alone).
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const api = vi.hoisted(() => ({ fetch: vi.fn(), request: vi.fn() }));
vi.mock("../../../lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../lib/api")>()),
  apiFetch: api.fetch,
  apiRequest: api.request,
}));
vi.mock("../../components/MicButton", () => ({ MicButton: () => <span data-testid="mic" /> }));

import { AgentPane, reportSections } from "../AgentPane";
import { useLaneOf } from "../AgentLane";
import { WindowIdContext } from "../../components/window/windowIdContext";
import { __resetLane, useLane } from "../../lane/laneStore";
import type { LaneWire } from "../../lane/laneWire";
import { useAgentFlights } from "../../agentFlights";
import { useSteering } from "../../steering";
import { ApiError } from "../../../lib/api";
import { useGate } from "../../gate";
import { __resetConductor } from "../store";
import type { ConductorMember } from "../members";

const QUESTION = "The runbook needs a rollback owner. Jordan or Avery?";
const KEY = "claude:c1a0de00-runbook";
const T = (hhmm: string) => `2026-10-07T${hhmm}:00Z`;

function fixture(over: Partial<LaneWire> = {}): LaneWire {
  return {
    launch: {
      launch_id: "launch_f2_runbook", state: "launched", agent: "claude",
      origin_ref: { kind: "action", id: "a1" }, branch: "hs/write-the-rollback-runbook",
      worktree_path: "~/dev/wt/hs-action-a1", launched_at: T("09:42"), control_mode: "yolo",
      brief_text: "Write the ledger rollback runbook.\nOwner: you.", session_key: KEY,
    },
    session: { state: "waiting" },
    follow_through: {
      pr: {
        number: 413, url: "https://github.com/acme/payments-ledger/pull/413", state: "open", review_decision: "",
        ci: "pending",
        checks: [
          ...Array.from({ length: 6 }, (_, i) => ({ name: `ci ${i}`, state: "success" })),
          { name: "ci 6", state: "in_progress" },
        ],
      },
      merged: null, done: false,
    },
    control: { mode: "yolo", armed: false, direct: true },
    wait: { question: QUESTION, kind: "TO ANSWER", wait_id: "w-1", started: new Date(Date.now() - 6 * 60_000).toISOString(),
      draft: { verdict: "real", reason: "a person", text: "Jordan owns it. Avery reviews." } },
    events: [
      { id: 1, ts: T("09:42"), event: "SessionStart", detail: { source: "startup" } },
      { id: 2, ts: T("09:42"), event: "UserPromptSubmit", text: "Write the ledger rollback runbook." },
      { id: 3, ts: T("09:43"), event: "PostToolUse", tool: "Read", head: "ledger/freeze.py" },
      { id: 4, ts: T("09:43"), event: "PostToolUse", tool: "Grep", head: "docs/runbooks/README.md" },
      { id: 5, ts: T("09:44"), event: "PostToolUse", tool: "Read", head: "ledger/cutover.py" },
      { id: 6, ts: T("09:44"), event: "PostToolUse", tool: "Glob", head: "tests/**" },
      { id: 7, ts: T("09:45"), event: "Stop", text: "I will draft the runbook from the freeze decision." },
      { id: 8, ts: T("09:47"), event: "PostToolUse", tool: "Write", head: "docs/runbooks/ledger-rollback.md" },
      { id: 9, ts: T("09:48"), event: "PostToolUse", tool: "Bash", head: "pytest tests/runbooks -q" },
    ],
    events_next_after: null,
    gated: [{ id: "toolu_psql", tool: "Bash", args_head: '{"command":"psql -h staging-ledger -c \'select 1\'"}', state: "held", created_at: Date.parse(T("09:55")) / 1000 }],
    answers: [],
    attempt_events: [],
    worktree: {
      base: "origin/main", branch: "hs/write-the-rollback-runbook",
      commits: [{ sha: "a1c9e02", at: Date.parse(T("09:51")) / 1000, subject: "Draft the ledger rollback runbook" }],
      files: [{ status: "A", path: "docs/runbooks/ledger-rollback.md" }, { status: "M", path: "ledger/freeze.py" }],
      uncommitted: { staged: 0, modified: 0, untracked: 0 },
    },
    usage: null,
    ...over,
  };
}

function serve(lane: LaneWire) {
  api.fetch.mockImplementation(async (url: string) => {
    if (String(url).startsWith("/api/agent/launches/")) return lane;
    if (String(url).startsWith("/api/inference/assignments")) {
      return { task_overrides: [{ id: "background.cadence_draft", effective: { assignment: { entries: [{ profile_id: "p1", label: "api.anthropic.com", boundary: "external_service" }] } } }] };
    }
    if (String(url).includes("/decide")) return { state: "approved" };
    if (String(url).startsWith("/api/gate/proposals")) return { proposals: [] };
    return {};
  });
}

/** The hub's answers to the lane's own POSTs, by path suffix. */
function answer(map: Record<string, [number, Record<string, unknown>]>) {
  api.request.mockImplementation(async (url: string) => {
    const hit = Object.entries(map).find(([suffix]) => String(url).endsWith(suffix));
    const [status, body] = hit ? hit[1] : [200, { status: "delivered" }];
    return { ok: status < 300, status, json: async () => body } as unknown as Response;
  });
}

function posts(suffix: string): Array<Record<string, unknown>> {
  return api.request.mock.calls
    .filter(([url]) => String(url).endsWith(suffix))
    .map(([, init]) => JSON.parse(String((init as RequestInit).body)));
}

function steering(over: Record<string, unknown> = {}) {
  act(() => {
    useSteering.setState({
      openKey: null, session: null, paneStatus: "no_pane", armed: false, postureAuthorized: false,
      steerState: "idle", steerDetail: "", answerSeq: 0, answerOpen: false,
      openSession: vi.fn(), closeSession: vi.fn(), ...over,
    } as never);
  });
}


function member(over: Partial<ConductorMember> = {}): ConductorMember {
  return {
    id: "launch:launch_f2_runbook", ref: "launch:launch_f2_runbook", kind: "coder", name: "Claude Code: Write the rollback runbook",
    role: "live", agent: "claude", launchId: "launch_f2_runbook", sessionKey: KEY, live: "work",
    facts: { from: "Write the rollback runbook", where: "Payments ledger" }, sprite: "", ...over,
  } as ConductorMember;
}

async function openPane(lane: LaneWire, over: Partial<ConductorMember> = {}, steer: Record<string, unknown> = {}) {
  serve(lane);
  answer({});
  steering(steer);
  render(<AgentPane member={member(over)} pill={{ word: "Working", tone: "info" }} row={undefined} onStart={() => undefined} />);
  await waitFor(() => expect(useLane.getState().lane).not.toBeNull());
  await screen.findByTestId("agents-mast");
}

const STEER = `/api/coders/${encodeURIComponent(KEY)}/steer`;
const ARM = `/api/coders/${encodeURIComponent(KEY)}/arm`;
const KILL = `/api/coders/${encodeURIComponent(KEY)}/kill`;
const REBRIEF = "/api/agent/launches/launch_f2_runbook/rebrief";

beforeEach(() => {
  api.fetch.mockReset();
  api.request.mockReset();
  localStorage.clear();
  __resetLane();
  __resetConductor();
  useGate.setState({ held: [], loaded: false, error: null });
  useAgentFlights.setState({ flights: [], sessions: [], loaded: true });
});
afterEach(() => __resetLane());

describe("a guide borrows an unread agent", () => {
  it.each([true, false])("guide=%s: only the owner's selection marks the report seen", async (guided) => {
    serve(fixture());
    function Probe() { useLaneOf("launch_f2_runbook"); return null; }
    render(<div id="guide-agent" {...(guided ? { "data-guide-running": "" } : {})}>
      <WindowIdContext.Provider value="guide-agent"><Probe /></WindowIdContext.Provider>
    </div>);
    await waitFor(() => expect(useLane.getState().lane).not.toBeNull());
    expect(api.fetch.mock.calls.some(([url]) => String(url).endsWith("/seen"))).toBe(!guided);
  });
});

describe("the held call is the plate (Allow / Deny on the ask row)", () => {
  it("a launched agent whose lane holds a call shows it on the ask row with Allow and Deny", async () => {
    await openPane(fixture(), { live: "work" });
    const plate = await screen.findByTestId("conductor-ask-row");
    await waitFor(() => expect(within(plate).getByTestId("conductor-held-call").textContent).toContain("psql -h staging-ledger"));
    expect(within(plate).getByTestId("conductor-approve").textContent).toBe("Allow");
    expect(within(plate).getByTestId("conductor-deny")).toBeTruthy();
  });
});

describe("a cut call is read whole in the terminal (B63)", () => {
  const head = "cd /private/var/folders/q7/T/hs-r2/.holdspeak/repositories/karolsw";
  const whole = `${head}dev/rehearsal && git status --short && echo done`;
  const cutLane = () => fixture({
    wait: { question: "Codex needs your permission to use Bash", kind: "TO APPROVE", started: null },
    gated: [{ id: "toolu_cut", tool: "Bash", args_head: `{"command":"${head}`, args_shown: head, args_cut: true,
      args_hidden: whole.length - head.length, state: "held", hold_reason: "OUTSIDE THE WORKTREE",
      created_at: Date.parse(T("09:55")) / 1000 }],
  });

  it("no Allow on the plate; Terminal shows the pane and the whole call, and Allow there decides it", async () => {
    await openPane(cutLane());
    const base = api.fetch.getMockImplementation()!;
    api.fetch.mockImplementation(async (url: string, init?: RequestInit) => {
      if (String(url) === "/api/gate/proposals/toolu_cut/command") return { id: "toolu_cut", state: "held", command: whole, whole: true, hold_reason: "OUTSIDE THE WORKTREE" };
      return base(url, init);
    });
    const plate = await screen.findByTestId("conductor-ask-row");
    await waitFor(() => expect(within(plate).getByTestId("agent-row-terminal")).toBeTruthy());
    expect(within(plate).queryByTestId("conductor-approve")).toBeNull();
    fireEvent.click(within(plate).getByTestId("agent-row-terminal"));
    const held = await screen.findByTestId("lane-raw-held");
    await waitFor(() => expect(within(held).getByTestId("lane-raw-command").textContent).toBe(whole));
    expect(within(held).getByText("Held · Outside the worktree")).toBeTruthy();
    fireEvent.click(within(held).getByTestId("lane-raw-approve"));
    await waitFor(() => expect(api.fetch.mock.calls.some(([url, init]) =>
      String(url) === "/api/gate/proposals/toolu_cut/decide" && (init as { json?: { decision?: string } })?.json?.decision === "approved")).toBe(true));
    await waitFor(() => expect(screen.getByTestId("lane-receipt").textContent).toMatch(/^Approved · .+$/));
    expect(screen.getByTestId("lane-raw-pane")).toBeTruthy();
  });

  it("a call the hub did not keep whole is Deny only", async () => {
    await openPane(cutLane());
    const base = api.fetch.getMockImplementation()!;
    api.fetch.mockImplementation(async (url: string, init?: RequestInit) => {
      if (String(url) === "/api/gate/proposals/toolu_cut/command") return { id: "toolu_cut", state: "held", command: head, whole: false,
        hold_reason: "OUTSIDE THE WORKTREE", shown_chars: head.length, declared_chars: whole.length };
      return base(url, init);
    });
    act(() => useLane.getState().setRaw(true));
    const held = await screen.findByTestId("lane-raw-held");
    await waitFor(() => expect(within(held).getByTestId("lane-raw-command").textContent).toBe(head));
    expect(within(held).getByText(`Held · Outside the worktree · Cut · ${head.length} of ${whole.length} chars`)).toBeTruthy();
    expect(within(held).queryByTestId("lane-raw-approve")).toBeNull();
  });
});

describe("Tell it (B46) and Take back (B67)", () => {
  it("Tell it sends through the Re-brief route; mid-turn it is queued; the receipt stays", async () => {
    await openPane(fixture({ wait: null, gated: [] }));
    answer({ [REBRIEF]: [202, { status: "queued", at: "2026-10-07T16:40:00Z" }] });
    serve(fixture({ wait: null, gated: [], launch: { ...fixture().launch, queued_rebrief: { text: "Re-brief: use the security address.", at: "2026-10-07T16:40:00Z" } } }));
    fireEvent.click(within(screen.getByTestId("agents-mast")).getByTestId("lane-rebrief"));
    const field = within(screen.getByTestId("lane-rebrief-well")).getByRole("textbox", { name: "Tell it" }) as HTMLInputElement;
    fireEvent.change(field, { target: { value: "Re-brief: use the security address." } });
    fireEvent.keyDown(field, { key: "Enter" });
    await waitFor(() => expect(screen.getByTestId("lane-queued").textContent).toBe("Queued after this turn · Re-brief: use the security address."));
    expect(posts(REBRIEF)).toEqual([{ text: "Re-brief: use the security address." }]);
    expect(posts(STEER)).toEqual([]);
    expect(screen.queryByTestId("lane-rebrief-well")).toBeNull();
  });

  it("Take back discards a queued Re-brief and says Taken back", async () => {
    await openPane(fixture({ wait: null, gated: [], launch: { ...fixture().launch, queued_rebriefs: [
      { id: "press-1", text: "Re-brief: do not write outside the worktree.", at: "2026-10-07T21:30:00Z" },
    ] } }));
    answer({ [`${REBRIEF}/press-1/take-back`]: [200, { status: "taken_back" }] });
    serve(fixture({ wait: null, gated: [] }));
    fireEvent.click(screen.getByTestId("lane-take-back"));
    await waitFor(() => expect(screen.getByTestId("lane-receipt").textContent).toMatch(/^Taken back · .* · Re-brief: do not write outside/));
    expect(posts(`${REBRIEF}/press-1/take-back`)).toEqual([{}]);
  });

  it("a stopped launch says so and offers no Tell it and no Stop", async () => {
    await openPane(fixture({ wait: null, gated: [], launch: { ...fixture().launch, state: "stopped_by_owner", stopped: { by: "owner", at: T("10:01"), audit_id: 1 } } }));
    expect(screen.getByTestId("lane-stopped").textContent).toMatch(/^Stopped by you · .+$/);
    expect(screen.queryByTestId("lane-rebrief")).toBeNull();
  });
});

describe("what it made: the PR row, the files, the check log", () => {
  it("the PR row: its own number and title, checks and review as words, Open the PR; files one fold; the checks in Details", async () => {
    await openPane(fixture({ gated: [], wait: null }));
    const pr = screen.getByTestId("lane-pr");
    expect(pr.textContent).toContain("#413 Write the rollback runbook");
    expect(pr.textContent).toContain("Checks 6 of 7");
    expect(screen.getByTestId("lane-pr-checks").getAttribute("data-tone")).toBe("warn");
    expect(pr.getAttribute("data-tone")).toBe("steel");
    const opened = vi.spyOn(window, "open").mockImplementation(() => null);
    fireEvent.click(within(pr).getByRole("button", { name: "Open the PR" }));
    expect(opened).toHaveBeenCalledWith("https://github.com/acme/payments-ledger/pull/413", "_blank", "noopener,noreferrer");
    opened.mockRestore();
    expect(screen.getByTestId("lane-files").textContent).toContain("2 files changed");
    expect(screen.getByTestId("lane-files").textContent).toContain("ledger/freeze.py");
    expect(within(screen.getByTestId("agents-details")).getByTestId("lane-checks").textContent).toContain("ci 6");
  });

  it("a red check turns the PR row coral", async () => {
    const lane = fixture({ gated: [], wait: null });
    lane.follow_through.pr!.checks = [{ name: "ci", state: "failure" }];
    await openPane(lane);
    expect(screen.getByTestId("lane-pr").getAttribute("data-tone")).toBe("coral");
  });

  it("says each unread part in one line, never as empty", async () => {
    await openPane(fixture({
      events: { not_read: "events: OperationalError: locked" },
      worktree: { not_read: "the worktree is gone" },
      gated: { not_read: "gated: OperationalError" },
      usage: { not_read: "usage: RuntimeError" },
    }));
    expect(screen.getByTestId("lane-events-not-read").textContent).toBe("Timeline not read · events: OperationalError: locked");
    expect(screen.getByTestId("lane-files-not-read").textContent).toBe("Files not read · the worktree is gone");
    expect(screen.getByTestId("lane-not-read-held").textContent).toBe("Held not read · gated: OperationalError");
    expect(screen.getByTestId("lane-not-read-usage").textContent).toBe("Usage not read · usage: RuntimeError");
  });
});

describe("the terminal is in the pane", () => {
  it("Terminal shows the lane's own pane (bound to its session); Back to the agent returns", async () => {
    await openPane(fixture({ gated: [], wait: null }));
    fireEvent.click(screen.getByTestId("agents-terminal"));
    expect(useSteering.getState().openSession).toHaveBeenCalledWith(KEY);
    const pane = screen.getByTestId("lane-raw-pane");
    expect(pane.textContent).toContain("Terminal unavailable");
    fireEvent.click(within(pane).getByRole("button", { name: "Back to the agent" }));
    expect(screen.queryByTestId("lane-raw-pane")).toBeNull();
    expect(screen.getByTestId("agents-ledger")).toBeTruthy();
  });
});

describe("Stop on a launched agent (the lane's kill)", () => {
  it("YOLO: the confirm arms, then kills the lane's session", async () => {
    await openPane(fixture({ gated: [], wait: null, control: { mode: "yolo", armed: false, direct: true } }));
    answer({ "/arm": [200, { status: "armed", pane_id: "%0" }], "/kill": [200, { status: "killed" }] });
    fireEvent.click(screen.getByTestId("conductor-stop"));
    fireEvent.click(screen.getByTestId("conductor-stop-confirm"));
    await waitFor(() => expect(posts(KILL)).toEqual([{ scope: "session" }]));
    expect(posts(ARM)).toHaveLength(1);
  });
});

describe("the ledger", () => {
  it("tool activity by time, newest first, the time in its own slot", async () => {
    await openPane(fixture({ gated: [], wait: null }));
    const rows = screen.getAllByTestId("agents-ledger-row");
    // The commit (09:51) is newer than the test run (09:48).
    expect(rows[0].textContent).toContain("a1c9e02 Draft the ledger rollback runbook");
    expect(rows[1].textContent).toContain("pytest tests/runbooks -q");
    expect(rows[1].querySelector(".surface-ledger-time")?.textContent).toMatch(/^\d\d:\d\d$/);
    expect(screen.getByTestId("agents-ledger").textContent).not.toContain("#413");
  });

  it("a report is rows, one per section; Read opens a section in the pane", async () => {
    const report = "## What changed\nThe runbook names the owner.\n\n## What is left\nAvery reviews it.";
    await openPane(fixture({ gated: [], wait: null, last_words: report } as Partial<LaneWire>));
    const sections = screen.getAllByTestId("agents-ledger-row").filter((row) => row.textContent?.includes("Report"));
    expect(sections.map((row) => row.querySelector(".aw-ledger-text")?.textContent)).toEqual(["What changed", "What is left"]);
    fireEvent.click(within(sections[1]).getByTestId("agents-ledger-read"));
    expect(screen.getByText("Avery reviews it.")).toBeTruthy();
  });

  it("a launch with only its brief shows The brief, and Read opens it", async () => {
    await openPane(fixture({ gated: [], wait: null, events: [], worktree: { base: "origin/main", branch: "b", commits: [], files: [] },
      follow_through: { pr: null } }));
    const rows = screen.getAllByTestId("agents-ledger-row");
    expect(rows).toHaveLength(1);
    expect(rows[0].textContent).toContain("The brief");
    fireEvent.click(within(rows[0]).getByTestId("agents-ledger-read"));
    expect(screen.getByText(/Owner: you\./)).toBeTruthy();
  });

  it("reportSections: headings start sections; without headings each paragraph is one", () => {
    expect(reportSections("**Done**\nAll green.\nNext:\nmerge it").map((s) => s.title)).toEqual(["Done", "Next"]);
    expect(reportSections("First part.\n\nSecond part.").map((s) => s.title)).toEqual(["First part.", "Second part."]);
  });
});
