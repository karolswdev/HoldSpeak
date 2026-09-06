// useSpeakDeck — the 20+ state variables and 8 async handlers that
// drive the SpeakFace deck, extracted from DictationCore.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { apiFetch, readableError } from "../../../lib/api";
import {
  DICTATION_FAILURES,
  applicableActions,
  dictationFailure,
  type DictationFailure,
} from "../../../lib/dictationRecovery";
import { useDurableDraft } from "../../../lib/durableDraft";
import { asRows, useResource } from "../../pageSupport";
import type {
  DictationBlocksResponse,
  DictationCorrectionsResponse,
  DictationDryRunResponse,
  DictationReadinessResponse,
} from "../core-types";
import type { MicState } from "../../../desk/components/MicButton";
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
  CORRECTION_FIELDS,
  teachReceiptFor,
  truncateSpan,
  type TeachReceipt,
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
  /* HS-176-02 — the teach row. FIELD defaults to TEXT: the Tuesday
     mistake is a words mistake, and the routing kinds are a pick over
     the real enum. `correctionValue` carries the picked ID (never a
     typed label); `correctionSaid` carries the edited transcript. */
  const [correctionKind, setCorrectionKind] = useState("text");
  const [correctionValue, setCorrectionValue] = useState("");
  const [correctionSaid, setCorrectionSaid] = useState("");
  const [receipt, setReceipt] = useState<TeachReceipt | null>(null);
  const receiptTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const [verdict, setVerdict] = useState<"" | "right" | "wrong">("");
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
  /* HS-176-02 — the two label sources (D3/R12). The wire carries ids;
     the face renders labels. `target.overrides` is the readiness
     route's six-entry pick list (never `auto`); the intent labels are
     the loaded blocks' own descriptions. */
  const corrections = useResource<DictationCorrectionsResponse>(
    "/api/dictation/corrections",
    {},
  );
  const blocks = useResource<DictationBlocksResponse>(
    "/api/dictation/blocks?scope=global",
    {},
  );
  const targetOverrides = useMemo(
    () =>
      (Array.isArray(readinessTarget.overrides)
        ? (readinessTarget.overrides as Record<string, unknown>[])
        : []
      ).map((row) => ({
        value: String(row.id ?? ""),
        label: String(row.label ?? row.id ?? ""),
      })),
    [readinessTarget.overrides],
  );
  const blockRows = (blocks.data.document as Record<string, unknown> | undefined)
    ?.blocks;
  const intentOptions = useMemo(
    () =>
      asRows(blockRows, []).map((row) => ({
        value: String(row.id ?? ""),
        label: String(row.description ?? row.id ?? ""),
      })),
    [blockRows],
  );
  /* The pick the teach row draws for the current FIELD. TEXT has none —
     it is one StringGadget, pre-filled with the raw transcript. */
  const correctionOptions =
    correctionKind === "target"
      ? targetOverrides
      : correctionKind === "intent"
        ? intentOptions
        : [];
  const optionKey = correctionOptions.map((o) => o.value).join(",");
  /* A routing correction is a pick, so the picked id is always a member
     of the offered set — never an empty POST, never a typed id. */
  useEffect(() => {
    if (correctionKind === "text") return;
    if (correctionOptions.some((o) => o.value === correctionValue)) return;
    setCorrectionValue(correctionOptions[0]?.value ?? "");
    // correctionOptions is rebuilt per render; optionKey is its identity.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [correctionKind, optionKey]);

  /** The id -> label map for a routing kind (E.4: never a raw id). */
  const labelFor = useCallback(
    (kind: string, id: string): string => {
      const table = kind === "target" ? targetOverrides : intentOptions;
      return table.find((o) => o.value === id)?.label ?? id;
    },
    [targetOverrides, intentOptions],
  );

  /* N2 — the string the `text` rule is applied to. The diff is
     heard(raw) vs said(his edit); a key harvested from the LANDED text
     would be matched against a string it never equals whenever the
     rewrite pass did its job. */
  const rawText = String(
    result?.raw_text ?? result?.final_text ?? result?.text ?? result?.output ?? "",
  );
  /* R2 — the chip reads the run's own stored fact, never a read-time
     "would match" over the whole journal. */
  const appliedIds = useMemo(() => {
    const raw = result?.corrections_applied;
    if (!Array.isArray(raw)) return [] as number[];
    return raw
      .map((x) => Number(x))
      .filter((x) => Number.isFinite(x));
  }, [result]);
  const correctionRows = useMemo(
    () => asRows(corrections.data, ["items", "corrections"]),
    [corrections.data],
  );
  /** The rules that FIRED on this run, resolved against the store. */
  const appliedRules = useMemo(
    () =>
      appliedIds.map((id) => {
        const row = correctionRows.find((r) => Number(r.id) === id);
        const kind = String(row?.kind ?? "");
        const value = String(row?.value ?? "");
        return {
          id,
          kind,
          key: String(row?.key ?? ""),
          value,
          label: kind && kind !== "text" ? labelFor(kind, value) : value,
        };
      }),
    [appliedIds, correctionRows, labelFor],
  );

  /* The receipt replaces the teach row, then fades. A new landing
     clears it and re-fills the TEXT well from the new raw transcript. */
  useEffect(() => {
    clearTimeout(receiptTimer.current);
    setReceipt(null);
    setCorrectionSaid(rawText);
    // rawText is derived from `result`; the landing is the event.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [result]);
  useEffect(() => () => clearTimeout(receiptTimer.current), []);
  const showReceipt = useCallback((next: TeachReceipt) => {
    clearTimeout(receiptTimer.current);
    setReceipt(next);
    receiptTimer.current = setTimeout(() => setReceipt(null), 5000);
  }, []);
  /** Switching FIELD never carries the previous field's answer over. */
  const pickCorrectionKind = useCallback(
    (next: string) => {
      setCorrectionKind(next);
      setCorrectionValue("");
      setReceipt(null);
    },
    [],
  );
  useEffect(() => {
    if (utteranceRecovered) announce("Draft restored");
  }, [utteranceRecovered, announce]);
  /* REHEARSE — the explicit dry run. It previews the assigned pipeline and
     delivers NOTHING; it is never what a plain TALK release does. */
  const run = async (text: string = utterance) => {
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
     idempotency claim as the global hotkey. One id per utterance.

     HS-132-04 — ONE utterance, ONE pipeline. Spoken text arrives here
     already carrying a pipeline receipt (the TALK key's streaming final and
     the open mic's transcription both ran the DIR pass), so it is delivered
     `raw: true`: verbatim, no second pass, no second journal row. Text the
     user TYPED into the well carries no receipt and takes the pipeline here,
     exactly once. */
  const deliver = async (
    text: string,
    { pipelined = false }: { pipelined?: boolean } = {},
  ) => {
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
          // already piped once -> delivered exactly as it reads.
          ...(pipelined ? { raw: true } : {}),
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
    else void deliver(text, { pipelined: true });
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
  /* HS-176-02 — the teach. One POST, one receipt, no sentence.

     The journal route is primary (it links the taught row); the
     corrections route is the fallback for a run that returned no
     `journal_id` (journal off, no repository, unknown source).

     R4: `recorded` is the ONE key both routes answer with (`taught` is
     this route's long-standing mirror), and a refusal carries a named
     `reason` — so `REFUSED · SECRET` is true rather than smoothed.

     A.7 — the name is said ONCE per face: the outcome lives in the
     RESULT row's receipt (a `role="status"` line, so it is announced
     to assistive tech there) and is NEVER mirrored into the footer.
     The footer keeps its own status vocabulary (`REHEARSED · NOT
     DELIVERED`, the landing and refusal lines). */
  const teach = async () => {
    const journalId = result?.journal_id;
    const onJournal = journalId !== undefined && journalId !== null;
    const kind = correctionKind;
    const said = correctionSaid;
    const heard = rawText || utterance;
    setBusy(true);
    try {
      const reply = await apiFetch<Record<string, unknown>>(
        onJournal
          ? `/api/dictation/journal/${encodeURIComponent(String(journalId))}/correct`
          : "/api/dictation/corrections",
        {
          method: "POST",
          json:
            kind === "text"
              ? { kind, heard, said }
              : onJournal
                ? { kind, value: correctionValue }
                : { kind, text: heard, value: correctionValue },
        },
      );
      const recorded = Boolean(reply.recorded ?? reply.taught);
      if (!recorded) {
        showReceipt(teachReceiptFor(String(reply.reason ?? "")));
        return;
      }
      const tail =
        kind === "text"
          ? `${truncateSpan(String(reply.key ?? heard))} → ${truncateSpan(
              String(reply.value ?? said),
            )}`
          : labelFor(kind, String(reply.value ?? correctionValue));
      showReceipt({ token: "TAUGHT", tone: "ok", tail });
      void corrections.reload();
    } catch {
      // An HTTP refusal carries no body the face can name; what is TRUE
      // either way is that nothing was written.
      showReceipt({ token: "REFUSED", tone: "danger", tail: "nothing written" });
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
    pickCorrectionKind,
    correctionValue,
    setCorrectionValue,
    correctionSaid,
    setCorrectionSaid,
    correctionOptions,
    correctionFields: CORRECTION_FIELDS,
    receipt,
    rawText,
    appliedRules,
    labelFor,
    verdict,
    setVerdict,
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
    keepDraft,
    teach,
  };
}
