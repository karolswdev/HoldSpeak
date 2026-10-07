// PHILO-14 A1 — the screen (board A-1, RATIFIED 2026-10-07): the Chair is the
// desk of objects. Composed from a fixture world: drawer counts and lamps,
// loose vs. filed objects, agents, selection, the open calls, the 393 grid,
// and ChairHome rendering it after arrival.
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../lib/api";
import { EMPTY_ITEMS } from "../../api";
import { useAgentFlights, fromWireSessionRow } from "../../agentFlights";
import { useChairWindows } from "../../chair/chairWindows";
import { useDesk } from "../../store";
import { composeScreen, layoutScreen, shortItemName, normalizeRef, type ScreenInputs } from "..";
import { Screen } from "../Screen";

const shell = vi.hoisted(() => ({
  openProjectRoom: vi.fn(),
  openSurfaceOr: vi.fn(),
  openCoderSession: vi.fn(),
}));
vi.mock("../../shell", async (original) => ({
  ...(await original<typeof import("../../shell")>()),
  openProjectRoom: shell.openProjectRoom,
  openSurfaceOr: shell.openSurfaceOr,
  openCoderSession: shell.openCoderSession,
}));
const openMeeting = vi.hoisted(() => vi.fn());
vi.mock("../../openObject", async (original) => {
  const real = await original<typeof import("../../openObject")>();
  return {
    ...real,
    refOpener: (ref: string) => (ref.startsWith("meeting:") ? () => openMeeting(ref) : real.refOpener(ref)),
  };
});
vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: vi.fn(),
}));

/* ── the fixture world ───────────────────────────────────────────────── */

const ITEMS = {
  ...EMPTY_ITEMS,
  project: [
    { kind: "project", id: "p-ledger", name: "Payments ledger cutover", description: "", keywords: [], teamMembers: [], meetingCount: 1, createdAt: "", updatedAt: "" },
    { kind: "project", id: "p-obs", name: "Platform observability", description: "", keywords: [], teamMembers: [], meetingCount: 0, createdAt: "", updatedAt: "" },
  ],
  meeting: [
    { kind: "meeting", id: "m-standup", title: "Ledger cutover sync" },
    { kind: "meeting", id: "m-vendor", title: "Vendor call" },
  ],
  note: [{ kind: "note", id: "n-2", title: "Questions for Avery 1:1" }],
  decision: [
    { kind: "decision", id: "d-freeze", title: "Freeze the old ledger on Nov 5" },
    { kind: "decision", id: "d-otel", title: "Adopt OpenTelemetry" },
  ],
  repository: [{ kind: "repository", id: "repo-ledger", name: "payments-ledger" }],
  thread: [{ kind: "thread", id: "t-1", title: "Idea: shard the reconciliation", tokenIn: 0, tokenOut: 0, createdAt: "" }],
} as never;

const RESOURCES: Record<string, string[]> = {
  "p-ledger": ["desk_decision:d-freeze", "people:p-jordan", "repository:repo-other"],
  "p-obs": [],
};
const MEETINGS: Record<string, string[]> = { "p-ledger": ["m-standup"], "p-obs": [] };
const PEOPLE = [
  { id: "p-jordan", display_name: "Jordan Patel" },
  { id: "p-avery", display_name: "Avery Chen" },
];
const NEEDS_ITEMS = [
  { id: "a1", projectId: "p-ledger", ref: "action:a1", title: "Write the rollback runbook", rankClass: "due_today" },
  { id: "a2", projectId: "p-ledger", ref: "action:a2", title: "Shard", rankClass: "due_today" },
  { id: "a3", projectId: "p-obs", ref: "action:a3", title: "Trace sampling", rankClass: "due_today" },
  { id: "m", projectId: "", ref: "meeting:m-vendor", title: "Vendor call", rankClass: "due_today" },
];

const SESSIONS = [
  {
    session: { agent: "claude", session_id: "c1", project_name: "payments-ledger", state: "waiting", awaiting_response: true, notification_type: "idle_prompt" },
    flight: { origin_ref: "action:a1", kind: "action", id: "a1", title: "Write the rollback runbook", agent: "claude", state: "waiting", session_key: "claude:c1" },
  },
  {
    session: { agent: "codex", session_id: "x1", project_name: "payments-ledger", state: "running" },
    flight: { origin_ref: "action:a2", kind: "action", id: "a2", title: "Shard the reconciliation job", agent: "codex", state: "working", session_key: "codex:x1" },
  },
];

function wire() {
  vi.mocked(apiFetch).mockImplementation(async (path: string) => {
    const p = String(path);
    const res = /^\/api\/projects\/([^/]+)\/resources$/.exec(p);
    if (res) return { resources: (RESOURCES[decodeURIComponent(res[1])] ?? []).map((resource_ref) => ({ resource_ref })) };
    const meet = /^\/api\/projects\/([^/]+)\/meetings$/.exec(p);
    if (meet) return { meetings: (MEETINGS[decodeURIComponent(meet[1])] ?? []).map((id) => ({ id })) };
    if (p === "/api/people/relationships") return { relationships: PEOPLE };
    if (p.startsWith("/api/desk/needs-you")) {
      return {
        count: NEEDS_ITEMS.length,
        members: NEEDS_ITEMS.map((i) => ({ ref: i.ref, kind: "attention" })),
        items: NEEDS_ITEMS,
        projectCounts: { "p-ledger": 2, "p-obs": 1 },
      };
    }
    return null;
  });
}

function setCompact(on: boolean) {
  window.matchMedia = ((query: string) => ({
    matches: on && query.includes("max-width: 720px"),
    media: query,
    onchange: null,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
    addListener: () => undefined,
    removeListener: () => undefined,
    dispatchEvent: () => false,
  })) as unknown as typeof window.matchMedia;
}
const realMatchMedia = window.matchMedia;

const icon = (name: RegExp) => screen.getByRole("button", { name });
const keys = () => [...document.querySelectorAll<HTMLElement>(".desk-screen [data-object-id]")].map((el) => el.dataset.objectId);

beforeEach(() => {
  setCompact(false);
  localStorage.clear();
  vi.mocked(apiFetch).mockReset();
  shell.openProjectRoom.mockReset();
  shell.openSurfaceOr.mockReset();
  shell.openCoderSession.mockReset();
  openMeeting.mockReset();
  useChairWindows.setState({ closed: { "chair:needs": true, "chair:brief": true, "chair:week": true, "chair:capture": true }, phone: "" });
  useDesk.setState({ items: ITEMS, updatedAt: 1 });
  useAgentFlights.setState({ sessions: SESSIONS.map(fromWireSessionRow), flights: [], loaded: true });
  wire();
});
afterEach(() => {
  window.matchMedia = realMatchMedia;
});

describe("PHILO-14 A1 — the screen of objects", () => {
  it("composes the drawers, the loose objects and the agents from the desk", async () => {
    render(<Screen />);
    await waitFor(() => expect(keys()).toContain("meeting:m-vendor"));
    // the drawers: every Project with its count notch and lamp, People, the Conductor
    const ledger = icon(/^Payments ledger cutover, PROJECT/);
    expect(ledger.getAttribute("aria-label")).toBe("Payments ledger cutover, PROJECT, 2 need you");
    expect(within(ledger).getByText("2", { selector: ".desk-icon-count" })).toBeTruthy();
    expect(ledger.querySelector(".desk-icon-lamp")?.getAttribute("data-tone")).toBe("ask");
    expect(icon(/^Platform observability, PROJECT, 1 need you/)).toBeTruthy();
    expect(icon(/^People, DRAWER$/).querySelector(".desk-icon-lamp")).toBeNull();
    const conductor = icon(/^Conductor, DRAWER/);
    expect(conductor.querySelector(".desk-icon-badge")).toBeTruthy();
    expect(conductor.querySelector(".desk-icon-lamp")?.getAttribute("data-tone")).toBe("ask");
    // Needs you: the desk's count; Parked: no lamp
    const needs = icon(/^Needs you, SMART DRAWER/);
    expect(within(needs).getByText("4", { selector: ".desk-icon-count" })).toBeTruthy();
    expect(icon(/^Parked, DRAWER$/).querySelector(".desk-icon-lamp")).toBeNull();
    // loose: what no Project holds; the filed meeting, decision and person are not on the screen
    expect(keys()).toEqual(expect.arrayContaining([
      "meeting:m-vendor", "note:n-2", "decision:d-otel", "repository:repo-ledger", "thread:t-1", "people:p-avery",
    ]));
    for (const filed of ["meeting:m-standup", "decision:d-freeze", "people:p-jordan"]) expect(keys()).not.toContain(filed);
    // a loose object Needs you lists wears a lamp
    expect(icon(/^Vendor call, MEETING, NEEDS YOU/).querySelector(".desk-icon-lamp")?.getAttribute("data-tone")).toBe("warn");
    // the agents: `<Agent>: <item short name>`, the lamp by state
    const asks = icon(/^Claude Code: rollback runbook, AGENT, ASKS/);
    expect(asks.querySelector(".desk-icon-lamp")?.getAttribute("data-tone")).toBe("ask");
    const works = icon(/^Codex: reconciliation job, AGENT, WORKS/);
    expect(works.querySelector(".desk-icon-lamp")?.getAttribute("data-tone")).toBe("info");
    // no chips on the screen: only lamps and count notches
    expect(document.querySelector(".desk-screen .state-chip, .desk-screen .surface-token")).toBeNull();
  });

  it("1440: the drawers down the left, Needs you top right, Parked bottom right, the field between", async () => {
    render(<Screen />);
    await waitFor(() => expect(keys()).toContain("meeting:m-vendor"));
    expect(screen.getByTestId("desk-screen").getAttribute("data-layout")).toBe("free");
    const at = (name: RegExp) => {
      const el = icon(name);
      return { x: parseFloat(el.style.left), y: parseFloat(el.style.top) };
    };
    expect(at(/^Payments ledger cutover/)).toEqual({ x: 20, y: 12 });
    expect(at(/^Platform observability/)).toEqual({ x: 20, y: 124 });
    expect(at(/^People/)).toEqual({ x: 20, y: 236 });
    expect(at(/^Conductor/)).toEqual({ x: 20, y: 348 });
    expect(at(/^Needs you/)).toEqual({ x: 1300, y: 12 });
    expect(at(/^Parked/)).toEqual({ x: 1300, y: 660 });
    expect(at(/^Claude Code: rollback runbook/)).toEqual({ x: 1170, y: 12 });
    expect(at(/^Vendor call/).x).toBe(210);
  });

  it("393: one 4-column grid in A-1-393's order, no positions", async () => {
    setCompact(true);
    render(<Screen />);
    await waitFor(() => expect(keys()).toContain("meeting:m-vendor"));
    expect(screen.getByTestId("desk-screen").getAttribute("data-layout")).toBe("grid");
    const order = keys();
    expect(order.slice(0, 6)).toEqual([
      "project:p-ledger", "project:p-obs", "drawer:people", "drawer:conductor", "drawer:needs", "drawer:parked",
    ]);
    expect(order.at(-1)).toBe("coder:codex:x1");
    for (const el of document.querySelectorAll<HTMLElement>(".desk-screen .desk-icon")) expect(el.style.left).toBe("");
  });

  it("a press selects, a press on empty glass clears, the rubber band selects many", async () => {
    render(<Screen />);
    await waitFor(() => expect(keys()).toContain("meeting:m-vendor"));
    fireEvent.click(icon(/^Vendor call/), { detail: 1 });
    expect(icon(/^Vendor call/).getAttribute("aria-pressed")).toBe("true");
    fireEvent.click(icon(/^Payments ledger cutover/), { detail: 1 });
    expect(icon(/^Vendor call/).getAttribute("aria-pressed")).toBe("false");
    expect(icon(/^Payments ledger cutover/).getAttribute("aria-pressed")).toBe("true");
    // jsdom has no PointerEvent: a MouseEvent carries button and clientX/Y.
    if (!("PointerEvent" in window)) Object.defineProperty(window, "PointerEvent", { value: MouseEvent, configurable: true });
    const grid = screen.getByRole("group", { name: "Desk" });
    fireEvent.pointerDown(grid, { button: 0, pointerId: 1 });
    expect(icon(/^Payments ledger cutover/).getAttribute("aria-pressed")).toBe("false");
    // the band meets the icons it covers (jsdom lays every icon at 0,0)
    fireEvent.pointerMove(grid, { pointerId: 1, clientX: 50, clientY: 50 });
    const pressed = document.querySelectorAll('.desk-screen .desk-icon[aria-pressed="true"]');
    expect(pressed.length).toBe(keys().length);
    fireEvent.pointerUp(grid, { pointerId: 1 });
  });

  it("Enter or a double press opens: the Room, Needs you, the Conductor, People, Parked, the object, the agent", async () => {
    render(<Screen />);
    await waitFor(() => expect(keys()).toContain("meeting:m-vendor"));
    fireEvent.keyDown(icon(/^Payments ledger cutover/), { key: "Enter" });
    expect(shell.openProjectRoom).toHaveBeenCalledWith("p-ledger");
    fireEvent.doubleClick(icon(/^Needs you/));
    expect(useChairWindows.getState().closed["chair:needs"]).toBe(false);
    fireEvent.keyDown(icon(/^Conductor/), { key: "Enter" });
    expect(shell.openSurfaceOr).toHaveBeenCalledWith("inspect-personas-and-coders", "/companion");
    fireEvent.keyDown(icon(/^People, DRAWER/), { key: "Enter" });
    expect(shell.openSurfaceOr).toHaveBeenCalledWith("open-people", "/");
    fireEvent.keyDown(icon(/^Parked/), { key: "Enter" });
    expect(shell.openSurfaceOr).toHaveBeenCalledWith("review-meetings", "/history");
    fireEvent.doubleClick(icon(/^Vendor call/));
    expect(openMeeting).toHaveBeenCalledWith("meeting:m-vendor");
    fireEvent.keyDown(icon(/^Avery Chen/), { key: "Enter" });
    expect(shell.openSurfaceOr).toHaveBeenCalledWith("open-people", "/", "people:p-avery");
    fireEvent.keyDown(icon(/^Claude Code: rollback runbook/), { key: "Enter" });
    expect(shell.openCoderSession).toHaveBeenCalledWith("claude:c1");
  });

  it("no Projects: the drawers that always exist stand; one line only when nothing else exists", async () => {
    useDesk.setState({ items: { ...EMPTY_ITEMS } as never });
    useAgentFlights.setState({ sessions: [], flights: [] });
    vi.mocked(apiFetch).mockImplementation(async () => null);
    render(<Screen />);
    await waitFor(() => expect(screen.getByTestId("desk-screen-empty")).toBeTruthy());
    expect(keys()).toEqual(["drawer:people", "drawer:conductor", "drawer:needs", "drawer:parked"]);
    // a loose note: the line goes
    act(() => useDesk.setState({ items: { ...EMPTY_ITEMS, note: [{ kind: "note", id: "n1", title: "A note" }] } as never, updatedAt: 2 }));
    await waitFor(() => expect(keys()).toContain("note:n1"));
    expect(screen.queryByTestId("desk-screen-empty")).toBeNull();
  });
});

describe("PHILO-14 A1 — the pure parts", () => {
  it("names the item short and normalizes a Project's ref names", () => {
    expect(shortItemName("Write the rollback runbook")).toBe("rollback runbook");
    expect(shortItemName("Add the ledger freeze flag")).toBe("ledger freeze flag");
    expect(shortItemName("Ship it")).toBe("Ship it");
    expect(normalizeRef("desk_decision:d1")).toBe("decision:d1");
    expect(normalizeRef("person:x")).toBe("people:x");
  });

  it("wraps the drawers into a second column and moves the field right", () => {
    const base: ScreenInputs = {
      items: { ...EMPTY_ITEMS, project: Array.from({ length: 9 }, (_, i) => ({ kind: "project", id: `p${i}`, name: `P${i}` })) } as never,
      projectCounts: {}, needsCount: 0, needsRefs: new Set(), heldCalls: 0, sessions: [], flights: [],
      filed: new Set(), persons: [{ id: "a", name: "A" }], membersLoaded: true,
    };
    const objects = composeScreen(base);
    const at = layoutScreen(objects, 1440, 796);
    expect(at["project:p6"]).toEqual({ x: 20, y: 684 });
    expect(at["project:p7"]).toEqual({ x: 140, y: 12 });
    expect(at["people:a"]).toEqual({ x: 330, y: 24 });
  });

  it("a held call lights the Conductor even when no agent asks", () => {
    const objects = composeScreen({
      items: { ...EMPTY_ITEMS } as never, projectCounts: {}, needsCount: 1, needsRefs: new Set(), heldCalls: 1,
      sessions: [], flights: [], filed: new Set(), persons: [], membersLoaded: true,
    });
    expect(objects.find((o) => o.key === "drawer:conductor")?.lamp?.tone).toBe("ask");
  });
});
