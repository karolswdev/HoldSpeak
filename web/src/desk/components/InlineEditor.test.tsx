// HS-129-08 — editors use the desk window contract, not a lightbox.
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useDesk } from "../store";
import { InlineEditor } from "./InlineEditor";
import { NotePullout } from "../pullouts/NotePullout";
import { KbPullout } from "../pullouts/KbPullout";
import { RecipePullout } from "../pullouts/RecipePullout";
import { WorkflowPullout } from "../pullouts/WorkflowPullout";
import { useDebouncedSave } from "../pullouts/editors/useDebouncedSave";

vi.mock("../pullouts/editors", () => {
  const Content = ({ object }: { object: { kind: string } }) => (
    <div data-testid={`editor-${object.kind}`}>Editor</div>
  );
  return {
    EDITOR_LABELS: { note: "Note", kb: "Knowledge", recipe: "Recipe", workflow: "Workflow" },
    INLINE_EDITOR_CONTENT: { note: Content, kb: Content, recipe: Content, workflow: Content },
  };
});

const closeRefresh = vi.fn();
const object = (kind: "note" | "kb" | "recipe" | "workflow") => ({
  id: `${kind}-1`,
  kind,
  title: `${kind} title`,
  ref: { id: `${kind}-1`, kind },
}) as any;

function MountedEditor({ o }: { o: ReturnType<typeof object> }) {
  const editingId = useDesk((s) => s.editingId);
  return editingId === o.id ? <InlineEditor o={o} u={{ x: 0.25, y: 0.25 }} /> : null;
}

function SaveProbe() {
  const save = useDebouncedSave("note", "note-1");
  return <button type="button" onClick={() => save({ title: "Saved" })}>Write</button>;
}

beforeEach(() => {
  closeRefresh.mockReset();
  useDesk.setState({
    pullouts: [],
    editingId: null,
    editorOrigin: null,
    panelMin: [],
    panelMax: [],
    panelOrder: [],
    panelRects: {},
    refresh: closeRefresh,
  });
});

describe("HS-129-08 editor windows", () => {
  it.each(["note", "kb", "recipe", "workflow"] as const)(
    "opens %s in a desk window without a vignette and returns focus on Escape",
    async (kind) => {
      const o = object(kind);
      const view = render(
        <>
          <button type="button">Open {kind}</button>
          <MountedEditor o={o} />
        </>,
      );
      const opener = screen.getByRole("button", { name: `Open ${kind}` });
      opener.focus();
      act(() => useDesk.setState({ editingId: o.id, editorOrigin: { x: 24, y: 24 } }));

      const window = await screen.findByRole("region", { name: `Edit ${kind} title` });
      expect(window).toHaveClass("desk-window-shell");
      expect(screen.getByTestId(`editor-${kind}`)).toBeInTheDocument();
      expect(view.container.querySelector(".desk-vignette")).toBeNull();

      fireEvent.keyDown(window, { key: "Escape" });
      await waitFor(() => expect(screen.queryByRole("region", { name: `Edit ${kind} title` })).toBeNull());
      expect(document.activeElement).toBe(screen.getByRole("button", { name: `Open ${kind}` }));
      view.unmount();
    },
  );

  it.each([
    ["note", NotePullout],
    ["kb", KbPullout],
    ["recipe", RecipePullout],
    ["workflow", WorkflowPullout],
  ] as const)("hosts %s editing in its open pullout", (kind, Pullout) => {
    const o = object(kind);
    useDesk.setState({ editingId: o.id, pullouts: [{ id: o.id, origin: null }] });
    const { container } = render(<Pullout object={o} onClose={vi.fn()} />);

    expect(screen.getByTestId(`editor-${kind}`)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save" })).toBeInTheDocument();
    expect(container.querySelector(".desk-vignette")).toBeNull();
  });

  it("keeps the debounced editor write path", () => {
    vi.useFakeTimers();
    const updatePrimitive = vi.fn();
    useDesk.setState({ updatePrimitive });
    render(<SaveProbe />);

    fireEvent.click(screen.getByRole("button", { name: "Write" }));
    act(() => vi.advanceTimersByTime(450));
    expect(updatePrimitive).toHaveBeenCalledWith("note", "note-1", { title: "Saved" });
    vi.useRealTimers();
  });
});
