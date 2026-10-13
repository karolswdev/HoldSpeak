// PHILO-9-03 (F1): ONE registered key opens a project's Room. The key
// `project-room` was registered nowhere and its fallback `/projects` is no
// route, so eight callers opened nothing. `openProjectRoom` is the one way in.
import { afterEach, describe, expect, it, vi } from "vitest";
import { __resetSurfaces, openProjectRoom, PROJECT_ROOM_KEY, registerSurface } from "../shell";
import { DESK_APPLICATIONS } from "../applications";

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

});
