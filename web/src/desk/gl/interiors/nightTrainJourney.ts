/** Authored continuous travel, in scene metres and seconds; no geographic claim. */
export const TRAIN_TERRAIN_SPAN = 600;
export const TRAIN_TERRAIN_EXTENTS = [38, 34, 12, 3.2] as const;
export const TRAIN_TERRAIN_SPEEDS = [0.095, 0.17, 0.30, 1.08] as const;
export const TRAIN_TREE_LAYERS = [
  { name: "distant woods", count: 84, depth: 57, spread: 500, speed: TRAIN_TERRAIN_SPEEDS[2], height: 3.1 },
  { name: "shore woods", count: 96, depth: 47, spread: 360, speed: TRAIN_TERRAIN_SPEEDS[2], height: 2.8 },
  { name: "near vegetation", count: 28, depth: 9, spread: 240, speed: TRAIN_TERRAIN_SPEEDS[3], height: 2.5 },
] as const;

export function trainTravelPosition(initial: number, elapsed: number, speed: number, span: number): number {
  return ((initial - Math.max(0, elapsed) * speed + span / 2) % span + span) % span - span / 2;
}

/** A few different summits, with unequal shoulders and long front buttresses. */
export const TRAIN_MASSIFS = [
  [
    { x: -255, z: 2, height: 20, left: 42, right: 58, front: 14, back: 18 },
    { x: -155, z: -3, height: 28, left: 61, right: 34, front: 12, back: 16 },
    { x: -35, z: -4, height: 26, left: 27, right: 43, front: 13, back: 17 },
    { x: 18, z: 1, height: 33, left: 38, right: 26, front: 11, back: 15 },
    { x: 70, z: -2, height: 23, left: 22, right: 48, front: 15, back: 12 },
    { x: 169, z: 4, height: 29, left: 52, right: 37, front: 10, back: 17 },
    { x: 267, z: -5, height: 21, left: 38, right: 48, front: 16, back: 11 },
  ],
  [
    { x: -268, z: 1, height: 12, left: 44, right: 29, front: 15, back: 12 },
    { x: -163, z: -2, height: 16, left: 32, right: 47, front: 10, back: 15 },
    { x: -55, z: -3, height: 13, left: 39, right: 22, front: 13, back: 11 },
    { x: 7, z: 3, height: 18, left: 32, right: 46, front: 10, back: 14 },
    { x: 78, z: -5, height: 11, left: 37, right: 24, front: 14, back: 10 },
    { x: 182, z: 2, height: 14, left: 48, right: 29, front: 12, back: 16 },
    { x: 273, z: -4, height: 17, left: 29, right: 41, front: 10, back: 13 },
  ],
] as const;

function hash(x: number, z: number, salt: number): number {
  let n = (Math.imul(x, 374761393) ^ Math.imul(z, 668265263) ^ salt) >>> 0;
  n = Math.imul(n ^ (n >>> 13), 1274126177);
  return ((n ^ (n >>> 16)) >>> 0) / 4294967295;
}

/** Smooth, repeatable detail tiles in travel x only, preserving the long seam. */
function noise(x: number, z: number, cells: number, salt: number): number {
  const px = x / TRAIN_TERRAIN_SPAN * cells, pz = z / TRAIN_TERRAIN_SPAN * cells;
  const ix = Math.floor(px), iz = Math.floor(pz);
  const fx = px - ix, fz = pz - iz;
  const u = fx * fx * (3 - 2 * fx), v = fz * fz * (3 - 2 * fz);
  const wrap = (i: number) => ((i % cells) + cells) % cells;
  const a = hash(wrap(ix), iz, salt), b = hash(wrap(ix + 1), iz, salt);
  const c = hash(wrap(ix), iz + 1, salt), d = hash(wrap(ix + 1), iz + 1, salt);
  return (a + (b - a) * u) * (1 - v) + (c + (d - c) * u) * v;
}

/** Connected rock masses and glacial cuts; detail follows their landform. */
export function trainTerrainHeight(x: number, z: number, layer: number, phase: number): number {
  const salt = Math.floor(phase * 4096);
  if (layer >= 2) {
    const warped = x + (noise(x, z, 16, salt) - 0.5) * 7;
    const width = layer === 2 ? 7.5 : 3.0;
    const spine = (noise(x, 0, 32, salt + 1) - 0.5) * (layer === 2 ? 6 : 2.5);
    const envelope = Math.exp(-(((z - spine) / width) ** 2) * 0.85);
    const crest = layer === 2 ? 0.25 + noise(warped, z, 32, salt + 3) * 2.8
      : -0.35 + noise(warped, z, 64, salt + 3) * 1.35;
    return -2.5 + (crest + 2.5) * envelope;
  }
  const wx = x + (noise(x, z, 32, salt) - 0.5) * 3.8;
  const wz = z + (noise(x, z, 32, salt + 2) - 0.5) * 2.4;
  const merge = (a: number,b: number,width: number) => {
    const blend=Math.max(0,1-Math.abs(a-b)/width);
    return Math.max(a,b)+blend*blend*width*0.25;
  };
  let mass = 0.5;
  for (const peak of TRAIN_MASSIFS[layer]) {
    const dx = trainTravelPosition(wx - peak.x, 0, 0, TRAIN_TERRAIN_SPAN), dz = wz - peak.z;
    const radius = Math.hypot(dx / (dx < 0 ? peak.left : peak.right), dz / (dz > 0 ? peak.front : peak.back));
    mass = merge(mass,peak.height*Math.max(0,1-radius)**1.20,2.2);
    // Three arêtes descend unequally from each summit, leaving deep side gullies.
    if (dz > -1 && dz < 32) {
      for (const direction of [-0.59, 0.12, 0.73]) {
        const width=4.3+dz*0.17;
        const across=Math.exp(-(((dx-dz*direction)/width)**2));
        const length = Math.max(0, 1 - Math.max(0, dz) / (direction === 0.12 ? 32 : 25));
        mass=merge(mass,peak.height*length**1.65*across,1.8);
      }
    }
  }
  for (const valley of layer === 0 ? [-8, 46] : [-21, 45]) {
    const dx = trainTravelPosition(wx - valley - wz * 0.27, 0, 0, TRAIN_TERRAIN_SPAN);
    const cut = Math.exp(-((dx / 7.5) ** 2)) * Math.max(0, 1 - Math.abs(wz - 4) / 27);
    mass -= Math.min(Math.max(0, mass - 0.5), layer === 0 ? 7 : 3.5) * cut;
  }
  const ridged = 1 - Math.abs(noise(wx, wz, 128, salt + 5) * 2 - 1);
  const fine = noise(wx, wz, 256, salt + 9) - 0.5;
  const detail=((ridged-0.55)*3.6+fine*1.35)*Math.min(1,mass/9);
  const extent=TRAIN_TERRAIN_EXTENTS[layer];
  const edge=Math.min(1,Math.max(0,(Math.abs(z)-extent*0.70)/(extent*0.28)));
  const fade=1-edge*edge*(3-2*edge);
  return -2.5+((mass+detail)*(layer===0?0.748:0.60)+2.5)*fade;
}

export function trainRidgeHeight(x: number, layer: number, phase: number): number {
  return trainTerrainHeight(x, 0, layer, phase);
}

export function trainStationPosition(elapsed: number): number {
  return trainTravelPosition(180, elapsed, 1.08, 600);
}
