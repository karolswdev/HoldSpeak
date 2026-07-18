/** HS-95-01 — texture factory for the GL world. Sprite PNGs load through
 * pixi Assets (nearest-neighbor, the DOM's image-rendering: pixelated);
 * every soft visual the DOM did with CSS gradients/blur (object glow, ground
 * shadow, zone shadow, paper ruling, motes) is generated once into a texture
 * here and reused as sprites — nothing is painted per frame. */
import { Assets, Texture } from "pixi.js";
import { parseColor, withMixAlpha, type Rgba } from "./colors";

const spriteCache = new Map<string, Texture>();
const pending = new Map<string, Promise<Texture | null>>();

/** Load (and cache) a world sprite PNG; resolves null on a missing asset so
 * a bad kind never wedges the scene. */
export function loadSprite(
  url: string,
  onReady?: (t: Texture) => void,
): Texture | null {
  const hit = spriteCache.get(url);
  if (hit) return hit;
  if (!pending.has(url)) {
    pending.set(
      url,
      Assets.load<Texture>({ src: url, loadParser: "loadTextures" })
        .then((t) => {
          t.source.scaleMode = "nearest";
          spriteCache.set(url, t);
          onReady?.(t);
          return t;
        })
        .catch(() => null),
    );
  } else if (onReady) {
    void pending.get(url)!.then((t) => {
      if (t) onReady(t);
    });
  }
  return null;
}

function canvasTexture(
  w: number,
  h: number,
  draw: (ctx: CanvasRenderingContext2D) => void,
): Texture {
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  const ctx = c.getContext("2d");
  if (ctx) draw(ctx);
  return Texture.from(c);
}

const generated = new Map<string, Texture>();

function memo(key: string, make: () => Texture): Texture {
  const hit = generated.get(key);
  if (hit) return hit;
  const t = make();
  generated.set(key, t);
  return t;
}

/** The per-kind radial glow pool (desk.css .desk-obj-glow): tint at 55%
 * fading to transparent by 68%, blurred. Drawn at 2x for softness. */
export function glowTexture(tint: string): Texture {
  return memo(`glow:${tint}`, () => {
    const S = 168;
    const c = parseColor(tint);
    return canvasTexture(S, S, (ctx) => {
      const g = ctx.createRadialGradient(
        S / 2,
        S * 0.55,
        0,
        S / 2,
        S * 0.55,
        S / 2,
      );
      g.addColorStop(0, `rgba(${c.r},${c.g},${c.b},0.55)`);
      g.addColorStop(0.68, `rgba(${c.r},${c.g},${c.b},0)`);
      g.addColorStop(1, "rgba(0,0,0,0)");
      ctx.filter = "blur(7px)";
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, S, S);
    });
  });
}

/** The detached ground shadow (desk.css .desk-obj-shadow): 70×16 radial,
 * 0.62 black to transparent at 78%, 2px blur. */
export function shadowTexture(): Texture {
  return memo("obj-shadow", () => {
    const W = 84;
    const H = 26;
    return canvasTexture(W, H, (ctx) => {
      ctx.filter = "blur(2px)";
      const g = ctx.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, W / 2);
      g.addColorStop(0, "rgba(0,0,0,0.62)");
      g.addColorStop(0.78, "rgba(0,0,0,0)");
      g.addColorStop(1, "rgba(0,0,0,0)");
      ctx.save();
      ctx.translate(W / 2, H / 2);
      ctx.scale(1, H / W);
      ctx.translate(-W / 2, -H / 2);
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, W, W);
      ctx.restore();
    });
  });
}

/** The note/artifact paper ruling overlay (desk.css ::after): ruled lines,
 * an ink margin diagonal corner fold — generated to the lift's inset box. */
export function paperTexture(): Texture {
  return memo("paper", () => {
    const W = 65; // lift 96 - inset 16/15
    const H = 65;
    return canvasTexture(W, H, (ctx) => {
      // Ruled lines: repeating 180deg, transparent 0..11, ink 11..12.
      ctx.fillStyle = "rgba(72,62,46,0.28)";
      for (let y = 12 + 11; y < H; y += 12) ctx.fillRect(0, y, W, 1);
      // The corner fold: a 225deg gradient band in the top-right corner.
      ctx.save();
      ctx.translate(W, 0);
      ctx.rotate(Math.PI / 4);
      ctx.fillStyle = "rgba(0,0,0,0.22)";
      ctx.fillRect(-9, -14, 9, 28);
      ctx.fillStyle = "rgba(255,255,255,0.28)";
      ctx.fillRect(-10, -14, 1, 28);
      ctx.restore();
    });
  });
}

/** One soft rounded-rect drop shadow, nine-slice-scaled under zones and
 * panels (replaces the CSS box-shadow paint). */
export function zoneShadowTexture(): Texture {
  return memo("zone-shadow", () => {
    const S = 96;
    const R = 24;
    return canvasTexture(S, S, (ctx) => {
      ctx.filter = "blur(12px)";
      ctx.fillStyle = "rgba(0,0,0,0.5)";
      roundRect(ctx, 16, 20, S - 32, S - 36, R);
      ctx.fill();
    });
  });
}

/** A single soft mote speck (the Stage's dust, GPU-resident now). */
export function moteTexture(): Texture {
  return memo("mote", () => {
    const S = 16;
    return canvasTexture(S, S, (ctx) => {
      const g = ctx.createRadialGradient(
        S / 2,
        S / 2,
        0,
        S / 2,
        S / 2,
        S / 2,
      );
      g.addColorStop(0, "rgba(255,246,238,1)");
      g.addColorStop(0.6, "rgba(255,246,238,0.6)");
      g.addColorStop(1, "rgba(255,246,238,0)");
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, S, S);
    });
  });
}

/** The zone tray body: gradient fill + tinted border + inner top highlight
 * (desk.css .desk-zone recipe), rendered per (tint,width,height) size. */
export function zonePanelTexture(
  tint: string,
  width: number,
  height: number,
  emphasized: boolean,
): Texture {
  const key = `zone:${tint}:${Math.round(width)}x${Math.round(height)}:${emphasized ? 1 : 0}`;
  return memo(key, () => {
    const w = Math.max(8, Math.round(width));
    const h = Math.max(8, Math.round(height));
    const t = parseColor(tint);
    const border: Rgba = emphasized
      ? mix(t, { r: 255, g: 255, b: 255, a: 0.12 }, 0.8)
      : mix(t, { r: 255, g: 255, b: 255, a: 0.12 }, 0.34);
    return canvasTexture(w, h, (ctx) => {
      const g = ctx.createLinearGradient(0, 0, 0, h);
      const topFill = mix(t, { r: 18, g: 14, b: 24, a: 0.55 }, 0.15);
      g.addColorStop(0, `rgba(${topFill.r},${topFill.g},${topFill.b},0.62)`);
      g.addColorStop(1, "rgba(10,9,14,0.6)");
      roundRect(ctx, 0.5, 0.5, w - 1, h - 1, 16);
      ctx.fillStyle = g;
      ctx.fill();
      ctx.strokeStyle = `rgba(${border.r},${border.g},${border.b},${Math.min(1, border.a + 0.35)})`;
      ctx.lineWidth = 1;
      roundRect(ctx, 0.5, 0.5, w - 1, h - 1, 16);
      ctx.stroke();
      // inset 0 1px 0 tint@30%
      const hl = withMixAlpha(t, 0.3);
      ctx.strokeStyle = `rgba(${hl.r},${hl.g},${hl.b},${hl.a})`;
      ctx.beginPath();
      ctx.moveTo(14, 1.5);
      ctx.lineTo(w - 14, 1.5);
      ctx.stroke();
    });
  });
}

/** The zone resize grip (two diagonal tinted strokes, desk.css recipe). */
export function gripTexture(tint: string): Texture {
  return memo(`grip:${tint}`, () => {
    const S = 16;
    const t = parseColor(tint);
    return canvasTexture(S, S, (ctx) => {
      ctx.strokeStyle = `rgba(${t.r},${t.g},${t.b},0.85)`;
      ctx.lineWidth = 1.6;
      ctx.beginPath();
      ctx.moveTo(S - 2, 4);
      ctx.lineTo(4, S - 2);
      ctx.moveTo(S - 2, 9);
      ctx.lineTo(9, S - 2);
      ctx.stroke();
    });
  });
}

function mix(a: Rgba, b: Rgba, p: number): Rgba {
  const q = 1 - p;
  return {
    r: Math.round(a.r * p + b.r * q),
    g: Math.round(a.g * p + b.g * q),
    b: Math.round(a.b * p + b.b * q),
    a: a.a * p + b.a * q,
  };
}

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
) {
  const rr = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + rr, y);
  ctx.arcTo(x + w, y, x + w, y + h, rr);
  ctx.arcTo(x + w, y + h, x, y + h, rr);
  ctx.arcTo(x, y + h, x, y, rr);
  ctx.arcTo(x, y, x + w, y, rr);
  ctx.closePath();
}

/** Test seam: drop generated textures (jsdom has no real canvas). */
export function __resetTextureCaches(): void {
  spriteCache.clear();
  pending.clear();
  generated.clear();
}
