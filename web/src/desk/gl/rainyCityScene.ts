import * as THREE from "three";

const PIXEL_SCALE = 3;
const MAX_RENDER_WIDTH = 720;
const MAX_RENDER_HEIGHT = 480;
const RAIN_COUNT = 520;
const SPLASH_COUNT = 72;
const PUDDLE_Y = 0.035;
const PUDDLE_X = -1.7;
const PUDDLE_Z = -1.3;

interface RainDrop {
  x: number;
  y: number;
  z: number;
  speed: number;
}

interface SplashDrop {
  x: number;
  z: number;
  vx: number;
  vy: number;
  vz: number;
  offset: number;
  cycle: number;
}

interface Ripple {
  mesh: THREE.Mesh<THREE.RingGeometry, THREE.MeshBasicMaterial>;
  offset: number;
  cycle: number;
}

/** A tiny deterministic generator keeps the skyline stable across reloads. */
function makeRandom(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 0x100000000;
  };
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
    (1 + Math.sin(angle * 3 + 0.4) * 0.055 + Math.sin(angle * 7 - 0.8) * 0.032)
  );
}

function puddleGeometry(radius: number, segments = 48): THREE.CircleGeometry {
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

function puddleContour(radius: number, segments = 48): THREE.BufferGeometry {
  const points = Array.from({ length: segments }, (_, index) => {
    const angle = (index / segments) * Math.PI * 2;
    const edge = puddleRadius(angle, radius);
    return new THREE.Vector3(Math.cos(angle) * edge, Math.sin(angle) * edge, 0);
  });
  return new THREE.BufferGeometry().setFromPoints(points);
}

class RainyCityScene {
  private readonly scene = new THREE.Scene();
  private readonly camera = new THREE.PerspectiveCamera(43, 1, 0.1, 120);
  private readonly renderer: THREE.WebGLRenderer;
  private readonly random = makeRandom(0x484f4c44);
  private readonly clock = new THREE.Clock();
  private readonly rainDrops: RainDrop[] = [];
  private readonly splashDrops: SplashDrop[] = [];
  private readonly ripples: Ripple[] = [];
  private rain!: THREE.InstancedMesh;
  private splashes!: THREE.InstancedMesh;
  private animationFrame = 0;
  private elapsed = 0;
  private reducedMotion = false;
  private destroyed = false;
  private pointerX = 0;
  private pointerY = 0;
  private readonly motionQuery = window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  );

  constructor(private readonly canvas: HTMLCanvasElement) {
    this.renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: false,
      alpha: false,
      depth: true,
      powerPreference: "high-performance",
    });
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.28;
    this.scene.background = new THREE.Color(0x0b1b2d);
    this.scene.fog = new THREE.FogExp2(0x10243a, 0.017);

    this.camera.position.set(0, 9.2, 18.5);
    this.camera.lookAt(0, 2.6, -10);

    this.buildLights();
    this.buildStreet();
    this.buildSkyline();
    this.buildLamp();
    this.buildRain();
    this.buildSplashes();

    this.reducedMotion = this.motionQuery.matches;
    this.resize();
    this.updateRain(0);
    this.updateSplashes();
    this.renderer.render(this.scene, this.camera);

    window.addEventListener("resize", this.resize, { passive: true });
    window.addEventListener("pointermove", this.onPointerMove, {
      passive: true,
    });
    document.addEventListener("visibilitychange", this.onVisibilityChange);
    this.motionQuery.addEventListener("change", this.onMotionChange);
    if (!this.reducedMotion && !document.hidden) this.start();
  }

  private buildLights(): void {
    this.scene.add(new THREE.HemisphereLight(0x8fb4d2, 0x07101a, 2.15));
    const moonWash = new THREE.DirectionalLight(0xa1c1d9, 2.2);
    moonWash.position.set(-8, 14, 8);
    this.scene.add(moonWash);
  }

  private buildStreet(): void {
    const street = new THREE.Mesh(
      new THREE.PlaneGeometry(54, 55),
      new THREE.MeshStandardMaterial({
        color: 0x101f2e,
        roughness: 0.32,
        metalness: 0.42,
      }),
    );
    street.rotation.x = -Math.PI / 2;
    street.position.set(0, 0, -7);
    this.scene.add(street);

    const curbMaterial = new THREE.MeshLambertMaterial({ color: 0x17212b });
    box(this.scene, [48, 0.28, 1.15], [0, 0.12, -10.8], curbMaterial);
    box(this.scene, [48, 0.16, 2.8], [0, 0.25, -12.55], curbMaterial);

    const puddle = new THREE.Mesh(
      puddleGeometry(3.8),
      new THREE.MeshStandardMaterial({
        color: 0x102c44,
        emissive: 0x07111e,
        emissiveIntensity: 0.8,
        transparent: true,
        opacity: 0.9,
        roughness: 0.12,
        metalness: 0.68,
      }),
    );
    puddle.rotation.x = -Math.PI / 2;
    puddle.scale.set(1.48, 0.64, 1);
    puddle.position.set(PUDDLE_X, PUDDLE_Y, PUDDLE_Z);
    this.scene.add(puddle);

    const puddleRim = new THREE.LineLoop(
      puddleContour(3.8),
      new THREE.LineBasicMaterial({
        color: 0x6da3b8,
        transparent: true,
        opacity: 0.46,
      }),
    );
    puddleRim.rotation.x = -Math.PI / 2;
    puddleRim.scale.set(1.48, 0.64, 1);
    puddleRim.position.set(PUDDLE_X, PUDDLE_Y + 0.012, PUDDLE_Z);
    this.scene.add(puddleRim);

    // Chunky amber tiles read as the lamp's broken reflection in wet asphalt.
    const reflectionMaterial = new THREE.MeshBasicMaterial({
      color: 0xffb44a,
      transparent: true,
      opacity: 0.17,
      depthWrite: false,
    });
    const reflections: Array<[number, number, number, number]> = [
      [-4.25, -2.75, 0.7, 2.6],
      [-3.3, -1.95, 1.0, 1.8],
      [-2.15, -1.2, 0.65, 1.2],
      [-1.2, -0.62, 0.4, 0.7],
    ];
    for (const [x, z, width, depth] of reflections) {
      const tile = new THREE.Mesh(
        new THREE.PlaneGeometry(width, depth),
        reflectionMaterial,
      );
      tile.rotation.x = -Math.PI / 2;
      tile.position.set(x, PUDDLE_Y + 0.008, z);
      this.scene.add(tile);
    }

    const laneMaterial = new THREE.MeshBasicMaterial({
      color: 0x52606c,
      transparent: true,
      opacity: 0.18,
    });
    for (let x = -16; x <= 18; x += 6.5) {
      const lane = new THREE.Mesh(
        new THREE.PlaneGeometry(2.4, 0.08),
        laneMaterial,
      );
      lane.rotation.x = -Math.PI / 2;
      lane.position.set(x, PUDDLE_Y / 2, 8.5);
      this.scene.add(lane);
    }
  }

  private buildSkyline(): void {
    const facadePalette = [0x1d3044, 0x233a50, 0x1a2c40, 0x293c51];
    const coolWindows: THREE.Matrix4[] = [];
    const warmWindows: THREE.Matrix4[] = [];
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
      const material = new THREE.MeshLambertMaterial({ color: shade });
      box(
        this.scene,
        [width, height, depth],
        [x, height / 2 + 0.25, z],
        material,
      );

      const columns = Math.max(1, Math.floor(width / 0.7));
      const floors = Math.max(2, Math.floor(height / 0.75));
      const gapX = width / (columns + 1);
      const gapY = height / (floors + 1);
      for (let floor = 1; floor <= floors; floor += 1) {
        for (let column = 1; column <= columns; column += 1) {
          if (this.random() > windowChance) continue;
          const wx = x - width / 2 + gapX * column;
          const wy = 0.25 + gapY * floor;
          matrix.makeTranslation(wx, wy, z + depth / 2 + 0.012);
          (this.random() > 0.2 ? coolWindows : warmWindows).push(
            matrix.clone(),
          );
        }
      }
    };

    // Three silhouette bands make the city feel much larger than the Desk.
    for (let layer = 0; layer < 3; layer += 1) {
      const z = -35 + layer * 7.5;
      let x = -25 - this.random() * 2;
      while (x < 26) {
        const width = 1.8 + this.random() * 3.4;
        const height = 4.5 + this.random() * (layer === 0 ? 11 : 7.5);
        const depth = 3.4 + this.random() * 2.4;
        x += width / 2;
        addBuilding(
          x,
          z + this.random() * 1.2,
          width,
          height,
          depth,
          facadePalette[
            (layer + Math.floor(this.random() * 3)) % facadePalette.length
          ],
          layer === 0 ? 0.34 : 0.22,
        );
        x += width / 2 + 0.3 + this.random() * 0.8;
      }
    }

    // A stepped, needle-topped landmark gives the silhouette an NYC cadence
    // without reproducing a branded or exact real-world building.
    const landmarkMaterial = new THREE.MeshLambertMaterial({ color: 0x31475e });
    box(this.scene, [5.2, 10.5, 4.1], [4.4, 5.5, -31], landmarkMaterial);
    box(this.scene, [3.4, 4.2, 3.2], [4.4, 12.8, -31], landmarkMaterial);
    box(this.scene, [1.7, 3.1, 2.1], [4.4, 16.45, -31], landmarkMaterial);
    box(this.scene, [0.48, 4.2, 0.48], [4.4, 20.05, -31], landmarkMaterial);
    box(
      this.scene,
      [0.72, 0.34, 0.72],
      [4.4, 22.1, -31],
      new THREE.MeshBasicMaterial({ color: 0xff705d }),
    );

    const windowGeometry = new THREE.PlaneGeometry(0.22, 0.28);
    const addWindowInstances = (entries: THREE.Matrix4[], color: number) => {
      const windows = new THREE.InstancedMesh(
        windowGeometry,
        new THREE.MeshBasicMaterial({ color, toneMapped: false }),
        entries.length,
      );
      entries.forEach((entry, index) => windows.setMatrixAt(index, entry));
      windows.instanceMatrix.needsUpdate = true;
      this.scene.add(windows);
    };
    addWindowInstances(coolWindows, 0x7fa8b9);
    addWindowInstances(warmWindows, 0xe6b064);

    // Rooftop aerials break otherwise rectangular horizons.
    const aerialMaterial = new THREE.MeshBasicMaterial({ color: 0x35475a });
    for (const [x, y, z] of [
      [-12, 13, -33],
      [13.5, 11, -28],
      [-19, 9.5, -24],
    ] as Array<[number, number, number]>) {
      box(this.scene, [0.12, 3.2, 0.12], [x, y, z], aerialMaterial);
      box(this.scene, [1.7, 0.15, 0.12], [x, y + 0.8, z], aerialMaterial);
    }
  }

  private buildLamp(): void {
    const structure = new THREE.MeshStandardMaterial({
      color: 0x344854,
      emissive: 0x101820,
      emissiveIntensity: 0.65,
      roughness: 0.7,
    });
    const edge = new THREE.MeshLambertMaterial({ color: 0x61747c });
    const amber = new THREE.MeshStandardMaterial({
      color: 0xffc05a,
      emissive: 0xff8c2a,
      emissiveIntensity: 3.4,
      roughness: 0.3,
      toneMapped: false,
    });
    const lamp = new THREE.Group();
    lamp.position.set(-7.2, 0, -3.1);
    box(lamp, [0.85, 0.35, 0.85], [0, 0.18, 0], edge);
    box(lamp, [0.42, 6.9, 0.42], [0, 3.55, 0], structure);
    box(lamp, [2.75, 0.34, 0.42], [1.15, 6.75, 0], structure);
    box(lamp, [0.95, 0.34, 0.95], [2.28, 6.48, 0], edge);
    box(lamp, [0.62, 0.42, 0.62], [2.28, 6.2, 0], amber);
    this.scene.add(lamp);

    const lampLight = new THREE.PointLight(0xffa43a, 38, 17, 1.7);
    lampLight.position.set(-4.92, 6.05, -3.1);
    this.scene.add(lampLight);

    const poolLight = new THREE.PointLight(0xff8a24, 11, 10, 2);
    poolLight.position.set(PUDDLE_X - 0.6, 0.65, PUDDLE_Z);
    this.scene.add(poolLight);
  }

  private buildRain(): void {
    const geometry = new THREE.BoxGeometry(0.035, 0.58, 0.035);
    const material = new THREE.MeshBasicMaterial({
      color: 0x8bbbd0,
      transparent: true,
      opacity: 0.58,
      depthWrite: false,
    });
    this.rain = new THREE.InstancedMesh(geometry, material, RAIN_COUNT);
    this.rain.frustumCulled = false;
    this.scene.add(this.rain);
    for (let index = 0; index < RAIN_COUNT; index += 1) {
      this.rainDrops.push({
        x: -21 + this.random() * 42,
        y: 0.3 + this.random() * 20,
        z: -39 + this.random() * 53,
        speed: 8 + this.random() * 8,
      });
    }
  }

  private buildSplashes(): void {
    const geometry = new THREE.BoxGeometry(0.12, 0.12, 0.12);
    const material = new THREE.MeshBasicMaterial({
      color: 0xb8e3eb,
      transparent: true,
      opacity: 0.78,
      depthWrite: false,
    });
    this.splashes = new THREE.InstancedMesh(geometry, material, SPLASH_COUNT);
    this.splashes.frustumCulled = false;
    this.scene.add(this.splashes);

    for (let index = 0; index < SPLASH_COUNT; index += 1) {
      const angle = this.random() * Math.PI * 2;
      const radius = this.random() * 3.2;
      const outward = 0.7 + this.random() * 1.5;
      this.splashDrops.push({
        x: PUDDLE_X + Math.cos(angle) * radius * 1.6,
        z: PUDDLE_Z + Math.sin(angle) * radius * 0.55,
        vx: Math.cos(angle) * outward,
        vy: 1.4 + this.random() * 2.2,
        vz: Math.sin(angle) * outward,
        offset: this.random() * 3.2,
        cycle: 2.1 + this.random() * 1.4,
      });
    }

    const ringMaterial = new THREE.MeshBasicMaterial({
      color: 0x86c6d6,
      transparent: true,
      opacity: 0.4,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    for (let index = 0; index < 7; index += 1) {
      const ring = new THREE.Mesh(
        new THREE.RingGeometry(0.18, 0.23, 24),
        ringMaterial.clone(),
      );
      ring.rotation.x = -Math.PI / 2;
      const angle = this.random() * Math.PI * 2;
      const radius = this.random() * 2.8;
      ring.position.set(
        PUDDLE_X + Math.cos(angle) * radius * 1.55,
        PUDDLE_Y + 0.025,
        PUDDLE_Z + Math.sin(angle) * radius * 0.52,
      );
      this.scene.add(ring);
      this.ripples.push({
        mesh: ring,
        offset: this.random() * 3,
        cycle: 2.1 + this.random() * 1.5,
      });
    }
  }

  private updateRain(delta: number): void {
    const transform = new THREE.Object3D();
    transform.rotation.z = 0.075;
    for (let index = 0; index < this.rainDrops.length; index += 1) {
      const drop = this.rainDrops[index];
      drop.y -= drop.speed * delta;
      drop.x -= drop.speed * delta * 0.08;
      if (drop.y < 0) {
        drop.y += 20;
        drop.x = -21 + this.random() * 42;
      }
      transform.position.set(drop.x, drop.y, drop.z);
      transform.scale.setScalar(drop.z > 1 ? 1.15 : drop.z > -16 ? 0.8 : 0.55);
      transform.updateMatrix();
      this.rain.setMatrixAt(index, transform.matrix);
    }
    this.rain.instanceMatrix.needsUpdate = true;
  }

  private updateSplashes(): void {
    const transform = new THREE.Object3D();
    for (let index = 0; index < this.splashDrops.length; index += 1) {
      const drop = this.splashDrops[index];
      const local = (this.elapsed + drop.offset) % drop.cycle;
      const flight = 0.5;
      if (local < flight) {
        const y = PUDDLE_Y + drop.vy * local - 4.9 * local * local;
        transform.position.set(
          drop.x + drop.vx * local,
          Math.max(PUDDLE_Y, y),
          drop.z + drop.vz * local,
        );
        const scale = 0.7 + (1 - local / flight) * 0.8;
        transform.scale.setScalar(scale);
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
      const local = (this.elapsed + ripple.offset) % ripple.cycle;
      const progress = Math.min(local / 1.15, 1);
      ripple.mesh.scale.setScalar(0.5 + progress * 5.5);
      ripple.mesh.material.opacity = progress < 1 ? 0.36 * (1 - progress) : 0;
    }
  }

  private renderFrame = () => {
    if (this.destroyed || this.reducedMotion || document.hidden) return;
    const delta = Math.min(this.clock.getDelta(), 0.05);
    this.elapsed += delta;
    this.updateRain(delta);
    this.updateSplashes();

    const targetX = this.pointerX * 0.55;
    const targetY = 9.2 - this.pointerY * 0.22;
    this.camera.position.x += (targetX - this.camera.position.x) * 0.025;
    this.camera.position.y += (targetY - this.camera.position.y) * 0.025;
    this.camera.lookAt(0, 2.6, -10);

    this.renderer.render(this.scene, this.camera);
    this.animationFrame = requestAnimationFrame(this.renderFrame);
  };

  private start(): void {
    if (this.animationFrame || this.destroyed) return;
    this.clock.start();
    this.animationFrame = requestAnimationFrame(this.renderFrame);
  }

  private stop(): void {
    if (this.animationFrame) cancelAnimationFrame(this.animationFrame);
    this.animationFrame = 0;
    this.clock.stop();
  }

  private resize = () => {
    const width = Math.max(window.innerWidth, 1);
    const height = Math.max(window.innerHeight, 1);
    const scale = Math.max(
      PIXEL_SCALE,
      width / MAX_RENDER_WIDTH,
      height / MAX_RENDER_HEIGHT,
    );
    this.renderer.setSize(
      Math.max(1, Math.round(width / scale)),
      Math.max(1, Math.round(height / scale)),
      false,
    );
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.render(this.scene, this.camera);
  };

  private onPointerMove = (event: PointerEvent) => {
    if (this.reducedMotion) return;
    this.pointerX = (event.clientX / Math.max(window.innerWidth, 1)) * 2 - 1;
    this.pointerY = (event.clientY / Math.max(window.innerHeight, 1)) * 2 - 1;
  };

  private onVisibilityChange = () => {
    if (document.hidden) this.stop();
    else if (!this.reducedMotion) this.start();
  };

  private onMotionChange = (event: MediaQueryListEvent) => {
    this.reducedMotion = event.matches;
    if (this.reducedMotion) {
      this.stop();
      this.renderer.render(this.scene, this.camera);
    } else if (!document.hidden) {
      this.start();
    }
  };

  destroy(): void {
    if (this.destroyed) return;
    this.destroyed = true;
    this.stop();
    window.removeEventListener("resize", this.resize);
    window.removeEventListener("pointermove", this.onPointerMove);
    document.removeEventListener("visibilitychange", this.onVisibilityChange);
    this.motionQuery.removeEventListener("change", this.onMotionChange);
    disposeScene(this.scene);
    this.renderer.dispose();
  }
}

/** Mount the procedural scene and return the exact React-effect cleanup. WebGL
 * setup may fail on old/test glass; the CSS grade remains a useful fallback. */
export function mountRainyCityScene(canvas: HTMLCanvasElement): () => void {
  try {
    const city = new RainyCityScene(canvas);
    return () => city.destroy();
  } catch {
    return () => undefined;
  }
}
