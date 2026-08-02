// HS-112-01 — the one dial. The Prefs `models` module is the ONLY face
// that edits endpoint/model identity: the target list (the profiles
// table via /api/inference-targets, the one write path), a per-feature
// RUNS ON picker (dictation / meetings / rails), the hub's own local
// engine, and the rails observer's knobs. Everything composes from the
// settings gadget kit; errors land in the Prefs footer receipt, never
// over the UI.
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { apiFetch, readableError, type JsonRecord } from "../../lib/api";
import {
  CheckGadget,
  CycleGadget,
  GadgetGroup,
  GadgetRow,
  GadgetTable,
  LampGadget,
  StepperGadget,
  StringGadget,
} from "../../desk/surface/gadgets";

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

function fromWire(row: JsonRecord): Target {
  const readiness = (row.readiness ?? {}) as JsonRecord;
  const secret = (row.secret ?? {}) as JsonRecord;
  const kind = String(row.kind ?? "");
  return {
    id: String(row.id ?? ""),
    name: String(row.name ?? ""),
    kind: WIRE_KIND[kind] ?? kind,
    model: String(row.model ?? ""),
    profile_id: row.profile_id == null ? null : String(row.profile_id),
    base_url: "",
    node: "",
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
  settings: JsonRecord;
  /** The Prefs debounced settings writer (path → value). */
  update(path: string[], next: unknown): void;
  /** The footer receipt bar; "" clears. */
  onRefuse(refusal: string): void;
}) {
  const [targets, setTargets] = useState<Target[]>([]);
  const [probe, setProbe] = useState<{ ok: boolean; detail: string } | null>(
    null,
  );
  const [probing, setProbing] = useState(false);
  const saveTimers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

  const reload = useCallback(async () => {
    try {
      const wire = await apiFetch<{ targets?: JsonRecord[] }>(
        "/api/inference-targets",
      );
      const rows = (wire.targets ?? [])
        .filter((row) => row.profile_id != null)
        .map(fromWire);
      // The endpoint/node columns live on the profile shape.
      const legacy = await apiFetch<{ profiles?: JsonRecord[] }>(
        "/api/profiles",
      );
      const byId = new Map(
        (legacy.profiles ?? []).map((row) => [String(row.id), row]),
      );
      setTargets(
        rows.map((row) => {
          const profile = byId.get(row.id);
          return profile
            ? {
                ...row,
                base_url: String(profile.base_url ?? ""),
                node: String(profile.node ?? ""),
                kind: String(profile.kind ?? row.kind),
              }
            : row;
        }),
      );
    } catch (error) {
      onRefuse(readableError(error));
    }
  }, [onRefuse]);

  useEffect(() => {
    void reload();
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

  const runProbe = async () => {
    setProbing(true);
    setProbe(null);
    try {
      const value = await apiFetch<{ ok?: boolean; detail?: string }>(
        "/api/setup/runtime-test",
        { method: "POST" },
      );
      setProbe({ ok: Boolean(value.ok), detail: String(value.detail ?? "") });
    } catch (error) {
      setProbe({ ok: false, detail: readableError(error) });
    } finally {
      setProbing(false);
    }
  };

  const val = (path: string[]): unknown =>
    path.reduce<unknown>(
      (acc, part) =>
        acc && typeof acc === "object" ? (acc as JsonRecord)[part] : undefined,
      settings,
    );

  const pointerOptions = [
    { value: "", label: "HUB DEFAULT" },
    ...targets.map((row) => ({
      value: row.id,
      label: (row.name || row.id).toUpperCase(),
      disabled: row.readiness_state === "unsupported",
    })),
  ];

  const pointerRow = (label: string, path: string[]) => (
    <GadgetRow key={path.join(".")} label={label}>
      <CycleGadget
        label={`${label} runs on`}
        value={String(val(path) ?? "")}
        options={pointerOptions}
        onChange={(next) => update(path, next || null)}
      />
    </GadgetRow>
  );

  const lampTone = (row: Target): "ok" | "warn" | "fail" =>
    row.readiness_state === "ready"
      ? "ok"
      : row.readiness_state === "needs_key" || row.readiness_state === "offline"
        ? "warn"
        : "fail";

  const runtime = (settings.dictation as JsonRecord | undefined)?.runtime as
    | JsonRecord
    | undefined;
  const backend = String(runtime?.backend ?? "auto");

  return (
    <>
      <GadgetGroup label="Destinations">
        <GadgetRow wide label="Destinations" fact={`${targets.length}`}>
          <GadgetTable
            head={["NAME", "KIND", "ENDPOINT", "MODEL", "KEY", "STATE"]}
            deleteLabel="FORGET?"
            rowKey={(index) => targets[index]?.id ?? String(index)}
            onDelete={(index) => void remove(index)}
            onAdd={() => void add()}
            addLabel="+ DESTINATION"
            rows={targets.map((row) => [
              <StringGadget
                key="name"
                label={`Target ${row.id} name`}
                value={row.name}
                onChange={(next) => patch(row.id, { name: next })}
              />,
              <CycleGadget
                key="kind"
                label={`Target ${row.id} kind`}
                value={row.kind}
                options={KIND_OPTIONS}
                onChange={(next) => patch(row.id, { kind: next })}
              />,
              row.kind === "meshNode" ? (
                <StringGadget
                  key="node"
                  label={`Target ${row.id} node`}
                  value={row.node}
                  placeholder="node"
                  onChange={(next) => patch(row.id, { node: next })}
                />
              ) : (
                <StringGadget
                  key="endpoint"
                  label={`Target ${row.id} endpoint`}
                  value={row.base_url}
                  placeholder="http://…/v1"
                  onChange={(next) => patch(row.id, { base_url: next })}
                />
              ),
              <StringGadget
                key="model"
                label={`Target ${row.id} model`}
                value={row.model}
                onChange={(next) => patch(row.id, { model: next })}
              />,
              <span key="key" className="gadget-key-cell">
                <CheckGadget
                  label={`Target ${row.id} requires key`}
                  checked={row.requires_key}
                  onChange={(checked) =>
                    patch(row.id, { requires_key: checked })
                  }
                />
                {row.requires_key ? (
                  <LampGadget
                    on={row.key_present}
                    tone={row.key_present ? "ok" : "warn"}
                    label={row.key_present ? "SET" : "UNSET"}
                  />
                ) : null}
              </span>,
              <LampGadget
                key="state"
                on={row.readiness_state === "ready"}
                tone={lampTone(row)}
                label={row.readiness_state.toUpperCase()}
              />,
            ])}
          />
        </GadgetRow>
        <GadgetRow label="Reachability" fact="tests the dictation leg">
          <Button dense loading={probing} onClick={() => void runProbe()}>
            PROBE
          </Button>
          {probe ? (
            <LampGadget
              on={probe.ok}
              tone={probe.ok ? "ok" : "fail"}
              label={probe.detail || (probe.ok ? "OK" : "FAILED")}
            />
          ) : null}
        </GadgetRow>
      </GadgetGroup>
      <GadgetGroup label="Runs on">
        {pointerRow("Dictation", ["dictation", "runtime", "profile_id"])}
        {pointerRow("Meetings", ["meeting", "intel_profile_id"])}
        {pointerRow("Rails", ["rails_observer", "profile_id"])}
      </GadgetGroup>
      <GadgetGroup label="Hub default engine">
        <GadgetRow label="Backend">
          <CycleGadget
            label="Local backend"
            value={backend}
            options={[
              { value: "auto", label: "AUTO" },
              { value: "mlx", label: "MLX" },
              { value: "llama_cpp", label: "LLAMA.CPP" },
            ]}
            onChange={(next) => update(["dictation", "runtime", "backend"], next)}
          />
        </GadgetRow>
        <GadgetRow label="MLX model">
          <StringGadget
            label="MLX model"
            value={String(runtime?.mlx_model ?? "")}
            placeholder="~/Models/mlx/…"
            onChange={(next) =>
              update(["dictation", "runtime", "mlx_model"], next)
            }
          />
        </GadgetRow>
        <GadgetRow label="llama.cpp model">
          <StringGadget
            label="llama.cpp model file"
            value={String(runtime?.llama_cpp_model_path ?? "")}
            placeholder="~/Models/gguf/…"
            onChange={(next) =>
              update(["dictation", "runtime", "llama_cpp_model_path"], next)
            }
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
        <GadgetRow label="Warm on start">
          <CheckGadget
            label="Warm on start"
            checked={Boolean(runtime?.warm_on_start)}
            onChange={(checked) =>
              update(["dictation", "runtime", "warm_on_start"], checked)
            }
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
      <GadgetGroup label="Rails observer">
        <GadgetRow label="Enabled">
          <CheckGadget
            label="Rails observer"
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
    </>
  );
}
