/* Programs (canvas programs-2026-10-28, kit list "NEW StationTrack"): a
 * step's six stations, BRIEF · WORK · CHECK · REVIEW · PR · MERGE.
 *
 * `form="dots"` is the board row's track: six 8 px dots joined by 10 px
 * links, the current one 10 px in its tone (98 px in all). `form="words"`
 * is the Gate fold's track: each station a dot and its word, the quiet
 * word after it (`Check green`, `PR #1591`). Passed stations are filled
 * grey, ahead ones hollow, a station outside the step's gate (no reviewer)
 * is a short dash. A person's review draws her portrait in place of the
 * dot. The lit station breathes with the kit's live lamp (`kit-lamp-live`,
 * 2.4 s, a box-shadow; none under reduced motion); nothing moves on hover.
 * The track is one `ol` with the whole state as its accessible name. */
import { Avatar } from "../surface";
import type { StationView } from "./model";

export function trackLabel(stations: readonly StationView[]): string {
  const current = stations.find((station) => station.state === "current");
  return current ? `At ${current.word}${current.sub ? ` ${current.sub}` : ""}` : "Not started";
}

export function StationTrack({
  stations,
  form = "dots",
  label,
  "data-testid": testId,
}: {
  stations: readonly StationView[];
  form?: "dots" | "words";
  /** The accessible name; default the current station in words. */
  label?: string;
  "data-testid"?: string;
}) {
  return (
    <ol className="pg-track" data-form={form} aria-label={label ?? trackLabel(stations)} data-testid={testId}>
      {stations.map((station) => (
        <li
          key={station.key}
          className="pg-station"
          data-station={station.key}
          data-state={station.state}
          data-tone={station.tone}
          aria-current={station.state === "current" ? "step" : undefined}
        >
          {station.person ? (
            <span className="pg-station-person" title={station.person}><Avatar name={station.person} /></span>
          ) : (
            <span className="pg-station-dot" data-live={station.live ? "" : undefined} aria-hidden="true" />
          )}
          {form === "words" ? (
            <span className="pg-station-word">
              {station.word}
              {station.sub ? <span className="pg-station-sub"> {station.sub}</span> : null}
            </span>
          ) : null}
        </li>
      ))}
    </ol>
  );
}
