import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ChangePlacesCore } from "../ChangePlacesCore";
import {
  ATMOSPHERE_FAVORITES_KEY,
  parseAtmosphereFavorites,
} from "../../../desk/gl/atmosphereFavorites";
import { ATMOSPHERE_STORAGE_KEY } from "../../../desk/gl/atmospherePreference";
import { useSettleState } from "../../../desk/settleState";
import { useChairState } from "../../../desk/chairState";

beforeEach(() => {
  localStorage.clear();
  useSettleState.setState({ settled: false });
  useChairState.setState({ surface: "chair" });
});

describe("Change places", () => {
  it("shows eight scenes plus Quiet Desk without changing the current work surface", () => {
    render(<ChangePlacesCore />);
    expect(screen.getAllByRole("radio")).toHaveLength(9);
    fireEvent.click(screen.getByRole("radio", { name: /Night Train/ }));
    expect(localStorage.getItem(ATMOSPHERE_STORAGE_KEY)).toBe("night-train");
    expect(useChairState.getState().surface).toBe("chair");
    fireEvent.click(screen.getByRole("button", { name: "View on Floor" }));
    expect(useChairState.getState().surface).toBe("floor");
  });
  it("favorites never switch the room and the filter retains keyboard entry", () => {
    render(<ChangePlacesCore />);
    fireEvent.click(
      screen.getByRole("button", { name: "Favorite Night Train" }),
    );
    expect(localStorage.getItem(ATMOSPHERE_STORAGE_KEY)).toBeNull();
    expect(JSON.parse(localStorage.getItem(ATMOSPHERE_FAVORITES_KEY)!)).toEqual(
      ["night-train"],
    );
    fireEvent.click(screen.getByRole("button", { name: "Favorites" }));
    const radio = screen.getByRole("radio");
    expect(radio).toHaveAttribute("tabindex", "0");
    expect(radio).not.toBeChecked();
    fireEvent.keyDown(radio, { key: "ArrowRight" });
    expect(radio).toBeChecked();
    expect(radio).toHaveFocus();
  });
  it("loads favorites on reopen and synchronizes a different tab", () => {
    localStorage.setItem(ATMOSPHERE_FAVORITES_KEY, '["lantern-garden"]');
    render(<ChangePlacesCore />);
    expect(
      screen.getByRole("button", { name: "Favorite Lantern Garden" }),
    ).toHaveAttribute("aria-pressed", "true");
    act(() => {
      localStorage.setItem(ATMOSPHERE_FAVORITES_KEY, '["rainy-city"]');
      window.dispatchEvent(
        new StorageEvent("storage", { key: ATMOSPHERE_FAVORITES_KEY }),
      );
    });
    expect(
      screen.getByRole("button", { name: "Favorite Rainy City" }),
    ).toHaveAttribute("aria-pressed", "true");
    expect(
      screen.getByRole("button", { name: "Favorite Lantern Garden" }),
    ).toHaveAttribute("aria-pressed", "false");
  });
  it("retains keyboard focus when removing the last filtered favorite", () => {
    localStorage.setItem(ATMOSPHERE_FAVORITES_KEY, '["night-train"]');
    render(<ChangePlacesCore />);
    fireEvent.click(screen.getByRole("button", { name: "Favorites" }));
    const favorite = screen.getByRole("button", {
      name: "Favorite Night Train",
    });
    favorite.focus();
    fireEvent.click(favorite);
    expect(screen.getByRole("radiogroup")).toHaveFocus();
    expect(screen.getByRole("status")).toHaveTextContent("No favorite places");
    expect(screen.queryAllByRole("radio")).toHaveLength(0);
  });
  it("names an empty favorites list and still offers All places", () => {
    render(<ChangePlacesCore />);
    fireEvent.click(screen.getByRole("button", { name: "Favorites" }));
    expect(screen.getByRole("status")).toHaveTextContent("No favorite places");
    fireEvent.click(screen.getByRole("button", { name: "All places" }));
    expect(screen.getAllByRole("radio")).toHaveLength(9);
  });
  it("settles without implicitly turning on motion, sound or capture", () => {
    render(<ChangePlacesCore />);
    fireEvent.click(screen.getByRole("button", { name: "Settle in" }));
    expect(useSettleState.getState().settled).toBe(true);
    expect(localStorage.getItem("hs.desk.atmosphere.sound")).toBeNull();
  });
  it("ignores malformed, duplicate and removed favorites", () => {
    expect(parseAtmosphereFavorites("not json")).toEqual([]);
    expect(parseAtmosphereFavorites("{}")).toEqual([]);
    expect(
      parseAtmosphereFavorites('["rainy-city",null,"bad","rainy-city"]'),
    ).toEqual(["rainy-city"]);
  });
  it("keeps favorites usable when storage writes are refused", () => {
    render(<ChangePlacesCore />);
    const write = vi
      .spyOn(Storage.prototype, "setItem")
      .mockImplementation(() => {
        throw new Error("Quota exceeded");
      });
    fireEvent.click(
      screen.getByRole("button", { name: "Favorite Rainy City" }),
    );
    expect(
      screen.getByRole("button", { name: "Favorite Rainy City" }),
    ).toHaveAttribute("aria-pressed", "true");
    write.mockRestore();
    act(() => window.dispatchEvent(new StorageEvent("storage")));
  });
});
