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

/** Today's Since this morning line (design §9 Seams, "Today"): `Programs:
 *  1 running, 1 waits on you`, when any Program moved today; else "". */
export function programsTodayLine(programs: readonly { state: string; updated_at: string }[], now: Date): string {
  const day = (value: Date) => `${value.getFullYear()}-${value.getMonth()}-${value.getDate()}`;
  const moved = programs.filter((row) => {
    const at = new Date(row.updated_at);
    return Number.isFinite(at.getTime()) && day(at) === day(now);
  });
  if (!moved.length) return "";
  const running = moved.filter((row) => row.state === "running").length;
  const waiting = moved.filter((row) => row.state === "waiting" || row.state === "failed").length;
  const done = moved.filter((row) => row.state === "done").length;
  const parts = [
    running ? `${running} running` : "",
    waiting ? `${waiting} ${waiting === 1 ? "waits" : "wait"} on you` : "",
    done ? `${done} done` : "",
  ].filter(Boolean);
  return parts.length ? `Programs: ${parts.join(", ")}` : "";
}

/** The Programs that moved today, read once (and on a Program frame). */
export function useProgramsToday(now: Date): string {
  const [rows, setRows] = useState<{ state: string; updated_at: string }[]>([]);
  const alive = useRef(true);
  useEffect(() => () => { alive.current = false; }, []);
  const load = useCallback(() => {
    void readPrograms()
      .then((list) => { if (alive.current) setRows(list.programs); })
      .catch(() => undefined);
  }, []);
  useEffect(() => { load(); }, [load]);
  useProgramFrames(() => load());
  return programsTodayLine(rows, now);
}
