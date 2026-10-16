/** Authored cinematic sizes and periods, not an ephemeris. */
export const SATURN_RADIUS = 3.4;
export const SATURN_OBLATENESS = 0.902;
export const SATURN_RING_INNER = 4.1;
export const SATURN_RING_OUTER = 7.7;
export const SATURN_CASSINI_INNER = 6.48;
export const SATURN_CASSINI_OUTER = 6.76;

export const SATURN_MOONS = [
  { name: "Titan", radius: 0.29, orbit: 8.8, period: 390, phase: 2.35, inclination: 0.12 },
  { name: "Enceladus", radius: 0.115, orbit: 5.35, period: 175, phase: 5.2, inclination: -0.08 },
] as const;

export function saturnMoonPosition(
  index: number,
  elapsed: number,
  target: [number, number, number] = [0, 0, 0],
): [number, number, number] {
  const moon = SATURN_MOONS[index];
  if (!moon) throw new RangeError("Unknown Saturn moon");
  const phase = moon.phase + Math.max(0, elapsed) / moon.period * Math.PI * 2;
  target[0] = Math.cos(phase) * moon.orbit;
  target[1] = Math.sin(phase) * moon.orbit * moon.inclination;
  target[2] = Math.sin(phase) * moon.orbit;
  return target;
}

/** The camera fits the ring span on phones without stretching the globe. */
export function saturnFraming(width: number, height: number) {
  const aspect = Math.max(1, width) / Math.max(1, height);
  const halfHeight = Math.max(6, 8.25 / aspect);
  const halfWidth = halfHeight * aspect;
  return { halfWidth, halfHeight, x: aspect < 0.8 ? 0 : Math.min(3.3, Math.max(0, halfWidth - 8.1)), y: -0.35 };
}

export function saturnRenderSize(width: number, height: number, dpr: number) {
  const safeWidth = Math.max(1, width), safeHeight = Math.max(1, height);
  const scale = Math.min(1, 1600 / safeWidth, 1000 / safeHeight);
  return {
    width: Math.max(1, Math.round(safeWidth * scale)),
    height: Math.max(1, Math.round(safeHeight * scale)),
    dpr: Math.min(Math.max(dpr || 1, 1), 1.5),
  };
}
