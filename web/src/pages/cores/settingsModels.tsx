// HS-156-04 — Settings → Models is the front door.
// When unconfigured: pack cards. When configured: health strip + advanced fold.
// The advanced fold contains the unchanged Model Library + Assignments.
import { FrontDoorView } from "./frontDoor";

export function ModelsModule({ onRefuse: _onRefuse }: { onRefuse(refusal: string): void }) {
  void _onRefuse;
  return <FrontDoorView />;
}
