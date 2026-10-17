/** Authored continuous travel, in scene metres and seconds; no geographic claim. */
export const TRAIN_TERRAIN_SPAN = 600;
export const TRAIN_TERRAIN_SPEEDS = [0.095, 0.17, 0.30, 1.08] as const;
export const TRAIN_TREE_LAYERS = [
  { name: "distant woods", count: 84, depth: 57, spread: 500, speed: TRAIN_TERRAIN_SPEEDS[2], height: 3.1 },
  { name: "shore woods", count: 96, depth: 47, spread: 360, speed: TRAIN_TERRAIN_SPEEDS[2], height: 2.8 },
  { name: "near vegetation", count: 28, depth: 9, spread: 240, speed: TRAIN_TERRAIN_SPEEDS[3], height: 2.5 },
] as const;

/** Recycling occurs far beyond the window; all visible travel is continuous. */
export function trainTravelPosition(initial: number, elapsed: number, speed: number, span: number): number {
  const distance = Math.max(0, elapsed) * speed;
  return ((initial - distance + span / 2) % span + span) % span - span / 2;
}

/** Periodic ridges join beyond the camera's visible world, with a long journey. */
export function trainRidgeHeight(x: number, layer: number, phase: number): number {
  const p = x / TRAIN_TERRAIN_SPAN * Math.PI * 2;
  const broad = Math.sin(p * (3 + layer) + phase) * 0.53
    + Math.sin(p * (7 + layer * 2) - phase * 0.7) * 0.29
    + Math.sin(p * (19 + layer * 3) + phase * 1.8) * 0.12
    + Math.sin(p * (43 + layer * 7) - phase) * 0.06;
  return [13.5, 7.2, 1.1, 0.10][layer] + broad * [7.3, 4.3, 1.6, 0.75][layer];
}

export function trainStationPosition(elapsed: number): number {
  return trainTravelPosition(180, elapsed, 1.08, 600);
}

/** Full x/z relief: ridges bend into valleys instead of forming vertical strips. */
export function trainTerrainHeight(x: number, z: number, layer: number, phase: number): number {
  const p = x / TRAIN_TERRAIN_SPAN * Math.PI * 2;
  const spine = Math.sin(p * 9 + phase) * 3.6 + Math.sin(p * 23 - phase) * 1.5;
  const cross = (z - spine) / [12.0, 10.0, 7.5, 3.0][layer];
  const envelope = Math.exp(-cross * cross * 0.85);
  const peak = trainRidgeHeight(x + Math.sin(z * 0.17 + phase) * 2.5, layer, phase);
  const crag = (1 - Math.abs(Math.sin(p * 67 + z * 0.34 + phase)))
    * Math.sin(p * 109 - z * 0.58) * [1.5, 0.9, 0.23, 0.08][layer];
  const gullies = Math.pow(Math.abs(Math.sin(p * 41 + z * 0.13)), 5)
    * [1.4, 0.7, 0.18, 0.04][layer] * envelope;
  return -2.5 + (peak + 2.5 + crag - gullies) * envelope;
}
