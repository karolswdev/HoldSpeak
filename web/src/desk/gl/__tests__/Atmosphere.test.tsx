import { act, render, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const {
  cleanup, factory, jupiterFactory, jupiterModuleLoad, load,
  mountAtmosphereScene, activityDispose, observeAtmosphereActivity, controls,
} = vi.hoisted(() => {
  const cleanup = vi.fn();
  const factory = vi.fn();
  return {
    cleanup,
    factory,
    jupiterFactory: vi.fn(),
    jupiterModuleLoad: vi.fn(),
    load: vi.fn(async () => factory),
    mountAtmosphereScene: vi.fn(() => cleanup),
    activityDispose: vi.fn(),
    observeAtmosphereActivity: vi.fn(),
    controls: { motion: true },
  };
});

vi.mock("../atmosphereRegistry", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../atmosphereRegistry")>();
  return {
    ...actual,
    DEFAULT_ATMOSPHERE_ID: "rainy-city",
    resolveAtmosphere: (id = "rainy-city") =>
      id === "jupiter-orbit" || id === "quiet-desk"
        ? actual.resolveAtmosphere(id)
        : {
            id,
            name: "Rainy City",
            description: "A test storm.",
            seed: 72,
            gradeClassName: "desk-atmosphere-grade--rainy-city",
            previewUrl: "/rainy-city.png",
            load,
          },
  };
});
vi.mock("../jupiterOrbitScene", () => {
  jupiterModuleLoad();
  return { createJupiterOrbitScene: jupiterFactory };
});
vi.mock("../atmosphereRuntime", () => ({ mountAtmosphereScene }));
vi.mock("../atmosphereActivity", () => ({ observeAtmosphereActivity }));
vi.mock("../atmosphereControls", () => ({ useAtmosphereControls: () => controls }));
vi.mock("../atmosphereSound", () => ({ useAtmosphereSound: vi.fn() }));

import { Atmosphere } from "../Atmosphere";

beforeEach(() => {
  controls.motion = true;
  cleanup.mockReset();
  factory.mockReset();
  jupiterFactory.mockReset();
  jupiterModuleLoad.mockClear();
  load.mockReset().mockResolvedValue(factory);
  mountAtmosphereScene.mockReset().mockReturnValue(cleanup);
  activityDispose.mockReset();
  observeAtmosphereActivity.mockReset().mockImplementation(() => ({
    read: () => ({ recording: false, speaking: false, level: 0, arrival: 0 }),
    subscribe: () => () => undefined,
    dispose: activityDispose,
  }));
});

describe("Desk atmosphere host", () => {
  it("loads one registered decorative scene and releases its runtime", async () => {
    const onReadyChange = vi.fn();
    const view = render(<Atmosphere onReadyChange={onReadyChange} />);
    const stage = view.container.querySelector(".desk-stage");
    const canvas = view.container.querySelector(
      "canvas.desk-atmosphere-canvas",
    );

    expect(stage).toHaveAttribute("aria-hidden", "true");
    expect(stage).toHaveAttribute("data-atmosphere", "rainy-city");
    expect(canvas).toBeInstanceOf(HTMLCanvasElement);
    expect(stage).toHaveAttribute("data-atmosphere-state", "loading");
    expect(onReadyChange).toHaveBeenLastCalledWith(false);
    expect(view.container.querySelector(".desk-atmosphere-grade")).toHaveClass(
      "desk-atmosphere-grade--rainy-city",
    );
    await waitFor(() =>
      expect(mountAtmosphereScene).toHaveBeenCalledWith(
        canvas,
        factory,
        expect.objectContaining({
          seed: 72,
        }),
      ),
    );
    expect(stage).toHaveAttribute("data-atmosphere-state", "ready");
    expect(canvas).toHaveAttribute("data-ready", "true");
    expect(onReadyChange).toHaveBeenLastCalledWith(true);

    view.unmount();
    expect(cleanup).toHaveBeenCalledOnce();
    expect(activityDispose).toHaveBeenCalledOnce();
  });

  it("selects the quiet Desk without allocating a WebGL canvas", () => {
    const view = render(<Atmosphere id="quiet-desk" />);
    expect(view.container.querySelector(".desk-stage")).toHaveAttribute(
      "data-atmosphere",
      "quiet-desk",
    );
    expect(view.container.querySelector("canvas")).toBeNull();
    expect(load).not.toHaveBeenCalled();
    expect(mountAtmosphereScene).not.toHaveBeenCalled();
    expect(observeAtmosphereActivity).not.toHaveBeenCalled();
  });

  it("loads Jupiter through its real registry entry only when selected", async () => {
    controls.motion = false;
    const view = render(<Atmosphere id="quiet-desk" />);
    expect(jupiterModuleLoad).not.toHaveBeenCalled();

    view.rerender(<Atmosphere id="jupiter-orbit" />);
    const canvas = view.container.querySelector("canvas");
    await waitFor(() =>
      expect(mountAtmosphereScene).toHaveBeenCalledWith(
        canvas,
        jupiterFactory,
        expect.objectContaining({ seed: 0x4a555049, motion: false }),
      ),
    );
    expect(jupiterModuleLoad).toHaveBeenCalledOnce();
    expect(load).not.toHaveBeenCalled();
    expect(view.container.querySelector(".desk-stage")).toHaveAttribute(
      "data-atmosphere",
      "jupiter-orbit",
    );
    expect(canvas).toHaveAttribute("data-ready", "true");

    view.unmount();
    expect(cleanup).toHaveBeenCalledOnce();
    expect(activityDispose).toHaveBeenCalledOnce();
  });

  it("releases the active scene when a live selection disables it", async () => {
    const view = render(<Atmosphere id="rainy-city" />);
    await waitFor(() => expect(mountAtmosphereScene).toHaveBeenCalledOnce());

    view.rerender(<Atmosphere id="quiet-desk" />);

    expect(view.container.querySelector("canvas")).toBeNull();
    expect(cleanup).toHaveBeenCalledOnce();
  });

  it("gives the next renderer a new canvas after disposal loses the old context", async () => {
    const view = render(<Atmosphere id="radio-station" />);
    await waitFor(() => expect(mountAtmosphereScene).toHaveBeenCalledOnce());
    const firstCanvas = view.container.querySelector("canvas");
    view.rerender(<Atmosphere id="night-train" />);
    await waitFor(() => expect(mountAtmosphereScene).toHaveBeenCalledTimes(2));
    expect(view.container.querySelector("canvas")).not.toBe(firstCanvas);
    expect(cleanup).toHaveBeenCalledOnce();
  });

  it.each(["load", "mount"])("keeps a failed %s unready and releases activity immediately", async (failure) => {
    if (failure === "load") load.mockRejectedValueOnce(new Error("Scene import failed"));
    else mountAtmosphereScene.mockImplementationOnce(() => { throw new Error("WebGL unavailable"); });
    const onReadyChange = vi.fn();
    const view = render(<Atmosphere id="night-train" onReadyChange={onReadyChange} />);

    await waitFor(() => expect(view.container.querySelector(".desk-stage")).toHaveAttribute("data-atmosphere-state", "failed"));
    expect(view.container.querySelector("canvas")).not.toHaveAttribute("data-ready");
    expect(onReadyChange).not.toHaveBeenCalledWith(true);
    expect(activityDispose).toHaveBeenCalledOnce();
    expect(cleanup).not.toHaveBeenCalled();
    view.unmount();
    expect(activityDispose).toHaveBeenCalledOnce();
  });

  it("cancels a pending scene when a new place wins and ignores its late completion", async () => {
    let finishFirst!: (value: typeof factory) => void;
    load.mockImplementationOnce(() => new Promise((resolve) => { finishFirst = resolve; }));
    const onReadyChange = vi.fn();
    const view = render(<Atmosphere id="radio-station" onReadyChange={onReadyChange} />);
    view.rerender(<Atmosphere id="night-train" onReadyChange={onReadyChange} />);
    await waitFor(() => expect(mountAtmosphereScene).toHaveBeenCalledOnce());
    expect(activityDispose).toHaveBeenCalledOnce();
    const calls = onReadyChange.mock.calls.length;

    await act(async () => finishFirst(factory));

    expect(mountAtmosphereScene).toHaveBeenCalledOnce();
    expect(onReadyChange).toHaveBeenCalledTimes(calls);
    expect(view.container.querySelector(".desk-stage")).toHaveAttribute("data-atmosphere", "night-train");
    view.unmount();
    expect(activityDispose).toHaveBeenCalledTimes(2);
    expect(cleanup).toHaveBeenCalledOnce();
  });

  it("cancels a pending import on unmount without mounting or announcing readiness", async () => {
    let finish!: (value: typeof factory) => void;
    load.mockImplementationOnce(() => new Promise((resolve) => { finish = resolve; }));
    const onReadyChange = vi.fn();
    const view = render(<Atmosphere onReadyChange={onReadyChange} />);
    view.unmount();
    await act(async () => finish(factory));

    expect(mountAtmosphereScene).not.toHaveBeenCalled();
    expect(onReadyChange).not.toHaveBeenCalledWith(true);
    expect(activityDispose).toHaveBeenCalledOnce();
  });

  it("remounts with the explicit motion choice and reports loading again", async () => {
    const onReadyChange = vi.fn();
    const view = render(<Atmosphere id="night-train" onReadyChange={onReadyChange} />);
    await waitFor(() => expect(mountAtmosphereScene).toHaveBeenCalledOnce());
    const firstCanvas = view.container.querySelector("canvas");
    controls.motion = false;
    view.rerender(<Atmosphere id="night-train" onReadyChange={onReadyChange} />);

    expect(view.container.querySelector(".desk-stage")).toHaveAttribute("data-atmosphere-state", "loading");
    expect(onReadyChange).toHaveBeenLastCalledWith(false);
    expect(view.container.querySelector("canvas")).not.toBe(firstCanvas);
    await waitFor(() => expect(mountAtmosphereScene).toHaveBeenCalledTimes(2));
    expect(mountAtmosphereScene).toHaveBeenLastCalledWith(expect.any(HTMLCanvasElement), factory, expect.objectContaining({ motion: false }));
    expect(cleanup).toHaveBeenCalledOnce();
  });
});
