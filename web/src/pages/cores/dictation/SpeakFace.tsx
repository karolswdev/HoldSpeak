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
import { apiFetch } from "../../../lib/api";
import { DICTATION_FAILURES } from "../../../lib/dictationRecovery";
import type { MicPhase } from "../../../lib/micSession";

/** Whether a hostname is on a local/LAN network (RFC1918, loopback,
 *  link-local, CGNAT/Tailscale, or named local suffixes). Mirrors
 *  concierge_service._is_lan_host on the server. */
export function isLanHost(host: string): boolean {
  if (!host) return false;
  // Named local suffixes
  for (const suffix of [".local", ".internal", ".lan", ".home", ".localhost", ".ts.net"])
    if (host.endsWith(suffix)) return true;
  if (host === "localhost") return true;
  // IPv4 classification
  const parts = host.split(".");
  if (parts.length === 4 && parts.every((p) => /^\d{1,3}$/.test(p))) {
    const octets = parts.map(Number);
    if (octets.some((o) => o > 255)) return false;
    const [a, b] = octets;
    // 10.0.0.0/8
    if (a === 10) return true;
    // 172.16.0.0/12
    if (a === 172 && b >= 16 && b <= 31) return true;
    // 192.168.0.0/16
    if (a === 192 && b === 168) return true;
    // 127.0.0.0/8
    if (a === 127) return true;
    // 169.254.0.0/16 (link-local)
    if (a === 169 && b === 254) return true;
    // 100.64.0.0/10 (CGNAT / Tailscale)
    if (a === 100 && b >= 64 && b <= 127) return true;
  }
  return false;
}

/** Extract hostname from a URL string. */
function hostnameOf(url: string): string {
  try {
    return new URL(url).hostname;
  } catch {
    return "";
  }
}

/** Format the egress label from a host and its LAN classification. */
function egressFromHost(host: string): { egressLabel: string; egressHost: string } {
  if (!host || host === "localhost" || host === "127.0.0.1" || host === "::1")
    return { egressLabel: "THIS DEVICE", egressHost: "" };
  if (isLanHost(host))
    return { egressLabel: `${host} · LAN`, egressHost: host };
  return { egressLabel: "CLOUD", egressHost: host };
}

/** A lightweight profile record from /api/inference-targets. */
export interface TargetProfile {
  id: string;
  profile_id: string | null;
  name: string;
  base_url?: string;
  model?: string;
  engine?: string;
}

/** Derive the engine display name and egress from detect + assignment +
 *  optionally the legacy target profiles.
 *
 *  Resolution order:
 *  (a) Match by profileId on the detect engine
 *  (b) Match by base_url host: assignment profile's base_url host
 *      matches a detect engine's host
 *  (c) No match: name from the assignment's label (reject "Migrated ...")
 *      and classify the host with the LAN rule
 */
export type ResolvedEngine = {
  name: string | null;
  egressLabel: string;
  egressHost: string;
  /** The detect engine's state (READY, NOT_SET, etc.) when available. */
  engineState: string | null;
  keySet: boolean | null;
};

/** Try exact profileId / id matches against one candidate id. */
function exactMatch(engines: Engine[], pid: string): Engine | undefined {
  return engines.find(
    (e) =>
      e.profileId === pid ||
      e.id === pid ||
      e.id === `cloud:${pid}` ||
      e.id === `lan:${pid}` ||
      e.id === `local:${pid}`,
  );
}

/** Match a profile_id against detect engines.
 *
 *  (a) exact profileId / id match
 *  (d) strip leading "legacy-" repeatedly and retry exact matches
 *      (the 143 migration double-prefixed some ids: "legacy-legacy-intel")
 *  (e) match by legacyLabel === entry label (detect carries legacyLabel
 *      for every profile-born engine) */
export function findEngine(
  engines: Engine[],
  profileId: string,
  entryLabel?: string,
): Engine | undefined {
  // (a) exact
  const exact = exactMatch(engines, profileId);
  if (exact) return exact;

  // (d) strip leading "legacy-" repeatedly
  let stripped = profileId;
  while (stripped.startsWith("legacy-")) {
    stripped = stripped.slice("legacy-".length);
    const found = exactMatch(engines, stripped);
    if (found) return found;
  }

  // (e) match by legacyLabel
  if (entryLabel) {
    const byLabel = engines.find((e) => e.legacyLabel === entryLabel);
    if (byLabel) return byLabel;
  }

  return undefined;
}

/** Build the result from a matched detect engine. */
function fromDetectEngine(engine: Engine, fallbackLabel: string): ResolvedEngine {
  const name = engine.name || fallbackLabel;
  const state = engine.state ?? null;
  const keySet = engine.keySet ?? null;
  switch (engine.kind) {
    case "lan":
      return { name, egressLabel: `${engine.host} · LAN`, egressHost: engine.host, engineState: state, keySet };
    case "cloud":
      // Article III: the host is named on the egress chip.
      return {
        name,
        egressLabel: engine.host ? `${engine.host.toUpperCase()}` : "CLOUD",
        egressHost: engine.host,
        engineState: state,
        keySet,
      };
    default:
      return { name, egressLabel: "THIS DEVICE", egressHost: "", engineState: state, keySet };
  }
}

const NO_ENGINE: ResolvedEngine = { name: null, egressLabel: "THIS DEVICE", egressHost: "", engineState: null, keySet: null };

export function resolveEngine(
  assignment: AssignmentEditorProjection | null,
  engines: Engine[],
  targets?: TargetProfile[],
): ResolvedEngine {
  const entries = assignment?.effective?.assignment?.entries;
  if (!entries?.length) return NO_ENGINE;

  const profileId = entries[0].profile_id;
  const label = entries[0].label;

  // (a) Match by profileId on the detect engine
  const byProfile = findEngine(engines, profileId, label);
  if (byProfile) return fromDetectEngine(byProfile, label);

  // Find the profile's base_url from the targets list
  const targetProfile = targets?.find(
    (t) => t.profile_id === profileId || t.id === profileId,
  );
  const baseUrl = targetProfile?.base_url ?? "";
  const profileHost = hostnameOf(baseUrl);

  // (b) Match by base_url host against detect engines
  if (profileHost) {
    const byHost = engines.find((e) => e.host === profileHost);
    if (byHost) return fromDetectEngine(byHost, label);
  }

  // (c) No detect match — name and classify from what we have
  const isMigrationLabel = label.startsWith("Migrated");

  let name: string;
  if (!isMigrationLabel) {
    name = label;
  } else if (targetProfile?.model && targetProfile.model !== "default") {
    name = targetProfile.model;
  } else if (baseUrl) {
    try {
      const u = new URL(baseUrl);
      name = u.port ? `${u.hostname}:${u.port}` : u.hostname;
    } catch {
      name = label;
    }
  } else {
    name = label;
  }

  if (profileHost) {
    const egress = egressFromHost(profileHost);
    return { name, ...egress, engineState: null, keySet: null };
  }

  switch (entries[0].boundary) {
    case "private_network":
      return { name, egressLabel: "LAN", egressHost: "", engineState: null, keySet: null };
    case "mesh":
      return { name, egressLabel: "PAIRED", egressHost: "", engineState: null, keySet: null };
    case "cloud":
      return { name, egressLabel: "CLOUD", egressHost: "", engineState: null, keySet: null };
    default:
      return { name, egressLabel: "THIS DEVICE", egressHost: "", engineState: null, keySet: null };
  }
}

export function SpeakFace() {
  const announce = useAnnounce();
  const deck = useSpeakDeck(announce);

  // Engine: assignment projection + concierge detect + legacy targets
  const [assignment, setAssignment] = useState<AssignmentEditorProjection | null>(null);
  const [engines, setEngines] = useState<Engine[]>([]);
  const [targets, setTargets] = useState<TargetProfile[]>([]);
  const [detectStatus, setDetectStatus] = useState<"pending" | "ok" | "failed">("pending");
  useEffect(() => {
    void getAssignmentEditor(
      { kind: "capability", capability_id: "speech.rewrite" },
      "speech.rewrite",
    ).then(setAssignment).catch(() => {});
    void conciergeDetect()
      .then((r) => { setEngines(r.engines); setDetectStatus("ok"); })
      .catch(() => { setDetectStatus("failed"); });
    void apiFetch<{ targets?: TargetProfile[] }>("/api/inference-targets")
      .then((r) => setTargets(r.targets ?? []))
      .catch(() => {});
  }, []);

  const resolved = resolveEngine(assignment, engines, targets);

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
      <EngineRow engine={resolved.name} egress={resolved.egressLabel} engineState={resolved.engineState} keySet={resolved.keySet} detectStatus={detectStatus} readiness={deck} />

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
  engineState,
  keySet,
  detectStatus,
  readiness,
}: {
  engine: string | null;
  egress: string;
  engineState: string | null;
  keySet: boolean | null;
  detectStatus: "pending" | "ok" | "failed";
  readiness: ReturnType<typeof useSpeakDeck>;
}) {
  const openConcierge = () => {
    import("../../../desk/shell").then(({ openSurface }) =>
      openSurface("open-concierge"),
    );
  };

  // No engine assigned at all
  if (!engine) {
    return (
      <div className="speak-engine" data-engine-state="not-set">
        <span className="speak-engine-caption">DICTATION</span>
        <span className="speak-engine-dot">{"·"}</span>
        <StateChip state="warning" label="NOT SET" />
        <span className="speak-transport-spacer" />
        <Button variant="ghost" dense onClick={openConcierge}>
          Choose
        </Button>
      </div>
    );
  }

  // Pending: detect hasn't resolved yet.  Show the assignment name
  // muted with CHECKING... — no state chip, no host claim beyond the
  // assignment boundary's base_url LAN rule (already in egress).
  if (detectStatus === "pending") {
    return (
      <div className="speak-engine" data-engine-state="pending">
        <span className="speak-engine-caption">DICTATION</span>
        <span className="speak-engine-dot">{"·"}</span>
        <span className="speak-engine-name" data-muted="">{engine}</span>
        {egress !== "THIS DEVICE" && egress !== "CLOUD" && egress !== "LAN" ? (
          <EgressChip label={egress} />
        ) : null}
        <span className="speak-transport-spacer" />
        <span className="speak-engine-checking">CHECKING...</span>
      </div>
    );
  }

  // Failed: detect errored.  State is unknown — never claim READY.
  if (detectStatus === "failed" && !engineState) {
    return (
      <div className="speak-engine" data-engine-state="unknown">
        <span className="speak-engine-caption">DICTATION</span>
        <span className="speak-engine-dot">{"·"}</span>
        <span className="speak-engine-name">{engine}</span>
        {egress ? <EgressChip label={egress} /> : null}
        <span className="speak-transport-spacer" />
        <StateChip state="warning" label="UNKNOWN" />
        <Button variant="ghost" dense onClick={openConcierge}>
          Choose
        </Button>
      </div>
    );
  }

  // Detect resolved — derive the state chip from the engine's state.
  let dataState: string;
  let chipState: "success" | "warning";
  let chipLabel: string;
  let showChoose = false;

  if (engineState === "NOT_SET") {
    dataState = "not-set";
    chipState = "warning";
    chipLabel = keySet === false ? "KEY NOT SET" : "NOT SET";
    showChoose = true;
  } else if (engineState === "UNREACHABLE") {
    dataState = "unknown";
    chipState = "warning";
    chipLabel = "UNREACHABLE";
    showChoose = true;
  } else if (engineState === "READY") {
    dataState = "ready";
    chipState = "success";
    chipLabel = "READY";
  } else if (engineState === "WAITING" || engineState === "CHECKING") {
    dataState = "waiting";
    chipState = "warning";
    chipLabel = engineState;
    showChoose = true;
  } else if (engineState) {
    dataState = "unknown";
    chipState = "warning";
    chipLabel = engineState.replace(/_/g, " ");
    showChoose = true;
  } else {
    // detectStatus === "ok" but no engine matched — fallback
    dataState = "unknown";
    chipState = "warning";
    chipLabel = "UNKNOWN";
    showChoose = true;
  }

  return (
    <div className="speak-engine" data-engine-state={dataState}>
      <span className="speak-engine-caption">DICTATION</span>
      <span className="speak-engine-dot">{"·"}</span>
      <span className="speak-engine-name">{engine}</span>
      <EgressChip label={egress} />
      <span className="speak-transport-spacer" />
      <StateChip state={chipState} label={chipLabel} />
      {showChoose ? (
        <Button variant="ghost" dense onClick={openConcierge}>
          Choose
        </Button>
      ) : null}
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
        <span className="speak-detail-label">Runs on</span>
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
