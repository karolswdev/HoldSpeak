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
      expect.stringContaining("rainy-city.webp"),
    );
    expect(garden.querySelector("img")).toHaveAttribute(
      "src",
      expect.stringContaining("lantern-garden.webp"),
    );

    await user.click(garden);

    expect(garden).toBeChecked();
    expect(rainy).not.toBeChecked();
    expect(localStorage.getItem(ATMOSPHERE_STORAGE_KEY)).toBe("lantern-garden");
  });

  it("lets the keyboard select the whole collection from one tab stop", async () => {
    const user = userEvent.setup();
    render(<WallpaperModule />);
    await user.tab();
    await user.keyboard("{ArrowRight}{ArrowRight}");
    expect(
      screen.getByRole("radio", { name: /After-Hours Radio/ }),
    ).toHaveFocus();
    expect(
      screen.getByRole("radio", { name: /After-Hours Radio/ }),
    ).toBeChecked();
    expect(localStorage.getItem(ATMOSPHERE_STORAGE_KEY)).toBe("radio-station");
    await user.keyboard("{End}");
    expect(screen.getByRole("radio", { name: /Quiet Desk/ })).toHaveFocus();
    await user.keyboard("{Home}");
    expect(screen.getByRole("radio", { name: /Rainy City/ })).toHaveFocus();
    expect(
      screen.getByRole("checkbox", { name: "Environment sound" }),
    ).not.toBeChecked();
  });
});
