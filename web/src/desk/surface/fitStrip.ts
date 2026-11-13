export const VERB_OVERFLOW_WORD = "Actions";
/** Whole controls only; a selected item keeps its seat before overflow. */
export function fitStrip(width: number, sizes: readonly number[], more: number, gap: number, selected = -1): number[] {
  const total = (ids: number[]) => ids.reduce((n, i) => n + sizes[i], 0) + gap * Math.max(0, ids.length - 1);
  const all = sizes.map((_, i) => i);
  if (width <= 0 || total(all) <= width) return all;
  const shown = selected >= 0 ? [selected] : [];
  for (const i of all) {
    if (i === selected) continue;
    if (total([...shown, i]) + gap + more > width) break;
    shown.push(i);
  }
  return shown.sort((a, b) => a - b);
}
