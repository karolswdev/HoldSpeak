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

describe("Ask: visible receipt egress and ordinary status, no host and no receipt id", () => {
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

  it("the Answer turn and footer disclose the actual LAN route, with no host string and no receipt id", async () => {
    const { container } = await askWith(LAN_ASK);
    const answerTurn = [...container.querySelectorAll(".surface-traffic-turn")]
      .find((node) => node.querySelector(".surface-traffic-prefix")?.textContent === "Answer")!;
    const lamp = answerTurn.querySelector(".gadget-lamp")!;
    expect(lamp).toHaveTextContent("LAN");
    await waitFor(() => expect(container.querySelector(".surface-traffic .gadget-lamp")).toBeVisible());
    const chip = container.querySelector(".surface-footer-egress .gadget-chip-egress")!;
    expect(chip.textContent).toBe("LAN");
    expect(chip).toHaveAttribute("data-scope", "local");
    await waitFor(() => expect(container.querySelector(".surface-footer-egress .gadget-chip-egress")).toBeVisible());
    expect(container.querySelector(".surface-footer-receipt")!.textContent).toMatch(/^(Answered in [1-9]\d* s)?$/);
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

  it("a refused Ask keeps its visible cloud egress and its reason in words", async () => {
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
    expect(chip.textContent).toBe("CLOUD");
    expect(chip).toHaveAttribute("data-scope", "cloud");
    const error = container.querySelector("[data-testid=run-line][data-state=failure]")!;
    expect(error).toHaveTextContent("did not answer");
    expect(error).toBeVisible();
    expect(within(error as HTMLElement).getByRole("button", { name: "Try again" })).toBeVisible();
    expect(container.querySelector(".surface-footer-receipt")?.textContent ?? "").not.toContain("Answered");
    expect(within(container).queryByText("The cutover is on 17 October.")).toBeNull();
    expect(container.textContent).not.toContain("api.openai.com");
    expect(container.textContent).not.toContain("No assigned model");
  });

  it("a refusal with no sent attempt has no lamp", async () => {
    const { container } = await askWith({ error: "No assigned model completed this request", route: { lamp: "", host: "", model: "", receipt: "exec-1" } }, 409);
    expect(container.querySelector(".surface-traffic .gadget-lamp")).toBeNull();
    expect(container.querySelector(".gadget-chip-egress")).toBeNull();
  });

  it("discloses fallback egress and keeps its completed status fixed as time advances", async () => {
    const clock = vi.spyOn(Date, "now").mockReturnValue(1_000);
    try {
      const fallback = {
        ...LAN_ASK,
        model: "assigned-model",
        route: { lamp: "private_network", host: "fallback-box", model: "fallback-model", receipt: "exec-fallback", fallback: true },
      };
      const view = await askWith(fallback, 200, () => clock.mockReturnValue(4_100));
      const chip = view.container.querySelector(".surface-footer-egress .gadget-chip-egress")!;
      expect(chip.textContent).toBe("LAN");
      const completedStatus = "Answered in 3 s · Fallback";
      expect(view.container.querySelector(".surface-footer-receipt")?.textContent).toBe(completedStatus);
      expect(view.container.querySelector("[data-testid=run-line]")).toBeNull();
      expect(view.container.textContent).not.toContain("fallback-box");

      clock.mockReturnValue(9_000);
      view.rerender(<AskPanel />);
      expect(view.container.querySelector(".surface-footer-receipt")?.textContent).toBe(completedStatus);
    } finally {
      clock.mockRestore();
    }
  });
});
