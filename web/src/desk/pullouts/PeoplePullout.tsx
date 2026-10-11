/** HS-151-07 — People pullout content.
 *
 * PHILO-17 (2b): a person icon opens THAT person, in their own window
 * (`pullout:people:<relationship id>`), on the People RelationshipPane; the
 * People drawer stays the roster. The People desk object itself (`people`)
 * is the roster application, never this window. */
import { lazy, Suspense, useState } from "react";
import { SurfaceFooter } from "../surface/SurfaceFooter";
import { SurfaceState } from "../surface/Surface";
import { takePersonLens } from "../objectWindows";
import type { PulloutContentProps } from "./types";

const PersonWindowBody = lazy(() =>
  import("../../pages/cores/PeopleCore").then((m) => ({ default: m.PersonWindowBody })),
);

export function PeoplePullout({ object: o, onClose }: PulloutContentProps) {
  // The lens a door asked for, taken once when the window opens.
  const [lens] = useState(() => takePersonLens(o.id));
  if (o.kind !== "people" || o.id === "people") {
    return (
      <>
        <SurfaceState empty emptyLabel="Not a person" emptyGlyph="?" />
        <SurfaceFooter />
      </>
    );
  }
  return (
    <Suspense fallback={<SurfaceState loading />}>
      <PersonWindowBody relationshipId={o.id} initialLens={lens} onClose={onClose} />
    </Suspense>
  );
}
