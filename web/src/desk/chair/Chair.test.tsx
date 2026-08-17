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
// The all-blank invitation (counsel condition 2, mechanism revised at the
// acceptance review: always rendered, CSS-gated by the :has() empty rule)
// ---------------------------------------------------------------------------

describe("Chair all-blank invitation", () => {
  it("renders the invitation node always (CSS owns visibility)", () => {
    render(<Chair lanes={{}} />);
    expect(screen.getByText("Speak. The desk will file it.")).toBeInTheDocument();
  });

  it("keeps the invitation node in the DOM when lanes have content (hidden by CSS)", () => {
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
    expect(screen.getByText("Speak. The desk will file it.")).toBeInTheDocument();
  });

  it("chair.css gates the invitation and hero scaling on the :has() empty rule", () => {
    const css = fs.readFileSync(path.resolve(__dirname, "chair.css"), "utf-8");
    expect(css).toContain(".chair-empty-invitation { display: none; }");
    expect(css).toContain(
      ".chair:not(:has(.chair-lane .surface-section)) .chair-empty-invitation",
    );
    expect(css).toContain(
      ".chair:not(:has(.chair-lane .surface-section)) .chair-hero",
    );
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

// ---------------------------------------------------------------------------
// HS-135-13: void polish -- the hero holds the room, lanes grid, empty collapse
// ---------------------------------------------------------------------------

describe("Chair void polish (HS-135-13)", () => {
  const cssPath = path.resolve(__dirname, "chair.css");
  const css = fs.readFileSync(cssPath, "utf-8");
  const stripped = css.replace(/\/\*[\s\S]*?\*\//g, "");

  it("chair.css contains the empty-state hero treatment selector", () => {
    // The :has()-based selector that scales the hero when no lane has data.
    // A lane is populated when it contains .surface-section (real data rows).
    expect(stripped).toMatch(/\.chair:not\(:has\(\.chair-lane \.surface-section\)\)/);
    // The hero gets flex: 1 in the sparse state.
    expect(stripped).toMatch(/\.chair-hero[\s\S]*?flex:\s*1/);
  });

  it("chair.css contains the hero key scale-up in the sparse state", () => {
    // The hero key gets larger when lanes are quiet.
    expect(stripped).toMatch(/\.capture-hero-key[\s\S]*?calc\(var\(--size-key\)/);
  });

  it("chair.css hides empty lane wrappers with :empty", () => {
    expect(stripped).toMatch(/\.chair-lane:empty\s*\{[^}]*display:\s*none/);
  });

  it("chair.css uses CSS grid for lane layout", () => {
    expect(stripped).toMatch(/\.chair-lanes\s*\{[^}]*display:\s*grid/);
    expect(stripped).toMatch(/grid-template-columns:\s*1fr\s*1fr/);
  });

  it("chair.css fills the working area height", () => {
    expect(stripped).toMatch(
      /\.chair\s*\{[^}]*min-height:\s*calc\(100vh\s*-\s*var\(--desk-snap-top\)/,
    );
  });

  it("empty lane wrappers render as empty divs (enabling :empty CSS)", () => {
    // When a lane's ReactNode is a component that returns null, the wrapper
    // div is empty. This test confirms the wrapper renders without children
    // when the lane content returns null.
    const NullLane = () => null;
    const { container } = render(
      <Chair
        hero={<div data-testid="hero-content">MIC</div>}
        lanes={{ brief: <NullLane /> }}
      />,
    );
    const briefLane = container.querySelector('[data-lane="brief"]');
    expect(briefLane).not.toBeNull();
    // The wrapper has no child ELEMENTS (NullLane rendered null).
    expect(briefLane!.childElementCount).toBe(0);
  });

  it("populated lanes have content for the grid layout", () => {
    const onOpen = vi.fn();
    const { container } = render(
      <Chair
        hero={<div>MIC</div>}
        lanes={{
          brief: (
            <ChairLane
              title="BRIEF"
              items={makeItems(3)}
              onOpenInWindow={onOpen}
              surfaceId="intelligence"
            />
          ),
          meetings: (
            <ChairLane
              title="MEETINGS"
              items={makeItems(2)}
              onOpenInWindow={onOpen}
              surfaceId="meetings"
            />
          ),
        }}
      />,
    );
    const lanes = container.querySelectorAll(".chair-lane:not(:empty)");
    // jsdom doesn't support :empty pseudo-class fully, so check child count.
    const populatedLanes = container.querySelectorAll("[data-lane]");
    const withContent = Array.from(populatedLanes).filter(
      (el) => el.childElementCount > 0,
    );
    expect(withContent.length).toBe(2);
  });
});
