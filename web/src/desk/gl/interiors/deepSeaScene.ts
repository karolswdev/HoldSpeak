import type { AtmosphereSceneContext } from "../atmosphereRuntime";
import { Room, THREE } from "./sceneKit";

export function createDeepSeaScene(context: AtmosphereSceneContext) {
  const room = new Room(context, {
    camera: [0.1, 2.9, 10],
    target: [0, 2.5, -5],
    background: 0x062731,
    fog: 0.024,
    ambient: 0.66,
  });
  const steel = room.surface(0x294448, "plaster", [4, 3]);
  const iron = room.material(0x1c3439, 0.55, 0.65);
  const brass = room.material(0x857856, 0.46, 0.6);
  const dark = room.material(0x0a1c24, 0.65, 0.35);
  room.floor(22, 38, room.surface(0x273837, "tile", [6, 8]));
  room.box([18, 0.2, 18], [0, 6.4, -2], steel);
  for (const side of [-1, 1])
    room.box([0.3, 7, 24], [side * 7, 3.5, -4], steel);
  // An annular wall, not a painted window. The water and its inhabitants sit beyond it.
  const bulkhead = room.mesh(
    new THREE.RingGeometry(3.18, 12, 96),
    steel,
    [0, 3.3, -6],
  );
  bulkhead.receiveShadow = true;
  room.ring(3.22, 0.2, [0, 3.3, -5.89], brass);
  room.ring(3.45, 0.085, [0, 3.3, -5.81], iron);
  for (let i = 0; i < 28; i++) {
    const angle = (i * Math.PI * 2) / 28;
    room.sphere(
      0.057,
      [Math.cos(angle) * 3.46, 3.3 + Math.sin(angle) * 3.46, -5.7],
      brass,
    );
  }
  const seaGlow = room.halo(0x2e8992, [0, 4.9, -24], 32, 0.24);
  seaGlow.material.opacity = 0.3;
  room.point(0x3697b8, 155, [0, 4, -5.2], 19);
  const rib = room.material(0x3a5555, 0.6, 0.5);
  for (const x of [-6.2, 6.2]) {
    room.beam([x, 0, -5.5], [x, 6.2, -5.5], 0.1, rib);
    room.beam([x - 0.2, 5.8, -5], [x - 0.2, 5.8, 6], 0.085, brass);
  }
  // Diffuse shafts in the water use transparent geometry, with no expensive volumetric pass.
  const shaftMaterial = new THREE.MeshBasicMaterial({
    color: 0x52919b,
    transparent: true,
    opacity: 0.035,
    depthWrite: false,
    side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending,
  });
  for (let i = 0; i < 5; i++) {
    const shaft = room.mesh(
      new THREE.PlaneGeometry(0.6 + i * 0.25, 19),
      shaftMaterial,
      [-7 + i * 4, 4, -24 - i * 2],
    );
    shaft.rotation.z = -0.25;
  }
  room.dust(170, [20, 14, 18], [0, 4, -19], 0x7bb8b6, 0.055);
  const creatures: THREE.Group[] = [];
  const fishMaterial = room.material(0x0b222b);
  for (let i = 0; i < 9; i++) {
    const fish = room.moving(
      room.group([0, 3 + room.random() * 5, -21 - room.random() * 14]),
    );
    const body = room.sphere(1, [0, 0, 0], fishMaterial, fish);
    body.scale.set(0.6, 0.17, 0.15);
    const tail = room.mesh(
      new THREE.ConeGeometry(0.24, 0.35, 3),
      fishMaterial,
      [-0.65, 0, 0],
      fish,
    );
    tail.rotation.z = -Math.PI / 2;
    tail.scale.z = 0.2;
    creatures.push(fish);
  }
  // A ray travels much further away, passing rarely and very slowly.
  const ray = room.moving(room.group([0, 5.8, -42]));
  const rayBody = room.sphere(1, [0, 0, 0], fishMaterial, ray);
  rayBody.scale.set(2.6, 0.16, 1.1);
  ray.rotation.x = 0.6;
  room.beam([-1.5, 0, 0], [-5.1, 0, 0], 0.035, fishMaterial, ray);
  for (const side of [-1, 1]) {
    room.box([3.3, 1.12, 2], [side * 4.55, 0.8, -1.5], iron);
    const panel = room.group([side * 4.5, 1.7, -1.65]);
    panel.rotation.x = -0.24;
    room.box([3.4, 0.95, 0.22], [0, 0, 0], steel, panel);
    for (let i = 0; i < 3; i++) {
      const x = -1.06 + i * 1.05;
      room.ring(0.23, 0.037, [x, 0.07, 0.15], brass, panel);
      room.sphere(
        0.22,
        [x, 0.07, 0.145],
        room.glow(0xc7b681, 0.3),
        panel,
      ).scale.z = 0.05;
      room.beam([x, 0.07, 0.17], [x - 0.09, 0.22, 0.17], 0.011, dark, panel);
      room.cylinder(
        0.045,
        0.045,
        0.065,
        [x, -0.27, 0.18],
        brass,
        panel,
      ).rotation.x = Math.PI / 2;
    }
  }
  // Circular phosphor display: the sweep is ambient, the ring intensity follows actual capture.
  const sonar = room.group([-4.5, 3.47, -4.8]);
  room.box([2.1, 2.1, 0.36], [0, 0, 0], iron, sonar);
  room.sphere(0.85, [0, 0, 0.22], room.glow(0x0d3b39, 0.6), sonar).scale.z =
    0.1;
  const phosphor = room.glow(0x51b9a1, 0.65);
  for (const radius of [0.24, 0.5, 0.77])
    room.ring(radius, 0.007, [0, 0, 0.325], phosphor, sonar);
  const sweep = room.moving(room.group([0, 0, 0.34], sonar));
  room.beam([0, 0, 0], [0, 0.76, 0], 0.009, phosphor, sweep);
  room.label(
    "PELAGIC  /  09",
    2.9,
    0.3,
    [0, 6.06, -5.7],
    "#aac6bb",
    "#1c363b",
    0.18,
  );
  room.label(
    "LISTENING STATION",
    1.8,
    0.23,
    [-4.5, 2.29, -4.6],
    "#a4c1a5",
    "#152e30",
    0.25,
  );
  room.lamp([5.3, 1.38, -1.5], 0x5d674f, 1.1);
  room.spot(0xc4a671, 95, [5.2, 5.8, 1], [4.1, 0, -2], 0.85, true);
  room.ticks.push(({ elapsed, activity }) => {
    creatures.forEach((fish, i) => {
      fish.position.x = ((elapsed * (0.16 + i * 0.009) + i * 4) % 42) - 21;
      fish.rotation.y = Math.sin(elapsed * 0.8 + i) * 0.12;
    });
    ray.position.x = ((elapsed * 0.22 + 17) % 75) - 37;
    sweep.rotation.z = -elapsed * 0.25;
    phosphor.emissiveIntensity =
      0.65 + (activity?.level ?? 0) * 2 + (activity?.recording ? 0.8 : 0);
  });
  return room.finish();
}
