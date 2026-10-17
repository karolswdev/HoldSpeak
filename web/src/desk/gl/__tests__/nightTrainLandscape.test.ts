import { afterEach, describe, expect, it, vi } from "vitest";
import * as THREE from "three";
import { randomSource, type Room } from "../interiors/sceneKit";
import { createTrainLandscape } from "../interiors/nightTrainLandscape";
import { TRAIN_TREE_LAYERS } from "../interiors/nightTrainJourney";

function fakeRoom(seed = 73) {
  const protectedObjects = new Set<THREE.Object3D>();
  const root = new THREE.Group();
  const room = {
    root, random: randomSource(seed),
    moving: <T extends THREE.Object3D>(object: T): T => { protectedObjects.add(object); return object; },
    group: (at: [number, number, number] = [0, 0, 0], parent: THREE.Object3D = root) => {
      const group = new THREE.Group(); group.position.set(...at); parent.add(group); return group;
    },
  } as unknown as Room;
  return { room, protectedObjects };
}
afterEach(() => vi.restoreAllMocks());

describe("Night Train landscape ownership", () => {
  it("initializes layered actual geometry behind the window and protects moving assets from batching", () => {
    const { room, protectedObjects } = fakeRoom();
    const landscape = createTrainLandscape(room);
    const world = room.root.getObjectByName("Night train landscape")!;
    expect(protectedObjects.has(world)).toBe(true);
    for (let index = 0; index < 4; index++) {
      const ridge = world.getObjectByName(`Train ridge layer ${index}`)!;
      expect(protectedObjects.has(ridge)).toBe(true);
      expect(ridge.position.z).toBeLessThan(-3);
      const shape = (ridge.children[0] as THREE.Mesh).geometry;
      expect(shape.getAttribute("position").count).toBeGreaterThan(30_000);
      const normal = shape.getAttribute("normal");
      const slopes = new Set(Array.from({length: normal.count},(_,i) => normal.getY(i).toFixed(2)));
      expect(slopes.size).toBeGreaterThan(index >= 2 ? 10 : 20);
    }
    const water = world.getObjectByName("Train lake") as THREE.Mesh;
    expect(water.position.z).toBeLessThan(-3);
    expect(water.position.y).toBeCloseTo(0.30);
    expect(water.position.z + (water.geometry as THREE.PlaneGeometry).parameters.height / 2).toBeLessThan(-3);
    for (const layer of TRAIN_TREE_LAYERS) {
      const trees = world.getObjectByName(`Train ${layer.name} trees`) as THREE.InstancedMesh;
      expect(trees.count).toBe(layer.count);
      const matrix = new THREE.Matrix4();
      trees.getMatrixAt(0, matrix);
      expect(matrix.elements[14]).toBeLessThan(-3);
      expect(matrix.elements.every(Number.isFinite)).toBe(true);
      expect(protectedObjects.has(trees.parent!)).toBe(true);
    }
    const platform = world.getObjectByName("Train station platform") as THREE.Mesh<THREE.BoxGeometry>;
    expect(platform.position.y - platform.geometry.parameters.height / 2).toBeGreaterThan(water.position.y);
    const posts = world.getObjectByName("Train station posts") as THREE.InstancedMesh<THREE.CylinderGeometry>;
    const post = new THREE.Matrix4(); posts.getMatrixAt(0,post);
    expect(post.elements[13] - posts.geometry.parameters.height / 2)
      .toBeCloseTo(platform.position.y + platform.geometry.parameters.height / 2);
    landscape.dispose();
  });

  it("is seeded, deterministic at a time, and changes water and layers only on explicit update", () => {
    const { room } = fakeRoom(), { room: other } = fakeRoom();
    const landscape = createTrainLandscape(room), copy = createTrainLandscape(other);
    const trees = room.root.getObjectByName("Train near vegetation trees") as THREE.InstancedMesh;
    const copied = other.root.getObjectByName("Train near vegetation trees") as THREE.InstancedMesh;
    expect(trees.instanceMatrix.array).toEqual(copied.instanceMatrix.array);
    const initial = Array.from(trees.instanceMatrix.array);
    const layers = TRAIN_TREE_LAYERS.map(layer => room.root.getObjectByName(`Train ${layer.name} trees`) as THREE.InstancedMesh);
    const shapes = layers.map(layer => Array.from(layer.instanceMatrix.array));
    landscape.update(35); copy.update(35);
    layers.forEach((layer,index) => {
      Array.from(layer.instanceMatrix.array).forEach((value,component) => {
        if(component % 16 !== 12) expect(value).toBe(shapes[index][component]);
      });
    });
    expect(trees.instanceMatrix.array).toEqual(copied.instanceMatrix.array);
    expect(Array.from(trees.instanceMatrix.array)).not.toEqual(initial);
    const lake = room.root.getObjectByName("Train lake") as THREE.Mesh<THREE.BufferGeometry, THREE.ShaderMaterial>;
    expect(lake.material.uniforms.uTime.value).toBe(35);
    const moved = Array.from(trees.instanceMatrix.array); landscape.update(35);
    expect(Array.from(trees.instanceMatrix.array)).toEqual(moved);
    landscape.dispose(); copy.dispose();
  });

  it("disposes direct geometries, materials and instance buffers once without touching Room assets", () => {
    const { room } = fakeRoom();
    const retainedGeometry = new THREE.BoxGeometry(), retainedMaterial = new THREE.MeshBasicMaterial();
    const retained = new THREE.Mesh(retainedGeometry, retainedMaterial); room.root.add(retained);
    const geometryDisposes = vi.spyOn(THREE.BufferGeometry.prototype, "dispose");
    const materialDisposes = vi.spyOn(THREE.Material.prototype, "dispose");
    const instanceDisposes = vi.spyOn(THREE.InstancedMesh.prototype, "dispose");
    const landscape = createTrainLandscape(room);
    const world = room.root.getObjectByName("Night train landscape")!;
    const water = world.getObjectByName("Train lake") as THREE.Mesh<THREE.BufferGeometry, THREE.ShaderMaterial>;
    landscape.dispose(); landscape.dispose(); landscape.update(100);
    expect(room.root.children).toEqual([retained]);
    expect(water.material.uniforms.uTime.value).toBe(0);
    expect(geometryDisposes).toHaveBeenCalledTimes(10);
    expect(materialDisposes).toHaveBeenCalledTimes(11);
    expect(instanceDisposes).toHaveBeenCalledTimes(5);
    expect(new Set(geometryDisposes.mock.contexts).size).toBe(geometryDisposes.mock.contexts.length);
    expect(new Set(materialDisposes.mock.contexts).size).toBe(materialDisposes.mock.contexts.length);
    expect(geometryDisposes.mock.contexts).not.toContain(retainedGeometry);
    expect(materialDisposes.mock.contexts).not.toContain(retainedMaterial);
  });
});
