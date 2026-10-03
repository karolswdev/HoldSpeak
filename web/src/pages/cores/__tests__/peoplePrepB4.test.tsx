/** PHILO-13-09 (B4-W): the 1:1 finds its person, on the People face.
 *
 * - the Next 1:1 side section reads as the header does (one formatter, no ISO);
 * - Prep shows the agenda, what the report owes from meetings (each row opens
 *   its meeting) and the report's projects; an empty section is withheld;
 * - a calendar suggestion links only on his press ("Link this 1:1"), through
 *   the existing calendar-links route; then NEXT 1:1 shows.
 */
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const opened: string[] = [];
vi.mock("../../../desk/openObject", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../../desk/openObject")>();
  return { ...actual, refOpener: (ref: string) => () => { opened.push(ref); } };
});

import { PeopleCore } from "../PeopleCore";

const ISO = /\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/;
const SOON = new Date(Date.now() + 25 * 3_600_000).toISOString();

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

type Call = { url: string; method: string; body?: string };
const calls: Call[] = [];

function stub(state: { linked: boolean; brief: Record<string, unknown> }) {
  vi.stubGlobal("fetch", vi.fn(async (input: string, opts?: { method?: string; body?: string }) => {
    const url = String(input);
    const method = opts?.method ?? "GET";
    calls.push({ url, method, body: opts?.body });
    if (url.startsWith("/api/people/readiness")) return json({ readiness: "ready", store: "encrypted" });
    if (url.startsWith("/api/people/relationships/r1/calendar-links") && method === "POST") {
      state.linked = true;
      return json({ relationship: { id: "r1" } });
    }
    if (url.startsWith("/api/people/relationships/r1/brief")) {
      return json({ brief: {
        relationship_id: "r1", display_name: "Priya Sharma", open_commitments: [], agenda_items: [],
        grounding_note_count: 0, linked_meetings: [], unlinked_meeting_count: 0,
        ...state.brief,
        ...(state.linked ? { calendar_link_suggestions: [], next_one_on_one: EVENT } : {}),
      } });
    }
    if (url.startsWith("/api/people/relationships/r1/one-on-ones")) return json({ one_on_ones: [] });
    if (url.startsWith("/api/people/relationships/r1")) {
      return json({ relationship: {
        id: "r1", display_name: "Priya Sharma", relationship_kind: "direct_report",
        calendar_links: state.linked ? [{ uid: EVENT.uid, source_id: EVENT.source_id, label: EVENT.title }] : [],
        next_one_on_one: state.linked ? EVENT.starts_at : null,
        owner_aliases: ["Priya"],
      } });
    }
    if (url.startsWith("/api/people/relationships")) return json({ relationships: [{ id: "r1", display_name: "Priya Sharma", relationship_kind: "direct_report" }] });
    if (url.startsWith("/api/door")) return json({ upcoming: [] });
    throw new Error(`Unexpected request: ${url}`);
  }));
}

const EVENT = {
  id: "ev1", uid: "uid-priya", title: "1:1 Priya / Karol", starts_at: SOON,
  ends_at: SOON, source_id: "work", source_label: "Work",
};

const FULL = {
  agenda_items: [{ id: "a1", body: "Review the dry-run report", visibility: "shared_intent", state: "open" }],
  open_meeting_actions: [{
    id: "act1", meeting_id: "m-1", task: "Send the dry-run report", owner: "Priya", due: null,
    delegated_at: null, meeting_title: "1:1 Priya / Karol", meeting_started_at: SOON,
  }],
  projects: [{ id: "p-dry", name: "Dry-run project" }],
};

afterEach(() => { vi.unstubAllGlobals(); calls.length = 0; opened.length = 0; });

describe("PHILO-13-09 B4-W: the 1:1 finds its person", () => {
  it("formats the Next 1:1 side section as the header does: no raw ISO", async () => {
    stub({ linked: true, brief: {} });
    render(<PeopleCore scope="people:r1" />);
    const header = await screen.findByTestId("people-next-1on1");
    const side = await screen.findByTestId("people-next-side");
    const label = header.textContent!.replace(/^NEXT 1:1\s*·\s*/, "");
    expect(label).toMatch(/^(TODAY|TOMORROW|[A-Z]{3}) /);
    expect(side.textContent).toContain(label);
    expect(document.body.textContent).not.toMatch(ISO);
  });

  it("Prep shows the agenda, what Priya owes (opens its meeting) and her projects", async () => {
    stub({ linked: true, brief: FULL });
    render(<PeopleCore scope="people:r1:prep" />);
    await screen.findByTestId("people-prep-lens");
    expect(within(await screen.findByTestId("prep-agenda")).getByText("Review the dry-run report")).toBeTruthy();
    const owed = await screen.findByTestId("prep-owed");
    expect(within(owed).getByText("Waiting on Priya")).toBeTruthy();
    fireEvent.click(within(owed).getByRole("button", { name: /Send the dry-run report/ }));
    expect(opened).toEqual(["meeting:m-1"]);
    const projects = screen.getByTestId("prep-projects");
    fireEvent.click(within(projects).getByRole("button", { name: /Dry-run project/ }));
    expect(opened).toEqual(["meeting:m-1", "project:p-dry"]);
    expect(document.body.textContent).not.toMatch(ISO);
  });

  it("withholds an empty section: no owed, no projects, no agenda heading", async () => {
    stub({ linked: true, brief: {} });
    render(<PeopleCore scope="people:r1:prep" />);
    await screen.findByTestId("people-prep-lens");
    expect(screen.queryByTestId("prep-owed")).toBeNull();
    expect(screen.queryByTestId("prep-projects")).toBeNull();
    expect(screen.queryByTestId("prep-agenda")).toBeNull();
    expect(screen.queryByTestId("prep-link-suggestion")).toBeNull();
  });

  it("a suggestion links only on his press; then NEXT 1:1 shows", async () => {
    stub({ linked: false, brief: { calendar_link_suggestions: [EVENT], next_one_on_one: null } });
    render(<PeopleCore scope="people:r1:prep" />);
    const suggestion = await screen.findByTestId("prep-link-suggestion");
    expect(within(suggestion).getByText("1:1 Priya / Karol")).toBeTruthy();
    expect(screen.queryByTestId("people-next-1on1")).toBeNull();
    expect(calls.some((c) => c.method === "POST")).toBe(false);
    fireEvent.click(within(suggestion).getByRole("button", { name: "Link this 1:1" }));
    const header = await screen.findByTestId("people-next-1on1");
    expect(header.textContent).toMatch(/^NEXT 1:1 · (TODAY|TOMORROW|[A-Z]{3}) /);
    const post = calls.find((c) => c.method === "POST")!;
    expect(post.url).toBe("/api/people/relationships/r1/calendar-links");
    expect(JSON.parse(post.body!)).toEqual({ uid: "uid-priya", source_id: "work", label: "1:1 Priya / Karol" });
    await waitFor(() => expect(screen.queryByTestId("prep-link-suggestion")).toBeNull());
  });

  it("the Now side offers the suggestion instead of a false 'No 1:1 planned'", async () => {
    stub({ linked: false, brief: { calendar_link_suggestions: [EVENT], next_one_on_one: null } });
    render(<PeopleCore scope="people:r1" />);
    const side = await screen.findByTestId("people-next-side");
    await waitFor(() => expect(within(side).getByRole("button", { name: "Link this 1:1" })).toBeTruthy());
    expect(side.textContent).not.toContain("No 1:1 planned");
  });
});
