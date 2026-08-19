// HS-135-06 -- ChairHome tests: fresh load renders Chair; dock button
// swaps both ways; open DeskWindow survives the swap; route suite green.

import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ChairHome } from "./ChairHome";
import { useChairState } from "../chairState";

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
    expect(screen.getByTestId("chair-lanes")).toBeInTheDocument();
  });

  it("default surface state is 'chair'", () => {
    expect(useChairState.getState().surface).toBe("chair");
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

  it("keeps the existing Chair byte-for-byte path for a normal owner", () => {
    render(<ChairHome arrivalRequired={false} />);

    expect(screen.getByTestId("chair")).toBeInTheDocument();
    expect(screen.getByTestId("chair-hero")).toBeInTheDocument();
    expect(screen.getByTestId("chair-lanes")).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Dictate one sentence" }),
    ).not.toBeInTheDocument();
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

  it("renders registered lanes from the registry (HS-135-08 follow-through present)", () => {
    render(<ChairHome />);
    // The Chair renders; the follow-through lane slot exists (HS-135-08
    // registered it). The 300ms all-blank fallback does NOT fire because
    // hasAnyLane is true.
    expect(screen.getByTestId("chair")).toBeInTheDocument();
    expect(screen.getByTestId("chair-lanes")).toBeInTheDocument();
    // The follow-through lane slot is rendered.
    const laneEl = screen.getByTestId("chair-lanes").querySelector('[data-lane="follow-through"]');
    expect(laneEl).toBeTruthy();
  });
});
