import { fireEvent, render, screen, waitFor } from "@testing-library/react";
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
