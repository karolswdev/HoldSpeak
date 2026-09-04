import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { ATMOSPHERE_STORAGE_KEY } from "../../../desk/gl/atmospherePreference";
import { WallpaperModule } from "../settingsWallpaper";

beforeEach(() => localStorage.clear());

describe("Settings wallpaper picker", () => {
  it("shows catalog previews and persists the live selection", async () => {
    const user = userEvent.setup();
    render(<WallpaperModule />);

    const rainy = screen.getByRole("radio", { name: /Rainy City/ });
    const garden = screen.getByRole("radio", { name: /Lantern Garden/ });
    const quiet = screen.getByRole("radio", { name: /Quiet Desk/ });
    expect(rainy).toBeChecked();
    expect(garden).not.toBeChecked();
    expect(quiet).not.toBeChecked();
    expect(rainy.querySelector("img")).toHaveAttribute(
      "src",
      expect.stringContaining("rainy-city.png"),
    );
    expect(garden.querySelector("img")).toHaveAttribute(
      "src",
      expect.stringContaining("lantern-garden.png"),
    );

    await user.click(garden);

    expect(garden).toBeChecked();
    expect(rainy).not.toBeChecked();
    expect(localStorage.getItem(ATMOSPHERE_STORAGE_KEY)).toBe("lantern-garden");
  });
});
