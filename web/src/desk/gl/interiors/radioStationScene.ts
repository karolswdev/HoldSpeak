import type { AtmosphereSceneContext } from "../atmosphereRuntime";
import { Room, THREE } from "./sceneKit";

export function createRadioStationScene(context: AtmosphereSceneContext) {
  const room = new Room(context, {
    camera: [0.4, 2.65, 8.6],
    target: [0, 2.0, -4],
    background: 0x101921,
    ambient: 0.55,
  });
  const walnut = room.surface(0x4e3022, "wood", [2, 1]);
  const darkWood = room.surface(0x261e18, "wood", [2, 2]);
  const charcoal = room.surface(0x27282a, "fabric", [3, 3]);
  const metal = room.material(0x333b3b, 0.4, 0.65);
  const brass = room.material(0x957c4b, 0.35, 0.7);
  room.floor(22, 35, room.surface(0x292624, "fabric", [8, 10]));
  room.box([0.3, 7, 20], [-7.7, 3.5, -3], walnut);
  room.box([0.3, 7, 20], [7.7, 3.5, -3], walnut);
  room.box([16, 0.2, 20], [0, 6.1, -3], darkWood);
  room.box([16, 1.8, 0.3], [0, 0.9, -6], walnut);
  room.box([16, 1.3, 0.3], [0, 5.55, -6], charcoal);
  room.box([3.8, 3.4, 0.3], [-5.7, 3.4, -6], charcoal);
  room.box([2, 3.4, 0.3], [7, 3.4, -6], charcoal);
  for (let x = -7.5; x < -3.7; x += 0.16)
    room.box([0.04, 3.15, 0.16], [x, 3.45, -5.76], darkWood);
  // The window is a real opening: distant city geometry sits behind the mullions.
  for (const x of [-3.75, 1.2, 5.95])
    room.box([0.16, 3.5, 0.38], [x, 3.4, -5.86], darkWood);
  for (const y of [1.72, 5.08])
    room.box([10, 0.14, 0.45], [1.1, y, -5.82], walnut);
  const city = room.group([0, 0, -24]);
  const cityMat = room.material(0x111c27);
  const windowMat = room.glow(0xe9ac5c, 0.65);
  for (let i = 0; i < 38; i++) {
    const x = (i - 19) * 1.3,
      height = 2 + room.random() * 7;
    room.box(
      [1.1, height, 1],
      [x, height / 2 - 1, -room.random() * 5],
      cityMat,
      city,
    );
    for (let y = 0; y < height - 0.3; y += 0.65) {
      if (room.random() < 0.4) continue;
      room.box([0.12, 0.19, 0.04], [x - 0.26, y, 0.54], windowMat, city);
      room.box([0.12, 0.19, 0.04], [x + 0.26, y, 0.54], windowMat, city);
    }
  }
  room.rain(9.4, 3.1, [1.1, 3.4, -6.1], 230);
  room.point(0x648bb3, 45, [1.1, 4.2, -5.5], 13);
  // The board wraps the viewer, leaving the middle of the image quiet.
  room.box([13.7, 0.18, 3.2], [0, 0.98, -0.5], walnut);
  room.box([13.6, 0.28, 0.22], [0, 0.96, 1.15], darkWood);
  for (const x of [-5.8, 5.8])
    room.box([0.5, 1, 2.3], [x, 0.5, -0.6], darkWood);
  const console = room.group([-1.65, 1.16, -0.6]);
  console.rotation.x = -0.14;
  room.box([4.9, 0.17, 1.85], [0, 0, 0], metal, console);
  for (const x of [-2.51, 2.51])
    room.box([0.16, 0.25, 2], [x, 0, 0], walnut, console);
  const cream = room.material(0xd1c3a0, 0.6);
  const meters: THREE.Mesh[] = [];
  for (let i = 0; i < 12; i++) {
    const x = -2.1 + i * 0.38;
    room.box(
      [0.017, 0.017, 0.59],
      [x, 0.103, 0.43],
      room.material(0x070b0b),
      console,
    );
    room.box(
      [0.17, 0.045, 0.085],
      [x, 0.13, 0.33 + room.random() * 0.3],
      cream,
      console,
    );
    for (let j = 0; j < 3; j++)
      room.cylinder(
        0.055,
        0.055,
        0.067,
        [x, 0.13, -0.06 - j * 0.2],
        j === 0 ? brass : metal,
        console,
      );
    const meter = room.moving(
      room.box(
        [0.14, 0.018, 0.04],
        [x, 0.1, -0.78],
        room.glow(0xb7c978, 1.3),
        console,
      ),
    );
    meters.push(meter);
  }
  room.lamp([4.55, 1.08, -0.75], 0x64503a, 1.5);
  // A tape deck and monitor speaker, deliberately imperfect and hand owned.
  const deck = room.group([-5.3, 1.55, -1.25]);
  room.box([1.7, 0.94, 0.55], [0, 0, 0], metal, deck);
  room.box(
    [1.48, 0.72, 0.035],
    [0, 0, 0.3],
    room.material(0x777971, 0.4, 0.7),
    deck,
  );
  const reels: THREE.Group[] = [];
  for (const x of [-0.42, 0.42]) {
    const reel = room.moving(room.group([x, 0.1, 0.35], deck));
    room.ring(0.24, 0.023, [0, 0, 0], brass, reel);
    room.sphere(0.055, [0, 0, 0], metal, reel);
    for (let i = 0; i < 3; i++) {
      const spoke = room.box([0.44, 0.028, 0.016], [0, 0, 0], brass, reel);
      spoke.rotation.z = (i * Math.PI) / 3;
    }
    reels.push(reel);
  }
  for (const x of [-5, 5.0]) {
    room.box([0.95, 1.55, 0.8], [x, 2.57, -4.82], darkWood);
    for (const [y, radius] of [
      [2.26, 0.29],
      [2.98, 0.12],
    ]) {
      room.sphere(radius, [x, y, -4.35], room.material(0x0d1112)).scale.z =
        0.16;
      room.ring(radius, 0.025, [x, y, -4.28], metal);
    }
  }
  room.label(
    "NIGHT FREQUENCY",
    2.4,
    0.28,
    [-5.55, 4.75, -5.57],
    "#b4a28a",
    "#202421",
  );
  const onAir = room.label(
    "ON AIR",
    1.32,
    0.35,
    [0.9, 5.48, -5.7],
    "#ff915e",
    "#371710",
    0.18,
  );
  room.box([1.52, 0.5, 0.15], [0.9, 5.48, -5.8], metal);
  room.label(
    "88.6 FM",
    0.9,
    0.19,
    [-5.3, 1.28, -0.94],
    "#cab586",
    "#262d2a",
    0.2,
  );
  room.cylinder(0.14, 0.12, 0.22, [3.0, 1.19, -0.15], room.material(0xcebd9d));
  room.ring(0.095, 0.026, [3.19, 1.2, -0.15], cream).rotation.y = Math.PI / 2;
  room.box([0.72, 0.015, 0.5], [3.3, 1.09, 0.53], cream).rotation.y = 0.23;
  room.spot(0xffbf70, 130, [-3, 5.8, 1], [-2, 0.7, -1], 0.82, true);
  room.spot(0xf4b276, 75, [5.4, 5, -3.8], [3, 0.4, -1], 0.8);
  room.dust(60, [10, 4, 4], [0, 2.5, -2]);
  room.ticks.push(({ delta, activity }) => {
    const live = activity?.recording || activity?.speaking;
    (onAir.material as THREE.MeshStandardMaterial).emissiveIntensity = live
      ? 2.5
      : 0.18;
    for (const reel of reels) reel.rotation.z -= live ? delta * 0.7 : 0;
    meters.forEach((meter, i) => {
      meter.scale.z = 1 + (activity?.level ?? 0) * (3 + (i % 3));
    });
  });
  return room.finish();
}
