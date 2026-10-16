/** Authored cinematic scale and periods, not an ephemeris. */
export const MARS_RADIUS = 4.95;
export const MARS_MOONS = [
  { name: "Phobos", radius: 0.34, orbit: 6.8, period: 145, phase: 2.40 },
  { name: "Deimos", radius: 0.21, orbit: 9.3, period: 330, phase: 5.10 },
] as const;

export function marsMoonPosition(
  index: number, elapsed: number, target: [number, number, number] = [0, 0, 0],
): [number, number, number] {
  const moon = MARS_MOONS[index];
  if (!moon) throw new RangeError("Unknown Mars moon");
  const phase = moon.phase + Math.max(0, elapsed) / moon.period * Math.PI * 2;
  target[0] = Math.cos(phase) * moon.orbit;
  target[1] = Math.sin(phase) * (1.25 + index * 0.4) + index * 0.45;
  target[2] = Math.sin(phase) * moon.orbit;
  return target;
}

export function marsRenderSize(width: number, height: number, dpr: number) {
  const safeWidth = Math.max(1, width), safeHeight = Math.max(1, height);
  const scale = Math.min(1, 1600 / safeWidth, 1000 / safeHeight);
  return {
    width: Math.max(1, Math.round(safeWidth * scale)),
    height: Math.max(1, Math.round(safeHeight * scale)),
    dpr: Math.min(Math.max(dpr || 1, 1), 1.5),
  };
}
