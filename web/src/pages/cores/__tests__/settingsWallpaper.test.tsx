import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { ATMOSPHERE_STORAGE_KEY } from "../../../desk/gl/atmospherePreference";
import { ATMOSPHERE_MOTION_KEY, ATMOSPHERE_SOUND_KEY } from "../../../desk/gl/atmosphereControls";
import { WallpaperModule } from "../settingsWallpaper";

beforeEach(() => {
  localStorage.clear();
  window.dispatchEvent(new Event("storage"));
});

describe("Settings wallpaper picker", () => {
  it("shows catalog previews and persists the live selection", async () => {
    const user = userEvent.setup();
    render(<WallpaperModule />);

    const rainy = screen.getByRole("radio", { name: /Rainy city/ });
    const garden = screen.getByRole("radio", { name: /Lantern garden/ });
    const quiet = screen.getByRole("radio", { name: /Quiet desk/ });
    // PHILO-16 (A1) §2: the backdrop (Quiet desk) is the default; the
    // scenes stay in the picker.
    expect(quiet).toBeChecked();
    expect(rainy).not.toBeChecked();
    expect(garden).not.toBeChecked();
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
    expect(quiet).not.toBeChecked();
    expect(localStorage.getItem(ATMOSPHERE_STORAGE_KEY)).toBe("lantern-garden");
  });

  it.each([
    { planet: "Jupiter", name: "In Jupiter's orbit", id: "jupiter-orbit" },
    { planet: "Mars", name: "In Mars' orbit", id: "mars-orbit" },
    { planet: "Saturn", name: "In Saturn's orbit", id: "saturn-orbit" },
  ])("selects $planet from the collection and restores it on reopening", async ({ name, id }) => {
    localStorage.setItem(ATMOSPHERE_STORAGE_KEY, "lantern-garden");
    localStorage.setItem(ATMOSPHERE_MOTION_KEY, "false");
    const user = userEvent.setup();
    const view = render(<WallpaperModule />);
    const planet = screen.getByRole("radio", { name: new RegExp(name) });

    expect(screen.getByRole("radio", { name: /Lantern garden/ })).toBeChecked();
    expect(planet).not.toBeChecked();
    expect(planet.querySelector("img")).toHaveAttribute(
      "src",
      expect.stringContaining(`desk/atmospheres/${id}.webp`),
    );

    await user.click(planet);

    expect(planet).toBeChecked();
    expect(localStorage.getItem(ATMOSPHERE_STORAGE_KEY)).toBe(id);
    expect(localStorage.getItem(ATMOSPHERE_MOTION_KEY)).toBe("false");
    expect(localStorage.getItem(ATMOSPHERE_SOUND_KEY)).toBeNull();
    view.unmount();
    render(<WallpaperModule />);
    expect(screen.getByRole("radio", { name: new RegExp(name) })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: "Wallpaper motion" })).not.toBeChecked();
    expect(localStorage.getItem(ATMOSPHERE_MOTION_KEY)).toBe("false");
    expect(localStorage.getItem(ATMOSPHERE_SOUND_KEY)).toBeNull();
  });

  it("lets the keyboard select the whole collection from one tab stop", async () => {
    const user = userEvent.setup();
    render(<WallpaperModule />);
    await user.tab();
    // the one tab stop is the checked default, Quiet desk (PHILO-16 A1)
    expect(screen.getByRole("radio", { name: /Quiet desk/ })).toHaveFocus();
    await user.keyboard("{Home}{ArrowRight}{ArrowRight}");
    expect(
      screen.getByRole("radio", { name: /After-hours radio/ }),
    ).toHaveFocus();
    expect(
      screen.getByRole("radio", { name: /After-hours radio/ }),
    ).toBeChecked();
    expect(localStorage.getItem(ATMOSPHERE_STORAGE_KEY)).toBe("radio-station");
    await user.keyboard("{End}");
    expect(screen.getByRole("radio", { name: /Quiet desk/ })).toHaveFocus();
    await user.keyboard("{ArrowLeft}");
    expect(screen.getByRole("radio", { name: /In Saturn's orbit/ })).toHaveFocus();
    expect(screen.getByRole("radio", { name: /In Saturn's orbit/ })).toBeChecked();
    expect(localStorage.getItem(ATMOSPHERE_STORAGE_KEY)).toBe("saturn-orbit");
    await user.keyboard("{ArrowLeft}");
    expect(screen.getByRole("radio", { name: /In Mars' orbit/ })).toHaveFocus();
    expect(screen.getByRole("radio", { name: /In Mars' orbit/ })).toBeChecked();
    expect(localStorage.getItem(ATMOSPHERE_STORAGE_KEY)).toBe("mars-orbit");
    await user.keyboard("{ArrowLeft}");
    expect(screen.getByRole("radio", { name: /In Jupiter's orbit/ })).toHaveFocus();
    expect(screen.getByRole("radio", { name: /In Jupiter's orbit/ })).toBeChecked();
    expect(localStorage.getItem(ATMOSPHERE_STORAGE_KEY)).toBe("jupiter-orbit");
    await user.keyboard("{Home}");
    expect(screen.getByRole("radio", { name: /Rainy city/ })).toHaveFocus();
    expect(screen.queryByRole("checkbox", { name: "Environment sound" })).toBeNull();
    expect(screen.queryByRole("checkbox", { name: "Environment animation" })).toBeNull();
    expect(screen.queryByText("SAVED ON THIS BROWSER · APPLIES LIVE TO THE FLOOR")).toBeNull();
  });

  it("pauses and resumes wallpaper motion with the stored control and keeps sound opt-in", async () => {
    const user = userEvent.setup();
    const view = render(<WallpaperModule />);
    const motion = screen.getByRole("checkbox", { name: "Wallpaper motion" });
    expect(motion).toBeChecked();

    await user.click(motion);
    expect(motion).not.toBeChecked();
    expect(localStorage.getItem(ATMOSPHERE_MOTION_KEY)).toBe("false");
    expect(localStorage.getItem(ATMOSPHERE_SOUND_KEY)).toBeNull();
    view.unmount();
    render(<WallpaperModule />);
    const restored = screen.getByRole("checkbox", { name: "Wallpaper motion" });
    expect(restored).not.toBeChecked();
    restored.focus();
    await user.keyboard(" ");
    expect(restored).toBeChecked();
    expect(localStorage.getItem(ATMOSPHERE_MOTION_KEY)).toBe("true");
    expect(localStorage.getItem(ATMOSPHERE_SOUND_KEY)).toBeNull();
  });

  it("reads a motion preference changed by another settings surface", () => {
    render(<WallpaperModule />);
    act(() => {
      localStorage.setItem(ATMOSPHERE_MOTION_KEY, "false");
      window.dispatchEvent(new Event("storage"));
    });
    expect(screen.getByRole("checkbox", { name: "Wallpaper motion" })).not.toBeChecked();
  });
});
