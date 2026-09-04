import * as THREE from "three";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import type {
  AtmosphereFrame,
  AtmosphereScene,
  AtmosphereSceneContext,
  AtmosphereViewport,
} from "./atmosphereRuntime";

const MAX_RENDER_WIDTH = 1_600;
const MAX_RENDER_HEIGHT = 1_000;
const CAMERA_X = 1.8;
const CAMERA_Y = 2.45;
const CAMERA_Z = 16.4;
const CAMERA_TARGET_X = -2.4;
const CAMERA_TARGET_Y = 1.25;
const CAMERA_TARGET_Z = -18;
const DRIP_COUNT = 56;
const DRIZZLE_COUNT = 320;
const LANTERN_DRIZZLE_COUNT = 52;
const LANTERN_POSITIONS: ReadonlyArray<readonly [number, number, number]> = [
  [-7.0, 0.72, 6.0],
  [1.45, 0.74, 3.3],
  [-6.6, 0.71, 0.2],
  [0.35, 0.7, -2.6],
  [-7.0, 0.67, -5.2],
  [-0.25, 0.63, -8.0],
  [-6.0, 0.58, -10.7],
  [-0.65, 0.53, -13.3],
];

interface LanternEmitter {
  glass: THREE.MeshStandardMaterial;
  halo: THREE.Sprite;
  groundGlow: THREE.Mesh<THREE.PlaneGeometry, THREE.MeshBasicMaterial>;
  light: THREE.PointLight | null;
  phase: number;
  strength: number;
}

interface PoolRing {
  mesh: THREE.Mesh<THREE.RingGeometry, THREE.MeshBasicMaterial>;
  phase: number;
}

interface DrizzleDrop {
  originX: number;
  x: number;
  y: number;
  z: number;
  speed: number;
  drift: number;
}

export function makeGardenRandom(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (Math.imul(state, 1103515245) + 12345) >>> 0;
    return state / 0x100000000;
  };
}

/** Solar cells and inexpensive LEDs never hold a perfectly flat output. */
export function lanternGlowAt(elapsed: number, phase: number): number {
  return (
    0.965 +
    Math.sin(elapsed * 1.17 + phase) * 0.022 +
    Math.sin(elapsed * 0.31 + phase * 1.73) * 0.013
  );
}

/** A broad quiet breeze, deliberately too slow to read as looping animation. */
export function gardenBreezeAt(elapsed: number, phase = 0): number {
  return (
    Math.sin(elapsed * 0.29 + phase) * 0.68 +
    Math.sin(elapsed * 0.73 + phase * 1.9) * 0.32
  );
}

function disposeScene(scene: THREE.Scene): void {
  const geometries = new Set<THREE.BufferGeometry>();
  const materials = new Set<THREE.Material>();
  scene.traverse((object) => {
    if (
      !(object instanceof THREE.Mesh) &&
      !(object instanceof THREE.Line) &&
      !(object instanceof THREE.Points) &&
      !(object instanceof THREE.Sprite)
    ) {
      return;
    }
    if (
      object instanceof THREE.Mesh ||
      object instanceof THREE.Line ||
      object instanceof THREE.Points
    ) {
      geometries.add(object.geometry);
    }
    const entries = Array.isArray(object.material)
      ? object.material
      : [object.material];
    for (const material of entries) materials.add(material);
  });
  for (const geometry of geometries) geometry.dispose();
  for (const material of materials) material.dispose();
}

function box(
  parent: THREE.Object3D,
  size: [number, number, number],
  position: [number, number, number],
  material: THREE.Material,
): THREE.Mesh {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(...size), material);
  mesh.position.set(...position);
  parent.add(mesh);
  return mesh;
}

function beamBetween(
  parent: THREE.Object3D,
  start: THREE.Vector3,
  end: THREE.Vector3,
  thickness: number,
  depth: number,
  material: THREE.Material,
): THREE.Mesh {
  const direction = end.clone().sub(start);
  const beam = new THREE.Mesh(
    new THREE.BoxGeometry(thickness, direction.length(), depth),
    material,
  );
  beam.position.copy(start).add(end).multiplyScalar(0.5);
  beam.quaternion.setFromUnitVectors(
    new THREE.Vector3(0, 1, 0),
    direction.normalize(),
  );
  parent.add(beam);
  return beam;
}

function radialGlowTexture(
  size = 96,
  color: [number, number, number] = [255, 200, 112],
): THREE.DataTexture {
  const pixels = new Uint8Array(size * size * 4);
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const dx = (x + 0.5) / size - 0.5;
      const dy = (y + 0.5) / size - 0.5;
      const radius = Math.sqrt(dx * dx + dy * dy) * 2;
      const falloff = Math.pow(Math.max(0, 1 - radius), 2.65);
      const offset = (y * size + x) * 4;
      pixels[offset] = color[0];
      pixels[offset + 1] = color[1];
      pixels[offset + 2] = color[2];
      pixels[offset + 3] = Math.round(falloff * 255);
    }
  }
  const texture = new THREE.DataTexture(
    pixels,
    size,
    size,
    THREE.RGBAFormat,
    THREE.UnsignedByteType,
  );
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.needsUpdate = true;
  return texture;
}

function groundTexture(seed: number): THREE.DataTexture {
  const size = 128;
  const pixels = new Uint8Array(size * size * 4);
  const random = makeGardenRandom(seed);
  for (let index = 0; index < size * size; index += 1) {
    const grain = Math.floor(random() * 20);
    const bark = random() > 0.88 ? 14 : 0;
    const offset = index * 4;
    pixels[offset] = 31 + grain + bark;
    pixels[offset + 1] = 28 + Math.floor(grain * 0.62);
    pixels[offset + 2] = 20 + Math.floor(grain * 0.35);
    pixels[offset + 3] = 255;
  }
  const texture = new THREE.DataTexture(
    pixels,
    size,
    size,
    THREE.RGBAFormat,
    THREE.UnsignedByteType,
  );
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(9, 12);
  texture.minFilter = THREE.LinearMipmapLinearFilter;
  texture.magFilter = THREE.LinearFilter;
  texture.generateMipmaps = true;
  texture.needsUpdate = true;
  return texture;
}

function surfaceTexture(
  seed: number,
  base: [number, number, number],
  kind: "stone" | "wood" | "concrete" | "fabric",
  repeat: [number, number],
): THREE.DataTexture {
  const size = 128;
  const pixels = new Uint8Array(size * size * 4);
  const random = makeGardenRandom(seed);
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const fine = (random() - 0.5) * 12;
      const stone =
        Math.sin(x * 0.115 + Math.sin(y * 0.067) * 1.8) * 5 +
        Math.sin((x + y) * 0.043) * 7;
      const wood =
        Math.sin(x * 0.42 + Math.sin(y * 0.055) * 2.7) * 9 +
        Math.sin(x * 0.12) * 5;
      const concrete =
        Math.sin(x * 0.061) * 3 + Math.sin(y * 0.077) * 3 + fine * 0.7;
      const fabric = Math.sin(x * 0.62) * 3 + Math.sin(x * 0.13) * 5;
      const value =
        kind === "wood"
          ? wood + fine * 0.38
          : kind === "stone"
            ? stone + fine
            : kind === "fabric"
              ? fabric + fine * 0.25
              : concrete;
      const offset = (y * size + x) * 4;
      pixels[offset] = Math.max(0, Math.min(255, base[0] + value));
      pixels[offset + 1] = Math.max(0, Math.min(255, base[1] + value * 0.9));
      pixels[offset + 2] = Math.max(0, Math.min(255, base[2] + value * 0.75));
      pixels[offset + 3] = 255;
    }
  }
  const texture = new THREE.DataTexture(
    pixels,
    size,
    size,
    THREE.RGBAFormat,
    THREE.UnsignedByteType,
  );
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.wrapS = THREE.MirroredRepeatWrapping;
  texture.wrapT = THREE.MirroredRepeatWrapping;
  texture.repeat.set(...repeat);
  texture.minFilter = THREE.LinearMipmapLinearFilter;
  texture.magFilter = THREE.LinearFilter;
  texture.generateMipmaps = true;
  texture.needsUpdate = true;
  return texture;
}

function irregularStoneGeometry(
  radiusX: number,
  radiusZ: number,
  random: () => number,
): THREE.ExtrudeGeometry {
  const shape = new THREE.Shape();
  const count = 11;
  for (let index = 0; index < count; index += 1) {
    const angle = (index / count) * Math.PI * 2;
    const edge = 0.88 + random() * 0.2;
    const x = Math.cos(angle) * radiusX * edge;
    const z = Math.sin(angle) * radiusZ * edge;
    if (index === 0) shape.moveTo(x, z);
    else shape.lineTo(x, z);
  }
  shape.closePath();
  const geometry = new THREE.ExtrudeGeometry(shape, {
    depth: 0.13,
    bevelEnabled: true,
    bevelSegments: 2,
    bevelSize: 0.055,
    bevelThickness: 0.035,
  });
  geometry.rotateX(Math.PI / 2);
  geometry.computeVertexNormals();
  return geometry;
}

class LanternGardenScene implements AtmosphereScene {
  private readonly scene = new THREE.Scene();
  private readonly camera = new THREE.PerspectiveCamera(44, 1, 0.1, 130);
  private readonly renderer: THREE.WebGLRenderer;
  private readonly composer: EffectComposer;
  private readonly bloomPass: UnrealBloomPass;
  private readonly outputPass: OutputPass;
  private readonly layoutRandom: () => number;
  private readonly motionRandom: () => number;
  private readonly cameraTarget = new THREE.Vector3(
    CAMERA_TARGET_X,
    CAMERA_TARGET_Y,
    CAMERA_TARGET_Z,
  );
  private readonly textures: THREE.Texture[] = [];
  private readonly lanterns: LanternEmitter[] = [];
  private readonly canopyGroups: THREE.Group[] = [];
  private readonly poolRings: PoolRing[] = [];
  private readonly drizzleDrops: DrizzleDrop[] = [];
  private readonly lanternDrizzleDrops: DrizzleDrop[] = [];
  private glowTexture!: THREE.DataTexture;
  private drips!: THREE.Points<THREE.BufferGeometry, THREE.PointsMaterial>;
  private drizzle!: THREE.InstancedMesh;
  private lanternDrizzle!: THREE.InstancedMesh;
  private poolWater!: THREE.Mesh<
    THREE.BufferGeometry,
    THREE.MeshPhysicalMaterial
  >;
  private lastElapsed = 0;
  private reducedMotion: boolean;
  private destroyed = false;

  constructor(context: AtmosphereSceneContext) {
    this.layoutRandom = makeGardenRandom(context.seed);
    this.motionRandom = makeGardenRandom(context.seed ^ 0x9e3779b9);
    this.reducedMotion = context.reducedMotion;
    this.renderer = new THREE.WebGLRenderer({
      canvas: context.canvas,
      antialias: true,
      alpha: false,
      depth: true,
      powerPreference: "high-performance",
    });
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.34;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    this.composer = new EffectComposer(this.renderer);
    this.composer.addPass(new RenderPass(this.scene, this.camera));
    this.bloomPass = new UnrealBloomPass(
      new THREE.Vector2(1, 1),
      0.42,
      0.76,
      0.74,
    );
    this.composer.addPass(this.bloomPass);
    this.outputPass = new OutputPass();
    this.composer.addPass(this.outputPass);

    this.scene.background = new THREE.Color(0x06100d);
    this.scene.fog = new THREE.FogExp2(0x07110e, 0.024);
    this.camera.position.set(CAMERA_X, CAMERA_Y, CAMERA_Z);
    this.camera.lookAt(this.cameraTarget);

    this.buildLights();
    this.buildGround();
    this.buildFence();
    this.buildHouseEdge();
    this.buildPoolEdge();
    this.buildPlanting();
    this.buildLanterns();
    this.buildDrizzle();
    this.buildDrips();
  }

  private buildLights(): void {
    this.scene.add(new THREE.HemisphereLight(0x526b66, 0x120b07, 1.18));
    const moon = new THREE.DirectionalLight(0x8eaaa4, 0.86);
    moon.position.set(-14, 22, 12);
    moon.castShadow = true;
    moon.shadow.mapSize.set(1024, 1024);
    moon.shadow.camera.left = -24;
    moon.shadow.camera.right = 24;
    moon.shadow.camera.top = 24;
    moon.shadow.camera.bottom = -24;
    this.scene.add(moon);

    const houseLight = new THREE.PointLight(0xffbd73, 4, 20, 1.9);
    houseLight.position.set(-13.8, 5.3, -17.8);
    this.scene.add(houseLight);
  }

  private buildGround(): void {
    const mulchTexture = groundTexture(0x4d554c43);
    const concreteTexture = surfaceTexture(
      0x50415449,
      [194, 199, 196],
      "concrete",
      [4, 2],
    );
    const stoneTexture = surfaceTexture(
      0x53544f4e,
      [210, 207, 194],
      "stone",
      [1.7, 1.7],
    );
    this.textures.push(mulchTexture, concreteTexture, stoneTexture);
    const soil = new THREE.Mesh(
      new THREE.PlaneGeometry(70, 82),
      new THREE.MeshStandardMaterial({
        color: 0x5d5141,
        map: mulchTexture,
        bumpMap: mulchTexture,
        bumpScale: 0.075,
        roughness: 0.91,
      }),
    );
    soil.rotation.x = -Math.PI / 2;
    soil.position.set(0, -0.12, -16);
    soil.receiveShadow = true;
    this.scene.add(soil);

    const patioMaterial = new THREE.MeshPhysicalMaterial({
      color: 0x6d7772,
      map: concreteTexture,
      bumpMap: concreteTexture,
      bumpScale: 0.024,
      roughness: 0.68,
      metalness: 0.04,
      clearcoat: 0.56,
      clearcoatRoughness: 0.46,
    });
    const patio = new THREE.Mesh(
      new THREE.PlaneGeometry(34, 12),
      patioMaterial,
    );
    patio.rotation.x = -Math.PI / 2;
    patio.position.set(-1, 0, 10.9);
    patio.receiveShadow = true;
    this.scene.add(patio);

    const seamMaterial = new THREE.MeshBasicMaterial({
      color: 0x111918,
      transparent: true,
      opacity: 0.75,
    });
    for (const x of [-9.4, -1.6, 6.5]) {
      box(this.scene, [0.045, 0.008, 12], [x, 0.012, 10.9], seamMaterial);
    }
    for (const z of [6.8, 11.2, 15.1]) {
      box(this.scene, [34, 0.008, 0.045], [-1, 0.012, z], seamMaterial);
    }

    const wetGlintMaterial = new THREE.MeshBasicMaterial({
      color: 0xb8d1c7,
      transparent: true,
      opacity: 0.052,
      depthWrite: false,
    });
    for (let index = 0; index < 34; index += 1) {
      const glint = new THREE.Mesh(
        new THREE.PlaneGeometry(
          0.12 + this.layoutRandom() * 0.8,
          0.012 + this.layoutRandom() * 0.035,
        ),
        wetGlintMaterial,
      );
      glint.rotation.x = -Math.PI / 2;
      glint.position.set(
        -15 + this.layoutRandom() * 30,
        0.018,
        6 + this.layoutRandom() * 9,
      );
      this.scene.add(glint);
    }

    const stonePalette = [0xbca882, 0xaa9878, 0xc3ae88, 0xa99778];
    const stoneMaterials = stonePalette.map(
      (color) =>
        new THREE.MeshPhysicalMaterial({
          color,
          map: stoneTexture,
          bumpMap: stoneTexture,
          bumpScale: 0.035,
          roughness: 0.5,
          metalness: 0.018,
          clearcoat: 0.58,
          clearcoatRoughness: 0.38,
        }),
    );
    const path: Array<[number, number, number, number]> = [
      [-3.0, 6.2, 2.35, 1.42],
      [-1.8, 3.5, 2.0, 1.3],
      [-3.9, 0.75, 2.25, 1.28],
      [-2.25, -2.2, 1.95, 1.2],
      [-4.15, -5.0, 2.12, 1.16],
      [-2.85, -7.8, 1.82, 1.07],
      [-4.05, -10.45, 1.68, 0.98],
      [-3.15, -12.9, 1.48, 0.9],
      [-3.75, -15.15, 1.28, 0.78],
      [-3.25, -17.25, 1.1, 0.66],
    ];
    for (let index = 0; index < path.length; index += 1) {
      const [x, z, width, depth] = path[index];
      const material = stoneMaterials[index % stoneMaterials.length];
      const stone = new THREE.Mesh(
        irregularStoneGeometry(width * 0.62, depth * 0.66, this.layoutRandom),
        material,
      );
      stone.position.set(x, 0.085 + this.layoutRandom() * 0.018, z);
      stone.rotation.y = (this.layoutRandom() - 0.5) * 0.18;
      stone.castShadow = true;
      stone.receiveShadow = true;
      this.scene.add(stone);
    }

    const twigGeometry = new THREE.CylinderGeometry(0.018, 0.025, 1, 5);
    const twigMaterial = new THREE.MeshStandardMaterial({
      color: 0x4b3423,
      roughness: 0.96,
    });
    const twigs = new THREE.InstancedMesh(twigGeometry, twigMaterial, 170);
    const matrix = new THREE.Matrix4();
    const quaternion = new THREE.Quaternion();
    const scale = new THREE.Vector3();
    for (let index = 0; index < 170; index += 1) {
      const side = index % 2 === 0 ? -1 : 1;
      const x = -3 + side * (2.2 + this.layoutRandom() * 10.5);
      const z = 6.7 - this.layoutRandom() * 26;
      quaternion.setFromEuler(
        new THREE.Euler(
          Math.PI / 2 + (this.layoutRandom() - 0.5) * 0.2,
          this.layoutRandom() * Math.PI,
          (this.layoutRandom() - 0.5) * 0.2,
        ),
      );
      scale.set(1, 0.12 + this.layoutRandom() * 0.48, 1);
      matrix.compose(new THREE.Vector3(x, 0.015, z), quaternion, scale);
      twigs.setMatrixAt(index, matrix);
    }
    this.scene.add(twigs);

    const pebbleGeometry = new THREE.IcosahedronGeometry(0.075, 1);
    const pebbleMaterial = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      vertexColors: true,
      roughness: 0.78,
    });
    const pebbles = new THREE.InstancedMesh(
      pebbleGeometry,
      pebbleMaterial,
      260,
    );
    const pebbleColors = [0x7d7669, 0x999180, 0x68665f, 0xb0a58f];
    const pebbleColor = new THREE.Color();
    for (let index = 0; index < 260; index += 1) {
      const x = 4.2 + this.layoutRandom() * 14.8;
      const z = 3.8 - this.layoutRandom() * 20.5;
      quaternion.setFromEuler(
        new THREE.Euler(
          this.layoutRandom() * Math.PI,
          this.layoutRandom() * Math.PI,
          this.layoutRandom() * Math.PI,
        ),
      );
      scale.set(
        0.65 + this.layoutRandom() * 1.3,
        0.38 + this.layoutRandom() * 0.58,
        0.62 + this.layoutRandom() * 1.15,
      );
      matrix.compose(new THREE.Vector3(x, 0.005, z), quaternion, scale);
      pebbles.setMatrixAt(index, matrix);
      pebbleColor.setHex(
        pebbleColors[Math.floor(this.layoutRandom() * pebbleColors.length)],
      );
      pebbles.setColorAt(index, pebbleColor);
    }
    pebbles.instanceMatrix.needsUpdate = true;
    if (pebbles.instanceColor) pebbles.instanceColor.needsUpdate = true;
    pebbles.receiveShadow = true;
    this.scene.add(pebbles);
  }

  private buildFence(): void {
    const fence = new THREE.Group();
    fence.position.z = -20.8;
    const woodTexture = surfaceTexture(
      0x47415445,
      [198, 178, 148],
      "wood",
      [1, 3.6],
    );
    this.textures.push(woodTexture);
    const boardColors = [0x805a3a, 0x8a6140, 0x745034, 0x936a45];
    for (let index = 0; index < 38; index += 1) {
      const material = new THREE.MeshStandardMaterial({
        color: boardColors[index % boardColors.length],
        map: woodTexture,
        bumpMap: woodTexture,
        bumpScale: 0.028,
        roughness: 0.82,
      });
      const height = 5.25 + (this.layoutRandom() - 0.5) * 0.13;
      box(
        fence,
        [0.93, height, 0.3],
        [-17.6 + index * 0.95, height / 2, 0],
        material,
      );
    }
    const railMaterial = new THREE.MeshStandardMaterial({
      color: 0x51351f,
      map: woodTexture,
      bumpMap: woodTexture,
      bumpScale: 0.025,
      roughness: 0.78,
    });
    box(fence, [37, 0.3, 0.46], [0, 1.25, 0.18], railMaterial);
    box(fence, [37, 0.3, 0.46], [0, 4.1, 0.18], railMaterial);

    // The center gate reads through its heavier posts, latch and diagonal.
    box(fence, [0.56, 6.1, 0.58], [-6.25, 3.05, 0.1], railMaterial);
    box(fence, [0.56, 6.1, 0.58], [0.45, 3.05, 0.1], railMaterial);
    beamBetween(
      fence,
      new THREE.Vector3(-5.88, 0.72, 0.26),
      new THREE.Vector3(0.08, 4.72, 0.26),
      0.32,
      0.42,
      railMaterial,
    );
    box(
      fence,
      [0.44, 0.18, 0.18],
      [-5.48, 2.7, 0.42],
      new THREE.MeshStandardMaterial({
        color: 0x1d211f,
        metalness: 0.75,
        roughness: 0.34,
      }),
    );
    this.scene.add(fence);
  }

  private buildHouseEdge(): void {
    const sidingTexture = surfaceTexture(
      0x484f5553,
      [184, 186, 169],
      "wood",
      [1, 5],
    );
    this.textures.push(sidingTexture);
    const siding = new THREE.MeshStandardMaterial({
      color: 0xb8b8a5,
      map: sidingTexture,
      bumpMap: sidingTexture,
      bumpScale: 0.015,
      roughness: 0.8,
    });
    const wall = box(this.scene, [0.7, 8.8, 21], [-15.3, 4.25, 1.8], siding);
    wall.castShadow = true;
    const trim = new THREE.MeshStandardMaterial({
      color: 0xd6d2bc,
      roughness: 0.58,
    });
    box(this.scene, [0.82, 0.18, 21.1], [-14.91, 0.28, 1.8], trim);
    box(this.scene, [0.82, 0.16, 21.1], [-14.91, 4.7, 1.8], trim);
    const sidingShadow = new THREE.MeshBasicMaterial({
      color: 0x5f645a,
      transparent: true,
      opacity: 0.2,
    });
    for (let y = 0.62; y < 8.3; y += 0.44) {
      box(this.scene, [0.014, 0.035, 20.8], [-14.93, y, 1.8], sidingShadow);
    }

    const downspout = new THREE.MeshStandardMaterial({
      color: 0xc7c6b4,
      roughness: 0.42,
      metalness: 0.22,
    });
    box(this.scene, [0.22, 5.7, 0.22], [-14.82, 2.95, 9.3], downspout);
    box(this.scene, [0.22, 0.22, 2.1], [-14.82, 0.22, 10.25], downspout);

    const sconceMetal = new THREE.MeshStandardMaterial({
      color: 0x202521,
      roughness: 0.38,
      metalness: 0.7,
    });
    box(this.scene, [0.18, 0.78, 0.7], [-14.7, 5.55, -4.8], sconceMetal);
    const sconceGlass = new THREE.MeshStandardMaterial({
      color: 0xffdeb0,
      emissive: 0xffb45e,
      emissiveIntensity: 3.7,
      roughness: 0.16,
      toneMapped: false,
    });
    box(this.scene, [0.2, 0.42, 0.42], [-14.58, 5.56, -4.8], sconceGlass);
  }

  private buildPoolEdge(): void {
    const fabricTexture = surfaceTexture(
      0x504f4f4c,
      [174, 185, 181],
      "fabric",
      [9, 1],
    );
    this.textures.push(fabricTexture);
    const wall = new THREE.Mesh(
      new THREE.CylinderGeometry(6, 6, 2.55, 48, 1, true),
      new THREE.MeshStandardMaterial({
        color: 0x3a4644,
        map: fabricTexture,
        bumpMap: fabricTexture,
        bumpScale: 0.02,
        roughness: 0.62,
        metalness: 0.2,
        side: THREE.DoubleSide,
      }),
    );
    wall.scale.z = 0.72;
    wall.position.set(12.2, 1.18, -9.8);
    this.scene.add(wall);

    const rim = new THREE.Mesh(
      new THREE.TorusGeometry(6, 0.15, 10, 64),
      new THREE.MeshStandardMaterial({
        color: 0xa6aaa0,
        roughness: 0.5,
        metalness: 0.14,
      }),
    );
    rim.rotation.x = Math.PI / 2;
    rim.scale.y = 0.72;
    rim.position.set(12.2, 2.48, -9.8);
    this.scene.add(rim);

    this.poolWater = new THREE.Mesh(
      new THREE.CircleGeometry(5.83, 64),
      new THREE.MeshPhysicalMaterial({
        color: 0x153c42,
        emissive: 0x071a1b,
        emissiveIntensity: 0.2,
        roughness: 0.08,
        metalness: 0.06,
        clearcoat: 1,
        clearcoatRoughness: 0.11,
        transparent: true,
        opacity: 0.92,
      }),
    );
    this.poolWater.rotation.x = -Math.PI / 2;
    this.poolWater.scale.y = 0.72;
    this.poolWater.position.set(12.2, 2.51, -9.8);
    this.scene.add(this.poolWater);

    const supportMaterial = new THREE.MeshStandardMaterial({
      color: 0x283330,
      roughness: 0.42,
      metalness: 0.62,
    });
    for (let index = 0; index < 8; index += 1) {
      const angle = Math.PI * (0.12 + (index / 7) * 0.76);
      const x = 12.2 + Math.cos(angle) * 6.2;
      const z = -9.8 + Math.sin(angle) * 4.48;
      beamBetween(
        this.scene,
        new THREE.Vector3(x, 0.08, z + 0.68),
        new THREE.Vector3(x, 2.48, z),
        0.11,
        0.11,
        supportMaterial,
      );
    }

    for (let index = 0; index < 4; index += 1) {
      const ring = new THREE.Mesh(
        new THREE.RingGeometry(0.2, 0.215, 44),
        new THREE.MeshBasicMaterial({
          color: 0x7ba2a0,
          transparent: true,
          opacity: 0,
          side: THREE.DoubleSide,
          depthWrite: false,
        }),
      );
      ring.rotation.x = -Math.PI / 2;
      ring.position.set(
        8.2 + this.layoutRandom() * 7,
        2.625,
        -12.8 + this.layoutRandom() * 6,
      );
      this.scene.add(ring);
      this.poolRings.push({ mesh: ring, phase: index / 4 });
    }
  }

  private addLeafCluster(
    position: THREE.Vector3,
    size: THREE.Vector3,
    count: number,
    leafGeometry: THREE.BufferGeometry,
    leafMaterial: THREE.MeshStandardMaterial,
    palette: readonly number[],
    sways: boolean,
  ): void {
    const group = new THREE.Group();
    group.position.copy(position);
    const core = new THREE.Mesh(
      new THREE.SphereGeometry(1, 18, 12),
      new THREE.MeshStandardMaterial({
        color: 0x13291c,
        roughness: 0.94,
      }),
    );
    core.scale.copy(size).multiplyScalar(0.69);
    core.castShadow = true;
    group.add(core);

    const leaves = new THREE.InstancedMesh(leafGeometry, leafMaterial, count);
    const matrix = new THREE.Matrix4();
    const quaternion = new THREE.Quaternion();
    const scale = new THREE.Vector3();
    const color = new THREE.Color();
    for (let index = 0; index < count; index += 1) {
      const theta = this.layoutRandom() * Math.PI * 2;
      const vertical = this.layoutRandom() * 2 - 1;
      const radial = Math.sqrt(Math.max(0, 1 - vertical * vertical));
      const shell = 0.68 + this.layoutRandom() * 0.4;
      const leafPosition = new THREE.Vector3(
        Math.cos(theta) * radial * size.x * shell,
        vertical * size.y * shell,
        Math.sin(theta) * radial * size.z * shell,
      );
      quaternion.setFromEuler(
        new THREE.Euler(
          this.layoutRandom() * Math.PI,
          this.layoutRandom() * Math.PI,
          this.layoutRandom() * Math.PI,
        ),
      );
      const leafScale = 0.72 + this.layoutRandom() * 0.85;
      scale.set(leafScale * 1.34, leafScale * 0.58, leafScale * 0.78);
      matrix.compose(leafPosition, quaternion, scale);
      leaves.setMatrixAt(index, matrix);
      color.setHex(palette[Math.floor(this.layoutRandom() * palette.length)]);
      color.offsetHSL(
        (this.layoutRandom() - 0.5) * 0.025,
        0,
        (this.layoutRandom() - 0.5) * 0.055,
      );
      leaves.setColorAt(index, color);
    }
    leaves.castShadow = true;
    leaves.receiveShadow = true;
    leaves.instanceMatrix.needsUpdate = true;
    if (leaves.instanceColor) leaves.instanceColor.needsUpdate = true;
    group.add(leaves);
    this.scene.add(group);
    if (sways) this.canopyGroups.push(group);
  }

  private buildPlanting(): void {
    const trunkMaterial = new THREE.MeshStandardMaterial({
      color: 0x33271b,
      roughness: 0.94,
    });
    const leafPalette = [0x245438, 0x2b6240, 0x347049, 0x3d7b50];
    const leafGeometry = new THREE.SphereGeometry(0.095, 7, 5);
    const leafMaterial = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      emissive: 0x041109,
      emissiveIntensity: 0.14,
      vertexColors: true,
      roughness: 0.87,
    });

    const trees: Array<[number, number, number]> = [
      [-11.2, -14.5, 0.12],
      [-6.9, -24.2, -0.08],
      [5.8, -24.8, 0.05],
      [12.8, -18.8, -0.13],
    ];
    for (let treeIndex = 0; treeIndex < trees.length; treeIndex += 1) {
      const [x, z, lean] = trees[treeIndex];
      const trunk = new THREE.Mesh(
        new THREE.CylinderGeometry(0.27, 0.48, 10.5, 12),
        trunkMaterial,
      );
      trunk.position.set(x, 4.5, z);
      trunk.rotation.z = lean;
      trunk.castShadow = true;
      this.scene.add(trunk);
      for (let branch = 0; branch < 4; branch += 1) {
        const direction = branch % 2 === 0 ? -1 : 1;
        beamBetween(
          this.scene,
          new THREE.Vector3(x, 6.2 + branch * 0.45, z),
          new THREE.Vector3(
            x + direction * (1.8 + branch * 0.28),
            8.1 + branch * 0.38,
            z + (this.layoutRandom() - 0.5) * 2.4,
          ),
          0.18,
          0.2,
          trunkMaterial,
        );
      }
      for (let crown = 0; crown < 4; crown += 1) {
        this.addLeafCluster(
          new THREE.Vector3(
            x + (crown - 1.5) * 1.65,
            8.6 + (crown % 2) * 1.25,
            z + (this.layoutRandom() - 0.5) * 2.4,
          ),
          new THREE.Vector3(2.35, 1.45, 1.9),
          164,
          leafGeometry,
          leafMaterial,
          leafPalette,
          true,
        );
      }
    }

    const shrubs: Array<[number, number, number, number, number]> = [
      [-10.0, 5.2, 1.7, 0.62, 1.25],
      [-7.6, 3.2, 1.25, 0.52, 0.95],
      [-9.2, 0.2, 1.55, 0.68, 1.15],
      [-7.4, -3.0, 1.35, 0.58, 1.0],
      [-9.0, -6.5, 1.55, 0.66, 1.18],
      [-7.2, -10.3, 1.3, 0.54, 0.98],
      [-8.7, -14.2, 1.42, 0.6, 1.08],
      [4.3, 5.0, 1.25, 0.58, 0.98],
      [6.5, 2.3, 1.65, 0.72, 1.25],
      [4.6, -0.8, 1.4, 0.62, 1.08],
      [6.2, -3.7, 1.6, 0.67, 1.22],
      [4.8, -7.1, 1.3, 0.54, 0.98],
      [5.8, -10.5, 1.48, 0.62, 1.1],
      [4.4, -14.1, 1.18, 0.5, 0.9],
    ];
    for (const [x, z, width, height, depth] of shrubs) {
      this.addLeafCluster(
        new THREE.Vector3(x, height * 0.78, z),
        new THREE.Vector3(width, height, depth),
        88,
        leafGeometry,
        leafMaterial,
        leafPalette,
        false,
      );
    }

    // One detailed violet planting echoes the only bright color in the source.
    const flowerCount = 20;
    const stemGeometry = new THREE.CylinderGeometry(0.012, 0.018, 1, 6);
    const stems = new THREE.InstancedMesh(
      stemGeometry,
      new THREE.MeshStandardMaterial({ color: 0x31543b, roughness: 0.9 }),
      flowerCount,
    );
    const petalGeometry = new THREE.SphereGeometry(0.075, 8, 5);
    const petals = new THREE.InstancedMesh(
      petalGeometry,
      new THREE.MeshStandardMaterial({
        color: 0xffffff,
        vertexColors: true,
        roughness: 0.68,
      }),
      flowerCount * 5,
    );
    const matrix = new THREE.Matrix4();
    const quaternion = new THREE.Quaternion();
    const petalScale = new THREE.Vector3(1, 0.42, 0.62);
    const flowerColors = [0x9172ba, 0xab8ace, 0x77599f];
    const color = new THREE.Color();
    for (let flower = 0; flower < flowerCount; flower += 1) {
      const x = -0.4 + (this.layoutRandom() - 0.5) * 1.8;
      const z = 5.0 + (this.layoutRandom() - 0.5) * 1.35;
      const height = 0.34 + this.layoutRandom() * 0.48;
      matrix.compose(
        new THREE.Vector3(x, height / 2, z),
        quaternion.identity(),
        new THREE.Vector3(1, height, 1),
      );
      stems.setMatrixAt(flower, matrix);
      for (let petal = 0; petal < 5; petal += 1) {
        const angle = (petal / 5) * Math.PI * 2;
        quaternion.setFromEuler(new THREE.Euler(0, -angle, angle * 0.12));
        matrix.compose(
          new THREE.Vector3(
            x + Math.cos(angle) * 0.075,
            height + Math.sin(angle) * 0.075,
            z,
          ),
          quaternion,
          petalScale,
        );
        const instance = flower * 5 + petal;
        petals.setMatrixAt(instance, matrix);
        color.setHex(flowerColors[flower % flowerColors.length]);
        petals.setColorAt(instance, color);
      }
    }
    stems.instanceMatrix.needsUpdate = true;
    petals.instanceMatrix.needsUpdate = true;
    if (petals.instanceColor) petals.instanceColor.needsUpdate = true;
    this.scene.add(stems, petals);
  }

  private buildLanterns(): void {
    this.glowTexture = radialGlowTexture();
    const metal = new THREE.MeshStandardMaterial({
      color: 0x151a18,
      roughness: 0.42,
      metalness: 0.72,
    });
    for (let index = 0; index < LANTERN_POSITIONS.length; index += 1) {
      const [x, height, z] = LANTERN_POSITIONS[index];
      const group = new THREE.Group();
      group.position.set(x, 0, z);
      const stake = new THREE.Mesh(
        new THREE.CylinderGeometry(0.045, 0.06, height, 8),
        metal,
      );
      stake.position.y = height / 2;
      group.add(stake);
      const bottom = new THREE.Mesh(
        new THREE.CylinderGeometry(0.2, 0.2, 0.065, 8),
        metal,
      );
      bottom.position.y = height + 0.08;
      group.add(bottom);
      const roof = new THREE.Mesh(
        new THREE.CylinderGeometry(0.1, 0.24, 0.13, 8),
        metal,
      );
      roof.position.y = height + 0.54;
      group.add(roof);
      const cap = new THREE.Mesh(
        new THREE.CylinderGeometry(0.12, 0.12, 0.055, 8),
        metal,
      );
      cap.position.y = height + 0.63;
      group.add(cap);
      for (let post = 0; post < 6; post += 1) {
        const angle = (post / 6) * Math.PI * 2;
        const upright = new THREE.Mesh(
          new THREE.CylinderGeometry(0.014, 0.014, 0.4, 5),
          metal,
        );
        upright.position.set(
          Math.cos(angle) * 0.17,
          height + 0.31,
          Math.sin(angle) * 0.17,
        );
        group.add(upright);
      }
      const glass = new THREE.MeshStandardMaterial({
        color: 0xffd394,
        emissive: 0xffa943,
        emissiveIntensity: 3.2,
        transparent: true,
        opacity: 0.86,
        roughness: 0.18,
        toneMapped: false,
      });
      const bulb = new THREE.Mesh(
        new THREE.CylinderGeometry(0.13, 0.15, 0.34, 12),
        glass,
      );
      bulb.position.y = height + 0.31;
      group.add(bulb);

      const haloMaterial = new THREE.SpriteMaterial({
        color: 0xffbd70,
        map: this.glowTexture,
        transparent: true,
        opacity: 0.32,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        toneMapped: false,
      });
      const halo = new THREE.Sprite(haloMaterial);
      const apparentScale = 1.28 - index * 0.05;
      halo.scale.set(apparentScale, apparentScale, 1);
      halo.position.y = height + 0.31;
      group.add(halo);

      const light =
        index < 5
          ? new THREE.PointLight(0xffb25b, 2.8 - index * 0.14, 5.8, 2)
          : null;
      if (light) {
        light.position.set(x, height + 0.33, z);
        this.scene.add(light);
      }
      const groundGlow = new THREE.Mesh(
        new THREE.PlaneGeometry(3.4, 3.4),
        new THREE.MeshBasicMaterial({
          color: 0xffa94e,
          map: this.glowTexture,
          transparent: true,
          opacity: 0.105 * (1 - index * 0.055),
          depthWrite: false,
          blending: THREE.AdditiveBlending,
          toneMapped: false,
        }),
      );
      groundGlow.rotation.x = -Math.PI / 2;
      groundGlow.position.set(x, 0.018, z);
      groundGlow.scale.setScalar(1 - index * 0.045);
      this.scene.add(groundGlow);
      this.scene.add(group);
      this.lanterns.push({
        glass,
        halo,
        groundGlow,
        light,
        phase: this.layoutRandom() * Math.PI * 2,
        strength: 1 - index * 0.035,
      });
    }
  }

  private buildDrizzle(): void {
    const buildField = (
      count: number,
      warm: boolean,
      drops: DrizzleDrop[],
    ): THREE.InstancedMesh => {
      const geometry = new THREE.PlaneGeometry(
        warm ? 0.007 : 0.004,
        warm ? 0.105 : 0.072,
      );
      const material = new THREE.MeshBasicMaterial({
        color: warm ? 0xffd08a : 0x9eb4b0,
        transparent: true,
        opacity: warm ? 0.11 : 0.04,
        depthWrite: false,
        side: THREE.DoubleSide,
        blending: warm ? THREE.AdditiveBlending : THREE.NormalBlending,
        toneMapped: false,
      });
      const mesh = new THREE.InstancedMesh(geometry, material, count);
      const matrix = new THREE.Matrix4();
      for (let index = 0; index < count; index += 1) {
        let x: number;
        let z: number;
        let y: number;
        if (warm) {
          const lantern =
            LANTERN_POSITIONS[
              Math.floor(this.motionRandom() * LANTERN_POSITIONS.length)
            ];
          x = lantern[0] + (this.motionRandom() - 0.5) * 2.5;
          z = lantern[2] + (this.motionRandom() - 0.5) * 2.2;
          y = 0.18 + this.motionRandom() * 3.6;
        } else {
          x = -18 + this.motionRandom() * 36;
          z = -24 + this.motionRandom() * 38;
          y = 0.3 + this.motionRandom() * 12;
        }
        drops.push({
          originX: x,
          x,
          y,
          z,
          speed: (warm ? 0.72 : 0.58) + this.motionRandom() * 0.72,
          drift: -0.055 + this.motionRandom() * 0.035,
        });
        matrix.makeRotationZ(-0.07);
        matrix.setPosition(x, y, z);
        mesh.setMatrixAt(index, matrix);
      }
      mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
      mesh.instanceMatrix.needsUpdate = true;
      this.scene.add(mesh);
      return mesh;
    };

    this.drizzle = buildField(DRIZZLE_COUNT, false, this.drizzleDrops);
    this.lanternDrizzle = buildField(
      LANTERN_DRIZZLE_COUNT,
      true,
      this.lanternDrizzleDrops,
    );
  }

  private buildDrips(): void {
    const positions = new Float32Array(DRIP_COUNT * 3);
    for (let index = 0; index < DRIP_COUNT; index += 1) {
      positions.set(
        [
          -18 + this.motionRandom() * 36,
          5 + this.motionRandom() * 10,
          -28 + this.motionRandom() * 18,
        ],
        index * 3,
      );
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    const material = new THREE.PointsMaterial({
      color: 0xa7c7c2,
      size: 0.035,
      transparent: true,
      opacity: 0.33,
      depthWrite: false,
    });
    this.drips = new THREE.Points(geometry, material);
    this.scene.add(this.drips);
  }

  private updateLanterns(frame: AtmosphereFrame): void {
    for (const lantern of this.lanterns) {
      const glow = lanternGlowAt(frame.elapsed, lantern.phase);
      lantern.glass.emissiveIntensity = 3.2 * glow;
      lantern.halo.material.opacity = 0.3 * glow * lantern.strength;
      lantern.groundGlow.material.opacity = 0.105 * lantern.strength * glow;
      if (lantern.light) {
        lantern.light.intensity = 2.8 * lantern.strength * glow;
      }
    }
  }

  private updateWater(frame: AtmosphereFrame): void {
    const waterMaterial = this.poolWater.material;
    waterMaterial.emissiveIntensity =
      0.18 + Math.sin(frame.elapsed * 0.34) * 0.025;
    for (const ring of this.poolRings) {
      const progress = (frame.elapsed * 0.085 + ring.phase) % 1;
      const scale = 0.8 + progress * 5.5;
      ring.mesh.scale.setScalar(scale);
      ring.mesh.material.opacity = Math.sin(progress * Math.PI) * 0.11;
    }
  }

  private updateDrips(frame: AtmosphereFrame): void {
    const positions = this.drips.geometry.getAttribute(
      "position",
    ) as THREE.BufferAttribute;
    for (let index = 0; index < DRIP_COUNT; index += 1) {
      let y = positions.getY(index) - frame.delta * (1.9 + (index % 7) * 0.18);
      if (y < 0.2) y = 5.5 + ((index * 2.37) % 8.5);
      positions.setY(index, y);
    }
    positions.needsUpdate = true;
  }

  private updateDrizzle(frame: AtmosphereFrame): void {
    const updateField = (
      mesh: THREE.InstancedMesh,
      drops: DrizzleDrop[],
      height: number,
    ) => {
      const matrix = new THREE.Matrix4();
      for (let index = 0; index < drops.length; index += 1) {
        const drop = drops[index];
        drop.y -= drop.speed * frame.delta;
        drop.x += drop.drift * frame.delta;
        if (drop.y < 0.08) {
          drop.y = height + ((index * 1.618) % height);
          drop.x = drop.originX;
        }
        matrix.makeRotationZ(-0.07 + drop.drift * 0.35);
        matrix.setPosition(drop.x, drop.y, drop.z);
        mesh.setMatrixAt(index, matrix);
      }
      mesh.instanceMatrix.needsUpdate = true;
    };
    updateField(this.drizzle, this.drizzleDrops, 6.5);
    updateField(this.lanternDrizzle, this.lanternDrizzleDrops, 3.8);
  }

  update(frame: AtmosphereFrame): void {
    if (this.destroyed) return;
    this.lastElapsed = frame.elapsed;
    if (!this.reducedMotion) {
      this.updateLanterns(frame);
      this.updateWater(frame);
      this.updateDrips(frame);
      this.updateDrizzle(frame);
      for (let index = 0; index < this.canopyGroups.length; index += 1) {
        const breeze = gardenBreezeAt(frame.elapsed, index * 0.83);
        this.canopyGroups[index].rotation.z = breeze * 0.012;
        this.canopyGroups[index].rotation.x = breeze * 0.004;
      }
    }

    const targetX = CAMERA_X + frame.pointer.x * 0.58;
    const targetY = CAMERA_Y - frame.pointer.y * 0.14;
    this.camera.position.x += (targetX - this.camera.position.x) * 0.024;
    this.camera.position.y += (targetY - this.camera.position.y) * 0.024;
    this.cameraTarget.x = CAMERA_TARGET_X + frame.pointer.x * 0.28;
    this.camera.lookAt(this.cameraTarget);
  }

  setReducedMotion(reducedMotion: boolean): void {
    this.reducedMotion = reducedMotion;
    if (reducedMotion) {
      for (const group of this.canopyGroups) group.rotation.set(0, 0, 0);
      this.updateLanterns({
        delta: 0,
        elapsed: this.lastElapsed,
        pointer: { x: 0, y: 0 },
      });
    }
  }

  resize(viewport: AtmosphereViewport): void {
    if (this.destroyed) return;
    const desiredPixelRatio = Math.min(viewport.devicePixelRatio, 1.25);
    const backingScale = Math.min(
      1,
      MAX_RENDER_WIDTH / (viewport.width * desiredPixelRatio),
      MAX_RENDER_HEIGHT / (viewport.height * desiredPixelRatio),
    );
    const pixelRatio = Math.max(0.72, desiredPixelRatio * backingScale);
    this.renderer.setPixelRatio(pixelRatio);
    this.renderer.setSize(viewport.width, viewport.height, false);
    this.composer.setPixelRatio(pixelRatio);
    this.composer.setSize(viewport.width, viewport.height);
    this.camera.aspect = viewport.width / viewport.height;
    this.camera.updateProjectionMatrix();
  }

  render(): void {
    if (!this.destroyed) this.composer.render();
  }

  dispose(): void {
    if (this.destroyed) return;
    this.destroyed = true;
    disposeScene(this.scene);
    for (const texture of this.textures) texture.dispose();
    this.glowTexture.dispose();
    this.bloomPass.dispose();
    this.outputPass.dispose();
    this.composer.dispose();
    this.renderer.dispose();
  }
}

export function createLanternGardenScene(
  context: AtmosphereSceneContext,
): AtmosphereScene {
  return new LanternGardenScene(context);
}
