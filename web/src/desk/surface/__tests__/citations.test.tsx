// HS-111-05 — the citation token species (the ONE openable "grounded
// on" rendering, promoted out of ProjectMemoryCore): a smoke lock on
// its label grammar, its open verb, and the honest match arithmetic.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { CitationChips, NO_WINDOW_REF_KINDS, groundedMatchCount, openSourceRef, refOpensWindow, sourceLabel } from "../citations";
import { EMPTY_ITEMS, type Items } from "../../api";
import { useDesk } from "../../store";

vi.mock("../../shell", () => ({
  openPrimitive: vi.fn(),
  openSurfaceOr: vi.fn(),
}));

const items = {
  ...EMPTY_ITEMS,
  note: [{ kind: "note", id: "shared", title: "Release checklist" }],
  project: [{ kind: "project", id: "shared", name: "Migration release" }],
  kb: [{ kind: "kb", id: "shared", name: "Architecture decisions" }],
  thread: [{ kind: "thread", id: "shared", title: "Release discussion" }],
  meeting: [{ kind: "meeting", id: "shared", title: "Release review" }],
} as unknown as Items;

beforeEach(() => useDesk.setState({ items: EMPTY_ITEMS }));
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("the citation token species", () => {
  it("renders one openable token per source ref", () => {
    const onOpen = vi.fn();
    render(
      <CitationChips refs={["meeting:m1", "decision:d1"]} onOpen={onOpen} />,
    );
    const meeting = screen.getByRole("button", { name: "Meeting · m1" });
    expect(meeting).toHaveAttribute("title", "meeting:m1");
    expect(screen.getByRole("button", { name: "Decision · d1" })).toBeTruthy();
    fireEvent.click(meeting);
    expect(onOpen).toHaveBeenCalledWith("meeting:m1");
  });

  it.each([
    ["note:shared", "Note · Release checklist"],
    ["project:shared", "Project · Migration release"],
    ["knowledge:shared", "Knowledge · Architecture decisions"],
  ])("names cached qualified %s without borrowing another kind's identical ID", (ref, label) => {
    useDesk.setState({ items });
    const onOpen = vi.fn();
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    render(<CitationChips refs={[ref]} onOpen={onOpen} />);
    const token = screen.getByRole("button", { name: label });
    expect(token).toHaveAttribute("title", ref);
    fireEvent.click(token);
    expect(onOpen).toHaveBeenCalledExactlyOnceWith(ref);
    expect(fetch).not.toHaveBeenCalled();
  });

  it.each([
    ["thread:shared#message-7", "Thread · Release discussion"],
    ["meeting:shared?view=review&segment=2", "Meeting · Release review"],
  ])("names scoped %s but gives the opener the original exact ref", (ref, label) => {
    useDesk.setState({ items });
    const onOpen = vi.fn();
    render(<CitationChips refs={[ref]} onOpen={onOpen} />);
    const token = screen.getByRole("button", { name: label });
    expect(token).toHaveAttribute("title", ref);
    fireEvent.click(token);
    expect(onOpen).toHaveBeenCalledExactlyOnceWith(ref);
  });

  it("a missing qualified kind stays openable and never borrows an unrelated cached name", () => {
    useDesk.setState({ items });
    const onOpen = vi.fn();
    render(<CitationChips refs={["decision:shared"]} onOpen={onOpen} />);
    const token = screen.getByRole("button", { name: "Decision · shared" });
    expect(token).toBeEnabled();
    fireEvent.click(token);
    expect(onOpen).toHaveBeenCalledExactlyOnceWith("decision:shared");
  });

  it("the cached name can arrive after the citation without a separate fetch", () => {
    render(<CitationChips refs={["note:shared"]} onOpen={vi.fn()} />);
    expect(screen.getByRole("button", { name: "Note · shared" })).toBeEnabled();
    act(() => useDesk.setState({ items }));
    expect(screen.getByRole("button", { name: "Note · Release checklist" })).toHaveAttribute("title", "note:shared");
  });

  it("keeps a full long cached title and its original identity", () => {
    const title = "Architecture migration review and release readiness across every platform and integration";
    useDesk.setState({ items: { ...items, note: [{ ...items.note[0], title }] } });
    render(<CitationChips refs={["note:shared"]} onOpen={vi.fn()} />);
    const token = screen.getByRole("button", { name: `Note · ${title}` });
    expect(token).toHaveTextContent(title);
    expect(token).toHaveAttribute("title", "note:shared");
  });

  it("sourceLabel keeps the pure fallback metadata grammar", () => {
    expect(sourceLabel("note:shared")).toBe("Note · shared");
    expect(sourceLabel("desk_decision:shared")).toBe("Decision · shared");
  });

  // Astra's finding on PR #786: an Ask citation of a memory kind with no
  // window was a dead click (`openPullout: unknown id`). It is plain text.
  it.each([
    ["send:csend_1", "Send · csend_1"],
    ["project_update:u1", "Project update · u1"],
    ["prep_brief:b1", "Prep brief · b1"],
    ["calendar_event:e1", "Calendar event · e1"],
  ])("%s is plain text, never a button; the default open does nothing", async (ref, label) => {
    const shell = await import("../../shell");
    vi.mocked(shell.openPrimitive).mockClear();
    render(<CitationChips refs={[ref, "meeting:m1"]} />);
    expect(screen.getByTestId("citation-plain").textContent).toBe(label);
    expect(screen.getByTestId("citation-plain")).toHaveAttribute("title", ref);
    expect(screen.queryByRole("button", { name: label })).toBeNull();
    expect(screen.getByRole("button", { name: "Meeting · m1" })).toBeTruthy();
    openSourceRef(ref);
    expect(shell.openPrimitive).not.toHaveBeenCalled();
    expect(refOpensWindow(ref)).toBe(false);
    expect(NO_WINDOW_REF_KINDS).toContain(ref.split(":")[0]);
  });

  it("renders nothing for an empty receipt (no zero-theater)", () => {
    const { container } = render(<CitationChips refs={[]} />);
    expect(container.innerHTML).toBe("");
  });

  it("derives the honest grounded-on count: matches minus overflow", () => {
    expect(groundedMatchCount({ matchedCount: 47, overflowCount: 35 })).toBe(
      12,
    );
    expect(groundedMatchCount(null)).toBe(0);
  });
});
