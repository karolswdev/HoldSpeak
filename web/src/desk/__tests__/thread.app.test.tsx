/** Thread (Betterment Q0, "Threads tell the truth"): the face half.
 *
 * The real ThreadPullout, the real thread store and the real `getThread`
 * parse; only fetch is mocked, and the GET answers are the hub's own,
 * recorded from an isolated rig hub with the LAN engine
 * (`web/src/test/wire/thread.*.wire.json`). The hub half (a failed turn
 * completes with `error_json`; a seed ref is stored as the real ref) is in
 * tests/unit/test_desk_thread.py. */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { useThreadStore } from "../threads";
import { ThreadPullout } from "../pullouts/ThreadPullout";
import { RuntimeBusProvider } from "../../runtime/RuntimeBus";
import { useDesk } from "../store";
import failedTurn from "../../test/wire/thread.failed-turn.wire.json";
import seeded from "../../test/wire/thread.seeded.wire.json";

type Call = { url: string; method: string; body: unknown };
let calls: Call[] = [];

function hub(routes: Record<string, { status?: number; body: unknown }>) {
  calls = [];
  vi.stubGlobal("fetch", vi.fn((input: string, init: RequestInit = {}) => {
    const url = String(input);
    const method = String(init.method ?? "GET");
    calls.push({ url, method, body: init.body ? JSON.parse(String(init.body)) : undefined });
    const hit = Object.entries(routes).find(([key]) => `${method} ${url}`.endsWith(key));
    if (!hit) return Promise.reject(new TypeError("no hub in this test"));
    const { status = 200, body } = hit[1];
    return Promise.resolve({
      ok: status < 400, status,
      headers: { get: () => "application/json" },
      json: () => Promise.resolve(structuredClone(body)),
      text: () => Promise.resolve(JSON.stringify(body)),
    });
  }));
}

beforeEach(() => {
  vi.stubGlobal("WebSocket", class {
    addEventListener() {}
    removeEventListener() {}
    close() {}
    send() {}
    readyState = 3;
  });
});
afterEach(() => {
  vi.unstubAllGlobals();
  useThreadStore.setState({ threads: {}, buffers: {}, loading: {}, toolRows: {}, statusLines: {} });
});

function renderThread(id: string) {
  return render(
    <RuntimeBusProvider>
      <ThreadPullout
        object={{ kind: "thread", id, title: "", ref: { kind: "thread", id, title: "" } as never }}
        onClose={() => {}}
      />
    </RuntimeBusProvider>,
  );
}

describe("Thread: a failed reply says why", () => {
  it("renders the recorded failed turn's reason in words, with Ask again", async () => {
    const id = failedTurn.wire.id;
    const assistant = failedTurn.wire.messages.find((m) => m.role === "assistant")!;
    // The recording is the truth this face reads: a reason, no parts.
    expect(assistant.error_json).toMatchObject({ reason: "no_engine" });
    expect(assistant.parts).toEqual([]);
    hub({
      [`GET /api/threads/${id}`]: { body: failedTurn.wire },
      // The regenerate route answers with start_turn's shape (routes/threads.py api_regenerate).
      [`POST /api/threads/${id}/regenerate`]: { status: 201, body: {
        thread_id: id, user_message_id: assistant.parent_id, assistant_message_id: "tm_again",
      } },
    });
    renderThread(id);
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("No engine for answers");
    expect(alert).not.toHaveTextContent("{");
    fireEvent.click(within(alert).getByRole("button", { name: "Ask again" }));
    await waitFor(() => expect(calls.some((c) =>
      c.method === "POST" && c.url.endsWith(`/api/threads/${id}/regenerate`)
      && (c.body as { message_id?: string })?.message_id === assistant.id)).toBe(true));
  });
});

describe("Thread: Continue in thread brings the object", () => {
  it("lists the seeded note by its title under Sources, and the reply that used it", async () => {
    const id = seeded.wire.id;
    hub({ [`GET /api/threads/${id}`]: { body: seeded.wire } });
    renderThread(id);
    expect(await screen.findByText(/reconciliation job/)).toBeTruthy();
    fireEvent.click(screen.getByText(/^Sources ·/));
    expect(screen.getByText("Ledger migration risks")).toBeTruthy();
    expect(screen.queryByText(/ref_kind/)).toBeNull();
    expect(screen.queryByText("Source unavailable")).toBeNull();
  });

  it("reads a seed row stored before the fix by its identity, never as a dict", async () => {
    // The row RECON.md step 11 saw on the face, as the hub stored it then.
    const id = seeded.wire.id;
    const legacy = structuredClone(seeded.wire);
    legacy.refs = [{ ...legacy.refs[0], id: "tr_legacy", ref_kind: "seed",
      ref_id: "{'ref_kind': 'note', 'ref_id': 'n-risks'}", frozen_json: null as never }];
    const priorItems = useDesk.getState().items;
    useDesk.setState({ items: { ...priorItems, note: [{ id: "n-risks", title: "Ledger migration risks" }] as never } });
    try {
      hub({ [`GET /api/threads/${id}`]: { body: legacy } });
      renderThread(id);
      fireEvent.click(await screen.findByText("Sources · 1"));
      expect(screen.getByText("Ledger migration risks")).toBeTruthy();
      expect(screen.queryByText(/ref_kind/)).toBeNull();
    } finally {
      useDesk.setState({ items: priorItems });
    }
  });
});
