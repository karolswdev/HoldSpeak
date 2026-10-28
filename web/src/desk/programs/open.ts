/* Programs: open a Program's window (`pullout:program:<id>`). */
import { useDesk } from "../store";

export function openProgram(id: string): void {
  useDesk.getState().openPullout(`program:${id}`);
}
