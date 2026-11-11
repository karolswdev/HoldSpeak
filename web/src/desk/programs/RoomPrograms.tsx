import { useState } from "react";
import { FoldGadget, ListView } from "../surface";
import { openProgram } from "./open";
import { programRow } from "./liveModel";
import type { ListMark } from "./types";
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

export function RoomProgramRows({
  programs,
}: {
  programs: readonly RoomProgram[];
}) {
  const [picked, setPicked] = useState<string | null>(null);
  return (
    <ListView
      label="Programs"
      data-testid="room-programs"
      headerless
      rows={programs.map((row) =>
        programRow({ ...row, state: row.state as "running" }),
      )}
      columns={[{ key: "name", word: "Program" }]}
      selectedId={picked}
      onSelect={setPicked}
      onOpen={openProgram}
      verbs={[
        {
          id: "open",
          label: "Open program",
          run: (row) => {
            if (row) openProgram(row.id);
          },
        },
      ]}
    />
  );
}
export function RoomPrograms({
  programs,
}: {
  programs: readonly RoomProgram[];
}) {
  return programs.length ? (
    <FoldGadget title="Programs" open>
      <RoomProgramRows programs={programs} />
    </FoldGadget>
  ) : null;
}
