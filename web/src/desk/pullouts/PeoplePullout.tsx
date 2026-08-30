/** HS-150-07 — People pullout content.
 * Shows thread TITLES only — People content never leaves the encrypted store.
 * The "Threads" section lists threads whose thread_refs name this person. */
import { SurfaceFooter } from "../surface/SurfaceFooter";
import { SurfaceState } from "../surface/Surface";
import { ThreadsSection } from "./shared/ThreadsSection";
import type { PulloutContentProps } from "./types";

export function PeoplePullout({ object: o }: PulloutContentProps) {
  if (o.ref.kind !== "people") {
    return (
      <>
        <div className="desk-pullout-body desk-surface-body">
          <SurfaceState empty emptyLabel="Not a person" emptyGlyph="?" />
        </div>
        <SurfaceFooter />
      </>
    );
  }

  return (
    <>
      <div className="desk-pullout-body desk-surface-body">
        <ThreadsSection refId={o.id} />
      </div>
      <SurfaceFooter />
    </>
  );
}
