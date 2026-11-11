/* Parked: the live kit owns the Programs window grammar. */
/* Programs: the station track. It moved into the surface
 * (web/src/desk/surface/programTrack.tsx, 2026-10-31) so the thin kit and
 * the briefing page can carry it; this module keeps every desk import as it
 * was. A `StationView` (./model) is a `TrackStation`. */
import type { TrackStation } from "../surface/programTrack";
import type { ListMark } from "./types";

export { StationTrack, trackLabel, type TrackStation } from "../surface/programTrack";

const MARK_STATION: Record<ListMark["mark"], { state: TrackStation["state"]; tone: string; live?: boolean }> = {
  done: { state: "passed", tone: "ok" }, skipped: { state: "passed", tone: "idle" }, here: { state: "current", tone: "ask", live: true },
  running: { state: "ahead", tone: "info", live: true }, red: { state: "ahead", tone: "fail" },
  parked: { state: "ahead", tone: "idle" }, planned: { state: "ahead", tone: "idle" },
};

/** A Program's mini track (one dot per step), as the Programs list and the
 *  Room's Programs fold draw it. */
export function listStations(track: readonly ListMark[] | undefined): TrackStation[] {
  return (track ?? []).map((dot) => ({
    key: String(dot.ordinal), word: `${dot.ordinal} ${dot.title}`, mark: dot.mark, ...MARK_STATION[dot.mark],
  }));
}
