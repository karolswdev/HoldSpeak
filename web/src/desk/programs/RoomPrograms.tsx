/* Programs (design §9b, "Where it lives: the Project"): the Room's
 * Programs fold, in the Project drawer. One row per Program, worst first:
 * the program sprite, the title, its StateChip, "4 of 6", the your-turn
 * DotWord only when it is not zero, and Open (the Program window). Nothing
 * when the Project has no Program. */
import { Button } from "../../components/signal/Signal";
import { DotWord, FoldGadget, ListView, StateChip } from "../surface";
import { spriteUrl } from "../sprites";
import { programChip } from "./model";
import { openProgram } from "./open";
import "./programs.css";

export interface RoomProgram {
  id: string;
  title: string;
  state: string;
  state_word: string;
  done: number;
  total: number;
  your_turn: number;
}

export function RoomPrograms({ programs }: { programs: readonly RoomProgram[] }) {
  if (!programs.length) return null;
  return (
    <FoldGadget className="pg-room" title="Programs" token={String(programs.length)} open>
      <ListView label="Programs" data-testid="room-programs">
        <ul className="kit-listrows">
          {programs.map((row) => (
            <li key={row.id} className="kit-listrow pg-room-row" data-state={row.state} data-testid="room-program-row">
              <span className="kit-listrow-main">
                <img className="kit-listrow-glyph" src={spriteUrl("program", row.id, "rest", null, 20)} alt="" width={20} height={20} />
                <span className="kit-listrow-name">{row.title}</span>
              </span>
              <StateChip state={programChip(row.state)} label={row.state_word} />
              <span className="kit-listrow-age">{row.total ? `${row.done} of ${row.total}` : ""}</span>
              {row.your_turn ? <DotWord tone="ask">{`${row.your_turn} ${row.your_turn === 1 ? "waits" : "wait"} on you`}</DotWord> : null}
              <span className="kit-listrow-verbs">
                <Button dense variant="secondary" onClick={() => openProgram(row.id)} aria-label={`Open ${row.title}`}
                  data-testid="room-program-open">Open program</Button>
              </span>
            </li>
          ))}
        </ul>
      </ListView>
    </FoldGadget>
  );
}
