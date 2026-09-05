import { render, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const { cleanup, factory, load, mountAtmosphereScene } = vi.hoisted(() => {
  const cleanup = vi.fn();
  const factory = vi.fn();
  return {
    cleanup,
    factory,
    load: vi.fn(async () => factory),
    mountAtmosphereScene: vi.fn(() => cleanup),
  };
});

vi.mock("../atmosphereRegistry", () => ({
  DEFAULT_ATMOSPHERE_ID: "rainy-city",
  resolveAtmosphere: (id = "rainy-city") =>
    id === "quiet-desk"
      ? {
          id: "quiet-desk",
          name: "Quiet Desk",
          description: "No scene.",
          seed: 0,
          gradeClassName: "desk-atmosphere-grade--quiet-desk",
          previewUrl: null,
          load: null,
        }
      : {
          id,
          name: "Rainy City",
          description: "A test storm.",
          seed: 72,
          gradeClassName: "desk-atmosphere-grade--rainy-city",
          previewUrl: "/rainy-city.png",
          load,
        },
}));
vi.mock("../atmosphereRuntime", () => ({ mountAtmosphereScene }));

import { Atmosphere } from "../Atmosphere";

afterEach(() => {
  cleanup.mockClear();
  factory.mockClear();
  load.mockClear();
  mountAtmosphereScene.mockClear();
});

describe("Desk atmosphere host", () => {
  it("loads one registered decorative scene and releases its runtime", async () => {
    const view = render(<Atmosphere />);
    const stage = view.container.querySelector(".desk-stage");
    const canvas = view.container.querySelector(
      "canvas.desk-atmosphere-canvas",
    );

    expect(stage).toHaveAttribute("aria-hidden", "true");
    expect(stage).toHaveAttribute("data-atmosphere", "rainy-city");
    expect(canvas).toBeInstanceOf(HTMLCanvasElement);
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

    view.unmount();
    expect(cleanup).toHaveBeenCalledOnce();
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
});
