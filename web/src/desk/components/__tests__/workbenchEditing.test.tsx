// HS-132-07 — Workbench edits hold.
//
// Four honesty defects, four proofs: the item body keeps every character it
// was given (and hands the hub one PUT per pause), the drop overlay names
// what the payload under the cursor will really do, RUN names what is
// missing instead of standing bare, and the empty runs ledger offers the
// step that ends it.
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../../api";
import { useDesk } from "../../store";
import { clearWriteFailure } from "../../hooks/useWriteReceipt";
import { deskQueryClient, deskResourceKey } from "../../../lib/queryClient";
import * as MicCapture from "../MicButton";
import { workbenchVoiceGrammar } from "../../voice/grammars/workbench";
import {
  BODY_SAVE_PAUSE_MS,
  WorkbenchWindow,
  dropIntentLabel,
  dropTypes,
  workbenchDropVerb,
} from "../WorkbenchWindow";

vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    lastFrame: null,
    subscribe: () => () => undefined,
  }),
}));

const ITEM = {
  id: "i-1",
  title: "Draft the brief",
  body: "",
  priority: 3,
  status: "pending",
  grounding: {},
  result: null,
  result_egress: null,
  result_artifact_id: null,
  artifact_status: null,
  mint_attempted: false,
  tokens_consumed: 0,
  created_at: "2026-01-01T00:00:00Z",
  completed_at: null,
};

function detail(overrides: Record<string, unknown> = {}) {
  return {
    id: "wb1",
    name: "Daily",
    recipe_id: "r1",
    profile_id: "p1",
    schedule: null,
    schedule_enabled: false,
    items: [ITEM],
    last_run: null,
    ...overrides,
  };
}

// Real isolated-hub GET /api/workbenches/workbench_6ad52d3c08af, captured
// 2026-10-15 by the visual-refinement rig (base 94551006a). The pending
// item was created through POST workbench + POST item; Runs/Memory were
// {runs: []}/{entries: []}. Kept here so the test has no scratch dependency.
const RECORDED_READ_DETAIL = {
  id: "workbench_6ad52d3c08af", name: "Architecture review",
  recipe_id: null, profile_id: null, resolver_profile_id: null,
  schedule: null, schedule_enabled: false, schedule_revision: 1,
  item_order: [], created_at: "2026-10-15T06:33:38Z",
  last_modified: "2026-10-15T06:33:38Z", deleted: false,
  items: [{
    id: "wbi_cc3626366ca7", workbench_id: "workbench_6ad52d3c08af",
    title: "Review the migration", body: "Confirm rollback ownership and the release gate.",
    priority: 3, status: "pending", grounding: {}, context: {},
    result: null, result_artifact_id: null, result_egress: null,
    tokens_consumed: 0, created_at: "2026-10-15T06:33:38Z",
    last_modified: "2026-10-15T06:33:38Z", claimed_at: null,
    completed_at: null, parked: false,
  }],
  item_count: 1, pending_count: 1, last_run: null,
  assignment_summary: { status: "no_assignment", source: null, chain: [], repair: "Choose default" },
};

/** The hub takes every write; GETs answer the same detail every time. */
function mockHub(wb: Record<string, unknown>) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const json = (body: unknown, status = 200) =>
      new Response(JSON.stringify(body), {
        status,
        headers: { "content-type": "application/json" },
      });
    if ((init?.method || "GET").toUpperCase() !== "GET") return json({ ok: true });
    if (/\/runs$/.test(url)) return json({ runs: [] });
    if (/\/memory$/.test(url)) return json({ entries: [] });
    if (/\/api\/skills/.test(url)) return json({ skills: [] });
    if (url.endsWith(`/api/workbenches/${wb.id}`)) return json({ workbench: wb });
    return json({});
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

/** The rendered document root, for the class-addressed chrome (receipt
 * line, drop overlay) that carries no role of its own. */
let dom: HTMLElement;

async function openWindow(wb: Record<string, unknown> = detail()) {
  const fetchMock = mockHub(wb);
  return { fetchMock, ...(await mount()) };
}

async function mount(workbenchId = "wb1", itemTitle = "Draft the brief") {
  useDesk.setState({
    items: {
      ...EMPTY_ITEMS,
      workbench: [{ kind: "workbench", id: workbenchId, name: "Daily" } as never],
    },
    inferenceTargets: [],
    profiles: [],
  });
  const view = render(<WorkbenchWindow workbenchId={workbenchId} />);
  dom = view.baseElement as HTMLElement;
  await screen.findByText(itemTitle);
  return view;
}

const receiptText = () =>
  dom.querySelector(".write-receipt-label")?.textContent || "";
const dropChip = () => dom.querySelector(".wb-drop-zone");
const wbBody = () => dom.querySelector(".wb-body") as HTMLElement;

function itemPuts(fetchMock: ReturnType<typeof vi.fn>) {
  return fetchMock.mock.calls.filter(
    ([input, init]) =>
      (init as RequestInit | undefined)?.method === "PUT" &&
      /\/items\//.test(String(input)),
  );
}

describe("HS-132-07 item body draft", () => {
  beforeEach(() => {
    localStorage.clear();
    clearWriteFailure();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  // The audit's probe, kept: two rapid changes used to arrive as "a","b"
  // (each keystroke PUT + refetch overwrote the well). The draft holds both.
  it("keeps every character of a fast burst and saves once per pause", async () => {
    const { fetchMock } = await openWindow();
    await userEvent.setup().click(screen.getByText("Draft the brief"));
    const pad = screen.getByLabelText("Item body") as HTMLTextAreaElement;

    fireEvent.change(pad, { target: { value: "a" } });
    fireEvent.change(pad, { target: { value: "ab" } });

    // Mid-burst: the characters are on screen and the hub has not been asked.
    expect(pad).toHaveValue("ab");
    expect(itemPuts(fetchMock)).toHaveLength(0);

    await waitFor(() => expect(itemPuts(fetchMock)).toHaveLength(1), {
      timeout: BODY_SAVE_PAUSE_MS + 1500,
    });
    const [, init] = itemPuts(fetchMock)[0];
    expect(JSON.parse(String((init as RequestInit).body))).toEqual({ body: "ab" });
    // One PUT for the burst, not one per keystroke.
    await new Promise((r) => setTimeout(r, BODY_SAVE_PAUSE_MS));
    expect(itemPuts(fetchMock)).toHaveLength(1);
    expect(pad).toHaveValue("ab");
  });

  it("names a refused body save and keeps the typed text", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const json = (body: unknown, status = 200) =>
        new Response(JSON.stringify(body), {
          status,
          headers: { "content-type": "application/json" },
        });
      if ((init?.method || "GET").toUpperCase() !== "GET") return json({}, 500);
      if (/\/runs$/.test(url)) return json({ runs: [] });
      if (/\/memory$/.test(url)) return json({ entries: [] });
      if (/\/api\/skills/.test(url)) return json({ skills: [] });
      if (/\/api\/workbenches\/wb1$/.test(url)) return json({ workbench: detail() });
      return json({});
    });
    vi.stubGlobal("fetch", fetchMock);
    await mount();
    await userEvent.setup().click(screen.getByText("Draft the brief"));
    const pad = screen.getByLabelText("Item body") as HTMLTextAreaElement;
    fireEvent.change(pad, { target: { value: "keep me" } });

    await waitFor(
      () =>
        expect(receiptText()).toBe("SAVE ITEM FAILED · HTTP 500"),
      { timeout: BODY_SAVE_PAUSE_MS + 1500 },
    );
    expect(pad).toHaveValue("keep me");
  });

  it.each(["Keep this instruction", ""])("flushes a closing instruction and recovers the refused snapshot %j", async (body) => {
    const wb = detail({ items: [{ ...ITEM, body: "Saved instruction" }] });
    const fetchMock = mockHub(wb);
    const read = fetchMock.getMockImplementation()!;
    fetchMock.mockImplementation(async (input, init) => init?.method === "PUT"
      ? new Response(JSON.stringify({ error: "Unavailable" }), { status: 503, headers: { "content-type": "application/json" } })
      : read(input, init));
    const view = await mount();
    fireEvent.click(screen.getByText("Draft the brief"));
    fireEvent.change(screen.getByLabelText("Item body"), { target: { value: body } });
    expect(itemPuts(fetchMock)).toHaveLength(0);
    view.unmount();
    await waitFor(() => expect(itemPuts(fetchMock)).toHaveLength(1));
    expect(JSON.parse(String(itemPuts(fetchMock)[0][1]?.body))).toEqual({ body });
    expect(useDesk.getState().drafts["workbench/wb1/item/i-1/body"]).toBe(body);
    await mount();
    fireEvent.click(screen.getByText("Draft the brief"));
    expect(screen.getByLabelText("Item body")).toHaveValue(body);
    expect(itemPuts(fetchMock)).toHaveLength(1);
  });

  it("keeps the next instruction while an older body save lands", async () => {
    const { fetchMock, unmount } = await openWindow();
    const read = fetchMock.getMockImplementation()!;
    let release!: (response: Response) => void;
    fetchMock.mockImplementation((input, init) => init?.method === "PUT"
      ? new Promise<Response>((resolve) => { release = resolve; }) : read(input, init));
    fireEvent.click(screen.getByText("Draft the brief"));
    fireEvent.change(screen.getByLabelText("Item body"), { target: { value: "First instruction" } });
    await waitFor(() => expect(release).toBeTypeOf("function"), { timeout: BODY_SAVE_PAUSE_MS + 1500 });
    fireEvent.change(screen.getByLabelText("Item body"), { target: { value: "Newer instruction" } });
    await act(async () => { release(new Response("{}", { headers: { "content-type": "application/json" } })); });
    expect(screen.getByLabelText("Item body")).toHaveValue("Newer instruction");
    expect(useDesk.getState().drafts["workbench/wb1/item/i-1/body"]).toBe("Newer instruction");
    fetchMock.mockImplementation(read);
    unmount();
    await waitFor(() => expect(itemPuts(fetchMock)).toHaveLength(2));
  });

  it.each(["Closing instruction B", ""])("orders a closing body %j behind the pending older save across reopen", async (body) => {
    const wb = detail({ items: [{ ...ITEM, body: body ? "Original instruction" : "" }] });
    const fetchMock = mockHub(wb);
    const read = fetchMock.getMockImplementation()!;
    const writes: Array<{ body: string; resolve(): void }> = [];
    fetchMock.mockImplementation((input, init) => init?.method === "PUT"
      ? new Promise<Response>((resolve) => {
        const sent = JSON.parse(String(init.body)).body as string;
        writes.push({ body: sent, resolve: () => {
          wb.items = [{ ...ITEM, body: sent }];
          resolve(new Response("{}", { headers: { "content-type": "application/json" } }));
        } });
      }) : read(input, init));
    const view = await mount();
    fireEvent.click(screen.getByText("Draft the brief"));
    fireEvent.change(screen.getByLabelText("Item body"), { target: { value: "Pending instruction A" } });
    await waitFor(() => expect(writes).toHaveLength(1), { timeout: BODY_SAVE_PAUSE_MS + 1500 });
    fireEvent.change(screen.getByLabelText("Item body"), { target: { value: body } });
    view.unmount();
    await mount();
    fireEvent.click(screen.getByText("Draft the brief"));
    expect(screen.getByLabelText("Item body")).toHaveValue(body);
    // B cannot complete before A: it has not been sent yet.
    expect(writes).toHaveLength(1);
    expect(useDesk.getState().drafts["workbench/wb1/item/i-1/body"]).toBe(body);
    await act(async () => { writes[0].resolve(); });
    await waitFor(() => expect(writes).toHaveLength(2));
    expect(writes[1].body).toBe(body);
    expect(screen.getByLabelText("Item body")).toHaveValue(body);
    await act(async () => { writes[1].resolve(); });
    await waitFor(() => expect(useDesk.getState().drafts["workbench/wb1/item/i-1/body"]).toBeUndefined());
    expect(wb.items[0].body).toBe(body);
    expect(screen.getByLabelText("Item body")).toHaveValue(body);
    expect(itemPuts(fetchMock)).toHaveLength(2);
  });
});

describe("Workbench independent reads", () => {
  beforeEach(() => { localStorage.clear(); clearWriteFailure(); });
  afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks(); });

  it.each([
    { wing: "Runs", suffix: "runs", empty: "No agent bound" },
    { wing: "Memory", suffix: "memory", empty: "No memories yet" },
  ])("names a failed $wing read and retries only that read", async ({ wing, suffix, empty }) => {
    const fetchMock = mockHub(RECORDED_READ_DETAIL);
    const read = fetchMock.getMockImplementation()!;
    let unavailable = true;
    fetchMock.mockImplementation(async (input, init) => String(input).endsWith(`/${suffix}`) && (!init?.method || init.method === "GET")
      ? new Response(JSON.stringify(unavailable ? { error: "Read unavailable" } : suffix === "runs" ? { runs: [] } : { entries: [] }), {
        status: unavailable ? 503 : 200,
        headers: { "content-type": "application/json" },
      }) : read(input, init));
    await mount(RECORDED_READ_DETAIL.id, RECORDED_READ_DETAIL.items[0].title);
    fireEvent.change(screen.getByRole("combobox", { name: "New item instruction" }), { target: { value: "Keep the next instruction" } });
    fireEvent.click(screen.getByRole("tab", { name: wing }));

    expect(await screen.findByRole("alert")).toHaveTextContent(new RegExp(wing, "i"));
    expect(screen.queryByText(empty)).toBeNull();
    expect(screen.queryByRole("button", { name: "Run now" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Bind an agent" })).toBeNull();
    const readsBeforeRetry = fetchMock.mock.calls.filter(([input]) => String(input).endsWith(`/${suffix}`)).length;
    const detailPath = `/workbenches/${RECORDED_READ_DETAIL.id}`;
    const detailReadsBeforeRetry = fetchMock.mock.calls.filter(([input]) => String(input).endsWith(detailPath)).length;
    unavailable = false;
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));

    await screen.findByText(empty);
    expect(screen.queryByRole("alert")).toBeNull();
    expect(fetchMock.mock.calls.filter(([input]) => String(input).endsWith(`/${suffix}`))).toHaveLength(readsBeforeRetry + 1);
    expect(fetchMock.mock.calls.filter(([input]) => String(input).endsWith(detailPath))).toHaveLength(detailReadsBeforeRetry);
    expect(fetchMock.mock.calls.filter(([input, init]) => String(input).endsWith("/run") && init?.method === "POST")).toHaveLength(0);
    fireEvent.click(screen.getByRole("tab", { name: "Items" }));
    expect(screen.getByText(RECORDED_READ_DETAIL.items[0].title)).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "New item instruction" })).toHaveValue("Keep the next instruction");
  });

  it("keeps known memory and its disclosure while a refresh fails, then retries the read", async () => {
    const entry = {
      run_id: "run-memory", kind: "observation", content: "Keep the rollback owner in the next brief.",
      item_title: "Draft the brief", timestamp: "2026-10-15T06:33:38Z", provenance: { model: "local-model" },
    };
    const fetchMock = mockHub(detail());
    const read = fetchMock.getMockImplementation()!;
    let unavailable = false;
    fetchMock.mockImplementation(async (input, init) => String(input).endsWith("/memory") && (!init?.method || init.method === "GET")
      ? new Response(JSON.stringify(unavailable ? { error: "Read unavailable" } : { entries: [entry] }), {
        status: unavailable ? 503 : 200, headers: { "content-type": "application/json" },
      }) : read(input, init));
    await mount();
    fireEvent.click(screen.getByRole("tab", { name: "Memory" }));
    await screen.findByText(entry.content);
    fireEvent.click(screen.getByRole("button", { name: new RegExp(entry.content) }));
    expect(screen.getByRole("button", { name: "Promote to skill" })).toBeInTheDocument();

    unavailable = true;
    await act(async () => { await deskQueryClient.invalidateQueries({ queryKey: deskResourceKey("workbench-memory", "wb1") }); });

    expect(await screen.findByRole("alert")).toHaveTextContent(/Memory/i);
    expect(screen.getAllByText(entry.content)).toHaveLength(2);
    expect(screen.getByRole("button", { name: "Promote to skill" })).toBeInTheDocument();
    expect(screen.queryByText("No memories yet")).toBeNull();
    unavailable = false;
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
    expect(screen.getAllByText(entry.content)).toHaveLength(2);
  });

  it("opens the linked artifact without repeating its result in the item", async () => {
    const output = "Rollback ownership is confirmed.";
    await openWindow(detail({ items: [{ ...ITEM, status: "done", result: output, result_artifact_id: "artifact-result" }] }));
    const open = vi.spyOn(useDesk.getState(), "openPullout").mockImplementation(() => undefined);
    fireEvent.click(screen.getByText("Draft the brief"));
    expect(screen.getAllByText(output)).toHaveLength(1);

    fireEvent.click(screen.getByRole("button", { name: "Open artifact" }));

    await waitFor(() => expect(open).toHaveBeenCalledWith("artifact:artifact-result"));
    expect(screen.getAllByText(output)).toHaveLength(1);
    expect(screen.queryByText("artifact-result", { exact: true })).toBeNull();
    expect(screen.queryByRole("button", { name: "Collapse" })).toBeNull();
    expect(screen.getByRole("button", { name: "Copy" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Re-run" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Park" })).toBeInTheDocument();
  });
});

describe("Workbench inlet draft custody", () => {
  beforeEach(() => { localStorage.clear(); clearWriteFailure(); });
  afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks(); });

  const inletKey = "workbench/wb1/inlet";
  const instruction = "Review release ownership with the team and keep the complete source instruction after returning.";

  it("seats a visible multiline instruction and primary Add in the named inset", async () => {
    await openWindow();
    const group = screen.getByRole("region", { name: "Add item" });
    expect(group).toHaveAttribute("data-material", "inset");
    expect(within(group).getByText("Instruction", { exact: true })).toBeVisible();
    expect(within(group).getByRole("combobox", { name: "New item instruction" }).tagName).toBe("TEXTAREA");
    const add = within(group).getByRole("button", { name: "Add" });
    expect(add).toHaveClass("btn--primary");
    expect(add.closest("footer")).toHaveClass("gadget-group-actions");
    expect(within(group).getAllByRole("button", { name: /^Speak(?: ·|$)/ })).toHaveLength(1);
    fireEvent.click(screen.getByText("Draft the brief"));
    expect(within(screen.getByRole("region", { name: "Instruction" })).getByRole("textbox", { name: "Item body" })).toBeInTheDocument();
  });

  it("the single grammar mic fills the paired Pad and sends its complete instruction and source through Add", async () => {
    // Observe the existing real MicButton and inject at its transcription
    // callback boundary; capture hardware and provider egress are not exercised.
    const capture = vi.spyOn(MicCapture, "MicButton");
    const fetchMock = mockHub(RECORDED_READ_DETAIL);
    const read = fetchMock.getMockImplementation()!;
    fetchMock.mockImplementation(async (input, init) => String(input).endsWith("/voice/resolve")
      ? new Response(JSON.stringify({ refs: [] }), { headers: { "content-type": "application/json" } })
      : read(input, init));
    await mount(RECORDED_READ_DETAIL.id, RECORDED_READ_DETAIL.items[0].title);
    act(() => useDesk.setState({ items: { ...useDesk.getState().items, directory: [
      { kind: "directory", id: "release", name: "Release sources", nameNormalized: "release sources", memberIds: [] } as never,
    ] } }));
    const group = screen.getByRole("region", { name: "Add item" });
    expect(within(group).getAllByRole("button", { name: /^Speak(?: ·|$)/ })).toHaveLength(1);
    const authority = capture.mock.calls.find(([props]) => props.draftScope === `workbench:${RECORDED_READ_DETAIL.id}`)?.[0];
    expect(authority?.grammar).toBe(workbenchVoiceGrammar);
    expect(authority?.onProposalConfirm).toBeTypeOf("function");
    const pad = within(group).getByRole("combobox", { name: "New item instruction" });
    fireEvent.change(pad, { target: { value: "Review.\nConfirm rollback owner." } });
    // Read the latest controlled callback after the typed draft changed.
    const latest = capture.mock.calls.filter(([props]) => props.draftScope === `workbench:${RECORDED_READ_DETAIL.id}`).at(-1)![0];
    await act(async () => { latest.onText("Use Release sources."); });
    const complete = "Review.\nConfirm rollback owner. Use Release sources.";
    expect(pad).toHaveValue(complete);
    expect(within(group).getByRole("button", { name: "Remove Release sources" })).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([path, init]) => String(path).endsWith("/voice/resolve") && JSON.parse(String(init?.body)).transcript === "Use Release sources.")).toBe(true);
    fireEvent.click(within(group).getByRole("button", { name: "Add" }));
    await waitFor(() => expect(pad).toHaveValue(""));
    const posts = fetchMock.mock.calls.filter(([path, init]) => String(path).endsWith("/items") && init?.method === "POST");
    expect(posts).toHaveLength(1);
    expect(JSON.parse(String(posts[0][1]?.body))).toEqual({
      title: complete, body: complete, priority: 3, grounding: { refs: ["zone:release"] },
    });
  });

  it("keeps Shift+Enter as a newline and Enter submits the complete instruction once", async () => {
    const { fetchMock } = await openWindow();
    const user = userEvent.setup();
    const input = screen.getByRole("combobox", { name: "New item instruction" });
    await user.type(input, "Review the plan");
    await user.keyboard("{Shift>}{Enter}{/Shift}Confirm rollback ownership");
    expect(input).toHaveValue("Review the plan\nConfirm rollback ownership");
    const posts = () => fetchMock.mock.calls.filter(([path, init]) => String(path).endsWith("/items") && init?.method === "POST");
    expect(posts()).toHaveLength(0);
    await user.keyboard("{Enter}");
    await waitFor(() => expect(posts()).toHaveLength(1));
    expect(JSON.parse(String(posts()[0][1]?.body))).toEqual({
      title: "Review the plan\nConfirm rollback ownership", body: "Review the plan\nConfirm rollback ownership", priority: 3,
    });
  });

  it("selects a typed source before Add and keeps pasted @ as instruction text", async () => {
    const previousScroll = Object.getOwnPropertyDescriptor(HTMLElement.prototype, "scrollIntoView");
    Object.defineProperty(HTMLElement.prototype, "scrollIntoView", { configurable: true, value: vi.fn() });
    try {
    const { fetchMock } = await openWindow();
    act(() => useDesk.setState({ items: { ...useDesk.getState().items, directory: [
      { kind: "directory", id: "release", name: "Release sources", nameNormalized: "release sources", memberIds: [] } as never,
    ] } }));
    const user = userEvent.setup();
    const input = screen.getByRole("combobox", { name: "New item instruction" });
    await user.type(input, "Review @Rel");
    expect(input).toHaveAttribute("aria-expanded", "true");
    await user.keyboard("{Enter}");
    expect(input).toHaveValue("Review");
    expect(input).toHaveFocus();
    expect(screen.getByRole("button", { name: "Remove Release sources" })).toBeInTheDocument();
    expect(fetchMock.mock.calls.filter(([path, init]) => String(path).endsWith("/items") && init?.method === "POST")).toHaveLength(0);
    fireEvent.paste(input);
    fireEvent.change(input, { target: { value: "Review @Release sources" } });
    expect(input).toHaveAttribute("aria-expanded", "false");
    await user.keyboard("{Enter}");
    await waitFor(() => expect(fetchMock.mock.calls.filter(([path, init]) => String(path).endsWith("/items") && init?.method === "POST")).toHaveLength(1));
    const post = fetchMock.mock.calls.find(([path, init]) => String(path).endsWith("/items") && init?.method === "POST")!;
    expect(JSON.parse(String(post[1]?.body))).toMatchObject({ body: "Review @Release sources", grounding: { refs: ["zone:release"] } });
    } finally {
      if (previousScroll) Object.defineProperty(HTMLElement.prototype, "scrollIntoView", previousScroll);
      else Reflect.deleteProperty(HTMLElement.prototype, "scrollIntoView");
    }
  });

  it("keeps the successful detail and composer when an aggregate read loses the workbench bucket", async () => {
    await openWindow();
    fireEvent.change(screen.getByRole("combobox", { name: "New item instruction" }), { target: { value: instruction } });
    act(() => useDesk.setState({ items: { ...useDesk.getState().items, workbench: [] } }));
    expect(screen.getByText("Draft the brief")).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "New item instruction" })).toHaveValue(instruction);
    expect(screen.getByRole("button", { name: "Edit Workbench name" })).toHaveTextContent("Daily");
    fireEvent.click(screen.getByRole("button", { name: "Add" }));
    await waitFor(() => expect(screen.getByRole("combobox", { name: "New item instruction" })).toHaveValue(""));
    expect(screen.getByText("Draft the brief")).toBeInTheDocument();
  });

  it("keeps the full instruction, priority and source references across close and reopen without submitting", async () => {
    const { fetchMock, unmount } = await openWindow();
    fireEvent.change(screen.getByRole("combobox", { name: "New item instruction" }), { target: { value: instruction } });
    fireEvent.click(screen.getByRole("button", { name: "P3" }));
    act(() => {
      const draft = JSON.parse(useDesk.getState().drafts[inletKey]);
      useDesk.getState().setDraft(inletKey, JSON.stringify({ ...draft, refs: [{ id: "dir-release", kind: "zone", ref: "zone:dir-release", name: "Release sources" }] }));
    });
    unmount();
    await mount();
    expect(screen.getByRole("combobox", { name: "New item instruction" })).toHaveValue(instruction);
    await waitFor(() => expect(screen.getByRole("button", { name: "P1" })).toBeVisible());
    await waitFor(() => expect(screen.getByText("Release sources")).toBeVisible());
    expect(fetchMock.mock.calls.filter(([input, init]) => String(input).endsWith("/items") && init?.method === "POST")).toHaveLength(0);
  });

  it("keeps a refused Add and its references, then clears only after Retry accepts that snapshot", async () => {
    const { fetchMock } = await openWindow();
    const read = fetchMock.getMockImplementation()!;
    let accepted = false;
    fetchMock.mockImplementation(async (input, init) => String(input).endsWith("/items") && init?.method === "POST"
      ? new Response(JSON.stringify({ error: "Unavailable" }), { status: accepted ? 200 : 503, headers: { "content-type": "application/json" } }) : read(input, init));
    fireEvent.change(screen.getByRole("combobox", { name: "New item instruction" }), { target: { value: instruction } });
    fireEvent.click(screen.getByRole("button", { name: "Add" }));
    await waitFor(() => expect(receiptText()).toContain("ADD ITEM FAILED"));
    expect(screen.getByRole("combobox", { name: "New item instruction" })).toHaveValue(instruction);
    expect(useDesk.getState().drafts[inletKey]).toContain(instruction);
    accepted = true;
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(screen.getByRole("combobox", { name: "New item instruction" })).toHaveValue(""));
    expect(useDesk.getState().drafts[inletKey]).toBeUndefined();
  });

  it("does not erase the next instruction typed while Add is in flight", async () => {
    const { fetchMock } = await openWindow();
    const read = fetchMock.getMockImplementation()!;
    let release!: (response: Response) => void;
    fetchMock.mockImplementation((input, init) => String(input).endsWith("/items") && init?.method === "POST"
      ? new Promise<Response>((resolve) => { release = resolve; }) : read(input, init));
    fireEvent.change(screen.getByRole("combobox", { name: "New item instruction" }), { target: { value: instruction } });
    fireEvent.click(screen.getByRole("button", { name: "Add" }));
    await waitFor(() => expect(release).toBeTypeOf("function"));
    fireEvent.change(screen.getByRole("combobox", { name: "New item instruction" }), { target: { value: "Keep this next instruction" } });
    await act(async () => { release(new Response("{}", { status: 200, headers: { "content-type": "application/json" } })); });
    expect(screen.getByRole("combobox", { name: "New item instruction" })).toHaveValue("Keep this next instruction");
    expect(useDesk.getState().drafts[inletKey]).toContain("Keep this next instruction");
  });

  it("allows one Add or exact Retry in flight while retaining the next inlet", async () => {
    const { fetchMock } = await openWindow();
    const read = fetchMock.getMockImplementation()!;
    let release!: (response: Response) => void;
    fetchMock.mockImplementation((input, init) => String(input).endsWith("/items") && init?.method === "POST"
      ? new Promise<Response>((resolve) => { release = resolve; }) : read(input, init));
    const field = screen.getByRole("combobox", { name: "New item instruction" });
    const add = screen.getByRole("button", { name: "Add" });
    const posts = () => fetchMock.mock.calls.filter(([input, init]) => String(input).endsWith("/items") && init?.method === "POST");
    fireEvent.change(field, { target: { value: instruction } });
    fireEvent.click(add);
    fireEvent.click(add);
    expect(add).toBeDisabled();
    expect(posts()).toHaveLength(1);
    fireEvent.change(field, { target: { value: "Keep the next item" } });
    await act(async () => { release(new Response("{}", { status: 503, headers: { "content-type": "application/json" } })); });
    const retry = screen.getByRole("button", { name: "Retry" });
    fireEvent.click(retry);
    fireEvent.click(retry);
    fireEvent.click(add);
    expect(posts()).toHaveLength(2);
    expect(posts()[1][1]?.body).toBe(posts()[0][1]?.body);
    await act(async () => { release(new Response("{}", { headers: { "content-type": "application/json" } })); });
    expect(field).toHaveValue("Keep the next item");
    expect(useDesk.getState().drafts[inletKey]).toContain("Keep the next item");
  });
});

describe("HS-132-07 drop-target honesty", () => {
  beforeEach(() => {
    localStorage.clear();
    clearWriteFailure();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("names the verb each payload type really gets", () => {
    expect(workbenchDropVerb(["application/x-desk-item"])).toEqual({
      verb: "ADD ITEM",
      accepted: true,
    });
    expect(workbenchDropVerb(["Files"])).toEqual({
      verb: "IMPORT AS MEETING",
      accepted: false,
    });
    expect(workbenchDropVerb(["text/plain"])).toEqual({
      verb: "NOT A WORKBENCH ITEM",
      accepted: false,
    });
    expect(dropIntentLabel(workbenchDropVerb(["Files"]))).toBe(
      "DROP TARGET · IMPORT AS MEETING",
    );
    expect(dropIntentLabel(workbenchDropVerb([]))).toBe(
      "NO DROP · NOT A WORKBENCH ITEM",
    );
    expect(dropTypes({ types: ["Files"] } as unknown as DataTransfer)).toEqual([
      "Files",
    ]);
    expect(dropTypes(null)).toEqual([]);
  });

  it("never promises ADD ITEM for a dragged file", async () => {
    await openWindow();
    const body = wbBody();

    fireEvent.dragOver(body, { dataTransfer: { types: ["Files"] } });
    expect(dropChip()?.textContent).toBe(
      "DROP TARGET · IMPORT AS MEETING",
    );

    fireEvent.dragOver(body, {
      dataTransfer: { types: ["application/x-desk-item"] },
    });
    expect(dropChip()?.textContent).toBe(
      "DROP TARGET · ADD ITEM",
    );

    fireEvent.dragOver(body, { dataTransfer: { types: ["text/uri-list"] } });
    expect(dropChip()?.textContent).toBe(
      "NO DROP · NOT A WORKBENCH ITEM",
    );

    fireEvent.dragLeave(body);
    expect(dropChip()).toBeNull();
  });

  it("leaves a dropped file to the desk and names a refused payload", async () => {
    const { fetchMock } = await openWindow();
    const body = wbBody();
    const posts = () =>
      fetchMock.mock.calls.filter(
        ([, init]) => (init as RequestInit | undefined)?.method === "POST",
      ).length;

    fireEvent.drop(body, {
      dataTransfer: { types: ["Files"], getData: () => "" },
    });
    await waitFor(() => expect(dropChip()).toBeNull());
    // The workbench never claimed it: no item was minted here.
    expect(posts()).toBe(0);
    expect(receiptText()).toBe("");

    fireEvent.drop(body, {
      dataTransfer: { types: ["text/plain"], getData: () => "" },
    });
    await waitFor(() =>
      expect(receiptText()).toBe("DROP TO WORK FAILED · NOT A WORKBENCH ITEM"),
    );
  });
});

describe("HS-143-13 canonical workbench assignments", () => {
  beforeEach(() => {
    localStorage.clear();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("mounts the two exact workbench subject summaries instead of target pickers", async () => {
    const { container } = await openWindow();
    await userEvent.setup().click(screen.getByRole("button", { name: "Configure" }));
    expect(container.querySelector('[data-capability="workbench.item"]')).toBeInTheDocument();
    expect(container.querySelector('[data-capability="voice.reference_resolve"]')).toBeInTheDocument();
    expect(screen.queryByRole("combobox", { name: /runs on|resolves with/i })).toBeNull();
  });
});

describe("HS-132-07 no bare disabled control", () => {
  beforeEach(() => {
    localStorage.clear();
    clearWriteFailure();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("names the missing agent on RUN and offers the next step", async () => {
    await openWindow(detail({ recipe_id: null }));
    const run = screen.getByRole("button", { name: /^Run:/ });
    expect(run).toBeDisabled();
    expect(run).toHaveAttribute("title", "Bind an agent first");

    await userEvent.setup().click(screen.getByRole("tab", { name: "Runs" }));
    expect(screen.getByText("No agent bound")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Bind an agent" }),
    ).toBeInTheDocument();
  });

  it("offers RUN NOW from the empty ledger once an agent is bound", async () => {
    await openWindow();
    const run = screen.getByRole("button", { name: "Run this workbench now" });
    expect(run).toBeEnabled();

    await userEvent.setup().click(screen.getByRole("tab", { name: "Runs" }));
    expect(screen.getByText("No runs yet")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Run now" })).toBeInTheDocument();
  });
});
