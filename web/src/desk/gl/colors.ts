/** HS-95-01 — tiny sRGB color helpers so the GL world reproduces the CSS
 * `color-mix(in srgb, …)` recipes the DOM world used. Pure, testable. */

export interface Rgba {
  r: number;
  g: number;
  b: number;
  a: number;
}

export function parseColor(input: string): Rgba {
  const s = String(input || "").trim();
  if (s.startsWith("#")) {
    const hex = s.slice(1);
    const full =
      hex.length === 3
        ? hex
            .split("")
            .map((c) => c + c)
            .join("")
        : hex;
    const v = parseInt(full.slice(0, 6), 16);
    const a = full.length >= 8 ? parseInt(full.slice(6, 8), 16) / 255 : 1;
    return {
      r: (v >> 16) & 255,
      g: (v >> 8) & 255,
      b: v & 255,
      a,
    };
  }
  const m = s.match(/rgba?\(([^)]+)\)/);
  if (m) {
    const parts = m[1].split(",").map((p) => parseFloat(p.trim()));
    return {
      r: parts[0] || 0,
      g: parts[1] || 0,
      b: parts[2] || 0,
      a: parts.length > 3 ? parts[3] : 1,
    };
  }
  return { r: 255, g: 107, b: 53, a: 1 };
}

/** CSS `color-mix(in srgb, a p, b (1-p))` — channel-wise, alpha included. */
export function mixColors(a: string | Rgba, b: string | Rgba, p: number): Rgba {
  const ca = typeof a === "string" ? parseColor(a) : a;
  const cb = typeof b === "string" ? parseColor(b) : b;
  const q = 1 - p;
  return {
    r: Math.round(ca.r * p + cb.r * q),
    g: Math.round(ca.g * p + cb.g * q),
    b: Math.round(ca.b * p + cb.b * q),
    a: ca.a * p + cb.a * q,
  };
}

/** `color-mix(in srgb, c p, transparent)` — CSS transparent is black@0. */
export function withMixAlpha(c: string | Rgba, p: number): Rgba {
  return mixColors(c, { r: 0, g: 0, b: 0, a: 0 }, p);
}

export function toNumber(c: Rgba): number {
  return (c.r << 16) + (c.g << 8) + c.b;
}

export function toCss(c: Rgba): string {
  return `rgba(${c.r},${c.g},${c.b},${c.a.toFixed(3)})`;
}
