import { SurfaceState } from "../surface";
import { SetupFace, useSetupInventory } from "./SetupFace";

/** First launch and HoldSpeak ▸ Setup use the same producer-backed face. */
export function FirstRun() {
  const setup = useSetupInventory();
  if (setup.loading && !setup.inventory) return <SurfaceState loading />;
  if (setup.error && !setup.inventory) {
    return <SurfaceState error={setup.error} onRetry={() => void setup.reload()} />;
  }
  if (!setup.inventory) {
    return <SurfaceState error="Setup could not be read. Your settings are unchanged. Try again." onRetry={() => void setup.reload()} />;
  }
  return <SetupFace initial={setup.inventory} />;
}
