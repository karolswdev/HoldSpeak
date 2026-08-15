// HS-132-06 — with the hub refusing, every wired write verb names its
// failure in flow. No verb may look like a no-op.
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Note } from "../../../lib/primitives";
import { EMPTY_ITEMS } from "../../api";
import { floorMenuEntries } from "../../floorMenu";
import type { WorkMenuEntry } from "../DeskMenu";
import { useDesk } from "../../store";
import { clearWriteFailure } from "../../hooks/useWriteReceipt";
import { WorkbenchWindow } from "../WorkbenchWindow";
import { DeskChrome } from "../DeskChrome";
import { EmptyDesk } from "../EmptyDesk";

// Query helper scoped to the render root (testing-library renders into
// document.body, so this equals baseElement.querySelector).
const q = (sel: string): HTMLElement | null => document.body.querySelector(sel);
const qa = (sel: string) => document.body.querySelectorAll(sel);


vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    lastFrame: null,
    subscribe: () => () => undefined,
  }),
}));

const DETAIL = {
  id: "wb1",
  name: "Daily",
  recipe_id: "r1",
  profile_id: "p1",
  schedule: null,
  schedule_enabled: false,
  items: [
    {
      id: "i-pending",
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
    },
    {
      id: "i-mint-failed",
      title: "Summarize the call",
      body: "",
      priority: 3,
      status: "done",
      grounding: {},
      result: "Here is the summary.",
      result_egress: null,
      result_artifact_id: null,
      artifact_status: null,
      mint_attempted: true,
      tokens_consumed: 40,
      created_at: "2026-01-01T00:00:00Z",
      completed_at: "2026-01-01T00:01:00Z",
    },
  ],
  last_run: null,
};

/** GETs answer; every write is refused with HTTP 500. */
function mockHub() {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = (init?.method || "GET").toUpperCase();
    const json = (body: unknown, status = 200) =>
      new Response(JSON.stringify(body), {
        status,
        headers: { "content-type": "application/json" },
      });
    if (method !== "GET") return json({ error: "refused" }, 500);
    if (/\/runs$/.test(url)) return json({ runs: [] });
    if (/\/memory$/.test(url)) return json({ entries: [] });
    if (/\/api\/skills/.test(url)) return json({ skills: [] });
    if (/\/api\/workbenches\/wb1$/.test(url)) return json({ workbench: DETAIL });
    return json({});
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

async function openWindow() {
  useDesk.setState({
    items: {
      ...EMPTY_ITEMS,
      workbench: [{ kind: "workbench", id: "wb1", name: "Daily" } as never],
    },
    inferenceTargets: [],
    profiles: [],
  });
  const view = render(<WorkbenchWindow workbenchId="wb1" />);
  await screen.findByText("Draft the brief");
  return view;
}

async function expand(title: string) {
  await userEvent.setup().click(screen.getByText(title));
}

function receiptText(): string {
  return q(".write-receipt-label")?.textContent || "";
}

describe("HS-132-06 workbench write receipts", () => {
  beforeEach(() => {
    localStorage.clear();
    clearWriteFailure();
    mockHub();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("names a refused ADD ITEM and keeps the typed instruction", async () => {
    const user = userEvent.setup();
    await openWindow();
    const inlet = screen.getByLabelText("New item instruction");
    await user.type(inlet, "Write the memo");
    await user.click(screen.getByRole("button", { name: /GO/ }));

    await waitFor(() =>
      expect(receiptText()).toBe("ADD ITEM FAILED · HTTP 500"),
    );
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
    expect(inlet).toHaveValue("Write the memo");
  });

  it("re-issues the refused add when RETRY is pressed", async () => {
    const user = userEvent.setup();
    const fetchMock = mockHub();
    await openWindow();
    await user.type(screen.getByLabelText("New item instruction"), "Write the memo");
    await user.click(screen.getByRole("button", { name: /GO/ }));
    await waitFor(() => expect(receiptText()).toContain("ADD ITEM FAILED"));

    const posts = () =>
      fetchMock.mock.calls.filter(
        ([, init]) => (init as RequestInit | undefined)?.method === "POST",
      ).length;
    const before = posts();
    await user.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(posts()).toBe(before + 1));
  });

  it("names a refused DISMISS ITEM", async () => {
    const user = userEvent.setup();
    await openWindow();
    await expand("Draft the brief");
    await user.click(screen.getByRole("button", { name: "Dismiss" }));
    await waitFor(() =>
      expect(receiptText()).toBe("DISMISS ITEM FAILED · HTTP 500"),
    );
  });

  it("names a refused RE-RUN ITEM", async () => {
    const user = userEvent.setup();
    await openWindow();
    await expand("Summarize the call");
    await user.click(screen.getByRole("button", { name: "Re-run" }));
    await waitFor(() =>
      expect(receiptText()).toBe("RE-RUN ITEM FAILED · HTTP 500"),
    );
  });

  it("names a refused RETRY MINT", async () => {
    const user = userEvent.setup();
    await openWindow();
    await expand("Summarize the call");
    await user.click(screen.getByRole("button", { name: "Retry mint" }));
    await waitFor(() =>
      expect(receiptText()).toBe("RETRY MINT FAILED · HTTP 500"),
    );
  });

  it("names a refused RUN", async () => {
    const user = userEvent.setup();
    await openWindow();
    await user.click(screen.getByRole("button", { name: /Run/ }));
    await waitFor(() => expect(receiptText()).toBe("RUN FAILED · HTTP 500"));
  });

  it("names a refused DROP TO WORK and a malformed drop", async () => {
    await openWindow();
    const body = q(".wb-body") as HTMLElement;

    fireEvent.drop(body, {
      dataTransfer: {
        getData: () =>
          JSON.stringify([{ kind: "note", id: "n1", title: "Rollout risks" }]),
      },
    });
    await waitFor(() =>
      expect(receiptText()).toBe("DROP TO WORK FAILED · HTTP 500"),
    );

    fireEvent.drop(body, { dataTransfer: { getData: () => "not-json" } });
    await waitFor(() =>
      expect(receiptText()).toBe("DROP TO WORK FAILED · BAD PAYLOAD"),
    );
  });

  it("stays quiet when the hub takes the write", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        const json = (body: unknown) =>
          new Response(JSON.stringify(body), {
            status: 200,
            headers: { "content-type": "application/json" },
          });
        if ((init?.method || "GET").toUpperCase() !== "GET") return json({ ok: true });
        if (/\/runs$/.test(url)) return json({ runs: [] });
        if (/\/memory$/.test(url)) return json({ entries: [] });
        if (/\/api\/skills/.test(url)) return json({ skills: [] });
        if (/\/api\/workbenches\/wb1$/.test(url)) return json({ workbench: DETAIL });
        return json({});
      }),
    );
    const user = userEvent.setup();
    await openWindow();
    await user.type(screen.getByLabelText("New item instruction"), "Write the memo");
    await user.click(screen.getByRole("button", { name: /GO/ }));
    await waitFor(() =>
      expect(screen.getByLabelText("New item instruction")).toHaveValue(""),
    );
    expect(q(".write-receipt")).toBeNull();
  });
});

describe("HS-132-06 desk-floor write receipts", () => {
  beforeEach(() => {
    localStorage.clear();
    clearWriteFailure();
    useDesk.setState({ items: { ...EMPTY_ITEMS }, setup: null, error: "" });
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("names a refused SEED DESK on the empty floor", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify({}), { status: 500 })),
    );
    const user = userEvent.setup();
    render(<EmptyDesk />);
    await user.click(screen.getByRole("button", { name: /Seed the desk/ }));
    await waitFor(() =>
      expect(
        q(".write-receipt-label")?.textContent,
      ).toBe("SEED DESK FAILED · HTTP 500"),
    );
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });

  it("names a refused CREATE NOTE on the empty floor", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        if ((init?.method || "GET").toUpperCase() === "POST")
          return new Response(JSON.stringify({}), { status: 500 });
        return new Response(JSON.stringify({}), {
          status: 200,
          headers: { "content-type": "application/json" },
        });
      }),
    );
    const user = userEvent.setup();
    render(<EmptyDesk />);
    await user.click(screen.getByRole("button", { name: /New Note/ }));
    await waitFor(() =>
      expect(
        q(".write-receipt-label")?.textContent,
      ).toBe("CREATE NOTE FAILED · HTTP 500"),
    );
  });

  it("keeps a landed create quiet", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(JSON.stringify({ note: { id: "n1" } }), {
            status: 200,
            headers: { "content-type": "application/json" },
          }),
      ),
    );
    await useDesk.getState().createPrimitive("note");
    expect(q(".write-receipt")).toBeNull();
    expect(useDesk.getState().error).not.toContain("FAILED");
  });
});

/** The floor menu's own NEW > Note entry — the exact path the right-click runs. */
function floorNewNote() {
  const news = floorMenuEntries().find(
    (e) => e.type === "sub" && e.id === "floor.new",
  ) as Extract<WorkMenuEntry, { type: "sub" }>;
  return news.entries[0] as Extract<WorkMenuEntry, { type: "item" }>;
}

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

describe("HS-132-06 populated-floor write receipts", () => {
  beforeEach(() => {
    localStorage.clear();
    clearWriteFailure();
    // A populated desk: the arrival's EmptyDesk is NOT the surface here.
    useDesk.setState({
      items: {
        ...EMPTY_ITEMS,
        note: [{ kind: "note", id: "n1", title: "Release checklist" } as Note],
      },
      updatedAt: Date.now(),
      setup: null,
      error: "",
    });
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("names a refused floor-menu create in the system bar, and retries", async () => {
    let refuse = true;
    const fetchMock = vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
      const method = (init?.method || "GET").toUpperCase();
      if (method === "POST") return refuse ? json({}, 500) : json({ note: { id: "n2" } });
      return json({});
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <DeskChrome />
      </MemoryRouter>,
    );
    expect(q(".write-receipt")).toBeNull();

    await act(async () => {
      floorNewNote().onSelect();
    });
    await waitFor(() =>
      expect(q(".write-receipt-label")?.textContent).toBe(
        "CREATE NOTE FAILED · HTTP 500",
      ),
    );
    // In flow inside the system bar — not a floating overlay.
    expect(
      q(".desk-menubar .desk-chrome-receipt .write-receipt"),
    ).toBeTruthy();

    const posts = () =>
      fetchMock.mock.calls.filter(
        ([, init]) => (init as RequestInit | undefined)?.method === "POST",
      ).length;
    const before = posts();
    await user.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(posts()).toBe(before + 1));
    expect(q(".write-receipt-label")?.textContent).toBe(
      "CREATE NOTE FAILED · HTTP 500",
    );

    // A landed retry clears the line: success is quiet.
    refuse = false;
    await user.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() =>
      expect(q(".write-receipt")).toBeNull(),
    );
  });

  it("prints one receipt only: a nearer line silences the system bar", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (_i: RequestInfo | URL, init?: RequestInit) =>
        (init?.method || "GET").toUpperCase() === "POST" ? json({}, 500) : json({}),
      ),
    );
    render(
      <MemoryRouter>
        <DeskChrome />
        <EmptyDesk />
      </MemoryRouter>,
    );
    await act(async () => {
      floorNewNote().onSelect();
    });
    await waitFor(() =>
      expect(qa(".write-receipt")).toHaveLength(1),
    );
    expect(
      q(".desk-menubar .desk-chrome-receipt"),
    ).toBeNull();
    expect(q(".write-receipt-row .write-receipt")).toBeTruthy();
  });
});
