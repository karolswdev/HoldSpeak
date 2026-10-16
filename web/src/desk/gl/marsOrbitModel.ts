/** Physical relative body sizes; orbit distances and periods remain authored. */
export const MARS_RADIUS = 4.95;
/** NASA/JPL mean radius in km; moon radii use equivalent-volume means. */
export const MARS_MEAN_RADIUS_KM = 3389.50;
export const MARS_MOONS = [
  { name: "Phobos", physicalRadiusKm: 11.08, radius: MARS_RADIUS * 11.08 / MARS_MEAN_RADIUS_KM, orbit: 6.8, period: 145, phase: 2.40 },
  { name: "Deimos", physicalRadiusKm: 6.2, radius: MARS_RADIUS * 6.2 / MARS_MEAN_RADIUS_KM, orbit: 9.3, period: 330, phase: 5.10 },
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
