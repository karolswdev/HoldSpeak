import type { AtmosphereSceneContext } from "../atmosphereRuntime";
import { Room, THREE } from "./sceneKit";

export function createMidnightArchiveScene(context: AtmosphereSceneContext) {
  const room = new Room(context, {
    camera: [0, 2.7, 10],
    target: [-0.1, 2.4, -9],
    background: 0x131c1b,
    fog: 0.038,
    ambient: 0.54,
  });
  const oak = room.surface(0x513d28, "wood", [2, 3]);
  const darkOak = room.surface(0x2a261e, "wood");
  const brass = room.material(0xa18c59, 0.4, 0.7);
  const wall = room.surface(0x474d41, "plaster", [3, 2]);
  room.floor(22, 56, room.surface(0x38332a, "wood", [9, 22]));
  room.box([20, 0.2, 46], [0, 7.2, -14], room.material(0x28322e));
  for (const x of [-6.3, 6.3]) room.box([0.3, 7.2, 42], [x, 3.6, -12], wall);
  room.box([12.7, 7.2, 0.3], [0, 3.6, -33], wall);
  // Receding wooden portals give the archive its long, hushed perspective.
  for (let z = 3; z > -30; z -= 6) {
    for (const x of [-6, 6]) room.box([0.28, 7, 0.4], [x, 3.5, z], darkOak);
    room.box([12.3, 0.4, 0.4], [0, 6.65, z], oak);
    const light = room.cylinder(
      0.14,
      0.54,
      0.3,
      [0, 5.7, z - 1],
      room.material(0x203d31),
    );
    room.beam([0, 5.85, z - 1], [0, 7, z - 1], 0.025, brass);
    room.cylinder(
      0.48,
      0.48,
      0.014,
      [0, 5.54, z - 1],
      room.glow(0xffd698, 1.5),
    );
    room.spot(0xffd698, 100, [0, 5.48, z - 1], [0, 0, z - 1], 0.95, z === 3);
    light.name = "Archive pendant";
  }
  const paper = room.material(0xc1ad7a, 0.85);
  for (const side of [-1, 1]) {
    for (let z = 0; z > -28; z -= 4.1) {
      const cabinet = room.group([side * 5.32, 0, z]);
      cabinet.rotation.y = (side * -Math.PI) / 2;
      room.box([3.55, 4.7, 1.05], [0, 2.35, 0], darkOak, cabinet);
      for (let col = 0; col < 4; col++) {
        for (let row = 0; row < 8; row++) {
          const x = -1.3 + col * 0.865,
            y = 0.42 + row * 0.53;
          room.box([0.8, 0.47, 0.09], [x, y, 0.56], oak, cabinet);
          room.box([0.29, 0.105, 0.021], [x, y + 0.07, 0.62], brass, cabinet);
          room.box([0.23, 0.06, 0.018], [x, y + 0.07, 0.636], paper, cabinet);
          room.beam(
            [x - 0.11, y - 0.08, 0.67],
            [x + 0.11, y - 0.08, 0.67],
            0.023,
            brass,
            cabinet,
          );
        }
      }
      room.box([3.75, 0.14, 1.18], [0, 4.77, 0], oak, cabinet);
      // Archival boxes above the drawers, with irregular gaps and faded colors.
      for (let i = 0; i < 6; i++) {
        room.box(
          [0.44, 0.65 + room.random() * 0.16, 0.78],
          [-1.4 + i * 0.54, 5.16, 0],
          room.material([0x595648, 0x414b44, 0x5f5140][i % 3]),
          cabinet,
        );
      }
    }
  }
  // The foreground reading table anchors the camera at a seat in the archive.
  room.box([6.8, 0.17, 2.9], [-0.1, 1.05, 1.1], oak);
  for (const x of [-2.9, 2.7]) room.box([0.19, 1, 2.3], [x, 0.5, 1.1], darkOak);
  room.box(
    [2.8, 0.018, 1.7],
    [-0.2, 1.15, 1.1],
    room.surface(0x253d31, "fabric"),
  );
  room.lamp([-2.35, 1.15, 0.3], 0x1f583d, 1.45);
  room.lamp([2.4, 1.15, 0.3], 0x1f583d, 1.45);
  for (let i = 0; i < 5; i++) {
    const folio = room.box(
      [0.9, 0.055, 0.67],
      [1.75, 1.17 + i * 0.065, 1.75],
      i === 4 ? room.material(0x713b29) : paper,
    );
    folio.rotation.y = i * 0.025;
  }
  room.box([0.75, 0.028, 0.54], [-0.4, 1.175, 1.0], paper).rotation.y = -0.12;
  room.beam([-0.4, 1.2, 1.1], [0.04, 1.2, 1.24], 0.015, brass);
  room.label(
    "THE MIDNIGHT ARCHIVE",
    3.8,
    0.36,
    [0, 5.7, -8.0],
    "#bdad80",
    "#24352e",
    0.25,
  );
  room.label(
    "READING ROOM  /  04",
    2.4,
    0.27,
    [0, 4.8, -20],
    "#b3aa85",
    "#28372f",
    0.5,
  );
  // Pneumatic tube at the right of the desk; a kept object gives a brief warm receipt lamp.
  room.beam([3.5, 1.1, 0.3], [3.5, 4.5, 0.3], 0.1, brass);
  room.beam([3.5, 4.5, 0.3], [5.9, 4.5, 0.3], 0.1, brass);
  room.cylinder(0.17, 0.17, 0.55, [3.5, 1.5, 0.3], brass);
  const receipt = room.glow(0xe9bb6e, 0.16);
  room.sphere(0.055, [3.5, 1.8, 0.48], receipt);
  let lastArrival = 0,
    glowUntil = -1;
  room.ticks.push(({ elapsed, activity }) => {
    if (activity && activity.arrival !== lastArrival) {
      lastArrival = activity.arrival;
      glowUntil = elapsed + 2;
    }
    receipt.emissiveIntensity =
      elapsed < glowUntil ? 2.5 : activity?.speaking ? 0.8 : 0.16;
  });
  room.dust(100, [9, 5, 22], [0, 3, -9], 0xbbae83, 0.018);
  room.point(0x96b5a5, 30, [0, 4, -12], 15);
  return room.finish();
}
