import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../../lib/api";
import { useDesk } from "../../store";
import { StartAgent } from "../StartAgent";
import { readWorkspaceHandoffDraft, workspaceHandoffScope, type WorkspaceHandoffPreparation } from "../../terminals/workspaceHandoff";
import { hubWire } from "../../__tests__/wire/hubWire";

const apiFetch = vi.hoisted(() => vi.fn());
vi.mock("../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../lib/api")>("../../../lib/api");
  return { ...actual, apiFetch };
});
vi.mock("../../components/MicButton", () => ({ MicButton: () => <span data-testid="mic" /> }));

const AG8_PROJECTS = hubWire<{ projects: Array<Record<string, unknown>> }>("../fixtures/agents-ag8/projects").wire;
const AG8_NOTE = hubWire<{ note: { id?: string; note_id?: string } }>("../fixtures/agents-ag8/note.create").wire;
const AG8_RESOURCE = hubWire<Record<string, unknown>>("../fixtures/agents-ag8/resource.add").wire;
const AG8_REFUSED = hubWire<Record<string, unknown>>("../fixtures/agents-ag8/hand.refused").wire;
const AG8_QUEUE = hubWire<{ queue_id: string }>("../fixtures/agents-ag8/queue.cancel").wire;

const prepA: WorkspaceHandoffPreparation = {
  words: "Review the ledger file",
  context: {
    project: { id: "p-ledger", name: "Ledger" },
    source: { id: "repo-payments", title: "Payments repository" },
    worktree: { id: "wt-review", branch: "feature/review" },
    file: { path: "src/ledger.ts", revision: "sha-a", content: "export const ready = true;" },
  },
};
const prepB: WorkspaceHandoffPreparation = {
  words: "Check the API file",
  context: {
    project: { id: "p-ledger", name: "Ledger" },
    source: { id: "repo-payments", title: "Payments repository" },
    worktree: { id: "wt-review", branch: "feature/review" },
    file: { path: "src/api.ts", revision: "sha-b", content: "export const api = true;" },
  },
};

function projectReply() {
  return AG8_PROJECTS;
}

beforeEach(() => {
  apiFetch.mockReset();
  apiFetch.mockImplementation(async (url: string) => {
    if (url === "/api/projects") return projectReply();
    if (url === "/api/notes") return AG8_NOTE;
    if (url.includes("/resources/note%3A")) return AG8_RESOURCE;
    if (url === "/api/agent/hand") throw new ApiError(409, "refused", AG8_REFUSED);
    throw new Error(`unhandled ${url}`);
  });
  useDesk.setState({ drafts: {} });
  localStorage.clear();
});

function renderStart(preparation: WorkspaceHandoffPreparation | null = prepA, initialProjectId: string | null = "p-ledger") {
  return render(<StartAgent preparation={preparation} initialProjectId={initialProjectId} onCancel={vi.fn()} onStarted={vi.fn()} />);
}

describe("StartAgent prepared workspace handoff", () => {
  it("shows the initial words and source plate, with the exact captured context behind Source context", async () => {
    renderStart();
    expect(await screen.findByTestId("conductor-start-words")).toHaveValue("Review the ledger file");
    expect(screen.getByTestId("conductor-start-source")).toHaveTextContent("Payments repository · src/ledger.ts");
    expect(screen.getByTestId("conductor-start-context")).toHaveTextContent("feature/review");
    fireEvent.click(screen.getByRole("button", { name: "Source context" }));
    expect(screen.getByTestId("conductor-start-context-preview")).toHaveTextContent("Read revision: sha-a");
    expect(screen.getByTestId("conductor-start-context-preview")).toHaveTextContent("export const ready = true;");
  });

  it("keeps each file's words in the existing Desk drafts when the workspace wing changes", async () => {
    const view = renderStart(prepA);
    const input = await screen.findByTestId("conductor-start-words");
    fireEvent.change(input, { target: { value: "Keep the ledger draft" } });
    view.rerender(<StartAgent preparation={prepB} initialProjectId="p-ledger" onCancel={vi.fn()} onStarted={vi.fn()} />);
    await waitFor(() => expect(screen.getByTestId("conductor-start-words")).toHaveValue("Check the API file"));
    view.rerender(<StartAgent preparation={prepA} initialProjectId="p-ledger" onCancel={vi.fn()} onStarted={vi.fn()} />);
    await waitFor(() => expect(screen.getByTestId("conductor-start-words")).toHaveValue("Keep the ledger draft"));
    view.unmount();
    const reopened = renderStart(prepA);
    await waitFor(() => expect(screen.getByTestId("conductor-start-words")).toHaveValue("Keep the ledger draft"));
    fireEvent.change(screen.getByTestId("conductor-start-words"), { target: { value: "" } });
    reopened.unmount();
    renderStart(prepA);
    await waitFor(() => expect(screen.getByTestId("conductor-start-words")).toHaveValue(""));
  });

  it("does not let the late Project read replace words typed before it answered", async () => {
    let answerProjects!: (value: unknown) => void;
    apiFetch.mockImplementation((url: string) => {
      if (url === "/api/projects") return new Promise((resolve) => { answerProjects = resolve; });
      if (url === "/api/notes") return Promise.resolve(AG8_NOTE);
      if (url.includes("/resources/note%3A")) return Promise.resolve(AG8_RESOURCE);
      if (url === "/api/agent/hand") return Promise.reject(new ApiError(409, "refused", AG8_REFUSED));
      return Promise.reject(new Error(`unhandled ${url}`));
    });
    const unbound: WorkspaceHandoffPreparation = { ...prepA, context: { ...prepA.context, project: null } };
    renderStart(unbound, null);
    const input = await screen.findByTestId("conductor-start-words");
    fireEvent.change(input, { target: { value: "These are newer owner words" } });
    answerProjects(projectReply());
    await waitFor(() => expect(screen.getByTestId("conductor-start-words")).toHaveValue("These are newer owner words"));
    fireEvent.click(screen.getByTestId("conductor-start-go"));
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/api/notes", expect.objectContaining({ json: expect.objectContaining({ body_markdown: expect.stringContaining("These are newer owner words") }) })));
    expect(apiFetch).toHaveBeenCalledWith("/api/agent/hand", expect.objectContaining({ json: expect.objectContaining({ project_id: "p-ledger" }) }));
  });

  it("keeps a deliberate empty task when the initial Project read answers late", async () => {
    let answerProjects!: (value: unknown) => void;
    apiFetch.mockImplementation((url: string) => {
      if (url === "/api/projects") return new Promise((resolve) => { answerProjects = resolve; });
      return Promise.reject(new Error(`unexpected dispatch ${url}`));
    });
    const unbound: WorkspaceHandoffPreparation = { ...prepA, context: { ...prepA.context, project: null } };
    renderStart(unbound, null);
    fireEvent.change(await screen.findByTestId("conductor-start-words"), { target: { value: "" } });
    answerProjects(projectReply());
    await waitFor(() => expect(screen.getByRole("combobox", { name: "Project" })).toHaveValue("p-ledger"));
    expect(screen.getByTestId("conductor-start-words")).toHaveValue("");
    expect(screen.getByTestId("conductor-start-go")).toBeDisabled();
  });

  it("does not retarget a prepared hand to a remembered or first Project when its captured Project is gone", async () => {
    apiFetch.mockImplementation(async (url: string) => {
      if (url === "/api/projects") return AG8_PROJECTS;
      throw new Error(`unexpected dispatch ${url}`);
    });
    const gone = { ...prepA, context: { ...prepA.context, project: { id: "p-gone", name: "Gone" } } };
    renderStart(gone, "p-gone");
    await screen.findByTestId("conductor-start-project-unavailable");
    expect(screen.getByTestId("conductor-start-go")).toBeDisabled();
    expect(apiFetch.mock.calls.some(([url]) => url === "/api/notes")).toBe(false);
  });

  it("clears the pre-Project draft after a successful late read and does not resurrect it on reopen", async () => {
    let answerProjects!: (value: unknown) => void;
    apiFetch.mockImplementation((url: string) => {
      if (url === "/api/projects") return new Promise((resolve) => { answerProjects = resolve; });
      if (url === "/api/notes") return Promise.resolve(AG8_NOTE);
      if (url.includes("/resources/note%3A")) return Promise.resolve(AG8_RESOURCE);
      if (url === "/api/agent/hand") return Promise.resolve(AG8_QUEUE);
      return Promise.reject(new Error(`unhandled ${url}`));
    });
    const unbound: WorkspaceHandoffPreparation = { ...prepA, context: { ...prepA.context, project: null } };
    const onStarted = vi.fn();
    const view = render(<StartAgent preparation={unbound} onCancel={vi.fn()} onStarted={onStarted} />);
    const input = await screen.findByTestId("conductor-start-words");
    fireEvent.change(input, { target: { value: "Late project words" } });
    answerProjects(projectReply());
    await waitFor(() => expect(screen.getByRole("combobox", { name: "Project" })).toHaveValue("p-ledger"));
    fireEvent.click(screen.getByTestId("conductor-start-go"));
    await waitFor(() => expect(onStarted).toHaveBeenCalled());
    const unboundScope = workspaceHandoffScope(unbound.context, null);
    const resolvedScope = workspaceHandoffScope(unbound.context, "p-ledger");
    expect(useDesk.getState().drafts[unboundScope]).toBeUndefined();
    expect(useDesk.getState().drafts[resolvedScope]).toBeUndefined();
    view.unmount();
    render(<StartAgent preparation={unbound} onCancel={vi.fn()} onStarted={vi.fn()} />);
    await waitFor(() => expect(screen.getByTestId("conductor-start-words")).toHaveValue("Review the ledger file"));
  });

  it("keeps Start disabled while a changed prepared Project is still being validated", async () => {
    const pending: Array<(value: unknown) => void> = [];
    apiFetch.mockImplementation((url: string) => {
      if (url === "/api/projects") return new Promise((resolve) => pending.push(resolve));
      if (url === "/api/notes") return Promise.resolve(AG8_NOTE);
      if (url.includes("/resources/note%3A")) return Promise.resolve(AG8_RESOURCE);
      if (url === "/api/agent/hand") return Promise.reject(new ApiError(409, "refused", AG8_REFUSED));
      return Promise.reject(new Error(`unexpected dispatch ${url}`));
    });
    const changed = { ...prepB, context: { ...prepB.context, project: { id: "p-platform", name: "Platform" } } };
    const view = renderStart(prepA, "p-ledger");
    expect(screen.getByTestId("conductor-start-go")).toBeDisabled();
    view.rerender(<StartAgent preparation={changed} initialProjectId="p-platform" onCancel={vi.fn()} onStarted={vi.fn()} />);
    expect(screen.getByTestId("conductor-start-go")).toBeDisabled();
    fireEvent.keyDown(screen.getByTestId("conductor-start-words"), { key: "Enter" });
    expect(apiFetch.mock.calls.some(([url]) => url === "/api/notes")).toBe(false);
    pending.forEach((resolve) => resolve(AG8_PROJECTS));
    await waitFor(() => expect(screen.getByRole("combobox", { name: "Project" })).toHaveValue("p-platform"));
    expect(screen.getByTestId("conductor-start-go")).toBeEnabled();
  });

  it("names a failed Project read and retries it without losing the prepared words", async () => {
    let reads = 0;
    apiFetch.mockImplementation(async (url: string) => {
      if (url === "/api/projects") {
        reads += 1;
        if (reads === 1) throw new Error("offline");
        return AG8_PROJECTS;
      }
      throw new Error(`unexpected dispatch ${url}`);
    });
    renderStart();
    expect(await screen.findByTestId("conductor-start-project-read-error")).toHaveTextContent("Project list not available");
    expect(screen.getByTestId("conductor-start-words")).toHaveValue("Review the ledger file");
    expect(screen.getByTestId("conductor-start-go")).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(screen.getByRole("combobox", { name: "Project" })).toHaveValue("p-ledger"));
    expect(screen.getByTestId("conductor-start-go")).toBeEnabled();
  });

  it("does not let an old Note acknowledgement overwrite newer words in a reopened same-file form", async () => {
    let resolveNote!: (value: unknown) => void;
    apiFetch.mockImplementation((url: string) => {
      if (url === "/api/projects") return Promise.resolve(AG8_PROJECTS);
      if (url === "/api/notes") return new Promise((resolve) => { resolveNote = resolve; });
      if (url.includes("/resources/note%3A")) return Promise.resolve(AG8_RESOURCE);
      if (url === "/api/agent/hand") return Promise.reject(new ApiError(409, "refused", AG8_REFUSED));
      return Promise.reject(new Error(`unexpected dispatch ${url}`));
    });
    const old = renderStart();
    await screen.findByTestId("conductor-start-words");
    fireEvent.click(screen.getByTestId("conductor-start-go"));
    await waitFor(() => expect(apiFetch.mock.calls.some(([url]) => url === "/api/notes")).toBe(true));
    old.unmount();
    renderStart();
    const current = await screen.findByTestId("conductor-start-words");
    fireEvent.change(current, { target: { value: "Newer words in the reopened form" } });
    resolveNote(AG8_NOTE);
    await waitFor(() => expect(apiFetch.mock.calls.some(([url]) => String(url).includes("/resources/note%3A"))).toBe(true));
    const scope = workspaceHandoffScope(prepA.context, "p-ledger");
    expect(readWorkspaceHandoffDraft(useDesk.getState().drafts[scope])?.words).toBe("Newer words in the reopened form");
  });

  it("retains the file draft scope but makes a new Note when the captured read changes", async () => {
    apiFetch.mockImplementation(async (url: string) => {
      if (url === "/api/projects") return AG8_PROJECTS;
      if (url === "/api/notes") return AG8_NOTE;
      if (url.includes("/resources/note%3A")) return AG8_RESOURCE;
      if (url === "/api/agent/hand") throw new ApiError(409, "refused", AG8_REFUSED);
      throw new Error(`unexpected dispatch ${url}`);
    });
    const view = renderStart(prepA);
    await screen.findByTestId("conductor-start-words");
    fireEvent.click(screen.getByTestId("conductor-start-go"));
    await screen.findByRole("alert");
    const newerRead: WorkspaceHandoffPreparation = {
      ...prepA,
      context: { ...prepA.context, file: { ...prepA.context.file!, revision: "sha-new", content: "export const ready = false;" } },
    };
    view.rerender(<StartAgent preparation={newerRead} initialProjectId="p-ledger" onCancel={vi.fn()} onStarted={vi.fn()} />);
    fireEvent.click(screen.getByTestId("conductor-start-go"));
    await waitFor(() => expect(apiFetch.mock.calls.filter(([url]) => url === "/api/notes")).toHaveLength(2));
  });

  it("reuses the acknowledged prepared Note after a hand refusal", async () => {
    apiFetch.mockImplementation(async (url: string) => {
      if (url === "/api/projects") return projectReply();
      if (url === "/api/notes") return AG8_NOTE;
      if (url.includes("/resources/note%3A")) return AG8_RESOURCE;
      if (url === "/api/agent/hand") throw new ApiError(409, "refused", AG8_REFUSED);
      throw new Error(`unhandled ${url}`);
    });
    const view = renderStart();
    await screen.findByTestId("conductor-start-words");
    fireEvent.click(screen.getByTestId("conductor-start-go"));
    await screen.findByRole("alert");
    view.unmount();
    renderStart();
    await waitFor(() => expect(screen.getByTestId("conductor-start-words")).toHaveValue("Review the ledger file"));
    fireEvent.click(screen.getByTestId("conductor-start-go"));
    await waitFor(() => expect(apiFetch.mock.calls.filter(([url]) => url === "/api/agent/hand")).toHaveLength(2));
    expect(apiFetch.mock.calls.filter(([url]) => url === "/api/notes")).toHaveLength(1);
    expect(apiFetch.mock.calls.filter(([url]) => String(url).includes("/resources/note%3A"))).toHaveLength(1);
  });
});
