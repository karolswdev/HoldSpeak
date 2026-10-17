import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as THREE from "three";
import { createMarsOrbitScene } from "../marsOrbitScene";
import { MARS_MOONS, MARS_RADIUS, MARS_MEAN_RADIUS_KM } from "../marsOrbitModel";

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
  onload: (() => void) | null = null; onerror: (() => void) | null = null; src = "";
  removeAttribute(name: string) { if (name === "src") this.src = ""; }
  constructor() { ControlledImage.instances.push(this); }
}
beforeEach(() => { ControlledImage.instances = []; vi.stubGlobal("Image", ControlledImage); });
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });
const construct = (reducedMotion = false) => createMarsOrbitScene({ canvas: document.createElement("canvas"), seed: 123, reducedMotion });
const frame = (elapsed: number) => ({ elapsed, delta: 0.05, pointer: { x: 0.8, y: 0.6 } });

describe("Mars atmosphere lifecycle", () => {
  it("builds distinct irregular cratered moons with real depth and a thin atmospheric shell", () => {
    const atmosphere = construct(); atmosphere.render();
    const [scene] = rendererState.latest!.render.mock.calls[0] as [THREE.Scene];
    const mars = scene.getObjectByName("Mars") as THREE.Mesh<THREE.SphereGeometry>;
    const limb = scene.getObjectByName("Mars atmosphere") as THREE.Mesh<THREE.SphereGeometry>;
    expect(limb.geometry.parameters.radius / mars.geometry.parameters.radius).toBeLessThan(1.004);
    const moons = ["Phobos", "Deimos"].map(name => scene.getObjectByName(name) as THREE.Mesh);
    expect(moons[0].geometry).not.toBe(moons[1].geometry);
    expect(moons[0].position.z).toBeGreaterThan(0); expect(moons[1].position.z).toBeLessThan(0);
    for (const moon of moons) {
      const positions = moon.geometry.getAttribute("position");
      let minimum = Infinity, maximum = 0;
      for (let i = 0; i < positions.count; i++) {
        const radius = Math.hypot(positions.getX(i), positions.getY(i), positions.getZ(i));
        minimum = Math.min(minimum, radius); maximum = Math.max(maximum, radius);
      }
      expect(maximum / minimum).toBeGreaterThan(1.15);
    }
    atmosphere.dispose();
  });

  it("preserves physical equivalent volumes in closed irregular meshes without size compensation", () => {
    const atmosphere = construct(); atmosphere.render();
    const [scene, camera] = rendererState.latest!.render.mock.calls[0] as [THREE.Scene, THREE.Camera];
    expect(camera).toBeInstanceOf(THREE.OrthographicCamera);
    const mars = scene.getObjectByName("Mars") as THREE.Mesh<THREE.SphereGeometry, THREE.ShaderMaterial>;
    const shadowRadii = mars.material.uniforms.uRadii.value as number[];
    MARS_MOONS.forEach((moon, index) => {
      const mesh = scene.getObjectByName(moon.name) as THREE.Mesh<THREE.SphereGeometry>;
      const positions = mesh.geometry.getAttribute("position"), indices = mesh.geometry.index!;
      let signedVolume = 0;
      // Independent determinant expansion over the rendered triangles.
      for (let i = 0; i < indices.count; i += 3) {
        const a = indices.getX(i), b = indices.getX(i + 1), c = indices.getX(i + 2);
        signedVolume += (positions.getX(a) * (positions.getY(b) * positions.getZ(c) - positions.getZ(b) * positions.getY(c))
          - positions.getY(a) * (positions.getX(b) * positions.getZ(c) - positions.getZ(b) * positions.getX(c))
          + positions.getZ(a) * (positions.getX(b) * positions.getY(c) - positions.getY(b) * positions.getX(c))) / 6;
      }
      const physicalMappedRadius = MARS_RADIUS * moon.physicalRadiusKm / MARS_MEAN_RADIUS_KM;
      const targetVolume = 4 * Math.PI * physicalMappedRadius ** 3 / 3;
      expect(Math.abs(signedVolume) / targetVolume).toBeCloseTo(1, 6);
      expect(mesh.scale.toArray()).toEqual([1, 1, 1]);
      expect(mesh.parent!.scale.toArray()).toEqual([1, 1, 1]);
      expect(shadowRadii[index]).toBe(physicalMappedRadius);
      const columns = mesh.geometry.parameters.widthSegments + 1;
      for (let row = 0; row <= mesh.geometry.parameters.heightSegments; row++) {
        const first = row * columns;
        const isPole = row === 0 || row === mesh.geometry.parameters.heightSegments;
        for (let column = isPole ? 1 : columns - 1; column < columns; column++) {
          for (const read of ["getX", "getY", "getZ"] as const) {
            expect(positions[read](first + column)).toBe(positions[read](first));
          }
        }
      }
    });
    expect(scene.children.some(child => child instanceof THREE.Sprite)).toBe(false);
    atmosphere.dispose();
  });

  it("keeps the globe and initial foreground moon inside portrait and desktop framing", () => {
    const atmosphere = construct(true);
    for (const [width, height] of [[393, 852], [1440, 900]]) {
      atmosphere.resize({ width, height, devicePixelRatio: 3 }); atmosphere.render();
      const [scene, camera] = rendererState.latest!.render.mock.calls.at(-1)! as [THREE.Scene, THREE.OrthographicCamera];
      const planet = scene.getObjectByName("Mars") as THREE.Mesh<THREE.SphereGeometry>;
      const centre = planet.getWorldPosition(new THREE.Vector3());
      expect(centre.x - planet.geometry.parameters.radius).toBeGreaterThan(camera.left);
      expect(centre.x + planet.geometry.parameters.radius).toBeLessThan(camera.right);
      const phobos = scene.getObjectByName("Phobos")!.getWorldPosition(new THREE.Vector3());
      expect(phobos.x).toBeGreaterThan(camera.left + 0.4);
      expect(phobos.x).toBeLessThan(camera.right - 0.4);
    }
    atmosphere.dispose();
  });

  it("freezes all motion, resizes and refines both local maps while frozen, and resumes together", () => {
    const atmosphere = construct(true); atmosphere.render();
    const renderer = rendererState.latest!;
    const [scene, camera] = renderer.render.mock.calls[0] as [THREE.Scene, THREE.Camera];
    const planet = scene.getObjectByName("Mars") as THREE.Mesh<THREE.SphereGeometry, THREE.ShaderMaterial>;
    const phobos = scene.getObjectByName("Phobos")!;
    const moonInitial = phobos.position.clone(), cameraInitial = camera.position.clone(), rotation = planet.rotation.y;
    atmosphere.update(frame(80));
    expect(phobos.position.toArray()).toEqual(moonInitial.toArray());
    expect(camera.position.toArray()).toEqual(cameraInitial.toArray()); expect(planet.rotation.y).toBe(rotation);
    atmosphere.resize({ width: 393, height: 852, devicePixelRatio: 3 });
    ControlledImage.instances.forEach(image => image.onload!());
    expect(renderer.render).toHaveBeenCalledTimes(3);
    expect(planet.material.uniforms.uReady.value).toBe(true);
    expect(renderer.setPixelRatio).toHaveBeenCalledWith(1.5);
    expect(renderer.setSize).toHaveBeenCalledWith(393, 852, false);
    atmosphere.setReducedMotion!(false); atmosphere.update(frame(80));
    expect(phobos.position.toArray()).not.toEqual(moonInitial.toArray()); expect(planet.rotation.y).not.toBe(rotation);
    const moved = phobos.position.clone(), rotated = planet.rotation.y, cameraMoved = camera.position.clone();
    atmosphere.setReducedMotion!(true); atmosphere.update(frame(140));
    expect(phobos.position.toArray()).toEqual(moved.toArray()); expect(planet.rotation.y).toBe(rotated);
    expect(camera.position.toArray()).toEqual(cameraMoved.toArray());
    atmosphere.dispose();
  });

  it("retains procedural fallback when a local map fails", () => {
    const atmosphere = construct(true);
    ControlledImage.instances.forEach(image => image.onerror!());
    const [scene] = rendererState.latest!.render.mock.calls[0] as [THREE.Scene];
    const mars = scene.getObjectByName("Mars") as THREE.Mesh<THREE.SphereGeometry, THREE.ShaderMaterial>;
    expect(mars.material.uniforms.uReady.value).toBe(false);
    expect(rendererState.latest!.render).toHaveBeenCalledTimes(2);
    expect(ControlledImage.instances.every(image => image.src === "")).toBe(true);
    atmosphere.dispose();
  });

  it("disposes each resource once and ignores late loads, errors, resize, render and update", () => {
    const geometries = vi.spyOn(THREE.BufferGeometry.prototype, "dispose");
    const materials = vi.spyOn(THREE.Material.prototype, "dispose");
    const textures = vi.spyOn(THREE.Texture.prototype, "dispose");
    const atmosphere = construct();
    const images = ControlledImage.instances;
    const callbacks = images.flatMap(image => [image.onload!, image.onerror!]);
    atmosphere.dispose(); atmosphere.dispose(); callbacks.forEach(callback => callback());
    atmosphere.render(); atmosphere.update(frame(140)); atmosphere.resize({ width: 1440, height: 900, devicePixelRatio: 2 });
    expect(rendererState.latest!.dispose).toHaveBeenCalledTimes(1);
    expect(rendererState.latest!.render).not.toHaveBeenCalled(); expect(rendererState.latest!.setSize).not.toHaveBeenCalled();
    expect(geometries).toHaveBeenCalledTimes(6); expect(materials).toHaveBeenCalledTimes(6); expect(textures).toHaveBeenCalledTimes(2);
    expect(new Set(geometries.mock.contexts).size).toBe(geometries.mock.contexts.length);
    expect(new Set(materials.mock.contexts).size).toBe(materials.mock.contexts.length);
    expect(images.every(image => image.onload === null && image.onerror === null && image.src === "")).toBe(true);
  });
});
