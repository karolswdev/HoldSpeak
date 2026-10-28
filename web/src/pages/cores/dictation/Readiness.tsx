// HS-111-02 — the gear door's Pipeline/Delivery sheet and footer bar.
import { useState, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch } from "../../../lib/api";
import { openSurfaceOr } from "../../../desk/shell";
import { useResource } from "../../pageSupport";
import { useBuilderTools } from "../../../desk/builderTools";
import type { DictationReadinessResponse } from "../core-types";
import { egressScopeLamp } from "../../../desk/inferenceEgress";
import { presentValue } from "../../../desk/surface/format";
import { DotWord } from "../../../desk/surface/kit";
import { countToken } from "../../../desk/surface";
import { SurfaceFooter } from "../../../desk/surface/SurfaceFooter";
import {
  SurfaceCode,
  SurfaceState,
} from "../../../desk/surface/Surface";
import {
  FoldGadget,
  GadgetGroup,
  GadgetRow,
  LampGadget,
} from "../../../desk/surface/gadgets";
import type { Receipt } from "./shared";

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
  const raw = useBuilderTools((state) => state.on);
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
  const modelMissing = otherWarnings.some((warning) => warning.code === "runtime_model_missing");
  /* Window Program W1 (2026-10-27): each warning is a row of the label /
     control grid: the axis on the left, a dot and a word on the right. */
  const warningRows: Record<string, { axis: string; word: string }> = {
    no_project: { axis: "Project", word: "No project" },
    no_blocks: { axis: "Blocks", word: "No blocks" },
    invalid_blocks: { axis: "Blocks", word: "Not valid" },
    invalid_project_kb: { axis: "Project KB", word: "Not valid" },
    runtime_unavailable: { axis: "Engine", word: "Not available" },
  };
  const rest = otherWarnings.filter((warning) => warning.code !== "runtime_model_missing");
  const latency = presentValue(config.max_total_latency_ms);
  return (
    <SurfaceState
      loading={resource.loading}
      error={resource.error}
      onRetry={() => void resource.reload()}
    >
      {modelMissing ? (
        <GadgetGroup label="Engine">
          <GadgetRow label="Speech model">
            <DotWord tone="warn">Model missing</DotWord>
            <Button dense variant="secondary" onClick={() => openSurfaceOr("open-concierge", "/models", "writing_dictation")}>
              Choose engine
            </Button>
          </GadgetRow>
        </GadgetGroup>
      ) : null}
      {rest.length ? (
        <GadgetGroup label="Needs a check">
          {rest.map((warning, index) => {
            const known = warningRows[String(warning.code)] ?? { axis: "Readiness", word: "Needs a check" };
            return (
              <GadgetRow key={String(warning.code ?? index)} label={known.axis}>
                <DotWord tone="warn">{known.word}</DotWord>
              </GadgetRow>
            );
          })}
        </GadgetGroup>
      ) : null}
      <GadgetGroup label="Pipeline">
        {/* HS-130-07: the pipeline's ON/OFF is a Settings-owned preference
            (one writer). This sheet shows the EFFECTIVE state; the toolbar's
            Manage in Settings opens the exact module. */}
        <GadgetRow
          label="Dictation pipeline"
          fact={`${presentValue(config.backend) || "Automatic"}${latency ? ` · ${latency} ms` : ""}`}
        >
          <DotWord tone={enabled ? "ok" : "warn"}>{enabled ? "On" : "Off"}</DotWord>
          {enabled ? null : (
            <Button
              dense
              variant="ghost"
              onClick={() =>
                openSurfaceOr("configure-settings", "/settings", "voice-typing")
              }
            >
              Turn on in Settings
            </Button>
          )}
        </GadgetRow>
        {hasKbWarning ? (
          <GadgetRow label="Project KB">
            <DotWord tone="warn">Missing</DotWord>
            <Button dense loading={kbBusy} onClick={() => void createStarterKb()}>
              Create
            </Button>
          </GadgetRow>
        ) : null}
      </GadgetGroup>
      <GadgetGroup label="Delivery">
        <GadgetRow label="Delivery target">
          <span className="prefs-value">
            {presentValue(target.label).trim()
              ? `${presentValue(target.label)}${
                  target.source === "hints" ? " · browser bridge" : ""
                }`
              : "Not known yet"}
          </span>
        </GadgetRow>
        {confidencePct ? (
          <GadgetRow label="Confidence">
            <span className="prefs-value">{confidencePct}%</span>
          </GadgetRow>
        ) : null}
        {/* HS-202-04 (UX-CANON A.8: no counters of zero) — the row stands
            only once there is a run to name. */}
        {runs > 0 ? (
          <GadgetRow label="Runs">
            <span className="prefs-value">{runs}</span>
          </GadgetRow>
        ) : null}
      </GadgetGroup>
      {/* HS-202-04 — this fold shows the readiness WIRE verbatim, zeros
          and all; a raw fold that edits the wire is a lie. It now says so
          in the owner's own word (debug hides behind RAW), which is the
          same title grammar Live uses (`LiveCore.tsx` RAW · ROUTE). */}
      {/* Betterment C8: the wire fold is behind RAW (Builder tools). */}
      {raw ? (
        <FoldGadget title="RAW · READINESS">
          <SurfaceCode>{JSON.stringify(resource.data, null, 2)}</SurfaceCode>
        </FoldGadget>
      ) : null}
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
      data-words=""
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
        verbs={<>{exportVerb}<Button dense variant="ghost" onClick={onOpenDoor}>Review</Button></>}
      />
    );
  }

  const config = (resource.data.config ?? {}) as Record<string, unknown>;
  const target = (resource.data.target ?? {}) as Record<string, unknown>;
  const warnings = Array.isArray(resource.data.warnings)
    ? resource.data.warnings
    : [];
  const egress = egressScopeLamp(resource.data.egress_boundary);
  const live = config.pipeline_enabled === true && warnings.length === 0;
  const state = live
    ? [
        target.label ? `→ ${presentValue(target.label)}` : "PIPELINE LIVE",
        config.max_total_latency_ms ? `${presentValue(config.max_total_latency_ms)} MS` : "",
      ].filter(Boolean).join(" · ")
    : config.pipeline_enabled === true
      ? (countToken(warnings.length, "WARNING") ?? "WARNINGS")
      : "PIPELINE OFF";

  return (
    <SurfaceFooter
      egress={
        <LampGadget
          label={egress.label}
          on={egress.tone === "ok"}
          tone={egress.tone}
        />
      }
      receipt={receiptSlot || <span className="surface-footer-readiness" role="status">{state}</span>}
      verbs={
        <>
          {live ? null : <Button dense variant="ghost" onClick={onOpenDoor}>Review</Button>}
          {exportVerb}
        </>
      }
    />
  );
}
