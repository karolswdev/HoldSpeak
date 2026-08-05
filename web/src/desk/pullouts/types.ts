/** Pullout content component contract (HS-117-15). */
import type { WorldObject } from "../world";

export interface PulloutContentProps {
  object: WorldObject;
  onClose: () => void;
}

/** A pullout content component — renders body + footer inside DeskWindowFrame. */
export type PulloutContent = React.FC<PulloutContentProps>;
