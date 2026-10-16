import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as THREE from "three";
import { createOrbitalSky, ORBITAL_SKY_STAR_COUNT } from "../orbitalSky";

class ControlledImage {
  static instances: ControlledImage[] = [];
  onload: (() => void) | null = null;
  onerror: (() => void) | null = null;
  src = "";
  removeAttribute(name: string) { if (name === "src") this.src = ""; }
  constructor() { ControlledImage.instances.push(this); }
}
beforeEach(() => { ControlledImage.instances = []; vi.stubGlobal("Image", ControlledImage); });
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });

describe("shared local orbital sky", () => {
  it("seeds rich distant stars repeatably and bounds their DPR", () => {
    const scene = new THREE.Scene(), other = new THREE.Scene();
    const sky = createOrbitalSky(scene, 81, vi.fn()), copy = createOrbitalSky(other, 81, vi.fn());
    const stars = scene.getObjectByName("Orbital stars") as THREE.Points<THREE.BufferGeometry, THREE.ShaderMaterial>;
    const copied = other.getObjectByName("Orbital stars") as THREE.Points;
    const position = stars.geometry.getAttribute("position");
    expect(position.count).toBe(ORBITAL_SKY_STAR_COUNT);
    expect(position.array).toEqual(copied.geometry.getAttribute("position").array);
    const sizes = stars.geometry.getAttribute("aSize");
    let bright = 0, near = 0, far = 0;
    for (let i = 0; i < position.count; i++) {
      if (sizes.getX(i) >= 3.4) bright++;
      if (position.getZ(i) > -30) near++;
      if (position.getZ(i) < -50) far++;
    }
    expect(bright).toBeGreaterThan(40); expect(bright).toBeLessThan(200);
    expect(near).toBeGreaterThan(2000); expect(far).toBeGreaterThan(2000);
    sky.setDpr(3); expect(stars.material.uniforms.uDpr.value).toBe(1.5);
    sky.dispose(); copy.dispose();
  });

  it("refines a still on load or failure and retains the procedural fallback", () => {
    for (const succeeds of [true, false]) {
      const scene = new THREE.Scene(), ready = vi.fn();
      const sky = createOrbitalSky(scene, 1, ready);
      const image = ControlledImage.instances.at(-1)!;
      const dust = scene.getObjectByName("Orbital galactic sky") as THREE.Mesh<THREE.PlaneGeometry, THREE.ShaderMaterial>;
      if (succeeds) image.onload!(); else image.onerror!();
      expect(ready).toHaveBeenCalledTimes(1);
      expect(dust.material.uniforms.uSkyReady.value).toBe(succeeds);
      expect(image.onload).toBeNull(); expect(image.onerror).toBeNull();
      sky.dispose();
    }
  });

  it("disposes exactly once, removes only its objects and ignores captured late callbacks", () => {
    const geometries = vi.spyOn(THREE.BufferGeometry.prototype, "dispose");
    const materials = vi.spyOn(THREE.Material.prototype, "dispose");
    const textures = vi.spyOn(THREE.Texture.prototype, "dispose");
    const scene = new THREE.Scene(), retained = new THREE.Group(), ready = vi.fn();
    scene.add(retained);
    const sky = createOrbitalSky(scene, 1, ready), image = ControlledImage.instances[0];
    const load = image.onload!, error = image.onerror!;
    sky.dispose(); sky.dispose(); load(); error(); sky.setDpr(2);
    expect(scene.children).toEqual([retained]);
    expect(ready).not.toHaveBeenCalled(); expect(image.src).toBe("");
    expect(geometries).toHaveBeenCalledTimes(2);
    expect(materials).toHaveBeenCalledTimes(2);
    expect(textures).toHaveBeenCalledTimes(1);
  });
});
