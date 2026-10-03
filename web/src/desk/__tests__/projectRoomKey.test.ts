// PHILO-9-03 (F1): ONE registered key opens a project's Room. The key
// `project-room` was registered nowhere and its fallback `/projects` is no
// route, so eight callers (the Chair, the shade, recall, the meeting review)
// opened nothing. The census closes the class (handover XXX law 9): no
// source file may ask for `project-room` again; its mutation proves the check
// bites.
import { afterEach, describe, expect, it, vi } from "vitest";
import { __resetSurfaces, openProjectRoom, PROJECT_ROOM_KEY, registerSurface } from "../shell";
import { DESK_APPLICATIONS } from "../applications";

const sources = import.meta.glob<string>("/src/**/*.{ts,tsx}", { query: "?raw", import: "default", eager: true });

/** Every surface-open call in `text` that names the dead key. */
export function deadRoomCalls(text: string): string[] {
  return [...text.matchAll(/open(?:Surface|SurfaceOr|SurfaceWhenReady)\(\s*["'`]project-room["'`]/g)].map((m) => m[0]);
}

describe("PHILO-9-03 F1: the one Room key", () => {
  afterEach(() => __resetSurfaces());

  it("the Room key is a registered Desk application", () => {
    expect(PROJECT_ROOM_KEY).toBe("open-project-memory");
    expect(DESK_APPLICATIONS.some((a) => a.action === PROJECT_ROOM_KEY)).toBe(true);
  });

  it("openProjectRoom opens that key scoped to the project", () => {
    const opener = vi.fn();
    registerSurface(PROJECT_ROOM_KEY, opener);
    openProjectRoom("proj-1");
    openProjectRoom("");
    expect(opener.mock.calls).toEqual([
      ["project:proj-1", undefined],
      [undefined, undefined],
    ]);
  });

  it("no source file asks for the dead key (census)", () => {
    const offenders = Object.entries(sources)
      .filter(([path]) => !/__tests__|\.test\./.test(path))
      .flatMap(([path, text]) => deadRoomCalls(text).map((call) => `${path}: ${call}`));
    expect(offenders).toEqual([]);
  });

  it("mutation: the census catches a caller that re-adds the dead key", () => {
    expect(deadRoomCalls('openSurfaceOr("project-room", "/projects", id);')).toHaveLength(1);
    expect(deadRoomCalls("openSurface('project-room', scope)")).toHaveLength(1);
  });
});
