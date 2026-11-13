/* The Decision app, rendered over the hub's wire (the test diet, 2026-10-11).
 *
 * The one decision face (2026-11-08): every decision ref opens its record in
 * the Decisions window reader, and a Desk decision is accepted, retired,
 * edited, copied and filed there. The Decision pullout is parked
 * (pullouts/_parked/DecisionPullout.tsx; its cases in
 * pullouts/_parked/__tests__/decisionPullout.app.test.tsx). The real well
 * (MeetingDecideWell), the real Decisions app (DecisionsCore), the real desk store,
 * the real `lib/api` and wire adapters run; only `fetch` is replaced. Its
 * bodies are the hub's own shapes, never invented (SCAR LAW):
 *   - a decision: `DecisionRecord.to_dict` (holdspeak/db/models/__init__.py:609);
 *     `POST /api/decisions` answers `{decision}` with 201
 *     (holdspeak/web/routes/primitives/decisions.py:95), `GET /api/decisions`
 *     `{decisions}`, `GET /api/decisions/{id}` `{decision}`;
 *   - a record: `DecisionRecordService._decorate` over the record row
 *     (holdspeak/services/decision_record_service.py): a Desk source's
 *     status and title, `rationale` = Background then Consequences
 *     (`create_from_desk`), `GET /api/decision-records/{id}`,
 *     `GET /api/decision-records/source/{type}/{id}` a list;
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
import { useLayoutEffect } from "react";
import { readdirSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { loadDeskWorkspace, useDesk } from "../store";
import { seatMounted, seatUnmounted } from "../deleteSeat";
import { OBJECT_DELETE_REQUEST } from "../verbRegistry";
import { DecisionsCore } from "../../pages/cores/DecisionsCore";
import { PULLOUT_CONTENT } from "../pullouts/registry";
import { DecisionToReader } from "../pullouts/DecisionToReader";
import { openRef } from "../openObject";
import { MeetingDecideWell } from "../../meetings/MeetingDecideWell";
import { DeskReceiptRow } from "../components/DeskReceiptRow";
import { dismissWriteFailure } from "../hooks/useWriteReceipt";
import { keptEditorPatch } from "../pullouts/editors/editorDraft";
import { DeskDecisionEditor, useDeskDecisionEdit } from "../pullouts/views/DeskDecisionEdit";
import { CLOCK } from "../../test/clock";

type Wire = Record<string, unknown>;

// The reader re-reads on the desk's change frames; one bus for the file.
vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ subscribe: () => () => undefined }),
}));

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
  /** HS-S42: canonical records per source decision id; `fail` answers 500. */
  records: {} as Record<string, Wire[] | "fail">,
  /** Meeting decisions (`decisions` lifecycle rows) by id, and their records. */
  meetingDecisions: {} as Record<string, Wire>,
  meetingRecords: {} as Record<string, Wire[]>,
  relationships: {} as Record<string, Wire[]>,
};

/** The record of a Desk decision, as the hub reads it back. */
const recordId = (deskId: string) => `record-of-${deskId}`;
const recordWire = (decision: Wire): Wire => ({
  id: recordId(String(decision.id)),
  title: decision.title || null,
  decision_text: String(decision.decision_markdown || "").trim() || String(decision.title || ""),
  rationale: [decision.context_markdown, decision.consequences_markdown].map((part) => String(part || "").trim()).filter(Boolean).join("\n\n") || null,
  alternatives: null, owner: null, review_date: null, lifecycle: "active",
  status: decision.status, source_type: "desk", source_id: decision.id,
  created_at: "2026-10-01T09:31:00", sources: [], work: [], revisions: [],
});

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
  // HS-S42: the canonical producer answers `{decision, record}` with 201
  // (holdspeak/web/routes/decision_records.py, from_desk); the source
  // decision carries the project and meeting tags.
  if (url === "/api/decision-records/from-desk" && method === "POST") {
    hub.posts.push(body);
    const tags = [
      ...(body.project_id ? [`project:${body.project_id}`] : []),
      ...(body.meeting_id ? [`meeting:${body.meeting_id}`] : []),
    ];
    const decision = decisionWire({
      id: `decision_${hub.posts.length}`, title: body.title, status: body.status ?? "accepted", tags,
      context_markdown: body.project_name ? `About: ${body.project_name}` : "",
      consequences_markdown: body.why ? `Why: ${body.why}` : "",
    });
    hub.decisions = [...hub.decisions, decision];
    // One decision writer (2026-11-08): the hub files the record in the
    // Project in the same call; the record names it.
    const record = { id: `rec_${hub.posts.length}`, source_type: "desk", source_id: decision.id, project_id: body.project_id ?? null };
    hub.records[String(decision.id)] = [record];
    if (body.project_id) hub.relationships[`decision_record:${record.id}`] = [{ project_id: body.project_id, resource_ref: `decision_record:${record.id}`, relationship: "member" }];
    return Promise.resolve(json({ decision, record }, 201));
  }
  const bySource = /^\/api\/decision-records\/source\/desk\/([^/?]+)$/.exec(url);
  if (bySource) {
    const id = decodeURIComponent(bySource[1]);
    // Every Desk decision has its record (primitive_service create_decision
    // and update_decision `sync_from_desk`).
    const records = hub.records[id] ?? (hub.decisions.some((d) => d.id === id) ? [{ id: recordId(id) }] : []);
    return Promise.resolve(records === "fail" ? json({ error: "boom" }, 500) : json(records));
  }
  const byMeeting = /^\/api\/decision-records\/source\/meeting\/([^/?]+)$/.exec(url);
  if (byMeeting) return Promise.resolve(json(hub.meetingRecords[decodeURIComponent(byMeeting[1])] ?? []));
  const record = /^\/api\/decision-records\/(record-of-[^/?]+)$/.exec(url);
  if (record && method === "GET") {
    const id = decodeURIComponent(record[1]).slice("record-of-".length);
    const decision = hub.decisions.find((d) => d.id === id);
    return Promise.resolve(decision ? json(recordWire(decision)) : json({ detail: "decision record not found" }, 404));
  }
  const rel = /^\/api\/desk\/relationships\/(.+)$/.exec(url);
  if (rel) {
    const ref = decodeURIComponent(rel[1]);
    return Promise.resolve(json({ resource_ref: ref, zone: null, knowledge: [], projects: hub.relationships[ref] ?? [] }));
  }
  if (url === "/api/projects" && method === "GET") return Promise.resolve(json({ projects: [{ id: "proj-checkout", name: "Checkout" }] }));
  if (url === "/api/kbs") return Promise.resolve(json({ kbs: [] }));
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
    const meeting = hub.meetingDecisions[decodeURIComponent(one[1])];
    if (meeting) return Promise.resolve(json({ decision: meeting }));
    const decision = hub.decisions.find((d) => d.id === decodeURIComponent(one[1]));
    return Promise.resolve(decision ? json({ decision }) : json({ error: "Unknown decision" }, 404));
  }
  const projects = /^\/api\/meetings\/([^/]+)\/projects$/.exec(url);
  if (projects) return Promise.resolve(json({ projects: hub.meetingProjects[decodeURIComponent(projects[1])] ?? [] }));
  if (url.startsWith("/api/projects/") && method === "PUT") {
    const path = decodeURIComponent(url);
    hub.puts.push({ url: path, body });
    const [, , , projectId, , ref] = path.split("/");
    hub.relationships[ref] = [{ project_id: projectId, resource_ref: ref, relationship: body.relationship ?? "member" }];
    return Promise.resolve(json({ resource: { project_id: projectId, resource_ref: ref, relationship: body.relationship ?? "member" } }));
  }
  return Promise.resolve(json({}));
}

beforeEach(() => {
  dismissWriteFailure();
  hub.decisions = [];
  hub.posts = [];
  hub.puts = [];
  hub.records = {};
  hub.meetingDecisions = {};
  hub.meetingRecords = {};
  hub.relationships = {};
  // get_meeting_projects rows (holdspeak/db/projects.py:265-273).
  hub.meetingProjects = {
    "p13-checkout": [{
      project_id: "proj-checkout", project_name: "Checkout", source: "manual",
      confidence: 1.0, detected_at: "2026-10-01T09:00:00",
    }],
  };
  vi.stubGlobal("fetch", vi.fn(hubFetch));
  useDesk.setState({ pullouts: [], editingId: null, newIds: [], windowsById: {} } as never);
});

/** The reader on one Desk decision's record, with the desk's receipt line. */
function Reader({ deskId }: { deskId: string }) {
  return <><DecisionsCore scope={`record:${recordId(deskId)}`} /><DeskReceiptRow /></>;
}
const stateText = () => screen.queryByTestId("decision-reader-state")?.textContent ?? "";

describe("every decision ref opens its record in the Decisions window reader", () => {
  // The one decision face (2026-11-08). Red on main: `decision:<desk id>` and
  // `desk_decision:<desk id>` opened the Decision pullout (openObject.ts
  // openSourceRef), a second face of the same decision.
  const scope = () => useDesk.getState().windowsById["surface-decisions"]?.scope;
  beforeEach(async () => {
    hub.decisions = [decisionWire({ id: "d1", title: "Use the shared runners" })];
    await act(async () => { await useDesk.getState().refresh(); });
  });

  for (const ref of ["decision:d1", "desk_decision:d1"]) {
    it(`${ref} opens record:<its record> in the Decisions window, never a pullout`, async () => {
      await act(async () => { openRef(ref); });
      await waitFor(() => expect(scope()).toBe("record:record-of-d1"));
      expect(useDesk.getState().pullouts).toEqual([]);
    });
  }

  it("a Desk decision opened as a desk object (openPullout) opens its record too", async () => {
    await act(async () => { useDesk.getState().openPullout("decision:d1"); });
    await waitFor(() => expect(scope()).toBe("record:record-of-d1"));
    expect(useDesk.getState().pullouts).toEqual([]);
  });

  it("decision:<meeting decision> opens that decision's record", async () => {
    hub.meetingDecisions = { "m-dec": { id: "m-dec", text: "Cut the release on Friday", source_meeting_id: "m1" } };
    hub.meetingRecords = { "m-dec": [{ id: "rec-m" }] };
    await act(async () => { openRef("decision:m-dec"); });
    await waitFor(() => expect(scope()).toBe("record:rec-m"));
    expect(useDesk.getState().pullouts).toEqual([]);
  });

  it("the pullout registry holds no Decision pullout: a decision window opens the reader and closes", async () => {
    expect(PULLOUT_CONTENT.decision).toBe(DecisionToReader);
    const onClose = vi.fn();
    const object = { id: "d1", kind: "decision", title: "Use the shared runners" } as never;
    await act(async () => { render(<DecisionToReader object={object} onClose={onClose} />); });
    expect(onClose).toHaveBeenCalled();
    await waitFor(() => expect(scope()).toBe("record:record-of-d1"));
  });

  it("no live file imports the parked Decision pullout", () => {
    const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
    const live: string[] = [];
    const walk = (folder: string) => {
      for (const entry of readdirSync(folder, { withFileTypes: true })) {
        const path = join(folder, entry.name);
        if (entry.isDirectory()) { if (entry.name !== "_parked" && entry.name !== "node_modules") walk(path); continue; }
        if (!/\.(ts|tsx)$/.test(entry.name) || path === fileURLToPath(import.meta.url)) continue;
        if (/from\s+["'][^"']*\/DecisionPullout["']|import\(["'][^"']*\/DecisionPullout["']\)/.test(readFileSync(path, "utf8"))) live.push(path);
      }
    };
    walk(root);
    expect(live).toEqual([]);
  });
});

describe("the reader's editor keeps its draft until the save is accepted", () => {
  const deskId = "body-decision";
  const path = "/api/decisions/body-decision";
  const initial = { context_markdown: "Current context", decision_markdown: "Current decision", consequences_markdown: "Current consequences" };

  async function renderEditor() {
    hub.decisions = [decisionWire({ id: deskId, title: "Use the shared runners", ...initial })];
    await act(async () => { await useDesk.getState().refresh(); });
    const view = render(<Reader deskId={deskId} />);
    fireEvent.click(await screen.findByTestId("decision-reader-edit"));
    await screen.findByRole("textbox", { name: "Decision" });
    return { ...view, reopen: () => render(<Reader deskId={deskId} />) };
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

  it("an edit started as the record arrives is not lost to its identity reset", async () => {
    hub.decisions = [decisionWire({ id: deskId, title: "Use the shared runners", ...initial })];
    function ArrivingRecord({ id }: { id: string }) {
      const edit = useDeskDecisionEdit(id, () => undefined);
      // Start at commit, before passive effects: a press must belong to
      // the record the controls already show, even when it just arrived.
      useLayoutEffect(() => { if (id) void edit.start(); }, [id]);
      return edit.editing ? <DeskDecisionEditor edit={edit} /> : <span>Reading</span>;
    }
    const face = render(<ArrivingRecord id="" />);
    face.rerender(<ArrivingRecord id={deskId} />);
    expect(await screen.findByRole("textbox", { name: "Decision" })).toHaveValue(initial.decision_markdown);
    fillDraft("kept");
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Save" })); });
    expect(hub.puts).toHaveLength(1);
    expect(hub.puts[0].body.decision_markdown).toBe("Decision kept");
  });

  it("Save waits for one write and disables Save and Cancel; the reader then reads the saved words", async () => {
    let complete!: () => void;
    vi.mocked(fetch).mockImplementation((input, init) => {
      if (String(input) === path && init?.method === "PUT") {
        hub.puts.push({ url: path, body: JSON.parse(String(init.body)) });
        return new Promise((resolve) => { complete = () => {
          hub.decisions = [{ ...hub.decisions[0], ...hub.puts[0].body }];
          resolve(json({ decision: hub.decisions[0] }));
        }; });
      }
      return hubFetch(input, init);
    });
    await renderEditor();
    // An open editor hides the state verbs: one write at a time.
    expect(screen.queryByTestId("decision-reader-accept")).toBeNull();
    fillDraft("to keep");
    const done = screen.getByRole("button", { name: "Save" });
    act(() => { fireEvent.click(done); fireEvent.click(done); });
    expect(hub.puts).toHaveLength(1);
    expectDraft("to keep");
    expect(done).toBeDisabled();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();
    await act(async () => complete());
    await waitFor(() => expect(screen.queryByRole("textbox", { name: "Decision" })).toBeNull());
    await waitFor(() => expect(screen.getByTestId("decision-reader").textContent).toContain("Decision to keep"));
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
    await screen.findByText("Could not save the decision");
    expectDraft("refused");
    await waitFor(() => expect(screen.getByRole("button", { name: "Save" })).not.toBeDisabled());
    expect(screen.getByText("Save failed")).toBeInTheDocument();
    fillDraft("typed later");
    refuse = false;
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
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
    expect(useDesk.getState().items.decision.find((d) => d.id === deskId)?.decisionMarkdown).toBe("Decision submitted");
  });

  it("close and reload restore this object's draft, including emptied fields, without a write", async () => {
    const face = await renderEditor();
    fillDraft("after reopening");
    fireEvent.change(screen.getByRole("textbox", { name: "Consequences" }), { target: { value: "" } });
    face.unmount();
    // Rehydrate the same workspace document a fresh page loads.
    useDesk.setState({ drafts: loadDeskWorkspace().drafts ?? {}, newIds: [] });
    face.reopen();
    expect(await screen.findByRole("textbox", { name: "Decision" })).toHaveValue("Decision after reopening");
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
    expect(keptEditorPatch("decision", deskId)).toEqual({});
    expect(keptEditorPatch("decision", "another-decision").decision_markdown).toBe("Other work");
    face.unmount();
    face.reopen();
    expect(await screen.findByText("Current decision")).toBeInTheDocument();
    expect(screen.queryByRole("textbox", { name: "Decision" })).toBeNull();
    expect(hub.puts).toEqual([]);
  });

  it("an acknowledged current Save clears its retained fields and returns to the saved document", async () => {
    const face = await renderEditor();
    fillDraft("saved");
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Save" })); });
    expect(keptEditorPatch("decision", deskId)).toEqual({});
    expect(screen.getByText("Saved")).toBeInTheDocument();
    face.unmount();
    face.reopen();
    expect(await screen.findByText("Decision saved")).toBeInTheDocument();
    expect(screen.queryByRole("textbox", { name: "Decision" })).toBeNull();
  });

  it("a late Save from a closed reader cannot erase newer words in the reopened editor", async () => {
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
    fireEvent.change(await screen.findByRole("textbox", { name: "Decision" }), { target: { value: "Newer reopened words" } });
    await act(async () => complete());
    expect(screen.getByRole("textbox", { name: "Decision" })).toHaveValue("Newer reopened words");
    expect(keptEditorPatch("decision", deskId)).toEqual({ decision_markdown: "Newer reopened words" });
    reopened.unmount();
    face.reopen();
    expect(await screen.findByRole("textbox", { name: "Decision" })).toHaveValue("Newer reopened words");
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
    // HS-S42: the one linked project is shown and chosen before Save.
    await waitFor(() => expect(screen.getByRole("button", { name: "Checkout" })).toHaveAttribute("aria-pressed", "true"));

    // Gesture 2: type the title and press Enter.
    fireEvent.change(title, { target: { value: "Roll back the cache change" } });
    await act(async () => { fireEvent.keyDown(title, { key: "Enter" }); });
    await waitFor(() => expect(hub.posts).toHaveLength(1));
    expect(hub.posts[0]).toMatchObject({
      title: "Roll back the cache change",
      status: "accepted",
      meeting_id: "p13-checkout",
      project_id: "proj-checkout",
    });
    expect(String(hub.posts[0].why)).toMatch(/^Meeting: Checkout latency review · 2026-10-01/);
    // One decision writer (2026-11-08): the hub filed it in that call; the
    // client makes no second write.
    expect(hub.puts).toEqual([]);

    // The receipt is in the meeting, on the decision's row (read back from the hub).
    await waitFor(() => expect(screen.getByTestId("decide-receipt").textContent).toMatch(new RegExp(`^Decided ${CLOCK}$`)));
    expect(screen.getByTestId("decide-project").textContent).toBe("CheckoutFiled");
    expect(screen.queryByRole("textbox", { name: "Decision title" })).toBeNull();

    // One face (2026-11-08): the row opens the record in the Decisions
    // window reader, never the Decision pullout.
    const row = screen.getByRole("button", { name: /Roll back the cache change/ });
    await act(async () => { fireEvent.click(row); });
    await waitFor(() => expect(useDesk.getState().windowsById["surface-decisions"]?.scope).toBe("record:rec_1"));
    expect(useDesk.getState().pullouts.map((p) => p.id)).not.toContain("decision:decision_1");
  });

  it("a meeting with no project files the decision under its meeting only", async () => {
    render(<MeetingDecideWell meetingId="p13-hiring" title="Hiring debrief" startedAt="2026-09-30T14:00:00" />);
    fireEvent.click(screen.getByRole("button", { name: "Decide" }));
    await waitFor(() => expect(screen.getByTestId("decide-scope-state")).toHaveTextContent("No linked project"));
    fireEvent.change(screen.getByRole("textbox", { name: "Decision title" }), { target: { value: "Typed under B" } });
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Save" })); });
    await waitFor(() => expect(hub.posts).toHaveLength(1));
    expect(hub.posts[0].meeting_id).toBe("p13-hiring");
    expect(hub.posts[0].project_id).toBeUndefined();
    expect(hub.puts).toEqual([]);
    await waitFor(() => expect(screen.getByTestId("decide-receipt")).toBeTruthy());
  });
});

describe("HS-S42 the reader files the decision's canonical record", () => {
  it("Assign writes decision_record:<id>; the source decision keeps its tags", async () => {
    hub.decisions = [decisionWire({ id: "d1", title: "Roll back the cache change", status: "accepted", tags: ["meeting:m1", "project:proj-checkout"] })];
    await act(async () => { await useDesk.getState().refresh(); });
    render(<Reader deskId="d1" />);
    const assign = await screen.findAllByRole("button", { name: "Assign to Checkout Project", hidden: true });
    await act(async () => { fireEvent.click(assign[0]); });
    await waitFor(() => expect(hub.puts).toEqual([{
      url: "/api/projects/proj-checkout/resources/decision_record:record-of-d1", body: { relationship: "member" },
    }]));
    expect(hub.decisions[0].tags).toEqual(["meeting:m1", "project:proj-checkout"]);
  });
});

describe("the reader's editor: the decision first, support as folds", () => {
  const CASES: Wire[] = [
    { id: "decision_title-only", title: "Glass title only decision" },
    {
      id: "decision_context-and-decision", title: "Move the nightly build to the shared runners",
      context_markdown: "Our own runners are full every night. The shared runner pool has spare capacity after 8 PM.",
      decision_markdown: "Move the nightly build to the shared runners.",
    },
  ];
  beforeEach(async () => {
    hub.decisions = CASES.map((fields) => decisionWire(fields));
    await act(async () => { await useDesk.getState().refresh(); });
  });
  async function edit(deskId: string) {
    render(<Reader deskId={deskId} />);
    fireEvent.click(await screen.findByTestId("decision-reader-edit"));
    await screen.findByRole("textbox", { name: "Decision" });
  }

  it("uses the shared form, keeps all fields and has one completion row", async () => {
    await edit("decision_title-only");
    expect(screen.getByRole("textbox", {name:"Decision"})).toHaveFocus();
    fireEvent.change(screen.getByRole("textbox",{name:"Background"}),{target:{value:"A reason to retain"}});
    expect(screen.getByRole("textbox",{name:"Background"})).toHaveValue("A reason to retain");
    expect(screen.getByTestId("decision-reader-editor").querySelector(".surface-inspector-actions")).toBeTruthy();
    expect(screen.getAllByRole("button",{name:"Save"})).toHaveLength(1);
    expect(hub.puts).toHaveLength(0);
  });
  it("shows saved support fields in the same form", async () => {
    await edit("decision_context-and-decision");
    expect(screen.getByRole("textbox",{name:"Background"})).toHaveValue("Our own runners are full every night. The shared runner pool has spare capacity after 8 PM.");
  });
  it("Edit on a title-only decision still offers all three fields", async () => {
    await edit("decision_title-only");
    for (const name of ["Background", "Decision", "Consequences"]) {
      expect(screen.getByLabelText(name, { selector: "textarea" })).toBeTruthy();
    }
  });
});

describe("PHILO-3-01 the default title yields to the first line", () => {
  async function saveFirstLine(title: string, words: string) {
    hub.decisions = [decisionWire({ id: "d-title", title })];
    await act(async () => { await useDesk.getState().refresh(); });
    render(<Reader deskId="d-title" />);
    fireEvent.click(await screen.findByTestId("decision-reader-edit"));
    fireEvent.change(await screen.findByRole("textbox", { name: "Decision" }), { target: { value: words } });
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Save" })); });
    await waitFor(() => expect(hub.puts).toHaveLength(1));
    return hub.puts[0].body;
  }

  it("a New decision is titled by the first line of its words", async () => {
    expect(await saveFirstLine("New decision", "# Adopt the one bus\nfor every frame")).toMatchObject({
      title: "Adopt the one bus", decision_markdown: "# Adopt the one bus\nfor every frame",
    });
  });

  it("an owner title is never replaced", async () => {
    expect(await saveFirstLine("Bus choice", "Adopt it")).not.toHaveProperty("title");
  });
});

describe("the reader changes the state by one verb: Decide, Retire", () => {
  async function renderDecision(status: string, others: string[] = []) {
    hub.decisions = [
      decisionWire({ id: "state-decision", title: "Use the shared runners", status }),
      ...others.map((other, i) => decisionWire({ id: `other-${i}`, title: `Other ${i}`, status: other })),
    ];
    await act(async () => { await useDesk.getState().refresh(); });
    render(<Reader deskId="state-decision" />);
    await screen.findByTestId("decision-reader-edit");
  }
  const statusWrites = (refuse: () => boolean, hold?: (resolve: () => void) => void) =>
    vi.mocked(fetch).mockImplementation((input, init) => {
      const id = /^\/api\/decisions\/([^/?]+)\/status$/.exec(String(input))?.[1];
      if (id && init?.method === "PUT") {
        const body = JSON.parse(String(init.body));
        hub.puts.push({ url: String(input), body });
        if (refuse()) return Promise.resolve(json({ error: "state_refused" }, 403));
        const write = () => {
          hub.decisions = hub.decisions.map((d) => d.id === id ? { ...d, status: body.status } : d);
          return json({ decision: hub.decisions.find((d) => d.id === id) });
        };
        if (hold) return new Promise((resolve) => hold(() => resolve(write())));
        return Promise.resolve(write());
      }
      return hubFetch(input, init);
    });

  it("Retire writes once; the state says Retiring, then Retired", async () => {
    await renderDecision("accepted");
    expect(stateText()).toBe("");
    let complete!: () => void;
    statusWrites(() => false, (resolve) => { complete = resolve; });
    const retire = screen.getByTestId("decision-reader-retire");
    fireEvent.click(retire);
    const confirm = within(screen.getByTestId("decision-reader-question")).getByRole("button",{name:"Retire"});
    expect(hub.puts).toHaveLength(0);
    fireEvent.click(confirm);
    expect(stateText()).toBe("Retiring");
    expect(retire).toBeDisabled();
    fireEvent.click(confirm);
    expect(hub.puts).toHaveLength(1);
    expect(hub.puts[0]).toEqual({ url: "/api/decisions/state-decision/status", body: { status: "deprecated" } });
    await act(async () => complete());
    await waitFor(() => expect(hub.decisions[0].status).toBe("deprecated"));
    expect(screen.queryByTestId("decision-reader-retire")).toBeNull();
  });

  it("a refused Retire says so and keeps the old state; Retire again repeats the choice", async () => {
    await renderDecision("accepted");
    let refuse = true;
    statusWrites(() => refuse);
    fireEvent.click(screen.getByTestId("decision-reader-retire"));
    fireEvent.click(within(screen.getByTestId("decision-reader-question")).getByRole("button",{name:"Retire"}));
    expect((await screen.findByTestId("decision-reader-failure")).textContent).toMatch(/^Could not retire it · /);
    expect(stateText()).toBe("");
    refuse = false;
    fireEvent.click(within(screen.getByTestId("decision-reader-question")).getByRole("button",{name:"Retire"}));
    await waitFor(() => expect(hub.decisions[0].status).toBe("deprecated"));
    expect(hub.puts.map((put) => put.body)).toEqual([{ status: "deprecated" }, { status: "deprecated" }]);
  });

  it("DELIGHT 2: Decide makes the status bar say \"Decided · 3 proposed\"", async () => {
    await renderDecision("proposed", ["proposed", "proposed", "proposed", "accepted"]);
    statusWrites(() => false);
    expect(stateText()).toBe("Proposed");
    fireEvent.click(screen.getByTestId("decision-reader-accept"));
    await waitFor(() => expect(hub.decisions[0].status).toBe("accepted"));
    expect(stateText()).toBe("");
  });

  it("DELIGHT 2: the last open decision reads \"all decided\", never a count of zero", async () => {
    await renderDecision("proposed", ["accepted"]);
    statusWrites(() => false);
    fireEvent.click(screen.getByTestId("decision-reader-accept"));
    await waitFor(() => expect(hub.decisions[0].status).toBe("accepted"));
    expect(stateText()).toBe("");
    expect(stateText()).not.toMatch(/\b0\b/);
  });
});

describe("W6 (atlas pass 3): every verb of a Desk decision says its word in the reader", () => {
  const kafka = decisionWire({
    id: "decision_kafka", title: "Use Kafka for the settlement events", status: "accepted",
    decision_markdown: "Use Kafka for the settlement events",
    context_markdown: "About: Payments Platform Rewrite",
    consequences_markdown: "Why: It is the team standard and the ops team runs it.",
  });
  beforeEach(async () => {
    hub.decisions = [kafka];
    await act(async () => { await useDesk.getState().refresh(); });
  });

  it("keeps the working verbs in the toolbar and the other verbs in its Actions menu", async () => {
    const {container}=render(<Reader deskId="decision_kafka" />);
    const toolbar=await screen.findByTestId("decision-reader-toolbar");
    for (const name of ["Edit","Retire","Send…","Copy","Delete","Commit","File"]) {
      expect(within(toolbar).getByRole("button",{name})).toBeInTheDocument();
    }
    fireEvent.click(within(toolbar).getByRole("button",{name:"Actions ▾"}));
    expect(await screen.findByRole("menuitem",{name:"Dictate about this"})).toBeInTheDocument();
    expect(screen.getByRole("menuitem",{name:"Run as a program"})).toBeInTheDocument();
    fireEvent.keyDown(screen.getByRole("menu"),{key:"Escape"});
    expect(container.querySelector(".surface-mast,.surface-spine,.decisions-plate")).toBeNull();
    fireEvent.click(screen.getByRole("tab",{name:"Facts"}));
    expect(screen.getByText("Payments Platform Rewrite")).toBeInTheDocument();
  });
  it("Delete asks in this window; Cancel keeps the decision and confirmation uses the one Undo path", async () => {
    const seat=seatMounted();
    const asked:string[]=[];
    const listen=(event:Event)=>asked.push(String((event as CustomEvent<{ref:string}>).detail.ref));
    window.addEventListener(OBJECT_DELETE_REQUEST,listen);
    try {
      render(<Reader deskId="decision_kafka" />);
      fireEvent.click(await screen.findByTestId("decision-reader-delete"));
      const question=screen.getByTestId("decision-reader-question");
      expect(within(question).getByRole("button",{name:"Cancel"})).toHaveFocus();
      expect(screen.getByTestId("decision-words")).toBeVisible();
      expect(screen.getByTestId("decision-words")).toHaveTextContent(String(kafka.decision_markdown));
      expect(question.closest(".surface-pane-actions")).not.toBeNull();
      expect(screen.getByTestId("decision-reader-edit")).toBeDisabled();
      expect(asked).toEqual([]);
      fireEvent.click(within(question).getByRole("button",{name:"Cancel"}));
      fireEvent.click(screen.getByTestId("decision-reader-delete"));
      fireEvent.click(within(screen.getByTestId("decision-reader-question")).getByRole("button",{name:"Delete"}));
      await waitFor(()=>expect(asked).toEqual(["decision:decision_kafka"]));
    } finally {
      window.removeEventListener(OBJECT_DELETE_REQUEST,listen);
      if(seat)seatUnmounted();
    }
  });
  it("keeps the words above the Retire question", async () => {
    render(<Reader deskId="decision_kafka" />);
    fireEvent.click(await screen.findByTestId("decision-reader-retire"));
    expect(screen.getByTestId("decision-words")).toBeVisible();
    expect(screen.getByTestId("decision-words")).toHaveTextContent(String(kafka.decision_markdown));
    const question=screen.getByTestId("decision-reader-question");
    expect(within(question).getByRole("button",{name:"Cancel"})).toHaveFocus();
    expect(question.closest(".surface-pane-actions")).not.toBeNull();
  });
  it("Edit edits the fields as written (nothing is lost)", async () => {
    render(<Reader deskId="decision_kafka" />);
    fireEvent.click(await screen.findByTestId("decision-reader-edit"));
    expect(await screen.findByRole("textbox", { name: "Background" })).toHaveValue("About: Payments Platform Rewrite");
    expect(screen.getByRole("textbox", { name: "Consequences" })).toHaveValue("Why: It is the team standard and the ops team runs it.");
  });
});
