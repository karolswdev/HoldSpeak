import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as THREE from "three";
import { createJupiterOrbitScene } from "../jupiterOrbitScene";
import { JUPITER_SKY_STAR_COUNT } from "../jupiterOrbitModel";

const rendererState = vi.hoisted(() => ({
  latest: null as null | {
    render: ReturnType<typeof vi.fn>;
    dispose: ReturnType<typeof vi.fn>;
    setSize: ReturnType<typeof vi.fn>;
    setPixelRatio: ReturnType<typeof vi.fn>;
  },
}));

vi.mock("three", async () => {
  const actual = await vi.importActual<typeof import("three")>("three");
  return {
    ...actual,
    WebGLRenderer: class {
      capabilities = { getMaxAnisotropy: () => 16 };
      render = vi.fn();
      dispose = vi.fn();
      setSize = vi.fn();
      setPixelRatio = vi.fn();
      constructor() { rendererState.latest = this; }
    },
  };
});

class ControlledImage {
  static instances: ControlledImage[] = [];
  onload: (() => void) | null = null;
  onerror: (() => void) | null = null;
  src = "";
  removeAttribute(name: string) { if (name === "src") this.src = ""; }
  constructor() { ControlledImage.instances.push(this); }
}

beforeEach(() => {
  ControlledImage.instances = [];
  vi.stubGlobal("Image", ControlledImage);
});
afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

const construct = (reducedMotion = false) => createJupiterOrbitScene({
  canvas: document.createElement("canvas"), seed: 0x4a555049, reducedMotion,
});
const frame = (elapsed: number) => ({ delta: 0.05, elapsed, pointer: { x: 0.8, y: 0.6 } });

describe("Jupiter atmosphere lifecycle", () => {
  it("has actual separate sphere moons and keeps visitors absent initially", () => {
    const atmosphere = construct();
    atmosphere.render();
    const [scene] = rendererState.latest!.render.mock.calls[0] as [THREE.Scene];
    for (const name of ["Io", "Europa", "Ganymede", "Callisto"]) {
      const moon = scene.getObjectByName(name) as THREE.Mesh;
      expect(moon.geometry).toBeInstanceOf(THREE.SphereGeometry);
    }
    for (const name of ["pioneer", "voyager", "monolith"]) {
      expect(scene.getObjectByName(`Jupiter ${name}`)?.visible).toBe(false);
    }
    atmosphere.dispose();
  });

  it("refines both local maps while frozen and pauses cloud flow with the geometry", () => {
    const atmosphere = construct(true);
    atmosphere.resize({ width: 393, height: 852, devicePixelRatio: 3 });
    atmosphere.render();
    const renderer = rendererState.latest!;
    const [scene] = renderer.render.mock.calls[0] as [THREE.Scene];
    const moon = scene.getObjectByName("Io")!;
    const planet = scene.getObjectByName("Jupiter") as THREE.Mesh<THREE.SphereGeometry, THREE.ShaderMaterial>;
    const sky = scene.getObjectByName("Jupiter galactic sky") as THREE.Mesh<THREE.PlaneGeometry, THREE.ShaderMaterial>;
    const initial = moon.position.clone();
    atmosphere.update(frame(80));
    expect(moon.position.toArray()).toEqual(initial.toArray());
    expect(planet.material.uniforms.uCloudTime.value).toBe(0);
    ControlledImage.instances[0].onload!();
    ControlledImage.instances[1].onload!();
    expect(renderer.render).toHaveBeenCalledTimes(3);
    expect(planet.material.uniforms.uReady.value).toBe(true);
    expect(sky.material.uniforms.uSkyReady.value).toBe(true);
    expect(renderer.setPixelRatio).toHaveBeenCalledWith(1.5);
    expect(renderer.setSize).toHaveBeenCalledWith(393, 852, false);
    atmosphere.setReducedMotion!(false);
    atmosphere.update(frame(80));
    expect(moon.position.toArray()).not.toEqual(initial.toArray());
    expect(planet.material.uniforms.uCloudTime.value).toBe(80);
    atmosphere.setReducedMotion!(true);
    atmosphere.update(frame(140));
    expect(planet.material.uniforms.uCloudTime.value).toBe(80);
    atmosphere.dispose();
  });

  it("has a rich seeded star field with a sparse bright tier and galactic depth", () => {
    const atmosphere = construct();
    atmosphere.render();
    const [scene] = rendererState.latest!.render.mock.calls[0] as [THREE.Scene];
    const stars = scene.getObjectByName("Jupiter stars") as THREE.Points;
    const positions = stars.geometry.getAttribute("position");
    const sizes = stars.geometry.getAttribute("aSize");
    expect(positions.count).toBe(JUPITER_SKY_STAR_COUNT);
    expect(positions.count).toBeGreaterThanOrEqual(18_000);
    let bright = 0, near = 0, far = 0;
    for (let index = 0; index < positions.count; index++) {
      if (sizes.getX(index) >= 3.4) bright++;
      if (positions.getZ(index) > -30) near++;
      if (positions.getZ(index) < -50) far++;
    }
    expect(bright).toBeGreaterThan(40);
    expect(bright).toBeLessThan(200);
    expect(near).toBeGreaterThan(2000);
    expect(far).toBeGreaterThan(2000);
    expect(scene.getObjectByName("Jupiter galactic sky")).toBeInstanceOf(THREE.Mesh);
    atmosphere.dispose();
  });

  it("retains procedural planet and star field if either local map fails", () => {
    const atmosphere = construct(true);
    ControlledImage.instances[0].onerror!();
    ControlledImage.instances[1].onerror!();
    const [scene] = rendererState.latest!.render.mock.calls[0] as [THREE.Scene];
    const planet = scene.getObjectByName("Jupiter") as THREE.Mesh<THREE.SphereGeometry, THREE.ShaderMaterial>;
    const sky = scene.getObjectByName("Jupiter galactic sky") as THREE.Mesh<THREE.PlaneGeometry, THREE.ShaderMaterial>;
    expect(planet.material.uniforms.uReady.value).toBe(false);
    expect(sky.material.uniforms.uSkyReady.value).toBe(false);
    expect(ControlledImage.instances[0].src).toBe("");
    expect(ControlledImage.instances[1].src).toBe("");
    atmosphere.dispose();
  });

  it("disposes each owned resource once and ignores a captured late image callback", () => {
    const disposeGeometry = vi.spyOn(THREE.BufferGeometry.prototype, "dispose");
    const disposeMaterial = vi.spyOn(THREE.Material.prototype, "dispose");
    const disposeTexture = vi.spyOn(THREE.Texture.prototype, "dispose");
    const atmosphere = construct();
    const images = ControlledImage.instances;
    const lateLoads = images.map(image => image.onload!);
    atmosphere.dispose();
    atmosphere.dispose();
    for (const lateLoad of lateLoads) lateLoad();
    atmosphere.render();
    atmosphere.update(frame(900));
    expect(rendererState.latest!.dispose).toHaveBeenCalledTimes(1);
    expect(rendererState.latest!.render).not.toHaveBeenCalled();
    expect(disposeGeometry.mock.contexts.length).toBeGreaterThan(20);
    expect(new Set(disposeGeometry.mock.contexts).size).toBe(disposeGeometry.mock.contexts.length);
    expect(new Set(disposeMaterial.mock.contexts).size).toBe(disposeMaterial.mock.contexts.length);
    expect(disposeTexture).toHaveBeenCalledTimes(3);
    for (const image of images) {
      expect(image.onload).toBeNull();
      expect(image.onerror).toBeNull();
      expect(image.src).toBe("");
    }
  });
});
