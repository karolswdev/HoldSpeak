// PHILO-14 canvas seats: [product file (suffix), import line or null, [[anchor, replacement, count?], ...]].
// Each hook calls p14.tsx (the proposal). With no alternative chosen (the CONTROL, and every boot)
// each hook returns undefined and the product renders exactly as on main. A missing or doubled
// anchor STOPS THE SERVER (the seat guard in vite.config.mjs).
const G = "(globalThis as any)";

export default [
  // The screen: an alternative's desk of objects takes the Chair's place (the Chair's four
  // windows unmount, as the build would); with no alternative chosen the Chair renders.
  ["src/desk/DeskApp.tsx", null, [
    ["        <ChairHome arrivalRequired={arrivalRequired} />\n",
      `        (${G}.__pScreen?.(<ChairHome arrivalRequired={arrivalRequired} />) ?? <ChairHome arrivalRequired={arrivalRequired} />)\n`],
  ]],
];
