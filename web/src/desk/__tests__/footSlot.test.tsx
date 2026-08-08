// HS-129-01 — hosted cores publish their foot into the frame, while direct
// windows retain their in-place footer.
import { lazy } from "react";
import { render, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import {
  SurfaceWindowHost,
  type SurfaceRow,
} from "../components/SurfaceWindows";
import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";
import { SurfaceFooter } from "../surface/SurfaceFooter";
import "../components/window-chrome.css";

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

beforeEach(() => {
  useDesk.setState({
    items: EMPTY_ITEMS,
    panelMin: [],
    panelMax: [],
    panelOrder: [],
    panelRects: {},
  });
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
