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
  resolveAtmosphere: () => ({
    id: "rainy-city",
    name: "Rainy City",
    description: "A test storm.",
    seed: 72,
    gradeClassName: "desk-atmosphere-grade--rainy-city",
    load,
  }),
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
      expect(mountAtmosphereScene).toHaveBeenCalledWith(canvas, factory, {
        seed: 72,
      }),
    );

    view.unmount();
    expect(cleanup).toHaveBeenCalledOnce();
  });
});
