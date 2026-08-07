/** Inline editor content component contract (HS-117-15). */
import type { WorldObject } from "../../world";

export interface InlineEditorContentProps {
  object: WorldObject;
  onClose: () => void;
}

/** An inline editor content component — renders form fields + footer
 * inside the positioned editor container. */
export type InlineEditorContent = React.FC<InlineEditorContentProps>;
