// HS-135-05 -- Chair surface tests: lane contract (maxItems bound,
// open-in-window fires, fixed order), the 300ms all-blank fallback
// (fake timers), and ember-only (no accent-cool/gradient in chair.css).

import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import fs from "node:fs";
import path from "node:path";
import { Chair } from "./Chair";
import { ChairLane } from "./Lane";
import type { LaneItem } from "./Lane";
import { LANE_ORDER, DEFAULT_MAX_ITEMS } from "./laneContract";

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

function makeItems(count: number): LaneItem[] {
  return Array.from({ length: count }, (_, i) => ({
    id: `item-${i}`,
    title: `Item ${i}`,
    detail: `Detail ${i}`,
  }));
}

// ---------------------------------------------------------------------------
// lane contract
// ---------------------------------------------------------------------------

describe("Chair lane contract", () => {
  it("renders four lane slots in the fixed order", () => {
    const onOpen = vi.fn();
    const { container } = render(
      <Chair
        lanes={{
          brief: (
            <ChairLane
              title="BRIEF"
              items={makeItems(2)}
              onOpenInWindow={onOpen}
              surfaceId="intelligence"
            />
          ),
          "follow-through": (
            <ChairLane
              title="FOLLOW-THROUGH"
              items={makeItems(1)}
              onOpenInWindow={onOpen}
              surfaceId="follow-through"
            />
          ),
          meetings: (
            <ChairLane
              title="MEETINGS"
              items={makeItems(3)}
              onOpenInWindow={onOpen}
              surfaceId="meetings"
            />
          ),
          agents: (
            <ChairLane
              title="AGENTS"
              items={makeItems(1)}
              onOpenInWindow={onOpen}
              surfaceId="agents"
            />
          ),
        }}
      />,
    );
    const laneEls = container.querySelectorAll("[data-lane]");
    expect(laneEls).toHaveLength(4);
    const order = Array.from(laneEls).map((el) => el.getAttribute("data-lane"));
    expect(order).toEqual([...LANE_ORDER]);
  });

  it("LANE_ORDER is exactly [brief, follow-through, meetings, agents]", () => {
    expect(LANE_ORDER).toEqual(["brief", "follow-through", "meetings", "agents"]);
  });

  it("DEFAULT_MAX_ITEMS is 12", () => {
    expect(DEFAULT_MAX_ITEMS).toBe(12);
  });

  it("maxItems caps the visible rows", () => {
    const onOpen = vi.fn();
    render(
      <ChairLane
        title="TEST"
        maxItems={3}
        items={makeItems(7)}
        onOpenInWindow={onOpen}
        surfaceId="test"
        footerVerb="Open Test"
      />,
    );
    // Only 3 items should be visible in the list.
    const rows = screen.getAllByRole("button", { name: /Item \d/ });
    expect(rows).toHaveLength(3);
    // The footer shows the overflow.
    expect(screen.getByText(/4 more/)).toBeInTheDocument();
  });

  it("header click fires onOpenInWindow with the surfaceId", () => {
    const onOpen = vi.fn();
    render(
      <ChairLane
        title="BRIEF"
        items={makeItems(2)}
        onOpenInWindow={onOpen}
        surfaceId="intelligence"
      />,
    );
    const headerBtn = screen.getByLabelText("Open BRIEF");
    fireEvent.click(headerBtn);
    expect(onOpen).toHaveBeenCalledWith("intelligence");
  });

  it("row click fires onOpenInWindow with the item id", () => {
    const onOpen = vi.fn();
    render(
      <ChairLane
        title="BRIEF"
        items={[{ id: "abc-123", title: "My item" }]}
        onOpenInWindow={onOpen}
        surfaceId="intelligence"
      />,
    );
    // The SurfaceRow renders an onOpen button wrapping the title.
    const rowBtn = screen.getByRole("button", { name: /My item/ });
    fireEvent.click(rowBtn);
    expect(onOpen).toHaveBeenCalledWith("abc-123");
  });

  it("hero slot renders its placeholder", () => {
    render(
      <Chair
        hero={<div data-testid="hero-content">MIC PLACEHOLDER</div>}
        lanes={{}}
      />,
    );
    expect(screen.getByTestId("hero-content")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// 300ms all-blank fallback (counsel condition 2)
// ---------------------------------------------------------------------------

describe("Chair 300ms all-blank fallback", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("shows nothing before 300ms when all lanes are blank", () => {
    render(<Chair lanes={{}} />);
    // Before the timer fires, no fallback state.
    expect(screen.queryByText("Nothing yet")).not.toBeInTheDocument();
  });

  it("shows exactly ONE SurfaceState after 300ms when all lanes are blank", () => {
    render(<Chair lanes={{}} />);
    act(() => {
      vi.advanceTimersByTime(300);
    });
    expect(screen.getByText("Nothing yet")).toBeInTheDocument();
  });

  it("does NOT show fallback when at least one lane has content", () => {
    const onOpen = vi.fn();
    render(
      <Chair
        lanes={{
          brief: (
            <ChairLane
              title="BRIEF"
              items={makeItems(1)}
              onOpenInWindow={onOpen}
              surfaceId="intelligence"
            />
          ),
        }}
      />,
    );
    act(() => {
      vi.advanceTimersByTime(500);
    });
    expect(screen.queryByText("Nothing yet")).not.toBeInTheDocument();
  });

  it("clears the fallback when a lane arrives after the timer fired", () => {
    const onOpen = vi.fn();
    const { rerender } = render(<Chair lanes={{}} />);
    act(() => {
      vi.advanceTimersByTime(300);
    });
    expect(screen.getByText("Nothing yet")).toBeInTheDocument();

    // A lane arrives -- the fallback should clear.
    rerender(
      <Chair
        lanes={{
          brief: (
            <ChairLane
              title="BRIEF"
              items={makeItems(1)}
              onOpenInWindow={onOpen}
              surfaceId="intelligence"
            />
          ),
        }}
      />,
    );
    expect(screen.queryByText("Nothing yet")).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// ember-only: no accent-cool/gradient in chair.css (style grep test)
// ---------------------------------------------------------------------------

describe("Chair ember-only (no accent-cool/gradient in chair.css)", () => {
  it("chair.css uses neither --accent-cool nor --accent-gradient as CSS values", () => {
    const cssPath = path.resolve(__dirname, "chair.css");
    const css = fs.readFileSync(cssPath, "utf-8");
    // Strip CSS comments so only property/value text is checked.
    const stripped = css.replace(/\/\*[\s\S]*?\*\//g, "");
    expect(stripped).not.toMatch(/--accent-cool/);
    expect(stripped).not.toMatch(/--accent-gradient/);
  });
});
