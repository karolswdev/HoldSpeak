import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import PresencePage from "../PresencePage";

const runtime = vi.hoisted(() => ({ state: "connected", frame: vi.fn() }));
vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: runtime.state }),
  useRuntimeFrame: runtime.frame,
}));

function DeskLanding() {
  const location = useLocation();
  return <div data-testid="desk-location">{location.pathname + location.search}</div>;
}

function open() {
  return render(<MemoryRouter initialEntries={[window.location.pathname + window.location.search]}>
    <Routes>
      <Route path="/presence" element={<PresencePage />} />
      <Route path="/" element={<DeskLanding />} />
    </Routes>
  </MemoryRouter>);
}

beforeEach(() => {
  window.history.replaceState({}, "", "/presence");
  runtime.state = "connected";
  runtime.frame.mockReset().mockReturnValue(null);
});
afterEach(() => {
  cleanup();
  window.history.replaceState({}, "", "/");
});

describe("Presence standalone status", () => {
  it("uses one Runtime caption, a library Desk button and a polite block lamp", () => {
    const { container } = open();
    expect(screen.getAllByRole("heading", { name: "Runtime" })).toHaveLength(1);
    expect(screen.getByRole("button", { name: /^Desk$/ })).toHaveClass("btn");
    expect(container.querySelector("a")).toBeNull();
    const status = screen.getByRole("status");
    expect(status).toHaveAttribute("aria-live", "polite");
    expect(status).toHaveTextContent("Ready");
    expect(status.querySelector(".gadget-lamp")).toHaveClass("is-block");
    expect(runtime.frame).toHaveBeenCalledWith("runtime_activity");
  });

  it.each([
    { state: "connected", label: "Ready", on: "true", tone: "ok" },
    { state: "connecting", label: "Connecting", on: "false", tone: "warn" },
    { state: "reconnecting", label: "Connecting", on: "false", tone: "warn" },
    { state: "offline", label: "Connecting", on: "false", tone: "warn" },
  ])("$state retains its existing label and lamp truth", ({ state, label, on, tone }) => {
    runtime.state = state;
    open();
    const lamp = screen.getByRole("status").querySelector(".gadget-lamp");
    expect(lamp).toHaveTextContent(label);
    expect(lamp).toHaveAttribute("data-on", on);
    expect(lamp).toHaveAttribute("data-tone", tone);
  });

  it.each(["connected", "offline"])("%s keeps a producer error label and fail tone", (state) => {
    runtime.state = state;
    runtime.frame.mockReturnValue({ state: "error", label: "Task failed", source: "declared test source" });
    open();
    const lamp = screen.getByRole("status").querySelector(".gadget-lamp");
    expect(lamp).toHaveTextContent("Task failed");
    expect(lamp).toHaveAttribute("data-tone", "fail");
    expect(lamp).toHaveAttribute("data-on", String(state === "connected"));
  });

  it("keeps the complete activity label on the block lamp", () => {
    const label = "Reading architecture migration decisions and release readiness across every platform and integration";
    runtime.frame.mockReturnValue({ state: "working", label });
    open();
    const lamp = screen.getByRole("status").querySelector(".gadget-lamp");
    expect(lamp).toHaveTextContent(label);
    expect(lamp).toHaveAttribute("title", label);
    expect(lamp).toHaveClass("is-block");
  });

  it.each(["pointer", "keyboard"])("%s returns to Desk with the exact current query", async (input) => {
    const search = "?context=review&mode=a%2Bb&context=second";
    window.history.replaceState({}, "", "/presence" + search);
    open();
    const desk = screen.getByRole("button", { name: /^Desk$/ });
    if (input === "pointer") fireEvent.click(desk);
    else {
      const user = userEvent.setup();
      await user.tab();
      expect(desk).toHaveFocus();
      await user.keyboard("{Enter}");
    }
    expect(screen.getByTestId("desk-location")).toHaveTextContent("/" + search);
    expect(screen.queryByRole("status")).toBeNull();
  });
});
