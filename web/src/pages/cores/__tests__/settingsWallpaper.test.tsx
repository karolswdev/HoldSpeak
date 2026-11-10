import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { ATMOSPHERE_STORAGE_KEY } from "../../../desk/gl/atmospherePreference";
import {
  ATMOSPHERE_MOTION_KEY,
  ATMOSPHERE_SOUND_KEY,
} from "../../../desk/gl/atmosphereControls";
import { WallpaperModule } from "../settings/Wallpaper";

beforeEach(() => {
  localStorage.clear();
  window.dispatchEvent(new Event("storage"));
});

describe("Settings wallpaper selection", () => {
  it("selects without applying and opens with Return; motion and sound stay unchanged", async () => {
    localStorage.setItem(ATMOSPHERE_MOTION_KEY, "false");
    const user = userEvent.setup();
    render(<WallpaperModule showFavorites />);
    const row = screen.getByText("Lantern garden").closest('[role="row"]')!;
    await user.click(row);
    expect(localStorage.getItem(ATMOSPHERE_STORAGE_KEY)).not.toBe(
      "lantern-garden",
    );
    expect(row.querySelector("button")).toBeNull();
    await user.keyboard("{Enter}");
    expect(localStorage.getItem(ATMOSPHERE_STORAGE_KEY)).toBe("lantern-garden");
    expect(localStorage.getItem(ATMOSPHERE_MOTION_KEY)).toBe("false");
    expect(localStorage.getItem(ATMOSPHERE_SOUND_KEY)).toBeNull();
    await user.click(screen.getByRole("button", { name: "Change favorite" }));
    expect(row).toHaveTextContent("Favorite");
  });
  it.each([
    ["In Jupiter's orbit", "jupiter-orbit"],
    ["In Mars' orbit", "mars-orbit"],
    ["In Saturn's orbit", "saturn-orbit"],
  ])("opens %s and restores the stored choice", async (name, id) => {
    const user = userEvent.setup();
    const view = render(<WallpaperModule />);
    await user.dblClick(screen.getByText(name));
    expect(localStorage.getItem(ATMOSPHERE_STORAGE_KEY)).toBe(id);
    view.unmount();
    render(<WallpaperModule />);
    expect(screen.getByText(name).closest('[role="row"]')).toHaveTextContent(
      "In use",
    );
  });
  it("moves selection by arrow keys without changing the wallpaper", async () => {
    const user = userEvent.setup();
    render(<WallpaperModule />);
    await user.click(screen.getByText("Rainy city"));
    await user.keyboard("{End}{Home}{ArrowDown}");
    expect(localStorage.getItem(ATMOSPHERE_STORAGE_KEY)).toBeNull();
    expect(document.activeElement?.getAttribute("role")).toBe("row");
  });
  it("persists motion and reads changes made by another surface", async () => {
    const user = userEvent.setup();
    render(<WallpaperModule />);
    const motion = screen.getByRole("checkbox", { name: "Wallpaper motion" });
    await user.click(motion);
    expect(motion).not.toBeChecked();
    expect(localStorage.getItem(ATMOSPHERE_MOTION_KEY)).toBe("false");
    act(() => {
      localStorage.setItem(ATMOSPHERE_MOTION_KEY, "true");
      window.dispatchEvent(new Event("storage"));
    });
    expect(motion).toBeChecked();
    expect(localStorage.getItem(ATMOSPHERE_SOUND_KEY)).toBeNull();
  });
});
