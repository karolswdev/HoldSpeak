// HS-111-02 — the gear door's Pipeline/Delivery sheet and footer bar.
import { useState, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch } from "../../../lib/api";
import { openSurfaceOr } from "../../../desk/shell";
import { useResource } from "../../pageSupport";
import type { DictationReadinessResponse } from "../core-types";
import { presentValue } from "../../../desk/surface/format";
import { SurfaceFooter } from "../../../desk/surface/SurfaceFooter";
import {
  SurfaceFacts,
  SurfaceState,
} from "../../../desk/surface/Surface";
import {
  FoldGadget,
  GadgetGroup,
  GadgetRow,
  LampGadget,
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
  const [kbBusy, setKbBusy] = useState(false);
  const config = (resource.data.config ?? {}) as Record<string, unknown>;
  const target = (resource.data.target ?? {}) as Record<string, unknown>;
  const depth = (resource.data.depth ?? {}) as Record<string, unknown>;
  const warnings = Array.isArray(resource.data.warnings)
    ? (resource.data.warnings as Record<string, unknown>[])
    : [];
  const enabled = config.pipeline_enabled === true;
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
        {/* HS-130-07: the pipeline's ON/OFF is a Settings-owned preference
            (one writer). This readiness sheet shows the EFFECTIVE state and
            opens the exact Settings module; it no longer persists the toggle
            (two writers silently clobbered each other before). */}
        <GadgetRow
          label="Dictation pipeline"
          fact={`${presentValue(config.backend) || "automatic"} · ${
            presentValue(config.max_total_latency_ms) || "—"
          } MS`}
        >
          <span className="gadget-checkline">
            <LampGadget
              label={enabled ? "ON" : "OFF"}
              on={enabled}
              tone={enabled ? "ok" : "warn"}
            />
            <Button
              dense
              variant="ghost"
              onClick={() =>
                openSurfaceOr("configure-settings", "/settings", "voice-typing")
              }
            >
              {enabled ? "Manage in Settings" : "Enable in Settings"}
            </Button>
          </span>
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

/* HS-129-05 — Speak's readiness is not a second sticky rail. The same
   readiness wire publishes through the frame-owned footer: lamp at egress,
   state or landing receipt at center, and Review beside Export. */
export function ReadinessFooter({
  onOpenDoor,
  receipt,
  exportVerb,
}: {
  onOpenDoor: () => void;
  receipt: Receipt | null;
  exportVerb: ReactNode;
}) {
  const root = localStorage.getItem("holdspeak.projectRootOverride") ?? "";
  const resource = useResource<DictationReadinessResponse>(
    `/api/dictation/readiness${root ? `?project_root=${encodeURIComponent(root)}` : ""}`,
    {},
  );
  const receiptSlot = receipt ? (
    <span
      className="surface-footer-readiness"
      data-tone={receipt.tone === "warn" ? "warn" : undefined}
      role={receipt.tone === "warn" ? "alert" : "status"}
    >
      {receipt.text}
    </span>
  ) : null;

  if (resource.loading) {
    return (
      <SurfaceFooter
        egress={<LampGadget label="PIPELINE" on={false} tone="warn" />}
        receipt={receiptSlot || <span className="surface-footer-readiness">CHECKING PIPELINE</span>}
        verbs={exportVerb}
      />
    );
  }
  if (resource.error) {
    return (
      <SurfaceFooter
        egress={<LampGadget label="PIPELINE UNAVAILABLE" on={false} tone="fail" />}
        receipt={receiptSlot || <span className="surface-footer-readiness" role="alert">READINESS UNAVAILABLE</span>}
        verbs={<>{exportVerb}<button type="button" className="desk-chip" onClick={onOpenDoor}>Review</button></>}
      />
    );
  }

  const config = (resource.data.config ?? {}) as Record<string, unknown>;
  const target = (resource.data.target ?? {}) as Record<string, unknown>;
  const warnings = Array.isArray(resource.data.warnings)
    ? resource.data.warnings
    : [];
  const live = config.pipeline_enabled === true && warnings.length === 0;
  const state = live
    ? [
        target.label ? `→ ${presentValue(target.label)}` : "PIPELINE LIVE",
        config.max_total_latency_ms ? `${presentValue(config.max_total_latency_ms)} MS` : "",
      ].filter(Boolean).join(" · ")
    : config.pipeline_enabled === true
      ? `${warnings.length} ${warnings.length === 1 ? "WARNING" : "WARNINGS"}`
      : "PIPELINE OFF";

  return (
    <SurfaceFooter
      egress={
        <LampGadget
          label={live ? "PIPELINE LIVE" : state}
          on={live}
          tone={live ? "ok" : "warn"}
        />
      }
      receipt={receiptSlot || <span className="surface-footer-readiness" role="status">{state}</span>}
      verbs={
        <>
          {live ? null : <button type="button" className="desk-chip" onClick={onOpenDoor}>Review</button>}
          {exportVerb}
        </>
      }
    />
  );
}
