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

describe("RoomPeopleSection (HS-200-14)", () => {
  it("AC1: an ambiguous owner is typed, resolvable in place, and never attributed", async () => {
    apiFetch.mockResolvedValueOnce(ready());
    render(<RoomPeopleSection projectId="p1" />);
    const token = await screen.findByText("Owner not clear · 2 matches");
    expect(token).toBeTruthy();
    expect(screen.getByText("People 1 of 3")).toBeTruthy();
    expect(screen.getByTestId("room-people-gaps")).toHaveTextContent("1 AMBIGUOUS · 1 NOT LINKED");
    // Nothing attributed: the commitment sits under the OWNER row, not a person.
    const priyaRow = screen.getByText("Priya").closest("li")!;
    expect(within(priyaRow).getByText("Confirm the freeze window")).toBeTruthy();
    expect(screen.queryByText("Priya Sharma")).toBeNull();
    // Resolve unfolds the candidates under the row; no dialog anywhere.
    // HS-S41: a candidate press selects; the write is the separate Link.
    let roomReads = 0;
    apiFetch.mockImplementation(async (url: string, init?: { method?: string }) => {
      if (url === "/api/people/relationships") return { relationships: people() };
      if (init?.method === "POST") return {};
      roomReads += 1;
      return prep({ expected: 3, resolved: 2, gaps: { ambiguous: 0, not_linked: 1, unreadable: 0 }, people: [
        { relationship_id: "rel-sharma", display_name: "Priya Sharma", link: "linked", commitments: [commitment], facts: [] },
      ], unresolved: [{ owner: "Zbigniew", link: "not_linked", commitments: [], candidates: [] }] });
    });
    fireEvent.click(screen.getByRole("button", { name: "Resolve: Priya" }));
    const well = screen.getByTestId("room-people-resolve");
    expect(await within(well).findByRole("button", { name: "Select: Priya Sharma · Peer · Platform lead" })).toBeTruthy();
    expect(within(well).getByRole("button", { name: "Select: Priya Nair · Direct report · Data lead" })).toBeTruthy();
    expect(document.querySelector("[role='dialog']")).toBeNull();
    fireEvent.click(within(well).getByRole("button", { name: "Select: Priya Sharma · Peer · Platform lead" }));
    expect(posts()).toHaveLength(0);
    fireEvent.click(within(well).getByTestId("room-people-link"));
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith(
      "/api/people/relationships/rel-sharma/owner-aliases",
      expect.objectContaining({ method: "POST", json: { alias: "Priya" } }),
    ));
    expect(await screen.findAllByText("Priya Sharma")).toBeTruthy();
    expect(screen.getByText("People 2 of 3")).toBeTruthy();
    expect(roomReads).toBe(1);
    expect(rawButtons()).toEqual([]);
  });

  it("AC2: a linked person's row carries commitments with their source and facts with their Watch", async () => {
    apiFetch.mockResolvedValueOnce(ready());
    render(<RoomPeopleSection projectId="p1" />);
    const row = (await screen.findByText("Marek Kubiak")).closest("li")!;
    expect(within(row).getByText("1 open commitment")).toBeTruthy();
    // The count is drawn ONCE, on the fact row that names its source.
    expect(within(row).getAllByText("2 PRs waiting")).toHaveLength(1);
    const commitmentRow = within(row).getByTestId("room-people-commitment");
    expect(within(commitmentRow).getByText("Own the PostgreSQL migration")).toBeTruthy();
    /* HS-202-04 (F21) re-points this rig, which pinned the OLD token.
     * `MTG` and `SEG` were abbreviations no face defined
     * (`02-coherence-astra.md:133`); the line now says the words
     * (`RoomPeopleSection.tsx` sourceToken). The assertion still proves
     * the commitment carries its source — in plain words. */
    expect(within(commitmentRow).getByText("Meeting · Architecture review · Segment 4")).toBeTruthy();
    expect(within(commitmentRow).getByText(/^Due /)).toBeTruthy();
    fireEvent.click(within(commitmentRow).getByRole("button", { name: "Open source: Architecture review" }));
    expect(openPrimitive).toHaveBeenCalledWith("meeting:m1");
    const fact = within(row).getByTestId("room-people-fact");
    expect(within(fact).getByText("karolswdev/HoldSpeak")).toBeTruthy();
    expect(within(fact).getByText("2 PRs waiting")).toBeTruthy();
    // No inferred field, no score, no zero.
    expect(row.textContent).not.toMatch(/\b0 /);
    expect(row.textContent).not.toMatch(/score|rank|sentiment/i);
  });

  it("AC2 (revoked source): a paused Watch's facts are omitted WITH its state, never silently", async () => {
    apiFetch.mockResolvedValueOnce(prep({ expected: 1, resolved: 1, people: [{
      relationship_id: "rel-marek", display_name: "Marek Kubiak", link: "linked", commitments: [], facts: [],
      omitted_sources: [{ kind: "watch", watch_id: "w9", connector_id: "gh", label: "karolswdev/HoldSpeak", state: "paused" }],
    }] }));
    render(<RoomPeopleSection projectId="p1" />);
    const row = (await screen.findByText("Marek Kubiak")).closest("li")!;
    const omitted = within(row).getByTestId("room-people-omitted");
    expect(within(omitted).getByText("karolswdev/HoldSpeak")).toBeTruthy();
    expect(within(omitted).getByTestId("room-people-omitted-token")).toHaveTextContent("Paused · Omitted");
    expect(within(row).queryByText(/PRS WAITING/)).toBeNull();
  });

  it("AC4: People remembers the verb, opens PeopleCore scoped to the Project, and the return re-reads", async () => {
    apiFetch.mockResolvedValueOnce(ready());
    render(<RoomPeopleSection projectId="p1" />);
    const verb = await screen.findByTestId("room-people-head-verb");
    expect(verb).toHaveTextContent("People");
    verb.focus();
    fireEvent.click(verb);
    expect(openSurfaceOr).toHaveBeenCalledWith("open-people", "/", "people:project:p1");
    expect(taskFocusPending()).toBe(true);
    // The way back: the one signal; the section re-reads and focus lands on the verb.
    (document.activeElement as HTMLElement | null)?.blur();
    apiFetch.mockResolvedValueOnce(prep({ expected: 3, resolved: 3, people: [
      { relationship_id: "rel-marek", display_name: "Marek Kubiak", link: "linked", commitments: [], facts: [] },
      { relationship_id: "rel-sharma", display_name: "Priya Sharma", link: "linked", commitments: [], facts: [] },
      { relationship_id: "rel-z", display_name: "Zbigniew Nowak", link: "linked", commitments: [], facts: [] },
    ] }));
    announceTaskReturn();
    expect(await screen.findByText("People 3")).toBeTruthy();
    await waitFor(() => expect(document.activeElement).toBe(screen.getByTestId("room-people-head-verb")));
  });

  it("AC5: a locked ledger is a typed partial with Unlock; not-set-up likewise; nobody named draws nothing", async () => {
    apiFetch.mockResolvedValueOnce(prep({ state: "locked", expected: 2, resolved: 0, gaps: { ambiguous: 0, not_linked: 0, unreadable: 2 }, unresolved: [
      { owner: "Priya", link: "locked", commitments: [commitment], candidates: [] },
      { owner: "Marek", link: "locked", commitments: [], candidates: [] },
    ] }));
    const first = render(<RoomPeopleSection projectId="p1" />);
    expect(await screen.findByText("People 0 of 2")).toBeTruthy();
    expect(screen.getByTestId("room-people-gaps")).toHaveTextContent("LOCKED");
    expect(screen.getAllByText("Owner locked")).toHaveLength(2);
    const unlock = screen.getByTestId("room-people-head-verb");
    expect(unlock).toHaveTextContent("Unlock");
    expect(unlock.className).toContain("btn--secondary");
    expect(screen.queryByTestId("room-people-resolve-verb")).toBeNull();
    fireEvent.click(unlock);
    expect(openSurfaceOr).toHaveBeenCalledWith("open-people", "/", "people:project:p1");
    expect(document.querySelectorAll(".btn--primary")).toHaveLength(0);
    first.unmount();

    apiFetch.mockResolvedValueOnce(prep({ state: "unconfigured", expected: 1, resolved: 0, gaps: { ambiguous: 0, not_linked: 0, unreadable: 1 }, unresolved: [
      { owner: "Priya", link: "unconfigured", commitments: [], candidates: [] },
    ] }));
    const second = render(<RoomPeopleSection projectId="p1" />);
    expect(await screen.findByText("Set up People")).toBeTruthy();
    expect(screen.getByTestId("room-people-gaps")).toHaveTextContent("NOT SET UP");
    // The row agrees with the head (counsel P2-ii): never LOCKED under NOT SET UP.
    expect(screen.getByText("Owner not set up")).toBeTruthy();
    expect(screen.queryByText("Owner locked")).toBeNull();
    second.unmount();

    apiFetch.mockResolvedValueOnce(prep({ state: "unconfigured" }));
    const { container } = render(<RoomPeopleSection projectId="p1" />);
    await waitFor(() => expect(apiFetch).toHaveBeenCalledTimes(3));
    expect(container.innerHTML).toBe("");
  });

  it("AC5: an owner nobody answers for is NOT LINKED · Link, and Link with no candidate opens People", async () => {
    apiFetch.mockResolvedValueOnce(ready());
    render(<RoomPeopleSection projectId="p1" />);
    await screen.findByText("Owner not linked");
    const link = screen.getByRole("button", { name: "Link: Zbigniew" });
    fireEvent.click(link);
    expect(openSurfaceOr).toHaveBeenCalledWith("open-people", "/", "people:project:p1");
    expect(taskFocusPending()).toBe(true);
  });
});

// HS-S41 (D16/G41 ruling 2026-11-07): an informed, separate, reusable-alias
// link. Select, Inspect, Cancel and Check never write; Link writes once.
describe("HS-S41: deliberate reusable alias resolution", () => {
  function route(over: {
    list?: () => Promise<unknown>;
    post?: () => Promise<unknown>;
    room?: () => Promise<unknown>;
  } = {}) {
    apiFetch.mockImplementation((url: string, init?: { method?: string }) => {
      if (url === "/api/people/relationships") return over.list ? over.list() : Promise.resolve({ relationships: people() });
      if (init?.method === "POST") return over.post ? over.post() : Promise.resolve({});
      return over.room ? over.room() : Promise.resolve(ready());
    });
  }

  async function openWell() {
    render(<RoomPeopleSection projectId="p1" />);
    fireEvent.click(await screen.findByRole("button", { name: "Resolve: Priya" }));
    const well = screen.getByTestId("room-people-resolve");
    await within(well).findByRole("button", { name: "Select: Priya Sharma · Peer · Platform lead" });
    return well;
  }

  it("selecting, inspecting, cancelling and checking write nothing; the scope is shown before Link", async () => {
    route();
    const well = await openWell();
    // Only the exact current candidates are joined; nobody else is drawn.
    expect(well.textContent).not.toContain("Someone Unrelated");
    expect(within(well).queryByTestId("room-people-link")).toBeNull();
    fireEvent.click(within(well).getByRole("button", { name: "Select: Priya Sharma · Peer · Platform lead" }));
    expect(within(well).getByTestId("room-people-confirm-scope")).toHaveTextContent(
      'Link the name "Priya" to Priya Sharma · Peer · Platform lead. Every owner named "Priya", in all projects, then goes to this person.',
    );
    fireEvent.click(within(well).getByTestId("room-people-inspect"));
    expect(openPersonSpy).toHaveBeenCalledWith("rel-sharma");
    expect(taskFocusPending()).toBe(false);
    fireEvent.click(within(well).getByTestId("room-people-check"));
    fireEvent.click(within(well).getByTestId("room-people-cancel"));
    expect(within(well).queryByTestId("room-people-confirm")).toBeNull();
    await waitFor(() => expect(apiFetch.mock.calls.filter(([u]) => u === "/api/people/relationships")).toHaveLength(2));
    expect(posts()).toHaveLength(0);
  });

  it("candidates with the same details keep Link off, also after Inspect", async () => {
    route({ list: async () => ({ relationships: [
      { id: "rel-sharma", display_name: "Priya", relationship_kind: "peer", role_context: "", owner_aliases: [] },
      { id: "rel-nair", display_name: "Priya", relationship_kind: "peer", role_context: "", owner_aliases: [] },
    ] }) });
    render(<RoomPeopleSection projectId="p1" />);
    fireEvent.click(await screen.findByRole("button", { name: "Resolve: Priya" }));
    const well = screen.getByTestId("room-people-resolve");
    const same = await within(well).findAllByRole("button", { name: "Select: Priya · Peer" });
    expect(same).toHaveLength(2);
    fireEvent.click(same[1]);
    expect(within(well).getByTestId("room-people-confirm-same")).toHaveTextContent("another match has the same details");
    expect(within(well).queryByTestId("room-people-link")).toBeNull();
    fireEvent.click(within(well).getByTestId("room-people-inspect"));
    expect(openPersonSpy).toHaveBeenCalledWith("rel-nair");
    expect(within(well).queryByTestId("room-people-link")).toBeNull();
    expect(posts()).toHaveLength(0);
  });

  it("a candidate missing from the current People list cannot be selected", async () => {
    route({ list: async () => ({ relationships: [people()[0]] }) });
    render(<RoomPeopleSection projectId="p1" />);
    fireEvent.click(await screen.findByRole("button", { name: "Resolve: Priya" }));
    const well = screen.getByTestId("room-people-resolve");
    await within(well).findByRole("button", { name: "Select: Priya Sharma · Peer · Platform lead" });
    expect(within(well).getByRole("button", { name: "Select: Priya Nair" })).toBeDisabled();
  });

  it("a known conflict names the holder from the structured answer and changes nothing", async () => {
    route({ post: async () => { throw new ApiError(409, "x", { detail: { code: "owner_alias_taken", holder_id: "rel-x", holder_name: "Priya Patel" } }); } });
    const well = await openWell();
    fireEvent.click(within(well).getByRole("button", { name: "Select: Priya Sharma · Peer · Platform lead" }));
    fireEvent.click(within(well).getByTestId("room-people-link"));
    const result = await screen.findByTestId("room-people-link-result");
    expect(result).toHaveAttribute("data-status", "conflict");
    expect(result).toHaveTextContent('"Priya" is already linked to Priya Patel. Nothing changed.');
    expect(posts()).toHaveLength(1);
  });

  it("a 503 is not known: Link stays off, nothing repeats, and Check finds the exact saved name", async () => {
    let aliases: string[] = [];
    route({
      post: async () => { aliases = ["Priya"]; throw new ApiError(503, "x", { detail: "people_store_unavailable" }); },
      list: async () => ({ relationships: people().map((p) => p.id === "rel-sharma" ? { ...p, owner_aliases: aliases } : p) }),
    });
    const well = await openWell();
    fireEvent.click(within(well).getByRole("button", { name: "Select: Priya Sharma · Peer · Platform lead" }));
    fireEvent.click(within(well).getByTestId("room-people-link"));
    const result = await screen.findByTestId("room-people-link-result");
    expect(result).toHaveAttribute("data-status", "uncertain");
    expect(result).toHaveTextContent('The link result for "Priya" is not known. Check before you try again.');
    expect(within(well).getByTestId("room-people-link")).toBeDisabled();
    fireEvent.click(within(well).getByTestId("room-people-check"));
    await waitFor(() => expect(screen.getByTestId("room-people-link-result")).toHaveAttribute("data-status", "current"));
    expect(screen.getByTestId("room-people-link-result")).toHaveTextContent('"Priya" is linked to Priya Sharma · Peer · Platform lead now.');
    expect(posts()).toHaveLength(1);
  });

  it("an acknowledged link stays acknowledged when the Room read after it fails", async () => {
    let roomReads = 0;
    route({ room: async () => { roomReads += 1; if (roomReads > 1) throw new Error("room down"); return ready(); } });
    const well = await openWell();
    fireEvent.click(within(well).getByRole("button", { name: "Select: Priya Sharma · Peer · Platform lead" }));
    await act(async () => { fireEvent.click(within(well).getByTestId("room-people-link")); });
    const result = await screen.findByTestId("room-people-link-result");
    await waitFor(() => expect(result).toHaveTextContent("Could not read the Room again."));
    expect(result).toHaveAttribute("data-status", "linked");
    expect(result).toHaveTextContent('Linked "Priya" to Priya Sharma · Peer · Platform lead.');
    expect(posts()).toHaveLength(1);
  });

  it("another project retires the well and its private context", async () => {
    route();
    const { rerender } = render(<RoomPeopleSection projectId="p1" />);
    fireEvent.click(await screen.findByRole("button", { name: "Resolve: Priya" }));
    await screen.findByRole("button", { name: "Select: Priya Sharma · Peer · Platform lead" });
    rerender(<RoomPeopleSection projectId="p2" />);
    await waitFor(() => expect(screen.queryByTestId("room-people-resolve")).toBeNull());
    expect(document.body.textContent).not.toContain("Platform lead");
  });
});
