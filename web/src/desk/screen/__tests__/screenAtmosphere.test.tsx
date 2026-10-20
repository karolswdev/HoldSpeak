import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../../api";
import { useDesk } from "../../store";
import { WallpaperModule } from "../../../pages/cores/settingsWallpaper";

const { load, factory, release, mountAtmosphereScene, activityDispose, compact } = vi.hoisted(() => ({
  load: vi.fn(),
  factory: vi.fn(),
  release: vi.fn(),
  mountAtmosphereScene: vi.fn(),
  activityDispose: vi.fn(),
  compact: { value: false },
}));

vi.mock("../../gl/atmosphereRegistry", async (original) => {
  const registry = await original<typeof import("../../gl/atmosphereRegistry")>();
  return {
    ...registry,
    resolveAtmosphere: (id: string) => {
      const definition = registry.resolveAtmosphere(id);
      return definition.load ? { ...definition, load: () => load(definition.id) } : definition;
    },
  };
});
vi.mock("../../gl/atmosphereRuntime", () => ({ mountAtmosphereScene }));
vi.mock("../../gl/atmosphereActivity", () => ({
  observeAtmosphereActivity: () => ({
    read: () => ({ recording: false, speaking: false, level: 0, arrival: 0 }),
    subscribe: () => () => undefined,
    dispose: activityDispose,
  }),
}));
vi.mock("../../useCompactViewport", () => ({ useCompactViewport: () => compact.value }));
vi.mock("../../components/MicButton", () => ({ MicButton: () => null }));
vi.mock("../../needsYou", () => ({
  projectOpenHere: () => ({}),
  useNeedsYou: () => ({ unmutedItems: [], failedMeetings: [], count: 0 }),
}));
vi.mock("../members", () => ({
  useScreenMembers: () => ({ filed: new Set(), persons: [], loaded: true }),
  retryPeople: vi.fn(),
  retryProject: vi.fn(),
}));
vi.mock("../nextOneOnOne", () => ({ useNextOneOnOneRead: () => ({ reading: false }) }));

import { Screen } from "../Screen";

beforeEach(() => {
  localStorage.clear();
  window.dispatchEvent(new Event("storage"));
  compact.value = false;
  load.mockReset().mockResolvedValue(factory);
  factory.mockReset();
  release.mockReset();
  mountAtmosphereScene.mockReset().mockReturnValue(release);
  activityDispose.mockReset();
  // Preserve the overloaded canvas contract: this measurement stub only
  // answers 2D requests. The scene runtime is mocked separately above.
  vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockImplementation(
    ((contextId: string) => contextId === "2d"
      ? { measureText: () => ({ width: 7 }) }
      : null) as HTMLCanvasElement["getContext"],
  );
  useDesk.setState({ items: { ...EMPTY_ITEMS }, projects: [], selectedIds: [], updatedAt: 1 });
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("the current Screen's live atmosphere", () => {
  it.each([false, true])("loads only the selected scene behind the %s compact Screen and clears its still after first render", async (isCompact) => {
    compact.value = isCompact;
    let finish!: (value: typeof factory) => void;
    load.mockImplementationOnce(() => new Promise((resolve) => { finish = resolve; }));
    localStorage.setItem("hs.desk.atmosphere", "night-train");
    const audio = vi.fn();
    vi.stubGlobal("AudioContext", audio);
    const view = render(<Screen />);
    const desk = screen.getByTestId("desk-screen");
    const canvas = desk.querySelector("canvas");

    expect(desk).toHaveAttribute("data-place", "night-train");
    expect(desk).toHaveAttribute("data-place-still");
    expect(desk.style.getPropertyValue("--desk-place-still")).toContain("night-train.webp");
    expect(canvas).toBeInstanceOf(HTMLCanvasElement);
    expect(desk.querySelectorAll("canvas")).toHaveLength(1);
    expect(load.mock.calls).toEqual([["night-train"]]);
    expect(mountAtmosphereScene).not.toHaveBeenCalled();
    expect(desk.firstElementChild).toHaveClass("desk-stage");

    await act(async () => finish(factory));

    await waitFor(() => expect(canvas).toHaveAttribute("data-ready", "true"));
    expect(desk).not.toHaveAttribute("data-place-still");
    expect(desk.style.getPropertyValue("--desk-place-still")).toBe("");
    expect(audio).not.toHaveBeenCalled();
    view.unmount();
    expect(release).toHaveBeenCalledOnce();
  });

  it("allocates no host or renderer for Quiet desk and releases a live selection when Quiet wins", async () => {
    const view = render(<><Screen /><WallpaperModule /></>);
    const desk = screen.getByTestId("desk-screen");
    expect(desk).toHaveAttribute("data-place", "quiet-desk");
    expect(desk).not.toHaveAttribute("data-place-still");
    expect(desk.querySelector(".desk-stage, canvas")).toBeNull();
    expect(load).not.toHaveBeenCalled();
    expect(mountAtmosphereScene).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("radio", { name: /After-hours radio/ }));
    await waitFor(() => expect(mountAtmosphereScene).toHaveBeenCalledOnce());
    fireEvent.click(screen.getByRole("radio", { name: /Quiet desk/ }));
    expect(desk.querySelector(".desk-stage, canvas")).toBeNull();
    expect(desk).not.toHaveAttribute("data-place-still");
    expect(release).toHaveBeenCalledOnce();
    expect(activityDispose).toHaveBeenCalledOnce();
    view.unmount();
  });

  it.each(["import", "WebGL"])("keeps the selected still when %s fails", async (failure) => {
    localStorage.setItem("hs.desk.atmosphere", "rainy-city");
    if (failure === "import") load.mockRejectedValueOnce(new Error("Scene import failed"));
    else mountAtmosphereScene.mockImplementationOnce(() => { throw new Error("WebGL unavailable"); });
    render(<Screen />);
    const desk = screen.getByTestId("desk-screen");

    await waitFor(() => expect(desk.querySelector(".desk-stage")).toHaveAttribute("data-atmosphere-state", "failed"));
    expect(desk).toHaveAttribute("data-place-still");
    expect(desk.style.getPropertyValue("--desk-place-still")).toContain("rainy-city.webp");
    expect(activityDispose).toHaveBeenCalledOnce();
  });

  it("restores the next place's still and ignores the old import after a quick selection change", async () => {
    let finishOld!: (value: typeof factory) => void;
    let finishNext!: (value: typeof factory) => void;
    load.mockImplementationOnce(() => new Promise((resolve) => { finishOld = resolve; }));
    load.mockImplementationOnce(() => new Promise((resolve) => { finishNext = resolve; }));
    localStorage.setItem("hs.desk.atmosphere", "radio-station");
    render(<><Screen /><WallpaperModule /></>);
    const desk = screen.getByTestId("desk-screen");
    const oldCanvas = desk.querySelector("canvas");
    fireEvent.click(screen.getByRole("radio", { name: /Night train/ }));

    expect(desk).toHaveAttribute("data-place-still");
    expect(desk.style.getPropertyValue("--desk-place-still")).toContain("night-train.webp");
    expect(desk.querySelector("canvas")).not.toBe(oldCanvas);
    await act(async () => finishOld(factory));
    expect(mountAtmosphereScene).not.toHaveBeenCalled();
    expect(desk).toHaveAttribute("data-place-still");
    await act(async () => finishNext(factory));
    expect(mountAtmosphereScene).toHaveBeenCalledOnce();
    expect(desk).not.toHaveAttribute("data-place-still");
  });

  it("restores the still during a motion preference remount and retains object selection and clear", async () => {
    localStorage.setItem("hs.desk.atmosphere", "night-train");
    useDesk.setState({ items: { ...EMPTY_ITEMS, note: [{ kind: "note", id: "n1", title: "Architecture notes" }] } as never });
    render(<><Screen /><WallpaperModule /></>);
    const desk = screen.getByTestId("desk-screen");
    await waitFor(() => expect(desk).not.toHaveAttribute("data-place-still"));
    const note = screen.getByRole("button", { name: /^Architecture notes/ });
    fireEvent.click(note);
    expect(useDesk.getState().selectedIds).toEqual(["note:n1"]);

    let finish!: (value: typeof factory) => void;
    load.mockImplementationOnce(() => new Promise((resolve) => { finish = resolve; }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Wallpaper motion" }));
    expect(desk).toHaveAttribute("data-place-still");
    expect(note).toHaveAttribute("aria-pressed", "true");
    if (!("PointerEvent" in window)) vi.stubGlobal("PointerEvent", MouseEvent);
    fireEvent.pointerDown(screen.getByRole("group", { name: "Desk" }), { button: 0 });
    expect(useDesk.getState().selectedIds).toEqual([]);

    await act(async () => finish(factory));
    expect(mountAtmosphereScene).toHaveBeenLastCalledWith(expect.any(HTMLCanvasElement), factory, expect.objectContaining({ motion: false }));
    expect(desk).not.toHaveAttribute("data-place-still");
  });
});
