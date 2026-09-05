// HS-170-04 — Speak: the face built to the settled artboards.
// One screen: talk, see it land, teach once.  Everything that was
// the cockpit register strip folds behind > Details.
//
// Transport row (Talk MicButton transport + Open latch + LedMeter)
// Utterance well (PadGadget, placeholder "Talk, or type here")
// LANDS IN row (target name · picker · DRY RUN toggle · latency token)
// RESULT row (landed text + OK/Wrong ghosts; Wrong unfolds teach row)
// ENGINE row (DICTATION · model name · THIS DEVICE chip · READY chip;
//             or NOT SET + Choose when no engine)
// > Details (Disclosure: the old register strip, folded)
import { useCallback, useEffect, useMemo, useState, type KeyboardEvent } from "react";
import { useAnnounce } from "./shared";
import { useSpeakDeck } from "./useSpeakDeck";
import {
  STATE_TOKENS,
  MIC_PHASE_FACT,
  MIC_PHASE_LIVE,
  AIM_OPTIONS,
  AIM_FACT,
  refusalLabel,
} from "./shared";
import { MicButton, type MicState } from "../../../desk/surface/controls/MicButton";
import { Button } from "../../../components/signal/Signal";
import {
  LedMeter,
  TransportKey,
  LampGadget,
  CycleGadget,
  PadGadget,
  StringGadget,
  EgressChip,
  CheckGadget,
} from "../../../desk/surface/gadgets";
import { StateChip } from "../../../desk/surface/patterns";
import { Disclosure } from "../../../desk/surface/patterns";
import { presentValue } from "../../../desk/surface/format";
import { egressScopeLamp } from "../../../desk/inferenceEgress";
import {
  getAssignmentEditor,
  type AssignmentEditorProjection,
} from "../assignmentExperience";
import {
  conciergeDetect,
  type Engine,
} from "../../../features/concierge/api";
import { DICTATION_FAILURES } from "../../../lib/dictationRecovery";
import type { MicPhase } from "../../../lib/micSession";

/** Derive the engine display name and egress from detect + assignment.
 *  The detect payload carries the real served model name and host;
 *  the assignment's label is often a stale migration artifact. */
export function resolveEngine(
  assignment: AssignmentEditorProjection | null,
  engines: Engine[],
): { name: string | null; egressLabel: string; egressHost: string } {
  const entries = assignment?.effective?.assignment?.entries;
  if (!entries?.length) return { name: null, egressLabel: "THIS DEVICE", egressHost: "" };

  const profileId = entries[0].profile_id;
  const boundary = entries[0].boundary;
  const matched = engines.find(
    (e) => e.profileId === profileId || e.id === profileId,
  );

  // Name: prefer the detect engine's name; fall back to assignment label.
  const name = matched?.name || entries.map((e) => e.label).join(" + ");

  // Host: the detect engine carries the real host (e.g. "192.168.1.43").
  // Kind determines the chip label.
  if (matched) {
    switch (matched.kind) {
      case "lan":
        return { name, egressLabel: `${matched.host} · LAN`, egressHost: matched.host };
      case "cloud":
        return { name, egressLabel: "CLOUD", egressHost: matched.host };
      default:
        return { name, egressLabel: "THIS DEVICE", egressHost: "" };
    }
  }

  // No detect match — fall back to the assignment's boundary field.
  switch (boundary) {
    case "private_network":
      return { name, egressLabel: "LAN", egressHost: "" };
    case "cloud":
      return { name, egressLabel: "CLOUD", egressHost: "" };
    case "mesh":
      return { name, egressLabel: "PAIRED", egressHost: "" };
    default:
      return { name, egressLabel: "THIS DEVICE", egressHost: "" };
  }
}

export function SpeakFace() {
  const announce = useAnnounce();
  const deck = useSpeakDeck(announce);

  // Engine: assignment projection + concierge detect for real name/host
  const [assignment, setAssignment] = useState<AssignmentEditorProjection | null>(null);
  const [engines, setEngines] = useState<Engine[]>([]);
  useEffect(() => {
    void getAssignmentEditor(
      { kind: "capability", capability_id: "speech.rewrite" },
      "speech.rewrite",
    ).then(setAssignment).catch(() => {});
    void conciergeDetect()
      .then((r) => setEngines(r.engines))
      .catch(() => {});
  }, []);

  const resolved = resolveEngine(assignment, engines);

  return (
    <div className="speak-face">
      {/* 1. THE TRANSPORT ROW */}
      <TransportRow
        deck={deck}
        announce={announce}
      />

      {/* 2. THE UTTERANCE WELL */}
      <div className="speak-well">
        <PadGadget
          label="Utterance"
          value={deck.utterance}
          onChange={deck.setUtterance}
          placeholder="Talk, or type here"
          onKeyDown={(e: KeyboardEvent<HTMLTextAreaElement>) => {
            if ((e.metaKey || e.ctrlKey) && e.key === "Enter" && deck.utterance.trim()) {
              e.preventDefault();
              if (deck.previewOnly) void deck.run();
              else void deck.deliver(deck.utterance);
            }
          }}
        />
      </div>

      {/* 3. LANDS IN row */}
      <LandsInRow deck={deck} />

      {/* 4. RESULT (when landed) */}
      {deck.result ? (
        <ResultRow
          result={deck.result}
          verdict={deck.verdict}
          setVerdict={deck.setVerdict}
          correctionKind={deck.correctionKind}
          setCorrectionKind={deck.setCorrectionKind}
          correctionValue={deck.correctionValue}
          setCorrectionValue={deck.setCorrectionValue}
          busy={deck.busy}
          onTeach={() => void deck.teach()}
          announce={announce}
        />
      ) : null}

      {/* 5. ENGINE row */}
      <EngineRow engine={resolved.name} egress={resolved.egressLabel} readiness={deck} />

      {/* 6. Details (Disclosure, folded) */}
      <Disclosure label="Details" defaultOpen={false}>
        <DetailsContent deck={deck} />
      </Disclosure>
    </div>
  );
}

/* ── Transport row ── */

function TransportRow({
  deck,
  announce,
}: {
  deck: ReturnType<typeof useSpeakDeck>;
  announce: (text: string, tone?: "ok" | "warn") => void;
}) {
  return (
    <div className="speak-transport" role="group" aria-label="Dictation transport">
      <MicButton
        variant="transport"
        draftScope="dictation-dry-run-voice"
        label="Talk"
        onText={deck.onReleased}
        onState={(next) => {
          if (next === "busy") deck.releasedAt.current = performance.now();
          if (next === "listening") {
            deck.releasedAt.current = null;
            deck.setPhase("idle");
            deck.setLandedMs(null);
            deck.setRefusal("");
          }
          deck.setMicState(next);
        }}
        onLevel={deck.setLevel}
        onCommand={(fired) => {
          deck.setLandedMs(null);
          if (fired.ok) {
            deck.setPhase("landed");
            deck.setRefusal("");
            announce(`COMMAND · ${fired.preview}`);
          } else {
            deck.setPhase("refused");
            deck.setRefusal("command_failed");
            announce(`COMMAND FAILED · ${fired.preview}`, "warn");
          }
        }}
        onFailure={(category) => {
          deck.setPhase("refused");
          deck.setRefusal(category);
          deck.setLandedMs(null);
          announce(DICTATION_FAILURES[category].message, "warn");
        }}
      />
      <TransportKey
        label="Open mic"
        word="Open"
        glyph={"◉"}
        active={deck.openMic}
        disabled={!deck.captureSupported}
        title={deck.captureReason ?? undefined}
        onClick={() => void deck.toggleOpenMic()}
      />
      <span className="speak-transport-spacer" />
      <LedMeter label="Level" value={deck.level} scanning={deck.micState === "busy"} />
    </div>
  );
}

/* ── LANDS IN row ── */

function LandsInRow({ deck }: { deck: ReturnType<typeof useSpeakDeck> }) {
  const targetName =
    presentValue((deck.readinessTarget as Record<string, unknown>).label) || "---";

  return (
    <div className="speak-lands-in">
      <span className="speak-lands-in-caption">LANDS IN</span>
      <span className="speak-lands-in-dot">{"·"}</span>
      <span className="speak-lands-in-target">{targetName}</span>
      {deck.landedMs !== null ? (
        <>
          <span className="speak-lands-in-dot">{"·"}</span>
          <span className="speak-lands-in-latency">{deck.landedMs} MS</span>
        </>
      ) : null}
      <span className="speak-transport-spacer" />
      <CycleGadget
        label="Aim"
        value={deck.aim}
        options={AIM_OPTIONS}
        onChange={deck.pickAim}
      />
      <CheckGadget
        label="DRY RUN"
        checked={deck.rehearse}
        onChange={deck.setRehearse}
        variant="token"
      />
    </div>
  );
}

/* ── RESULT row ── */

function ResultRow({
  result,
  verdict,
  setVerdict,
  correctionKind,
  setCorrectionKind,
  correctionValue,
  setCorrectionValue,
  busy,
  onTeach,
  announce,
}: {
  result: Record<string, unknown>;
  verdict: "" | "right" | "wrong";
  setVerdict: (next: "" | "right" | "wrong") => void;
  correctionKind: string;
  setCorrectionKind: (next: string) => void;
  correctionValue: string;
  setCorrectionValue: (next: string) => void;
  busy: boolean;
  onTeach: () => void;
  announce: (text: string, tone?: "ok" | "warn") => void;
}) {
  const finalText = String(result.final_text ?? result.text ?? result.output ?? "");

  return (
    <section className="speak-result" aria-label="Pipeline result">
      <div className="speak-result-line">
        <span className="speak-result-text">{finalText}</span>
        <Button
          variant="ghost"
          dense
          onClick={() => {
            setVerdict("right");
            announce("Marked OK");
          }}
        >
          OK
        </Button>
        <Button
          variant="ghost"
          dense
          onClick={() => setVerdict("wrong")}
        >
          Wrong
        </Button>
      </div>
      {verdict === "wrong" ? (
        <div
          className="speak-teach"
          role="group"
          aria-label="Correct this result"
        >
          <CycleGadget
            label="Correction field"
            value={correctionKind}
            options={[
              { value: "target", label: "Delivery target" },
              { value: "intent", label: "Intent" },
            ]}
            onChange={setCorrectionKind}
          />
          <StringGadget
            label="Correct value"
            value={correctionValue}
            onChange={setCorrectionValue}
            placeholder="Terminal"
          />
          <Button
            variant="primary"
            dense
            loading={busy}
            disabled={!correctionValue.trim()}
            aria-label="Teach correction"
            onClick={onTeach}
          >
            Teach
          </Button>
        </div>
      ) : null}
    </section>
  );
}

/* ── ENGINE row ── */

function EngineRow({
  engine,
  egress,
  readiness,
}: {
  engine: string | null;
  egress: string;
  readiness: ReturnType<typeof useSpeakDeck>;
}) {
  const pipelineReady = readiness.pipelineOn && readiness.readinessConfig.pipeline_enabled === true;

  if (!engine) {
    return (
      <div className="speak-engine">
        <span className="speak-engine-caption">DICTATION</span>
        <span className="speak-engine-dot">{"·"}</span>
        <StateChip state="warning" label="NOT SET" />
        <span className="speak-transport-spacer" />
        <Button
          variant="ghost"
          dense
          onClick={() => {
            import("../../../desk/shell").then(({ openSurface }) =>
              openSurface("open-concierge"),
            );
          }}
        >
          Choose
        </Button>
      </div>
    );
  }

  return (
    <div className="speak-engine">
      <span className="speak-engine-caption">DICTATION</span>
      <span className="speak-engine-dot">{"·"}</span>
      <span className="speak-engine-name">{engine}</span>
      <EgressChip label={egress} />
      <span className="speak-transport-spacer" />
      <StateChip
        state={pipelineReady ? "success" : "warning"}
        label={pipelineReady ? "READY" : "NOT READY"}
      />
    </div>
  );
}

/* ── Details content (the old register strip, folded) ── */

function DetailsContent({ deck }: { deck: ReturnType<typeof useSpeakDeck> }) {
  return (
    <div className="speak-details">
      <div className="speak-detail-row">
        <span className="speak-detail-label">Pipeline</span>
        <LampGadget
          label={deck.pipelineOn ? "Live" : "Off"}
          on={deck.pipelineOn}
          tone={deck.pipelineOn ? "ok" : "warn"}
        />
      </div>
      <div className="speak-detail-row">
        <span className="speak-detail-label">Target</span>
        <span className="speak-detail-value">
          {presentValue((deck.readinessTarget as Record<string, unknown>).label) || "—"}
        </span>
      </div>
      <div className="speak-detail-row">
        <span className="speak-detail-label">Mic</span>
        <LampGadget
          label={MIC_PHASE_FACT[deck.micPhase]}
          on={MIC_PHASE_LIVE.includes(deck.micPhase)}
          tone={MIC_PHASE_LIVE.includes(deck.micPhase) ? "ok" : "warn"}
        />
      </div>
      <div className="speak-detail-row">
        <span className="speak-detail-label">Landed</span>
        <span className="speak-detail-value">
          {deck.phase === "refused" && deck.refusal
            ? refusalLabel(deck.refusal)
            : deck.landedMs !== null
              ? `${deck.landedMs} MS`
              : "—"}
        </span>
      </div>
      <div className="speak-detail-row">
        <span className="speak-detail-label">Budget</span>
        <span className="speak-detail-value">
          {presentValue(deck.readinessConfig.max_total_latency_ms)
            ? `${presentValue(deck.readinessConfig.max_total_latency_ms)} MS`
            : "—"}
        </span>
      </div>
      <div className="speak-detail-row">
        <span className="speak-detail-label">State</span>
        <span className="speak-detail-value speak-detail-state">
          {STATE_TOKENS.map((token) => (
            <span
              key={token.id}
              className="speak-detail-state-token"
              data-active={deck.activeState === token.id || undefined}
            >
              {token.label}
            </span>
          ))}
        </span>
      </div>
    </div>
  );
}
