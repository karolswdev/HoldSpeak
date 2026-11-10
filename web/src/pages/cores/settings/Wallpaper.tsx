import { useState } from "react";
import { ATMOSPHERES } from "../../../desk/gl/atmosphereRegistry";
import { useAtmospherePreference } from "../../../desk/gl/atmospherePreference";
import { useAtmosphereControls } from "../../../desk/gl/atmosphereControls";
import { useAtmosphereFavorites } from "../../../desk/gl/atmosphereFavorites";
import { PaneGroup, GadgetGroup, GadgetRow, CheckGadget, ListView, type ListVerb } from "../../../desk/surface";

function sentenceCase(value: string): string {
  const sentence = value[0].toLocaleUpperCase() + value.slice(1).toLocaleLowerCase();
  return sentence.replace(/\b(jupiter|mars|saturn)\b/gi, (planet) => planet[0].toLocaleUpperCase() + planet.slice(1));
}
export function WallpaperModule({
  showFavorites = false,
  favoritesOnly = false,
  highlight,
}: {
  showFavorites?: boolean;
  favoritesOnly?: boolean;
  highlight?: string | null;
} = {}) {
  const [selectedId, select] = useAtmospherePreference();
  const [picked, pick] = useState<string | null>(selectedId);
  const { motion, setMotion } = useAtmosphereControls();
  const { favorites, toggle } = useAtmosphereFavorites();
  const choices = favoritesOnly ? ATMOSPHERES.filter((entry) => favorites.includes(entry.id)) : ATMOSPHERES;
  const verbs: ListVerb[] = [
    {
      id: "choose",
      label: "Use wallpaper",
      key: "Enter",
      enabled: (row) => Boolean(row),
      run: (row) => select(row!.id),
    },
    ...(showFavorites
      ? [
          {
            id: "favorite",
            label: "Change favorite",
            enabled: (row) => Boolean(row),
            run: (row) => toggle(row!.id),
          } satisfies ListVerb,
        ]
      : []),
  ];
  return (
    <>
      <PaneGroup label="Wallpaper">
        <ListView
          label="Desk wallpaper"
          rows={choices.map((entry) => ({
            id: entry.id,
            kind: "wallpaper",
            name: sentenceCase(entry.name),
            sprite: entry.previewUrl || undefined,
            cells: {
              favorite: favorites.includes(entry.id) ? "Favorite" : "",
              use: entry.id === selectedId ? "In use" : "",
            },
          }))}
          columns={[
            { key: "name", word: "Place", priority: 100, track: "minmax(0, 2fr)" },
            { key: "favorite", word: "Favorite", priority: 20, track: "minmax(0, 1fr)" },
            { key: "use", word: "State", priority: 20, track: "minmax(0, 1fr)" },
          ]}
          selectedId={picked}
          onSelect={pick}
          verbs={verbs}
          defaultVerb="choose"
        />
      </PaneGroup>
      <GadgetGroup>
        <GadgetRow label="Motion" highlight={highlight === "motion"}>
          <CheckGadget label="Wallpaper motion" checked={motion} onChange={setMotion} variant="state" />
        </GadgetRow>
      </GadgetGroup>
    </>
  );
}
