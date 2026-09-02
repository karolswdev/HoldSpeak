import type { AtmosphereSceneFactory } from "./atmosphereRuntime";

export interface AtmosphereDefinition {
  id: string;
  name: string;
  description: string;
  /** Stable seed keeps authored composition repeatable across reloads. */
  seed: number;
  gradeClassName: string;
  load: () => Promise<AtmosphereSceneFactory>;
}

const rainyCity: AtmosphereDefinition = {
  id: "rainy-city",
  name: "Rainy City",
  description: "A cinematic night storm above a lamplit city street.",
  seed: 0x484f4c44,
  gradeClassName: "desk-atmosphere-grade--rainy-city",
  load: () =>
    import("./rainyCityScene").then((module) => module.createRainyCityScene),
};

/** Catalog seam for the Desk personalization layer. Each entry is metadata
 * plus an isolated lazy scene factory; adding backgrounds does not grow the
 * initial Desk bundle or couple one scene's runtime to another. */
export const ATMOSPHERES = [rainyCity] as const;

export type AtmosphereId = (typeof ATMOSPHERES)[number]["id"];
export const DEFAULT_ATMOSPHERE_ID: AtmosphereId = "rainy-city";

export function resolveAtmosphere(
  id: string = DEFAULT_ATMOSPHERE_ID,
): AtmosphereDefinition {
  return ATMOSPHERES.find((atmosphere) => atmosphere.id === id) ?? rainyCity;
}
