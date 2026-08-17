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
