import type { AtmosphereSceneFactory } from "./atmosphereRuntime";

export interface AtmosphereDefinition {
  id: string;
  name: string;
  description: string;
  /** Stable seed keeps authored composition repeatable across reloads. */
  seed: number;
  gradeClassName: string;
  /** Product-facing still used by the Settings picker. Null is a CSS preview. */
  previewUrl: string | null;
  /** Null deliberately selects the quiet Desk without allocating WebGL. */
  load: (() => Promise<AtmosphereSceneFactory>) | null;
}

const PUBLIC_BASE = import.meta.env.BASE_URL || "/_built/";

const rainyCity = {
  id: "rainy-city",
  name: "Rainy City",
  description: "A cinematic night storm above a lamplit city street.",
  seed: 0x484f4c44,
  gradeClassName: "desk-atmosphere-grade--rainy-city",
  previewUrl: `${PUBLIC_BASE}desk/atmospheres/rainy-city.png`,
  load: () =>
    import("./rainyCityScene").then((module) => module.createRainyCityScene),
} satisfies AtmosphereDefinition;

const lanternGarden = {
  id: "lantern-garden",
  name: "Lantern Garden",
  description: "A rain-dark flagstone path lit through a fine garden drizzle.",
  seed: 0x59415244,
  gradeClassName: "desk-atmosphere-grade--lantern-garden",
  previewUrl: `${PUBLIC_BASE}desk/atmospheres/lantern-garden.png`,
  load: () =>
    import("./lanternGardenScene").then(
      (module) => module.createLanternGardenScene,
    ),
} satisfies AtmosphereDefinition;

const quietDesk = {
  id: "quiet-desk",
  name: "Quiet Desk",
  description: "The unanimated Desk field with no atmospheric scene.",
  seed: 0,
  gradeClassName: "desk-atmosphere-grade--quiet-desk",
  previewUrl: null,
  load: null,
} satisfies AtmosphereDefinition;

/** Catalog seam for the Desk personalization layer. Each entry is metadata
 * plus an isolated lazy scene factory; adding backgrounds does not grow the
 * initial Desk bundle or couple one scene's runtime to another. */
export const ATMOSPHERES = [
  rainyCity,
  lanternGarden,
  quietDesk,
] as const satisfies readonly AtmosphereDefinition[];

export type AtmosphereId = (typeof ATMOSPHERES)[number]["id"];
export const DEFAULT_ATMOSPHERE_ID: AtmosphereId = "rainy-city";

export function isAtmosphereId(id: string): id is AtmosphereId {
  return ATMOSPHERES.some((atmosphere) => atmosphere.id === id);
}

export function resolveAtmosphere(
  id: string = DEFAULT_ATMOSPHERE_ID,
): AtmosphereDefinition {
  return ATMOSPHERES.find((atmosphere) => atmosphere.id === id) ?? rainyCity;
}
