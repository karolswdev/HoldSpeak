/** PHILO-13-08 (B3) — decide where the meeting is.
 *
 * - `New Decision` (⌘K, ⌘⇧N, the floor menu) writes nothing until the
 *   decision has a title; its window asks it (the owner, 2026-10-25: the
 *   New decision window, no longer the palette); an abandoned try
 *   writes nothing (grounding F9: each try left a `New decision` record).
 * - The meeting record's `Decide` asks the title inline and creates ONE
 *   decision carrying the meeting and the meeting's project; the meeting
 *   then lists it, and the row opens its own window.
 * Real store slice, real window face and well; the hub transport is the double. */
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const hub = vi.hoisted(() => ({
  decisions: [] as Array<Record<string, unknown>>,
  posts: [] as Array<Record<string, unknown>>,
  resourcePuts: [] as string[],
  projects: [{ project_id: "proj-1", project_name: "Checkout" }] as Array<Record<string, unknown>>,
  // HS-S42 faults: the meeting's project read, the canonical POST, an
  // answer that does not name the Project.
  projectsFail: false,
  canonical: "ok" as "ok" | "malformed",
  answerUnfiled: false,
  // One face (2026-11-08): the hub refuses the next N creates (a 4xx).
  refuse: 0,
}));

function decisionWire(body: Record<string, unknown>, n: number) {
  return {
    id: `decision_${n}`, title: body.title, status: body.status ?? "proposed", deciders: [],
    decided_at: null, context_markdown: body.context_markdown ?? "", decision_markdown: "",
    alternatives: [], consequences_markdown: "", tags: body.tags ?? [],
    created_at: `2026-10-02T00:00:0${n}Z`, updated_at: "2026-10-02T00:00:00Z", deleted: false,
  };
}

vi.mock("../../lib/api", async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>();
  const post = (raw: unknown) => {
    const body = JSON.parse(String(raw ?? "{}")) as Record<string, unknown>;
    hub.posts.push(body);
    const decision = decisionWire(body, hub.posts.length);
    hub.decisions = [...hub.decisions, decision];
    return decision;
  };
  return {
    ...real,
    apiRequest: vi.fn((url: string, init?: RequestInit) => {
      if (url === "/api/decisions" && init?.method === "POST") {
        const decision = post(init.body);
        return Promise.resolve({ ok: true, status: 201, json: () => Promise.resolve({ decision }) });
      }
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) });
    }),
    apiFetch: vi.fn((url: string, init?: RequestInit & { json?: unknown }) => {
      // HS-S42: the canonical producer, shaped as the real route answers
      // (tests/integration/test_meeting_decision_filing.py): the source
      // decision carries the meeting and project tags, the record its id.
      if (url === "/api/decision-records/from-desk" && init?.method === "POST") {
        const json = init.json as Record<string, unknown>;
        hub.posts.push(json);
        if (hub.refuse > 0) {
          hub.refuse -= 1;
          return Promise.reject(new (real.ApiError as typeof import("../../lib/api").ApiError)(409, "Project Checkout is archived", {}));
        }
        if (hub.canonical === "malformed") return Promise.resolve({});
        const tags = [
          ...(json.project_id ? [`project:${json.project_id}`] : []),
          ...(json.meeting_id ? [`meeting:${json.meeting_id}`] : []),
        ];
        const decision = decisionWire({ title: json.title, status: json.status, tags }, hub.posts.length);
        hub.decisions = [...hub.decisions, decision];
        // One decision writer (2026-11-08): the record names the Project the
        // hub filed it in, in the same call.
        const project_id = hub.answerUnfiled ? null : (json.project_id ?? null);
        return Promise.resolve({ decision, record: { id: `rec_${hub.posts.length}`, source_id: decision.id, project_id } });
      }
      if (url === "/api/decisions" && init?.method === "POST")
        return Promise.resolve({ decision: post(init.body) });
      if (url === "/api/decisions") return Promise.resolve({ decisions: hub.decisions });
      if (url.startsWith("/api/decision-records/source/desk/"))
        return Promise.resolve([{ id: `rec_of_${decodeURIComponent(url.split("/").pop() ?? "")}` }]);
      if (/^\/api\/meetings\/[^/]+\/projects$/.test(url))
        return hub.projectsFail ? Promise.reject(new TypeError("Failed to fetch")) : Promise.resolve({ projects: hub.projects });
      if (url.startsWith("/api/projects/") && init?.method === "PUT") {
        hub.resourcePuts.push(decodeURIComponent(url));
        return Promise.resolve({});
      }
      return Promise.resolve({});
    }),
  };
});
vi.mock("../setup", () => ({ loadSetup: vi.fn(() => Promise.resolve(null)) }));

import { useDesk } from "../store";
import { useNamePrompt, usePalette } from "../chromeState";
import { DecisionsCore } from "../../pages/cores/DecisionsCore";
import { MeetingDecideWell } from "../../meetings/MeetingDecideWell";
import { VERBS } from "../verbRegistry";

beforeEach(() => {
  hub.decisions = [];
  hub.posts = [];
  hub.resourcePuts = [];
  hub.projects = [{ project_id: "proj-1", project_name: "Checkout" }];
  hub.projectsFail = false;
  hub.canonical = "ok";
  hub.answerUnfiled = false;
  hub.refuse = 0;
  useNamePrompt.getState().clear();
  usePalette.getState().setOpen(false);
  useDesk.setState({ pullouts: [], editingId: null, newIds: [], windowsById: {}, drafts: {} });
});

const newDecision = () => VERBS.find((v) => v.id === "desk.new-decision")!;

describe("PHILO-13-08 New Decision writes nothing before it is named", () => {
  // The native Decisions app (2026-11-08): the title is asked by the
  // Decisions window's composer plate (scope `new`), not in the palette and
  // not in a second window. The whole press is
  // pages/cores/__tests__/decisions.app.test.tsx.
  const form = () => render(<DecisionsCore scope="new" />);

  it("the verb opens the Decisions window's composer and posts nothing", async () => {
    await act(async () => { newDecision().run({ selectedRef: null }); });
    expect(hub.posts).toEqual([]);
    expect(useDesk.getState().windowsById["surface-decisions"]?.scope).toBe("new");
    expect(usePalette.getState().open).toBe(false);
  });

  it("an abandoned try (Cancel) leaves no record", async () => {
    await act(async () => { newDecision().run({ selectedRef: null }); });
    form();
    fireEvent.change(screen.getByRole("textbox", { name: "Decision title" }), { target: { value: "Half a thought" } });
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(useDesk.getState().windowsById["surface-decisions"]?.scope).toBeNull();
    expect(hub.posts).toEqual([]);
    expect(hub.decisions.filter((d) => d.title === "New decision")).toEqual([]);
  });

  it("type + Enter creates one decision with that title and opens it", async () => {
    await act(async () => { newDecision().run({ selectedRef: null }); });
    form();
    const well = screen.getByRole("textbox", { name: "Decision title" });
    fireEvent.change(well, { target: { value: "Adopt feature flags" } });
    await act(async () => { fireEvent.keyDown(well, { key: "Enter" }); });
    await waitFor(() => expect(hub.posts).toHaveLength(1));
    expect(hub.posts[0].title).toBe("Adopt feature flags");
    // PHILO-15-09 (B12): the owner's own decision is DECIDED, not to review.
    expect(hub.posts[0].status).toBe("accepted");
    // The one decision face (2026-11-08): the one decision opens its record
    // in the Decisions window reader, never a Decision pullout.
    await waitFor(() => expect(useDesk.getState().windowsById["surface-decisions"]?.scope).toBe("record:rec_of_decision_1"));
    expect(useDesk.getState().pullouts.map((p) => p.id)).not.toContain("decision_1");
  });

  it("Create stays off until a title, then creates once", async () => {
    form();
    expect(screen.getByRole("group", { name: "New decision" })).toBeInTheDocument();
    const create = screen.getByRole("button", { name: /Record/ });
    expect(create).toBeDisabled();
    fireEvent.change(screen.getByRole("textbox", { name: "Decision title" }), { target: { value: "Use one ledger" } });
    expect(create).not.toBeDisabled();
    expect(hub.posts).toEqual([]);
    await act(async () => { fireEvent.click(create); });
    await waitFor(() => expect(hub.posts).toHaveLength(1));
    expect(hub.posts[0].title).toBe("Use one ledger");
  });

  it("Enter with no title writes nothing", async () => {
    form();
    const well = screen.getByRole("textbox", { name: "Decision title" });
    await act(async () => { fireEvent.keyDown(well, { key: "Enter" }); });
    expect(hub.posts).toEqual([]);
  });
});

describe("PHILO-13-08 Decide in the meeting record", () => {
  // An unconfirmed title stays in its meeting's well: a case that leaves one
  // names its own meeting.
  const well = (meetingId = "m-42") =>
    render(
      <MeetingDecideWell meetingId={meetingId} title="Checkout latency review"
        startedAt="2026-10-01T09:00:00" summary="p99 doubled after the cache change."
        deciders={["Mira", "Theo"]} />,
    );

  it("Decide, type + Enter: ONE call makes the decision with the meeting, its one project and its deciders", async () => {
    well();
    fireEvent.click(screen.getByRole("button", { name: "Decide" }));
    // HS-S42: the one linked project is shown, and chosen, before Save.
    await waitFor(() => expect(screen.getByRole("button", { name: "Checkout" }).getAttribute("aria-pressed")).toBe("true"));
    const title = screen.getByRole("textbox", { name: "Decision title" });
    fireEvent.change(title, { target: { value: "Roll back the cache change" } });
    await act(async () => { fireEvent.keyDown(title, { key: "Enter" }); });
    await waitFor(() => expect(hub.posts).toHaveLength(1));
    const body = hub.posts[0];
    expect(body.status).toBe("accepted");
    expect(body.title).toBe("Roll back the cache change");
    expect(body.meeting_id).toBe("m-42");
    expect(body.project_id).toBe("proj-1");
    expect(String(body.why)).toContain("Meeting: Checkout latency review · 2026-10-01");
    expect(String(body.why)).toContain("p99 doubled");
    expect(body.deciders).toEqual(["Mira", "Theo"]);
    // the receipt is where the click happened: the meeting lists it
    await waitFor(() => expect(screen.getByTestId("decide-receipt").textContent).toMatch(/^Decided \d\d:\d\d$/));
    // The project is its own object row: sprite, name, the quiet word Filed.
    const project = screen.getByTestId("decide-project");
    expect(project.querySelector("img")).toBeTruthy();
    expect(project.textContent).toBe("CheckoutFiled");
    // The hub filed it: the client makes no second write.
    expect(hub.resourcePuts).toEqual([]);
    expect(screen.getByText("Roll back the cache change")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Decide" })).toBeTruthy();
  });

  it("a meeting with no project still decides; no project, no edge", async () => {
    hub.projects = [];
    well();
    fireEvent.click(screen.getByRole("button", { name: "Decide" }));
    await waitFor(() => expect(screen.getByTestId("decide-scope-state").textContent).toContain("No linked project"));
    fireEvent.change(screen.getByRole("textbox", { name: "Decision title" }), { target: { value: "Ship it" } });
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Save" })); });
    await waitFor(() => expect(hub.posts).toHaveLength(1));
    expect(hub.posts[0].project_id).toBeUndefined();
    expect(hub.resourcePuts).toEqual([]);
  });

  it("several linked projects: Save waits for his pick; never the first", async () => {
    hub.projects = [{ project_id: "proj-1", project_name: "Checkout" }, { project_id: "proj-2", project_name: "Ledger" }];
    well();
    fireEvent.click(screen.getByRole("button", { name: "Decide" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Ledger" })).toBeTruthy());
    fireEvent.change(screen.getByRole("textbox", { name: "Decision title" }), { target: { value: "Split the ledger" } });
    expect(screen.getByRole("button", { name: "Checkout" }).getAttribute("aria-pressed")).toBe("false");
    expect((screen.getByRole("button", { name: "Save" }) as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Ledger" }));
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Save" })); });
    await waitFor(() => expect(hub.posts).toHaveLength(1));
    expect(hub.posts[0].project_id).toBe("proj-2");
    expect(hub.resourcePuts).toEqual([]);
  });

  it("a failed project read is not 'no project': Save waits for No project", async () => {
    hub.projectsFail = true;
    well();
    fireEvent.click(screen.getByRole("button", { name: "Decide" }));
    await waitFor(() => expect(screen.getByTestId("decide-scope-state").textContent).toContain("Projects not read"));
    expect(screen.getByRole("button", { name: "Read again" })).toBeTruthy();
    fireEvent.change(screen.getByRole("textbox", { name: "Decision title" }), { target: { value: "Ship it" } });
    expect((screen.getByRole("button", { name: "Save" }) as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "No project" }));
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Save" })); });
    await waitFor(() => expect(hub.posts).toHaveLength(1));
    expect(hub.resourcePuts).toEqual([]);
  });

  it("an unconfirmed Save never creates again: no legacy POST, Save off for that title", async () => {
    hub.canonical = "malformed";
    well("m-unconfirmed");
    fireEvent.click(screen.getByRole("button", { name: "Decide" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Checkout" })).toBeTruthy());
    const title = screen.getByRole("textbox", { name: "Decision title" });
    fireEvent.change(title, { target: { value: "Roll back" } });
    await act(async () => { fireEvent.keyDown(title, { key: "Enter" }); });
    await waitFor(() => expect(screen.getByTestId("decide-unconfirmed")).toBeTruthy());
    expect(hub.posts).toHaveLength(1);
    expect(hub.decisions).toEqual([]);
    expect((screen.getByRole("button", { name: "Save" }) as HTMLButtonElement).disabled).toBe(true);
    await act(async () => { fireEvent.keyDown(title, { key: "Enter" }); });
    expect(hub.posts).toHaveLength(1);
    expect((title as HTMLInputElement).value).toBe("Roll back");
  });

  it("an answer that does not name the Project shows the project row without Filed; no dead line, no second write", async () => {
    hub.answerUnfiled = true;
    well();
    fireEvent.click(screen.getByRole("button", { name: "Decide" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Checkout" }).getAttribute("aria-pressed")).toBe("true"));
    const title = screen.getByRole("textbox", { name: "Decision title" });
    fireEvent.change(title, { target: { value: "Roll back" } });
    await act(async () => { fireEvent.keyDown(title, { key: "Enter" }); });
    await waitFor(() => expect(screen.getByTestId("decide-project").textContent).toBe("Checkout"));
    expect(screen.queryByTestId("decide-filed")).toBeNull();
    expect(screen.queryByText(/Not filed/)).toBeNull();
    expect(screen.queryByRole("textbox", { name: "Decision title" })).toBeNull();
    expect(hub.resourcePuts).toEqual([]);
    expect(hub.posts).toHaveLength(1);
  });

  it("one face: a row opens the record reader in the Decisions window, never the Decision pullout", async () => {
    const open = vi.fn();
    const real = useDesk.getState().openSurfaceWindow;
    useDesk.setState({ openSurfaceWindow: open });
    try {
      hub.decisions = [{ ...decisionWire({ title: "Older call", tags: ["meeting:m-face"] }, 0), id: "decision_old" }];
      well("m-face");
      fireEvent.click(screen.getByRole("button", { name: "Decide" }));
      await waitFor(() => expect(screen.getByRole("button", { name: "Checkout" }).getAttribute("aria-pressed")).toBe("true"));
      const title = screen.getByRole("textbox", { name: "Decision title" });
      fireEvent.change(title, { target: { value: "Roll back" } });
      await act(async () => { fireEvent.keyDown(title, { key: "Enter" }); });
      await waitFor(() => expect(screen.getByTestId("decide-receipt")).toBeTruthy());
      // The record this press made: its reader, at once.
      await act(async () => { fireEvent.click(screen.getByRole("button", { name: /Roll back/ })); });
      expect(open).toHaveBeenCalledWith("open-decisions", "record:rec_1");
      expect(useDesk.getState().pullouts.map((p) => p.id)).toEqual([]);
      // A decision made before (no receipt): its record, as the hub names it.
      open.mockClear();
      await act(async () => { fireEvent.click(screen.getByRole("button", { name: /Older call/ })); });
      await waitFor(() => expect(open).toHaveBeenCalledWith("open-decisions", "record:rec_of_decision_old"));
      expect(useDesk.getState().pullouts.map((p) => p.id)).toEqual([]);
    } finally {
      useDesk.setState({ openSurfaceWindow: real });
    }
  });

  it("a refused create shows the hub's reason and Retry; Retry calls create once more", async () => {
    hub.refuse = 1;
    well("m-refused");
    fireEvent.click(screen.getByRole("button", { name: "Decide" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Checkout" }).getAttribute("aria-pressed")).toBe("true"));
    const title = screen.getByRole("textbox", { name: "Decision title" });
    fireEvent.change(title, { target: { value: "Roll back" } });
    await act(async () => { fireEvent.keyDown(title, { key: "Enter" }); });
    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("Project Checkout is archived"));
    expect(hub.posts).toHaveLength(1);
    expect(screen.getByTestId("decide-scope")).toBeVisible();
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Retry" })); });
    await waitFor(() => expect(hub.posts).toHaveLength(2));
    expect(hub.posts[1].title).toBe("Roll back");
    await waitFor(() => expect(screen.getByTestId("decide-receipt")).toBeTruthy());
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("Cancel abandons: nothing is written", async () => {
    well();
    fireEvent.click(screen.getByRole("button", { name: "Decide" }));
    fireEvent.change(screen.getByRole("textbox", { name: "Decision title" }), { target: { value: "Maybe" } });
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(hub.posts).toEqual([]);
    expect(screen.queryByRole("textbox", { name: "Decision title" })).toBeNull();
  });

  it("Save stays off until the title has words", () => {
    well();
    fireEvent.click(screen.getByRole("button", { name: "Decide" }));
    expect((screen.getByRole("button", { name: "Save" }) as HTMLButtonElement).disabled).toBe(true);
  });
});

// Muad'Dib's ruling 2026-10-04: one filled primary per face. `Decide` is
// filled, as ratified next to SEND, on a record with no `Run summary`; it is
// ghost only while `Run summary` is on the face. `Save` follows the same rule.
describe("the Decide verbs and the record's Run summary", () => {
  // One meeting per state: an open title well is kept per meeting.
  const well = (runSummaryOnFace: boolean) =>
    render(<MeetingDecideWell meetingId={`m-weight-${runSummaryOnFace}`} title="Checkout latency review"
      runSummaryOnFace={runSummaryOnFace} />);

  it("no Run summary on the face: Decide and Save are filled", () => {
    well(false);
    const decide = screen.getByRole("button", { name: "Decide" });
    expect(decide.className).toContain("btn--primary");
    fireEvent.click(decide);
    expect(screen.getByRole("button", { name: "Save" }).className).toContain("btn--primary");
  });

  it("Run summary on the face: Decide and Save are ghost", () => {
    well(true);
    const decide = screen.getByRole("button", { name: "Decide" });
    expect(decide.className).not.toContain("btn--primary");
    expect(decide.className).toContain("btn--ghost");
    fireEvent.click(decide);
    const save = screen.getByRole("button", { name: "Save" });
    expect(save.className).not.toContain("btn--primary");
    expect(save.className).toContain("btn--ghost");
  });
});

describe("PHILO-13-08 a draft belongs to its meeting (Astra's single pass)", () => {
  const props = (id: string) => ({
    meetingId: id, title: `Meeting ${id}`, startedAt: "2026-10-01T09:00:00", summary: null,
  });

  it("a title typed under A never files under B; back on A it is A's again", async () => {
    const view = render(<MeetingDecideWell {...props("m-A")} />);
    fireEvent.click(screen.getByRole("button", { name: "Decide" }));
    fireEvent.change(screen.getByRole("textbox", { name: "Decision title" }), { target: { value: "Typed under A" } });

    // He selects meeting B: the same seat, a new meeting.
    view.rerender(<MeetingDecideWell {...props("m-B")} />);
    expect(screen.queryByDisplayValue("Typed under A")).toBeNull();
    const save = screen.queryByRole("button", { name: "Save" });
    if (save) await act(async () => { fireEvent.click(save); });
    expect(hub.posts).toEqual([]);

    fireEvent.click(screen.getByRole("button", { name: "Decide" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Checkout" }).getAttribute("aria-pressed")).toBe("true"));
    const b = screen.getByRole("textbox", { name: "Decision title" });
    fireEvent.change(b, { target: { value: "Typed under B" } });
    await act(async () => { fireEvent.keyDown(b, { key: "Enter" }); });
    await waitFor(() => expect(hub.posts).toHaveLength(1));
    expect(hub.posts[0].title).toBe("Typed under B");
    expect([hub.posts[0].meeting_id, hub.posts[0].project_id]).toEqual(["m-B", "proj-1"]);
    expect(String(hub.posts[0].why)).toContain("Meeting: Meeting m-B");

    // Back on A: A's own draft, and it files under A.
    view.rerender(<MeetingDecideWell {...props("m-A")} />);
    const a = screen.getByRole("textbox", { name: "Decision title" }) as HTMLInputElement;
    expect(a.value).toBe("Typed under A");
    await waitFor(() => expect(screen.getByRole("button", { name: "Checkout" }).getAttribute("aria-pressed")).toBe("true"));
    await act(async () => { fireEvent.keyDown(a, { key: "Enter" }); });
    await waitFor(() => expect(hub.posts).toHaveLength(2));
    expect(hub.posts[1].title).toBe("Typed under A");
    expect([hub.posts[1].meeting_id, hub.posts[1].project_id]).toEqual(["m-A", "proj-1"]);
  });
});
