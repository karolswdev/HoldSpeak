import { Room, THREE } from "./sceneKit";

/** Metre-scale cabin and props; the shared Room owns every resource created here. */
export function createTrainCompartment(room: Room) {
  const woodTexture = room.texture((ctx, size) => {
    ctx.fillStyle = "#68452c";
    ctx.fillRect(0, 0, size, size);
    for (let row = 0; row < size; row += 1.5) {
      const warmth = Math.sin(row * 0.11) * 0.5 + Math.sin(row * 0.037) * 0.5;
      ctx.strokeStyle = warmth > 0 ? `rgba(215,158,88,${0.045 + warmth * 0.075})`
        : `rgba(25,13,7,${0.055 - warmth * 0.10})`;
      ctx.lineWidth = 0.65 + room.random() * 0.75;
      ctx.beginPath();
      for (let x = 0; x <= size; x += 12) {
        const y = row + Math.sin(x * 0.014 + row * 0.024) * 5.5
          + Math.sin(x * 0.047 + row * 0.008) * 0.7;
        if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }
    for (let i = 0; i < 1800; i++) {
      ctx.fillStyle = `rgba(31,17,9,${room.random() * 0.12})`;
      ctx.fillRect(room.random() * size, room.random() * size, 2 + room.random() * 14, 0.45);
    }
  }, 512);
  woodTexture.wrapS = woodTexture.wrapT = THREE.RepeatWrapping;
  const walnut = room.material(0xffffff, 0.43, 0.025);
  walnut.map = walnut.bumpMap = woodTexture;
  walnut.bumpScale = 0.0012;
  const darkWood = room.material(0x73573e, 0.52);
  darkWood.map = darkWood.bumpMap = woodTexture;
  darkWood.bumpScale = 0.0008;
  const wall = room.surface(0x7b6a50, "fabric", [5, 4]);
  wall.bumpScale = 0.0005;
  const brass = room.material(0xb59659, 0.29, 0.79);
  const darkMetal = room.material(0x303a36, 0.48, 0.68);
  const velvet = room.surface(0x164d43, "fabric", [7, 6]);
  velvet.bumpScale = 0.001;
  velvet.roughness = 0.83;
  const piping = room.material(0x40665a, 0.74);
  const floor = room.surface(0x302f28, "fabric", [8, 8]);
  floor.bumpScale = 0.0009;
  room.box([2.25, 0.08, 2.9], [0, -0.04, 0.03], floor);
  room.box([2.25, 0.1, 2.9], [0, 2.32, 0.03], darkWood);
  for (const side of [-1, 1]) {
    room.box([0.09, 2.3, 2.9], [side * 1.17, 1.15, 0.03], walnut);
    room.box([0.018, 0.67, 2.75], [side * 1.116, 1.77, 0.03], wall);
    room.beam([side * 1.095, 1.42, -1.25], [side * 1.095, 1.42, 1.2], 0.009, brass);
  }
  // The wall is genuinely open: the landscape sits beyond this deep reveal.
  room.box([2.25, 0.92, 0.12], [0, 0.46, -1.41], walnut);
  room.box([2.25, 0.38, 0.12], [0, 2.11, -1.41], wall);
  for (const side of [-1, 1]) room.box([0.3, 1.02, 0.12], [side * 0.975, 1.42, -1.41], walnut);
  for (const y of [0.895, 1.945]) {
    room.box([1.79, 0.065, 0.19], [0, y, -1.30], darkWood);
    room.box([1.77, 0.008, 0.012], [0, y + (y < 1 ? 0.034 : -0.034), -1.197], brass);
  }
  for (const side of [-1, 1]) {
    room.box([0.065, 1.05, 0.19], [side * 0.857, 1.42, -1.30], darkWood);
    room.box([0.008, 1.01, 0.012], [side * 0.819, 1.42, -1.197], brass);
  }
  const sill = room.box([1.83, 0.055, 0.28], [0, 0.865, -1.23], walnut);
  sill.name = "Night Train window sill";
  const curtain = room.surface(0x7c5d3d, "fabric", [2, 8]);
  curtain.bumpScale = 0.0008;
  curtain.side = THREE.DoubleSide;
  for (const side of [-1, 1]) {
    const fold = new THREE.PlaneGeometry(0.20, 1.12, 32, 12);
    const points = fold.getAttribute("position");
    for (let i = 0; i < points.count; i++) {
      const x = points.getX(i), y = points.getY(i);
      points.setZ(i, Math.sin(x * 150) * 0.023 + Math.sin(y * 3.8) * 0.009);
    }
    fold.computeVertexNormals();
    room.mesh(fold, curtain, [side * 0.947, 1.425, -1.16]);
    room.ring(0.053, 0.004, [side * 0.947, 1.30, -1.105], brass).scale.set(1.65, 0.7, 1);
  }
  room.beam([-1.06, 2.03, -1.16], [1.06, 2.03, -1.16], 0.012, brass);

  // A softly arched shoulder, rather than a rectangular slab, frames the seat.
  const backProfile = new THREE.Shape();
  backProfile.moveTo(-0.31, 0);
  backProfile.lineTo(0.31, 0);
  backProfile.lineTo(0.31, 0.57);
  backProfile.bezierCurveTo(0.31, 0.82, 0.17, 0.89, 0, 0.89);
  backProfile.bezierCurveTo(-0.17, 0.89, -0.31, 0.82, -0.31, 0.57);
  backProfile.closePath();
  const backGeometry = new THREE.ExtrudeGeometry(backProfile, {
    depth: 0.095, bevelEnabled: true, bevelSegments: 5, steps: 1,
    bevelSize: 0.035, bevelThickness: 0.035, curveSegments: 20,
  });
  const seatBack = room.mesh(backGeometry, velvet, [-0.88, 0.49, 0.25]);
  seatBack.name = "Night Train curved berth";
  room.moving(seatBack);
  seatBack.rotation.y = -0.12;
  room.box([0.64, 0.19, 1.28], [-0.88, 0.45, -0.04], velvet);
  room.box([0.64, 0.16, 1.30], [-0.88, 0.29, -0.04], darkWood);
  room.box([0.10, 0.12, 1.18], [-0.52, 0.66, 0.04], walnut);
  room.box([0.10, 0.055, 1.12], [-0.52, 0.735, 0.04], velvet);
  const seamPoints: THREE.Vector3[] = [];
  for (let i = 0; i <= 64; i++) {
    const t = i / 64;
    const angle = Math.PI * (1 - t);
    seamPoints.push(new THREE.Vector3(Math.cos(angle) * 0.278, 0.59 + Math.sin(angle) * 0.245, 0.141));
  }
  room.mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(seamPoints), 64, 0.0025, 6, false), piping, [-0.88, 0.49, 0.25]);
  for (const x of [-1.0, -0.76]) {
    const tuft = room.sphere(0.012, [x, 0.97, 0.393], velvet);
    tuft.scale.z = 0.25;
  }
  room.box([0.44, 0.20, 1.45], [0.94, 0.45, -0.05], velvet);
  room.box([0.17, 0.72, 1.48], [1.10, 0.83, -0.05], velvet);
  room.box([0.50, 0.09, 0.11], [0.92, 0.70, 0.72], walnut);

  const table = room.box([0.78, 0.055, 0.48], [0.12, 0.75, -0.57], walnut);
  table.name = "Night Train walnut table";
  room.moving(table);
  room.box([0.76, 0.009, 0.46], [0.12, 0.72, -0.57], brass);
  room.cylinder(0.025, 0.043, 0.69, [0.12, 0.35, -0.57], darkMetal);
  room.box([0.28, 0.025, 0.24], [0.12, 0.02, -0.57], darkMetal);

  const lamp = room.moving(room.group([0.10, 0.78, -0.68]));
  lamp.name = "Night Train practical lamp";
  room.cylinder(0.058, 0.070, 0.014, [0, 0.008, 0], brass, lamp);
  room.cylinder(0.009, 0.012, 0.27, [0, 0.15, 0], brass, lamp);
  const shadeMaterial = room.surface(0xcfb987, "fabric", [3, 1]);
  shadeMaterial.bumpScale = 0.0004;
  shadeMaterial.side = THREE.DoubleSide;
  shadeMaterial.emissive.set(0xb98a46);
  shadeMaterial.emissiveIntensity = 0.07;
  const shade = room.mesh(new THREE.CylinderGeometry(0.075, 0.12, 0.13, 64, 1, true), shadeMaterial, [0, 0.31, 0], lamp);
  shade.name = "Night Train lamp shade";
  room.ring(0.12, 0.003, [0, 0.245, 0], brass, lamp).rotation.x = Math.PI / 2;
  room.ring(0.075, 0.0025, [0, 0.375, 0], brass, lamp).rotation.x = Math.PI / 2;
  const diffuser = room.cylinder(0.112, 0.112, 0.003, [0, 0.247, 0], room.glow(0xffd8a2, 2.0), lamp);
  diffuser.castShadow = false;
  room.point(0xffd29a, 0.27, [0.10, 1.025, -0.68], 1.7);
  const pool = room.spot(0xffd7a4, 0.85, [0.10, 1.018, -0.68], [0.12, 0.75, -0.47], 0.94, true);
  pool.shadow.camera.near = 0.02;
  pool.shadow.camera.far = 3;
  pool.shadow.mapSize.set(1024, 1024);
  pool.shadow.bias = -0.0001;
  room.point(0x98c1df, 0.40, [-0.12, 1.75, -1.10], 3.6);
  room.point(0xe7ba7c, 0.12, [-0.8, 1.95, 0.70], 2.3);

  const ceramic = room.material(0xd0c9ad, 0.23);
  const cup = room.moving(room.group([0.20, 0.80, -0.54]));
  cup.name = "Night Train glazed cup";
  const cupProfile = [
    new THREE.Vector2(0.027, 0), new THREE.Vector2(0.032, 0.008),
    new THREE.Vector2(0.038, 0.069), new THREE.Vector2(0.037, 0.081),
    new THREE.Vector2(0.033, 0.082), new THREE.Vector2(0.032, 0.071),
    new THREE.Vector2(0.027, 0.012), new THREE.Vector2(0, 0.012),
  ];
  room.mesh(new THREE.LatheGeometry(cupProfile, 48), ceramic, [0, 0, 0], cup);
  const handle = room.ring(0.024, 0.005, [0.047, 0.043, 0], ceramic, cup);
  handle.scale.set(0.75, 1, 1);
  room.cylinder(0.059, 0.050, 0.007, [0, -0.012, 0], ceramic, cup);
  const tea = room.material(0x29180e, 0.13);
  room.cylinder(0.031, 0.031, 0.001, [0, 0.067, 0], tea, cup);

  // The cover rests on the 0.7775 m table top; all paper is part of a block.
  const book = room.moving(room.group([-0.08, 0.7805, -0.44]));
  book.name = "Night Train open book";
  book.rotation.y = -0.18;
  const cover = room.material(0x354d41, 0.65);
  const edgeTexture = room.texture((ctx, size) => {
    ctx.fillStyle = "#cbbd9e";
    ctx.fillRect(0, 0, size, size);
    ctx.fillStyle = "rgba(112,96,72,0.24)";
    for (let y = 0; y < size; y += 8) ctx.fillRect(0, y, size, 0.7);
  }, 128);
  edgeTexture.wrapT = THREE.RepeatWrapping;
  const edges = room.material(0xffffff, 0.9);
  edges.map = edgeTexture;
  const printTexture = room.texture((ctx, size) => {
    ctx.fillStyle = "#d8cbae";
    ctx.fillRect(0, 0, size, size);
    ctx.fillStyle = "rgba(91,79,59,0.54)";
    for (let row = 0; row < 18; row++) {
      let x = 53;
      for (let word = 0; word < 7; word++) {
        const width = 20 + ((row * 17 + word * 29) % 31);
        if (x + width > size - 48) break;
        ctx.fillRect(x, 53 + row * 23, width, 2.2);
        x += width + 9;
      }
    }
  }, 512);
  const paper = room.material(0xffffff, 0.9);
  paper.map = printTexture;
  const pageHeight = (t: number) => 0.010 + Math.sin(t * Math.PI) * 0.008 + t * 0.003;
  room.box([0.002, 0.006, 0.17], [0, 0, 0], cover, book);
  for (const side of [-1, 1]) {
    room.box([0.112, 0.006, 0.17], [side * 0.057, 0, 0], cover, book);
    // A continuous, gently curved solid block reaches from cover to paper.
    const profile = new THREE.Shape();
    profile.moveTo(side * 0.003, 0.003);
    profile.lineTo(side * 0.109, 0.003);
    profile.lineTo(side * 0.109, pageHeight(1));
    for (let step = 24; step >= 0; step--) {
      const t = step / 24;
      profile.lineTo(side * (0.003 + t * 0.106), pageHeight(t));
    }
    profile.closePath();
    const block = new THREE.ExtrudeGeometry(profile, { depth: 0.16, bevelEnabled: false, steps: 1 });
    const positions = block.getAttribute("position"), uv = block.getAttribute("uv");
    for (let i = 0; i < positions.count; i++) uv.setXY(i, positions.getX(i) * 4, positions.getY(i) * 50);
    room.mesh(block, edges, [0, 0, -0.08], book);

    // Printed top follows exactly the block below it, including the low gutter.
    const top = new THREE.PlaneGeometry(0.106, 0.16, 24, 4);
    top.rotateX(-Math.PI / 2);
    const vertices = top.getAttribute("position");
    for (let i = 0; i < vertices.count; i++) {
      const t = vertices.getX(i) / 0.106 + 0.5;
      const across = side > 0 ? t : 1 - t;
      vertices.setXYZ(i, side > 0 ? 0.003 + t * 0.106 : -0.109 + t * 0.106,
        pageHeight(across) + 0.00005, vertices.getZ(i));
    }
    top.computeVertexNormals();
    room.mesh(top, paper, [0, 0, 0], book);
  }
}
