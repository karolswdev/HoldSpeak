import {
  micPhase,
  subscribeCaptureLevel,
  subscribeMicPhase,
} from "../../lib/micSession";
import { useDesk } from "../store";
import type { AtmosphereActivitySource } from "./atmosphereRuntime";

/** Observes existing capture and Desk stores. No microphone acquisition,
 * network requests or scene-authored product state. */
export function observeAtmosphereActivity(): AtmosphereActivitySource & {
  dispose(): void;
} {
  let level = 0;
  let phase = micPhase();
  let recording = useDesk.getState().recording === "recording";
  let arrival = 0;
  let previousItems = useDesk.getState().items;
  const keys = (items: typeof previousItems) =>
    new Set(
      Object.entries(items).flatMap(([kind, objects]) =>
        objects.map((object) => `${kind}:${object.id}`),
      ),
    );
  let previousKeys = keys(previousItems);
  let initialized = useDesk.getState().updatedAt !== null;
  const listeners = new Set<() => void>();
  const notify = () => listeners.forEach((listener) => listener());
  const cleanup = [
    subscribeCaptureLevel((value) => {
      level = Number.isFinite(value) ? Math.min(Math.max(value * 5, 0), 1) : 0;
    }),
    subscribeMicPhase((next) => {
      phase = next;
      if (next === "closed" || next === "suspended") level = 0;
      notify();
    }),
    useDesk.subscribe((state) => {
      let changed = recording !== (state.recording === "recording");
      recording = state.recording === "recording";
      if (state.items !== previousItems) {
        const nextKeys = keys(state.items);
        if (initialized) {
          const added = [...nextKeys].filter(
            (key) => !previousKeys.has(key),
          ).length;
          arrival += added;
          changed ||= added > 0;
        }
        initialized = state.updatedAt !== null;
        previousItems = state.items;
        previousKeys = nextKeys;
      }
      if (changed) notify();
    }),
  ];
  return {
    read: () => ({
      recording,
      speaking: phase === "held" || phase === "segmenting",
      level,
      arrival,
    }),
    subscribe: (listener) => {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
    dispose: () => {
      cleanup.forEach((dispose) => dispose());
      listeners.clear();
    },
  };
}
