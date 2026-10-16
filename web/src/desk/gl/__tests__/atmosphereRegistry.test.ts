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
    // PHILO-16 (A1) §2: the backdrop (Quiet Desk) is the default.
    expect(DEFAULT_ATMOSPHERE_ID).toBe("quiet-desk");
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
          id: "jupiter-orbit",
          name: "In Jupiter's orbit",
          seed: 0x4a555049,
          previewUrl: expect.stringContaining("desk/atmospheres/jupiter-orbit.webp"),
          load: expect.any(Function),
        }),
        expect.objectContaining({
          id: "mars-orbit",
          name: "In Mars' orbit",
          seed: 0x4d415253,
          gradeClassName: "desk-atmosphere-grade--mars-orbit",
          previewUrl: expect.stringContaining("desk/atmospheres/mars-orbit.webp"),
          load: expect.any(Function),
        }),
        expect.objectContaining({
          id: "saturn-orbit",
          name: "In Saturn's orbit",
          seed: 0x53415455,
          gradeClassName: "desk-atmosphere-grade--saturn-orbit",
          previewUrl: expect.stringContaining("desk/atmospheres/saturn-orbit.webp"),
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
      "jupiter-orbit",
      "mars-orbit",
      "saturn-orbit",
      "quiet-desk",
    ]);
    expect(isAtmosphereId("lantern-garden")).toBe(true);
    expect(isAtmosphereId("jupiter-orbit")).toBe(true);
    expect(isAtmosphereId("mars-orbit")).toBe(true);
    expect(isAtmosphereId("saturn-orbit")).toBe(true);
    expect(isAtmosphereId("quiet-desk")).toBe(true);
    expect(isAtmosphereId("unknown")).toBe(false);
    expect(resolveAtmosphere("unknown").id).toBe(DEFAULT_ATMOSPHERE_ID);
  });

  it("includes every authored world in one scenic collection", () => {
    expect(SCENIC_ATMOSPHERES).toContainEqual(resolveAtmosphere("jupiter-orbit"));
    expect(SCENIC_ATMOSPHERES).toContainEqual(resolveAtmosphere("mars-orbit"));
    expect(SCENIC_ATMOSPHERES).toContainEqual(resolveAtmosphere("saturn-orbit"));
    expect(SCENIC_ATMOSPHERES).not.toContainEqual(resolveAtmosphere("quiet-desk"));
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
