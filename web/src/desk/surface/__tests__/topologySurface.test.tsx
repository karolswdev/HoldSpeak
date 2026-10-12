/** TopologySurface contract suite — council codex section 2.6.
 *  Tests: nodes/edges render from a model, home node anchored, keyboard
 *  select/move between nodes, pan containment, reduced-motion honored,
 *  roving inside, inspector + add-node slots. */
import { render, screen, fireEvent, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import {
  TopologySurface,
  type GraphNode,
  type GraphFlow,
} from "../graph/TopologySurface";

const HOME: GraphNode = {
  id: "this_machine",
  label: "This Mac",
  home: true,
  state: "success",
  x: 100,
  y: 120,
  children: <span>MLX, llama.cpp</span>,
};

const ENDPOINT: GraphNode = {
  id: "lan-server",
  label: "LAN Server",
  home: false,
  state: "success",
  x: 380,
  y: 120,
  children: <span>qwen3.6</span>,
};

const UNREACHABLE: GraphNode = {
  id: "offline",
  label: "Offline Node",
  home: false,
  state: "unreachable",
  x: 380,
  y: 260,
};

const NODES: GraphNode[] = [HOME, ENDPOINT, UNREACHABLE];

const FLOWS: GraphFlow[] = [
  {
    id: "flow-1",
    from: "this_machine",
    to: "lan-server",
    labels: ["Chat & agents", "Speech recognition"],
  },
  {
    id: "flow-2",
    from: "this_machine",
    to: "offline",
    labels: ["Translation"],
  },
];

/* ──────────────────────────────────────────────────────────────────
   1. Nodes and edges render from model
   ────────────────────────────────────────────────────────────────── */

describe("TopologySurface — nodes render from model", () => {
  it("renders all nodes as buttons with aria-label", () => {
    render(<TopologySurface nodes={NODES} flows={FLOWS} />);
    for (const node of NODES) {
      expect(
        screen.getByRole("button", { name: node.label }),
      ).toBeInTheDocument();
    }
  });

  it("renders node children content", () => {
    render(<TopologySurface nodes={NODES} flows={FLOWS} />);
    expect(screen.getByText("MLX, llama.cpp")).toBeInTheDocument();
    expect(screen.getByText("qwen3.6")).toBeInTheDocument();
  });

  it("renders edges as SVG paths", () => {
    const { container } = render(
      <TopologySurface nodes={NODES} flows={FLOWS} />,
    );
    const paths = container.querySelectorAll(".surface-topology-edge");
    expect(paths.length).toBe(2);
  });

  it("renders flow labels", () => {
    render(<TopologySurface nodes={NODES} flows={FLOWS} />);
    // Bundled flow shows combined label
    expect(screen.getByText("Chat & agents, Speech recognition")).toBeInTheDocument();
    expect(screen.getByText("Translation")).toBeInTheDocument();
  });

  it("renders 3+ bundled labels as summary", () => {
    const manyFlows: GraphFlow[] = [
      {
        id: "many",
        from: "this_machine",
        to: "lan-server",
        labels: ["A", "B", "C", "D"],
      },
    ];
    render(<TopologySurface nodes={NODES} flows={manyFlows} />);
    expect(screen.getByText("A +3")).toBeInTheDocument();
  });
});

/* ──────────────────────────────────────────────────────────────────
   2. Home node anchored
   ────────────────────────────────────────────────────────────────── */

describe("TopologySurface — home node", () => {
  it("marks the home node with data-home", () => {
    const { container } = render(
      <TopologySurface nodes={NODES} flows={FLOWS} />,
    );
    const homeNode = container.querySelector("[data-home]");
    expect(homeNode).toBeTruthy();
    expect(homeNode?.getAttribute("aria-label")).toBe("This Mac");
  });

  it("renders a home badge inside the home node", () => {
    const { container } = render(
      <TopologySurface nodes={NODES} flows={FLOWS} />,
    );
    const badge = container.querySelector(".surface-topology-home-badge");
    expect(badge).toBeTruthy();
  });
});

/* ──────────────────────────────────────────────────────────────────
   3. Keyboard select and move between nodes
   ────────────────────────────────────────────────────────────────── */

describe("TopologySurface — keyboard navigation", () => {
  it("selects home node on first arrow key when nothing is selected", () => {
    const onSelect = vi.fn();
    const { container } = render(
      <TopologySurface nodes={NODES} flows={FLOWS} onSelect={onSelect} />,
    );
    const group = container.querySelector("[data-testid='topology-surface']")!;
    fireEvent.keyDown(group, { key: "ArrowRight" });
    expect(onSelect).toHaveBeenCalledWith("this_machine");
  });

  it("moves selection to the right on ArrowRight", () => {
    const onSelect = vi.fn();
    const { container } = render(
      <TopologySurface
        nodes={NODES}
        flows={FLOWS}
        selectedId="this_machine"
        onSelect={onSelect}
      />,
    );
    const group = container.querySelector("[data-testid='topology-surface']")!;
    fireEvent.keyDown(group, { key: "ArrowRight" });
    // Should select the nearest node to the right (lan-server at same y)
    expect(onSelect).toHaveBeenCalledWith("lan-server");
  });

  it("marks the selected node with data-selected", () => {
    const { container } = render(
      <TopologySurface
        nodes={NODES}
        flows={FLOWS}
        selectedId="lan-server"
      />,
    );
    const selected = container.querySelector("[data-selected]");
    expect(selected).toBeTruthy();
    expect(selected?.getAttribute("aria-label")).toBe("LAN Server");
  });

  it("Home key jumps to the home node", () => {
    const onSelect = vi.fn();
    const { container } = render(
      <TopologySurface
        nodes={NODES}
        flows={FLOWS}
        selectedId="offline"
        onSelect={onSelect}
      />,
    );
    const group = container.querySelector("[data-testid='topology-surface']")!;
    fireEvent.keyDown(group, { key: "Home" });
    expect(onSelect).toHaveBeenCalledWith("this_machine");
  });
});

/* ──────────────────────────────────────────────────────────────────
   4. Pan containment (Shift+Arrow)
   ────────────────────────────────────────────────────────────────── */

describe("TopologySurface — pan", () => {
  it("does not crash on Shift+Arrow pan", () => {
    const { container } = render(
      <TopologySurface nodes={NODES} flows={FLOWS} />,
    );
    const group = container.querySelector("[data-testid='topology-surface']")!;
    // Should not throw
    fireEvent.keyDown(group, { key: "ArrowRight", shiftKey: true });
    fireEvent.keyDown(group, { key: "ArrowLeft", shiftKey: true });
    fireEvent.keyDown(group, { key: "ArrowUp", shiftKey: true });
    fireEvent.keyDown(group, { key: "ArrowDown", shiftKey: true });
    expect(group).toBeInTheDocument();
  });
});

/* ──────────────────────────────────────────────────────────────────
   5. Reduced motion honored
   ────────────────────────────────────────────────────────────────── */

describe("TopologySurface — reduced motion", () => {
  it("uses CSS classes that map to token durations (not raw values)", () => {
    // This test verifies the component renders the correct class names
    // that the CSS file maps to token-based durations with reduced-motion
    // media queries.
    const { container } = render(
      <TopologySurface nodes={NODES} flows={FLOWS} />,
    );
    expect(container.querySelector(".surface-topology")).toBeTruthy();
    expect(container.querySelector(".surface-topology-viewport")).toBeTruthy();
  });
});

/* ──────────────────────────────────────────────────────────────────
   6. Roving tabindex inside
   ────────────────────────────────────────────────────────────────── */

describe("TopologySurface — roving tabindex", () => {
  it("selected node has tabIndex 0, others have -1", () => {
    const { container } = render(
      <TopologySurface
        nodes={NODES}
        flows={FLOWS}
        selectedId="lan-server"
      />,
    );
    const nodes = container.querySelectorAll("[data-topology-node]");
    for (const node of nodes) {
      if (node.getAttribute("aria-label") === "LAN Server") {
        expect(node.getAttribute("tabindex")).toBe("0");
      } else {
        expect(node.getAttribute("tabindex")).toBe("-1");
      }
    }
  });
});

/* ──────────────────────────────────────────────────────────────────
   7. Inspector slot
   ────────────────────────────────────────────────────────────────── */

describe("TopologySurface — inspector slot", () => {
  it("renders inspector slot when a node is selected", () => {
    render(
      <TopologySurface
        nodes={NODES}
        flows={FLOWS}
        selectedId="lan-server"
        inspectorSlot={<div>Inspector content</div>}
      />,
    );
    expect(screen.getByText("Inspector content")).toBeInTheDocument();
    expect(
      screen.getByRole("complementary", { name: "Node inspector" }),
    ).toBeInTheDocument();
  });

  it("hides inspector slot when no node is selected", () => {
    render(
      <TopologySurface
        nodes={NODES}
        flows={FLOWS}
        selectedId={null}
        inspectorSlot={<div>Inspector content</div>}
      />,
    );
    expect(screen.queryByText("Inspector content")).toBeNull();
  });
});

/* ──────────────────────────────────────────────────────────────────
   8. Add-node slot
   ────────────────────────────────────────────────────────────────── */

describe("TopologySurface — add-node slot", () => {
  it("renders the add-node slot", () => {
    render(
      <TopologySurface
        nodes={NODES}
        flows={FLOWS}
        addNodeSlot={<button>+ Add node</button>}
      />,
    );
    expect(
      screen.getByRole("button", { name: "+ Add node" }),
    ).toBeInTheDocument();
  });
});

/* ──────────────────────────────────────────────────────────────────
   9. State on nodes
   ────────────────────────────────────────────────────────────────── */

describe("TopologySurface — node states", () => {
  it("renders data-state on each node", () => {
    const { container } = render(
      <TopologySurface nodes={NODES} flows={FLOWS} />,
    );
    expect(container.querySelector('[data-state="success"]')).toBeTruthy();
    expect(container.querySelector('[data-state="unreachable"]')).toBeTruthy();
  });

  it("renders state icon glyph in the header", () => {
    const { container } = render(
      <TopologySurface nodes={NODES} flows={FLOWS} />,
    );
    const stateIcons = container.querySelectorAll(
      ".surface-topology-node-state",
    );
    expect(stateIcons.length).toBe(3);
  });
});

/* ──────────────────────────────────────────────────────────────────
   10. Token compliance
   ────────────────────────────────────────────────────────────────── */

describe("TopologySurface — token compliance", () => {
  it("uses surface-topology class name", () => {
    const { container } = render(
      <TopologySurface nodes={NODES} flows={FLOWS} />,
    );
    expect(container.querySelector(".surface-topology")).toBeTruthy();
  });

  it("has role=group with aria-label", () => {
    render(
      <TopologySurface
        nodes={NODES}
        flows={FLOWS}
        ariaLabel="Infrastructure map"
      />,
    );
    expect(
      screen.getByRole("group", { name: "Infrastructure map" }),
    ).toBeInTheDocument();
  });

  it("renders edges SVG as aria-hidden", () => {
    const { container } = render(
      <TopologySurface nodes={NODES} flows={FLOWS} />,
    );
    const svg = container.querySelector(".surface-topology-edges");
    expect(svg?.getAttribute("aria-hidden")).toBe("true");
  });
});

/* ──────────────────────────────────────────────────────────────────
   11. Controlled vs uncontrolled selection
   ────────────────────────────────────────────────────────────────── */

describe("TopologySurface — selection modes", () => {
  it("works in uncontrolled mode (click to select)", () => {
    const { container } = render(
      <TopologySurface nodes={NODES} flows={FLOWS} />,
    );
    const node = screen.getByRole("button", { name: "LAN Server" });
    fireEvent.click(node);
    expect(node.getAttribute("data-selected")).toBe("true");
  });

  it("works in controlled mode", () => {
    const onSelect = vi.fn();
    render(
      <TopologySurface
        nodes={NODES}
        flows={FLOWS}
        selectedId="this_machine"
        onSelect={onSelect}
      />,
    );
    const node = screen.getByRole("button", { name: "LAN Server" });
    fireEvent.click(node);
    expect(onSelect).toHaveBeenCalledWith("lan-server");
  });
});

/* ──────────────────────────────────────────────────────────────────
   12. Active edges highlight on selection
   ────────────────────────────────────────────────────────────────── */

describe("TopologySurface — edge highlighting", () => {
  it("marks edges connected to the selected node as active", () => {
    const { container } = render(
      <TopologySurface
        nodes={NODES}
        flows={FLOWS}
        selectedId="lan-server"
      />,
    );
    const activePaths = container.querySelectorAll(
      ".surface-topology-edge[data-active]",
    );
    expect(activePaths.length).toBeGreaterThan(0);
  });
});

describe("TopologySurface — fit to a narrow box (PHILO-17, owner: shrink it)", () => {
  it("keeps the layout when it fits, and brings the nodes closer and narrower when it does not", async () => {
    const { fitLayout } = await import("../graph/TopologySurface");
    const nodes = [
      { id: "home", label: "This Mac", home: true, x: 40, y: 100 },
      { id: "lan", label: "LAN Server", x: 360, y: 35 },
    ];
    expect(fitLayout(nodes, 640)).toMatchObject({ fitted: false, nodeW: 180 });
    const narrow = fitLayout(nodes, 363);
    expect(narrow.fitted).toBe(true);
    expect(narrow.nodeW).toBeGreaterThanOrEqual(128);
    const right = Math.max(...narrow.nodes.map((n) => n.x)) + narrow.nodeW - Math.min(...narrow.nodes.map((n) => n.x));
    expect(right).toBeLessThanOrEqual(363 - 48);
    // Astra on #1113: two cards side by side would sit closer than a label
    // needs, so the narrow map stacks, one card per row, never touching.
    expect(narrow.mode).toBe("stack");
    const ys = narrow.nodes.map((n) => n.y).sort((a, b) => a - b);
    for (let i = 1; i < ys.length; i++) expect(ys[i] - ys[i - 1]).toBeGreaterThanOrEqual(80 + 40);
  });
});
