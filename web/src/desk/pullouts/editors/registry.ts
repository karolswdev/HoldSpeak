/** Kind-keyed inline editor content registry (HS-117-15).
 * The `satisfies` gate ensures compile-time completeness. */
import { createElement, lazy, Suspense } from "react";
import type { PrimitiveKind } from "../../../lib/primitives";
import type { InlineEditorContent } from "./types";
import { SurfaceState } from "../../surface";
import { watchChunk } from "../../../runtime/freshBuild";
import { KbEditor } from "./KbEditor";
import { WorkflowEditor } from "./WorkflowEditor";
import { RecipeEditor } from "./RecipeEditor";

/** The note editor is not on glass at first paint: it and CodeMirror are
 *  their own chunk (measure 2026-11-08), loaded when a note opens, with the
 *  surface's loading face until it arrives. */
const NoteEditorCore = lazy(watchChunk(() => import("./NoteEditor").then((m) => ({ default: m.NoteEditor }))));

const NoteEditor: InlineEditorContent = (props) =>
  createElement(Suspense, { fallback: createElement(SurfaceState, { loading: true }) }, createElement(NoteEditorCore, props));

/** The eyebrow label shown in the editor header for each kind. */
export const EDITOR_LABELS: Record<PrimitiveKind, string> = {
  note: "Note",
  kb: "Drawer",
  recipe: "Mode",
  workflow: "Workflow",
  decision: "Decision",
  meeting: "Meeting",
  artifact: "Artifact",
  chain: "Sequence",
  coder: "Agent",
  directory: "Zone",
  project: "Project",
  repository: "Repository",
  roadmap: "Roadmap",
  story: "Story",
  workbench: "Automation",
  intelligence: "Intelligence",
  people: "People",
  thread: "Thread",
  game: "Game",
  layout: "Layout",
} satisfies Record<PrimitiveKind, string>;

export const INLINE_EDITOR_CONTENT: Record<PrimitiveKind, InlineEditorContent | null> = {
  note: NoteEditor,
  kb: KbEditor,
  workflow: WorkflowEditor,
  recipe: RecipeEditor,
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
  people: null,
  thread: null,
  game: null,
  layout: null,
} satisfies Record<PrimitiveKind, InlineEditorContent | null>;
