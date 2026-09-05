import type { AtmosphereSceneContext } from "../atmosphereRuntime";
import { Room, THREE } from "./sceneKit";

export function createLaundromatScene(context: AtmosphereSceneContext) {
  const room = new Room(context, {
    camera: [0.4, 2.55, 10.4],
    target: [0, 2.0, -7],
    background: 0x15282c,
    ambient: 0.75,
    fog: 0.023,
    fov: 50,
  });
  const tile = room.surface(0x77918a, "tile", [5, 3]);
  const floor = room.surface(0x536b66, "tile", [7, 10]);
  const cream = room.surface(0xafa98e, "plaster", [2, 2]);
  const steel = room.material(0x8b9992, 0.32, 0.68);
  const dark = room.material(0x1d3236, 0.4, 0.4);
  const orange = room.material(0xaa5a32, 0.7);
  room.floor(22, 35, floor);
  room.box(
    [17, 0.15, 28],
    [0, 6.0, -5],
    room.surface(0x69766a, "tile", [4, 6]),
  );
  for (const side of [-1, 1]) room.box([0.2, 6, 28], [side * 7.4, 3, -5], tile);
  room.box([15, 1.5, 0.2], [0, 0.75, -12], tile);
  room.box([15, 1.4, 0.2], [0, 5.3, -12], cream);
  for (const x of [-7.3, -2.5, 2.5, 7.3])
    room.box([0.13, 3.15, 0.25], [x, 3.08, -11.9], steel);
  for (const y of [1.5, 4.65])
    room.box([14.7, 0.1, 0.26], [0, y, -11.9], steel);
  room.box(
    [1.7, 3.15, 0.15],
    [0, 3.08, -11.8],
    room.material(0x18343e, 0.18, 0.5),
  );
  room.beam([0.61, 2.0, -11.65], [0.61, 2.55, -11.65], 0.025, steel);
  room.rain(14.2, 3, [0, 3.15, -12.3], 200);
  room.halo(0x6aa3aa, [-3, 3, -18], 15, 0.35);
  const drums: THREE.Group[] = [];
  for (const side of [-1, 1]) {
    for (let i = 0; i < 6; i++) {
      const machine = room.group([side * 5.5, 0, 2.5 - i * 2.27]);
      machine.rotation.y = (side * -Math.PI) / 2;
      room.box([2.13, 2.6, 1.65], [0, 1.3, 0], cream, machine);
      room.box([2.03, 2.0, 0.035], [0, 1.08, 0.85], steel, machine);
      room.box([2.0, 0.4, 0.075], [0, 2.3, 0.84], dark, machine);
      room.box(
        [0.38, 0.16, 0.015],
        [-0.5, 2.31, 0.89],
        room.glow(0xa8c6a0, 0.25),
        machine,
      );
      room.box([0.025, 0.12, 0.022], [0.68, 2.31, 0.89], steel, machine);
      const knob = room.cylinder(
        0.086,
        0.086,
        0.055,
        [0.29, 2.31, 0.92],
        steel,
        machine,
      );
      knob.rotation.x = Math.PI / 2;
      room.ring(0.7, 0.078, [0, 1.12, 0.9], steel, machine);
      room.ring(0.61, 0.035, [0, 1.12, 0.925], dark, machine);
      room.sphere(
        0.6,
        [0, 1.12, 0.915],
        room.material(0x13282c, 0.18, 0.4),
        machine,
      ).scale.z = 0.045;
      const drum = room.group([0, 1.12, 0.95], machine);
      for (let j = 0; j < 4; j++) {
        const angle = (j * Math.PI) / 2;
        const fabric = room.sphere(
          0.28,
          [Math.sin(angle) * 0.3, Math.cos(angle) * 0.3, 0],
          room.material([0x596b66, 0x7e8c86, 0x455e66, 0x967a62][j]),
          drum,
        );
        fabric.scale.set(1.2, 0.7, 0.17);
        fabric.rotation.z = angle;
      }
      if (i % 3 !== 0) drums.push(room.moving(drum));
      room.box([2.15, 0.07, 1.75], [0, 2.64, 0], steel, machine);
    }
  }
  // Tired fluorescent tubes: stable output, a slow brightness drift rather than flicker.
  const tubes: THREE.MeshStandardMaterial[] = [];
  for (let z = 2; z > -12; z -= 5) {
    for (const x of [-3.4, 3.4]) {
      room.box([0.48, 0.12, 2.3], [x, 5.75, z], steel);
      const light = room.glow(0xd1e9c8, 1.8);
      tubes.push(light);
      for (const offset of [-0.12, 0.12])
        room.box([0.04, 0.04, 2.06], [x + offset, 5.66, z], light);
      room.spot(0xc6dfbd, 92, [x, 5.55, z], [x, 0, z], 0.94, z === 2 && x < 0);
    }
  }
  room.box([3.5, 0.12, 1.9], [0, 1.02, 0.6], cream);
  for (const x of [-1.5, 1.5])
    room.beam([x, 0.02, 0.6], [x, 1.02, 0.6], 0.04, steel);
  for (let i = 0; i < 3; i++) {
    room.box([1.05, 0.11, 0.83], [-1.25 + i * 1.24, 0.65, -8.7], orange);
    room.box([1.05, 0.88, 0.12], [-1.25 + i * 1.24, 1.12, -9.1], orange);
    room.beam(
      [-1.25 + i * 1.24, 0.1, -8.7],
      [-1.25 + i * 1.24, 0.65, -8.7],
      0.04,
      steel,
    );
  }
  // A vending machine gives one strong warm note at the back of the room.
  room.box([1.45, 2.8, 0.9], [5.3, 1.4, -10.2], room.material(0x583a2a));
  room.box([1.16, 1.78, 0.04], [5.3, 1.77, -9.72], room.glow(0xe0aa58, 0.4));
  for (let row = 0; row < 4; row++)
    for (let col = 0; col < 4; col++) {
      room.box(
        [0.16, 0.22, 0.035],
        [4.87 + col * 0.29, 1.2 + row * 0.33, -9.68],
        room.material([0x536b50, 0x9b6543, 0x86866b][(row + col) % 3]),
      );
    }
  room.point(0xe9ae59, 32, [5.3, 2, -9.5], 8);
  room.label(
    "OPEN ALL NIGHT",
    3.6,
    0.4,
    [0, 5.27, -11.78],
    "#f2b889",
    "#384946",
    0.55,
  );
  room.label(
    "WASH  /  FOLD",
    1.55,
    0.23,
    [0, 3.65, -11.67],
    "#bdcfbe",
    "#223b40",
    0.4,
  );
  const receipt = room.glow(0xedd795, 0.15);
  room.box([0.7, 0.06, 0.4], [0.6, 1.12, 0.6], dark);
  room.sphere(0.025, [0.8, 1.165, 0.7], receipt);
  room.ticks.push(({ elapsed, delta, activity }) => {
    drums.forEach((drum, i) => {
      drum.rotation.z += delta * (0.12 + (i % 2) * 0.05);
    });
    tubes.forEach((tube, i) => {
      tube.emissiveIntensity = 1.8 + Math.sin(elapsed * 0.18 + i) * 0.035;
    });
    receipt.emissiveIntensity =
      activity?.speaking || activity?.recording ? 1.8 : 0.15;
  });
  return room.finish();
}
