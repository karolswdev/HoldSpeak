// HS-129-01 — hosted cores publish their foot into the frame, while direct
// windows retain their in-place footer.
import { lazy } from "react";
import { act, render, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  SurfaceWindowHost,
  type SurfaceRow,
} from "../components/SurfaceWindows";
import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";
import { SurfaceFooter } from "../surface/SurfaceFooter";
import { keepPlace } from "../deskMemory";
import { surfaceScrollPlaceKey } from "../hooks/useSurfaceScrollPlace";
import "../components/window-chrome.css";
import "../components/dock.css";

const HostedCore = () => (
  <>
    <p>Hosted body</p>
    <SurfaceFooter receipt={<span>Hosted receipt</span>} />
  </>
);

const hostedRow: SurfaceRow = {
  key: "test-foot-slot",
  id: "test-foot-slot",
  title: "Foot slot",
  glyph: "▣",
  eyebrow: "Test",
  Core: lazy(async () => ({ default: HostedCore })),
};

const defaultMatchMedia = window.matchMedia;

beforeEach(() => {
  useDesk.setState({
    items: EMPTY_ITEMS,
    panelMin: [],
    panelMax: [],
    panelOrder: [],
    panelRects: {},
  });
});

afterEach(() => {
  window.matchMedia = defaultMatchMedia;
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe("HS-129-01 foot slot", () => {
  it("makes a hosted footer a sibling after the scrolling body", async () => {
    const { container } = render(
      <div className="desk-next">
        <SurfaceWindowHost row={hostedRow} scope={undefined} items={EMPTY_ITEMS} />
      </div>,
    );

    await waitFor(() => expect(container.querySelector(".surface-footer")).toBeTruthy());
    const shell = container.querySelector(".desk-surface-window");
    const body = container.querySelector(".desk-surface-body");
    const footer = container.querySelector(".surface-footer");
    expect(shell).toBeTruthy();
    expect(body).toBeTruthy();
    expect(footer?.parentElement).toBe(shell);
    expect(body?.contains(footer)).toBe(false);
    expect(body?.nextElementSibling).toBe(footer);
  });

  it("leaves shell overflow alone and gives the body the scroll path", async () => {
    const { container } = render(
      <div className="desk-next">
        <SurfaceWindowHost row={hostedRow} scope={undefined} items={EMPTY_ITEMS} />
      </div>,
    );

    await waitFor(() => expect(container.querySelector(".desk-surface-body")).toBeTruthy());
    const shell = container.querySelector(".desk-surface-window") as HTMLElement;
    const body = container.querySelector(".desk-surface-body") as HTMLElement;
    expect(getComputedStyle(shell).overflow).not.toBe("auto");
    expect(getComputedStyle(body).overflow).toBe("auto");
  });

  it("restores the hosted body's place for the window scope", async () => {
    vi.useFakeTimers();
    keepPlace(surfaceScrollPlaceKey(hostedRow.id), "72");
    const { container } = render(
      <div className="desk-next">
        <SurfaceWindowHost row={hostedRow} scope={undefined} items={EMPTY_ITEMS} />
      </div>,
    );

    const body = container.querySelector(".desk-surface-body") as HTMLElement;
    expect(body).toBeTruthy();
    Object.defineProperty(body, "scrollHeight", { configurable: true, value: 420 });
    Object.defineProperty(body, "clientHeight", { configurable: true, value: 180 });
    act(() => vi.runOnlyPendingTimers());
    expect(body.scrollTop).toBe(72);
  });

  it("keeps a compact sheet's scroll path in the body", async () => {
    // HS-129-02 — a phone sheet keeps the same frame anatomy as a desktop
    // window: only its material scrolls.
    window.matchMedia = vi.fn((query: string) =>
      ({
        matches: query === "(max-width: 720px)",
        media: query,
        onchange: null,
        addListener: () => {},
        removeListener: () => {},
        addEventListener: () => {},
        removeEventListener: () => {},
        dispatchEvent: () => false,
      }) as MediaQueryList,
    );

    const { container } = render(
      <div className="desk-next">
        <SurfaceWindowHost row={hostedRow} scope={undefined} items={EMPTY_ITEMS} />
      </div>,
    );

    await waitFor(() => expect(container.querySelector(".surface-footer")).toBeTruthy());
    const shell = container.querySelector(".desk-surface-window") as HTMLElement;
    const body = container.querySelector(".desk-surface-body") as HTMLElement;
    const footer = container.querySelector(".surface-footer");
    expect(shell).toHaveClass("is-sheet");
    expect(getComputedStyle(body).overflow).toBe("auto");
    expect(body.contains(footer)).toBe(false);
    expect(footer?.parentElement).toBe(shell);
  });

  it("keeps an unhosted footer in place", () => {
    const { container } = render(
      <div className="zone-window-reference">
        <SurfaceFooter receipt={<span>Zone receipt</span>} />
      </div>,
    );
    const reference = container.querySelector(".zone-window-reference");
    expect(reference?.querySelector(".surface-footer")).toBeTruthy();
    expect(reference?.textContent).toContain("Zone receipt");
  });
});
