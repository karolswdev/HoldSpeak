// HS-170-04 — Speak: the face built to the settled artboards.
// One screen: talk, see it land, teach once.  Everything that was
// the cockpit register strip folds behind > Details.
//
// Transport row (Talk — the one Talk rule, desk/components/Talk.tsx — and
//               the LedMeter; the Open latch only behind RAW)
// Utterance well (PadGadget, placeholder "Talk, or type here")
// TYPES INTO row (Types into: the app in front ▾ · Try it here)  [C8 words]
// RESULT row (landed text + OK/Wrong ghosts; Wrong unfolds teach row)
// ENGINE row (Clean-up runs on · model name · READY chip; no host chip,
//             owner ruling 2026-10-25; or NOT SET + Choose when no engine)
// HOTKEY block (HS-200-05: only when the physical key is not proven up —
//             the listener's state, and every macOS grant that is missing)
// > Details (Disclosure: the old register strip, folded; behind RAW, C8)
import { Fragment, createContext, type ReactNode, useCallback, useContext, useEffect, useLayoutEffect, useMemo, useState, type KeyboardEvent } from "react";
import { StatusBar, ToolGlyph, Toolbar, type StatusBarItem } from "../../../desk/surface/kit";
import { useWindowInterior } from "../../../desk/surface/interior";
import { useAnnounce } from "./shared";
import { useSpeakDeck } from "./useSpeakDeck";
import {
  STATE_TOKENS,
  MIC_PHASE_FACT,
  MIC_PHASE_LIVE,
  AIM_OPTIONS,
  refusalLabel,
} from "./shared";
import { type MicState } from "../../../desk/surface/controls/MicButton";
import { useTalk } from "../../../desk/components/Talk";
import { useBuilderTools } from "../../../desk/builderTools";
import { Button } from "../../../components/signal/Signal";
import {
  LedMeter,
  TransportKey,
  LampGadget,
  CycleGadget,
  PadGadget,
} from "../../../desk/surface/gadgets";
import { StateChip } from "../../../desk/surface/patterns";
import { Disclosure } from "../../../desk/surface/patterns";
import { presentValue } from "../../../desk/surface/format";
import {
  getAssignmentEditor,
  type AssignmentEditorProjection,
} from "../assignmentExperience";
import {
  conciergeDetect,
  type Engine,
} from "../../../features/concierge/api";
import { apiFetch } from "../../../lib/api";
import { onReturnToTask, rememberTaskFocus } from "../../../desk/returnToTask";
import { DICTATION_FAILURES } from "../../../lib/dictationRecovery";
import type { MicPhase } from "../../../lib/micSession";
import { readHotkeyCustody, type HotkeyCustody } from "./hotkeyCustody";
import { useSpeechSetup, type SpeechSetupState } from "../../../desk/firstrun/SpeechSetup";
import { openSurfaceOr } from "../../../desk/shell";
import { useDesk } from "../../../desk/store";
import type { VoiceCommandFired } from "../../../lib/micStreamSession";
import { Token } from "../../../desk/surface/Token";
import { wireWords } from "../../../desk/surface/words";

/** Extract hostname from a URL string. */
function hostnameOf(url: string): string {
  try {
    return new URL(url).hostname;
  } catch {
    return "";
  }
}

/** Apply the server's closed Desk result. A command receipt never invents an
 * object: New note opens only the note returned by desk.create, and UI-only
 * verbs reuse the same Desk openers as their menu verbs. */
function openDeskCommandResult(
  fired: VoiceCommandFired,
  announce: (text: string, tone?: "ok" | "warn") => void,
  setPhase: (phase: "landed" | "refused") => void,
  setRefusal: (value: string) => void,
): boolean {
  if (!fired.ok || fired.kind !== "desk_verb") return false;
  setPhase("landed");
  setRefusal("");
  const value = fired.result ?? {};
  const intent = value.ui_intent;
  if (intent === "ask") {
    useDesk.getState().openAsk();
    announce("Opened Ask");
    return true;
  }
  if (intent === "open_today") {
    openSurfaceOr("open-intelligence", "/");
    announce("Opened Today");
    return true;
  }
  if (value.desk_verb === "new_note") {
    const created = value.created;
    const note =
      created && typeof created === "object" && "note" in created
        ? (created as { note?: unknown }).note
        : created;
    const id = useDesk.getState().adoptCreated("note", note);
    if (id) {
      useDesk.getState().openPullout(`note:${id}`);
      announce("Made a new note");
      return true;
    }
    setPhase("refused");
    setRefusal("command_result_missing");
    announce("Could not open the new note · Nothing changed · Try again", "warn");
    return true;
  }
  announce(fired.preview);
  return true;
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
  /** The engine by name. No host and no place word on Speak (owner ruling
   *  2026-10-25): Settings ▸ Engines says where it runs. */
  name: string | null;
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
  return { name: engine.name || fallbackLabel, engineState: engine.state ?? null, keySet: engine.keySet ?? null };
}

const NO_ENGINE: ResolvedEngine = { name: null, engineState: null, keySet: null };

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

  // (c) No detect match — name it from what we have. Never an address: a
  // migrated label with no model id is the plain "Assigned engine".
  const isMigrationLabel = label.startsWith("Migrated");
  let name: string;
  if (!isMigrationLabel) {
    name = label;
  } else if (targetProfile?.model && targetProfile.model !== "default") {
    name = targetProfile.model;
  } else {
    name = "Assigned engine";
  }
  return { name, engineState: null, keySet: null };
}

/** Window grammar (2026-10-24): Speak's facts (the phase, the one fact,
 *  the hold key) join the Speak window's one status bar, which its host
 *  (DictationCore) draws with the receipt and the window's verbs. Without
 *  a host the face draws its own status bar. */
export type SpeakStatusReport = {
  /** The facts at the bar's left: the level, the phase, the fact, clean-up. */
  items: StatusBarItem[];
  /** The bar's right end: the one verb (Choose engine, only when clean-up
   *  needs one) and the quiet hold-key hint. */
  trailing: ReactNode;
};
export const SpeakStatusContext = createContext<((report: SpeakStatusReport | null) => void) | null>(null);

/** Lane speak (2026-10-25): the window's own verbs (Review, Export) that
 *  the host (DictationCore) hands to the Speak face, so they sit at the
 *  right end of the ONE toolbar instead of on the status bar's edge. */
export const SpeakVerbsContext = createContext<ReactNode>(null);

const PHASE_LAMP: Record<string, StatusBarItem["lamp"]> = {
  warn: "warn", live: "fail", info: "info", ok: "ok", danger: "fail",
};

/** The time since `since` as a tabular m:ss that ticks once a second;
 *  null while `since` is null. */
export function useElapsed(since: number | null): string | null {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (since == null) return;
    setNow(Date.now());
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [since]);
  if (since == null) return null;
  const seconds = Math.max(0, Math.floor((now - since) / 1000));
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}

/** The speech engine in words (`whisper-base-mlx`), from the hub's one
 *  speech read; null until it is read. */
export function speechEngineName(speech: Pick<SpeechSetupState, "status">): string | null {
  const read = speech.status?.speech;
  if (!read?.model) return null;
  const backend = String(read.backend ?? "").trim();
  return ["whisper", read.model, backend && backend !== "auto" ? backend : ""].filter(Boolean).join("-");
}

export function SpeakFace() {
  const announce = useAnnounce();
  useWindowInterior("editor");
  const deck = useSpeakDeck(announce);

  // Engine: assignment projection + concierge detect + legacy targets
  const [assignment, setAssignment] = useState<AssignmentEditorProjection | null>(null);
  const [engines, setEngines] = useState<Engine[]>([]);
  const [targets, setTargets] = useState<TargetProfile[]>([]);
  const [detectStatus, setDetectStatus] = useState<"pending" | "ok" | "failed">("pending");
  const readEngine = useCallback(() => {
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
  useEffect(() => { readEngine(); }, [readEngine]);
  // HS-200-04 (return-to-task): the owner opens Models from the ENGINE row,
  // picks an engine, and comes back. The utterance in the well is untouched;
  // only readiness is re-read. No reload, no second configuration.
  // HS-200-41: the one shared subscription (`desk/returnToTask.ts`), so the
  // event name lives in one place and the focus half rides the same signal.
  useEffect(
    () => onReturnToTask(() => { readEngine(); deck.refreshReadiness(); }),
    [readEngine, deck],
  );

  const resolved = resolveEngine(assignment, engines, targets);
  /* HS-200-05 — the physical hotkey's custody. Until this story the runtime
     recorded `global_hotkey_available` / `global_hotkey_error` and nothing
     read them: a refused grant made Right Option do nothing, silently. */
  const custody = readHotkeyCustody(deck.readinessData);
  // PHILO-17 speech: the speech model is the first thing Talk needs.
  const speech = useSpeechSetup();

  /* PHILO-17 REFIT: the head says the one fact (ready, or how many things
     to fix); the Talk plate is the focus object; the checks sit on a dotted
     rail below it, each broken one with the verb that fixes it. */
  const engineReady = detectStatus === "ok" && resolved.engineState === "READY";
  const enginePending = Boolean(resolved.name) && detectStatus === "pending";
  // Betterment C8: no clean-up engine is not a fault for Speak (the words
  // land as said). An engine that is chosen and not ready still is.
  const engineFault = Boolean(resolved.name) && !engineReady && !enginePending;
  const toFix =
    (speech.notSetUp ? 1 : 0) +
    (engineFault ? 1 : 0) +
    (custody.show ? 1 : 0);
  const raw = useBuilderTools((state) => state.on);
  const hotkey = custody.display || hotkeyDisplay(deck.readinessData);

  const { talkKey, setupRow } = useSpeakTalk(deck, announce, speech);
  // Window grammar (2026-10-24): the status bar says the phase with its
  // lamp, how long he has talked (a tabular m:ss that ticks), and the
  // engine that hears him, by name (`Listening · 0:42 · whisper-base-mlx`;
  // no place word: owner ruling 2026-10-25); at rest
  // `Ready · whisper-base-mlx`; with no speech
  // `Not ready · Talk sets up speech first`. The level meter leads it.
  const phase = phaseOf(deck, toFix);
  const listening = deck.activeState === "listening";
  const [listenSince, setListenSince] = useState<number | null>(null);
  useEffect(() => {
    setListenSince(listening ? Date.now() : null);
  }, [listening]);
  const elapsed = useElapsed(listenSince);
  const speechName = speechEngineName(speech);
  const fact = speech.notSetUp
    ? "Talk sets up speech first"
    : toFix
      ? `${toFix} to fix`
      : speechName
        ? speechName
        : "Ready to talk";
  const report = useContext(SpeakStatusContext);
  const meter = <span className="speak-level" data-testid="speak-level"><LedMeter label="Audio level" labelHidden segments={12} value={deck.level} scanning={deck.micState === "busy"} /></span>;
  // Clean-up is a setting, not a strip: its state is one status bar fact
  // and, only when it needs one, the bar's one verb.
  const engine = engineView(resolved.name, resolved.engineState, resolved.keySet, detectStatus);
  const openConcierge = useCallback(() => {
    // HS-200-41: remember the verb he left, so the Concierge's Apply can
    // put focus back here instead of on nothing (design D2(a)).
    rememberTaskFocus();
    import("../../../desk/shell").then(({ openSurface }) =>
      // PHILO-16 (C): Runs on opens on the job this face runs.
      openSurface("open-concierge", "writing_dictation"),
    );
  }, []);
  const statusItems = useMemo<StatusBarItem[]>(() => [
    { key: "level", text: meter },
    { key: "phase", lamp: PHASE_LAMP[phase.tone], text: <span className="speak-phase" data-tone={phase.tone} data-testid="speak-phase">{phase.word}{phase.tail}</span> },
    elapsed ? { key: "elapsed", text: <span className="speak-elapsed" data-testid="speak-elapsed">{elapsed}</span> } : null,
    { key: "fact", text: <span className="speak-fact" data-testid="speak-fact">{fact}</span> },
    { key: "engine", text: <EngineFact engine={resolved.name} view={engine} /> },
  ].filter(Boolean) as StatusBarItem[],
  // eslint-disable-next-line react-hooks/exhaustive-deps
  [phase.tone, phase.word, phase.tail, fact, elapsed, deck.level, deck.micState, resolved.name, engine.dataState, engine.chipLabel, engine.chipState]);
  const trailing = useMemo<ReactNode>(() => (
    <>
      {engine.choose ? (
        <Button variant="ghost" dense onClick={openConcierge} title="Clean-up engine">
          {engine.choose}
        </Button>
      ) : null}
      {/* The hold key is a hint once Talk can hear him; before speech is
          set up the bar says that instead (one line at 1440). */}
      {hotkey && !listening && !speech.notSetUp ? (
        <span className="speak-strip speak-hold-hint" data-testid="speak-hold-hint">Hold <kbd className="speak-kbd">{hotkey}</kbd> anywhere</span>
      ) : null}
    </>
  ), [engine.choose, openConcierge, hotkey, listening, speech.notSetUp]);
  useLayoutEffect(() => {
    if (!report) return;
    report({ items: statusItems, trailing });
  }, [report, statusItems, trailing]);
  const windowVerbs = useContext(SpeakVerbsContext);
  useLayoutEffect(() => (report ? () => report(null) : undefined), [report]);

  return (
    <div className="speak-face">
      {/* Window grammar (2026-10-24): an editor window like the Note.
          Toolbar [Talk (the one mic authority, click to toggle)] [Types
          into ▾] [Try it here] · the level → the words as the editor body,
          edge to edge → the result → the checks → the status bar. No
          headline, no plate in the window. */}
      <article className="speak-plate" aria-label="Talk">
        {/* W3-B (atlas 2026-10-27): one row at every width (the Note's
            rule): a narrow window shows the secondary verbs as their glyph,
            the word kept as the accessible name and the hover title. */}
        <Toolbar label="Speak" className="speak-toolbar" data-testid="speak-toolbar" trailing={windowVerbs} trailingStays>
          <TransportRow deck={deck} speech={speech} talkKey={talkKey} raw={raw} />
          <TypesIntoRow deck={deck} />
          <CopyVerb text={deck.utterance} announce={announce} />
        </Toolbar>
        {setupRow ? <div className="speak-setup" data-testid="speak-setup">{setupRow}</div> : null}
        <div className="speak-plate-body">
          <div className="speak-well">
            {/* HS-176-05 (ruling R13) — the well carries NO mic. `Talk` above is
                this face's ONE mic authority (Article IV.3). The census
                allowlist entry keys on `label="Utterance"`
                (scripts/ux_canon_scan.py:214). */}
            <PadGadget
              label="Utterance"
              mic={false}
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
          {deck.result ? <ResultRow deck={deck} announce={announce} /> : null}
        </div>
      </article>

      {/* THE CHECKS: only the hotkey, and only when the key is known to be
          stopped (it carries the fix: the grants and Re-check). Clean-up is
          a status bar fact (lane speak, 2026-10-25), not a strip. */}
      {custody.show ? (
        <ol className="speak-checks" aria-label="Checks">
          <li className="speak-check" data-tone={custody.kind === "failure" ? "danger" : "warn"}>
            <span className="speak-check-bead" aria-hidden="true" />
            <HotkeyRow custody={custody} onRecheck={deck.refreshReadiness} />
          </li>
        </ol>
      ) : null}

      {/* Betterment C8: the pipeline, the budget and the states are
          diagnostics: behind RAW (Settings ▸ System ▸ Builder tools). */}
      {raw ? (
        <Disclosure label="Details" defaultOpen={false}>
          <DetailsContent deck={deck} />
        </Disclosure>
      ) : null}
      {report ? null : <StatusBar data-testid="speak-status" items={statusItems} verbs={trailing} />}
    </div>
  );
}

/** A state token in plain words: `NOT SET` reads "Not set" (Today's pills). */
function plain(token: string): string {
  const words = token.replace(/_/g, " ").trim().toLowerCase();
  return words ? words[0].toUpperCase() + words.slice(1) : words;
}

/** The hotkey's display (`⌥R`) from readiness, also when the block is silent. */
function hotkeyDisplay(readiness: unknown): string {
  const block = (readiness as Record<string, unknown> | null | undefined)?.hotkey as
    | Record<string, unknown>
    | undefined;
  return block && typeof block.display === "string" ? block.display : "";
}

/* The plate's state word: a pill with a lamp dot, plain words. */
const PHASE_WORDS: Record<string, { word: string; tone: string }> = {
  idle: { word: "Ready", tone: "idle" },
  listening: { word: "Listening", tone: "live" },
  busy: { word: "Working", tone: "info" },
  landed: { word: "Landed", tone: "ok" },
  refused: { word: "Not landed", tone: "danger" },
};

function phaseOf(deck: ReturnType<typeof useSpeakDeck>, toFix: number): { word: string; tone: string; tail: string } {
  // At rest, the phase agrees with the fact: not ready while a check is open.
  const phase =
    deck.activeState === "idle" && toFix
      ? { word: "Not ready", tone: "warn" }
      : (PHASE_WORDS[deck.activeState] ?? PHASE_WORDS.idle);
  const tail =
    deck.activeState === "refused" && deck.refusal
      ? ` · ${refusalLabel(deck.refusal).toLowerCase()}`
      : "";
  return { ...phase, tail };
}

/* ── Transport row ── */

/** The one Talk rule (desk/components/Talk.tsx), lifted to the face so the
 *  key sits in the toolbar and its setup row under the toolbar. */
function useSpeakTalk(
  deck: ReturnType<typeof useSpeakDeck>,
  announce: (text: string, tone?: "ok" | "warn") => void,
  /** The face's one speech read, shared with the Talk rule. */
  speech: SpeechSetupState,
) {
  return useTalk(
    {
      draftScope: "dictation-dry-run-voice",
      label: "Talk",
      onText: deck.onReleased,
      onState: (next: MicState) => {
        if (next === "busy") deck.releasedAt.current = performance.now();
        if (next === "listening") {
          deck.releasedAt.current = null;
          deck.setPhase("idle");
          deck.setLandedMs(null);
          deck.setRefusal("");
        }
        deck.setMicState(next);
      },
      onLevel: deck.setLevel,
      onCommand: (fired) => {
        deck.setLandedMs(null);
        if (openDeskCommandResult(fired, announce, deck.setPhase, deck.setRefusal)) return;
        if (fired.ok) {
          deck.setPhase("landed");
          deck.setRefusal("");
          announce(`Command ran · ${fired.preview}`);
        } else {
          deck.setPhase("refused");
          deck.setRefusal("command_failed");
          announce(`Could not run “${fired.preview}” · Nothing changed · Try again`, "warn");
        }
      },
      onFailure: (category) => {
        deck.setPhase("refused");
        deck.setRefusal(category);
        deck.setLandedMs(null);
        announce(DICTATION_FAILURES[category].message, "warn");
      },
    },
    // Speech setup is Speak's one job while the model is missing: primary.
    { speech, testId: "speak-speech-setup", primary: true, onReady: deck.refreshReadiness },
  );
}

function TransportRow({
  deck,
  speech,
  talkKey,
  raw = false,
}: {
  deck: ReturnType<typeof useSpeakDeck>;
  speech: SpeechSetupState;
  talkKey: ReactNode;
  /** RAW (Builder tools): the Open mic latch shows. */
  raw?: boolean;
}) {
  return (
    <span className="speak-transport" role="group" aria-label="Dictation transport">
      {talkKey}
      {raw ? (
        <TransportKey
          label="Open mic"
          word="Open"
          glyph={"◉"}
          active={deck.openMic}
          disabled={speech.notSetUp || !deck.captureSupported}
          title={speech.notSetUp ? "Set up speech first" : (deck.captureReason ?? undefined)}
          onClick={() => void deck.toggleOpenMic()}
        />
      ) : null}
    </span>
  );
}

/** Copy: the words in the well, to the clipboard (quiet; the receipt says
 *  it). */
function CopyVerb({ text, announce }: { text: string; announce: (text: string, tone?: "ok" | "warn") => void }) {
  return (
    <Button
      dense
      variant="secondary"
      disabled={!text.trim()}
      data-testid="speak-copy"
      className="speak-verb"
      title="Copy"
      onClick={() => {
        const write = navigator.clipboard?.writeText(text);
        if (!write) {
          announce("Not copied", "warn");
          return;
        }
        void write.then(() => announce("Copied"), () => announce("Not copied", "warn"));
      }}
    >
      <ToolGlyph kind="copy" />
      <span className="speak-verb-label">Copy</span>
    </Button>
  );
}

/* ── TYPES INTO row (betterment C8 words) ──
   `Types into: the app in front ▾ · Try it here`. Try it here replaces the
   DRY RUN latch: it runs the words in the box through clean-up and shows
   the result here; it types nothing into any app. */

function TypesIntoRow({ deck }: { deck: ReturnType<typeof useSpeakDeck> }) {
  return (
    <span className="speak-lands-in" data-testid="speak-types-into">
      <span className="speak-lands-in-caption">Types into</span>
      <CycleGadget
        label="Types into"
        value={deck.aim}
        options={AIM_OPTIONS}
        onChange={deck.pickAim}
      />
      {deck.landedMs !== null ? (
        <>
          <span className="speak-lands-in-dot">{"·"}</span>
          <span className="speak-lands-in-latency">{deck.landedMs} ms</span>
        </>
      ) : null}
      <span className="speak-transport-spacer" />
      <Button
        dense
        variant="secondary"
        loading={deck.busy && deck.phase !== "busy"}
        disabled={!deck.utterance.trim()}
        onClick={() => void deck.run()}
        data-testid="speak-try-it-here"
        className="speak-verb"
        title="Try it here" data-glyph="narrow"
      >
        <ToolGlyph kind="run" />
        <span className="speak-verb-label">Try it here</span>
      </Button>
    </span>
  );
}

/* ── RESULT row ──

   HS-176-02 — the teach loop, element by element:
   - the RESULT line: the landed text + the `APPLIED` chip (only when
     this run's own `corrections_applied` is non-empty) + the verdict
     pair OK / Wrong (one species, two states: the selected verdict
     takes `data-verdict-active`).
   - `APPLIED` unfolds a well beneath naming each rule that FIRED.
   - `Wrong` unfolds the teach row: FIELD cycles TEXT · INTENT · TARGET;
     TEXT is one wrapping well pre-filled with the RAW transcript, the
     routing kinds are a pick over the real enum (label on the face, id
     on the wire).
   - `Teach` replaces the row with a receipt: `Taught` · a -> b,
     `No change`, `Not taught · It looks like a secret` (W6-H, W6-I words:
     sentence case). Never a modal. */

function AppliedRule({
  rule,
}: {
  rule: { id: number; kind: string; key: string; value: string; label: string };
}) {
  const text = rule.kind === "text";
  return (
    <div className="speak-applied-rule">
      <div className="speak-applied-fact">
        <span className="speak-applied-caption">{text ? "HEARD" : "WHEN"}</span>
        <span className="speak-applied-heard">{rule.key}</span>
      </div>
      <div className="speak-applied-fact">
        <span className="speak-applied-caption">{text ? "SAID" : "ROUTE"}</span>
        <span className="speak-applied-said">{rule.label || rule.value}</span>
      </div>
      <div className="speak-applied-fact">
        <Token className="surface-token" data-chip="">
          {wireWords(rule.kind || "rule")}
        </Token>
      </div>
    </div>
  );
}

function TeachRow({
  deck,
  onTeach,
}: {
  deck: ReturnType<typeof useSpeakDeck>;
  onTeach: () => void;
}) {
  const text = deck.correctionKind === "text";
  const pickLabel =
    deck.correctionKind === "target" ? "Delivery target" : "Intent block";
  return (
    <div className="speak-teach" role="group" aria-label="Correct this result">
      <span className="speak-teach-field">
        <span className="speak-teach-caption">FIELD</span>
        <CycleGadget
          label="Correction field"
          value={deck.correctionKind}
          options={deck.correctionFields}
          onChange={deck.pickCorrectionKind}
        />
      </span>
      {text ? (
        /* The well he EDITS never truncates what it is holding: the
           value WRAPS (design P2 / the phone board), so at 393 the
           transcript takes a second line with `Teach` level with the
           first. A single-line text field cannot wrap, so the species
           is the kit's one multiline face at a single row, grown by its
           content — and it carries its own mic, as every well does. */
        <PadGadget
          label="What you said"
          value={deck.correctionSaid}
          onChange={deck.setCorrectionSaid}
          rows={1}
          autoGrow
        />
      ) : (
        <CycleGadget
          label={pickLabel}
          value={deck.correctionValue}
          options={deck.correctionOptions}
          onChange={deck.setCorrectionValue}
        />
      )}
      <Button
        variant="primary"
        dense
        loading={deck.busy}
        disabled={
          text
            ? !deck.correctionSaid.trim()
            : !deck.correctionValue.trim()
        }
        aria-label="Teach correction"
        onClick={onTeach}
      >
        Teach
      </Button>
    </div>
  );
}

function ResultRow({
  deck,
  announce,
}: {
  deck: ReturnType<typeof useSpeakDeck>;
  announce: (text: string, tone?: "ok" | "warn") => void;
}) {
  const result = (deck.result ?? {}) as Record<string, unknown>;
  const finalText = String(result.final_text ?? result.text ?? result.output ?? "");
  const [appliedOpen, setAppliedOpen] = useState(false);
  const applied = deck.appliedRules;
  const receipt = deck.receipt;

  return (
    <section className="speak-result" aria-label="Pipeline result">
      <div className="speak-result-line">
        <span className="speak-result-text">{finalText}</span>
        {applied.length ? (
          <Button
            variant="ghost"
            dense
            className="speak-applied-chip"
            aria-expanded={appliedOpen}
            aria-label="Corrections applied"
            onClick={() => setAppliedOpen(!appliedOpen)}
          >
            Applied
          </Button>
        ) : null}
        <Button
          variant="ghost"
          dense
          data-verdict-active={deck.verdict === "right" || undefined}
          onClick={() => {
            deck.setVerdict("right");
            announce("Marked OK");
          }}
        >
          OK
        </Button>
        <Button
          variant="ghost"
          dense
          data-verdict-active={deck.verdict === "wrong" || undefined}
          onClick={() => deck.setVerdict("wrong")}
        >
          Wrong
        </Button>
      </div>
      {applied.length && appliedOpen ? (
        <div
          className="speak-applied-body"
          role="region"
          aria-label="Corrections applied"
        >
          {applied.map((rule) => (
            <AppliedRule key={rule.id} rule={rule} />
          ))}
        </div>
      ) : null}
      {receipt ? (
        <div className="speak-receipt" role="status">
          <Token
            className="surface-token"
            data-chip=""
            data-tone={receipt.tone}
          >
            {receipt.token}
          </Token>
          {receipt.tail ? (
            <span className="speak-receipt-tail">{receipt.tail}</span>
          ) : null}
        </div>
      ) : deck.verdict === "wrong" ? (
        <TeachRow deck={deck} onTeach={() => void deck.teach()} />
      ) : null}
    </section>
  );
}

/* ── ENGINE fact (clean-up) ──
   Lane speak (2026-10-25): clean-up is a setting. Its state is ONE status
   bar fact (`Clean-up` · the engine by name · a dot and a word), and the
   bar's one verb (`Choose engine`, `Choose`) only when it needs one. */

type EngineView = {
  dataState: "not-set" | "pending" | "unknown" | "ready" | "waiting";
  chipState: "success" | "warning" | "idle" | null;
  chipLabel: string;
  /** The verb's word, or null when the fact needs no verb. */
  choose: string | null;
};

function engineView(
  engine: string | null,
  engineState: string | null,
  keySet: boolean | null,
  detectStatus: "pending" | "ok" | "failed",
): EngineView {
  // No engine assigned at all. Betterment C8: not a fault for Speak — the
  // words land as said. `Clean-up off · Choose engine`.
  if (!engine) return { dataState: "not-set", chipState: "idle", chipLabel: "Off", choose: "Choose engine" };
  // Pending: detect hasn't resolved yet — the name, muted, and `Checking`.
  if (detectStatus === "pending") return { dataState: "pending", chipState: null, chipLabel: "Checking", choose: null };
  // Failed: detect errored. State is unknown — never claim READY.
  if (detectStatus === "failed" && !engineState) return { dataState: "unknown", chipState: "warning", chipLabel: "Unknown", choose: "Choose" };
  if (engineState === "NOT_SET")
    return { dataState: "not-set", chipState: "warning", chipLabel: plain(keySet === false ? "KEY NOT SET" : "NOT SET"), choose: "Choose" };
  if (engineState === "UNREACHABLE") return { dataState: "unknown", chipState: "warning", chipLabel: "Unreachable", choose: "Choose" };
  if (engineState === "READY") return { dataState: "ready", chipState: "success", chipLabel: "Ready", choose: null };
  if (engineState === "WAITING" || engineState === "CHECKING")
    return { dataState: "waiting", chipState: "warning", chipLabel: plain(engineState), choose: "Choose" };
  if (engineState) return { dataState: "unknown", chipState: "warning", chipLabel: plain(engineState), choose: "Choose" };
  // detectStatus === "ok" but no engine matched — fallback
  return { dataState: "unknown", chipState: "warning", chipLabel: "Unknown", choose: "Choose" };
}

function EngineFact({ engine, view }: { engine: string | null; view: EngineView }) {
  return (
    <span className="speak-engine" data-engine-state={view.dataState}>
      <span className="speak-engine-caption">Clean-up</span>
      {engine ? <span className="speak-engine-name" data-muted={view.dataState === "pending" || undefined}>{engine}</span> : null}
      {view.chipState ? (
        <StateChip state={view.chipState} label={view.chipLabel} />
      ) : (
        <span className="speak-engine-checking">{view.chipLabel}</span>
      )}
    </span>
  );
}

/* ── HOTKEY block (HS-200-05) ──
   The listener's own state, then one row per macOS grant that is NOT granted:
   the permission, what it costs, the path to walk, and its honest state. The
   whole block is absent when the key is proven up and all three are granted
   (no counters of zero, no decorative "all fine" row). */

function HotkeyRow({
  custody,
  onRecheck,
}: {
  custody: HotkeyCustody;
  onRecheck: () => void;
}) {
  return (
    <div
      className="speak-hotkey"
      data-hotkey-state={custody.token.toLowerCase().replace(/ /g, "-")}
      data-testid="speak-hotkey"
    >
      <div className="speak-hotkey-head">
        <span className="speak-hotkey-ident">
          <span className="speak-engine-caption">Hotkey</span>
          {custody.display ? (
            <>
              <span className="speak-engine-dot">{"\u00b7"}</span>
              <span className="speak-engine-name">{custody.display}</span>
            </>
          ) : null}
          {custody.reason ? (
            <Token className="surface-token" data-chip="" data-testid="speak-hotkey-reason">
              {custody.reason}
            </Token>
          ) : null}
        </span>
        <span className="speak-hotkey-tail">
          <StateChip state={custody.kind} label={plain(custody.token)} />
          <Button
            variant="ghost"
            dense
            onClick={onRecheck}
            data-testid="speak-hotkey-recheck"
          >
            Re-check
          </Button>
        </span>
      </div>
      {custody.rows.map((row) => (
        <div
          className="speak-hotkey-row"
          key={row.id}
          data-testid={`speak-permission-${row.id}`}
        >
          <span className="speak-hotkey-ident">
            <span className="speak-hotkey-name">{row.label}</span>
            {row.neededFor ? (
              <Token className="surface-token" data-chip="">{row.neededFor}</Token>
            ) : null}
          </span>
          <span className="speak-hotkey-tail">
            <StateChip state={row.kind} label={plain(row.token)} />
          </span>
          <span className="speak-hotkey-path">
            {row.path.map((token, i) => (
              <Fragment key={token}>
                {i ? (
                  <span className="speak-engine-dot" aria-hidden="true">
                    {"\u203a"}
                  </span>
                ) : null}
                <Token className="surface-token" data-chip="">{token}</Token>
              </Fragment>
            ))}
          </span>
        </div>
      ))}
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
        <span className="speak-detail-label">Engine</span>
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
