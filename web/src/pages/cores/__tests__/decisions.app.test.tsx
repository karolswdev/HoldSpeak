/** Decisions, the native app (2026-11-08): the rail of decisions, the mast,
 * the plate and the ledger, in one window. The ledger rows are the hub's
 * recorded answer for the honest-faces seed (tests/integration/
 * test_face_wire_fences.py, `decision.ledger`); a committed record is the
 * Room's recorded wire. Only the transport (`apiFetch`, `apiRequest`) and
 * the openers are doubles. The cases of the parked list page
 * (pullouts/views/_parked/DecisionsView_20261108.test.tsx) that the native
 * face keeps are here: search and Current only by the hub, Show more, a
 * late answer dropped, every row's door, the reader's verbs. */
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import HONEST_DECISIONS from "../../../test/wire/decisions.honest-faces.wire.json";
import CREATED_PROGRAM from "../../../desk/programs/__fixtures__/program.create_project.json";
// Recorded by tests/integration/test_desk_project_room.py::
// test_a_committed_decision_names_its_person_on_the_decided_line (HOLDSPEAK_WIRE_WRITE=1).
import COMMITTED from "../../../features/project-room/__tests__/room-wires/committedWord.json";

const apiFetch = vi.hoisted(() => vi.fn());
const apiRequest = vi.hoisted(() => vi.fn());
const openRef = vi.hoisted(() => vi.fn());
const openProgram = vi.hoisted(() => vi.fn());
const bus = vi.hoisted(() => {
  const handlers = new Set<(frame: unknown) => void>();
  const subscribe = (type: string, handler: (frame: unknown) => void) => {
    if (type !== "desk_changed") return () => undefined;
    handlers.add(handler);
    return () => handlers.delete(handler);
  };
  return { handlers, subscribe };
});
vi.mock("../../../lib/api", async (importOriginal) => ({
  ApiError: (await importOriginal<typeof import("../../../lib/api")>()).ApiError,
  apiFetch,
  apiRequest,
  readableError: (reason: unknown) => reason instanceof Error ? reason.message : "Request failed",
}));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ subscribe: bus.subscribe }),
  useOptionalRuntimeBus: () => ({ state: "offline", subscribe: bus.subscribe }),
}));
vi.mock("../../../desk/programs/open", () => ({ openProgram }));
vi.mock("../../../desk/openObject", async (importOriginal) => ({
  ...await importOriginal<typeof import("../../../desk/openObject")>(),
  openRef,
}));

import { DecisionsCore } from "../DecisionsCore";
import { DESK_APPLICATIONS } from "../../../desk/applications";
import { useDesk } from "../../../desk/store";

const rail = () => within(screen.getByTestId("decisions-rail"));
const params = (path: string) => new URLSearchParams(path.split("?")[1] ?? "");

/** A record (DecisionRecordService.get), as the parked list page's cases had it. */
const detail = {
  id: "receipt-abcdef0123456789", decision_text: "Ship the Desk Intelligence pullout",
  rationale: "The Desk needs a durable answer to why.", alternatives: "Leave the placeholder in place",
  owner: "Karol", review_date: "2026-08-14", lifecycle: "active", status: null,
  source_type: "meeting", source_id: "dec-1", created_at: "2026-10-09T14:00:00",
  sources: [{ source_type: "segment", source_ref: "segment-1", meeting_id: "meeting-1", speaker: "Karol", text: "Receipts must explain the decision." }],
  work: [{ id: "work-1", work_type: "story", work_ref: "HS-128-04" }],
  predecessor_id: "receipt-old", successor_id: null,
  revisions: [{ id: "revision-1", field_name: "rationale", old_value: "Old rationale", new_value: "The Desk needs a durable answer to why.", created_at: "2026-08-07T10:00:00Z" }],
};

const ledger: import("../../../desk/decisions/api").LedgerRow[] = [
  { source: "meeting", id: "dec-1", text: detail.decision_text, rationale: detail.rationale, decided_at: "2026-10-09T14:00:00",
    lifecycle: "active", status: "accepted", meeting_id: "m-1", meeting_title: "Ledger cutover sync", record_id: detail.id, committed: 0, committed_to: null },
  { source: "meeting", id: "dec-2", text: "Freeze the old ledger on Nov 5", rationale: "Agreed in the meeting.", decided_at: "2026-10-09T14:05:00",
    lifecycle: "recorded", status: "recorded", meeting_id: "m-1", meeting_title: "Ledger cutover sync", record_id: null, committed: 0, committed_to: null },
  { source: "meeting", id: "dec-3", text: "Keep the old ledger", rationale: null, decided_at: "2026-10-01T09:00:00",
    lifecycle: "superseded", status: "superseded", meeting_id: "m-0", meeting_title: "Ledger kickoff", record_id: null, committed: 0, committed_to: null },
  { source: "desk", id: "d-adr", text: "Use OTel for tracing", rationale: null, decided_at: "2026-10-02",
    lifecycle: "accepted", status: "proposed", meeting_id: null, meeting_title: null, record_id: null, committed: 0, committed_to: null },
];

function hub(path: string): Promise<unknown> {
  if (path === `/api/decision-records/${detail.id}`) return Promise.resolve(structuredClone(detail));
  if (path.startsWith("/api/decisions/ledger?")) {
    const p = params(path);
    let rows = ledger.slice();
    const id = p.get("decision_id");
    if (id) rows = rows.filter((r) => r.id === id);
    if (p.get("current") === "true") rows = rows.filter((r) => ["recorded", "accepted", "active"].includes(r.lifecycle ?? ""));
    const q = (p.get("q") ?? "").toLowerCase().split(/\s+/).filter(Boolean);
    rows = rows.filter((r) => q.every((w) => `${r.text} ${r.meeting_title ?? ""}`.toLowerCase().includes(w)));
    const offset = Number(p.get("offset") ?? 0);
    const limit = Number(p.get("limit") ?? 100);
    return Promise.resolve({ decisions: rows.slice(offset, offset + limit), page: { total: rows.length } });
  }
  return Promise.resolve({});
}

beforeEach(() => {
  apiFetch.mockReset();
  apiRequest.mockReset();
  openRef.mockReset();
  openProgram.mockReset();
  apiFetch.mockImplementation(hub);
  apiRequest.mockImplementation(async () => new Response("{}", { status: 200 }));
  useDesk.setState({ refresh: vi.fn(() => Promise.resolve()) } as never);
});
afterEach(() => vi.useRealTimers());

describe("Decisions: the rail", () => {
  it("draws the desk's decisions from the hub's ledger read, by their words and their state", async () => {
    apiFetch.mockImplementation(async () => structuredClone(HONEST_DECISIONS.wire));
    const { container } = render(<DecisionsCore />);
    await waitFor(() => expect(container.querySelector("[data-testid=decisions-row]")?.textContent).toContain("Freeze the old ledger on Nov 5"));
    expect(apiFetch).toHaveBeenCalledWith("/api/decisions/ledger?limit=100&offset=0");
    const rows = container.querySelectorAll("[data-testid=decisions-row]");
    expect(rows).toHaveLength(1);
    expect(rows[0].textContent).toContain("Ledger cutover sync");
    expect(rows[0].getAttribute("data-kind")).toBe("decision");
    // The spine's meaning colour: a recorded meeting decision is decided (steel).
    expect(rows[0].getAttribute("data-state")).toBe("steel");
    expect(rows[0].querySelector(".surface-spine-part")?.getAttribute("data-tone")).toBe("steel");
    expect(rows[0].textContent).not.toMatch(/dec-[0-9a-f]{6,}|record-[0-9a-f]{6,}/);
  });

  it("is an application the Go menu lists; New decision is its composer, not a second window", async () => {
    const app = DESK_APPLICATIONS.find((a) => a.action === "open-decisions")!;
    expect(app.windowId).toBe("surface-decisions");
    expect(app.go?.group).toBe("daily");
    const loaded = await app.surface!.load();
    expect(loaded.default).toBe(DecisionsCore);
    expect(DESK_APPLICATIONS.some((a) => a.action === "new-decision")).toBe(false);
  });

  it("each state has its colour: proposed brass, decided steel, superseded graphite", async () => {
    render(<DecisionsCore />);
    await screen.findByText("Keep the old ledger");
    const tone = (words: string) => screen.getAllByTestId("decisions-row").find((row) => row.textContent?.includes(words))?.getAttribute("data-state");
    expect(tone("Use OTel for tracing")).toBe("brass");
    expect(tone("Freeze the old ledger")).toBe("steel");
    expect(tone("Keep the old ledger")).toBe("graphite");
  });

  it("on open the first record is picked (the one that waits on him, else the newest); the plate leads with its own verb", async () => {
    render(<DecisionsCore />);
    // No proposal has a record here: the newest record is picked, beside the rail.
    expect((await screen.findByTestId("decision-reader-title")).textContent).toBe(detail.decision_text);
    const row = screen.getAllByTestId("decisions-row").find((r) => r.textContent?.includes(detail.decision_text))!;
    expect(within(row).getByRole("button").getAttribute("aria-current")).toBe("true");
    expect(screen.getByTestId("decision-spine")).toBeTruthy();
    expect(screen.getByTestId("decision-reader-commit").textContent).toBe("Commit");
    expect(screen.queryByRole("button", { name: /^Open$/ })).toBeNull();
    // A proposal with a record comes first.
    ledger.push({ ...ledger[3], id: "d-prop", text: "Adopt OpenTelemetry", record_id: "rec-prop" });
    try {
      apiFetch.mockImplementation((path: string) => path === "/api/decision-records/rec-prop"
        ? Promise.resolve({ ...detail, id: "rec-prop", title: "Adopt OpenTelemetry", decision_text: "Adopt OpenTelemetry", status: "proposed", source_type: "desk", source_id: "d-prop" })
        : hub(path));
      cleanup();
      render(<DecisionsCore />);
      expect((await screen.findByTestId("decision-reader-accept")).textContent).toBe("Decide");
      expect(screen.getByTestId("decision-reader-title").textContent).toBe("Adopt OpenTelemetry");
    } finally {
      ledger.pop();
    }
  });

  it("an empty desk: the plate is New decision itself", async () => {
    apiFetch.mockImplementation(async () => ({ decisions: [], page: { total: 0 } }));
    const createPrimitive = vi.fn(async () => undefined);
    const before = useDesk.getState().createPrimitive;
    useDesk.setState({ createPrimitive } as never);
    try {
      render(<DecisionsCore />);
      const plate = await screen.findByRole("group", { name: "New decision" });
      fireEvent.change(within(plate).getByRole("textbox", { name: "Decision title" }), { target: { value: "Use one ledger" } });
      fireEvent.click(within(plate).getByRole("button", { name: /Create/ }));
      expect(createPrimitive).toHaveBeenCalledWith("decision", { title: "Use one ledger" });
    } finally {
      useDesk.setState({ createPrimitive: before } as never);
    }
  });

  it("the hub searches; Current only asks the hub for standing decisions", async () => {
    render(<DecisionsCore />);
    await rail().findByText("Keep the old ledger");
    fireEvent.click(screen.getByRole("checkbox", { name: "Current only" }));
    await waitFor(() => expect(rail().queryByText("Keep the old ledger")).toBeNull());
    expect(apiFetch).toHaveBeenCalledWith("/api/decisions/ledger?current=true&limit=100&offset=0");
    fireEvent.change(screen.getByRole("searchbox", { name: "Search decisions" }), { target: { value: "cutover freeze" } });
    await waitFor(() => expect(rail().queryByText(detail.decision_text)).toBeNull());
    expect(rail().getByText("Freeze the old ledger on Nov 5")).toBeInTheDocument();
    expect(apiFetch).toHaveBeenCalledWith("/api/decisions/ledger?q=cutover+freeze&current=true&limit=100&offset=0");
  });

  it("a ledger longer than one page says so and shows more", async () => {
    const many = Array.from({ length: 130 }, (_, i) => ({ ...ledger[1], id: `dec-${i}`, text: `Decision ${i}` }));
    apiFetch.mockImplementation((path: string) => {
      const offset = Number(params(path).get("offset") ?? 0);
      return Promise.resolve({ decisions: many.slice(offset, offset + 100), page: { total: many.length } });
    });
    const { container } = render(<DecisionsCore />);
    const more = await screen.findByTestId("decisions-more");
    expect(more.textContent).toBe("Show more");
    expect(container.querySelectorAll("[data-testid=decisions-row]")).toHaveLength(100);
    fireEvent.click(more);
    await waitFor(() => expect(container.querySelectorAll("[data-testid=decisions-row]")).toHaveLength(130));
    expect(screen.queryByTestId("decisions-more")).toBeNull();
  });

  // Astra, #785 finding 2 (kept): a slow bus re-read for an older search must
  // not land over the new one.
  it("drops a late answer for an older query", async () => {
    let releaseAlpha: (body: unknown) => void = () => undefined;
    let alphaReads = 0;
    const page = (text: string) => ({ decisions: [{ ...ledger[1], id: text, text }], page: { total: 1 } });
    apiFetch.mockImplementation((path: string) => {
      const q = params(path).get("q");
      if (q === "alpha") {
        alphaReads += 1;
        return alphaReads === 1 ? Promise.resolve(page("Alpha decision")) : new Promise((resolve) => { releaseAlpha = resolve; });
      }
      if (q === "beta") return Promise.resolve(page("Beta decision"));
      return Promise.resolve({ decisions: [], page: { total: 0 } });
    });
    vi.useFakeTimers();
    const step = (ms: number) => act(async () => { await vi.advanceTimersByTimeAsync(ms); });
    render(<DecisionsCore />);
    const field = screen.getByRole("searchbox", { name: "Search decisions" });
    fireEvent.change(field, { target: { value: "alpha" } });
    await step(200);
    expect(rail().getByText("Alpha decision")).toBeTruthy();
    act(() => bus.handlers.forEach((handler) => handler({ type: "desk_changed", data: {} })));
    await step(300);
    expect(alphaReads).toBe(2);
    fireEvent.change(field, { target: { value: "beta" } });
    await step(200);
    expect(rail().getByText("Beta decision")).toBeTruthy();
    await act(async () => { releaseAlpha(page("Alpha decision")); });
    await step(50);
    expect(rail().getByText("Beta decision")).toBeTruthy();
    expect(rail().queryByText("Alpha decision")).toBeNull();
  });
});

describe("Decisions: a pick is one object (mast, spine, plate, ledger)", () => {
  it("a row with a record opens it beside the rail: the mast, the evidence, the history by time", async () => {
    render(<DecisionsCore />);
    const row = (await screen.findAllByTestId("decisions-row")).find((r) => r.textContent?.includes(detail.decision_text))!;
    fireEvent.click(within(row).getByRole("button"));
    const reader = await screen.findByTestId("decision-reader");
    expect((await within(reader).findByTestId("decision-reader-title")).textContent).toBe(detail.decision_text);
    expect(within(reader).getByTestId("decision-mast").textContent).toContain("from Ledger cutover sync");
    expect(within(row).getByRole("button").getAttribute("aria-current")).toBe("true");
    expect(reader.textContent).toContain(detail.rationale);
    expect(reader.textContent).toContain("Leave the placeholder in place");
    const evidence = within(reader).getByTestId("decision-evidence");
    expect(evidence.textContent).toContain("Receipts must explain the decision.");
    fireEvent.click(within(evidence).getByRole("button", { name: "Open meeting" }));
    expect(openRef).toHaveBeenCalledWith("meeting:meeting-1");
    expect(within(evidence).getByRole("button", { name: "Open story · HS-128-04" })).toBeTruthy();
    const history = within(reader).getByTestId("decision-history");
    expect(history.textContent).toContain("Old rationale");
    expect(within(history).getByRole("button", { name: "Previous decision" })).toBeTruthy();
    // No tinted callout, no left chevron rows: the ledger rows open nothing by themselves.
    expect(reader.querySelector(".surface-ledger-line[aria-expanded]")).toBeNull();
  });

  it("a meeting's decision with no record opens itself; Open meeting goes through the opener", async () => {
    render(<DecisionsCore />);
    const row = (await screen.findAllByTestId("decisions-row")).find((r) => r.textContent?.includes("Freeze the old ledger"))!;
    fireEvent.click(within(row).getByRole("button"));
    const reader = await screen.findByTestId("decision-reader");
    expect(reader.getAttribute("data-from")).toBe("meeting");
    expect(reader.textContent).toContain("Agreed in the meeting.");
    expect(reader.textContent).toContain("Ledger cutover sync");
    fireEvent.click(within(reader).getByTestId("decision-reader-meeting"));
    expect(openRef).toHaveBeenCalledWith("meeting:m-1");
  });

  it("a Desk decision with no record id opens through its desk_decision ref, with no desk read first", async () => {
    const refresh = vi.fn(() => Promise.resolve());
    useDesk.setState({ refresh } as never);
    render(<DecisionsCore />);
    const row = (await screen.findAllByTestId("decisions-row")).find((r) => r.textContent?.includes("Use OTel"))!;
    fireEvent.click(within(row).getByRole("button"));
    await waitFor(() => expect(openRef).toHaveBeenCalledWith("desk_decision:d-adr"));
    expect(refresh).not.toHaveBeenCalled();
  });

  it("decision:<id> is read by its id from the ledger, never found in the page", async () => {
    render(<DecisionsCore scope="decision:dec-2" />);
    expect((await screen.findByTestId("decision-reader")).textContent).toContain("Freeze the old ledger on Nov 5");
    expect(apiFetch).toHaveBeenCalledWith("/api/decisions/ledger?decision_id=dec-2&limit=1");
  });

  it("a failed record read says so with Try again", async () => {
    let fail = true;
    apiFetch.mockImplementation((path: string) => path === "/api/decision-records/receipt-new"
      ? (fail ? Promise.reject(new Error("Record did not load")) : Promise.resolve({ ...detail, id: "receipt-new", decision_text: "Use the revised rollout" }))
      : hub(path));
    render(<DecisionsCore scope="record:receipt-new" />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Record did not load");
    fail = false;
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByText("Use the revised rollout")).toBeInTheDocument();
  });

  it("a committed record names its person in the mast and its commitment in the ledger; no plate asks Commit", async () => {
    const id = COMMITTED.record.id;
    apiFetch.mockImplementation((path: string) => path === `/api/decision-records/${id}` ? Promise.resolve(structuredClone(COMMITTED.record)) : hub(path));
    render(<DecisionsCore scope={`record:${id}`} />);
    expect((await screen.findByTestId("decision-reader-title")).textContent).toBe("Adopt quorumdb");
    expect(screen.getByTestId("decision-reader-committed").textContent).toBe("Committed · Mira Okafor");
    expect(screen.getByTestId("decision-commitment").textContent).toContain("Mira Okafor");
    expect(screen.queryByTestId("decision-reader-commit")).toBeNull();
    expect(screen.getByTestId("decision-spine").querySelector(".surface-spine-part")?.getAttribute("data-tone")).toBe("moss");
  });
});

describe("Decisions: the plate is the one thing that matters now, with its verb", () => {
  // The from-desk producer's record (decision_records.py create_from_desk):
  // source_type desk, source_id the Desk decision, the state read from that
  // decision (decision_record_service `_decorate`).
  const open = {
    id: "rec-open", title: "Drop the nightly export", decision_text: "Drop the nightly export",
    rationale: "About: Payments Platform Rewrite\n\nWhy: The event bus replaces it.",
    alternatives: null, owner: "Mira", review_date: null, lifecycle: "active", status: "proposed",
    source_type: "desk", source_id: "d-open", created_at: "2026-10-27T09:00:00",
    sources: [], work: [], revisions: [], committed_to: null as string | null, successor_id: null as string | null,
  };
  let record = { ...open };
  beforeEach(() => {
    record = { ...open };
    apiFetch.mockImplementation((path: string, init?: { method?: string; json?: unknown }) => {
      if (path === "/api/decision-records/rec-open") return Promise.resolve(structuredClone(record));
      if (path === "/api/decision-records/rec-open/commit" && init?.method === "POST") {
        record = { ...record, committed_to: "Mira" };
        return Promise.resolve({ id: "commitment-rec-open", owner: "Mira", replayed: false });
      }
      if (path === "/api/decisions/d-open/supersede" && init?.method === "POST") return Promise.resolve({ decision: { id: "d-next" } });
      if (path === "/api/programs" && init?.method === "POST") return Promise.resolve(CREATED_PROGRAM.response.body);
      return hub(path);
    });
    apiRequest.mockImplementation(async (path: string, init?: RequestInit) => {
      if (!path.endsWith("/status")) return new Response("{}", { status: 200 });
      record = { ...record, status: JSON.parse(String(init?.body)).status };
      return new Response(JSON.stringify({ decision: { id: "d-open", status: record.status } }), { status: 200 });
    });
  });

  it("a proposal waits on him: Decide writes the Desk decision's state; the plate becomes Commit", async () => {
    render(<DecisionsCore scope="record:rec-open" />);
    const decide = await screen.findByTestId("decision-reader-accept");
    expect(decide.textContent).toBe("Decide");
    expect(screen.getByTestId("decisions-plate").getAttribute("data-tone")).toBe("brass");
    expect(screen.queryByTestId("decision-reader-send")).toBeNull();
    expect(screen.queryByTestId("decision-reader-program")).toBeNull();
    expect(screen.getByTestId("decision-reader-state").textContent).toBe("Proposed");
    fireEvent.click(decide);
    await waitFor(() => expect(apiRequest).toHaveBeenCalledWith("/api/decisions/d-open/status", expect.objectContaining({ method: "PUT" })));
    const write = apiRequest.mock.calls.find(([path]) => String(path).endsWith("/status"))!;
    expect(JSON.parse(String(write[1].body))).toEqual({ status: "accepted" });
    await waitFor(() => expect(screen.getByTestId("decision-reader-commit")).toBeTruthy());
    expect(screen.queryByTestId("decision-reader-accept")).toBeNull();
    expect(screen.getByTestId("decision-reader-send")).toBeTruthy();
  });

  it("a refused Decide says so in words and keeps the proposal", async () => {
    apiRequest.mockImplementation(async (path: string) => new Response("{}", { status: String(path).endsWith("/status") ? 503 : 200 }));
    render(<DecisionsCore scope="record:rec-open" />);
    fireEvent.click(await screen.findByTestId("decision-reader-accept"));
    expect((await screen.findByTestId("decision-reader-failure")).textContent).toBe("Could not decide it · Not available now");
    expect(screen.getByTestId("decision-reader-state").textContent).toBe("Proposed");
  });

  it("a decided record no one owns: Commit makes the commitment (the declared operation); the mast names it", async () => {
    record = { ...open, status: "accepted" };
    render(<DecisionsCore scope="record:rec-open" />);
    const commit = await screen.findByTestId("decision-reader-commit");
    expect(screen.getByTestId("decisions-plate").textContent).toContain("Commit to Mira");
    fireEvent.click(commit);
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/api/decision-records/rec-open/commit", { method: "POST", json: { who: "Mira" } }));
    expect((await screen.findByTestId("decision-reader-committed")).textContent).toBe("Committed · Mira");
    expect(screen.queryByTestId("decision-reader-commit")).toBeNull();
  });

  it("a superseded record: Open the new one opens its successor", async () => {
    record = { ...open, status: "accepted", lifecycle: "superseded", successor_id: "receipt-abcdef0123456789" };
    render(<DecisionsCore scope="record:rec-open" />);
    const next = await screen.findByTestId("decision-reader-successor");
    expect(screen.getByTestId("decisions-plate").getAttribute("data-tone")).toBe("graphite");
    fireEvent.click(next);
    expect((await screen.findByTestId("decision-reader-title")).textContent).toBe(detail.decision_text);
  });

  it("a disputed record is at risk: Resolve makes the newer decision and opens it", async () => {
    record = { ...open, status: "accepted", lifecycle: "disputed" };
    render(<DecisionsCore scope="record:rec-open" />);
    const resolve = await screen.findByTestId("decision-reader-resolve");
    expect(screen.getByTestId("decisions-plate").getAttribute("data-tone")).toBe("coral");
    fireEvent.click(resolve);
    await waitFor(() => expect(openRef).toHaveBeenCalledWith("desk_decision:d-next"));
  });

  it("Edit opens the Desk decision's editor in this pane", async () => {
    apiFetch.mockImplementation((path: string) => {
      if (path === "/api/decision-records/rec-open") return Promise.resolve(structuredClone(record));
      if (path === "/api/decisions/d-open") return Promise.resolve({ decision: {
        id: "d-open", title: "Drop the nightly export", decision_markdown: "Drop the nightly export",
        context_markdown: "About: Payments Platform Rewrite", consequences_markdown: "Why: The event bus replaces it.",
      } });
      return hub(path);
    });
    render(<DecisionsCore scope="record:rec-open" />);
    fireEvent.click(await screen.findByTestId("decision-reader-edit"));
    expect(await screen.findByRole("textbox", { name: "Decision" })).toHaveValue("Drop the nightly export");
    expect(screen.getByRole("textbox", { name: "Background" })).toHaveValue("About: Payments Platform Rewrite");
    fireEvent.click(screen.getByTestId("decision-reader-cancel"));
    expect(screen.queryByRole("textbox", { name: "Decision" })).toBeNull();
  });

  it("Run as a program in the mast makes a program from the decision and opens it", async () => {
    record = { ...open, status: "accepted", sources: [{ source_type: "project", source_ref: "proj-holdspeak" }] as never };
    render(<DecisionsCore scope="record:rec-open" />);
    const mast = await screen.findByTestId("decision-mast");
    const verb = await screen.findByRole("button", { name: "Run as a program: Drop the nightly export" });
    expect(mast.contains(verb)).toBe(true);
    fireEvent.click(verb);
    await waitFor(() => expect(openProgram).toHaveBeenCalledWith(CREATED_PROGRAM.response.body.id));
    const posted = apiFetch.mock.calls.filter(([path, init]) => path === "/api/programs" && init?.method === "POST");
    expect(posted.map(([, init]) => init.json)).toEqual([{
      title: "Drop the nightly export", goal: `Drop the nightly export\n\n${open.rationale}`, template: "fast-cycle",
      origin_ref: "decision_record:rec-open", project_id: "proj-holdspeak",
    }]);
  });
});
