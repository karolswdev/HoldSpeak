/** TopologyMapView — the map that runs the desk.
 *
 *  HS-156-06: the advanced layer opens on a MAP, not a table.
 *  This Mac as the home node, endpoints as nodes, the seven job groups
 *  as flows. Add-node opens the EXISTING connect grammar in-world.
 *  Selecting a node shows its models + jobs and re-points a flow
 *  through the existing assignments editor, in place.
 *
 *  Every gesture performs the REAL operation — no read-only mode.
 *  Built FROM the library: TopologySurface, StateChip, ActionNotice,
 *  Popover, Disclosure, ProvenanceChip. No one-off furniture.
 */
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { readableError, newDeliveryId } from "../../lib/api";
import {
  TopologySurface,
  type GraphNode,
  type GraphFlow,
  StateChip,
  ActionNotice,
  Disclosure,
  SurfaceState,
  StringGadget,
  EgressChip,
} from "../../desk/surface";
import { Button } from "../../components/signal/Signal";
import {
  getTopologyFull,
  nodeChipState,
  nodeStateLabel,
  nodeKindLabel,
  type TopologyNodeWire,
  type TopologyWire,
} from "./topologyService";
import {
  getAssignmentEditor,
  saveAssignment,
  type AssignmentSummary,
  type AssignmentSummaryRow,
  type AssignmentEditorProjection,
} from "./assignmentExperience";
import {
  defineEndpoint,
  connectHostedModel,
  type ModelLibraryProjection,
} from "./modelLibrary";
import "./topologyMap.css";

// ── Layout: radial positioning ──────────────────────────────────────

const HOME_X = 40;
const HOME_Y = 100;
const NODE_SPACING_X = 320;
const NODE_SPACING_Y = 130;

function layoutNodes(wireNodes: TopologyNodeWire[]): GraphNode[] {
  const home = wireNodes.find((n) => n.home);
  const others = wireNodes.filter((n) => !n.home);
  const result: GraphNode[] = [];

  if (home) {
    result.push({
      id: home.id,
      label: home.label,
      home: true,
      state: nodeChipState(home.state),
      x: HOME_X,
      y: HOME_Y,
      children: (
        <NodeContent node={home} />
      ),
    });
  }

  // Place other nodes to the right, stacked vertically
  others.forEach((node, i) => {
    result.push({
      id: node.id,
      label: node.label,
      home: false,
      state: nodeChipState(node.state),
      x: HOME_X + NODE_SPACING_X,
      y: HOME_Y + (i - (others.length - 1) / 2) * NODE_SPACING_Y,
      children: (
        <NodeContent node={node} />
      ),
    });
  });

  return result;
}

function NodeContent({ node }: { node: TopologyNodeWire }) {
  return (
    <>
      <span className="topology-node-kind">{nodeKindLabel(node.kind)}</span>
      {node.runtimes?.length ? (
        <span className="topology-node-runtimes">
          {node.runtimes
            .filter((r) => r.state === "available")
            .map((r) => r.id.replace(/_v\d+$/, "").replace(/_/g, " "))
            .join(", ")}
        </span>
      ) : null}
      {node.models?.length ? (
        <span className="topology-node-models">
          {node.models.length <= 2
            ? node.models.join(", ")
            : `${node.models[0]} +${node.models.length - 1}`}
        </span>
      ) : null}
      {node.base_url ? (
        <span className="topology-node-url">{node.base_url}</span>
      ) : null}
    </>
  );
}

// ── Flow bundling ───────────────────────────────────────────────────

function bundleFlows(
  topology: TopologyWire,
): GraphFlow[] {
  // Group flows by (from, to) pair. All flows come FROM this_machine.
  const bundles = new Map<string, GraphFlow>();
  for (const flow of topology.flows) {
    const key = `this_machine->${flow.target_node_id}`;
    const existing = bundles.get(key);
    if (existing) {
      existing.labels.push(flow.group_label);
    } else {
      bundles.set(key, {
        id: key,
        from: "this_machine",
        to: flow.target_node_id,
        labels: [flow.group_label],
      });
    }
  }
  return [...bundles.values()];
}

// ── Inspector ───────────────────────────────────────────────────────

function NodeInspector({
  node,
  assignments,
  library,
  onRepoint,
}: {
  node: TopologyNodeWire;
  assignments: AssignmentSummary;
  library: ModelLibraryProjection;
  onRepoint: () => void;
}) {
  // Find flows assigned to this node
  const nodeJobs = assignments.rows.filter((row) => {
    if (!row.assignment?.entries?.length) return false;
    // Check if any entry in the chain targets this node's profile
    return row.assignment.entries.some(
      (entry) =>
        entry.profile_id === node.id ||
        (node.id === "this_machine" &&
          (entry.boundary === "same_device" ||
            entry.boundary === "local")),
    );
  });

  // Find models on this node
  const nodeModels = library.rows.filter((row) => {
    if (node.id === "this_machine") {
      return row.source === "installed" || row.source === "detected";
    }
    return row.id.includes(node.id);
  });

  return (
    <div className="topology-inspector-body">
      <div className="topology-inspector-header">
        <span className="topology-inspector-label">{node.label}</span>
        <StateChip
          state={nodeChipState(node.state)}
          label={nodeStateLabel(node.state)}
        />
      </div>

      <span className="topology-inspector-kind">
        {nodeKindLabel(node.kind)}
      </span>

      {node.base_url ? (
        <span className="topology-inspector-url">{node.base_url}</span>
      ) : null}

      {nodeModels.length > 0 ? (
        <Disclosure label="Models" defaultOpen token={`${nodeModels.length}`}>
          <ul className="topology-inspector-list">
            {nodeModels.map((m) => (
              <li key={m.id}>
                <span>{m.label}</span>
                <small>{m.status}</small>
              </li>
            ))}
          </ul>
        </Disclosure>
      ) : null}

      {nodeJobs.length > 0 ? (
        <Disclosure label="Jobs" defaultOpen token={`${nodeJobs.length}`}>
          <ul className="topology-inspector-list">
            {nodeJobs.map((j) => (
              <li key={j.id}>
                <span>{j.label}</span>
                {j.repair ? <small>{j.repair}</small> : null}
              </li>
            ))}
          </ul>
        </Disclosure>
      ) : null}

      {node.state === "unreachable" || node.state === "unavailable" ? (
        <ActionNotice tone="warn" action={{ label: "Fix", onClick: onRepoint }}>
          {node.label} is {nodeStateLabel(node.state).toLowerCase()}
        </ActionNotice>
      ) : null}

      <button
        type="button"
        className="topology-inspector-repoint"
        onClick={onRepoint}
      >
        Re-point a flow
      </button>
    </div>
  );
}

// ── Re-point flow ───────────────────────────────────────────────────

function RepointPanel({
  row,
  onDone,
}: {
  row: AssignmentSummaryRow;
  onDone: () => void;
}) {
  const [editor, setEditor] = useState<AssignmentEditorProjection | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedCandidate, setSelectedCandidate] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!row.editor_capability_id) return;
    setLoading(true);
    setError("");
    const scope =
      row.id === "global"
        ? ({ kind: "global" } as const)
        : ({ kind: "group", group_id: row.id } as const);
    getAssignmentEditor(scope, row.editor_capability_id)
      .then((ed) => {
        setEditor(ed);
        // Pre-select the current assignment if any
        if (ed.configured_assignment?.entries?.length) {
          setSelectedCandidate(ed.configured_assignment.entries[0].profile_id);
        }
      })
      .catch((e) => setError(readableError(e)))
      .finally(() => setLoading(false));
  }, [row]);

  const doSave = async () => {
    if (!editor || !selectedCandidate) return;
    setSaving(true);
    try {
      const candidate = editor.candidates.find(
        (c) => c.profile_id === selectedCandidate,
      );
      if (!candidate) return;
      await saveAssignment(
        editor.scope,
        editor.draft_base_revision,
        [{ profile_id: candidate.profile_id, profile_revision: candidate.profile_revision }],
        editor.retry_policy.default_id,
      );
      onDone();
    } catch (e) {
      setError(readableError(e));
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <SurfaceState loading />;
  if (error) return <SurfaceState error={error} />;
  if (!editor) return null;

  return (
    <div className="topology-repoint" data-testid="topology-repoint">
      <span className="topology-repoint-label">
        Re-point: {row.label}
      </span>
      <div className="topology-repoint-candidates" role="radiogroup" aria-label={`Candidates for ${row.label}`}>
        {editor.candidates.map((c) => (
          <label key={c.profile_id} className="topology-repoint-candidate">
            <input
              type="radio"
              name="repoint-candidate"
              value={c.profile_id}
              checked={selectedCandidate === c.profile_id}
              onChange={() => setSelectedCandidate(c.profile_id)}
            />
            <span>{c.label}</span>
            <small>{c.boundary} · {c.readiness}</small>
          </label>
        ))}
      </div>
      <div className="topology-repoint-actions">
        <Button
          variant="primary"
          loading={saving}
          disabled={saving || !selectedCandidate}
          onClick={() => void doSave()}
        >
          Assign
        </Button>
      </div>
    </div>
  );
}

// ── Add node (connect grammar — in-world via Disclosure, no modal) ──

function AddNodePanel({
  onAdded,
}: {
  onAdded: () => void;
}) {
  const [face, setFace] = useState<"choices" | "endpoint" | "hosted">("choices");
  const [endpoint, setEndpoint] = useState({ label: "", url: "", model: "" });
  const [hosted, setHosted] = useState({ label: "", model: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const secretRef = useRef<HTMLInputElement>(null);

  const reset = () => {
    setFace("choices");
    setEndpoint({ label: "", url: "", model: "" });
    setHosted({ label: "", model: "" });
    setError("");
  };

  const submitEndpoint = async () => {
    if (!endpoint.label.trim() || !endpoint.url.trim() || !endpoint.model.trim()) {
      setError("Name, endpoint, and model are required.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const key = secretRef.current?.value ?? "";
      const pid = `library-${endpoint.label.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 75)}`;
      await defineEndpoint(
        {
          request_id: newDeliveryId(),
          profile_id: pid,
          expected_profile_revision: 0,
          label: endpoint.label.trim(),
          provider_family: "openai_compatible",
          model: endpoint.model.trim(),
          endpoint: endpoint.url.trim(),
          requires_key: Boolean(key.trim()),
        },
        key.trim() || null,
      );
      reset();
      onAdded();
    } catch (e) {
      setError(readableError(e));
    } finally {
      setBusy(false);
    }
  };

  const submitHosted = async () => {
    if (!hosted.label.trim() || !hosted.model.trim()) {
      setError("Name, model, and key are required.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const key = secretRef.current?.value ?? "";
      const pid = `library-${hosted.label.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 75)}`;
      await connectHostedModel(
        {
          request_id: newDeliveryId(),
          profile_id: pid,
          expected_profile_revision: 0,
          label: hosted.label.trim(),
          provider_family: "openrouter",
          model: hosted.model.trim(),
          requires_key: true,
        },
        key || null,
      );
      reset();
      onAdded();
    } catch (e) {
      setError(readableError(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="topology-add-node-body" data-testid="topology-add-node">
      {face === "choices" ? (
        <div className="topology-add-choices">
          <span className="topology-add-title">Add node</span>
          <button type="button" onClick={() => setFace("endpoint")} data-testid="add-endpoint">
            Define endpoint
          </button>
          <button type="button" onClick={() => setFace("hosted")} data-testid="add-hosted">
            Connect hosted
          </button>
        </div>
      ) : face === "endpoint" ? (
        <div className="topology-add-form">
          <span className="topology-add-title">Define endpoint</span>
          <StringGadget label="Name" value={endpoint.label} onChange={(v) => setEndpoint((c) => ({ ...c, label: v }))} placeholder="My server" />
          <StringGadget label="Endpoint" value={endpoint.url} onChange={(v) => setEndpoint((c) => ({ ...c, url: v }))} placeholder="http://192.168.1.43:8080/v1" />
          <StringGadget label="Model" value={endpoint.model} onChange={(v) => setEndpoint((c) => ({ ...c, model: v }))} placeholder="model-name" />
          <label className="topology-add-secret">
            <span>Key (optional)</span>
            <input ref={secretRef} type="password" autoComplete="new-password" aria-label="Provider key" />
          </label>
          {error ? <ActionNotice tone="danger">{error}</ActionNotice> : null}
          <div className="topology-add-actions">
            <button type="button" onClick={() => setFace("choices")}>Back</button>
            <Button variant="primary" loading={busy} disabled={busy} onClick={() => void submitEndpoint()}>
              Add
            </Button>
          </div>
        </div>
      ) : (
        <div className="topology-add-form">
          <span className="topology-add-title">Connect hosted</span>
          <EgressChip label="Egress" scope="cloud" title="Request leaves this hub." />
          <StringGadget label="Name" value={hosted.label} onChange={(v) => setHosted((c) => ({ ...c, label: v }))} placeholder="Provider" />
          <StringGadget label="Model" value={hosted.model} onChange={(v) => setHosted((c) => ({ ...c, model: v }))} placeholder="model-name" />
          <label className="topology-add-secret">
            <span>Key</span>
            <input ref={secretRef} type="password" autoComplete="new-password" aria-label="Provider key" />
          </label>
          {error ? <ActionNotice tone="danger">{error}</ActionNotice> : null}
          <div className="topology-add-actions">
            <button type="button" onClick={() => setFace("choices")}>Back</button>
            <Button variant="primary" loading={busy} disabled={busy} onClick={() => void submitHosted()}>
              Connect
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main component ──────────────────────────────────────────────────

export function TopologyMapView({
  onOpenAssignments,
}: {
  onOpenAssignments?: () => void;
}) {
  const [topology, setTopology] = useState<TopologyWire | null>(null);
  const [assignments, setAssignments] = useState<AssignmentSummary | null>(null);
  const [library, setLibrary] = useState<ModelLibraryProjection | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [repointRow, setRepointRow] = useState<AssignmentSummaryRow | null>(null);
  const [addOpen, setAddOpen] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError("");
    try {
      const data = await getTopologyFull();
      setTopology(data.topology);
      setAssignments(data.assignments);
      setLibrary(data.library);
    } catch (e) {
      setLoadError(readableError(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  // ── Build graph model ──
  const graphNodes = useMemo(() => {
    if (!topology) return [];
    return layoutNodes(topology.nodes);
  }, [topology]);

  const graphFlows = useMemo(() => {
    if (!topology) return [];
    return bundleFlows(topology);
  }, [topology]);

  // ── Selected node wire data ──
  const selectedNode = useMemo(
    () => topology?.nodes.find((n) => n.id === selectedId) ?? null,
    [topology, selectedId],
  );

  // ── Re-point handler ──
  const startRepoint = useCallback(() => {
    if (!assignments) return;
    // Find the first assignment row that targets the selected node
    const row = assignments.rows.find(
      (r) => r.editor_capability_id && r.id !== "global",
    );
    if (row) setRepointRow(row);
    else onOpenAssignments?.();
  }, [assignments, onOpenAssignments]);

  const finishRepoint = useCallback(() => {
    setRepointRow(null);
    void load();
  }, [load]);

  if (loading) return <SurfaceState loading />;
  if (loadError)
    return <SurfaceState error={loadError} onRetry={() => void load()} />;

  return (
    <div className="topology-map" data-testid="topology-map">
      <TopologySurface
        nodes={graphNodes}
        flows={graphFlows}
        selectedId={selectedId}
        onSelect={setSelectedId}
        ariaLabel="Infrastructure topology"
        inspectorSlot={
          selectedNode && assignments && library ? (
            repointRow ? (
              <RepointPanel
                row={repointRow}
                onDone={finishRepoint}
              />
            ) : (
              <NodeInspector
                node={selectedNode}
                assignments={assignments}
                library={library}
                onRepoint={startRepoint}
              />
            )
          ) : null
        }
        addNodeSlot={
          <Disclosure
            label="+ Add node"
            open={addOpen}
            onOpenChange={setAddOpen}
          >
            <AddNodePanel onAdded={() => void load()} />
          </Disclosure>
        }
      />
    </div>
  );
}
