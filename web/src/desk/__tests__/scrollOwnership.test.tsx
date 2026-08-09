// HS-129-04 — each repaired window names exactly one primary scroll owner.
import { render, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DeliveryBoard } from "../components/DeliveryBoard";
import { activateLauncher } from "../components/DeskWindow";
import { DeskToolInspector } from "../components/DeskToolInspector";
import "../components/chrome-menus.css";
import "../components/window-chrome.css";
import { useDelivery } from "../delivery";
import { useDeliveryFactory } from "../deliveryFactory";
import { useDesk } from "../store";
import { ConstitutionalContextCore } from "../../pages/cores/ConstitutionalContextCore";
import "../../pages/cores/constitutional-context.css";

const json = (body: unknown) =>
  new Response(JSON.stringify(body), {
    status: 200,
    headers: { "content-type": "application/json" },
  });

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
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => json({})),
  );
});

afterEach(() => vi.unstubAllGlobals());

function expectBodyOwnsScroll(container: HTMLElement, shellSelector: string) {
  const shell = container.querySelector(shellSelector) as HTMLElement;
  const body = shell.querySelector(".desk-surface-body") as HTMLElement;
  expect(shell).toBeTruthy();
  expect(body).toBeTruthy();
  expect(getComputedStyle(shell).overflow).toBe("hidden");
  expect(getComputedStyle(body).overflow).toBe("auto");
  expect(body.parentElement).toBe(shell);
}

describe("HS-129-04 scroll ownership", () => {
  it("keeps the DeliveryBoard frame fixed around its body and footer", async () => {
    const { container } = render(
      <div className="desk-next">
        <DeliveryBoard />
      </div>,
    );

    await waitFor(() => expect(activateLauncher("delivery-board")).toBe(true));
    await waitFor(() =>
      expect(container.querySelector(".desk-dlv-board")).toBeTruthy(),
    );
    expectBodyOwnsScroll(container, ".desk-dlv-board");
    const shell = container.querySelector(".desk-dlv-board") as HTMLElement;
    expect(shell.querySelector(".surface-footer")?.parentElement).toBe(shell);
  });

  it("keeps the DeskToolInspector title bar outside its body scroller", () => {
    useDesk.setState({
      toolInspector: { kind: "integration", id: "slack" },
      setup: {
        trust: {
          destinations: [
            {
              id: "slack",
              name: "Slack",
              operation: "Send approved text",
              enabled: true,
              destination: "Launch workspace",
              boundary: "External service",
              data_class: "Selected text",
              authority_basis: "Per-action approval",
              background_ability: "No",
              revoke_action: "Clear credential",
            },
          ],
        },
      },
    });
    const { container } = render(
      <div className="desk-next">
        <DeskToolInspector />
      </div>,
    );

    expectBodyOwnsScroll(container, ".desk-tool-inspector");
  });

  it("leaves ConstitutionalContextCore with the host's single body scroller", async () => {
    const { container } = render(
      <div className="desk-next">
        <div className="desk-surface-body">
          <ConstitutionalContextCore />
        </div>
      </div>,
    );

    await waitFor(() =>
      expect(
        container.querySelector(".constitutional-context-core"),
      ).toBeTruthy(),
    );
    const bodies = container.querySelectorAll(".desk-surface-body");
    const hostBody = bodies[0] as HTMLElement;
    const core = container.querySelector(
      ".constitutional-context-core",
    ) as HTMLElement;
    expect(bodies).toHaveLength(1);
    expect(getComputedStyle(hostBody).overflow).toBe("auto");
    expect(getComputedStyle(core).overflow).not.toBe("auto");
  });
});
