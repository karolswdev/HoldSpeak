import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import {
  ATMOSPHERE_STORAGE_KEY,
  persistAtmospherePreference,
  readAtmospherePreference,
  useAtmospherePreference,
} from "../atmospherePreference";

beforeEach(() => localStorage.clear());

describe("Desk atmosphere preference", () => {
  it("falls back safely when storage is empty or stale", () => {
    expect(readAtmospherePreference()).toBe("rainy-city");
    localStorage.setItem(ATMOSPHERE_STORAGE_KEY, "retired-scene");
    expect(readAtmospherePreference()).toBe("rainy-city");
  });

  it("persists a valid selection", () => {
    persistAtmospherePreference("quiet-desk");
    expect(localStorage.getItem(ATMOSPHERE_STORAGE_KEY)).toBe("quiet-desk");
    expect(readAtmospherePreference()).toBe("quiet-desk");
  });

  it("synchronizes the Settings picker and Floor host in the same tab", () => {
    const picker = renderHook(() => useAtmospherePreference());
    const floor = renderHook(() => useAtmospherePreference());

    act(() => picker.result.current[1]("quiet-desk"));

    expect(picker.result.current[0]).toBe("quiet-desk");
    expect(floor.result.current[0]).toBe("quiet-desk");
    expect(localStorage.getItem(ATMOSPHERE_STORAGE_KEY)).toBe("quiet-desk");
  });
});
