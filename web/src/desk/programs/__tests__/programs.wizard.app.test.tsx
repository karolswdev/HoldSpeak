/* The Programs app (T2), New program: the wizard inside the window, the
 * creation context and the templates.
 *
 * The mocks, the recorded hub answers and the helpers are in
 * programs.test-setup.tsx, shared by every programs.*.app.test.tsx. */
import {
  dreamingFixture, createProjectsFixture, createProjectFixture, createNoRepositoryFixture,
  createRepositoryRequiredFixture, createPersonFixture, resetScreenMembers, needsYouRecorded,
  roomPrograms13, mocks, ApiError, ProgramsCore, ProgramBody, SurfaceWindowHost, useDesk,
  EMPTY_ITEMS, programsCss, clone, list, calls, hub, status, renderWindow, menuWords, menuItem,
  type Program, type ProgramList, type SurfaceRow,
} from "./programs.test-setup";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { lazy } from "react";

describe("New program is a wizard inside the window (owner, live walk 2026-11-08; recorded real wire)", () => {
  type Capture = { request: { method: string; path: string; json?: Record<string, unknown> }; response: { status: number; body: unknown } };
  const projects = createProjectsFixture as unknown as Capture;
  const made = createProjectFixture as unknown as Capture;
  const noRepository = createNoRepositoryFixture as unknown as Capture;
  const required = createRepositoryRequiredFixture as unknown as Capture;
  const madeProgram = made.response.body as Program;
  const roster = (projects.response.body as { projects: Array<{ id: string; name: string }> }).projects;
  const nameOf = (id: unknown) => roster.find((row) => row.id === id)!.name;
  const refusal = (capture: Capture) => () => {
    const body = capture.response.body as { error?: string };
    throw new ApiError(capture.response.status, body.error ?? "", capture.response.body);
  };
  const posts = () => calls.filter((call) => call.startsWith("POST /api/programs"));
  /** The bodies he sent, parsed (the recorded fixture sorts its keys). */
  const sent = () => posts().map((call) => JSON.parse(call.slice("POST /api/programs ".length)));
  const rowOf = (id: string) => screen.getAllByTestId("programs-wizard-project")
    .find((node) => within(node).getByTestId("programs-wizard-name").textContent === nameOf(id))!;
  const choose = (id: string) => fireEvent.click(within(rowOf(id)).getByTestId("programs-wizard-pick"));
  const next = () => screen.getByTestId("programs-wizard-next") as HTMLButtonElement;
  const ready = () => screen.findAllByTestId("programs-wizard-project");
  const templateItem = (name: string) => [...document.querySelectorAll<HTMLElement>("[role=menuitem],[role=menuitemradio]")]
    .find((node) => node.textContent?.startsWith(`${name} · `))!;
  /** Where → Go with nothing but the project chosen. */
  const toGo = () => { fireEvent.click(next()); fireEvent.click(next()); fireEvent.click(next()); };

  it("the recorded scenario is one coherent roster: the made Program and the refusal name its members", () => {
    expect(made.request.json).toEqual({ title: "New program", template: "fast-cycle", project_id: madeProgram.project_id });
    expect(made.response.status).toBe(201);
    expect(madeProgram.state).toBe("drafting");
    expect(roster.map((row) => row.id)).toContain(madeProgram.project_id);
    expect(roster.map((row) => row.id)).toContain(noRepository.request.json!.project_id);
    expect(required.request.json).toEqual({ title: "New program", template: "fast-cycle" });
  });

  // Fails on main: New program there opens the inline "Choose a project" well (programs-make), no wizard.
  it("New program replaces the list with the wizard at step 1 (Where): the projects as rows and a folder row; Next waits for a choice", async () => {
    hub({ "GET /api/programs": list, "GET /api/projects": projects.response.body, "POST /api/programs": made.response.body });
    renderWindow(<ProgramsCore />);
    await screen.findAllByTestId("programs-band");
    // A Project filter is on: it is never the creation target.
    fireEvent.click(screen.getByTestId("programs-project"));
    fireEvent.click(menuItem("HoldSpeak"));
    fireEvent.click(screen.getByTestId("programs-new"));
    const wizard = await screen.findByTestId("programs-wizard");
    expect(wizard.getAttribute("data-template")).toBe("fast-cycle");
    expect(screen.getByTestId("programs-wizard-step-1")).toBeTruthy();
    // The body is the wizard: the list is gone, the toolbar and the status bar stay.
    expect(screen.queryByTestId("programs-list")).toBeNull();
    expect(screen.getByTestId("programs-toolbar")).toBeTruthy();
    expect(screen.getByTestId("programs-status")).toBeTruthy();
    expect(screen.queryByTestId("programs-make")).toBeNull();
    const rows = await ready();
    expect(rows.map((row) => within(row).getByTestId("programs-wizard-pick").textContent)).toEqual(roster.map((row) => row.name));
    expect(screen.getByTestId("programs-wizard-folder").textContent).toBe("A folder on this machine");
    // Two projects: none is chosen for him; Next waits.
    expect(rows.some((row) => row.hasAttribute("data-selected"))).toBe(false);
    expect(next().disabled).toBe(true);
    await waitFor(() => expect(document.activeElement).toBe(within(rows[0]).getByTestId("programs-wizard-pick")));
    fireEvent.click(next());
    expect(screen.getByTestId("programs-wizard-step-1")).toBeTruthy();
    choose(madeProgram.project_id as string);
    expect(screen.getByTestId("programs-wizard-card-name").textContent).toBe(nameOf(madeProgram.project_id));
    expect(next().disabled).toBe(false);
    // The progress: four dots in the title bar, the first is now; none in the bar.
    const dots = within(screen.getByTestId("window-head")).getByTestId("programs-wizard-dots").querySelectorAll(".surface-progress-dot");
    expect([...dots].map((dot) => dot.getAttribute("data-state"))).toEqual(["now", null, null, null]);
    expect(posts()).toEqual([]);
  });

  it("the four steps: Where, What (title, brief, templates), How (control in his words, agent, review, check, spending), Go; Create posts the recorded body once and opens it", async () => {
    hub({ "GET /api/programs": list, "GET /api/projects": projects.response.body, "POST /api/programs": made.response.body });
    renderWindow(<ProgramsCore />);
    await screen.findAllByTestId("programs-band");
    fireEvent.click(screen.getByTestId("programs-new"));
    await ready();
    choose(madeProgram.project_id as string);
    fireEvent.click(next());
    const what = screen.getByTestId("programs-wizard-step-2");
    expect(within(what).getByLabelText("Title")).toBeTruthy();
    expect(within(what).getByLabelText("Brief")).toBeTruthy();
    // The default template is a quiet word on the card; one press opens the chips.
    expect(within(what).queryByRole("group", { name: "Template" })).toBeNull();
    fireEvent.click(screen.getByTestId("programs-wizard-template"));
    expect(within(what).getByRole("group", { name: "Template" })).toBeTruthy();
    await waitFor(() => expect(document.activeElement).toBe(within(what).getByLabelText("Title")));
    fireEvent.click(next());
    const how = screen.getByTestId("programs-wizard-step-3");
    expect(within(how).getByRole("button", { name: "Runs by itself" })).toBeTruthy();
    expect(within(how).getByRole("button", { name: "Asks before it merges or sends" })).toBeTruthy();
    expect(within(how).getByRole("button", { name: "Asks at every step" })).toBeTruthy();
    expect(screen.getByTestId("programs-wizard-agent")).toBeTruthy();
    expect(screen.getByTestId("programs-wizard-reviewer")).toBeTruthy();
    expect(screen.getByTestId("programs-wizard-spending").textContent).toBe("Not capped");
    fireEvent.click(next());
    expect(screen.getByTestId("programs-wizard-step-4")).toBeTruthy();
    expect(screen.getByTestId("programs-wizard-sum-where").textContent).toBe(nameOf(madeProgram.project_id));
    expect(screen.getByTestId("programs-wizard-sum-title").textContent).toBe("New program · Fast cycle");
    expect(screen.queryByTestId("programs-wizard-next")).toBeNull();
    const dots = screen.getByTestId("programs-wizard-dots").querySelectorAll(".surface-progress-dot");
    expect([...dots].map((dot) => dot.getAttribute("data-state"))).toEqual(["done", "done", "done", "now"]);
    // Back keeps what he chose.
    fireEvent.click(screen.getByTestId("programs-wizard-back"));
    expect(screen.getByTestId("programs-wizard-step-3")).toBeTruthy();
    fireEvent.click(next());
    expect(posts()).toEqual([]);
    fireEvent.click(screen.getByTestId("programs-wizard-create"));
    await waitFor(() => expect(mocks.openPullout).toHaveBeenCalledWith(`program:${madeProgram.id}`));
    expect(sent()).toEqual([made.request.json]);
    // Back to the list, which reads again.
    await waitFor(() => expect(screen.queryByTestId("programs-wizard")).toBeNull());
    expect(await screen.findByTestId("programs-list")).toBeTruthy();
    expect(calls.filter((call) => call === "GET /api/programs").length).toBeGreaterThan(1);
  });

  it("what he sets in What and How rides on the body: title, brief, control and template", async () => {
    hub({ "GET /api/programs": list, "GET /api/projects": projects.response.body, "POST /api/programs": made.response.body });
    renderWindow(<ProgramsCore />);
    await screen.findAllByTestId("programs-band");
    fireEvent.click(screen.getByTestId("programs-new"));
    await ready();
    choose(madeProgram.project_id as string);
    fireEvent.click(next());
    expect(screen.getByTestId("programs-wizard-template").textContent).toBe("Template · Fast cycle");
    fireEvent.click(screen.getByTestId("programs-wizard-template"));
    fireEvent.click(within(screen.getByRole("group", { name: "Template" })).getByRole("button", { name: /^Build and review/ }));
    // A template that is not the default keeps its chips above the title.
    expect(screen.queryByTestId("programs-wizard-template")).toBeNull();
    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "Ship the wizard" } });
    fireEvent.change(screen.getByLabelText("Brief"), { target: { value: "Four steps, one screen each." } });
    fireEvent.click(next());
    fireEvent.click(screen.getByRole("button", { name: "Runs by itself" }));
    fireEvent.click(next());
    expect(screen.getByTestId("programs-wizard-sum-title").textContent).toBe("Ship the wizard · Build and review");
    expect(screen.getByTestId("programs-wizard-sum-how").textContent).toBe("Runs by itself");
    fireEvent.click(screen.getByTestId("programs-wizard-create"));
    await waitFor(() => expect(mocks.openPullout).toHaveBeenCalledWith(`program:${madeProgram.id}`));
    expect(sent()).toEqual([{
      ...made.request.json, title: "Ship the wizard", template: "build-and-review", goal: "Four steps, one screen each.", control: "yolo",
    }]);
  });

  describe("Person: who reviews the person-gated steps (recorded People roster and create body)", () => {
    const scene = createPersonFixture as unknown as { readiness: Capture; people: Capture; made: Capture };
    const persons = (scene.people.response.body as { relationships: Array<{ id: string; display_name: string }> }).relationships;
    const picked = scene.made.request.json!.for_person_id as string;
    const pickedName = persons.find((row) => row.id === picked)!.display_name;
    const personHub = () => hub({
      "GET /api/programs": list, "GET /api/projects": projects.response.body,
      "GET /api/people/readiness": scene.readiness.response.body,
      "GET /api/people/relationships": scene.people.response.body,
      "POST /api/programs": scene.made.response.body,
    });
    const toHow = async () => {
      renderWindow(<ProgramsCore />);
      await screen.findAllByTestId("programs-band");
      fireEvent.click(screen.getByTestId("programs-new"));
      await ready();
      choose(scene.made.request.json!.project_id as string);
      fireEvent.click(next());
      fireEvent.click(next());
    };
    beforeEach(() => resetScreenMembers());

    it("the recorded scene: the made Program carries the person the body names", () => {
      expect((scene.made.response.body as Program).for_person_id).toBe(picked);
      expect(persons.length).toBeGreaterThan(1);
    });

    // Fails on main: the How screen has Agent and Review only, no Person row.
    it("the How screen has a Person row under Review: Nobody yet, then the People roster when it opens; no People read before", async () => {
      personHub();
      await toHow();
      const how = screen.getByTestId("programs-wizard-step-3");
      const person = within(how).getByTestId("programs-wizard-person");
      expect(person.textContent).toBe("Nobody yet");
      const labels = [...how.querySelectorAll(".gadget-row")].map((row) => row.querySelector(".gadget-row-label")?.textContent?.trim());
      expect(labels.indexOf("Person")).toBe(labels.indexOf("Review") + 1);
      expect(calls.some((call) => call.startsWith("GET /api/people"))).toBe(false);
      fireEvent.click(person);
      await waitFor(() => expect(menuItem(pickedName)).toBeTruthy());
      expect(persons.every((row) => menuItem(row.display_name))).toBe(true);
      expect(menuItem("Nobody yet").getAttribute("aria-checked")).toBe("true");
    });

    it("a picked person rides on the body as for_person_id and the summary names her; Nobody yet sends no field", async () => {
      personHub();
      await toHow();
      fireEvent.click(screen.getByTestId("programs-wizard-person"));
      await waitFor(() => expect(menuItem(pickedName)).toBeTruthy());
      fireEvent.click(menuItem(pickedName));
      expect(screen.getByTestId("programs-wizard-person").textContent).toBe(pickedName);
      fireEvent.click(next());
      expect(screen.getByTestId("programs-wizard-sum-review").textContent).toBe(`The template's · ${pickedName} reviews`);
      fireEvent.click(screen.getByTestId("programs-wizard-create"));
      await waitFor(() => expect(posts()).toHaveLength(1));
      expect(sent()).toEqual([scene.made.request.json]);
      cleanup();
      calls.length = 0;
      resetScreenMembers();
      // No pick: no field, and no Review row on the summary.
      personHub();
      await toHow();
      fireEvent.click(next());
      expect(screen.queryByTestId("programs-wizard-sum-review")).toBeNull();
      fireEvent.click(screen.getByTestId("programs-wizard-create"));
      await waitFor(() => expect(posts()).toHaveLength(1));
      expect(sent()[0]).not.toHaveProperty("for_person_id");
      expect(sent()).toEqual([made.request.json]);
    });
  });

  it("the only project, or the scope's project, is chosen for him", async () => {
    const one = { projects: [(projects.response.body as { projects: unknown[] }).projects[1]] };
    hub({ "GET /api/programs": list, "GET /api/projects": one });
    renderWindow(<ProgramsCore />);
    await screen.findAllByTestId("programs-band");
    fireEvent.click(screen.getByTestId("programs-new"));
    // The screen opens on the card: Next is one press.
    expect((await screen.findByTestId("programs-wizard-card-name")).textContent).toBe(roster[1].name);
    expect(screen.queryByTestId("programs-wizard-project")).toBeNull();
    expect(next().disabled).toBe(false);
    cleanup();
    hub({ "GET /api/programs": list, "GET /api/projects": projects.response.body });
    renderWindow(<ProgramsCore scope={`project:${roster[1].id}`} />);
    await screen.findAllByTestId("programs-band");
    fireEvent.click(screen.getByTestId("programs-new"));
    expect((await screen.findByTestId("programs-wizard-card-name")).textContent).toBe(roster[1].name);
    // Change returns to the rows, the scope's project still the selection.
    fireEvent.click(screen.getByTestId("programs-wizard-change"));
    await ready();
    expect(rowOf(roster[1].id).hasAttribute("data-selected")).toBe(true);
    expect(rowOf(roster[0].id).hasAttribute("data-selected")).toBe(false);
  });

  it("A folder on this machine: Next waits for the folder, and the body names the repository, not a project", async () => {
    hub({ "GET /api/programs": list, "GET /api/projects": projects.response.body, "POST /api/programs": made.response.body });
    renderWindow(<ProgramsCore />);
    await screen.findAllByTestId("programs-band");
    fireEvent.click(screen.getByTestId("programs-new"));
    await ready();
    fireEvent.click(screen.getByTestId("programs-wizard-folder"));
    expect(next().disabled).toBe(true);
    fireEvent.change(screen.getByLabelText("Folder"), { target: { value: "~/dev/tools/HoldSpeak" } });
    toGo();
    expect(screen.getByTestId("programs-wizard-sum-where").textContent).toBe("~/dev/tools/HoldSpeak");
    fireEvent.click(screen.getByTestId("programs-wizard-create"));
    await waitFor(() => expect(posts()).toHaveLength(1));
    expect(sent()).toEqual([{ title: "New program", template: "fast-cycle", repository: "~/dev/tools/HoldSpeak" }]);
  });

  it("Escape, Cancel and New again return to the list with no POST; a template opens the wizard with its template", async () => {
    hub({ "GET /api/programs": list, "GET /api/projects": projects.response.body });
    renderWindow(<ProgramsCore />);
    fireEvent.click(await screen.findByTestId("programs-templates"));
    fireEvent.click(templateItem("Build and review"));
    expect((await screen.findByTestId("programs-wizard")).getAttribute("data-template")).toBe("build-and-review");
    await ready();
    choose(roster[0].id);
    fireEvent.click(next());
    fireEvent.keyDown(screen.getByLabelText("Title"), { key: "Escape" });
    expect(screen.queryByTestId("programs-wizard")).toBeNull();
    expect(screen.getByTestId("programs-list")).toBeTruthy();
    expect(document.activeElement).toBe(screen.getByTestId("programs-new"));
    // New program pressed again closes the wizard (a toggle).
    fireEvent.click(screen.getByTestId("programs-new"));
    expect(await screen.findByTestId("programs-wizard-step-1")).toBeTruthy();
    fireEvent.click(screen.getByTestId("programs-new"));
    expect(screen.queryByTestId("programs-wizard")).toBeNull();
    fireEvent.click(screen.getByTestId("programs-new"));
    await ready();
    // The title bar's narrow Back says Cancel while the wizard is open.
    expect(screen.getByTestId("window-back").textContent).toBe("Cancel");
    fireEvent.click(screen.getByTestId("window-back"));
    expect(screen.queryByTestId("programs-wizard")).toBeNull();
    expect(screen.getByTestId("window-back").textContent).toBe("Back");
    cleanup();
    hub({ "GET /api/projects": projects.response.body });
    renderWindow(<ProgramsCore />);
    await screen.findByText("No program yet");
    // The empty object's own Button (not the toolbar's New program).
    fireEvent.click(screen.getAllByRole("button", { name: /New program/ }).find((node) => node.getAttribute("data-testid") !== "programs-new")!);
    expect((await screen.findByTestId("programs-wizard")).getAttribute("data-template")).toBe("fast-cycle");
    expect(posts()).toEqual([]);
  });

  it("the project read: loading, failed with the state species' retry, then the rows", async () => {
    let answer: unknown = new ApiError(503, "down", {});
    hub({ "GET /api/programs": list, "GET /api/projects": () => { if (answer instanceof Error) throw answer; return answer; } });
    renderWindow(<ProgramsCore />);
    await screen.findAllByTestId("programs-band");
    fireEvent.click(screen.getByTestId("programs-new"));
    expect(screen.getByTestId("programs-wizard-reading")).toBeTruthy();
    const failed = await screen.findByTestId("programs-wizard-read-failed");
    expect(failed.textContent).toContain("The projects did not load");
    expect(next().disabled).toBe(true);
    answer = projects.response.body;
    fireEvent.click(within(failed).getByRole("button"));
    expect(await ready()).toHaveLength(roster.length);
    expect(posts()).toEqual([]);
  });

  it("the recorded no_repository refusal names the project; no window opens", async () => {
    hub({ "GET /api/programs": list, "GET /api/projects": projects.response.body, "POST /api/programs": refusal(noRepository) });
    renderWindow(<ProgramsCore />);
    await screen.findAllByTestId("programs-band");
    fireEvent.click(screen.getByTestId("programs-new"));
    await ready();
    const target = noRepository.request.json!.project_id as string;
    choose(target);
    toGo();
    fireEvent.click(screen.getByTestId("programs-wizard-create"));
    const words = await screen.findByTestId("programs-wizard-refused");
    expect(words.textContent).toBe(`Not made · ${nameOf(target)} has no local repository · Add one in the project, or choose a different project`);
    expect(sent()).toEqual([noRepository.request.json]);
    expect(mocks.openPullout).not.toHaveBeenCalled();
    expect(document.body.textContent).not.toContain("Nothing changed");
  });

  it.each([
    ["a hub failure", () => { throw new ApiError(500, "program_failed", { code: "program_failed" }); }],
    ["an answer with no id", () => ({})],
    ["an empty id", () => ({ ...madeProgram, id: "" })],
    ["an id that is not a string", () => ({ ...madeProgram, id: 7 })],
    ["a 409 with another code", () => { throw new ApiError(409, "conflict", { code: "changed" }); }],
  ])("%s is not confirmed: no retry, no window, no Nothing changed", async (_name, answer) => {
    hub({ "GET /api/programs": list, "GET /api/projects": projects.response.body, "POST /api/programs": answer });
    renderWindow(<ProgramsCore />);
    await screen.findAllByTestId("programs-band");
    fireEvent.click(screen.getByTestId("programs-new"));
    await ready();
    choose(madeProgram.project_id as string);
    toGo();
    fireEvent.click(screen.getByTestId("programs-wizard-create"));
    expect((await screen.findByTestId("programs-wizard-unknown")).textContent)
      .toBe("Not confirmed · The program can exist · Look at the list before you try again");
    expect(posts()).toHaveLength(1);
    expect(mocks.openPullout).not.toHaveBeenCalled();
    expect(document.body.textContent).not.toContain("Nothing changed");
    const reads = calls.filter((call) => call === "GET /api/programs").length;
    fireEvent.click(screen.getByTestId("programs-wizard-look"));
    await waitFor(() => expect(calls.filter((call) => call === "GET /api/programs").length).toBe(reads + 1));
    expect(posts()).toHaveLength(1);
  });

  it("one press in flight: Create is busy; a second press, Back, Escape or New cannot send again", async () => {
    let settle: (value: unknown) => void = () => undefined;
    mocks.apiFetch.mockImplementation(async (path: string, init?: { method?: string; json?: unknown }) => {
      const key = `${(init?.method ?? "GET").toUpperCase()} ${path}`;
      calls.push(init?.json !== undefined ? `${key} ${JSON.stringify(init.json)}` : key);
      if (key === "GET /api/programs") return clone(list);
      if (key === "GET /api/projects") return clone(projects.response.body);
      if (key === "POST /api/programs") return new Promise((resolve) => { settle = resolve; });
      throw new ApiError(404, "Not Found", {});
    });
    renderWindow(<ProgramsCore />);
    await screen.findAllByTestId("programs-band");
    fireEvent.click(screen.getByTestId("programs-new"));
    await ready();
    choose(madeProgram.project_id as string);
    toGo();
    const create = screen.getByTestId("programs-wizard-create");
    fireEvent.click(create);
    expect(create.getAttribute("aria-busy")).toBe("true");
    fireEvent.click(create);
    fireEvent.keyDown(create, { key: "Enter" });
    expect((screen.getByTestId("programs-wizard-back") as HTMLButtonElement).disabled).toBe(true);
    fireEvent.keyDown(create, { key: "Escape" });
    expect(screen.getByTestId("programs-wizard")).toBeTruthy();
    expect((screen.getByTestId("programs-new") as HTMLButtonElement).disabled).toBe(true);
    expect(sent()).toEqual([made.request.json]);
    await act(async () => { settle(clone(madeProgram)); });
    await waitFor(() => expect(mocks.openPullout).toHaveBeenCalledWith(`program:${madeProgram.id}`));
    expect(posts()).toHaveLength(1);
  });

  it("a made Program whose window does not open keeps its id: Open the program reveals the same id and never makes another", async () => {
    hub({ "GET /api/programs": list, "GET /api/projects": projects.response.body, "POST /api/programs": made.response.body });
    mocks.openPullout.mockImplementationOnce(() => { throw new Error("the desk did not mount the window"); });
    renderWindow(<ProgramsCore />);
    await screen.findAllByTestId("programs-band");
    fireEvent.click(screen.getByTestId("programs-new"));
    await ready();
    choose(madeProgram.project_id as string);
    toGo();
    fireEvent.click(screen.getByTestId("programs-wizard-create"));
    expect((await screen.findByTestId("programs-wizard-made")).textContent).toBe("Program made · Its window did not open");
    expect(screen.queryByTestId("programs-wizard-create")).toBeNull();
    fireEvent.click(screen.getByTestId("programs-wizard-open"));
    expect(mocks.openPullout).toHaveBeenLastCalledWith(`program:${madeProgram.id}`);
    expect(mocks.openPullout).toHaveBeenCalledTimes(2);
    expect(posts()).toHaveLength(1);
    await waitFor(() => expect(screen.queryByTestId("programs-wizard")).toBeNull());
  });

  it("closing the window while the create is in flight: the late answer opens nothing", async () => {
    let settle: (value: unknown) => void = () => undefined;
    mocks.apiFetch.mockImplementation(async (path: string, init?: { method?: string; json?: unknown }) => {
      const key = `${(init?.method ?? "GET").toUpperCase()} ${path}`;
      calls.push(key);
      if (key === "GET /api/programs") return clone(list);
      if (key === "GET /api/projects") return clone(projects.response.body);
      if (key === "POST /api/programs") return new Promise((resolve) => { settle = resolve; });
      throw new ApiError(404, "Not Found", {});
    });
    const view = render(<ProgramsCore />);
    await screen.findAllByTestId("programs-band");
    fireEvent.click(screen.getByTestId("programs-new"));
    await ready();
    choose(madeProgram.project_id as string);
    toGo();
    fireEvent.click(screen.getByTestId("programs-wizard-create"));
    view.unmount();
    await act(async () => { settle(clone(madeProgram)); });
    expect(mocks.openPullout).not.toHaveBeenCalled();
    expect(posts()).toHaveLength(1);
  });

  // Fails on main: there a picked project stays a row (no programs-wizard-card) and the title stays "New program".
  it("W2: a picked row grows into the card, the title bar reads the project, Change returns to the rows; the dots live in the title bar", async () => {
    hub({ "GET /api/programs": list, "GET /api/projects": projects.response.body });
    renderWindow(<ProgramsCore />);
    await screen.findAllByTestId("programs-band");
    fireEvent.click(screen.getByTestId("programs-new"));
    await ready();
    expect(screen.getByTestId("window-title").textContent).toBe("New program");
    expect(screen.queryByTestId("programs-wizard-card")).toBeNull();
    choose(roster[0].id);
    const card = screen.getByTestId("programs-wizard-card");
    expect(card.hasAttribute("data-grow")).toBe(true);
    expect(within(card).getByTestId("programs-wizard-card-name").textContent).toBe(roster[0].name);
    expect((card.querySelector("img") as HTMLImageElement).width).toBe(44);
    // The other rows went under it.
    expect(screen.queryByTestId("programs-wizard-project")).toBeNull();
    expect(screen.getByTestId("window-title").textContent).toBe(`New program · ${roster[0].name}`);
    // The dots ride the title bar, not the wizard's bar.
    expect(within(screen.getByTestId("window-head")).getByTestId("programs-wizard-dots")).toBeTruthy();
    expect(within(screen.getByTestId("programs-wizard")).queryByTestId("programs-wizard-dots")).toBeNull();
    // The bar holds the one primary on the first screen: no Cancel, no Back.
    expect(screen.queryByTestId("programs-wizard-cancel")).toBeNull();
    expect(screen.queryByTestId("programs-wizard-back")).toBeNull();
    await waitFor(() => expect(document.activeElement).toBe(next()));
    fireEvent.click(within(card).getByTestId("programs-wizard-change"));
    expect(screen.queryByTestId("programs-wizard-card")).toBeNull();
    const rows = await ready();
    expect(rows).toHaveLength(roster.length);
    expect(rowOf(roster[0].id).hasAttribute("data-selected")).toBe(true);
    choose(roster[1].id);
    expect(screen.getByTestId("programs-wizard-card-name").textContent).toBe(roster[1].name);
    expect(screen.getByTestId("window-title").textContent).toBe(`New program · ${roster[1].name}`);
    expect(posts()).toEqual([]);
  });

  it("W2: screen 2 keeps the card over the Title and the Brief; the peek row names the next screen and is no Button", async () => {
    hub({ "GET /api/programs": list, "GET /api/projects": projects.response.body });
    renderWindow(<ProgramsCore />);
    await screen.findAllByTestId("programs-band");
    fireEvent.click(screen.getByTestId("programs-new"));
    await ready();
    choose(roster[0].id);
    const peek = within(screen.getByTestId("programs-wizard-step-1")).getByTestId("programs-wizard-peek");
    expect(peek.textContent).toContain("Next · the goal");
    expect(peek.getAttribute("aria-hidden")).toBe("true");
    expect(peek.hasAttribute("inert")).toBe(true);
    expect(peek.querySelector("button, input, textarea, [role=button]")).toBeNull();
    fireEvent.click(next());
    const goal = screen.getByTestId("programs-wizard-step-2");
    expect(screen.getByTestId("programs-wizard-card-name").textContent).toBe(roster[0].name);
    expect((within(goal).getByLabelText("Title") as HTMLInputElement).placeholder).toBe("Title");
    expect((within(goal).getByLabelText("Brief") as HTMLTextAreaElement).placeholder).toBe("Brief");
    expect(within(goal).getByRole("button", { name: /^Speak Brief/ })).toBeTruthy();
    // No step words and no Template label on the face.
    expect(goal.textContent).not.toMatch(/Template|What|Where|How/);
    expect(within(goal).getByTestId("programs-wizard-peek").textContent).toContain("Next · how it runs");
    expect(within(goal).getByTestId("programs-wizard-peek").querySelector("button")).toBeNull();
    fireEvent.click(next());
    expect(within(screen.getByTestId("programs-wizard-step-3")).getByTestId("programs-wizard-peek").textContent).toContain("Next · create");
    fireEvent.click(next());
    expect(within(screen.getByTestId("programs-wizard-step-4")).queryByTestId("programs-wizard-peek")).toBeNull();
    expect(screen.getByTestId("programs-wizard-sum-where").textContent).toBe(roster[0].name);
  });

  it("W2: screen 3 shows the desk's level pressed (the recorded policy) in one segmented control; Create posts the recorded body unchanged", async () => {
    const policy = (needsYouRecorded as unknown as { calendar: { none: { gets: Record<string, { control_mode: string }> } } })
      .calendar.none.gets["/api/authority/policy"];
    expect(policy.control_mode).toBe("yolo");
    hub({
      "GET /api/programs": list, "GET /api/projects": projects.response.body, "POST /api/programs": made.response.body,
      "GET /api/authority/policy": policy,
    });
    renderWindow(<ProgramsCore />);
    await screen.findAllByTestId("programs-band");
    fireEvent.click(screen.getByTestId("programs-new"));
    await ready();
    choose(madeProgram.project_id as string);
    fireEvent.click(next());
    fireEvent.click(next());
    const runs = screen.getByTestId("programs-wizard-step-3");
    const levels = within(runs).getByRole("group", { name: "Runs" });
    const segments = within(levels).getAllByRole("button");
    expect(segments.map((node) => node.querySelector(".pg-wiz-level-word")!.textContent)).toEqual(["Runs by itself", "Asks before it merges or sends", "Asks at every step"]);
    await waitFor(() => expect(within(levels).getByRole("button", { name: "Runs by itself" }).getAttribute("aria-pressed")).toBe("true"));
    expect(segments.filter((node) => node.getAttribute("aria-pressed") === "true")).toHaveLength(1);
    expect(screen.getByTestId("programs-wizard-level-line").textContent).toBe("HoldSpeak decides all it can; only core questions come to you");
    expect(screen.getByTestId("programs-wizard-agent")).toBeTruthy();
    expect(screen.getByTestId("programs-wizard-reviewer")).toBeTruthy();
    fireEvent.click(next());
    expect(screen.getByTestId("programs-wizard-sum-how").textContent).toBe("Runs by itself");
    fireEvent.click(screen.getByTestId("programs-wizard-create"));
    await waitFor(() => expect(mocks.openPullout).toHaveBeenCalledWith(`program:${madeProgram.id}`));
    // The desk's level is not his choice: the body is the recorded one.
    expect(sent()).toEqual([made.request.json]);
  });

  // Fails on main: there the frame's close calls closeSurfaceWindow and the draft is gone.
  it("the frame's close while the wizard is open is its Cancel: back to the list, the window stays, no POST", async () => {
    hub({ "GET /api/programs": list, "GET /api/projects": projects.response.body, "POST /api/programs": made.response.body });
    const closeSurfaceWindow = vi.fn();
    const before = useDesk.getState().closeSurfaceWindow;
    useDesk.setState({ items: EMPTY_ITEMS, panelMin: [], panelMax: [], panelOrder: [], panelRects: {}, closeSurfaceWindow });
    const row: SurfaceRow = { key: "open-programs", id: "surface-programs", title: "Programs", glyph: "▦", eyebrow: "Orchestration", Core: lazy(async () => ({ default: ProgramsCore })) };
    try {
      render(<div className="desk-next"><SurfaceWindowHost row={row} scope={undefined} items={EMPTY_ITEMS} /></div>);
      await screen.findAllByTestId("programs-band");
      fireEvent.click(screen.getByTestId("programs-new"));
      await ready();
      choose(roster[0].id);
      const close = () => document.querySelector<HTMLButtonElement>(".desk-gadget-close")!;
      fireEvent.click(close());
      await waitFor(() => expect(screen.queryByTestId("programs-wizard")).toBeNull());
      expect(screen.getByTestId("programs-list")).toBeTruthy();
      expect(closeSurfaceWindow).not.toHaveBeenCalled();
      expect(posts()).toEqual([]);
      // With the list back, the frame's close closes the window again.
      fireEvent.click(close());
      await waitFor(() => expect(closeSurfaceWindow).toHaveBeenCalledWith("open-programs"));
    } finally {
      useDesk.setState({ closeSurfaceWindow: before });
    }
  });

  it("the card's quiet line: no counter of zero; a project with programs says how many", async () => {
    const target = roster[1].id;
    const projectOf = (row: ProgramList["programs"][number]) => row.project?.id ?? row.project_id;
    const one = { projects: [(projects.response.body as { projects: unknown[] }).projects[1]] };
    hub({ "GET /api/programs": { ...list, programs: list.programs.filter((row) => projectOf(row) !== target) }, "GET /api/projects": one });
    renderWindow(<ProgramsCore />);
    fireEvent.click(await screen.findByTestId("programs-new"));
    await screen.findByTestId("programs-wizard-card-name");
    expect(screen.getByTestId("programs-wizard-card-line").textContent).toBe("Fast cycle");
    cleanup();
    const owned = list.programs.slice(0, 2).map((row) => ({ ...row, project_id: target, project: row.project ? { ...row.project, id: target } : row.project }));
    hub({ "GET /api/programs": { ...list, programs: owned }, "GET /api/projects": one });
    renderWindow(<ProgramsCore />);
    fireEvent.click(await screen.findByTestId("programs-new"));
    await screen.findByTestId("programs-wizard-card-name");
    expect(screen.getByTestId("programs-wizard-card-line").textContent).toBe("2 programs · Fast cycle");
  });

  // Fails on main: there is no programs-wizard-fold row and no short level words.
  it("screen 3 on the phone: the short level words and one folded Check · Spending row under a 480 surface container", async () => {
    hub({ "GET /api/programs": list, "GET /api/projects": projects.response.body });
    renderWindow(<ProgramsCore />);
    await screen.findAllByTestId("programs-band");
    fireEvent.click(screen.getByTestId("programs-new"));
    await ready();
    choose(roster[0].id);
    fireEvent.click(next());
    fireEvent.click(next());
    const runs = screen.getByTestId("programs-wizard-step-3");
    const levels = within(runs).getByRole("group", { name: "Runs" });
    expect([...levels.querySelectorAll(".pg-wiz-level-short")].map((node) => node.textContent)).toEqual(["By itself", "Asks to merge", "Asks each step"]);
    // The accessible name stays the whole meaning at every width.
    expect(within(levels).getByRole("button", { name: "Asks before it merges or sends" })).toBeTruthy();
    const fold = screen.getByTestId("programs-wizard-fold");
    expect(fold.textContent).toBe("Check · The repository's · Spending not capped");
    fireEvent.change(screen.getByLabelText("Check"), { target: { value: "make check" } });
    expect(fold.textContent).toBe("Check · make check · Spending not capped");
    // A press on the folded row opens Check (the phone can still set it).
    expect(runs.querySelector(".pg-wiz-runs")!.hasAttribute("data-check-open")).toBe(false);
    fireEvent.click(fold);
    expect(runs.querySelector(".pg-wiz-runs")!.hasAttribute("data-check-open")).toBe(true);
    await waitFor(() => expect(document.activeElement).toBe(screen.getByLabelText("Check")));
    // jsdom has no container queries: the fold is proven as the rule text.
    const phone = programsCss.slice(programsCss.indexOf("@container surface (max-width: 480px)"));
    expect(phone.startsWith("@container surface (max-width: 480px)")).toBe(true);
    const block = phone.slice(0, phone.indexOf("\n}\n") + 2);
    expect(block).toContain(".pg-wiz-levels .pg-wiz-level-word { display: none; }");
    expect(block).toContain(".pg-wiz-levels .pg-wiz-level-short { display: inline; }");
    expect(block).toContain(".pg-wiz-runs:not([data-check-open]) .gadget-row:has(.pg-wiz-check)");
    expect(block).toContain(".pg-wiz-runs:not([data-check-open]) .gadget-row:has(.pg-wiz-spending) { display: none; }");
    expect(block).toContain(".pg-wiz-runs:not([data-check-open]) > .btn.pg-wiz-fold { display: flex; }");
    expect(programsCss).toMatch(/\.pg-wiz-level-short,\s*\.btn\.pg-wiz-fold \{ display: none; \}/);
    expect(posts()).toEqual([]);
  });
});

describe("HS-S13 + HS-S11: the Program made for a project is the row its Room lists", () => {
  type Capture = { request: { method: string; path: string; json?: Record<string, unknown> }; response: { status: number; body: unknown } };
  const hand = roomPrograms13.creationHandoff;
  const create = hand.create as unknown as Capture;
  const madeProgram = create.response.body as Program;
  const projectId = roomPrograms13.projects.a;

  it("Create in the chosen project sends the recorded tuple, opens its id, and that id is the Room's row and detail", async () => {
    expect(create.request.json).toEqual({ title: "New program", template: "fast-cycle", project_id: projectId });
    hub({ "GET /api/programs": list, "GET /api/projects": hand.projects.response.body, "POST /api/programs": madeProgram });
    render(<ProgramsCore />);
    await screen.findAllByTestId("programs-band");
    fireEvent.click(screen.getByTestId("programs-new"));
    const rows = await screen.findAllByTestId("programs-wizard-project");
    const name = (hand.projects.response.body as { projects: Array<{ id: string; name: string }> }).projects.find((project) => project.id === projectId)!.name;
    const row = rows.find((node) => within(node).getByTestId("programs-wizard-name").textContent === name)!;
    fireEvent.click(within(row).getByTestId("programs-wizard-pick"));
    for (let step = 0; step < 3; step += 1) fireEvent.click(screen.getByTestId("programs-wizard-next"));
    fireEvent.click(screen.getByTestId("programs-wizard-create"));
    await waitFor(() => expect(mocks.openPullout).toHaveBeenCalledWith(`program:${madeProgram.id}`));
    const posted = calls.filter((call) => call.startsWith("POST /api/programs"))
      .map((call) => JSON.parse(call.slice("POST /api/programs ".length)));
    expect(posted).toEqual([create.request.json]);
    // The acknowledged id is the project's Room row and the detail it opens.
    expect(hand.roomBefore.programs.programs).toEqual([]);
    expect(hand.roomAfter.project_id).toBe(projectId);
    expect(hand.roomAfter.programs.programs.map((row) => row.id)).toEqual([madeProgram.id]);
    expect(hand.detail.id).toBe(madeProgram.id);
    expect(hand.detail.project_id).toBe(projectId);
  });
});

describe("#1697: the Dreaming template (recorded through the real route, test_desk_program_night.py)", () => {
  it("is in Templates with its meaning; a night program in Drafting sleeps until its window and Start says what the night does", async () => {
    const dream = dreamingFixture as unknown as Program;
    hub({ "GET /api/programs": list });
    render(<ProgramsCore />);
    fireEvent.click(await screen.findByTestId("programs-templates"));
    expect(menuWords()).toContain("Dreaming · Runs at night on the idle home engine; fills itself from tasks marked Tonight");
    cleanup();
    hub({ [`GET /api/programs/${dream.id}`]: dream });
    render(<ProgramBody programId={dream.id} />);
    const line = await screen.findByTestId("programs-line");
    expect(line.querySelector("[data-station=night]")!.textContent).toContain(`Sleeps until ${dream.night!.start}`);
    // No steps yet: the night fills itself, so Start is there with its window as the quiet fact.
    const tray = screen.getByTestId("programs-tray");
    expect(within(tray).getByTestId("program-start").className).toMatch(/primary/);
    expect(within(tray).getByTestId("programs-start-words").textContent)
      .toBe(`Tonight ${dream.night!.start} to ${dream.night!.end}`);
  });
});
