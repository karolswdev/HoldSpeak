/** Owner pick 2026-10-05 (canvas section 4, option C "Route in footer"):
 * each turn wears only its LAMP, the turn's receipt boundary; the footer's
 * egress slot names the FULL route of the LAST turn (host chip, model,
 * receipt) and the model is named once. Ask (LAN) and a chat with LAN,
 * LOCAL, CLOUD turns and one turn with no model call. */
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useThreadStore, type ThreadMessage, type ThreadDetail } from "../threads";
import { ThreadPullout } from "../pullouts/ThreadPullout";
import { RuntimeBusProvider } from "../../runtime/RuntimeBus";
import { AskPanel } from "../components/AskPanel";
import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";

const now = new Date().toISOString();

function turn(id: string, over: Partial<ThreadMessage> = {}): ThreadMessage {
  return {
    id, threadId: "t-1", parentId: null, role: "assistant", streaming: false,
    operationId: null, receiptId: null, egressScope: null, egressHost: null,
    modelId: null, statsJson: null, errorJson: null, createdAt: now,
    updatedAt: now, completedAt: now, abortedAt: null,
    parts: [{ id: `${id}-p`, messageId: id, ordinal: 0, kind: "text", text: `answer ${id}`, sensitive: false }],
    ...over,
  };
}

function you(id: string, text: string): ThreadMessage {
  return turn(id, {
    role: "user",
    parts: [{ id: `${id}-p`, messageId: id, ordinal: 0, kind: "text", text, sensitive: false }],
  });
}

function seed(messages: ThreadMessage[]) {
  const detail: ThreadDetail = {
    thread: {
      id: "t-1", title: "Cutover risks", recipe_id: null, profile_override: null,
      directory_id: null, parent_thread_id: null, status_line: null, mode: null,
      call_mode: 0, token_in: 0, token_out: 0, created_at: now, updated_at: now,
      last_turn_at: null,
    },
    messages, siblings: {}, refs: [], draftAnnotations: [],
  };
  useThreadStore.setState({ threads: { "t-1": detail }, buffers: {}, loading: {} });
}

function renderThread() {
  return render(
    <RuntimeBusProvider>
      <ThreadPullout
        object={{ kind: "thread", id: "t-1", title: "Cutover risks", ref: { kind: "thread", id: "t-1", title: "Cutover risks" } as any }}
        onClose={() => {}}
      />
    </RuntimeBusProvider>,
  );
}

const LAN = turn("a1", { egressScope: "private_network", egressHost: "192.168.1.43", modelId: "qwen3.8-27b", receiptId: "exec-0000a91f" });
const LOCAL = turn("a2", { egressScope: "local", egressHost: "", modelId: "Qwen3.5 4B", receiptId: "exec-0000e4d1" });
const CLOUD = turn("a3", { egressScope: "cloud", egressHost: "api.openai.com", modelId: "gpt-5-mini", receiptId: "exec-00007c02" });
const NONE = turn("a4", { egressScope: "", egressHost: "", modelId: "qwen3.8-27b", receiptId: "", errorJson: { error: "Turn failed" }, parts: [] });

function rowLamp(container: HTMLElement, id: string): string | null {
  const row = container.querySelector(`[data-message-id="${id}"] .thread-row-head`);
  return row?.querySelector(".gadget-lamp")?.textContent ?? null;
}

function footer(container: HTMLElement) {
  return container.querySelector(".thread-route-footer");
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
afterEach(() => vi.unstubAllGlobals());

describe("chat: a lamp per turn, the route of the last turn in the footer", () => {
  it("each turn's lamp equals its receipt boundary; no model call, no lamp", () => {
    seed([you("u1", "List the risks."), LAN, you("u2", "Shorter."), LOCAL, you("u3", "The notice."), CLOUD, you("u4", "Again."), NONE]);
    const { container } = renderThread();
    expect(rowLamp(container, "a1")).toBe("LAN");
    expect(rowLamp(container, "a2")).toBe("LOCAL");
    expect(rowLamp(container, "a3")).toBe("CLOUD");
    expect(rowLamp(container, "a4")).toBeNull();
    // The thread head carries no second lamp.
    expect(container.querySelector(".thread-head .gadget-lamp")).toBeNull();
  });

  it("the footer names the last turn's full route: host chip, model, receipt", () => {
    seed([you("u1", "List the risks."), LAN, you("u2", "Shorter."), LOCAL, you("u3", "The notice."), CLOUD]);
    const { container } = renderThread();
    const foot = footer(container)!;
    expect(foot).toBeTruthy();
    const chip = foot.querySelector(".surface-footer-egress .gadget-chip-egress")!;
    expect(chip.textContent).toBe("api.openai.com");
    expect(chip.getAttribute("data-scope")).toBe("cloud");
    expect(foot.querySelector(".surface-footer-receipt")!.textContent).toBe("LAST TURN · gpt-5-mini · RECEIPT ··7c02");
  });

  it("names each model once: in the footer for the last turn, never on the rows", () => {
    seed([you("u1", "List the risks."), LAN, you("u3", "The notice."), CLOUD]);
    const { container } = renderThread();
    const text = container.textContent ?? "";
    expect(text.split("gpt-5-mini").length - 1).toBe(1);
    expect(text).not.toContain("qwen3.8-27b");
  });

  it("a LAN last turn shows host · LAN; a LOCAL one THIS DEVICE", () => {
    seed([you("u1", "q"), LAN]);
    const lan = renderThread();
    expect(footer(lan.container)!.querySelector(".gadget-chip-egress")!.textContent).toBe("192.168.1.43 · LAN");
    lan.unmount();
    seed([you("u1", "q"), LOCAL]);
    const local = renderThread();
    expect(footer(local.container)!.querySelector(".gadget-chip-egress")!.textContent).toBe("THIS DEVICE");
  });

  it("a streaming turn has no receipt yet: no lamp, the footer keeps the last finished turn", () => {
    seed([you("u1", "q"), LAN, you("u2", "q2"), turn("a9", { streaming: true, completedAt: null, egressScope: "external_service", modelId: "gpt-5-mini" })]);
    const { container } = renderThread();
    expect(rowLamp(container, "a9")).toBeNull();
    expect(footer(container)!.querySelector(".gadget-chip-egress")!.textContent).toBe("192.168.1.43 · LAN");
  });

  it("the footer updates when a new turn lands (thread_turn_done is the receipt)", () => {
    seed([you("u1", "q"), LAN, you("u2", "q2"), turn("a9", { streaming: true, completedAt: null, egressScope: "private_network", modelId: "plan-model" })]);
    useThreadStore.setState((s) => ({ buffers: { ...s.buffers, a9: { messageId: "a9", parts: new Map(), highSeq: -1 } } }));
    const { container } = renderThread();
    act(() => {
      useThreadStore.getState().applyTurnDone({
        thread_id: "t-1", message_id: "a9", receipt_id: "exec-00007c02",
        outcome: "succeeded", egress: "cloud", host: "api.openai.com",
        model: "gpt-5-mini", stats: null,
      });
    });
    expect(rowLamp(container, "a9")).toBe("CLOUD");
    const foot = footer(container)!;
    expect(foot.querySelector(".gadget-chip-egress")!.textContent).toBe("api.openai.com");
    expect(foot.querySelector(".surface-footer-receipt")!.textContent).toBe("LAST TURN · gpt-5-mini · RECEIPT ··7c02");
  });

  it("a done frame with no model call clears the planned lamp", () => {
    seed([you("u1", "q"), turn("a9", { streaming: true, completedAt: null, egressScope: "private_network" })]);
    useThreadStore.setState((s) => ({ buffers: { ...s.buffers, a9: { messageId: "a9", parts: new Map(), highSeq: -1 } } }));
    const { container } = renderThread();
    act(() => {
      useThreadStore.getState().applyTurnDone({
        thread_id: "t-1", message_id: "a9", receipt_id: "", outcome: "failed",
        egress: "", host: "", model: "", stats: { error: "no route" },
      });
    });
    expect(rowLamp(container, "a9")).toBeNull();
    expect(footer(container)).toBeNull();
  });
});

describe("Ask: the lamp on the turn, the route once in the footer", () => {
  const LAN_ASK = {
    output: "The cutover is on 17 October.",
    invocation_id: "inv-1",
    model: "qwen3.8-27b",
    profile_id: "lan-qwen",
    actual_placement: { target_id: "lan-qwen", target_name: "lan-qwen", boundary: "private_network", model: "qwen3.8-27b" },
    egress: { scope: "private_network", host: "192.168.1.43" },
    route_execution_receipt: { execution_id: "exec-0000a91f" },
    context_ids: [],
    context_titles: [],
  };

  beforeEach(() => {
    Element.prototype.scrollIntoView = () => {};
    localStorage.clear();
    useDesk.setState({ items: EMPTY_ITEMS, selectedIds: [], askOpen: true, pullouts: [], panelRects: {}, panelSaved: [], panelOrder: [] });
  });

  async function askWith(payload: Record<string, unknown>) {
    vi.stubGlobal("fetch", vi.fn((url: string) => Promise.resolve({
      ok: true,
      status: 200,
      json: () => Promise.resolve(String(url).includes("/api/ask") ? payload : {}),
    })));
    const view = render(<AskPanel />);
    fireEvent.change(view.container.querySelector("textarea")!, { target: { value: "What did we decide about the cutover date?" } });
    fireEvent.keyDown(view.container.querySelector("textarea")!, { key: "Enter" });
    await waitFor(() => expect(screen.getByText("The cutover is on 17 October.")).toBeTruthy());
    return view;
  }

  it("the HUB> turn wears the LAN lamp; the footer names host, model, receipt", async () => {
    const { container } = await askWith(LAN_ASK);
    const hubTurn = [...container.querySelectorAll(".surface-traffic-turn, [class*='traffic-turn']")]
      .find((n) => n.textContent?.includes("HUB>"))!;
    expect(hubTurn.querySelector(".gadget-lamp")!.textContent).toBe("LAN");
    const chip = container.querySelector(".surface-footer-egress .gadget-chip-egress")!;
    expect(chip.textContent).toBe("192.168.1.43 · LAN");
    expect(container.querySelector(".surface-footer-receipt")!.textContent).toBe("LAST TURN · qwen3.8-27b · RECEIPT ··a91f");
  });

  it("names the model once (the CONTROL named it twice)", async () => {
    const { container } = await askWith(LAN_ASK);
    const text = container.textContent ?? "";
    expect(text.split("qwen3.8-27b").length - 1).toBe(1);
  });

  it("the lamp is the receipt's egress word, not the placement boundary", async () => {
    // #855: a loopback engine stored as private_network runs LOCAL.
    const { container } = await askWith({ ...LAN_ASK, egress: { scope: "local" } });
    expect(container.querySelector(".surface-traffic .gadget-lamp, .gadget-lamp")!.textContent).toBe("LOCAL");
    expect(container.querySelector(".gadget-chip-egress")!.textContent).toBe("THIS DEVICE");
  });
});
