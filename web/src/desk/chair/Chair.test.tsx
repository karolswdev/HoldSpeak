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
  it("renders Door, Meetings, and Agents in the fixed order", () => {
    const onOpen = vi.fn();
    const { container } = render(
      <Chair
        lanes={{
          door: <ChairLane title="DOOR" items={makeItems(2)} onOpenInWindow={onOpen} surfaceId="door" />,
          meetings: <ChairLane title="MEETINGS" items={makeItems(3)} onOpenInWindow={onOpen} surfaceId="meetings" />,
          agents: <ChairLane title="AGENTS" items={makeItems(1)} onOpenInWindow={onOpen} surfaceId="agents" />,
        }}
      />,
    );
    const laneEls = container.querySelectorAll("[data-lane]");
    expect(laneEls).toHaveLength(3);
    const order = Array.from(laneEls).map((el) => el.getAttribute("data-lane"));
    expect(order).toEqual([...LANE_ORDER]);
  });

  it("LANE_ORDER is exactly [door, meetings, agents]", () => {
    expect(LANE_ORDER).toEqual(["door", "meetings", "agents"]);
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

  it("renders immediate owner work outside the fixed four-lane registry", () => {
    const { container } = render(
      <Chair activeWork={<section>Finish thoughts</section>} lanes={{}} />,
    );
    expect(screen.getByTestId("chair-active-work")).toHaveTextContent("Finish thoughts");
    expect(container.querySelectorAll("[data-lane]")).toHaveLength(0);
    expect(LANE_ORDER).toEqual(["door", "meetings", "agents"]);
  });
});

// ---------------------------------------------------------------------------
// The all-blank invitation (counsel condition 2, mechanism revised at the
// acceptance review: always rendered, CSS-gated by the :has() empty rule)
// ---------------------------------------------------------------------------

describe("Chair all-blank invitation", () => {
  it("renders the invitation node always (CSS owns visibility)", () => {
    render(<Chair lanes={{}} />);
    expect(screen.getByText("Start rough. Keep developing it.")).toBeInTheDocument();
  });

  it("keeps the invitation node in the DOM when lanes have content (hidden by CSS)", () => {
    const onOpen = vi.fn();
    render(
      <Chair
        lanes={{
          door: (
            <ChairLane
              title="DOOR"
              items={makeItems(1)}
              onOpenInWindow={onOpen}
              surfaceId="door"
            />
          ),
        }}
      />,
    );
    expect(screen.getByText("Start rough. Keep developing it.")).toBeInTheDocument();
  });

  it("chair.css gates the invitation and hero scaling on the :has() empty rule", () => {
    const css = fs.readFileSync(path.resolve(__dirname, "chair.css"), "utf-8");
    expect(css).toContain(".chair-empty-invitation { display: none; }");
    expect(css).toContain(
      ".chair:not(:has(.chair-lane .surface-section)):not(:has(.finish-thoughts)) .chair-empty-invitation",
    );
    expect(css).toContain(
      ".chair:not(:has(.chair-lane .surface-section)):not(:has(.finish-thoughts)) .chair-hero",
    );
    expect(css).toContain(
      ".desk-next .chair:not(:has(.chair-lane .surface-section)):not(:has(.finish-thoughts)) .chair-empty-invitation",
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
    expect(stripped).toMatch(/\.chair:not\(:has\(\.chair-lane \.surface-section\)\):not\(:has\(\.finish-thoughts\)\)/);
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

  it("lets populated lanes shrink inside a 393px Chair", () => {
    // `1fr` alone retains the widest row as its automatic minimum and made
    // a real returned Chair widen the phone document to 464px.
    expect(stripped).toMatch(
      /\.chair-lanes\s*\{[^}]*grid-template-columns:\s*minmax\(0,\s*1fr\)/,
    );
    expect(stripped).toMatch(/\.chair-lane\s*\{[^}]*min-width:\s*0/);
  });

  it("seats the normal Chair inside the complete working band", () => {
    expect(stripped).toMatch(
      /\.chair\s*\{[^}]*min-height:\s*calc\(100dvh\s*-\s*var\(--desk-snap-top\)/,
    );
    expect(stripped).toMatch(
      /\.chair\s*\{[^}]*margin:\s*var\(--desk-work-top\)\s+auto\s+var\(--desk-work-bottom\)/,
    );
  });

  it("caps a populated short Chair and scrolls its contained lane column", () => {
    expect(stripped).toMatch(
      /\.chair:not\(\.chair-first-value\)\s*\{[^}]*box-sizing:\s*border-box[^}]*height:\s*calc\(100dvh\s*-\s*var\(--desk-work-top\)\s*-\s*var\(--desk-work-bottom\)\)/,
    );
    expect(stripped).toMatch(
      /\.chair-lanes\s*\{[^}]*flex:\s*1\s+1\s+auto[^}]*min-height:\s*0[^}]*overflow-y:\s*auto/,
    );
  });

  it("caps the Door board and future rail inside the short phone lane", () => {
    expect(stripped).toMatch(/@media\s*\(max-height:\s*720px\)[\s\S]*?\.door-board-viewport\s*\{[^}]*max-block-size/);
    expect(stripped).toMatch(/@media\s*\(max-height:\s*720px\)[\s\S]*?\.door-upcoming-list\s*\{[^}]*max-block-size/);
  });

  it("does not reserve absent chrome around the first-value Chair", () => {
    expect(stripped).toMatch(
      /\.chair\.chair-first-value\s*\{[^}]*margin:\s*0\s+auto/,
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
        lanes={{ door: <NullLane /> }}
      />,
    );
    const doorLane = container.querySelector('[data-lane="door"]');
    expect(doorLane).not.toBeNull();
    // The wrapper has no child ELEMENTS (NullLane rendered null).
    expect(doorLane!.childElementCount).toBe(0);
  });

  it("populated lanes have content for the grid layout", () => {
    const onOpen = vi.fn();
    const { container } = render(
      <Chair
        hero={<div>MIC</div>}
        lanes={{
          door: (
            <ChairLane
              title="DOOR"
              items={makeItems(3)}
              onOpenInWindow={onOpen}
              surfaceId="door"
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
