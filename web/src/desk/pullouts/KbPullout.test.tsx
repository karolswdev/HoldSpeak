import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../lib/api";
import { EMPTY_ITEMS, fromWireKb, fromWireNote } from "../api";
import { useDesk } from "../store";
import { KbPullout } from "./KbPullout";

vi.mock("../surface/SurfaceFooter", () => ({
  SurfaceFooter: ({ receipt, verbs }: { receipt?: React.ReactNode; verbs: React.ReactNode }) => <footer>{receipt}{verbs}</footer>,
}));
vi.mock("../components/DeskFilingStrip", () => ({ DeskFilingStrip: () => <div data-testid="filing-strip" /> }));
vi.mock("./editors", () => ({ INLINE_EDITOR_CONTENT: {} }));
vi.mock("../../lib/api", async (original) => ({ ...(await original<typeof import("../../lib/api")>()), apiFetch: vi.fn() }));

// Exact selected rows from root's isolated real GET /api/notes and GET
// /api/kbs answers, captured after accepted Note/Knowledge creates on
// 2026-10-15 in .tmp/surface-refinement/recorded-wire/wire.json (reads).
const note = fromWireNote({ id: "note_4a61dff7ea64", title: "Migration checkpoints", body_markdown: "Keep the rollback owner visible.", tags: [],
  created_at: "2026-10-15T07:51:33Z", updated_at: "2026-10-15T07:51:33Z", last_modified: "2026-10-15T07:51:33Z", deleted: false })!;
const mixed = fromWireKb({ id: "kb_e0979c2ebb25", name: "Architecture knowledge",
  member_ids: ["note:note_4a61dff7ea64", "note:unavailable-audit-member"], created_at: "2026-10-15T07:51:33Z", last_modified: "2026-10-15T07:51:33Z", deleted: false })!;
const unavailable = fromWireKb({ id: "kb_31c00b037075", name: "Unavailable knowledge",
  member_ids: ["note:unavailable-audit-member"], created_at: "2026-10-15T07:51:34Z", last_modified: "2026-10-15T07:51:34Z", deleted: false })!;
const copy = vi.fn();
const openPullout = vi.fn();
const openEditor = vi.fn();
const object = (kb = mixed) => ({ kind: "kb" as const, id: kb.id, title: kb.name, ref: kb });
const memberRow = (ref: string) => {
  const identity = document.querySelector(`[data-member-ref="${ref}"]`);
  expect(identity).not.toBeNull();
  return identity!.closest(".surface-ledger-row") as HTMLElement;
};

beforeEach(() => {
  vi.clearAllMocks();
  copy.mockResolvedValue(undefined);
  Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText: copy } });
  useDesk.setState({ items: { ...EMPTY_ITEMS, kb: [mixed, unavailable], note: [note] }, editingId: null,
    openPullout, openEditor, closeEditor: vi.fn() });
});
afterEach(cleanup);

describe("Knowledge reader membership", () => {
  it("retains available and unavailable stored members, with Open only on a real object", () => {
    render(<KbPullout object={object()} onClose={vi.fn()} />);
    const available = memberRow(mixed.memberIds[0]);
    const missing = memberRow(mixed.memberIds[1]);
    expect(available).toHaveTextContent(note.title);
    expect(missing).toHaveTextContent("Item unavailable");
    expect(missing).toHaveTextContent("Unavailable");
    expect(within(missing).queryByRole("button", { name: /Open/ })).toBeNull();
    expect(screen.queryByText("No entries")).toBeNull();
    fireEvent.click(within(available).getByRole("button", { name: "Open note" }));
    expect(openPullout).toHaveBeenCalledWith(mixed.memberIds[0]);
    expect(screen.getByTestId("filing-strip")).toBeInTheDocument();
    expect(apiFetch).not.toHaveBeenCalled();
  });

  it("keeps all-unavailable membership distinct from an empty collection and copies its ref", async () => {
    render(<KbPullout object={object(unavailable)} onClose={vi.fn()} />);
    expect(memberRow(unavailable.memberIds[0])).toHaveTextContent("Item unavailable");
    expect(screen.queryByText("No entries")).toBeNull();
    expect(screen.queryByRole("button", { name: "Open" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Copy" }));
    await waitFor(() => expect(copy).toHaveBeenCalledWith(unavailable.memberIds[0]));
    expect(await screen.findByText("COPIED")).toBeInTheDocument();
  });

  it("copies every member in stored order using real titles or unresolved qualified refs", async () => {
    render(<KbPullout object={object()} onClose={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: "Copy" }));
    await waitFor(() => expect(copy).toHaveBeenCalledWith(`${note.title}\n${mixed.memberIds[1]}`));
    expect(await screen.findByText("COPIED")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Edit" }));
    expect(openEditor).toHaveBeenCalledWith(mixed.id);
  });

  it("reserves No entries for genuinely empty stored membership", () => {
    render(<KbPullout object={object({ ...mixed, memberIds: [] })} onClose={vi.fn()} />);
    expect(screen.getByText("No entries")).toBeInTheDocument();
    expect(screen.queryByText("Item unavailable")).toBeNull();
    expect(screen.queryByRole("button", { name: "Open" })).toBeNull();
    expect(apiFetch).not.toHaveBeenCalled();
  });
});
