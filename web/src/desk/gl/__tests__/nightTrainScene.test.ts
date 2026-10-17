import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as THREE from "three";
import { Reflector } from "three/addons/objects/Reflector.js";
import { createNightTrainScene } from "../interiors/nightTrainScene";

const state = vi.hoisted(() => ({
  renderer: null as null | { dispose: ReturnType<typeof vi.fn>; forceContextLoss: ReturnType<typeof vi.fn> },
  composer: null as null | {
    passes: { scene?: THREE.Scene; camera?: THREE.PerspectiveCamera; dispose: ReturnType<typeof vi.fn> }[];
    render: ReturnType<typeof vi.fn>; dispose: ReturnType<typeof vi.fn>;
  },
  landscape: null as null | { update: ReturnType<typeof vi.fn>; dispose: ReturnType<typeof vi.fn> },
}));

vi.mock("three", async () => {
  const actual = await vi.importActual<typeof import("three")>("three");
  return {
    ...actual,
    WebGLRenderer: class {
      shadowMap = { enabled: false, type: 0 };
      setPixelRatio = vi.fn(); setSize = vi.fn(); dispose = vi.fn(); forceContextLoss = vi.fn();
      constructor() { state.renderer = this; }
    },
    PMREMGenerator: class {
      fromScene() { return new actual.WebGLRenderTarget(32, 32); }
      dispose = vi.fn();
    },
  };
});
vi.mock("three/addons/postprocessing/EffectComposer.js", () => ({ EffectComposer: class {
  passes: { scene?: THREE.Scene; camera?: THREE.PerspectiveCamera; dispose: ReturnType<typeof vi.fn> }[] = [];
  render = vi.fn(); dispose = vi.fn(); setPixelRatio = vi.fn(); setSize = vi.fn();
  constructor() { state.composer = this; }
  addPass(pass: { dispose: ReturnType<typeof vi.fn> }) { this.passes.push(pass); }
} }));
vi.mock("three/addons/postprocessing/RenderPass.js", () => ({ RenderPass: class {
  dispose = vi.fn();
  constructor(public scene: THREE.Scene, public camera: THREE.PerspectiveCamera) {}
} }));
vi.mock("three/addons/postprocessing/UnrealBloomPass.js", () => ({ UnrealBloomPass: class { dispose = vi.fn(); } }));
vi.mock("three/addons/postprocessing/OutputPass.js", () => ({ OutputPass: class { dispose = vi.fn(); } }));
vi.mock("../interiors/nightTrainLandscape", () => ({
  createTrainLandscape(room: { root: THREE.Group; group(): THREE.Group; moving(value: THREE.Group): THREE.Group }) {
    const world = room.moving(room.group());
    world.name = "Night Train test journey";
    const landscape = {
      update: vi.fn((elapsed: number) => { world.position.x = elapsed * 0.01; }),
      dispose: vi.fn(() => { world.removeFromParent(); }),
    };
    state.landscape = landscape;
    return landscape;
  },
}));

beforeEach(() => {
  const context = { fillStyle: "", fillRect() {}, strokeStyle: "", lineWidth: 0, strokeRect() {},
    beginPath() {}, moveTo() {}, lineTo() {}, stroke() {} };
  vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(context as unknown as CanvasRenderingContext2D);
});
afterEach(() => { vi.restoreAllMocks(); });
const construct = (reducedMotion = false) => createNightTrainScene({
  canvas: document.createElement("canvas"), seed: 6419, reducedMotion,
});
const inspect = () => {
  const pass = state.composer!.passes[0];
  return { scene: pass.scene!, camera: pass.camera! };
};
const frame = (elapsed: number) => ({ elapsed, delta: 0.05, pointer: { x: 0.8, y: -0.6 } });
const rainOf = (scene: THREE.Scene) => scene.getObjectByName("Night Train glass droplets") as
  THREE.Mesh<THREE.PlaneGeometry, THREE.ShaderMaterial>;

describe("Night Train compartment lifecycle", () => {
  it("preserves an actual bounded Reflector through Room batching and uses metre-scale props", () => {
    const atmosphere = construct();
    const { scene, camera } = inspect();
    expect(camera.far).toBe(400);
    const pane = scene.getObjectByName("Night Train reflective window") as Reflector;
    expect(pane).toBeInstanceOf(Reflector);
    expect(pane.getRenderTarget().width).toBe(512);
    expect(pane.getRenderTarget().height).toBeLessThanOrEqual(512);
    expect((pane.material as THREE.ShaderMaterial).transparent).toBe(true);
    expect((pane.material as THREE.ShaderMaterial).depthWrite).toBe(false);
    const table = scene.getObjectByName("Night Train walnut table") as THREE.Mesh;
    table.geometry.computeBoundingBox();
    const size = table.geometry.boundingBox!.getSize(new THREE.Vector3());
    expect(size.x).toBeCloseTo(0.78);
    expect(size.z).toBeCloseTo(0.48);
    expect(table.position.y).toBe(0.75);
    expect(scene.getObjectByName("Night Train curved berth")).toBeInstanceOf(THREE.Mesh);
    expect(scene.getObjectByName("Night Train practical lamp")).toBeInstanceOf(THREE.Group);
    expect(scene.getObjectByName("Night Train glazed cup")).toBeInstanceOf(THREE.Group);
    expect(scene.getObjectByName("Night Train open book")).toBeInstanceOf(THREE.Group);
    atmosphere.dispose();
  });

  it("populates the first still then freezes landscape, rain, vibration and parallax", () => {
    const atmosphere = construct(true);
    atmosphere.resize({ width: 393, height: 852, devicePixelRatio: 3 });
    const { scene, camera } = inspect();
    const droplets = rainOf(scene);
    expect(droplets.geometry).toBeInstanceOf(THREE.PlaneGeometry);
    expect(droplets.material.uniforms.uTime.value).toBe(0);
    const initialCamera = camera.matrixWorld.toArray();
    expect(state.landscape!.update).toHaveBeenCalledExactlyOnceWith(0);
    atmosphere.update(frame(60));
    expect(droplets.material.uniforms.uTime.value).toBe(0);
    expect(camera.matrixWorld.toArray()).toEqual(initialCamera);
    expect(state.landscape!.update).toHaveBeenCalledTimes(1);
    atmosphere.render(); expect(state.composer!.render).toHaveBeenCalledTimes(1);
    atmosphere.setReducedMotion!(false); atmosphere.update(frame(60));
    expect(droplets.material.uniforms.uTime.value).toBe(60);
    expect(camera.matrixWorld.toArray()).not.toEqual(initialCamera);
    expect(state.landscape!.update).toHaveBeenLastCalledWith(60);
    atmosphere.setReducedMotion!(true);
    const frozenCamera = camera.matrixWorld.toArray();
    atmosphere.update(frame(130));
    expect(droplets.material.uniforms.uTime.value).toBe(60);
    expect(camera.matrixWorld.toArray()).toEqual(frozenCamera);
    expect(state.landscape!.update).toHaveBeenCalledTimes(2);
    atmosphere.dispose();
  });

  it("keeps the window and lamp in the responsive frame after both resize and base updates", () => {
    const atmosphere = construct();
    const { scene, camera } = inspect();
    for (const [width, height] of [[1440, 900], [393, 852]]) {
      atmosphere.resize({ width, height, devicePixelRatio: 1 });
      for (const elapsed of [0, 30]) {
        atmosphere.update(frame(elapsed));
        scene.updateMatrixWorld(true);
        for (const name of ["Night Train reflective window", "Night Train practical lamp"]) {
          const position = scene.getObjectByName(name)!.getWorldPosition(new THREE.Vector3()).project(camera);
          expect(Math.abs(position.x)).toBeLessThan(0.8);
          expect(Math.abs(position.y)).toBeLessThan(0.9);
        }
      }
    }
    atmosphere.dispose();
  });

  it("disposes the pane geometry, material and reflection target once and rejects later work", () => {
    const atmosphere = construct();
    const { scene, camera } = inspect();
    const pane = scene.getObjectByName("Night Train reflective window") as Reflector;
    const geometryDispose = vi.spyOn(pane.geometry, "dispose");
    const materialDispose = vi.spyOn(pane.material as THREE.Material, "dispose");
    const targetDispose = vi.spyOn(pane.getRenderTarget(), "dispose");
    const composer = state.composer!, renderer = state.renderer!, landscape = state.landscape!;
    atmosphere.dispose(); atmosphere.dispose();
    const cameraPosition = camera.position.toArray();
    atmosphere.update(frame(100)); atmosphere.resize({ width: 1, height: 1, devicePixelRatio: 1 });
    atmosphere.setReducedMotion!(false); atmosphere.render();
    expect(geometryDispose).toHaveBeenCalledTimes(1);
    expect(materialDispose).toHaveBeenCalledTimes(1);
    expect(targetDispose).toHaveBeenCalledTimes(1);
    expect(landscape.dispose).toHaveBeenCalledTimes(1);
    expect(composer.dispose).toHaveBeenCalledTimes(1);
    expect(renderer.dispose).toHaveBeenCalledTimes(1);
    expect(renderer.forceContextLoss).toHaveBeenCalledTimes(1);
    expect(composer.render).not.toHaveBeenCalled();
    expect(camera.position.toArray()).toEqual(cameraPosition);
    expect(scene.children).toHaveLength(0);
    expect(pane.parent).toBeNull();
  });
});
