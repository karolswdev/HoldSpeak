import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../lib/api";
import { EMPTY_ITEMS, fromWireDirectory, fromWireNote, qualifiedRef } from "../api";
import { useDesk } from "../store";
import { DirectoryPullout } from "./DirectoryPullout";

vi.mock("../surface/SurfaceFooter", () => ({
  SurfaceFooter: ({ receipt, verbs }: { receipt?: React.ReactNode; verbs?: React.ReactNode }) => <footer>{receipt}{verbs}</footer>,
}));
vi.mock("../components/DeskFilingStrip", () => ({
  DeskFilingStrip: ({ objectRef }: { objectRef: string }) => <div data-testid="filing-strip" data-ref={objectRef} />,
}));
const shell = vi.hoisted(() => ({ openPrimitive: vi.fn(), openProjectRoom: vi.fn(), openSurfaceOr: vi.fn() }));
vi.mock("../shell", async (original) => ({ ...(await original<typeof import("../shell")>()), ...shell }));
vi.mock("../../lib/api", async (original) => ({ ...(await original<typeof import("../../lib/api")>()), apiFetch: vi.fn() }));

// Actual isolated directory and note route answers, produced 2026-10-15.
// .tmp/desk-drawers-live/produced-{directory,note}-wire.json.
const folder = fromWireDirectory({ id: "dir_b5c056b59f3e", name: "Platform", name_normalized: "platform", parent_id: null,
  member_ids: ["note:note_0b9ebdadf0fa"], created_at: "2026-10-16T01:39:56Z" })!;
const child = fromWireDirectory({ id: "dir_3e8aa70e9523", name: "Architecture", name_normalized: "architecture", parent_id: folder.id,
  member_ids: [], created_at: "2026-10-16T01:39:56Z" })!;
const note = fromWireNote({ id: "note_0b9ebdadf0fa", title: "Rollback plan", body_markdown: "Keep the previous deployment ready.", tags: [],
  created_at: "2026-10-16T01:39:56Z", updated_at: "2026-10-16T01:39:56Z", last_modified: "2026-10-16T01:39:56Z", deleted: false })!;
const openPullout = vi.fn();
const object = (directory = folder) => ({ kind: "directory" as const, id: directory.id, title: directory.name, ref: directory });

beforeEach(() => {
  vi.clearAllMocks();
  useDesk.setState({ items: { ...EMPTY_ITEMS, directory: [folder, child], note: [note] }, openPullout });
});
afterEach(cleanup);

// W3-ZONE: the list is a dense ObjectList; a pointer press (detail 1) opens.
const press = (name: RegExp) => fireEvent.click(screen.getByRole("button", { name }), { detail: 1 });

describe("Directory contents", () => {
  it("renders actual child folders and stored members and opens their canonical refs", () => {
    render(<DirectoryPullout object={object()} onClose={vi.fn()} />);
    // W3-ZONE: no "Contents · N" heading; the count is the status bar's.
    expect(screen.queryByRole("heading")).toBeNull();
    expect(screen.getByTestId("zone-facts")).toHaveTextContent(/^2 objects$/);
    expect(screen.getByRole("toolbar", { name: "Drawer" })).toBeInTheDocument();
    press(/^Architecture, Drawer/);
    expect(openPullout).toHaveBeenCalledWith(qualifiedRef("directory", child.id));
    press(/^Rollback plan, Note/);
    expect(shell.openPrimitive).toHaveBeenCalledWith(`note:${note.id}`);
    expect(openPullout).not.toHaveBeenCalledWith(note.id);
    expect(screen.getByTestId("filing-strip")).toHaveAttribute("data-ref", qualifiedRef("directory", folder.id));
    expect(apiFetch).not.toHaveBeenCalled();
  });

  it("deduplicates child membership, supports bare refs and retains kind-qualified collisions", () => {
    const mixed = { ...folder, memberIds: [`directory:${child.id}`, note.id, `note:${child.id}`] };
    const otherNote = { ...note, id: child.id, title: "Same id, different kind" };
    useDesk.setState({ items: { ...EMPTY_ITEMS, directory: [mixed, child], note: [note, otherNote] } });
    render(<DirectoryPullout object={object(mixed)} onClose={vi.fn()} />);
    expect(screen.getAllByRole("button", { name: /^Architecture/ })).toHaveLength(1);
    expect(screen.getByTestId("zone-facts")).toHaveTextContent(/^3 objects$/);
    press(/^Rollback plan/);
    expect(shell.openPrimitive).toHaveBeenCalledWith(`note:${note.id}`);
    press(/^Same id, different kind/);
    expect(shell.openPrimitive).toHaveBeenCalledWith(`note:${child.id}`);
  });

  it("shows unresolved stored membership as unavailable, with no false Open or empty state", () => {
    const missing = { ...folder, memberIds: ["note:unavailable-member"] };
    useDesk.setState({ items: { ...EMPTY_ITEMS, directory: [missing] } });
    render(<DirectoryPullout object={object(missing)} onClose={vi.fn()} />);
    const identity = screen.getByTestId("zone-unavailable");
    expect(identity).toHaveTextContent("Item unavailable");
    const row = identity.closest(".object-list-row")!;
    expect(row).toHaveAttribute("data-object-id", missing.memberIds[0]);
    expect(within(row as HTMLElement).getByText("Unavailable")).toBeInTheDocument();
    // A press selects the row but opens nothing; no Open verb for it.
    press(/^Item unavailable/);
    expect(shell.openPrimitive).not.toHaveBeenCalled();
    expect(openPullout).not.toHaveBeenCalled();
    expect(screen.queryByTestId("zone-open")).toBeNull();
    expect(screen.queryByText("Nothing filed here")).toBeNull();
    expect(screen.queryByText("No members")).toBeNull();
  });

  it("reserves the empty state for an empty drawer and has no zero count or dead Drop action", () => {
    useDesk.setState({ items: { ...EMPTY_ITEMS, directory: [child] } });
    render(<DirectoryPullout object={object(child)} onClose={vi.fn()} />);
    expect(screen.getByText("Nothing filed here")).toBeInTheDocument();
    expect(screen.queryByRole("heading")).toBeNull();
    expect(screen.queryByText(/0 members/)).toBeNull();
    expect(screen.queryByText(/0 objects/)).toBeNull();
    expect(screen.getByTestId("zone-facts")).toBeEmptyDOMElement();
    expect(screen.queryByRole("button", { name: /Drop/ })).toBeNull();
    const dictate = within(screen.getByRole("toolbar", { name: "Drawer" })).getByRole("button", { name: "Dictate about this" });
    expect(dictate).toHaveClass("btn", "btn--ghost");
    fireEvent.click(dictate);
    expect(shell.openSurfaceOr).toHaveBeenCalledWith("dictate", "/dictation", qualifiedRef("directory", child.id));
  });

  it("a press selects and the toolbar's Open opens; Icons is the other view, remembered", () => {
    render(<DirectoryPullout object={object()} onClose={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: /^Rollback plan/ }));
    expect(screen.getByTestId("zone-facts")).toHaveTextContent("2 objects · 1 selected");
    fireEvent.click(screen.getByTestId("zone-open"));
    expect(shell.openPrimitive).toHaveBeenCalledWith(`note:${note.id}`);
    fireEvent.click(screen.getByRole("button", { name: "Icons" }));
    expect(useDesk.getState().zoneViewPrefs[`directory:${folder.id}`]?.view).toBe("icons");
    expect(screen.queryByRole("grid")).toBeNull();
    expect(screen.getByRole("button", { name: "List" })).toHaveAttribute("aria-pressed", "false");
  });
});
