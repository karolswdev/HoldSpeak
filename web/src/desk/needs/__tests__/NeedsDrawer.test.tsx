// PHILO-14 A5 — Needs you as a smart drawer (board A-5). The drawer reads the
// hub's one answer (`/api/desk/needs-you`) and draws each member as its
// object: icon by kind, name, one fact line, ONE lamp + word, its own verbs.
//
// Stable testids: `needs-drawer` (the body), `needs-row` (a member's row),
// `needs-source-row` (a source not read, no calendar), `needs-row-verb`
// (every row verb; `data-verb` names it: answer, open, deny, approve,
// open-pr, review, done, name-owner, set-date, confirm, defer, decline, door-verb,
// summarize, setup, repair, cancel, connect-calendar), `needs-well`,
// `needs-next` (a strip token), `needs-filter` (the FilterBar; its
// `Muted` token opens `needs-muted`).
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch } from "../../../lib/api";
import { useAgentFlights, type AgentFlight } from "../../agentFlights";
import { openCoderSession, openSurfaceOr } from "../../shell";
import { useDesk } from "../../store";
import { WindowIdContext } from "../../components/window/windowIdContext";
import { ApplicationMenu } from "../../components/DeskMenuBar";
import { NeedsDrawer, useDropped, useSourceReceipt } from "../NeedsDrawer";
import { useArmingOutcome } from "../arming";
import { useState as useHarnessState, type ReactNode } from "react";
import { ProjectRoomCore } from "../../../features/project-room/ProjectRoomCore";
import { TitleSlotContext } from "../../surface/title";
import { WingSlotContext } from "../../surface/wings";
import { useDrawers } from "../../drawer/store";
// PG-DIRECTION DIR3: recorded by tests/integration/test_desk_reach.py.
import needsPageNone from "../../programs/__fixtures__/needs_you.page_none.json";
import needsPageOpen from "../../programs/__fixtures__/needs_you.page_open.json";
import reachPackage from "../../programs/__fixtures__/reach.package.json";
// PG-DIRECTION DIR4/DIR5: recorded by tests/integration/test_desk_reach_settings.py.
import needsLater from "../../reach/__fixtures__/needs_you.later.json";
import needsSent from "../../reach/__fixtures__/needs_you.sent.json";
// Owner walk 2026-11-08: recorded by scripts/record_needs_you_fixture.py --rows
// (the owner's own findings titled Must fix / Should fix / Noted, a plain one,
// one Bea owes; Done on the Must fix row, and the read after).
import needsRows from "../__fixtures__/needs_you.rows.json";
import { recordedGet, type Gets } from "../../../test/recordedHub";
import { INTELLIGENCE_NAVIGATE, openIntelligence } from "../../intelligenceNavigation";
import { openProgram } from "../../programs/open";
import madeFromAction from "../../programs/__fixtures__/program.from_action.json";
import { markDone, readDoneReceipt } from "../needsApi";
import { readdirSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: vi.fn(),
}));
vi.mock("../../shell", async (original) => ({
  ...(await original<typeof import("../../shell")>()),
  openCoderSession: vi.fn(),
  openSurfaceOr: vi.fn(),
}));
vi.mock("../../components/MicButton", () => ({ MicButton: () => null }));
vi.mock("../../programs/open", async (original) => ({
  ...(await original<typeof import("../../programs/open")>()),
  openProgram: vi.fn(),
}));
// One Done (2026-11-08): every Done goes through needsApi's markDone (a spy
// over the real function).
vi.mock("../needsApi", async (original) => {
  const real = await original<typeof import("../needsApi")>();
  return { ...real, markDone: vi.fn(real.markDone) };
});
vi.mock("../../intelligenceNavigation", async (original) => ({
  ...(await original<typeof import("../../intelligenceNavigation")>()),
  openIntelligence: vi.fn(),
}));

const NOW = Date.now();
const ago = (minutes: number) => new Date(NOW - minutes * 60_000).toISOString();

const FLIGHT: AgentFlight = {
  originRef: "action:ai-flag",
  kind: "action",
  id: "ai-flag",
  title: "Add the ledger freeze flag",
  projectId: "p1",
  projectName: "Payments ledger",
  agent: "claude",
  state: "pr_open",
  sessionKey: "claude:s-flag",
  pr: { number: 412, url: "https://github.com/acme/ledger/pull/412", state: "open" },
  close: null,
  sessionCleanup: null,
  mergedAt: null,
  launchId: null,
};
const WORKING: AgentFlight = {
  ...FLIGHT,
  originRef: "action:ai-worked",
  id: "ai-worked",
  title: "Write the rollback runbook",
  state: "working",
  sessionKey: "claude:s-worked",
  pr: null,
};

const ITEMS = [
  {
    id: "coder:claude:s-run", ref: "coder:claude:s-run", kind: "coder", source: "coder",
    title: "The runbook needs a rollback owner. Jordan or Avery?",
    question: "The runbook needs a rollback owner. Jordan or Avery?",
    why: "TO ANSWER", severity: "warning", sessionKey: "claude:s-run", agent: "claude",
    waitKind: "answer", waitStartedAt: ago(6), since: ago(6), projectId: "", projectName: "rollback runbook",
  },
  {
    id: "gate:prop-1", ref: "gate:prop-1", kind: "gate", source: "gate",
    title: "Approve: psql -h staging-ledger -c 'select count(*) from entries'",
    why: "TO APPROVE", severity: "warning", sessionKey: "codex:s-recon", waitKind: "approve",
    since: ago(2), projectId: "", projectName: "reconciliation",
  },
  {
    id: "door:ai-flag", ref: "ai-flag", kind: "action_item", source: "action_item",
    title: "Add the ledger freeze flag", why: "Due today", severity: "warning",
    projectId: "p1", projectName: "Payments ledger", owner: null,
    _isDoor: true, _isUnassigned: false,
    _doorCard: { id: "ai-flag", target_ref: "action_item:ai-flag" },
  },
  {
    id: "door:ai-worked", ref: "ai-worked", kind: "action_item", source: "action_item",
    title: "Write the rollback runbook", why: "Unassigned", severity: "warning",
    projectId: "p1", projectName: "Payments ledger", owner: null,
    _isDoor: true, _isUnassigned: true,
    _doorCard: { id: "ai-worked", target_ref: "action_item:ai-worked" },
  },
  {
    id: "decision:d-ops", ref: "decision:d-ops", kind: "decision", source: "decision",
    title: "Run a second ops interview", why: "To review", severity: "warning",
    projectId: "p2", projectName: "Staff hiring loop", openRef: "decision:d-ops",
  },
  {
    id: "commitment:c-sam", ref: "commitment:c-sam", kind: "commitment", source: "commitment",
    title: "Sam: send the status by Thursday", why: "Due today", severity: "warning",
    projectId: "p3", projectName: "1:1", owner: "Sam Rivera", actionItemId: "ai-sam",
    nextAction: "mark_done",
  },
  {
    id: "door:ai-orphan", ref: "ai-orphan", kind: "action_item", source: "action_item",
    title: "Pick the vendor", why: "Unassigned", severity: "warning",
    projectId: "p1", projectName: "Payments ledger", owner: null,
    _isDoor: true, _isUnassigned: true,
    _doorCard: {
      id: "ai-orphan", target_ref: "action_item:ai-orphan",
      lawful_verbs: [{ name: "follow_through.complete", arguments: { card_id: "ai-orphan", verb: "delegate" } }],
    },
  },
];

const ANSWER = {
  count: 8,
  items: ITEMS,
  blockers: [],
  failedMeetings: [
    {
      id: "m-vendor", title: "Vendor call", started_at: ago(90), ended_at: ago(70),
      duration_seconds: 1200, intel_status: "error",
      intel_job: { status: "failed", attempts: 1, last_error: "timeout" },
    },
  ],
  coverage: [],
  complete: true,
};

const REAL_START = useDesk.getState().startRecording;
let gateCalls: Array<{ path: string; json: unknown }> = [];
const REAL_CANCEL = useDesk.getState().cancelArmedSchedule;
let DOOR: Record<string, unknown> = { upcoming: [], calendar_configured: true };

beforeEach(() => {
  // Betterment D3: a Drop's Undo receipt lives 8 s in its store; one test's
  // Drop never reaches the next test's foot.
  useDropped.getState().set(null);
  gateCalls = [];
  DOOR = { upcoming: [], calendar_configured: true };
  useDesk.setState({ scheduledArming: null, cancelArmedSchedule: REAL_CANCEL, startRecording: REAL_START } as never);
  useArmingOutcome.setState({ refusal: null, receipt: null, busy: false });
  (globalThis as { __resetNeedsYou?: () => void }).__resetNeedsYou?.();
  useAgentFlights.setState({ flights: [FLIGHT, WORKING], sessions: [] } as never);
  vi.mocked(openCoderSession).mockClear();
  vi.mocked(apiFetch).mockImplementation(async (path: string, init?: unknown) => {
    const value = String(path);
    if (value.startsWith("/api/desk/needs-you")) return ANSWER as never;
    if (value.startsWith("/api/gate/proposals/")) {
      gateCalls.push({ path: value, json: (init as { json?: unknown })?.json });
      return { ok: true } as never;
    }
    if (value.startsWith("/api/gate/proposals")) return { proposals: [] } as never;
    if (value === "/api/door") return DOOR as never;
    return {} as never;
  });
});

function row(name: RegExp | string): HTMLElement {
  const rows = screen.getAllByRole("listitem").filter((li) => li.classList.contains("needs-row"));
  const hit = rows.find((li) =>
    typeof name === "string"
      ? li.querySelector(".needs-row-name")?.textContent === name
      : name.test(li.querySelector(".needs-row-name")?.textContent ?? ""));
  if (!hit) throw new Error(`no row ${String(name)}`);
  return hit;
}

function face(li: HTMLElement) {
  return {
    kind: li.getAttribute("data-kind"),
    fact: li.querySelector(".needs-row-fact")?.textContent ?? "",
    lamps: [...li.querySelectorAll("[data-testid=needs-row-state]")].map((n) => n.textContent),
    verbs: [...li.querySelectorAll(".needs-row-verbs button")].map((b) => b.textContent),
    egress: li.querySelector(".needs-row-verbs .egress-chip, .needs-row-verbs [class*='egress']")?.textContent ?? "",
    plate: li.querySelector("[data-testid='kit-kind']")?.textContent ?? "",
    // Window grammar: the row leads with its glyph; its alt names the kind.
    glyph: li.querySelector(":scope > img")?.getAttribute("alt") ?? "",
  };
}

async function mount() {
  render(<NeedsDrawer />);
  await screen.findByText("8 need you");
}

describe("NeedsDrawer (PHILO-14 A5, board A-5)", () => {
  it("names a speech setup blocker by its capability", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (String(path).startsWith("/api/desk/needs-you")) {
        return {
          items: [],
          blockers: [{ key: "speech", label: "No engine for speech", verb: "Choose an engine" }],
          failedMeetings: [],
          coverage: [],
          complete: true,
        } as never;
      }
      if (path === "/api/door") return { ...DOOR } as never;
      return {} as never;
    });
    render(<NeedsDrawer />);
    await screen.findByText("1 needs you");
    expect(face(row("No engine for speech"))).toMatchObject({
      fact: "Speech",
      verbs: ["Choose an engine"],
    });
  });

  it("re-reads a failed setup path with fresh data when Try again is pressed", async () => {
    const reads: string[] = [];
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      const value = String(path);
      if (value.startsWith("/api/desk/needs-you")) {
        reads.push(value);
        return {
          items: [],
          blockers: [{ key: "unknown", label: "Could not read setup", verb: "Try again" }],
          failedMeetings: [], coverage: [], complete: false,
        } as never;
      }
      if (value === "/api/door") return { ...DOOR } as never;
      return {} as never;
    });
    render(<NeedsDrawer />);
    const button = await screen.findByRole("button", { name: "Try again: Could not read setup" });
    expect(reads).toEqual(["/api/desk/needs-you"]);
    fireEvent.click(button);
    await waitFor(() => expect(reads.at(-1)).toBe("/api/desk/needs-you?fresh=1"));
  });

  it("a Secure helper request has one Allow press with its exact request id", async () => {
    const allow = vi.fn();
    vi.mocked(apiFetch).mockImplementation(async (path: string, init?: unknown) => {
      if (String(path).startsWith("/api/desk/needs-you")) return {
        ...ANSWER, count: 9, items: [...ITEMS, {
          id: "coder:launch:parent:helper", ref: "coder:launch:parent:helper",
          kind: "coder", source: "coder", title: "Review the runbook", question: "Review the runbook",
          why: "TO APPROVE", severity: "warning", sessionKey: "", launchId: "parent",
          agent: "claude", counted: true,
          helperRequest: { status: "awaiting_owner", requestId: "helper-request-1" },
        }],
      } as never;
      if (path === "/api/agent/launches/parent/helper/allow") { allow(init); return { status: "launched" } as never; }
      return { ...DOOR } as never;
    });
    render(<NeedsDrawer />);
    const button = await screen.findByRole("button", { name: /^Allow helper:/ });
    fireEvent.click(button);
    await waitFor(() => expect(allow).toHaveBeenCalledWith({
      method: "POST", json: { request_id: "helper-request-1" },
    }));
  });

  it("heads with the hub's number, once, and nothing else", async () => {
    await mount();
    const drawer = screen.getByTestId("needs-drawer");
    expect(screen.getByTestId("arrival-display").textContent).toBe("8 need you");
    // The bold mast (2026-11-08): one title, the day and the head (no must
    // fix here); the status bar says the number once, with its lamp.
    const titles = drawer.querySelectorAll("h1, h2");
    expect(titles.length).toBe(1);
    expect(titles[0].textContent).toMatch(/^(Sun|Mon|Tues|Wednes|Thurs|Fri|Satur)day · 8 need you$/);
    expect(drawer.querySelectorAll(".kit-disp").length).toBe(0);
    expect(screen.getByTestId("arrival-display").closest(".kit-statusbar")).toBeTruthy();
    expect(screen.getAllByText("8 need you")).toHaveLength(1);
    expect(screen.getByTestId("needs-mast").querySelector(".surface-mast-glyph")?.getAttribute("src")).toMatch(/dock-intelligence\.png$/);
    // DELIGHT slice 2: the number wears the tick (it fades only on a change, never on the first paint).
    const tick = screen.getByTestId("arrival-display").querySelector(".kit-tick");
    expect(tick?.textContent).toBe("8 need you");
    expect(tick?.hasAttribute("data-tick")).toBe(false);
  });

  it("draws every member as its object: icon, name, fact, one lamp, its verbs", async () => {
    await mount();
    const agent = face(row("Claude Code: rollback runbook"));
    expect(agent).toMatchObject({
      kind: "agent",
      fact: "The runbook needs a rollback owner. Jordan or Avery?",
      lamps: ["Asks · 6 min"],
      verbs: ["Open session", "Answer"],
    });
    // Window grammar: the agent's own glyph leads the row; it names the agent.
    expect(agent.plate).toBe("");
    expect(agent.glyph).toBe("Claude Code");

    const held = face(row("Codex: reconciliation"));
    expect(held).toMatchObject({
      kind: "agent",
      fact: "psql -h staging-ledger -c 'select count(*) from entries'",
      lamps: ["Held call"],
      verbs: ["Deny", "Approve"],
    });
    expect(face(row("Codex: reconciliation")).glyph).toBe("Codex");

    const pr = face(row("#412 Add the ledger freeze flag"));
    expect(pr).toMatchObject({ kind: "pr", lamps: ["PR open"], verbs: ["Open PR"] });
    // Owner ruling 2026-10-25: no host on the row; Open PR names the link.
    expect(row("#412 Add the ledger freeze flag").textContent).not.toContain("github.com");
    expect(within(row("#412 Add the ledger freeze flag")).getByRole("button", { name: /Open PR/ }).getAttribute("title")).toMatch(/^https:\/\/github\.com\//);

    expect(face(row("Run a second ops interview"))).toMatchObject({
      // One meaning for Decide (it opens choices): a decision to review opens.
      kind: "decision", fact: "Staff hiring loop", lamps: ["To review"], verbs: ["Open item"],
    });
    expect(face(row("Sam: send the status by Thursday"))).toMatchObject({
      kind: "action", fact: "Sam Rivera · 1:1", lamps: ["Due today"], verbs: ["Done"],
    });
    expect(face(row("Vendor call"))).toMatchObject({
      kind: "meeting", fact: "20 min · summary failed", lamps: ["No summary"], verbs: ["Summarize"],
    });
    expect(face(row("Pick the vendor"))).toMatchObject({
      kind: "action", lamps: ["Unassigned"], verbs: ["Name an owner"],
    });
  });

  it("DELIGHT: Done settles the row out, then the list reads again; a row the hub still holds shows again", async () => {
    const media = vi.fn((query: string) => ({ matches: query.includes("no-preference"), media: query,
      addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} }));
    vi.stubGlobal("matchMedia", media);
    try {
      await mount();
      const sam = row("Sam: send the status by Thursday");
      const reads = () => vi.mocked(apiFetch).mock.calls.filter(([path]) => String(path).startsWith("/api/desk/needs-you")).length;
      const before = reads();
      fireEvent.click(within(sam).getByRole("button", { name: /^Done/ }));
      await waitFor(() => expect(sam.getAttribute("data-settle")).toBe("done"));
      expect(vi.mocked(apiFetch).mock.calls.some(([path]) => String(path).includes("follow-through"))).toBe(true);
      await waitFor(() => expect(reads()).toBeGreaterThan(before));
      expect(vi.mocked(apiFetch).mock.calls
        .filter(([path]) => String(path).startsWith("/api/desk/needs-you"))
        .at(-1)?.[0]).toBe("/api/desk/needs-you");
      await waitFor(() => expect(row("Sam: send the status by Thursday").hasAttribute("data-settle")).toBe(false));
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("an item an agent works names the agent and never reads UNASSIGNED", async () => {
    await mount();
    const worked = face(row("Write the rollback runbook"));
    expect(worked.lamps).toEqual(["Working"]);
    expect(worked.fact).toBe("Claude Code · Payments ledger");
    expect(worked.verbs).toEqual(["Open session"]);
    expect(row("Write the rollback runbook").textContent).not.toMatch(/UNASSIGNED|Name an owner/);
  });

  it("puts the agents first, then the rest in the hub's order", async () => {
    await mount();
    const names = [...document.querySelectorAll("[data-testid='needs-ledger'] .needs-row-name")].map((n) => n.textContent);
    // The bold face: the first plate holds the one thing that waits most
    // (no weight, no Program, no age here: the hub's first that is not an
    // agent's ask); the ledger keeps the rest in the hub's order.
    expect(screen.getByTestId("needs-first").querySelector(".needs-row-name")?.textContent).toBe("Run a second ops interview");
    expect(names.slice(0, 4)).toEqual([
      "Claude Code: rollback runbook",
      "Codex: reconciliation",
      "#412 Add the ledger freeze flag",
      "Write the rollback runbook",
    ]);
    expect(names.slice(4)).toEqual([
      "Sam: send the status by Thursday",
      "Pick the vendor",
      "Vendor call",
    ]);
  });

  it("draws no ⚠, no flight chip, no chip species, no Hand to coder", async () => {
    await mount();
    const drawer = screen.getByTestId("needs-drawer");
    expect(drawer.textContent).not.toContain("⚠");
    expect(drawer.querySelector("[data-testid='flight-chip']")).toBeNull();
    expect(drawer.querySelector(".state-chip, .signal-chip, [class*='StateChip'], [class*='state-chip']")).toBeNull();
    expect(screen.queryByText("Hand to coder")).toBeNull();
    // ONE filled verb on the face: the first plate's lead, the brass Button.
    expect(drawer.querySelectorAll(".btn--primary").length).toBe(0);
    expect(drawer.querySelectorAll(".btn--brass").length).toBe(1);
    expect(within(screen.getByTestId("needs-first")).getByText("Open item").className).toContain("btn--brass");
  });

  it("Deny and Approve decide the held call through the gate", async () => {
    await mount();
    fireEvent.click(within(row("Codex: reconciliation")).getByText("Approve"));
    await waitFor(() => expect(gateCalls.length).toBe(1));
    expect(gateCalls[0].path).toBe("/api/gate/proposals/prop-1/decide");
    expect(gateCalls[0].json).toMatchObject({ decision: "approved" });
    fireEvent.click(within(row("Codex: reconciliation")).getByText("Deny"));
    await waitFor(() => expect(gateCalls.length).toBe(2));
    expect(gateCalls[1].json).toMatchObject({ decision: "denied" });
  });

  it("Answer opens the agent with the answer field focused; Open opens it plain", async () => {
    await mount();
    fireEvent.click(within(row("Claude Code: rollback runbook")).getByText("Answer"));
    expect(openCoderSession).toHaveBeenCalledWith("claude:s-run", { answer: true });
    fireEvent.click(within(row("Claude Code: rollback runbook")).getByText("Open session"));
    expect(openCoderSession).toHaveBeenLastCalledWith("claude:s-run");
  });

  it("Name an owner unfolds the owner well in place", async () => {
    await mount();
    fireEvent.click(within(row("Pick the vendor")).getByText("Name an owner"));
    expect(screen.getByTestId("needs-well")).toBeTruthy();
    expect(screen.getByRole("region", { name: "Owner: Pick the vendor" })).toBeTruthy();
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "Jordan" } });
    fireEvent.click(screen.getByRole("button", { name: "Save owner: Pick the vendor" }));
    await waitFor(() => expect(vi.mocked(apiFetch).mock.calls
      .filter(([path]) => String(path).startsWith("/api/desk/needs-you")).at(-1)?.[0])
      .toBe("/api/desk/needs-you"));
  });

  it("Whose? confirms the chosen owner and follows with a plain read", async () => {
    const reads: string[] = [];
    const proposal = {
      id: "proposal:prop-whose", ref: "Choose an owner", kind: "proposal", source: "proposal",
      title: "Choose an owner", why: "PROPOSED · Cutover sync", severity: "info",
      projectId: "", projectName: "", proposalId: "prop-whose", proposalKind: "action",
      meetingId: "m-cutover", meetingTitle: "Cutover sync", whose: ["Mira", "Sam"],
    };
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      const value = String(path);
      if (value.startsWith("/api/desk/needs-you")) {
        reads.push(value);
        return { count: 1, items: [proposal], blockers: [], failedMeetings: [], coverage: [], complete: true } as never;
      }
      if (value === "/api/door") return { ...DOOR } as never;
      return {} as never;
    });
    render(<NeedsDrawer />);
    const need = await screen.findByText("Choose an owner");
    fireEvent.click(need.closest("li.needs-row")!.querySelector("[data-verb='whose']")!);
    fireEvent.click(screen.getByRole("button", { name: "Mira: Choose an owner" }));
    await waitFor(() => expect(reads.at(-1)).toBe("/api/desk/needs-you"));
  });

  it("says Nothing needs you only on a complete read", async () => {
    vi.mocked(apiFetch).mockImplementation(async () => ({ count: 0, items: [], coverage: [], complete: true }) as never);
    render(<NeedsDrawer />);
    await screen.findByText("Nothing needs you");
    expect(document.querySelectorAll(".needs-row").length).toBe(0);
  });

  // HS-S43 (D22/G43 = A): the People overlay shows what he owes his people and
  // leaves out what they owe him. Owner walk 2026-11-08: the toolbar is ONE
  // band, Mine · People at its left and nothing at its right; the People
  // scope ends with Open People (the coverage, one press away).
  it("S43: the toolbar is one segmented control, Mine · People; People ends with Open People, in every settled state", async () => {
    vi.mocked(openSurfaceOr).mockClear();
    const calls = () => vi.mocked(apiFetch).mock.calls.map((c) => String(c[0]));
    await mount();
    expect(screen.queryByText(/does not show People commitments/)).toBeNull();
    const toolbar = screen.getByTestId("needs-toolbar");
    expect(toolbar.querySelector(".kit-toolbar-trailing")).toBeNull();
    const scope = within(toolbar).getByTestId("needs-scope");
    expect([...scope.querySelectorAll("button")].map((b) => b.getAttribute("data-testid"))).toEqual(["needs-chip-mine", "needs-open-people"]);
    expect(within(scope).getByRole("button", { name: "Mine" }).getAttribute("aria-pressed")).toBe("true");
    expect(within(scope).getByRole("button", { name: "People" }).getAttribute("aria-pressed")).toBe("false");
    expect(screen.getByText("8 need you")).toBeTruthy();
    fireEvent.click(within(scope).getByRole("button", { name: "People" }));
    expect(within(scope).getByRole("button", { name: "People" }).getAttribute("aria-pressed")).toBe("true");
    fireEvent.click(screen.getByTestId("needs-people-open"));
    expect(openSurfaceOr).toHaveBeenCalledWith("open-people", "/");
    // No People read is made to draw the control or on the press.
    expect(calls().some((p) => p.startsWith("/api/people"))).toBe(false);

    // Empty and People unread: the control stays and the warning stays.
    vi.mocked(apiFetch).mockImplementation(async () =>
      ({ count: 0, items: [], coverage: [], complete: true, peopleStoreState: "locked" }) as never);
    (globalThis as { __resetNeedsYou?: () => void }).__resetNeedsYou?.();
    render(<NeedsDrawer />);
    await screen.findByText("Nothing needs you");
    await screen.findByTestId("needs-people-read-failed");
    expect(screen.getAllByTestId("needs-open-people").length).toBeGreaterThan(0);
  });

  it("one object, one row: the item an agent works carries its agent's question", async () => {
    const asking: AgentFlight = { ...WORKING, state: "waiting", sessionKey: "claude:s-run" };
    useAgentFlights.setState({ flights: [FLIGHT, asking], sessions: [] } as never);
    // PHILO-15-09 (B11): the hub folds the ask into the item it works
    // (`foldedInto`, needs_you_membership.fold_asks), so its one number and
    // the rows agree: one object, one row, one count.
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (String(path).startsWith("/api/desk/needs-you"))
        return { ...ANSWER, count: 7, items: ITEMS.map((item) => item.id === "coder:claude:s-run"
          ? { ...item, foldedInto: "ai-worked" } : item) } as never;
      return { ...DOOR } as never;
    });
    render(<NeedsDrawer />);
    await screen.findByText("7 need you");
    expect(document.querySelectorAll("[data-testid='needs-list'] li.needs-row")).toHaveLength(7);
    const item = row("Write the rollback runbook");
    expect(face(item)).toMatchObject({
      kind: "action",
      fact: "The runbook needs a rollback owner. Jordan or Avery?",
      lamps: ["Asks · 6 min"],
      verbs: ["Open session", "Answer"],
    });
    expect(document.querySelector(".needs-row[data-object-id='coder:claude:s-run']")).toBeNull();
    expect([...document.querySelectorAll(".needs-row-name")].filter((n) => n.textContent?.includes("rollback runbook"))).toHaveLength(1);
  });

  it("a recording that arms is the first row; the countdown ticks; Cancel cancels it", async () => {
    const cancel = vi.fn(async () => ({ ok: true }));
    useDesk.setState({
      scheduledArming: { scheduleId: "sch-1", title: "Ledger cutover sync", countdownSeconds: 10, fireAt: Date.now() + 8_000, outcome: null },
      cancelArmedSchedule: cancel,
    } as never);
    // PHILO-15-09 (B11): the hub counts the recording that arms; it is a row.
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (String(path).startsWith("/api/desk/needs-you"))
        return { ...ANSWER, arming: [{ scheduleId: "sch-1", title: "Ledger cutover sync" }] } as never;
      return { ...DOOR } as never;
    });
    render(<NeedsDrawer />);
    await screen.findByText("9 need you");
    // The first ledger row (the plate holds the one thing that waits most).
    const rows = document.querySelectorAll<HTMLElement>("[data-testid='needs-ledger'] [data-testid='needs-row']");
    expect(rows[0].getAttribute("data-object-id")).toBe("arming:sch-1");
    expect(rows[0].getAttribute("data-kind")).toBe("meeting");
    const first = rows[0].querySelector("[data-testid=needs-row-state]")?.textContent ?? "";
    expect(first).toMatch(/^Arms · 0:0[78]$/);
    expect(face(rows[0]).verbs).toEqual(["Cancel", "Open meetings"]);
    await waitFor(() => expect(rows[0].querySelector("[data-testid=needs-row-state]")?.textContent).not.toBe(first), { timeout: 2500 });
    fireEvent.click(rows[0].querySelector("[data-verb='cancel']")!);
    expect(cancel).toHaveBeenCalledWith("sch-1");
  });

  it("reconciles an arming mismatch with a plain read", async () => {
    const reads: string[] = [];
    useDesk.setState({
      scheduledArming: { scheduleId: "sch-stale", title: "Stale arming", countdownSeconds: 10, fireAt: Date.now() + 8_000, outcome: null },
    } as never);
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (String(path).startsWith("/api/desk/needs-you")) {
        reads.push(String(path));
        return { ...ANSWER, arming: [] } as never;
      }
      return { ...DOOR } as never;
    });
    render(<NeedsDrawer />);
    await screen.findByText("8 need you");
    await waitFor(() => expect(reads.length).toBeGreaterThan(0));
    expect(reads.every((path) => path === "/api/desk/needs-you")).toBe(true);
  });

  it("a failed fire stays in Needs you and Record now starts its calendar meeting", async () => {
    const start = vi.fn().mockResolvedValue(undefined);
    useDesk.setState({ startRecording: start });
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (String(path).startsWith("/api/desk/needs-you")) {
        return {
          ...ANSWER,
          arming: [{
            scheduleId: "sch-failed",
            calendarEventId: "event-ledger",
            title: "Ledger cutover sync",
            didNotRecord: { at: "2026-10-07T16:00:00Z", reason: "No microphone" },
          }],
        } as never;
      }
      return { ...DOOR } as never;
    });
    render(<NeedsDrawer />);
    await screen.findByText("9 need you");
    const failed = document.querySelector<HTMLElement>("[data-object-id='arming:sch-failed']");
    expect(failed).toBeTruthy();
    expect(failed?.querySelector(".needs-row-fact")?.textContent).toContain("Did not record");
    expect(failed?.querySelector(".needs-row-fact")?.textContent).toContain("No microphone");
    expect(face(failed!).verbs).toEqual(["Record now", "Open meetings"]);
    fireEvent.click(failed!.querySelector("[data-verb='record']")!);
    expect(start).toHaveBeenCalledWith({ calendarEventId: "event-ledger" });
  });

  it("NEXT is a quiet footer line; with a next meeting there is no calendar offer (PHILO-15-09 B11, W1-DOORS)", async () => {
    const at = new Date();
    at.setHours(14, 0, 0, 0);
    DOOR = { upcoming: [{ title: "Ledger cutover sync", starts_at: at.toISOString(), source: "calendar_event" }], calendar_configured: false };
    await mount();
    await waitFor(() => expect(screen.getByTestId("needs-next").textContent).toBe("Next 14:00 · Ledger cutover sync"));
    // W1-DOORS (atlas 2026-10-27): one truth. A next meeting in the status
    // bar means there is a calendar: the toolbar does not say "No calendar".
    expect(screen.queryByTestId("needs-no-calendar")).toBeNull();
    // One count: the head says the number of rows under it.
    const rows = document.querySelectorAll("[data-testid='needs-list'] li.needs-row");
    expect(screen.getByTestId("arrival-display").textContent).toBe(`${rows.length} need you`);
    expect(rows.length).toBe(8);
  });

  it("no calendar and no next meeting: the offer is in the toolbar, never a row (PHILO-15-09 B11)", async () => {
    DOOR = { upcoming: [], calendar_configured: false };
    await mount();
    const offer = await screen.findByTestId("needs-no-calendar");
    expect(offer.textContent).toBe("No calendarConnect calendar");
    expect(offer.closest("[data-testid='needs-mast']")).toBeTruthy();
    expect(screen.queryByTestId("needs-source-row")).toBeNull();
    fireEvent.click(screen.getByTestId("needs-drawer").querySelector("[data-verb='connect-calendar']")!);
    expect(openSurfaceOr).toHaveBeenCalledWith("configure-settings", "/settings", "integration:calendar");
  });

  it("muted rows are not drawn; Muted · N opens them", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (String(path).startsWith("/api/desk/needs-you"))
        return { ...ANSWER, items: [...ITEMS, { ...ITEMS[4], id: "decision:d-muted", ref: "decision:d-muted", openRef: "decision:d-muted", title: "A muted decision", muted: true }] } as never;
      return { upcoming: [], calendar_configured: true } as never;
    });
    await mount();
    expect(screen.queryByText("A muted decision")).toBeNull();
    // The bold mast: Muted · N (drawn while a muted row exists) shows them.
    fireEvent.click(screen.getByRole("button", { name: "Muted · 1" }));
    expect(within(screen.getByTestId("needs-muted")).getByText("A muted decision")).toBeTruthy();
    expect(screen.getByTestId("needs-muted").querySelector("h3")?.textContent).toBe("Muted · 1");
  });

  it("a press on the row body opens the item; a press on a verb does only the verb", async () => {
    await mount();
    const agent = row("Claude Code: rollback runbook");
    fireEvent.click(agent.querySelector(".needs-row-name")!);
    expect(openCoderSession).toHaveBeenCalledWith("claude:s-run");
    vi.mocked(openCoderSession).mockClear();
    fireEvent.click(within(agent).getByText("Answer"));
    expect(openCoderSession).toHaveBeenCalledTimes(1);
    expect(openCoderSession).toHaveBeenCalledWith("claude:s-run", { answer: true });
    expect(agent.getAttribute("data-opens")).toBe("true");
  });

  // The one decision face (2026-11-08): a decision row opens its record in
  // the Decisions window reader, never the Decision pullout.
  it("a decision row's body opens its record in the Decisions window reader", async () => {
    const room = vi.mocked(apiFetch).getMockImplementation()!;
    vi.mocked(apiFetch).mockImplementation(async (path: string, init?: unknown) => {
      if (path === "/api/decisions/d-ops") return { decision: { id: "d-ops", title: "Run a second ops interview" } } as never;
      if (path === "/api/decision-records/source/desk/d-ops") return [{ id: "rec-ops" }] as never;
      return room(path, init as never);
    });
    useDesk.setState({ pullouts: [], windowsById: {} } as never);
    await mount();
    fireEvent.click(row("Run a second ops interview").querySelector(".needs-row-name")!);
    await waitFor(() => expect(useDesk.getState().windowsById["surface-decisions"]?.scope).toBe("record:rec-ops"));
    expect(useDesk.getState().pullouts).toEqual([]);
  });

  it("the row body opens inside a window region too (the Chair window is role=region)", async () => {
    render(<div role="region" aria-label="Needs you"><NeedsDrawer /></div>);
    await screen.findByText("8 need you");
    fireEvent.click(row("Claude Code: rollback runbook").querySelector(".needs-row-fact")!);
    expect(openCoderSession).toHaveBeenCalledWith("claude:s-run");
  });

  // ── Astra r1 on #935 ──────────────────────────────────────────────

  it("P1-1: a held call the hub cannot show whole offers Deny and Open, never Approve", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (String(path).startsWith("/api/desk/needs-you")) {
        const cut = { ...ITEMS[1], id: "gate:prop-cut", ref: "gate:prop-cut", title: "Approve: psql -h staging-ledger -c 'select", argsCut: true, argsHidden: 78 };
        return { ...ANSWER, count: 1, items: [cut], failedMeetings: [] } as never;
      }
      return { upcoming: [], calendar_configured: true } as never;
    });
    render(<NeedsDrawer />);
    await screen.findByText("1 needs you");
    const held = face(row("Codex: reconciliation"));
    expect(held.fact).toBe("psql -h staging-ledger -c 'select… +78 CHARS");
    expect(held.lamps).toEqual(["Cut · Approve in raw"]);
    expect(held.verbs).toEqual(["Deny", "Open raw lane"]);
    expect(screen.queryByRole("button", { name: /^Approve/ })).toBeNull();
    fireEvent.click(within(row("Codex: reconciliation")).getByText("Open raw lane"));
    // PHILO-15 20 (B63): Open opens the lane on Raw, where the cut call is approved.
    expect(openCoderSession).toHaveBeenCalledWith("codex:s-recon", { raw: true });
  });

  it("PHILO-15 15: a held call says why it waits; a cut one says CUT · APPROVE IN RAW, never Approve", async () => {
    const head = "cat > /tmp/hs15_long.md <<'EOF'\n1. Rule one of three: always branch from main before mak";
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (String(path).startsWith("/api/desk/needs-you")) {
        const cut = {
          ...ITEMS[1], id: "gate:prop-long", ref: "gate:prop-long",
          title: `Approve: ${head}`, command: head, argsCut: true, argsHidden: 1666,
          holdReason: "OUTSIDE THE WORKTREE · /tmp/hs15_long.md",
        };
        return { ...ANSWER, count: 1, items: [cut], failedMeetings: [] } as never;
      }
      return { upcoming: [], calendar_configured: true } as never;
    });
    render(<NeedsDrawer />);
    await screen.findByText("1 needs you");
    const item = row("Codex: reconciliation");
    const held = face(item);
    expect(held.fact).toBe(`OUTSIDE THE WORKTREE · /tmp/hs15_long.md\n${head}… +1666 CHARS`);
    expect(item.querySelector(".needs-row-fact")?.classList.contains("is-code")).toBe(true);
    expect(held.lamps).toEqual(["Cut · Approve in raw"]);
    expect(held.verbs).toEqual(["Deny", "Open raw lane"]);
  });

  it("P1-2: a refused Cancel is named on the row with Retry; a cancel leaves a receipt after the row goes", async () => {
    useDesk.getState().applyScheduledRecordingEvent("scheduled_recording.arming", {
      schedule_id: "sch-9", title: "Ledger cutover sync", countdown_seconds: 30, fire_at: Date.now() / 1000 + 30,
    });
    let refuse = true;
    let cancelled = false;
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      const value = String(path);
      if (value === "/api/scheduled-recordings/sch-9/cancel") {
        if (refuse) throw new ApiError(409, "conflict", { error: "the recording already started", code: "already_started" });
        cancelled = true;
        return { ok: true } as never;
      }
      if (value.startsWith("/api/desk/needs-you"))
        return { ...ANSWER, arming: refuse || !cancelled ? [{ scheduleId: "sch-9", title: "Ledger cutover sync" }] : [] } as never;
      if (value.startsWith("/api/scheduled-recordings")) return { items: [] } as never;
      return { upcoming: [], calendar_configured: true } as never;
    });
    // PHILO-15-09 (B11): the arming row counts.
    render(<NeedsDrawer />);
    await screen.findByText("9 need you");
    const armed = () => document.querySelector<HTMLElement>("[data-object-id='arming:sch-9']");
    fireEvent.click(armed()!.querySelector("[data-verb='cancel']")!);
    await waitFor(() => expect(armed()!.querySelector(".needs-row-fact")?.textContent)
      .toBe("Could not cancel · Nothing changed"));
    // W6-H words: the hub's reason rides the hover title.
    expect(armed()!.querySelector(".needs-row-fact")?.getAttribute("title")).toBe("the recording already started");
    expect(armed()!.querySelector("[data-verb='retry']")?.textContent).toBe("Retry");
    refuse = false;
    fireEvent.click(armed()!.querySelector("[data-verb='retry']")!);
    await waitFor(() => expect(armed()!.querySelector("[data-verb='cancel']")).toBeTruthy());
    // The hub's event: the row goes, the receipt stays.
    act(() => useDesk.getState().applyScheduledRecordingEvent("scheduled_recording.cancelled", { schedule_id: "sch-9" }));
    expect(armed()).toBeNull();
    expect(screen.getByTestId("needs-receipt").textContent).toMatch(/^Cancelled · Ledger cutover sync · \d\d:\d\d$/);
  });

  it("P1-3: one object, one count: an ask the hub folded into its item is its item's row, not a member", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (String(path).startsWith("/api/desk/needs-you")) {
        const ask = { ...ITEMS[0], foldedInto: "ai-worked" };
        return { ...ANSWER, count: 7, items: [ask, ...ITEMS.slice(1)] } as never;
      }
      return { upcoming: [], calendar_configured: true } as never;
    });
    useAgentFlights.setState({ flights: [], sessions: [] } as never);
    await mount7();
    const members = document.querySelectorAll("[data-testid='needs-row'][data-counted='true']");
    expect(screen.getByTestId("arrival-display").textContent).toBe(`${members.length} need you`);
    expect(members).toHaveLength(7);
    expect(face(row("Write the rollback runbook")).lamps).toEqual(["Asks · 6 min"]);
    expect(document.querySelector("[data-object-id='coder:claude:s-run']")).toBeNull();
  });
  it("one object, one row, always: a held call and a question on one item lead with the held call, +1 MORE", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (String(path).startsWith("/api/desk/needs-you")) {
        const question = { ...ITEMS[0], foldedInto: "ai-worked" };
        const held = { ...ITEMS[1], sessionKey: "claude:s-run", foldedInto: "ai-worked" };
        return { ...ANSWER, count: 6, items: [question, held, ...ITEMS.slice(2)] } as never;
      }
      return { upcoming: [], calendar_configured: true } as never;
    });
    useAgentFlights.setState({ flights: [], sessions: [] } as never);
    render(<NeedsDrawer />);
    await screen.findByText("6 need you");
    const item = row("Write the rollback runbook");
    expect(face(item)).toMatchObject({ lamps: ["Held call"], verbs: ["Deny", "Approve"] });
    expect(within(item).getByTestId("needs-more-asks").textContent).toBe("+1 more");
    expect(document.querySelectorAll("[data-testid='needs-row'][data-counted='true']")).toHaveLength(6);
    expect(document.querySelectorAll(".needs-row[data-kind='agent']")).toHaveLength(0);
    // The row body opens the agent's lane, where every ask is answered.
    fireEvent.click(item.querySelector(".needs-row-name")!);
    expect(openCoderSession).toHaveBeenCalledWith("claude:s-run");
  });
  it("PHILO-15 08: a proposal from a meeting in no Project has Confirm, Defer and Decline with words", async () => {
    const proposals = [
      {
        id: "proposal:prop-priya", ref: "Add the named failure fence before ship", kind: "proposal",
        source: "proposal", title: "Add the named failure fence before ship",
        why: "PROPOSED · philo3_architect_meeting", severity: "info", projectId: "", projectName: "",
        proposalId: "prop-priya", proposalKind: "action", meetingId: "m-wav",
        meetingTitle: "philo3_architect_meeting", proposalActionItemId: "action_1",
      },
      {
        id: "proposal:prop-sqlite", ref: "Use SQLite for the local meeting ledger", kind: "proposal",
        source: "proposal", title: "Use SQLite for the local meeting ledger",
        why: "PROPOSED · philo3_architect_meeting", severity: "info", projectId: "", projectName: "",
        proposalId: "prop-sqlite", proposalKind: "decision", meetingId: "m-wav",
        meetingTitle: "philo3_architect_meeting",
      },
    ];
    const posted: string[] = [];
    const needsReads: string[] = [];
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      const value = String(path);
      if (value.startsWith("/api/desk/needs-you")) {
        needsReads.push(value);
        return { count: 2, items: proposals, blockers: [], failedMeetings: [], coverage: [], complete: true } as never;
      }
      if (value.startsWith("/api/proposals/")) posted.push(value);
      if (value === "/api/door") return DOOR as never;
      return {} as never;
    });
    render(<NeedsDrawer />);
    await screen.findByText("2 need you");
    const action = row("Add the named failure fence before ship");
    expect(face(action)).toMatchObject({
      kind: "action",
      fact: "from philo3_architect_meeting",
      lamps: ["To confirm"],
      verbs: ["Confirm"],
    });
    // No glyph-only control: every verb carries its word.
    for (const button of action.querySelectorAll(".needs-row-verbs button")) {
      expect((button.textContent ?? "").trim()).toMatch(/^[A-Z][a-z]+$/);
    }
    // Betterment D2: a decision waits for Decide (Accept, Not now, Drop in place).
    expect(face(row("Use SQLite for the local meeting ledger")).verbs).toEqual(["Decide"]);
    expect(action.getAttribute("data-opens")).toBe("true");

    fireEvent.click(within(action).getByRole("button", { name: "Confirm: Add the named failure fence before ship" }));
    await waitFor(() => expect(posted).toContain("/api/proposals/prop-priya/confirm"));
    const sqlite = "Use SQLite for the local meeting ledger";
    fireEvent.click(within(row(sqlite)).getByRole("button", { name: `Decide: ${sqlite}` }));
    fireEvent.click(screen.getByRole("button", { name: `Not now: ${sqlite}` }));
    await waitFor(() => expect(posted).toContain("/api/proposals/prop-sqlite/defer"));
    await waitFor(() => expect(screen.queryByTestId("needs-decide")).toBeNull());
    fireEvent.click(within(row(sqlite)).getByRole("button", { name: `Decide: ${sqlite}` }));
    fireEvent.click(screen.getByRole("button", { name: `Drop: ${sqlite}` }));
    await waitFor(() => expect(posted).toContain("/api/proposals/prop-sqlite/dismiss"));
    expect(needsReads.every((path) => path === "/api/desk/needs-you")).toBe(true);
  });
});

async function mount7() {
  render(<NeedsDrawer />);
  await screen.findByText("7 need you");
}

// PHILO-15-09 (B11, B12): one count, and every row says what it is.
describe("NeedsDrawer one count and kind words (PHILO-15-09)", () => {
  it("the head is the number of rows, and each member row names its kind", async () => {
    DOOR = { upcoming: [], calendar_configured: false };
    await mount();
    const rows = Array.from(document.querySelectorAll<HTMLElement>("[data-testid='needs-list'] li.needs-row"));
    expect(screen.getByTestId("arrival-display").textContent).toBe(`${rows.length} need you`);
    // Window grammar: the glyph leads; its alt is the kind word.
    const word = (title: string) =>
      rows.find((r) => r.textContent?.includes(title))?.querySelector(":scope > img")?.getAttribute("alt");
    expect(word("Run a second ops interview")).toBe("Decision");
    expect(word("Pick the vendor")).toBe("Action");
    expect(word("Vendor call")).toBe("Meeting");
    expect(word("Jordan or Avery")).toBe("Claude Code");
    for (const row of rows) {
      expect(row.querySelector(":scope > img")?.getAttribute("alt")).toBeTruthy();
      expect(row.querySelector("[data-testid='kit-kind']")).toBeNull();
      expect(row.querySelector("[data-testid='needs-row-kind']")).toBeNull();
    }
  });

  it("one thing says `1 needs you`", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (String(path).startsWith("/api/desk/needs-you"))
        return { ...ANSWER, count: 1, items: [ITEMS[4]], failedMeetings: [] } as never;
      return { upcoming: [], calendar_configured: false } as never;
    });
    render(<NeedsDrawer />);
    await screen.findByText("1 needs you");
    expect(document.querySelectorAll("[data-testid='needs-list'] li.needs-row")).toHaveLength(1);
  });
});

describe("NeedsDrawer every row counts (PHILO-15-09 B11, Astra r1)", () => {
  it("the hub's one number counts a source not read, a recording that arms and a folded ask; the rows agree", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (String(path).startsWith("/api/desk/needs-you"))
        return {
          ...ANSWER,
          complete: false,
          coverage: [
            { source_id: "gh:ledger", kind: "project", state: "failed", observed_at: null, label: "CI red on main", project_id: "p1", reason: "gh not signed in" },
            { source_id: "jira:ops", kind: "project", state: "available", observed_at: null, label: "Ops", project_id: "p2" },
          ],
          arming: [{ scheduleId: "sch-2", title: "Standup" }],
          // the hub folded the agent's question into the item it works
          items: ITEMS.map((item) => item.id === "coder:claude:s-run" ? { ...item, foldedInto: "ai-worked" } : item),
        } as never;
      return { upcoming: [], calendar_configured: false } as never;
    });
    useDesk.setState({
      scheduledArming: { scheduleId: "sch-2", title: "Standup", countdownSeconds: 60, fireAt: Date.now() + 60_000, outcome: null },
    } as never);
    render(<NeedsDrawer />);
    await screen.findByText("9 need you");
    const rows = document.querySelectorAll<HTMLElement>("[data-testid='needs-list'] li.needs-row");
    expect(rows).toHaveLength(9);
    // The Dock badge and the bell read the same snapshot (`useNeedsYou`).
    const { readNeedsYouAnswer } = await import("../../needsYou");
    const answer = await vi.mocked(apiFetch).getMockImplementation()!("/api/desk/needs-you") as never;
    expect(readNeedsYouAnswer(answer).count).toBe(9);
    expect(screen.getAllByTestId("needs-source-row")).toHaveLength(1);
    for (const row of rows) expect(row.getAttribute("data-counted")).toBe("true");
  });
});

// PHILO-15-09 (Astra r2): the one-number seed shared with Dock.test.tsx.
describe("NeedsDrawer one-number seed (PHILO-15-09 r3)", () => {
  it("draws the seed's rows under the head that says their number", async () => {
    const { ONE_NUMBER_SEED, ONE_NUMBER_ROWS } = await import("../../../test/oneNumberSeed");
    vi.mocked(apiFetch).mockImplementation(async (path: string) =>
      (String(path).startsWith("/api/desk/needs-you") ? ONE_NUMBER_SEED : { upcoming: [], calendar_configured: true }) as never);
    useAgentFlights.setState({ flights: [], sessions: [] } as never);
    render(<NeedsDrawer />);
    await screen.findByText(`${ONE_NUMBER_ROWS} need you`);
    expect(document.querySelectorAll("[data-testid='needs-list'] li.needs-row")).toHaveLength(ONE_NUMBER_ROWS);
  });
});

// PHILO-15 21 (B60, B61, B74): the second morning. The hub's rows from the
// rehearsal at 07:05: a GitHub source held by quiet hours, a meeting source
// that is stale for another reason.
describe("NeedsDrawer the second morning (PHILO-15 21)", () => {
  const yesterday = (() => {
    const d = new Date();
    d.setDate(d.getDate() - 1);
    d.setHours(21, 23, 0, 0);
    return d.toISOString();
  })();
  const MORNING = {
    ...ANSWER,
    count: 1,
    items: [],
    failedMeetings: [],
    complete: false,
    coverage: [
      {
        source_id: "watch:w-gh", kind: "watch", state: "quiet", observed_at: yesterday,
        label: "GitHub · karolswdev/holdspeak-dayone-rehearsal-1558", project_id: "p1",
        reason: "quiet until 08:00", watch_ids: ["w-gh"], host: "github.com",
        repair: { token: "Quiet until 08:00", verb: "Retry", href: "/projects/p1" },
      },
      {
        source_id: "watch:w-mtg", kind: "watch", state: "stale", observed_at: yesterday,
        label: "Meetings", project_id: "p1", reason: "not checked recently", watch_ids: ["w-mtg"],
        repair: { token: "Stale", verb: "Retry", href: "/projects/p1" },
      },
    ],
  };
  let evaluated: string[] = [];
  let refuse = false;
  beforeEach(() => {
    evaluated = [];
    refuse = false;
    useAgentFlights.setState({ flights: [], sessions: [] } as never);
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      const value = String(path);
      if (value.startsWith("/api/desk/needs-you")) return MORNING as never;
      if (value.startsWith("/api/watches/")) {
        evaluated.push(value);
        if (refuse) throw new ApiError(400, "gh is not signed in", {});
        return { success: true, state: "no_op" } as never;
      }
      return { upcoming: [], calendar_configured: true } as never;
    });
  });

  it("B60: a quiet source reads QUIET UNTIL 08:00, is drawn, and is not counted", async () => {
    render(<NeedsDrawer />);
    await screen.findByText("1 needs you");
    const sources = screen.getAllByTestId("needs-source-row");
    expect(sources).toHaveLength(2);
    const quiet = sources.find((li) => /GitHub/.test(li.textContent ?? ""))!;
    expect(face(quiet).lamps).toContain("Quiet until 08:00");
    expect(quiet.getAttribute("data-counted")).toBe("false");
    const stale = sources.find((li) => /Meetings/.test(li.textContent ?? ""))!;
    expect(face(stale).lamps).toContain("Stale");
    expect(stale.getAttribute("data-counted")).toBe("true");
  });

  it("B74: names, never ids, and the day on a time from yesterday", async () => {
    render(<NeedsDrawer />);
    await screen.findByText("1 needs you");
    const [quiet, stale] = ["GitHub", "Meetings"].map((name) =>
      screen.getAllByTestId("needs-source-row").find((li) => li.textContent?.includes(name))!);
    expect(quiet.querySelector(".needs-row-name")?.textContent).toBe("GitHub · karolswdev/holdspeak-dayone-rehearsal-1558");
    expect(face(quiet).fact).toBe("observed yesterday 21:23");
    expect(stale.querySelector(".needs-row-name")?.textContent).toBe("Meetings");
    expect(face(stale).fact).toBe("not checked recently · observed yesterday 21:23");
  });

  it("Astra r1 P2-6 (amended 2026-10-25): a Retry that reaches GitHub names the host in its title; no badge on either row", async () => {
    render(<NeedsDrawer />);
    await screen.findByText("1 needs you");
    const [gh, mtg] = ["GitHub", "Meetings"].map((name) =>
      screen.getAllByTestId("needs-source-row").find((li) => li.textContent?.includes(name))!);
    expect(face(gh).egress).toBe("");
    expect(face(mtg).egress).toBe("");
    expect(within(gh).getByRole("button", { name: /^Retry/ }).getAttribute("title")).toBe("Checks github.com again");
    expect(within(mtg).getByRole("button", { name: /^Retry/ }).getAttribute("title")).toBeNull();
  });

  it("B61: Retry re-checks THAT source through the single-Watch route and leaves a receipt", async () => {
    render(<NeedsDrawer />);
    await screen.findByText("1 needs you");
    const stale = screen.getAllByTestId("needs-source-row").find((li) => li.textContent?.includes("Meetings"))!;
    fireEvent.click(within(stale).getByRole("button", { name: "Retry: Meetings" }));
    await waitFor(() => expect(screen.getByTestId("needs-source-receipt").textContent).toMatch(/^Checked Meetings at \d\d:\d\d$/));
    expect(evaluated).toEqual(["/api/watches/w-mtg/evaluate"]);
    await waitFor(() => expect(vi.mocked(apiFetch).mock.calls
      .filter(([path]) => String(path).startsWith("/api/desk/needs-you")).at(-1)?.[0])
      .toBe("/api/desk/needs-you?fresh=1"));
    // A refused check says so in plain words; the hub's reason is the hover.
    refuse = true;
    fireEvent.click(within(stale).getByRole("button", { name: "Retry: Meetings" }));
    await waitFor(() => expect(screen.getByTestId("needs-source-receipt").textContent).toBe(
      "Could not check Meetings · Nothing changed · Try again"));
    await waitFor(() => expect(vi.mocked(apiFetch).mock.calls
      .filter(([path]) => String(path).startsWith("/api/desk/needs-you")).at(-1)?.[0])
      .toBe("/api/desk/needs-you?fresh=1"));
    expect(screen.getByTestId("needs-source-receipt").querySelector("[title]")?.getAttribute("title")).toBe("gh is not signed in");
  });

  it("a coverage Retry without Watch ids forces the aggregate read", async () => {
    const noWatch = {
      ...MORNING,
      coverage: [{ ...MORNING.coverage[1], watch_ids: [] }],
    };
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      const value = String(path);
      if (value.startsWith("/api/desk/needs-you")) return noWatch as never;
      return { upcoming: [], calendar_configured: true } as never;
    });
    render(<NeedsDrawer />);
    await screen.findByText("1 needs you");
    const meetings = screen.getAllByTestId("needs-source-row").find((li) => li.textContent?.includes("Meetings"))!;
    fireEvent.click(within(meetings).getByRole("button", { name: "Retry: Meetings" }));
    await waitFor(() => expect(vi.mocked(apiFetch).mock.calls
      .filter(([path]) => String(path).startsWith("/api/desk/needs-you")).at(-1)?.[0])
      .toBe("/api/desk/needs-you?fresh=1"));
  });
});

// Phase 16 (the interior kit; the canvas window "Needs you"): AppHead and its
// strip, the FilterBar, the Section over every row, the kind plates, the Foot.
describe("NeedsDrawer on the interior kit (Phase 16)", () => {
  it("every row is drawn (no cap): `Actions · 8` over eight rows, the Ledger scrolls with its ScrollHint", async () => {
    render(<NeedsDrawer />);
    await screen.findByText("8 need you");
    const list = screen.getByTestId("needs-list");
    expect(list.querySelectorAll("li.needs-row")).toHaveLength(8);
    // The bold ledger: no row has a weight here, so one group, To do, with
    // every row but the plate's (`To do · 7 more`).
    expect([...list.querySelectorAll(".needs-ledger-head")].map((h) => h.textContent)).toEqual(["To do · 7 more"]);
    expect(list.querySelector(".surface-scroll-hint[data-axis='y']")).toBeTruthy();
    // No cap: nothing says "N more" beyond the group head.
    expect(screen.queryAllByText(/more$/).filter((n) => !n.classList.contains("needs-ledger-head"))).toEqual([]);
    expect(screen.queryByRole("button", { name: "Show all" })).toBeNull();
  });

  it("the strip says the facts as tokens; the foot says when the hub ranked", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (String(path).startsWith("/api/desk/needs-you"))
        return {
          ...ANSWER,
          computedAt: new Date(Date.now() - 30_000).toISOString(),
          coverage: [
            { source_id: "jira:ops", kind: "project", state: "available", observed_at: null, label: "Ops", project_id: "p2" },
          ],
        } as never;
      return { upcoming: [], calendar_configured: false } as never;
    });
    useSourceReceipt.setState({ receipt: null });
    render(<NeedsDrawer />);
    await screen.findByText("8 need you");
    // The bold mast carries the offer; the status bar the facts.
    const toolbar = screen.getByTestId("needs-mast");
    // W5-WORDS: every source read draws no coverage row (no `1 of 1 available`).
    expect(screen.queryByRole("button", { name: "Coverage" })).toBeNull();
    await waitFor(() => expect(toolbar.textContent).toContain("No calendar"));
    expect(within(toolbar).getByRole("button", { name: "Connect calendar" })).toBeTruthy();
    expect(screen.getByTestId("needs-checked").textContent).toMatch(/^checked \d{2}:\d{2}$/);
    expect(toolbar.querySelector(".surface-mast-facts")?.textContent).toMatch(/^checked \d{2}:\d{2}$/);
    expect(screen.getByTestId("needs-checked").closest("[data-testid='arrival-headline']")).toBeTruthy();
  });

  // The bold face (2026-11-08): the narrowing chips left the window (owner:
  // "way too cluttered"). The mast says Mine · People and Later; the People
  // tab narrows by person.
  it("draws no chip strip: the mast's verbs are Mine · People only on a desk of today", async () => {
    render(<WindowIdContext.Provider value="chair:needs"><ApplicationMenu windowId="chair:needs" /><NeedsDrawer /></WindowIdContext.Provider>);
    await screen.findByText("8 need you");
    expect(screen.queryByTestId("needs-filter")).toBeNull();
    expect(screen.queryByTestId("needs-chip-week")).toBeNull();
    expect(screen.queryByTestId("needs-chip-later")).toBeNull();
    const verbs = screen.getByTestId("needs-mast").querySelectorAll(".surface-mast-verbs button");
    // Show me belongs to the app menu; the mast keeps its own actions.
    expect([...verbs].map((b) => b.textContent)).toEqual(["Mine", "People"]);
    fireEvent.click(within(screen.getByTestId("desk-screen-title")).getByRole("button"));
    expect(screen.getByRole("menuitem", { name: "Show me" })).toBeVisible();
  });

  it("every row leads with its glyph, named in plain words", async () => {
    await mount();
    const words = [...document.querySelectorAll("li.needs-row > img")].map((n) => n.getAttribute("alt"));
    // The plate's row first (the decision), then the ledger's.
    expect(words).toEqual(["Decision", "Claude Code", "Codex", "Pull request", "Action", "Action", "Action", "Meeting"]);
    expect(document.querySelectorAll("li.needs-row [data-testid='kit-kind']")).toHaveLength(0);
  });
});

// Astra r1 M4: a dated proposal carries its date as `proposalDue` (the
// producer: needs_you_aggregate.py), never `dueAt`; it is Due today, not
// No due date.
describe("NeedsDrawer reads a proposal's own date (Phase 16, Betterment D2)", () => {
  it("a proposal due today says its date on the row", async () => {
    const t = new Date();
    const today = `${t.getFullYear()}-${String(t.getMonth() + 1).padStart(2, "0")}-${String(t.getDate()).padStart(2, "0")}`;
    const proposals = [
      {
        id: "proposal:prop-dated", ref: "Ship the runbook", kind: "proposal",
        source: "proposal", title: "Ship the runbook",
        why: "PROPOSED · cutover sync", severity: "info", projectId: "", projectName: "",
        proposalId: "prop-dated", proposalKind: "action", meetingId: "m-cut",
        meetingTitle: "cutover sync", proposalDue: today,
      },
      {
        id: "proposal:prop-undated", ref: "Pick the vendor", kind: "proposal",
        source: "proposal", title: "Pick the vendor",
        why: "PROPOSED · cutover sync", severity: "info", projectId: "", projectName: "",
        proposalId: "prop-undated", proposalKind: "action", meetingId: "m-cut",
        meetingTitle: "cutover sync",
      },
    ];
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (String(path).startsWith("/api/desk/needs-you"))
        return { count: 2, items: proposals, blockers: [], failedMeetings: [], coverage: [], complete: true } as never;
      return { upcoming: [], calendar_configured: true } as never;
    });
    render(<NeedsDrawer />);
    await screen.findByText("2 need you");
    expect(row("Ship the runbook").querySelector(".needs-row-fact")?.textContent).toContain(`by ${today}`);
    expect(row("Pick the vendor").querySelector(".needs-row-fact")?.textContent ?? "").not.toContain(" by ");
  });
});

// PHILO-17 (needsyou, walker BLOCKS): 30 GitHub sources that cannot be
// checked for one cause were 30 rows above the work, each with a raw runner
// error. Sources with one cause and one repair are ONE row now, after the
// work, counted once; raw lines stay in the row's detail; Reconnect opens
// Settings · Connections on GitHub. The fixtures carry the words the real
// producer writes (`ProjectService._plain_reason`: "Not signed in").
describe("NeedsDrawer groups the sources of one cause (PHILO-17)", () => {
  const ghSource = (n: number, extra: Record<string, unknown> = {}) => ({
    source_id: `watch:w-gh-${n}`, kind: "watch", state: "failed", observed_at: null,
    label: `GitHub · acme/repo-${n}`, project_id: `p${n}`, provider: "github",
    reason: "Not signed in", cause: "Not signed in", watch_ids: [`w-gh-${n}`], host: "github.com",
    repair: { token: "Cant check", verb: "Reconnect", href: "/settings" },
    ...extra,
  });
  const paused = (n: number, room: string) => ({
    source_id: `watch:w-p-${n}`, kind: "watch", state: "unavailable", observed_at: null,
    label: `GitHub · acme/paused-${n}`, project_id: room, provider: "github",
    reason: "paused", cause: "paused", watch_ids: [`w-p-${n}`], host: "github.com",
    repair: { token: "PAUSED", verb: "Open source", href: `/projects/${room}` },
  });
  const GROUPED = {
    ...ANSWER,
    // The hub's one number: 8 members + ONE grouped cause.
    count: 9,
    complete: false,
    coverage: [1, 2, 3].map((n) => ghSource(n)),
  };
  const answerWith = (coverage: unknown[], count: number) => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (String(path).startsWith("/api/desk/needs-you")) return { ...GROUPED, coverage, count } as never;
      return { upcoming: [], calendar_configured: true } as never;
    });
  };
  beforeEach(() => {
    vi.mocked(openSurfaceOr).mockClear();
    answerWith(GROUPED.coverage, 9);
  });

  it("draws ONE row for one cause and one repair, after the work", async () => {
    render(<NeedsDrawer />);
    await screen.findByText("9 need you");
    const sources = screen.getAllByTestId("needs-source-row");
    expect(sources).toHaveLength(1);
    const group = sources[0];
    expect(group.querySelector(".needs-row-name")?.textContent).toBe("GitHub · 3 sources");
    expect(face(group).fact).toBe("Not signed in");
    expect(face(group).lamps).toEqual(["Cant check"]);
    // The work leads; the plumbing is last.
    const members = screen.getAllByTestId("needs-row");
    expect(group.compareDocumentPosition(members[members.length - 1]) & Node.DOCUMENT_POSITION_PRECEDING).toBeTruthy();
    expect(group.getAttribute("data-counted")).toBe("true");
    // The browser twin counts the cause once, as the hub does.
    const { readNeedsYouAnswer } = await import("../../needsYou");
    expect(readNeedsYouAnswer(GROUPED as never).count).toBe(9);
  });

  it("lists every source of the group behind Details", async () => {
    render(<NeedsDrawer />);
    await screen.findByText("9 need you");
    const group = screen.getByTestId("needs-source-row");
    expect(screen.queryByTestId("needs-detail")).toBeNull();
    fireEvent.click(within(group).getByRole("button", { name: "Details: GitHub · 3 sources" }));
    const detail = screen.getByTestId("needs-detail");
    expect(detail.querySelectorAll("li")).toHaveLength(3);
    expect(detail.textContent).toContain("GitHub · acme/repo-2");
  });

  it("keeps two unknown failures apart, and their raw lines behind Details (Astra r1 2)", async () => {
    answerWith([
      ghSource(1, { cause: null, reason: "HTTP 404: Not Found (repos/acme/repo-1)" }),
      ghSource(2, { cause: null, reason: "HTTP 429: rate limit exceeded" }),
    ], 10);
    render(<NeedsDrawer />);
    await screen.findByText("10 need you");
    const sources = screen.getAllByTestId("needs-source-row");
    expect(sources).toHaveLength(2);
    for (const row of sources) {
      expect(face(row).fact).toBe("Cannot check");
      expect(row.textContent).not.toMatch(/HTTP 4/);
    }
    fireEvent.click(within(sources[1]).getByRole("button", { name: /^Details: / }));
    expect(screen.getByTestId("needs-detail").textContent).toContain("HTTP 429: rate limit exceeded");
  });

  it("keeps two Rooms' paused sources apart: each opens its own Room (Astra r1 1)", async () => {
    answerWith([paused(1, "pA"), paused(2, "pB")], 10);
    render(<NeedsDrawer />);
    await screen.findByText("10 need you");
    const sources = screen.getAllByTestId("needs-source-row");
    expect(sources.map((r) => r.querySelector(".needs-row-name")?.textContent)).toEqual([
      "GitHub · acme/paused-1", "GitHub · acme/paused-2",
    ]);
  });

  it("Reconnect opens Settings · Connections with GitHub focused", async () => {
    render(<NeedsDrawer />);
    await screen.findByText("9 need you");
    const group = screen.getByTestId("needs-source-row");
    fireEvent.click(within(group).getByRole("button", { name: "Reconnect: GitHub · 3 sources" }));
    expect(openSurfaceOr).toHaveBeenCalledWith("configure-settings", "/settings", "integration:github");
  });
});

// The test diet (2026-10-11): the Needs you -> Room seam of the A2b paths glass.
// replaces: tests/e2e/test_philo14_a2b_paths_glass.py::TestA2bPathsGlass::test_a_proposal_row_opens_the_room_with_the_proposal_selected
// The Needs you row (the hub's aggregate row, needs_you_aggregate._proposal_fields)
// and the Room (its NEEDS YOU proposal row, project_service.py `source: "proposal"`)
// are both mounted; his press on the row body opens the Room through the shell
// and the Room selects THAT proposal, its Confirm on the row; no drawer opens.
describe("A2b: a proposal row in Needs you opens the Room with the proposal selected", () => {
  const PROPOSAL = "Run the dry run on Nov 3";
  const now = new Date().toISOString();
  const roomNeeds = (id: string, text: string) => ({
    source: "proposal", kind: "proposal", title: text, why: "PROPOSED · Ledger cutover sync", since: now, url: null,
    verb: "confirm", verbHref: `/api/proposals/${id}/confirm`, severity: "info", proposal_id: id, proposal_kind: "action",
    host: null, speaker_label: null, due_hint: null, owner_hint: null, original_text: text, meeting_id: "m-sync",
    action_item_id: null, meeting_title: "Ledger cutover sync", meeting_started_at: now, created_at: now,
  });
  const ROOM = {
    project_id: "p-ledger", revision: 1, observed_at: now,
    project: { id: "p-ledger", name: "Payments ledger cutover", is_archived: false, meeting_count: 1, created_at: now, updated_at: now, target_at: null, revision: 1 },
    items: { state: "ok", focus: [], totals_by_type: {}, total: 0 },
    meetings: { state: "ok", count: 1, latest: null },
    resources: { state: "ok", count: 0, latest: null },
    changes: { state: "ok", recent: [] },
    review: { state: "absent", reason: "not_yet_built" },
    needsYou: { state: "ok", count: 2, items: [roomNeeds("prop-other", "Name the rollback owner"), roomNeeds("prop-dry", PROPOSAL)] },
    sources: { state: "ok", items: [], count: 0, nextCheckAt: null },
    health: { state: "ok", assessment: "on_track", reason: null, inputs: { overdue: 0, ciFailing: false, reviewWaitingDays: null, targetPassed: false } },
    sinceRead: { state: "ok", readAt: null, groups: [] },
    decisions: { state: "ok", items: [] },
    commitments: { state: "ok", items: [] },
    target: { state: "absent", reason: "x" },
    updates: { state: "absent", reason: "x" },
    steward: { state: "absent", reason: "x" },
  };
  const NEEDS = {
    count: 2, blockers: [], failedMeetings: [], coverage: [], complete: true,
    items: [
      { id: "proposal:prop-dry", ref: PROPOSAL, kind: "proposal", source: "proposal", title: PROPOSAL,
        why: "PROPOSED · Ledger cutover sync", severity: "info", projectId: "p-ledger", projectName: "Payments ledger cutover",
        proposalId: "prop-dry", proposalKind: "action", proposalHost: null, proposalDue: null,
        meetingTitle: "Ledger cutover sync", meetingId: "m-sync" },
      { id: "proposal:prop-budget", ref: "Cut the budget", kind: "proposal", source: "proposal", title: "Cut the budget",
        why: "PROPOSED · Budget sync", severity: "info", projectId: "p-infra", projectName: "Infra budget",
        proposalId: "prop-budget", proposalKind: "action", proposalHost: null, proposalDue: null,
        meetingTitle: "Budget sync", meetingId: "m-infra" },
    ],
  };

  function Room() {
    const [, setWings] = useHarnessState<ReactNode>(null);
    return (
      <TitleSlotContext.Provider value={() => {}}>
        <WingSlotContext.Provider value={setWings}>
          <ProjectRoomCore scope="project:p-ledger" />
        </WingSlotContext.Provider>
      </TitleSlotContext.Provider>
    );
  }

  it("the row body opens the Room; the Room selects that proposal with its Confirm; no drawer", async () => {
    useDrawers.setState({ drawers: [], infos: [] } as never);
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      const value = String(path);
      if (value.startsWith("/api/desk/needs-you")) return NEEDS as never;
      if (value === "/api/door") return DOOR as never;
      if (value.startsWith("/api/projects/p-ledger/room") && !value.includes("/room/read")) return ROOM as never;
      return {} as never;
    });
    render(<><NeedsDrawer /><Room /></>);
    await screen.findByText("2 need you");
    // R1 (#1923): the Room's rows wait behind the status line's "n need you".
    expect(screen.queryByTestId("proposal-row")).toBeNull();
    fireEvent.click(screen.getByTestId("room-status-need"));
    await waitFor(() => expect(screen.getAllByTestId("proposal-row")).toHaveLength(2));
    expect(document.querySelector("li[data-selected] [data-testid=proposal-row]")).toBeNull();

    const needsRow = row(PROPOSAL);
    expect(needsRow.getAttribute("data-opens")).toBe("true");
    fireEvent.click(needsRow.querySelector(".needs-row-name")!);

    await waitFor(() => expect(document.querySelectorAll("li[data-selected] [data-testid=proposal-row]")).toHaveLength(1));
    const selected = document.querySelector("li[data-selected]") as HTMLElement;
    expect(selected.textContent).toContain(PROPOSAL);
    expect(within(selected).getAllByTestId("proposal-confirm")).toHaveLength(1);
    expect(useDrawers.getState().drawers).toEqual([]);
  });
});

// HS-171 (the arrival glass, muted leg): the muted are listed dimmed. The dim
// is needs.css's `.needs-drawer-muted.surface-section` rule (CSS values are not
// pinned in vitest: push 2's vitest-scan); this checks the rendered Muted
// section wears that class.
describe("NeedsDrawer muted rows are dimmed", () => {
  it("the Muted section wears needs-drawer-muted", async () => {
    // replaces: tests/e2e/test_hs170_arrival_glass.py::TestArrivalGlass::test_arrival_muted_1440 (the dim)
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (String(path).startsWith("/api/desk/needs-you"))
        return { ...ANSWER, items: [...ITEMS, { ...ITEMS[4], id: "decision:d-muted", ref: "decision:d-muted", openRef: "decision:d-muted", title: "A muted decision", muted: true }] } as never;
      return { upcoming: [], calendar_configured: true } as never;
    });
    await mount();
    fireEvent.click(screen.getByTestId("needs-chip-more"));
    const muted = screen.getByTestId("needs-muted");
    expect(muted.classList.contains("needs-drawer-muted")).toBe(true);
    expect(muted.classList.contains("surface-section")).toBe(true);
    expect(within(muted).getByText("A muted decision")).toBeTruthy();
  });
});

describe("W1-DOORS (atlas 2026-10-27): a meeting that names a Project", () => {
  it("is named after the meeting; the matched word is its state", async () => {
    const { needFace } = await import("../needsFace");
    // The hub's row (needs_you_aggregate, a recorded seeded-hub answer).
    const item = {
      projectId: "p-ledger", projectName: "Payments ledger cutover", ref: "meeting:m-standup",
      title: "mentions ledger", why: "Ledger cutover sync", kind: "meeting_match", source: "meeting",
      severity: "info", id: "p-ledger:meeting:meeting:m-standup", meetingId: "m-standup",
      meetingTitle: "Ledger cutover sync", since: "2026-10-27T00:57:26",
    };
    const face = needFace({ ref: item.id, kind: "attention", item } as never,
      { flights: [], sessions: [], now: new Date("2026-10-27T03:00:00") });
    expect(face.name).toBe("Ledger cutover sync");
    expect(face.lamp?.label).toBe("Mentions ledger");
  });
});


describe("W4 (the words): the meetings that say one Project's word are one row", () => {
  const match = (id: string, title: string, word: string) => ({
    projectId: "p-ledger", projectName: "Payments ledger cutover", ref: `meeting:${id}`,
    title: `mentions ${word}`, why: title, kind: "meeting_match", source: "meeting",
    severity: "info", id: `p-ledger:meeting:meeting:${id}`, meetingId: id, openRef: `meeting:${id}`,
    meetingTitle: title, since: "2026-10-27T00:57:26",
  });
  it("folds three cutover meetings into `3 mentions of cutover`; Show lists each by its title", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (String(path).startsWith("/api/desk/needs-you"))
        return { ...ANSWER, items: [
          ...ITEMS,
          match("m-1", "Vendor sync", "cutover"),
          match("m-2", "Q1 planning", "cutover"),
          match("m-3", "Sprint retro", "cutover"),
          match("m-4", "1:1 Avery", "ledger"),
        ] } as never;
      return { upcoming: [], calendar_configured: true } as never;
    });
    render(<NeedsDrawer />);
    const list = await screen.findByTestId("needs-list");
    expect(await within(list).findByText("3 mentions of cutover")).toBeTruthy();
    // One meeting for a word keeps its own row, named after the meeting.
    expect(within(list).getByText("1:1 Avery")).toBeTruthy();
    expect(within(list).queryByText("Vendor sync")).toBeNull();
    expect(within(list).queryAllByText("Mentions cutover")).toHaveLength(0);
    fireEvent.click(within(list).getByTestId("needs-match-toggle"));
    for (const title of ["Vendor sync", "Q1 planning", "Sprint retro"]) expect(within(list).getByText(title)).toBeTruthy();
    expect(within(list).getByTestId("needs-match-toggle").getAttribute("aria-expanded")).toBe("true");
  });
});

// Phone (PHONE-DESIGN §9): the recorded phone_items (needs_you.phone.json,
// recorded by PH-HUB through the real routes). Each verb is the hub's own.
import needsPhone from "../../calls/__fixtures__/needs_you.phone.json";
import { usePhoneFocus } from "../../calls/phoneFocus";

describe("Phone: asked on your phone, a missed call, a held call", () => {
  it("draws the hub's line and verbs; Call now presses its href; the row leaves on the next read; Answer here opens the Phone wing", async () => {
    let answered = false;
    const pressed: Array<{ path: string; json: unknown }> = [];
    const phoneItems = (needsPhone as { items: Array<Record<string, unknown>> }).items;
    vi.mocked(apiFetch).mockImplementation(async (path: string, init?: unknown) => {
      const value = String(path);
      if (value.startsWith("/api/desk/needs-you")) {
        const items = answered ? phoneItems.filter((item) => (item.phone as { kind: string }).kind !== "asked") : phoneItems;
        return { ...ANSWER, count: items.length, items } as never;
      }
      if (value.startsWith("/api/phone/")) {
        pressed.push({ path: value, json: (init as { json?: unknown })?.json });
        answered = true;
        return { call_id: "pcall_new", state: "ringing" } as never;
      }
      if (value === "/api/door") return DOOR as never;
      return {} as never;
    });
    render(<NeedsDrawer />);
    const asked = phoneItems.find((item) => (item.phone as { kind: string }).kind === "asked")!;
    const callNow = await screen.findByRole("button", { name: `Call now: ${asked.title}` });
    expect(screen.getByText("Asked on your phone · now · no reply")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: `Let it wait: ${asked.title}` })).toBeInTheDocument();
    fireEvent.click(callNow);
    await waitFor(() => expect(pressed[0]).toEqual({
      path: "/api/phone/calls", json: (asked.phone as { verbs: Array<{ body: unknown }> }).verbs[0].body,
    }));
    await waitFor(() => expect(screen.queryByRole("button", { name: `Call now: ${asked.title}` })).toBeNull());
    // The missed call's Answer here needs his words: it opens the Phone wing to reply.
    const missed = phoneItems.find((item) => (item.phone as { kind: string }).kind === "missed_call")!;
    fireEvent.click(screen.getByRole("button", { name: `Answer here: ${missed.title}` }));
    expect(usePhoneFocus.getState()).toMatchObject({ pending: true, replyTo: (missed.phone as { msgId: string }).msgId });
    expect(openSurfaceOr).toHaveBeenCalledWith("open-calls", "/");
    expect(pressed).toHaveLength(1);
  });
});

describe("the briefing page on a Program row (PG-DIRECTION DIR3)", () => {
  const read = (items: unknown[]) => ({ items, blockers: [], failedMeetings: [], coverage: [], complete: true });

  it("Copy page link makes the page and copies its link; the row's line then says the page is open, with Revoke", async () => {
    const writeText = vi.fn(async () => undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    const posts: { path: string; json: unknown }[] = [];
    let made = false;
    vi.mocked(apiFetch).mockImplementation(async (path: string, init?: unknown) => {
      const value = String(path);
      if (value.startsWith("/api/desk/needs-you")) return read(made ? needsPageOpen.items : needsPageNone.items) as never;
      if (value === "/api/reach/packages") {
        posts.push({ path: value, json: (init as { json?: unknown })?.json });
        made = true;
        return reachPackage as never;
      }
      if (value === "/api/door") return DOOR as never;
      return {} as never;
    });
    render(<NeedsDrawer />);
    // Owner walk 2026-11-08: the row is the Program; Send is in its menu.
    const title = needsPageNone.items[0].group;
    await waitFor(() => expect(face(row(title)).verbs).toEqual(["Decide"]));
    expect(face(row(title)).fact).not.toMatch(/Page/);
    fireEvent.contextMenu(row(title), { clientX: 40, clientY: 60 });
    fireEvent.click(await screen.findByRole("menuitem", { name: "Send" }));
    fireEvent.click(await screen.findByRole("menuitem", { name: "Copy page link" }));
    await waitFor(() => expect(face(row(title)).verbs).toEqual(["Decide"]));
    await waitFor(() => expect(face(row(title)).fact).toMatch(/Page link copied/));
    fireEvent.contextMenu(row(title), { clientX: 40, clientY: 60 });
    const menu = await screen.findByRole("menu", { name: title });
    expect(within(menu).getAllByRole("menuitem").map((m) => m.textContent)).toContain("Revoke the page");
    expect(within(menu).queryByRole("menuitem", { name: "Send" })).toBeNull();
    fireEvent.keyDown(menu, { key: "Escape" });
    expect(posts).toEqual([{ path: "/api/reach/packages", json: { refs: [needsPageNone.items[0].id] } }]);
    expect(writeText).toHaveBeenCalledWith(`${window.location.origin}${reachPackage.path}`);
    expect(face(row(title)).fact).toMatch(/Page link copied · open until \d\d:\d\d$/);
  });

  it("Revoke ends the page; the item stays with its own verbs", async () => {
    let revoked = false;
    const page = needsPageOpen.items[0].program.page;
    const posts: string[] = [];
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      const value = String(path);
      if (value.startsWith("/api/desk/needs-you")) return read(revoked ? needsPageNone.items : needsPageOpen.items) as never;
      if (value.startsWith("/api/reach/packages/")) {
        posts.push(value);
        revoked = true;
        return { id: page.package_id, revoked: true } as never;
      }
      if (value === "/api/door") return DOOR as never;
      return {} as never;
    });
    render(<NeedsDrawer />);
    const title = needsPageOpen.items[0].group;
    // (The copy above, in this module, marked the same recorded page copied.)
    await waitFor(() => expect(face(row(title)).fact).toMatch(/(Page open|Page link copied · open) until \d\d:\d\d$/));
    fireEvent.contextMenu(row(title), { clientX: 40, clientY: 60 });
    fireEvent.click(await screen.findByRole("menuitem", { name: "Revoke the page" }));
    await waitFor(() => expect(face(row(title)).fact).not.toMatch(/Page/));
    expect(face(row(title)).verbs).toEqual(["Decide"]);
    expect(posts).toEqual([`/api/reach/packages/${page.package_id}/revoke`]);
  });
});

describe("Later and Telegram on a Program row (PG-DIRECTION DIR4, DIR5)", () => {
  const read = (items: unknown[]) => ({ items, blockers: [], failedMeetings: [], coverage: [], complete: true });
  const clock = (stamp: string) => {
    const at = new Date(stamp);
    return `${String(at.getHours()).padStart(2, "0")}:${String(at.getMinutes()).padStart(2, "0")}`;
  };

  it("the line says it was sent to Telegram and the page is open; no chip", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      const value = String(path);
      if (value.startsWith("/api/desk/needs-you")) return read(needsSent.items) as never;
      if (value === "/api/door") return DOOR as never;
      return {} as never;
    });
    render(<NeedsDrawer />);
    const item = needsSent.items[0];
    const sent = item.program.page.sent;
    await waitFor(() => expect(face(row(item.group)).fact).toContain(
      `Sent to Telegram ${clock(sent.at)} · page open until ${clock(item.program.page.expires_at)}`));
    expect(face(row(item.group)).egress).toBe("");
    expect(face(row(item.group)).verbs).toEqual(["Decide"]);
  });

  it("Later ▸ In 1 hour in the row's menu defers the item: it leaves the desk of today for Later, not counted, with its time", async () => {
    let deferred = false;
    const posts: { path: string; json: unknown }[] = [];
    vi.mocked(apiFetch).mockImplementation(async (path: string, init?: unknown) => {
      const value = String(path);
      if (value.startsWith("/api/desk/needs-you")) return read(deferred ? needsLater.items : needsSent.items) as never;
      if (value === "/api/reach/later") {
        posts.push({ path: value, json: (init as { json?: unknown })?.json });
        deferred = true;
        return { until: needsLater.items[0].later.until, words: "Later · back at 13:00" } as never;
      }
      if (value === "/api/door") return DOOR as never;
      return {} as never;
    });
    render(<NeedsDrawer />);
    const item = needsSent.items[0];
    fireEvent.contextMenu(await waitFor(() => row(item.group)), { clientX: 40, clientY: 60 });
    fireEvent.click(await screen.findByRole("menuitem", { name: "Later" }));
    fireEvent.click(await screen.findByRole("menuitem", { name: "In 1 hour" }));
    await waitFor(() => expect(posts).toEqual([{ path: "/api/reach/later", json: { ref: item.id, later: "in_1h" } }]));
    const later = needsLater.items[0];
    // The bold mast (2026-11-08): a row for a later day waits behind Later.
    fireEvent.click(await screen.findByTestId("needs-chip-later"));
    await waitFor(() => expect(face(row(later.group)).fact).toContain(`Later · back at ${clock(later.later.until)}`));
    fireEvent.contextMenu(row(later.group), { clientX: 40, clientY: 60 });
    const menu = await screen.findByRole("menu", { name: later.group });
    expect(within(menu).queryByRole("menuitem", { name: "Later" })).toBeNull();
    await waitFor(() => expect(row(later.group).getAttribute("data-counted")).toBe("false"));
  });
});

// Owner walk 2026-11-08 ("way too cluttered, 'more' doesn't even look like a
// button… the 'Done', the 'Yours'"): one row, one verb. Replays the hub's
// recorded answers (needs_you.rows.json), never typed rows.
describe("one row, one verb (owner walk 2026-11-08)", () => {
  const [before, afterDone] = needsRows.steps as Array<{ gets: Gets; post?: string; body?: unknown }>;
  const must = "openSystemShade() fires an event nobody hears";
  let hub: Gets;
  let posts: Array<{ path: string; json: unknown }>;

  beforeEach(() => {
    hub = before.gets;
    posts = [];
    vi.mocked(openIntelligence).mockClear();
    vi.mocked(apiFetch).mockImplementation(async (path: string, init?: unknown) => {
      const method = (init as { method?: string } | undefined)?.method ?? "GET";
      if (method !== "GET") {
        posts.push({ path: String(path), json: (init as { json?: unknown }).json });
        if (String(path) === afterDone.post) hub = afterDone.gets;
        return {} as never;
      }
      return recordedGet(hub, String(path)) as never;
    });
  });

  const names = () => [...document.querySelectorAll<HTMLElement>("[data-testid='needs-list'] li.needs-row .needs-row-name")]
    .map((n) => n.textContent);

  it("a row under Mine is the glyph, the name and Done: no Yours, no More", async () => {
    render(<NeedsDrawer />);
    await screen.findByText("4 need you");
    const li = row(must);
    expect(li.querySelector("[data-testid=needs-row-state]")).toBeNull();
    expect(li.textContent).not.toMatch(/Yours/i);
    expect([...li.querySelectorAll(".needs-row-verbs button")].map((b) => b.textContent)).toEqual(["Done"]);
    // The must-fix row is the first plate: its Done is the brass Button.
    expect(li.closest("[data-testid='needs-first']")).toBeTruthy();
    expect(within(li).getByRole("button", { name: `Done: ${must}` }).className).toContain("btn--brass");
    expect(li.querySelector("[data-verb='more']")).toBeNull();
  });

  it("the three prefixes become kinds: the glyph's tint and the order, must first", async () => {
    render(<NeedsDrawer />);
    await screen.findByText("4 need you");
    // The hub ranks must, noted, plain, should; the rows sort by weight.
    expect(names()).toEqual([
      must,
      "the walk sheet keeps its old height",
      "Book the cutover dry run",
      "the Dock badge reads the count twice",
    ]);
    expect(names().some((n) => /^(Must fix|Should fix|Noted):/.test(n ?? ""))).toBe(false);
    const tiers = [...document.querySelectorAll<HTMLElement>("[data-testid='needs-list'] li.needs-row")]
      .map((li) => [li.getAttribute("data-tier"), li.querySelector(":scope > img")?.getAttribute("alt")]);
    expect(tiers).toEqual([["must", "Must fix"], ["should", "Should fix"], [null, "Action"], ["noted", "Noted"]]);
  });

  it("a press on the row reads the item in place; Done does not", async () => {
    render(<NeedsDrawer />);
    await screen.findByText("4 need you");
    fireEvent.click(row(must).querySelector(".needs-row-name")!);
    expect(await screen.findByTestId("needs-reader")).toBeTruthy();
    expect(openIntelligence).not.toHaveBeenCalled();
    fireEvent.click(screen.getByTestId("needs-reader-back"));
    fireEvent.click(within(row(must)).getByRole("button", { name: `Done: ${must}` }));
    await waitFor(() => expect(posts).toHaveLength(1));
    expect(screen.queryByTestId("needs-reader")).toBeNull();
    expect(openIntelligence).not.toHaveBeenCalled();
  });

  it("Done posts the done act; the row leaves and the count ticks down", async () => {
    render(<NeedsDrawer />);
    await screen.findByText("4 need you");
    expect(screen.getByTestId("needs-mast").querySelector("h2")?.textContent).toMatch(/· 1 must fix$/);
    fireEvent.click(within(row(must)).getByRole("button", { name: `Done: ${must}` }));
    await screen.findByText("3 need you");
    expect(posts).toEqual([{ path: afterDone.post, json: afterDone.body }]);
    expect(names()).not.toContain(must);
    expect(names()).toHaveLength(3);
    expect(screen.getByTestId("needs-mast").querySelector("h2")?.textContent).toMatch(/· 3 need you$/);
  });

  it("the other verbs are the row's context menu; More is gone", async () => {
    render(<NeedsDrawer />);
    await screen.findByText("4 need you");
    fireEvent.contextMenu(row(must), { clientX: 40, clientY: 60 });
    const menu = await screen.findByRole("menu", { name: must });
    expect(within(menu).getAllByRole("menuitem").map((m) => m.textContent)).toEqual(
      expect.arrayContaining(["Open", "Later", "Drop", "Run as a program", "Hand to an agent session"]),
    );
    fireEvent.click(within(menu).getByRole("menuitem", { name: /Later/ }));
    await waitFor(() => expect(posts.map((p) => (p.json as { verb?: string }).verb)).toEqual(["snooze"]));
  });

  // One verb, one name (2026-11-08): the menu's agent entry is the one Run as
  // a program (RunAsProgram.tsx), never a second "Hand to agent".
  it("Run as a program in the row menu makes the program from the action and opens it", async () => {
    vi.mocked(openProgram).mockClear();
    const answer = vi.mocked(apiFetch).getMockImplementation()!;
    vi.mocked(apiFetch).mockImplementation(async (path: string, init?: unknown) => {
      const done = await answer(path, init as never);
      return (String(path) === "/api/programs/from-action" ? madeFromAction : done) as never;
    });
    render(<NeedsDrawer />);
    await screen.findByText("4 need you");
    fireEvent.contextMenu(row(must), { clientX: 40, clientY: 60 });
    const menu = await screen.findByRole("menu", { name: must });
    expect(within(menu).queryByRole("menuitem", { name: "Hand to agent" })).toBeNull();
    fireEvent.click(within(menu).getByRole("menuitem", { name: "Run as a program" }));
    await waitFor(() => expect(openProgram).toHaveBeenCalledWith(String((madeFromAction as { id?: string }).id)));
    expect(posts).toEqual([{ path: "/api/programs/from-action", json: { action_id: "rows-must" } }]);
  });

  it("the toolbar is one segmented control; People shows what a person owes, named by the person", async () => {
    render(<NeedsDrawer />);
    await screen.findByText("4 need you");
    const toolbar = screen.getByTestId("needs-toolbar");
    // The band: the one control at its left; at its right only the calendar
    // offer this recorded desk has (no calendar), never a People Button.
    const scope = within(toolbar).getByTestId("needs-scope");
    expect(scope.getAttribute("role")).toBe("group");
    expect([...scope.querySelectorAll("button")].map((b) => b.textContent)).toEqual(["Mine", "People"]);
    expect([...toolbar.querySelectorAll("[data-testid='needs-no-calendar'] button")].map((b) => b.textContent)).toEqual(["Connect calendar"]);
    expect(toolbar.querySelector(".kit-toolglyph")).toBeNull();
    expect(names()).not.toContain("Send the vendor contract");
    fireEvent.click(within(toolbar).getByRole("button", { name: "People" }));
    expect(names()).toEqual(["Send the vendor contract"]);
    const li = row("Send the vendor contract");
    expect(li.querySelector("[data-testid=needs-row-state]")?.textContent).toBe("Bea");
    expect(screen.getByTestId("needs-people-open")).toBeTruthy();
  });
});

// The owner, 2026-11-08, on his phone: "I can't open any of these when double
// clicking on the title… right clicking and using the open option - still
// nothing happened." An action item with no other home reads ITSELF in place
// (ItemReader.tsx). Replays needs_you.rows.json (the recorded hub answers).
describe("the item reader: an action item opens itself (2026-11-08)", () => {
  const [before, afterDone] = needsRows.steps as Array<{ gets: Gets; post?: string; body?: unknown }>;
  const must = "openSystemShade() fires an event nobody hears";
  let hub: Gets;
  let posts: Array<{ path: string; json: unknown }>;

  beforeEach(() => {
    hub = before.gets;
    posts = [];
    vi.mocked(openIntelligence).mockClear();
    vi.mocked(markDone).mockClear();
    vi.mocked(apiFetch).mockImplementation(async (path: string, init?: unknown) => {
      const method = (init as { method?: string } | undefined)?.method ?? "GET";
      if (method !== "GET") {
        posts.push({ path: String(path), json: (init as { json?: unknown }).json });
        if (String(path) === afterDone.post) hub = afterDone.gets;
        return {} as never;
      }
      return recordedGet(hub, String(path)) as never;
    });
  });

  const reader = () => screen.getByTestId("needs-reader");

  it("a press on a bare action item's row shows the reader: the whole text, the facts in words, the verbs", async () => {
    render(<NeedsDrawer />);
    await screen.findByText("4 need you");
    fireEvent.click(row(must).querySelector(".needs-row-name")!);
    await screen.findByTestId("needs-reader");
    // The list gives the window to the reader; nothing opens elsewhere.
    expect(screen.queryByTestId("needs-list")).toBeNull();
    expect(openIntelligence).not.toHaveBeenCalled();
    const text = within(reader()).getByTestId("needs-reader-text");
    expect(text.textContent).toBe(must);
    expect(text.tagName).toBe("H2");
    const facts = within(reader()).getByTestId("needs-reader-facts").textContent ?? "";
    expect(facts.split(" · ")[0]).toBe("Must fix");
    expect(facts).toContain("Yours");
    expect(facts).toMatch(/since \S/);
    expect(facts).toContain("from a meeting");
    expect(facts).not.toMatch(/\b0\b|undefined|null/);
    const verbs = [...within(screen.getByTestId("needs-reader-toolbar")).getAllByRole("button")].map((b) => b.textContent);
    expect(verbs).toEqual(expect.arrayContaining(["‹ Needs you", "Done", "Later", "Run as a program", "Hand to an agent session"]));
    // No Project on this item: no Open the Project.
    expect(verbs.some((v) => /Open the Project/.test(v ?? ""))).toBe(false);
    expect(within(reader()).getByRole("button", { name: `Done: ${must}` }).className).toContain("btn--primary");
  });

  it("Open in the row menu shows the reader", async () => {
    render(<NeedsDrawer />);
    await screen.findByText("4 need you");
    fireEvent.contextMenu(row(must), { clientX: 40, clientY: 60 });
    const menu = await screen.findByRole("menu", { name: must });
    fireEvent.click(within(menu).getByRole("menuitem", { name: "Open" }));
    expect((await screen.findByTestId("needs-reader-text")).textContent).toBe(must);
    expect(openIntelligence).not.toHaveBeenCalled();
  });

  it("Back returns to the list", async () => {
    render(<NeedsDrawer />);
    await screen.findByText("4 need you");
    fireEvent.click(row(must).querySelector(".needs-row-name")!);
    await screen.findByTestId("needs-reader");
    fireEvent.click(screen.getByTestId("needs-reader-back"));
    expect(screen.queryByTestId("needs-reader")).toBeNull();
    expect(row(must)).toBeTruthy();
    expect(posts).toEqual([]);
  });

  it("Done in the reader is markDone's; the reader returns to the list without the item", async () => {
    render(<NeedsDrawer />);
    await screen.findByText("4 need you");
    fireEvent.click(row(must).querySelector(".needs-row-name")!);
    await screen.findByTestId("needs-reader");
    fireEvent.click(within(reader()).getByRole("button", { name: `Done: ${must}` }));
    await screen.findByText("3 need you");
    expect(markDone).toHaveBeenCalledTimes(1);
    expect(posts).toEqual([{ path: afterDone.post, json: afterDone.body }]);
    expect(screen.queryByTestId("needs-reader")).toBeNull();
    expect(screen.getByTestId("needs-list")).toBeTruthy();
    expect(screen.queryByText(must)).toBeNull();
  });

  it("Later in the reader snoozes the item to tomorrow, as the row menu's Later does", async () => {
    render(<NeedsDrawer />);
    await screen.findByText("4 need you");
    fireEvent.click(row(must).querySelector(".needs-row-name")!);
    await screen.findByTestId("needs-reader");
    fireEvent.click(within(reader()).getByRole("button", { name: `Later: ${must}` }));
    await waitFor(() => expect(posts.map((p) => (p.json as { verb?: string }).verb)).toEqual(["snooze"]));
    expect((posts[0].json as { card_id?: string }).card_id).toBe("rows-must");
    await waitFor(() => expect(screen.queryByTestId("needs-reader")).toBeNull());
  });

  it("an action_item ref (the follow-through request) opens that item in the reader", async () => {
    render(<NeedsDrawer />);
    await screen.findByText("4 need you");
    act(() => {
      window.dispatchEvent(new CustomEvent(INTELLIGENCE_NAVIGATE, {
        detail: { view: "follow-through", followThroughId: "rows-plain" },
      }));
    });
    expect((await screen.findByTestId("needs-reader-text")).textContent).toBe("Book the cutover dry run");
    // A plain item has no weight word: its facts lead with whose it is.
    expect(within(reader()).getByTestId("needs-reader-facts").textContent).toMatch(/^Yours · since /);
  });
});

// Owner walk 2026-11-08, the Program rows: the row is the Program (its title),
// the ask's quiet word and ONE verb; Later and Send are the row's menu.
// Replays the hub's recorded answers (needs_you.rows.json `program`, recorded
// by scripts/record_needs_you_fixture.py --rows on the Programs rig).
describe("a Program row is the object (owner walk 2026-11-08)", () => {
  const program = (needsRows as unknown as { program: { title: string; steps: Array<{ gets: Gets; post?: string; body?: unknown }> } }).program;
  const [before, afterMerge] = program.steps;
  const title = program.title;
  const ask = (before.gets["/api/desk/needs-you?fresh=1"] as { items: Array<{ title: string; openRef: string }> }).items[0];
  let hub: Gets;
  let posts: Array<{ path: string; json: unknown }>;
  const openPullout = vi.fn();
  const REAL_PULLOUT = useDesk.getState().openPullout;

  beforeEach(() => {
    hub = before.gets;
    posts = [];
    openPullout.mockClear();
    useDesk.setState({ openPullout } as never);
    vi.mocked(apiFetch).mockImplementation(async (path: string, init?: unknown) => {
      const method = (init as { method?: string } | undefined)?.method ?? "GET";
      if (method !== "GET") {
        posts.push({ path: String(path), json: (init as { json?: unknown }).json });
        if (String(path) === afterMerge.post) hub = afterMerge.gets;
        return {} as never;
      }
      return recordedGet(hub, String(path)) as never;
    });
    return () => useDesk.setState({ openPullout: REAL_PULLOUT } as never);
  });

  it("a Merge ask is the Program's title, the quiet word Merge and one verb, Merge; no Later ▾, no Send ▾", async () => {
    render(<NeedsDrawer />);
    const li = await waitFor(() => row(title));
    expect(face(li).lamps).toEqual(["Merge"]);
    expect(face(li).verbs).toEqual(["Merge"]);
    // The bold face: the Program that waits is the first plate; Merge is its
    // brass Button, beside Open the Program and Later (the times).
    expect(li.closest("[data-testid='needs-first']")).toBeTruthy();
    expect(within(li).getByRole("button", { name: `Merge: ${title}` }).className).toContain("btn--brass");
    expect(within(li).getByTestId("needs-first-open").textContent).toBe("Open the Program");
    // The one rule: the step's number stays; the step's question is the hover.
    expect(face(li).fact).toBe("Step 1");
    expect(li.querySelector(".needs-row-fact")?.getAttribute("title")).toBe(ask.title);
    expect(li.querySelector("[data-verb='program-defer'], [data-verb='program-send']")).toBeNull();
    expect(li.textContent).not.toMatch(/▾/);
  });

  it("the row's context menu carries Not yet, Later (the times) and Send (the page)", async () => {
    render(<NeedsDrawer />);
    fireEvent.contextMenu(await waitFor(() => row(title)), { clientX: 40, clientY: 60 });
    const menu = await screen.findByRole("menu", { name: title });
    expect(within(menu).getAllByRole("menuitem").map((m) => m.textContent)).toEqual(["Open", "Not yet", "Later»", "Send»"]);
    fireEvent.click(within(menu).getByRole("menuitem", { name: "Later" }));
    for (const time of ["In 1 hour", "At 13:00", "Tonight", "Tomorrow"]) {
      expect(await screen.findByRole("menuitem", { name: time })).toBeTruthy();
    }
    fireEvent.click(within(menu).getByRole("menuitem", { name: "Send" }));
    expect(await screen.findByRole("menuitem", { name: "Copy page link" })).toBeTruthy();
    expect(screen.getByRole("menuitem", { name: "Send to Telegram" })).toBeTruthy();
  });

  it("a press on the row opens the Program; a press on Merge does only the merge", async () => {
    render(<NeedsDrawer />);
    fireEvent.click((await waitFor(() => row(title))).querySelector(".needs-row-name")!);
    await waitFor(() => expect(openPullout).toHaveBeenCalledWith(ask.openRef));
    openPullout.mockClear();
    fireEvent.click(within(row(title)).getByRole("button", { name: `Merge: ${title}` }));
    await waitFor(() => expect(posts).toEqual([{ path: afterMerge.post, json: afterMerge.body }]));
    expect(openPullout).not.toHaveBeenCalled();
  });

  it("after the merge the Program's close is his turn: the quiet word Your turn, the verb Open", async () => {
    render(<NeedsDrawer />);
    fireEvent.click(within(await waitFor(() => row(title))).getByRole("button", { name: `Merge: ${title}` }));
    await waitFor(() => expect(face(row(title)).lamps).toEqual(["Your turn"]));
    expect(face(row(title)).verbs).toEqual(["Open"]);
    fireEvent.click(within(row(title)).getByRole("button", { name: `Open: ${title}` }));
    await waitFor(() => expect(openPullout).toHaveBeenCalledWith(ask.openRef));
  });
});

// Glue 2026-11-08 (the row is the object, one verb): Decide decides in place
// on a Program row, the row's open carries the step, and one function writes
// a decision's status. Replays the hub's recorded Decide ask (a core question
// with Go on / Park, needs_you.page_none.json, recorded by
// tests/integration/test_desk_reach.py) and the Merge ask of needs_you.rows.json.
describe("Decide decides in place; the step travels (glue 2026-11-08)", () => {
  const item = needsPageNone.items[0];
  const title = item.group;
  const openPullout = vi.fn();
  const REAL_PULLOUT = useDesk.getState().openPullout;
  let posts: Array<{ path: string; json: unknown }>;
  let decided: boolean;

  beforeEach(() => {
    posts = [];
    decided = false;
    openPullout.mockClear();
    useDesk.setState({ openPullout } as never);
    vi.mocked(apiFetch).mockImplementation(async (path: string, init?: unknown) => {
      const value = String(path);
      const method = (init as { method?: string } | undefined)?.method ?? "GET";
      if (method !== "GET") {
        posts.push({ path: value, json: (init as { json?: unknown }).json });
        if (value === item.program.decide) decided = true;
        return {} as never;
      }
      if (value.startsWith("/api/desk/needs-you")) {
        return { items: decided ? [] : needsPageNone.items, blockers: [], failedMeetings: [], coverage: [], complete: true } as never;
      }
      if (value === "/api/door") return DOOR as never;
      return {} as never;
    });
    return () => useDesk.setState({ openPullout: REAL_PULLOUT } as never);
  });

  it("Decide opens the hub's choices under the row; a choice posts to the step's decide route and the row goes", async () => {
    render(<NeedsDrawer />);
    const li = await waitFor(() => row(title));
    expect(face(li).verbs).toEqual(["Decide"]);
    fireEvent.click(within(li).getByRole("button", { name: `Decide: ${title}` }));
    const panel = await screen.findByRole("region", { name: `Decide: ${title}` });
    // The same panel the meeting's decision uses, built from the hub's choices.
    expect(panel.getAttribute("data-testid")).toBe("needs-decide");
    expect(within(panel).getAllByRole("button").map((b) => b.textContent)).toEqual(["Go on", "Park", "Open item"]);
    expect(openPullout).not.toHaveBeenCalled();
    fireEvent.click(within(panel).getByRole("button", { name: `Go on: ${title}` }));
    await waitFor(() => expect(posts).toEqual([{ path: item.program.decide, json: { kind: "core", choice: "go_on" } }]));
    await waitFor(() => expect(screen.queryByRole("region", { name: `Decide: ${title}` })).toBeNull());
    await waitFor(() => expect(() => row(title)).toThrow());
  });

  it("the row's open carries the step: the Program window opens with that step asked for", async () => {
    const { takeProgramStepRequest } = await import("../../openObject");
    render(<NeedsDrawer />);
    fireEvent.click((await waitFor(() => row(title))).querySelector(".needs-row-name")!);
    await waitFor(() => expect(openPullout).toHaveBeenCalledWith(`program:${item.program.programId}`));
    expect(takeProgramStepRequest(item.program.programId)).toBe(item.program.stepId);
    // Once: the request is taken.
    expect(takeProgramStepRequest(item.program.programId)).toBeNull();
  });

  it("one accept: no face writes a decision's status but decide.ts", async () => {
    const fs = await import("node:fs");
    const path = await import("node:path");
    const root = path.resolve(__dirname, "../../..");
    const writers: string[] = [];
    const walk = (dir: string) => {
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) { if (!["__tests__", "_parked", "node_modules"].includes(entry.name)) walk(full); continue; }
        if (!/\.tsx?$/.test(entry.name) || /\.test\.tsx?$/.test(entry.name)) continue;
        if (/\/api\/decisions\/\$\{[^}]+\}\/status/.test(fs.readFileSync(full, "utf8"))) writers.push(path.relative(root, full));
      }
    };
    walk(root);
    expect(writers).toEqual(["desk/decide.ts"]);
  });
});

// One Done (2026-11-08): Done on a work row, a Room commitment and a People
// promise each reach their route through the one markDone, read one receipt
// and settle the row. Replays needs_you.rows.json (`steps` and `done`,
// recorded by scripts/record_needs_you_fixture.py --rows), never typed rows.
describe("one Done for a promise (2026-11-08)", () => {
  type Step = { gets: Gets; post?: string; body?: unknown; answer?: unknown };
  const done = needsRows.done as unknown as { commitment: string; promise: string; steps: Step[] };
  let hub: Gets;
  let posts: Array<{ path: string; json: unknown }>;

  const replay = (steps: Step[]) => {
    hub = steps[0].gets;
    posts = [];
    vi.mocked(markDone).mockClear();
    vi.mocked(apiFetch).mockImplementation(async (path: string, init?: unknown) => {
      const method = (init as { method?: string } | undefined)?.method ?? "GET";
      if (method !== "GET") {
        posts.push({ path: String(path), json: (init as { json?: unknown }).json });
        const step = steps.find((s) => s.post === String(path));
        if (!step) throw new Error(`no recorded answer for ${String(path)}`);
        hub = step.gets;
        return step.answer as never;
      }
      return recordedGet(hub, String(path)) as never;
    });
  };
  const names = () => [...document.querySelectorAll<HTMLElement>("[data-testid='needs-list'] li.needs-row .needs-row-name")]
    .map((n) => n.textContent);

  it("Done on a work row is markDone to the follow-through complete; the row settles", async () => {
    const steps = needsRows.steps as unknown as Step[];
    replay(steps);
    const must = "openSystemShade() fires an event nobody hears";
    render(<NeedsDrawer />);
    await screen.findByText("4 need you");
    fireEvent.click(within(row(must)).getByRole("button", { name: `Done: ${must}` }));
    await screen.findByText("3 need you");
    expect(markDone).toHaveBeenCalledTimes(1);
    expect(posts).toEqual([{ path: "/api/follow-through/complete", json: steps[1].body }]);
    expect(names()).not.toContain(must);
  });

  it("Done on a Room commitment is markDone to the follow-through complete; the row settles", async () => {
    replay(done.steps);
    render(<NeedsDrawer />);
    // The commitment is due on a later day (the count leaves it out): it
    // waits behind the mast's Later.
    fireEvent.click(await screen.findByTestId("needs-chip-later"));
    await waitFor(() => expect(names()).toContain(done.commitment));
    fireEvent.click(within(row(done.commitment)).getByRole("button", { name: `Done: ${done.commitment}` }));
    await waitFor(() => expect(names()).not.toContain(done.commitment));
    expect(markDone).toHaveBeenCalledTimes(1);
    const step = done.steps.find((s) => s.post === "/api/follow-through/complete")!;
    expect(posts).toEqual([{ path: step.post, json: step.body }]);
  });

  it("Done on a People promise is markDone to People's transition; the row settles", async () => {
    replay(done.steps);
    render(<NeedsDrawer />);
    await waitFor(() => expect(names()).toContain(done.promise));
    fireEvent.click(within(row(done.promise)).getByRole("button", { name: `Done: ${done.promise}` }));
    await waitFor(() => expect(names()).not.toContain(done.promise));
    expect(markDone).toHaveBeenCalledTimes(1);
    const step = done.steps.find((s) => String(s.post).startsWith("/api/people/commitments/"))!;
    expect(posts).toEqual([{ path: step.post, json: { verb: "done" } }]);
  });

  it("both routes answer the one receipt: the row's id, done, and when", () => {
    for (const step of [...done.steps.slice(1), (needsRows.steps as unknown as Step[])[1]]) {
      const receipt = readDoneReceipt(step.answer);
      expect(receipt.status).toBe("done");
      expect(receipt.id).toBe(String((step.answer as { card_id: string }).card_id));
      expect(receipt.doneAt).toMatch(/^\d{4}-\d{2}-\d{2}T/);
    }
  });

  it("no module in desk/needs but needsApi.ts posts to a Done route", () => {
    const dir = resolve(__dirname, "..");
    const routes = /\/api\/follow-through\/complete|\/api\/people\/commitments\/[^"'`]*\/transition/;
    const posting = readdirSync(dir).filter((name) => /\.tsx?$/.test(name))
      .filter((name) => routes.test(readFileSync(resolve(dir, name), "utf8")));
    expect(posting).toEqual(["needsApi.ts"]);
  });
});

// Engines 2026-11-08: an AI job that did not run waits on him. Replays the
// hub's recorded answers (needs_you.rows.json `engine`, recorded by
// scripts/record_needs_you_fixture.py --engine): a decision draft whose engine
// did not answer, Retry with the engine answering, the read after.
describe("an engine row: the job that did not run, and Retry (engines 2026-11-08)", () => {
  const engine = (needsRows as unknown as { engine: { title: string; steps: Array<{ gets: Gets; post?: string; body?: unknown }> } }).engine;
  const [before, afterRetry] = engine.steps;
  const title = engine.title;
  let hub: Gets;
  let posts: Array<{ path: string; json: unknown }>;

  beforeEach(() => {
    hub = before.gets;
    posts = [];
    vi.mocked(apiFetch).mockImplementation(async (path: string, init?: unknown) => {
      const method = (init as { method?: string } | undefined)?.method ?? "GET";
      if (method !== "GET") {
        posts.push({ path: String(path), json: (init as { json?: unknown }).json });
        if (String(path) === afterRetry.post) hub = afterRetry.gets;
        return {} as never;
      }
      return recordedGet(hub, String(path)) as never;
    });
  });

  it("names the engine, the job and why in one line, with the kind's sprite and one verb, Retry", async () => {
    render(<NeedsDrawer />);
    const li = await waitFor(() => row(title));
    expect(title).toMatch(/^drafts could not run the decision draft · /);
    expect(face(li).kind).toBe("decision");
    expect(face(li).verbs).toEqual(["Retry"]);
    expect(li.textContent).not.toMatch(/refused|Traceback|\//);
  });

  it("Retry runs the same job again through the door, and the row leaves when it answers", async () => {
    render(<NeedsDrawer />);
    fireEvent.click(within(await waitFor(() => row(title))).getByRole("button", { name: `Retry: ${title}` }));
    await waitFor(() => expect(posts).toEqual([{ path: afterRetry.post, json: afterRetry.body }]));
    await waitFor(() => expect(() => row(title)).toThrow());
  });
});

// Owner walk 2026-11-08 ("I can't open any of these when double clicking on
// the title… right clicking and using the open option - still nothing
// happened"). Every row kind opens its object as a window through the one
// open grammar (openObject's refOpener): a double-click on the title and the
// context menu's Open alike. Replays the hub's recorded answers.
describe("every row opens its object (owner walk 2026-11-08)", () => {
  const rows = needsRows as unknown as {
    done: { steps: Array<{ gets: Gets }> };
    program: { steps: Array<{ gets: Gets }> };
    engine: { steps: Array<{ gets: Gets }> };
  };
  const phoneItems = (needsPhone as { items: Array<{ title: string }> }).items;
  const people = (rows.done.steps[0].gets["/api/desk/needs-you?fresh=1"] as { items: Array<{ title: string; person_id: string }> }).items[0];
  const program = (rows.program.steps[0].gets["/api/desk/needs-you?fresh=1"] as { items: Array<{ group: string; openRef: string }> }).items[0];
  const engine = (rows.engine.steps[0].gets["/api/desk/needs-you?fresh=1"] as { items: Array<{ engine: { line: string } }> }).items[0];
  const phoneHub: Gets = { "/api/desk/needs-you?fresh=1": { ...ANSWER, failedMeetings: [], count: phoneItems.length, items: phoneItems } };
  const openPullout = vi.fn();
  const openSurfaceWindow = vi.fn();
  const REAL = { openPullout: useDesk.getState().openPullout, openSurfaceWindow: useDesk.getState().openSurfaceWindow };

  beforeEach(() => {
    openPullout.mockClear();
    openSurfaceWindow.mockClear();
    vi.mocked(openSurfaceOr).mockClear();
    useDesk.setState({ openPullout, openSurfaceWindow } as never);
    return () => useDesk.setState(REAL as never);
  });

  /** The windows asked for, in one list: a pull-out, a surface window, a surface. */
  const opened = () => [
    ...openPullout.mock.calls.map((c) => `pullout:${String(c[0])}`),
    ...openSurfaceWindow.mock.calls.map((c) => `surface:${String(c[0])}`),
    ...vi.mocked(openSurfaceOr).mock.calls.map((c) => `surface:${String(c[0])}`),
  ];

  const cases: Array<[string, () => Gets, string, string]> = [
    ["a Program step", () => rows.program.steps[0].gets, program.group, `pullout:${program.openRef.split(":").slice(0, 2).join(":")}`],
    ["a person's obligation", () => rows.done.steps[0].gets, people.title, `pullout:people:${people.person_id}`],
    ["an engine that did not run (Retry)", () => rows.engine.steps[0].gets, engine.engine.line, "surface:open-decisions"],
    ...phoneItems.map((item) => ["a phone row", () => phoneHub, item.title, "surface:open-calls"] as [string, () => Gets, string, string]),
  ];

  for (const [kind, hub, title, window] of cases) {
    it(`${kind}: a double-click on the title and the menu's Open open it as a window (${title.slice(0, 24)})`, async () => {
      vi.mocked(apiFetch).mockImplementation(async (path: string) => recordedGet(hub(), String(path)) as never);
      render(<NeedsDrawer />);
      const name = (await waitFor(() => row(title))).querySelector(".needs-row-name")!;
      // A double-click in a browser: two clicks, then the dblclick.
      fireEvent.click(name);
      fireEvent.click(name);
      fireEvent.doubleClick(name);
      await waitFor(() => expect(opened()).toContain(window));

      openPullout.mockClear();
      openSurfaceWindow.mockClear();
      vi.mocked(openSurfaceOr).mockClear();
      fireEvent.contextMenu(row(title));
      fireEvent.click(await screen.findByRole("menuitem", { name: "Open" }));
      await waitFor(() => expect(opened()).toContain(window));
    });
  }
});
