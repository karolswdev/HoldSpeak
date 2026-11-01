/* Programs (canvas programs-2026-10-28, kit list "NEW StationTrack"): a
 * track of stations: a step's six (BRIEF · WORK · CHECK · REVIEW · PR ·
 * MERGE), or, on the briefing page (2026-10-31), a program's steps with
 * this step lit and the steps that wait on it marked.
 *
 * `form="dots"` is the board row's track: six 8 px dots joined by 10 px
 * links, the current one 10 px in its tone (98 px in all). `form="words"`
 * is the Gate fold's track: each station a dot and its word, the quiet
 * word after it (`Check green`, `PR #1591`). Passed stations are filled
 * grey, ahead ones hollow, a station outside the step's gate (no reviewer)
 * is a short dash. A person's review draws her portrait in place of the
 * dot. The lit station breathes with the kit's live lamp (`kit-lamp-live`,
 * 2.4 s, a box-shadow; none under reduced motion); nothing moves on hover.
 * A station with a `mark` carries it as `data-mark` (the page's "blocked").
 * A `note` is a second quiet line (the Program window's line, PG-WINDOW).
 * The track is one `ol` with the whole state as its accessible name.
 *
 * It lives in the surface so the thin kit (./thin.ts) can carry it: it
 * reaches neither the desk's auth client nor the microphone.
 * web/src/desk/programs/StationTrack.tsx re-exports it unchanged. */
import { Avatar } from "./kit";

export type TrackStation = {
  key: string;
  word: string;
  /** The quiet word after it (`green`, `passed`, `#1591`, `log`). */
  sub?: string;
  state: "passed" | "current" | "ahead" | "skip";
  tone: string;
  /** The current station breathes. */
  live?: boolean;
  /** A person's review: her name (the station draws her portrait). */
  person?: string;
  /** A mark the face styles (`blocked`: a step that waits on the lit one). */
  mark?: string;
  /** PG-WINDOW: a second quiet line under the word (the Program window's
   *  line: `PR #1601 merged`, `Waits on you`). Words form only. */
  note?: string;
};

export function trackLabel(stations: readonly TrackStation[]): string {
  const current = stations.find((station) => station.state === "current");
  return current ? `At ${current.word}${current.sub ? ` ${current.sub}` : ""}` : "Not started";
}

export function StationTrack({
  stations,
  form = "dots",
  label,
  "data-testid": testId,
}: {
  stations: readonly TrackStation[];
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
          data-mark={station.mark || undefined}
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
          {form === "words" && station.note ? <span className="pg-station-note">{station.note}</span> : null}
        </li>
      ))}
    </ol>
  );
}
