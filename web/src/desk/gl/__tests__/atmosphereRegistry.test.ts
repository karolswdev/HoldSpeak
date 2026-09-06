import { describe, expect, it } from "vitest";
import {
  ATMOSPHERES,
  DEFAULT_ATMOSPHERE_ID,
  SCENIC_ATMOSPHERES,
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
          previewUrl: expect.stringContaining("rainy-city.webp"),
          load: expect.any(Function),
        }),
        expect.objectContaining({
          id: "lantern-garden",
          name: "Lantern Garden",
          seed: expect.any(Number),
          previewUrl: expect.stringContaining("lantern-garden.webp"),
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
      "radio-station",
      "midnight-archive",
      "night-train",
      "deep-sea",
      "greenhouse",
      "laundromat",
      "quiet-desk",
    ]);
    expect(isAtmosphereId("lantern-garden")).toBe(true);
    expect(isAtmosphereId("quiet-desk")).toBe(true);
    expect(isAtmosphereId("unknown")).toBe(false);
    expect(resolveAtmosphere("unknown").id).toBe(DEFAULT_ATMOSPHERE_ID);
  });

  it("includes both original worlds and all interiors in one scenic collection", () => {
    expect(SCENIC_ATMOSPHERES).toHaveLength(8);
    expect(SCENIC_ATMOSPHERES.map(({ id }) => id)).toEqual(
      ATMOSPHERES.filter(({ load }) => load).map(({ id }) => id),
    );
    expect(
      SCENIC_ATMOSPHERES.every(({ previewUrl }) =>
        previewUrl?.endsWith(".webp"),
      ),
    ).toBe(true);
  });
});
