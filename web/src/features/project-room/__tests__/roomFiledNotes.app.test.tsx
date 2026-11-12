import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../../lib/api";
import { RoomFiledNotesSection, filedNoteRefs, type FiledNoteRequest } from "../RoomFiledNotesSection";
import type { ResourcesRead, ResourcesState } from "../../../desk/drawer/useDrawerData";
import type { DrawerMember } from "../../../desk/drawer/members";

const wire = vi.hoisted(() => ({ apiFetch: vi.fn(), openRef: vi.fn() }));
vi.mock("../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../lib/api")>("../../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => wire.apiFetch(...args) };
});
vi.mock("../../../desk/openObject", async () => {
  const actual = await vi.importActual<typeof import("../../../desk/openObject")>("../../../desk/openObject");
  return { ...actual, openRef: (...args: unknown[]) => wire.openRef(...args) };
});

const projectId = "atlas";
const ref = "note:api-boundary" as const;

function mount({ resourceRefs = [ref], resourcesState = "ok", request = null, refreshResources = vi.fn(async () => ({ state: "ok", refs: [ref] } as ResourcesRead)),
  followCurrentResources = async (result: ResourcesRead) => result,
  members = [], onRequestHandled = vi.fn(), presentationReady = true,
}: {
  resourceRefs?: string[];
  resourcesState?: ResourcesState;
  request?: FiledNoteRequest;
  refreshResources?: () => Promise<ResourcesRead>;
  followCurrentResources?: (result: ResourcesRead) => Promise<ResourcesRead>;
  members?: DrawerMember[];
  onRequestHandled?: (seq: number) => void;
  presentationReady?: boolean;
} = {}) {
  return {
    ...render(<RoomFiledNotesSection projectId={projectId} resourceRefs={resourceRefs}
      resourcesState={resourcesState} refreshResources={refreshResources} followCurrentResources={followCurrentResources} members={members}
      request={request} onRequestHandled={onRequestHandled} presentationReady={presentationReady} />),
    refreshResources,
    onRequestHandled,
  };
}

beforeEach(() => {
  wire.apiFetch.mockReset();
  wire.openRef.mockReset();
});
afterEach(cleanup);

describe("active Room filed Note", () => {
  it("filters raw successful resource refs to live Note identities", () => {
    expect(filedNoteRefs([ref, "thread:t1", "note:", ref, "repository:r1"])).toEqual([ref]);
  });

  it("reads an uncached filed Note on Files open and opens it only on the owner's explicit press", async () => {
    wire.apiFetch.mockResolvedValue({ note: { id: "api-boundary", title: "API boundary", body_markdown: "Saved" } });
    mount();
    const row = await screen.findByRole("row", { name: /API boundary/i });
    const grid = screen.getByRole("grid", { name: "Files" });
    expect(within(grid).getAllByRole("columnheader").map((head) => head.getAttribute("data-col"))).toEqual(["name", "kind"]);
    expect(within(grid).getAllByRole("row")[1].querySelectorAll('[role="gridcell"]')).toHaveLength(2);
    fireEvent.click(row);
    expect(wire.openRef).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Open" })).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    await waitFor(() => expect(wire.openRef).toHaveBeenCalledExactlyOnceWith(ref,
      { projectReturn: { projectId, resourceRef: ref } }));
    expect(wire.apiFetch.mock.calls.every(([url, init]) => url === "/api/notes/api-boundary" && !init?.method)).toBe(true);
    expect(wire.apiFetch).toHaveBeenCalledTimes(2); // list read and explicit Open recheck
  });

  it("requires an authoritative Note GET for a cached row; 404 and read failure cannot Open", async () => {
    const member = { ref, id: ref, name: "Cached title", kind: "note" } as DrawerMember;
    wire.apiFetch.mockRejectedValueOnce(new ApiError(404, "Unknown note", {}));
    const first = mount({ members: [member] });
    await screen.findByRole("row", { name: /Note not available/i });
    expect(screen.getByRole("button", { name: "Open" })).toBeDisabled();
    first.unmount();
    wire.apiFetch.mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce({ note: { title: "Live title" } });
    mount({ members: [member] });
    await screen.findByRole("row", { name: /Note not read/i });
    expect(screen.getByRole("button", { name: "Open" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await screen.findByRole("row", { name: /Live title/i });
    expect(wire.openRef).not.toHaveBeenCalled();
  });

  it("rechecks a previously readable Note on Open and refuses a newly deleted one", async () => {
    wire.apiFetch.mockResolvedValueOnce({ note: { title: "Before deletion" } })
      .mockRejectedValueOnce(new ApiError(404, "Unknown note", {}));
    mount({ members: [{ ref, id: ref, name: "Cached title", kind: "note" } as DrawerMember] });
    fireEvent.click(await screen.findByRole("row", { name: /Before deletion/i }));
    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    await screen.findAllByText("Note not available");
    expect(wire.openRef).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Open" })).toBeDisabled();
  });

  it("returns to the exact filed row only after fresh membership and a successful Note read", async () => {
    wire.apiFetch.mockResolvedValue({ note: { id: "api-boundary", title: "API boundary" } });
    const result = mount({ request: { ref, seq: 5 } });
    await screen.findByText("Filed here");
    expect(result.refreshResources).toHaveBeenCalledOnce();
    expect(result.onRequestHandled).toHaveBeenCalledWith(5);
    const grid = screen.getByRole("grid", { name: "Files" });
    const row = within(grid).getByRole("row", { name: /API boundary/i });
    expect(row).toHaveAttribute("aria-selected", "true");
    expect(document.activeElement).toBe(row);
    expect(wire.openRef).not.toHaveBeenCalled();
  });

  it("keeps the filed return focus pending until the Room presents its Files slot", async () => {
    wire.apiFetch.mockResolvedValue({ note: { title: "API boundary" } });
    const request = { ref, seq: 17 };
    const followCurrentResources = async (result: ResourcesRead) => result;
    const mounted = mount({ request, followCurrentResources, presentationReady: false });
    const prior = document.createElement("button");
    document.body.append(prior);
    prior.focus();
    await screen.findByText("Filed here");
    const row = within(screen.getByRole("grid", { name: "Files" })).getByRole("row", { name: /API boundary/i });
    const button = row;
    const focus = vi.spyOn(button, "focus");
    expect(row).toHaveAttribute("aria-selected", "true");
    expect(document.activeElement).toBe(prior);
    expect(focus).not.toHaveBeenCalled();

    const props = { projectId, resourceRefs: [ref], resourcesState: "ok" as const,
      refreshResources: mounted.refreshResources, followCurrentResources, members: [],
      request, onRequestHandled: mounted.onRequestHandled };
    mounted.rerender(<RoomFiledNotesSection {...props} presentationReady />);
    expect(document.activeElement).toBe(button);
    expect(focus).toHaveBeenCalledOnce();
    mounted.rerender(<RoomFiledNotesSection {...props} presentationReady />);
    expect(focus).toHaveBeenCalledOnce();
    expect(mounted.onRequestHandled).toHaveBeenCalledOnce();
    prior.remove();
  });

  it("keeps the return target through two stale membership results and focuses only the current filed row", async () => {
    wire.apiFetch.mockResolvedValue({ note: { title: "Current record" } });
    const followCurrentResources = vi.fn(async (result: ResourcesRead) => {
      expect(result.state).toBe("stale");
      // Two legitimate newer reads superseded the original return read.
      const next: ResourcesRead = { state: "stale" };
      expect(next.state).toBe("stale");
      return { state: "ok", refs: [ref] } as ResourcesRead;
    });
    const refreshResources = vi.fn(async () => ({ state: "stale" } as ResourcesRead));
    const result = mount({ request: { ref, seq: 13 }, refreshResources, followCurrentResources });
    await screen.findByText("Filed here");
    expect(followCurrentResources).toHaveBeenCalledOnce();
    expect(result.onRequestHandled).toHaveBeenCalledWith(13);
    const row = within(screen.getByRole("grid", { name: "Files" })).getByRole("row", { name: /Current record/i });
    expect(row).toHaveAttribute("aria-selected", "true");
    expect(document.activeElement).toBe(row);
  });

  it("reports moved membership without inventing a filed row or reading the Note", async () => {
    const refreshResources = vi.fn(async () => ({ state: "ok", refs: [] } as ResourcesRead));
    mount({ resourceRefs: [ref], request: { ref, seq: 7 }, refreshResources });
    await screen.findByText("Not filed here");
    expect(refreshResources).toHaveBeenCalledOnce();
    expect(wire.apiFetch).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Open" })).toBeDisabled();
  });

  it("distinguishes an unavailable filed Note from a failed Note read and keeps Retry local", async () => {
    wire.apiFetch.mockRejectedValueOnce(new ApiError(404, "Unknown note", {}))
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce({ note: { id: "api-boundary", title: "API boundary" } });
    const first = mount({ request: { ref, seq: 8 } });
    await screen.findAllByText("Note not available");
    expect(screen.getByRole("button", { name: "Open" })).toBeDisabled();
    first.unmount();
    const second = mount({ request: { ref, seq: 9 } });
    await screen.findByText("Could not read the note · Nothing changed");
    expect(screen.getByRole("button", { name: "Retry" })).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await screen.findByText("Filed here");
    expect(second.refreshResources).toHaveBeenCalledTimes(2);
    expect(wire.openRef).not.toHaveBeenCalled();
  });

  it("keeps prior material labeled Last read when resource membership is not read", () => {
    mount({ resourcesState: "failed" });
    expect(screen.getByText("Could not read the files · Nothing changed")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Open" })).toBeDisabled();
  });

  it("keeps a retained row in place while the fresh Files read status moves into its action row", async () => {
    wire.apiFetch.mockResolvedValue({ note: { title: "API boundary" } });
    const mounted = mount();
    fireEvent.click(await screen.findByRole("row", { name: /API boundary/i }));
    const selectedRow = within(screen.getByRole("grid", { name: "Files" })).getByRole("row", { name: /API boundary/i });
    expect(screen.getByRole("button", { name: "Open" })).toBeEnabled();

    mounted.rerender(<RoomFiledNotesSection projectId={projectId} resourceRefs={[ref]} resourcesState="loading"
      refreshResources={mounted.refreshResources} followCurrentResources={async (result) => result} members={[]}
      request={null} onRequestHandled={mounted.onRequestHandled} />);

    const section = screen.getByTestId("room-files");
    expect(within(section).getByText("Reading files · Last read")).toBeInTheDocument();
    expect(within(section).getByRole("row", { name: /API boundary/i })).toBe(selectedRow);
    expect(selectedRow).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("button", { name: "Open" })).toBeDisabled();
    expect(wire.apiFetch).toHaveBeenCalledTimes(1);
  });

  it("offers Retry for an uncached Note read failure before any row is selected", async () => {
    wire.apiFetch.mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce({ note: { id: "api-boundary", title: "API boundary" } });
    mount();
    await screen.findByRole("row", { name: /Note not read/i });
    expect(screen.getByRole("button", { name: "Retry" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Open" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await screen.findByRole("row", { name: /API boundary/i });
    expect(wire.openRef).not.toHaveBeenCalled();
  });
});
