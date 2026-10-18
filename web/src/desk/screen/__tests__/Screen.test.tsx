// PHILO-14 A1 — the screen (board A-1, RATIFIED 2026-10-07): the Chair is the
// desk of objects. Composed from a fixture world: drawer counts and lamps,
// loose vs. filed objects, agents, selection, the open calls, the 393 grid,
// and ChairHome rendering it after arrival.
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../lib/api";
import { EMPTY_ITEMS, fromWireDirectory, fromWireNote, qualifiedRef, type Items } from "../../api";
import { useAgentFlights, fromWireSessionRow } from "../../agentFlights";
import { useChairWindows } from "../../chair/chairWindows";
import { useDrawers } from "../../drawer/store";
import { useDesk } from "../../store";
import { composeScreen, layoutScreen, screenIsBare, shortItemName, normalizeRef, type ScreenInputs } from "..";
import { Screen } from "../Screen";
import { rootDirectories } from "../compose";
import { resetScreenMembers } from "../members";
import { DeskIcon } from "../../surface";
import { verbById } from "../../verbRegistry";
import { dispatchKey, keyContext } from "../../keymap";
import { DeskMenuBar } from "../../components/DeskMenuBar";

const shell = vi.hoisted(() => ({
  openProjectRoom: vi.fn(),
  openSurfaceOr: vi.fn(),
  openCoderSession: vi.fn(),
  openPrimitive: vi.fn(),
}));
vi.mock("../../shell", async (original) => ({
  ...(await original<typeof import("../../shell")>()),
  openProjectRoom: shell.openProjectRoom,
  openSurfaceOr: shell.openSurfaceOr,
  openCoderSession: shell.openCoderSession,
  openPrimitive: shell.openPrimitive,
}));
const openMeeting = vi.hoisted(() => vi.fn());
const atmosphere = vi.hoisted(() => ({ ready: null as null | ((ready: boolean) => void) }));
vi.mock("../../gl/Atmosphere", () => ({
  Atmosphere: ({ id, onReadyChange }: { id: string; onReadyChange: (ready: boolean) => void }) => {
    atmosphere.ready = onReadyChange;
    return <div data-testid="live-atmosphere" data-atmosphere={id} />;
  },
}));
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
} as unknown as Items;

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
    if (p === "/api/people/readiness") return { state: "ready" };
    if (p === "/api/people/relationships") return { relationships: PEOPLE };
    if (p.startsWith("/api/desk/needs-you")) {
      return {
        count: NEEDS_ITEMS.length,
        members: NEEDS_ITEMS.map((i) => ({ ref: i.ref, kind: "attention" })),
        items: NEEDS_ITEMS,
        projectCounts: { "p-ledger": 2, "p-obs": 1 },
        // The Room's own counts (its head's "N open here"): one number.
        roomCounts: { "p-ledger": 2, "p-obs": 1 },
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

// Recorded GET /api/directories after root's isolated POST root/child and
// PUT member. Source: .tmp/desk-drawers-live/produced-directory-wire.json.
const folder = fromWireDirectory({ id: "dir_b5c056b59f3e", name: "Platform", name_normalized: "platform",
  parent_id: null, member_ids: ["note:note_0b9ebdadf0fa"], created_at: "2026-10-16T01:39:56Z" })!;
const childFolder = fromWireDirectory({ id: "dir_3e8aa70e9523", name: "Architecture", name_normalized: "architecture",
  parent_id: folder.id, member_ids: [], created_at: "2026-10-16T01:39:56Z" })!;
const filedNote = fromWireNote({ id: "note_0b9ebdadf0fa", title: "Rollback plan", body_markdown: "Keep the previous deployment ready.", tags: [],
  created_at: "2026-10-16T01:39:56Z", updated_at: "2026-10-16T01:39:56Z", last_modified: "2026-10-16T01:39:56Z", deleted: false })!;

const icon = (name: RegExp) => screen.getByRole("button", { name });
const keys = () => [...document.querySelectorAll<HTMLElement>(".desk-screen [data-object-id]")].map((el) => el.dataset.objectId);

beforeEach(() => {
  resetScreenMembers();
  useDrawers.setState({ drawers: [], parked: null });
  setCompact(false);
  localStorage.clear();
  vi.mocked(apiFetch).mockReset();
  shell.openProjectRoom.mockReset();
  shell.openSurfaceOr.mockReset();
  shell.openCoderSession.mockReset();
  atmosphere.ready = null;
  openMeeting.mockReset();
  useChairWindows.setState({ closed: { "chair:needs": true, "chair:brief": true, "chair:week": true, "chair:capture": true }, phone: "" });
  useDesk.setState({ items: ITEMS, updatedAt: 1, selectedIds: [], editingId: null });
  useAgentFlights.setState({ sessions: SESSIONS.map(fromWireSessionRow), flights: [], loaded: true });
  wire();
});
afterEach(() => {
  window.matchMedia = realMatchMedia;
});

describe("PHILO-14 A1 — the screen of objects", () => {
  it("renders real root drawers, recovers missing parents and opens the qualified directory", async () => {
    const orphan = { ...childFolder, id: "missing-parent-child", name: "Unfiled drawer", parentId: "missing-parent" };
    useDesk.setState({ items: { ...ITEMS, directory: [childFolder, folder, orphan], note: [...ITEMS.note, filedNote] } });
    const open = vi.spyOn(useDesk.getState(), "openPullout").mockImplementation(() => undefined);
    try {
      render(<><Screen /><DeskMenuBar /></>);
      await waitFor(() => expect(keys()).toContain("note:n-2"));
      expect(keys()).toContain(qualifiedRef("directory", folder.id));
      expect(keys()).toContain(qualifiedRef("directory", orphan.id));
      expect(keys()).not.toContain(qualifiedRef("directory", childFolder.id));
      expect(keys()).not.toContain(qualifiedRef("note", filedNote.id));
      expect(icon(/^Platform, DRAWER$/)).toBeTruthy();
      fireEvent.click(icon(/^Platform, DRAWER$/));
      expect(useDesk.getState().selectedIds).toEqual([qualifiedRef("directory", folder.id)]);
      // Betterment shell S0: the Object menu is titled by the kind in front.
      fireEvent.click(screen.getByRole("button", { name: /^Drawer$/ }));
      const objectMenu = screen.getByRole("menu", { name: "Drawer menu" });
      fireEvent.click(within(objectMenu).getByRole("menuitem", { name: /^Open/ }));
      expect(open).toHaveBeenCalledWith(qualifiedRef("directory", folder.id), undefined);
      open.mockClear();
      fireEvent.contextMenu(icon(/^Platform, DRAWER$/), { clientX: 100, clientY: 100 });
      const contextMenu = screen.getByRole("menu", { name: "Platform menu" });
      fireEvent.click(within(contextMenu).getByRole("menuitem", { name: /^Open/ }));
      expect(open).toHaveBeenCalledWith(qualifiedRef("directory", folder.id), undefined);
      open.mockClear();
      fireEvent.keyDown(icon(/^Platform, DRAWER$/), { key: "Enter" });
      expect(open).toHaveBeenCalledWith(qualifiedRef("directory", folder.id));
      expect(screen.queryByTestId("desk-screen-empty")).toBeNull();
    } finally {
      open.mockRestore();
    }
  });

  it("composes the drawers, the loose objects and the agents from the desk", async () => {
    render(<Screen />);
    await waitFor(() => expect(keys()).toContain("meeting:m-vendor"));
    // the drawers: every Project with its count notch and lamp, People, the Conductor
    const ledger = icon(/^Payments ledger cutover, PROJECT/);
    expect(ledger.getAttribute("aria-label")).toBe("Payments ledger cutover, PROJECT, 2 open here");
    expect(within(ledger).getByText("2", { selector: ".desk-icon-count" })).toBeTruthy();
    expect(ledger.querySelector(".desk-icon-lamp")?.getAttribute("data-tone")).toBe("ask");
    expect(icon(/^Platform observability, PROJECT, 1 open here/)).toBeTruthy();
    expect(icon(/^People, DRAWER$/).querySelector(".desk-icon-lamp")).toBeNull();
    const conductor = icon(/^Agents, DRAWER/);
    expect(conductor.querySelector(".desk-icon-badge")).toBeTruthy();
    expect(conductor.querySelector(".desk-icon-lamp")?.getAttribute("data-tone")).toBe("ask");
    // Needs you: one attention lamp; the desk keeps the count in the drawer
    // face rather than repeating it as an icon notch.
    const needs = icon(/^Needs you, SMART DRAWER/);
    expect(needs.querySelector(".desk-icon-count")).toBeNull();
    expect(needs.querySelector(".desk-icon-lamp")?.getAttribute("data-tone")).toBe("ask");
    expect(icon(/^Archive, DRAWER$/).querySelector(".desk-icon-lamp")).toBeNull();
    // loose: what no Project holds; the filed meeting, decision and person are not on the screen
    expect(keys()).toEqual(expect.arrayContaining([
      "meeting:m-vendor", "note:n-2", "decision:d-otel", "repository:repo-ledger", "people:p-avery",
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
      const el = icon(name).closest<HTMLElement>(".desk-screen-cell")!;
      return { x: parseFloat(el.style.left), y: parseFloat(el.style.top) };
    };
    expect(at(/^Payments ledger cutover/)).toEqual({ x: 20, y: 12 });
    expect(at(/^Platform observability/)).toEqual({ x: 20, y: 108 });
    expect(at(/^People/)).toEqual({ x: 20, y: 204 });
    expect(at(/^Agents/)).toEqual({ x: 20, y: 300 });
    expect(at(/^Needs you/)).toEqual({ x: 1300, y: 12 });
    expect(at(/^Archive/)).toEqual({ x: 1300, y: 660 });
    expect(at(/^Claude Code: rollback runbook/)).toEqual({ x: 1170, y: 12 });
    expect(at(/^Vendor call/).x).toBe(210);
  });

  it("393: one 4-column grid in A-1-393's order, no positions", async () => {
    setCompact(true);
    render(<Screen />);
    expect(screen.getByTestId("desk-screen").getAttribute("data-layout")).toBe("grid");
    // The phone face is the Go index; object placement is available from the
    // desktop face and is not duplicated below the menu.
    expect(keys()).toEqual([]);
    expect(screen.getByRole("menu", { name: "Go menu" })).toBeTruthy();
    for (const el of document.querySelectorAll<HTMLElement>(".desk-screen-cell")) expect(el.style.left).toBe("");
    // TALK lives in the Capture window at 393 (Speak opens it on demand)
    expect(screen.queryByTestId("desk-screen-talk")).toBeNull();
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
    // PHILO-17 U30: a Project opens its Room (one home), never a drawer.
    expect(shell.openProjectRoom).toHaveBeenCalledWith("p-ledger");
    expect(useDrawers.getState().drawers).toEqual([]);
    fireEvent.doubleClick(icon(/^Needs you/));
    expect(useChairWindows.getState().closed["chair:needs"]).toBe(false);
    fireEvent.keyDown(icon(/^Agents/), { key: "Enter" });
    expect(shell.openSurfaceOr).toHaveBeenCalledWith("open-conductor", "/conductor");
    fireEvent.keyDown(icon(/^People, DRAWER/), { key: "Enter" });
    expect(shell.openSurfaceOr).toHaveBeenCalledWith("open-people", "/");
    // PHILO-15 04 (gap 14): Parked opens the Parked drawer, not Meetings.
    fireEvent.keyDown(icon(/^Archive/), { key: "Enter" });
    expect(useDrawers.getState().parked).not.toBeNull();
    expect(shell.openSurfaceOr).not.toHaveBeenCalledWith("review-meetings", "/history");
    fireEvent.doubleClick(icon(/^Vendor call/));
    expect(openMeeting).toHaveBeenCalledWith("meeting:m-vendor");
    fireEvent.keyDown(icon(/^Avery Chen/), { key: "Enter" });
    // PHILO-17 (2b): a person icon opens THAT person, in their own window.
    expect(shell.openPrimitive).toHaveBeenCalledWith("people:p-avery");
    expect(shell.openSurfaceOr).not.toHaveBeenCalledWith("open-people", "/", "people:p-avery");
    fireEvent.keyDown(icon(/^Claude Code: rollback runbook/), { key: "Enter" });
    expect(shell.openCoderSession).toHaveBeenCalledWith("claude:c1");
  });

  it("Astra's P1: a failed membership read keeps a filed object off the screen; Retry rereads only it", async () => {
    let resourcesFail = true;
    const calls: string[] = [];
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      const p = String(path);
      calls.push(p);
      if (p === "/api/projects/p-ledger/resources") {
        if (resourcesFail) throw new Error("503 Service Unavailable");
        return { resources: [{ resource_ref: "desk_decision:d-freeze" }] };
      }
      if (/\/resources$/.test(p)) return { resources: [] };
      if (/\/meetings$/.test(p)) return { meetings: [] };
      if (p === "/api/people/readiness") return { state: "ready" };
      if (p === "/api/people/relationships") return { relationships: [] };
      return null;
    });
    render(<Screen />);
    await waitFor(() => expect(screen.getByTestId("desk-screen-notread-project:p-ledger")).toBeTruthy());
    const ledger = icon(/^Payments ledger cutover, PROJECT/);
    expect(ledger.getAttribute("aria-label")).toContain("NOT READ");
    expect(ledger.querySelector(".desk-icon-lamp")?.getAttribute("data-tone")).toBe("fail");
    // unknown stays unknown: the filed decision (and every loose object) is not drawn loose
    expect(keys()).not.toContain("decision:d-freeze");
    expect(keys().some((k) => k?.startsWith("note:") || k?.startsWith("meeting:"))).toBe(false);
    // Retry rereads exactly the failed read
    resourcesFail = false;
    const before = calls.length;
    fireEvent.click(screen.getByRole("button", { name: "Retry Payments ledger cutover" }));
    await waitFor(() => expect(screen.queryByTestId("desk-screen-notread-project:p-ledger")).toBeNull());
    expect(calls.slice(before)).toEqual(["/api/projects/p-ledger/resources"]);
    // the read answered: the filed decision stays filed, the loose ones return
    await waitFor(() => expect(keys()).toContain("decision:d-otel"));
    expect(keys()).not.toContain("decision:d-freeze");
  });

  it("Astra's P1: one read per Project, shared across faces and renders", async () => {
    const calls: string[] = [];
    const base = vi.mocked(apiFetch).getMockImplementation()!;
    vi.mocked(apiFetch).mockImplementation(async (path: string, ...rest: unknown[]) => {
      calls.push(String(path));
      return (base as (p: string, ...r: unknown[]) => Promise<unknown>)(path, ...rest);
    });
    const view = render(<><Screen /><Screen /></>);
    await waitFor(() => expect(document.querySelectorAll('[data-object-id="meeting:m-vendor"]').length).toBe(2));
    act(() => useDesk.setState({ updatedAt: 99 })); // a store refresh is not a reason to read again
    view.rerender(<><Screen /><Screen /></>);
    const reads = calls.filter((c) => /^\/api\/projects\/.+\/(resources|meetings)$/.test(c));
    expect(reads.sort()).toEqual([
      "/api/projects/p-ledger/meetings", "/api/projects/p-ledger/resources",
      "/api/projects/p-obs/meetings", "/api/projects/p-obs/resources",
    ]);
  });

  it("Astra's P1: a People read that fails wears NOT READ on People and draws no person", async () => {
    const base = vi.mocked(apiFetch).getMockImplementation()!;
    vi.mocked(apiFetch).mockImplementation(async (path: string, ...rest: unknown[]) => {
      if (String(path) === "/api/people/relationships") throw new Error("503");
      return (base as (p: string, ...r: unknown[]) => Promise<unknown>)(path, ...rest);
    });
    render(<Screen />);
    await waitFor(() => expect(screen.getByTestId("desk-screen-notread-drawer:people")).toBeTruthy());
    expect(keys().some((k) => k?.startsWith("people:"))).toBe(false);
  });

  it("keeps the chosen still until the live backdrop is ready; Quiet Desk has no atmosphere", async () => {
    localStorage.setItem("hs.desk.atmosphere", "night-train");
    const view = render(<Screen />);
    const desk = screen.getByTestId("desk-screen");
    expect(desk.getAttribute("data-place")).toBe("night-train");
    expect(desk.hasAttribute("data-place-still")).toBe(true);
    expect(desk.style.getPropertyValue("--desk-place-still")).toContain("night-train.webp");
    expect(screen.getByTestId("live-atmosphere").getAttribute("data-atmosphere")).toBe("night-train");
    act(() => atmosphere.ready?.(true));
    expect(desk.hasAttribute("data-place-still")).toBe(false);
    expect(desk.style.getPropertyValue("--desk-place-still")).toBe("");
    view.unmount();
    localStorage.setItem("hs.desk.atmosphere", "quiet-desk");
    render(<Screen />);
    expect(screen.getByTestId("desk-screen").hasAttribute("data-place-still")).toBe(false);
    expect(screen.queryByTestId("live-atmosphere")).toBeNull();
    localStorage.removeItem("hs.desk.atmosphere");
  });

  it("Astra's P3 (ruling): TALK is one press on the Chair at 1440", async () => {
    render(<Screen />);
    const talk = screen.getByTestId("desk-screen-talk");
    expect(within(talk).getByRole("button", { name: /talk/i })).toBeTruthy();
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
  it("resolves bare members to one canonical kind without hiding colliding drawers or decisions", () => {
    const directory = [
      { ...folder, memberIds: ["shared", "unknown-person"] },
      { ...childFolder, id: "shared", parentId: null, memberIds: [] },
    ];
    const items: Items = { ...EMPTY_ITEMS, directory, note: [{ ...filedNote, id: "shared" }],
      decision: [{ ...ITEMS.decision[0], id: "shared", title: "Different kind" }] };
    expect(rootDirectories(items).map((row) => row.id)).toEqual([folder.id, "shared"]);
    const objects = composeScreen({ items, projectCounts: {}, needsCount: 0, needsRefs: new Set(), heldCalls: 0, sessions: [], flights: [],
      filed: new Set(), persons: [{ id: "unknown-person", name: "Unresolved person" }], membersLoaded: true });
    expect(objects.map((row) => row.key)).toEqual(expect.arrayContaining(["zone:shared", "decision:shared", "people:unknown-person"]));
    expect(objects.map((row) => row.key)).not.toContain("note:shared");
  });

  it("keeps the original root reachable when filing it into its own child creates a parent cycle", () => {
    const childHoldingRoot = { ...childFolder, memberIds: [qualifiedRef("directory", folder.id)] };
    for (const directory of [[folder, childHoldingRoot], [childHoldingRoot, folder]]) {
      expect(rootDirectories({ ...EMPTY_ITEMS, directory }).map((row) => row.id)).toEqual([folder.id]);
    }
  });

  it("keeps one deterministic root for a membership-only cycle regardless of input order", () => {
    const parent = { ...folder, memberIds: [qualifiedRef("directory", childFolder.id)] };
    const child = { ...childFolder, parentId: null, memberIds: [`directory:${folder.id}`] };
    for (const directory of [[parent, child], [child, parent]]) {
      expect(rootDirectories({ ...EMPTY_ITEMS, directory }).map((row) => row.id)).toEqual([childFolder.id]);
    }
  });

  it("keeps a self-filed or self-parented drawer as a reachable root", () => {
    for (const parentId of [null, folder.id]) {
      const self = { ...folder, parentId, memberIds: [qualifiedRef("directory", folder.id)] };
      expect(rootDirectories({ ...EMPTY_ITEMS, directory: [self] }).map((row) => row.id)).toEqual([folder.id]);
    }
  });

  it("reaches folders filed by canonical or directory alias member refs through their parent", () => {
    const otherChild = { ...childFolder, id: "legacy-child", parentId: null };
    const base: ScreenInputs = {
      items: { ...EMPTY_ITEMS, directory: [{ ...folder, memberIds: [qualifiedRef("directory", childFolder.id), `directory:${otherChild.id}`] },
        { ...childFolder, parentId: null }, otherChild] },
      projectCounts: {}, needsCount: 0, needsRefs: new Set(), heldCalls: 0, sessions: [], flights: [],
      filed: new Set(), persons: [], membersLoaded: true,
    };
    expect(composeScreen(base).filter((o) => o.kind === "directory").map((o) => o.key)).toEqual([qualifiedRef("directory", folder.id)]);
  });

  it("keeps canonical and legacy directory members filed without hiding a different qualified kind", () => {
    const base: ScreenInputs = {
      items: { ...ITEMS, directory: [{ ...folder, memberIds: ["note:n-2", "desk_decision:d-otel", "m-vendor", "person:p-avery"] }],
        meeting: [{ kind: "meeting", id: "n-2", title: "Same id, different kind" }, { kind: "meeting", id: "m-vendor", title: "Vendor call" }] } as never,
      projectCounts: {}, needsCount: 0, needsRefs: new Set(), heldCalls: 0, sessions: [], flights: [],
      filed: new Set(), persons: [{ id: "p-avery", name: "Avery Chen" }], membersLoaded: true,
    };
    const objects = composeScreen(base);
    expect(objects.map((o) => o.key)).toContain("meeting:n-2");
    for (const ref of ["note:n-2", "decision:d-otel", "meeting:m-vendor", "people:p-avery"])
      expect(objects.map((o) => o.key)).not.toContain(ref);
    expect(objects.find((o) => o.key === qualifiedRef("directory", folder.id))?.target).toEqual({ type: "ref", ref: qualifiedRef("directory", folder.id) });
    expect(screenIsBare(composeScreen({ ...base, items: { ...EMPTY_ITEMS, directory: [folder] } }))).toBe(false);
  });

  it("names the item short and normalizes a Project's ref names", () => {
    expect(shortItemName("Write the rollback runbook")).toBe("rollback runbook");
    expect(shortItemName("Add the ledger freeze flag")).toBe("ledger freeze flag");
    expect(shortItemName("Ship it")).toBe("Ship it");
    expect(normalizeRef("desk_decision:d1")).toBe("decision:d1");
    expect(normalizeRef("person:x")).toBe("people:x");
    expect(normalizeRef("directory:x")).toBe(qualifiedRef("directory", "x"));
  });

  it("wraps the drawers into a second column and moves the field right", () => {
    const base: ScreenInputs = {
      items: { ...EMPTY_ITEMS, project: Array.from({ length: 9 }, (_, i) => ({ kind: "project", id: `p${i}`, name: `P${i}` })) } as never,
      projectCounts: {}, needsCount: 0, needsRefs: new Set(), heldCalls: 0, sessions: [], flights: [],
      filed: new Set(), persons: [{ id: "a", name: "A" }], membersLoaded: true,
    };
    const objects = composeScreen(base);
    const at = layoutScreen(objects, 1440, 796);
    // the column stops above TALK at the foot (Astra's P3 on #939)
    expect(at["project:p5"]).toEqual({ x: 20, y: 492 });
    expect(at["project:p6"]).toEqual({ x: 20, y: 588 });
    expect(at["project:p7"]).toEqual({ x: 140, y: 12 });
    expect(at["people:a"]).toEqual({ x: 330, y: 24 });
  });

  it("PHILO-17 phonepass: a captioned People drawer takes a taller row (the next drawer's notch never touches it)", () => {
    const base: ScreenInputs = {
      items: { ...EMPTY_ITEMS } as never,
      projectCounts: {}, needsCount: 0, needsRefs: new Set(), heldCalls: 0, sessions: [], flights: [],
      filed: new Set(), persons: [], membersLoaded: true,
    };
    const plain = layoutScreen(composeScreen(base), 1440, 796);
    const captioned = layoutScreen(composeScreen({ ...base, peopleCaption: "1:1 15:00" }), 1440, 796);
    expect(plain["drawer:conductor"].y - plain["drawer:people"].y).toBe(96);
    // Keep the extra 24 px caption allowance above the next count notch.
    expect(captioned["drawer:conductor"].y - captioned["drawer:people"].y).toBe(120);
  });

  it("the Conductor wears the count notch alone while its agents only work", () => {
    const working = fromWireSessionRow(SESSIONS[1]);
    const objects = composeScreen({
      items: { ...EMPTY_ITEMS } as never, projectCounts: {}, needsCount: 0, needsRefs: new Set(), heldCalls: 0,
      sessions: [working], flights: [{ ...working.flight!, state: "working" }], filed: new Set(), persons: [],
      membersLoaded: true,
    });
    const conductor = objects.find((o) => o.key === "drawer:conductor")!;
    expect(conductor.lamp).toBeUndefined();
    expect(conductor.count).toBe(1);
    render(<DeskIcon id="drawer:conductor" kind="conductor" name="Conductor" count={1} />);
    const drawn = screen.getByRole("button", { name: /^Conductor/ });
    expect(drawn.querySelector(".desk-icon-lamp")).toBeNull();
    expect(within(drawn).getByText("1", { selector: ".desk-icon-count" })).toBeTruthy();
  });

  it("a held call lights the Conductor even when no agent asks", () => {
    const objects = composeScreen({
      items: { ...EMPTY_ITEMS } as never, projectCounts: {}, needsCount: 1, needsRefs: new Set(), heldCalls: 1,
      sessions: [], flights: [], filed: new Set(), persons: [], membersLoaded: true,
    });
    expect(objects.find((o) => o.key === "drawer:conductor")?.lamp?.tone).toBe("ask");
  });
});

describe("PHILO-17 objverbs — the Chair has the desk's one selection", () => {
  it("a press on the Chair writes the store selection: the Object menu verbs are live, F2 renames", async () => {
    render(<Screen />);
    await waitFor(() => expect(keys()).toContain("note:n-2"));
    const rename = verbById("object.rename")!;
    // Nothing selected: the menu bar reads the store and ghosts the verb.
    expect(rename.ghost(keyContext())).toBe("Select an object");
    fireEvent.click(icon(/^Questions for Avery 1:1/));
    expect(useDesk.getState().selectedIds).toEqual(["note:n-2"]);
    expect(icon(/^Questions for Avery 1:1/).getAttribute("aria-pressed")).toBe("true");
    // The menu bar's context (DeskMenuBar) and the keymap's are the same read.
    expect(keyContext()).toEqual({ selectedRef: "note:n-2" });
    expect(rename.ghost(keyContext())).toBeNull();
    expect(verbById("object.open")!.ghost(keyContext())).toBeNull();
    // F2 runs Rename: the note's editor opens.
    const ran = dispatchKey(new KeyboardEvent("keydown", { key: "F2", bubbles: true, cancelable: true }));
    expect(ran?.id).toBe("object.rename");
    expect(useDesk.getState().editingId).toBe("n-2");
  });

  it("the rubber band and a press on empty glass write the store too", async () => {
    render(<Screen />);
    await waitFor(() => expect(keys()).toContain("note:n-2"));
    fireEvent.click(icon(/^Questions for Avery 1:1/));
    expect(useDesk.getState().selectedIds).toEqual(["note:n-2"]);
    act(() => useDesk.getState().setSelected(["decision:d-otel"]));
    expect(icon(/^Adopt OpenTelemetry/).getAttribute("aria-pressed")).toBe("true");
    expect(icon(/^Questions for Avery 1:1/).getAttribute("aria-pressed")).toBe("false");
  });

  it("a right-click on an icon selects it and opens the Floor's object menu", async () => {
    render(<Screen />);
    await waitFor(() => expect(keys()).toContain("note:n-2"));
    fireEvent.contextMenu(icon(/^Questions for Avery 1:1/), { clientX: 200, clientY: 200 });
    expect(useDesk.getState().selectedIds).toEqual(["note:n-2"]);
    const menu = await screen.findByRole("menu", { name: "Questions for Avery 1:1 menu" });
    const item = within(menu).getByRole("menuitem", { name: /^Rename/ });
    expect(item.getAttribute("aria-disabled")).not.toBe("true");
    fireEvent.click(item);
    expect(useDesk.getState().editingId).toBe("n-2");
  });

  it("a drawer with no desk object opens no menu", async () => {
    render(<Screen />);
    await waitFor(() => expect(keys()).toContain("note:n-2"));
    fireEvent.contextMenu(icon(/^Archive, DRAWER$/));
    expect(screen.queryByRole("menu")).toBeNull();
  });
});
