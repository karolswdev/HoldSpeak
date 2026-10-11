/** People — the app's face facts that only the browser tests held (the test
 * diet, 2026-10-11).
 *
 * replaces: tests/e2e/test_hs172_people_glass.py::test_prep_at_1440
 * replaces: tests/e2e/test_hs172_people_glass.py::test_prep_at_393 (words; the 393 layout is the sweep's)
 * replaces: tests/e2e/test_hs172_people_glass.py::test_now_wing_from_prep
 * replaces: tests/e2e/test_hs172_people_glass.py::test_now_wing_at_393 (words; the 393 layout is the sweep's)
 * replaces: tests/e2e/test_philo17_meeting_window_glass.py::TestOneMeetingOneWindow::test_a_person_icon_opens_the_person (the window body;
 *   the hub window `pullout:people:<id>` is tests/integration/test_desk_chair.py)
 *
 * The rest of those walks is already fenced in
 * web/src/pages/cores/__tests__/peoplePrepEnrichment.test.tsx (name, PRS
 * WAITING ON ANIA, ASSIGNMENT row, THIS DEVICE, PREPARED receipt, pronouns,
 * Open → Now with the Now tab selected). This file adds what only the glass
 * asserted: no raw <button> in the Prep card, no zero counter in the summary,
 * and one Open per PR on the Now side.
 *
 * The brief's watch_summary is the shape PeopleService._brief_watch_summary
 * writes (holdspeak/services/people_service.py: title, repo, pr_number,
 * days_waiting, url, room_id, room_name; summary, key, status, url, overdue,
 * room_id, room_name), from the glass seed: two open PRs that ask ania-k
 * for review (5 and 2 days old), one Jira issue assigned to ania-k.
 * tests/unit/test_hs172_people_sources.py::TestBriefEnrichment proves the
 * producer writes it from the persisted watch snapshots.
 */
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PeopleCore, PersonWindowBody } from "../../pages/cores/PeopleCore";

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

const WATCH_SUMMARY = {
  prs_waiting: [
    { title: "Fix migration", repo: "karolswdev/holdspeak", pr_number: 612, days_waiting: 5,
      url: "https://github.com/karolswdev/holdspeak/pull/612", room_id: "proj-platform", room_name: "Platform" },
    { title: "Update types", repo: "karolswdev/holdspeak", pr_number: 618, days_waiting: 2,
      url: "https://github.com/karolswdev/holdspeak/pull/618", room_id: "proj-platform", room_name: "Platform" },
  ],
  oldest_waiting_days: 5,
  open_assignments: [
    { summary: "PostgreSQL migration", key: "GOV-412", status: "In Progress",
      url: "https://jira.example.com/browse/GOV-412", overdue: false, room_id: "proj-platform", room_name: "Platform" },
  ],
};

function stubHub(watchSummary: unknown = WATCH_SUMMARY) {
  const routes: Record<string, () => Response> = {
    "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted" }),
    "/api/people/relationships/r1/brief": () => json({ brief: {
      relationship_id: "r1", display_name: "Ania", open_commitments: [], agenda_items: [],
      grounding_note_count: 0, linked_meetings: [], unlinked_meeting_count: 0,
      watch_summary: watchSummary, last_meeting: null,
    } }),
    "/api/people/relationships/r1/one-on-ones": () => json({ one_on_ones: [] }),
    "/api/people/relationships/r1": () => json({ relationship: {
      id: "r1", display_name: "Ania", relationship_kind: "direct_report", calendar_links: [],
      owner_aliases: ["ania-k"], project_refs: ["proj-platform"],
    } }),
    "/api/people/relationships": () => json({ relationships: [{ id: "r1", display_name: "Ania", relationship_kind: "direct_report" }] }),
    "/api/door": () => json({ upcoming: [] }),
  };
  vi.stubGlobal("fetch", vi.fn(async (input: string) => {
    const url = String(input);
    const hit = Object.keys(routes).find((p) => url === p || url.startsWith(`${p}?`));
    if (!hit) throw new Error(`Unexpected request: ${url}`);
    return routes[hit]();
  }));
}

/** The glass's check, verbatim: a <button> in the card wears a library class. */
function rawButtons(root: HTMLElement): string[] {
  return Array.from(root.querySelectorAll("button"))
    .map((b) => b.outerHTML.match(/<button\b[^>]*>/)![0])
    .filter((tag) => !(tag.includes("class=") && (
      tag.includes("btn ") || tag.includes('btn"') || tag.includes("signal-button")
      || tag.includes("gadget-chip") || tag.includes("surface-"))));
}

afterEach(() => vi.unstubAllGlobals());

describe("People: the Prep card (HS-172-05)", () => {
  it("every verb in the Prep card is the library Button; no zero counter; no pronoun", async () => {
    stubHub();
    render(<PeopleCore scope="people:r1:prep" />);
    const lens = await screen.findByTestId("people-prep-lens");
    expect(screen.getByTestId("prep-display-name").textContent).toBe("Ania");
    expect(lens.querySelectorAll("button").length).toBeGreaterThan(0);
    expect(rawButtons(lens)).toEqual([]);
    const summary = screen.getByTestId("prep-summary-rows").textContent ?? "";
    expect(summary).toContain("2 PRS WAITING ON ANIA");
    expect(summary).not.toMatch(/\b0\s+(PRS?|ASSIGNMENTS?|COMMITMENTS?|ITEMS?)\b/);
    expect(summary).not.toMatch(/\b(her|him|she|he)\b/i);
  });

  it("a summary with nothing in it draws no zero counter", async () => {
    stubHub({ prs_waiting: [], oldest_waiting_days: 0, open_assignments: [] });
    render(<PeopleCore scope="people:r1:prep" />);
    await screen.findByTestId("people-prep-lens");
    const summary = screen.queryByTestId("prep-summary-rows")?.textContent ?? "";
    expect(summary).not.toMatch(/\b0\s+(PRS?|ASSIGNMENTS?|COMMITMENTS?|ITEMS?)\b/);
  });

  it("Open on PRS WAITING moves to Now; each PR has its own Open", async () => {
    stubHub();
    render(<PeopleCore scope="people:r1:prep" />);
    await screen.findByTestId("people-prep-lens");
    fireEvent.click(screen.getByTestId("prep-prs-open"));
    await screen.findByTestId("people-now-concern");
    const detail = screen.getByTestId("now-prs-detail");
    expect(within(detail).getAllByRole("button", { name: "Open" })).toHaveLength(2);
    expect(screen.getByRole("tab", { name: "Now" }).getAttribute("aria-selected")).toBe("true");
  });
});

describe("People: a person's own window (PHILO-17 2b)", () => {
  it("draws THAT person on the RelationshipPane: six lenses, no Back, not the roster", async () => {
    stubHub();
    render(<PersonWindowBody relationshipId="r1" />);
    const win = await screen.findByTestId("person-window");
    await within(win).findByRole("tablist");
    expect(win.textContent).toContain("Ania");
    expect(within(win).getAllByRole("tab")).toHaveLength(6);
    const head = win.querySelector(".people-detail-head");
    expect(head).toBeTruthy();
    expect(head!.textContent).not.toMatch(/\bBack\b/);
    expect(document.getElementById("surface-people")).toBeNull();
  });
});

/* ── Add on "They owe you", then the saved item (Astra r1 on #1100) ────── */

const PEOPLE_WIRE = join(dirname(fileURLToPath(import.meta.url)), "fixtures", "people-wire");
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const recorded = (name: string): any => JSON.parse(readFileSync(join(PEOPLE_WIRE, `${name}.json`), "utf8"));

describe("People: Add on They owe you shows the saved item", () => {
  /** The hub's own answers from ONE boot (tests/integration/test_desk_chair.py::
   * test_they_owe_you_add_saves_and_the_next_read_carries_the_item, fenced
   * against invented fields): the reads before the press, the POST answer,
   * and the relationship read after it.
   *
   * replaces: tests/e2e/test_philo13_09_prep_glass.py::TestPrepFindsItsPerson::test_the_one_on_one_finds_its_person (the They owe you add)
   */
  it("Add posts the item and the hub's next read draws it under They owe you", async () => {
    const before = recorded("relationship-before");
    const after = recorded("relationship-after");
    const id: string = before.relationship.id;
    const owedBody = "Send me the API migration estimate";
    let saved = false;
    const reads: Record<string, () => unknown> = {
      "/api/people/readiness": () => recorded("readiness"),
      "/api/people/relationships": () => recorded("relationships"),
      [`/api/people/relationships/${id}`]: () => (saved ? after : before),
      [`/api/people/relationships/${id}/one-on-ones`]: () => recorded("one-on-ones"),
      [`/api/people/relationships/${id}/brief`]: () => recorded("brief"),
      "/api/door": () => recorded("door"),
      "/api/projects": () => recorded("projects"),
    };
    const fetchSpy = vi.fn(async (input: string, opts?: { method?: string; body?: string }) => {
      const path = String(input);
      if (opts?.method === "POST" && path === `/api/people/relationships/${id}/owed`) {
        saved = true;
        return json(recorded("owed-created"), 201);
      }
      const read = reads[path];
      if (!read || (opts?.method && opts.method !== "GET")) throw new Error(`no recorded hub answer for ${opts?.method ?? "GET"} ${path}`);
      return json(read());
    });
    vi.stubGlobal("fetch", fetchSpy);
    render(<PeopleCore scope={`people:${id}`} />);
    const owed = await screen.findByTestId("people-they-owe");
    expect(within(owed).queryByText(owedBody)).toBeNull();
    fireEvent.change(within(owed).getByLabelText("They owe you"), { target: { value: owedBody } });
    fireEvent.click(within(owed).getByRole("button", { name: "Add" }));
    await waitFor(() => expect(within(screen.getByTestId("people-they-owe")).getByText(owedBody)).toBeTruthy());
    const posted = fetchSpy.mock.calls.filter(([url, o]) => String(url) === `/api/people/relationships/${id}/owed` && o?.method === "POST");
    expect(posted).toHaveLength(1);
    expect(JSON.parse(String(posted[0][1]?.body)).body).toBe(owedBody);
    expect(within(screen.getByTestId("people-they-owe")).getByText(/They owe you · 1/)).toBeTruthy();
    // It is what they owe, never a request asked of him.
    expect(fetchSpy.mock.calls.some(([url]) => String(url).endsWith("/requests"))).toBe(false);
  });
});
