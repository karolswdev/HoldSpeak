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
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
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

/** Compute the bounding box of all nodes + padding. */
function contentBounds(nodes: GraphNode[]): {
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
    if (n.x + NODE_W > maxX) maxX = n.x + NODE_W;
    if (n.y + NODE_H > maxY) maxY = n.y + NODE_H;
  }
  const pad = 80;
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
): string {
  const x1 = from.x + NODE_W / 2;
  const y1 = from.y + NODE_H / 2;
  const x2 = to.x + NODE_W / 2;
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
): { x: number; y: number } {
  return {
    x: (from.x + to.x + NODE_W) / 2,
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
  nodes,
  flows,
  selectedId,
  onSelect,
  inspectorSlot,
  addNodeSlot,
  ariaLabel = "Topology map",
}: TopologySurfaceProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewportRef = useRef<HTMLDivElement>(null);
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
  const bounds = useMemo(() => contentBounds(nodes), [nodes]);
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
        const maxPanX = Math.max(0, (contentW - cw) / 2 + 80);
        const maxPanY = Math.max(0, (contentH - ch) / 2 + 80);
        return {
          x: clamp(prev.x + dx, -maxPanX, maxPanX),
          y: clamp(prev.y + dy, -maxPanY, maxPanY),
        };
      });
    },
    [bounds],
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
        x: -(home.x + NODE_W / 2) + 60,
        y: -(home.y + NODE_H / 2),
      };
    }
    return {
      x: -(bounds.minX + bounds.maxX) / 2,
      y: -(bounds.minY + bounds.maxY) / 2,
    };
  }, [bounds, nodes]);

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
          transform: `translate(calc(50% + ${pan.x + offset.x}px), calc(50% + ${pan.y + offset.y}px))`,
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
                  d={edgePath(from, to)}
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
          const mid = edgeMidpoint(from, to);
          return (
            <div
              key={`label-${flow.id}`}
              className="surface-topology-flow-label"
              style={{
                left: mid.x,
                top: mid.y,
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
            <button
              key={node.id}
              ref={(el) => {
                nodeRefs.current[node.id] = el;
              }}
              type="button"
              className="surface-topology-node"
              data-topology-node=""
              data-home={node.home || undefined}
              data-selected={isSelected || undefined}
              data-state={stateValue}
              style={{
                left: node.x,
                top: node.y,
                width: NODE_W,
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
            </button>
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
