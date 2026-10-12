/** TopologySurface — DOM nodes over an SVG edge layer with bounded pan.
 *  Council codex section 2.6: presentation and interaction ONLY —
 *  service callbacks remain with the feature.
 *
 *  Contract:
 *  - DOM nodes positioned absolute over an SVG edge layer
 *  - Bounded pan (viewport pans within constrained area)
 *  - Home-node designation (one node anchored, visually distinct)
 *  - Bundled labeled flows (multiple labels on one from-to edge)
 *  - Roving selection: Tab enters, arrows navigate between nodes
 *  - Keyboard pan (Shift+Arrow), select (Enter), re-point slot
 *  - Inspector + add-node slots (consumer-provided via render prop)
 *  - Reduced-motion support (all transitions honor prefers-reduced-motion)
 */
import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { Button } from "../../../components/signal/Signal";
import "./topology-surface.css";

// ── Public model ────────────────────────────────────────────────────

export type GraphNode = {
  id: string;
  label: string;
  home?: boolean;
  /** Health state — maps to StateChip vocabulary. */
  state?: "idle" | "active" | "working" | "success" | "warning" | "failure" | "unreachable";
  /** Position in graph coordinates. */
  x: number;
  y: number;
  /** Content rendered inside the node card. */
  children?: ReactNode;
};

export type GraphFlow = {
  /** Unique id for the bundled flow group. */
  id: string;
  from: string;
  to: string;
  /** Labels for each job/group bundled into this edge. */
  labels: string[];
};

export type TopologySurfaceProps = {
  nodes: GraphNode[];
  flows: GraphFlow[];
  selectedId?: string | null;
  onSelect?: (id: string | null) => void;
  /** Rendered beside the selected node. */
  inspectorSlot?: ReactNode;
  /** Rendered as a persistent add-node action area. */
  addNodeSlot?: ReactNode;
  ariaLabel?: string;
};

// ── Geometry ────────────────────────────────────────────────────────

const PAN_STEP = 60;
const NODE_W = 180;
const NODE_H = 80;

function clamp(v: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, v));
}

/** PHILO-17 (owner ruling 2026-10-12, "shrink it"; Astra's post-merge
 *  review of #1113): a map wider than its box is fitted, and the cards never
 *  touch.
 *   - "free": the layout as given (it fits), or brought closer, but never
 *     closer than one card plus LABEL_GAP between two cards side by side,
 *     so a flow label always has the gap to sit in.
 *   - "stack": when two cards cannot stand side by side with that gap, the
 *     cards reflow into ONE column, home first, with a row gap that holds
 *     the flow label of the card under it; the edges run down the left
 *     gutter.
 *  The words keep their size (12 px and up); only the layout changes. A
 *  fitted map is whole in its box, so it does not pan sideways. */
const MIN_NODE_W = 128;
const FIT_MARGIN = 24;
/** The least room between two cards side by side: a wrapped label fits. */
const LABEL_GAP = 104;
/** The stack: the left gutter the edges run in, and the row gap a label sits in. */
const STACK_GUTTER = 16;
const STACK_ROW_GAP = 52;

export type FitMode = "free" | "stack";
export type Fit = { nodes: GraphNode[]; nodeW: number; fitted: boolean; mode: FitMode };

export function fitLayout(nodes: GraphNode[], viewW: number): Fit {
  if (!nodes.length || !viewW) return { nodes, nodeW: NODE_W, fitted: false, mode: "free" };
  const xs = nodes.map((n) => n.x);
  const minX = Math.min(...xs);
  const span = Math.max(...xs) - minX;
  const room = viewW - 2 * FIT_MARGIN;
  if (span + NODE_W <= room) return { nodes, nodeW: NODE_W, fitted: false, mode: "free" };
  // Side by side, closer: the factor that fits, and the least one that
  // keeps LABEL_GAP between every two cards that stand side by side.
  const nodeW = MIN_NODE_W;
  const fit = span ? Math.min(1, (room - nodeW) / span) : 1;
  let need = 0;
  for (const a of nodes) for (const b of nodes) {
    const dx = Math.abs(a.x - b.x);
    const sideBySide = dx > 0 && Math.abs(a.y - b.y) < NODE_H + LABEL_GAP;
    if (sideBySide) need = Math.max(need, (nodeW + LABEL_GAP) / dx);
  }
  if (span && fit > 0 && need <= fit) {
    return { nodes: nodes.map((n) => ({ ...n, x: minX + (n.x - minX) * fit })), nodeW, fitted: true, mode: "free" };
  }
  // One column, home first, then the rest as they read (top to bottom, left to right).
  const order = [...nodes].sort((a, b) => Number(Boolean(b.home)) - Number(Boolean(a.home)) || a.y - b.y || a.x - b.x);
  const stackW = Math.max(MIN_NODE_W, Math.min(NODE_W, room - STACK_GUTTER));
  const placed = new Map(order.map((n, i) => [n.id, { ...n, x: STACK_GUTTER, y: i * (NODE_H + STACK_ROW_GAP) }]));
  return { nodes: nodes.map((n) => placed.get(n.id)!), nodeW: stackW, fitted: true, mode: "stack" };
}

/** Where a flow's label sits: in the gap between two cards side by side, as
 *  wide as the gap (it wraps); in the stack, in the row gap above its lower
 *  card. Never on a card. */
export function labelPlace(
  from: GraphNode, to: GraphNode, w: number, mode: FitMode,
): { left: number; top: number; maxWidth?: number; centred: boolean } {
  if (mode === "stack") {
    const lower = from.y > to.y ? from : to;
    return { left: lower.x, top: lower.y - STACK_ROW_GAP + 6, maxWidth: w, centred: false };
  }
  const [l, r] = from.x <= to.x ? [from, to] : [to, from];
  const gap = r.x - (l.x + w);
  const y = (from.y + to.y + NODE_H) / 2;
  if (gap >= LABEL_GAP) return { left: l.x + w + gap / 2, top: y, maxWidth: gap - 8, centred: true };
  const mid = edgeMidpoint(from, to, w);
  return { left: mid.x, top: mid.y, centred: true };
}

/** Compute the bounding box of all nodes + padding. */
function contentBounds(nodes: GraphNode[], w = NODE_W, pad = 80): {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
} {
  if (!nodes.length) return { minX: 0, minY: 0, maxX: 400, maxY: 300 };
  let minX = Infinity,
    minY = Infinity,
    maxX = -Infinity,
    maxY = -Infinity;
  for (const n of nodes) {
    if (n.x < minX) minX = n.x;
    if (n.y < minY) minY = n.y;
    if (n.x + w > maxX) maxX = n.x + w;
    if (n.y + NODE_H > maxY) maxY = n.y + NODE_H;
  }
  return {
    minX: minX - pad,
    minY: minY - pad,
    maxX: maxX + pad,
    maxY: maxY + pad,
  };
}

/** SVG path for a bundled edge between two node rects. */
function edgePath(
  from: GraphNode,
  to: GraphNode,
  w = NODE_W,
  mode: FitMode = "free",
): string {
  if (mode === "stack") {
    // Out of the left side, down the gutter, into the left side.
    const g = Math.min(from.x, to.x) - STACK_GUTTER / 2;
    return `M${from.x},${from.y + NODE_H / 2} H${g} V${to.y + NODE_H / 2} H${to.x}`;
  }
  const x1 = from.x + w / 2;
  const y1 = from.y + NODE_H / 2;
  const x2 = to.x + w / 2;
  const y2 = to.y + NODE_H / 2;
  // Simple cubic bezier with a horizontal bias
  const dx = x2 - x1;
  const cpx = dx * 0.5;
  return `M${x1},${y1} C${x1 + cpx},${y1} ${x2 - cpx},${y2} ${x2},${y2}`;
}

/** Midpoint of the edge path for label placement. */
function edgeMidpoint(
  from: GraphNode,
  to: GraphNode,
  w = NODE_W,
): { x: number; y: number } {
  return {
    x: (from.x + to.x + w) / 2,
    y: (from.y + to.y + NODE_H) / 2,
  };
}

// ── Nearest-neighbor nav ────────────────────────────────────────────

function nearestInDirection(
  nodes: GraphNode[],
  current: GraphNode,
  dir: "left" | "right" | "up" | "down",
): GraphNode | null {
  let best: GraphNode | null = null;
  let bestDist = Infinity;
  for (const n of nodes) {
    if (n.id === current.id) continue;
    const dx = n.x - current.x;
    const dy = n.y - current.y;
    let valid = false;
    switch (dir) {
      case "right":
        valid = dx > 0;
        break;
      case "left":
        valid = dx < 0;
        break;
      case "down":
        valid = dy > 0;
        break;
      case "up":
        valid = dy < 0;
        break;
    }
    if (!valid) continue;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist < bestDist) {
      bestDist = dist;
      best = n;
    }
  }
  return best;
}

// ── State icon glyphs (mirror StateChip defaults) ───────────────────

const STATE_ICONS: Record<string, string> = {
  idle: "○",
  active: "●",
  working: "↻",
  success: "✓",
  warning: "⚠",
  failure: "✗",
  unreachable: "—",
};

// ── Component ───────────────────────────────────────────────────────

export function TopologySurface({
  nodes: givenNodes,
  flows,
  selectedId,
  onSelect,
  inspectorSlot,
  addNodeSlot,
  ariaLabel = "Topology map",
}: TopologySurfaceProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewportRef = useRef<HTMLDivElement>(null);
  // The box's width: a map wider than it is fitted (fitLayout).
  const [viewW, setViewW] = useState(0);
  useLayoutEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const read = () => setViewW(el.clientWidth);
    read();
    if (typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(read);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  const fit = useMemo(() => fitLayout(givenNodes, viewW), [givenNodes, viewW]);
  const nodes = fit.nodes;
  const nodeW = fit.nodeW;
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [internalSelected, setInternalSelected] = useState<string | null>(null);
  const nodeRefs = useRef<Record<string, HTMLButtonElement | null>>({});

  const selected = selectedId !== undefined ? selectedId : internalSelected;
  const select = useCallback(
    (id: string | null) => {
      if (selectedId !== undefined) {
        onSelect?.(id);
      } else {
        setInternalSelected(id);
        onSelect?.(id);
      }
    },
    [selectedId, onSelect],
  );

  // ── Bounded pan ──
  const bounds = useMemo(() => contentBounds(nodes, nodeW, fit.fitted ? 0 : 80), [nodes, nodeW, fit.fitted]);
  const applyPan = useCallback(
    (dx: number, dy: number) => {
      setPan((prev) => {
        const container = containerRef.current;
        if (!container) return prev;
        const cw = container.clientWidth;
        const ch = container.clientHeight;
        const contentW = bounds.maxX - bounds.minX;
        const contentH = bounds.maxY - bounds.minY;
        // Allow panning to show all content but not past it
        // A fitted map is whole in its box: it never pans sideways (Astra).
        const maxPanX = fit.fitted ? 0 : Math.max(0, (contentW - cw) / 2 + 80);
        const maxPanY = fit.fitted ? 0 : Math.max(0, (contentH - ch) / 2 + 80);
        return {
          x: clamp(prev.x + dx, -maxPanX, maxPanX),
          y: clamp(prev.y + dy, -maxPanY, maxPanY),
        };
      });
    },
    [bounds, fit.fitted],
  );

  // ── SVG dimensions ──
  const svgW = bounds.maxX - bounds.minX;
  const svgH = bounds.maxY - bounds.minY;

  // ── Node map for lookups ──
  const nodeMap = useMemo(() => {
    const m = new Map<string, GraphNode>();
    for (const n of nodes) m.set(n.id, n);
    return m;
  }, [nodes]);

  // ── Keyboard handler ──
  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      // Shift+Arrow: pan
      if (event.shiftKey) {
        switch (event.key) {
          case "ArrowLeft":
            event.preventDefault();
            applyPan(PAN_STEP, 0);
            return;
          case "ArrowRight":
            event.preventDefault();
            applyPan(-PAN_STEP, 0);
            return;
          case "ArrowUp":
            event.preventDefault();
            applyPan(0, PAN_STEP);
            return;
          case "ArrowDown":
            event.preventDefault();
            applyPan(0, -PAN_STEP);
            return;
        }
        return;
      }

      // Arrow: navigate between nodes
      const currentNode = selected ? nodeMap.get(selected) : null;
      if (!currentNode) {
        // Select home node if nothing selected
        if (
          event.key === "ArrowDown" ||
          event.key === "ArrowUp" ||
          event.key === "ArrowLeft" ||
          event.key === "ArrowRight"
        ) {
          const home = nodes.find((n) => n.home) ?? nodes[0];
          if (home) {
            event.preventDefault();
            select(home.id);
            nodeRefs.current[home.id]?.focus();
          }
        }
        return;
      }

      const dirMap: Record<string, "left" | "right" | "up" | "down"> = {
        ArrowLeft: "left",
        ArrowRight: "right",
        ArrowUp: "up",
        ArrowDown: "down",
      };
      const dir = dirMap[event.key];
      if (dir) {
        event.preventDefault();
        const next = nearestInDirection(nodes, currentNode, dir);
        if (next) {
          select(next.id);
          nodeRefs.current[next.id]?.focus();
        }
        return;
      }

      // Home key: jump to home node
      if (event.key === "Home") {
        event.preventDefault();
        const home = nodes.find((n) => n.home) ?? nodes[0];
        if (home) {
          select(home.id);
          nodeRefs.current[home.id]?.focus();
          setPan({ x: 0, y: 0 });
        }
      }
    },
    [selected, nodeMap, nodes, select, applyPan],
  );

  // ── Pointer pan (drag) ──
  const dragging = useRef(false);
  const lastPointer = useRef({ x: 0, y: 0 });

  const onPointerDown = useCallback((e: React.PointerEvent) => {
    // Only pan when clicking the background, not a node
    if ((e.target as HTMLElement).closest("[data-topology-node]")) return;
    dragging.current = true;
    lastPointer.current = { x: e.clientX, y: e.clientY };
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
  }, []);

  const onPointerMove = useCallback(
    (e: React.PointerEvent) => {
      if (!dragging.current) return;
      const dx = e.clientX - lastPointer.current.x;
      const dy = e.clientY - lastPointer.current.y;
      lastPointer.current = { x: e.clientX, y: e.clientY };
      applyPan(dx, dy);
    },
    [applyPan],
  );

  const onPointerUp = useCallback(() => {
    dragging.current = false;
  }, []);

  // ── Auto-center on mount ──
  useEffect(() => {
    setPan({ x: 0, y: 0 });
  }, [nodes.length]);

  // ── Reduce motion check ──
  const reduceMotion = useRef(false);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    reduceMotion.current = mq.matches;
    const handler = (e: MediaQueryListEvent) => {
      reduceMotion.current = e.matches;
    };
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  // ── Offset: anchor on home node (center-left) or content center ──
  const offset = useMemo(() => {
    const home = nodes.find((n) => n.home);
    if (home) {
      // Place home node at ~30% from the left, vertically centered
      return {
        x: -(home.x + nodeW / 2) + 60,
        y: -(home.y + NODE_H / 2),
      };
    }
    return {
      x: -(bounds.minX + bounds.maxX) / 2,
      y: -(bounds.minY + bounds.maxY) / 2,
    };
  }, [bounds, nodes, nodeW]);

  return (
    <div
      ref={containerRef}
      className="surface-topology"
      role="group"
      aria-label={ariaLabel}
      onKeyDown={handleKeyDown}
      data-testid="topology-surface"
    >
      <div className="surface-topology-map-area">
      <div
        ref={viewportRef}
        className="surface-topology-viewport"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        style={{
          // PHILO-17 (the desk sweep): the anchor holds, but the map never
          // starts cut: the content's right edge stays inside the view when
          // it fits (min), and its left edge always does (max). A map wider
          // than the view still pans.
          // A fitted map sits whole in its box: centred across, from the top,
          // and the box is as tall as the map.
          transform: fit.fitted
            ? `translate(calc((100% - ${bounds.maxX - bounds.minX}px) / 2 - ${bounds.minX}px), ${FIT_MARGIN - bounds.minY}px)`
            : `translate(calc(max(${8 - bounds.minX}px, min(50% + ${offset.x}px, 100% - ${bounds.maxX + 8}px)) + ${pan.x}px), calc(50% + ${pan.y + offset.y}px))`,
          minHeight: fit.fitted ? bounds.maxY - bounds.minY + 2 * FIT_MARGIN : undefined,
        }}
      >
        {/* SVG edge layer */}
        <svg
          className="surface-topology-edges"
          viewBox={`${bounds.minX} ${bounds.minY} ${svgW} ${svgH}`}
          width={svgW}
          height={svgH}
          style={{
            position: "absolute",
            left: bounds.minX,
            top: bounds.minY,
          }}
          aria-hidden="true"
        >
          {flows.map((flow) => {
            const from = nodeMap.get(flow.from);
            const to = nodeMap.get(flow.to);
            if (!from || !to) return null;
            const isSelected = selected === flow.from || selected === flow.to;
            return (
              <g key={flow.id} data-flow={flow.id}>
                <path
                  className="surface-topology-edge"
                  d={edgePath(from, to, nodeW, fit.mode)}
                  data-active={isSelected || undefined}
                />
              </g>
            );
          })}
        </svg>

        {/* Flow labels */}
        {flows.map((flow) => {
          const from = nodeMap.get(flow.from);
          const to = nodeMap.get(flow.to);
          if (!from || !to || !flow.labels.length) return null;
          const at = labelPlace(from, to, nodeW, fit.mode);
          return (
            <div
              key={`label-${flow.id}`}
              className="surface-topology-flow-label"
              data-wrap={at.maxWidth ? "" : undefined}
              data-centred={at.centred ? "" : undefined}
              style={{
                left: at.left,
                top: at.top,
                maxWidth: at.maxWidth,
              }}
              aria-hidden="true"
            >
              {flow.labels.length <= 2
                ? flow.labels.join(", ")
                : `${flow.labels[0]} +${flow.labels.length - 1}`}
            </div>
          );
        })}

        {/* DOM nodes */}
        {nodes.map((node) => {
          const isSelected = selected === node.id;
          const stateValue = node.state ?? "idle";
          return (
            <Button
              variant="chrome"
              key={node.id}
              ref={(el) => {
                nodeRefs.current[node.id] = el;
              }}
              className="surface-topology-node"
              data-topology-node=""
              data-home={node.home || undefined}
              data-selected={isSelected || undefined}
              data-state={stateValue}
              style={{
                left: node.x,
                top: node.y,
                width: nodeW,
                minHeight: NODE_H,
              }}
              tabIndex={isSelected ? 0 : -1}
              aria-label={node.label}
              aria-pressed={isSelected}
              onClick={() => select(node.id)}
            >
              <span className="surface-topology-node-header">
                {node.home ? (
                  <span className="surface-topology-home-badge" aria-hidden="true">
                    {"*"}
                  </span>
                ) : null}
                <span className="surface-topology-node-label">
                  {node.label}
                </span>
                <span
                  className="surface-topology-node-state"
                  data-state={stateValue}
                  aria-hidden="true"
                >
                  {STATE_ICONS[stateValue] ?? STATE_ICONS.idle}
                </span>
              </span>
              {node.children ? (
                <span className="surface-topology-node-content">
                  {node.children}
                </span>
              ) : null}
            </Button>
          );
        })}
      </div>

      {/* Inspector slot (beside the viewport, inside the map-area flex row) */}
      {inspectorSlot && selected ? (
        <aside
          className="surface-topology-inspector"
          aria-label="Node inspector"
          aria-live="polite"
        >
          {inspectorSlot}
        </aside>
      ) : null}
      </div>{/* end map-area */}

      {/* Add node slot: toolbar row below the map area, never overlaps inspector */}
      {addNodeSlot ? (
        <div className="surface-topology-toolbar">{addNodeSlot}</div>
      ) : null}
    </div>
  );
}
