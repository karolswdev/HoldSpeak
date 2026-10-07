// PHILO-14 C2 (ratified board A-4 + C-4's station track): the agent's lane
// window renders each section from the lane JSON (`GET /api/agent/launches/
// {id}/lane`), says every unread part in one line, draws the three kinds of
// wait, sends an answer on Enter through the steer route, decides a held call
// through the gate route, and puts the terminal pane behind Raw.
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const api = vi.hoisted(() => ({ fetch: vi.fn() }));
vi.mock("../../../lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../lib/api")>()),
  apiFetch: api.fetch,
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
    wait: { question: QUESTION, kind: "TO ANSWER", started: new Date(Date.now() - 6 * 60_000).toISOString(),
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

function steering(over: Record<string, unknown> = {}) {
  const steer = vi.fn(async () => true);
  act(() => {
    useSteering.setState({
      openKey: KEY, session: null, paneStatus: "no_pane", armed: false, postureAuthorized: false,
      steerState: "idle", steerDetail: "", answerSeq: 0, answerOpen: false,
      openSession: vi.fn(), closeSession: vi.fn(), steer, ...over,
    } as never);
  });
  return steer;
}

async function openLane(lane: LaneWire, over: Record<string, unknown> = {}) {
  serve(lane);
  const steer = steering(over);
  render(<LaneWindow />);
  await act(async () => {
    await useLane.getState().open("launch_f2_runbook", { sessionKey: KEY });
  });
  await screen.findByTestId("lane-track");
  return steer;
}

beforeEach(() => {
  api.fetch.mockReset();
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
      ["HELD", "1 call", "current"],
      ["ASKS", "now", "current"],
      ["MERGE", "yours", "ahead"],
    ]);
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
    expect(screen.getByTestId("lane-question").textContent).toBe(QUESTION);
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
    await waitFor(() => expect(within(screen.getByTestId("lane-draft")).getByText("API.ANTHROPIC.COM")).toBeTruthy());
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

  it("TO ANSWER: Use draft fills the field and does not send; Enter sends through the steer route", async () => {
    const steer = await openLane(fixture());
    const field = screen.getByRole("textbox", { name: "Answer" }) as HTMLInputElement;
    fireEvent.click(screen.getByTestId("lane-use-draft"));
    expect(field.value).toBe("Jordan owns it. Avery reviews.");
    expect(steer).not.toHaveBeenCalled();
    fireEvent.change(field, { target: { value: "Jordan owns it." } });
    fireEvent.keyDown(field, { key: "Enter" });
    await waitFor(() => expect(steer).toHaveBeenCalledWith("Jordan owns it.", true));
    await waitFor(() => expect(field.value).toBe(""));
  });

  it("TO ANSWER: Speak answer starts the well's mic", async () => {
    await openLane(fixture(), { answerSeq: 3, answerOpen: true });
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

  it("Re-brief opens the steer well prefilled; Stop asks twice", async () => {
    const steer = await openLane(fixture({ wait: null }));
    fireEvent.click(screen.getByTestId("lane-rebrief"));
    const field = within(screen.getByTestId("lane-rebrief-well")).getByRole("textbox", { name: "Re-brief" }) as HTMLInputElement;
    expect(field.value).toBe("Re-brief: ");
    fireEvent.change(field, { target: { value: "Re-brief: name Jordan as the owner." } });
    fireEvent.keyDown(field, { key: "Enter" });
    await waitFor(() => expect(steer).toHaveBeenCalledWith("Re-brief: name Jordan as the owner.", true));
    fireEvent.click(screen.getByTestId("lane-stop"));
    expect(screen.getByTestId("lane-stop-confirm").textContent).toBe("Stop · sure?");
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
    steering();
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
