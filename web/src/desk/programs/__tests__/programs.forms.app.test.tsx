import { useState } from "react";
import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import {
  createProjectsFixture,
  createProjectFixture,
  createNoRepositoryFixture,
  needsYouRecorded,
  drafting,
  bindingUnboundFixture,
  bindingBoundFixture,
  shapeFixture,
  planFixture,
  splitFixture,
  mocks,
  hub,
  clone,
  ApiError,
  type Program,
} from "./programs.seats.test-setup";
import { ProgramForm } from "../ProgramForm";
import { ProgramEdit } from "../ProgramEdit";
import { ProgramBulkAgents } from "../ProgramRecords";
import { ProgramDetail } from "../ProgramWindow";
const made = createProjectFixture.response.body as unknown as Program;
const projects = createProjectsFixture.response.body;
const tab = (name: string) =>
  fireEvent.click(screen.getByRole("tab", { name }));
const press = (name: string) =>
  fireEvent.click(screen.getByRole("button", { name }));
function change(label: string, value: string) {
  fireEvent.change(screen.getByLabelText(label), { target: { value } });
}
function Form({
  kind = "new",
  initial = drafting,
}: {
  kind?: "new" | "amend";
  initial?: Program;
}) {
  const [p, setP] = useState(initial),
    [done, setDone] = useState(false);
  return done ? (
    <ProgramDetail
      program={p}
      loading={false}
      error={null}
      reload={async () => {}}
      onError={() => {}}
      onApplied={(next) => {
        if (next) setP(next);
      }}
    />
  ) : (
    <ProgramForm
      kind={kind}
      program={p}
      onCancel={() => setDone(true)}
      onApplied={(next) => {
        if (next) setP(next);
        setDone(true);
      }}
    />
  );
}
function newHub(extra: Record<string, unknown> = {}) {
  hub({
    "GET /api/projects": projects,
    "GET /api/authority/policy":
      needsYouRecorded.calendar.none.gets["/api/authority/policy"],
    "POST /api/programs": made,
    ...extra,
  });
}
async function chooseProject() {
  await screen.findByRole("option", {
    name: projects.projects.find((row) => row.id === made.project_id)!.name,
  });
  fireEvent.change(screen.getByRole("combobox", { name: "Project" }), {
    target: { value: made.project_id },
  });
}

describe("New and Edit inspector seats", () => {
  it("shows the selected agent after the picker closes and across form tabs", async () => {
    newHub();
    render(<Form />);
    await chooseProject();
    tab("Work");
    press("Choose agent");
    fireEvent.click(await screen.findByRole("menuitem", { name: "Codex · Ready" }));
    expect(screen.getByRole("button", { name: "Choose agent" }).textContent).toContain("Codex");
    tab("Program");
    tab("Work");
    expect(screen.getByRole("button", { name: "Choose agent" }).textContent).toContain("Codex");
  });
  it("Escape in a new program form cancels without a write",()=>{
    newHub();const cancel=vi.fn();render(<ProgramForm kind="new" program={null} onCancel={cancel} onApplied={()=>{}}/>);
    fireEvent.keyDown(screen.getByLabelText("Program name"),{key:"Escape"});expect(cancel).toHaveBeenCalledOnce();
    expect(mocks.apiFetch.mock.calls.some(([,init])=>init?.method==="POST")).toBe(false);
  });
  it("scope and a prefilled queue keep their project, title, brief and steps until Create", async () => {
    newHub();
    const applied = vi.fn();
    const prefill = {
      title: "A kept queue",
      goal: "Keep the old tasks.",
      steps: [{ title: "Read the queue", brief: "Read its tasks." }],
    };
    render(
      <ProgramForm
        kind="new"
        program={null}
        scopeProjectId={made.project_id!}
        prefill={prefill}
        onApplied={applied}
        onCancel={() => {}}
      />,
    );
    await waitFor(() =>
      expect(
        (screen.getByRole("combobox", { name: "Project" }) as HTMLSelectElement)
          .value,
      ).toBe(made.project_id),
    );
    press("Create");
    await waitFor(() => expect(applied).toHaveBeenCalledWith(made));
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/api/programs",
      expect.objectContaining({
        json: expect.objectContaining({
          ...prefill,
          project_id: made.project_id,
        }),
      }),
    );
  });
  it("one in-flight Create cannot dispatch twice and an unmounted form opens nothing", async () => {
    let done: (answer: Program) => void = () => {};
    newHub({
      "POST /api/programs": () =>
        new Promise<Program>((resolve) => {
          done = resolve;
        }),
    });
    const applied = vi.fn();
    const view = render(
      <ProgramForm
        kind="new"
        program={null}
        onApplied={applied}
        onCancel={() => {}}
      />,
    );
    await chooseProject();
    change("Program name", "Keep one press");
    press("Create");
    press("Create");
    expect(
      mocks.apiFetch.mock.calls.filter(([, init]) => init?.method === "POST"),
    ).toHaveLength(1);
    view.unmount();
    done(made);
    await Promise.resolve();
    expect(applied).not.toHaveBeenCalled();
  });
  it("creation keeps the fields across tabs, sends spending as a note and draws the created program", async () => {
    newHub();
    render(<Form />);
    await chooseProject();
    change("Program name", "Ship the wizard");
    change("Program goal", "Keep each field.");
    tab("Checks");
    change("Spending note in USD", "$40");
    change("Check command", "true");
    tab("Program");
    expect(
      (screen.getByLabelText("Program name") as HTMLInputElement).value,
    ).toBe("Ship the wizard");
    press("Create");
    await screen.findByRole("tab", { name: "Now" });
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/api/programs",
      expect.objectContaining({
        json: expect.objectContaining({
          title: "Ship the wizard",
          goal: "Keep each field.",
          project_id: made.project_id,
          spend_limit_usd: 40,
          check_command: "true",
        }),
      }),
    );
  });
  it("failed project read keeps entered text and Retry restores the project choices", async () => {
    newHub({
      "GET /api/projects": () => {
        throw new ApiError(503, "Unavailable", {});
      },
    });
    render(<Form />);
    change("Program name", "Keep this title");
    await screen.findByRole("button", { name: "Retry projects" });
    newHub();
    press("Retry projects");
    await chooseProject();
    expect(
      (screen.getByLabelText("Program name") as HTMLInputElement).value,
    ).toBe("Keep this title");
    expect(screen.queryByRole("button", { name: "Retry projects" })).toBeNull();
  });
  it("a repository refusal retains the form and its fields", async () => {
    const no = createNoRepositoryFixture;
    newHub({
      "POST /api/programs": () => {
        throw new ApiError(no.response.status, "Refused", no.response.body);
      },
    });
    render(<Form />);
    await chooseProject();
    change("Program name", "Keep the refusal");
    press("Create");
    await screen.findByText(/The change was not saved/);
    expect(
      (screen.getByLabelText("Program name") as HTMLInputElement).value,
    ).toBe("Keep the refusal");
  });
  it("Cancel sends no create and a new form uses its default template", async () => {
    newHub();
    const cancel = vi.fn();
    render(
      <ProgramForm
        kind="new"
        program={null}
        onCancel={cancel}
        onApplied={() => {}}
      />,
    );
    press("Cancel");
    expect(cancel).toHaveBeenCalledOnce();
    expect(
      mocks.apiFetch.mock.calls.some(([, init]) => init?.method === "POST"),
    ).toBe(false);
  });
  it("Edit sends only touched language fields and draws the acknowledged goal", async () => {
    hub({ [`PATCH /api/programs/${drafting.id}`]: drafting });
    const applied = vi.fn();
    render(
      <ProgramEdit
        program={drafting}
        onCancel={() => {}}
        onApplied={applied}
      />,
    );
    change("Goal", "A new goal");
    tab("Agents");
    fireEvent.click(screen.getByRole("checkbox", { name: "When idle" }));
    tab("Checks");
    change("Check command", "true");
    tab("Limits");
    fireEvent.click(screen.getByRole("checkbox", { name: "May call you" }));
    press("Save program");
    await waitFor(() => expect(applied).toHaveBeenCalledWith(drafting));
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        json: {
          goal: "A new goal",
          prefer_idle: !drafting.prefer_idle,
          check_command: "true",
          may_call: !drafting.may_call,
        },
      }),
    );
  });
  it("bulk agents refuses an action-carrying program without a plan write", () => {
    const p = bindingBoundFixture as unknown as Program;
    render(
      <ProgramBulkAgents program={p} onApplied={() => {}} onError={() => {}} />,
    );
    expect(
      (
        screen.getByRole("button", {
          name: "Change all agents",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    expect(
      mocks.apiFetch.mock.calls.some(([path]) => path.endsWith("/plan")),
    ).toBe(false);
  });
  it("bulk agents rereads before rebuilding and stops when that read fails", async () => {
    const p = drafting;
    hub({
      [`GET /api/programs/${p.id}`]: () => {
        throw new ApiError(503, "Unavailable", {});
      },
    });
    render(
      <ProgramBulkAgents program={p} onApplied={() => {}} onError={() => {}} />,
    );
    press("Change all agents");
    await screen.findByText(/The change was not saved/);
    expect(
      mocks.apiFetch.mock.calls.some(([path]) => path.endsWith("/plan")),
    ).toBe(false);
  });
});
