// HS-158-05 — title slot: cores push a runtime title into the hosting
// window's head, overriding the manifest label. Unmount restores the
// manifest label (no stale titles on rescope/close).
import { lazy } from "react";
import { render, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  SurfaceWindowHost,
  type SurfaceRow,
} from "../components/SurfaceWindows";
import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";
import { TitleSlotContext, useWindowTitle } from "../surface/title";
import "../components/window-chrome.css";
import "../components/dock.css";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function makeRow(id: string, Core: React.ComponentType<any>): SurfaceRow {
  return {
    key: `test-${id}`,
    id: `test-${id}`,
    title: "Manifest Label",
    glyph: "T",
    eyebrow: "Test",
    Core: lazy(async () => ({ default: Core })),
  };
}

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
  vi.restoreAllMocks();
});

describe("HS-158-05 title slot", () => {
  it("shows the manifest title by default when no core pushes a title", async () => {
    const PlainCore = () => <p>Plain body</p>;
    const row = makeRow("plain", PlainCore);
    const { container } = render(
      <div className="desk-next">
        <SurfaceWindowHost row={row} scope={undefined} items={EMPTY_ITEMS} />
      </div>,
    );

    await waitFor(() =>
      expect(container.querySelector(".desk-window-title")).toBeTruthy(),
    );
    expect(container.querySelector(".desk-window-title")!.textContent).toBe(
      "Manifest Label",
    );
  });

  it("a core-pushed title overrides the manifest label in the head", async () => {
    const PushCore = () => {
      useWindowTitle("Runtime Title", ["Runtime Title"]);
      return <p>body</p>;
    };
    const row = makeRow("push", PushCore);
    const { container } = render(
      <div className="desk-next">
        <SurfaceWindowHost row={row} scope={undefined} items={EMPTY_ITEMS} />
      </div>,
    );

    await waitFor(() =>
      expect(
        container.querySelector(".desk-window-title")?.textContent,
      ).toBe("Runtime Title"),
    );
  });

  it("unmounting the pushing core restores the manifest label", async () => {
    const PushCore = () => {
      useWindowTitle("Override", ["Override"]);
      return <p>pushing</p>;
    };
    const row = makeRow("restore", PushCore);
    const { container, unmount } = render(
      <div className="desk-next">
        <SurfaceWindowHost row={row} scope={undefined} items={EMPTY_ITEMS} />
      </div>,
    );

    await waitFor(() =>
      expect(
        container.querySelector(".desk-window-title")?.textContent,
      ).toBe("Override"),
    );

    // Unmount and re-render with a plain core.
    unmount();
    const PlainCore = () => <p>plain</p>;
    const plainRow = makeRow("restore", PlainCore);
    const { container: c2 } = render(
      <div className="desk-next">
        <SurfaceWindowHost
          row={plainRow}
          scope={undefined}
          items={EMPTY_ITEMS}
        />
      </div>,
    );

    await waitFor(() =>
      expect(c2.querySelector(".desk-window-title")?.textContent).toBe(
        "Manifest Label",
      ),
    );
  });

  it("useWindowTitle cleanup calls setter with null on unmount", () => {
    const setTitle = vi.fn();

    function Inner() {
      useWindowTitle("Test Override", ["Test Override"]);
      return null;
    }

    const { unmount } = render(
      <TitleSlotContext.Provider value={setTitle}>
        <Inner />
      </TitleSlotContext.Provider>,
    );

    expect(setTitle).toHaveBeenCalledWith("Test Override");
    setTitle.mockClear();

    unmount();
    expect(setTitle).toHaveBeenCalledWith(null);
  });

  it("changing deps republishes the title", () => {
    const setTitle = vi.fn();

    function Inner({ name }: { name: string }) {
      useWindowTitle(name, [name]);
      return null;
    }

    const { rerender } = render(
      <TitleSlotContext.Provider value={setTitle}>
        <Inner name="Alpha" />
      </TitleSlotContext.Provider>,
    );

    expect(setTitle).toHaveBeenCalledWith("Alpha");

    rerender(
      <TitleSlotContext.Provider value={setTitle}>
        <Inner name="Beta" />
      </TitleSlotContext.Provider>,
    );

    expect(setTitle).toHaveBeenCalledWith("Beta");
  });
});
