import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as THREE from "three";
import { Reflector } from "three/addons/objects/Reflector.js";
import { createNightTrainScene } from "../interiors/nightTrainScene";
import { Room } from "../interiors/sceneKit";

const state = vi.hoisted(() => ({
  maxSamples: 4,
  renderer: null as null | {
    domElement: HTMLCanvasElement; dispose: ReturnType<typeof vi.fn>; forceContextLoss: ReturnType<typeof vi.fn>;
  },
  composer: null as null | {
    passes: { scene?: THREE.Scene; camera?: THREE.PerspectiveCamera; dispose: () => void }[];
    render: ReturnType<typeof vi.fn>; dispose: ReturnType<typeof vi.fn>;
    renderTarget1: THREE.WebGLRenderTarget; renderTarget2: THREE.WebGLRenderTarget;
  },
  landscape: null as null | { update: ReturnType<typeof vi.fn>; dispose: ReturnType<typeof vi.fn> },
}));

vi.mock("three", async () => {
  const actual = await vi.importActual<typeof import("three")>("three");
  return {
    ...actual,
    WebGLRenderer: class {
      shadowMap = { enabled: false, type: 0 };
      capabilities = { maxSamples: state.maxSamples };
      domElement: HTMLCanvasElement;
      private pixelRatio = 1;
      private width = 1;
      private height = 1;
      setPixelRatio = vi.fn((value: number) => { this.pixelRatio = value; });
      setSize = vi.fn((width: number, height: number) => {
        this.width = width; this.height = height;
        this.domElement.width = Math.floor(width * this.pixelRatio);
        this.domElement.height = Math.floor(height * this.pixelRatio);
      });
      getPixelRatio() { return this.pixelRatio; }
      getSize(target: THREE.Vector2) { return target.set(this.width, this.height); }
      dispose = vi.fn(); forceContextLoss = vi.fn();
      constructor(options: { canvas: HTMLCanvasElement }) { this.domElement = options.canvas; state.renderer = this; }
    },
    PMREMGenerator: class {
      fromScene() { return new actual.WebGLRenderTarget(32, 32); }
      dispose = vi.fn();
    },
  };
});
vi.mock("three/addons/postprocessing/EffectComposer.js", async () => {
  const actual = await vi.importActual<typeof import("three/addons/postprocessing/EffectComposer.js")>(
    "three/addons/postprocessing/EffectComposer.js",
  );
  return { EffectComposer: class extends actual.EffectComposer {
    render = vi.fn();
    dispose = vi.fn(() => super.dispose());
    constructor(renderer: THREE.WebGLRenderer, target?: THREE.WebGLRenderTarget) {
      super(renderer, target);
      state.composer = this;
    }
  } };
});
vi.mock("three/addons/postprocessing/RenderPass.js", () => ({ RenderPass: class {
  dispose = vi.fn(); setSize = vi.fn();
  constructor(public scene: THREE.Scene, public camera: THREE.PerspectiveCamera) {}
} }));
vi.mock("three/addons/postprocessing/UnrealBloomPass.js", () => ({ UnrealBloomPass: class { dispose = vi.fn(); setSize = vi.fn(); } }));
vi.mock("three/addons/postprocessing/OutputPass.js", () => ({ OutputPass: class { dispose = vi.fn(); setSize = vi.fn(); } }));
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
  state.maxSamples = 4;
  const context = { fillStyle: "", fillRect() {}, strokeStyle: "", lineWidth: 0, strokeRect() {},
    beginPath() {}, moveTo() {}, lineTo() {}, stroke() {} };
  vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(context as never);
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
    let pool: THREE.SpotLight | undefined;
    scene.traverse(object => { if (object instanceof THREE.SpotLight) pool = object; });
    expect(pool!.shadow.mapSize.toArray()).toEqual([1024, 1024]);
    atmosphere.dispose();
  });

  it("populates the first still then freezes landscape and rain while the camera stays steady", () => {
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
    expect(camera.matrixWorld.toArray()).toEqual(initialCamera);
    expect(state.landscape!.update).toHaveBeenLastCalledWith(60);
    atmosphere.setReducedMotion!(true);
    const frozenCamera = camera.matrixWorld.toArray();
    atmosphere.update(frame(130));
    expect(droplets.material.uniforms.uTime.value).toBe(60);
    expect(camera.matrixWorld.toArray()).toEqual(frozenCamera);
    expect(state.landscape!.update).toHaveBeenCalledTimes(2);
    atmosphere.dispose();
  });

  it("keeps both responsive seated cameras fixed across elapsed time and pointer movement", () => {
    const atmosphere = construct();
    const { camera } = inspect();
    for (const [width, height] of [[1440, 1000], [393, 852]]) {
      atmosphere.resize({ width, height, devicePixelRatio: 2 });
      const initial = camera.matrixWorld.toArray();
      for (const elapsed of [0, 1, 30, 90, 600]) {
        atmosphere.update({ elapsed, delta: 0.05, pointer: { x: Math.sin(elapsed), y: Math.cos(elapsed) } });
        expect(camera.matrixWorld.toArray()).toEqual(initial);
      }
    }
    atmosphere.dispose();
  });

  it("rests the entire gently curved book on the table with no upright paper", () => {
    const atmosphere = construct();
    const { scene } = inspect();
    const book = scene.getObjectByName("Night Train open book")!;
    scene.updateMatrixWorld(true);
    const bounds = new THREE.Box3().setFromObject(book);
    expect(bounds.min.y).toBeCloseTo(0.7775, 6);
    expect(bounds.getSize(new THREE.Vector3()).y).toBeLessThan(0.03);
    let curvedTop = false;
    book.traverse(object => {
      if (!(object instanceof THREE.Mesh)) return;
      const normals = object.geometry.getAttribute("normal");
      for (let i = 0; i < normals.count; i++) {
        if (normals.getY(i) > 0.94 && normals.getY(i) < 0.999) curvedTop = true;
      }
    });
    expect(curvedTop).toBe(true);
    atmosphere.dispose();
  });

  it("uses real multisampled HalfFloat composer buffers and bounded retina canvas dimensions", () => {
    const atmosphere = construct();
    atmosphere.resize({ width: 1440, height: 1000, devicePixelRatio: 2 });
    const composer = state.composer!, canvas = state.renderer!.domElement;
    expect(composer.renderTarget1.samples).toBe(4);
    expect(composer.renderTarget2.samples).toBe(4);
    expect(composer.renderTarget1.texture.type).toBe(THREE.HalfFloatType);
    expect(composer.renderTarget2.texture.type).toBe(THREE.HalfFloatType);
    expect([canvas.width, canvas.height]).toEqual([2304, 1600]);
    expect([composer.renderTarget1.width, composer.renderTarget1.height]).toEqual([2304, 1600]);
    expect(composer.passes.map(pass => pass.constructor.name)).toEqual(["RenderPass", "UnrealBloomPass", "OutputPass"]);
    atmosphere.resize({ width: 3840, height: 2160, devicePixelRatio: 3 });
    expect([canvas.width, canvas.height]).toEqual([2560, 1440]);
    atmosphere.resize({ width: 393, height: 852, devicePixelRatio: 3 });
    expect([canvas.width, canvas.height]).toEqual([738, 1600]);
    atmosphere.dispose();
  });

  it.each([0, 2])("clamps composer MSAA to the supported %i samples", maxSamples => {
    state.maxSamples = maxSamples;
    const atmosphere = construct();
    expect(state.composer!.renderTarget1.samples).toBe(maxSamples);
    expect(state.composer!.renderTarget2.samples).toBe(maxSamples);
    atmosphere.dispose();
  });

  it("retains the original Room resolution and zero-sample buffers without the train opt-in", () => {
    const room = new Room({ canvas: document.createElement("canvas"), seed: 1, reducedMotion: false }, {
      camera: [0, 1, 3], target: [0, 1, 0], background: 0x101820,
    });
    const atmosphere = room.finish();
    atmosphere.resize({ width: 1440, height: 1000, devicePixelRatio: 2 });
    expect([state.renderer!.domElement.width, state.renderer!.domElement.height]).toEqual([1440, 1000]);
    expect(state.composer!.renderTarget1.samples).toBe(0);
    expect(state.composer!.renderTarget2.samples).toBe(0);
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
    const composerTarget1Dispose = vi.spyOn(composer.renderTarget1, "dispose");
    const composerTarget2Dispose = vi.spyOn(composer.renderTarget2, "dispose");
    atmosphere.dispose(); atmosphere.dispose();
    const cameraPosition = camera.position.toArray();
    atmosphere.update(frame(100)); atmosphere.resize({ width: 1, height: 1, devicePixelRatio: 1 });
    atmosphere.setReducedMotion!(false); atmosphere.render();
    expect(geometryDispose).toHaveBeenCalledTimes(1);
    expect(materialDispose).toHaveBeenCalledTimes(1);
    expect(targetDispose).toHaveBeenCalledTimes(1);
    expect(landscape.dispose).toHaveBeenCalledTimes(1);
    expect(composer.dispose).toHaveBeenCalledTimes(1);
    expect(composerTarget1Dispose).toHaveBeenCalledTimes(1);
    expect(composerTarget2Dispose).toHaveBeenCalledTimes(1);
    expect(renderer.dispose).toHaveBeenCalledTimes(1);
    expect(renderer.forceContextLoss).toHaveBeenCalledTimes(1);
    expect(composer.render).not.toHaveBeenCalled();
    expect(camera.position.toArray()).toEqual(cameraPosition);
    expect(scene.children).toHaveLength(0);
    expect(pane.parent).toBeNull();
  });
});
