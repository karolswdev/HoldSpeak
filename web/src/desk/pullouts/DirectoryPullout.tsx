/** Directory (Zone) pullout content (HS-117-15).
 * Directories open as pullouts but have no custom body today. */
import type { PulloutContentProps } from "./types";

export function DirectoryPullout({ object: o }: PulloutContentProps) {
  return (
    <>
      <div className="desk-pullout-body desk-surface-body" />
      <footer className="desk-pullout-foot" />
    </>
  );
}
