import { useDesk } from "../store";
import executionLinked from "./fixtures/people-wire/execution-linked.json";
import { personView } from "../../pages/cores/__tests__/peopleView";
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
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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

afterEach(() => {
  vi.unstubAllGlobals();
  // W1-TRUTH: the "Your name is not set" row shows once per browser.
  try { window.localStorage.removeItem("hs.people.name-asked"); } catch { /* none */ }
});

describe("People: the Prep card (HS-172-05)", () => {
  it("every verb in the Prep card is the library Button; no zero counter; no pronoun", async () => {
    stubHub();
    render(<PersonWindowBody relationshipId="r1" />);
    const lens = await screen.findByTestId("people-prep-lens");
    expect(screen.getByTestId("prep-display-name").textContent).toBe("Ania");
    expect(lens.querySelectorAll("button").length).toBeGreaterThan(0);
    expect(rawButtons(lens)).toEqual([]);
    await personView("1:1 brief");const summary = screen.getByRole("grid",{name:"1:1 brief"}).textContent ?? "";
    expect(summary).toContain("#612");expect(summary).toContain("#618");
    expect(summary).not.toMatch(/\b0\s+(PRS?|ASSIGNMENTS?|COMMITMENTS?|ITEMS?)\b/);
    expect(summary).not.toMatch(/\b(her|him|she|he)\b/i);
  });

  it("a summary with nothing in it draws no zero counter", async () => {
    stubHub({ prs_waiting: [], oldest_waiting_days: 0, open_assignments: [] });
    render(<PersonWindowBody relationshipId="r1" />);
    await screen.findByTestId("people-prep-lens");
    await personView("1:1 brief");const grid=screen.getByRole("grid",{name:"1:1 brief"});
    expect(within(grid).queryAllByRole("row")).toHaveLength(0);const summary=grid.textContent??"";
    expect(summary).not.toMatch(/\b0\s+(PRS?|ASSIGNMENTS?|COMMITMENTS?|ITEMS?)\b/);
  });

  it("Show on PRS WAITING draws each PR with its own Open", async () => {
    stubHub();
    render(<PersonWindowBody relationshipId="r1" />);
    await screen.findByTestId("people-prep-lens");
    await personView("1:1 brief");
    for (const pr of WATCH_SUMMARY.prs_waiting){const row=screen.getByRole("row",{name:new RegExp(`#${pr.pr_number}`)});expect(row.querySelector("button")).toBeNull();fireEvent.click(row);expect(screen.getAllByRole("button",{name:"Open PR"})).toHaveLength(1);}
    expect(screen.getByTestId("people-prep-lens")).toBeTruthy();
  });
});

describe("People: a person's own window (PHILO-17 2b)", () => {
  it("keeps a loading face until the ready person's detail arrives", async () => {
    let finishRelationship!: (response: Response) => void;
    const relationship = new Promise<Response>((resolve) => { finishRelationship = resolve; });
    vi.stubGlobal("fetch", vi.fn(async (input: string) => {
      const url = String(input);
      if (url === "/api/people/readiness") return json({ readiness: "ready", store: "encrypted" });
      if (url === "/api/people/relationships/r1") return relationship;
      if (url === "/api/people/relationships/r1/one-on-ones") return json({ one_on_ones: [] });
      if (url === "/api/people/relationships/r1/brief") return json({ brief: {
        relationship_id: "r1", display_name: "Ania", open_commitments: [], agenda_items: [],
        grounding_note_count: 0, linked_meetings: [], unlinked_meeting_count: 0,
      } });
      throw new Error(`Unexpected request: ${url}`);
    }));
    render(<PersonWindowBody relationshipId="r1" />);
    expect(screen.getByRole("status")).toHaveAttribute("aria-busy", "true");
    expect(screen.queryByTestId("person-window")).toBeNull();
    finishRelationship(json({ relationship: { id: "r1", display_name: "Ania", relationship_kind: "direct_report", calendar_links: [] } }));
    await screen.findByTestId("people-detail-head");
    expect(screen.getByTestId("person-window").querySelector(':scope > .surface-state[data-kind="loading"]')).toBeNull();
  });

  it("names a failed detail read and retries into the person", async () => {
    let fail = true;
    vi.stubGlobal("fetch", vi.fn(async (input: string) => {
      const url = String(input);
      if (url === "/api/people/readiness") return json({ readiness: "ready", store: "encrypted" });
      if (url === "/api/people/relationships/r1") {
        return fail
          ? json({ detail: "people_store_unavailable" }, 503)
          : json({ relationship: { id: "r1", display_name: "Ania", relationship_kind: "direct_report", calendar_links: [] } });
      }
      if (url === "/api/people/relationships/r1/one-on-ones") return json({ one_on_ones: [] });
      if (url === "/api/people/relationships/r1/brief") return json({ brief: {
        relationship_id: "r1", display_name: "Ania", open_commitments: [], agenda_items: [],
        grounding_note_count: 0, linked_meetings: [], unlinked_meeting_count: 0,
      } });
      throw new Error(`Unexpected request: ${url}`);
    }));
    render(<PersonWindowBody relationshipId="r1" />);
    const failure = await screen.findByTestId("people-read-failed");
    expect(within(failure).getByRole("button", { name: "Try again" })).toBeTruthy();
    fail = false;
    fireEvent.click(within(failure).getByRole("button", { name: "Try again" }));
    await screen.findByTestId("people-detail-head");
    expect(screen.queryByTestId("people-read-failed")).toBeNull();
  });

  it("draws THAT person as a ledger with one composer and no disclosure pages", async () => {
    stubHub();
    render(<PersonWindowBody relationshipId="r1" />);
    const win = await screen.findByTestId("person-window");
    await within(win).findByTestId("people-composer");
    expect(win.textContent).toContain("Ania");
    // Betterment D7: the prep, then Context, History and Info as folds under it.
    expect(within(win).getByTestId("people-prep-lens")).toBeTruthy();
    expect(win.querySelector(".surface-disclosure")).toBeNull();
    expect(win.querySelectorAll("textarea")).toHaveLength(1);
    const head = within(win).getByTestId("people-detail-head");
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
    render(<PersonWindowBody relationshipId={id} />);
    const owed = await screen.findByTestId("people-commitments", {}, { timeout: 5000 });
    expect(within(owed).queryByText(owedBody)).toBeNull();
    expect(within(owed).queryByLabelText("Priya owes me")).toBeNull();
    const composer = screen.getByTestId("people-composer");
    fireEvent.change(within(composer).getByRole("combobox", { name: "Add to this person" }), { target: { value: "they" } });
    fireEvent.change(within(composer).getByLabelText("Priya owes me"), { target: { value: owedBody } });
    const owedInput = within(composer).getByLabelText("Priya owes me");
    fireEvent.change(within(composer).getByRole("combobox", { name: "Add to this person" }), { target: { value: "note" } });
    const noteInput = within(composer).getByLabelText("Note");
    // A different voice target mounts for each kind; late dictation cannot
    // follow a reused pad into the other draft.
    expect(noteInput).not.toBe(owedInput);
    expect(noteInput).toHaveValue("");
    fireEvent.change(within(composer).getByRole("combobox", { name: "Add to this person" }), { target: { value: "they" } });
    expect(within(composer).getByLabelText("Priya owes me")).toHaveValue(owedBody);
    fireEvent.click(within(composer).getByRole("button", { name: /^Add$/ }));
    // 5 s, not the 1 s default: the full suite runs in parallel (#1100).
    await waitFor(() => expect(within(screen.getByTestId("people-commitments")).getByText(owedBody)).toBeTruthy(), { timeout: 5000 });
    const posted = fetchSpy.mock.calls.filter(([url, o]) => String(url) === `/api/people/relationships/${id}/owed` && o?.method === "POST");
    expect(posted).toHaveLength(1);
    expect(JSON.parse(String(posted[0][1]?.body)).body).toBe(owedBody);
    expect(screen.getByTestId("people-commitments-facts").textContent).toContain("1 owed to you");
    expect(within(screen.getByTestId("people-commitments")).queryByLabelText("Priya owes me")).toBeNull();
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
    await screen.findByTestId("people-prep-lens");await personView("Agenda");
    const rows = await screen.findAllByTestId("prep-agenda", {}, { timeout: 5000 });
    expect(rows.map((row) => row.textContent)).toEqual(expect.arrayContaining([expect.stringContaining(removedBody)]));
    const row = rows.find((r) => r.textContent?.includes(removedBody))!;
    fireEvent.click(row);fireEvent.click(screen.getByRole("button",{name:"Remove"}));
    expect(fetchSpy.mock.calls.filter(([,o])=>o?.method==="POST")).toHaveLength(0);
    fireEvent.click(within(screen.getByRole("region",{name:`Remove ${removedBody}?`})).getByRole("button",{name:"Remove"}));
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

  it("with no people, FROM YOUR MEETINGS names Theo, Jun and Mira, each with Add and Hide; no Set up step", async () => {
    replayWeek();
    render(<PeopleCore />);
    // The native face: the names sit on the rail under the people; the
    // status bar counts them; a picked name is the plate with its two verbs.
    expect((await screen.findByTestId("people-suggestions")).textContent).toBe("3 from your meetings");
    const rows = screen.getAllByTestId("people-suggestion");
    expect(rows.map((row) => row.textContent ?? "").sort()).toEqual([
      expect.stringContaining("Jun"), expect.stringContaining("Mira"), expect.stringContaining("Theo"),
    ]);
    for (const row of rows) {
      fireEvent.click(row);
      expect(screen.getByTestId("people-summary")).toHaveTextContent(/Named in/);
      expect(screen.getByRole("button", { name: "Add from meetings" })).toBeEnabled();
      expect(screen.getByRole("button", { name: "Hide" })).toBeEnabled();
      expect(rawButtons(row)).toEqual([]);
      expect(row.querySelector("button")).toBeNull();
    }
    expect(screen.queryByTestId("people-who-are-you")).toBeNull();
    expect(screen.queryByText("Your name is not set")).toBeNull();
  });

  it("three Add presses make them, and Mira's prep shows her promise with no other step", async () => {
    const { wire, posts } = replayWeek();
    render(<PeopleCore />);
    for (const name of ["Theo", "Jun", "Mira"]) {
      const row = (await screen.findAllByTestId("people-suggestion")).find((r) => r.textContent?.includes(name))!;
      fireEvent.click(row);
      fireEvent.click(screen.getByRole("button", { name: "Add from meetings" }));
      await waitFor(() => expect(screen.queryAllByTestId("people-suggestion").some((row) => row.textContent?.startsWith(name))).toBe(false));
    }
    expect(posts.filter((p) => p.url === "/api/people/suggestions/add").map((p) => (p.body as { key: string }).key))
      .toEqual(["theo", "jun", "mira"]);
    await waitFor(() => expect(screen.queryByTestId("people-suggestions")).toBeNull());
    expect(await screen.findByRole("row", { name: /Mira/ })).toBeTruthy();
    // Mira's prep: her promise, from the meeting, with no alias press.
    cleanupAndOpen(wire.added.mira.relationship.id);
    const owed = await screen.findByTestId("people-commitments", {}, { timeout: 5000 });
    expect(owed.textContent).toContain("Draft the rollback runbook");
  });

  it("Hide takes the name off for good", async () => {
    const { posts } = replayWeek();
    render(<PeopleCore />);
    const jun = (await screen.findAllByTestId("people-suggestion")).find((r) => r.textContent?.includes("Jun"))!;
    fireEvent.click(jun);
    fireEvent.click(await screen.findByRole("button", { name: "Hide" }));
    await waitFor(() => expect(screen.queryAllByTestId("people-suggestion").some((row) => row.textContent?.startsWith("Jun"))).toBe(false));
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
    const empty = await screen.findByText("People you meet appear here.");
    // DELIGHT (2026-10-27): the empty roster is an object, one line, one verb.
    expect(empty).toHaveTextContent("People you meet appear here.");
    expect(screen.queryByTestId("people-suggestions")).toBeNull();
    // The verb is Add person: the press opens the add row (the rendered outcome).
    fireEvent.click(screen.getByRole("button", { name: "Add person" }));
    expect(await screen.findByTestId("people-add-row")).toBeTruthy();
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
    expect(await screen.findByRole("row", { name: /Mira/ })).toBeTruthy();
    expect(screen.queryByTestId("people-read-failed")).toBeNull();
  });
});

// Betterment daily D8: a Mac whose HOME has no keychain (#1328). The hub's own
// answers (tests/unit/test_desk_notices.py::
// test_the_hub_says_people_is_not_set_up_on_this_mac): one line, no verb, never
// "could not be read" with a Try again that cannot work.
describe("People on a Mac with no keychain (Betterment daily D8)", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("says People is not set up on this Mac, with no Try again", async () => {
    const wire = week("people-no-key-store");
    const asked: string[] = [];
    vi.stubGlobal("fetch", vi.fn(async (input: string) => {
      const path = String(input);
      asked.push(path);
      if (path in wire.before) return json(wire.before[path]);
      throw new Error(`no recorded hub answer for GET ${path}`);
    }));
    render(<PeopleCore />);
    const line = await screen.findByTestId("people-not-here");
    expect(within(line).getByRole("alert")).toHaveTextContent("People is not set up on this Mac.");
    expect(screen.getByTestId("people-status")).toHaveTextContent("Unavailable");
    expect(within(line).queryByRole("button")).toBeNull();
    expect(screen.queryByTestId("people-read-failed")).toBeNull();
    expect(screen.queryByRole("button", { name: "Try again" })).toBeNull();
    expect(asked).toEqual(["/api/people/readiness"]);
  });
});

function cleanupAndOpen(id: string) {
  document.body.innerHTML = "";
  render(<PersonWindowBody relationshipId={id} />);
}

describe("DELIGHT 2 small joy: a person's next 1:1 in their own teal", () => {
  /** The recorded People wire (fixtures/people-wire): four people, and the
   *  Door's upcoming 1:1 with Priya (`person_relationship_id`), at the time of
   *  the boot (2026-10-11 20:40Z, before the 21:27Z 1:1). */
  it("the rail row with a next 1:1 says it in the person ink; no 1:1 says nothing", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date("2026-10-11T20:40:00Z"));
    try {
      const reads: Record<string, () => unknown> = {
        "/api/people/readiness": () => recorded("readiness"),
        "/api/people/relationships": () => recorded("relationships"),
        "/api/door": () => recorded("door"),
        "/api/projects": () => recorded("projects"),
        "/api/people/suggestions": () => ({ suggestions: [] }),
      };
      vi.stubGlobal("fetch", vi.fn(async (input: string, opts?: { method?: string }) => {
        const path = String(input).replace("?counts=1", "");
        const read = reads[path];
        if (!read || (opts?.method && opts.method !== "GET")) throw new Error(`no recorded hub answer for ${opts?.method ?? "GET"} ${path}`);
        return json(read());
      }));
      render(<PeopleCore />);
      const priya = await waitFor(() => {
        const row = screen.getAllByTestId("people-row").find((r) => r.textContent?.includes("Priya Nair"));
        expect(row?.querySelector('[data-col="next"]')?.textContent).not.toBe("");
        return row!;
      }, { timeout: 5000 });
      expect(priya.querySelector("button")).toBeNull();
      const avery = screen.getAllByTestId("people-row").find((r) => r.textContent?.includes("Avery Chen"))!;
      expect(avery.querySelector('[data-col="next"]')).toHaveTextContent("");
    } finally {
      vi.useRealTimers();
    }
  });
});

// The roster consumes recorded People answers; the person editor has its own host.
describe("People selection window", () => {
  it("selects into a plain summary, opens through the declared verb, and keeps Find from opening a person", async () => {
    const door = await import("../openObject");
    const open = vi.spyOn(door, "openPerson").mockImplementation(() => {});
    const person = recorded("relationship-before").relationship;
    vi.stubGlobal("fetch", vi.fn(async (input: string) => {
      const path = String(input).replace("?counts=1", "");
      if (path === "/api/people/readiness") return json(recorded("readiness"));
      if (path === "/api/people/relationships") return json(recorded("relationships"));
      if (path === `/api/people/relationships/${person.id}`) return json(recorded("relationship-before"));
      if (path.endsWith("/one-on-ones")) return json(recorded("one-on-ones"));
      if (path === "/api/door") return json(recorded("door"));
      if (path === "/api/people/suggestions") return json({ suggestions: [] });
      throw new Error(`No recorded answer: ${path}`);
    }));
    try {
      render(<PeopleCore />);
      const row = await screen.findByRole("row", { name: /Priya Nair/ });
      expect(screen.getByRole("button", { name: "Open" })).toBeDisabled();
      fireEvent.click(row);
      const summary = screen.getByTestId("people-summary");
      await within(summary).findByText(person.commitments[0].body);
      expect(row).toHaveAttribute("aria-selected", "true");
      expect(summary.querySelector("button, textarea, .people-now")).toBeNull();
      expect(row.querySelector("button, .surface-spine")).toBeNull();
      expect(open).not.toHaveBeenCalled();
      fireEvent.keyDown(row, { key: "Enter" });
      expect(open).toHaveBeenLastCalledWith(person.id);
      fireEvent.doubleClick(row);
      expect(open).toHaveBeenCalledTimes(2);
      fireEvent.click(screen.getByRole("button", { name: "Prep 1:1" }));
      expect(open).toHaveBeenLastCalledWith(person.id, "prep");
      fireEvent.contextMenu(row, { clientX: 80, clientY: 80 });
      expect(screen.getByRole("menuitem", { name: /Prep 1:1/ })).toBeEnabled();
      fireEvent.keyDown(row, { key: "Escape" });
      fireEvent.change(screen.getByRole("textbox", { name: "Find a person" }), { target: { value: "does not match" } });
      expect(screen.getByTestId("people-summary")).toHaveTextContent("No names match");
      expect(screen.getByRole("button", { name: "Open" })).toBeDisabled();
      expect(open).toHaveBeenCalledTimes(3);
      expect(screen.queryByText("Your name is not set")).toBeNull();
    } finally { open.mockRestore(); }
  });
});

 it("drops a late selection read after Find, then names a failed read and retries the same person", async () => {
    const person = recorded("relationship-before").relationship;
    let finish!: (response: Response) => void;
    let attempts = 0;
    vi.stubGlobal("fetch", vi.fn(async (input: string) => {
      const path = String(input).replace("?counts=1", "");
      if (path === "/api/people/readiness") return json(recorded("readiness"));
      if (path === "/api/people/relationships") return json(recorded("relationships"));
      if (path === `/api/people/relationships/${person.id}`) {
        attempts += 1;
        if (attempts === 1) return new Promise<Response>((resolve) => { finish = resolve; });
        if (attempts === 2) return json({ detail: "people_store_unavailable" }, 503);
        return json(recorded("relationship-before"));
      }
      if (path.endsWith("/one-on-ones")) return json(recorded("one-on-ones"));
      if (path === "/api/door") return json(recorded("door"));
      if (path === "/api/people/suggestions") return json({ suggestions: [] });
      throw new Error(`No recorded answer: ${path}`);
    }));
    render(<PeopleCore />);
    fireEvent.click(await screen.findByRole("row", { name: /Priya Nair/ }));
    const find = screen.getByRole("textbox", { name: "Find a person" });
    fireEvent.change(find, { target: { value: "Avery" } });
    await act(async () => { finish(json(recorded("relationship-before"))); });
    expect(screen.getByTestId("people-summary")).toHaveTextContent("Select a person");
    expect(screen.getByTestId("people-summary")).not.toHaveTextContent(person.commitments[0].body);
    fireEvent.change(find, { target: { value: "" } });
    fireEvent.click(screen.getByRole("row", { name: /Priya Nair/ }));
    await within(screen.getByTestId("people-summary")).findByRole("alert");
    expect(screen.getByTestId("people-summary")).toHaveTextContent("Commitments not read");
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await within(screen.getByTestId("people-summary")).findByText(person.commitments[0].body);
    expect(within(screen.getByTestId("people-summary")).queryByRole("alert")).toBeNull();
  });

const listBus = vi.hoisted(() => {
  const listeners = new Set<(frame: unknown) => void>();
  return { listeners, subscribe: (type: string, listener: (frame: unknown) => void) => {
    if (type === "desk_changed") listeners.add(listener);
    return () => { listeners.delete(listener); };
  } };
});
vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ subscribe: listBus.subscribe }),
  useOptionalRuntimeBus: () => ({ subscribe: listBus.subscribe }),
}));
const changedPerson = () => act(() => listBus.listeners.forEach(listener => listener({type:"desk_changed",data:{kind:"relationship",op:"update"}})));

describe("People roster lifecycle", () => {
  function replay() {
    let people = recorded("relationships").relationships;
    let readiness = recorded("readiness");
    let rosterReads = 0;
    vi.stubGlobal("fetch", vi.fn(async (input: string) => {
      const path = String(input).replace("?counts=1", "");
      if (path === "/api/people/readiness") return json(readiness);
      if (path === "/api/people/relationships") { rosterReads++; return json({relationships:people}); }
      if (path === "/api/people/suggestions") return json({suggestions:[]});
      if (path === "/api/door") return json(recorded("door"));
      if (path.endsWith("/one-on-ones")) return json(recorded("one-on-ones"));
      if (path.endsWith(recorded("relationship-before").relationship.id)) return json(recorded("relationship-before"));
      throw new Error(`No recorded answer: ${path}`);
    }));
    return {
      remove: () => { people = people.filter((row: {id:string}) => row.id !== recorded("relationship-before").relationship.id); },
      refuse: () => { readiness = week("people-no-key-store").before["/api/people/readiness"]; },
      reads: () => rosterReads,
    };
  }
  it("closes the selected person's pane when that person leaves the roster", async () => {
    const wire = replay();
    render(<PeopleCore />);
    fireEvent.click(await screen.findByRole("row",{name:/Priya Nair/}));
    await within(screen.getByTestId("people-summary")).findByText(recorded("relationship-before").relationship.commitments[0].body);
    wire.remove(); changedPerson();
    await waitFor(() => expect(screen.queryByRole("row",{name:/Priya Nair/})).toBeNull());
    expect(screen.getByTestId("people-summary")).toHaveTextContent("Select a person");
    expect(screen.queryByTestId("people-summary-name")).toBeNull();
    expect(screen.getByRole("button",{name:"Open"})).toBeDisabled();
  });
  it("keeps the selected person through a roster reload", async () => {
    const wire = replay();
    render(<PeopleCore />);
    const row = await screen.findByRole("row",{name:/Priya Nair/}); fireEvent.click(row);
    await screen.findByTestId("people-summary-name");
    const before = wire.reads(); changedPerson();
    await waitFor(() => expect(wire.reads()).toBeGreaterThan(before));
    expect(row).toHaveAttribute("aria-selected","true");
    expect(screen.getByTestId("people-summary-name")).toHaveTextContent("Priya Nair");
  });
  it("replaces the roster with the named refusal when readiness changes", async () => {
    const wire = replay(); render(<PeopleCore />);
    await screen.findByRole("row",{name:/Priya Nair/});
    wire.refuse(); changedPerson();
    expect(await screen.findByTestId("people-not-here")).toHaveTextContent("People is not set up on this Mac.");
    expect(screen.queryByRole("grid",{name:"People"})).toBeNull();
    expect(screen.queryByText("People you meet appear here.")).toBeNull();
  });
});

describe("round 2 failure seats", () => {
  it.each(["locked", "unavailable", "no_key_store", "key_unavailable"])("uses the kit refusal state and keeps the status bar for %s", async state => {
    vi.stubGlobal("fetch", vi.fn(async () => json({readiness:state})));
    const {container} = render(<PeopleCore />);
    await waitFor(() => expect(container.querySelector('.surface-action-notice[role="alert"]')).toBeTruthy());
    expect(screen.getByTestId("people-status")).toHaveTextContent(state === "locked" ? "Locked" : "Unavailable");
    expect(container.querySelector('.surface-state-glyph')).toBeNull();
    expect(screen.queryByRole("grid",{name:"People"})).toBeNull();
  });
  it("keeps an Add failure in the form and retries with its primary verb", async () => {
    let refused = true, finish!:(response:Response)=>void;
    const person=recorded("relationship-before").relationship;
    let reading=true;
    vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
      const path=String(input);
      if (path === "/api/people/readiness") return json(recorded("readiness"));
      if (path===`/api/people/relationships/${person.id}`)return reading?new Promise<Response>(resolve=>{finish=resolve;}):json(recorded("relationship-before"));
      if (path.endsWith("/one-on-ones"))return json(recorded("one-on-ones"));
      if (path.startsWith("/api/people/relationships") && init?.method === "POST") return refused ? json({detail:"people_store_unavailable"},503) : json(recorded("people-add-recovery"));
      if (path.startsWith("/api/people/relationships")) return json(recorded("relationships"));
      if (path === "/api/door") return json(recorded("door"));
      if (path === "/api/people/suggestions") return json({suggestions:[]});
      throw new Error(path);
    }));
    render(<PeopleCore />);fireEvent.click(await screen.findByRole("row",{name:/Priya Nair/}));
    await waitFor(()=>expect(finish).toBeTypeOf("function"));fireEvent.click(screen.getByRole("button",{name:"Add person"}));
    const form=screen.getByTestId("people-add-row"), name=within(form).getByRole("textbox",{name:"Add person"});
    fireEvent.change(name,{target:{value:"Keep this name"}}); fireEvent.click(within(form).getByRole("button",{name:"Add"}));
    await within(form).findByRole("alert");
    reading=false;await act(async()=>finish(json(recorded("relationship-before"))));
    const fail=within(form).getByRole("alert");
    expect(fail.closest('.surface-inspector-notice')).toBeTruthy();
    expect(name).toHaveValue("Keep this name");
    expect(screen.getAllByRole("button",{name:"Try again"})).toHaveLength(1);
    const retry=within(form).getByRole("button",{name:"Try again"}); expect(retry.closest('.surface-inspector-actions')).toBeTruthy();
    refused=false; fireEvent.click(retry); await waitFor(() => expect(name).toHaveValue(""));
  });
});

describe("Person records share kit selection and forms", () => {
  function readPersonRecords() {
    vi.stubGlobal("fetch",vi.fn(async (input:string) => {
      const path=String(input);
      if(path.endsWith("/brief"))return json(recorded("brief"));
      if(path==="/api/projects")return json(recorded("projects"));
      if(path==="/api/door")return json(recorded("door"));
      throw new Error(`No recorded read: ${path}`);
    }));
  }
  it("keeps a note draft when Views change and every record opens from its verb",async()=>{
    readPersonRecords();const {RelationshipPane}=await import("../../pages/cores/PeopleCore");
    render(<RelationshipPane relationship={recorded("relationship-before").relationship} onRefresh={vi.fn()} onProtectedFailure={vi.fn()} onArchived={vi.fn()}/>);
    await screen.findByTestId("people-composer");fireEvent.click(screen.getByRole("button",{name:"Note"}));
    fireEvent.change(screen.getByRole("textbox",{name:"Note"}),{target:{value:"Keep the rollout draft."}});
    await personView("Agenda");fireEvent.click(screen.getByRole("button",{name:"Add…"}));
    expect(screen.getByRole("textbox",{name:"Add to the agenda"})).toHaveValue("");
    expect(screen.queryByRole("combobox",{name:"Add to this person"})).toBeNull();
    fireEvent.click(screen.getByRole("button",{name:"Cancel"}));expect(screen.queryByRole("textbox",{name:"Add to the agenda"})).toBeNull();
    await personView("Links");await personView("1:1 brief");
    for(const row of within(screen.getByRole("grid",{name:"1:1 brief"})).queryAllByRole("row"))expect(row.querySelector("a,button")).toBeNull();
    await personView("Ledger");expect(screen.getByRole("textbox",{name:"Note"})).toHaveValue("Keep the rollout draft.");
    expect(screen.getByTestId("people-composer").querySelectorAll('.surface-inspector-actions')).toHaveLength(1);
  });
  it("closes a removal question when the saved relationship content changes",async()=>{
    readPersonRecords();const {RelationshipPane}=await import("../../pages/cores/PeopleCore");
    const person={...recorded("relationship-before").relationship,owner_aliases:["Priya S."]};
    const props={onRefresh:vi.fn(),onProtectedFailure:vi.fn(),onArchived:vi.fn()};
    const mounted=render(<RelationshipPane relationship={person} {...props}/>);
    await screen.findByTestId("people-prep-lens");await personView("Links");
    fireEvent.click(screen.getByRole("row",{name:/Priya S\./}));fireEvent.click(screen.getByRole("button",{name:"Remove"}));
    const question=screen.getByRole("region",{name:"Remove Priya S.?"});expect(within(question).getByRole("button",{name:"Cancel"})).toHaveFocus();
    mounted.rerender(<RelationshipPane relationship={{...person,updated_at:"2026-11-11T03:15:00+00:00"}} {...props}/>);
    expect(screen.queryByRole("region",{name:"Remove Priya S.?"})).toBeNull();
    expect(vi.mocked(fetch).mock.calls.some(([,options])=>options?.method==="DELETE")).toBe(false);
  });
});

it("a quiet person read cannot clear a newer failed write or its draft",async()=>{
  const person=recorded("relationship-before").relationship;
  let reads=0,finish!:(response:Response)=>void;
  vi.stubGlobal("fetch",vi.fn(async(input:string,init?:RequestInit)=>{
    const path=String(input);
    if(path==="/api/people/readiness")return json(recorded("readiness"));
    if(path===`/api/people/relationships/${person.id}`){reads+=1;return reads===1?json(recorded("relationship-before")):new Promise<Response>(resolve=>{finish=resolve;});}
    if(path.endsWith("/one-on-ones"))return json(recorded("one-on-ones"));
    if(path.endsWith("/brief"))return json(recorded("brief"));
    if(path.endsWith("/notes")&&init?.method==="POST")return json({detail:"people_store_unavailable"},503);
    throw new Error(`No recorded read: ${path}`);
  }));
  render(<PersonWindowBody relationshipId={person.id}/>);
  await screen.findByTestId("people-composer");fireEvent.click(screen.getByRole("button",{name:"Note"}));
  const note=screen.getByRole("textbox",{name:"Note"});fireEvent.change(note,{target:{value:"Keep this note after the failed save."}});
  changedPerson();await waitFor(()=>expect(reads).toBe(2));
  fireEvent.click(screen.getByRole("button",{name:"Add"}));
  await within(screen.getByTestId("people-composer")).findByRole("alert");
  await act(async()=>finish(json(recorded("relationship-before"))));
  expect(within(screen.getByTestId("people-composer")).getByRole("alert")).toHaveTextContent("Could not do that");
  expect(note).toHaveValue("Keep this note after the failed save.");
  expect(screen.getByTestId("person-status")).toHaveTextContent("Failed");
});


it("an existing automation execution opens from the inspector without another send",async()=>{
  useDesk.setState({workbenchWindows:[]});
  const person=executionLinked.relationship.relationship;
  vi.stubGlobal("fetch",vi.fn(async(input:string,init?:RequestInit)=>{
    const reads:Record<string,unknown>={
      "/api/people/readiness":executionLinked.readiness,
      [`/api/people/relationships/${person.id}`]:executionLinked.relationship,
      [`/api/people/relationships/${person.id}/one-on-ones`]:executionLinked.sessions,
      [`/api/people/relationships/${person.id}/brief`]:executionLinked.brief,
      [`/api/people/commitments/${executionLinked.commitment_id}/execution`]:executionLinked.execution,
      "/api/workbenches":executionLinked.workbenches,
    };
    if(init?.method&&init.method!=="GET")throw new Error("Opening an existing execution must not send it again");
    if(!(String(input) in reads))throw new Error(`No recorded read: ${input}`);
    return json(reads[String(input)]);
  }));
  render(<PersonWindowBody relationshipId={person.id}/>);
  fireEvent.click(await screen.findByRole("row",{name:/Review the rollout plan before Friday/}));
  fireEvent.click(screen.getByRole("button",{name:"Open"}));
  const form=screen.getByTestId("people-commitment-inspector");
  expect(await within(form).findByRole("button",{name:"Open automation"})).toBeEnabled();
  fireEvent.click(within(form).getByRole("button",{name:"Open automation"}));
  expect(useDesk.getState().workbenchWindows.map(row=>row.id)).toContain(executionLinked.execution.items[0].workbench_id);
  const facts=screen.getByTestId("people-commitment-facts");
  expect(facts).toHaveTextContent("Prepare the rollout");
  expect(within(facts).getByText("Done",{exact:true})).toBeInTheDocument();
  expect(within(facts).getByText("The rollout brief is ready.").closest('[data-feedback-redact="true"]')).toBeTruthy();
  expect(within(form).queryByRole("button",{name:"Send to automation"})).toBeNull();
  expect(within(form).queryByRole("combobox",{name:"Automation"})).toBeNull();
  fireEvent.change(within(form).getByRole("combobox",{name:"Commitment action"}),{target:{value:"satisfy"}});
  expect(within(form).getByRole("textbox",{name:"Satisfaction note"})).toBeInTheDocument();
  expect(vi.mocked(fetch).mock.calls.some(([,options])=>options?.method==="POST")).toBe(false);
  await personView("1:1 brief");
  const last=await screen.findByTestId("prep-last");
  expect(last).toHaveTextContent("1 item");
  expect(last).not.toHaveTextContent("1 items");
});
