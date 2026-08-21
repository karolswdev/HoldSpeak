// HS-112-01 — the one dial. The Prefs `models` module is the ONLY face
// that edits endpoint/model identity: the target list (the profiles
// table via /api/inference-targets, the one write path), a per-feature
// RUNS ON picker (dictation / meetings / rails), the hub's own local
// engine, and the rails observer's knobs. Everything composes from the
// settings gadget kit; errors land in the Prefs footer receipt, never
// over the UI.
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { apiFetch, readableError } from "../../lib/api";
import type {
  SettingsResponse,
  InferenceTargetsResponse,
} from "./core-types";
import { ConfirmVerb } from "../../desk/surface/Surface";
import {
  CheckGadget,
  CycleGadget,
  FoldGadget,
  GadgetGroup,
  GadgetRow,
  LampGadget,
  StepperGadget,
  StringGadget,
} from "../../desk/surface/gadgets";
import { useRovingRows } from "../../desk/surface/roving";
import {
  INTEL_PROVIDER_OPTIONS,
  meetingPlacement,
} from "./settingsPrefs";

type Target = {
  id: string;
  name: string;
  kind: string;
  model: string;
  profile_id: string | null;
  base_url: string;
  node: string;
  context_limit: number;
  requires_key: boolean;
  key_present: boolean;
  readiness_state: string;
  readiness_reason: string;
};

type ProbeResult = {
  reachable: boolean;
  latency_ms: number | null;
  models: string[];
  error: string | null;
};

type RuntimeTestResult = {
  ok: boolean;
  status: string;
  backend: string | null;
  detail: string;
};

type RunnableModel = { id: string; name: string; ready?: boolean };

type RuntimeOptions = {
  platform: { system: string; machine: string; apple_silicon: boolean };
  mlx: Array<{ label: string; value: string }>;
  gguf: Array<{ label: string; value: string }>;
};

const KIND_OPTIONS = [
  { value: "openAICompatible", label: "ENDPOINT" },
  { value: "onDevice", label: "THIS DEVICE" },
  { value: "desktop", label: "PAIRED" },
  { value: "meshNode", label: "MESH" },
];

// The wire's target taxonomy → the storage kind the editor cycles.
const WIRE_KIND: Record<string, string> = {
  private_endpoint: "openAICompatible",
  external_service: "openAICompatible",
  this_device: "onDevice",
  paired_device: "desktop",
  mesh_node: "meshNode",
};

/** Keep transport state out of the owner's destination ledger. */
function readinessLabel(state: string): string {
  switch (state) {
    case "needs_key":
      return "KEY NEEDED";
    case "unsupported":
      return "NOT AVAILABLE";
    default:
      return state.replace(/[_-]+/g, " ").toUpperCase();
  }
}

function fromWire(row: Record<string, unknown>): Target {
  const readiness = (row.readiness ?? {}) as Record<string, unknown>;
  const secret = (row.secret ?? {}) as Record<string, unknown>;
  const kind = String(row.kind ?? "");
  return {
    id: String(row.id ?? ""),
    name: String(row.name ?? ""),
    kind: WIRE_KIND[kind] ?? kind,
    model: String(row.model ?? ""),
    profile_id: row.profile_id == null ? null : String(row.profile_id),
    // HS-134-02: endpoint/node now ride the target contract directly.
    base_url: String(row.endpoint ?? ""),
    node: String(row.node ?? ""),
    context_limit: Number(row.context_limit ?? 16384),
    requires_key: Boolean(secret.required),
    key_present: Boolean(secret.present),
    readiness_state: String(readiness.state ?? "ready"),
    readiness_reason: String(readiness.reason ?? ""),
  };
}

export function ModelsModule({
  settings,
  update,
  onRefuse,
}: {
  settings: SettingsResponse;
  /** The Prefs debounced settings writer (path → value). */
  update(path: string[], next: unknown): void;
  /** The footer receipt bar; "" clears. */
  onRefuse(refusal: string): void;
}) {
  const [targets, setTargets] = useState<Target[]>([]);
  const [probeResults, setProbeResults] = useState<Record<string, ProbeResult>>({});
  const [probingIds, setProbingIds] = useState<Set<string>>(() => new Set());
  const [keyDrafts, setKeyDrafts] = useState<Record<string, string>>({});
  const [keyEditingId, setKeyEditingId] = useState<string | null>(null);
  const [savingKeyIds, setSavingKeyIds] = useState<Set<string>>(() => new Set());
  const [hubDefault, setHubDefault] = useState<{ engine: string; model: string; available: boolean }>({
    engine: "", model: "", available: false,
  });
  const [testingRuntime, setTestingRuntime] = useState(false);
  const [runtimeTest, setRuntimeTest] = useState<RuntimeTestResult | null>(null);
  const [runtimeOptions, setRuntimeOptions] = useState<RuntimeOptions | null>(null);
  const [manualLocalSetup, setManualLocalSetup] = useState<boolean | null>(null);
  const [connectionsOpen, setConnectionsOpen] = useState(false);
  const saveTimers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});
  const localSetupRef = useRef<HTMLDivElement>(null);
  const connectionsRef = useRef<HTMLDivElement>(null);

  const reload = useCallback(async () => {
    try {
      // HS-134-02: one fetch — the target contract carries endpoint/node.
      const wire = await apiFetch<InferenceTargetsResponse>(
        "/api/inference-targets",
      );
      setTargets(
        (wire.targets ?? [])
          .filter((row) => row.profile_id != null)
          .map(fromWire),
      );
    } catch (error) {
      onRefuse(readableError(error));
    }
  }, [onRefuse]);

  useEffect(() => {
    void reload();
    void apiFetch<{ engine: string; model: string; available: boolean }>(
      "/api/setup/hub-default-summary",
    ).then(setHubDefault).catch(() => {});
    void apiFetch<RuntimeOptions>("/api/setup/runtime-options").then(setRuntimeOptions).catch(() => {});
    const timers = saveTimers.current;
    return () => Object.values(timers).forEach(clearTimeout);
  }, [reload]);

  const put = async (target: Target) => {
    try {
      await apiFetch(`/api/inference-targets/${encodeURIComponent(target.id)}`, {
        method: "PUT",
        json: {
          name: target.name,
          kind: target.kind,
          base_url: target.base_url,
          model: target.model,
          node: target.node,
          context_limit: target.context_limit,
          requires_key: target.requires_key,
        },
      });
      onRefuse("");
      await reload();
    } catch (error) {
      onRefuse(readableError(error));
    }
  };

  const patch = (id: string, next: Partial<Target>) => {
    if ("base_url" in next || "node" in next || "kind" in next) {
      setProbeResults(({ [id]: _discarded, ...remaining }) => remaining);
    }
    setTargets((rows) => {
      const updated = rows.map((row) =>
        row.id === id ? { ...row, ...next } : row,
      );
      const target = updated.find((row) => row.id === id);
      if (target) {
        clearTimeout(saveTimers.current[id]);
        saveTimers.current[id] = setTimeout(() => void put(target), 700);
      }
      return updated;
    });
  };

  const add = async () => {
    try {
      await apiFetch("/api/inference-targets", {
        method: "POST",
        json: {
          name: "NEW DESTINATION",
          kind: "openAICompatible",
          base_url: "",
          model: "",
        },
      });
      onRefuse("");
      await reload();
    } catch (error) {
      onRefuse(readableError(error));
    }
  };

  const remove = async (index: number) => {
    const target = targets[index];
    if (!target) return;
    try {
      await apiFetch(`/api/inference-targets/${encodeURIComponent(target.id)}`, {
        method: "DELETE",
      });
      onRefuse("");
      await reload();
    } catch (error) {
      onRefuse(readableError(error));
    }
  };

  const setKey = async (row: Target) => {
    const value = keyDrafts[row.id] ?? "";
    if (!value) return;
    setSavingKeyIds((ids) => new Set(ids).add(row.id));
    try {
      await apiFetch(`/api/inference-targets/${encodeURIComponent(row.id)}/secret`, {
        method: "PUT",
        json: { value },
      });
      setKeyDrafts((drafts) => ({ ...drafts, [row.id]: "" }));
      setKeyEditingId(null);
      onRefuse("");
      await reload();
    } catch (error) {
      onRefuse(readableError(error));
    } finally {
      setSavingKeyIds((ids) => {
        const next = new Set(ids);
        next.delete(row.id);
        return next;
      });
    }
  };

  const clearKey = async (row: Target) => {
    setSavingKeyIds((ids) => new Set(ids).add(row.id));
    try {
      await apiFetch(`/api/inference-targets/${encodeURIComponent(row.id)}/secret`, {
        method: "DELETE",
      });
      setKeyDrafts((drafts) => ({ ...drafts, [row.id]: "" }));
      setKeyEditingId(null);
      onRefuse("");
      await reload();
    } catch (error) {
      onRefuse(readableError(error));
    } finally {
      setSavingKeyIds((ids) => {
        const next = new Set(ids);
        next.delete(row.id);
        return next;
      });
    }
  };

  const probeTarget = async (id: string) => {
    setProbingIds((ids) => new Set(ids).add(id));
    try {
      const result = await apiFetch<ProbeResult>(
        `/api/inference-targets/${encodeURIComponent(id)}/probe`,
        { method: "POST" },
      );
      setProbeResults((results) => ({ ...results, [id]: result }));
      onRefuse("");
    } catch (error) {
      setProbeResults((results) => ({
        ...results,
        [id]: {
          reachable: false,
          latency_ms: null,
          models: [],
          error: readableError(error),
        },
      }));
    } finally {
      setProbingIds((ids) => {
        const next = new Set(ids);
        next.delete(id);
        return next;
      });
    }
  };

  const testRuntime = async () => {
    setTestingRuntime(true);
    try {
      const listing = await apiFetch<{ models?: RunnableModel[] }>("/api/models");
      const local = (listing.models ?? []).find((model) => model.id === "this_machine");
      const result: RuntimeTestResult = local?.ready
        ? { ok: true, status: "ready", backend: null, detail: `${local.name} can answer on this device.` }
        : { ok: false, status: "unavailable", backend: null, detail: "No working model was found. Check the model location, then try again." };
      setRuntimeTest(result);
      onRefuse("");
      const summary = await apiFetch<{ engine: string; model: string; available: boolean }>(
        "/api/setup/hub-default-summary",
      );
      setHubDefault(summary);
    } catch (error) {
      const detail = readableError(error);
      setRuntimeTest({ ok: false, status: "error", backend: null, detail });
    } finally {
      setTestingRuntime(false);
    }
  };

  const probeLabel = (row: Target): { on: boolean; tone: "ok" | "fail"; label: string } | null => {
    const result = probeResults[row.id];
    if (!result) return null;
    if (result.reachable) {
      return {
        on: true,
        tone: "ok",
        label: `READY${result.latency_ms == null ? "" : ` ${result.latency_ms}ms`}`,
      };
    }
    return {
      on: false,
      tone: "fail",
      label: result.error ? "OFFLINE. Settings are unchanged. Retry." : "OFFLINE",
    };
  };

  const val = (path: string[]): unknown =>
    path.reduce<unknown>(
      (acc, part) =>
        acc && typeof acc === "object" ? (acc as Record<string, unknown>)[part] : undefined,
      settings,
    );

  const pointerOptions = [
    { value: "", label: hubDefault.available
      ? `HUB DEFAULT · ${hubDefault.engine.toUpperCase()} · ${hubDefault.model.toUpperCase()}`
      : "HUB DEFAULT · NO MODEL" },
    ...targets.map((row) => ({
      value: row.id,
      label: (row.name || row.id).toUpperCase(),
      disabled: row.readiness_state === "unsupported",
    })),
  ];

  const pointerRow = (label: string, path: string[], fact?: string) => (
    <GadgetRow key={path.join(".")} label={label} fact={fact}>
      <CycleGadget
        label={`${label} AI`}
        value={String(val(path) ?? "")}
        options={pointerOptions}
        onChange={(next) => update(path, next || null)}
      />
    </GadgetRow>
  );

  /* One Meetings choice, one plain consequence. The hub provenance still
     decides whether the fallback is live; its implementation explanation
     stays off the owner's glass. */
  const placement = meetingPlacement(settings);
  const droppedDestination = String(placement?.placement_reason ?? "");
  const destinationDecides = placement?.placement_source === "destination";
  const meetingTarget = String(placement?.target_name || placement?.node || "").trim();
  const meetingSummary = meetingTarget
    ? `Meetings uses ${meetingTarget}`
    : placement?.boundary === "cloud"
      ? "Meetings uses the cloud"
      : "Meetings uses this device";
  const plainReason = (reason: unknown) => {
    const text = String(reason ?? "").replace(/[_-]+/g, " ").replace(/\s+/g, " ").trim();
    if (/no language model/i.test(text)) return "Choose a local model in Intelligence";
    return text ? text[0].toUpperCase() + text.slice(1) : "Check the selected model";
  };
  const meetingsNotice = placement?.runnable === false
    ? droppedDestination
      ? "Meetings can’t use the selected destination. Choose a local model in Intelligence."
      : `Meetings can’t run: ${plainReason(placement.runnable_reason)}`
    : droppedDestination
      ? "Selected destination isn’t compatible"
      : "";
  const meetingsBlock = (
    <>
      <GadgetRow
        label={
          <>
            <span>Meetings</span>
            <span className="models-meeting-summary">{meetingSummary}</span>
          </>
        }
      >
        <CycleGadget
          label="Meetings AI"
          value={String(val(["meeting", "intel_profile_id"]) ?? "")}
          options={pointerOptions}
          onChange={(next) => update(["meeting", "intel_profile_id"], next || null)}
        />
      </GadgetRow>
      {meetingsNotice ? (
        <div
          className="models-meeting-notice"
          data-tone={placement?.runnable === false ? "danger" : undefined}
        >
          {meetingsNotice}
        </div>
      ) : null}
      <FoldGadget title="Meeting routing options" className="models-meeting-routing">
        <GadgetRow label="If no destination">
          <CycleGadget
            label="Meetings provider"
            value={String(val(["meeting", "intel_provider"]) ?? "local")}
            options={INTEL_PROVIDER_OPTIONS}
            disabled={Boolean(destinationDecides)}
            onChange={(next) => update(["meeting", "intel_provider"], next)}
          />
        </GadgetRow>
        {/* HS-139-03: intel_realtime_model moved from Settings > Meetings. */}
        <GadgetRow label="Realtime model">
          <StringGadget
            label="Realtime model"
            value={String(val(["meeting", "intel_realtime_model"]) ?? "")}
            placeholder="path to local model"
            onChange={(next) => update(["meeting", "intel_realtime_model"], next || null)}
          />
        </GadgetRow>
      </FoldGadget>
    </>
  );

  const lampTone = (row: Target): "ok" | "warn" | "fail" =>
    row.readiness_state === "ready"
      ? "ok"
      : row.readiness_state === "needs_key" || row.readiness_state === "offline"
        ? "warn"
        : "fail";

  const runtime = (settings.dictation as Record<string, unknown> | undefined)?.runtime as
    | Record<string, unknown>
    | undefined;
  const backend = String(runtime?.backend ?? "auto");

  /* The matrix needs a genuinely useful editorial width. Below it, a row
     cannot keep a name, endpoint, model and health honest, so it becomes a
     compact disclosure instead of pretending that six clipped cells are a
     table. This observes the surface container, never the viewport. */
  const destRef = useRef<HTMLDivElement>(null);
  const matrixRef = useRef<HTMLDivElement>(null);
  const [narrow, setNarrow] = useState(false);
  const [expandedTargetId, setExpandedTargetId] = useState<string | null>(null);
  useLayoutEffect(() => {
    const el = destRef.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    // ResizeObserver follows this initial measurement in a live window. The
    // guard keeps unmeasured/jsdom nodes from masquerading as a zero-width
    // phone sheet.
    const initialWidth = el.getBoundingClientRect().width;
    if (initialWidth > 0) setNarrow(initialWidth < 840);
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setNarrow(entry.contentRect.width < 840);
      }
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  useRovingRows(matrixRef, {
    selector:
      ".models-destination-row button, .models-destination-row input, .models-destination-row select",
    rowSelector: ".models-destination-row",
  });

  const endpointField = (row: Target) =>
    row.kind === "meshNode" ? (
      <StringGadget
        label={`Target ${row.id} node`}
        value={row.node}
        placeholder="node"
        onChange={(next) => patch(row.id, { node: next })}
      />
    ) : (
      <StringGadget
        label={`Target ${row.id} endpoint`}
        value={row.base_url}
        placeholder="http://…/v1"
        onChange={(next) => patch(row.id, { base_url: next })}
      />
    );

  const modelField = (row: Target) => {
    const result = probeResults[row.id];
    return result?.models.length ? (
      <CycleGadget
        label={`Target ${row.id} model`}
        value={row.model}
        options={result.models.map((model) => ({ value: model }))}
        onChange={(next) => patch(row.id, { model: next })}
      />
    ) : (
      <StringGadget
        label={`Target ${row.id} model`}
        value={row.model}
        onChange={(next) => patch(row.id, { model: next })}
      />
    );
  };

  const healthField = (row: Target) => {
    const state = probeLabel(row);
    return (
      <span className="models-destination-health">
        <span className="gadget-key-cell">
          <CheckGadget
            label={`Target ${row.id} requires key`}
            checked={row.requires_key}
            onChange={(checked) => patch(row.id, { requires_key: checked })}
          />
          {row.requires_key ? (
            <button
              type="button"
              className="models-key-affordance"
              aria-label={`${row.name || "Destination"} key ${row.key_present ? "set" : "needed"}`}
              onClick={() => setKeyEditingId(row.id)}
            >
              <LampGadget
                on={row.key_present}
                tone={row.key_present ? "ok" : "warn"}
                label={row.key_present ? "KEY SET" : "KEY NEEDED"}
              />
            </button>
          ) : null}
        </span>
        {state || !row.requires_key ? (
          <LampGadget
            on={state ? state.on : row.readiness_state === "ready"}
            tone={state ? state.tone : lampTone(row)}
            label={state ? state.label : readinessLabel(row.readiness_state)}
          />
        ) : null}
      </span>
    );
  };

  const keyEditor = (row: Target) => (
    <div className="models-key-editor" data-testid={`target-key-editor-${row.id}`}>
      <label>
        <span>API KEY</span>
        <input
          type="password"
          autoComplete="new-password"
          aria-label={`Destination ${row.id} API key`}
          value={keyDrafts[row.id] ?? ""}
          onChange={(event) => setKeyDrafts((drafts) => ({ ...drafts, [row.id]: event.target.value }))}
        />
      </label>
      <Button
        dense
        variant="ghost"
        loading={savingKeyIds.has(row.id)}
        disabled={!(keyDrafts[row.id] ?? "")}
        onClick={() => void setKey(row)}
      >
        {row.key_present ? "REPLACE" : "SET KEY"}
      </Button>
      {row.key_present ? (
        <Button dense variant="ghost" disabled={savingKeyIds.has(row.id)} onClick={() => void clearKey(row)}>
          REMOVE
        </Button>
      ) : null}
    </div>
  );

  /* Narrow does not expose five long forms at once. A destination is a
     readable summary until the owner explicitly opens the one to edit. */
  const destinationCard = (row: Target, index: number) => {
    const state = probeLabel(row);
    const expanded = expandedTargetId === row.id;
    return (
      <article
        key={row.id}
        className="dest-card"
        data-expanded={expanded || undefined}
        data-testid={`dest-card-${row.id}`}
      >
        <button
          type="button"
          className="dest-card-summary"
          aria-expanded={expanded}
          aria-controls={`destination-${row.id}`}
          onClick={() => setExpandedTargetId(expanded ? null : row.id)}
        >
          <span className="dest-card-index">{String(index + 1).padStart(2, "0")}</span>
          <span className="dest-card-name">{row.name || "NEW DESTINATION"}</span>
          <LampGadget
            on={state ? state.on : row.readiness_state === "ready"}
            tone={state ? state.tone : lampTone(row)}
            label={state ? state.label : readinessLabel(row.readiness_state)}
          />
          <span className="dest-card-disclosure" aria-hidden="true">⌄</span>
        </button>
        {expanded ? (
          <div className="dest-card-detail" id={`destination-${row.id}`}>
            <div className="dest-card-field" data-field="name">
              <span>NAME</span>
              <StringGadget
                label={`Target ${row.id} name`}
                value={row.name}
                onChange={(next) => patch(row.id, { name: next })}
              />
            </div>
            <div className="dest-card-field" data-field="kind">
              <span>KIND</span>
              <CycleGadget
                label={`Target ${row.id} kind`}
                value={row.kind}
                options={KIND_OPTIONS}
                onChange={(next) => patch(row.id, { kind: next })}
              />
            </div>
            <div className="dest-card-field" data-field="endpoint">
              <span>{row.kind === "meshNode" ? "NODE" : "ENDPOINT"}</span>
              {endpointField(row)}
            </div>
            <div className="dest-card-field" data-field="model">
              <span>MODEL</span>
              {modelField(row)}
            </div>
            <div className="dest-card-field" data-field="health">
              <span>HEALTH</span>
              {healthField(row)}
            </div>
            {row.requires_key ? keyEditor(row) : null}
            <div className="dest-card-verbs">
              <Button
                dense
                variant="ghost"
                loading={probingIds.has(row.id)}
                onClick={() => void probeTarget(row.id)}
              >
                TEST
              </Button>
              <ConfirmVerb
                label="×"
                confirmLabel="FORGET?"
                ariaLabel={`Delete destination ${index + 1}`}
                onConfirm={() => void remove(index)}
              />
            </div>
          </div>
        ) : null}
      </article>
    );
  };

  const destinationMatrix = (
    <div
      ref={matrixRef}
      className="models-destination-matrix"
      data-testid="models-destination-matrix"
      aria-label="AI connections"
    >
      <div className="models-destination-head" aria-hidden="true">
        <span>NAME</span>
        <span>KIND</span>
        <span>ENDPOINT</span>
        <span>MODEL</span>
        <span>HEALTH</span>
        <span>MANAGE</span>
      </div>
      {targets.map((row, index) => (
        <div key={row.id}>
        <div className="models-destination-row">
          <span className="models-destination-cell" data-column="name">
            <StringGadget
              label={`Target ${row.id} name`}
              value={row.name}
              onChange={(next) => patch(row.id, { name: next })}
            />
          </span>
          <span className="models-destination-cell" data-column="kind">
            <CycleGadget
              label={`Target ${row.id} kind`}
              value={row.kind}
              options={KIND_OPTIONS}
              onChange={(next) => patch(row.id, { kind: next })}
            />
          </span>
          <span className="models-destination-cell" data-column="endpoint">
            {endpointField(row)}
          </span>
          <span className="models-destination-cell" data-column="model">
            {modelField(row)}
          </span>
          <span className="models-destination-cell" data-column="health">
            {healthField(row)}
          </span>
          <span className="models-destination-actions">
            <Button
              dense
              variant="ghost"
              loading={probingIds.has(row.id)}
              onClick={() => void probeTarget(row.id)}
            >
              TEST
            </Button>
            <ConfirmVerb
              label="×"
              confirmLabel="FORGET?"
              ariaLabel={`Delete destination ${index + 1}`}
              onConfirm={() => void remove(index)}
            />
          </span>
        </div>
        {keyEditingId === row.id && row.requires_key ? (
          <div className="models-destination-key-row">{keyEditor(row)}</div>
        ) : null}
        </div>
      ))}
      <button type="button" className="gadget-table-add" onClick={() => void add()}>
        + ADD AI CONNECTION
      </button>
    </div>
  );

  const readyTargets = targets.filter((target) => target.readiness_state === "ready").length;
  const attentionTargets = targets.filter((target) => target.readiness_state !== "ready").length;
  const localSummary = hubDefault.available
    ? `${hubDefault.model} · ${hubDefault.engine}`
    : "No working local model yet";
  const preferredLocalEngine = backend === "mlx" || backend === "llama_cpp"
    ? backend
    : runtimeOptions?.platform?.apple_silicon ? "mlx" : "llama_cpp";
  const discoveredModels = [
    ...(runtimeOptions?.mlx ?? []).map((model) => ({
      value: `mlx:${model.value}`,
      label: `APPLE MLX · ${model.label}`,
      engine: "mlx" as const,
      path: model.value,
    })),
    ...(runtimeOptions?.gguf ?? []).map((model) => ({
      value: `llama_cpp:${model.value}`,
      label: `GGUF · ${model.label}`,
      engine: "llama_cpp" as const,
      path: model.value,
    })),
  ];
  const configuredLocalPath = preferredLocalEngine === "mlx"
    ? String(runtime?.mlx_model ?? "")
    : String(runtime?.llama_cpp_model_path ?? "");
  const selectedDiscoveredModel = discoveredModels.find((model) => model.path === configuredLocalPath)?.value ?? "";
  const showManualLocalPath = !discoveredModels.length
    || manualLocalSetup === true
    || (manualLocalSetup === null && Boolean(configuredLocalPath && !selectedDiscoveredModel));
  const chooseDiscoveredModel = (value: string) => {
    if (value === "__manual__") {
      setManualLocalSetup(true);
      setRuntimeTest(null);
      return;
    }
    const selected = discoveredModels.find((model) => model.value === value);
    if (!selected) return;
    setManualLocalSetup(false);
    setRuntimeTest(null);
    update(["dictation", "runtime", "backend"], selected.engine);
    update(
      ["dictation", "runtime", selected.engine === "mlx" ? "mlx_model" : "llama_cpp_model_path"],
      selected.path,
    );
  };

  const focusLocalSetup = () => {
    localSetupRef.current?.scrollIntoView({ block: "start", behavior: "smooth" });
    requestAnimationFrame(() => localSetupRef.current?.querySelector<HTMLElement>(
      '[aria-label="Model on this device"], [aria-label="Apple MLX model folder"], [aria-label="GGUF model file"]',
    )?.focus());
  };

  const openConnections = () => {
    setConnectionsOpen(true);
    requestAnimationFrame(() => {
      connectionsRef.current?.scrollIntoView({ block: "start", behavior: "smooth" });
      connectionsRef.current?.closest("details")?.querySelector<HTMLElement>("summary")?.focus();
    });
  };

  return (
    <div className="models-setup">
      <section className="models-setup-intro" aria-labelledby="models-setup-title">
        <div>
          <p className="models-setup-kicker">AI setup</p>
          <h2 id="models-setup-title">Choose your AI</h2>
          <p>Start with this device. Choose a different connection for a job only when you need one.</p>
        </div>
        <div className="models-setup-status" data-ready={hubDefault.available || undefined}>
          <LampGadget
            on={hubDefault.available}
            tone={hubDefault.available ? "ok" : "warn"}
            label={hubDefault.available ? "READY" : "SETUP NEEDED"}
          />
          <strong>{localSummary}</strong>
        </div>
        <div className="models-setup-actions">
          <Button variant="primary" onClick={focusLocalSetup}>{hubDefault.available ? "REVIEW THIS DEVICE" : "SET UP THIS DEVICE"}</Button>
          <Button variant="ghost" onClick={openConnections}>USE ANOTHER AI</Button>
        </div>
      </section>

      <div ref={localSetupRef} className="models-local-setup">
        <GadgetGroup label="This device">
          <p className="models-section-help">Private by default. Pick the model already stored on this Mac; HoldSpeak never downloads one silently.</p>
          <GadgetRow label="How to run it" fact="Auto is recommended">
            <CycleGadget
              label="Local AI engine"
              value={backend}
              options={[
                { value: "auto", label: "AUTO · RECOMMENDED" },
                { value: "mlx", label: "APPLE MLX" },
                { value: "llama_cpp", label: "GGUF · LLAMA.CPP" },
              ]}
              onChange={(next) => { setRuntimeTest(null); update(["dictation", "runtime", "backend"], next); }}
            />
          </GadgetRow>
          {discoveredModels.length ? <GadgetRow label="Model on this device" fact={`${discoveredModels.length} found`}>
            <CycleGadget
              label="Model on this device"
              value={showManualLocalPath ? "__manual__" : selectedDiscoveredModel}
              options={[
                { value: "", label: "CHOOSE A MODEL…", disabled: true },
                ...discoveredModels.map(({ value, label }) => ({ value, label })),
                { value: "__manual__", label: "OTHER MODEL LOCATION…" },
              ]}
              onChange={chooseDiscoveredModel}
            />
          </GadgetRow> : null}
          {showManualLocalPath ? <GadgetRow
            label={preferredLocalEngine === "mlx" ? "Apple MLX model" : "GGUF model"}
            fact={preferredLocalEngine === "mlx" ? "folder" : ".gguf file"}
          >
            <StringGadget
              label={preferredLocalEngine === "mlx" ? "Apple MLX model folder" : "GGUF model file"}
              value={configuredLocalPath}
              placeholder={preferredLocalEngine === "mlx" ? "~/Models/mlx/…" : "~/Models/gguf/…"}
              mic={false}
              onChange={(next) => {
                setRuntimeTest(null);
                update(
                  ["dictation", "runtime", preferredLocalEngine === "mlx" ? "mlx_model" : "llama_cpp_model_path"],
                  next,
                );
              }}
            />
          </GadgetRow> : null}
          <div className="models-local-check">
            <Button dense loading={testingRuntime} onClick={() => void testRuntime()}>CHECK THIS AI</Button>
            {runtimeTest ? <p role="status" data-ok={runtimeTest.ok || undefined}>{runtimeTest.ok ? "Ready" : "Not ready"} · {runtimeTest.detail}</p> : <p>Checks whether Thoughts can use it without sending a prompt.</p>}
          </div>
        </GadgetGroup>
      </div>

      <div className="models-job-routing">
        <GadgetGroup label="Choose AI for each job">
          <p className="models-section-help">Most people can leave these on This device. A connection here changes only that job.</p>
          {pointerRow("Writing & dictation", ["dictation", "runtime", "profile_id"], "Polishes spoken text")}
            {meetingsBlock}
        </GadgetGroup>
      </div>

      <FoldGadget
        title="AI connections"
        token={`${targets.length} ${targets.length === 1 ? "connection" : "connections"}${attentionTargets ? ` · ${attentionTargets} needs attention` : readyTargets ? ` · ${readyTargets} ready` : ""}`}
        open={connectionsOpen}
        onToggle={setConnectionsOpen}
        className="models-connections"
      >
        <p className="models-section-help">Private endpoints, paired devices, mesh nodes, and external services live here.</p>
        <div ref={connectionsRef} className="models-connections-anchor">
          <div ref={destRef} className="models-destinations" data-layout={narrow ? "cards" : "matrix"}>
            {narrow ? <div className="dest-cards-narrow">
              {targets.map((row, index) => destinationCard(row, index))}
              <button type="button" className="gadget-table-add" onClick={() => void add()}>+ ADD AI CONNECTION</button>
            </div> : destinationMatrix}
          </div>
        </div>
      </FoldGadget>

      <FoldGadget title="Advanced" token="optional" className="models-advanced">
        <GadgetGroup label="Local performance">
          <GadgetRow label="Keep model warm">
            <CheckGadget
              label="Keep local model warm"
              checked={Boolean(runtime?.warm_on_start)}
              onChange={(checked) => update(["dictation", "runtime", "warm_on_start"], checked)}
            />
          </GadgetRow>
          <GadgetRow label="Context window" fact="tokens">
            <StepperGadget
              label="Context window"
              value={Number(runtime?.n_ctx ?? 2048)}
              min={0}
              step={256}
              onChange={(next) => update(["dictation", "runtime", "n_ctx"], next)}
            />
          </GadgetRow>
          <GadgetRow label="Idle eviction" fact="s">
            <StepperGadget
              label="Idle eviction seconds"
              value={Number(runtime?.eviction_idle_seconds ?? 0)}
              min={0}
              step={30}
              onChange={(next) =>
                update(["dictation", "runtime", "eviction_idle_seconds"], next)
              }
            />
          </GadgetRow>
        </GadgetGroup>
        <GadgetGroup label="Background assistance">
          {pointerRow("Background assistance", ["rails_observer", "profile_id"])}
          <GadgetRow label="Enabled">
            <CheckGadget
              label="Background assistance"
              checked={Boolean(val(["rails_observer", "enabled"]))}
              onChange={(checked) => update(["rails_observer", "enabled"], checked)}
            />
          </GadgetRow>
          <GadgetRow label="Poll" fact="s">
            <StepperGadget
              label="Observer poll seconds"
              value={Number(val(["rails_observer", "poll_seconds"]) ?? 30)}
              min={5}
              step={5}
              onChange={(next) => update(["rails_observer", "poll_seconds"], next)}
            />
          </GadgetRow>
          <GadgetRow label="Tail" fact="events">
            <StepperGadget
              label="Observer tail"
              value={Number(val(["rails_observer", "tail"]) ?? 20)}
              min={1}
              step={5}
              onChange={(next) => update(["rails_observer", "tail"], next)}
            />
          </GadgetRow>
        </GadgetGroup>
      </FoldGadget>
    </div>
  );
}
