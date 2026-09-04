import { ATMOSPHERES } from "../../desk/gl/atmosphereRegistry";
import { useAtmospherePreference } from "../../desk/gl/atmospherePreference";
import { GadgetGroup } from "../../desk/surface/gadgets";

export function WallpaperModule() {
  const [selectedId, select] = useAtmospherePreference();

  return (
    <GadgetGroup label="Wallpaper">
      <div
        className="prefs-wallpaper-grid"
        role="radiogroup"
        aria-label="Desk wallpaper"
      >
        {ATMOSPHERES.map((atmosphere) => {
          const selected = atmosphere.id === selectedId;
          return (
            <button
              key={atmosphere.id}
              type="button"
              role="radio"
              aria-checked={selected}
              className="prefs-wallpaper-card"
              data-selected={selected || undefined}
              onClick={() => select(atmosphere.id)}
            >
              <span className="prefs-wallpaper-preview" aria-hidden="true">
                {atmosphere.previewUrl ? (
                  <img src={atmosphere.previewUrl} alt="" />
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
          );
        })}
      </div>
      <p className="prefs-wallpaper-fact">
        SAVED ON THIS BROWSER · APPLIES LIVE TO THE FLOOR
      </p>
    </GadgetGroup>
  );
}
