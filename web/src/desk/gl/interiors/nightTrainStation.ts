import { mergeGeometries } from "three/addons/utils/BufferGeometryUtils.js";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";
import { THREE, randomSource, type Room, type Vec } from "./sceneKit";
import { trainStationPosition } from "./nightTrainJourney";

/** A small shore station in metres. Room owns rendering; this module owns assets. */
export function createTrainStation(room: Room, parent: THREE.Group): {
  update(elapsed: number): void;
  dispose(): void;
} {
  const station = room.moving(room.group([0, 0, -6], parent));
  station.name = "Train passing station";
  const materials = new Set<THREE.Material>();
  const geometries = new Set<THREE.BufferGeometry>();
  const textures = new Set<THREE.Texture>();
  const lights = new Set<THREE.SpotLight>();
  const parts = new Map<THREE.Material, THREE.BufferGeometry[]>();
  const labels = new Map<THREE.Material, string>();
  const textureScale = new Map<THREE.Material, [number, number]>();
  const random = randomSource(0x53544154);
  function texture(pattern: "plaster" | "stone" | "timber" | "roof" | "window") {
    const canvas = document.createElement("canvas");
    canvas.width = pattern === "roof" ? 512 : 256;
    canvas.height = pattern === "timber" ? 512 : 256;
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("Train station material canvas unavailable");
    const w = canvas.width, h = canvas.height;
    ctx.fillStyle = "#dedbd1"; ctx.fillRect(0, 0, w, h);
    if (pattern === "plaster" || pattern === "stone") {
      // Quiet broad mineral changes sit under fine grit, rather than noisy paint.
      for (let i = 0; i < 100; i++) {
        ctx.fillStyle = i % 2 ? "rgba(85,79,64,0.018)" : "rgba(255,250,229,0.025)";
        ctx.fillRect(random() * w, random() * h, 8 + random() * 30, 6 + random() * 22);
      }
      for (let i = 0; i < 2400; i++) {
        ctx.fillStyle = i % 3 ? "rgba(51,49,42,0.035)" : "rgba(255,253,239,0.055)";
        ctx.fillRect(random() * w, random() * h, pattern === "stone" ? 1.8 : 1, 1);
      }
    } else if (pattern === "timber") {
      for (let line = 0; line < 75; line++) {
        const x = line / 75 * w;
        ctx.strokeStyle = line % 4 ? "rgba(66,45,25,0.11)" : "rgba(255,242,206,0.14)";
        ctx.lineWidth = line % 7 === 0 ? 1.6 : 0.7;
        ctx.beginPath();
        for (let y = 0; y <= h; y += 8) {
          const grain = x + Math.sin(y * 0.014 + line * 0.6) * 2.3 + Math.sin(y * 0.037 + line) * 0.8;
          if (y === 0) ctx.moveTo(grain, y); else ctx.lineTo(grain, y);
        }
        ctx.stroke();
      }
    } else if (pattern === "roof") {
      for (let row = 0; row < 4; row++) for (let column = -1; column < 5; column++) {
        const x = column * 128 + (row % 2 ? 64 : 0), y = row * 64;
        const shade = 169 + Math.floor(random() * 17);
        ctx.fillStyle = `rgb(${shade},${shade - 1},${shade - 5})`;
        ctx.fillRect(x, y, 127, 63);
        ctx.strokeStyle = "rgba(44,39,35,0.36)"; ctx.lineWidth = 1.5;
        ctx.strokeRect(x, y, 128, 64);
        ctx.fillStyle = "rgba(241,225,196,0.16)"; ctx.fillRect(x + 2, y + 2, 124, 1);
      }
    } else {
      const glow = ctx.createRadialGradient(w * 0.68, h * 0.72, 0, w * 0.55, h * 0.55, h * 0.75);
      glow.addColorStop(0, "#c9b58e"); glow.addColorStop(0.45, "#806c4e"); glow.addColorStop(1, "#282923");
      ctx.fillStyle = glow; ctx.fillRect(0, 0, w, h);
      ctx.fillStyle = "rgba(24,23,20,0.36)"; ctx.fillRect(w * 0.13, h * 0.19, w * 0.055, h * 0.81);
      ctx.fillRect(w * 0.18, h * 0.75, w * 0.55, h * 0.045);
      const glint = ctx.createLinearGradient(0, 0, w, h);
      glint.addColorStop(0, "rgba(174,204,220,0.10)"); glint.addColorStop(0.45, "rgba(174,204,220,0)");
      ctx.fillStyle = glint; ctx.fillRect(0, 0, w, h);
    }
    const map = new THREE.CanvasTexture(canvas);
    map.colorSpace = THREE.SRGBColorSpace;
    map.wrapS = map.wrapT = THREE.RepeatWrapping;
    map.anisotropy = 4;
    textures.add(map);
    return map;
  }
  const finish = <T extends THREE.Material>(name: string, material: T): T => {
    materials.add(material);
    labels.set(material, name);
    return material;
  };
  const standard = (name: string, color: number, roughness = 0.92, metalness = 0) =>
    finish(name, new THREE.MeshStandardMaterial({ color, roughness, metalness }));
  const shore = standard("Train station shore footprint", 0x60644f);
  const stone = standard("Train station masonry", 0x71776f);
  const paleStone = standard("Train station pale masonry", 0x85867a);
  const platform = standard("Train station platform", 0x898b7e);
  const plaster = standard("Train station waiting room", 0xb6b199);
  const roof = standard("Train station pitched roof", 0x574a42);
  const timber = standard("Train station timber canopy and bench", 0x594832, 0.86);
  const metal = standard("Train station lantern metalwork", 0x26312d, 0.56, 0.48);
  const glazing = finish("Train station lantern glass", new THREE.MeshStandardMaterial({
    color: 0xbca174, roughness: 0.19, transparent: true, opacity: 0.16,
    depthWrite: false, side: THREE.DoubleSide,
  }));
  const core = finish("Train station warm lantern cores", new THREE.MeshStandardMaterial({
    color: 0xeeb067, emissive: 0xffa34b, emissiveIntensity: 1.15, roughness: 0.5,
  }));
  const windows = finish("Train station warm waiting-room windows", new THREE.MeshStandardMaterial({
    color: 0x9b7953, emissive: 0xe9a254, emissiveIntensity: 0.22, roughness: 0.24,
  }));
  const mineralMap = texture("stone");
  for (const material of [shore, stone, paleStone, platform]) {
    material.map = material.bumpMap = mineralMap; material.bumpScale = 0.012;
    textureScale.set(material, [0.60, 0.60]);
  }
  plaster.map = plaster.bumpMap = texture("plaster"); plaster.bumpScale = 0.009;
  textureScale.set(plaster, [0.75, 0.75]);
  timber.map = timber.bumpMap = texture("timber"); timber.bumpScale = 0.006;
  textureScale.set(timber, [0.14, 0.90]);
  roof.map = roof.bumpMap = texture("roof"); roof.bumpScale = 0.007;
  textureScale.set(roof, [0.96, 0.64]);
  windows.map = windows.emissiveMap = texture("window");

  function add(shape: THREE.BufferGeometry, material: THREE.Material, at: Vec, rotation: Vec = [0, 0, 0]) {
    // One attribute grammar permits a single construction-time merge per finish.
    const part = shape.index ? shape.toNonIndexed() : shape;
    if (part !== shape) shape.dispose();
    part.applyMatrix4(new THREE.Matrix4().compose(
      new THREE.Vector3(...at), new THREE.Quaternion().setFromEuler(new THREE.Euler(...rotation)),
      new THREE.Vector3(1, 1, 1),
    ));
    const scale = textureScale.get(material);
    if (scale) {
      part.computeBoundingBox();
      const extent = part.boundingBox!.getSize(new THREE.Vector3()).toArray();
      const grainAxis = extent.indexOf(Math.max(...extent));
      const positions = part.getAttribute("position"), normals = part.getAttribute("normal");
      const uv = part.getAttribute("uv");
      for (let i = 0; i < positions.count; i++) {
        const p = [positions.getX(i), positions.getY(i), positions.getZ(i)];
        const n = [Math.abs(normals.getX(i)), Math.abs(normals.getY(i)), Math.abs(normals.getZ(i))];
        const face = n.indexOf(Math.max(...n));
        if (material === timber) {
          const across = [0, 1, 2].find(axis => axis !== grainAxis && axis !== face)
            ?? (grainAxis + 1) % 3;
          uv.setXY(i, p[across] / scale[0], p[grainAxis] / scale[1]);
        } else {
          const axes = face === 1 ? [0, 2] : face === 0 ? [2, 1] : [0, 1];
          uv.setXY(i, p[axes[0]] / scale[0], p[axes[1]] / scale[1]);
        }
      }
    }
    const collection = parts.get(material) ?? [];
    collection.push(part);
    parts.set(material, collection);
  }
  const box = (size: Vec, at: Vec, material: THREE.Material, rotation?: Vec) =>
    add(new THREE.BoxGeometry(...size), material, at, rotation);
  const cylinder = (top: number, bottom: number, height: number, at: Vec, material: THREE.Material, sides = 10) =>
    add(new THREE.CylinderGeometry(top, bottom, height, sides), material, at);
  function beam(from: Vec, to: Vec, width: number, depth: number, material: THREE.Material) {
    const start = new THREE.Vector3(...from), end = new THREE.Vector3(...to);
    const shape = new THREE.BoxGeometry(width, start.distanceTo(end), depth);
    shape.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(
      new THREE.Vector3(0, 1, 0), end.clone().sub(start).normalize(),
    ));
    add(shape, material, start.add(end).multiplyScalar(0.5).toArray() as Vec);
  }

  // The land continues below the lake surface (0.30), with an irregular quay
  // footprint and visible stonework; the platform is supported on this grade.
  const outline = new THREE.Shape();
  const shorePoints = [[-7.5, -2.7], [-5.9, -3.6], [4.9, -3.45], [7.4, -2.3],
    [7.8, 0.9], [6.25, 2.0], [-5.9, 1.95], [-7.6, 0.7]];
  shorePoints.forEach(([x, z], index) => {
    if (index === 0) outline.moveTo(x, -z);
    else outline.lineTo(x, -z);
  });
  outline.closePath();
  add(new THREE.ExtrudeGeometry(outline, { depth: 0.95, bevelEnabled: false, steps: 1 }),
    shore, [0, -0.35, 0], [-Math.PI / 2, 0, 0]);
  const deckTop = 0.78;
  add(new RoundedBoxGeometry(14, 0.18, 2.9, 2, 0.045), platform, [0, 0.69, 0]);
  // Staggered masonry blocks have mortar relief, including the underwater toe.
  box([13.9, 0.91, 0.24], [0, 0.145, 1.38], stone);
  for (let row = 0; row < 3; row++) {
    for (let column = 0; column < 20; column++) {
      const x = -6.65 + column * 0.68 + (row % 2 ? 0.18 : 0);
      box([0.65, 0.285, 0.075], [x, -0.16 + row * 0.30, 1.535],
        (column + row * 3) % 5 === 0 ? paleStone : stone);
    }
  }
  box([0.25, 0.91, 2.75], [-6.87, 0.145, 0], stone);
  box([0.25, 0.91, 2.75], [6.87, 0.145, 0], stone);
  box([4.28, 0.18, 2.35], [2.2, 0.69, -1.8], paleStone);

  // Plaster walls have actual window/door apertures and deep timber jambs.
  const front = -0.725, wallHeight = 2.10, wallTop = deckTop + wallHeight;
  box([0.17, wallHeight, 2.15], [0.235, deckTop + wallHeight / 2, -1.8], plaster);
  box([0.17, wallHeight, 2.15], [4.165, deckTop + wallHeight / 2, -1.8], plaster);
  box([4.10, wallHeight, 0.17], [2.2, deckTop + wallHeight / 2, -2.79], plaster);
  for (const [left, right] of [[0.15, 0.56], [1.14, 1.80], [2.50, 3.18], [3.76, 4.25]]) {
    box([right - left, wallHeight, 0.17], [(left + right) / 2, deckTop + wallHeight / 2, front], plaster);
    box([right - left, 0.28, 0.20], [(left + right) / 2, deckTop + 0.14, front + 0.015], paleStone);
  }
  for (const x of [0.85, 3.47]) {
    const bottom = deckTop + 0.80, top = deckTop + 1.52;
    box([0.58, 0.80, 0.17], [x, deckTop + 0.40, front], plaster);
    box([0.58, wallTop - top, 0.17], [x, (top + wallTop) / 2, front], plaster);
    box([0.56, top - bottom - 0.04, 0.018], [x, (top + bottom) / 2, front - 0.045], windows);
    box([0.56, top - bottom - 0.04, 0.006], [x, (top + bottom) / 2, front + 0.018], glazing);
    box([0.42, 0.045, 0.025], [x + 0.015, bottom + 0.20, front - 0.022], timber);
    for (const side of [-1, 1])
      box([0.045, top - bottom + 0.045, 0.10], [x + side * 0.29, (top + bottom) / 2, front + 0.025], timber);
    for (const y of [bottom, top]) box([0.65, 0.045, 0.13], [x, y, front + 0.035], timber);
    box([0.025, top - bottom, 0.06], [x, (top + bottom) / 2, front + 0.032], timber);
    box([0.65, 0.065, 0.19], [x, bottom - 0.04, front + 0.06], paleStone);
  }
  box([0.70, wallTop - deckTop - 1.90, 0.17], [2.15, wallTop - 0.10, front], plaster);
  box([0.68, 1.88, 0.075], [2.15, deckTop + 0.94, front - 0.02], timber);
  box([0.34, 0.43, 0.014], [2.15, deckTop + 1.43, front + 0.025], windows);
  box([0.34, 0.43, 0.006], [2.15, deckTop + 1.43, front + 0.040], glazing);
  cylinder(0.024, 0.024, 0.035, [2.39, deckTop + 0.97, front + 0.06], metal);

  // A pitched roof is a solid pair of sloping planes with gables and deep eaves.
  const rise = 0.85, halfDepth = 1.35, slope = Math.hypot(rise, halfDepth);
  const pitch = Math.atan2(rise, halfDepth);
  for (const side of [-1, 1]) {
    box([4.65, 0.10, slope], [2.2, wallTop + rise / 2, -1.8 + side * halfDepth / 2],
      roof, [side * pitch, 0, 0]);
    box([4.70, 0.12, 0.085], [2.2, wallTop - 0.015, -1.8 + side * halfDepth], timber);
    for (const course of [0.28, 0.56, 0.84, 1.12])
      box([4.66, 0.018, 0.024], [2.2, wallTop + rise * (1 - course / halfDepth) + 0.054, -1.8 + side * course], roof);
  }
  const gable = new THREE.Shape();
  const gableShoulder = rise * (1 - 1.075 / halfDepth);
  gable.moveTo(-1.075, 0); gable.lineTo(-1.075, gableShoulder);
  gable.lineTo(0, rise); gable.lineTo(1.075, gableShoulder);
  gable.lineTo(1.075, 0); gable.closePath();
  add(new THREE.ExtrudeGeometry(gable, { depth: 4.10, bevelEnabled: false, steps: 1 }),
    plaster, [0.15, wallTop, -1.8], [0, Math.PI / 2, 0]);
  box([4.72, 0.065, 0.11], [2.2, wallTop + rise, -1.8], roof);
  add(new THREE.CylinderGeometry(0.07, 0.07, 4.72, 12), roof,
    [2.2, wallTop + rise + 0.025, -1.8], [0, 0, Math.PI / 2]);

  // The attached canopy is slender timber, with visible diagonal load paths.
  for (const x of [-4.10, -1.40, 1.30]) {
    box([0.105, 2.0, 0.105], [x, deckTop + 1.0, 0.85], timber);
    box([0.17, 0.12, 0.17], [x, deckTop + 0.06, 0.85], paleStone);
    beam([x, 2.22, 0.85], [x + 0.42, 2.78, 0.85], 0.065, 0.065, timber);
    beam([x, 2.22, 0.85], [x, 2.78, 0.35], 0.065, 0.065, timber);
  }
  for (const x of [-4.10, -1.40]) box([0.095, 2.0, 0.095], [x, deckTop + 1.0, -0.65], timber);
  for (const z of [-0.65, 0.85]) box([5.85, 0.12, 0.10], [-1.40, 2.78, z], timber);
  box([6.10, 0.095, 1.85], [-1.40, 2.91, 0.10], roof, [0.085, 0, 0]);
  for (const x of [-4.10, -2.75, -1.40, -0.05, 1.30])
    box([0.075, 0.11, 1.80], [x, 2.84, 0.10], timber, [0.085, 0, 0]);

  // A human-sized slatted bench stands on two supports; nothing floats.
  for (const x of [-2.16, -0.94]) {
    for (const z of [0.02, 0.37]) box([0.055, 0.43, 0.055], [x, deckTop + 0.215, z], metal);
    box([0.065, 0.055, 0.45], [x, deckTop + 0.42, 0.195], metal);
    box([0.055, 0.76, 0.055], [x, deckTop + 0.38, -0.04], metal);
  }
  for (const z of [0.045, 0.17, 0.295]) box([1.65, 0.045, 0.105], [-1.55, deckTop + 0.45, z], timber);
  for (const y of [0.62, 0.75]) box([1.65, 0.095, 0.045], [-1.55, deckTop + y, -0.035], timber);

  for (const [index, x] of [-5.4, -0.05, 5.45].entries()) {
    const z = 1.16;
    const fixture = new THREE.Group();
    fixture.name = `Train station lantern ${index}`;
    fixture.position.set(x, deckTop, z);
    station.add(fixture);
    cylinder(0.052, 0.08, 0.12, [x, deckTop + 0.06, z], metal);
    cylinder(0.022, 0.032, 1.62, [x, deckTop + 0.93, z], metal);
    const bodyY = deckTop + 1.88;
    box([0.17, 0.27, 0.17], [x, bodyY, z], glazing);
    for (const dx of [-0.082, 0.082]) for (const dz of [-0.082, 0.082])
      cylinder(0.009, 0.009, 0.29, [x + dx, bodyY, z + dz], metal, 6);
    cylinder(0.115, 0.10, 0.045, [x, bodyY - 0.145, z], metal, 4);
    cylinder(0.025, 0.145, 0.085, [x, bodyY + 0.18, z], metal, 4);
    cylinder(0.022, 0.027, 0.13, [x, bodyY, z], core, 10);
    if (index < 2) {
      const practical = new THREE.SpotLight(0xffbd75, 10.5, 5, 0.75, 1, 2);
      practical.position.set(0.06, 1.66, 0);
      practical.target.position.set(index === 1 ? -0.45 : 0.30, 0.03, -0.55);
      practical.castShadow = true;
      practical.shadow.mapSize.set(512, 512);
      practical.shadow.camera.near = 0.15; practical.shadow.camera.far = 5;
      practical.shadow.bias = -0.0003; practical.shadow.normalBias = 0.008;
      fixture.add(practical, practical.target);
      lights.add(practical);
    }
  }

  // Direct assets must not be absorbed into Room's tracked-material batches.
  // There is one mesh per finish, and each remains a protected moving object.
  for (const [material, collection] of parts) {
    const merged = mergeGeometries(collection);
    collection.forEach(part => part.dispose());
    if (!merged) throw new Error("Train station geometry could not be combined");
    geometries.add(merged);
    const object = room.moving(new THREE.Mesh(merged, material));
    object.name = labels.get(material)!;
    object.castShadow = material !== glazing && material !== core && material !== windows;
    object.receiveShadow = material !== glazing && material !== core && material !== windows;
    station.add(object);
  }
  parts.clear();
  let disposed = false;
  function update(elapsed: number) {
    if (!disposed) station.position.x = trainStationPosition(elapsed);
  }
  update(0);
  return {
    update,
    dispose() {
      if (disposed) return;
      disposed = true;
      station.removeFromParent();
      for (const geometry of geometries) geometry.dispose();
      for (const material of materials) material.dispose();
      for (const texture of textures) texture.dispose();
      for (const light of lights) light.dispose();
      station.clear();
    },
  };
}
