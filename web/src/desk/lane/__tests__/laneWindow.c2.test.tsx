// PHILO-14 C2 (ratified board A-4 + C-4's station track): the agent's lane
// window renders each section from the lane JSON (`GET /api/agent/launches/
// {id}/lane`), says every unread part in one line, draws the three kinds of
// wait, sends an answer on Enter through the steer route, decides a held call
// through the gate route, and puts the terminal pane behind Raw.
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const api = vi.hoisted(() => ({ fetch: vi.fn(), request: vi.fn() }));
vi.mock("../../../lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../lib/api")>()),
  apiFetch: api.fetch,
  apiRequest: api.request,
}));
vi.mock("../../components/MicButton", () => ({
  MicButton: (props: { label?: string; startSignal?: number }) => (
    <span data-testid="mic" data-label={props.label} data-auto={String(Boolean(props.startSignal))} />
  ),
}));

import { LaneWindow, __resetDraftEgress } from "../LaneWindow";
import { __resetLane, useLane } from "../laneStore";
import { laneEntries, laneStations, eventEntries, type LaneWire } from "../laneWire";
import { SessionPullout } from "../../components/SessionPullout";
import { fromWireFlight, useAgentFlights } from "../../agentFlights";
import { useSteering } from "../../steering";
import { wireClock } from "../../surface/format";

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

async function openLane(lane: LaneWire, over: Record<string, unknown> = {}, opts: { answer?: boolean } = {}) {
  serve(lane);
  answer({});
  steering(over);
  render(<LaneWindow />);
  await act(async () => {
    await useLane.getState().open("launch_f2_runbook", { sessionKey: KEY, answer: opts.answer });
  });
  await screen.findByTestId("lane-track");
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
  __resetDraftEgress();
  useAgentFlights.setState({ flights: [], sessions: [], loaded: true });
});
afterEach(() => {
  __resetLane();
});

describe("the station track (C-4's borrow)", () => {
  it("counts the calls, the commits, the PR, the held call and the ask; MERGE is yours", () => {
    const lane = fixture();
    const stations = laneStations(lane, lane.events as never);
    expect(stations.map((s) => [s.word, s.sub, s.state])).toEqual([
      ["BRIEF", expect.stringMatching(/^\d\d:\d\d$/), "reached"],
      ["WORK", "6 calls", "reached"],
      ["COMMIT", "1", "reached"],
      ["PR", "#413", "reached"],
      ["HELD", "1 HELD · 1 WAITING", "current"],
      ["ASKS", "now", "current"],
      ["MERGE", "yours", "ahead"],
    ]);
  });

  it("PHILO-15 15 (B45): counts every held call and its outcome; a call the mode passed is not a hold", () => {
    const call = (id: string, state: string, extra: Record<string, unknown> = {}) => ({
      id, tool: "Bash", args_head: `{"command":"echo ${id}"}`, state, created_at: Date.parse(T("09:55")) / 1000,
      was_held: true, ...extra,
    });
    const gated = [
      ...["a1", "a2", "a3"].map((id) => call(id, "approved", { decided_by: "owner" })),
      ...["d1", "d2", "d3", "d4", "d5"].map((id) => call(id, "denied", { decided_by: "owner" })),
      call("e1", "expired"),
      // Passed at once by the Control mode (YOLO, in the worktree): a run.
      call("p1", "approved", { decided_by: "control-mode", was_held: false }),
      call("p2", "approved", { decided_by: "control-mode", was_held: false }),
    ];
    const lane = fixture({ gated });
    const by = Object.fromEntries(laneStations(lane, lane.events as never).map((s) => [s.word, s]));
    expect(by.HELD).toMatchObject({ sub: "9 HELD · 3 APPROVED · 5 DENIED · 1 EXPIRED", state: "reached" });
    const rail = laneEntries(lane, lane.events as never).filter((e) => e.word === "HELD");
    expect(rail).toHaveLength(9);
  });

  it("PHILO-15 15: a done report reads DONE on the station and the rail, with the agent's last words", () => {
    const lane = fixture({ wait: { question: "PR #413 is open; both tests pass.", kind: "DONE", turn_end: "done",
      wait_id: "w-9", started: new Date(Date.now() - 60_000).toISOString() } });
    const by = Object.fromEntries(laneStations(lane, lane.events as never).map((s) => [s.word, s]));
    expect(by.DONE).toMatchObject({ state: "reached", tone: "ok" });
    expect(by.ASKS).toBeUndefined();
    const done = laneEntries(lane, lane.events as never).find((e) => e.word === "DONE");
    expect(done?.text).toBe("PR #413 is open; both tests pass.");
  });

  it("PHILO-15 15 (B43): a held call's rail entry says why it waits", () => {
    const lane = fixture({
      gated: [{
        id: "toolu_tmp", tool: "Bash", args_head: '{"command":"echo x > /tmp/hs_write_probe.txt"}', state: "held",
        created_at: Date.parse(T("09:55")) / 1000, was_held: true,
        hold_reason: "OUTSIDE THE WORKTREE · /tmp/hs_write_probe.txt",
      }],
    });
    const held = laneEntries(lane, lane.events as never).find((e) => e.word === "HELD");
    expect(held?.text).toBe("OUTSIDE THE WORKTREE · /tmp/hs_write_probe.txt");
    expect(held?.code).toBe("echo x > /tmp/hs_write_probe.txt");
  });

  it("says no zero: an empty station is hollow and reads —; an unread worktree says so", () => {
    const lane = fixture({ events: [], gated: [], wait: null, follow_through: { pr: null, merged: null },
      worktree: { not_read: "the worktree is gone" } });
    const stations = laneStations(lane, []);
    const by = Object.fromEntries(stations.map((s) => [s.word, s]));
    expect(by.WORK).toMatchObject({ sub: "—", state: "ahead" });
    expect(by.COMMIT).toMatchObject({ sub: "not read", state: "ahead" });
    expect(by.PR).toMatchObject({ sub: "—", state: "ahead" });
    expect(by.HELD).toMatchObject({ sub: "—", state: "ahead" });
    expect(by.ASKS).toMatchObject({ sub: "—", state: "ahead" });
    expect(stations.some((s) => /\b0\b/.test(String(s.sub)))).toBe(false);
  });

  it("a merged launch reaches MERGE", () => {
    const lane = fixture({ follow_through: { ...fixture().follow_through, merged: { merged_at: T("10:30") } } });
    expect(laneStations(lane, []).at(-1)).toMatchObject({ word: "MERGE", sub: "merged", state: "reached" });
  });
});

describe("the timeline words", () => {
  it("maps events to words: reads collapse with +n, the agent's words are quoted, the brief is not repeated", () => {
    const entries = eventEntries(fixture().events as never);
    expect(entries.map((e) => e.word)).toEqual(["READ", "SAYS", "WRITE", "RUN"]);
    expect(entries[0].code).toBe("ledger/freeze.py · docs/runbooks/README.md · +2");
    expect(entries[1].quote).toBe("I will draft the runbook from the freeze decision.");
    expect(entries[2].code).toBe("docs/runbooks/ledger-rollback.md");
    expect(entries[3].code).toBe("pytest tests/runbooks -q");
  });

  it("a read with no head (the hook keeps no path for a Grep) counts in +n and names nothing", () => {
    const [read] = eventEntries([
      { id: 1, ts: T("09:43"), event: "PostToolUse", tool: "Grep", head: null },
      { id: 2, ts: T("09:43"), event: "PostToolUse", tool: "Read", head: "a.py" },
    ]);
    expect(read.code).toBe("a.py · +1");
  });

  it("a run shows its result only when the event carries it", () => {
    const [run] = eventEntries([{ id: 1, ts: T("09:48"), event: "PostToolUse", tool: "Bash", head: "pytest -q", detail: { result: "6 passed" } }]);
    expect(run.code).toBe("pytest -q · 6 passed");
  });

  it("orders BRIEF, the work, COMMIT, PR, HELD, ASKS and the hollow MERGE", () => {
    const lane = fixture();
    expect(laneEntries(lane, lane.events as never).map((e) => e.word)).toEqual([
      "BRIEF", "READ", "SAYS", "WRITE", "RUN", "COMMIT", "PR", "HELD", "ASKS", "MERGE",
    ]);
    const pr = laneEntries(lane, lane.events as never).find((e) => e.word === "PR");
    expect(pr?.text).toBe("#413 opened · checks 6 of 7 · review none yet");
    const held = laneEntries(lane, lane.events as never).find((e) => e.word === "HELD");
    expect(held?.code).toBe("psql -h staging-ledger -c 'select 1'");
  });
});

describe("the agent's window", () => {
  it("renders the title, the track, the ask well, the rail, the PR card, the files and the footer", async () => {
    useAgentFlights.setState({ flights: [fromWireFlight({ origin_ref: "action:a1", title: "Write the rollback runbook", agent: "claude", state: "waiting", session_key: KEY, launch_id: "launch_f2_runbook" })] });
    await openLane(fixture());
    expect(screen.getAllByText("Claude Code: Write the rollback runbook").length).toBeGreaterThan(0);
    expect(screen.getByTestId("lane-ask").querySelector(".ask-well-question")?.textContent).toBe(QUESTION);
    expect(screen.getByText("CLAUDE CODE ASKS · 6 MIN")).toBeTruthy();
    const rail = screen.getByTestId("lane-rail");
    expect(within(rail).getByText("COMMIT")).toBeTruthy();
    expect(within(rail).getByText("a1c9e02 Draft the ledger rollback runbook")).toBeTruthy();
    expect(within(rail).getByText("Your press in GitHub")).toBeTruthy();
    const pr = screen.getByTestId("lane-pr");
    expect(pr.textContent).toContain("#413 Write the rollback runbook");
    expect(pr.textContent).toContain("CHECKS 6 OF 7");
    expect(pr.textContent).toContain("1 RUNNING");
    expect(pr.textContent).toContain("NONE YET");
    expect(pr.textContent).toContain("hs/write-the-rollback-runbook → main");
    expect(screen.getByTestId("lane-files").textContent).toContain("ledger/freeze.py");
    expect(screen.getByText("GITHUB.COM")).toBeTruthy();
    expect(screen.getByTestId("lane-branch").textContent).toBe("hs/write-the-rollback-runbook");
    expect(screen.getByTestId("lane-rebrief")).toBeTruthy();
    expect(screen.getByTestId("lane-stop")).toBeTruthy();
    expect(screen.getByTestId("lane-open-pr")).toBeTruthy();
    // The draft's host is the drafting model's.
    await waitFor(() => expect(within(screen.getByTestId("lane-ask").querySelector(".ask-well-draft") as HTMLElement).getByText("API.ANTHROPIC.COM")).toBeTruthy());
  });

  it("the Brief verb unfolds the brief in a well", async () => {
    await openLane(fixture());
    expect(screen.queryByTestId("lane-brief-text")).toBeNull();
    fireEvent.click(screen.getByTestId("lane-brief"));
    expect(screen.getByTestId("lane-brief-text").textContent).toContain("Owner: you.");
  });

  it("says each unread part in one line, never as empty", async () => {
    await openLane(fixture({
      events: { not_read: "events: OperationalError: locked" },
      worktree: { not_read: "the worktree is gone" },
      wait: { not_read: "sessions: OSError" },
      gated: { not_read: "gated: OperationalError" },
    }));
    expect(screen.getByTestId("lane-events-not-read").textContent).toBe("TIMELINE · NOT READ · events: OperationalError: locked");
    expect(screen.getByTestId("lane-files-not-read").textContent).toBe("FILES · NOT READ · the worktree is gone");
    expect(screen.getByText("ASKS · NOT READ · sessions: OSError")).toBeTruthy();
    expect(screen.getByText("HELD · NOT READ · gated: OperationalError")).toBeTruthy();
    expect(screen.queryByTestId("lane-files")).toBeNull();
  });

  it("TO ANSWER: Use draft fills the field and does not send; Enter sends to the lane's session with the wait id", async () => {
    await openLane(fixture());
    const field = screen.getByRole("textbox", { name: "Answer" }) as HTMLInputElement;
    fireEvent.click(within(screen.getByTestId("lane-ask")).getByRole("button", { name: "Use draft" }));
    expect(field.value).toBe("Jordan owns it. Avery reviews.");
    expect(posts("/steer")).toEqual([]);
    fireEvent.change(field, { target: { value: "Jordan owns it." } });
    fireEvent.keyDown(field, { key: "Enter" });
    await waitFor(() => expect(posts(STEER)).toEqual([{ text: "Jordan owns it.", submit: true, kind: "answer", wait_id: "w-1" }]));
    await waitFor(() => expect(field.value).toBe(""));
    expect(screen.getByTestId("lane-receipt").textContent).toMatch(/^SENT · \d\d:\d\d · Jordan owns it\.$/);
  });

  it("the lane's actions go to its own session, not to the pane Panes picked", async () => {
    await openLane(fixture(), { openKey: "pane:%9" });
    const field = screen.getByRole("textbox", { name: "Answer" }) as HTMLInputElement;
    fireEvent.change(field, { target: { value: "For launch A only." } });
    fireEvent.keyDown(field, { key: "Enter" });
    await waitFor(() => expect(posts(STEER)).toHaveLength(1));
    expect(api.request.mock.calls.every(([url]) => !String(url).includes("pane%3A"))).toBe(true);
  });

  it("a stalled send: the draft stays editable; after 20 s Answer returns and says NOT CONFIRMED; the next press is a new answer", async () => {
    await openLane(fixture());
    // The hub never answers the first send.
    let late: ((r: Response) => void) | null = null;
    api.request.mockImplementation((url: string) => {
      if (String(url).endsWith("/steer")) return new Promise<Response>((resolve) => { late = resolve; });
      return Promise.resolve({ ok: true, status: 200, json: async () => ({}) } as unknown as Response);
    });
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    try {
      const field = screen.getByRole("textbox", { name: "Answer" }) as HTMLInputElement;
      const button = within(screen.getByTestId("lane-ask")).getByRole("button", { name: "Answer" });
      fireEvent.change(field, { target: { value: "Jordan owns it." } });
      fireEvent.keyDown(field, { key: "Enter" });
      await act(async () => { await vi.advanceTimersByTimeAsync(0); });
      expect(posts(STEER)).toHaveLength(1);
      expect(button.getAttribute("aria-busy")).toBe("true");
      // Pending: the draft is still the owner's to edit.
      expect(field.disabled).toBe(false);
      fireEvent.change(field, { target: { value: "Jordan owns it. Avery reviews." } });
      expect(field.value).toBe("Jordan owns it. Avery reviews.");
      await act(async () => { await vi.advanceTimersByTimeAsync(19_999); });
      expect(button.getAttribute("aria-busy")).toBe("true");
      await act(async () => { await vi.advanceTimersByTimeAsync(1); });
      expect(button.getAttribute("aria-busy")).toBeNull();
      expect(button).not.toBeDisabled();
      const receipt = screen.getByTestId("lane-receipt");
      expect(receipt.textContent).toMatch(/^NOT CONFIRMED · \d\d:\d\d · Jordan owns it\.$/);
      expect(receipt.textContent).not.toContain("NOT SENT");
      // Nothing is sent again by itself.
      await act(async () => { await vi.advanceTimersByTimeAsync(60_000); });
      expect(posts(STEER)).toHaveLength(1);
      // A late reply to the stalled send changes nothing.
      await act(async () => {
        late?.({ ok: true, status: 200, json: async () => ({ status: "delivered" }) } as unknown as Response);
        await vi.advanceTimersByTimeAsync(0);
      });
      expect(screen.getByTestId("lane-receipt").textContent).toMatch(/^NOT CONFIRMED/);
      expect(field.value).toBe("Jordan owns it. Avery reviews.");
      // The next press sends again: a new answer to the same wait.
      answer({});
      fireEvent.keyDown(field, { key: "Enter" });
      await act(async () => { await vi.advanceTimersByTimeAsync(0); });
      expect(posts(STEER)).toEqual([
        { text: "Jordan owns it.", submit: true, kind: "answer", wait_id: "w-1" },
        { text: "Jordan owns it. Avery reviews.", submit: true, kind: "answer", wait_id: "w-1" },
      ]);
      expect(screen.getByTestId("lane-receipt").textContent).toMatch(/^SENT · /);
    } finally {
      vi.useRealTimers();
    }
  });

  it("an answer to a wait the hub no longer holds is refused and said", async () => {
    await openLane(fixture());
    answer({ "/steer": [409, { status: "wait_not_current", detail: "the question was answered or changed" }] });
    const field = screen.getByRole("textbox", { name: "Answer" }) as HTMLInputElement;
    fireEvent.change(field, { target: { value: "Late." } });
    fireEvent.keyDown(field, { key: "Enter" });
    await waitFor(() => expect(screen.getByTestId("lane-receipt").textContent).toMatch(/NOT SENT · \d\d:\d\d · QUESTION ANSWERED OR CHANGED/));
    expect(field.value).toBe("Late.");
  });

  it("Normal, unarmed: the ARM is on the lane with the mode; Answer says ARM FIRST and sends nothing; ARM arms the lane's session", async () => {
    await openLane(fixture({ control: { mode: "neutral", armed: false, direct: false } }));
    const arm = screen.getByTestId("lane-arm");
    expect(arm.textContent).toContain("ARM FIRST");
    const field = screen.getByRole("textbox", { name: "Answer" }) as HTMLInputElement;
    fireEvent.change(field, { target: { value: "Jordan." } });
    fireEvent.keyDown(field, { key: "Enter" });
    await waitFor(() => expect(screen.getByTestId("lane-receipt").textContent).toContain("ARM FIRST"));
    expect(posts("/steer")).toEqual([]);
    answer({ "/arm": [200, { status: "armed", pane_id: "%0" }] });
    fireEvent.click(within(arm).getByRole("button", { name: /ARM/ }));
    await waitFor(() => expect(posts(ARM)).toHaveLength(1));
  });

  it("Stop: Normal unarmed never arms by itself; YOLO arms per press, then kills", async () => {
    await openLane(fixture({ control: { mode: "neutral", armed: false, direct: false } }));
    fireEvent.click(screen.getByTestId("lane-stop"));
    expect(screen.getByTestId("lane-stop-confirm").textContent).toBe("Stop · sure? (ends the agent's session)");
    fireEvent.click(screen.getByTestId("lane-stop-confirm"));
    await waitFor(() => expect(screen.getByTestId("lane-receipt").textContent).toContain("ARM FIRST"));
    expect(posts("/arm")).toEqual([]);
    expect(posts("/kill")).toEqual([]);
  });

  it("Stop in YOLO: the second press arms, then kills the lane's session", async () => {
    await openLane(fixture({ control: { mode: "yolo", armed: false, direct: true } }));
    answer({ "/arm": [200, { status: "armed", pane_id: "%0" }], "/kill": [200, { status: "killed" }] });
    fireEvent.click(screen.getByTestId("lane-stop"));
    fireEvent.click(screen.getByTestId("lane-stop-confirm"));
    await waitFor(() => expect(posts(KILL)).toEqual([{ scope: "session" }]));
    expect(posts(ARM)).toHaveLength(1);
  });

  it("a stopped launch shows its receipt and withdraws Answer, Re-brief and Stop", async () => {
    await openLane(fixture({ wait: null, launch: { ...fixture().launch, state: "stopped_by_owner", stopped: { by: "owner", at: T("10:01"), audit_id: 1 } } }));
    expect(screen.getByTestId("lane-stopped").textContent).toMatch(/^STOPPED · \d\d:\d\d · BY YOU$/);
    expect(screen.queryByTestId("lane-ask")).toBeNull();
    expect(screen.queryByTestId("lane-stop")).toBeNull();
    expect(screen.queryByTestId("lane-rebrief")).toBeNull();
  });

  it("each unread collection is one line (answers, attempt, usage, session, control)", async () => {
    await openLane(fixture({
      answers: { not_read: "answers: RuntimeError" },
      attempt_events: { not_read: "attempt events: RuntimeError" },
      usage: { not_read: "usage: RuntimeError" },
    }));
    expect(screen.getByTestId("lane-not-read-answers").textContent).toBe("ANSWERS · NOT READ · answers: RuntimeError");
    expect(screen.getByTestId("lane-not-read-attempt").textContent).toBe("ATTEMPT · NOT READ · attempt events: RuntimeError");
    expect(screen.getByTestId("lane-not-read-usage").textContent).toBe("USAGE · NOT READ · usage: RuntimeError");
  });

  it("TO ANSWER: Speak answer starts the well's mic", async () => {
    await openLane(fixture(), {}, { answer: true });
    const mic = within(screen.getByTestId("lane-ask")).getByTestId("mic");
    expect(mic.getAttribute("data-auto")).toBe("true");
  });

  it("TO APPROVE: the held call with Deny / Approve; both decide through the gate route", async () => {
    await openLane(fixture({ wait: { question: "Claude needs your permission to use Bash", kind: "TO APPROVE", started: null } }));
    const well = screen.getByTestId("lane-approve-well");
    expect(within(well).queryByRole("textbox")).toBeNull();
    expect(well.textContent).toContain("psql -h staging-ledger");
    fireEvent.click(within(well).getByTestId("lane-approve"));
    await waitFor(() =>
      expect(api.fetch).toHaveBeenCalledWith("/api/gate/proposals/toolu_psql/decide", expect.objectContaining({
        method: "POST", json: expect.objectContaining({ decision: "approved" }),
      })),
    );
    fireEvent.click(within(screen.getByTestId("lane-rail")).getByTestId("lane-deny"));
    await waitFor(() =>
      expect(api.fetch).toHaveBeenCalledWith("/api/gate/proposals/toolu_psql/decide", expect.objectContaining({
        json: expect.objectContaining({ decision: "denied" }),
      })),
    );
  });

  it("PHILO-14 A5: a held call the hub cannot show whole: the head + `… +90 CHARS`, Deny and Raw, never Approve", async () => {
    // The wire as `launch_lane.gated()` builds it from the real 198-char hook
    // arrival (`db.gate.command_view`; tests/unit/test_philo14_a5_needs_drawer.py).
    const head = "psql -h staging-ledger -U ops -d payments -c 'select count(*) from entries where ledger_id = 777777777777777";
    await openLane(fixture({
      wait: { question: "Claude needs your permission to use Bash", kind: "TO APPROVE", started: null },
      gated: [{ id: "toolu_cut", tool: "Bash", args_head: `{"command":"${head}`, args_shown: head, args_cut: true, args_hidden: 90,
        state: "held", created_at: Date.parse(T("09:55")) / 1000 }],
    }));
    const well = screen.getByTestId("lane-approve-well");
    expect(well.textContent).toContain(`${head}… +90 CHARS`);
    expect(within(well).getByTestId("lane-deny")).toBeTruthy();
    expect(within(well).getByTestId("lane-raw-cut")).toBeTruthy();
    expect(screen.queryByTestId("lane-approve")).toBeNull();
    expect(within(screen.getByTestId("lane-rail")).getByText(`${head}… +90 CHARS`)).toBeTruthy();
    fireEvent.click(within(well).getByTestId("lane-raw-cut"));
    expect(useLane.getState().raw).toBe(true);
  });

  it("DECIDING: one line, no field", async () => {
    await openLane(fixture({ wait: { question: QUESTION, kind: "DECIDING", started: null } }));
    expect(screen.getByTestId("lane-deciding").textContent).toContain(QUESTION);
    expect(screen.queryByRole("textbox", { name: "Answer" })).toBeNull();
  });

  it("no wait: no well, no empty box", async () => {
    await openLane(fixture({ wait: null }));
    expect(screen.queryByTestId("lane-ask")).toBeNull();
    expect(screen.queryByTestId("lane-approve-well")).toBeNull();
    expect(screen.queryByTestId("lane-deciding")).toBeNull();
  });

  it("no PR: no GITHUB.COM chip and no Open PR", async () => {
    await openLane(fixture({ follow_through: { pr: null, merged: null } }));
    expect(screen.queryByText("GITHUB.COM")).toBeNull();
    expect(screen.queryByTestId("lane-open-pr")).toBeNull();
    expect(screen.queryByTestId("lane-pr")).toBeNull();
  });

  it("Raw puts the terminal pane in place of the lane, and back", async () => {
    await openLane(fixture());
    const raw = screen.getByTestId("lane-raw");
    fireEvent.click(raw);
    expect(screen.getByTestId("lane-raw-pane")).toBeTruthy();
    expect(screen.queryByTestId("lane-rail")).toBeNull();
    expect(raw.getAttribute("aria-pressed")).toBe("true");
    fireEvent.click(raw);
    expect(screen.queryByTestId("lane-raw-pane")).toBeNull();
    expect(screen.getByTestId("lane-rail")).toBeTruthy();
  });

  it("Re-brief opens the steer well prefilled; its receipt stays after the well closes", async () => {
    await openLane(fixture({ wait: null }));
    fireEvent.click(screen.getByTestId("lane-rebrief"));
    const field = within(screen.getByTestId("lane-rebrief-well")).getByRole("textbox", { name: "Re-brief" }) as HTMLInputElement;
    expect(field.value).toBe("Re-brief: ");
    fireEvent.change(field, { target: { value: "Re-brief: name Jordan as the owner." } });
    fireEvent.keyDown(field, { key: "Enter" });
    // PHILO-15 B46: the Re-brief route of the launch (typed now, or queued mid-turn).
    await waitFor(() => expect(posts(REBRIEF)).toEqual([{ text: "Re-brief: name Jordan as the owner." }]));
    expect(posts(STEER)).toEqual([]);
    await waitFor(() => expect(screen.queryByTestId("lane-rebrief-well")).toBeNull());
    expect(screen.getByTestId("lane-receipt").textContent).toContain("SENT");
    expect(screen.getByTestId("lane-receipt").textContent).toContain("Re-brief: name Jordan as the owner.");
  });

  it("pages the events: the next read asks after the last event and appends", async () => {
    const first = fixture({ events_next_after: 9 });
    await openLane(first);
    expect(api.fetch).toHaveBeenCalledWith("/api/agent/launches/launch_f2_runbook/lane?after=0&limit=200");
    serve(fixture({ events: [{ id: 10, ts: T("09:50"), event: "PostToolUse", tool: "Edit", head: "ledger/freeze.py" }], events_next_after: null }));
    await act(async () => {
      await useLane.getState().load();
    });
    expect(api.fetch).toHaveBeenCalledWith("/api/agent/launches/launch_f2_runbook/lane?after=9&limit=200");
    expect(useLane.getState().events.map((e) => e.id)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
    expect(useLane.getState().more).toBe(false);
  });
});

describe("which window a session opens", () => {
  it("a plain session keeps the session window; a launch's session opens the lane", async () => {
    serve(fixture());
    steering({ openKey: KEY });
    const { unmount } = render(<><SessionPullout /><LaneWindow /></>);
    expect(document.querySelector(".is-session")).toBeTruthy();
    expect(document.querySelector(".is-lane")).toBeNull();
    unmount();

    useAgentFlights.setState({ flights: [fromWireFlight({ origin_ref: "action:a1", title: "Write the rollback runbook", agent: "claude", state: "waiting", session_key: KEY, launch_id: "launch_f2_runbook" })] });
    render(<><SessionPullout /><LaneWindow /></>);
    await waitFor(() => expect(document.querySelector(".is-lane")).toBeTruthy());
    expect(document.querySelector(".is-session")).toBeNull();
    await waitFor(() => expect(useLane.getState().launchId).toBe("launch_f2_runbook"));
  });
});

describe("PHILO-15 lane 14: the stations tell the truth", () => {
  it("B42: BRIEF reads the delivery time, not the launch time; a held brief reads waiting", () => {
    const sent = fixture({ launch: { ...fixture().launch, launched_at: "2026-10-07T16:26:00Z", instruction_state: "sent", brief_sent_at: "2026-10-07T16:29:00Z" } });
    const [brief] = laneStations(sent, []);
    const clock = (iso: string) => wireClock(iso);
    expect(brief).toMatchObject({ word: "BRIEF", state: "reached", sub: clock("2026-10-07T16:29:00Z") });
    expect(brief.sub).not.toBe(clock("2026-10-07T16:26:00Z"));
    const railBrief = laneEntries(sent, []).find((e) => e.word === "BRIEF");
    expect(railBrief?.time).toBe(clock("2026-10-07T16:29:00Z"));

    const held = fixture({ launch: { ...fixture().launch, instruction_state: "pending", brief_sent_at: null } });
    expect(laneStations(held, [])[0]).toMatchObject({ word: "BRIEF", sub: "waiting", state: "current", tone: "warn" });
    const railHeld = laneEntries(held, []).find((e) => e.word === "BRIEF");
    expect(railHeld).toMatchObject({ time: "", pending: true });
    expect(railHeld?.text).toContain("waiting");
    const refused = fixture({ launch: { ...fixture().launch, instruction_state: "expired" } });
    expect(laneStations(refused, [])[0]).toMatchObject({ sub: "not sent", tone: "fail" });
  });

  it("B48: a turn end with no question reads IDLE, with the PR open DONE; ASKS only for a question", () => {
    const at = (turn: string | undefined) =>
      laneStations(fixture({ wait: { ...(fixture().wait as object), kind: "TO ANSWER", turn_end: turn } as never }), []).find((s) => s.word !== "MERGE" && ["ASKS", "IDLE", "DONE"].includes(String(s.word)));
    expect(at("asks")).toMatchObject({ word: "ASKS", sub: "now", state: "current", tone: "ask" });
    expect(at("idle")).toMatchObject({ word: "IDLE", state: "current", tone: "info" });
    expect(at("done")).toMatchObject({ word: "DONE", state: "reached", tone: "ok" });
    const approve = laneStations(fixture({ wait: { question: "Run psql?", kind: "TO APPROVE", turn_end: "asks" } }), []);
    expect(approve.find((s) => s.word === "ASKS")).toMatchObject({ sub: "now" });
  });

  it("B48: the well of an idle turn end says IDLE, not ASKS", async () => {
    await openLane(fixture({ wait: { ...(fixture().wait as object), turn_end: "idle", question: "Understood — stopping here." } as never }));
    expect(screen.getByText(/^CLAUDE CODE IDLE/)).toBeTruthy();
    expect(screen.queryByText(/^CLAUDE CODE ASKS/)).toBeNull();
    expect(within(screen.getByTestId("lane-track")).getByText("IDLE")).toBeTruthy();
  });

  it("B50: the PR card names the PR's own title and number; the item is the second line", async () => {
    useAgentFlights.setState({ flights: [fromWireFlight({ origin_ref: "action:a1", title: "Write the rollback runbook", agent: "claude", state: "pr_open", session_key: KEY, launch_id: "launch_f2_runbook" })] });
    const base = fixture();
    await openLane(fixture({ follow_through: { ...base.follow_through, pr: { ...base.follow_through.pr!, title: "Add the ledger rollback runbook" } } }));
    const pr = screen.getByTestId("lane-pr");
    expect(pr.querySelector(".pr-card-title")?.textContent).toBe("#413 Add the ledger rollback runbook");
    expect(screen.getByTestId("lane-pr-item").textContent).toBe("Write the rollback runbook");
  });

  it("B50: with no PR title read yet, the card keeps the item and draws no second line", async () => {
    useAgentFlights.setState({ flights: [fromWireFlight({ origin_ref: "action:a1", title: "Write the rollback runbook", agent: "claude", state: "pr_open", session_key: KEY, launch_id: "launch_f2_runbook" })] });
    await openLane(fixture());
    expect(screen.getByTestId("lane-pr").querySelector(".pr-card-title")?.textContent).toBe("#413 Write the rollback runbook");
    expect(screen.queryByTestId("lane-pr-item")).toBeNull();
  });

  it("B46: a Re-brief mid-turn says QUEUED · AFTER THIS TURN, and the lane keeps it until the turn ends", async () => {
    await openLane(fixture({ wait: null }));
    answer({ [REBRIEF]: [202, { status: "queued", at: "2026-10-07T16:40:00Z" }] });
    serve(fixture({ wait: null, launch: { ...fixture().launch, queued_rebrief: { text: "Re-brief: use the security address.", at: "2026-10-07T16:40:00Z" } } }));
    fireEvent.click(screen.getByTestId("lane-rebrief"));
    const field = within(screen.getByTestId("lane-rebrief-well")).getByRole("textbox", { name: "Re-brief" }) as HTMLInputElement;
    fireEvent.change(field, { target: { value: "Re-brief: use the security address." } });
    fireEvent.keyDown(field, { key: "Enter" });
    await waitFor(() => expect(screen.getByTestId("lane-queued").textContent).toBe("QUEUED · AFTER THIS TURN · Re-brief: use the security address."));
    expect(screen.queryByTestId("lane-rebrief-well")).toBeNull();
    expect(posts(STEER)).toEqual([]);

    // The turn ends; the hub types it. The same mounted lane says SENT, not QUEUED.
    serve(fixture({ wait: null, answers: [{ id: 9, ts: "2026-10-07T16:52:00Z", outcome: "delivered", text_head: "Re-brief: use the security address." }] }));
    await act(async () => {
      await useLane.getState().load();
    });
    await waitFor(() => expect(screen.queryByTestId("lane-queued")).toBeNull());
    expect(screen.getByTestId("lane-receipt").textContent).toBe(`SENT · ${wireClock("2026-10-07T16:52:00Z")} · Re-brief: use the security address.`);
    expect(screen.queryByText(/QUEUED/)).toBeNull();
  });

  it("provenance: the rail shows each Re-brief receipt with the press that approved it and the delivery's command id", async () => {
    const rebriefs = [
      { id: "p1", state: "sent", text_head: "Re-brief: use the security address.", approved_at: "2026-10-07T16:40:00Z",
        at: "2026-10-07T16:52:00Z", press_id: "p1", command_id: "c0ffee00-0000-5000-8000-000000000001", how: "after_turn" },
      { id: "p2", state: "expired", text_head: "Re-brief: late.", approved_at: "2026-10-07T14:00:00Z",
        at: "2026-10-07T16:01:00Z", press_id: "p2", command_id: null, detail: "AGENT NEVER RETURNED" },
      { id: "p3", state: "superseded", text_head: "Re-brief: first.", approved_at: "2026-10-07T16:41:00Z",
        at: "2026-10-07T16:43:00Z", press_id: "p3", command_id: null, detail: "A NEWER RE-BRIEF" },
    ];
    await openLane(fixture({ wait: null, launch: { ...fixture().launch, rebriefs: rebriefs as never } }));
    const rail = screen.getByTestId("lane-rail");
    expect(within(rail).getByText(`SENT · ${wireClock("2026-10-07T16:52:00Z")} · BY YOUR PRESS ${wireClock("2026-10-07T16:40:00Z")}`)).toBeTruthy();
    expect(within(rail).getByText("command c0ffee00-0000-5000-8000-000000000001")).toBeTruthy();
    expect(within(rail).getByText(`EXPIRED · ${wireClock("2026-10-07T16:01:00Z")} · AGENT NEVER RETURNED · BY YOUR PRESS ${wireClock("2026-10-07T14:00:00Z")}`)).toBeTruthy();
    expect(within(rail).getByText(/^SUPERSEDED · .* · A NEWER RE-BRIEF · BY YOUR PRESS/)).toBeTruthy();
    expect(within(rail).getByText("press p3")).toBeTruthy();
  });

  it("two queued Re-briefs each say when they go", async () => {
    await openLane(fixture({ wait: null, launch: { ...fixture().launch, queued_rebriefs: [
      { id: "a", text: "Re-brief: a.", at: "2026-10-07T16:40:00Z" }, { id: "b", text: "Re-brief: b.", at: "2026-10-07T16:41:00Z" },
    ] } }));
    expect(screen.getAllByTestId("lane-queued").map((el) => el.textContent)).toEqual([
      "QUEUED · AFTER THIS TURN · Re-brief: a.", "QUEUED · AFTER 2 TURNS · Re-brief: b.",
    ]);
  });

  it("B46: a YOLO answer names the registered pane, so the hub's registered-destination rule passes", async () => {
    await openLane(fixture({ control: { mode: "yolo", armed: false, direct: true, pane_id: "%42" } }));
    const field = within(screen.getByTestId("lane-ask")).getByRole("textbox") as HTMLInputElement;
    fireEvent.change(field, { target: { value: "Jordan." } });
    fireEvent.keyDown(field, { key: "Enter" });
    await waitFor(() => expect(posts(STEER)[0]).toMatchObject({ text: "Jordan.", expected_pane_id: "%42", kind: "answer" }));
  });
});

// PHILO-15 20 (B63, B67): Raw shows a cut held call whole, read from the
// hub, with Deny and Approve; a queued Re-brief has Take back.
describe("PHILO-15 20: Raw approves a cut call; Take back", () => {
  const head = 'cd /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs-r2.faJEcODmah/.holdspeak/repositories/karolsw';
  const whole = `${head}dev/holdspeak-dayone-rehearsal-1558 && git status --short && echo done`;
  const cutLane = () => fixture({
    wait: { question: "Codex needs your permission to use Bash", kind: "TO APPROVE", started: null },
    gated: [{ id: "toolu_cut", tool: "Bash", args_head: `{"command":"${head}`, args_shown: head, args_cut: true,
      args_hidden: whole.length - head.length, state: "held", hold_reason: "OUTSIDE THE WORKTREE",
      created_at: Date.parse(T("09:55")) / 1000 }],
  });

  function serveWhole(lane: LaneWire, body: Record<string, unknown>) {
    serve(lane);
    const base = api.fetch.getMockImplementation()!;
    api.fetch.mockImplementation(async (url: string, init?: RequestInit) => {
      if (String(url) === "/api/gate/proposals/toolu_cut/command") return body;
      return base(url, init);
    });
  }

  it("B63: Raw reads the whole command from the hub and approves it there", async () => {
    await openLane(cutLane());
    serveWhole(cutLane(), { id: "toolu_cut", state: "held", command: whole, whole: true, hold_reason: "OUTSIDE THE WORKTREE" });
    fireEvent.click(within(screen.getByTestId("lane-approve-well")).getByTestId("lane-raw-cut"));
    const held = await screen.findByTestId("lane-raw-held");
    await waitFor(() => expect(within(held).getByTestId("lane-raw-command").textContent).toBe(whole));
    expect(within(held).getByText("HELD · OUTSIDE THE WORKTREE")).toBeTruthy();
    expect(within(held).getByTestId("lane-raw-deny")).toBeTruthy();
    fireEvent.click(within(held).getByTestId("lane-raw-approve"));
    await waitFor(() => expect(api.fetch.mock.calls.some(([url, init]) =>
      String(url) === "/api/gate/proposals/toolu_cut/decide" && (init as { json?: { decision?: string } })?.json?.decision === "approved")).toBe(true));
    // Astra r1 on #1011 (P2-6): the decision leaves its receipt on Raw.
    await waitFor(() => expect(screen.getByTestId("lane-receipt").textContent).toMatch(/^APPROVED · \d\d:\d\d$/));
    expect(screen.getByTestId("lane-raw-pane")).toBeTruthy();
  });

  it("B63: a call decided elsewhere first says NOT DECIDED · ALREADY DENIED", async () => {
    await openLane(cutLane());
    serveWhole(cutLane(), { id: "toolu_cut", state: "held", command: whole, whole: true, hold_reason: "OUTSIDE THE WORKTREE" });
    const base = api.fetch.getMockImplementation()!;
    const { ApiError } = await import("../../../lib/api");
    api.fetch.mockImplementation(async (url: string, init?: RequestInit) => {
      if (String(url).endsWith("/decide")) throw new ApiError(409, "conflict", { error: "already_decided", state: "denied" });
      return base(url, init);
    });
    act(() => useLane.getState().setRaw(true));
    const held = await screen.findByTestId("lane-raw-held");
    await waitFor(() => expect(within(held).getByTestId("lane-raw-approve")).toBeTruthy());
    fireEvent.click(within(held).getByTestId("lane-raw-approve"));
    await waitFor(() => expect(screen.getByTestId("lane-receipt").textContent).toMatch(/^NOT DECIDED · \d\d:\d\d · ALREADY DENIED$/));
  });

  it("B63: a call the hub did not keep whole is Deny only", async () => {
    await openLane(cutLane());
    serveWhole(cutLane(), { id: "toolu_cut", state: "held", command: head, whole: false, hold_reason: "OUTSIDE THE WORKTREE",
      shown_chars: head.length, declared_chars: whole.length });
    act(() => useLane.getState().setRaw(true));
    const held = await screen.findByTestId("lane-raw-held");
    await waitFor(() => expect(within(held).getByTestId("lane-raw-command").textContent).toBe(head));
    // Astra r1 on #1011 (P1-2): a part says how much of the call is there.
    expect(within(held).getByText(`HELD · OUTSIDE THE WORKTREE · CUT · ${head.length} OF ${whole.length} CHARS`)).toBeTruthy();
    expect(within(held).queryByTestId("lane-raw-approve")).toBeNull();
    expect(within(held).getByTestId("lane-raw-deny")).toBeTruthy();
  });

  it("B63: open on Raw binds the lane's session and shows Raw first", async () => {
    serve(cutLane());
    answer({});
    steering();
    render(<LaneWindow />);
    await act(async () => {
      await useLane.getState().open("launch_f2_runbook", { sessionKey: KEY, raw: true });
    });
    expect(useLane.getState().raw).toBe(true);
    expect(useSteering.getState().openSession).toHaveBeenCalledWith(KEY);
    expect(await screen.findByTestId("lane-raw-pane")).toBeTruthy();
  });

  it("B67: Take back discards a queued Re-brief and says TAKEN BACK", async () => {
    const queued = fixture({ wait: null, launch: { ...fixture().launch, queued_rebriefs: [
      { id: "press-1", text: "Re-brief: do not write outside the worktree.", at: "2026-10-07T21:30:00Z" },
    ] } });
    await openLane(queued);
    answer({ [`${REBRIEF}/press-1/take-back`]: [200, { status: "taken_back" }] });
    serve(fixture({ wait: null }));
    fireEvent.click(screen.getByTestId("lane-take-back"));
    await waitFor(() => expect(screen.getByTestId("lane-receipt").textContent).toMatch(/^TAKEN BACK · .* · Re-brief: do not write outside/));
    expect(posts(`${REBRIEF}/press-1/take-back`)).toEqual([{}]);
    await waitFor(() => expect(screen.queryByTestId("lane-queued")).toBeNull());
  });

  it("B67: a Re-brief already typed is NOT TAKEN BACK · ALREADY SENT", async () => {
    await openLane(fixture({ wait: null, launch: { ...fixture().launch, queued_rebriefs: [
      { id: "press-2", text: "Re-brief: two.", at: "2026-10-07T21:30:00Z" },
    ] } }));
    answer({ [`${REBRIEF}/press-2/take-back`]: [409, { status: "not_queued" }] });
    fireEvent.click(screen.getByTestId("lane-take-back"));
    await waitFor(() => expect(screen.getByTestId("lane-receipt").textContent).toMatch(/^NOT TAKEN BACK · .* · ALREADY SENT$/));
  });

  it("the rail names a taken-back press", async () => {
    await openLane(fixture({ wait: null, launch: { ...fixture().launch, rebriefs: [
      { id: "p9", state: "taken_back", text_head: "Re-brief: x.", approved_at: "2026-10-07T21:30:00Z",
        at: "2026-10-07T21:31:00Z", press_id: "p9", command_id: null, detail: "BY YOU" },
    ] as never } }));
    expect(within(screen.getByTestId("lane-rail")).getByText(
      `TAKEN BACK · ${wireClock("2026-10-07T21:31:00Z")} · BY YOU · BY YOUR PRESS ${wireClock("2026-10-07T21:30:00Z")}`,
    )).toBeTruthy();
  });
});
