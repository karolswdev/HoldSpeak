import { render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const { cleanup, mountRainyCityScene } = vi.hoisted(() => {
  const cleanup = vi.fn();
  return { cleanup, mountRainyCityScene: vi.fn(() => cleanup) };
});

vi.mock("../rainyCityScene", () => ({ mountRainyCityScene }));

import { Atmosphere } from "../Atmosphere";

afterEach(() => {
  cleanup.mockClear();
  mountRainyCityScene.mockClear();
});

describe("rainy city atmosphere", () => {
  it("mounts one decorative Three.js canvas and releases it with the Floor", () => {
    const view = render(<Atmosphere />);
    const stage = view.container.querySelector(".desk-stage");
    const canvas = view.container.querySelector("canvas.desk-rain-city");

    expect(stage).toHaveAttribute("aria-hidden", "true");
    expect(canvas).toBeInstanceOf(HTMLCanvasElement);
    expect(mountRainyCityScene).toHaveBeenCalledWith(canvas);

    view.unmount();
    expect(cleanup).toHaveBeenCalledOnce();
  });
});
