// A Vite-only review surface for the real scenes. No hub or seeded work data.
import { useEffect, useRef, useState } from "react";
import { Atmosphere } from "../desk/gl/Atmosphere";
import {
  SCENIC_ATMOSPHERES,
  type AtmosphereId,
} from "../desk/gl/atmosphereRegistry";
import { useAtmosphereControls } from "../desk/gl/atmosphereControls";
import { useAtmospherePreference } from "../desk/gl/atmospherePreference";
import "../styles/tokens.css";
import "../styles/global.css";
import "../desk/desk.css";
import "./atmosphere-preview.css";

const collection = SCENIC_ATMOSPHERES;

export function AtmospherePreview() {
  const [id, setId] = useState<AtmosphereId>(() => {
    const requested = location.hash.slice(1);
    return (collection.find((entry) => entry.id === requested) ?? collection[0])
      .id;
  });
  const [savedId, select] = useAtmospherePreference();
  const controls = useAtmosphereControls();
  const definition = collection.find((entry) => entry.id === id)!;
  const position = collection.findIndex((entry) => entry.id === id);
  const strip = useRef<HTMLElement>(null);
  useEffect(() => {
    strip.current?.querySelector('[aria-pressed="true"]')?.scrollIntoView?.({
      block: "nearest",
      inline: "nearest",
    });
  }, [id]);
  const change = (next: AtmosphereId) => {
    setId(next);
    history.replaceState(null, "", `#${next}`);
  };
  const step = (direction: number) =>
    change(
      collection[(position + direction + collection.length) % collection.length]
        .id,
    );
  return (
    <main className="desk-next atmosphere-preview">
      <Atmosphere id={id} />
      <header className="atmosphere-preview-head">
        <a href="/_built/" className="atmosphere-preview-brand">
          HoldSpeak <span>/ Places to think</span>
        </a>
        <div className="atmosphere-preview-controls">
          <button
            type="button"
            aria-pressed={controls.motion}
            onClick={() => controls.setMotion(!controls.motion)}
          >
            {controls.motion ? "Pause motion" : "Play motion"}
          </button>
          <button
            type="button"
            aria-pressed={controls.sound}
            onClick={() => controls.setSound(!controls.sound)}
          >
            {controls.sound ? "Sound on" : "Sound off"}
          </button>
        </div>
      </header>
      <footer className="atmosphere-preview-foot">
        <div className="atmosphere-preview-description" aria-live="polite">
          <p className="atmosphere-preview-kicker">
            THE NIGHT COLLECTION{" "}
            <span>
              {String(position + 1).padStart(2, "0")} /{" "}
              {String(collection.length).padStart(2, "0")}
            </span>
          </p>
          <h1>{definition.name}</h1>
          <p>{definition.description}</p>
        </div>
        <div className="atmosphere-preview-actions">
          <button
            type="button"
            aria-label="Previous environment"
            onClick={() => step(-1)}
          >
            ←
          </button>
          <button
            type="button"
            aria-label="Next environment"
            onClick={() => step(1)}
          >
            →
          </button>
          <button
            type="button"
            onClick={() => select(id)}
            disabled={savedId === id}
          >
            {savedId === id ? "Selected for your Floor" : "Use on my Floor"}
          </button>
        </div>
        <nav
          ref={strip}
          aria-label="Environment previews"
          className="atmosphere-preview-strip"
        >
          {collection.map((entry, index) => (
            <button
              type="button"
              key={entry.id}
              data-scene={entry.id}
              aria-pressed={id === entry.id}
              onClick={() => change(entry.id)}
            >
              <img src={entry.previewUrl!} alt="" />
              <span>
                <small>{String(index + 1).padStart(2, "0")}</small>
                {entry.name}
              </span>
            </button>
          ))}
        </nav>
      </footer>
    </main>
  );
}
