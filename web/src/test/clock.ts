// The desk has one clock format and it follows the system (owner decision
// 2026-11-13). A test that expects a clock reads the formatter, so it holds
// on a 12-hour machine and on a 24-hour machine.
import { clockOf } from "../desk/surface/format";

/** The desk's clock for a local wall time: `at(21, 6)` is `21:06` or
 *  `9:06 PM`; with seconds, `at(21, 6, 9)`. */
export function at(hours: number, minutes: number, seconds?: number): string {
  return clockOf(new Date(2026, 0, 1, hours, minutes, seconds ?? 0), seconds !== undefined);
}

/** The desk's clock for an instant (an ISO string, epoch ms or a Date). */
export function clockAt(value: string | number | Date): string {
  return clockOf(new Date(value));
}

/** The shape of the desk's clock as the source of a regular expression. */
export const CLOCK = / [AP]M$/.test(at(23, 59)) ? String.raw`\d{1,2}:\d\d [AP]M` : String.raw`\d\d:\d\d`;
