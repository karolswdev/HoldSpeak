// PHILO-14 A2 (ratified boards A-2, A-2L, A-2 at 393): a Project opens as a
// drawer. The head is the Room's intelligence line; Icons | List is
// remembered per drawer; the list sorts by header; selection is the row;
// the footer never says a zero; Get Info and Open act on the selection.
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../../api";
import { useDesk } from "../../store";
import { useAgentFlights } from "../../agentFlights";
import { DrawerWindow, drawerReceipt } from "../DrawerWindow";
import { DrawerInfoWindow } from "../InfoWindow";
import { drawerHead, drawerMembers, type DrawerMember } from "../members";
import { openDrawer, useDrawers } from "../store";
import { memberOpens, openMember } from "../open";
import { refOpener, calendarOpener } from "../../openObject";
import { PreparePosture } from "../../../features/project-room/prepare/PreparePosture";
import { usePrepareController } from "../../../features/project-room/prepare/usePrepareController";
import { decodeBrief } from "../../../features/project-room/prepare/model";

const apiFetch = vi.fn();
vi.mock("../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../lib/api")>("../../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
vi.mock("../../../runtime/RuntimeBus", () => {
  const value = { state: "connected", lastFrame: null, subscribe: () => () => undefined };
  return { useRuntimeBus: () => value, useOptionalRuntimeBus: () => value, useRuntimeFrame: () => null };
});
const opened = vi.hoisted(() => ({ refs: [] as string[] }));
vi.mock("../../openObject", async () => {
  const actual = await vi.importActual<typeof import("../../openObject")>("../../openObject");
  return { ...actual, openRef: (ref: string) => opened.refs.push(ref) };
});
const shell = vi.hoisted(() => ({ rooms: [] as string[] }));
vi.mock("../../shell", async () => {
  const actual = await vi.importActual<typeof import("../../shell")>("../../shell");
  return { ...actual, openProjectRoom: (id: string) => shell.rooms.push(id) };
});

const NOW = new Date();
const today = NOW.toISOString();

const ROOM = {
  project_id: "p-ledger",
  revision: 1,
  observed_at: today,
  project: { id: "p-ledger", name: "Payments ledger cutover", is_archived: false, meeting_count: 1, created_at: today, updated_at: today, target_at: "2026-11-05", revision: 1 },
  items: { state: "ok", focus: [], totals_by_type: {}, total: 0 },
  meetings: { state: "ok", count: 1, latest: null },
  resources: { state: "ok", count: 1, latest: null },
  changes: { state: "ok", recent: [] },
  review: { state: "absent", reason: "not_yet_built" },
  needsYou: {
    state: "ok",
    count: 3,
    items: [
      { source: "meeting", kind: "action_item", title: "Write the rollback runbook", why: "OWNER · UNKNOWN", since: today, url: null, verb: "open", severity: "warning", action_item_id: "a1", meeting_id: "m-standup", owner: null },
      { source: "meeting", kind: "action_item", title: "Shard the reconciliation job", why: "OWNER · UNKNOWN", since: today, url: null, verb: "open", severity: "warning", action_item_id: "a2", meeting_id: "m-standup", owner: null },
      { source: "github", kind: "review", title: "#7 docs", why: "WAITING", since: today, url: "https://example.test/7", verb: "open", severity: "info" },
    ],
  },
  sources: { state: "ok", items: [], count: 0, nextCheckAt: null },
  health: { state: "ok", assessment: "on_track", reason: null, inputs: { overdue: 0, overdueMilestones: 0, ciFailing: false, reviewWaitingDays: null, targetPassed: false } },
  sinceRead: { state: "ok", readAt: null, groups: [] },
  // The Room's record of the meeting decision dec-1 (its source), worded differently:
  // one decision, by identity, never by text.
  decisions: { state: "ok", items: [{ id: "record-1", text: "Freeze the old ledger (Nov 5)", at: today, url: null, kind: "decision", source_type: "meeting", source_id: "dec-1" }] },
  commitments: { state: "ok", items: [] },
  target: { state: "ok", targetAt: "2026-11-05", daysLeft: 30, passed: false },
  updates: { state: "absent", reason: "x" },
  steward: { state: "absent", reason: "x" },
  receipts: { state: "ok", items: [] },
};

/** PHILO-15 16: the Project's repository as the hub answers it (a test sets it). */
const repo = vi.hoisted(() => ({
  state: null as null | Record<string, unknown>,
  posts: [] as unknown[],
}));

function route(url: string, init?: { method?: string; json?: unknown }): unknown {
  if (url.endsWith("/repository")) {
    if (init?.method === "POST") {
      repo.posts.push(init.json);
      const name = String((init.json as { repository?: string })?.repository ?? "");
      repo.state = { ...(repo.state ?? {}), repository: name, registered: true, cloned: false };
    }
    return repo.state ?? { project_id: "p-ledger", repository: null, registered: false, cloned: false, watched: [], host: "github.com" };
  }
  if (url.includes("/room")) return ROOM;
  if (url.includes("/meetings")) return { meetings: [{ id: "m-standup", title: "Ledger cutover sync", started_at: today }] };
  if (url.startsWith("/api/decisions")) return { decisions: [{ id: "dec-1", text: "Freeze the old ledger on Nov 5", source_meeting_id: "m-standup", created_at: today }] };
  if (url.includes("/artifacts")) return { artifacts: [{ id: "art-1", title: "Cutover requirements", meeting_id: "m-standup", created_at: today }] };
  if (url.includes("/people")) return { people: [{ relationship_id: "rel-j", display_name: "Jordan Patel" }] };
  if (url.includes("/resources")) return { resources: [{ resource_ref: "note:n-1", created_at: today }] };
  if (url.startsWith("/api/coders/sessions")) {
    return {
      sessions: [{ session: { agent: "claude", session_id: "s1", state: "waiting", updated_at: today }, flight: null }],
      flights: [
        { origin_ref: "action:a1", kind: "action", id: "a1", title: "Write the rollback runbook", project_id: "p-ledger", project_name: "Payments ledger cutover", agent: "claude", state: "waiting", session_key: "claude:s1", pr: null },
        { origin_ref: "action:a3", kind: "action", id: "a3", title: "Add the freeze flag", project_id: "p-ledger", project_name: "Payments ledger cutover", agent: "claude", state: "pr_open", session_key: null, pr: { number: 412, url: "https://github.com/acme/ledger/pull/412", state: "open" } },
      ],
    };
  }
  return {};
}

beforeEach(() => {
  localStorage.clear();
  opened.refs = [];
  shell.rooms = [];
  apiFetch.mockReset();
  apiFetch.mockImplementation((url: string, init?: { method?: string; json?: unknown }) => Promise.resolve(route(url, init)));
  repo.state = null;
  repo.posts = [];
  useAgentFlights.setState({ sessions: [], flights: [], loaded: false });
  useDrawers.setState({ drawers: [], infos: [], revision: 0, receipts: {} });
  useDesk.setState({
    items: { ...EMPTY_ITEMS, note: [{ kind: "note", id: "n-1", title: "Ledger cutover risks", createdAt: today } as never] },
    zoneViewPrefs: {},
    panelRects: {},
    panelOrder: [],
    panelMin: [],
  });
});
afterEach(() => vi.restoreAllMocks());

const EXPECTED = [
  "Ledger cutover sync",
  "Freeze the old ledger (Nov 5)",
  "Write the rollback runbook",
  "Shard the reconciliation job",
  "Add the freeze flag",
  "Cutover requirements",
  "Ledger cutover risks",
  "Jordan Patel",
  "Claude Code: Write the rollback runbook",
  "#412 Add the freeze flag",
];

async function renderDrawer() {
  const view = render(<DrawerWindow drawer={{ projectId: "p-ledger", origin: null }} />);
  // Under a loaded related run the first paint takes over the default 1 s.
  await screen.findByRole("button", { name: /^Jordan Patel, Person/ }, { timeout: 5000 });
  return view;
}

const footer = () => document.querySelector(".drawer-receipt")?.textContent ?? "";

describe("PHILO-14 A2 the drawer", () => {
  it("composes every object filed in the Project, once each", async () => {
    await renderDrawer();
    const names = [...document.querySelectorAll(".desk-icon-name")].map((n) => n.textContent);
    expect(names).toEqual(EXPECTED);
    // The meeting decision the Room's record already holds is not listed twice.
    expect(names.filter((n) => n.startsWith("Freeze the old ledger"))).toHaveLength(1);
    const ids = [...document.querySelectorAll(".desk-icon")].map((n) => n.getAttribute("data-object-id"));
    expect(ids).toContain("decision:dec-1"); // the `decisions` row its opener reads
    expect(ids).toContain("pr:acme/ledger#412"); // repository-qualified
  });

  it("the head is the Room's intelligence line", async () => {
    await renderDrawer();
    const facts = screen.getByTestId("drawer-facts");
    // W2-BUILDER (atlas 2026-10-27): dot + sentence-case word, no caps tokens.
    expect(facts).toHaveTextContent("3 need you");
    expect(facts).toHaveTextContent("Target Nov 5");
    expect(facts).toHaveTextContent("On track");
    expect(facts).toHaveTextContent(`${EXPECTED.length} objects`);
    expect(facts.textContent).not.toMatch(/NEED YOU|STATUS|OBJECTS/);
    fireEvent.click(screen.getByRole("button", { name: "Room" }), { detail: 1 });
    expect(shell.rooms).toEqual(["p-ledger"]);
  });

  it("icons wear their lamps: the agent asks, the item names its agent", async () => {
    await renderDrawer();
    expect(screen.getByRole("button", { name: "Write the rollback runbook, Action item, Claude Code asks" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Claude Code: Write the rollback runbook, Agent, ASKS" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "#412 Add the freeze flag, Pull request, OPEN" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add the freeze flag, Action item, PR #412 open" })).toBeInTheDocument();
  });

  it("Icons | List is remembered per drawer", async () => {
    const first = await renderDrawer();
    expect(document.querySelector(".desk-icon-grid")).not.toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "List" }), { detail: 1 });
    expect(useDesk.getState().zoneViewPrefs["project:p-ledger"]?.view).toBe("list");
    expect(screen.getByRole("grid", { name: "Payments ledger cutover" })).toBeInTheDocument();
    first.unmount();
    await renderDrawer();
    expect(document.querySelector(".desk-icon-grid")).toBeNull();
    expect(screen.getByRole("grid", { name: "Payments ledger cutover" })).toBeInTheDocument();
  });

  it("the list sorts by header", async () => {
    useDesk.getState().setZoneViewPref("project:p-ledger", { view: "list" });
    await renderDrawer();
    const grid = screen.getByRole("grid", { name: "Payments ledger cutover" });
    const rowNames = () =>
      [...grid.querySelectorAll(".object-list-name-word")].map((n) => n.textContent);
    expect(rowNames()).toEqual([...EXPECTED].sort((a, b) => a.localeCompare(b)));
    const kindHead = within(grid).getAllByRole("columnheader")[1];
    fireEvent.click(within(kindHead).getByRole("button"));
    expect(kindHead).toHaveAttribute("aria-sort", "ascending");
    expect(rowNames()[0]).toBe("Add the freeze flag"); // ACTION ITEM, then by name
    fireEvent.click(within(kindHead).getByRole("button"));
    expect(kindHead).toHaveAttribute("aria-sort", "descending");
    expect(rowNames()[0]).toBe("#412 Add the freeze flag"); // PULL REQUEST
  });

  it("selection is the row; the footer never says a zero", async () => {
    useDesk.getState().setZoneViewPref("project:p-ledger", { view: "list" });
    await renderDrawer();
    // W3-B: the foot holds the head facts in sentence case, the count among them.
    expect(footer()).toContain(`${EXPECTED.length} objects`);
    expect(footer()).not.toMatch(/selected/i);
    // PHILO-15 16: nothing selected, Get Info is the Project's own Info.
    expect(screen.getByRole("button", { name: "Get Info" })).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: /^Ledger cutover sync, Meeting/ }), { detail: 1 });
    const row = document.querySelector('.object-list-row[data-object-id="meeting:m-standup"]')!;
    expect(row).toHaveAttribute("aria-selected", "true");
    expect(footer()).toContain(`${EXPECTED.length} objects`);
    expect(footer()).toContain("1 selected");
  });

  it("Get Info opens the object's Info window; Open opens the object", async () => {
    await renderDrawer();
    fireEvent.click(screen.getByRole("button", { name: /^Ledger cutover sync, Meeting/ }), { detail: 1 });
    fireEvent.click(screen.getByRole("button", { name: "Get Info" }), { detail: 1 });
    expect(useDrawers.getState().infos.map((i) => i.ref)).toEqual(["meeting:m-standup"]);
    fireEvent.click(screen.getByRole("button", { name: "Open" }), { detail: 1 });
    expect(opened.refs).toEqual(["meeting:m-standup"]);
    // Enter on an icon opens it too.
    fireEvent.keyDown(screen.getByRole("button", { name: /^Jordan Patel, Person/ }), { key: "Enter" });
    expect(opened.refs).toEqual(["meeting:m-standup", "people:rel-j"]);
  });

  it("W6 (atlas pass 3): no dead foot; the verbs live in the toolbar; Open shows only for a selection", async () => {
    await renderDrawer();
    const toolbar = screen.getByTestId("drawer-filter");
    expect(within(toolbar).getByRole("button", { name: "Get Info" })).toBeTruthy();
    // Nothing selected: no Open at all (never a ghost).
    expect(screen.queryByRole("button", { name: "Open" })).toBeNull();
    // No foot of verbs: the status bar holds the facts only.
    expect(document.querySelector(".surface-footer-verbs")).toBeNull();
    const status = screen.getByTestId("drawer-status");
    expect(within(status).queryAllByRole("button")).toHaveLength(0);
    fireEvent.click(screen.getByRole("button", { name: /^Ledger cutover sync, Meeting/ }), { detail: 1 });
    expect(within(toolbar).getByRole("button", { name: "Open" })).toBeEnabled();
    // On a narrow window the quiet verbs fold into More: the menu holds them.
    fireEvent.click(within(toolbar).getByRole("button", { name: "More" }));
    const items = within(screen.getByRole("menu", { name: "More" })).getAllByRole("menuitem").map((i) => i.textContent?.trim());
    expect(items).toContain("Get Info");
    expect(items).toContain("History");
  });

  it("a pull request opens its page, and names where in the verb's hover title", async () => {
    const open = vi.spyOn(window, "open").mockReturnValue(null);
    await renderDrawer();
    fireEvent.click(screen.getByRole("button", { name: /^#412 Add the freeze flag/ }), { detail: 1 });
    // Owner ruling 2026-10-25: no host chip in the status bar; Open names
    // the address in its hover title.
    expect(document.querySelector(".gadget-chip-egress")).toBeNull();
    expect(screen.getByRole("button", { name: "Open" }).getAttribute("title")).toBe("https://github.com/acme/ledger/pull/412");
    fireEvent.doubleClick(screen.getByRole("button", { name: /^#412 Add the freeze flag/ }));
    expect(open).toHaveBeenCalledWith("https://github.com/acme/ledger/pull/412", "_blank", "noopener");
  });

  it("a failed read is named, the drawer reads PARTIAL, and Retry re-runs only it", async () => {
    let peopleFails = true;
    apiFetch.mockImplementation((url: string) =>
      url.includes("/people") && peopleFails ? Promise.reject(new Error("locked")) : Promise.resolve(route(url)));
    render(<DrawerWindow drawer={{ projectId: "p-ledger", origin: null }} />);
    await screen.findByText(/People not read/);
    expect(screen.getByTestId("drawer-facts")).toHaveTextContent("People not read");
    expect(screen.getByTestId("drawer-partial")).toHaveTextContent("Partial");
    expect(screen.queryByRole("button", { name: /^Jordan Patel/ })).toBeNull();
    const before = apiFetch.mock.calls.map(([u]) => String(u));
    peopleFails = false;
    fireEvent.click(screen.getByRole("button", { name: "Retry" }), { detail: 1 });
    await screen.findByRole("button", { name: /^Jordan Patel, Person/ });
    const retried = apiFetch.mock.calls.slice(before.length).map(([u]) => String(u));
    expect(retried.every((u) => u.includes("/people"))).toBe(true);
    expect(screen.queryByTestId("drawer-partial")).toBeNull();
  });

  it("A2b: a degraded decisions section is a failed read: NOT READ, PARTIAL, Retry, no second copy", async () => {
    let degraded = true;
    const recordFlight = { origin_ref: "decision_record:record-1", kind: "decision_record", id: "record-1", title: "Freeze the old ledger (Nov 5)",
      project_id: "p-ledger", project_name: "Payments ledger cutover", agent: "claude", state: "working", session_key: null, pr: null };
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room")) {
        return Promise.resolve(degraded ? { ...ROOM, decisions: { state: "degraded", error_code: "decisions_read_failed" } } : ROOM);
      }
      if (url.startsWith("/api/coders/sessions")) return Promise.resolve({ sessions: [], flights: [recordFlight] });
      return Promise.resolve(route(url));
    });
    await renderDrawer();
    await screen.findByText(/Decisions not read/);
    expect(screen.getByTestId("drawer-facts")).toHaveTextContent("Decisions not read");
    expect(screen.getByTestId("drawer-partial")).toHaveTextContent("Partial");
    expect(screen.getByTestId("drawer-facts")).not.toHaveTextContent("On track");
    // One decision (the lifecycle read), never a second copy from the flight.
    const refs = () => [...document.querySelectorAll(".drawer-window [data-object-id], [data-object-id]")]
      .map((e) => (e as HTMLElement).dataset.objectId ?? "");
    expect(refs().filter((r) => r.startsWith("decision"))).toEqual(["decision:dec-1"]);
    const rooms = () => apiFetch.mock.calls.filter(([u]) => String(u).includes("/room")).length;
    const before = rooms();
    degraded = false;
    fireEvent.click(screen.getByRole("button", { name: "Retry" }), { detail: 1 });
    await waitFor(() => expect(screen.queryByTestId("drawer-partial")).toBeNull());
    expect(rooms()).toBeGreaterThan(before);
    expect(screen.getByTestId("drawer-facts")).toHaveTextContent("On track");
    expect(refs().filter((r) => r.startsWith("decision"))).toEqual(["decision:dec-1"]);
  });

  it("A2b: a decision record opens in the Decisions window reader (the owner, 2026-10-25)", () => {
    const member: DrawerMember = { id: "decision_record:record-9", ref: "decision_record:record-9", kind: "decision", name: "X", facts: {} } as never;
    expect(memberOpens(member)).toBe(true);
    apiFetch.mockImplementation((url: string) => Promise.resolve(route(url)));
    openMember(member);
    // The reader reads its own record: no read in the press, no source window.
    expect(useDesk.getState().windowsById["surface-decisions"]?.scope).toBe("record:record-9");
    expect(apiFetch.mock.calls.some(([u]) => String(u).startsWith("/api/decision"))).toBe(false);
    expect(opened.refs).toEqual([]);
  });

  it("a Room commitment opens its action item's card; a decision-kind one stays a decision", () => {
    const members = drawerMembers({
      projectId: "p", projectName: "P", meetings: [], decisions: [], artifacts: [], people: [], resources: [],
      flights: [], sessions: [], items: EMPTY_ITEMS,
      room: { decisions: { state: "ok", items: [] }, needsYou: { state: "absent", reason: "x" },
        commitments: { state: "ok", items: [
          { id: "c1", text: "Send the plan", dueAt: null, owner: null, kind: "action", actionItemId: "ai-9" },
          { id: "c2", text: "Keep the old API", dueAt: null, owner: null, kind: "decision" },
        ] } } as never,
    });
    expect(members.map((m) => [m.ref, m.kind])).toEqual([["action:ai-9", "action"], ["commitment:c2", "decision"]]);
  });

  it("Park leaves its receipt on the drawer, with Restore", async () => {
    await renderDrawer();
    useDrawers.getState().setReceipt("p-ledger", { kind: "parked", text: "Parked Ledger cutover sync", ids: ["m-standup"] });
    const receipt = await screen.findByTestId("drawer-park-receipt");
    expect(receipt).toHaveTextContent("Parked Ledger cutover sync");
    fireEvent.click(within(receipt).getByRole("button", { name: "Restore" }), { detail: 1 });
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/api/meetings/m-standup/restore", { method: "POST" }));
    await waitFor(() => expect(screen.getByTestId("drawer-park-receipt")).toHaveTextContent("Restored at"));
  });

  it("an empty drawer says so and counts nothing", async () => {
    apiFetch.mockImplementation((url: string) =>
      Promise.resolve(url.includes("/room") ? { ...ROOM, needsYou: { state: "ok", count: 0, items: [] }, decisions: { state: "ok", items: [] } } : url.startsWith("/api/coders") ? { sessions: [], flights: [] } : { meetings: [], decisions: [], artifacts: [], people: [], resources: [] }),
    );
    useDesk.setState({ items: EMPTY_ITEMS });
    render(<DrawerWindow drawer={{ projectId: "p-ledger", origin: null }} />);
    const line = await screen.findByText("Nothing filed here");
    // DELIGHT slice 3: the empty drawer wears the Project's object.
    expect(line.closest('.surface-state[data-object="project"]')?.querySelector("img")).toBeTruthy();
    expect(screen.getByTestId("drawer-facts")).not.toHaveTextContent(/need you|object/i);
    // W3-B: the foot holds the head facts; it counts nothing and says no zero.
    expect(footer()).not.toMatch(/object|selected|\b0\b/i);
  });

  // PHILO-17 U30: a project ref and a calendar row open the Room (one home);
  // the drawer is parked as a project face and opens only by its own key.
  it("a project ref and a calendar row open the Room, never a drawer", () => {
    const before = shell.rooms.length;
    refOpener("project:p-ledger")!();
    calendarOpener({ project_id: "p-obs" })!();
    expect(shell.rooms.slice(before)).toEqual(["p-ledger", "p-obs"]);
    expect(useDrawers.getState().drawers).toEqual([]);
    openDrawer("p-ledger");
    expect(useDrawers.getState().drawers.map((d) => d.projectId)).toEqual(["p-ledger"]);
  });
});

describe("PHILO-14 A2 drawer members (pure)", () => {
  it("A2b: a flight on a decision record is its decision, with an Open and the agent's state", () => {
    const flight = {
      originRef: "decision_record:record-77", kind: "decision_record", id: "record-77", title: "Freeze the old ledger",
      projectId: "p", projectName: "P", agent: "claude", state: "working", sessionKey: null, pr: null,
      close: null, sessionCleanup: null, mergedAt: null, launchId: "l-1",
    };
    const room = { needsYou: { state: "absent", reason: "x" }, commitments: { state: "ok", items: [] },
      decisions: { state: "ok", items: [
        { id: "record-77", text: "Freeze the old ledger", at: "", url: null, kind: "decision", sourceType: "meeting", sourceId: "dec-9" },
      ] } };
    const members = drawerMembers({
      projectId: "p", projectName: "P", room: room as never, meetings: [], decisions: [], artifacts: [], people: [],
      resources: [], flights: [flight] as never, sessions: [], items: EMPTY_ITEMS,
    });
    // One object, named by the record's source (never the record's id).
    expect(members.map((m) => m.ref)).toEqual(["decision:dec-9"]);
    const record = members[0];
    expect(record.kind).toBe("decision");
    expect(record.state?.label).toMatch(/^Claude Code /);
    expect(memberOpens(record)).toBe(true);
    opened.refs.length = 0;
    openMember(record);
    expect(opened.refs).toEqual(["decision:dec-9"]);
  });

  it("head omits what the Room did not read", () => {
    expect(drawerHead(null)).toEqual({ needsYou: 0, target: null, targetPassed: false, status: null, statusTone: "ok" });
  });
  it("receipt never says a zero", () => {
    expect(drawerReceipt(0, 0)).toBe("");
    expect(drawerReceipt(1, 0)).toBe("1 object");
    expect(drawerReceipt(16, 1)).toBe("16 objects · 1 selected");
  });
  it("a filed ref the desk cannot name is left out, never shown as an id", () => {
    const members = drawerMembers({
      projectId: "p", projectName: "P", room: null, meetings: [], decisions: [], artifacts: [], people: [],
      resources: [{ resource_ref: "note:gone" }], flights: [], sessions: [], items: EMPTY_ITEMS,
    });
    expect(members).toEqual([]);
  });
});

function member(over: Partial<DrawerMember> = {}): DrawerMember {
  return {
    id: "meeting:m1", ref: "meeting:m1", kind: "meeting", name: "Ledger cutover sync",
    facts: { where: "Payments ledger cutover", made: "TODAY 08:40" }, parks: true, ...over,
  };
}

describe("PHILO-15 16 the Project knows its repository", () => {
  const REPO = "karolswdev/holdspeak-dayone-rehearsal-1558";

  it("Get Info with nothing selected: REPOSITORY · owner/name · Not cloned", async () => {
    repo.state = { project_id: "p-ledger", repository: REPO, registered: true, cloned: false, watched: [REPO], host: "github.com" };
    await renderDrawer();
    expect(screen.queryByTestId("drawer-register")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Get Info" }), { detail: 1 });
    const info = useDrawers.getState().infos[0];
    expect(info.ref).toBe("project:p-ledger");
    render(<DrawerInfoWindow info={info} />);
    const fact = await waitFor(() => {
      const el = document.querySelector('.object-info-fact[data-fact="repository"]');
      expect(el).toBeTruthy();
      return el!;
    });
    expect(within(fact as HTMLElement).getByText("Repository")).toBeTruthy();
    expect(within(fact as HTMLElement).getByText(`${REPO} · Not cloned`)).toBeTruthy();
  });

  it("Get Info pressed before the Room read landed names the Project once the desk knows it (test_windows_glass C5)", async () => {
    // The Room read is slow: the drawer's name is still the stand-in.
    apiFetch.mockImplementation((url: string, init?: { method?: string; json?: unknown }) =>
      url.includes("/room") ? new Promise(() => undefined) : Promise.resolve(route(url, init)));
    render(<DrawerWindow drawer={{ projectId: "p-ledger", origin: null }} />);
    fireEvent.click(screen.getByRole("button", { name: "Get Info" }), { detail: 1 });
    const info = useDrawers.getState().infos[0];
    expect(info.member.name).toBe("Project");
    render(<DrawerInfoWindow info={info} />);
    act(() => {
      useDesk.setState((s) => ({
        items: { ...s.items, project: [{ kind: "project", id: "p-ledger", name: "Payments ledger cutover" } as never] },
      }));
    });
    await waitFor(() =>
      expect(document.querySelector(".drawer-info-window")?.getAttribute("aria-label")).toBe("Info: Payments ledger cutover"),
    );
  });

  it("a store the hub cannot read is Not read with Retry, never NOT REGISTERED (Astra r1 on #1000)", async () => {
    repo.state = { project_id: "p-ledger", repository: null, registered: false, cloned: false, watched: [REPO], host: "github.com", store: "not_read" };
    await renderDrawer();
    expect(screen.queryByTestId("drawer-register")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Get Info" }), { detail: 1 });
    render(<DrawerInfoWindow info={useDrawers.getState().infos[0]} />);
    const fact = await waitFor(() => {
      const el = document.querySelector('.object-info-fact[data-fact="repository"] dd');
      expect(el?.textContent).toBe("Not read");
      return el!;
    });
    expect(fact).toBeTruthy();
    expect(screen.queryByTestId("info-register")).toBeNull();
    repo.state = { project_id: "p-ledger", repository: REPO, registered: true, cloned: false, watched: [REPO], host: "github.com", store: "read" };
    fireEvent.click(screen.getByTestId("info-repository-retry"));
    await waitFor(() =>
      expect(document.querySelector('.object-info-fact[data-fact="repository"] dd')?.textContent).toBe(`${REPO} · Not cloned`),
    );
  });

  it("CLONED once the first hand cloned it, and where the clone lives", async () => {
    const folder = `~/.holdspeak/repositories/${REPO}/holdspeak-dayone-rehearsal-1558`;
    repo.state = { project_id: "p-ledger", repository: REPO, registered: true, cloned: true, watched: [REPO], host: "github.com", folder };
    await renderDrawer();
    fireEvent.click(screen.getByRole("button", { name: "Get Info" }), { detail: 1 });
    render(<DrawerInfoWindow info={useDrawers.getState().infos[0]} />);
    expect(await screen.findByText(`${REPO} · Cloned`)).toBeTruthy();
    expect(document.querySelector('.object-info-fact[data-fact="folder"] dd')?.textContent).toBe(folder);
  });

  it("an older Project the Room watches a repository for: Register on the drawer, one press", async () => {
    repo.state = { project_id: "p-ledger", repository: null, registered: false, cloned: false, watched: [REPO], host: "github.com" };
    await renderDrawer();
    const register = await screen.findByTestId("drawer-register");
    expect(register).toHaveTextContent("Register");
    fireEvent.click(register);
    await waitFor(() => expect(repo.posts).toEqual([{ repository: REPO }]));
    await waitFor(() => expect(screen.queryByTestId("drawer-register")).toBeNull());
  });
});

describe("PHILO-14 A2 Get Info window", () => {
  it("shows the facts the object has and its own verbs", () => {
    render(<DrawerInfoWindow info={{ ref: "action:a1", projectId: "p", member: member({
      id: "action:a1", ref: "action:a1", kind: "action", name: "Write the rollback runbook", parks: false,
      facts: { where: "Payments ledger cutover", from: "Ledger cutover sync", owner: "Claude Code (coder)", state: { label: "CLAUDE CODE ASKS", tone: "ask" } },
    }) }} />);
    const info = document.querySelector(".object-info")!;
    expect(info).toHaveTextContent("Write the rollback runbook");
    expect(info).toHaveTextContent("Action item");
    for (const word of ["Where", "From", "Owner", "State"]) expect(within(info as HTMLElement).getByText(word)).toBeInTheDocument();
    expect(within(info as HTMLElement).queryByText("Due")).toBeNull(); // no "None" filler
    // No rename path and no park path for an action item: no such verbs.
    expect(screen.queryByRole("button", { name: "Rename" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Park" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Open" }), { detail: 1 });
    expect(opened.refs).toEqual(["action:a1"]);
  });

  it("Park is one press, no confirm: the meeting parks and the window closes", async () => {
    useDrawers.setState({ infos: [{ ref: "meeting:m1", projectId: "p", member: member() }] });
    useDesk.setState({ refresh: vi.fn(() => Promise.resolve()) } as never);
    render(<DrawerInfoWindow info={useDrawers.getState().infos[0]} />);
    fireEvent.click(screen.getByRole("button", { name: "Park" }), { detail: 1 });
    await waitFor(() => expect(useDrawers.getState().infos).toEqual([]));
    expect(apiFetch).toHaveBeenCalledWith("/api/meetings/m1", { method: "DELETE" });
    expect(useDrawers.getState().receipts.p).toEqual({ kind: "parked", text: "Parked Ledger cutover sync", ids: ["m1"] });
    expect(useDrawers.getState().revision).toBe(1);
  });

  it("Rename edits the name in place through the desk record's own path", async () => {
    const updatePrimitive = vi.fn(() => Promise.resolve());
    useDesk.setState({
      items: { ...EMPTY_ITEMS, meeting: [{ kind: "meeting", id: "m1", title: "Ledger cutover sync" } as never] },
      updatePrimitive,
    } as never);
    render(<DrawerInfoWindow info={{ ref: "meeting:m1", projectId: "p", member: member({ renameRef: "meeting:m1" }) }} />);
    fireEvent.click(screen.getByRole("button", { name: "Rename" }), { detail: 1 });
    const field = await screen.findByRole("textbox", { name: "Name" });
    fireEvent.change(field, { target: { value: "Cutover sync" } });
    await act(async () => {
      fireEvent.keyDown(field, { key: "Enter" });
    });
    expect(updatePrimitive).toHaveBeenCalledWith("meeting", "m1", { title: "Cutover sync" }, "RENAME");
  });
});

// Phase 16 (the interior kit; the canvas window "Payments ledger cutover"):
// AppHead → FilterBar (Icons | List + Room, History) → the IconGrid well →
// Sources · n + Steward → the AskWell → the Foot.
describe("Phase 16 the Room window on the interior kit", () => {
  it("the title bar is the title; the toolbar, then the canvas order (W3-B)", async () => {
    await renderDrawer();
    // W3-B (atlas 2026-10-27): no second name in the body; the head facts
    // are the foot's, as dots and words.
    expect(document.querySelectorAll(".kit-disp")).toHaveLength(0);
    expect(screen.getByTestId("drawer-facts")).toHaveTextContent("3 need you");
    const toolbar = screen.getByTestId("drawer-filter");
    expect(toolbar).toHaveAttribute("role", "toolbar");
    expect(within(toolbar).getByRole("button", { name: "Icons" })).toHaveAttribute("aria-pressed", "true");
    expect(within(toolbar).getByRole("button", { name: "List" })).toHaveAttribute("aria-pressed", "false");
    const order = [
      toolbar,
      document.querySelector(".desk-icon-grid[data-well]"),
      screen.getByTestId("drawer-sources"),
      screen.getByTestId("room-ask-well"),
    ];
    for (let i = 1; i < order.length; i += 1) {
      expect(order[i - 1]!.compareDocumentPosition(order[i]!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    }
    expect(screen.getByRole("textbox", { name: "Ask this project" })).toBeInTheDocument();
  });

  it("History and Steward open the Room at that place", async () => {
    const { takeRoomAtRequest } = await import("../../openObject");
    await renderDrawer();
    fireEvent.click(screen.getByTestId("drawer-history"), { detail: 1 });
    expect(shell.rooms).toEqual(["p-ledger"]);
    expect(takeRoomAtRequest("p-ledger")).toBe("history");
    fireEvent.click(screen.getByTestId("drawer-steward"), { detail: 1 });
    expect(takeRoomAtRequest("p-ledger")).toBe("steward");
    expect(takeRoomAtRequest("p-ledger")).toBeNull();
  });

  it("Sources: no count at zero; each accepted source is a glyph row with its one state word", async () => {
    await renderDrawer();
    expect(screen.getByTestId("drawer-sources").querySelector("h3")?.textContent).toBe("Sources");
    const { sourceRows } = await import("../DrawerWindow");
    const checked = new Date(Date.now() - 10 * 60_000).toISOString();
    const rows = sourceRows({
      sources: {
        state: "ok",
        count: 3,
        nextCheckAt: null,
        items: [
          { watchId: "w1", watchIds: ["w1"], provider: "github", scope: "karolswdev/payments-ledger", state: "live", checkedAt: checked, tokens: [], suggested: false },
          { watchId: "w2", watchIds: ["w2"], provider: "jira", scope: "OPS", state: "cant_check", checkedAt: null, tokens: [], suggested: false },
          { watchId: "w3", watchIds: ["w3"], provider: "github", scope: "acme/suggested", state: "live", checkedAt: null, tokens: [], suggested: true },
        ],
      },
    } as never);
    expect(rows.map((r) => [r.provider, r.scope, r.tone])).toEqual([
      ["github", "karolswdev/payments-ledger", "ok"],
      ["jira", "OPS", "fail"],
    ]);
    // W3-B: quiet sans words (`Checked 10 min ago`), never mono caps.
    expect(rows[0].meta).toBe("Checked 10 min ago");
    expect(rows[1].meta).toBe("Can't check");
  });
});

// The test diet (2026-10-11): the A2b paths glass, the drawer's two rows.
// replaces: tests/e2e/test_philo14_a2b_paths_glass.py::TestA2bPathsGlass::test_a_degraded_decisions_read_is_named_and_retried
//   -> "A2b: a degraded decisions section is a failed read: NOT READ, PARTIAL, Retry, no second copy" above
//      (its degraded section is the hub's own: ProjectService._room_section answers
//      {state: "degraded", error_code: "decisions_read_failed"}).
// replaces: tests/e2e/test_philo14_a2b_paths_glass.py::TestA2bPathsGlass::test_prepare_opens_a_decision_record_through_its_source
// The kept brief below is the real producer's answer (PreparationBriefService.prepare
// + keep, deterministic, on the a2 drawer glass seed), trimmed to the fields the face reads.
const RECORD_ID = "record-f67e10fe705c45ada9d1d7b603bc06d3";
const SOURCE_DECISION = "dec-eee0dbcac4e95493623b";
const KEPT_BRIEF = {
  id: "pbrief_c59a7565cfa4a99109c569f2", project_id: "p-ledger", project_revision: 0,
  purpose: "Ledger decision review", lifecycle: "kept", manifest_revision: 1,
  manifest: {
    calendar: { present: false }, commitments: [], coverage: { available: 0, complete: true, expected: 0 },
    decisions: [{ at: "2026-10-11T15:14:00.599633+00:00", kind: "decision", lifecycle: "current", meeting_title: "",
      ref: `decision_record:${RECORD_ID}`, text: "Freeze the old ledger on Nov 5" }],
    not_included: [], omitted: [], prepared_at: "2026-10-11T15:14:01.182859+00:00", project_id: "p-ledger",
    project_revision: 0, purpose: "Ledger decision review", sources: [],
  },
  manifest_sha256: "d2a5ae5b46a261c26c825325d350d7406a1ecf91790e7227ecfa80514dbf1a2a",
  integrity: "verified",
  outline: { obligations: [], priorities: [{ span_id: "s_priorities_0", text: "Freeze the old ledger on Nov 5" }], questions: [] },
  body_md: "## DECIDE TODAY\n- Freeze the old ledger on Nov 5",
  claims_json: JSON.stringify([{ acceptance: "accepted", kind: "decision", refs: [`decision_record:${RECORD_ID}`],
    section: "priorities", span_id: "s_priorities_0", support: "supported",
    support_record: { fields: ["decision_text", "lifecycle"], method: "field_mapping",
      source_refs: [`decision_record:${RECORD_ID}`], source_version: "project:p-ledger@0" },
    text: "Freeze the old ledger on Nov 5" }]),
  generator: "deterministic", generator_host: null, generator_model: null, elapsed_ms: 0,
  created_at: "2026-10-11T15:14:01.182859+00:00", updated_at: "2026-10-11T15:14:01.183190+00:00",
  kept_at: "2026-10-11T15:14:01.183190+00:00",
};

function PrepareHarness() {
  const ctrl = usePrepareController("p-ledger", () => undefined);
  return (
    <>
      <button type="button" onClick={() => void ctrl.openBrief(decodeBrief(KEPT_BRIEF))}>open the kept brief</button>
      <PreparePosture ctrl={ctrl} projectName="Payments ledger cutover" onOpenRef={(ref) => opened.refs.push(ref)} onResultChange={() => undefined} />
    </>
  );
}

describe("PHILO-14 A2b Prepare's DEC citation opens its record in the Decisions window", () => {
  it("Open source on a DEC claim opens the Decisions window on the record; never /api/decisions/record-", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url === `/api/briefs/${KEPT_BRIEF.id}`) return Promise.resolve({ brief: KEPT_BRIEF });
      if (url.startsWith("/api/projects/p-ledger/briefs")) return Promise.resolve(url.includes("/briefs?") ? { briefs: [KEPT_BRIEF] } : {});
      return Promise.resolve(route(url));
    });
    render(<PrepareHarness />);
    fireEvent.click(screen.getByText("open the kept brief"));
    const ref = await screen.findByTestId("prepare-claim-ref");
    expect(ref.textContent).toMatch(/^DEC/);
    fireEvent.click(screen.getByTestId("prepare-claim-open"));
    await waitFor(() => expect(useDesk.getState().windowsById["surface-decisions"]?.scope).toBe(`record:${RECORD_ID}`));
    const asked = apiFetch.mock.calls.map(([u]) => String(u));
    expect(asked.some((u) => u.startsWith("/api/decisions/"))).toBe(false);
    expect(asked).not.toContain(`/api/decisions/${SOURCE_DECISION}`);
    expect(opened.refs).not.toContain(`decision_record:${RECORD_ID}`);
  });
});
