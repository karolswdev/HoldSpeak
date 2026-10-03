// PHILO-13-17 (C7) seats: [product file (suffix, #tag), import line or null, [[anchor, replacement, count?], ...]].
// Each hook calls c7.tsx (this folder); with the shim absent each is a no-op. Loaded by
// ../../story-15-canvas/harness/vite.config.mjs with CANVAS_SHIMS=c7.
const G = "(globalThis as any)";

export default [
  // Q2: at 393 the screen title is the window switcher (the open windows, a check on the front one).
  ["src/desk/components/DeskChrome.tsx", null, [
    ["  return (\n    <span className=\"desk-screen-title\" data-testid=\"desk-screen-title\">",
      `  const __c7 = ${G}.__c7ScreenTitle?.(name);\n  if (__c7) return __c7;\n  return (\n    <span className="desk-screen-title" data-testid="desk-screen-title">`],
  ]],
  // Q3: at 393 Go carries Chair ▸ Desk ▸ Object ▸ Window ▸ first, then its own rows (not one flat list).
  ["src/desk/components/DeskMenuBar.tsx", null, [
    ["    if (compact && id === \"go\")\n      for (const m of MENUS) if (m.id !== \"go\") menuEntries(m.id, out);",
      `    if (compact && id === "go" && ${G}.__c7GoGroups) ${G}.__c7GoGroups(out, menuEntries);\n    else if (compact && id === "go")\n      for (const m of MENUS) if (m.id !== "go") menuEntries(m.id, out);`],
  ]],
  // Q4: an arriving aftercare card opens the Capture window at 393 (the owner's ruling).
  ["src/desk/intelligenceAttention.ts", null, [
    ["function publish(next: AftercareSignal | null) {\n  aftercare = next;",
      `function publish(next: AftercareSignal | null) {\n  const __c7Was = aftercare;\n  aftercare = next;\n  ${G}.__c7Aftercare?.(next, __c7Was);`],
  ]],
  // Q4b (Astra canvas r1, condition 1): at 393 on the Chair an undismissed card with no slot waits for its
  // Capture window (still in the ring) instead of the fixed overlay over work.
  ["src/components/AmbientLayer.tsx", null, [
    ["  return aftercareSlot ? createPortal(card, aftercareSlot) : card;",
      `  return aftercareSlot ? createPortal(card, aftercareSlot) : (${G}.__c7HoldCard?.() ? null : card);`],
  ]],
];
