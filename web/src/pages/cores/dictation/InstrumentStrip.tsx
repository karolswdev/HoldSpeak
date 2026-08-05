// HS-111-02 — the instrument strip: TALK transport key, LED level meter,
// STATE register, etched readout cells.
import { MicButton, type MicState } from "../../../desk/components/MicButton";
import { presentValue } from "../../../desk/surface/format";
import {
  LampGadget,
  LedMeter,
  TransportKey,
} from "../../../desk/surface/gadgets";
import {
  STATE_TOKENS,
  MIC_PHASE_FACT,
  MIC_PHASE_LIVE,
  refusalLabel,
} from "./shared";
import type { MicPhase } from "../../../lib/micSession";
import type { DictationFailure } from "../../../lib/dictationRecovery";
import { DICTATION_FAILURES } from "../../../lib/dictationRecovery";

export function InstrumentStrip({
  micState,
  onMicState,
  level,
  onLevel,
  onReleased,
  onFailure,
  releasedAt,
  phase,
  setPhase,
  setLandedMs,
  setRefusal,
  announce,
  openMic,
  toggleOpenMic,
  captureSupported,
  captureReason,
  micPhase,
  pipelineOn,
  readinessTarget,
  readinessConfig,
  landedMs,
  refusal,
  activeState,
}: {
  micState: MicState;
  onMicState: (next: MicState) => void;
  level: number;
  onLevel: (next: number) => void;
  onReleased: (text: string) => void;
  onFailure: (category: DictationFailure) => void;
  releasedAt: React.RefObject<number | null>;
  phase: "idle" | "busy" | "landed" | "refused";
  setPhase: (next: "idle" | "busy" | "landed" | "refused") => void;
  setLandedMs: (next: number | null) => void;
  setRefusal: (next: string) => void;
  announce: (text: string, tone?: "ok" | "warn") => void;
  openMic: boolean;
  toggleOpenMic: () => void;
  captureSupported: boolean;
  captureReason: string | null;
  micPhase: MicPhase;
  pipelineOn: boolean;
  readinessTarget: Record<string, unknown>;
  readinessConfig: Record<string, unknown>;
  landedMs: number | null;
  refusal: string;
  activeState: string;
}) {
  return (
    <div className="speak-strip" role="group" aria-label="Dictation deck">
      <MicButton
        variant="transport"
        draftScope="dictation-dry-run-voice"
        label="Hold to talk"
        onText={onReleased}
        onState={(next) => {
          // the key came up: start the release-to-landed clock and
          // clear the previous verdict off the register.
          if (next === "busy") releasedAt.current = performance.now();
          if (next === "listening") {
            releasedAt.current = null;
            setPhase("idle");
            setLandedMs(null);
            setRefusal("");
          }
          onMicState(next);
        }}
        onLevel={onLevel}
        onFailure={(category) => {
          setPhase("refused");
          setRefusal(category);
          setLandedMs(null);
          announce(`⚠ ${DICTATION_FAILURES[category].message}`, "warn");
        }}
      />
      {/* HS-112-06 — the open mic latch: one grant, held open, VAD
          segmenting; pressing it again drops the stream for real. */}
      <TransportKey
        label="Open mic"
        word="Open"
        glyph="◉"
        active={openMic}
        // a mic this browser cannot open is visible, disabled, and says
        // why — it never vanishes and never refuses on click.
        disabled={!captureSupported}
        title={captureReason ?? undefined}
        onClick={() => void toggleOpenMic()}
      />
      <LedMeter label="Level" value={level} scanning={micState === "busy"} />
      <span className="speak-register" aria-label="Dictation state">
        <span className="speak-register-axis">State</span>
        {STATE_TOKENS.map((token) => (
          <span
            key={token.id}
            className="speak-register-token"
            data-active={activeState === token.id || undefined}
          >
            {token.label}
          </span>
        ))}
      </span>
      <span className="speak-cells">
        <span className="speak-cell">
          <span className="speak-cell-label">Pipeline</span>
          <span className="speak-cell-value">
            <LampGadget
              label={pipelineOn ? "Live" : "Off"}
              on={pipelineOn}
              tone={pipelineOn ? "ok" : "warn"}
            />
          </span>
        </span>
        <span className="speak-cell">
          <span className="speak-cell-label">{"-> Target"}</span>
          <span className="speak-cell-value">
            {presentValue(readinessTarget.label) || "—"}
          </span>
        </span>
        <span className="speak-cell">
          <span className="speak-cell-label">Mic</span>
          <span className="speak-cell-value" aria-label="Mic session">
            <LampGadget
              label={MIC_PHASE_FACT[micPhase]}
              on={MIC_PHASE_LIVE.includes(micPhase)}
              tone={MIC_PHASE_LIVE.includes(micPhase) ? "ok" : "warn"}
            />
          </span>
        </span>
        <span className="speak-cell">
          <span className="speak-cell-label">Landed</span>
          <span className="speak-cell-value" aria-label="Landed latency">
            {phase === "refused" && refusal
              ? refusalLabel(refusal)
              : landedMs !== null
                ? `${landedMs} MS`
                : "—"}
          </span>
        </span>
        <span className="speak-cell">
          <span className="speak-cell-label">Budget</span>
          <span className="speak-cell-value">
            {presentValue(readinessConfig.max_total_latency_ms)
              ? `${presentValue(readinessConfig.max_total_latency_ms)} MS`
              : "—"}
          </span>
        </span>
      </span>
    </div>
  );
}
