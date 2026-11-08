/* Programs (design §9b, "Where it lives: the Project"): a Project's
 * Programs. One row per Program, worst first: the program sprite, the
 * title, its state word and the step dots the Programs window draws
 * (`listStations`, the same track). A press on the row opens the Program
 * window. `RoomProgramRows` is the list; the Project Room puts it in its
 * own Programs fold, the drawer in `RoomPrograms`. */
import { FoldGadget, ListRow, ListView } from "../surface";
import { spriteUrl } from "../sprites";
import { programTone } from "./model";
import { openProgram } from "./open";
import { StationTrack, listStations } from "./StationTrack";
import type { ListMark } from "./types";
import "./programs.css";

export interface RoomProgram {
  id: string;
  title: string;
  state: string;
  state_word: string;
  done: number;
  total: number;
  your_turn: number;
  track?: ListMark[];
}

export function RoomProgramRows({ programs }: { programs: readonly RoomProgram[] }) {
  return (
    <ListView label="Programs" data-testid="room-programs" className="pg-room-rows">
      <ul className="kit-listrows">
        {programs.map((row) => {
          const stations = listStations(row.track);
          return (
            <ListRow key={row.id} data-testid="room-program-row" openTestId="room-program-open" openLabel={`Open ${row.title}`}
              glyph={spriteUrl("program", row.id, "rest", null, 20)} name={row.title} onOpen={() => openProgram(row.id)}
              state={{ word: row.state_word, tone: programTone(row.state), live: row.state === "waiting" || row.state === "running",
                testId: "room-program-state" }}
              age={stations.length
                ? <StationTrack stations={stations} label={`${row.done} of ${row.total} done`} data-testid="room-program-track" />
                : undefined} />
          );
        })}
      </ul>
    </ListView>
  );
}

/** The drawer's Programs fold: nothing when the Project has no Program. */
export function RoomPrograms({ programs }: { programs: readonly RoomProgram[] }) {
  if (!programs.length) return null;
  return (
    <FoldGadget className="pg-room" title="Programs" token={String(programs.length)} open>
      <RoomProgramRows programs={programs} />
    </FoldGadget>
  );
}
