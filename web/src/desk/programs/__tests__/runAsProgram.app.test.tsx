// JRN13: Run as a program on a project's action row. The answers are the
// hub's own, recorded through the real route by
// tests/integration/test_desk_program_from_action.py (HOLDSPEAK_WIRE_WRITE=1).
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import madeFixture from "../__fixtures__/program.from_action.json";
import programFixture from "../__fixtures__/program.from_action.program.json";
import refusedFixture from "../__fixtures__/program.from_action.refused.json";
import projectsFixture from "../__fixtures__/program.create_projects.json";
import createdFixture from "../__fixtures__/program.create_project.json";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn(), openProgram: vi.fn() }));
vi.mock("../../../lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../lib/api")>()),
  apiFetch: mocks.apiFetch,
}));
vi.mock("../open", () => ({ openProgram: mocks.openProgram }));

import { ApiError } from "../../../lib/api";
import { RunAsProgramVerb } from "../RunAsProgram";
import { runNoteAsProgram } from "../fromNote";

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

// Run as a program from a Note: a note in no project goes to the project the
// wizard picks (the window's scope's, else the only one). The answers are the
// hub's own (tests/integration/test_desk_programs.py, HOLDSPEAK_WIRE_WRITE=1).
describe("Run as a program from a Note", () => {
  const rows = (projectsFixture.response.body as { projects: { id: string }[] }).projects;
  const answer = (one: unknown) => (path: string, init?: { method?: string }) =>
    Promise.resolve(path === "/api/projects" && !init?.method ? one : createdFixture.response.body);
  const posted = () => mocks.apiFetch.mock.calls.filter(([path, init]) => path === "/api/programs" && init?.method === "POST")
    .map(([, init]) => init.json);
  const note = { id: "note-1", title: "Recap", body: "Add a recap to the Note." };

  it("a note in no project goes to the only project", async () => {
    mocks.apiFetch.mockImplementation(answer({ projects: [rows[0]] }));
    expect(await runNoteAsProgram({ ...note, projectId: null })).toBeNull();
    expect(posted()).toEqual([{ title: "Recap", goal: note.body, template: "fast-cycle", origin_ref: "note:note-1", project_id: rows[0].id }]);
    expect(mocks.openProgram).toHaveBeenCalledWith(createdFixture.response.body.id);
  });

  it("with several projects, the window's scope's project", async () => {
    mocks.apiFetch.mockImplementation(answer(projectsFixture.response.body));
    expect(await runNoteAsProgram({ ...note, scopeProjectId: rows[1].id })).toBeNull();
    expect(posted()[0].project_id).toBe(rows[1].id);
  });

  it("the note's own project wins; no project list is read", async () => {
    mocks.apiFetch.mockImplementation(answer(projectsFixture.response.body));
    await runNoteAsProgram({ ...note, projectId: rows[1].id, scopeProjectId: rows[0].id });
    expect(posted()[0].project_id).toBe(rows[1].id);
    expect(mocks.apiFetch.mock.calls.some(([path]) => path === "/api/projects")).toBe(false);
  });

  it("several projects and no scope: no project is guessed", async () => {
    mocks.apiFetch.mockImplementation(answer(projectsFixture.response.body));
    await runNoteAsProgram(note);
    expect(posted()[0]).not.toHaveProperty("project_id");
  });
});
