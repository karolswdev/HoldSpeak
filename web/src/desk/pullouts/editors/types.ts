/** Inline editor content component contract (HS-117-15). */
import type { WorldObject } from "../../world";
import type { PublishEditorWriter } from "./useDebouncedSave";

export interface InlineEditorContentProps {
  object: WorldObject;
  onClose: () => void;
  /** Publish this mounted editor's save authority to its local host. */
  onWriter?: PublishEditorWriter;
  /** True when the editor opened as part of a creation gesture — the name
   * field should receive focus so the user can name the thing immediately. */
  autoFocusName?: boolean;
  /** W2-BUILDER: the reader's Add opened the editor; a Knowledge editor
   *  opens on its item picker. */
  openAdd?: boolean;
  /** W3-B: the host's verbs (Done; Retry after a refusal) for an editor
   *  that draws its own toolbar (Knowledge). */
  toolbar?: React.ReactNode;
}

/** An inline editor content component — renders form fields + footer
 * inside the positioned editor container. */
export type InlineEditorContent = React.FC<InlineEditorContentProps>;
