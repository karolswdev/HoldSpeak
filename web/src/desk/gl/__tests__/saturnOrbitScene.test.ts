import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as THREE from "three";
import { createSaturnOrbitScene } from "../saturnOrbitScene";
import { SATURN_MOONS, SATURN_OBLATENESS } from "../saturnOrbitModel";

const rendererState = vi.hoisted(() => ({ latest: null as null | {
  render: ReturnType<typeof vi.fn>; dispose: ReturnType<typeof vi.fn>;
  setSize: ReturnType<typeof vi.fn>; setPixelRatio: ReturnType<typeof vi.fn>;
} }));
vi.mock("three", async () => {
  const actual = await vi.importActual<typeof import("three")>("three");
  return { ...actual, WebGLRenderer: class {
    capabilities = { getMaxAnisotropy: () => 16 };
    render = vi.fn(); dispose = vi.fn(); setSize = vi.fn(); setPixelRatio = vi.fn();
    constructor() { rendererState.latest = this; }
  } };
});
class ControlledImage {
  static instances: ControlledImage[] = [];
  onload: (() => void) | null = null;
  onerror: (() => void) | null = null;
  src = "";
  constructor() { ControlledImage.instances.push(this); }
  removeAttribute(name: string) { if (name === "src") this.src = ""; }
}
beforeEach(() => { ControlledImage.instances = []; vi.stubGlobal("Image", ControlledImage); });
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });
const construct = (reducedMotion = false) => createSaturnOrbitScene({
  canvas: document.createElement("canvas"), seed: 0x53415455, reducedMotion,
});
const frame = (elapsed: number) => ({ elapsed, delta: 0.05, pointer: { x: 0.8, y: 0.6 } });
const inspect = () => rendererState.latest!.render.mock.calls.at(-1) as [THREE.Scene, THREE.OrthographicCamera];

describe("Saturn atmosphere lifecycle", () => {
  it("builds an oblate globe, depth-tested translucent rings and two sphere moons", () => {
    const atmosphere = construct(); atmosphere.render();
    const [scene] = inspect();
    const planet = scene.getObjectByName("Saturn") as THREE.Mesh;
    expect(planet.geometry).toBeInstanceOf(THREE.SphereGeometry);
    expect(planet.scale.y).toBe(SATURN_OBLATENESS);
    const rings = scene.getObjectByName("Saturn rings") as THREE.Mesh<THREE.RingGeometry, THREE.ShaderMaterial>;
    expect(rings.geometry).toBeInstanceOf(THREE.RingGeometry);
    expect(rings.material.transparent).toBe(true);
    expect(rings.material.depthTest).toBe(true);
    expect(rings.material.depthWrite).toBe(false);
    expect(rings.material.side).toBe(THREE.DoubleSide);
    for (const { name } of SATURN_MOONS) expect((scene.getObjectByName(name) as THREE.Mesh).geometry).toBeInstanceOf(THREE.SphereGeometry);
    expect(scene.getObjectByName("Orbital galactic sky")).toBeInstanceOf(THREE.Mesh);
    expect(scene.getObjectByName("Orbital stars")).toBeInstanceOf(THREE.Points);
    atmosphere.dispose();
  });

  it("freezes geometry, clouds and camera while refining the local sky map", () => {
    const atmosphere = construct(true);
    atmosphere.resize({ width: 393, height: 852, devicePixelRatio: 3 }); atmosphere.render();
    const [scene, camera] = inspect();
    const planet = scene.getObjectByName("Saturn") as THREE.Mesh<THREE.SphereGeometry, THREE.ShaderMaterial>;
    const titan = scene.getObjectByName("Titan")!;
    const initial = titan.position.clone(), initialCamera = camera.position.clone();
    atmosphere.update(frame(80));
    expect(titan.position.toArray()).toEqual(initial.toArray());
    expect(camera.position.toArray()).toEqual(initialCamera.toArray());
    expect(planet.material.uniforms.uCloudTime.value).toBe(0);
    ControlledImage.instances[0].onload!();
    expect(rendererState.latest!.render).toHaveBeenCalledTimes(2);
    expect(rendererState.latest!.setPixelRatio).toHaveBeenCalledWith(1.5);
    expect(rendererState.latest!.setSize).toHaveBeenCalledWith(393, 852, false);
    atmosphere.setReducedMotion!(false); atmosphere.update(frame(80));
    expect(titan.position.toArray()).not.toEqual(initial.toArray());
    expect(planet.material.uniforms.uCloudTime.value).toBe(80);
    expect(planet.rotation.y).not.toBe(0);
    atmosphere.setReducedMotion!(true);
    const rotation = planet.rotation.y, moved = titan.position.clone(), cameraMoved = camera.position.clone();
    atmosphere.update(frame(140));
    expect(planet.rotation.y).toBe(rotation);
    expect(titan.position.toArray()).toEqual(moved.toArray());
    expect(camera.position.toArray()).toEqual(cameraMoved.toArray());
    expect(planet.material.uniforms.uCloudTime.value).toBe(80);
    atmosphere.dispose();
  });

  it("keeps the globe and Titan visible at desktop and phone aspect ratios", () => {
    const atmosphere = construct();
    for (const [width, height] of [[1440, 900], [393, 852]]) {
      atmosphere.resize({ width, height, devicePixelRatio: 1 }); atmosphere.render();
      const [scene, camera] = inspect();
      scene.updateMatrixWorld(true); camera.updateMatrixWorld(true);
      for (const name of ["Saturn", "Titan"]) {
        const projected = scene.getObjectByName(name)!.getWorldPosition(new THREE.Vector3()).project(camera);
        expect(Math.abs(projected.x)).toBeLessThan(0.9);
        expect(Math.abs(projected.y)).toBeLessThan(0.9);
      }
    }
    atmosphere.dispose();
  });

  it("disposes each resource once and rejects callbacks after teardown", () => {
    const geometryDispose = vi.spyOn(THREE.BufferGeometry.prototype, "dispose");
    const materialDispose = vi.spyOn(THREE.Material.prototype, "dispose");
    const textureDispose = vi.spyOn(THREE.Texture.prototype, "dispose");
    const atmosphere = construct();
    const lateLoad = ControlledImage.instances[0].onload!;
    atmosphere.dispose(); atmosphere.dispose(); lateLoad();
    atmosphere.render(); atmosphere.update(frame(120));
    expect(rendererState.latest!.dispose).toHaveBeenCalledTimes(1);
    expect(rendererState.latest!.render).not.toHaveBeenCalled();
    expect(geometryDispose.mock.contexts.length).toBeGreaterThanOrEqual(5);
    expect(new Set(geometryDispose.mock.contexts).size).toBe(geometryDispose.mock.contexts.length);
    expect(new Set(materialDispose.mock.contexts).size).toBe(materialDispose.mock.contexts.length);
    expect(textureDispose).toHaveBeenCalledTimes(1);
    expect(ControlledImage.instances[0].src).toBe("");
    expect(ControlledImage.instances[0].onload).toBeNull();
  });
});
