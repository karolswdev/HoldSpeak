/** Kind-keyed inline editor content registry (HS-117-15).
 * The `satisfies` gate ensures compile-time completeness. */
import type { PrimitiveKind } from "../../../lib/primitives";
import type { InlineEditorContent } from "./types";
import { NoteEditor } from "./NoteEditor";
import { KbEditor } from "./KbEditor";
import { WorkflowEditor } from "./WorkflowEditor";
import { RecipeEditor } from "./RecipeEditor";

/** The eyebrow label shown in the editor header for each kind. */
export const EDITOR_LABELS: Record<PrimitiveKind, string> = {
  note: "Note",
  kb: "Knowledge",
  recipe: "Agent",
  workflow: "Workflow",
  decision: "Decision",
  meeting: "Meeting",
  artifact: "Artifact",
  chain: "Sequence",
  coder: "Coder",
  directory: "Zone",
  project: "Project",
  repository: "Repository",
  roadmap: "Roadmap",
  story: "Story",
  workbench: "Workbench",
  intelligence: "Intelligence",
  people: "People",
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
  game: null,
  layout: null,
} satisfies Record<PrimitiveKind, InlineEditorContent | null>;
