// PHILO-14 A5 — Needs you as a smart drawer (board A-5). The drawer reads the
// hub's one answer (`/api/desk/needs-you`) and draws each member as its
// object: icon by kind, name, one fact line, ONE lamp + word, its own verbs.
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../lib/api";
import { useAgentFlights, type AgentFlight } from "../../agentFlights";
import { openCoderSession } from "../../shell";
import { NeedsDrawer } from "../NeedsDrawer";

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

beforeEach(() => {
  gateCalls = [];
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
    expect(screen.getByTestId("needs-drawer-head").textContent).toBe("8 need you");
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
    expect(agent.sprite).toMatch(/automaton/);

    const held = face(row("Codex: reconciliation"));
    expect(held).toMatchObject({
      kind: "agent",
      fact: "psql -h staging-ledger -c 'select count(*) from entries'",
      lamps: ["HELD CALL"],
      verbs: ["Deny", "Approve"],
    });

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
    expect(worked.lamps).toEqual(["CLAUDE CODE · WORKING"]);
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
});
