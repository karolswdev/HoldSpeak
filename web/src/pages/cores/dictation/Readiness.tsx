// HS-111-02 — the gear door's Pipeline/Delivery sheet and footer bar.
import { useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch } from "../../../lib/api";
import { useResource } from "../../pageSupport";
import type { DictationReadinessResponse } from "../core-types";
import { presentValue } from "../../../desk/surface/format";
import {
  SurfaceFacts,
  SurfaceState,
} from "../../../desk/surface/Surface";
import {
  CheckGadget,
  FoldGadget,
  GadgetGroup,
  GadgetRow,
} from "../../../desk/surface/gadgets";
import { readableValue, type Receipt } from "./shared";

/* HS-111-02 — the gear door's Pipeline/Delivery sheet: axis-named
   check, fact tokens, the KB verb at the point of the fact. The
   readiness wire (config/target/depth/warnings) renders as equipment,
   never sentences. */
export function Readiness() {
  const root = localStorage.getItem("holdspeak.projectRootOverride") ?? "";
  const query = root ? `?project_root=${encodeURIComponent(root)}` : "";
  const resource = useResource<DictationReadinessResponse>(
    `/api/dictation/readiness${query}`,
    {},
  );
  const [pending, setPending] = useState(false);
  const [kbBusy, setKbBusy] = useState(false);
  const config = (resource.data.config ?? {}) as Record<string, unknown>;
  const target = (resource.data.target ?? {}) as Record<string, unknown>;
  const depth = (resource.data.depth ?? {}) as Record<string, unknown>;
  const warnings = Array.isArray(resource.data.warnings)
    ? (resource.data.warnings as Record<string, unknown>[])
    : [];
  const enabled = config.pipeline_enabled === true;
  const togglePipeline = async (next: boolean) => {
    setPending(true);
    try {
      await apiFetch("/api/settings", {
        method: "PUT",
        json: { dictation: { pipeline: { enabled: next } } },
      });
      await resource.reload();
    } finally {
      setPending(false);
    }
  };
  const createStarterKb = async () => {
    setKbBusy(true);
    try {
      await apiFetch(`/api/dictation/project-kb/starter${query}`, {
        method: "POST",
      });
      await resource.reload();
    } finally {
      setKbBusy(false);
    }
  };
  const confidencePct =
    typeof target.confidence === "number"
      ? Math.round((target.confidence as number) * 100)
      : null;
  const runs = Number(depth.runs ?? 0);
  const hasKbWarning = warnings.some((w) => w.code === "missing_project_kb");
  const otherWarnings = warnings.filter(
    (w) => w.code !== "pipeline_disabled" && w.code !== "missing_project_kb",
  );
  return (
    <SurfaceState
      loading={resource.loading}
      error={resource.error}
      onRetry={() => void resource.reload()}
    >
      <GadgetGroup label="Pipeline">
        <GadgetRow
          label="Dictation pipeline"
          fact={`${presentValue(config.backend) || "automatic"} · ${
            presentValue(config.max_total_latency_ms) || "—"
          } MS`}
        >
          <CheckGadget
            label="Dictation pipeline"
            checked={enabled}
            disabled={pending}
            onChange={(next) => void togglePipeline(next)}
          />
        </GadgetRow>
        {hasKbWarning ? (
          <GadgetRow label="Project KB" fact="MISSING">
            <Button dense loading={kbBusy} onClick={() => void createStarterKb()}>
              Create
            </Button>
          </GadgetRow>
        ) : null}
        {otherWarnings.map((warning, index) => (
          <p
            className="speak-token-line"
            data-tone="warn"
            key={String(warning.code ?? index)}
          >
            ⚠ {presentValue(warning.message) || readableValue(warning)}
          </p>
        ))}
      </GadgetGroup>
      <GadgetGroup label="Delivery">
        <GadgetRow label="Delivery target">
          <span className="speak-token-line">
            {target.label
              ? `${presentValue(target.label)}${
                  target.source === "hints" ? " · BROWSER BRIDGE" : ""
                }`
              : "—"}
          </span>
        </GadgetRow>
        {confidencePct !== null ? (
          <GadgetRow label="Confidence">
            <span className="speak-token-line">{confidencePct}%</span>
          </GadgetRow>
        ) : null}
        <GadgetRow label="Runs">
          <span className="speak-token-line">{runs}</span>
        </GadgetRow>
      </GadgetGroup>
      <FoldGadget title="Wire details">
        <SurfaceFacts value={config} />
        <SurfaceFacts value={target} />
        <SurfaceFacts value={depth} />
      </FoldGadget>
    </SurfaceState>
  );
}

/* HS-100-07/HS-111-02 — the footer bar: readiness tokens on the left
   (quiet when live, a warning that opens the door when not), the
   program's last receipt/refusal on the right. The one status line. */
export function ReadinessLine({
  onOpenDoor,
  receipt,
}: {
  onOpenDoor: () => void;
  receipt: Receipt | null;
}) {
  const root = localStorage.getItem("holdspeak.projectRootOverride") ?? "";
  const resource = useResource<DictationReadinessResponse>(
    `/api/dictation/readiness${root ? `?project_root=${encodeURIComponent(root)}` : ""}`,
    {},
  );
  const receiptSlot = receipt ? (
    <span
      className="speak-receipt"
      data-tone={receipt.tone === "warn" ? "warn" : undefined}
      role={receipt.tone === "warn" ? "alert" : "status"}
    >
      {receipt.text}
    </span>
  ) : null;
  if (resource.loading || resource.error) {
    return receiptSlot ? (
      <p className="speak-status">{receiptSlot}</p>
    ) : null;
  }
  const config = (resource.data.config ?? {}) as Record<string, unknown>;
  const target = (resource.data.target ?? {}) as Record<string, unknown>;
  const warnings = Array.isArray(resource.data.warnings)
    ? resource.data.warnings
    : [];
  const live = config.pipeline_enabled === true && warnings.length === 0;
  if (live) {
    const budget = config.max_total_latency_ms;
    return (
      <p className="speak-status" role="status">
        <span><span className="speak-status-dot is-live" aria-hidden="true" /> Pipeline live</span>
        {target.label ? <span>{"-> "}{presentValue(target.label)}</span> : null}
        {budget ? <span>{presentValue(budget)} ms</span> : null}
        {receiptSlot}
      </p>
    );
  }
  return (
    <p className="speak-status is-warn" role="status">
      <span><span className="speak-status-dot" aria-hidden="true" /> {config.pipeline_enabled === true
        ? `${warnings.length} ${warnings.length === 1 ? "warning" : "warnings"}`
        : "Pipeline off"}</span>
      <span>
        <button type="button" className="speak-status-fix" onClick={onOpenDoor}>
          Review
        </button>
      </span>
      {receiptSlot}
    </p>
  );
}
