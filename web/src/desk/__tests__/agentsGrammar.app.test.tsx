/** Selection and recovery properties, using the hub's recorded fleet. */
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";
import { hubWire } from "./wire/hubWire";
const boundary = vi.hoisted(() => ({ fetch: vi.fn(), request: vi.fn() }));
vi.mock("../../lib/api", async (original) => ({
  ...(await original<typeof import("../../lib/api")>()),
  apiFetch: boundary.fetch,
  apiRequest: boundary.request,
}));
vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    subscribe: () => () => undefined,
  }),
  useOptionalRuntimeBus: () => null,
  useRuntimeFrame: () => null,
}));
vi.mock("../components/MicButton", () => ({ MicButton: () => null }));
import { ConductorWindow } from "../conductor/ConductorWindow";
import { __resetConductor } from "../conductor/store";
import { __resetLane } from "../lane/laneStore";
import { useAgentFlights } from "../agentFlights";
const fleet = hubWire("../fixtures/agents-ag8/coders-sessions");
const detect = hubWire("onboarding-agents.isolated");
beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date(fleet.captured_at));
  __resetConductor();
  __resetLane();
  useAgentFlights.setState({ sessions: [], flights: [], loaded: false });
  boundary.fetch.mockImplementation(async (url: string) => {
    if (url.startsWith("/api/coders/sessions")) return fleet.wire;
    if (url === "/api/onboarding/agents") return detect.wire;
    if (url.startsWith("/api/coders/own-agents")) return { agents: [] };
    if (url.startsWith("/api/agent/launches/launch_ag8_ask/lane"))
      return hubWire("../fixtures/agents-ag2/lane.asks").wire;
    return {};
  });
});
afterEach(() => {
  __resetLane();
  vi.useRealTimers();
});
describe("Agents window grammar", () => {
  it("selects grouped rows and shows the question in a redacted inspector, without a second mast or cards", async () => {
    render(<ConductorWindow />);
    const waiting = await screen.findByRole("rowgroup", {
      name: "Waits on you",
    });
    const row = within(waiting).getAllByRole("row")[0];
    fireEvent.click(row);
    expect(row.getAttribute("aria-selected")).toBe("true");
    expect(document.querySelector(".aw-plate,.aw-tile-open,.surface-mast:not(.surface-mast--framed)")).toBeNull();
    await waitFor(() =>
      expect(screen.getByTestId("conductor-ask-row").getAttribute("data-feedback-redact")).toBe("true"),
    );
    expect(screen.getByRole("rowgroup", { name: "Working" })).toBeTruthy();
    expect(screen.getByRole("rowgroup", { name: "Done today" })).toBeTruthy();
    expect(row.querySelector("button")).toBeNull();
  });
  it("reveals the selected inspector when its verb is pressed from the list", async () => {
    render(<ConductorWindow />);
    await screen.findByRole("rowgroup", { name: "Waits on you" });
    await screen.findByTestId("conductor-bar-answer");
    expect(document.querySelector(".surface-list-pane")?.hasAttribute("data-detail-open")).toBe(false);
    fireEvent.click(screen.getByTestId("conductor-bar-answer"));
    expect(document.querySelector(".surface-list-pane")?.hasAttribute("data-detail-open")).toBe(true);
  });
  it("keeps Start live and selection verbs dead when Find leaves no row", async () => {
    render(<ConductorWindow />);
    await screen.findByRole("rowgroup", { name: "Waits on you" });
    fireEvent.click(screen.getByRole("button", { name: "Find" } as never));
    fireEvent.change(screen.getByRole("textbox", { name: "Find a session" }), {
      target: { value: "no matching session" },
    });
    expect(screen.getByTestId("conductor-start")).not.toBeDisabled();
    await waitFor(() => expect(screen.getByTestId("conductor-bar-answer")).toBeDisabled());
  });
});
