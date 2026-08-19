import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../lib/api";
import { useDesk } from "../store";
import { NotePullout } from "./NotePullout";
import { adoptThought, originalThought, thoughtForNote } from "../thoughts";

vi.mock("../surface/SurfaceFooter", () => ({ SurfaceFooter: ({ verbs }: { verbs: unknown }) => <footer>{verbs as any}</footer> }));
vi.mock("../components/DeskFilingStrip", () => ({ DeskFilingStrip: () => null }));
vi.mock("../surface/Material", () => ({ Material: ({ children }: { children: unknown }) => <>{children}</> }));
vi.mock("../surface/Surface", () => ({ SurfaceState: () => null }));
vi.mock("./editors", () => ({ INLINE_EDITOR_CONTENT: {} }));
vi.mock("./editors/ThoughtNoteEditor", () => ({ ThoughtNoteEditor: () => null }));
vi.mock("../hooks/useCopyReceipt", () => ({ useCopyReceipt: () => ({ copy: vi.fn(), receipt: null }) }));
vi.mock("../api", async (importOriginal) => ({ ...(await importOriginal<typeof import("../api")>()), qualifiedRef: () => "note:note-1" }));
vi.mock("../shell", () => ({ openSurfaceOr: vi.fn() }));
vi.mock("../thoughts", () => ({
  thoughtForNote: vi.fn(), adoptThought: vi.fn(), originalThought: vi.fn(),
  sourceLabel: (kind: string) => kind,
}));

const ordinary = {
  ownership: "ordinary" as const,
  note: { id: "note-1", title: "Note", body_markdown: "body", tags: [], last_modified: "1" },
  source_precondition: { content_sha256: "sha-1", last_modified: "1" },
};
const object = { id: "note-1", kind: "note", title: "Note", ref: { kind: "note", bodyMarkdown: "body" } } as any;
const ownedThought = {
  id: "thought-1", source: { kind: "typed" as const }, raw_captured_at: "2026-01-01T00:00:00Z",
  state: "working" as const, aggregate_revision: 1, lifecycle_revision: 1, working_revision: 1,
  attachment_revision: 1, filing_status: "missing" as const,
  working_note: ordinary.note,
};

afterEach(() => { cleanup(); vi.clearAllMocks(); sessionStorage.clear(); });

describe("NotePullout adoption recovery", () => {
  it("keeps the request id and names a generic adoption failure without claiming a change", async () => {
    vi.mocked(thoughtForNote).mockResolvedValue(ordinary);
    vi.mocked(adoptThought).mockRejectedValue(new Error("offline"));
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    const develop = await screen.findByRole("button", { name: "Develop this thought" });
    await act(async () => { fireEvent.click(develop); });
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("unchanged and still here"));
    const firstId = vi.mocked(adoptThought).mock.calls[0][0].request_id;

    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Develop this thought" })); });
    await waitFor(() => expect(adoptThought).toHaveBeenCalledTimes(2));
    expect(vi.mocked(adoptThought).mock.calls[1][0].request_id).toBe(firstId);
  });

  it("uses changed-elsewhere language only for the named adoption CAS response", async () => {
    vi.mocked(thoughtForNote).mockResolvedValue(ordinary);
    vi.mocked(adoptThought).mockRejectedValue(new ApiError(409, "conflict", {
      error: "note_adoption_conflict", note: { ...ordinary.note, title: "Current", last_modified: "2" },
      source_precondition: { content_sha256: "sha-2", last_modified: "2" },
    }));
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    const develop = await screen.findByRole("button", { name: "Develop this thought" });
    await act(async () => { fireEvent.click(develop); });
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("changed elsewhere"));
  });

  it("does not claim unchanged when adoption recovery cannot read ownership", async () => {
    vi.mocked(thoughtForNote).mockResolvedValueOnce(ordinary).mockResolvedValueOnce(ordinary).mockRejectedValueOnce(new Error("offline"));
    vi.mocked(adoptThought).mockRejectedValue(new Error("offline"));
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);
    const develop = await screen.findByRole("button", { name: "Develop this thought" });
    await act(async () => { fireEvent.click(develop); });
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("couldn't confirm whether this was saved"));
    expect(screen.getByRole("status")).not.toHaveTextContent("unchanged");
  });

  it("scrolls a successful Original reveal into the nearest visible pullout position", async () => {
    const scrollIntoView = vi.fn();
    Object.defineProperty(HTMLElement.prototype, "scrollIntoView", { configurable: true, value: scrollIntoView });
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: ownedThought });
    vi.mocked(originalThought).mockResolvedValue({ ...ownedThought, raw_text: "Exact original" });
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);

    fireEvent.click(await screen.findByRole("button", { name: /Original kept/ }));
    await waitFor(() => expect(screen.getByText("Exact original")).toBeInTheDocument());
    expect(screen.getByText("Exact original")).toHaveClass("thought-original-raw");
    expect(scrollIntoView).toHaveBeenCalledWith({ block: "nearest", behavior: "smooth" });
    expect(screen.getByRole("region", { name: "Original kept" })).toHaveFocus();
  });

  it("does not scroll when Original fails to load", async () => {
    const scrollIntoView = vi.fn();
    Object.defineProperty(HTMLElement.prototype, "scrollIntoView", { configurable: true, value: scrollIntoView });
    vi.mocked(thoughtForNote).mockResolvedValue({ ownership: "thought", thought: ownedThought });
    vi.mocked(originalThought).mockRejectedValue(new Error("offline"));
    useDesk.setState({ editingId: null, refresh: vi.fn(), openEditor: vi.fn(), closeEditor: vi.fn() });
    render(<NotePullout object={object} onClose={vi.fn()} />);

    fireEvent.click(await screen.findByRole("button", { name: /Original kept/ }));
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Could not open the original"));
    expect(scrollIntoView).not.toHaveBeenCalled();
  });

  it("keeps Original raw text wrapped locally without normalizing its bytes", () => {
    const css = readFileSync(resolve(process.cwd(), "src/desk/components/pullout.css"), "utf8");
    expect(css).toMatch(/\.thought-original-raw\s*\{[^}]*white-space:\s*pre-wrap;/s);
    expect(css).toMatch(/\.thought-original-raw\s*\{[^}]*overflow-wrap:\s*anywhere;/s);
    expect(css).toMatch(/\.thought-original-raw\s*\{[^}]*max-width:\s*100%;/s);
  });
});
