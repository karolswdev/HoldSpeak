// HS-200-14 -- the PEOPLE section as a preparation face.
//
// AC1  an ambiguous owner is `Owner not clear · 2 matches` with `Resolve`;
//      the candidates unfold under the row (no modal); a pick links the
//      alias through the ledger's own write; nothing is attributed on its own.
// AC2  a linked person's row carries commitments (DUE, source, `Open source`)
//      and facts with their Watch; nothing else.
// AC4  `People` on the head remembers the verb and opens PeopleCore scoped
//      to the Project; the return signal re-reads the section.
// AC5  a locked / not-set-up ledger is a typed partial with its repair verb;
//      a Project that names nobody draws nothing.
// Every verb is the library Button; no counters of zero.

import { act, render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import { ApiError } from "../../../lib/api";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  RoomPeopleSection,
  peopleCaption,
  peopleGapTokens,
  ownerToken,
  headVerbLabel,
  factToken,
} from "../RoomPeopleSection";
import type { RoomPeoplePreparation } from "../api";

const apiFetch = vi.fn();
vi.mock("../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../lib/api")>("../../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});

const openPersonSpy = vi.fn();
vi.mock("../../../desk/openObject", async () => {
  const actual = await vi.importActual<typeof import("../../../desk/openObject")>("../../../desk/openObject");
  return { ...actual, openPerson: (...a: unknown[]) => openPersonSpy(...a) };
});

const openSurfaceOr = vi.fn();
const openPrimitive = vi.fn();
vi.mock("../../../desk/shell", async () => {
  const actual = await vi.importActual<typeof import("../../../desk/shell")>("../../../desk/shell");
  return { ...actual, openSurfaceOr: (...a: unknown[]) => openSurfaceOr(...a), openPrimitive: (...a: unknown[]) => openPrimitive(...a) };
});

import { announceTaskReturn, taskFocusPending, forgetTaskFocus } from "../../../desk/returnToTask";

function prep(over: Partial<RoomPeoplePreparation> = {}): RoomPeoplePreparation {
  return {
    state: "ready", expected: 0, resolved: 0,
    gaps: { ambiguous: 0, not_linked: 0, unreadable: 0 },
    people: [], unresolved: [], ...over,
  };
}

const commitment = {
  id: "c1", text: "Confirm the freeze window", due_at: "2099-01-01", owner: "Priya",
  source: { kind: "meeting" as const, meeting_id: "m1", label: "Architecture review", segment_index: 3 },
};

function ready(): RoomPeoplePreparation {
  return prep({
    expected: 3, resolved: 1,
    gaps: { ambiguous: 1, not_linked: 1, unreadable: 0 },
    people: [{
      relationship_id: "rel-marek", display_name: "Marek Kubiak", link: "linked", prs_waiting: 2,
      commitments: [{ ...commitment, id: "c2", text: "Own the PostgreSQL migration", owner: "marek" }],
      facts: [{ kind: "prs_waiting", count: 2, source: { kind: "watch", watch_id: "w1", connector_id: "gh", label: "karolswdev/HoldSpeak" } }],
    }],
    unresolved: [
      { owner: "Priya", link: "ambiguous", commitments: [commitment], candidates: [
        { relationship_id: "rel-sharma", display_name: "Priya Sharma" },
        { relationship_id: "rel-nair", display_name: "Priya Nair" },
      ] },
      { owner: "Zbigniew", link: "not_linked", commitments: [], candidates: [] },
    ],
  });
}

/** The owner-only People list the well reads (in memory only). */
function people() {
  return [
    { id: "rel-sharma", display_name: "Priya Sharma", relationship_kind: "peer", role_context: "Platform lead", owner_aliases: [] },
    { id: "rel-nair", display_name: "Priya Nair", relationship_kind: "direct_report", role_context: "Data lead", owner_aliases: [] },
    { id: "rel-other", display_name: "Someone Unrelated", relationship_kind: "peer", role_context: "", owner_aliases: [] },
  ];
}

function posts() {
  return apiFetch.mock.calls.filter(([, init]) => (init as { method?: string } | undefined)?.method === "POST");
}

function rawButtons(): string[] {
  return Array.from(document.querySelectorAll("button"))
    .filter((b) => !b.className.includes("btn") && !b.className.includes("surface-ledger-line"))
    .map((b) => `${b.className} :: ${b.textContent}`);
}

beforeEach(() => { apiFetch.mockReset(); openSurfaceOr.mockReset(); openPrimitive.mockReset(); openPersonSpy.mockReset(); forgetTaskFocus(); });
afterEach(() => { vi.restoreAllMocks(); });

describe("the pure token builders", () => {
  it("captions a typed partial and names the gaps once", () => {
    expect(peopleCaption({ expected: 3, resolved: 3 })).toBe("PEOPLE 3");
    expect(peopleCaption({ expected: 3, resolved: 2 })).toBe("PEOPLE 2 OF 3");
    expect(peopleCaption({ expected: 0, resolved: 0 })).toBe("PEOPLE");
    expect(peopleGapTokens({ state: "ready", gaps: { ambiguous: 1, not_linked: 2, unreadable: 0 } })).toEqual(["1 AMBIGUOUS", "2 NOT LINKED"]);
    expect(peopleGapTokens({ state: "ready", gaps: { ambiguous: 0, not_linked: 0, unreadable: 0 } })).toEqual([]);
    expect(peopleGapTokens({ state: "locked", gaps: { ambiguous: 0, not_linked: 0, unreadable: 2 } })).toEqual(["LOCKED"]);
    expect(peopleGapTokens({ state: "unconfigured", gaps: { ambiguous: 0, not_linked: 0, unreadable: 2 } })).toEqual(["NOT SET UP"]);
  });
  it("types the owner and the head verb", () => {
    expect(ownerToken({ link: "ambiguous", candidates: [{ relationship_id: "a", display_name: "A" }, { relationship_id: "b", display_name: "B" }] })).toBe("Owner not clear · 2 matches");
    expect(ownerToken({ link: "not_linked", candidates: [] })).toBe("Owner not linked");
    expect(ownerToken({ link: "locked", candidates: [] })).toBe("Owner locked");
    expect(ownerToken({ link: "unconfigured", candidates: [] })).toBe("Owner not set up");
    expect(ownerToken({ link: "unavailable", candidates: [] })).toBe("Owner not available");
    expect(headVerbLabel("ready")).toBe("People");
    expect(headVerbLabel("locked")).toBe("Unlock");
    expect(headVerbLabel("unconfigured")).toBe("Set up People");
    expect(factToken({ kind: "prs_waiting", count: 0, source: { kind: "watch", watch_id: "w", connector_id: "gh", label: "r" } })).toBeNull();
    expect(factToken({ kind: "assignments_overdue", count: 1, source: { kind: "watch", watch_id: "w", connector_id: "jira", label: "r" } })).toBe("1 ASSIGNMENT OVERDUE");
  });
});


function route(over: { list?: () => Promise<unknown>; post?: () => Promise<unknown>; room?: () => Promise<unknown> } = {}) {
  apiFetch.mockImplementation((url: string, init?: { method?: string }) => {
    if (url === "/api/people/relationships") return over.list ? over.list() : Promise.resolve({ relationships: people() });
    if (init?.method === "POST") return over.post ? over.post() : Promise.resolve({});
    return over.room ? over.room() : Promise.resolve(ready());
  });
}
async function openWell() {
  render(<RoomPeopleSection projectId="p1" />);
  fireEvent.click(await screen.findByRole("row", { name: /^Priya / }));
  await waitFor(() => expect(screen.getByRole("combobox", { name: "Person" }).querySelectorAll("option").length).toBeGreaterThan(1));
  return screen.getByRole("combobox", { name: "Person" });
}
function choosePerson(value = "rel-sharma") { fireEvent.change(screen.getByRole("combobox", { name: "Person" }), { target: { value } }); }
function press(label: string) { fireEvent.click(screen.getByRole("button", { name: label })); }

describe("People in the Room inspector", () => {
  it("selects an ambiguous owner without attributing or writing", async () => {
    route(); await openWell(); expect(posts()).toEqual([]); expect(screen.getByRole("button", { name: "Link" })).toBeDisabled();
  });
  it("keeps candidate role and kind in the roster and links only on the separate press", async () => {
    route(); const roster = await openWell();
    expect(roster).toHaveTextContent("Priya Sharma · Peer · Platform lead");
    choosePerson(); expect(posts()).toEqual([]);
    expect(screen.getByText('Every owner named "Priya", in all projects')).toBeInTheDocument();
    press("Link"); await waitFor(() => expect(posts()).toHaveLength(1));
    expect(posts()[0][0]).toBe("/api/people/relationships/rel-sharma/owner-aliases");
  });
  it("keeps commitments, their recorded source, and observable Watch facts in the selection", async () => {
    route(); render(<RoomPeopleSection projectId="p1" />); fireEvent.click(await screen.findByRole("row", { name: /^Marek Kubiak/ }));
    expect(screen.getByText(/Own the PostgreSQL migration/)).toBeInTheDocument();
    expect(screen.getByText(/2 PRs waiting/i)).toBeInTheDocument();
    press("Open source: Architecture review"); expect(openPrimitive).toHaveBeenCalledWith("meeting:m1");
  });
  it("names the paused source whose facts were omitted", async () => {
    const value = ready(); value.people[0].facts = []; value.people[0].omitted_sources = [{ kind: "watch", watch_id: "paused", connector_id: "github", label: "Paused repository", state: "paused" }];
    route({ room: async () => value }); render(<RoomPeopleSection projectId="p1" />); fireEvent.click(await screen.findByRole("row", { name: /^Marek Kubiak/ }));
    expect(screen.getByText("Paused repository")).toBeInTheDocument(); expect(screen.getByText("paused")).toBeInTheDocument();
  });
  it("Inspect, Cancel and Check write nothing", async () => {
    route(); await openWell(); choosePerson(); press("Inspect"); expect(openPersonSpy).toHaveBeenCalledWith("rel-sharma"); press("Check"); press("Cancel"); expect(posts()).toEqual([]);
  });
  it("keeps Link off when two candidates have the same current details", async () => {
    route({ list: async () => ({ relationships: people().map(row => ({ ...row, display_name: "Same name", relationship_kind: "peer", role_context: "Same role" })) }) });
    await openWell(); choosePerson(); expect(screen.getByRole("button", { name: "Link" })).toBeDisabled();
  });
  it("keeps Link off for a candidate missing from the current People read", async () => {
    route({ list: async () => ({ relationships: [] }) }); await openWell(); choosePerson(); expect(screen.getByRole("button", { name: "Link" })).toBeDisabled();
  });
  it("names a known alias conflict and changes nothing", async () => {
    route({ post: async () => { throw new ApiError(409, "taken", { detail: { code: "owner_alias_taken", holder_name: "Other person" } }); } });
    await openWell(); choosePerson(); press("Link"); expect(await screen.findByText(/Other person/)).toBeInTheDocument(); expect(posts()).toHaveLength(1);
  });
  it("treats a lost result as unknown and checks the saved alias before another Link", async () => {
    let linked = false;
    route({ post: async () => { linked = true; throw new ApiError(503, "lost", {}); }, list: async () => ({ relationships: people().map(row => row.id === "rel-sharma" && linked ? { ...row, owner_aliases: ["Priya"] } : row) }) });
    await openWell(); choosePerson(); press("Link"); await screen.findByText(/not known/); expect(screen.getByRole("button", { name: "Link" })).toBeDisabled();
    press("Check"); await screen.findByText(/is linked.*now/i); expect(posts()).toHaveLength(1);
  });
  it("keeps an acknowledged link when the following Room read fails", async () => {
    let reads = 0; route({ room: async () => { if (++reads > 1) throw new Error("offline"); return ready(); } });
    await openWell(); choosePerson(); press("Link"); expect(await screen.findByText(/Linked/)).toBeInTheDocument(); expect(posts()).toHaveLength(1);
  });
  it("clears private candidate context when the project changes", async () => {
    route(); const mounted = render(<RoomPeopleSection projectId="p1" />); fireEvent.click(await screen.findByRole("row", { name: /^Priya / }));
    await screen.findByRole("combobox", { name: "Person" }); mounted.rerender(<RoomPeopleSection projectId="p2" />);
    await waitFor(() => expect(screen.queryByRole("combobox", { name: "Person" })).toBeNull()); expect(posts()).toEqual([]);
  });
  it("opens People scoped to the project and rereads on return", async () => {
    route(); render(<RoomPeopleSection projectId="p1" />); await screen.findByRole("grid", { name: "People" }); press("People");
    expect(openSurfaceOr).toHaveBeenCalledWith("open-people", "/", "people:project:p1"); const before = apiFetch.mock.calls.length;
    act(() => announceTaskReturn()); await waitFor(() => expect(apiFetch.mock.calls.length).toBeGreaterThan(before)); expect(posts()).toEqual([]);
  });
});
