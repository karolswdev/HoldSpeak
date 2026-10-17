/** The turn's lamp and footer egress always come from its actual receipt.
 * Thread keeps the complete last-turn receipt in its footer. Ask's settled
 * 2026-10-17 composition keeps ordinary status there and the unchanged
 * canonical receipt in an inspectable Run details fold below the answer. */
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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

const LAN = turn("a1", { egressScope: "private_network", egressHost: "192.168.1.43", modelId: "qwen3.8-27b", receiptId: "exec-0000a91f", egressReceiptId: "exec-0000a91f" });
const LOCAL = turn("a2", { egressScope: "local", egressHost: "", modelId: "Qwen3.5 4B", receiptId: "exec-0000e4d1", egressReceiptId: "exec-0000e4d1" });
const CLOUD = turn("a3", { egressScope: "cloud", egressHost: "api.openai.com", modelId: "gpt-5-mini", receiptId: "exec-00007c02", egressReceiptId: "exec-00007c02" });
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

  it("a LAN last turn shows host · LAN; a LOCAL turn has no passive chip", () => {
    seed([you("u1", "q"), LAN]);
    const lan = renderThread();
    expect(footer(lan.container)!.querySelector(".gadget-chip-egress")!.textContent).toBe("192.168.1.43 · LAN");
    lan.unmount();
    seed([you("u1", "q"), LOCAL]);
    const local = renderThread();
    expect(footer(local.container)!.querySelector(".gadget-chip-egress")).toBeNull();
  });

  it("a scope with no receipt provenance wears no lamp (the plan is not a receipt)", () => {
    seed([you("u1", "q"), turn("a5", { egressScope: "cloud", egressHost: "api.openai.com", modelId: "gpt-5-mini", receiptId: "exec-1234" })]);
    const { container } = renderThread();
    expect(rowLamp(container, "a5")).toBeNull();
    expect(footer(container)).toBeNull();
  });

  it("a fallback after a cloud send names the cloud route and says FALLBACK", () => {
    seed([you("u1", "q"), turn("a6", { egressScope: "cloud", egressHost: "api.openai.com", modelId: "gpt-5-mini", receiptId: "exec-00007c02", egressReceiptId: "exec-00007c02", egressFallback: true })]);
    const { container } = renderThread();
    expect(rowLamp(container, "a6")).toBe("CLOUD");
    expect(footer(container)!.querySelector(".surface-footer-receipt")!.textContent).toBe("LAST TURN · gpt-5-mini · FALLBACK · RECEIPT ··7c02");
  });

  it("the footer token is the route's receipt, not the turn's last pass", () => {
    seed([you("u1", "q"), turn("a7", { egressScope: "cloud", egressHost: "api.openai.com", modelId: "gpt-5-mini", receiptId: "exec-local-pass-e4d1", egressReceiptId: "exec-cloud-pass-7c02" })]);
    const { container } = renderThread();
    const line = footer(container)!.querySelector(".surface-footer-receipt")!.textContent!;
    expect(line).toContain("RECEIPT ··7c02");
    expect(line).not.toContain("e4d1");
  });

  it("a streaming turn has no receipt yet: no lamp, the footer keeps the last finished turn", () => {
    seed([you("u1", "q"), LAN, you("u2", "q2"), turn("a9", { streaming: true, completedAt: null, egressScope: "external_service", modelId: "gpt-5-mini", egressReceiptId: "exec-earlier-pass" })]);
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
        model: "gpt-5-mini", route_receipt_id: "exec-00007c02", fallback: false, stats: null,
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
        egress: "", host: "", model: "", route_receipt_id: "", fallback: false, stats: { error: "no route" },
      });
    });
    expect(rowLamp(container, "a9")).toBeNull();
    expect(footer(container)).toBeNull();
  });
});

describe("Ask: visible receipt egress, ordinary status and inspectable Run details", () => {
  const LAN_ASK = {
    output: "The cutover is on 17 October.",
    invocation_id: "inv-1",
    model: "qwen3.8-27b",
    profile_id: "lan-qwen",
    actual_placement: { target_id: "lan-qwen", target_name: "lan-qwen", boundary: "private_network", model: "qwen3.8-27b" },
    egress: { scope: "private_network", host: "192.168.1.43" },
    route_execution_receipt: { execution_id: "exec-0000a91f" },
    route: { lamp: "private_network", host: "192.168.1.43", model: "qwen3.8-27b", receipt: "exec-0000a91f", fallback: false },
    context_ids: [],
    context_titles: [],
  };

  beforeEach(() => {
    Element.prototype.scrollIntoView = () => {};
    localStorage.clear();
    useDesk.setState({ items: EMPTY_ITEMS, selectedIds: [], askOpen: true, pullouts: [], panelRects: {}, panelSaved: [], panelOrder: [] });
  });

  async function askWith(payload: Record<string, unknown>, status = 200, onAsk?: () => void) {
    vi.stubGlobal("fetch", vi.fn((url: string) => {
      const isAsk = String(url).includes("/api/ask");
      if (isAsk) onAsk?.();
      return Promise.resolve({
        ok: !(isAsk && status >= 400),
        status: isAsk ? status : 200,
        json: () => Promise.resolve(isAsk ? payload : {}),
      });
    }));
    const view = render(<AskPanel />);
    fireEvent.change(view.container.querySelector("textarea")!, { target: { value: "What did we decide about the cutover date?" } });
    fireEvent.keyDown(view.container.querySelector("textarea")!, { key: "Enter" });
    if (status >= 400) await waitFor(() => expect(view.container.querySelector("[data-testid=run-line][data-state=failure]")).toBeTruthy());
    else await waitFor(() => expect(screen.getByText("The cutover is on 17 October.")).toBeTruthy());
    return view;
  }

  it("the Answer turn and footer disclose the actual LAN route, with its model and receipt in Run details", async () => {
    const { container } = await askWith(LAN_ASK);
    const answerTurn = [...container.querySelectorAll(".surface-traffic-turn")]
      .find((node) => node.querySelector(".surface-traffic-prefix")?.textContent === "Answer")!;
    const lamp = answerTurn.querySelector(".gadget-lamp")!;
    expect(lamp).toHaveTextContent("LAN");
    await waitFor(() => expect(container.querySelector(".surface-traffic .gadget-lamp")).toBeVisible());
    const chip = container.querySelector(".surface-footer-egress .gadget-chip-egress")!;
    expect(chip.textContent).toBe("192.168.1.43 · LAN");
    expect(chip).toHaveAttribute("data-scope", "local");
    await waitFor(() => expect(container.querySelector(".surface-footer-egress .gadget-chip-egress")).toBeVisible());
    expect(container.querySelector(".surface-footer-receipt")!.textContent).toMatch(/^Answered(?: in [1-9]\d* s)?$/);
    const details = within(container).getByText("Run details").closest("details")!;
    const receiptLine = "LAST TURN · qwen3.8-27b · RECEIPT ··a91f";
    expect(details.open).toBe(false);
    expect(within(details).getByText(receiptLine, { exact: true })).toBeInTheDocument();
    expect(within(container).getAllByText(receiptLine, { exact: true })).toHaveLength(1);
    fireEvent.click(within(container).getByText("Run details"));
    await waitFor(() => expect(within(container).getByText(receiptLine, { exact: true })).toBeVisible());
  });

  it("names the model once (the CONTROL named it twice)", async () => {
    const { container } = await askWith(LAN_ASK);
    const text = container.textContent ?? "";
    expect(text.split("qwen3.8-27b").length - 1).toBe(1);
  });

  it("the lamp is the receipt route, not the placement boundary", async () => {
    // #855: a loopback engine stored as private_network runs LOCAL.
    const { container } = await askWith({ ...LAN_ASK, route: { lamp: "local", host: "", model: "qwen3.8-27b", receipt: "exec-0000a91f" } });
    expect(container.querySelector(".surface-traffic .gadget-lamp")!.textContent).toBe("LOCAL");
    expect(container.querySelector(".gadget-chip-egress")).toBeNull();
  });

  it("an answer with no receipt route wears no lamp", async () => {
    const { container } = await askWith({ ...LAN_ASK, route: null });
    expect(container.querySelector(".surface-traffic .gadget-lamp")).toBeNull();
    expect(container.querySelector(".gadget-chip-egress")).toBeNull();
  });

  it("a refused Ask keeps its visible cloud egress and error, with the exact failed route inspectable", async () => {
    const refusal = {
      error: "No assigned model completed this request",
      receipt: { execution_id: "exec-00007c02", outcome: "failed", attempts: [{ boundary: "cloud", send_phase: "provider_no_generation" }] },
      route: { lamp: "cloud", host: "api.openai.com", model: "gpt-5-mini", receipt: "exec-00007c02", fallback: false },
    };
    const { container } = await askWith(refusal, 409);
    const lamp = container.querySelector(".surface-traffic .gadget-lamp")!;
    expect(lamp.textContent).toBe("CLOUD");
    await waitFor(() => expect(container.querySelector(".surface-traffic .gadget-lamp")).toBeVisible());
    const chip = container.querySelector(".surface-footer-egress .gadget-chip-egress")!;
    expect(chip.textContent).toBe("api.openai.com");
    expect(chip).toHaveAttribute("data-scope", "cloud");
    await waitFor(() => expect(container.querySelector(".surface-footer-egress .gadget-chip-egress")).toBeVisible());
    const error = container.querySelector("[data-testid=run-line][data-state=failure]")!;
    expect(error).toHaveTextContent("did not answer");
    expect(error).toBeVisible();
    expect(within(error as HTMLElement).getByRole("button", { name: "Try again" })).toBeVisible();
    expect(container.querySelector(".surface-footer-receipt")).not.toHaveTextContent("Answered");
    expect(within(container).queryByText("The cutover is on 17 October.")).toBeNull();
    const details = within(container).getByText("Run details").closest("details")!;
    const receiptLine = "LAST TURN · gpt-5-mini · RECEIPT ··7c02";
    expect(details.open).toBe(false);
    expect(within(details).getByText(receiptLine, { exact: true })).toBeInTheDocument();
    fireEvent.click(within(container).getByText("Run details"));
    await waitFor(() => expect(within(container).getByText(receiptLine, { exact: true })).toBeVisible());
  });

  it("a refusal with no sent attempt has no lamp", async () => {
    const { container } = await askWith({ error: "No assigned model completed this request", route: { lamp: "", host: "", model: "", receipt: "exec-1" } }, 409);
    expect(container.querySelector(".surface-traffic .gadget-lamp")).toBeNull();
    expect(container.querySelector(".gadget-chip-egress")).toBeNull();
  });

  it("discloses fallback egress and keeps its completed status and canonical receipt fixed as time advances", async () => {
    const clock = vi.spyOn(Date, "now").mockReturnValue(1_000);
    try {
      const fallback = {
        ...LAN_ASK,
        model: "assigned-model",
        route: { lamp: "private_network", host: "fallback-box", model: "fallback-model", receipt: "exec-fallback", fallback: true },
      };
      const view = await askWith(fallback, 200, () => clock.mockReturnValue(4_100));
      const chip = view.container.querySelector(".surface-footer-egress .gadget-chip-egress")!;
      expect(chip.textContent).toBe("fallback-box · LAN");
      await waitFor(() => expect(view.container.querySelector(".surface-footer-egress .gadget-chip-egress")).toBeVisible());
      const completedStatus = "Answered in 3 s · Fallback";
      expect(view.container.querySelector(".surface-footer-receipt")?.textContent).toBe(completedStatus);
      expect(within(view.container).getByText(completedStatus, { exact: true })).toBeVisible();
      const routeReceipt = "LAST TURN · fallback-model · FALLBACK · RECEIPT ··back";
      const details = within(view.container).getByText("Run details").closest("details")!;
      expect(details.open).toBe(false);
      expect(within(details).getByText(routeReceipt, { exact: true })).toBeInTheDocument();
      fireEvent.click(within(view.container).getByText("Run details"));
      await waitFor(() => expect(within(view.container).getByText(routeReceipt, { exact: true })).toBeVisible());
      expect(within(view.container).getAllByText(routeReceipt, { exact: true })).toHaveLength(1);
      expect(view.container.querySelector("[data-testid=run-line]")).toBeNull();
      expect(view.container.textContent).not.toContain("assigned-model");

      clock.mockReturnValue(9_000);
      view.rerender(<AskPanel />);
      expect(view.container.querySelector(".surface-footer-receipt")?.textContent).toBe(completedStatus);
      expect(within(view.container).getByText(completedStatus, { exact: true })).toBeVisible();
      expect(within(view.container).getAllByText(routeReceipt, { exact: true })).toHaveLength(1);
      expect(within(view.container).getByText(routeReceipt, { exact: true })).toBeVisible();
      expect(view.container.querySelector("[data-testid=run-line]")).toBeNull();
    } finally {
      clock.mockRestore();
    }
  });
});
