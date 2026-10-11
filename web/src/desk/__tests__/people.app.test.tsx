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
import { fireEvent, render, screen, within } from "@testing-library/react";
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
