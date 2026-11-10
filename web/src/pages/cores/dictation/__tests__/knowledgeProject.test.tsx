import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../../lib/api";
import { Knowledge } from "../Knowledge";
import { ReceiptContext } from "../shared";

vi.mock("../../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../../lib/api")>()),
  apiFetch: vi.fn(),
}));

const projectRoot = "/projects/payments ledger";
const instructionsUrl = `/api/dictation/project-hs?project_root=${encodeURIComponent(projectRoot)}`;
const project = { detected: { root: projectRoot }, kb: {}, kb_path: null };
const instructions = { files: { "instructions.md": { content: "Use the ledger glossary." } } };

beforeEach(() => {
  vi.mocked(apiFetch).mockReset();
  localStorage.clear();
});

describe("project instructions follow the detected project", () => {
  it("shows no selected project without requesting or offering instructions", async () => {
    vi.mocked(apiFetch).mockResolvedValue({ detected: null, kb: null, kb_path: null });
    render(<Knowledge />);

    expect(await screen.findByText("No project selected")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Edit Project instructions" })).toBeNull();
    expect(vi.mocked(apiFetch).mock.calls.map(([url]) => url)).toEqual(["/api/dictation/project-kb"]);
  });

  it("loads root-scoped instructions for an automatically detected project", async () => {
    vi.mocked(apiFetch).mockImplementation(async (url) =>
      (url === "/api/dictation/project-kb" ? project : instructions) as never);
    render(<Knowledge />);

    expect(await screen.findByRole("button", { name: "Edit Project instructions" })).toHaveTextContent("Use the ledger glossary.");
    expect(apiFetch).toHaveBeenCalledWith(instructionsUrl);
    expect(screen.queryByText("No project selected")).toBeNull();
  });

  it("names a failed instructions read, withholds the editor, and retries", async () => {
    let reads = 0;
    vi.mocked(apiFetch).mockImplementation(async (url) => {
      if (url === "/api/dictation/project-kb") return project as never;
      if (++reads === 1) throw new Error("Instructions unavailable");
      return instructions as never;
    });
    render(<Knowledge />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Instructions not loaded · Instructions unavailable");
    expect(screen.queryByRole("button", { name: "Edit Project instructions" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("button", { name: "Edit Project instructions" })).toHaveTextContent("Use the ledger glossary.");
    expect(reads).toBe(2);
  });

  it("keeps the successful write receipt when its following read fails", async () => {
    let reads = 0;
    const announce = vi.fn();
    vi.mocked(apiFetch).mockImplementation(async (url, options) => {
      if (url === "/api/dictation/project-kb") return project as never;
      if (options?.method === "PUT") return instructions as never;
      if (++reads > 1) throw new Error("Read unavailable");
      return instructions as never;
    });
    render(<ReceiptContext.Provider value={announce}><Knowledge /></ReceiptContext.Provider>);

    fireEvent.click(await screen.findByRole("button", { name: "Edit Project instructions" }));
    fireEvent.change(screen.getByRole("textbox", { name: "Project instructions" }), { target: { value: "Use the new glossary." } });
    fireEvent.keyDown(screen.getByRole("textbox", { name: "Project instructions" }), { key: "Enter" });

    expect(await screen.findByRole("alert")).toHaveTextContent("Instructions not loaded · Read unavailable");
    expect(apiFetch).toHaveBeenCalledWith(instructionsUrl, {
      method: "PUT", json: { files: { "instructions.md": "Use the new glossary." } },
    });
    await waitFor(() => expect(announce).toHaveBeenLastCalledWith(expect.stringMatching(/^Written /)));
    expect(screen.queryByRole("button", { name: "Edit Project instructions" })).toBeNull();
  });
});

it("a refreshed glossary cannot move an open Forget question to a different fact", async () => {
  let facts = { FIRST: "one", SECOND: "two", THIRD: "three" } as Record<string, string>;
  vi.mocked(apiFetch).mockImplementation(async (_url, options) => {
    if (options?.method === "PUT") return {} as never;
    return { detected: null, kb: facts, kb_path: null } as never;
  });
  const { container } = render(<Knowledge />);
  await screen.findByText("SECOND");
  fireEvent.click(within(withinRow("SECOND")).getByRole("button", {name:"×"}));
  expect(screen.getByText("Forget?")).toBeInTheDocument();
  facts = { SECOND: "two", THIRD: "three" };
  fireEvent.click(screen.getByRole("button", {name:"Use"}));
  await waitFor(() => expect(screen.queryByText("FIRST")).toBeNull());
  const question = container.querySelector("[data-question]");
  if (question) {
    expect(question.closest(".gadget-table-row")).toHaveTextContent("SECOND");
    fireEvent.click(within(question as HTMLElement).getByRole("button", {name:"Forget"}));
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/api/dictation/project-kb", {method:"PUT",json:{kb:{THIRD:"three"}}}));
  }
  function withinRow(key: string) { return screen.getByText(key).closest(".gadget-table-row") as HTMLElement; }
});
