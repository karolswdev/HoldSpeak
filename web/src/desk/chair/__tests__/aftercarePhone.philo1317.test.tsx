/* PHILO-13-17 (C7, Q4 + Q4b; the owner's ruling, ratified 2026-10-03):
 * at 393 an arriving aftercare card opens the Capture window, so it lands in
 * Capture's slot; a desk window in front iconifies (never closes). Capture
 * stays in the ring until it is closed; swiped away, the card waits for it
 * and NEVER takes the fixed overlay over work (AmbientLayer's fallback).
 * Red on main: the card arrives fixed (`ambient-aftercare-fixed`) over The
 * week, and once Capture is left the card falls back to the fixed overlay.
 */
import { act, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AmbientLayer } from "../../../components/AmbientLayer";
import { ChairHome } from "../ChairHome";
import {
  dismissAftercare,
  publishAftercare,
} from "../../intelligenceAttention";
import { useChairState } from "../../chairState";
import { EMPTY_ITEMS } from "../../api";
import { useDesk } from "../../store";

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
}));

vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: mocks.apiFetch,
}));

vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    lastFrame: null,
    subscribe: () => () => undefined,
  }),
  useRuntimeFrame: () => null,
}));

vi.mock("../../thoughts", () => ({
  unfinishedThoughts: async () => ({ items: [] }),
}));

vi.mock("../../components/MicButton", () => ({ MicButton: () => null }));

vi.mock("../../projections", () => {
  const state = {
    ambient: [],
    subject_counts: {},
    refreshAmbient: vi.fn(),
    present: vi.fn(),
  };
  const useProjections = Object.assign(
    (selector: (value: typeof state) => unknown) => selector(state),
    { getState: () => state },
  );
  return { useProjections };
});

import { lazy } from "react";
import { useChairWindows } from "../chairWindows";
import { SurfaceWindowHost, type SurfaceRow } from "../../components/SurfaceWindows";
import { announceWindow, retractWindow } from "../../components/window/windowRegistry";
import { phoneRing, stepRing } from "../../components/window/phoneRing";

function publish() {
  act(() => {
    publishAftercare({ meeting_id: "meeting-c7", title: "Ledger cutover sync", open_total: 2, decided_total: 1 });
  });
}

const fixed = () => document.querySelector(".ambient-aftercare-fixed");
const inCapture = () =>
  document.querySelector('[data-testid="arrival-aftercare-slot"] .ambient-aftercare-flow');

beforeEach(() => {
  vi.stubGlobal("matchMedia", (query: string) => ({
    matches: query.includes("720px"),
    media: query,
    addEventListener: () => {},
    removeEventListener: () => {},
    addListener: () => {},
    removeListener: () => {},
    onchange: null,
    dispatchEvent: () => false,
  }));
  Object.defineProperty(window, "innerWidth", { configurable: true, value: 393 });
  mocks.apiFetch.mockImplementation(async (path: string) => {
    if (path === "/api/desk/needs-you")
      return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true };
    if (path === "/api/door")
      return { board: {}, upcoming: [], counts: {}, calendar_configured: false };
    if (path === "/api/inference/assignments")
      return { schema: "InferenceAssignmentSummary@1", rows: [], task_overrides: [], issue_count: 0 };
    if (path === "/api/settings") return { presence: { enabled: false } };
    return null;
  });
  useChairState.setState({ surface: "chair" });
  useChairWindows.setState({ closed: {}, phone: "chair:week", captureInRing: false });
  useDesk.setState({
    items: EMPTY_ITEMS, divedZone: null, selectedIds: [], pullouts: [], editingId: null,
    askOpen: false, panelRects: {}, panelSaved: [], panelOrder: [], panelMin: [],
  });
  act(() => dismissAftercare());
});

afterEach(() => {
  act(() => dismissAftercare());
  retractWindow("surface:meetings");
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  Object.defineProperty(window, "innerWidth", { configurable: true, value: 1440 });
});

describe("PHILO-13-17 C7 aftercare at 393", () => {
  it("arrive -> swipe away -> Capture in the ring -> return: never a fixed card", async () => {
    render(<><AmbientLayer /><ChairHome /></>);
    await screen.findByTestId("chair-desk");
    publish();
    await waitFor(() => expect(useChairWindows.getState().phone).toBe("chair:capture"));
    await waitFor(() => expect(inCapture()).toBeTruthy());
    expect(fixed()).toBeNull();

    act(() => void stepRing(1)); // swipe away: wraps to Needs you
    expect(useChairWindows.getState().phone).toBe("chair:needs");
    await waitFor(() => expect(document.querySelector(".ambient-aftercare")).toBeNull());
    expect(fixed()).toBeNull();
    expect(phoneRing().map((w) => w.label)).toEqual(["Needs you", "Brief", "The week", "Capture"]);

    act(() => void stepRing(-1)); // back to Capture
    await waitFor(() => expect(inCapture()).toBeTruthy());
    expect(fixed()).toBeNull();
  });

  it("a desk window in front iconifies when the card arrives; it is not closed", async () => {
    render(<><AmbientLayer /><ChairHome /></>);
    await screen.findByTestId("chair-desk");
    act(() => {
      announceWindow("surface:meetings", "Meetings", "", () => retractWindow("surface:meetings"));
      useDesk.getState().focusPanel("surface:meetings");
    });
    publish();
    await waitFor(() => expect(useChairWindows.getState().phone).toBe("chair:capture"));
    expect(useDesk.getState().panelMin).toContain("surface:meetings");
    expect(phoneRing().map((w) => w.id)).toContain("surface:meetings");
    await waitFor(() => expect(inCapture()).toBeTruthy());
  });

  it("Muad'Dib's ruling 2026-10-03: the front window that hosts the card's slot keeps it; Capture does not open", async () => {
    const row: SurfaceRow = {
      key: "review-meetings", id: "c7-meetings-window", title: "Meetings", glyph: "M", eyebrow: "Test",
      Core: lazy(async () => ({ default: () => <p>The meeting record</p> })),
    };
    const { container } = render(<><AmbientLayer /><ChairHome /><SurfaceWindowHost row={row} scope={undefined} items={EMPTY_ITEMS} /></>);
    await screen.findByTestId("chair-desk");
    const shell = await waitFor(() => {
      const el = container.querySelector<HTMLElement>(".desk-surface-window.is-front");
      expect(el?.querySelector('[data-aftercare-window-slot="top"]')).toBeTruthy();
      return el!;
    });
    const id = shell.id;
    publish();
    await waitFor(() => expect(shell.querySelector('[data-aftercare-window-slot="top"] .ambient-aftercare-flow')).toBeTruthy());
    expect(useChairWindows.getState().phone).toBe("chair:week");
    expect(useDesk.getState().panelMin).not.toContain(id);
    expect(shell).toHaveClass("is-front");
    expect(fixed()).toBeNull();
  });

  it("1440 control: Capture already holds the card; nothing moves", async () => {
    vi.stubGlobal("matchMedia", (query: string) => ({
      matches: false, media: query, addEventListener: () => {}, removeEventListener: () => {},
      addListener: () => {}, removeListener: () => {}, onchange: null, dispatchEvent: () => false,
    }));
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 1440 });
    useChairWindows.setState({ closed: {}, phone: "chair:needs", captureInRing: false });
    render(<><AmbientLayer /><ChairHome /></>);
    await screen.findByTestId("chair-desk");
    publish();
    await waitFor(() => expect(inCapture()).toBeTruthy());
    expect(useChairWindows.getState().phone).toBe("chair:needs");
    expect(useChairWindows.getState().captureInRing).toBe(false);
  });
});
