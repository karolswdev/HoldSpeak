// useSpeakDeck — the 20+ state variables and 8 async handlers that
// drive the SpeakFace deck, extracted from DictationCore.
import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch, readableError } from "../../../lib/api";
import {
  DICTATION_FAILURES,
  applicableActions,
  dictationFailure,
  type DictationFailure,
} from "../../../lib/dictationRecovery";
import { useDurableDraft } from "../../../lib/durableDraft";
import { useResource } from "../../pageSupport";
import type {
  DictationDryRunResponse,
  DictationReadinessResponse,
} from "../core-types";
import type { InferenceTarget } from "../../../desk/api";
import type { MicState } from "../../../desk/components/MicButton";
import { openSurfaceOr } from "../../../desk/shell";
import {
  subscribeMicPhase,
  micCaptureSupported,
  micCaptureReason,
  type MicPhase,
} from "../../../lib/micSession";
import { FloorHeldError } from "../../../lib/audioFloor";
import { openMicDrop, openMicListen } from "../../../lib/openMic";
import { presentValue } from "../../../desk/surface/format";
import {
  AIM_KEY,
  AIM_FACT,
  refusalLabel,
  refusalCode,
  newDeliveryId,
} from "./shared";

export function useSpeakDeck(announce: (text: string, tone?: "ok" | "warn") => void) {
  const {
    value: utterance,
    setDraft: setUtterance,
    recovered: utteranceRecovered,
    clearPersisted,
  } = useDurableDraft("dictation-dry-run");
  const [projectRoot, setProjectRoot] = useState(
    () => localStorage.getItem("holdspeak.projectRootOverride") ?? "",
  );
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");
  const [failure, setFailure] = useState<DictationFailure | null>(null);
  const [busy, setBusy] = useState(false);
  const [correctionKind, setCorrectionKind] = useState("target");
  const [correctionValue, setCorrectionValue] = useState("");
  const [verdict, setVerdict] = useState<"" | "right" | "wrong">("");
  const [targets, setTargets] = useState<InferenceTarget[]>([]);
  const [targetId, setTargetId] = useState("this_machine");
  const [micState, setMicState] = useState<MicState>("idle");
  const [level, setLevel] = useState(0);
  // HS-112-02 — the delivery half of the deck.
  const [aim, setAim] = useState(
    () => localStorage.getItem(AIM_KEY) ?? "focused",
  );
  const [rehearse, setRehearse] = useState(false);
  const [phase, setPhase] = useState<"idle" | "busy" | "landed" | "refused">(
    "idle",
  );
  const [landedMs, setLandedMs] = useState<number | null>(null);
  const [refusal, setRefusal] = useState("");
  // release-to-landed is measured from the moment the key came up.
  const releasedAt = useRef<number | null>(null);
  /* HS-112-06 — the open mic: one grant, held open, VAD-segmented.
     Opt-in per session; the phase below is the session's own truth
     (CLOSED means the tracks are stopped, never merely muted). */
  const [openMic, setOpenMic] = useState(false);
  const [micPhase, setMicPhase] = useState<MicPhase>("closed");
  const captureSupported = micCaptureSupported();
  const captureReason = captureSupported ? null : micCaptureReason();
  // The strip's readout cells read the same wire the footer reads.
  const stripRoot = localStorage.getItem("holdspeak.projectRootOverride") ?? "";
  const readiness = useResource<DictationReadinessResponse>(
    `/api/dictation/readiness${stripRoot ? `?project_root=${encodeURIComponent(stripRoot)}` : ""}`,
    {},
  );
  const readinessConfig = (readiness.data.config ?? {}) as Record<string, unknown>;
  const readinessTarget = (readiness.data.target ?? {}) as Record<string, unknown>;
  const pipelineOn = readinessConfig.pipeline_enabled === true;
  useEffect(() => {
    if (utteranceRecovered) announce("Draft restored");
  }, [utteranceRecovered, announce]);
  /* REHEARSE — the explicit dry run. It previews the pipeline and
     delivers NOTHING; it is never what a plain TALK release does.
     HS-130-07: an optional `profileId` is a TRANSIENT one-run target
     override (the "Retry on" recovery). It rides the dry-run request for
     this run only and never persists to settings. */
  const run = async (text: string = utterance, profileId?: string | null) => {
    setBusy(true);
    setError("");
    setFailure(null);
    setVerdict("");
    try {
      setResult(
        await apiFetch<DictationDryRunResponse>("/api/dictation/dry-run", {
          method: "POST",
          json: {
            utterance: text,
            ...(projectRoot ? { project_root: projectRoot } : {}),
            ...(profileId !== undefined
              ? { profile_id: profileId === "this_machine" ? null : profileId }
              : {}),
          },
        }),
      );
      setPhase("idle");
      announce("REHEARSED · NOT DELIVERED");
      localStorage.setItem("holdspeak.projectRootOverride", projectRoot);
    } catch (reason) {
      const category = dictationFailure(reason);
      setFailure(category);
      const message = DICTATION_FAILURES[category].message;
      setError(message);
      announce(`⚠ ${message}`, "warn");
    } finally {
      setBusy(false);
    }
  };

  const pickAim = (next: string) => {
    setAim(next);
    localStorage.setItem(AIM_KEY, next);
  };

  const refuse = (code: string) => {
    setLandedMs(null);
    setPhase("refused");
    setRefusal(code);
    announce(`⚠ REFUSED · ${refusalLabel(code)}`, "warn");
  };

  /* THE FLAGSHIP ACT — release TALK and the words land where you aimed
     them, through the same route, pipeline, journal, kernel warrant and
     idempotency claim as the global hotkey. One id per utterance. */
  const deliver = async (text: string) => {
    const spoken = text.trim();
    if (!spoken) return;
    const since = releasedAt.current ?? performance.now();
    setBusy(true);
    setPhase("busy");
    setError("");
    setFailure(null);
    setRefusal("");
    setVerdict("");
    try {
      const landed = await apiFetch<DictationDryRunResponse>("/api/dictation/remote", {
        method: "POST",
        json: {
          text: spoken,
          target_mode: aim === "agent" ? "agent" : "focused",
          delivery_id: newDeliveryId(),
          // an aimed AGENT send refuses rather than free-typing into
          // whatever happens to be focused.
          ...(aim === "agent" ? { require_agent: true } : {}),
        },
      });
      setResult(landed);
      if (landed.delivered === false) {
        refuse("no_delivery_target");
        return;
      }
      const took = Math.round(performance.now() - since);
      setLandedMs(took);
      setPhase("landed");
      announce(`LANDED ${took} MS -> ${AIM_FACT[aim]}`);
    } catch (reason) {
      const code = refusalCode(reason);
      if (code) {
        refuse(code);
        return;
      }
      const category = dictationFailure(reason);
      setFailure(category);
      const message = DICTATION_FAILURES[category].message;
      setError(message);
      setLandedMs(null);
      setPhase("refused");
      setRefusal(category);
      announce(`⚠ ${message}`, "warn");
    } finally {
      setBusy(false);
    }
  };

  /* The one gesture contract: hold, talk, release. What happens on
     release is the AIM's business, never a hidden default. */
  const onReleased = (text: string) => {
    setUtterance(text);
    if (aim === "field" || !text.trim()) return;
    if (rehearse) void run(text);
    else void deliver(text);
  };

  /* An ambient utterance travels the SAME road as a released TALK — the
     aim, the rehearsal rule, the delivery id, the receipts. The ref
     keeps the open mic's long-lived handler on the current aim. */
  const releaseRef = useRef(onReleased);
  releaseRef.current = onReleased;

  useEffect(() => subscribeMicPhase(setMicPhase), []);
  // Leaving the room drops the stream: no grant outlives the deck.
  useEffect(() => () => openMicDrop(), []);

  const toggleOpenMic = async () => {
    if (openMic) {
      openMicDrop();
      setOpenMic(false);
      announce("OPEN MIC CLOSED");
      return;
    }
    try {
      await openMicListen({
        onText: (text) => releaseRef.current(text),
        onRefusal: (reason) => {
          const category = dictationFailure(reason);
          setFailure(category);
          setError(DICTATION_FAILURES[category].message);
          setPhase("refused");
          setRefusal(category);
          announce(`⚠ ${DICTATION_FAILURES[category].message}`, "warn");
        },
        // the floor was taken (a meeting started): the mic is already
        // down — the room says who took it, in flow.
        onFloorLost: (reason) => {
          setOpenMic(false);
          refuse(reason.refusal);
        },
        // HS-131-09 (Sol Amendment 3): the server's admitted interval ended
        // (inactivity, the 30-minute ceiling, the budget, a cancel, or a
        // revocation). The mic is already down; the latch follows so continuing
        // takes a fresh, authenticated click.
        onIntervalClosed: (reason) => {
          setOpenMic(false);
          const category = dictationFailure(reason);
          setFailure(category);
          setError(DICTATION_FAILURES[category].message);
          setPhase("refused");
          setRefusal(category);
          announce("OPEN MIC CLOSED. CLICK TO SPEAK AGAIN", "warn");
        },
      });
      setOpenMic(true);
      announce("OPEN MIC LISTENING");
    } catch (reason) {
      setOpenMic(false);
      // A floor refusal names its owner ("FLOOR HELD MEETING"); anything
      // else falls back to the shared dictation failure vocabulary.
      if (reason instanceof FloorHeldError) {
        refuse(reason.refusal);
        return;
      }
      const category = dictationFailure(reason);
      setFailure(category);
      setError(DICTATION_FAILURES[category].message);
      setPhase("refused");
      setRefusal(category);
      announce(`⚠ ${DICTATION_FAILURES[category].message}`, "warn");
    }
  };
  const actions = failure
    ? applicableActions(failure, { draftPresent: Boolean(utterance.trim()) })
    : [];
  useEffect(() => {
    if (!actions.includes("alternate_runs_on") || targets.length) return;
    let mounted = true;
    void apiFetch<{ targets?: InferenceTarget[] }>("/api/inference-targets")
      .then((result) => {
        if (mounted && Array.isArray(result.targets))
          setTargets(result.targets);
      })
      .catch(() => undefined);
    return () => {
      mounted = false;
    };
  }, [actions, targets.length]);
  /* HS-130-07: "Run elsewhere" is a TRANSIENT one-run override, not a
     standing preference. It retries THIS run on the chosen target and
     leaves `dictation.runtime.profile_id` in settings untouched — a
     recovery must never silently rewrite the desk's standing target
     (Settings is the one writer of that preference). */
  const runElsewhere = async (id: string) => {
    setTargetId(id);
    try {
      await run(utterance, id);
    } catch (reason) {
      announce(`⚠ ${readableError(reason)}`, "warn");
    }
  };
  const keepDraft = async () => {
    if (!utterance.trim()) return;
    try {
      await apiFetch("/api/notes", {
        method: "POST",
        json: {
          title: "Retained dictation draft",
          body_markdown: utterance,
          tags: ["dictation"],
        },
      });
      clearPersisted();
      announce("Kept as a Note on your Desk.");
    } catch (reason) {
      announce(
        `⚠ The Note was not kept. Your draft remains editable. ${readableError(reason)}`,
        "warn",
      );
    }
  };
  const teach = async () => {
    setBusy(true);
    try {
      const journalId = result?.journal_id;
      await apiFetch(
        journalId !== undefined && journalId !== null
          ? `/api/dictation/journal/${encodeURIComponent(String(journalId))}/correct`
          : "/api/dictation/corrections",
        {
          method: "POST",
          json:
            journalId !== undefined && journalId !== null
              ? { kind: correctionKind, value: correctionValue }
              : {
                  kind: correctionKind,
                  text: utterance,
                  value: correctionValue,
                },
        },
      );
      announce("Taught · reaches similar dictations");
      setCorrectionValue("");
    } catch (reason) {
      announce(`⚠ Refused · ${readableError(reason)}`, "warn");
    } finally {
      setBusy(false);
    }
  };
  /* The well's own verb: a rehearsal, or an aim that delivers nowhere,
     previews; anything else delivers for real. */
  const previewOnly = rehearse || aim === "field";
  const activeState =
    micState === "listening"
      ? "listening"
      : micState === "busy" || phase === "busy"
        ? "busy"
        : phase === "landed"
          ? "landed"
          : phase === "refused"
            ? "refused"
            : "idle";

  return {
    // state
    utterance,
    setUtterance,
    projectRoot,
    setProjectRoot,
    result,
    error,
    failure,
    busy,
    correctionKind,
    setCorrectionKind,
    correctionValue,
    setCorrectionValue,
    verdict,
    setVerdict,
    targets,
    targetId,
    micState,
    setMicState,
    level,
    setLevel,
    aim,
    rehearse,
    setRehearse,
    phase,
    setPhase,
    landedMs,
    setLandedMs,
    refusal,
    setRefusal,
    releasedAt,
    openMic,
    micPhase,
    captureSupported,
    captureReason,
    readinessConfig,
    readinessTarget,
    pipelineOn,
    // derived
    actions,
    previewOnly,
    activeState,
    // handlers
    run,
    pickAim,
    deliver,
    onReleased,
    toggleOpenMic,
    runElsewhere,
    keepDraft,
    teach,
  };
}
