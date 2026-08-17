/** Inline editor content component contract (HS-117-15). */
import type { WorldObject } from "../../world";

export interface InlineEditorContentProps {
  object: WorldObject;
  onClose: () => void;
  /** True when the editor opened as part of a creation gesture — the name
   * field should receive focus so the user can name the thing immediately. */
  autoFocusName?: boolean;
}

/** An inline editor content component — renders form fields + footer
 * inside the positioned editor container. */
export type InlineEditorContent = React.FC<InlineEditorContentProps>;
