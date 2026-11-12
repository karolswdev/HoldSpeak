// Parked: wave 13 replaces the raised voice plate with the live well and selection list.
import { createContext, useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch } from "../../../lib/api";
import { useOptionalRuntimeBus } from "../../../runtime/RuntimeBus";
import { useSpeakDeck } from "./useSpeakDeck";
import { refusalLabel } from "./shared";
import { useTalk } from "../../../desk/components/Talk";
import { type MicState } from "../../../desk/surface/controls/MicButton";
import { Mast, Spine, SurfaceState, PadGadget, LedMeter, StatusBar, type StatusBarItem } from "../../../desk/surface";
import { useWindowInterior } from "../../../desk/surface/interior";
import { plainFailure } from "../../../desk/surface/plainFailure";
import { wireWords } from "../../../desk/surface/words";
import { humanTime } from "../../../desk/surface/format";
import { SYSTEM } from "../../../desk/systemSprites";
import { ShowMe } from "../../../desk/walk/ShowMe";
import { useSpeechSetup, type SpeechSetupState } from "../../../desk/firstrun/SpeechSetup";
import { openSurfaceOr } from "../../../desk/shell";
import { useDesk } from "../../../desk/store";
import { DICTATION_FAILURES } from "../../../lib/dictationRecovery";
import type { VoiceCommandFired } from "../../../lib/micStreamSession";
import type { AssignmentEditorProjection } from "../assignmentExperience";
import type { Engine } from "../../../features/concierge/api";
import { readHotkeyCustody } from "./hotkeyCustody";
import { onReturnToTask, rememberTaskFocus } from "../../../desk/returnToTask";
import type { DictationJournalResponse } from "../core-types";
import "../../../desk/components/speak.css";

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

// Kept for small consumers that host the face; Speak itself has one status bar.
export type SpeakStatusReport = { items: StatusBarItem[]; trailing: ReactNode };
export const SpeakStatusContext = createContext<((report: SpeakStatusReport | null) => void) | null>(null);
export const SpeakVerbsContext = createContext<ReactNode>(null);

export function SpeakFace() {
  useWindowInterior("list");
  const [receipt, setReceipt] = useState("");
  const announce = useCallback((text: string) => setReceipt(text), []);
  const deck = useSpeakDeck(announce);
  const speech = useSpeechSetup();
  const refreshReadiness = deck.refreshReadiness;
  useEffect(() => onReturnToTask(() => { refreshReadiness(); }), [refreshReadiness]);
  const { talkKey, setupRow } = useSpeakTalk(deck, announce, speech);
  const bus = useOptionalRuntimeBus();
  const [journal, setJournal] = useState<DictationJournalResponse["items"]>([]);
  const [journalError, setJournalError] = useState("");
  const sequence = useRef(0);
  const refresh = useCallback(async () => {
    const mine = ++sequence.current;
    try {
      const answer = await apiFetch<DictationJournalResponse>("/api/dictation/journal?limit=50");
      if (mine === sequence.current) { setJournal(answer.items ?? []); setJournalError(""); }
    } catch (cause) { if (mine === sequence.current) setJournalError(plainFailure("Recent words not read", cause)); }
  }, []);
  useEffect(() => { void refresh(); return () => { sequence.current += 1; }; }, [refresh]);
  useEffect(() => bus?.subscribe("dictation.journal.entry", () => { void refresh(); }), [bus, refresh]);
  const custody = readHotkeyCustody(deck.readinessData);
  const failed = deck.activeState === "refused" || Boolean(deck.error);
  const working = deck.activeState === "busy" || deck.busy;
  const word = failed ? "Failed" : deck.activeState === "listening" ? "Listening" : working ? "Thinking" : deck.activeState === "landed" ? "Done" : speech.notSetUp ? "Speech not set up" : "Ready";
  const tone = failed ? "coral" : deck.activeState === "listening" || working ? "steel" : deck.activeState === "landed" ? "moss" : "brass";
  const copy = async (text: string) => {
    try { await navigator.clipboard.writeText(text); setReceipt("Copied"); }
    catch { setReceipt("Not copied · Retry"); }
  };
  const finalText = String(deck.result?.final_text || "");
  const retry = () => { if (deck.utterance.trim()) void deck.deliver(deck.utterance); else { deck.setPhase("idle"); deck.setRefusal(""); deck.refreshReadiness(); } };
  return <div className="speak-native" data-testid="speak-face">
    <Mast kind="dictation" glyph={SYSTEM.dockSpeak} title="Your voice" facts={<span data-testid="speak-phase">{word}</span>} data-testid="speak-mast">
      <Button dense variant="secondary" onClick={() => { rememberTaskFocus(); openSurfaceOr("configure-settings", "/settings", "speak"); }}>Settings</Button>
      <ShowMe app="surface-dictation" />
    </Mast>
    <Spine tone={tone} label={word} data-testid="speak-spine" />
    <div className="speak-native-scroll">
      <section className="speak-native-plate" aria-label="Talk" data-testid="speak-plate">
        <div className="speak-native-transport">
          {talkKey}
          <LedMeter label="Audio level" segments={12} value={deck.level} scanning={working} />
          <span data-testid="speak-types-into">{deck.aim === "agent" ? "To the agent" : "To the app in front"}</span>
        </div>
        {setupRow}
        <PadGadget label="Utterance" mic={false} value={deck.utterance} onChange={deck.setUtterance}
          placeholder="Hold Talk, then speak" rows={3} autoGrow onKeyDown={(event) => {
            if ((event.metaKey || event.ctrlKey) && event.key === "Enter" && !event.nativeEvent.isComposing) { event.preventDefault(); void deck.deliver(deck.utterance); }
          }} />
        {finalText && finalText !== deck.utterance ? <output className="speak-native-sent">{finalText}</output> : null}
        {failed ? <SurfaceState error={refusalLabel(deck.refusal || deck.failure || "unknown")} onRetry={deck.micState === "failed" ? undefined : retry} retryLabel="Retry" /> : null}
        {deck.utterance.trim() ? <div className="speak-native-verbs">
          <Button dense variant="secondary" data-testid="speak-copy" onClick={() => void copy(deck.utterance)}>Copy</Button>
          <Button dense variant="secondary" loading={deck.busy} onClick={() => void deck.deliver(deck.utterance)}>Put back</Button>
        </div> : null}
      </section>
      {custody.show ? <div className="speak-native-check" data-testid="speak-hotkey"><span>{custody.reason || "Hold key needs attention"}</span><Button dense variant="secondary" onClick={() => { rememberTaskFocus(); openSurfaceOr("configure-settings", "/settings", "speak"); }}>Fix hold key</Button></div> : null}
      {journalError ? <SurfaceState error={journalError} onRetry={() => void refresh()} retryLabel="Retry" /> : null}
      {journal?.length ? <section className="speak-native-ledger" aria-label="Recent dictations" data-testid="speak-recent">
        <h3>Recent dictations</h3>
        {journal.map((row) => <div className="speak-native-row" key={String(row.id)}>
          <div><strong>{String(row.final_text || row.transcript || "No words")}</strong><span>{humanTime(row.created_at || row.timestamp)} · {row.target_profile ? wireWords(String(row.target_profile)) : "Destination not recorded"}</span></div>
          <Button dense variant="ghost" onClick={() => void copy(String(row.final_text || row.transcript || ""))}>Copy</Button>
        </div>)}
      </section> : null}
    </div>
    {receipt || custody.display && !custody.show && !speech.notSetUp ? <StatusBar className="speak-footer" data-testid="speak-footer" items={[
      ...(receipt ? [{ key: "receipt", text: receipt }] : []),
      ...(custody.display && !custody.show && !speech.notSetUp ? [{ key: "hold", text: `Hold ${custody.display} anywhere` }] : []),
    ]} /> : null}
  </div>;
}

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
