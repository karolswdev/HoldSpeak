import { useState } from "react";
import { Button } from "../../components/signal/Signal";
import { SurfaceVerbs } from "../../desk/surface/Surface";
import { useDesk } from "../../desk/store";
import { useSettleState } from "../../desk/settleState";
import { useAtmospherePreference } from "../../desk/gl/atmospherePreference";
import { resolveAtmosphere } from "../../desk/gl/atmosphereRegistry";
import { WallpaperModule } from "./settingsWallpaper";
import type { CoreProps } from "./core-types";

/** One native window over the same browser-local picker used by Settings. */
export function ChangePlacesCore(_props: CoreProps) {
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const [id] = useAtmospherePreference();
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
        <Button
          type="button"
          dense
          onClick={() => {
            useDesk.getState().closeSurfaceWindow("change-places");
            useSettleState.getState().setSettled(true);
          }}
        >
          {/* HS-201-06: "Settle in" was an idiom; the verb hides the
              navigation chrome (Constitution tenet 4, ASD-STE100). */}
          Hide the menus
        </Button>
      </SurfaceVerbs>
      <WallpaperModule showFavorites favoritesOnly={favoritesOnly} />
    </>
  );
}
