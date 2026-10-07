// PHILO-14 A5 — Needs you as a smart drawer (board A-5). The drawer reads the
// hub's one answer (`/api/desk/needs-you`) and draws each member as its
// object: icon by kind, name, one fact line, ONE lamp + word, its own verbs.
//
// Stable testids: `needs-drawer` (the body), `needs-row` (a member's row),
// `needs-source-row` (a source not read, no calendar), `needs-row-verb`
// (every row verb; `data-verb` names it: answer, open, deny, approve,
// open-pr, review, done, name-owner, set-date, confirm, defer, decline, door-verb,
// summarize, setup, repair, cancel, connect-calendar), `needs-well`,
// `needs-next` (the footer line), `needs-muted-toggle`, `needs-muted`.
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch } from "../../../lib/api";
import { useAgentFlights, type AgentFlight } from "../../agentFlights";
import { openCoderSession, openSurfaceOr } from "../../shell";
import { useDesk } from "../../store";
import { NeedsDrawer } from "../NeedsDrawer";
import { useArmingOutcome } from "../arming";

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
    title: "Add the ledger freeze flag", why: "DUE TODAY", severity: "warning",
    projectId: "p1", projectName: "Payments ledger", owner: null,
    _isDoor: true, _isUnassigned: false,
    _doorCard: { id: "ai-flag", target_ref: "action_item:ai-flag" },
  },
  {
    id: "door:ai-worked", ref: "ai-worked", kind: "action_item", source: "action_item",
    title: "Write the rollback runbook", why: "UNASSIGNED", severity: "warning",
    projectId: "p1", projectName: "Payments ledger", owner: null,
    _isDoor: true, _isUnassigned: true,
    _doorCard: { id: "ai-worked", target_ref: "action_item:ai-worked" },
  },
  {
    id: "decision:d-ops", ref: "decision:d-ops", kind: "decision", source: "decision",
    title: "Run a second ops interview", why: "TO REVIEW", severity: "warning",
    projectId: "p2", projectName: "Staff hiring loop", openRef: "decision:d-ops",
  },
  {
    id: "commitment:c-sam", ref: "commitment:c-sam", kind: "commitment", source: "commitment",
    title: "Sam: send the status by Thursday", why: "DUE TODAY", severity: "warning",
    projectId: "p3", projectName: "1:1", owner: "Sam Rivera", actionItemId: "ai-sam",
    nextAction: "mark_done",
  },
  {
    id: "door:ai-orphan", ref: "ai-orphan", kind: "action_item", source: "action_item",
    title: "Pick the vendor", why: "UNASSIGNED", severity: "warning",
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

let gateCalls: Array<{ path: string; json: unknown }> = [];
const REAL_CANCEL = useDesk.getState().cancelArmedSchedule;
let DOOR: Record<string, unknown> = { upcoming: [], calendar_configured: true };

beforeEach(() => {
  gateCalls = [];
  DOOR = { upcoming: [], calendar_configured: true };
  useDesk.setState({ scheduledArming: null, cancelArmedSchedule: REAL_CANCEL } as never);
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
    lamps: [...li.querySelectorAll(".gadget-lamp")].map((n) => n.textContent),
    verbs: [...li.querySelectorAll(".needs-row-verbs button")].map((b) => b.textContent),
    egress: li.querySelector(".needs-row-verbs .egress-chip, .needs-row-verbs [class*='egress']")?.textContent ?? "",
    sprite: li.querySelector("img")?.getAttribute("src") ?? "",
  };
}

async function mount() {
  render(<NeedsDrawer />);
  await screen.findByText("8 need you");
}

describe("NeedsDrawer (PHILO-14 A5, board A-5)", () => {
  it("heads with the hub's number, once, and nothing else", async () => {
    await mount();
    const drawer = screen.getByTestId("needs-drawer");
    expect(screen.getByTestId("arrival-display").textContent).toBe("8 need you");
    expect(drawer.querySelectorAll("h1, h2").length).toBe(1);
    expect(drawer.textContent).not.toMatch(/AVAILABLE|RANKED|CHECKED/);
  });

  it("draws every member as its object: icon, name, fact, one lamp, its verbs", async () => {
    await mount();
    const agent = face(row("Claude Code: rollback runbook"));
    expect(agent).toMatchObject({
      kind: "agent",
      fact: "The runbook needs a rollback owner. Jordan or Avery?",
      lamps: ["ASKS · 6 MIN"],
      verbs: ["Open", "Answer"],
    });
    // The D1 mold: each agent has its own sprite (agentSpriteName).
    expect(agent.sprite).toMatch(/agent-claude-code\.png$/);

    const held = face(row("Codex: reconciliation"));
    expect(held).toMatchObject({
      kind: "agent",
      fact: "psql -h staging-ledger -c 'select count(*) from entries'",
      lamps: ["HELD CALL"],
      verbs: ["Deny", "Approve"],
    });
    expect(face(row("Codex: reconciliation")).sprite).toMatch(/agent-codex\.png$/);

    const pr = face(row("#412 Add the ledger freeze flag"));
    expect(pr).toMatchObject({ kind: "pr", lamps: ["PR OPEN"], verbs: ["Open PR"] });
    expect(row("#412 Add the ledger freeze flag").textContent).toContain("GITHUB.COM");

    expect(face(row("Run a second ops interview"))).toMatchObject({
      kind: "decision", fact: "Staff hiring loop", lamps: ["TO REVIEW"], verbs: ["Review"],
    });
    expect(face(row("Sam: send the status by Thursday"))).toMatchObject({
      kind: "action", fact: "Sam Rivera · 1:1", lamps: ["DUE TODAY"], verbs: ["Done"],
    });
    expect(face(row("Vendor call"))).toMatchObject({
      kind: "meeting", fact: "20 min · summary failed", lamps: ["NO SUMMARY"], verbs: ["Summarize"],
    });
    expect(face(row("Pick the vendor"))).toMatchObject({
      kind: "action", lamps: ["UNASSIGNED"], verbs: ["Name an owner"],
    });
  });

  it("an item an agent works names the agent and never reads UNASSIGNED", async () => {
    await mount();
    const worked = face(row("Write the rollback runbook"));
    expect(worked.lamps).toEqual(["WORKING"]);
    expect(worked.fact).toBe("Claude Code · Payments ledger");
    expect(worked.verbs).toEqual(["Open"]);
    expect(row("Write the rollback runbook").textContent).not.toMatch(/UNASSIGNED|Name an owner/);
  });

  it("puts the agents first, then the rest in the hub's order", async () => {
    await mount();
    const names = [...document.querySelectorAll(".needs-row-name")].map((n) => n.textContent);
    expect(names.slice(0, 4)).toEqual([
      "Claude Code: rollback runbook",
      "Codex: reconciliation",
      "#412 Add the ledger freeze flag",
      "Write the rollback runbook",
    ]);
    expect(names.slice(4)).toEqual([
      "Run a second ops interview",
      "Sam: send the status by Thursday",
      "Pick the vendor",
      "Vendor call",
    ]);
  });

  it("draws no ⚠, no flight chip, no chip species, no Hand to agent", async () => {
    await mount();
    const drawer = screen.getByTestId("needs-drawer");
    expect(drawer.textContent).not.toContain("⚠");
    expect(drawer.querySelector("[data-testid='flight-chip']")).toBeNull();
    expect(drawer.querySelector(".state-chip, .signal-chip, [class*='StateChip'], [class*='state-chip']")).toBeNull();
    expect(screen.queryByText("Hand to agent")).toBeNull();
    // ONE filled primary on the face: the first row's Answer.
    expect(drawer.querySelectorAll(".btn--primary").length).toBe(1);
    expect(within(row("Claude Code: rollback runbook")).getByText("Answer").className).toContain("btn--primary");
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
    fireEvent.click(within(row("Claude Code: rollback runbook")).getByText("Open"));
    expect(openCoderSession).toHaveBeenLastCalledWith("claude:s-run");
  });

  it("Name an owner unfolds the owner well in place", async () => {
    await mount();
    fireEvent.click(within(row("Pick the vendor")).getByText("Name an owner"));
    expect(screen.getByTestId("needs-well")).toBeTruthy();
    expect(screen.getByRole("region", { name: "Owner: Pick the vendor" })).toBeTruthy();
  });

  it("393: every verb in a narrow drawer is a 44 px target (the rule is in the CSS)", () => {
    const here = dirname(fileURLToPath(import.meta.url));
    const css = readFileSync(resolve(here, "../needs.css"), "utf8");
    expect(css).toMatch(/@container surface \(max-width: 520px\)[\s\S]*\.needs-row-verbs \.btn \{\s*min-height: 44px;/);
  });

  it("says Nothing needs you only on a complete read", async () => {
    vi.mocked(apiFetch).mockImplementation(async () => ({ count: 0, items: [], coverage: [], complete: true }) as never);
    render(<NeedsDrawer />);
    await screen.findByText("Nothing needs you");
    expect(document.querySelectorAll(".needs-row").length).toBe(0);
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
      lamps: ["ASKS · 6 MIN"],
      verbs: ["Open", "Answer"],
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
    const rows = document.querySelectorAll<HTMLElement>("[data-testid='needs-row']");
    expect(rows[0].getAttribute("data-object-id")).toBe("arming:sch-1");
    expect(rows[0].getAttribute("data-kind")).toBe("meeting");
    const first = rows[0].querySelector(".gadget-lamp")?.textContent ?? "";
    expect(first).toMatch(/^ARMS · 0:0[78]$/);
    expect(face(rows[0]).verbs).toEqual(["Cancel", "Open"]);
    await waitFor(() => expect(rows[0].querySelector(".gadget-lamp")?.textContent).not.toBe(first), { timeout: 2500 });
    fireEvent.click(rows[0].querySelector("[data-verb='cancel']")!);
    expect(cancel).toHaveBeenCalledWith("sch-1");
  });

  it("NEXT is a quiet footer line; no calendar is an offer in the foot, never a row (PHILO-15-09 B11)", async () => {
    const at = new Date();
    at.setHours(14, 0, 0, 0);
    DOOR = { upcoming: [{ title: "Ledger cutover sync", starts_at: at.toISOString(), source: "calendar_event" }], calendar_configured: false };
    await mount();
    await waitFor(() => expect(screen.getByTestId("needs-next").textContent).toBe("NEXT · 14:00 · Ledger cutover sync"));
    const offer = await screen.findByTestId("needs-no-calendar");
    expect(offer.textContent).toContain("NO CALENDAR");
    expect(screen.queryByTestId("needs-source-row")).toBeNull();
    fireEvent.click(offer.querySelector("[data-verb='connect-calendar']")!);
    expect(openSurfaceOr).toHaveBeenCalledWith("configure-settings", "/settings", "meetings");
    // One count: the head says the number of rows under it.
    const rows = document.querySelectorAll("[data-testid='needs-list'] li.needs-row");
    expect(screen.getByTestId("arrival-display").textContent).toBe(`${rows.length} need you`);
    expect(rows.length).toBe(8);
  });

  it("muted rows are not drawn; Muted · N opens them", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (String(path).startsWith("/api/desk/needs-you"))
        return { ...ANSWER, items: [...ITEMS, { ...ITEMS[4], id: "decision:d-muted", ref: "decision:d-muted", openRef: "decision:d-muted", title: "A muted decision", muted: true }] } as never;
      return { upcoming: [], calendar_configured: true } as never;
    });
    await mount();
    expect(screen.queryByText("A muted decision")).toBeNull();
    const toggle = screen.getByTestId("needs-muted-toggle");
    expect(toggle.textContent).toBe("Muted · 1");
    fireEvent.click(toggle);
    expect(within(screen.getByTestId("needs-muted")).getByText("A muted decision")).toBeTruthy();
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
    expect(held.verbs).toEqual(["Deny", "Open"]);
    expect(screen.queryByRole("button", { name: /^Approve/ })).toBeNull();
    fireEvent.click(within(row("Codex: reconciliation")).getByText("Open"));
    expect(openCoderSession).toHaveBeenCalledWith("codex:s-recon");
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
      .toBe("NOT CANCELLED · the recording already started"));
    expect(armed()!.querySelector("[data-verb='retry']")?.textContent).toBe("Retry");
    refuse = false;
    fireEvent.click(armed()!.querySelector("[data-verb='retry']")!);
    await waitFor(() => expect(armed()!.querySelector("[data-verb='cancel']")).toBeTruthy());
    // The hub's event: the row goes, the receipt stays.
    act(() => useDesk.getState().applyScheduledRecordingEvent("scheduled_recording.cancelled", { schedule_id: "sch-9" }));
    expect(armed()).toBeNull();
    expect(screen.getByTestId("needs-receipt").textContent).toMatch(/^CANCELLED · Ledger cutover sync · \d\d:\d\d$/);
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
    expect(face(row("Write the rollback runbook")).lamps).toEqual(["ASKS · 6 MIN"]);
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
    expect(face(item)).toMatchObject({ lamps: ["HELD CALL"], verbs: ["Deny", "Approve"] });
    expect(within(item).getByTestId("needs-more-asks").textContent).toBe("+1 MORE");
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
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      const value = String(path);
      if (value.startsWith("/api/desk/needs-you")) {
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
      lamps: ["TO CONFIRM"],
      verbs: ["Decline", "Defer", "Confirm"],
    });
    // No glyph-only control: every verb carries its word.
    for (const button of action.querySelectorAll(".needs-row-verbs button")) {
      expect((button.textContent ?? "").trim()).toMatch(/^[A-Z][a-z]+$/);
    }
    expect(face(row("Use SQLite for the local meeting ledger")).verbs).toEqual(["Decline", "Defer", "Confirm"]);
    expect(action.getAttribute("data-opens")).toBe("true");

    fireEvent.click(within(action).getByRole("button", { name: "Confirm: Add the named failure fence before ship" }));
    await waitFor(() => expect(posted).toContain("/api/proposals/prop-priya/confirm"));
    fireEvent.click(within(row("Use SQLite for the local meeting ledger")).getByRole("button", { name: /^Defer:/ }));
    await waitFor(() => expect(posted).toContain("/api/proposals/prop-sqlite/defer"));
    fireEvent.click(within(row("Use SQLite for the local meeting ledger")).getByRole("button", { name: /^Decline:/ }));
    await waitFor(() => expect(posted).toContain("/api/proposals/prop-sqlite/dismiss"));
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
    const word = (title: string) =>
      rows.find((r) => r.textContent?.includes(title))?.querySelector("[data-testid='needs-row-kind']")?.textContent;
    expect(word("Run a second ops interview")).toBe("DECISION");
    expect(word("Pick the vendor")).toBe("ACTION");
    expect(word("Vendor call")).toBe("MEETING");
    expect(word("Jordan or Avery")).toBe("AGENT");
    for (const row of rows) expect(row.querySelector("[data-testid='needs-row-kind']")).not.toBeNull();
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
