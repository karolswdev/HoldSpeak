import * as THREE from "three";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";
import { mergeGeometries } from "three/addons/utils/BufferGeometryUtils.js";
import type {
  AtmosphereFrame,
  AtmosphereScene,
  AtmosphereSceneContext,
} from "../atmosphereRuntime";

export { THREE };
export type Vec = [number, number, number];
export type Tick = (frame: AtmosphereFrame) => void;

export function randomSource(seed: number) {
  let n = seed >>> 0;
  return () => {
    n = (Math.imul(1664525, n) + 1013904223) >>> 0;
    return n / 4294967296;
  };
}

/** Shared construction tools, not a shared room: every scene authors its own
 * camera, architecture, practical light sources and motion. All texture work
 * happens once at construction; frames only move the scene graph. */
export class Room {
  scene = new THREE.Scene();
  camera: THREE.PerspectiveCamera;
  root = new THREE.Group();
  ticks: Tick[] = [];
  random: () => number;
  textures = new Set<THREE.Texture>();
  private materials = new Set<THREE.Material>();
  private geometries = new Set<THREE.BufferGeometry>();
  private baseCamera: THREE.Vector3;
  private target: THREE.Vector3;
  private renderer: THREE.WebGLRenderer;
  private composer: EffectComposer;
  private reduced = false;
  private disposed = false;
  private environment: THREE.WebGLRenderTarget;
  private animated = new Set<THREE.Object3D>();
  private surfaceCache = new Map<string, THREE.MeshStandardMaterial>();

  constructor(
    context: AtmosphereSceneContext,
    options: {
      camera: Vec;
      target: Vec;
      background: number;
      fog?: number;
      fov?: number;
      exposure?: number;
      ambient?: number;
    },
  ) {
    this.random = randomSource(context.seed);
    this.reduced = context.reducedMotion;
    this.scene.background = new THREE.Color(options.background);
    this.scene.fog = new THREE.FogExp2(
      options.background,
      options.fog ?? 0.028,
    );
    this.camera = new THREE.PerspectiveCamera(options.fov ?? 48, 1, 0.1, 130);
    this.baseCamera = new THREE.Vector3(...options.camera);
    this.target = new THREE.Vector3(...options.target);
    this.camera.position.copy(this.baseCamera);
    this.camera.lookAt(this.target);
    this.scene.add(this.root);
    this.scene.add(
      new THREE.HemisphereLight(0xa6bccb, 0x433326, options.ambient ?? 0.6),
    );
    this.renderer = new THREE.WebGLRenderer({
      canvas: context.canvas,
      antialias: true,
      alpha: false,
      powerPreference: "low-power",
    });
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = options.exposure ?? 1.15;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    const pmrem = new THREE.PMREMGenerator(this.renderer);
    const environment = new RoomEnvironment();
    this.environment = pmrem.fromScene(environment, 0.06);
    this.scene.environment = this.environment.texture;
    this.scene.environmentIntensity = 0.22;
    environment.dispose();
    pmrem.dispose();
    this.composer = new EffectComposer(this.renderer);
    this.composer.addPass(new RenderPass(this.scene, this.camera));
    this.composer.addPass(
      new UnrealBloomPass(new THREE.Vector2(1, 1), 0.26, 0.65, 0.86),
    );
    this.composer.addPass(new OutputPass());
  }

  material(color: number, roughness = 0.75, metalness = 0) {
    const material = new THREE.MeshStandardMaterial({
      color,
      roughness,
      metalness,
    });
    this.materials.add(material);
    return material;
  }

  glow(color: number, strength = 1) {
    const material = new THREE.MeshStandardMaterial({
      color,
      emissive: color,
      emissiveIntensity: strength,
      roughness: 0.4,
    });
    this.materials.add(material);
    return material;
  }

  mesh(
    geometry: THREE.BufferGeometry,
    material: THREE.Material,
    at: Vec,
    parent: THREE.Object3D = this.root,
  ) {
    this.geometries.add(geometry);
    this.materials.add(material);
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(...at);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    parent.add(mesh);
    return mesh;
  }

  box(size: Vec, at: Vec, material: THREE.Material, parent?: THREE.Object3D) {
    const smallest = Math.min(...size);
    const geometry =
      smallest >= 0.08 && Math.max(...size) < 7
        ? new RoundedBoxGeometry(...size, 1, Math.min(smallest * 0.12, 0.035))
        : new THREE.BoxGeometry(...size);
    return this.mesh(geometry, material, at, parent);
  }

  cylinder(
    top: number,
    bottom: number,
    height: number,
    at: Vec,
    material: THREE.Material,
    parent?: THREE.Object3D,
  ) {
    return this.mesh(
      new THREE.CylinderGeometry(top, bottom, height, 24),
      material,
      at,
      parent,
    );
  }

  sphere(
    radius: number,
    at: Vec,
    material: THREE.Material,
    parent?: THREE.Object3D,
  ) {
    return this.mesh(
      new THREE.SphereGeometry(radius, 20, 12),
      material,
      at,
      parent,
    );
  }

  ring(
    radius: number,
    thickness: number,
    at: Vec,
    material: THREE.Material,
    parent?: THREE.Object3D,
  ) {
    return this.mesh(
      new THREE.TorusGeometry(radius, thickness, 10, 64),
      material,
      at,
      parent,
    );
  }

  beam(
    a: Vec,
    b: Vec,
    radius: number,
    material: THREE.Material,
    parent?: THREE.Object3D,
  ) {
    const start = new THREE.Vector3(...a),
      end = new THREE.Vector3(...b);
    const beam = this.cylinder(
      radius,
      radius,
      start.distanceTo(end),
      [0, 0, 0],
      material,
      parent,
    );
    beam.position.copy(start).add(end).multiplyScalar(0.5);
    beam.quaternion.setFromUnitVectors(
      new THREE.Vector3(0, 1, 0),
      end.sub(start).normalize(),
    );
    return beam;
  }

  group(at: Vec = [0, 0, 0], parent: THREE.Object3D = this.root) {
    const group = new THREE.Group();
    group.position.set(...at);
    parent.add(group);
    return group;
  }

  moving<T extends THREE.Object3D>(object: T): T {
    this.animated.add(object);
    return object;
  }

  point(color: number, intensity: number, at: Vec, distance = 14) {
    const light = new THREE.PointLight(color, intensity, distance, 2);
    light.position.set(...at);
    this.root.add(light);
    return light;
  }

  spot(
    color: number,
    intensity: number,
    at: Vec,
    target: Vec,
    angle = 0.8,
    shadow = false,
  ) {
    const light = new THREE.SpotLight(color, intensity, 35, angle, 0.72, 2);
    light.position.set(...at);
    light.target.position.set(...target);
    light.castShadow = shadow;
    light.shadow.mapSize.set(1024, 1024);
    light.shadow.bias = -0.001;
    this.root.add(light, light.target);
    return light;
  }

  texture(
    draw: (ctx: CanvasRenderingContext2D, size: number) => void,
    size = 256,
  ) {
    const canvas = document.createElement("canvas");
    canvas.width = canvas.height = size;
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("Atmosphere texture canvas unavailable");
    draw(ctx, size);
    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    this.textures.add(texture);
    return texture;
  }

  surface(
    color: number,
    pattern: "wood" | "plaster" | "fabric" | "tile",
    repeat: [number, number] = [1, 1],
  ) {
    const key = `${color}:${pattern}:${repeat.join(",")}`;
    const cached = this.surfaceCache.get(key);
    if (cached) return cached;
    const texture = this.texture((ctx, size) => {
      ctx.fillStyle = `#${color.toString(16).padStart(6, "0")}`;
      ctx.fillRect(0, 0, size, size);
      for (let i = 0; i < 6500; i++) {
        const light = this.random() > 0.48;
        ctx.fillStyle = light
          ? `rgba(240,224,200,${this.random() * 0.035})`
          : `rgba(0,0,0,${this.random() * 0.055})`;
        const x = this.random() * size,
          y = this.random() * size;
        ctx.fillRect(
          x,
          y,
          pattern === "wood" ? this.random() * 100 : 1.5,
          pattern === "fabric" ? 6 : 1,
        );
      }
      if (pattern === "tile") {
        ctx.strokeStyle = "#222c2b";
        ctx.lineWidth = 2;
        for (let i = 0; i < size; i += 64) {
          ctx.strokeRect(i, 0, 64, size);
          ctx.strokeRect(0, i, size, 64);
        }
      }
    });
    texture.wrapS = texture.wrapT = THREE.RepeatWrapping;
    texture.repeat.set(...repeat);
    const material = this.material(0xffffff, pattern === "tile" ? 0.31 : 0.8);
    material.map = texture;
    material.bumpMap = texture;
    material.bumpScale = pattern === "plaster" ? 0.08 : 0.025;
    this.surfaceCache.set(key, material);
    return material;
  }

  label(
    text: string,
    width: number,
    height: number,
    at: Vec,
    ink = "#dac8a5",
    paper = "#12181a",
    emissive = 0,
    parent?: THREE.Object3D,
  ) {
    const texture = this.texture((ctx, size) => {
      ctx.fillStyle = paper;
      ctx.fillRect(0, 0, size, size);
      ctx.fillStyle = ink;
      ctx.font = "500 112px monospace";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(text, size / 2, size / 2, size * 0.87);
    });
    // Lettering is stretched onto a narrow sign: square mip levels would
    // erase the strokes long before the physical sign leaves the frame.
    texture.generateMipmaps = false;
    texture.minFilter = THREE.LinearFilter;
    texture.anisotropy = 4;
    const material = this.material(0xffffff, 0.8);
    material.map = texture;
    material.emissiveMap = texture;
    material.emissive.set(0xffffff);
    material.emissiveIntensity = emissive;
    return this.mesh(
      new THREE.PlaneGeometry(width, height),
      material,
      at,
      parent,
    );
  }

  halo(color: number, at: Vec, scale = 1, opacity = 0.25) {
    const texture = this.texture((ctx, size) => {
      const gradient = ctx.createRadialGradient(
        size / 2,
        size / 2,
        0,
        size / 2,
        size / 2,
        size / 2,
      );
      gradient.addColorStop(0, "rgba(255,255,255,0.6)");
      gradient.addColorStop(0.2, "rgba(255,255,255,0.2)");
      gradient.addColorStop(1, "rgba(255,255,255,0)");
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, size, size);
    }, 64);
    const material = new THREE.SpriteMaterial({
      map: texture,
      color,
      transparent: true,
      opacity,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });
    this.materials.add(material);
    const sprite = new THREE.Sprite(material);
    sprite.position.set(...at);
    sprite.scale.set(scale, scale, 1);
    this.root.add(sprite);
    return sprite;
  }

  floor(width: number, depth: number, material: THREE.Material, y = 0) {
    return this.box(
      [width, 0.12, depth],
      [0, y - 0.06, -depth / 2 + 5],
      material,
    );
  }

  /** A desk lamp with an opaque outer shade, luminous inner rim and pooled light. */
  lamp(at: Vec, shadeColor = 0x355349, scale = 1) {
    const group = this.group(at);
    group.scale.setScalar(scale);
    const brass = this.material(0x8e6b3d, 0.35, 0.65);
    this.cylinder(0.28, 0.34, 0.055, [0, 0.035, 0], brass, group);
    this.beam([0, 0.05, 0], [0, 0.8, 0], 0.035, brass, group);
    const shade = this.cylinder(
      0.27,
      0.43,
      0.25,
      [0, 0.87, 0],
      this.material(shadeColor, 0.28),
      group,
    );
    this.cylinder(
      0.39,
      0.39,
      0.013,
      [0, 0.75, 0],
      this.glow(0xffd391, 2),
      group,
    );
    this.point(
      0xffcb80,
      15 * scale,
      [at[0], at[1] + 0.7 * scale, at[2]],
      5 * scale,
    );
    this.spot(
      0xffd899,
      22 * scale,
      [at[0], at[1] + 0.73 * scale, at[2]],
      [at[0], at[1] - 0.4, at[2] + 0.1],
      1.1,
    );
    return shade;
  }

  dust(count: number, bounds: Vec, at: Vec, color = 0xc3b795, speed = 0.03) {
    const positions = new Float32Array(count * 3);
    const initial = new Float32Array(count * 3);
    for (let i = 0; i < count * 3; i++)
      initial[i] = (this.random() - 0.5) * bounds[i % 3];
    positions.set(initial);
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    const material = new THREE.PointsMaterial({
      color,
      size: 0.018,
      transparent: true,
      opacity: 0.3,
      depthWrite: false,
    });
    this.geometries.add(geometry);
    this.materials.add(material);
    const motes = new THREE.Points(geometry, material);
    motes.position.set(...at);
    this.root.add(motes);
    this.ticks.push(({ elapsed }) => {
      for (let i = 0; i < count; i++) {
        positions[i * 3] = initial[i * 3] + Math.sin(elapsed * 0.11 + i) * 0.12;
        positions[i * 3 + 1] =
          ((initial[i * 3 + 1] + bounds[1] / 2 + elapsed * speed) % bounds[1]) -
          bounds[1] / 2;
      }
      geometry.attributes.position.needsUpdate = true;
    });
  }

  rain(width: number, height: number, at: Vec, count = 180) {
    const positions = new Float32Array(count * 6);
    const seeds = Array.from({ length: count }, () => [
      this.random() * width,
      this.random() * height,
      this.random(),
    ]);
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    const material = new THREE.LineBasicMaterial({
      color: 0xadc7dd,
      transparent: true,
      opacity: 0.15,
      depthWrite: false,
    });
    const rain = new THREE.LineSegments(geometry, material);
    rain.position.set(...at);
    this.root.add(rain);
    this.geometries.add(geometry);
    this.materials.add(material);
    this.ticks.push(({ elapsed }) => {
      seeds.forEach(([x, y, z], i) => {
        const dropY = height / 2 - ((y + elapsed * (1.9 + z * 2)) % height);
        positions.set(
          [
            x - width / 2,
            dropY,
            -z * 0.2,
            x - width / 2 - 0.016,
            dropY + 0.05 + z * 0.14,
            -z * 0.2,
          ],
          i * 6,
        );
      });
      geometry.attributes.position.needsUpdate = true;
    });
  }

  plant(at: Vec, scale = 1, color = 0x29483c) {
    const group = this.moving(this.group(at));
    group.scale.setScalar(scale);
    const clay = this.surface(0x674a36, "plaster");
    this.cylinder(0.3, 0.21, 0.45, [0, 0.23, 0], clay, group);
    this.cylinder(0.32, 0.32, 0.06, [0, 0.44, 0], clay, group);
    const leafMat = this.material(color, 0.55);
    const stem = this.material(0x314432);
    for (let i = 0; i < 11; i++) {
      const angle = i * 2.4;
      const reach = 0.35 + this.random() * 0.4;
      const y = 0.7 + this.random() * 1.3;
      const x = Math.cos(angle) * reach,
        z = Math.sin(angle) * reach;
      this.beam([0, 0.4, 0], [x, y, z], 0.012, stem, group);
      const geometry = new THREE.PlaneGeometry(0.42, 0.87, 6, 12);
      const vertices = geometry.attributes.position;
      for (let vertex = 0; vertex < vertices.count; vertex++) {
        const v = vertices.getY(vertex) / 0.87 + 0.5;
        const u = vertices.getX(vertex) / 0.42;
        const arc = Math.max(
          0,
          Math.sin(Math.min(1, Math.max(0, v)) * Math.PI),
        );
        vertices.setXYZ(
          vertex,
          vertices.getX(vertex) * Math.pow(arc, 0.72),
          vertices.getY(vertex),
          arc * 0.13 - Math.abs(u) * 0.095,
        );
      }
      geometry.computeVertexNormals();
      leafMat.side = THREE.DoubleSide;
      const leaf = this.mesh(geometry, leafMat, [x, y, z], group);
      leaf.rotation.set(-0.65 + this.random() * 0.6, -angle, 0.2);
      for (let segment = 0; segment < 5; segment++) {
        const a = segment / 5,
          b = (segment + 1) / 5;
        this.beam(
          [0, a * 0.87 - 0.435, Math.sin(a * Math.PI) * 0.13 + 0.002],
          [0, b * 0.87 - 0.435, Math.sin(b * Math.PI) * 0.13 + 0.002],
          0.003,
          stem,
          leaf,
        );
      }
    }
    this.ticks.push(({ elapsed }) => {
      group.rotation.z = Math.sin(elapsed * 0.23 + at[0]) * 0.006;
    });
    return group;
  }

  finish(): AtmosphereScene {
    // Batch stationary architecture by material. The archive's thousands of
    // drawer faces become a handful of draw calls; moving props retain their
    // own transform roots. This also batches each plant's leaves and stems.
    this.root.updateMatrixWorld(true);
    const batch = (parent: THREE.Object3D) => {
      const inverse = parent.matrixWorld.clone().invert();
      const groups = new Map<THREE.Material, THREE.Mesh[]>();
      const visit = (object: THREE.Object3D) => {
        if (!object.visible || (object !== parent && this.animated.has(object)))
          return;
        if (
          object instanceof THREE.Mesh &&
          !(object instanceof THREE.InstancedMesh) &&
          !Array.isArray(object.material)
        ) {
          const group = groups.get(object.material) ?? [];
          group.push(object);
          groups.set(object.material, group);
        }
        object.children.forEach(visit);
      };
      parent.children.forEach(visit);
      groups.forEach((meshes, material) => {
        if (meshes.length < 2) return;
        const parts = meshes.map((mesh) => {
          const geometry = mesh.geometry.index
            ? mesh.geometry.toNonIndexed()
            : mesh.geometry.clone();
          geometry.applyMatrix4(inverse.clone().multiply(mesh.matrixWorld));
          geometry.clearGroups();
          return geometry;
        });
        const merged = mergeGeometries(parts);
        parts.forEach((part) => part.dispose());
        if (!merged) return;
        meshes.forEach((mesh) => mesh.removeFromParent());
        this.mesh(merged, material, [0, 0, 0], parent);
      });
    };
    this.animated.forEach(batch);
    batch(this.root);
    return {
      resize: ({ width, height, devicePixelRatio }) => {
        const ratio = Math.min(
          devicePixelRatio,
          1.5,
          1600 / width,
          1000 / height,
        );
        this.renderer.setPixelRatio(ratio);
        this.renderer.setSize(width, height, false);
        this.composer.setPixelRatio(ratio);
        this.composer.setSize(width, height);
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
      },
      update: (frame) => {
        if (!this.reduced) {
          this.camera.position.x = THREE.MathUtils.damp(
            this.camera.position.x,
            this.baseCamera.x + frame.pointer.x * 0.075,
            2,
            frame.delta,
          );
          this.camera.position.y = THREE.MathUtils.damp(
            this.camera.position.y,
            this.baseCamera.y - frame.pointer.y * 0.045,
            2,
            frame.delta,
          );
          this.camera.lookAt(this.target);
        }
        this.ticks.forEach((tick) => tick(frame));
      },
      setReducedMotion: (value) => {
        this.reduced = value;
        this.camera.position.copy(this.baseCamera);
        this.camera.lookAt(this.target);
      },
      render: () => {
        if (!this.disposed) this.composer.render();
      },
      dispose: () => {
        if (this.disposed) return;
        this.disposed = true;
        this.geometries.forEach((geometry) => geometry.dispose());
        this.materials.forEach((material) => material.dispose());
        this.textures.forEach((texture) => texture.dispose());
        this.composer.passes.forEach((pass) => pass.dispose());
        this.composer.dispose();
        this.environment.dispose();
        this.renderer.dispose();
        this.renderer.forceContextLoss();
        this.scene.clear();
      },
    };
  }
}
