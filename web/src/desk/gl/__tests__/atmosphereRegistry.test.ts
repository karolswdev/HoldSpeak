import { describe, expect, it } from "vitest";
import {
  ATMOSPHERES,
  DEFAULT_ATMOSPHERE_ID,
  isAtmosphereId,
  resolveAtmosphere,
} from "../atmosphereRegistry";

describe("atmosphere registry", () => {
  it("publishes lazy personalization metadata and a safe fallback", () => {
    expect(DEFAULT_ATMOSPHERE_ID).toBe("rainy-city");
    expect(ATMOSPHERES).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: "rainy-city",
          name: "Rainy City",
          seed: expect.any(Number),
          previewUrl: expect.stringContaining("rainy-city.png"),
          load: expect.any(Function),
        }),
        expect.objectContaining({
          id: "lantern-garden",
          name: "Lantern Garden",
          seed: expect.any(Number),
          previewUrl: expect.stringContaining("lantern-garden.png"),
          load: expect.any(Function),
        }),
        expect.objectContaining({
          id: "quiet-desk",
          previewUrl: null,
          load: null,
        }),
      ]),
    );
    expect(ATMOSPHERES.map(({ id }) => id)).toEqual([
      "rainy-city",
      "lantern-garden",
      "quiet-desk",
    ]);
    expect(isAtmosphereId("lantern-garden")).toBe(true);
    expect(isAtmosphereId("quiet-desk")).toBe(true);
    expect(isAtmosphereId("unknown")).toBe(false);
    expect(resolveAtmosphere("unknown").id).toBe(DEFAULT_ATMOSPHERE_ID);
  });
});
