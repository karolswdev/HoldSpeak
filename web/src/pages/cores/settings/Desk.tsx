// Settings > Desk: sounds and presence. Moved out of SettingsCore.tsx.
import { CheckGadget, GadgetGroup, GadgetRow } from "../../../desk/surface/gadgets";
import { SurfaceColumns } from "../../../desk/surface";
import { toggleSfx } from "../../../lib/sfx";
import { TtsSettingsBlock } from "../settingsTts";
import { WallpaperModule } from "../settingsWallpaper";
import { RecordingsSettings } from "../../../desk/recordings/RecordingsSettings";
import type { SettingsBindings } from "./bindings";

/* ── Sounds & Presence: desk sounds + presence + mascot ── */
function SoundsModule({ b }: { b: SettingsBindings }) {
  const { update, val, hl, check } = b;
        return (
          <SurfaceColumns variant="preferences" main={<>
              <GadgetGroup material="inset" label="Sounds">
                <GadgetRow
                  label="Desk sounds"
                  highlight={hl(["ui", "desk_sounds"])}
                  controlWidth="short"
                >
                  <CheckGadget
                    variant="state"
                    label="Desk sounds"
                    checked={Boolean(val(["ui", "desk_sounds"]) ?? true)}
                    onChange={(next) => {
                      update(["ui", "desk_sounds"], next);
                      toggleSfx(next);
                    }}
                  />
                </GadgetRow>
              </GadgetGroup>
              <GadgetGroup material="inset" label="Presence">
                {check(["presence", "enabled"], "Presence")}
                {check(["presence", "mascot"], "Mascot")}
              </GadgetGroup>
          </>} side={<TtsSettingsBlock />} />
        );
}

export function DeskSection({ b, focusHighlight }: { b: SettingsBindings; focusHighlight: string }) {
  return <>
    <SoundsModule b={b} />
    <WallpaperModule showFavorites highlight={focusHighlight} />
    <RecordingsSettings />
  </>;
}
