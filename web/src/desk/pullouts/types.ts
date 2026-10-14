/** Pullout content component contract (HS-117-15). */
import type { WorldObject } from "../world";

export type RegisterCloseGuard = (guard: () => Promise<boolean>) => () => void;

export interface PulloutContentProps {
  object: WorldObject;
  onClose: () => void;
  /** A mounted editor can defer its own frame close until its write lands. */
  registerClose?: RegisterCloseGuard;
}

/** A pullout content component — renders body + footer inside DeskWindowFrame. */
export type PulloutContent = React.FC<PulloutContentProps>;
