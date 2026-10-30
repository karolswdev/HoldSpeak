/* Programs (design §9 Seams, "Dock"): the Agents lamp takes the worst
 * Program state too. One read of `/api/programs` (the list's `worst`) on
 * mount and on each Program frame; a hub without Programs reads nothing. */
import { useCallback, useEffect, useRef, useState } from "react";
import { readPrograms, useProgramFrames } from "./api";
import type { ProgramState } from "./types";

export type FleetLamp = "ask" | "new" | "work" | null;

export interface ProgramsLamp {
  lamp: FleetLamp;
  /** `1 program waits on you`, `2 programs running`, or "". */
  words: string;
}

export function programsLampOf(worst: ProgramState | null, counts: Partial<Record<ProgramState, number>>): ProgramsLamp {
  if (worst === "waiting" || worst === "failed") {
    const n = (counts.waiting ?? 0) + (counts.failed ?? 0);
    return { lamp: "ask", words: `${n} ${n === 1 ? "program waits" : "programs wait"} on you` };
  }
  if (worst === "running") {
    const n = counts.running ?? 0;
    return { lamp: "work", words: `${n} ${n === 1 ? "program" : "programs"} running` };
  }
  return { lamp: null, words: "" };
}

/** The worse of two lamps (ask over new over work). */
export function worseLamp(a: FleetLamp, b: FleetLamp): FleetLamp {
  const rank = (lamp: FleetLamp) => (lamp === "ask" ? 3 : lamp === "new" ? 2 : lamp === "work" ? 1 : 0);
  return rank(a) >= rank(b) ? a : b;
}

export function useProgramsLamp(): ProgramsLamp {
  const [lamp, setLamp] = useState<ProgramsLamp>({ lamp: null, words: "" });
  const alive = useRef(true);
  useEffect(() => () => { alive.current = false; }, []);
  const load = useCallback(() => {
    void readPrograms()
      .then((list) => { if (alive.current) setLamp(programsLampOf(list.worst, list.counts ?? {})); })
      .catch(() => undefined);
  }, []);
  useEffect(() => { load(); }, [load]);
  useProgramFrames(() => load());
  return lamp;
}

/** Today's Programs line (design §9 Seams, "Today"; PG18): the hub's
 *  `programs` block of `GET /api/today/since-morning`
 *  (`ProgramService.since_morning`) as `Programs: 1 running, 1 waits on you`;
 *  "" when no Program moved today or the block could not be read. */
export interface ProgramsSinceMorning { moved: number; running: number; waiting: number; done: number; merged: number }

export function programsTodayLine(block: ProgramsSinceMorning | null | undefined): string {
  if (!block || !block.moved) return "";
  const parts = [
    block.running ? `${block.running} running` : "",
    block.waiting ? `${block.waiting} ${block.waiting === 1 ? "waits" : "wait"} on you` : "",
    block.done ? `${block.done} done` : "",
    block.merged ? `${block.merged} ${block.merged === 1 ? "PR" : "PRs"} merged` : "",
  ].filter(Boolean);
  return parts.length ? `Programs: ${parts.join(", ")}` : "";
}
