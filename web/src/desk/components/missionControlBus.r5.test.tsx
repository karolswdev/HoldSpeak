// Conductor R5: the conveyor listened for a DOM `hs-broadcast` event that
// nothing sends, so a coder or belt frame never moved it before the next poll.
// It now reads the one runtime bus (useOnCoderFrame for `scope:"coder"`).
import { act, render } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useMissionControl } from "../missioncontrol";
import { useProjections } from "../projections";
import { useSteering } from "../steering";
import { MissionControlConveyor } from "./MissionControlConveyor";

const bus = vi.hoisted(() => ({ handlers: new Map<string, Set<(frame: unknown) => void>>() }));

vi.mock("../../runtime/RuntimeBus", () => {
  const value = {
    state: "connected",
    lastFrame: null,
    subscribe: (type: string, handler: (frame: unknown) => void) => {
      const set = bus.handlers.get(type) ?? new Set();
      set.add(handler);
      bus.handlers.set(type, set);
      return () => set.delete(handler);
    },
  };
  return { useRuntimeBus: () => value, useOptionalRuntimeBus: () => value, useRuntimeFrame: () => null };
});

function emit(frame: { type: string; data: unknown }) {
  for (const handler of bus.handlers.get(frame.type) ?? []) handler(frame);
}

describe("Mission Control follows the runtime bus (Conductor R5)", () => {
  const mcRefresh = vi.fn(async () => {});
  const grants = vi.fn(async () => {});
  const ambient = vi.fn(async () => {});
  const projRefresh = vi.fn(async () => {});
  let saved: {
    mc: ReturnType<typeof useMissionControl.getState>["refresh"];
    grants: ReturnType<typeof useSteering.getState>["refreshGrants"];
    ambient: ReturnType<typeof useProjections.getState>["refreshAmbient"];
    proj: ReturnType<typeof useProjections.getState>["refresh"];
  };

  beforeEach(() => {
    bus.handlers.clear();
    for (const fn of [mcRefresh, grants, ambient, projRefresh]) fn.mockClear();
    saved = {
      mc: useMissionControl.getState().refresh,
      grants: useSteering.getState().refreshGrants,
      ambient: useProjections.getState().refreshAmbient,
      proj: useProjections.getState().refresh,
    };
    useMissionControl.setState({ refresh: mcRefresh });
    useSteering.setState({ refreshGrants: grants });
    useProjections.setState({ refreshAmbient: ambient, refresh: projRefresh });
  });

  afterEach(() => {
    useMissionControl.setState({ refresh: saved.mc });
    useSteering.setState({ refreshGrants: saved.grants });
    useProjections.setState({ refreshAmbient: saved.ambient, refresh: saved.proj });
  });

  it("re-reads the pins and the belt on a coder frame", () => {
    render(<MissionControlConveyor />);
    expect(mcRefresh).toHaveBeenCalledTimes(1); // the mount tick
    expect(grants).toHaveBeenCalledTimes(1);

    act(() => emit({ type: "intel_status", data: { state: "ready", scope: "coder" } }));

    expect(mcRefresh).toHaveBeenCalledTimes(2);
    expect(grants).toHaveBeenCalledTimes(2);
    expect(ambient).toHaveBeenCalledTimes(2);
    expect(projRefresh).toHaveBeenCalledWith(true);
  });

  it("re-reads the belt only on a belt frame", () => {
    render(<MissionControlConveyor />);
    act(() => emit({ type: "intel_status", data: { scope: "belt" } }));
    expect(mcRefresh).toHaveBeenCalledTimes(2);
    expect(grants).toHaveBeenCalledTimes(1);
    expect(projRefresh).not.toHaveBeenCalled();
  });

  it("does not listen for the dead hs-broadcast DOM event", () => {
    const source = readFileSync(resolve(__dirname, "MissionControlConveyor.tsx"), "utf-8");
    expect(source).not.toContain("hs-broadcast");
  });
});
