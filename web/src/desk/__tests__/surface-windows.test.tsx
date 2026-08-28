// HS-103-01 — the desk remembers it was open: opening/closing a surface
// window persists the open set (its own localStorage slot, `SurfaceWindows`
// is the sole writer), and a fresh module load (the reload simulation)
// rehydrates from it.
import { act, render, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { __resetSurfaces, openSurface, stageSurfaceOpen } from "../shell";
import {
  SurfaceWindows,
  useSurfaceWindows,
} from "../components/SurfaceWindows";

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
  useSurfaceWindows.setState({ open: {} });
  __resetSurfaces();
});

afterEach(__resetSurfaces);

describe("surface window open set persists across reload", () => {
  it("opening writes the key+scope to hs.desk.open-windows", () => {
    useSurfaceWindows.getState().openSurfaceWindow("dictate");
    useSurfaceWindows.getState().openSurfaceWindow("review-meetings", "meeting:m1");
    const raw = JSON.parse(localStorage.getItem("hs.desk.open-windows") || "{}");
    expect(raw).toEqual({ dictate: null, "review-meetings": "meeting:m1" });
  });

  it("closing drops the key from storage", () => {
    useSurfaceWindows.getState().openSurfaceWindow("dictate");
    useSurfaceWindows.getState().closeSurfaceWindow("dictate");
    const raw = JSON.parse(localStorage.getItem("hs.desk.open-windows") || "{}");
    expect(raw).toEqual({});
  });

  it("a fresh module load rehydrates the same windows (the reload case)", async () => {
    localStorage.setItem(
      "hs.desk.open-windows",
      JSON.stringify({ dictate: null, "review-meetings": "meeting:m1" }),
    );
    vi.resetModules();
    const fresh = await import("../components/SurfaceWindows");
    expect(fresh.useSurfaceWindows.getState().open).toEqual({
      dictate: null,
      "review-meetings": "meeting:m1",
    });
  });

  it("a corrupt/missing slot starts with nothing open", async () => {
    localStorage.setItem("hs.desk.open-windows", "not json");
    vi.resetModules();
    const fresh = await import("../components/SurfaceWindows");
    expect(fresh.useSurfaceWindows.getState().open).toEqual({});
  });

  it("publishes normal registry completion only after a staged Meetings open can land", async () => {
    stageSurfaceOpen("review-meetings");
    const { container } = render(<SurfaceWindows />);

    await waitFor(() => {
      expect(
        container.querySelector("[data-surface-registry-state]"),
      ).toHaveAttribute("data-surface-registry-state", "registered");
      expect(useSurfaceWindows.getState().open).toEqual({
        "review-meetings": null,
      });
    });
  });

  it("arrival clears stale windows and registers only explicit Setup recovery", async () => {
    useSurfaceWindows.setState({ open: { "configure-settings": null } });
    const { container } = render(<SurfaceWindows firstValueRecoveryOnly />);

    expect(
      container.querySelector("[data-surface-registry-state]"),
    ).toHaveAttribute("data-surface-registry-state", "recovery-only");
    await waitFor(() =>
      expect(useSurfaceWindows.getState().open).toEqual({}),
    );
    expect(
      JSON.parse(localStorage.getItem("hs.desk.open-windows") || "null"),
    ).toEqual({});
    expect(openSurface("configure-settings")).toBe(false);

    act(() => {
      expect(openSurface("configure-setup")).toBe(true);
    });
    expect(useSurfaceWindows.getState().open).toEqual({
      "configure-setup": null,
    });
  });
});
