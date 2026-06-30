// HS-69-10: the Workbench canvas — a pannable/zoomable dot-grid world with
// typed, draggable Signal node cards joined by type-colored SVG bezier cables.
// Pure vanilla (Pointer Events), no graph lib (the Phase-68 decision): SVG
// `<path>` cables + HTML node cards in ONE transformed world layer, so wires and
// nodes never desync. The dot grid is a CSS background on the viewport, synced
// to pan/zoom in JS (no per-dot DOM).

import { PORT_TYPE, graphFromWorkflow, loadLayout, saveLayout } from "./model.js";

const SVG_NS = "http://www.w3.org/2000/svg";
const GLYPHS = {
  transcript: "M4 6h16M4 10h16M4 14h10M4 18h7",
  pin: "M12 17v5M9 3h6l-1 6 3 3H7l3-3-1-6z",
  select: "M4 4h6M14 4h6M4 20h6M14 20h6M4 4v6M20 4v6M4 14v6M20 14v6",
  eye: "M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z",
  doc: "M7 3h7l4 4v14H7zM14 3v4h4",
  check: "M5 13l4 4L19 7",
  pen: "M4 20l4-1 11-11-3-3L5 16zM14 5l3 3",
  filter: "M3 5h18l-7 8v6l-4-2v-4z",
  spark: "M12 3v4M12 17v4M3 12h4M17 12h4M6 6l3 3M15 15l3 3M18 6l-3 3M9 15l-3 3",
  out: "M5 12h12M13 6l6 6-6 6",
};

function glyphSvg(name) {
  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("fill", "none");
  svg.setAttribute("stroke", "currentColor");
  svg.setAttribute("stroke-width", "2");
  svg.setAttribute("stroke-linecap", "round");
  svg.setAttribute("stroke-linejoin", "round");
  svg.setAttribute("aria-hidden", "true");
  const p = document.createElementNS(SVG_NS, "path");
  p.setAttribute("d", GLYPHS[name] || GLYPHS.spark);
  svg.appendChild(p);
  return svg;
}

// the iPad cable math: a horizontal-tangent cubic, control offset max(46,|dx|*0.45)
function cablePath(x0, y0, x1, y1) {
  const c = Math.max(46, Math.abs(x1 - x0) * 0.45);
  return `M ${x0} ${y0} C ${x0 + c} ${y0}, ${x1 - c} ${y1}, ${x1} ${y1}`;
}

export function mountWorkbench(root, workflow) {
  const viewport = root.querySelector("[data-wb-canvas]");
  const world = root.querySelector("[data-wb-world]");
  const svg = root.querySelector("[data-wb-cables]");
  if (!viewport || !world || !svg) return null;

  const state = { panX: 60, panY: 20, z: 1 };
  const layout = loadLayout(workflow.id) || {};
  const { nodes, edges } = graphFromWorkflow(workflow, layout);
  const nodeEls = new Map();
  const edgeEls = new Map();
  let onSelect = null;

  function applyTransform() {
    world.style.transform = `translate(${state.panX}px, ${state.panY}px) scale(${state.z})`;
    const step = 34 * state.z; // the iPad's 34pt dot step
    viewport.style.backgroundSize = `${step}px ${step}px`;
    viewport.style.backgroundPosition = `${state.panX}px ${state.panY}px`;
  }

  function portPos(node, side) {
    const el = nodeEls.get(node.id);
    const w = el ? el.offsetWidth : 200;
    const h = el ? el.offsetHeight : 64;
    return { x: node.x + (side === "out" ? w : 0), y: node.y + h / 2 };
  }

  function layoutCable(edge) {
    const from = nodes.find((n) => n.id === edge.from);
    const to = nodes.find((n) => n.id === edge.to);
    if (!from || !to) return;
    const a = portPos(from, "out");
    const b = portPos(to, "in");
    const path = edgeEls.get(edge.id);
    if (path) path.setAttribute("d", cablePath(a.x, a.y, b.x, b.y));
  }

  function layoutCablesFor(nodeId) {
    for (const e of edges) if (e.from === nodeId || e.to === nodeId) layoutCable(e);
  }

  function renderNode(node) {
    const el = document.createElement("div");
    el.className = `wb-node signal-card is-pressable role-${node.role}`;
    el.tabIndex = 0;
    el.dataset.nodeId = node.id;
    el.setAttribute("role", "group");
    el.setAttribute("aria-label", `${node.title} node`);

    const head = document.createElement("div");
    head.className = "wb-node-head";
    const chip = document.createElement("span");
    chip.className = "wb-node-glyph glyph-chip";
    chip.style.setProperty("--chip-size", "30px");
    chip.appendChild(glyphSvg(node.glyph));
    const title = document.createElement("span");
    title.className = "wb-node-title";
    title.textContent = node.title;
    head.append(chip, title);
    el.appendChild(head);

    if (node.subtitle) {
      const sub = document.createElement("p");
      sub.className = "wb-node-sub";
      sub.textContent = node.subtitle;
      el.appendChild(sub);
    }

    // typed port dots
    if (node.role !== "source") {
      const inDot = document.createElement("span");
      inDot.className = "wb-port wb-port-in";
      inDot.style.background = (PORT_TYPE[node.inType] || PORT_TYPE.text).color;
      el.appendChild(inDot);
    }
    if (node.role !== "output") {
      const outDot = document.createElement("span");
      outDot.className = "wb-port wb-port-out";
      outDot.style.background = (PORT_TYPE[node.outType] || PORT_TYPE.text).color;
      el.appendChild(outDot);
    }

    el.style.left = `${node.x}px`;
    el.style.top = `${node.y}px`;
    world.appendChild(el);
    nodeEls.set(node.id, el);
    wireNodeDrag(node, el);
  }

  function renderEdge(edge) {
    const path = document.createElementNS(SVG_NS, "path");
    const color = (PORT_TYPE[edge.type] || PORT_TYPE.text).color;
    path.setAttribute("class", "wb-cable");
    path.setAttribute("stroke", color);
    path.setAttribute("fill", "none");
    path.dataset.edgeId = edge.id;
    svg.appendChild(path);
    edgeEls.set(edge.id, path);
  }

  // ── interactions ──────────────────────────────────────────────────────
  function wireNodeDrag(node, el) {
    let dragging = false;
    let sx = 0;
    let sy = 0;
    let ox = 0;
    let oy = 0;
    el.addEventListener("pointerdown", (e) => {
      if (e.button !== 0) return;
      e.stopPropagation(); // don't pan
      dragging = true;
      sx = e.clientX;
      sy = e.clientY;
      ox = node.x;
      oy = node.y;
      el.setPointerCapture(e.pointerId);
      el.classList.add("is-dragging");
    });
    el.addEventListener("pointermove", (e) => {
      if (!dragging) return;
      node.x = ox + (e.clientX - sx) / state.z; // screen px → world px
      node.y = oy + (e.clientY - sy) / state.z;
      el.style.left = `${node.x}px`;
      el.style.top = `${node.y}px`;
      layoutCablesFor(node.id);
    });
    const end = (e) => {
      if (!dragging) return;
      dragging = false;
      el.classList.remove("is-dragging");
      try { el.releasePointerCapture(e.pointerId); } catch (_e) { /* ignore */ }
      layout[node.id] = { x: node.x, y: node.y };
      saveLayout(workflow.id, layout);
    };
    el.addEventListener("pointerup", end);
    el.addEventListener("pointercancel", end);
    el.addEventListener("click", () => onSelect && onSelect(node));
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter") onSelect && onSelect(node);
    });
  }

  function wirePan() {
    let panning = false;
    let sx = 0;
    let sy = 0;
    let opx = 0;
    let opy = 0;
    viewport.addEventListener("pointerdown", (e) => {
      if (e.button !== 0) return;
      panning = true;
      sx = e.clientX;
      sy = e.clientY;
      opx = state.panX;
      opy = state.panY;
      viewport.setPointerCapture(e.pointerId);
      viewport.classList.add("is-panning");
    });
    viewport.addEventListener("pointermove", (e) => {
      if (!panning) return;
      state.panX = opx + (e.clientX - sx);
      state.panY = opy + (e.clientY - sy);
      applyTransform();
    });
    const end = (e) => {
      panning = false;
      viewport.classList.remove("is-panning");
      try { viewport.releasePointerCapture(e.pointerId); } catch (_e) { /* ignore */ }
    };
    viewport.addEventListener("pointerup", end);
    viewport.addEventListener("pointercancel", end);
  }

  function wireZoom() {
    viewport.addEventListener("wheel", (e) => {
      e.preventDefault();
      const rect = viewport.getBoundingClientRect();
      const cx = e.clientX - rect.left;
      const cy = e.clientY - rect.top;
      // world point under the cursor before the zoom
      const wx = (cx - state.panX) / state.z;
      const wy = (cy - state.panY) / state.z;
      const factor = Math.exp(-e.deltaY * 0.0015);
      const nz = Math.min(2.0, Math.max(0.4, state.z * factor));
      state.z = nz;
      // re-translate so the point under the cursor stays put
      state.panX = cx - wx * nz;
      state.panY = cy - wy * nz;
      applyTransform();
    }, { passive: false });
  }

  function fit() {
    state.panX = 60;
    state.panY = 20;
    state.z = 1;
    applyTransform();
  }

  // ── boot ──────────────────────────────────────────────────────────────
  for (const e of edges) renderEdge(e);
  for (const n of nodes) renderNode(n);
  applyTransform();
  requestAnimationFrame(() => { for (const e of edges) layoutCable(e); });
  wirePan();
  wireZoom();

  return {
    fit,
    onSelect: (fn) => { onSelect = fn; },
    state,
    nodes,
  };
}
