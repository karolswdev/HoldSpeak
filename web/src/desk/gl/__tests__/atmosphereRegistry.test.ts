import { describe, expect, it } from "vitest";
import {
  ATMOSPHERES,
  DEFAULT_ATMOSPHERE_ID,
  resolveAtmosphere,
} from "../atmosphereRegistry";

describe("atmosphere registry", () => {
  it("publishes lazy personalization metadata and a safe fallback", () => {
    expect(DEFAULT_ATMOSPHERE_ID).toBe("rainy-city");
    expect(ATMOSPHERES).toEqual([
      expect.objectContaining({
        id: "rainy-city",
        name: "Rainy City",
        seed: expect.any(Number),
        load: expect.any(Function),
      }),
    ]);
    expect(resolveAtmosphere("unknown").id).toBe(DEFAULT_ATMOSPHERE_ID);
  });
});
