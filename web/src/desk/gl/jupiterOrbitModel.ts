/** Physical body size ratios; orbit distances and periods remain authored. */
export const JUPITER_RADIUS = 5.85;
/** NASA/JPL volume-equivalent mean radius: https://ssd.jpl.nasa.gov/planets/phys_par.html */
export const JUPITER_MEAN_RADIUS_KM = 69911;
export const JUPITER_ENCOUNTER_WINDOW_SECONDS = 600;

/** Bounded authored flow: neighbouring jets oppose, without hours of growing shear. */
export const JUPITER_CLOUD_FLOW = {
  jetAmplitude: 0.026,
  jetRate: 0.0028,
  eddyLongitude: 0.0018,
  eddyLatitude: 0.00055,
  eddyRate: 0.014,
  stormRate: 0.010,
} as const;
export const JUPITER_SKY_STAR_COUNT = 18_000;

export function jupiterZonalDisplacement(latitude: number, elapsed: number): number {
  const jets = Math.sin(latitude * 22) * 0.8 + Math.sin(latitude * 51) * 0.2;
  const poles = Math.max(0, 1 - Math.pow(Math.abs(latitude), 6));
  return jets * poles * JUPITER_CLOUD_FLOW.jetAmplitude
    * Math.sin(Math.max(0, elapsed) * JUPITER_CLOUD_FLOW.jetRate);
}

/** Moon mean radii: https://ssd.jpl.nasa.gov/sats/phys_par/ */
export const JUPITER_MOONS = [
  { name: "Io", physicalRadiusKm: 1821.49, radius: JUPITER_RADIUS * 1821.49 / JUPITER_MEAN_RADIUS_KM, orbit: 7.7, period: 160, phase: 2.42 },
  { name: "Europa", physicalRadiusKm: 1560.80, radius: JUPITER_RADIUS * 1560.80 / JUPITER_MEAN_RADIUS_KM, orbit: 9.1, period: 240, phase: 4.41 },
  { name: "Ganymede", physicalRadiusKm: 2631.20, radius: JUPITER_RADIUS * 2631.20 / JUPITER_MEAN_RADIUS_KM, orbit: 10.6, period: 360, phase: 4.83 },
  { name: "Callisto", physicalRadiusKm: 2410.30, radius: JUPITER_RADIUS * 2410.30 / JUPITER_MEAN_RADIUS_KM, orbit: 12.1, period: 480, phase: 4.57 },
] as const;

export type JupiterEncounterKind = "pioneer" | "voyager" | "monolith";

export interface JupiterEncounter {
  kind: JupiterEncounterKind;
  start: number;
  duration: number;
  height: number;
  direction: 1 | -1;
}

/** Independent integer hash: scheduling never consumes a per-frame RNG. */
function hashUnit(seed: number, salt: number, index: number, stream: number): number {
  let value = (seed ^ salt ^ Math.imul(index, 0x9e3779b1) ^ stream) >>> 0;
  value = Math.imul(value ^ (value >>> 16), 0x21f0aaad);
  value = Math.imul(value ^ (value >>> 15), 0x735a2d97);
  return ((value ^ (value >>> 15)) >>> 0) / 0x100000000;
}

export function makeJupiterRandom(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 0x100000000;
  };
}

export function jupiterMoonPosition(
  index: number,
  elapsed: number,
  target: [number, number, number] = [0, 0, 0],
): [number, number, number] {
  const moon = JUPITER_MOONS[index];
  if (!moon) throw new RangeError("Unknown Jupiter moon");
  const phase = moon.phase + (Math.max(elapsed, 0) / moon.period) * Math.PI * 2;
  target[0] = Math.cos(phase) * moon.orbit;
  target[1] = Math.sin(phase) * (0.62 + index * 0.11) + index * 0.13;
  target[2] = Math.sin(phase) * moon.orbit;
  return target;
}

/** One draw per eligible ten-minute window: 2%, 1%, 0.2%, then silence. */
export function jupiterEncounterForWindow(
  seed: number,
  sessionSalt: number,
  windowIndex: number,
): JupiterEncounter | null {
  if (!Number.isInteger(windowIndex) || windowIndex < 1) return null;
  const choice = hashUnit(seed, sessionSalt, windowIndex, 0x4a757069);
  const kind = choice < 0.02 ? "pioneer"
    : choice < 0.03 ? "voyager"
      : choice < 0.032 ? "monolith" : null;
  if (!kind) return null;
  const duration = 45 + hashUnit(seed, sessionSalt, windowIndex, 0x64757261) * 30;
  const offset = hashUnit(seed, sessionSalt, windowIndex, 0x73746172)
    * (JUPITER_ENCOUNTER_WINDOW_SECONDS - duration);
  return {
    kind,
    start: windowIndex * JUPITER_ENCOUNTER_WINDOW_SECONDS + offset,
    duration,
    height: 1.6 + hashUnit(seed, sessionSalt, windowIndex, 0x68656967) * 2.3,
    direction: hashUnit(seed, sessionSalt, windowIndex, 0x64697265) < 0.5 ? -1 : 1,
  };
}

/** Accepts runtime elapsed seconds, which exclude hidden and paused time. */
export function jupiterEncounterAtTime(seed: number, sessionSalt: number, elapsed: number):
  (JupiterEncounter & { progress: number; glint: number }) | null {
  if (!Number.isFinite(elapsed) || elapsed < JUPITER_ENCOUNTER_WINDOW_SECONDS) return null;
  const encounter = jupiterEncounterForWindow(
    seed, sessionSalt, Math.floor(elapsed / JUPITER_ENCOUNTER_WINDOW_SECONDS),
  );
  return jupiterEncounterState(encounter, elapsed);
}

export function jupiterEncounterState(encounter: JupiterEncounter | null, elapsed: number):
  (JupiterEncounter & { progress: number; glint: number }) | null {
  if (!encounter) return null;
  const progress = (elapsed - encounter.start) / encounter.duration;
  if (progress < 0 || progress > 1) return null;
  // A tiny reflected point on the craft, lasting about one second.
  const glint = jupiterEncounterGlint(progress);
  return { ...encounter, progress, glint };
}

export function jupiterEncounterGlint(progress: number): number {
  return Math.pow(Math.max(0, 1 - Math.abs(progress - 0.48) / 0.012), 2);
}

export function jupiterRenderSize(width: number, height: number, dpr: number) {
  const safeWidth = Math.max(1, width);
  const safeHeight = Math.max(1, height);
  const scale = Math.min(1, 1600 / safeWidth, 1000 / safeHeight);
  return {
    width: Math.max(1, Math.round(safeWidth * scale)),
    height: Math.max(1, Math.round(safeHeight * scale)),
    dpr: Math.min(Math.max(dpr || 1, 1), 1.5),
  };
}
