import type { AtmosphereSceneContext } from "../atmosphereRuntime";
import { Room, THREE } from "./sceneKit";

export function createNightTrainScene(context: AtmosphereSceneContext) {
  const room = new Room(context, {
    camera: [0, 2.5, 7.8],
    target: [0, 2.6, -4.5],
    background: 0x10232c,
    fog: 0.023,
    ambient: 0.55,
    fov: 49,
  });
  const walnut = room.surface(0x483125, "wood", [2, 1]);
  const woodDark = room.surface(0x281d18, "wood");
  const brass = room.material(0x9f8351, 0.38, 0.72);
  const velvet = room.surface(0x274b46, "fabric", [4, 3]);
  const wall = room.surface(0x635742, "plaster", [3, 2]);
  room.floor(18, 25, room.surface(0x302b24, "fabric", [6, 6]));
  room.box([18, 0.2, 18], [0, 5.8, -2.5], woodDark);
  for (const x of [-6.7, 6.7]) room.box([0.25, 6, 17], [x, 3, -3], walnut);
  room.box([14, 1.8, 0.3], [0, 0.9, -5.1], walnut);
  room.box([14, 1, 0.3], [0, 5.36, -5.1], wall);
  for (const x of [-5.7, 5.7])
    room.box([2.1, 3.25, 0.3], [x, 3.34, -5.1], wall);
  // Brass rails and a deep window reveal make the passing world feel outside.
  for (const y of [1.87, 4.92]) {
    room.box([9.3, 0.12, 0.4], [0, y, -4.9], woodDark);
    room.box([9.2, 0.035, 0.06], [0, y + 0.07, -4.66], brass);
  }
  for (const x of [-4.63, 4.63])
    room.box([0.15, 3.05, 0.4], [x, 3.4, -4.9], woodDark);
  const curtain = room.surface(0x594533, "fabric", [1, 3]);
  for (const side of [-1, 1]) {
    for (let i = 0; i < 9; i++) {
      room.cylinder(
        0.055,
        0.095,
        3.25,
        [side * (4.1 + i * 0.075), 3.39, -4.55 + Math.sin(i * 1.4) * 0.07],
        curtain,
      );
    }
  }
  const moon = room.sphere(0.36, [5, 7, -34], room.glow(0xa4c5d0, 0.8));
  moon.scale.z = 0.08;
  // Three layers move at different speeds. Trees are instanced for a bounded draw cost.
  for (let layer = 0; layer < 3; layer++) {
    const grove = room.group([0, 0, -18 - layer * 13]);
    const geometry = new THREE.ConeGeometry(1, 1, 7);
    const treeMaterial = room.material([0x102526, 0x172d31, 0x213b45][layer]);
    const trees = new THREE.InstancedMesh(geometry, treeMaterial, 60);
    grove.add(trees);
    // Track the shared geometry through the kit so switching rooms releases it.
    const tracked = room.mesh(geometry, treeMaterial, [0, -100, 0]);
    tracked.visible = false;
    const dummy = new THREE.Object3D();
    const heights = Array.from({ length: 60 }, () => 2.8 + room.random() * 4.3);
    room.ticks.push(({ elapsed }) => {
      heights.forEach((height, i) => {
        const x = ((i * 2.5 + elapsed * (3.4 - layer * 1.1)) % 150) - 75;
        dummy.position.set(x, height * 0.4 - 1.5, 0);
        dummy.scale.set(0.55 + height * 0.13, height, 1);
        dummy.updateMatrix();
        trees.setMatrixAt(i, dummy.matrix);
      });
      trees.instanceMatrix.needsUpdate = true;
    });
  }
  room.rain(8.2, 2.8, [0, 3.43, -5.3], 150);
  room.point(0x6a9fa9, 36, [0, 4.3, -4.5], 12);
  // Facing seats, stitched upholstery, and the small worktable between them.
  for (const side of [-1, 1]) {
    room.box([2.4, 0.52, 5.4], [side * 4.75, 0.66, -0.7], velvet);
    room.box([0.4, 1.7, 5.45], [side * 5.8, 1.4, -0.7], velvet);
    room.box([2.5, 0.3, 0.35], [side * 4.75, 1.45, 1.9], walnut);
    for (let z = -3; z < 2; z += 0.4)
      room.box(
        [2.35, 0.016, 0.014],
        [side * 4.72, 0.928, z],
        room.material(0x698073),
      );
    room.beam([side * 5.3, 4.87, -3.7], [side * 5.3, 4.87, 1.5], 0.035, brass);
    for (let z = -3.5; z < 1.5; z += 0.45)
      room.beam([side * 5.3, 4.87, z], [side * 6.5, 4.87, z], 0.024, brass);
  }
  room.box([5.4, 0.18, 2.1], [0, 1.15, -0.9], walnut);
  room.cylinder(0.13, 0.24, 1.1, [0, 0.56, -0.9], brass);
  room.lamp([1.7, 1.25, -1.25], 0x705638, 1.55);
  const paper = room.material(0xd9c6a1);
  room.box(
    [1.1, 0.05, 0.78],
    [-0.8, 1.27, -0.7],
    room.material(0x3e554b),
  ).rotation.y = -0.2;
  room.box([1.02, 0.03, 0.74], [-0.8, 1.31, -0.7], paper).rotation.y = -0.2;
  room.cylinder(0.135, 0.09, 0.2, [0.7, 1.35, -0.35], paper);
  room.cylinder(0.24, 0.24, 0.018, [0.7, 1.26, -0.35], paper);
  room.label(
    "COMPARTMENT 06",
    1.55,
    0.24,
    [-5.6, 4.6, -4.9],
    "#e2c792",
    "#44372a",
    0.15,
  );
  room.label(
    "THE NIGHT SERVICE",
    3.0,
    0.28,
    [0, 5.42, -4.87],
    "#b9a781",
    "#51432e",
    0.2,
  );
  room.spot(0xffc989, 160, [0, 5.5, 0], [0, 0.4, -1.5], 1, true);
  // A distant station's lamps pass silently; no app progress is invented.
  const station = room.moving(room.group([0, 0, -10]));
  for (let i = 0; i < 6; i++) {
    room.box([0.045, 2.9, 0.045], [i * 3, 0.5, 0], brass, station);
    room.box(
      [0.58, 0.065, 0.1],
      [i * 3, 1.96, 0],
      room.glow(0xffcf8f, 1.8),
      station,
    );
  }
  const recorderLamp = room.glow(0xebbe76, 0.1);
  room.sphere(0.035, [-0.1, 1.32, -0.95], recorderLamp);
  room.ticks.push(({ elapsed, activity }) => {
    station.position.x = ((elapsed * 3 + 56) % 140) - 100;
    room.root.rotation.z = Math.sin(elapsed * 0.7) * 0.0008;
    recorderLamp.emissiveIntensity =
      activity?.recording || activity?.speaking ? 2.3 : 0.1;
  });
  return room.finish();
}
