// HS-132-07 — Workbench edits hold.
//
// Four honesty defects, four proofs: the item body keeps every character it
// was given (and hands the hub one PUT per pause), the drop overlay names
// what the payload under the cursor will really do, RUN names what is
// missing instead of standing bare, and the empty runs ledger offers the
// step that ends it.
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../../api";
import { useDesk } from "../../store";
import { clearWriteFailure } from "../../hooks/useWriteReceipt";
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
    if (/\/api\/workbenches\/wb1$/.test(url)) return json({ workbench: wb });
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

async function mount() {
  useDesk.setState({
    items: {
      ...EMPTY_ITEMS,
      workbench: [{ kind: "workbench", id: "wb1", name: "Daily" } as never],
    },
    inferenceTargets: [],
    profiles: [],
  });
  const view = render(<WorkbenchWindow workbenchId="wb1" />);
  dom = view.baseElement as HTMLElement;
  await screen.findByText("Draft the brief");
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
