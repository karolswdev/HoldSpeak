/** The Ask turn's lamp and footer egress come from its actual receipt
 * (Betterment Q4: the chip names the lamp, never the host; the receipt id
 * stays off the face). The Thread window's half is parked with it
 * (`pullouts/_parked/__tests__/routeInFooter.thread.test.tsx`). */
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AskPanel } from "../components/AskPanel";
import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";

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

describe("Ask: no route lamp, no host, no scope word, no receipt id (owner ruling 2026-10-25)", () => {
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
      // Betterment Q7: the window also reads /api/ask/engine (the engine line).
      const isAsk = String(url).includes("/api/ask") && !String(url).endsWith("/api/ask/engine");
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
    if (status >= 400) await waitFor(() => expect(view.container.querySelector("[data-testid=ask-not-answered]")).toBeTruthy());
    else await waitFor(() => expect(screen.getByText("The cutover is on 17 October.")).toBeTruthy());
    return view;
  }

  it("the Answer turn draws no route lamp: no host string, no scope word and no receipt id", async () => {
    const { container } = await askWith(LAN_ASK);
    expect(container.querySelector("[data-testid=ask-status] .kit-statusbar-egress")).toBeNull();
    expect(container.querySelector("[data-testid=ask-status] .gadget-lamp")).toBeNull();
    expect(container.querySelector(".gadget-chip-egress")).toBeNull();
    expect(container.querySelector("[data-testid=ask-status]")?.textContent ?? "").not.toMatch(/\bLAN\b|CLOUD|LOCAL/);
    expect(container.querySelector("[data-testid=ask-status-receipt]")?.textContent ?? "").toMatch(/^(Answered in [1-9]\d* s)?$/);
    expect(container.textContent).not.toContain("192.168.1.43");
    expect(container.textContent).not.toContain("a91f");
    expect(within(container).queryByText("Run details")).toBeNull();
  });

  it("never names the model twice (the CONTROL named it twice)", async () => {
    // Betterment Q4: the Run details receipt that named it left the face; the
    // engine line names the engine when it is read (here it is not).
    const { container } = await askWith(LAN_ASK);
    const text = container.textContent ?? "";
    expect(text.split("qwen3.8-27b").length - 1).toBeLessThanOrEqual(1);
  });

  it("a local receipt route wears no lamp either", async () => {
    const { container } = await askWith({ ...LAN_ASK, route: { lamp: "local", host: "", model: "qwen3.8-27b", receipt: "exec-0000a91f" } });
    expect(container.querySelector("[data-testid=ask-status] .gadget-lamp")).toBeNull();
    expect(container.querySelector(".gadget-chip-egress")).toBeNull();
  });

  it("an answer with no receipt route wears no lamp", async () => {
    const { container } = await askWith({ ...LAN_ASK, route: null });
    expect(container.querySelector("[data-testid=ask-status] .gadget-lamp")).toBeNull();
    expect(container.querySelector(".gadget-chip-egress")).toBeNull();
  });

  it("a refused Ask keeps its reason in words, with no scope word", async () => {
    const refusal = {
      error: "No assigned model completed this request",
      receipt: { execution_id: "exec-00007c02", outcome: "failed", attempts: [{ boundary: "cloud", send_phase: "provider_no_generation" }] },
      route: { lamp: "cloud", host: "api.openai.com", model: "gpt-5-mini", receipt: "exec-00007c02", fallback: false },
    };
    const { container } = await askWith(refusal, 409);
    expect(container.querySelector("[data-testid=ask-status] .gadget-lamp")).toBeNull();
    expect(container.querySelector("[data-testid=ask-status]")?.textContent ?? "").not.toContain("CLOUD");
    expect(container.querySelector(".gadget-chip-egress")).toBeNull();
    const error = container.querySelector("[data-testid=ask-not-answered]")!;
    expect(error).toHaveTextContent("did not answer");
    // The window's entrance fades it in: wait for the frame to settle.
    await waitFor(() => expect(error).toBeVisible());
    expect(within(error as HTMLElement).getByRole("button", { name: "Try again" })).toBeVisible();
    expect(container.querySelector("[data-testid=ask-status-receipt]")?.textContent ?? "").not.toContain("Answered");
    expect(within(container).queryByText("The cutover is on 17 October.")).toBeNull();
    expect(container.textContent).not.toContain("api.openai.com");
    expect(container.textContent).not.toContain("No assigned model");
  });

  it("a refusal with no sent attempt has no lamp", async () => {
    const { container } = await askWith({ error: "No assigned model completed this request", route: { lamp: "", host: "", model: "", receipt: "exec-1" } }, 409);
    expect(container.querySelector("[data-testid=ask-status] .gadget-lamp")).toBeNull();
    expect(container.querySelector(".gadget-chip-egress")).toBeNull();
  });

  it("says Fallback with no route lamp and keeps its completed status fixed as time advances", async () => {
    const clock = vi.spyOn(Date, "now").mockReturnValue(1_000);
    try {
      const fallback = {
        ...LAN_ASK,
        model: "assigned-model",
        route: { lamp: "private_network", host: "fallback-box", model: "fallback-model", receipt: "exec-fallback", fallback: true },
      };
      const view = await askWith(fallback, 200, () => clock.mockReturnValue(4_100));
      expect(view.container.querySelector("[data-testid=ask-status] .gadget-lamp")).toBeNull();
      expect(view.container.querySelector(".gadget-chip-egress")).toBeNull();
      // Pass 2 (Ask): the answered face keeps its status bar: "Answered · … · 3 s".
      const completedStatus = "Fallback";
      const answered = /^Answered( · \d+ records?)? · 3 s$/;
      expect(view.container.querySelector("[data-testid=ask-status-receipt]")?.textContent).toBe(completedStatus);
      expect(view.container.querySelector("[data-testid=ask-status-answered]")?.textContent).toMatch(answered);
      expect(view.container.querySelector("[data-testid=run-line]")).toBeNull();
      expect(view.container.textContent).not.toContain("fallback-box");

      clock.mockReturnValue(9_000);
      view.rerender(<AskPanel />);
      expect(view.container.querySelector("[data-testid=ask-status-receipt]")?.textContent).toBe(completedStatus);
      expect(view.container.querySelector("[data-testid=ask-status-answered]")?.textContent).toMatch(answered);
    } finally {
      clock.mockRestore();
    }
  });
});
