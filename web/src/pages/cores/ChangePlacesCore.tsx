import { useState } from "react";
import { Button } from "../../components/signal/Signal";
import { SurfaceVerbs } from "../../desk/surface/Surface";
import { useDesk } from "../../desk/store";
import { useChairState } from "../../desk/chairState";
import { useSettleState } from "../../desk/settleState";
import { useAtmospherePreference } from "../../desk/gl/atmospherePreference";
import { resolveAtmosphere } from "../../desk/gl/atmosphereRegistry";
import { WallpaperModule } from "./settingsWallpaper";
import type { CoreProps } from "./core-types";

/** One native window over the same browser-local picker used by Settings. */
export function ChangePlacesCore(_props: CoreProps) {
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const [id] = useAtmospherePreference();
  const surface = useChairState((s) => s.surface);
  return (
    <>
      <SurfaceVerbs status={resolveAtmosphere(id).name}>
        <Button
          type="button"
          dense
          variant="ghost"
          aria-pressed={!favoritesOnly}
          onClick={() => setFavoritesOnly(false)}
        >
          All places
        </Button>
        <Button
          type="button"
          dense
          variant="ghost"
          aria-pressed={favoritesOnly}
          onClick={() => setFavoritesOnly(true)}
        >
          Favorites
        </Button>
        {surface !== "floor" && (
          <Button
            type="button"
            dense
            onClick={() => useChairState.getState().setSurface("floor")}
          >
            View on Floor
          </Button>
        )}
        <Button
          type="button"
          dense
          onClick={() => {
            useDesk.getState().closeSurfaceWindow("change-places");
            useSettleState.getState().setSettled(true);
          }}
        >
          Settle in
        </Button>
      </SurfaceVerbs>
      <WallpaperModule showFavorites favoritesOnly={favoritesOnly} />
    </>
  );
}
