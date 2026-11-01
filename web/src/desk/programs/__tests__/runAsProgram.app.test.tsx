// JRN13: Run as a program on a project's action row. The answers are the
// hub's own, recorded through the real route by
// tests/integration/test_desk_program_from_action.py (HOLDSPEAK_WIRE_WRITE=1).
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import madeFixture from "../__fixtures__/program.from_action.json";
import programFixture from "../__fixtures__/program.from_action.program.json";
import refusedFixture from "../__fixtures__/program.from_action.refused.json";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn(), openProgram: vi.fn() }));
vi.mock("../../../lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../lib/api")>()),
  apiFetch: mocks.apiFetch,
}));
vi.mock("../open", () => ({ openProgram: mocks.openProgram }));

import { ApiError } from "../../../lib/api";
import { RunAsProgramVerb } from "../RunAsProgram";

afterEach(() => { cleanup(); mocks.apiFetch.mockReset(); mocks.openProgram.mockReset(); });

describe("Run as a program (JRN13)", () => {
  it("makes a Drafting program from the action and opens its window", async () => {
    mocks.apiFetch.mockResolvedValue(madeFixture);
    render(<RunAsProgramVerb actionId="ai_runme" projectId="proj-holdspeak" title="Move the People routes" />);
    fireEvent.click(screen.getByRole("button", { name: "Run as a program: Move the People routes" }));
    const id = String((madeFixture as { id?: string }).id ?? (madeFixture as { program?: { id: string } }).program?.id);
    await waitFor(() => expect(mocks.openProgram).toHaveBeenCalledWith(id));
    expect(mocks.apiFetch).toHaveBeenCalledWith("/api/programs/from-action",
      { method: "POST", json: { action_id: "ai_runme", project_id: "proj-holdspeak" } });
    // The window it opens is the hub's: Drafting, the action as its origin, the goal its words.
    expect(programFixture.state).toBe("drafting");
    expect(programFixture.origin_ref).toBe("action:ai_runme");
    expect(programFixture.place.origin?.kind).toBe("action");
  });

  it("a refusal says the hub's words in place; nothing opens", async () => {
    mocks.apiFetch.mockRejectedValue(new ApiError(refusedFixture.status, "Not Found", refusedFixture.body));
    render(<RunAsProgramVerb actionId="ai_none" title="Gone" />);
    fireEvent.click(screen.getByTestId("run-as-program"));
    await waitFor(() => expect(screen.getByTestId("run-as-program-failed").textContent).toBe(refusedFixture.body.detail));
    expect(mocks.openProgram).not.toHaveBeenCalled();
  });
});
