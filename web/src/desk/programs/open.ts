import { keepPlace } from "../deskMemory";
import { useDesk } from "../store";
export function openProgram(id: string): void {
  keepPlace("programs/picked", id);
  useDesk.getState().openSurfaceWindow("open-programs", `program:${id}`);
}
