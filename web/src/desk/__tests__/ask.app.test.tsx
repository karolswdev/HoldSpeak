/** The Ask window (AskPanel), Betterment Q2 "Ask goes first": the face half.
 *
 * The hub half is tests/integration/test_desk_ask_priority.py. It records the
 * `ask_progress` frame the hub sends when meeting analysis holds the LAN
 * engine 5 s into an Ask, and that Ask's answer
 * (web/src/test/wire/ask.busy.wire.json; HOLDSPEAK_WIRE_WRITE=1 rewrites it).
 * Here the frame is delivered through the runtime bus, as the hub broadcasts
 * it, and fetch answers with the recorded answer. */
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AskPanel } from "../components/AskPanel";
import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";
import { latchAskSelection } from "../ask";
import { clearEngineCache } from "../hooks/useEngine";
import BUSY from "../../test/wire/ask.busy.wire.json";
import RETRY from "../../test/wire/ask.retry.wire.json";

const bus = vi.hoisted(() => ({ handlers: new Map<string, Set<(frame: unknown) => void>>() }));
vi.mock("../../runtime/RuntimeBus", () => {
  const value = {
    state: "connected",
    lastFrame: null,
    subscribe: (type: string, handler: (frame: unknown) => void) => {
      const set = bus.handlers.get(type) ?? new Set();
      set.add(handler);
      bus.handlers.set(type, set);
      return () => set.delete(handler);
    },
  };
  return { useRuntimeBus: () => value, useOptionalRuntimeBus: () => value, useRuntimeFrame: () => null };
});

function deliver(type: string, data: unknown) {
  for (const handler of bus.handlers.get(type) ?? []) handler({ type, data });
}

type Call = { url: string; method: string; body: Record<string, unknown> | undefined };
let calls: Call[] = [];
let answerAsk: (() => void) | null = null;

function reply(body: unknown, status = 200): Response {
  return { ok: status < 400, status, headers: { get: () => "application/json" }, json: () => Promise.resolve(body), text: () => Promise.resolve(JSON.stringify(body)) } as unknown as Response;
}

beforeEach(() => {
  Element.prototype.scrollIntoView = () => {};
  localStorage.clear();
  clearEngineCache();
  latchAskSelection(null);
  bus.handlers.clear();
  calls = [];
  useDesk.setState({ items: EMPTY_ITEMS, selectedIds: [], askOpen: true, pullouts: [], panelRects: {}, panelSaved: [], panelOrder: [] });
  // The recorded Ask's identity: the face mints `ask_<uuid without dashes>`.
  vi.spyOn(crypto, "randomUUID").mockReturnValue("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa");
  vi.stubGlobal("fetch", vi.fn((input: string, init: RequestInit = {}) => {
    const url = String(input);
    const method = String(init.method ?? "GET");
    calls.push({ url, method, body: init.body ? JSON.parse(String(init.body)) : undefined });
    if (method === "POST" && url.endsWith("/api/ask")) {
      // The engine is busy: the answer comes when the test says so.
      return new Promise<Response>((resolve) => { answerAsk = () => resolve(reply(BUSY.answer)); });
    }
    return Promise.resolve(reply({}));
  }));
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  answerAsk = null;
});

async function askMira() {
  render(<AskPanel />);
  fireEvent.change(screen.getByRole("textbox", { name: "Ask about your work" }), { target: { value: "What do I owe Mira this week?" } });
  fireEvent.click(screen.getByRole("button", { name: "Ask" }));
  await waitFor(() => expect(calls.some((c) => c.method === "POST" && c.url.endsWith("/api/ask"))).toBe(true));
}

describe("Betterment Q2: an Ask on a busy engine says so, and offers another engine", () => {
  it("the recorded busy frame reads 'Waiting for the LAN engine, busy with meeting analysis' and the answer still lands", async () => {
    await askMira();
    // The Ask goes out under the identity the frame names.
    const sent = calls.find((c) => c.url.endsWith("/api/ask"))!;
    expect(sent.body?.invocation_id).toBe(BUSY.busy.invocation_id);

    act(() => deliver("ask_progress", BUSY.busy));
    const line = await screen.findByTestId("run-line");
    expect(line.textContent).toContain("Waiting for the LAN engine, busy with meeting analysis");
    expect(screen.getByRole("button", { name: "Use Glass Local for this one" })).toBeInTheDocument();

    await act(async () => { answerAsk?.(); });
    expect(await screen.findByText(BUSY.answer.output)).toBeInTheDocument();
    expect(screen.queryByText(/busy with meeting analysis/)).toBeNull();
  });

  it("a frame for another Ask changes nothing here", async () => {
    await askMira();
    act(() => deliver("ask_progress", { ...BUSY.busy, invocation_id: "ask_someone_else" }));
    expect((await screen.findByTestId("run-line")).textContent).not.toContain("Waiting for");
  });

  it("Use … for this one runs this Ask on that engine under a one-run assignment", async () => {
    await askMira();
    act(() => deliver("ask_progress", BUSY.busy));
    vi.mocked(crypto.randomUUID).mockReturnValue("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb");
    fireEvent.click(await screen.findByRole("button", { name: "Use Glass Local for this one" }));

    await waitFor(() => expect(calls.filter((c) => c.url.endsWith("/api/ask"))).toHaveLength(2));
    const next = "ask_" + "b".repeat(32);
    expect(calls.some((c) => c.url === `/api/ask/${BUSY.busy.invocation_id}/cancel` && c.method === "POST")).toBe(true);
    const set = calls.find((c) => c.url.endsWith("/api/inference/assignments/set"))!;
    expect(set.body).toEqual({
      command_id: `ask-elsewhere-${next}`,
      expected_revision: 0,
      scope: { kind: "invocation", invocation_id: next, capability_id: "ask.answer" },
      entries: [{ profile_id: "glass-local", profile_revision: 1 }],
    });
    const asks = calls.filter((c) => c.url.endsWith("/api/ask"));
    expect(asks[1].body?.invocation_id).toBe(next);
    expect(calls.indexOf(set)).toBeLessThan(calls.indexOf(asks[1]));
  });

  it("a second attempt is said: 'Trying again, 1 of N'", async () => {
    await askMira();
    act(() => deliver("ask_progress", RETRY.retry));
    expect((await screen.findByTestId("run-line")).textContent).toContain(`Trying again, 1 of ${RETRY.retry.of}`);
  });
});
