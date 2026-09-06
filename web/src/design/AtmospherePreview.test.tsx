import { fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AtmospherePreview } from "./AtmospherePreview";

const select = vi.hoisted(() => vi.fn());
vi.mock("../desk/gl/Atmosphere", () => ({
  Atmosphere: ({ id }: { id: string }) => <div data-testid="scene">{id}</div>,
}));
vi.mock("../desk/gl/atmospherePreference", () => ({
  useAtmospherePreference: () => ["radio-station", select],
}));
vi.mock("../desk/gl/atmosphereControls", () => ({
  useAtmosphereControls: () => ({
    sound: false,
    motion: true,
    setSound: vi.fn(),
    setMotion: vi.fn(),
  }),
}));

beforeEach(() => {
  history.replaceState(null, "", "/");
  select.mockClear();
});

describe("the complete night collection", () => {
  it("opens with the original city and exposes all eight worlds", () => {
    render(<AtmospherePreview />);
    expect(
      screen.getByRole("heading", { name: "Rainy City" }),
    ).toBeInTheDocument();
    expect(
      within(screen.getByRole("navigation")).getAllByRole("button"),
    ).toHaveLength(8);
    expect(screen.getByText(/01\s*\/\s*08/)).toBeInTheDocument();
  });
  it("wraps through the entire collection in either direction", () => {
    render(<AtmospherePreview />);
    fireEvent.click(
      screen.getByRole("button", { name: "Previous environment" }),
    );
    expect(
      screen.getByRole("heading", { name: "Last Laundromat" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/08\s*\/\s*08/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Next environment" }));
    fireEvent.click(screen.getByRole("button", { name: "Next environment" }));
    expect(
      screen.getByRole("heading", { name: "Lantern Garden" }),
    ).toBeInTheDocument();
    expect(select).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Use on my Floor" }));
    expect(select).toHaveBeenCalledWith("lantern-garden");
  });
  it.each(["rainy-city", "lantern-garden", "radio-station"])(
    "honors a direct link to %s",
    (id) => {
      history.replaceState(null, "", `/#${id}`);
      render(<AtmospherePreview />);
      expect(screen.getByTestId("scene")).toHaveTextContent(id);
      expect(
        within(screen.getByRole("navigation")).getByRole("button", {
          pressed: true,
        }),
      ).toHaveAttribute("data-scene", id);
    },
  );
  it.each(["quiet-desk", "missing"])(
    "avoids a zero-numbered scene for #%s",
    (id) => {
      history.replaceState(null, "", `/#${id}`);
      render(<AtmospherePreview />);
      expect(screen.getByText(/01\s*\/\s*08/)).toBeInTheDocument();
      expect(screen.getByTestId("scene")).toHaveTextContent("rainy-city");
    },
  );
});
