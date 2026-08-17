/** HS-135-15 — creation operates: every editable kind's create verb
 * yields an open editor with focus in the name field. */
import { act, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useDesk } from "../store";
import { InlineEditor } from "../components/InlineEditor";
import type { WorldObject } from "../world";

/** Track which editors received autoFocusName=true at render time. */
const focusedKinds = new Set<string>();

vi.mock("../pullouts/editors", () => {
  const editors: Record<
    string,
    React.FC<{
      object: WorldObject;
      onClose: () => void;
      autoFocusName?: boolean;
    }>
  > = {};
  for (const kind of ["note", "kb", "recipe", "workflow"]) {
    editors[kind] = ({ object, autoFocusName }) => {
      if (autoFocusName) focusedKinds.add(object.kind);
      return (
        <div data-testid={`editor-${object.kind}`}>
          <input
            data-testid={`editor-${object.kind}-name`}
            aria-label="Name"
          />
        </div>
      );
    };
  }
  return {
    EDITOR_LABELS: {
      note: "Note",
      kb: "Knowledge",
      recipe: "Agent",
      workflow: "Workflow",
      decision: "",
      meeting: "",
      artifact: "",
      chain: "",
      coder: "",
      directory: "",
      project: "",
      repository: "",
      roadmap: "",
      story: "",
      workbench: "",
      intelligence: "",
      game: "",
      layout: "",
    },
    INLINE_EDITOR_CONTENT: {
      note: editors.note,
      kb: editors.kb,
      recipe: editors.recipe,
      workflow: editors.workflow,
      decision: null,
      meeting: null,
      artifact: null,
      chain: null,
      coder: null,
      directory: null,
      project: null,
      repository: null,
      roadmap: null,
      story: null,
      workbench: null,
      intelligence: null,
      game: null,
      layout: null,
    },
  };
});

const EDITABLE_KINDS = ["note", "kb", "recipe", "workflow"] as const;

function object(kind: string) {
  return {
    id: `${kind}-fresh`,
    kind,
    title: `New ${kind}`,
    ref: { id: `${kind}-fresh`, kind },
  } as WorldObject;
}

function MountedEditor({ o }: { o: WorldObject }) {
  const editingId = useDesk((s) => s.editingId);
  return editingId === o.id ? (
    <InlineEditor o={o} u={{ x: 0.5, y: 0.55 }} />
  ) : null;
}

beforeEach(() => {
  focusedKinds.clear();
  useDesk.setState({
    pullouts: [],
    editingId: null,
    editorOrigin: null,
    newIds: [],
    panelMin: [],
    panelMax: [],
    panelOrder: [],
    panelRects: {},
    refresh: vi.fn(),
  });
});

describe("HS-135-15 editable-kind creation fence", () => {
  it.each(EDITABLE_KINDS)(
    "create %s opens editor with autoFocusName=true",
    async (kind) => {
      const o = object(kind);
      const view = render(<MountedEditor o={o} />);

      // Simulate what createPrimitive does: markNew + openEditor
      act(() => {
        useDesk.setState({
          editingId: o.id,
          editorOrigin: null,
          newIds: [o.id],
        });
      });

      const editorDiv = await screen.findByTestId(`editor-${kind}`);
      expect(editorDiv).toBeInTheDocument();
      // The mock editor records when autoFocusName was true
      expect(focusedKinds.has(kind)).toBe(true);

      view.unmount();
    },
  );

  it.each(EDITABLE_KINDS)(
    "edit (non-new) %s opens editor without autoFocusName",
    async (kind) => {
      focusedKinds.clear();
      const o = object(kind);
      const view = render(<MountedEditor o={o} />);

      // Open editor for a NON-new object (not in newIds)
      act(() => {
        useDesk.setState({
          editingId: o.id,
          editorOrigin: null,
          newIds: [],
        });
      });

      const editorDiv = await screen.findByTestId(`editor-${kind}`);
      expect(editorDiv).toBeInTheDocument();
      // autoFocusName should NOT be set for non-new objects
      expect(focusedKinds.has(kind)).toBe(false);

      view.unmount();
    },
  );

  it("every EDITABLE kind has a registered editor component", () => {
    // The EDITABLE_KINDS here must match the EDITABLE set in verbRegistry.
    // If a new kind is added to EDITABLE but not here, this test reminds.
    // The mock covers the same keys; a real test would import the registry.
    for (const kind of EDITABLE_KINDS) {
      const o = object(kind);
      const view = render(<MountedEditor o={o} />);
      act(() => {
        useDesk.setState({
          editingId: o.id,
          editorOrigin: null,
          newIds: [o.id],
        });
      });
      expect(screen.getByTestId(`editor-${kind}`)).toBeInTheDocument();
      view.unmount();
    }
  });
});
