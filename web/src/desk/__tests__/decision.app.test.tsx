/* The Decision app, rendered over the hub's wire (the test diet, 2026-10-11).
 *
 * Two browser rigs move here: Decide in a meeting (PHILO-13-08) and the
 * decision window's headings (PHILO-8-04). The real well (MeetingDecideWell),
 * the real decision window (DecisionPullout), the real desk store, the real
 * `lib/api` and wire adapters run; only `fetch` is replaced. Its bodies are
 * the hub's own shapes, never invented (SCAR LAW):
 *   - a decision: `DecisionRecord.to_dict` (holdspeak/db/models/__init__.py:609);
 *     `POST /api/decisions` answers `{decision}` with 201
 *     (holdspeak/web/routes/primitives/decisions.py:95), `GET /api/decisions`
 *     `{decisions}`, `GET /api/decisions/{id}` `{decision}`;
 *   - a meeting's projects: `ProjectsRepository.get_meeting_projects`
 *     (holdspeak/db/projects.py:251) under `{projects}`
 *     (holdspeak/web/routes/projects.py:434).
 *
 * The hub half (the decision saved with its meeting and project) is
 * tests/integration/test_desk_meetings.py. Already fenced in vitest, so not
 * repeated here (web/src/desk/__tests__/philo1308Decide.test.tsx):
 *   - abandoned tries write nothing: "Cancel abandons: nothing is written",
 *     "an abandoned try (the palette closes) leaves no record";
 *   - a named New Decision opens its window: "type + Enter creates one
 *     decision with that title and opens it";
 *   - the draft stays with its meeting: "a title typed under A never files
 *     under B; back on A it is A's again".
 */
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useDesk } from "../store";
import { objectByRef } from "../world";
import { DecisionPullout } from "../pullouts/DecisionPullout";
import { MeetingDecideWell } from "../../meetings/MeetingDecideWell";

type Wire = Record<string, unknown>;

/** DecisionRecord.to_dict (holdspeak/db/models/__init__.py:609-631). */
const decisionWire = (fields: Wire): Wire => ({
  id: "", title: "", status: "proposed", deciders: [], decided_at: null,
  context_markdown: "", decision_markdown: "", alternatives: [], consequences_markdown: "",
  superseded_by: null, tags: [], created_at: "2026-10-01T09:31:00", updated_at: "2026-10-01T09:31:00",
  deleted: false, ...fields,
});

const hub = {
  decisions: [] as Wire[],
  meetingProjects: {} as Record<string, Wire[]>,
  posts: [] as Wire[],
  puts: [] as Array<{ url: string; body: Wire }>,
};

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });

function hubFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const url = String(input);
  const method = (init?.method ?? "GET").toUpperCase();
  const body = init?.body ? (JSON.parse(String(init.body)) as Wire) : {};
  if (url === "/api/decisions" && method === "POST") {
    hub.posts.push(body);
    const decision = decisionWire({
      id: `decision_${hub.posts.length}`, title: body.title, status: body.status ?? "proposed",
      context_markdown: body.context_markdown ?? "", tags: body.tags ?? [],
    });
    hub.decisions = [...hub.decisions, decision];
    return Promise.resolve(json({ decision }, 201));
  }
  if (url === "/api/decisions") return Promise.resolve(json({ decisions: hub.decisions }));
  const one = /^\/api\/decisions\/([^/?]+)$/.exec(url);
  if (one && method === "GET") {
    const decision = hub.decisions.find((d) => d.id === decodeURIComponent(one[1]));
    return Promise.resolve(decision ? json({ decision }) : json({ error: "Unknown decision" }, 404));
  }
  const projects = /^\/api\/meetings\/([^/]+)\/projects$/.exec(url);
  if (projects) return Promise.resolve(json({ projects: hub.meetingProjects[decodeURIComponent(projects[1])] ?? [] }));
  if (url.startsWith("/api/projects/") && method === "PUT") {
    hub.puts.push({ url: decodeURIComponent(url), body });
    return Promise.resolve(json({}));
  }
  return Promise.resolve(json({}));
}

beforeEach(() => {
  hub.decisions = [];
  hub.posts = [];
  hub.puts = [];
  // get_meeting_projects rows (holdspeak/db/projects.py:265-273).
  hub.meetingProjects = {
    "p13-checkout": [{
      project_id: "proj-checkout", project_name: "Checkout", source: "manual",
      confidence: 1.0, detected_at: "2026-10-01T09:00:00",
    }],
  };
  vi.stubGlobal("fetch", vi.fn(hubFetch));
  useDesk.setState({ pullouts: [], editingId: null, newIds: [] });
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Decide in a meeting: Decide -> name -> receipt -> the decision window", () => {
  /* replaces: tests/e2e/test_philo13_08_decide_glass.py::TestDecideGlass::test_decide_in_the_meetings_record (T2 half)
   * replaces: tests/e2e/test_philo13_08_decide_glass.py::TestDecideGlass::test_decide_in_the_meeting_window_and_abandoned_tries (T2 half) */
  it("two gestures make one decision with its meeting and project; its row opens its own window", async () => {
    render(
      <MeetingDecideWell meetingId="p13-checkout" title="Checkout latency review"
        startedAt="2026-10-01T09:00:00" summary="p99 doubled after the cache change." />,
    );
    // Gesture 1: Decide. (That the well takes the focus is a real-browser
    // fact: in jsdom the well is not the active element. It stays with the glass.)
    fireEvent.click(screen.getByRole("button", { name: "Decide" }));
    const title = screen.getByRole("textbox", { name: "Decision title" });
    expect(hub.posts).toEqual([]);

    // Gesture 2: type the title and press Enter.
    fireEvent.change(title, { target: { value: "Roll back the cache change" } });
    await act(async () => { fireEvent.keyDown(title, { key: "Enter" }); });
    await waitFor(() => expect(hub.posts).toHaveLength(1));
    expect(hub.posts[0]).toMatchObject({
      title: "Roll back the cache change",
      status: "accepted",
      tags: ["meeting:p13-checkout", "project:proj-checkout"],
    });
    expect(String(hub.posts[0].context_markdown)).toMatch(/^Meeting: Checkout latency review · 2026-10-01/);
    expect(hub.puts).toEqual([{
      url: "/api/projects/proj-checkout/resources/desk_decision:decision_1",
      body: { relationship: "member" },
    }]);

    // The receipt is in the meeting, on the decision's row (read back from the hub).
    await waitFor(() => expect(screen.getByTestId("decide-receipt").textContent).toMatch(/^✓ DECIDED \d\d:\d\d$/));
    expect(screen.queryByRole("textbox", { name: "Decision title" })).toBeNull();

    // The row opens the decision in its own window.
    const row = screen.getByRole("button", { name: /Roll back the cache change/ });
    await act(async () => { fireEvent.click(row); });
    await waitFor(() => expect(useDesk.getState().pullouts.map((p) => p.id)).toContain("decision:decision_1"));
  });

  it("a meeting with no project files the decision under its meeting only", async () => {
    render(<MeetingDecideWell meetingId="p13-hiring" title="Hiring debrief" startedAt="2026-09-30T14:00:00" />);
    fireEvent.click(screen.getByRole("button", { name: "Decide" }));
    fireEvent.change(screen.getByRole("textbox", { name: "Decision title" }), { target: { value: "Typed under B" } });
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Save" })); });
    await waitFor(() => expect(hub.posts).toHaveLength(1));
    expect(hub.posts[0].tags).toEqual(["meeting:p13-hiring"]);
    expect(hub.puts).toEqual([]);
    await waitFor(() => expect(screen.getByTestId("decide-receipt")).toBeTruthy());
  });
});

describe("the decision window shows a heading only with text under it", () => {
  /* replaces: tests/e2e/test_philo8_04_empty_decision_heads_glass.py::TestEmptyDecisionHeadsGlass::test_a_heading_shows_only_with_text_under_it
   * The decisions come from the hub's wire through the store's own adapter
   * (fromWireDecision), so the fields the window reads are the real ones. */
  const CASES: Array<[string, Wire, string[]]> = [
    ["title-only", { title: "Glass title only decision" }, []],
    ["context-only", { title: "Glass context only decision", context_markdown: "Our own runners are full every night." },
      ["Decision context"]],
    ["context-and-decision", {
      title: "Move the nightly build to the shared runners",
      context_markdown: "Our own runners are full every night. The shared runner pool has spare capacity after 8 PM.",
      decision_markdown: "Move the nightly build to the shared runners.",
    }, ["Decision context", "Decision"]],
  ];
  const heads = () =>
    // The decision's own headings (its SEND well carries its own head).
    Array.from(document.querySelectorAll(".desk-decision-card h3"))
      .filter((h) => !h.closest("[data-send]")).map((h) => (h.textContent ?? "").trim());

  beforeEach(async () => {
    hub.decisions = CASES.map(([slug, fields]) => decisionWire({ id: `decision_${slug}`, ...fields }));
    await act(async () => { await useDesk.getState().refresh(); });
  });

  for (const [slug, , want] of CASES) {
    it(`${slug}: headings ${JSON.stringify(want)}`, () => {
      const object = objectByRef(useDesk.getState().items, `decision:decision_${slug}`);
      expect(object).not.toBeNull();
      render(<DecisionPullout object={object!} onClose={() => {}} />);
      expect(heads()).toEqual(want);
    });
  }

  it("Edit on a title-only decision still offers all three fields", () => {
    const object = objectByRef(useDesk.getState().items, "decision:decision_title-only");
    render(<DecisionPullout object={object!} onClose={() => {}} />);
    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    for (const name of ["Context", "Decision", "Consequences"]) {
      expect(screen.getByRole("textbox", { name })).toBeTruthy();
    }
  });
});
