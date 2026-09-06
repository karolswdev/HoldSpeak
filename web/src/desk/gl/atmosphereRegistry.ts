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
  previewUrl: `${PUBLIC_BASE}desk/atmospheres/rainy-city.webp`,
  load: () =>
    import("./rainyCityScene").then((module) => module.createRainyCityScene),
} satisfies AtmosphereDefinition;

const lanternGarden = {
  id: "lantern-garden",
  name: "Lantern Garden",
  description: "A rain-dark flagstone path lit through a fine garden drizzle.",
  seed: 0x59415244,
  gradeClassName: "desk-atmosphere-grade--lantern-garden",
  previewUrl: `${PUBLIC_BASE}desk/atmospheres/lantern-garden.webp`,
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

const interiors = [
  {
    id: "radio-station",
    name: "After-Hours Radio",
    description: "Walnut, warm meters, and rain over a sleeping city.",
    seed: 886,
    load: () =>
      import("./interiors/radioStationScene").then(
        (module) => module.createRadioStationScene,
      ),
  },
  {
    id: "midnight-archive",
    name: "Midnight Archive",
    description: "Green reading lamps in a long hall of wooden drawers.",
    seed: 1904,
    load: () =>
      import("./interiors/midnightArchiveScene").then(
        (module) => module.createMidnightArchiveScene,
      ),
  },
  {
    id: "night-train",
    name: "Night Train",
    description: "A lamplit compartment. Forests passing in the rain.",
    seed: 213,
    load: () =>
      import("./interiors/nightTrainScene").then(
        (module) => module.createNightTrainScene,
      ),
  },
  {
    id: "deep-sea",
    name: "Deep-Sea Station",
    description: "Brass instruments, blue water, and distant silhouettes.",
    seed: 900,
    load: () =>
      import("./interiors/deepSeaScene").then(
        (module) => module.createDeepSeaScene,
      ),
  },
  {
    id: "greenhouse",
    name: "Storm Greenhouse",
    description:
      "Wet stone, terracotta, and violet light through iron rafters.",
    seed: 303,
    load: () =>
      import("./interiors/greenhouseScene").then(
        (module) => module.createGreenhouseScene,
      ),
  },
  {
    id: "laundromat",
    name: "Last Laundromat",
    description: "Slow drums and fluorescent quiet. Open all night.",
    seed: 2400,
    load: () =>
      import("./interiors/laundromatScene").then(
        (module) => module.createLaundromatScene,
      ),
  },
] as const;

const interiorAtmospheres = interiors.map((entry) => ({
  ...entry,
  gradeClassName: "desk-atmosphere-grade--interior",
  previewUrl: `${PUBLIC_BASE}desk/atmospheres/${entry.id}.webp`,
})) satisfies AtmosphereDefinition[];

/** Catalog seam for the Desk personalization layer. Each entry is metadata
 * plus an isolated lazy scene factory; adding backgrounds does not grow the
 * initial Desk bundle or couple one scene's runtime to another. */
export const ATMOSPHERES = [
  rainyCity,
  lanternGarden,
  ...interiorAtmospheres,
  quietDesk,
] as const satisfies readonly AtmosphereDefinition[];

export type AtmosphereId = (typeof ATMOSPHERES)[number]["id"];
export const DEFAULT_ATMOSPHERE_ID: AtmosphereId = "rainy-city";

/** Every authored world belongs in the collection. Quiet Desk remains a
 * Settings-only, no-WebGL choice rather than a numbered scene. */
export const SCENIC_ATMOSPHERES = ATMOSPHERES.filter(
  (atmosphere) => atmosphere.load !== null,
);

export function isAtmosphereId(id: string): id is AtmosphereId {
  return ATMOSPHERES.some((atmosphere) => atmosphere.id === id);
}

export function resolveAtmosphere(
  id: string = DEFAULT_ATMOSPHERE_ID,
): AtmosphereDefinition {
  return ATMOSPHERES.find((atmosphere) => atmosphere.id === id) ?? rainyCity;
}
