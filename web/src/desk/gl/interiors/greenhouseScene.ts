import type { AtmosphereSceneContext } from "../atmosphereRuntime";
import { Room } from "./sceneKit";

export function createGreenhouseScene(context: AtmosphereSceneContext) {
  const room = new Room(context, {
    camera: [0.6, 2.5, 10.2],
    target: [-0.3, 2.6, -12],
    background: 0x282436,
    fog: 0.036,
    ambient: 0.85,
    fov: 51,
    exposure: 1.05,
  });
  const iron = room.material(0x294239, 0.7, 0.35);
  const wood = room.surface(0x514337, "wood", [2, 3]);
  const darkWood = room.surface(0x29352b, "wood");
  room.floor(22, 50, room.surface(0x353c38, "plaster", [5, 15]));
  const glass = room.material(0x83938a, 0.16, 0.35);
  glass.transparent = true;
  glass.opacity = 0.13;
  glass.depthWrite = false;
  const slate = room.surface(0x555951, "plaster");
  slate.roughness = 0.32;
  for (let row = 0; row < 20; row++) {
    for (let col = 0; col < 3; col++) {
      room.box(
        [0.95, 0.04, 1.37],
        [-1.04 + col * 1.02, 0.02, 5 - row * 1.44],
        slate,
      ).rotation.y = (room.random() - 0.5) * 0.025;
    }
  }
  // A pitched iron roof repeated into the mist. Individually separated glass panes catch light.
  for (let z = 6; z > -30; z -= 3.3) {
    for (const side of [-1, 1]) {
      room.beam([side * 5.1, 0, z], [side * 5.1, 5.1, z], 0.052, iron);
      room.beam([side * 5.1, 5.1, z], [0, 7.1, z], 0.052, iron);
      for (const y of [0.9, 2.9, 5.1])
        room.beam([side * 5.1, y, z], [side * 5.1, y, z - 3.3], 0.035, iron);
      room.box([0.02, 4.1, 3.14], [side * 5.1, 3, z - 1.65], glass);
      const roof = room.box(
        [5.4, 0.018, 3.17],
        [side * 2.55, 6.1, z - 1.65],
        glass,
      );
      roof.rotation.z = side * -0.374;
    }
    room.beam([0, 7.1, z], [0, 7.1, z - 3.3], 0.052, iron);
  }
  for (const x of [-1.9, 1.9])
    room.beam([x, 0, -26], [x, 5.8, -26], 0.08, iron);
  room.beam([-1.9, 5.8, -26], [1.9, 5.8, -26], 0.08, iron);
  room.beam([0, 0, -26], [0, 5.8, -26], 0.05, iron);
  room.box([3.6, 5.6, 0.02], [0, 2.9, -26], glass);
  const soil = room.surface(0x242b21, "plaster");
  for (const side of [-1, 1]) {
    for (let z = 1; z > -25; z -= 4.4) {
      room.box([2.1, 0.12, 3.9], [side * 3.6, 0.95, z], wood);
      room.box([2.05, 0.1, 3.8], [side * 3.6, 0.7, z], darkWood);
      for (const dz of [-1.6, 1.6])
        room.box([0.13, 1, 0.15], [side * 4.4, 0.5, z + dz], iron);
      for (let i = 0; i < 3; i++) {
        const plant = room.plant(
          [side * (3.05 + room.random() * 0.9), 1.02, z - 1.4 + i * 1.2],
          0.85 + room.random() * 0.65,
          [0x284838, 0x365141, 0x4c5b36][i],
        );
        plant.rotation.y = room.random() * 5;
      }
      room.box([2.15, 0.18, 3.9], [side * 3.6, 0.15, z], soil);
    }
  }
  room.plant([-3.4, 0, 5], 2.25, 0x274432);
  room.plant([4.3, 0, 3.3], 2.35, 0x365b43);
  // Warm practical bulbs are sparse against the violet weather.
  for (let i = 0; i < 7; i++) {
    const z = 2 - i * 3.8;
    const x = Math.sin(i * 1.2) * 1.6;
    room.beam([x, 6.4, z], [x, 4.35, z], 0.013, iron);
    room.sphere(0.075, [x, 4.3, z], room.glow(0xffcf83, 3));
    room.halo(0xf9c97e, [x, 4.3, z], 0.9, 0.3);
    room.point(0xffc681, 18, [x, 4.2, z], 8);
  }
  room.spot(0xbdafde, 180, [-3, 8, -6], [0, 0, -7], 1.0, true);
  room.spot(0x97b6ac, 110, [5, 7, 0], [2, 1, -7], 0.9);
  const rainLight = room.point(0xbaa9de, 65, [0, 5, -16], 22);
  room.rain(12, 8, [0, 4, -28], 210);
  // Rain seen just outside both walls, rotated into their planes.
  room.rain(2.3, 5.1, [-5.5, 2.6, -4], 50);
  room.rain(2.3, 5.1, [5.5, 2.6, -4], 50);
  room.box([1.9, 0.12, 0.45], [-2.2, 0.56, -4], wood);
  room.label(
    "GLASSHOUSE  /  03",
    1.7,
    0.25,
    [0, 4.65, -12],
    "#cbbf9d",
    "#30483b",
    0.2,
  );
  const wateringCan = room.cylinder(
    0.25,
    0.3,
    0.43,
    [2.6, 0.23, 1.5],
    room.material(0x6a7965, 0.4, 0.6),
  );
  wateringCan.rotation.z = 0.05;
  room.beam([2.8, 0.29, 1.5], [3.3, 0.55, 1.5], 0.055, iron);
  room.dust(40, [7, 4, 20], [0, 3, -8], 0xbcba99, 0.011);
  room.ticks.push(({ elapsed, activity }) => {
    // Slow cloud illumination, never a flash; voice gently brightens the reflected water.
    rainLight.intensity =
      65 + Math.sin(elapsed * 0.12) * 7 + (activity?.level ?? 0) * 13;
  });
  return room.finish();
}
