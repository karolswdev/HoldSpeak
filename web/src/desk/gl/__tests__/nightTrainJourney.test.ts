import { describe, expect, it } from "vitest";
import { TRAIN_TERRAIN_SPAN, TRAIN_TERRAIN_SPEEDS, TRAIN_TREE_LAYERS, trainRidgeHeight, trainTerrainHeight, trainStationPosition, trainTravelPosition } from "../interiors/nightTrainJourney";

describe("Night Train continuous journey", () => {
  it("bounds population, separates depths and locks each wood layer to its terrain", () => {
    expect(TRAIN_TREE_LAYERS.reduce((total, layer) => total + layer.count, 0)).toBeLessThanOrEqual(240);
    expect(new Set(TRAIN_TREE_LAYERS.map(layer => layer.depth)).size).toBe(3);
    expect(TRAIN_TREE_LAYERS[0].speed).toBe(TRAIN_TERRAIN_SPEEDS[2]);
    expect(TRAIN_TREE_LAYERS[1].speed).toBe(TRAIN_TERRAIN_SPEEDS[2]);
    expect(TRAIN_TREE_LAYERS[2].speed).toBe(TRAIN_TERRAIN_SPEEDS[3]);
    expect(TRAIN_TREE_LAYERS[2].speed).toBeGreaterThan(TRAIN_TREE_LAYERS[0].speed);
  });

  it("travels smoothly in the visible world and recycles only far outside its view", () => {
    for (const layer of TRAIN_TREE_LAYERS) {
      expect(trainTravelPosition(0, 0, layer.speed, layer.spread)).toBe(0);
      expect(trainTravelPosition(0, 20.001, layer.speed, layer.spread) - trainTravelPosition(0, 20, layer.speed, layer.spread))
        .toBeCloseTo(-0.001 * layer.speed, 8);
      const before = trainTravelPosition(-layer.spread / 2 + 0.01, 0, layer.speed, layer.spread);
      const after = trainTravelPosition(-layer.spread / 2 + 0.01, 0.02 / layer.speed, layer.speed, layer.spread);
      expect(Math.abs(before)).toBeGreaterThan(100); expect(Math.abs(after)).toBeGreaterThan(100);
    }
    expect(trainTravelPosition(4, -1, 1, 600)).toBe(4);
  });

  it("gives terrain full depth with gullies, peaks and continuous heightfield boundaries", () => {
    for(let layer=0;layer<4;layer++){
      expect(trainTerrainHeight(23,0,layer,0.67)).not.toBe(trainTerrainHeight(23,8,layer,0.67));
      expect(trainTerrainHeight(23,4,layer,0.67)).toBeCloseTo(trainTerrainHeight(23+TRAIN_TERRAIN_SPAN,4,layer,0.67),9);
    }
  });

  it("joins long terrain cycles continuously and keeps the station occasional", () => {
    for (let layer = 0; layer < 4; layer++) {
      expect(trainRidgeHeight(18, layer, 0.67)).toBeCloseTo(trainRidgeHeight(18 + TRAIN_TERRAIN_SPAN, layer, 0.67), 10);
      expect(Number.isFinite(trainRidgeHeight(-123, layer, 0.67))).toBe(true);
    }
    expect(trainStationPosition(0)).toBe(180);
    expect(trainStationPosition(180 / 1.08)).toBeCloseTo(0);
    expect(Math.abs(trainStationPosition(300))).toBeGreaterThan(100);
  });
});
