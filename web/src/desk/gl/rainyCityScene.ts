import * as THREE from "three";
import type {
  AtmosphereFrame,
  AtmosphereScene,
  AtmosphereSceneContext,
  AtmosphereViewport,
} from "./atmosphereRuntime";

const MAX_RENDER_WIDTH = 1_600;
const MAX_RENDER_HEIGHT = 1_000;
const RAIN_COUNT = 720;
const SPLASH_COUNT = 84;
const PUDDLE_Y = 0.035;
const PUDDLE_X = -1.65;
const PUDDLE_Z = 1.8;
const CAMERA_X = 0;
const CAMERA_Y = 2.25;
const CAMERA_Z = 18;

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

function disposeScene(scene: THREE.Scene): void {
  const geometries = new Set<THREE.BufferGeometry>();
  const materials = new Set<THREE.Material>();
  scene.traverse((object) => {
    if (!(object instanceof THREE.Mesh) && !(object instanceof THREE.Line))
      return;
    geometries.add(object.geometry);
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

function puddleContour(radius: number, segments = 72): THREE.BufferGeometry {
  const points = Array.from({ length: segments }, (_, index) => {
    const angle = (index / segments) * Math.PI * 2;
    const edge = puddleRadius(angle, radius);
    return new THREE.Vector3(Math.cos(angle) * edge, Math.sin(angle) * edge, 0);
  });
  return new THREE.BufferGeometry().setFromPoints(points);
}

class RainyCityScene implements AtmosphereScene {
  private readonly scene = new THREE.Scene();
  private readonly camera = new THREE.PerspectiveCamera(50, 1, 0.1, 180);
  private readonly renderer: THREE.WebGLRenderer;
  private readonly layoutRandom: () => number;
  private readonly weatherRandom: () => number;
  private readonly rainDrops: RainDrop[] = [];
  private readonly splashDrops: SplashDrop[] = [];
  private readonly ripples: Ripple[] = [];
  private readonly windowBanks: WindowBank[] = [];
  private readonly reflections: ReflectionStreak[] = [];
  private readonly baseSky = new THREE.Color(0x07131f);
  private readonly lightningSky = new THREE.Color(0x7393ad);
  private readonly sky = new THREE.Color();
  private readonly fogBase = new THREE.Color(0x0a1a2a);
  private readonly fogLightning = new THREE.Color(0x66869f);
  private readonly cameraTarget = new THREE.Vector3(0, 5.3, -31);
  private readonly lightningBolts: Array<
    THREE.Line<THREE.BufferGeometry, THREE.LineBasicMaterial>
  > = [];
  private rain!: THREE.InstancedMesh;
  private splashes!: THREE.InstancedMesh;
  private hemisphere!: THREE.HemisphereLight;
  private lightning!: THREE.DirectionalLight;
  private lampLight!: THREE.PointLight;
  private readonly cloudBank = new THREE.Group();
  private nextLightning = 0;
  private lightningStarted = -1;
  private currentLightning = 0;
  private lastElapsed = 0;
  private destroyed = false;

  constructor(context: AtmosphereSceneContext) {
    this.layoutRandom = makeAtmosphereRandom(context.seed);
    this.weatherRandom = makeAtmosphereRandom(context.seed ^ 0x9e3779b9);
    this.renderer = new THREE.WebGLRenderer({
      canvas: context.canvas,
      antialias: true,
      alpha: false,
      depth: true,
      powerPreference: "high-performance",
    });
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.12;
    this.scene.background = this.baseSky.clone();
    this.scene.fog = new THREE.FogExp2(this.fogBase, 0.0125);

    this.camera.position.set(CAMERA_X, CAMERA_Y, CAMERA_Z);
    this.camera.lookAt(this.cameraTarget);

    this.buildLights();
    this.buildSkyAndClouds();
    this.buildLightningBolt();
    this.buildStreet();
    this.buildSkyline();
    this.buildLamp();
    this.buildRain();
    this.buildSplashes();
    this.nextLightning = context.reducedMotion
      ? Number.POSITIVE_INFINITY
      : 4.5 + this.weatherRandom() * 4;
  }

  private buildLights(): void {
    this.hemisphere = new THREE.HemisphereLight(0x6f91ad, 0x05090e, 1.35);
    this.scene.add(this.hemisphere);

    const moonWash = new THREE.DirectionalLight(0x91aec4, 1.25);
    moonWash.position.set(-18, 32, 14);
    this.scene.add(moonWash);

    this.lightning = new THREE.DirectionalLight(0xbdd9ef, 0);
    this.lightning.position.set(22, 48, -38);
    this.scene.add(this.lightning);
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
    const street = new THREE.Mesh(
      new THREE.PlaneGeometry(90, 95),
      new THREE.MeshStandardMaterial({
        color: 0x0b1721,
        roughness: 0.24,
        metalness: 0.58,
      }),
    );
    street.rotation.x = -Math.PI / 2;
    street.position.set(0, 0, -5);
    this.scene.add(street);

    const sidewalkMaterial = new THREE.MeshStandardMaterial({
      color: 0x172129,
      roughness: 0.72,
      metalness: 0.12,
    });
    box(this.scene, [90, 0.26, 1.15], [0, 0.13, -13.6], sidewalkMaterial);
    box(this.scene, [90, 0.2, 7.5], [0, 0.27, -17.9], sidewalkMaterial);

    const curbSeamMaterial = new THREE.MeshBasicMaterial({
      color: 0x80909a,
      transparent: true,
      opacity: 0.2,
    });
    for (let x = -40; x < 42; x += 2.8) {
      box(this.scene, [0.035, 0.025, 6.7], [x, 0.39, -18], curbSeamMaterial);
    }

    const puddle = new THREE.Mesh(
      puddleGeometry(2.9),
      new THREE.MeshPhysicalMaterial({
        color: 0x0b2638,
        emissive: 0x06101a,
        emissiveIntensity: 0.35,
        transparent: true,
        opacity: 0.88,
        roughness: 0.08,
        metalness: 0.72,
        clearcoat: 0.72,
        clearcoatRoughness: 0.12,
      }),
    );
    puddle.rotation.x = -Math.PI / 2;
    puddle.scale.set(1.45, 0.55, 1);
    puddle.position.set(PUDDLE_X, PUDDLE_Y, PUDDLE_Z);
    this.scene.add(puddle);

    const puddleRim = new THREE.LineLoop(
      puddleContour(2.9),
      new THREE.LineBasicMaterial({
        color: 0x7ba5b5,
        transparent: true,
        opacity: 0.25,
      }),
    );
    puddleRim.rotation.x = -Math.PI / 2;
    puddleRim.scale.set(1.45, 0.55, 1);
    puddleRim.position.set(PUDDLE_X, PUDDLE_Y + 0.012, PUDDLE_Z);
    this.scene.add(puddleRim);

    this.buildWetReflections();

    const laneMaterial = new THREE.MeshBasicMaterial({
      color: 0x9ca7ab,
      transparent: true,
      opacity: 0.14,
    });
    for (let x = -30; x <= 30; x += 8.5) {
      const lane = new THREE.Mesh(
        new THREE.PlaneGeometry(3.7, 0.1),
        laneMaterial,
      );
      lane.rotation.x = -Math.PI / 2;
      lane.position.set(x, 0.018, 10.5);
      this.scene.add(lane);
    }
  }

  private buildWetReflections(): void {
    const colors = [0xff9e38, 0xf4c36a, 0x5ca8b9, 0x7d91bc];
    for (let index = 0; index < 44; index += 1) {
      const warm = index < 22;
      const baseOpacity = warm ? 0.055 + this.layoutRandom() * 0.09 : 0.025;
      const material = new THREE.MeshBasicMaterial({
        color: colors[Math.floor(this.layoutRandom() * colors.length)],
        transparent: true,
        opacity: baseOpacity,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
      });
      const width = 0.05 + this.layoutRandom() * (warm ? 0.24 : 0.12);
      const depth = 0.35 + this.layoutRandom() * (warm ? 3.8 : 2.2);
      const reflection = new THREE.Mesh(
        new THREE.PlaneGeometry(width, depth),
        material,
      );
      reflection.rotation.x = -Math.PI / 2;
      reflection.position.set(
        warm
          ? -5.25 + (this.layoutRandom() - 0.5) * 3.8
          : -20 + this.layoutRandom() * 40,
        PUDDLE_Y + 0.009,
        warm ? -2 + this.layoutRandom() * 7.5 : -11 + this.layoutRandom() * 14,
      );
      this.scene.add(reflection);
      this.reflections.push({
        mesh: reflection,
        phase: this.layoutRandom() * Math.PI * 2,
        baseOpacity,
      });
    }
  }

  private buildSkyline(): void {
    const facadePalette = [0x101f2d, 0x172a3a, 0x1a3042, 0x22384a, 0x293f51];
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

    // Meter-like proportions and overlapping depth bands stop the city from
    // reading as a tabletop model. The nearest roofs disappear above frame.
    const layers = [
      { z: -72, maxHeight: 67, minHeight: 27, chance: 0.18, scale: 1.15 },
      { z: -52, maxHeight: 53, minHeight: 21, chance: 0.27, scale: 1 },
      { z: -34, maxHeight: 40, minHeight: 15, chance: 0.34, scale: 0.88 },
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
        addBuilding(
          x,
          band.z + this.layoutRandom() * 4,
          width,
          height,
          depth,
          facadePalette[
            (layer + Math.floor(this.layoutRandom() * 3)) % facadePalette.length
          ],
          band.chance,
        );
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
    box(this.scene, [9, 38, 8], [8, 19.4, -57], landmark);
    box(this.scene, [6.4, 13, 6.4], [8, 44.9, -57], landmark);
    box(this.scene, [3.5, 8, 4.2], [8, 55.4, -57], landmark);
    box(this.scene, [0.62, 14, 0.62], [8, 66.4, -57], landmark);
    box(
      this.scene,
      [0.9, 0.55, 0.9],
      [8, 73.7, -57],
      new THREE.MeshBasicMaterial({ color: 0xe45f55, toneMapped: false }),
    );

    this.addWindowBank(coolWindows, 0x86b3c5, 0.76, 0.4);
    this.addWindowBank(warmWindows, 0xf0b85f, 0.84, 1.7);
    this.addWindowBank(dimWindows, 0x66818d, 0.4, 2.8);
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
      color: 0xffd07a,
      emissive: 0xff8c2a,
      emissiveIntensity: 4.4,
      roughness: 0.24,
      toneMapped: false,
    });
    const lamp = new THREE.Group();
    lamp.position.set(-7.25, 0, -4.8);
    box(lamp, [0.72, 0.22, 0.72], [0, 0.11, 0], edge);
    box(lamp, [0.28, 7.45, 0.28], [0, 3.84, 0], structure);
    box(lamp, [2.75, 0.24, 0.3], [1.25, 7.47, 0], structure);
    box(lamp, [0.18, 0.9, 0.2], [2.52, 7.08, 0], structure);
    box(lamp, [0.92, 0.22, 0.82], [2.52, 6.67, 0], edge);
    box(lamp, [0.56, 0.28, 0.54], [2.52, 6.43, 0], amber);
    box(lamp, [0.12, 1.15, 0.12], [0.72, 7.03, 0], edge).rotation.z = -0.72;
    this.scene.add(lamp);

    this.lampLight = new THREE.PointLight(0xffa43d, 53, 22, 1.8);
    this.lampLight.position.set(-4.73, 6.36, -4.8);
    this.scene.add(this.lampLight);

    const poolLight = new THREE.PointLight(0xff8f2c, 9, 11, 2);
    poolLight.position.set(PUDDLE_X - 0.7, 0.48, PUDDLE_Z - 0.6);
    this.scene.add(poolLight);

    const cone = new THREE.Mesh(
      new THREE.ConeGeometry(4.5, 6.1, 32, 1, true),
      new THREE.MeshBasicMaterial({
        color: 0xffb559,
        transparent: true,
        opacity: 0.045,
        side: THREE.DoubleSide,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
      }),
    );
    cone.position.set(-4.73, 3.32, -4.8);
    this.scene.add(cone);
  }

  private buildRain(): void {
    const geometry = new THREE.BoxGeometry(0.026, 1, 0.026);
    const material = new THREE.MeshBasicMaterial({
      color: 0xa2cad8,
      transparent: true,
      opacity: 0.47,
      depthWrite: false,
    });
    this.rain = new THREE.InstancedMesh(geometry, material, RAIN_COUNT);
    this.rain.frustumCulled = false;
    this.scene.add(this.rain);
    for (let index = 0; index < RAIN_COUNT; index += 1) {
      this.rainDrops.push(this.newRainDrop(true));
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
      length: 0.45 + this.weatherRandom() * 1.35,
      drift: 0.55 + this.weatherRandom() * 0.85,
    };
  }

  private buildSplashes(): void {
    const geometry = new THREE.BoxGeometry(0.08, 0.14, 0.08);
    const material = new THREE.MeshBasicMaterial({
      color: 0xb9e0e7,
      transparent: true,
      opacity: 0.72,
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

  private puddlePoint(): [number, number] {
    const angle = this.weatherRandom() * Math.PI * 2;
    const radius = Math.sqrt(this.weatherRandom()) * 2.5;
    return [
      PUDDLE_X + Math.cos(angle) * radius * 1.43,
      PUDDLE_Z + Math.sin(angle) * radius * 0.53,
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
    this.hemisphere.intensity = 1.35 + this.currentLightning * 1.4;
    this.lampLight.intensity = 53 - this.currentLightning * 4;
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
        (0.78 + Math.sin(frame.elapsed * 2.1 + reflection.phase) * 0.22);
    }
    this.cloudBank.position.x = Math.sin(frame.elapsed * 0.018) * 3.2;
  }

  update(frame: AtmosphereFrame): void {
    if (this.destroyed) return;
    this.lastElapsed = frame.elapsed;
    this.updateRain(frame);
    this.updateSplashes(frame);
    this.updateWeather(frame);

    const targetX = CAMERA_X + frame.pointer.x * 0.72;
    const targetY = CAMERA_Y - frame.pointer.y * 0.16;
    this.camera.position.x += (targetX - this.camera.position.x) * 0.022;
    this.camera.position.y += (targetY - this.camera.position.y) * 0.022;
    this.cameraTarget.x = frame.pointer.x * 0.32;
    this.camera.lookAt(this.cameraTarget);
  }

  setReducedMotion(reducedMotion: boolean): void {
    if (reducedMotion) {
      this.lightningStarted = -1;
      this.currentLightning = 0;
      this.nextLightning = Number.POSITIVE_INFINITY;
      this.lightning.intensity = 0;
      for (const bolt of this.lightningBolts) bolt.visible = false;
    } else {
      this.nextLightning = this.lastElapsed + 4.5 + this.weatherRandom() * 4;
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
    this.renderer.setPixelRatio(
      Math.max(0.72, desiredPixelRatio * backingScale),
    );
    this.renderer.setSize(viewport.width, viewport.height, false);
    this.camera.aspect = viewport.width / viewport.height;
    this.camera.updateProjectionMatrix();
  }

  render(): void {
    if (!this.destroyed) this.renderer.render(this.scene, this.camera);
  }

  dispose(): void {
    if (this.destroyed) return;
    this.destroyed = true;
    disposeScene(this.scene);
    this.renderer.dispose();
  }
}

export function createRainyCityScene(
  context: AtmosphereSceneContext,
): AtmosphereScene {
  return new RainyCityScene(context);
}
