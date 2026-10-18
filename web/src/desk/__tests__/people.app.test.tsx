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
 * tests/unit/test_people_brief.py::TestBriefEnrichment proves the
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
      tag.includes("btn ") || tag.includes('btn"') || tag.includes("btn--chrome") || tag.includes("signal-button")
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

  it("Show on PRS WAITING draws each PR with its own Open", async () => {
    stubHub();
    render(<PeopleCore scope="people:r1:prep" />);
    await screen.findByTestId("people-prep-lens");
    fireEvent.click(screen.getByTestId("prep-prs-open"));
    const detail = await screen.findByTestId("now-prs-detail");
    expect(within(detail).getAllByRole("button", { name: "Open PR" })).toHaveLength(2);
    expect(screen.getByRole("tab", { name: "Prep" }).getAttribute("aria-selected")).toBe("true");
  });
});

describe("People: a person's own window (PHILO-17 2b)", () => {
  it("draws THAT person on the RelationshipPane: Prep and three folded tabs, no Back, not the roster", async () => {
    stubHub();
    render(<PersonWindowBody relationshipId="r1" />);
    const win = await screen.findByTestId("person-window");
    await within(win).findByRole("tablist");
    expect(win.textContent).toContain("Ania");
    expect(within(win).getAllByRole("tab").map((t) => t.textContent)).toEqual(["Prep", "Context", "History", "Info"]);
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
      const read = reads[path.replace("?counts=1", "")];
      if (!read || (opts?.method && opts.method !== "GET")) throw new Error(`no recorded hub answer for ${opts?.method ?? "GET"} ${path}`);
      return json(read());
    });
    vi.stubGlobal("fetch", fetchSpy);
    render(<PeopleCore scope={`people:${id}`} />);
    const owed = await screen.findByTestId("people-they-owe", {}, { timeout: 5000 });
    expect(within(owed).queryByText(owedBody)).toBeNull();
    expect(within(owed).queryByLabelText("They owe you")).toBeNull();
    fireEvent.click(within(owed).getByRole("button", { name: "Add" }));
    fireEvent.change(within(owed).getByLabelText("They owe you"), { target: { value: owedBody } });
    fireEvent.click(within(owed).getByRole("button", { name: "Add" }));
    // 5 s, not the 1 s default: the full suite runs in parallel (#1100).
    await waitFor(() => expect(within(screen.getByTestId("people-they-owe")).getByText(owedBody)).toBeTruthy(), { timeout: 5000 });
    const posted = fetchSpy.mock.calls.filter(([url, o]) => String(url) === `/api/people/relationships/${id}/owed` && o?.method === "POST");
    expect(posted).toHaveLength(1);
    expect(JSON.parse(String(posted[0][1]?.body)).body).toBe(owedBody);
    expect(screen.getByTestId("people-they-owe").querySelector("h3")!.textContent).toBe("THEY OWE YOU1");
    expect(within(screen.getByTestId("people-they-owe")).queryByLabelText("They owe you")).toBeNull();
    // It is what they owe, never a request asked of him.
    expect(fetchSpy.mock.calls.some(([url]) => String(url).endsWith("/requests"))).toBe(false);
  });
});

/* ── Remove on a TO RAISE row (PHILO-17 refit) ─────────────────────────── */

const AGENDA_WIRE = join(dirname(fileURLToPath(import.meta.url)), "fixtures", "people-agenda-wire");
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const agendaWire = (name: string): any => JSON.parse(readFileSync(join(AGENDA_WIRE, `${name}.json`), "utf8"));

describe("People: Remove on a TO RAISE row", () => {
  /** The hub's own answers from ONE boot (tests/integration/test_desk_chair.py::
   * test_agenda_remove_takes_the_item_off_to_raise, fenced against invented
   * fields): the brief before, the remove answer, the brief after. */
  it("Remove posts the transition and the hub's next brief drops the item", async () => {
    const id: string = agendaWire("relationship").relationship.id;
    const before = agendaWire("brief-before");
    const removedBody = "Ask about the EU shard backup plan";
    const drop = before.brief.agenda_items.find((item: { body: string }) => item.body === removedBody);
    let removed = false;
    const reads: Record<string, () => unknown> = {
      "/api/people/readiness": () => agendaWire("readiness"),
      "/api/people/relationships?counts=1": () => agendaWire("relationships"),
      [`/api/people/relationships/${id}`]: () => agendaWire("relationship"),
      [`/api/people/relationships/${id}/one-on-ones`]: () => agendaWire("one-on-ones"),
      [`/api/people/relationships/${id}/brief`]: () => (removed ? agendaWire("brief-after") : before),
    };
    const fetchSpy = vi.fn(async (input: string, opts?: { method?: string; body?: string }) => {
      const path = String(input);
      if (opts?.method === "POST" && path === `/api/people/agenda/${drop.id}/transition`) {
        removed = true;
        return json(agendaWire("agenda-removed"));
      }
      const read = reads[path];
      if (!read || (opts?.method && opts.method !== "GET")) throw new Error(`no recorded hub answer for ${opts?.method ?? "GET"} ${path}`);
      return json(read());
    });
    vi.stubGlobal("fetch", fetchSpy);
    render(<PersonWindowBody relationshipId={id} />);
    const rows = await screen.findAllByTestId("prep-agenda", {}, { timeout: 5000 });
    expect(rows.map((row) => row.textContent)).toEqual(expect.arrayContaining([expect.stringContaining(removedBody)]));
    const row = rows.find((r) => r.textContent?.includes(removedBody))!;
    fireEvent.click(within(row).getByRole("button", { name: `Remove ${removedBody}` }));
    await waitFor(() => expect(screen.getAllByTestId("prep-agenda").map((r) => r.textContent).join("|")).not.toContain(removedBody), { timeout: 5000 });
    expect(screen.getAllByTestId("prep-agenda").map((r) => r.textContent).join("|")).toContain("Pick the cutover date");
    const posted = fetchSpy.mock.calls.filter(([url, o]) => String(url).endsWith("/transition") && o?.method === "POST");
    expect(posted).toHaveLength(1);
    expect(JSON.parse(String(posted[0][1]?.body))).toEqual({ to: "removed" });
  });
});

/* ── Betterment D6: people come from his work ────────────────────────── */

const WEEK_WIRE = join(dirname(fileURLToPath(import.meta.url)), "fixtures", "daily-week");
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const week = (name: string): any => JSON.parse(readFileSync(join(WEEK_WIRE, `${name}.json`), "utf8"));

describe("People from his work (Betterment daily D6), on the recorded week", () => {
  /** The hub's own answers (tests/integration/test_desk_people.py::
   *  test_people_from_work_wire): the week with no people, the three Add
   *  answers, and the reads after them. */
  function replayWeek() {
    const wire = week("people-from-work");
    let added = 0;
    const posts: Array<{ url: string; body: unknown }> = [];
    const fetchSpy = vi.fn(async (input: string, opts?: { method?: string; body?: string }) => {
      const path = String(input);
      if (opts?.method && opts.method !== "GET") {
        const body = opts.body ? JSON.parse(String(opts.body)) : null;
        posts.push({ url: path, body });
        if (path === "/api/people/suggestions/add") {
          added += 1;
          return json(wire.added[body.key], 201);
        }
        if (path === "/api/people/suggestions/hide") return json({ hidden: body.key });
        if (path === "/api/settings") return json(wire.before["/api/settings"]);
        throw new Error(`no recorded hub answer for ${opts.method} ${path}`);
      }
      // Before the three adds the week reads as it did; after them, as after.
      // Between the adds: the recorded rows, less the ones already added.
      if (path === "/api/people/suggestions" && added > 0 && added < 3) {
        const left = Object.keys(wire.added).slice(added);
        return json({ suggestions: wire.before[path].suggestions.filter((s: { key: string }) => left.includes(s.key)) });
      }
      if (path === "/api/people/readiness" && added > 0) return json(wire.after[path]);
      if (path === "/api/people/relationships?counts=1" && added < 3) {
        return json({ relationships: wire.after[path].relationships.slice(0, added) });
      }
      const phase = added >= 3 ? wire.after : wire.before;
      if (path in phase) return json(phase[path]);
      throw new Error(`no recorded hub answer for GET ${path}`);
    });
    vi.stubGlobal("fetch", fetchSpy);
    return { wire, posts };
  }

  it("with no people, FROM YOUR MEETINGS names Theo, Jun and Mira, each with Add and Not a person; no Set up step", async () => {
    replayWeek();
    render(<PeopleCore />);
    const section = await screen.findByTestId("people-suggestions");
    const rows = within(section).getAllByTestId("people-suggestion");
    expect(rows.map((row) => row.textContent ?? "")).toEqual([
      expect.stringContaining("Theo"), expect.stringContaining("Jun"), expect.stringContaining("Mira"),
    ]);
    expect(rows[2].textContent).toContain("named in Payments platform sync · 1 promise");
    for (const row of rows) {
      expect(within(row).getByRole("button", { name: /^Add / })).toBeTruthy();
      expect(within(row).getByRole("button", { name: /is not a person$/ })).toBeTruthy();
      expect(rawButtons(row)).toEqual([]);
    }
    expect(screen.queryByText("Set up People")).toBeNull();
    expect(screen.queryByText("Do it")).toBeNull();
    // His own name is not set: People asks it once.
    expect(await screen.findByTestId("people-who-are-you")).toBeTruthy();
  });

  it("three Add presses make them, and Mira's prep shows her promise with no other step", async () => {
    const { wire, posts } = replayWeek();
    render(<PeopleCore />);
    for (const name of ["Theo", "Jun", "Mira"]) {
      fireEvent.click(await screen.findByRole("button", { name: `Add ${name}` }));
      await waitFor(() => expect(screen.queryByRole("button", { name: `Add ${name}` })).toBeNull());
    }
    expect(posts.filter((p) => p.url === "/api/people/suggestions/add").map((p) => (p.body as { key: string }).key))
      .toEqual(["theo", "jun", "mira"]);
    await waitFor(() => expect(screen.queryByTestId("people-suggestions")).toBeNull());
    expect(await screen.findByRole("button", { name: /Mira/ })).toBeTruthy();
    // Mira's prep: her promise, from the meeting, with no alias press.
    cleanupAndOpen(wire.added.mira.relationship.id);
    const owed = await screen.findByTestId("people-they-owe", {}, { timeout: 5000 });
    expect(owed.textContent).toContain("Draft the rollback runbook");
  });

  it("Not a person takes the name off for good", async () => {
    const { posts } = replayWeek();
    render(<PeopleCore />);
    fireEvent.click(await screen.findByRole("button", { name: "Jun is not a person" }));
    await waitFor(() => expect(screen.queryByRole("button", { name: "Add Jun" })).toBeNull());
    expect(posts).toEqual([{ url: "/api/people/suggestions/hide", body: { key: "jun" } }]);
  });

  it("no people and no suggestions: one line", async () => {
    const wire = week("people-from-work");
    vi.stubGlobal("fetch", vi.fn(async (input: string) => {
      const path = String(input);
      if (path === "/api/people/suggestions") return json({ suggestions: [] });
      if (path in wire.before) return json(wire.before[path]);
      throw new Error(`no recorded hub answer for GET ${path}`);
    }));
    render(<PeopleCore />);
    expect((await screen.findByTestId("people-empty-roster")).textContent).toBe("People you meet appear here.");
    expect(screen.queryByTestId("people-suggestions")).toBeNull();
  });

  it("a People read that fails is one line in place: People could not be read · Try again", async () => {
    let fail = true;
    const wire = week("people-from-work");
    vi.stubGlobal("fetch", vi.fn(async (input: string) => {
      const path = String(input);
      if (fail && path === "/api/people/readiness") return json({ detail: "people_store_unavailable" }, 503);
      if (path in wire.after) return json(wire.after[path]);
      throw new Error(`no recorded hub answer for GET ${path}`);
    }));
    render(<PeopleCore />);
    const line = await screen.findByTestId("people-read-failed");
    expect(line.textContent).toContain("People could not be read");
    fail = false;
    fireEvent.click(within(line).getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("button", { name: /Mira/ })).toBeTruthy();
    expect(screen.queryByTestId("people-read-failed")).toBeNull();
  });
});

function cleanupAndOpen(id: string) {
  document.body.innerHTML = "";
  render(<PeopleCore scope={`people:${id}:prep`} />);
}
