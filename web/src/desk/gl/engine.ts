/** HS-95-01 — the GL world engine. One pixi Application draws the whole
 * world layer (zones, objects, selection, drag, ambient motes) from the
 * pure scene model; the desk store stays the only truth and every store
 * write goes through the exact same actions the DOM world called. Per-frame
 * work is transform-only on the GPU scene graph — no DOM layout, no paint.
 *
 * Stacking parity with the DOM world: zones (z 2) draw above resting
 * objects; whatever is dragging rides at z 20; motes drift beneath all. */
import {
  Application,
  Container,
  Graphics,
  NineSliceSprite,
  Sprite,
  Text,
  Texture,
} from "pixi.js";
import { useDesk } from "../store";
import { useProjections } from "../projections";
import {
  buildScene,
  clampLabel,
  hitTest,
  objectRect,
  ropeObjects,
  zoneRect,
  DRAG_THRESHOLD,
  GRIP,
  LIFT,
  SPRITE,
  SPRITE_SMALL,
  type SceneObject,
  type SceneZone,
  type WorldScene,
} from "./sceneModel";
import {
  clientToUnit,
  unitToLocal,
  worldRectOf,
  OBJECT_CLAMP,
  ZONE_CLAMP,
  type WorldRect,
} from "./coords";
import {
  glowTexture,
  gripTexture,
  loadSprite,
  moteTexture,
  paperTexture,
  shadowTexture,
  zonePanelTexture,
  zoneShadowTexture,
} from "./textures";
import { parseColor } from "./colors";

const ACCENT = "#ff6b35";
const TEXT_COLOR = 0xf2f3f5;
const TEXT_MUTED = 0x9ba2b0;
const BOB_SECONDS = 4.6;

interface ObjectNode {
  root: Container;
  shadow: Sprite;
  lift: Container;
  glow: Sprite;
  glowTint: string;
  ring: Graphics;
  sprite: Sprite;
  highlight: Sprite;
  paper: Sprite | null;
  label: Text;
  badge: Container | null;
  badgeText: string;
  newBadge: Container | null;
  spriteUrl: string;
  labelText: string;
  ringState: string;
  bornAt: number;
  ringBornAt: number;
  wasNew: boolean;
  data: SceneObject;
}

interface ZoneNode {
  root: Container;
  shadow: NineSliceSprite;
  panel: Sprite;
  panelKey: string;
  title: Text;
  count: Text;
  thumbs: Container;
  thumbKeys: string;
  grip: Sprite;
  lift: number;
  liftTarget: number;
  scale: number;
  scaleTarget: number;
  data: SceneZone;
}

type DragState =
  | { type: "idle" }
  | {
      type: "pending";
      pointerId: number;
      startX: number;
      startY: number;
      hit: ReturnType<typeof hitTest>;
    }
  | { type: "object"; pointerId: number; id: string; startU?: { x: number; y: number } }
  | { type: "zone"; pointerId: number; id: string }
  | {
      type: "zone-grip";
      pointerId: number;
      id: string;
      baseWidth: number;
      startX: number;
    }
  | {
      type: "lasso";
      pointerId: number;
      x0: number;
      y0: number;
      x1: number;
      y1: number;
    }
  | { type: "scroll"; pointerId: number; lastY: number };

export interface EngineCallbacks {
  /** DOM overlays follow the GL lasso (kept as the proven .desk-lasso div). */
  onLasso(box: { left: number; top: number; w: number; h: number } | null): void;
  /** Tapping a zone title opens the DOM rename overlay. */
  onRenameZone(zoneId: string): void;
}

export class WorldEngine {
  private app: Application | null = null;
  private canvas: HTMLCanvasElement;
  private host: HTMLElement;
  private callbacks: EngineCallbacks;
  private zoneLayer = new Container();
  private objectLayer = new Container();
  private moteLayer = new Container();
  private objects = new Map<string, ObjectNode>();
  private zones = new Map<string, ZoneNode>();
  private motes: {
    sprite: Sprite;
    x: number;
    y: number;
    s: number;
    drift: number;
  }[] = [];
  private scene: WorldScene | null = null;
  private drag: DragState = { type: "idle" };
  private hoverKey: string | null = null;
  private unsubscribers: (() => void)[] = [];
  private reduceMotion = false;
  private destroyed = false;
  private rectCache: WorldRect | null = null;
  failed = false;

  constructor(
    canvas: HTMLCanvasElement,
    host: HTMLElement,
    callbacks: EngineCallbacks,
  ) {
    this.canvas = canvas;
    this.host = host;
    this.callbacks = callbacks;
  }

  async init(): Promise<void> {
    this.reduceMotion =
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const app = new Application();
    try {
      await app.init({
        canvas: this.canvas,
        resizeTo: this.host,
        backgroundAlpha: 0,
        antialias: true,
        resolution: Math.min(window.devicePixelRatio || 1, 2),
        autoDensity: true,
        preference: "webgl",
      });
    } catch {
      // No WebGL on this glass (test environments): the DOM overlays and
      // the a11y layer still function; the world simply does not draw.
      this.failed = true;
      return;
    }
    if (this.destroyed) {
      app.destroy();
      return;
    }
    this.app = app;
    // DOM parity: motes beneath, objects, then zones (z 2) above.
    app.stage.addChild(this.moteLayer, this.objectLayer, this.zoneLayer);
    this.seedMotes();
    this.refreshRect();
    this.rebuild();
    const rebuild = () => this.rebuild();
    this.unsubscribers.push(useDesk.subscribe(rebuild));
    this.unsubscribers.push(useProjections.subscribe(rebuild));
    // The world rect is CACHED and refreshed only when it can actually
    // change (resize, scroll, the world box growing) — per-frame and
    // per-move reads are pure math, never a forced layout (the GL upgrade
    // of the HS-71-05 fresh-rect robustness rule).
    const refresh = () => {
      this.refreshRect();
      this.rebuild();
    };
    const ro = new ResizeObserver(refresh);
    ro.observe(this.host);
    const onScroll = () => this.refreshRect();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });
    this.unsubscribers.push(() => {
      ro.disconnect();
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    });
    app.ticker.add(() => this.tick());
    this.bindPointer();
    // A read-only probe for the production walks (HS-95-01/10): where does
    // each object render, in client px? Lets Playwright drive the canvas
    // the way a hand does — by pointing at things.
    (window as unknown as Record<string, unknown>).__hsWorldProbe = () => {
      const rect = this.worldRect();
      return (this.scene?.objects || []).map((o) => ({
        id: o.id,
        ref: o.selectionRef,
        x: rect.left + o.u.x * rect.width,
        y: rect.top + o.u.y * rect.height,
      }));
    };
    (window as unknown as Record<string, unknown>).__hsWorldZoneProbe = () => {
      const rect = this.worldRect();
      return (this.scene?.zones || []).map((z) => ({
        id: z.id,
        x: rect.left + z.u.x * rect.width,
        y: rect.top + z.u.y * rect.height,
        width: z.width,
        height: z.height,
      }));
    };
  }

  private refreshRect(): void {
    this.rectCache = worldRectOf(this.host);
  }

  destroy(): void {
    this.destroyed = true;
    for (const u of this.unsubscribers) u();
    this.unsubscribers = [];
    this.app?.destroy(undefined, { children: true });
    this.app = null;
  }

  worldRect(): WorldRect {
    return this.rectCache ?? worldRectOf(this.host);
  }

  // ── scene sync ──────────────────────────────────────────────────────────

  private sceneInputs() {
    const s = useDesk.getState();
    const rect = this.worldRect();
    return {
      items: s.items,
      divedZone: s.divedZone,
      positions: s.positions,
      zoneWidths: s.zoneWidths,
      draggingId: s.draggingId,
      hoverZoneId: s.hoverZoneId,
      renamingZoneId: s.renamingZoneId,
      newIds: s.newIds,
      editingId: s.editingId,
      selectedIds: s.selectedIds,
      subjectCounts: useProjections.getState().subject_counts || {},
      compact: window.innerWidth <= 720,
      worldWidth: rect.width,
    };
  }

  rebuild(): void {
    if (!this.app) return;
    const rect = this.worldRect();
    const scene = buildScene(this.sceneInputs());
    this.scene = scene;
    this.syncObjects(scene, rect);
    this.syncZones(scene, rect);
  }

  private syncObjects(scene: WorldScene, rect: WorldRect): void {
    const seen = new Set<string>();
    for (const o of scene.objects) {
      seen.add(o.key);
      let node = this.objects.get(o.key);
      if (!node) {
        node = this.createObjectNode(o);
        this.objects.set(o.key, node);
        this.objectLayer.addChild(node.root);
      }
      this.updateObjectNode(node, o, rect);
    }
    for (const [key, node] of this.objects) {
      if (!seen.has(key)) {
        node.root.destroy({ children: true });
        this.objects.delete(key);
      }
    }
  }

  private createObjectNode(o: SceneObject): ObjectNode {
    const root = new Container();
    root.eventMode = "none";
    const shadow = new Sprite(shadowTexture());
    shadow.anchor.set(0.5);
    const lift = new Container();
    const glow = new Sprite(glowTexture(o.glow));
    glow.anchor.set(0.5);
    glow.alpha = 0.5;
    const ring = new Graphics();
    const sprite = new Sprite();
    sprite.anchor.set(0.5);
    const highlight = new Sprite();
    highlight.anchor.set(0.5);
    highlight.blendMode = "add";
    highlight.alpha = 0;
    const label = new Text({
      text: "",
      style: {
        fontFamily: bodyFont(),
        fontSize: 12,
        lineHeight: 15,
        fill: TEXT_MUTED,
        align: "center",
        dropShadow: {
          alpha: 0.7,
          angle: Math.PI / 2,
          blur: 3,
          color: 0x000000,
          distance: 1,
        },
      },
      resolution: Math.min((window.devicePixelRatio || 1) * 1.5, 3),
    });
    label.anchor.set(0.5, 0);
    lift.addChild(glow, ring, sprite, highlight);
    root.addChild(shadow, lift, label);
    return {
      root,
      shadow,
      lift,
      glow,
      glowTint: o.glow,
      ring,
      sprite,
      highlight,
      paper: null,
      label,
      badge: null,
      badgeText: "",
      newBadge: null,
      spriteUrl: "",
      labelText: "",
      ringState: " ",
      bornAt: performance.now(),
      ringBornAt: o.isNew ? performance.now() : 0,
      wasNew: o.isNew,
      data: o,
    };
  }

  private updateObjectNode(
    node: ObjectNode,
    o: SceneObject,
    rect: WorldRect,
  ): void {
    node.data = o;
    const p = unitToLocal(o.u, rect);
    node.root.position.set(p.x, p.y);
    node.root.zIndex = o.dragging ? 20 : 0;
    this.objectLayer.sortableChildren = true;
    const size = o.small ? SPRITE_SMALL : SPRITE;
    if (node.spriteUrl !== o.sprite) {
      node.spriteUrl = o.sprite;
      const tex = loadSprite(o.sprite, (t) => {
        if (node.spriteUrl === o.sprite) {
          node.sprite.texture = t;
          node.highlight.texture = t;
        }
      });
      if (tex) {
        node.sprite.texture = tex;
        node.highlight.texture = tex;
      }
    }
    node.sprite.width = size;
    node.sprite.height = size;
    node.highlight.width = size;
    node.highlight.height = size;
    if (o.small && !node.paper) {
      node.paper = new Sprite(paperTexture());
      node.paper.anchor.set(0.5);
      node.paper.position.set(0.5, 0.5);
      node.lift.addChild(node.paper);
    }
    if (node.paper) node.paper.visible = o.small;
    // Glow pool: kind tint, accent for new; alpha handled per-frame.
    const wantTint = o.isNew ? ACCENT : o.glow;
    if (node.glowTint !== wantTint) {
      node.glowTint = wantTint;
      node.glow.texture = glowTexture(wantTint);
    }
    node.glow.width = LIFT + 60;
    node.glow.height = LIFT + 60;
    // Shadow sits at lift bottom + ~40px (DOM: top 90px from lift top).
    node.shadow.position.set(0, 90 - LIFT / 2 + 8);
    node.shadow.width = 70;
    node.shadow.height = 16;
    // Ring: selected = steady dashed; new = pulsing solid (per-frame).
    // Redrawn only when its state actually flips — never on drags.
    const ringState = `${o.selected ? "s" : ""}${o.isNew ? "n" : ""}`;
    if (ringState !== node.ringState) {
      node.ringState = ringState;
      this.drawRing(node, o);
    }
    // Label: two-line clamp at 118px.
    if (node.labelText !== o.title) {
      node.labelText = o.title;
      const style = node.label.style;
      const measure = (s: string) => {
        node.label.text = s;
        return node.label.width;
      };
      void style;
      node.label.text = clampLabel(o.title, measure, 118);
    }
    node.label.position.set(0, LIFT / 2 + 4);
    // Attention badge (projection counts) + NEW badge.
    const badgeText = o.attention > 0 ? String(o.attention) : "";
    if (badgeText !== node.badgeText) {
      node.badgeText = badgeText;
      node.badge?.destroy({ children: true });
      node.badge = badgeText
        ? makeBadge(badgeText, 0xff4d4f, 0xffffff, 10)
        : null;
      if (node.badge) {
        node.badge.position.set(LIFT / 2 - 8, -LIFT / 2 + 6);
        node.lift.addChild(node.badge);
      }
    }
    if (o.isNew && !node.newBadge) {
      node.newBadge = makeBadge("NEW", parseColorNum(ACCENT), 0x06121f, 9);
      node.newBadge.position.set(LIFT / 2 - 10, -LIFT / 2 + 2);
      node.lift.addChild(node.newBadge);
      if (!node.wasNew) {
        node.ringBornAt = performance.now();
        node.wasNew = true;
      }
    }
    if (!o.isNew && node.newBadge) {
      node.newBadge.destroy({ children: true });
      node.newBadge = null;
      node.wasNew = false;
    }
    node.root.scale.set(o.scale);
  }

  private drawRing(node: ObjectNode, o: SceneObject): void {
    const g = node.ring;
    g.clear();
    if (!o.selected && !o.isNew) {
      g.visible = false;
      return;
    }
    g.visible = true;
    const r = LIFT / 2 - 2;
    if (o.selected) {
      // Dashed steady ring at 1.15 scale (the roped look).
      const dashes = 26;
      for (let i = 0; i < dashes; i++) {
        const a0 = (i / dashes) * Math.PI * 2;
        const a1 = a0 + (Math.PI * 2) / dashes / 1.9;
        g.arc(0, 0, r * 1.15, a0, a1);
        g.stroke({ width: 2, color: parseColorNum(ACCENT), alpha: 0.9 });
      }
    } else {
      g.circle(0, 0, r);
      g.stroke({ width: 2, color: parseColorNum(ACCENT), alpha: 0.85 });
    }
  }

  private syncZones(scene: WorldScene, rect: WorldRect): void {
    const seen = new Set<string>();
    for (const z of scene.zones) {
      seen.add(z.id);
      let node = this.zones.get(z.id);
      if (!node) {
        node = this.createZoneNode();
        this.zones.set(z.id, node);
        this.zoneLayer.addChild(node.root);
      }
      this.updateZoneNode(node, z, rect);
    }
    for (const [key, node] of this.zones) {
      if (!seen.has(key)) {
        node.root.destroy({ children: true });
        this.zones.delete(key);
      }
    }
  }

  private createZoneNode(): ZoneNode {
    const root = new Container();
    const shadow = new NineSliceSprite({
      texture: zoneShadowTexture(),
      leftWidth: 32,
      topHeight: 32,
      rightWidth: 32,
      bottomHeight: 32,
    });
    shadow.alpha = 0.85;
    const panel = new Sprite();
    const title = new Text({
      text: "",
      style: {
        fontFamily: bodyFont(),
        fontSize: 13,
        fontWeight: "600",
        fill: TEXT_COLOR,
      },
      resolution: Math.min((window.devicePixelRatio || 1) * 1.5, 3),
    });
    const count = new Text({
      text: "",
      style: { fontFamily: bodyFont(), fontSize: 12, fill: TEXT_MUTED },
      resolution: Math.min((window.devicePixelRatio || 1) * 1.5, 3),
    });
    const thumbs = new Container();
    const grip = new Sprite();
    grip.alpha = 0;
    root.addChild(shadow, panel, title, count, thumbs, grip);
    return {
      root,
      shadow,
      panel,
      panelKey: "",
      title,
      count,
      thumbs,
      thumbKeys: "",
      grip,
      lift: 0,
      liftTarget: 0,
      scale: 1,
      scaleTarget: 1,
      data: {} as SceneZone,
    };
  }

  private updateZoneNode(node: ZoneNode, z: SceneZone, rect: WorldRect): void {
    node.data = z;
    const r = zoneRect(z, rect);
    node.root.position.set(r.left, r.top);
    node.root.zIndex = z.dragging ? 20 : 2;
    this.zoneLayer.sortableChildren = true;
    node.root.pivot.set(0, 0);
    const emphasized = z.dropReady || this.hoverKey === `zone:${z.id}`;
    const panelKey = `${z.tint}:${Math.round(z.width)}x${z.height}:${emphasized ? 1 : 0}`;
    if (node.panelKey !== panelKey) {
      node.panelKey = panelKey;
      node.panel.texture = zonePanelTexture(
        z.tint,
        z.width,
        z.height,
        emphasized,
      );
    }
    node.shadow.position.set(-14, -8);
    node.shadow.width = z.width + 28;
    node.shadow.height = z.height + 34;
    node.title.text = z.title;
    node.title.position.set(16, 11);
    const countText =
      z.count === 0
        ? "drop things here"
        : z.count === 1
          ? "1 item"
          : `${z.count} items`;
    node.count.text = countText;
    node.count.position.set(
      z.thumbs.length > 0 ? 16 + z.thumbs.length * 26 + (z.more ? 26 : 0) : 16,
      z.thumbs.length > 0 ? z.height - 27 : z.height - 29,
    );
    const thumbKeys =
      z.thumbs.map((t) => t.id).join(",") + (z.more ? `+${z.more}` : "");
    if (node.thumbKeys !== thumbKeys) {
      node.thumbKeys = thumbKeys;
      node.thumbs.removeChildren().forEach((c) => c.destroy({ children: true }));
      z.thumbs.forEach((t, i) => {
        const s = new Sprite();
        const tex = loadSprite(t.sprite, (loaded) => {
          s.texture = loaded;
        });
        if (tex) s.texture = tex;
        s.width = 22;
        s.height = 22;
        s.position.set(16 + i * 26, z.height - 33);
        node.thumbs.addChild(s);
      });
      if (z.more > 0) {
        const more = new Text({
          text: `+${z.more}`,
          style: { fontFamily: bodyFont(), fontSize: 11, fill: TEXT_MUTED },
          resolution: 2,
        });
        more.position.set(16 + z.thumbs.length * 26, z.height - 30);
        node.thumbs.addChild(more);
      }
    }
    if (!node.grip.texture || node.grip.texture === Texture.EMPTY) {
      node.grip.texture = gripTexture(z.tint);
    }
    node.grip.position.set(z.width - GRIP - 3, z.height - GRIP - 3);
    node.grip.alpha = emphasized || z.dragging ? 0.9 : 0.35;
    node.liftTarget = z.dropReady ? -4 : emphasized ? -2 : 0;
    node.scaleTarget = z.dropReady ? 1.04 : 1;
    // Rename hides the GL title (the DOM input overlays it).
    node.title.visible = !z.renaming;
  }

  // ── per-frame (transform-only) ──────────────────────────────────────────

  private seedMotes(): void {
    const N = 18;
    for (let i = 0; i < N; i++) {
      const sprite = new Sprite(moteTexture());
      sprite.anchor.set(0.5);
      const r = 0.6 + Math.random() * 1.6;
      sprite.width = r * 4;
      sprite.height = r * 4;
      sprite.alpha = 0.06 + Math.random() * 0.12;
      this.moteLayer.addChild(sprite);
      this.motes.push({
        sprite,
        x: Math.random(),
        y: Math.random(),
        s: 0.006 + Math.random() * 0.014,
        drift: (Math.random() - 0.5) * 0.01,
      });
    }
  }

  private tick(): void {
    if (!this.app) return;
    const now = performance.now();
    const dt = Math.min(this.app.ticker.deltaMS / 1000, 0.05);
    const w = this.app.renderer.width / this.app.renderer.resolution;
    const h = this.app.renderer.height / this.app.renderer.resolution;
    if (!this.reduceMotion) {
      for (const m of this.motes) {
        m.y -= m.s * dt;
        m.x += m.drift * dt;
        if (m.y < -0.02) {
          m.y = 1.02;
          m.x = Math.random();
        }
        m.sprite.position.set(m.x * w, m.y * h);
      }
    } else {
      for (const m of this.motes) m.sprite.position.set(m.x * w, m.y * h);
    }
    for (const node of this.objects.values()) {
      const o = node.data;
      const settled = o.dragging || o.editing || this.reduceMotion;
      // The bob: rotate(tilt→-tilt) + translateY(0→-9), 4.6s, phase delay.
      const frac = settled
        ? 0
        : (((now / 1000 - o.phase) % BOB_SECONDS) + BOB_SECONDS) %
          BOB_SECONDS /
          BOB_SECONDS;
      const k = settled ? 0 : (1 - Math.cos(frac * Math.PI * 2)) / 2;
      node.lift.position.y = -9 * k;
      node.lift.rotation = ((o.tilt * (1 - 2 * k)) * Math.PI) / 180;
      node.shadow.scale.x = (1 - 0.2 * k) * (70 / node.shadow.texture.width);
      node.shadow.alpha = 0.5 - 0.2 * k;
      // Hover/selection glow levels (DOM: .5 rest, .82 hover, .95 new, .9 editing).
      const hovered = this.hoverKey === `obj:${o.key}`;
      node.glow.alpha = o.isNew
        ? 0.95
        : o.editing
          ? 0.9
          : hovered
            ? 0.82
            : o.selected
              ? 0.55
              : 0.5;
      node.highlight.alpha = hovered ? 0.12 : 0;
      // Materialize: 0.5s overshoot scale-in on spawn.
      const age = (now - node.bornAt) / 500;
      if (age < 1 && !this.reduceMotion) {
        const t = overshoot(Math.min(1, age));
        node.root.alpha = Math.min(1, age * 2);
        node.root.scale.set(o.scale * (0.35 + 0.65 * t));
      } else {
        node.root.alpha = 1;
        node.root.scale.set(o.scale);
      }
      // The NEW ring pulse: 1.1s ease-out, three beats.
      if (o.isNew && node.ringBornAt && !o.selected) {
        const beat = (now - node.ringBornAt) / 1100;
        if (beat < 3) {
          const bt = beat % 1;
          node.ring.visible = true;
          node.ring.alpha = 0.85 * (1 - bt);
          node.ring.scale.set(0.7 + 0.85 * bt);
        } else {
          node.ring.visible = false;
        }
      } else if (o.selected) {
        node.ring.alpha = 0.9;
        node.ring.scale.set(1);
      }
    }
    const rect = this.worldRect();
    for (const node of this.zones.values()) {
      node.lift += (node.liftTarget - node.lift) * Math.min(1, dt * 14);
      node.scale += (node.scaleTarget - node.scale) * Math.min(1, dt * 14);
      node.root.position.y = node.data.u.y * rect.height + node.lift;
      node.root.scale.set(node.scale);
    }
  }

  // ── input (the DOM world's exact semantics, HS-71-04/05/06) ─────────────

  private bindPointer(): void {
    const c = this.canvas;
    const down = (e: PointerEvent) => this.onDown(e);
    const move = (e: PointerEvent) => this.onMove(e);
    const up = (e: PointerEvent) => this.onUp(e);
    const hover = (e: PointerEvent) => this.onHover(e);
    c.addEventListener("pointerdown", down);
    c.addEventListener("pointermove", move);
    c.addEventListener("pointermove", hover);
    c.addEventListener("pointerup", up);
    c.addEventListener("pointercancel", up);
    this.unsubscribers.push(() => {
      c.removeEventListener("pointerdown", down);
      c.removeEventListener("pointermove", move);
      c.removeEventListener("pointermove", hover);
      c.removeEventListener("pointerup", up);
      c.removeEventListener("pointercancel", up);
    });
  }

  private local(e: PointerEvent): { x: number; y: number; rect: WorldRect } {
    // A FRESH world rect each event (the HS-71-05 robustness rule).
    const rect = this.worldRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top, rect };
  }

  private onDown(e: PointerEvent): void {
    if (!this.scene) return;
    if (e.button !== 0 && e.pointerType === "mouse") return;
    const { x, y, rect } = this.local(e);
    const hit = hitTest(this.scene, rect, x, y);
    if (hit.type === "background") {
      if (e.pointerType === "touch") {
        this.drag = { type: "scroll", pointerId: e.pointerId, lastY: e.clientY };
        this.canvas.setPointerCapture(e.pointerId);
        return;
      }
      this.drag = {
        type: "lasso",
        pointerId: e.pointerId,
        x0: e.clientX,
        y0: e.clientY,
        x1: e.clientX,
        y1: e.clientY,
      };
      this.canvas.setPointerCapture(e.pointerId);
      return;
    }
    this.drag = {
      type: "pending",
      pointerId: e.pointerId,
      startX: e.clientX,
      startY: e.clientY,
      hit,
    };
    this.canvas.setPointerCapture(e.pointerId);
  }

  private onMove(e: PointerEvent): void {
    const d = this.drag;
    if (d.type === "idle" || !this.scene) return;
    if ("pointerId" in d && d.pointerId !== e.pointerId) return;
    const state = useDesk.getState();
    if (d.type === "scroll") {
      const dy = e.clientY - d.lastY;
      (this.drag as typeof d).lastY = e.clientY;
      window.scrollBy(0, -dy);
      return;
    }
    if (d.type === "lasso") {
      d.x1 = e.clientX;
      d.y1 = e.clientY;
      const rect = this.worldRect();
      this.callbacks.onLasso({
        left: Math.min(d.x0, d.x1) - rect.left,
        top: Math.min(d.y0, d.y1) - rect.top,
        w: Math.abs(d.x1 - d.x0),
        h: Math.abs(d.y1 - d.y0),
      });
      return;
    }
    if (d.type === "pending") {
      const moved =
        Math.abs(e.clientX - d.startX) + Math.abs(e.clientY - d.startY) >
        DRAG_THRESHOLD;
      if (!moved) return;
      if (d.hit.type === "object") {
        state.setDragging(d.hit.object.id);
        this.drag = {
          type: "object",
          pointerId: d.pointerId,
          id: d.hit.object.id,
          // HS-101 B7 — the home position: a drop through the glass
          // hands the object over and returns it here (never consumed).
          startU: useDesk.getState().positions[d.hit.object.id],
        };
      } else if (d.hit.type === "zone" || d.hit.type === "zone-title") {
        state.setDragging(`zone:${d.hit.zone.id}`);
        this.drag = { type: "zone", pointerId: d.pointerId, id: d.hit.zone.id };
      } else if (d.hit.type === "zone-grip") {
        this.drag = {
          type: "zone-grip",
          pointerId: d.pointerId,
          id: d.hit.zone.id,
          baseWidth: d.hit.zone.width,
          startX: d.startX,
        };
      }
      // fall through so the first real move also positions
    }
    const rect = this.worldRect();
    if (this.drag.type === "object") {
      const u = clientToUnit(e.clientX, e.clientY, rect, OBJECT_CLAMP);
      state.setPosition(this.drag.id, u);
      // The drop affordance: hit-test fresh zone rects each move.
      const hit = hitTest(
        this.scene,
        rect,
        e.clientX - rect.left,
        e.clientY - rect.top,
        { ignoreObjectId: this.drag.id },
      );
      state.setHoverZone(
        hit.type === "zone" || hit.type === "zone-title" || hit.type === "zone-grip"
          ? hit.zone.id
          : null,
      );
    } else if (this.drag.type === "zone") {
      const u = clientToUnit(e.clientX, e.clientY, rect, ZONE_CLAMP);
      state.setPosition(`zone:${this.drag.id}`, u);
    } else if (this.drag.type === "zone-grip") {
      const next = Math.min(
        560,
        Math.max(148, this.drag.baseWidth + (e.clientX - this.drag.startX)),
      );
      state.setZoneWidth(this.drag.id, next, false);
    }
  }

  private onUp(e: PointerEvent): void {
    const d = this.drag;
    if (d.type === "idle") return;
    if ("pointerId" in d && d.pointerId !== e.pointerId) return;
    this.drag = { type: "idle" };
    const state = useDesk.getState();
    if (d.type === "scroll") return;
    if (d.type === "lasso") {
      this.callbacks.onLasso(null);
      const left = Math.min(d.x0, d.x1);
      const right = Math.max(d.x0, d.x1);
      const top = Math.min(d.y0, d.y1);
      const bottom = Math.max(d.y0, d.y1);
      if (right - left < 8 && bottom - top < 8) {
        // A bare tap on the desk settles the selection — unless the Ask
        // composer holds the rope (HSM-16-04).
        if (!state.askOpen) state.clearSelection();
        return;
      }
      if (!this.scene) return;
      const roped = ropeObjects(this.scene, this.worldRect(), {
        left,
        top,
        right,
        bottom,
      });
      if (roped.length) state.setSelected(roped);
      return;
    }
    if (d.type === "pending") {
      // Never moved past the threshold: this is a tap (HS-71-06).
      const hit = d.hit;
      if (hit.type === "object") {
        if (e.shiftKey || e.metaKey || e.ctrlKey) {
          state.toggleSelected(hit.object.selectionRef);
        } else {
          state.setDragging(null);
          state.openPullout(hit.object.id);
        }
      } else if (hit.type === "zone") {
        state.diveInto(hit.zone.id);
      } else if (hit.type === "zone-title") {
        this.callbacks.onRenameZone(hit.zone.id);
      } else if (hit.type === "zone-grip") {
        // A grip tap does nothing (DOM parity: click stopped propagation).
      }
      return;
    }
    if (d.type === "object") {
      const obj = this.scene?.objects.find((o) => o.id === d.id);
      // HS-101 B7 — through the glass: a drop landing on a marked DOM
      // well hands the object to that well and the object returns home.
      const overlay = document
        .elementFromPoint(e.clientX, e.clientY)
        ?.closest?.("[data-glass-accept~='desk-object']");
      if (overlay && obj) {
        state.setHoverZone(null);
        overlay.dispatchEvent(
          new CustomEvent("desk:glass-drop", {
            bubbles: true,
            detail: { id: d.id, kind: obj.kind },
          }),
        );
        if (d.startU) state.setPosition(d.id, d.startU);
        else state.clearPosition(d.id);
        state.persistPositions();
        setTimeout(() => useDesk.getState().setDragging(null), 0);
        return;
      }
      // Dropped onto a zone? File it (the real PUT); else persist the park.
      const over = state.hoverZoneId;
      state.setHoverZone(null);
      if (over && obj) {
        void state.fileIntoDir(d.id, over, obj.kind);
      } else {
        state.persistPositions();
      }
      // Cleared next tick — the click discrimination the DOM relied on
      // is structural here (a completed drag never reaches the tap arm),
      // but pullout-open guards still read draggingId (HS-71-06).
      setTimeout(() => useDesk.getState().setDragging(null), 0);
      return;
    }
    if (d.type === "zone") {
      state.persistPositions();
      setTimeout(() => useDesk.getState().setDragging(null), 0);
      return;
    }
    if (d.type === "zone-grip") {
      const z = this.scene?.zones.find((z) => z.id === d.id);
      if (z)
        state.setZoneWidth(
          d.id,
          Math.min(560, Math.max(148, d.baseWidth + (e.clientX - d.startX))),
          true,
        );
    }
  }

  private onHover(e: PointerEvent): void {
    if (!this.scene || this.drag.type !== "idle") return;
    const { x, y, rect } = this.local(e);
    const hit = hitTest(this.scene, rect, x, y);
    const key =
      hit.type === "object"
        ? `obj:${hit.object.key}`
        : hit.type === "background"
          ? null
          : `zone:${hit.zone.id}`;
    if (key !== this.hoverKey) {
      this.hoverKey = key;
      // Emphasis states resolve in the next sync (cheap, store-free).
      if (this.scene) this.rebuild();
    }
    this.canvas.style.cursor =
      hit.type === "object" || hit.type === "zone"
        ? "grab"
        : hit.type === "zone-grip"
          ? "ew-resize"
          : hit.type === "zone-title"
            ? "text"
            : "default";
  }
}

function overshoot(t: number): number {
  // cubic-bezier(0.2, 1.4, 0.4, 1) flavor: fast rise, slight overshoot.
  const s = 1.70158 * 0.7;
  const u = t - 1;
  return u * u * ((s + 1) * u + s) + 1;
}

function bodyFont(): string {
  if (typeof document !== "undefined") {
    const f = getComputedStyle(document.body).fontFamily;
    if (f) return f;
  }
  return "system-ui, sans-serif";
}

function parseColorNum(c: string): number {
  const p = parseColor(c);
  return (p.r << 16) + (p.g << 8) + p.b;
}

function makeBadge(
  text: string,
  bg: number,
  fg: number,
  fontSize: number,
): Container {
  const c = new Container();
  const label = new Text({
    text,
    style: {
      fontFamily: bodyFont(),
      fontSize,
      fontWeight: "800",
      letterSpacing: 0.5,
      fill: fg,
    },
    resolution: 2,
  });
  const padX = 6;
  const padY = 2;
  const g = new Graphics();
  g.roundRect(
    -label.width / 2 - padX,
    -label.height / 2 - padY,
    label.width + padX * 2,
    label.height + padY * 2,
    999,
  );
  g.fill({ color: bg });
  label.anchor.set(0.5);
  c.addChild(g, label);
  return c;
}
