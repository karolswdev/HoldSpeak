// New Project (the Door), app-level: the real Desk store, the real window
// host (SurfaceWindows) and the real DoorCore/useDoorController. Only
// apiFetch is mocked, with the hub's real answers:
//   GET  /api/connections  -> {tools: [...]}  (decodeConnectionsResponse)
//   POST /api/projects/door -> {projectId}    (ProjectDoorService.create; a blank
//        create is exempt, so the route adds no kernel fields; fenced by
//        tests/integration/test_desk_new_project.py)
//
// replaces: tests/e2e/test_hs169_door_legs_glass.py::test_cancel_door
// replaces: tests/e2e/test_hs169_door_legs_glass.py::test_blank_project (the Door-closes half;
//           the zero-watches half is tests/integration/test_desk_new_project.py)

import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { __resetSurfaces, stageSurfaceOpen } from "../../../../desk/shell";
import { SurfaceWindows } from "../../../../desk/components/SurfaceWindows";
import { useDesk } from "../../../../desk/store";

const apiFetch = vi.fn();
vi.mock("../../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../../lib/api")>("../../../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});

const DOOR_WINDOW = "surface-project-setup";
const NEW_PROJECT_ID = "proj_0a1b2c3d4e5f60718293a4b5";

function doorPosts(): Array<[string, { method?: string; json?: Record<string, unknown> }]> {
  return apiFetch.mock.calls.filter(
    ([url, init]) => String(url) === "/api/projects/door" && (init as { method?: string } | undefined)?.method === "POST",
  ) as Array<[string, { method?: string; json?: Record<string, unknown> }]>;
}

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
  useDesk.setState({
    windowsById: {},
    panelRects: {},
    panelSaved: [],
    panelOrder: [],
    panelMin: [],
    panelMax: [],
    zoneWindows: [],
    zoneViewPrefs: {},
  });
  __resetSurfaces();
  apiFetch.mockReset();
  apiFetch.mockImplementation((url: string, init?: { method?: string }) => {
    if (url === "/api/connections") return Promise.resolve({ tools: [] });
    if (url === "/api/projects/door" && init?.method === "POST") {
      return Promise.resolve({ projectId: NEW_PROJECT_ID });
    }
    // Everything else the Room window asks for once it opens: an empty answer.
    return Promise.resolve({});
  });
});

afterEach(__resetSurfaces);

/** The same open the browser test made: a staged `project-setup` open the
 *  window host consumes once its registry is ready. */
async function openTheDoor(): Promise<void> {
  stageSurfaceOpen("project-setup");
  render(<SurfaceWindows />);
  await screen.findByTestId("door-root", undefined, { timeout: 5000 });
  expect(useDesk.getState().windowsById[DOOR_WINDOW]?.applicationKey).toBe("project-setup");
}

describe("New Project: the Door", () => {
  it("Cancel closes the Door and creates no project", async () => {
    await openTheDoor();

    fireEvent.change(screen.getByTestId("door-outcome-input"), { target: { value: "This will be cancelled" } });
    fireEvent.click(screen.getByTestId("door-cancel"));

    await waitFor(() => expect(screen.queryByTestId("door-root")).toBeNull());
    expect(useDesk.getState().windowsById[DOOR_WINDOW]).toBeUndefined();
    expect(doorPosts()).toHaveLength(0);
  });

  it("Create with no sources sends a blank project, opens its Room and closes the Door", async () => {
    await openTheDoor();

    expect(screen.getByTestId("door-receipt").textContent).toBe("NO SOURCES · BLANK PROJECT");
    fireEvent.change(screen.getByTestId("door-outcome-input"), {
      target: { value: "Blank project for glass test" },
    });
    await act(async () => {
      fireEvent.click(screen.getByTestId("door-create"));
    });

    await waitFor(() => expect(screen.queryByTestId("door-root")).toBeNull());
    expect(doorPosts()).toHaveLength(1);
    expect(doorPosts()[0][1].json).toEqual({ outcome: "Blank project for glass test", sources: [] });
    expect(useDesk.getState().windowsById[DOOR_WINDOW]).toBeUndefined();
    expect(useDesk.getState().windowsById["surface-project-memory"]?.scope).toBe(`project:${NEW_PROJECT_ID}`);
  });
});
