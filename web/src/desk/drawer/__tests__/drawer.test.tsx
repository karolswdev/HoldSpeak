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

function route(url: string): unknown {
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
  apiFetch.mockImplementation((url: string) => Promise.resolve(route(url)));
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
  await screen.findByRole("button", { name: /^Jordan Patel, PERSON/ });
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
    expect(facts).toHaveTextContent("3 NEED YOU");
    expect(facts).toHaveTextContent("TARGET NOV 5");
    expect(facts).toHaveTextContent("STATUS ON TRACK");
    expect(facts).toHaveTextContent(`${EXPECTED.length} OBJECTS`);
    fireEvent.click(screen.getByRole("button", { name: "Room" }), { detail: 1 });
    expect(shell.rooms).toEqual(["p-ledger"]);
  });

  it("icons wear their lamps: the agent asks, the item names its agent", async () => {
    await renderDrawer();
    expect(screen.getByRole("button", { name: "Write the rollback runbook, ACTION ITEM, CLAUDE CODE ASKS" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Claude Code: Write the rollback runbook, AGENT, ASKS" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "#412 Add the freeze flag, PULL REQUEST, OPEN" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add the freeze flag, ACTION ITEM, PR #412 OPEN" })).toBeInTheDocument();
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
    expect(footer()).toBe(`${EXPECTED.length} OBJECTS`);
    expect(footer()).not.toMatch(/0 SELECTED/);
    expect(screen.getByRole("button", { name: "Get Info" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: /^Ledger cutover sync, MEETING/ }), { detail: 1 });
    const row = document.querySelector('.object-list-row[data-object-id="meeting:m-standup"]')!;
    expect(row).toHaveAttribute("aria-selected", "true");
    expect(footer()).toBe(`${EXPECTED.length} OBJECTS · 1 SELECTED`);
  });

  it("Get Info opens the object's Info window; Open opens the object", async () => {
    await renderDrawer();
    fireEvent.click(screen.getByRole("button", { name: /^Ledger cutover sync, MEETING/ }), { detail: 1 });
    fireEvent.click(screen.getByRole("button", { name: "Get Info" }), { detail: 1 });
    expect(useDrawers.getState().infos.map((i) => i.ref)).toEqual(["meeting:m-standup"]);
    fireEvent.click(screen.getByRole("button", { name: "Open" }), { detail: 1 });
    expect(opened.refs).toEqual(["meeting:m-standup"]);
    // Enter on an icon opens it too.
    fireEvent.keyDown(screen.getByRole("button", { name: /^Jordan Patel, PERSON/ }), { key: "Enter" });
    expect(opened.refs).toEqual(["meeting:m-standup", "people:rel-j"]);
  });

  it("a pull request opens its page, and says where at the verb", async () => {
    const open = vi.spyOn(window, "open").mockReturnValue(null);
    await renderDrawer();
    fireEvent.click(screen.getByRole("button", { name: /^#412 Add the freeze flag/ }), { detail: 1 });
    expect(document.querySelector(".surface-footer-egress")).toHaveTextContent("GITHUB.COM");
    fireEvent.doubleClick(screen.getByRole("button", { name: /^#412 Add the freeze flag/ }));
    expect(open).toHaveBeenCalledWith("https://github.com/acme/ledger/pull/412", "_blank", "noopener");
  });

  it("a failed read is named, the drawer reads PARTIAL, and Retry re-runs only it", async () => {
    let peopleFails = true;
    apiFetch.mockImplementation((url: string) =>
      url.includes("/people") && peopleFails ? Promise.reject(new Error("locked")) : Promise.resolve(route(url)));
    render(<DrawerWindow drawer={{ projectId: "p-ledger", origin: null }} />);
    await screen.findByText(/PEOPLE ·/);
    expect(screen.getByTestId("drawer-facts")).toHaveTextContent("PEOPLE · NOT READ");
    expect(screen.getByTestId("drawer-partial")).toHaveTextContent("PARTIAL");
    expect(screen.queryByRole("button", { name: /^Jordan Patel/ })).toBeNull();
    const before = apiFetch.mock.calls.map(([u]) => String(u));
    peopleFails = false;
    fireEvent.click(screen.getByRole("button", { name: "Retry" }), { detail: 1 });
    await screen.findByRole("button", { name: /^Jordan Patel, PERSON/ });
    const retried = apiFetch.mock.calls.slice(before.length).map(([u]) => String(u));
    expect(retried.every((u) => u.includes("/people"))).toBe(true);
    expect(screen.queryByTestId("drawer-partial")).toBeNull();
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
    useDrawers.getState().setReceipt("p-ledger", { kind: "parked", text: "PARKED · Ledger cutover sync", ids: ["m-standup"] });
    const receipt = await screen.findByTestId("drawer-park-receipt");
    expect(receipt).toHaveTextContent("PARKED · Ledger cutover sync");
    fireEvent.click(within(receipt).getByRole("button", { name: "Restore" }), { detail: 1 });
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/api/meetings/m-standup/restore", { method: "POST" }));
    await waitFor(() => expect(screen.getByTestId("drawer-park-receipt")).toHaveTextContent("RESTORED"));
  });

  it("an empty drawer says so and counts nothing", async () => {
    apiFetch.mockImplementation((url: string) =>
      Promise.resolve(url.includes("/room") ? { ...ROOM, needsYou: { state: "ok", count: 0, items: [] }, decisions: { state: "ok", items: [] } } : url.startsWith("/api/coders") ? { sessions: [], flights: [] } : { meetings: [], decisions: [], artifacts: [], people: [], resources: [] }),
    );
    useDesk.setState({ items: EMPTY_ITEMS });
    render(<DrawerWindow drawer={{ projectId: "p-ledger", origin: null }} />);
    await screen.findByText("Nothing filed here");
    expect(screen.getByTestId("drawer-facts")).not.toHaveTextContent(/NEED YOU|OBJECT/);
    expect(footer()).toBe("");
  });

  it("a project ref and a calendar row open the drawer", () => {
    refOpener("project:p-ledger")!();
    calendarOpener({ project_id: "p-obs" })!();
    openDrawer("p-ledger");
    expect(useDrawers.getState().drawers.map((d) => d.projectId)).toEqual(["p-ledger", "p-obs"]);
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
    expect(record.state?.label).toMatch(/^CLAUDE CODE /);
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
    expect(drawerReceipt(1, 0)).toBe("1 OBJECT");
    expect(drawerReceipt(16, 1)).toBe("16 OBJECTS · 1 SELECTED");
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

describe("PHILO-14 A2 Get Info window", () => {
  it("shows the facts the object has and its own verbs", () => {
    render(<DrawerInfoWindow info={{ ref: "action:a1", projectId: "p", member: member({
      id: "action:a1", ref: "action:a1", kind: "action", name: "Write the rollback runbook", parks: false,
      facts: { where: "Payments ledger cutover", from: "Ledger cutover sync", owner: "Claude Code (agent)", state: { label: "CLAUDE CODE ASKS", tone: "ask" } },
    }) }} />);
    const info = document.querySelector(".object-info")!;
    expect(info).toHaveTextContent("Write the rollback runbook");
    expect(info).toHaveTextContent("ACTION ITEM");
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
    expect(useDrawers.getState().receipts.p).toEqual({ kind: "parked", text: "PARKED · Ledger cutover sync", ids: ["m1"] });
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
