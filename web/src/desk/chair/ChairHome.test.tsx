// HS-135-06 -- ChairHome tests: fresh load renders Chair; dock button
// swaps both ways; open DeskWindow survives the swap; route suite green.

import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ChairHome } from "./ChairHome";
import { useChairState } from "../chairState";
import { useDesk } from "../store";

// ---------------------------------------------------------------------------
// HS-136-03: CaptureHero now uses useRuntimeBus; mock it for this test.
// ---------------------------------------------------------------------------

vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    lastFrame: null,
    subscribe: vi.fn(() => () => {}),
  }),
}));

vi.mock("../components/FirstWords", () => ({
  FirstWords: ({ onDismiss }: { onDismiss?: () => void }) => (
    <section className="desk-first-words">
      <h2>Dictate one sentence</h2>
      <button type="button">Click to dictate</button>
      <button type="button" onClick={onDismiss}>Continue later</button>
    </section>
  ),
}));

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

/** Reset the Chair/Floor toggle to its default ("chair") between tests. */
function resetChairState() {
  useChairState.setState({ surface: "chair" });
  useDesk.setState({ editingId: null, pullouts: [] });
}

// ---------------------------------------------------------------------------
// fresh load renders Chair
// ---------------------------------------------------------------------------

describe("ChairHome landing surface", () => {
  beforeEach(resetChairState);

  it("renders the Chair surface on fresh load", () => {
    render(<ChairHome />);
    expect(screen.getByTestId("chair")).toBeInTheDocument();
    expect(screen.getByTestId("chair-hero")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Develop a thought" })).toBeInTheDocument();
    expect(screen.getByTestId("chair-lanes")).toBeInTheDocument();
  });

  it("default surface state is 'chair'", () => {
    expect(useChairState.getState().surface).toBe("chair");
  });

  it("removes the competing capture action while an editor owns the foreground", () => {
    useDesk.setState({ editingId: "active-note" });
    render(<ChairHome />);

    expect(screen.queryByRole("button", { name: "Develop a thought" })).not.toBeInTheDocument();
  });

  it("removes the competing capture action while a pullout owns the foreground", () => {
    useDesk.setState({ pullouts: [{ id: "note:active-note", origin: null }] });
    render(<ChairHome />);

    expect(screen.queryByRole("button", { name: "Develop a thought" })).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// HS-140-01: first value is the Chair, not a second welcome surface.
// ---------------------------------------------------------------------------

describe("ChairHome first-value composition", () => {
  beforeEach(resetChairState);

  it("reuses FirstWords and removes the normal Chair competition", () => {
    render(<ChairHome arrivalRequired />);

    expect(screen.getByTestId("chair-first-value")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Dictate one sentence" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Click to dictate" })).toBeInTheDocument();
    expect(screen.queryByTestId("chair")).not.toBeInTheDocument();
    expect(screen.queryByTestId("chair-hero")).not.toBeInTheDocument();
    expect(screen.queryByTestId("chair-lanes")).not.toBeInTheDocument();
  });

  it("makes thought capture the normal-owner Chair entry", () => {
    render(<ChairHome arrivalRequired={false} />);

    expect(screen.getByTestId("chair")).toBeInTheDocument();
    expect(screen.getByTestId("chair-hero")).toBeInTheDocument();
    expect(screen.getByTestId("chair-lanes")).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Dictate one sentence" }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Develop a thought" })).toBeInTheDocument();
  });

  it("waits for the refreshed server prop before revealing the normal Chair", () => {
    render(<ChairHome arrivalRequired />);

    fireEvent.click(screen.getByRole("button", { name: "Continue later" }));

    expect(screen.getByTestId("chair-first-value")).toBeInTheDocument();
    expect(screen.queryByTestId("chair")).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Chair/Floor toggle state
// ---------------------------------------------------------------------------

describe("Chair/Floor toggle state", () => {
  beforeEach(resetChairState);

  it("toggle() swaps chair -> floor -> chair", () => {
    expect(useChairState.getState().surface).toBe("chair");
    act(() => useChairState.getState().toggle());
    expect(useChairState.getState().surface).toBe("floor");
    act(() => useChairState.getState().toggle());
    expect(useChairState.getState().surface).toBe("chair");
  });

  it("setSurface() sets an explicit surface", () => {
    act(() => useChairState.getState().setSurface("floor"));
    expect(useChairState.getState().surface).toBe("floor");
    act(() => useChairState.getState().setSurface("chair"));
    expect(useChairState.getState().surface).toBe("chair");
  });
});

// ---------------------------------------------------------------------------
// ChairHome renders the lane registry generically
// ---------------------------------------------------------------------------

describe("ChairHome lane registry composition", () => {
  beforeEach(resetChairState);

  it("renders the Door registry slot and leaves activeWork empty", () => {
    render(<ChairHome />);
    expect(screen.getByTestId("chair")).toBeInTheDocument();
    expect(screen.getByTestId("chair-lanes")).toBeInTheDocument();
    expect(screen.getByTestId("chair-lanes").querySelector('[data-lane="door"]')).toBeTruthy();
    expect(screen.getByTestId("chair-lanes").querySelector('[data-lane="brief"]')).toBeNull();
    expect(screen.getByTestId("chair-lanes").querySelector('[data-lane="follow-through"]')).toBeNull();
    expect(screen.getByTestId("chair-active-work")).toBeEmptyDOMElement();
  });
});
