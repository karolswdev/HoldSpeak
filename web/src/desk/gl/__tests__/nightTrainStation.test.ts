import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as THREE from "three";
import { Room } from "../interiors/sceneKit";
import { createTrainStation } from "../interiors/nightTrainStation";
import { trainStationPosition } from "../interiors/nightTrainJourney";

beforeEach(() => {
  const gradient = () => ({ addColorStop: vi.fn() });
  const context = {
    fillStyle: "", strokeStyle: "", lineWidth: 1,
    fillRect: vi.fn(), strokeRect: vi.fn(), beginPath: vi.fn(),
    moveTo: vi.fn(), lineTo: vi.fn(), stroke: vi.fn(),
    createRadialGradient: gradient, createLinearGradient: gradient,
  };
  vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(context as never);
});
afterEach(() => vi.restoreAllMocks());

function construct() {
  const root = new THREE.Group(), parent = new THREE.Group();
  root.add(parent);
  const protectedObjects = new Set<THREE.Object3D>();
  const register = vi.fn(() => { throw new Error("Station assets must not be registered with Room"); });
  const room = {
    root, animated: protectedObjects, ticks: [], mesh: register,
    moving: <T extends THREE.Object3D>(object: T): T => { protectedObjects.add(object); return object; },
    group: (at: [number, number, number] = [0, 0, 0], owner: THREE.Object3D = root) => {
      const group = new THREE.Group(); group.position.set(...at); owner.add(group); return group;
    },
  } as unknown as Room;
  const station = createTrainStation(room, parent);
  const group = parent.getObjectByName("Train passing station") as THREE.Group;
  const mesh = (name: string) => group.getObjectByName(name) as THREE.Mesh<THREE.BufferGeometry, THREE.MeshStandardMaterial>;
  return { root, room, parent, protectedObjects, register, station, group, mesh };
}

function bounds(mesh: THREE.Mesh<THREE.BufferGeometry>) {
  mesh.geometry.computeBoundingBox();
  return mesh.geometry.boundingBox!;
}

describe("Night Train lakeside station", () => {
  it("builds a supported shore quay, open waiting-room apertures and an actual pitched roof", () => {
    const { root, group, station, mesh } = construct();
    const land = bounds(mesh("Train station shore footprint"));
    const platform = bounds(mesh("Train station platform"));
    const masonry = bounds(mesh("Train station masonry"));
    expect(land.min.y).toBeLessThan(0.30);
    expect(land.max.y).toBeGreaterThan(0.30);
    expect(platform.min.y).toBeCloseTo(land.max.y, 5);
    expect(platform.max.y).toBeCloseTo(0.78, 5);
    expect(masonry.min.y).toBeLessThan(0.30);
    expect(masonry.max.y).toBeGreaterThan(0.55);
    expect(land.max.x - land.min.x).toBeGreaterThan(platform.max.x - platform.min.x);
    const roof = mesh("Train station pitched roof");
    expect(bounds(roof).max.y).toBeGreaterThan(3.5);
    const normals = roof.geometry.getAttribute("normal");
    expect(Array.from({ length: normals.count }, (_, i) => Math.abs(normals.getY(i)))
      .some(y => y > 0.70 && y < 0.98)).toBe(true);

    // These rays inspect the rendered wall geometry: a window opens all the
    // way to the room's rear wall, while its neighbouring pier is close.
    station.update(180 / 1.08);
    root.updateMatrixWorld(true);
    const wall = mesh("Train station waiting room");
    const throughWindow = new THREE.Raycaster(new THREE.Vector3(0.85, 1.94, 0), new THREE.Vector3(0, 0, -1));
    const againstPier = new THREE.Raycaster(new THREE.Vector3(1.45, 1.94, 0), new THREE.Vector3(0, 0, -1));
    const windowHit = throughWindow.intersectObject(wall)[0];
    const pierHit = againstPier.intersectObject(wall)[0];
    expect(windowHit).toBeDefined(); expect(pierHit).toBeDefined();
    expect(windowHit.distance - pierHit.distance).toBeGreaterThan(1.5);
    expect(group.position.z).toBe(-6);
    station.dispose();
  });

  it("uses three capped framed lanterns with small amber cores and two bounded shadow spots", () => {
    const { group, station, mesh } = construct();
    const fixtures = group.children.filter(object => /^Train station lantern \d$/.test(object.name));
    expect(fixtures).toHaveLength(3);
    const cores = mesh("Train station warm lantern cores");
    const corePositions = cores.geometry.getAttribute("position");
    const metal = mesh("Train station lantern metalwork");
    const metalPositions = metal.geometry.getAttribute("position");
    expect(cores.material.emissive.r).toBeGreaterThan(cores.material.emissive.g);
    expect(cores.material.emissive.g).toBeGreaterThan(cores.material.emissive.b);
    expect(cores.material.emissiveIntensity).toBeLessThanOrEqual(1.2);
    expect(cores.material.toneMapped).toBe(true);
    fixtures.forEach(fixture => {
      const coreBounds = new THREE.Box3();
      let darkCapVertices = 0, frameVertices = 0;
      const bodyY = fixture.position.y + 1.88;
      for (let i = 0; i < corePositions.count; i++) {
        if (Math.abs(corePositions.getX(i) - fixture.position.x) < 0.08)
          coreBounds.expandByPoint(new THREE.Vector3().fromBufferAttribute(corePositions, i));
      }
      const size = coreBounds.getSize(new THREE.Vector3());
      expect(size.x).toBeLessThan(0.06); expect(size.z).toBeLessThan(0.06);
      expect(size.y).toBeCloseTo(0.13, 5);
      for (let i = 0; i < metalPositions.count; i++) {
        const dx = Math.abs(metalPositions.getX(i) - fixture.position.x);
        const dz = Math.abs(metalPositions.getZ(i) - fixture.position.z);
        const y = metalPositions.getY(i);
        if (dx < 0.16 && dz < 0.16 && y > bodyY + 0.13) darkCapVertices++;
        if (dx > 0.06 && dx < 0.10 && dz > 0.06 && dz < 0.10 && Math.abs(y - bodyY) < 0.15)
          frameVertices++;
      }
      expect(darkCapVertices).toBeGreaterThan(10);
      expect(frameVertices).toBeGreaterThan(10);
    });
    const glass = mesh("Train station lantern glass").material;
    expect(glass.transparent).toBe(true); expect(glass.opacity).toBeLessThan(0.20);
    expect(glass.depthWrite).toBe(false);
    const lights: THREE.SpotLight[] = [];
    group.traverse(object => { if (object instanceof THREE.SpotLight) lights.push(object); });
    expect(lights).toHaveLength(2);
    lights.forEach(light => {
      expect(light.distance).toBeLessThanOrEqual(5);
      expect(light.intensity).toBeLessThanOrEqual(11);
      expect(light.penumbra).toBe(1);
      expect(light.castShadow).toBe(true);
      expect(light.shadow.mapSize.toArray()).toEqual([512, 512]);
      expect(light.target.position.y).toBeLessThan(light.position.y);
    });
    expect(fixtures[1].children.some(object => object instanceof THREE.SpotLight)).toBe(true);
    station.dispose();
  });

  it("shares small construction-time textures at metre scales and keeps glass outside the shadow pass", () => {
    const { group, station, mesh } = construct();
    const textures = new Set<THREE.Texture>();
    group.traverse(object => {
      if (!(object instanceof THREE.Mesh)) return;
      const material = object.material as THREE.MeshStandardMaterial;
      if (material.map) textures.add(material.map);
      if (material.bumpMap) textures.add(material.bumpMap);
      if (material.emissiveMap) textures.add(material.emissiveMap);
    });
    expect(textures.size).toBe(5);
    for (const texture of textures) {
      expect(texture).toBeInstanceOf(THREE.CanvasTexture);
      expect(texture.image).toBeInstanceOf(HTMLCanvasElement);
      expect(Math.max(texture.image.width, texture.image.height)).toBeLessThanOrEqual(512);
      expect(texture.anisotropy).toBeLessThanOrEqual(4);
    }
    const plaster = mesh("Train station waiting room").material;
    expect(plaster.bumpMap).toBe(plaster.map);
    expect(plaster.bumpScale).toBeLessThan(0.015);
    const window = mesh("Train station warm waiting-room windows");
    expect(window.material.emissiveMap).toBe(window.material.map);
    expect(window.castShadow).toBe(false);
    const glass = mesh("Train station lantern glass");
    expect(glass.castShadow).toBe(false);
    expect(glass.receiveShadow).toBe(false);
    const floorUv = mesh("Train station platform").geometry.getAttribute("uv");
    const u = Array.from({ length: floorUv.count }, (_, index) => floorUv.getX(index));
    expect(Math.max(...u) - Math.min(...u)).toBeGreaterThan(20);
    expect(mesh("Train station timber canopy and bench").castShadow).toBe(true);
    station.dispose();
  });

  it("preserves direct assets through actual Room batching and follows only the authored journey clock", () => {
    const { room, group, station, protectedObjects, register } = construct();
    const meshes = group.children.filter(object => object instanceof THREE.Mesh) as THREE.Mesh[];
    expect(meshes.length).toBeLessThanOrEqual(11);
    expect(new Set(meshes.map(mesh => mesh.material)).size).toBe(meshes.length);
    expect(meshes.reduce((sum, mesh) => sum + mesh.geometry.getAttribute("position").count, 0)).toBeLessThan(20_000);
    expect(protectedObjects.has(group)).toBe(true);
    expect(meshes.every(mesh => protectedObjects.has(mesh))).toBe(true);
    Room.prototype.finish.call(room);
    expect(meshes.every(mesh => mesh.parent === group)).toBe(true);
    expect(register).not.toHaveBeenCalled();
    const vertices = meshes.map(mesh => Array.from(mesh.geometry.getAttribute("position").array));
    for (const elapsed of [0, 60, 165, 500, 1000, -1, 165]) {
      station.update(elapsed);
      expect(group.position.x).toBe(trainStationPosition(elapsed));
      expect(group.position.z).toBe(-6);
      meshes.forEach((mesh, index) => expect(Array.from(mesh.geometry.getAttribute("position").array)).toEqual(vertices[index]));
    }
    expect(room.ticks).toEqual([]);
    station.dispose();
  });

  it("releases its own merged resources once, leaves Room assets alive and ignores updates after disposal", () => {
    const { parent, group, station, register } = construct();
    const retainedGeometry = new THREE.BoxGeometry();
    const retainedMaterial = new THREE.MeshStandardMaterial();
    const retained = new THREE.Mesh(retainedGeometry, retainedMaterial);
    parent.add(retained);
    const roomGeometryDispose = vi.spyOn(retainedGeometry, "dispose");
    const roomMaterialDispose = vi.spyOn(retainedMaterial, "dispose");
    const meshes = group.children.filter(object => object instanceof THREE.Mesh) as THREE.Mesh[];
    const geometries = meshes.map(mesh => vi.spyOn(mesh.geometry, "dispose"));
    const materials = meshes.map(mesh => vi.spyOn(mesh.material as THREE.Material, "dispose"));
    const textures = new Set<THREE.Texture>();
    for (const mesh of meshes) {
      const material = mesh.material as THREE.MeshStandardMaterial;
      if (material.map) textures.add(material.map);
      if (material.bumpMap) textures.add(material.bumpMap);
      if (material.emissiveMap) textures.add(material.emissiveMap);
    }
    const textureDisposes = [...textures].map(texture => vi.spyOn(texture, "dispose"));
    const lights: THREE.SpotLight[] = [];
    group.traverse(object => {
      if (object instanceof THREE.SpotLight) lights.push(object);
    });
    const targetDisposes = lights.map(light => {
      light.shadow.map = new THREE.WebGLRenderTarget(8, 8);
      return vi.spyOn(light.shadow.map, "dispose");
    });
    const lightDisposes = lights.map(light => vi.spyOn(light, "dispose"));
    station.update(165);
    const lastX = group.position.x;
    station.dispose(); station.dispose(); station.update(200);
    expect(parent.children).toEqual([retained]);
    expect(group.children).toEqual([]);
    expect(group.position.x).toBe(lastX);
    geometries.forEach(dispose => expect(dispose).toHaveBeenCalledOnce());
    materials.forEach(dispose => expect(dispose).toHaveBeenCalledOnce());
    textureDisposes.forEach(dispose => expect(dispose).toHaveBeenCalledOnce());
    lightDisposes.forEach(dispose => expect(dispose).toHaveBeenCalledOnce());
    targetDisposes.forEach(dispose => expect(dispose).toHaveBeenCalledOnce());
    expect(roomGeometryDispose).not.toHaveBeenCalled();
    expect(roomMaterialDispose).not.toHaveBeenCalled();
    expect(register).not.toHaveBeenCalled();
    retainedGeometry.dispose(); retainedMaterial.dispose();
  });
});
