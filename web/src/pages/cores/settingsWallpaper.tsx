import { ATMOSPHERES } from "../../desk/gl/atmosphereRegistry";
import { useAtmospherePreference } from "../../desk/gl/atmospherePreference";
import {
  GadgetGroup,
  GadgetRow,
  CheckGadget,
} from "../../desk/surface/gadgets";
import { useAtmosphereControls } from "../../desk/gl/atmosphereControls";
import { useAtmosphereFavorites } from "../../desk/gl/atmosphereFavorites";

export function WallpaperModule({
  showFavorites = false,
  favoritesOnly = false,
}: { showFavorites?: boolean; favoritesOnly?: boolean } = {}) {
  const [selectedId, select] = useAtmospherePreference();
  const controls = useAtmosphereControls();
  const { favorites, toggle } = useAtmosphereFavorites();
  const choices = favoritesOnly
    ? ATMOSPHERES.filter((entry) => favorites.includes(entry.id))
    : ATMOSPHERES;
  const tabId = choices.some((entry) => entry.id === selectedId)
    ? selectedId
    : choices[0]?.id;

  return (
    <GadgetGroup label="Environments">
      <div
        className="prefs-wallpaper-grid"
        role="radiogroup"
        aria-label="Desk wallpaper"
        tabIndex={-1}
      >
        {choices.length === 0 && (
          <p className="quiet" role="status">
            No favorite places
          </p>
        )}
        {choices.map((atmosphere) => {
          const selected = atmosphere.id === selectedId;
          return (
            <div key={atmosphere.id} className="prefs-wallpaper-choice">
              <button
                type="button"
                role="radio"
                data-atmosphere-choice={atmosphere.id}
                aria-checked={selected}
                tabIndex={atmosphere.id === tabId ? 0 : -1}
                className="prefs-wallpaper-card"
                data-selected={selected || undefined}
                onClick={() => select(atmosphere.id)}
                onKeyDown={(event) => {
                  const index = choices.findIndex(
                    (entry) => entry.id === atmosphere.id,
                  );
                  let next = index;
                  if (event.key === "ArrowRight" || event.key === "ArrowDown")
                    next = (index + 1) % choices.length;
                  else if (event.key === "ArrowLeft" || event.key === "ArrowUp")
                    next = (index - 1 + choices.length) % choices.length;
                  else if (event.key === "Home") next = 0;
                  else if (event.key === "End") next = choices.length - 1;
                  else return;
                  event.preventDefault();
                  select(choices[next].id);
                  event.currentTarget
                    .closest('[role="radiogroup"]')
                    ?.querySelectorAll<HTMLButtonElement>('[role="radio"]')
                    [next]?.focus();
                }}
              >
                <span className="prefs-wallpaper-preview" aria-hidden="true">
                  {atmosphere.previewUrl ? (
                    <img src={atmosphere.previewUrl} alt="" loading="lazy" />
                  ) : (
                    <span className="prefs-wallpaper-preview-quiet">
                      <span />
                      <span />
                      <span />
                    </span>
                  )}
                </span>
                <span className="prefs-wallpaper-copy">
                  <strong>{atmosphere.name}</strong>
                  <span>{atmosphere.description}</span>
                </span>
                <span className="prefs-wallpaper-state">
                  {selected ? "IN USE" : "CHOOSE"}
                </span>
              </button>
              {showFavorites && (
                <button
                  type="button"
                  className="prefs-wallpaper-favorite"
                  aria-label={`Favorite ${atmosphere.name}`}
                  aria-pressed={favorites.includes(atmosphere.id)}
                  onClick={(event) => {
                    if (favoritesOnly) {
                      // Removing a filtered card must not strand keyboard
                      // focus on the body, including the last favorite.
                      const group = event.currentTarget.closest<HTMLElement>(
                        '[role="radiogroup"]',
                      );
                      const next = Array.from(
                        group?.querySelectorAll<HTMLButtonElement>(
                          '[role="radio"]',
                        ) ?? [],
                      ).find(
                        (radio) =>
                          radio.dataset.atmosphereChoice !== atmosphere.id,
                      );
                      (next ?? group)?.focus({ preventScroll: true });
                    }
                    toggle(atmosphere.id);
                  }}
                >
                  <span aria-hidden="true">
                    {favorites.includes(atmosphere.id) ? "★" : "☆"}
                  </span>
                </button>
              )}
            </div>
          );
        })}
      </div>
      <GadgetRow label="Animation" fact="RESPECTS REDUCED MOTION">
        <CheckGadget
          label="Environment animation"
          checked={controls.motion}
          onChange={controls.setMotion}
        />
      </GadgetRow>
      <GadgetRow label="Room sound" fact="QUIET DURING CAPTURE">
        <CheckGadget
          label="Environment sound"
          checked={controls.sound}
          onChange={controls.setSound}
        />
      </GadgetRow>
      <p className="prefs-wallpaper-fact">
        SAVED ON THIS BROWSER · APPLIES LIVE TO THE FLOOR
      </p>
    </GadgetGroup>
  );
}
