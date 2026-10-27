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
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { loadDeskWorkspace, useDesk } from "../store";
import { objectByRef } from "../world";
import { DecisionPullout } from "../pullouts/DecisionPullout";
import { MeetingDecideWell } from "../../meetings/MeetingDecideWell";
import { DeskReceiptRow } from "../components/DeskReceiptRow";
import { dismissWriteFailure } from "../hooks/useWriteReceipt";
import { keptEditorPatch } from "../pullouts/editors/editorDraft";

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
  if (url.startsWith("/api/channels/sends")) return Promise.resolve(json({ sends: [] }));
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
  if (one && method === "PUT") {
    hub.puts.push({ url, body });
    const decision = hub.decisions.find((d) => d.id === decodeURIComponent(one[1]));
    if (!decision) return Promise.resolve(json({ error: "Unknown decision" }, 404));
    const saved = { ...decision, ...body };
    hub.decisions = hub.decisions.map((d) => d.id === saved.id ? saved : d);
    return Promise.resolve(json({ decision: saved }));
  }
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
  dismissWriteFailure();
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

describe("the decision editor keeps its draft until the save is accepted", () => {
  const ref = "decision:body-decision";
  const path = "/api/decisions/body-decision";
  const initial = { context_markdown: "Current context", decision_markdown: "Current decision", consequences_markdown: "Current consequences" };

  async function renderEditor(beforeEdit?: () => Promise<void>) {
    hub.decisions = [decisionWire({ id: "body-decision", title: "Use the shared runners", ...initial })];
    await act(async () => { await useDesk.getState().refresh(); });
    function Face() {
      const items = useDesk((state) => state.items);
      const object = objectByRef(items, ref);
      return <>{object ? <DecisionPullout object={object} onClose={() => {}} /> : null}<DeskReceiptRow /></>;
    }
    const view = render(<Face />);
    if (beforeEdit) await beforeEdit();
    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    return { ...view, reopen: () => render(<Face />) };
  }

  function fillDraft(suffix: string) {
    for (const name of ["Background", "Decision", "Consequences"]) {
      fireEvent.change(screen.getByRole("textbox", { name }), { target: { value: `${name} ${suffix}` } });
    }
  }

  function expectDraft(suffix: string) {
    for (const name of ["Background", "Decision", "Consequences"]) {
      expect(screen.getByRole("textbox", { name })).toHaveValue(`${name} ${suffix}`);
    }
  }

  it("Save waits for one write and disables conflicting status, Retry and cancel presses", async () => {
    let complete!: () => void;
    let statusWrites = 0;
    vi.mocked(fetch).mockImplementation((input, init) => {
      if (String(input) === `${path}/status`) {
        statusWrites += 1;
        return Promise.resolve(json({ error: "state_refused" }, 403));
      }
      if (String(input) === path && init?.method === "PUT") {
        hub.puts.push({ url: path, body: JSON.parse(String(init.body)) });
        return new Promise((resolve) => { complete = () => {
          hub.decisions = [{ ...hub.decisions[0], ...hub.puts[0].body }];
          resolve(json({ decision: hub.decisions[0] }));
        }; });
      }
      return hubFetch(input, init);
    });
    // W1-TRUTH: the state changes by a toolbar verb (Accept on an open
    // decision), never a cycle at the top; a refused write keeps its Retry.
    await renderEditor(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Accept" }));
      await screen.findByText(/STATUS FAILED.*HTTP 403/);
    });
    fillDraft("to keep");
    const statusRetry = screen.getByRole("button", { name: "Retry" });
    expect(statusRetry).not.toBeDisabled();
    const done = screen.getByRole("button", { name: "Save" });
    act(() => { fireEvent.click(done); fireEvent.click(done); });
    expect(hub.puts).toHaveLength(1);
    expectDraft("to keep");
    expect(done).toBeDisabled();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();
    expect(statusRetry).toBeDisabled();
    fireEvent.click(statusRetry);
    expect(statusWrites).toBe(1);
    await act(async () => complete());
    await waitFor(() => expect(screen.queryByRole("textbox", { name: "Decision" })).toBeNull());
    expect(document.querySelector(".desk-decision-card")?.textContent).toContain("Decision to keep");
  });

  it("a refusal keeps all fields; the existing exact Retry cannot replace a newer draft", async () => {
    await renderEditor();
    fillDraft("refused");
    let refuse = true;
    vi.mocked(fetch).mockImplementation((input, init) => {
      if (String(input) === path && init?.method === "PUT" && refuse) {
        hub.puts.push({ url: path, body: JSON.parse(String(init.body)) });
        return Promise.resolve(json({ error: "save_refused" }, 403));
      }
      return hubFetch(input, init);
    });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await screen.findByText(/SAVE FAILED.*HTTP 403/);
    expectDraft("refused");
    await waitFor(() => expect(screen.getByRole("button", { name: "Save" })).not.toBeDisabled());
    expect(screen.getByText("Save failed")).toBeInTheDocument();
    fillDraft("typed later");
    refuse = false;
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(hub.puts).toHaveLength(2));
    expect(hub.puts[1].body).toEqual(hub.puts[0].body);
    expectDraft("typed later");
    await waitFor(() => expect(screen.queryByText("Save failed")).toBeNull());
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Save" })); });
    expect(hub.puts.at(-1)?.body.decision_markdown).toBe("Decision typed later");
    expect(screen.queryByRole("textbox", { name: "Decision" })).toBeNull();
  });

  it("a successful older save keeps fields typed while it was pending", async () => {
    await renderEditor();
    fillDraft("submitted");
    let complete!: () => void;
    vi.mocked(fetch).mockImplementation((input, init) => {
      if (String(input) === path && init?.method === "PUT") {
        const body = JSON.parse(String(init.body));
        hub.puts.push({ url: path, body });
        return new Promise((resolve) => { complete = () => {
          hub.decisions = [{ ...hub.decisions[0], ...body }];
          resolve(json({ decision: hub.decisions[0] }));
        }; });
      }
      return hubFetch(input, init);
    });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expectDraft("submitted");
    fillDraft("typed later");
    await act(async () => complete());
    expectDraft("typed later");
    expect(screen.getByRole("button", { name: "Save" })).not.toBeDisabled();
    expect(useDesk.getState().items.decision.find((d) => d.id === "body-decision")?.decisionMarkdown).toBe("Decision submitted");
  });

  it("close and reload restore this object's draft, including emptied fields, without a write", async () => {
    const face = await renderEditor();
    fillDraft("after reopening");
    fireEvent.change(screen.getByRole("textbox", { name: "Consequences" }), { target: { value: "" } });
    face.unmount();
    // Rehydrate the same workspace document a fresh page loads.
    useDesk.setState({ drafts: loadDeskWorkspace().drafts ?? {}, newIds: [] });
    face.reopen();
    expect(screen.getByRole("textbox", { name: "Decision" })).toHaveValue("Decision after reopening");
    expect(screen.getByRole("textbox", { name: "Background" })).toHaveValue("Background after reopening");
    expect(screen.getByLabelText("Consequences")).toHaveValue("");
    expect(screen.getByText("Draft kept")).toBeInTheDocument();
    expect(hub.puts).toEqual([]);
  });

  it("Cancel discards only this object's retained fields; reopening reads the saved document", async () => {
    const face = await renderEditor();
    fillDraft("cancelled");
    useDesk.getState().setDraft("editor/decision/another-decision", JSON.stringify({ decision_markdown: "Other work" }));
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(keptEditorPatch("decision", "body-decision")).toEqual({});
    expect(keptEditorPatch("decision", "another-decision").decision_markdown).toBe("Other work");
    face.unmount();
    face.reopen();
    expect(screen.queryByRole("textbox", { name: "Decision" })).toBeNull();
    expect(screen.getByText("Current decision")).toBeInTheDocument();
    expect(hub.puts).toEqual([]);
  });

  it("an acknowledged current Save clears its retained fields and returns to the saved document", async () => {
    const face = await renderEditor();
    fillDraft("saved");
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Save" })); });
    expect(keptEditorPatch("decision", "body-decision")).toEqual({});
    expect(screen.getByText("Saved")).toBeInTheDocument();
    face.unmount();
    face.reopen();
    expect(screen.queryByRole("textbox", { name: "Decision" })).toBeNull();
    expect(screen.getByText("Decision saved")).toBeInTheDocument();
  });

  it("a late Save from a closed window cannot erase newer words in the reopened editor", async () => {
    const face = await renderEditor();
    fillDraft("submitted");
    let complete!: () => void;
    vi.mocked(fetch).mockImplementation((input, init) => {
      if (String(input) === path && init?.method === "PUT") {
        const body = JSON.parse(String(init.body));
        hub.puts.push({ url: path, body });
        return new Promise((resolve) => { complete = () => {
          hub.decisions = [{ ...hub.decisions[0], ...body }];
          resolve(json({ decision: hub.decisions[0] }));
        }; });
      }
      return hubFetch(input, init);
    });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    face.unmount();
    const reopened = face.reopen();
    fireEvent.change(screen.getByRole("textbox", { name: "Decision" }), { target: { value: "Newer reopened words" } });
    await act(async () => complete());
    expect(screen.getByRole("textbox", { name: "Decision" })).toHaveValue("Newer reopened words");
    expect(keptEditorPatch("decision", "body-decision")).toEqual({ decision_markdown: "Newer reopened words" });
    reopened.unmount();
    face.reopen();
    expect(screen.getByRole("textbox", { name: "Decision" })).toHaveValue("Newer reopened words");
    expect(hub.puts).toHaveLength(1);
  });
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
      ["Background"]],
    ["context-and-decision", {
      title: "Move the nightly build to the shared runners",
      context_markdown: "Our own runners are full every night. The shared runner pool has spare capacity after 8 PM.",
      decision_markdown: "Move the nightly build to the shared runners.",
    }, ["Background"]],
  ];
  const heads = () =>
    // The decision's own headings. W1-TRUTH (reader grammar): the decision
    // text reads with no "Decision" heading over it; a support field is a
    // fold only when it has text.
    Array.from(document.querySelectorAll(".desk-decision-reader > .gadget-fold > summary > .gadget-fold-title"))
      .map((h) => (h.textContent ?? "").trim()).filter((label) => label !== "State");

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

  it("writing starts in Decision; support folds keep their drafts when closed", () => {
    const object = objectByRef(useDesk.getState().items, "decision:decision_title-only");
    render(<DecisionPullout object={object!} onClose={() => {}} />);
    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    expect(screen.getByRole("textbox", { name: "Decision" })).toHaveFocus();
    const context = screen.getByText("Background", { selector: ".gadget-fold-title" });
    const consequences = screen.getByText("Consequences", { selector: ".gadget-fold-title" });
    expect(context.closest("details")).not.toHaveAttribute("open");
    expect(consequences.closest("details")).not.toHaveAttribute("open");
    expect(screen.getByLabelText("Background")).toHaveValue("");
    fireEvent.click(context);
    fireEvent.change(screen.getByRole("textbox", { name: "Background" }), { target: { value: "A reason to retain" } });
    fireEvent.click(context);
    expect(context.closest("details")).not.toHaveAttribute("open");
    expect(screen.getByLabelText("Background")).toHaveValue("A reason to retain");
    fireEvent.click(context);
    expect(screen.getByRole("textbox", { name: "Background" })).toHaveValue("A reason to retain");
    expect(hub.puts).toHaveLength(0);
  });

  it("populated support opens beside the primary decision when editing", () => {
    const object = objectByRef(useDesk.getState().items, "decision:decision_context-and-decision");
    render(<DecisionPullout object={object!} onClose={() => {}} />);
    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    expect(screen.getByRole("textbox", { name: "Decision" })).toHaveFocus();
    expect(screen.getByText("Background", { selector: ".gadget-fold-title" }).closest("details")).toHaveAttribute("open");
    expect(screen.getByRole("textbox", { name: "Background" })).toHaveValue("Our own runners are full every night. The shared runner pool has spare capacity after 8 PM.");
    expect(screen.getByText("Consequences", { selector: ".gadget-fold-title" }).closest("details")).not.toHaveAttribute("open");
  });

  it("Edit on a title-only decision still offers all three fields", () => {
    const object = objectByRef(useDesk.getState().items, "decision:decision_title-only");
    render(<DecisionPullout object={object!} onClose={() => {}} />);
    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    for (const name of ["Background", "Decision", "Consequences"]) {
      expect(screen.getByLabelText(name, { selector: "textarea" })).toBeTruthy();
    }
  });
});

describe("the decision window chooses a named state", () => {
  // W1-TRUTH (atlas 2026-10-27): the state is a dot and a word in the status
  // bar, and it changes by one toolbar verb (Accept, Retire), never a cycle.
  async function renderDecision() {
    hub.decisions = [decisionWire({ id: "state-decision", title: "Use the shared runners", status: "accepted" })];
    await act(async () => { await useDesk.getState().refresh(); });
    function Face() {
      const items = useDesk((state) => state.items);
      const object = objectByRef(items, "decision:state-decision");
      return object ? <DecisionPullout object={object} onClose={() => {}} /> : null;
    }
    render(<Face />);
  }
  const stateText = () => screen.getByTestId("desk-decision-state").textContent ?? "";

  it("reading the state writes nothing; a chosen state renders only after success", async () => {
    await renderDecision();
    expect(screen.queryByRole("combobox", { name: "Decision status" })).toBeNull();
    expect(stateText()).toContain("Accepted");
    expect(hub.puts).toHaveLength(0);
    let complete!: () => void;
    vi.mocked(fetch).mockImplementation((input, init) => {
      if (String(input).endsWith("/status")) {
        hub.puts.push({ url: String(input), body: JSON.parse(String(init?.body)) });
        return new Promise((resolve) => { complete = () => {
          hub.decisions = [{ ...hub.decisions[0], status: "deprecated" }];
          resolve(json({ decision: hub.decisions[0] }));
        }; });
      }
      return hubFetch(input, init);
    });
    const retire = screen.getByRole("button", { name: "Retire" });
    fireEvent.click(retire);
    expect(stateText()).toContain("Saving");
    expect(retire).toBeDisabled();
    fireEvent.click(retire);
    expect(hub.puts).toHaveLength(1);
    await act(async () => complete());
    await waitFor(() => expect(stateText()).toContain("Retired"));
  });

  it("a refused status keeps the old state and Retry repeats the exact choice", async () => {
    await renderDecision();
    let refuse = true;
    vi.mocked(fetch).mockImplementation((input, init) => {
      if (String(input).endsWith("/status")) {
        const body = JSON.parse(String(init?.body));
        hub.puts.push({ url: String(input), body });
        if (refuse) return Promise.resolve(json({ error: "state_refused" }, 403));
        hub.decisions = [{ ...hub.decisions[0], status: body.status }];
        return Promise.resolve(json({ decision: hub.decisions[0] }));
      }
      return hubFetch(input, init);
    });
    fireEvent.click(screen.getByRole("button", { name: "Retire" }));
    expect(await screen.findByText(/STATUS FAILED.*HTTP 403/)).toBeInTheDocument();
    expect(stateText()).toContain("Accepted");
    refuse = false;
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(stateText()).toContain("Retired"));
    expect(hub.puts.map((put) => put.body)).toEqual([{ status: "deprecated" }, { status: "deprecated" }]);
  });
});
