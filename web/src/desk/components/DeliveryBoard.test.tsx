// HS-139-03 — Delivery owns the companion-repo setting and must never leave
// a rejected optimistic value on screen.
import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DeliveryBoard } from "./DeliveryBoard";
import { activateLauncher } from "./DeskWindow";
import { useDelivery } from "../delivery";
import { useDeliveryFactory } from "../deliveryFactory";
import { useDesk } from "../store";

const initialSettings = {
  _revision: "rev-1",
  meeting: { companion_github_repo: "owner/original" },
};
const reconciledSettings = {
  _revision: "rev-2",
  meeting: { companion_github_repo: "owner/current" },
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

describe("CompanionRepoConfig (HS-139-03)", () => {
  beforeEach(() => {
    useDesk.setState({
      projects: [],
      inferenceTargets: [],
      models: [],
      setup: { trust: { destinations: [] } },
      selectedIds: [],
      toolInspector: null,
      closeToolInspector: vi.fn(),
      openPullout: vi.fn(),
      openChat: vi.fn(),
      panelMin: [],
      panelMax: [],
      panelOrder: [],
      panelRects: {},
    });
    useDelivery.setState({
      sources: [],
      attempts: [],
      updatedAt: Date.now(),
      inflight: false,
    });
    useDeliveryFactory.setState({ targets: [], profiles: [] });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("refuses a stale companion-repo PUT and reloads the server's value", async () => {
    let rejected = false;
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const path = new URL(String(input), "http://desk.test").pathname;
      if (path === "/api/settings") {
        if (init?.method === "PUT") {
          rejected = true;
          return json(
            { error: "Settings changed elsewhere. Reload before saving." },
            409,
          );
        }
        return json(rejected ? reconciledSettings : initialSettings);
      }
      return json({});
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<DeliveryBoard />);
    await act(async () => {
      expect(activateLauncher("delivery-board")).toBe(true);
    });

    const input = (await screen.findByLabelText("GitHub repo")) as HTMLInputElement;
    expect(input.value).toBe("owner/original");
    fireEvent.change(input, { target: { value: "owner/rejected" } });

    // The product intentionally debounces settings writes. Keep the elapsed
    // time inside act so the async refusal + reconciliation settle together.
    await act(async () => {
      await new Promise<void>((resolve) => window.setTimeout(resolve, 710));
    });

    expect(screen.getByRole("alert")).toHaveTextContent(
      "REFUSED · Settings changed elsewhere. Reload before saving.",
    );
    expect(screen.getByLabelText("GitHub repo")).toHaveValue("owner/current");

    const put = fetchMock.mock.calls.find(
      ([input, init]) =>
        new URL(String(input), "http://desk.test").pathname === "/api/settings" &&
        (init as RequestInit | undefined)?.method === "PUT",
    );
    expect(JSON.parse(String((put?.[1] as RequestInit).body))).toMatchObject({
      _revision: "rev-1",
      meeting: { companion_github_repo: "owner/rejected" },
    });
  });
});
