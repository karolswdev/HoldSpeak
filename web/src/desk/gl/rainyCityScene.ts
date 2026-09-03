import * as THREE from "three";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import rainyMasonryTextureUrl from "./textures/rainy-masonry.webp";
import wetAsphaltTextureUrl from "./textures/wet-asphalt.webp";
import wetConcreteTextureUrl from "./textures/wet-concrete.webp";
import type {
  AtmosphereFrame,
  AtmosphereScene,
  AtmosphereSceneContext,
  AtmosphereViewport,
} from "./atmosphereRuntime";

const MAX_RENDER_WIDTH = 1_600;
const MAX_RENDER_HEIGHT = 1_000;
const RAIN_COUNT = 790;
const LAMP_RAIN_COUNT = 40;
const NEON_RAIN_COUNT = 34;
const SPLASH_COUNT = 104;
const STEAM_COUNT = 28;
const PUDDLE_Y = 0.035;
const PUDDLE_RADIUS = 2.25;
const PUDDLE_SCALE_X = 1.45;
const PUDDLE_SCALE_Z = 0.5;
const PUDDLE_X = -3.55;
const PUDDLE_Z = 0.8;
const LAMP_X = -6.6;
const LAMP_Z = -5.2;
const BULB_X = -4.75;
const BULB_Y = 5.12;
const LAMP_INTENSITY = 7.5;
const CAMERA_X = 2.55;
const CAMERA_Y = 1.72;
const CAMERA_Z = 15.5;
const CAMERA_TARGET_X = -1.2;
const CAMERA_TARGET_Y = 1.68;
const CAMERA_TARGET_Z = -42;
const NEON_X = 6.88;
const NEON_Y = 2.18;
const NEON_Z = 1.0;

interface RainDrop {
  x: number;
  y: number;
  z: number;
  speed: number;
  length: number;
  drift: number;
}

interface SplashDrop {
  x: number;
  z: number;
  vx: number;
  vy: number;
  vz: number;
  offset: number;
  cycle: number;
  previousLocal: number;
}

interface Ripple {
  mesh: THREE.Mesh<THREE.RingGeometry, THREE.MeshBasicMaterial>;
  offset: number;
  cycle: number;
  previousLocal: number;
}

interface WindowBank {
  material: THREE.MeshBasicMaterial;
  baseOpacity: number;
  phase: number;
}

interface ReflectionStreak {
  mesh: THREE.Mesh<THREE.PlaneGeometry, THREE.MeshBasicMaterial>;
  phase: number;
  baseOpacity: number;
}

interface NeonTube {
  material: THREE.MeshBasicMaterial | THREE.SpriteMaterial;
  baseOpacity: number;
}

/** A deterministic authored seed makes each atmosphere repeatable while a
 * second derived stream keeps weather motion irregular within that world. */
export function makeAtmosphereRandom(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 0x100000000;
  };
}

/** A short double pulse reads as distant lightning without a hard full-screen
 * strobe. Reduced-motion users never advance this weather timeline. */
export function lightningIntensityAt(age: number): number {
  if (age < 0 || age > 1.15) return 0;
  const pulse = (center: number, width: number, strength: number) =>
    Math.max(0, 1 - Math.abs(age - center) / width) * strength;
  return Math.min(
    1,
    pulse(0.08, 0.1, 0.78) + pulse(0.28, 0.075, 0.42) + pulse(0.52, 0.18, 0.88),
  );
}

export function nextLightningDelay(random: () => number): number {
  return 9 + random() * 17;
}

export function steamProgressAt(
  elapsed: number,
  offset: number,
  cycle: number,
): number {
  return ((elapsed + offset) % cycle) / cycle;
}

interface SteamWisp {
  baseX: number;
  baseZ: number;
  cycle: number;
  drift: number;
  offset: number;
  scale: number;
  sprite: THREE.Sprite;
  sway: number;
}

export function nextNeonFlickerDelay(random: () => number): number {
  return 4 + random() * 12;
}

/** A deterministic stepped electrical flutter. The phase is drawn once per
 * event, so frame rate never changes the shape of a flicker. */
export function neonFlickerIntensityAt(age: number, phase: number): number {
  if (age < 0 || age > 0.72) return 1;
  if (age > 0.56) return 0.45 + ((age - 0.56) / 0.16) * 0.55;
  const step = Math.floor(age * 28);
  const value = Math.sin((step + 1) * 12.9898 + phase * 78.233) * 43758.5453;
  const noise = value - Math.floor(value);
  return noise > 0.42 ? 0.94 : 0.08 + noise * 0.28;
}

function disposeScene(scene: THREE.Scene): void {
  const geometries = new Set<THREE.BufferGeometry>();
  const materials = new Set<THREE.Material>();
  scene.traverse((object) => {
    if (
      !(object instanceof THREE.Mesh) &&
      !(object instanceof THREE.Line) &&
      !(object instanceof THREE.Sprite)
    )
      return;
    if (object instanceof THREE.Mesh || object instanceof THREE.Line) {
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
  material: THREE.Material,
): THREE.Mesh {
  const direction = end.clone().sub(start);
  const beam = new THREE.Mesh(
    new THREE.BoxGeometry(thickness, direction.length(), thickness),
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

/** A generated radial falloff keeps the lamp glow resolution-independent and
 * avoids shipping a painted halo asset for an otherwise procedural world. */
function radialGlowTexture(
  size = 64,
  color: [number, number, number] = [255, 174, 78],
  falloffPower = 2.35,
): THREE.DataTexture {
  const pixels = new Uint8Array(size * size * 4);
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const dx = (x + 0.5) / size - 0.5;
      const dy = (y + 0.5) / size - 0.5;
      const distance = Math.sqrt(dx * dx + dy * dy) * 2;
      const falloff = Math.pow(Math.max(0, 1 - distance), falloffPower);
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

function puddleRadius(angle: number, radius: number): number {
  return (
    radius *
    (1 +
      Math.sin(angle * 3 + 0.4) * 0.06 +
      Math.sin(angle * 7 - 0.8) * 0.035 +
      Math.sin(angle * 11 + 1.7) * 0.018)
  );
}

function puddleGeometry(radius: number, segments = 72): THREE.CircleGeometry {
  const geometry = new THREE.CircleGeometry(radius, segments);
  const positions = geometry.getAttribute("position");
  for (let index = 1; index < positions.count; index += 1) {
    const angle = ((index - 1) / segments) * Math.PI * 2;
    const edge = puddleRadius(angle, radius);
    positions.setXY(index, Math.cos(angle) * edge, Math.sin(angle) * edge);
  }
  positions.needsUpdate = true;
  return geometry;
}

function puddleArc(
  radius: number,
  start: number,
  end: number,
  segments = 18,
): THREE.BufferGeometry {
  const points = Array.from({ length: segments + 1 }, (_, index) => {
    const angle = (start + ((end - start) * index) / segments) * Math.PI * 2;
    const edge = puddleRadius(angle, radius);
    return new THREE.Vector3(Math.cos(angle) * edge, Math.sin(angle) * edge, 0);
  });
  return new THREE.BufferGeometry().setFromPoints(points);
}

class RainyCityScene implements AtmosphereScene {
  private readonly scene = new THREE.Scene();
  private readonly camera = new THREE.PerspectiveCamera(46, 1, 0.1, 180);
  private readonly renderer: THREE.WebGLRenderer;
  private readonly composer: EffectComposer;
  private readonly bloomPass: UnrealBloomPass;
  private readonly outputPass: OutputPass;
  private readonly layoutRandom: () => number;
  private readonly weatherRandom: () => number;
  private readonly streetRandom: () => number;
  private readonly neonRandom: () => number;
  private readonly rainDrops: RainDrop[] = [];
  private readonly lampRainDrops: RainDrop[] = [];
  private readonly neonRainDrops: RainDrop[] = [];
  private readonly splashDrops: SplashDrop[] = [];
  private readonly ripples: Ripple[] = [];
  private readonly windowBanks: WindowBank[] = [];
  private readonly reflections: ReflectionStreak[] = [];
  private readonly neonTubes: NeonTube[] = [];
  private readonly surfaceTextures: THREE.Texture[] = [];
  private readonly steamWisps: SteamWisp[] = [];
  private readonly baseSky = new THREE.Color(0x0a1d2d);
  private readonly lightningSky = new THREE.Color(0x7393ad);
  private readonly sky = new THREE.Color();
  private readonly fogBase = new THREE.Color(0x0c2132);
  private readonly fogLightning = new THREE.Color(0x66869f);
  private readonly cameraTarget = new THREE.Vector3(
    CAMERA_TARGET_X,
    CAMERA_TARGET_Y,
    CAMERA_TARGET_Z,
  );
  private readonly lightningBolts: Array<
    THREE.Line<THREE.BufferGeometry, THREE.LineBasicMaterial>
  > = [];
  private rain!: THREE.InstancedMesh;
  private lampRain!: THREE.InstancedMesh;
  private neonRain!: THREE.InstancedMesh;
  private lampGlowTexture!: THREE.DataTexture;
  private neonGlowTexture!: THREE.DataTexture;
  private steamTexture!: THREE.DataTexture;
  private splashes!: THREE.InstancedMesh;
  private hemisphere!: THREE.HemisphereLight;
  private lightning!: THREE.DirectionalLight;
  private lampLight!: THREE.PointLight;
  private neonLight!: THREE.PointLight;
  private readonly beaconMaterial = new THREE.MeshBasicMaterial({
    color: 0xe45f55,
    transparent: true,
    opacity: 0.38,
    toneMapped: false,
  });
  private readonly cloudBank = new THREE.Group();
  private nextLightning = 0;
  private lightningStarted = -1;
  private currentLightning = 0;
  private lastElapsed = 0;
  private nextNeonFlicker = 0;
  private neonFlickerStarted = -1;
  private neonFlickerPhase = 0;
  private currentNeonIntensity = 1;
  private destroyed = false;

  constructor(context: AtmosphereSceneContext) {
    this.layoutRandom = makeAtmosphereRandom(context.seed);
    this.weatherRandom = makeAtmosphereRandom(context.seed ^ 0x9e3779b9);
    this.streetRandom = makeAtmosphereRandom(context.seed ^ 0x6c8e9cf5);
    this.neonRandom = makeAtmosphereRandom(context.seed ^ 0x3c6ef372);
    this.renderer = new THREE.WebGLRenderer({
      canvas: context.canvas,
      antialias: true,
      alpha: false,
      depth: true,
      powerPreference: "high-performance",
    });
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.26;
    this.composer = new EffectComposer(this.renderer);
    this.composer.addPass(new RenderPass(this.scene, this.camera));
    this.bloomPass = new UnrealBloomPass(
      new THREE.Vector2(1, 1),
      0.46,
      0.64,
      0.72,
    );
    this.composer.addPass(this.bloomPass);
    this.outputPass = new OutputPass();
    this.composer.addPass(this.outputPass);
    this.scene.background = this.baseSky.clone();
    this.scene.fog = new THREE.FogExp2(this.fogBase, 0.011);

    this.camera.position.set(CAMERA_X, CAMERA_Y, CAMERA_Z);
    this.camera.lookAt(this.cameraTarget);

    this.buildLights();
    this.buildSkyAndClouds();
    this.buildLightningBolt();
    this.buildStreet();
    this.buildSkyline();
    this.buildLamp();
    this.buildRain();
    this.buildLampRain();
    this.buildNeonRain();
    this.buildSplashes();
    this.buildSteam();
    this.nextLightning = context.reducedMotion
      ? Number.POSITIVE_INFINITY
      : 4.5 + this.weatherRandom() * 4;
    this.nextNeonFlicker = context.reducedMotion
      ? Number.POSITIVE_INFINITY
      : 1.8 + this.neonRandom() * 3.4;
  }

  private buildLights(): void {
    this.hemisphere = new THREE.HemisphereLight(0x7698b1, 0x071019, 1.62);
    this.scene.add(this.hemisphere);

    const moonWash = new THREE.DirectionalLight(0x91aec4, 1.52);
    moonWash.position.set(-18, 32, 14);
    this.scene.add(moonWash);

    this.lightning = new THREE.DirectionalLight(0xbdd9ef, 0);
    this.lightning.position.set(22, 48, -38);
    this.scene.add(this.lightning);
  }

  private loadSurfaceTexture(
    url: string,
    repeat: [number, number],
  ): THREE.Texture {
    const texture = new THREE.TextureLoader().load(url, () => {
      if (!this.destroyed) this.render();
    });
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.wrapS = THREE.MirroredRepeatWrapping;
    texture.wrapT = THREE.MirroredRepeatWrapping;
    texture.repeat.set(...repeat);
    texture.anisotropy = Math.min(
      8,
      this.renderer.capabilities.getMaxAnisotropy(),
    );
    this.surfaceTextures.push(texture);
    return texture;
  }

  private buildSkyAndClouds(): void {
    const cloudMaterial = new THREE.MeshLambertMaterial({
      color: 0x13283a,
      transparent: true,
      opacity: 0.76,
      depthWrite: false,
    });
    for (let index = 0; index < 28; index += 1) {
      const width = 6 + this.layoutRandom() * 14;
      const height = 1.2 + this.layoutRandom() * 2.8;
      const depth = 3 + this.layoutRandom() * 8;
      box(
        this.cloudBank,
        [width, height, depth],
        [
          -48 + this.layoutRandom() * 96,
          24 + this.layoutRandom() * 20,
          -72 + this.layoutRandom() * 42,
        ],
        cloudMaterial,
      );
    }
    this.scene.add(this.cloudBank);
  }

  private buildLightningBolt(): void {
    const addBolt = (points: THREE.Vector3[], opacity: number) => {
      const material = new THREE.LineBasicMaterial({
        color: 0xdaf2ff,
        transparent: true,
        opacity: 0,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        toneMapped: false,
      });
      const bolt = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints(points),
        material,
      );
      bolt.userData.peakOpacity = opacity;
      this.scene.add(bolt);
      this.lightningBolts.push(bolt);
    };

    const main: THREE.Vector3[] = [];
    let x = 18;
    let y = 39;
    for (let index = 0; index < 11; index += 1) {
      main.push(new THREE.Vector3(x, y, -43));
      x += (this.layoutRandom() - 0.48) * 2.7;
      y -= 2.15 + this.layoutRandom() * 1.2;
    }
    addBolt(main, 0.92);
    addBolt(
      [
        main[4].clone(),
        main[4].clone().add(new THREE.Vector3(3.2, -2.7, 0)),
        main[4].clone().add(new THREE.Vector3(5.1, -5.6, 0)),
      ],
      0.56,
    );
    addBolt(
      [
        main[7].clone(),
        main[7].clone().add(new THREE.Vector3(-2.4, -2.1, 0)),
        main[7].clone().add(new THREE.Vector3(-3.6, -4.7, 0)),
      ],
      0.42,
    );
  }

  private buildStreet(): void {
    const asphaltTexture = this.loadSurfaceTexture(
      wetAsphaltTextureUrl,
      [7, 10],
    );
    const concreteTexture = this.loadSurfaceTexture(
      wetConcreteTextureUrl,
      [3, 16],
    );
    const street = new THREE.Mesh(
      new THREE.PlaneGeometry(90, 95),
      new THREE.MeshPhysicalMaterial({
        color: 0xb8c3c7,
        map: asphaltTexture,
        bumpMap: asphaltTexture,
        bumpScale: 0.028,
        roughness: 0.46,
        metalness: 0.08,
        clearcoat: 0.82,
        clearcoatRoughness: 0.28,
      }),
    );
    street.rotation.x = -Math.PI / 2;
    street.position.set(0, 0, -5);
    this.scene.add(street);

    const sidewalkMaterial = new THREE.MeshStandardMaterial({
      color: 0xa4adb0,
      map: concreteTexture,
      bumpMap: concreteTexture,
      bumpScale: 0.022,
      roughness: 0.62,
      metalness: 0.08,
    });
    // The curb runs toward the skyline. With the off-axis camera this strong
    // diagonal is what makes the scene read as a street rather than a stage.
    box(this.scene, [10.4, 0.26, 95], [-12.1, 0.13, -5], sidewalkMaterial);
    box(this.scene, [9.5, 0.22, 95], [11.65, 0.11, -5], sidewalkMaterial);

    const curbMaterial = new THREE.MeshStandardMaterial({
      color: 0x4a5a61,
      roughness: 0.66,
      metalness: 0.18,
    });
    box(this.scene, [0.42, 0.44, 95], [-6.72, 0.22, -5], curbMaterial);
    box(this.scene, [0.34, 0.34, 95], [6.72, 0.17, -5], curbMaterial);

    const curbSeamMaterial = new THREE.MeshBasicMaterial({
      color: 0x80909a,
      transparent: true,
      opacity: 0.11,
    });
    for (let z = -48; z < 40; z += 3.6) {
      box(
        this.scene,
        [9.4, 0.025, 0.035],
        [-12.15, 0.275, z],
        curbSeamMaterial,
      );
      box(
        this.scene,
        [8.7, 0.025, 0.035],
        [11.65, 0.235, z + 1.2],
        curbSeamMaterial,
      );
    }

    const puddle = new THREE.Mesh(
      puddleGeometry(PUDDLE_RADIUS),
      new THREE.MeshPhysicalMaterial({
        color: 0x102f3d,
        emissive: 0x06101a,
        emissiveIntensity: 0.12,
        transparent: true,
        opacity: 0.72,
        roughness: 0.06,
        metalness: 0.05,
        clearcoat: 1,
        clearcoatRoughness: 0.18,
      }),
    );
    puddle.rotation.x = -Math.PI / 2;
    puddle.scale.set(PUDDLE_SCALE_X, PUDDLE_SCALE_Z, 1);
    puddle.position.set(PUDDLE_X, PUDDLE_Y, PUDDLE_Z);
    this.scene.add(puddle);

    // Shallow curb-side pooling broadens the sense of accumulated water
    // without painting another luminous reflection onto the road.
    const runoffMaterial = new THREE.MeshPhysicalMaterial({
      color: 0x153846,
      transparent: true,
      opacity: 0.28,
      roughness: 0.07,
      metalness: 0.04,
      clearcoat: 1,
      clearcoatRoughness: 0.2,
      depthWrite: false,
    });
    const waterPatches: Array<[number, number, number, number]> = [
      [-5.82, -7.3, 1.42, 0.28],
      [5.92, -1.9, 1.16, 0.22],
      [-5.68, 7.4, 1.08, 0.2],
      [5.86, 8.8, 0.86, 0.17],
    ];
    for (const [x, z, scaleX, scaleZ] of waterPatches) {
      const patch = new THREE.Mesh(puddleGeometry(1.08, 48), runoffMaterial);
      patch.rotation.x = -Math.PI / 2;
      patch.scale.set(scaleX, scaleZ, 1);
      patch.position.set(x, PUDDLE_Y - 0.004, z);
      this.scene.add(patch);
    }

    const rimMaterial = new THREE.LineBasicMaterial({
      color: 0x7ba5b5,
      transparent: true,
      opacity: 0.1,
    });
    const rimSections: Array<[number, number]> = [
      [0.05, 0.17],
      [0.31, 0.45],
      [0.57, 0.68],
      [0.82, 0.93],
    ];
    for (const [start, end] of rimSections) {
      const puddleRim = new THREE.Line(
        puddleArc(PUDDLE_RADIUS, start, end),
        rimMaterial,
      );
      puddleRim.rotation.x = -Math.PI / 2;
      puddleRim.scale.set(PUDDLE_SCALE_X, PUDDLE_SCALE_Z, 1);
      puddleRim.position.set(PUDDLE_X, PUDDLE_Y + 0.012, PUDDLE_Z);
      this.scene.add(puddleRim);
    }

    this.buildWetReflections();
    this.buildStreetFurniture();

    const laneMaterial = new THREE.MeshBasicMaterial({
      color: 0x9ca7ab,
      transparent: true,
      opacity: 0.14,
    });
    for (let z = -44; z <= 16; z += 8.5) {
      const lane = new THREE.Mesh(
        new THREE.PlaneGeometry(0.12, 3.7),
        laneMaterial,
      );
      lane.rotation.x = -Math.PI / 2;
      lane.position.set(0.05, 0.018, z);
      this.scene.add(lane);
    }
  }

  private buildStreetFurniture(): void {
    const roadMark = new THREE.MeshBasicMaterial({
      color: 0xc8d0cf,
      transparent: true,
      opacity: 0.16,
    });
    for (let z = -19.5; z <= -15.2; z += 0.85) {
      const stripe = new THREE.Mesh(
        new THREE.PlaneGeometry(12.4, 0.42),
        roadMark,
      );
      stripe.rotation.x = -Math.PI / 2;
      stripe.position.set(0, 0.022, z);
      this.scene.add(stripe);
    }

    const darkMetal = new THREE.MeshStandardMaterial({
      color: 0x1a272d,
      roughness: 0.55,
      metalness: 0.62,
    });
    const grateLine = new THREE.MeshBasicMaterial({
      color: 0x89959b,
      transparent: true,
      opacity: 0.22,
    });
    const paintedRed = new THREE.MeshStandardMaterial({
      color: 0x6f2526,
      roughness: 0.64,
      metalness: 0.28,
    });

    // Hydrant and parking meter: small but unmistakable street-scale cues.
    const hydrant = new THREE.Group();
    hydrant.position.set(-8.25, 0.27, 2.9);
    const hydrantBody = new THREE.Mesh(
      new THREE.CylinderGeometry(0.25, 0.3, 0.72, 10),
      paintedRed,
    );
    hydrantBody.position.y = 0.42;
    hydrant.add(hydrantBody);
    box(hydrant, [0.72, 0.18, 0.2], [0, 0.5, 0], paintedRed);
    box(hydrant, [0.46, 0.16, 0.46], [0, 0.84, 0], paintedRed);
    this.scene.add(hydrant);

    const meter = new THREE.Group();
    meter.position.set(-8.1, 0.27, -1.8);
    box(meter, [0.1, 2.25, 0.1], [0, 1.12, 0], darkMetal);
    box(meter, [0.48, 0.62, 0.32], [0, 2.22, 0], darkMetal);
    box(
      meter,
      [0.28, 0.16, 0.02],
      [0, 2.3, 0.171],
      new THREE.MeshBasicMaterial({ color: 0x6f9cad }),
    );
    this.scene.add(meter);

    // A grated gutter explicitly locates the puddle beside the curb.
    box(this.scene, [0.72, 0.025, 1.65], [-6.2, 0.028, 4.25], darkMetal);
    for (let z = 3.58; z < 5; z += 0.22) {
      box(this.scene, [0.56, 0.012, 0.055], [-6.2, 0.046, z], grateLine);
    }

    const manhole = new THREE.Mesh(
      new THREE.RingGeometry(0.62, 0.72, 24),
      new THREE.MeshBasicMaterial({
        color: 0x53616a,
        transparent: true,
        opacity: 0.22,
        side: THREE.DoubleSide,
      }),
    );
    manhole.rotation.x = -Math.PI / 2;
    manhole.position.set(2.9, 0.027, 2.8);
    this.scene.add(manhole);

    // A distant signal closes the block and reinforces the vanishing point.
    const signal = new THREE.Group();
    signal.position.set(-6.85, 0.44, -21.6);
    box(signal, [0.12, 6.2, 0.12], [0, 3.1, 0], darkMetal);
    box(signal, [12.35, 0.12, 0.12], [6.12, 5.9, 0], darkMetal);
    box(signal, [0.58, 1.45, 0.5], [11.72, 5.25, 0], darkMetal);
    for (const [y, color] of [
      [5.7, 0x9c2f2e],
      [5.25, 0x8f7128],
      [4.8, 0x3d7656],
    ] as Array<[number, number]>) {
      box(
        signal,
        [0.2, 0.2, 0.025],
        [11.72, y, 0.265],
        new THREE.MeshBasicMaterial({ color, toneMapped: false }),
      );
    }
    this.scene.add(signal);
  }

  private addReflectionGlint(
    color: number,
    baseOpacity: number,
    width: number,
    depth: number,
    x: number,
    z: number,
  ): void {
    const material = new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity: baseOpacity,
      depthWrite: false,
      toneMapped: true,
    });
    const reflection = new THREE.Mesh(
      new THREE.PlaneGeometry(width, depth),
      material,
    );
    reflection.rotation.x = -Math.PI / 2;
    reflection.position.set(x, PUDDLE_Y + 0.014, z);
    this.scene.add(reflection);
    this.reflections.push({
      mesh: reflection,
      phase: this.layoutRandom() * Math.PI * 2,
      baseOpacity,
    });
  }

  private buildWetReflections(): void {
    // Sparse, low-energy sky catches suggest damp aggregate without drawing
    // a second graphic on top of the asphalt.
    const coolColors = [0x355f69, 0x485775, 0x51656d];
    for (let index = 0; index < 28; index += 1) {
      this.addReflectionGlint(
        coolColors[Math.floor(this.layoutRandom() * coolColors.length)],
        0.012 + this.layoutRandom() * 0.018,
        0.08 + this.layoutRandom() * 0.32,
        0.012 + this.layoutRandom() * 0.045,
        -20 + this.layoutRandom() * 40,
        -11 + this.layoutRandom() * 17,
      );
    }
  }

  private buildSkyline(): void {
    const masonryTexture = this.loadSurfaceTexture(
      rainyMasonryTextureUrl,
      [8, 9],
    );
    const facadePalette = [0x172b3a, 0x203849, 0x294457, 0x304e61, 0x38596a];
    const coolWindows: THREE.Matrix4[] = [];
    const warmWindows: THREE.Matrix4[] = [];
    const dimWindows: THREE.Matrix4[] = [];
    const matrix = new THREE.Matrix4();

    const addBuilding = (
      x: number,
      z: number,
      width: number,
      height: number,
      depth: number,
      shade: number,
      windowChance: number,
    ) => {
      const material = new THREE.MeshStandardMaterial({
        color: shade,
        roughness: 0.78,
        metalness: 0.08,
      });
      box(
        this.scene,
        [width, height, depth],
        [x, height / 2 + 0.38, z],
        material,
      );

      const columns = Math.max(2, Math.floor(width / 1.15));
      const floors = Math.max(3, Math.floor(height / 1.25));
      const gapX = width / (columns + 1);
      const gapY = height / (floors + 1);
      for (let floor = 1; floor <= floors; floor += 1) {
        for (let column = 1; column <= columns; column += 1) {
          if (this.layoutRandom() > windowChance) continue;
          const wx = x - width / 2 + gapX * column;
          const wy = 0.38 + gapY * floor;
          matrix.makeTranslation(wx, wy, z + depth / 2 + 0.015);
          const roll = this.layoutRandom();
          (roll > 0.34
            ? coolWindows
            : roll > 0.12
              ? warmWindows
              : dimWindows
          ).push(matrix.clone());
        }
      }

      if (height > 30 && this.layoutRandom() > 0.58) {
        this.buildRooftopDetail(x, height + 0.38, z, width);
      }
    };

    // The distant skyline closes the view beyond the block, while lower
    // foreground façades below run with the street rather than across it.
    const layers = [
      { z: -100, maxHeight: 50, minHeight: 25, chance: 0.17, scale: 1.12 },
      { z: -78, maxHeight: 38, minHeight: 18, chance: 0.24, scale: 1 },
      { z: -58, maxHeight: 25, minHeight: 12, chance: 0.31, scale: 0.9 },
    ];
    for (let layer = 0; layer < layers.length; layer += 1) {
      const band = layers[layer];
      let x = -52 - this.layoutRandom() * 6;
      while (x < 54) {
        const width = (4.2 + this.layoutRandom() * 6.8) * band.scale;
        const height =
          band.minHeight +
          this.layoutRandom() * (band.maxHeight - band.minHeight);
        const depth = 6 + this.layoutRandom() * 7;
        x += width / 2;
        const closesStreet = x - width / 2 < 8 && x + width / 2 > -8;
        if (layer === 0 || !closesStreet) {
          addBuilding(
            x,
            band.z + this.layoutRandom() * 4,
            width,
            height,
            depth,
            facadePalette[
              (layer + Math.floor(this.layoutRandom() * 3)) %
                facadePalette.length
            ],
            band.chance,
          );
        }
        x += width / 2 + 0.8 + this.layoutRandom() * 2.2;
      }
    }

    // A fictional stepped landmark gives the horizon an unmistakably tall-city
    // cadence without copying a branded building.
    const landmark = new THREE.MeshStandardMaterial({
      color: 0x30495f,
      roughness: 0.68,
      metalness: 0.14,
    });
    box(this.scene, [8.5, 32, 8], [-3, 16.4, -96], landmark);
    box(this.scene, [6.1, 12, 6.4], [-3, 38.4, -96], landmark);
    box(this.scene, [3.4, 7, 4.2], [-3, 47.9, -96], landmark);
    box(this.scene, [0.54, 10, 0.54], [-3, 56.4, -96], landmark);
    box(this.scene, [0.9, 0.55, 0.9], [-3, 61.7, -96], this.beaconMaterial);

    const sideRotation = {
      left: new THREE.Quaternion().setFromEuler(
        new THREE.Euler(0, Math.PI / 2, 0),
      ),
      right: new THREE.Quaternion().setFromEuler(
        new THREE.Euler(0, -Math.PI / 2, 0),
      ),
    };
    const canyonSegments = [
      { z: -3, depth: 21, baseHeight: 17 },
      { z: -24, depth: 17, baseHeight: 22 },
      { z: -43, depth: 17, baseHeight: 27 },
    ];
    for (const side of [-1, 1] as const) {
      const faceX = side * 7.05;
      for (let segment = 0; segment < canyonSegments.length; segment += 1) {
        const section = canyonSegments[segment];
        const width = 7.4 + this.layoutRandom() * 2.2;
        const height = section.baseHeight + this.layoutRandom() * 8;
        const centerX = faceX + (side * width) / 2;
        const material = new THREE.MeshStandardMaterial({
          color: side > 0 ? 0x8da2ac : 0x827c79,
          map: masonryTexture,
          bumpMap: masonryTexture,
          bumpScale: 0.035,
          roughness: 0.72,
          metalness: 0.06,
        });
        box(
          this.scene,
          [width, height, section.depth],
          [centerX, height / 2 + 0.38, section.z],
          material,
        );

        const rotation = side < 0 ? sideRotation.left : sideRotation.right;
        for (
          let windowZ = section.z - section.depth / 2 + 1.25;
          windowZ < section.z + section.depth / 2 - 0.8;
          windowZ += 1.65
        ) {
          for (let y = 2.2; y < height - 0.8; y += 1.45) {
            if (this.layoutRandom() > 0.39) continue;
            matrix.compose(
              new THREE.Vector3(faceX - side * 0.018, y, windowZ),
              rotation,
              new THREE.Vector3(2.45, 2.35, 1),
            );
            const roll = this.layoutRandom();
            (roll > 0.3
              ? coolWindows
              : roll > 0.1
                ? warmWindows
                : dimWindows
            ).push(matrix.clone());
          }
        }

        if (segment === 0) {
          for (
            let storefrontZ = section.z - section.depth / 2 + 2;
            storefrontZ < section.z + section.depth / 2 - 1;
            storefrontZ += 3.3
          ) {
            matrix.compose(
              new THREE.Vector3(faceX - side * 0.025, 2.15, storefrontZ),
              rotation,
              new THREE.Vector3(6, 3, 1),
            );
            dimWindows.push(matrix.clone());
            box(
              this.scene,
              [0.075, 1.3, 0.075],
              [faceX - side * 0.045, 2.15, storefrontZ],
              material,
            );
            box(
              this.scene,
              [0.62, 0.16, 2.45],
              [faceX - side * 0.28, 3.3, storefrontZ],
              material,
            );
          }

          // Sills, cornice courses, and drain pipes break the foreground
          // masses into human-scale masonry instead of featureless game-era
          // silhouettes. Their muted highlights become most legible in rain.
          const facadeTrim = new THREE.MeshStandardMaterial({
            color: side > 0 ? 0x344550 : 0x2c3b45,
            roughness: 0.66,
            metalness: 0.16,
          });
          for (let y = 4.25; y < height - 1; y += 4.35) {
            box(
              this.scene,
              [0.11, 0.14, section.depth - 0.5],
              [faceX - side * 0.07, y, section.z],
              facadeTrim,
            );
          }
          for (const offsetZ of [-7.4, 7.1]) {
            box(
              this.scene,
              [0.13, Math.min(height - 1, 15.5), 0.13],
              [
                faceX - side * 0.1,
                Math.min(height, 16.5) / 2,
                section.z + offsetZ,
              ],
              facadeTrim,
            );
          }
        }
      }
    }

    const fireEscape = new THREE.MeshStandardMaterial({
      color: 0x182126,
      roughness: 0.5,
      metalness: 0.72,
    });
    const escapeZ = -11;
    for (const y of [5.7, 9, 12.3]) {
      box(this.scene, [0.82, 0.1, 2.75], [-6.68, y, escapeZ], fireEscape);
      for (const z of [escapeZ - 1.25, escapeZ, escapeZ + 1.25]) {
        box(this.scene, [0.07, 0.9, 0.07], [-6.28, y + 0.48, z], fireEscape);
      }
      box(
        this.scene,
        [0.07, 0.07, 2.55],
        [-6.28, y + 0.9, escapeZ],
        fireEscape,
      );
    }
    for (const y of [6.05, 9.35]) {
      beamBetween(
        this.scene,
        new THREE.Vector3(-6.25, y, escapeZ - 1),
        new THREE.Vector3(-6.25, y + 2.55, escapeZ + 1),
        0.065,
        fireEscape,
      );
    }

    this.addWindowBank(coolWindows, 0x86b3c5, 0.34, 0.4);
    this.addWindowBank(warmWindows, 0xf0b85f, 0.42, 1.7);
    this.addWindowBank(dimWindows, 0x66818d, 0.15, 2.8);
    this.buildNeonAccents();
  }

  private buildRooftopDetail(
    x: number,
    y: number,
    z: number,
    width: number,
  ): void {
    const silhouette = new THREE.MeshLambertMaterial({ color: 0x172534 });
    const offset = (this.layoutRandom() - 0.5) * width * 0.42;
    box(this.scene, [1.7, 1.2, 1.8], [x + offset, y + 0.6, z], silhouette);
    box(this.scene, [0.1, 4.2, 0.1], [x + offset, y + 3.1, z], silhouette);
    if (width > 7) {
      box(this.scene, [2.6, 0.12, 0.12], [x + offset, y + 3.55, z], silhouette);
    }
  }

  private addWindowBank(
    entries: THREE.Matrix4[],
    color: number,
    opacity: number,
    phase: number,
  ): void {
    const geometry = new THREE.PlaneGeometry(0.3, 0.42);
    const material = new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity,
      toneMapped: false,
    });
    const windows = new THREE.InstancedMesh(geometry, material, entries.length);
    entries.forEach((entry, index) => windows.setMatrixAt(index, entry));
    windows.instanceMatrix.needsUpdate = true;
    this.scene.add(windows);
    this.windowBanks.push({ material, baseOpacity: opacity, phase });
  }

  private buildNeonAccents(): void {
    const signs: Array<[number, number, number, number]> = [
      [-15, 11, -27, 0x3eb6c5],
      [22, 16, -36, 0xb764b8],
      [-29, 8, -31, 0xd99045],
    ];
    for (const [x, y, z, color] of signs) {
      const sign = new THREE.Mesh(
        new THREE.PlaneGeometry(2.4, 0.55),
        new THREE.MeshBasicMaterial({
          color,
          transparent: true,
          opacity: 0.72,
          toneMapped: false,
        }),
      );
      sign.position.set(x, y, z);
      this.scene.add(sign);
    }
    this.buildForegroundNeonSign();
  }

  private buildForegroundNeonSign(): void {
    const storefront = new THREE.Group();
    storefront.position.set(NEON_X, NEON_Y, NEON_Z);
    storefront.rotation.y = -Math.PI / 2;

    const recess = new THREE.MeshStandardMaterial({
      color: 0x100e13,
      roughness: 0.34,
      metalness: 0.18,
    });
    const frame = new THREE.MeshStandardMaterial({
      color: 0x263239,
      roughness: 0.46,
      metalness: 0.62,
    });
    const warmGlass = new THREE.MeshBasicMaterial({
      color: 0x9c493c,
      transparent: true,
      opacity: 0.14,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      toneMapped: false,
    });
    box(storefront, [4.15, 3.15, 0.22], [0, 0, -0.08], recess);
    box(storefront, [3.82, 2.82, 0.035], [0, 0, 0.08], warmGlass);

    // A recessed street-level window, with enough joinery and interior depth
    // to read as architecture before the neon ever turns on.
    box(storefront, [4.32, 0.18, 0.24], [0, 1.65, 0.08], frame);
    box(storefront, [4.32, 0.2, 0.24], [0, -1.64, 0.08], frame);
    box(storefront, [0.18, 3.18, 0.24], [-2.07, 0, 0.08], frame);
    box(storefront, [0.18, 3.18, 0.24], [2.07, 0, 0.08], frame);
    box(storefront, [0.1, 2.95, 0.18], [1.35, 0, 0.16], frame);
    box(storefront, [1.35, 0.1, 0.16], [1.35, -0.48, 0.16], frame);

    const awningFabric = new THREE.MeshStandardMaterial({
      color: 0x4b2028,
      roughness: 0.82,
      metalness: 0.02,
    });
    const canopy = box(
      storefront,
      [4.5, 0.16, 1.08],
      [0, 1.78, 0.48],
      awningFabric,
    );
    canopy.rotation.x = -0.08;
    box(storefront, [4.5, 0.32, 0.08], [0, 1.61, 0.98], awningFabric);

    const doorGlass = new THREE.MeshPhysicalMaterial({
      color: 0x20363d,
      transparent: true,
      opacity: 0.62,
      roughness: 0.18,
      metalness: 0.22,
      clearcoat: 0.66,
      clearcoatRoughness: 0.12,
    });
    box(storefront, [1.12, 2.25, 0.045], [1.35, 0.28, 0.25], doorGlass);
    box(
      storefront,
      [0.06, 0.5, 0.06],
      [1.74, 0.2, 0.34],
      new THREE.MeshStandardMaterial({
        color: 0x9b7c55,
        roughness: 0.32,
        metalness: 0.7,
      }),
    );

    const interiorWood = new THREE.MeshStandardMaterial({
      color: 0x5c3028,
      roughness: 0.72,
      metalness: 0.04,
    });
    const bottleGlass = new THREE.MeshStandardMaterial({
      color: 0x284b47,
      emissive: 0x112f2d,
      emissiveIntensity: 0.45,
      roughness: 0.25,
      metalness: 0.14,
    });
    box(storefront, [2.35, 0.12, 0.24], [-0.52, -0.83, 0.02], interiorWood);
    box(storefront, [2.35, 0.09, 0.2], [-0.52, 0.77, 0.01], interiorWood);
    for (let index = 0; index < 7; index += 1) {
      const height = 0.22 + this.layoutRandom() * 0.34;
      box(
        storefront,
        [0.12 + this.layoutRandom() * 0.08, height, 0.09],
        [-1.43 + index * 0.31, 0.94 + height / 2, 0.12],
        bottleGlass,
      );
    }

    const cyan = new THREE.MeshBasicMaterial({
      color: 0x54e7e2,
      transparent: true,
      opacity: 0.94,
      toneMapped: false,
    });
    const coral = new THREE.MeshBasicMaterial({
      color: 0xff668f,
      transparent: true,
      opacity: 0.88,
      toneMapped: false,
    });
    const amber = new THREE.MeshBasicMaterial({
      color: 0xffb45c,
      transparent: true,
      opacity: 0.82,
      toneMapped: false,
    });
    this.neonTubes.push(
      { material: cyan, baseOpacity: 0.94 },
      { material: coral, baseOpacity: 0.88 },
      { material: amber, baseOpacity: 0.82 },
    );

    const addTube = (
      coordinates: Array<[number, number]>,
      material: THREE.MeshBasicMaterial,
      radius = 0.045,
    ) => {
      const curve = new THREE.CatmullRomCurve3(
        coordinates.map(([x, y]) => new THREE.Vector3(x, y, 0.32)),
      );
      storefront.add(
        new THREE.Mesh(
          new THREE.TubeGeometry(curve, 30, radius, 9, false),
          material,
        ),
      );
    };

    // A small hand-bent cup and rising steam live behind the glass. It reads
    // as a late-night cafe window, not a floating app logo or billboard.
    addTube(
      [
        [-1.02, 0.18],
        [-0.96, -0.22],
        [-0.7, -0.53],
        [-0.23, -0.6],
        [0.22, -0.5],
        [0.43, -0.17],
        [0.47, 0.18],
      ],
      cyan,
      0.062,
    );
    addTube(
      [
        [0.46, 0.08],
        [0.79, 0.13],
        [0.92, -0.06],
        [0.83, -0.3],
        [0.5, -0.34],
      ],
      cyan,
      0.055,
    );
    addTube(
      [
        [-0.68, 0.44],
        [-0.78, 0.7],
        [-0.62, 0.97],
        [-0.7, 1.18],
      ],
      coral,
      0.05,
    );
    addTube(
      [
        [-0.17, 0.43],
        [-0.27, 0.73],
        [-0.09, 0.98],
        [-0.16, 1.22],
      ],
      coral,
      0.05,
    );
    box(storefront, [1.78, 0.075, 0.07], [-0.24, -0.76, 0.31], amber);

    // Condensation trails catch only a fraction of the interior light.
    const condensation = new THREE.MeshBasicMaterial({
      color: 0xaed6d8,
      transparent: true,
      opacity: 0.11,
      depthWrite: false,
      toneMapped: false,
    });
    for (let index = 0; index < 9; index += 1) {
      const length = 0.18 + this.layoutRandom() * 0.62;
      box(
        storefront,
        [0.018, length, 0.015],
        [-1.82 + this.layoutRandom() * 3.58, 1.34 - length / 2, 0.38],
        condensation,
      );
    }

    this.neonGlowTexture = radialGlowTexture(64, [255, 255, 255]);
    const addNeonHalo = (
      color: number,
      size: [number, number],
      opacity: number,
    ) => {
      const halo = new THREE.Sprite(
        new THREE.SpriteMaterial({
          map: this.neonGlowTexture,
          color,
          transparent: true,
          opacity,
          depthWrite: false,
          blending: THREE.AdditiveBlending,
          toneMapped: false,
        }),
      );
      halo.position.set(-0.24, 0.18, 0.34);
      halo.scale.set(size[0], size[1], 1);
      storefront.add(halo);
      this.neonTubes.push({
        material: halo.material,
        baseOpacity: opacity,
      });
    };
    addNeonHalo(0x45d6d5, [3.25, 2.45], 0.12);
    addNeonHalo(0xf26086, [2.2, 2.25], 0.07);

    this.neonLight = new THREE.PointLight(0x55d9d5, 2.15, 9, 2);
    this.neonLight.position.set(-0.28, 0.08, 1.35);
    storefront.add(this.neonLight);
    const interiorLight = new THREE.PointLight(0xff8052, 1.8, 6.5, 2);
    interiorLight.position.set(0.75, 0.15, 0.85);
    storefront.add(interiorLight);
    const doorwayLight = new THREE.PointLight(0xffb069, 1.45, 5.2, 2);
    doorwayLight.position.set(0.25, 1.35, 0.95);
    storefront.add(doorwayLight);
    this.scene.add(storefront);
  }

  private buildLamp(): void {
    const structure = new THREE.MeshStandardMaterial({
      color: 0x273943,
      emissive: 0x091116,
      emissiveIntensity: 0.45,
      roughness: 0.62,
      metalness: 0.52,
    });
    const edge = new THREE.MeshStandardMaterial({
      color: 0x556872,
      roughness: 0.5,
      metalness: 0.58,
    });
    const amber = new THREE.MeshStandardMaterial({
      color: 0xffb24f,
      emissive: 0xff7518,
      emissiveIntensity: 3.1,
      roughness: 0.24,
      toneMapped: false,
    });
    const lamp = new THREE.Group();
    lamp.position.set(LAMP_X, 0, LAMP_Z);
    box(lamp, [0.64, 0.2, 0.64], [0, 0.1, 0], edge);

    // A short, segmented swan-neck silhouette reads as street furniture even
    // in the intentionally low-poly treatment—without a backboard-like arm.
    const neckPoints = [
      new THREE.Vector3(0, 0.2, 0),
      new THREE.Vector3(0, 4.12, 0),
      new THREE.Vector3(0.08, 4.52, 0),
      new THREE.Vector3(0.3, 4.86, 0),
      new THREE.Vector3(0.72, 5.12, 0),
      new THREE.Vector3(1.22, 5.22, 0),
      new THREE.Vector3(1.63, 5.13, 0),
    ];
    for (let index = 1; index < neckPoints.length; index += 1) {
      beamBetween(
        lamp,
        neckPoints[index - 1],
        neckPoints[index],
        index === 1 ? 0.27 : 0.23,
        structure,
      );
    }
    box(lamp, [1.0, 0.24, 0.64], [1.61, 5.06, 0], edge).rotation.z = -0.07;
    box(lamp, [0.64, 0.13, 0.46], [1.7, 4.94, 0], amber).rotation.z = -0.07;
    this.scene.add(lamp);

    this.lampGlowTexture = radialGlowTexture();
    const addHalo = (size: number, opacity: number, color: number) => {
      const halo = new THREE.Sprite(
        new THREE.SpriteMaterial({
          map: this.lampGlowTexture,
          color,
          transparent: true,
          opacity,
          depthWrite: false,
          blending: THREE.AdditiveBlending,
          toneMapped: false,
        }),
      );
      halo.position.set(BULB_X, BULB_Y, LAMP_Z + 0.03);
      halo.scale.set(size, size, 1);
      this.scene.add(halo);
    };
    addHalo(2.8, 0.27, 0xffba62);
    addHalo(6.4, 0.075, 0xff8a32);

    this.lampLight = new THREE.PointLight(0xffa43d, LAMP_INTENSITY, 20, 1.9);
    this.lampLight.position.set(BULB_X, BULB_Y, LAMP_Z);
    this.scene.add(this.lampLight);

    const lampWash = new THREE.SpotLight(
      0xffa34b,
      1.2,
      19,
      Math.PI * 0.25,
      0.94,
      1.9,
    );
    lampWash.position.copy(this.lampLight.position);
    lampWash.target.position.set(PUDDLE_X, PUDDLE_Y, PUDDLE_Z + 0.2);
    this.scene.add(lampWash, lampWash.target);
  }

  private buildRain(): void {
    const geometry = new THREE.BoxGeometry(0.018, 1, 0.018);
    const material = new THREE.MeshBasicMaterial({
      color: 0xa2cad8,
      transparent: true,
      opacity: 0.38,
      depthWrite: false,
    });
    this.rain = new THREE.InstancedMesh(geometry, material, RAIN_COUNT);
    this.rain.frustumCulled = false;
    this.scene.add(this.rain);
    for (let index = 0; index < RAIN_COUNT; index += 1) {
      this.rainDrops.push(this.newRainDrop(true));
    }
  }

  private buildLampRain(): void {
    const geometry = new THREE.BoxGeometry(0.025, 1, 0.025);
    const material = new THREE.MeshBasicMaterial({
      color: 0xffddb1,
      transparent: true,
      opacity: 0.42,
      depthWrite: false,
      toneMapped: false,
    });
    this.lampRain = new THREE.InstancedMesh(
      geometry,
      material,
      LAMP_RAIN_COUNT,
    );
    this.lampRain.frustumCulled = false;
    this.scene.add(this.lampRain);
    for (let index = 0; index < LAMP_RAIN_COUNT; index += 1) {
      this.lampRainDrops.push(this.newLampRainDrop(true));
    }
  }

  private buildNeonRain(): void {
    const geometry = new THREE.BoxGeometry(0.026, 1, 0.026);
    const material = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      vertexColors: true,
      transparent: true,
      opacity: 0.62,
      depthWrite: false,
      toneMapped: false,
    });
    this.neonRain = new THREE.InstancedMesh(
      geometry,
      material,
      NEON_RAIN_COUNT,
    );
    this.neonRain.frustumCulled = false;
    this.scene.add(this.neonRain);
    for (let index = 0; index < NEON_RAIN_COUNT; index += 1) {
      this.neonRainDrops.push(this.newNeonRainDrop(true));
      this.neonRain.setColorAt(index, new THREE.Color(0x23474d));
    }
    if (this.neonRain.instanceColor) {
      this.neonRain.instanceColor.needsUpdate = true;
    }
  }

  private newRainDrop(initial = false): RainDrop {
    return {
      x: -30 + this.weatherRandom() * 60,
      y: initial
        ? 0.2 + this.weatherRandom() * 34
        : 28 + this.weatherRandom() * 8,
      z: -65 + this.weatherRandom() * 86,
      speed: 13 + this.weatherRandom() * 17,
      length: 0.28 + this.weatherRandom() * 0.98,
      drift: 0.55 + this.weatherRandom() * 0.85,
    };
  }

  private newLampRainDrop(initial = false): RainDrop {
    return {
      x: BULB_X - 1.65 + this.weatherRandom() * 3.3,
      y: initial
        ? 2.4 + this.weatherRandom() * (BULB_Y + 0.6)
        : BULB_Y + 1 + this.weatherRandom() * 3,
      z: LAMP_Z - 2.4 + this.weatherRandom() * 4.8,
      speed: 10 + this.weatherRandom() * 7,
      length: 0.24 + this.weatherRandom() * 0.52,
      drift: 0.45 + this.weatherRandom() * 0.6,
    };
  }

  private newNeonRainDrop(initial = false): RainDrop {
    return {
      x: NEON_X - 3.45 + this.neonRandom() * 3.25,
      y: initial
        ? 0.38 + this.neonRandom() * 5.25
        : NEON_Y + 3.4 + this.neonRandom() * 1.8,
      z: NEON_Z - 2.5 + this.neonRandom() * 5,
      speed: 10 + this.neonRandom() * 9,
      length: 0.24 + this.neonRandom() * 0.68,
      drift: 0.42 + this.neonRandom() * 0.72,
    };
  }

  private buildSplashes(): void {
    const geometry = new THREE.BoxGeometry(0.045, 0.09, 0.045);
    const material = new THREE.MeshBasicMaterial({
      color: 0xb9e0e7,
      transparent: true,
      opacity: 0.56,
      depthWrite: false,
    });
    this.splashes = new THREE.InstancedMesh(geometry, material, SPLASH_COUNT);
    this.splashes.frustumCulled = false;
    this.scene.add(this.splashes);

    for (let index = 0; index < SPLASH_COUNT; index += 1) {
      const drop: SplashDrop = {
        x: 0,
        z: 0,
        vx: 0,
        vy: 0,
        vz: 0,
        offset: this.weatherRandom() * 3.8,
        cycle: 1.1 + this.weatherRandom() * 2.7,
        previousLocal: -1,
      };
      this.reseedSplash(drop);
      this.splashDrops.push(drop);
    }

    for (let index = 0; index < 10; index += 1) {
      const ring = new THREE.Mesh(
        new THREE.RingGeometry(0.09, 0.12, 32),
        new THREE.MeshBasicMaterial({
          color: 0x8cc4d0,
          transparent: true,
          opacity: 0.3,
          side: THREE.DoubleSide,
          depthWrite: false,
        }),
      );
      ring.rotation.x = -Math.PI / 2;
      this.repositionRipple(ring);
      this.scene.add(ring);
      this.ripples.push({
        mesh: ring,
        offset: this.weatherRandom() * 4.2,
        cycle: 1.8 + this.weatherRandom() * 3.2,
        previousLocal: -1,
      });
    }
  }

  private buildSteam(): void {
    this.steamTexture = radialGlowTexture(64, [202, 218, 222], 1.35);
    for (let index = 0; index < STEAM_COUNT; index += 1) {
      const sprite = new THREE.Sprite(
        new THREE.SpriteMaterial({
          color: 0xb7c8cc,
          map: this.steamTexture,
          transparent: true,
          opacity: 0,
          depthWrite: false,
        }),
      );
      this.scene.add(sprite);
      this.steamWisps.push({
        baseX: 2.9 + (this.streetRandom() - 0.5) * 0.44,
        baseZ: 2.8 + (this.streetRandom() - 0.5) * 0.38,
        cycle: 4.5 + this.streetRandom() * 2.3,
        drift: 0.35 + this.streetRandom() * 0.5,
        offset: this.streetRandom() * 6,
        scale: 0.3 + this.streetRandom() * 0.25,
        sprite,
        sway: this.streetRandom() * Math.PI * 2,
      });
    }
  }

  private puddlePoint(): [number, number] {
    const angle = this.weatherRandom() * Math.PI * 2;
    const radius = Math.sqrt(this.weatherRandom()) * PUDDLE_RADIUS * 0.84;
    return [
      PUDDLE_X + Math.cos(angle) * radius * PUDDLE_SCALE_X,
      PUDDLE_Z + Math.sin(angle) * radius * PUDDLE_SCALE_Z,
    ];
  }

  private reseedSplash(drop: SplashDrop): void {
    const [x, z] = this.puddlePoint();
    const angle = this.weatherRandom() * Math.PI * 2;
    const outward = 0.4 + this.weatherRandom() * 0.92;
    drop.x = x;
    drop.z = z;
    drop.vx = Math.cos(angle) * outward;
    drop.vy = 1.15 + this.weatherRandom() * 1.8;
    drop.vz = Math.sin(angle) * outward;
  }

  private repositionRipple(ring: Ripple["mesh"]): void {
    const [x, z] = this.puddlePoint();
    ring.position.set(x, PUDDLE_Y + 0.021, z);
  }

  private updateRain(frame: AtmosphereFrame): void {
    const transform = new THREE.Object3D();
    const gust =
      0.46 +
      Math.sin(frame.elapsed * 0.27) * 0.16 +
      Math.sin(frame.elapsed * 0.83 + 1.7) * 0.09;
    transform.rotation.z = 0.055 + gust * 0.028;
    for (let index = 0; index < this.rainDrops.length; index += 1) {
      const drop = this.rainDrops[index];
      drop.y -= drop.speed * frame.delta;
      drop.x -= gust * drop.drift * frame.delta;
      if (drop.y < 0 || drop.x < -34) Object.assign(drop, this.newRainDrop());
      transform.position.set(drop.x, drop.y, drop.z);
      const depthScale = drop.z > 2 ? 1.18 : drop.z > -25 ? 0.78 : 0.48;
      transform.scale.set(depthScale, drop.length * depthScale, depthScale);
      transform.updateMatrix();
      this.rain.setMatrixAt(index, transform.matrix);
    }
    this.rain.instanceMatrix.needsUpdate = true;

    // A separate seeded volume catches the lamp's warm light. Keeping it
    // local lets bloom reveal rainfall around the fixture without making the
    // entire storm equally luminous.
    transform.rotation.z = 0.045 + gust * 0.024;
    for (let index = 0; index < this.lampRainDrops.length; index += 1) {
      const drop = this.lampRainDrops[index];
      drop.y -= drop.speed * frame.delta;
      drop.x -= gust * drop.drift * frame.delta;
      if (drop.y < 2.35 || drop.x < BULB_X - 2.2) {
        Object.assign(drop, this.newLampRainDrop());
      }
      transform.position.set(drop.x, drop.y, drop.z);
      transform.scale.set(0.75, drop.length, 0.75);
      transform.updateMatrix();
      this.lampRain.setMatrixAt(index, transform.matrix);
    }
    this.lampRain.instanceMatrix.needsUpdate = true;

    // These drops are not a second weather system: they sample the same gust
    // while crossing a small ellipsoidal volume around the sign. Their color
    // and HDR brightness follow the electrical flicker, so bloom catches only
    // the part of each trajectory that is actually inside neon spill.
    const neonColor = new THREE.Color();
    for (let index = 0; index < this.neonRainDrops.length; index += 1) {
      const drop = this.neonRainDrops[index];
      drop.y -= drop.speed * frame.delta;
      drop.x -= gust * drop.drift * frame.delta;
      if (drop.y < 0.28 || drop.x < NEON_X - 3.8) {
        Object.assign(drop, this.newNeonRainDrop());
      }
      const dx = (drop.x - (NEON_X - 0.75)) / 3;
      const dy = (drop.y - NEON_Y) / 3.1;
      const dz = (drop.z - NEON_Z) / 2.7;
      const influence = Math.max(0, 1 - Math.sqrt(dx * dx + dy * dy + dz * dz));
      transform.position.set(drop.x, drop.y, drop.z);
      transform.scale.set(0.7, drop.length, 0.7);
      transform.updateMatrix();
      this.neonRain.setMatrixAt(index, transform.matrix);
      neonColor
        .setHex(index % 3 === 0 ? 0xef67c6 : 0x56e6eb)
        .multiplyScalar(0.11 + influence * this.currentNeonIntensity * 1.75);
      this.neonRain.setColorAt(index, neonColor);
    }
    this.neonRain.instanceMatrix.needsUpdate = true;
    if (this.neonRain.instanceColor) {
      this.neonRain.instanceColor.needsUpdate = true;
    }
  }

  private updateSplashes(frame: AtmosphereFrame): void {
    const transform = new THREE.Object3D();
    for (let index = 0; index < this.splashDrops.length; index += 1) {
      const drop = this.splashDrops[index];
      const local = (frame.elapsed + drop.offset) % drop.cycle;
      if (drop.previousLocal >= 0 && local < drop.previousLocal) {
        this.reseedSplash(drop);
        drop.cycle = 1.1 + this.weatherRandom() * 2.7;
      }
      drop.previousLocal = local;
      const flight = 0.52;
      if (local < flight) {
        const y = PUDDLE_Y + drop.vy * local - 4.9 * local * local;
        transform.position.set(
          drop.x + drop.vx * local,
          Math.max(PUDDLE_Y, y),
          drop.z + drop.vz * local,
        );
        const scale = 0.55 + (1 - local / flight) * 0.62;
        transform.scale.set(0.65 * scale, 1.15 * scale, 0.65 * scale);
      } else {
        transform.position.set(0, -20, 0);
        transform.scale.setScalar(0.001);
      }
      transform.rotation.set(local * 5, local * 3, local * 4);
      transform.updateMatrix();
      this.splashes.setMatrixAt(index, transform.matrix);
    }
    this.splashes.instanceMatrix.needsUpdate = true;

    for (const ripple of this.ripples) {
      const local = (frame.elapsed + ripple.offset) % ripple.cycle;
      if (ripple.previousLocal >= 0 && local < ripple.previousLocal) {
        this.repositionRipple(ripple.mesh);
        ripple.cycle = 1.8 + this.weatherRandom() * 3.2;
      }
      ripple.previousLocal = local;
      const progress = Math.min(local / 1.35, 1);
      ripple.mesh.scale.setScalar(0.45 + progress * 4.2);
      ripple.mesh.material.opacity = progress < 1 ? 0.28 * (1 - progress) : 0;
    }
  }

  private updateSteam(frame: AtmosphereFrame): void {
    for (const wisp of this.steamWisps) {
      const progress = steamProgressAt(frame.elapsed, wisp.offset, wisp.cycle);
      const fade = Math.sin(progress * Math.PI);
      const curl = Math.sin(frame.elapsed * 0.55 + wisp.sway);
      wisp.sprite.position.set(
        wisp.baseX - progress * wisp.drift + curl * 0.16,
        0.18 + progress * 1.25,
        wisp.baseZ + Math.sin(frame.elapsed * 0.34 + wisp.sway) * 0.12,
      );
      const spread = wisp.scale * (0.65 + progress * 1.5);
      wisp.sprite.scale.set(
        spread * 1.8,
        wisp.scale * (0.52 + progress * 0.8),
        1,
      );
      wisp.sprite.material.rotation = curl * 0.24 + progress * 0.18;
      wisp.sprite.material.opacity = fade * 0.085;
    }
  }

  private updateNeon(frame: AtmosphereFrame): void {
    if (this.neonFlickerStarted < 0 && frame.elapsed >= this.nextNeonFlicker) {
      this.neonFlickerStarted = frame.elapsed;
      this.neonFlickerPhase = this.neonRandom();
    }

    let electrical = 1;
    if (this.neonFlickerStarted >= 0) {
      const age = frame.elapsed - this.neonFlickerStarted;
      electrical = neonFlickerIntensityAt(age, this.neonFlickerPhase);
      if (age > 0.72) {
        this.neonFlickerStarted = -1;
        this.nextNeonFlicker =
          frame.elapsed + nextNeonFlickerDelay(this.neonRandom);
        electrical = 1;
      }
    }

    const transformerHum = 0.975 + Math.sin(frame.elapsed * 2.15) * 0.025;
    this.currentNeonIntensity = electrical * transformerHum;
    for (const emitter of this.neonTubes) {
      emitter.material.opacity =
        emitter.baseOpacity * (0.08 + this.currentNeonIntensity * 0.92);
    }
    this.neonLight.intensity = 2.15 * this.currentNeonIntensity;
  }

  private updateWeather(frame: AtmosphereFrame): void {
    if (this.lightningStarted < 0 && frame.elapsed >= this.nextLightning) {
      this.lightningStarted = frame.elapsed;
    }
    if (this.lightningStarted >= 0) {
      const age = frame.elapsed - this.lightningStarted;
      this.currentLightning = lightningIntensityAt(age);
      if (age > 1.15) {
        this.lightningStarted = -1;
        this.currentLightning = 0;
        this.nextLightning =
          frame.elapsed + nextLightningDelay(this.weatherRandom);
      }
    }

    this.lightning.intensity = this.currentLightning * 5.2;
    this.hemisphere.intensity = 1.62 + this.currentLightning * 1.4;
    this.lampLight.intensity = LAMP_INTENSITY - this.currentLightning * 2.5;
    this.sky.lerpColors(
      this.baseSky,
      this.lightningSky,
      this.currentLightning * 0.5,
    );
    this.scene.background = this.sky;
    for (const bolt of this.lightningBolts) {
      bolt.material.opacity =
        this.currentLightning * Number(bolt.userData.peakOpacity);
      bolt.visible = this.currentLightning > 0.04;
    }
    if (this.scene.fog instanceof THREE.FogExp2) {
      this.scene.fog.color.lerpColors(
        this.fogBase,
        this.fogLightning,
        this.currentLightning * 0.32,
      );
    }

    for (const bank of this.windowBanks) {
      const shimmer = Math.sin(frame.elapsed * 0.38 + bank.phase) * 0.025;
      bank.material.opacity = bank.baseOpacity + shimmer;
    }
    for (const reflection of this.reflections) {
      reflection.mesh.material.opacity =
        reflection.baseOpacity *
        (0.9 + Math.sin(frame.elapsed * 1.35 + reflection.phase) * 0.1);
    }
    const beaconPulse = Math.pow(
      Math.max(0, Math.sin(frame.elapsed * 1.45)),
      8,
    );
    this.beaconMaterial.opacity = 0.18 + beaconPulse * 0.7;
    this.cloudBank.position.x = Math.sin(frame.elapsed * 0.018) * 3.2;
  }

  update(frame: AtmosphereFrame): void {
    if (this.destroyed) return;
    this.lastElapsed = frame.elapsed;
    this.updateNeon(frame);
    this.updateRain(frame);
    this.updateSplashes(frame);
    this.updateSteam(frame);
    this.updateWeather(frame);

    const targetX = CAMERA_X + frame.pointer.x * 0.72;
    const targetY = CAMERA_Y - frame.pointer.y * 0.16;
    this.camera.position.x += (targetX - this.camera.position.x) * 0.022;
    this.camera.position.y += (targetY - this.camera.position.y) * 0.022;
    this.cameraTarget.x = CAMERA_TARGET_X + frame.pointer.x * 0.32;
    this.camera.lookAt(this.cameraTarget);
  }

  setReducedMotion(reducedMotion: boolean): void {
    if (reducedMotion) {
      this.lightningStarted = -1;
      this.currentLightning = 0;
      this.nextLightning = Number.POSITIVE_INFINITY;
      this.lightning.intensity = 0;
      for (const bolt of this.lightningBolts) bolt.visible = false;
      this.neonFlickerStarted = -1;
      this.nextNeonFlicker = Number.POSITIVE_INFINITY;
      this.currentNeonIntensity = 1;
      for (const emitter of this.neonTubes) {
        emitter.material.opacity = emitter.baseOpacity;
      }
      this.neonLight.intensity = 2.15;
    } else {
      this.nextLightning = this.lastElapsed + 4.5 + this.weatherRandom() * 4;
      this.nextNeonFlicker = this.lastElapsed + 1.8 + this.neonRandom() * 3.4;
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
    for (const texture of this.surfaceTextures) texture.dispose();
    this.lampGlowTexture.dispose();
    this.neonGlowTexture.dispose();
    this.steamTexture.dispose();
    this.bloomPass.dispose();
    this.outputPass.dispose();
    this.composer.dispose();
    this.renderer.dispose();
  }
}

export function createRainyCityScene(
  context: AtmosphereSceneContext,
): AtmosphereScene {
  return new RainyCityScene(context);
}
