// HS-200-14 -- the PEOPLE section as a preparation face.
//
// AC1  an ambiguous owner is `OWNER · AMBIGUOUS · 2 MATCHES` with `Resolve`;
//      the candidates unfold under the row (no modal); a pick links the
//      alias through the ledger's own write; nothing is attributed on its own.
// AC2  a linked person's row carries commitments (DUE, source, `Open source`)
//      and facts with their Watch; nothing else.
// AC4  `People` on the head remembers the verb and opens PeopleCore scoped
//      to the Project; the return signal re-reads the section.
// AC5  a locked / not-set-up ledger is a typed partial with its repair verb;
//      a Project that names nobody draws nothing.
// Every verb is the library Button; no counters of zero.

import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
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

function rawButtons(): string[] {
  return Array.from(document.querySelectorAll("button"))
    .filter((b) => !b.className.includes("btn") && !b.className.includes("surface-ledger-line"))
    .map((b) => `${b.className} :: ${b.textContent}`);
}

beforeEach(() => { apiFetch.mockReset(); openSurfaceOr.mockReset(); openPrimitive.mockReset(); forgetTaskFocus(); });
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
    expect(ownerToken({ link: "ambiguous", candidates: [{ relationship_id: "a", display_name: "A" }, { relationship_id: "b", display_name: "B" }] })).toBe("OWNER · AMBIGUOUS · 2 MATCHES");
    expect(ownerToken({ link: "not_linked", candidates: [] })).toBe("OWNER · NOT LINKED");
    expect(ownerToken({ link: "locked", candidates: [] })).toBe("OWNER · LOCKED");
    expect(ownerToken({ link: "unconfigured", candidates: [] })).toBe("OWNER · NOT SET UP");
    expect(ownerToken({ link: "unavailable", candidates: [] })).toBe("OWNER · UNAVAILABLE");
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
    const token = await screen.findByText("OWNER · AMBIGUOUS · 2 MATCHES");
    expect(token).toBeTruthy();
    expect(screen.getByText("PEOPLE 1 OF 3")).toBeTruthy();
    expect(screen.getByTestId("room-people-gaps")).toHaveTextContent("1 AMBIGUOUS · 1 NOT LINKED");
    // Nothing attributed: the commitment sits under the OWNER row, not a person.
    const priyaRow = screen.getByText("Priya").closest("li")!;
    expect(within(priyaRow).getByText("Confirm the freeze window")).toBeTruthy();
    expect(screen.queryByText("Priya Sharma")).toBeNull();
    // Resolve unfolds the candidates under the row; no dialog anywhere.
    fireEvent.click(screen.getByRole("button", { name: "Resolve: Priya" }));
    const well = screen.getByTestId("room-people-resolve");
    expect(within(well).getByRole("button", { name: "Link: Priya Sharma" })).toBeTruthy();
    expect(within(well).getByRole("button", { name: "Link: Priya Nair" })).toBeTruthy();
    expect(document.querySelector("[role='dialog']")).toBeNull();
    // A pick links the alias through the ledger's own write, then re-reads.
    apiFetch.mockResolvedValueOnce({});
    apiFetch.mockResolvedValueOnce(prep({ expected: 3, resolved: 2, gaps: { ambiguous: 0, not_linked: 1, unreadable: 0 }, people: [
      { relationship_id: "rel-sharma", display_name: "Priya Sharma", link: "linked", commitments: [commitment], facts: [] },
    ], unresolved: [{ owner: "Zbigniew", link: "not_linked", commitments: [], candidates: [] }] }));
    fireEvent.click(within(well).getByRole("button", { name: "Link: Priya Sharma" }));
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith(
      "/api/people/relationships/rel-sharma/owner-aliases",
      expect.objectContaining({ method: "POST", json: { alias: "Priya" } }),
    ));
    expect(await screen.findByText("Priya Sharma")).toBeTruthy();
    expect(screen.getByText("PEOPLE 2 OF 3")).toBeTruthy();
    expect(rawButtons()).toEqual([]);
  });

  it("AC2: a linked person's row carries commitments with their source and facts with their Watch", async () => {
    apiFetch.mockResolvedValueOnce(ready());
    render(<RoomPeopleSection projectId="p1" />);
    const row = (await screen.findByText("Marek Kubiak")).closest("li")!;
    expect(within(row).getByText("1 OPEN COMMITMENT")).toBeTruthy();
    // The count is drawn ONCE, on the fact row that names its source.
    expect(within(row).getAllByText("2 PRS WAITING")).toHaveLength(1);
    const commitmentRow = within(row).getByTestId("room-people-commitment");
    expect(within(commitmentRow).getByText("Own the PostgreSQL migration")).toBeTruthy();
    /* HS-202-04 (F21) re-points this rig, which pinned the OLD token.
     * `MTG` and `SEG` were abbreviations no face defined
     * (`02-coherence-astra.md:133`); the line now says the words
     * (`RoomPeopleSection.tsx` sourceToken). The assertion still proves
     * the commitment carries its source — in plain words. */
    expect(within(commitmentRow).getByText("Meeting · Architecture review · Segment 4")).toBeTruthy();
    expect(within(commitmentRow).getByText(/^DUE /)).toBeTruthy();
    fireEvent.click(within(commitmentRow).getByRole("button", { name: "Open source: Architecture review" }));
    expect(openPrimitive).toHaveBeenCalledWith("meeting:m1");
    const fact = within(row).getByTestId("room-people-fact");
    expect(within(fact).getByText("karolswdev/HoldSpeak")).toBeTruthy();
    expect(within(fact).getByText("2 PRS WAITING")).toBeTruthy();
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
    expect(within(omitted).getByTestId("room-people-omitted-token")).toHaveTextContent("PAUSED · OMITTED");
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
    expect(await screen.findByText("PEOPLE 3")).toBeTruthy();
    await waitFor(() => expect(document.activeElement).toBe(screen.getByTestId("room-people-head-verb")));
  });

  it("AC5: a locked ledger is a typed partial with Unlock; not-set-up likewise; nobody named draws nothing", async () => {
    apiFetch.mockResolvedValueOnce(prep({ state: "locked", expected: 2, resolved: 0, gaps: { ambiguous: 0, not_linked: 0, unreadable: 2 }, unresolved: [
      { owner: "Priya", link: "locked", commitments: [commitment], candidates: [] },
      { owner: "Marek", link: "locked", commitments: [], candidates: [] },
    ] }));
    const first = render(<RoomPeopleSection projectId="p1" />);
    expect(await screen.findByText("PEOPLE 0 OF 2")).toBeTruthy();
    expect(screen.getByTestId("room-people-gaps")).toHaveTextContent("LOCKED");
    expect(screen.getAllByText("OWNER · LOCKED")).toHaveLength(2);
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
    expect(screen.getByText("OWNER · NOT SET UP")).toBeTruthy();
    expect(screen.queryByText("OWNER · LOCKED")).toBeNull();
    second.unmount();

    apiFetch.mockResolvedValueOnce(prep({ state: "unconfigured" }));
    const { container } = render(<RoomPeopleSection projectId="p1" />);
    await waitFor(() => expect(apiFetch).toHaveBeenCalledTimes(3));
    expect(container.innerHTML).toBe("");
  });

  it("AC5: an owner nobody answers for is NOT LINKED · Link, and Link with no candidate opens People", async () => {
    apiFetch.mockResolvedValueOnce(ready());
    render(<RoomPeopleSection projectId="p1" />);
    await screen.findByText("OWNER · NOT LINKED");
    const link = screen.getByRole("button", { name: "Link: Zbigniew" });
    fireEvent.click(link);
    expect(openSurfaceOr).toHaveBeenCalledWith("open-people", "/", "people:project:p1");
    expect(taskFocusPending()).toBe(true);
  });
});
