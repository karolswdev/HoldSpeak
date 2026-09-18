/** ProjectButton (HS-200-15, species S6 of the daily-workflow design) —
 *  the way back to the originating Project, on every posture (story 09
 *  AC2; design D1 "the way back is on every posture").
 *
 *  A library `Button` (ghost, dense, caption step) inside a
 *  `role="group"` region named `Project` (canon D), accessible name
 *  `Open the Project: <name>`. It is a READ (it opens the Room); a write
 *  is never named as a way back.
 *
 *  Two rules the species enforces:
 *
 *  - **Withheld when the desk holds one Project** — the caller passes
 *    `withheld` and the species renders nothing: repeating one word on
 *    every row says nothing (UX-CANON A.7).
 *  - **Never a decorative token.** Before this species the arrival drew the
 *    Project name as inert text; a name the owner can read but not follow
 *    is a verb that does nothing (A.11).
 */
import { Button } from "../../../components/signal/Signal";
import "./project-button.css";

export interface ProjectButtonProps {
  name: string;
  onOpen: () => void;
  /** True when the desk holds exactly one Project: draw nothing. */
  withheld?: boolean;
  className?: string;
  "data-testid"?: string;
}

export function ProjectButton({
  name,
  onOpen,
  withheld = false,
  className,
  "data-testid": dataTestId = "project-button",
}: ProjectButtonProps) {
  const label = name.trim();
  if (withheld || !label) return null;
  return (
    <span
      role="group"
      aria-label="Project"
      className={className ? `surface-project-group ${className}` : "surface-project-group"}
    >
      <Button
        variant="ghost"
        dense
        className="surface-project-button"
        aria-label={`Open the Project: ${label}`}
        onClick={onOpen}
        data-testid={dataTestId}
      >
        {label.toUpperCase()}
      </Button>
    </span>
  );
}
