/** HS-130-09 — one creation gesture → exactly one persisted Workbench.
 *
 * The old create path POSTed a blank Workbench up front and opened it; the
 * blank's template picker then created ANOTHER record, orphaning the blank.
 * Now the gesture opens the Automations app on its starters and persists
 * nothing until a starter is pressed. This test proves the gesture creates
 * no record (no apiRequest) and opens the app instead.
 */
import { describe, it, expect, beforeEach, vi } from "vitest";

import { apiRequest } from "../../../lib/api";

vi.mock("../../../lib/api", () => ({
  apiRequest: vi.fn(() =>
    Promise.resolve({ ok: true, json: () => Promise.resolve({}) }),
  ),
  apiFetch: vi.fn(() => Promise.resolve({})),
}));

vi.mock("../setup", () => ({ loadSetup: vi.fn(() => Promise.resolve(null)) }));
vi.mock("../repository", () => ({
  registerRepository: vi.fn(() => Promise.resolve({ repository: { id: "r" } })),
  fetchRepositories: vi.fn(() => Promise.resolve([])),
}));
vi.mock("../roadmap", () => ({ fetchRoadmaps: vi.fn(() => Promise.resolve([])) }));

import { useDesk } from "../../store";

describe("createPrimitive('workbench') — one gesture, one record", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useDesk.setState({ workbenchWindows: [], windowsById: {} });
  });

  it("persists NO record and opens the Automations app on its starters", async () => {
    await useDesk.getState().createPrimitive("workbench");

    // No orphan blank automation was POSTed by the gesture.
    expect(apiRequest).not.toHaveBeenCalled();
    // The app is open on New automation (the single record is minted by
    // the starter he presses).
    expect(useDesk.getState().places["automations/new"]).toBeTruthy();
    expect(useDesk.getState().windowsById["surface-workbenches"]).toBeTruthy();
    // No window was opened for a not-yet-existing record.
    expect(useDesk.getState().workbenchWindows).toHaveLength(0);
  });
});
