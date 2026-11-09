// HS-130-09 — the pre-persistence "new workbench" chooser.
//
// The old create gesture persisted a blank Workbench, opened it, and the
// window then showed a template picker whose Template/Blank exits EACH
// created ANOTHER record — orphaning the blank. Now the gesture opens this
// chooser BEFORE any record exists. Exactly one of the picker's exits
// persists exactly one Workbench, then this window closes. One gesture →
// one record, no orphan.
//
// Betterment A7: the picker offers the starters and Start from scratch;
// the window opens wide enough for the compact pictogram cards.
import { useDesk } from "../store";
import { DeskWindowFrame } from "./DeskWindow";
import { WorkbenchTemplatePicker } from "./WorkbenchTemplatePicker";

export function NewWorkbenchChooser() {
  const chooser = useDesk((s) => s.newWorkbenchChooser);
  const close = useDesk((s) => s.closeNewWorkbenchChooser);
  if (!chooser) return null;
  return (
    <DeskWindowFrame
      id="workbench:__new__"
      glyph="W"
      label="New Automation"
      title="New Automation"
      minW={320}
      minH={340}
      defaultW={720}
      defaultH={460}
      open
      origin={chooser.origin}
      onClose={close}
      className="desk-pullout desk-workbench-window"
    >
      <div className="desk-surface-body wb-body">
        <WorkbenchTemplatePicker onCreated={() => close()} />
      </div>
    </DeskWindowFrame>
  );
}
