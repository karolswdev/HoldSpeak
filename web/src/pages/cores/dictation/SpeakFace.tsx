import { createContext, useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch } from "../../../lib/api";
import { useOptionalRuntimeBus } from "../../../runtime/RuntimeBus";
import { useSpeakDeck } from "./useSpeakDeck";
import { refusalLabel } from "./shared";
import { useTalk } from "../../../desk/components/Talk";
import { type MicState } from "../../../desk/surface/controls/MicButton";
import { Mast, SurfaceState, PadGadget, StatusBar, type StatusBarItem, PreferencePane, PaneInspector, InspectorForm, InspectorFacts, InspectorBody, PaneActions, ListPane, ListView, LiveWell, LiveLevel, Lamp, Elapsed, Toolbar, CycleGadget, listVerbEntries, type ListVerb, useWindowBack, useListApp, type ObjectListRow } from "../../../desk/surface";
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
import { WorkMenu } from "../../../desk/components/DeskMenu";
import { useStripFit } from "../../../desk/surface/stripMenu";

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
  const [receipt, setReceipt] = useState("");
  const [receiptKind, setReceiptKind] = useState<"deck" | "copy">("deck");
  const announce = useCallback((text: string) => { setReceipt(text); setReceiptKind("deck"); }, []);
  const deck = useSpeakDeck(announce);
  const speech = useSpeechSetup();
  const refreshReadiness = deck.refreshReadiness;
  useEffect(() => onReturnToTask(() => { refreshReadiness(); }), [refreshReadiness]);
  const { talkKey, setupRow } = useSpeakTalk(deck, announce, speech);
  const bus = useOptionalRuntimeBus();
  const readJournal = useCallback(async () => {
    const answer = await apiFetch<DictationJournalResponse>("/api/dictation/journal?limit=50");
    return { rows: answer.items ?? [], today: Number(answer.today) || 0 };
  }, []);
  const recent = useListApp({read:readJournal,keyOf:row=>String(row.id)});
  const {rows:journal,picked,setPicked,selected} = recent;
  const today = recent.page?.today ?? 0;
  const journalError = recent.error ? plainFailure("Recent words not read", recent.error) : "";
  const refresh = useRef(recent.reload);
  refresh.current = recent.reload;
  useEffect(() => bus?.subscribe("dictation.journal.entry", () => { void refresh.current(); }), [bus]);
  const custody = readHotkeyCustody(deck.readinessData);
  const holdReason = custody.reason === "PYNPUT MISSING" ? "Hold key did not start" : wireWords(custody.reason) || "Hold key needs attention";
  const [inspecting, setInspecting] = useState(false);
  const [typing, setTyping] = useState(false);
  const closeInspector = () => { setInspecting(false); setTyping(false); };
  useWindowBack(inspecting ? {onBack:closeInspector} : null, [inspecting]);
  const [ended, setEnded] = useState<number | undefined>(undefined);
  const [started, setStarted] = useState<number | null>(null);
  const listening = deck.activeState === "listening";
  const working = deck.activeState === "busy" || deck.busy;
  const failed = deck.activeState === "refused" || Boolean(deck.error);
  const failureCode = deck.refusal || deck.failure || "unknown";
  const failureWords = Object.prototype.hasOwnProperty.call(DICTATION_FAILURES, failureCode)
    ? DICTATION_FAILURES[failureCode as keyof typeof DICTATION_FAILURES].message.split(". ")[0].replace(/\.$/, "")
    : refusalLabel(failureCode);
  useEffect(() => { if (listening) { setStarted(Date.now()); setEnded(undefined); } else setEnded(Date.now()); }, [listening]);
  useEffect(() => { if (!selected && !typing) setInspecting(false); }, [selected, typing]);
  const word = failed ? "Failed" : listening ? "Listening" : working ? "Thinking" : deck.activeState === "landed" ? "Done" : speech.notSetUp ? "Speech not set up" : "Ready";
  const destination = deck.aim === "agent" ? "To the agent" : "To the app in front";
  const copy = async (text: string) => {
    setReceiptKind("copy");
    try { await navigator.clipboard.writeText(text); setReceipt("Copied"); }
    catch { setReceipt("Not copied · Try Copy again"); }
  };
  const rowText = (row: Record<string, unknown>) => String(row.final_text || row.transcript || "");
  const rows: ObjectListRow[] = journal.map(row => ({ id: String(row.id), kind: "dictation", name: rowText(row) || "No words",
    when: humanTime(row.created_at || row.timestamp), cells: { to: row.target_profile ? wireWords(String(row.target_profile)) : "Not recorded" } }));
  const pickedRow = rows.find(row => row.id === picked) ?? null;
  const settings = () => { rememberTaskFocus(); openSurfaceOr("configure-settings", "/settings", "speak"); };
  const verbs: ListVerb[] = [
    ...(inspecting ? [{id:"back",label:"Back",enabled:()=>true,run:closeInspector}] : []),
    { id: "open", label: "Open", key: "Enter", run: () => { setTyping(false); setInspecting(true); } },
    { id: "copy", label: "Copy", enabled: row => Boolean(row) && !listening && !working, run: () => { if (selected) void copy(rowText(selected)); } },
    { id: "put-back", label: "Put back", enabled: row => Boolean(row) && !listening && !working, run: () => { if (selected) void deck.deliver(rowText(selected)); } },
    { id: "type", label: "Type", enabled: () => !listening && !working, run: () => { setTyping(true); setInspecting(true); } },
    { id: "settings", label: custody.show ? "Fix hold key" : "Settings", enabled: () => true, run: settings },
  ];
  const retry = () => { if (deck.utterance.trim()) void deck.deliver(deck.utterance); else { deck.setPhase("idle"); deck.setRefusal(""); deck.refreshReadiness(); } };
  const finalText = String(deck.result?.final_text || "");
  return <PreferencePane label="Speak" testId="speak-face">
    <Mast kind="dictation" glyph={SYSTEM.dockSpeak} title="Speak" figures={today ? [{value:today,label:"today"}] : undefined} facts={<span data-testid="speak-phase">{word}{custody.display && !custody.show ? ` · Hold ${custody.display}` : ""}</span>} />
    <ShowMe app="surface-dictation" />
    <Toolbar label="Speak" trailing={<CycleGadget label="To" value={deck.aim === "agent" ? "agent" : "focused"} options={[{value:"focused",label:"App in front"},{value:"agent",label:"Agent"}]} onChange={deck.pickAim} disabled={listening || working} />}>
      {talkKey}<SpeakVerbs verbs={verbs} selected={pickedRow} />
    </Toolbar>
    {setupRow}
    {custody.show ? <PaneActions data-testid="speak-hotkey"><span>{holdReason}</span><Button dense variant="secondary" onClick={settings}>Fix hold key</Button></PaneActions> : null}
    {failed ? <SurfaceState error={failureWords} onRetry={deck.micState === "failed" ? undefined : retry} retryLabel="Retry" /> : null}
    {journalError ? <SurfaceState error={journalError} onRetry={() => void recent.reload()} retryLabel="Retry" /> : null}
    <ListPane deck={Boolean(selected) || typing} open={inspecting} hostBack label="Dictation" list={<div data-feedback-redact="true" className="object-list" style={{gap:12,padding:12,border:0,minHeight:0,overflow:"hidden"}}>
      <div className="surface-live-well" data-testid="speak-live" style={{height:"auto",maxHeight:"none",minHeight:100,flex:"0 1 180px",overflow:"auto",gap:12}}>
        <PaneActions><Lamp state={failed ? "failed" : listening || working ? "working" : speech.notSetUp ? "waiting" : deck.activeState === "landed" ? "done" : "off"} label={word} /><span>{word === "Speech not set up" ? "Not set up" : word}</span><span data-testid="speak-types-into">{destination}</span><span style={{marginLeft:"auto",fontSize:24,fontWeight:700}}>{started !== null ? <Elapsed start={started} running={listening} end={listening ? undefined : ended} /> : "0:00"}</span></PaneActions>
        <LiveLevel label="Audio level" level={listening ? deck.level : 0} expanded>
        <LiveWell label="Dictated words" lines={[{id:"utterance",text: listening ? "Listening" : finalText || deck.utterance || (working ? "Thinking" : "Hold Talk, then speak")}]} working={listening || working} data-feedback-redact="true" /></LiveLevel>
      </div>
      <ListView label="Recent dictations" data-feedback-redact="true" rows={rows} ordered wholeRows columns={[{key:"name",word:"Recent dictations"},{key:"when",word:"At",track:"100px",priority:1},{key:"to",word:"To",track:"120px"}]}
        selectedId={picked} onSelect={id => { setPicked(id); setTyping(false); }} onOpen={id => { setPicked(id); setTyping(false); setInspecting(true); }}
        verbs={verbs} externalToolbar empty={recent.loading ? "Reading dictations" : journalError ? "" : "No recent dictations"} />
    </div>}> {typing ? <PaneInspector label="Type words" testId="speak-editor"><InspectorForm
      rows={[{label:"Utterance",control:<PadGadget inputProps={{"data-feedback-redact":"true"} as import("react").TextareaHTMLAttributes<HTMLTextAreaElement>} label="Utterance" mic={false} value={deck.utterance} onChange={deck.setUtterance} rows={4} placeholder="Type your words" onKeyDown={event => { if ((event.metaKey || event.ctrlKey) && event.key === "Enter" && !event.nativeEvent.isComposing) {event.preventDefault();void deck.deliver(deck.utterance);} }} />} ]}
      notice={finalText && finalText !== deck.utterance ? <LiveWell label="Sent words" lines={[{id:"sent",text:finalText}]} data-feedback-redact="true" /> : undefined}
      completion={{cancel:closeInspector,leading:<Button dense variant="secondary" disabled={!deck.utterance.trim()} onClick={()=>void copy(deck.utterance)}>Copy words</Button>,primary:{label:"Put words back",run:()=>void deck.deliver(deck.utterance),disabled:!deck.utterance.trim() || listening,busy:deck.busy},state:destination}} />
    </PaneInspector> : selected ? <PaneInspector label="Dictation" subtitle={humanTime(selected.created_at || selected.timestamp)} testId="speak-inspector"><InspectorBody>
      <InspectorFacts name="Dictation" rows={[{label:"Words",value:rowText(selected)},{label:"To",value:selected.target_profile ? wireWords(String(selected.target_profile)) : "Not recorded"}]} data-feedback-redact="true" />
      <PaneActions>{verbs.filter(verb=>verb.id === "copy" || verb.id === "put-back").map(verb=><SpeakVerb key={verb.id} verb={verb} selected={pickedRow} />)}</PaneActions>
    </InspectorBody></PaneInspector> : null}</ListPane>
    <StatusBar data-testid="speak-footer" items={[
      {key:"speech",text:failed ? "Failed" : speech.notSetUp ? "Speech not set up" : listening ? "Listening" : working ? "Thinking" : deck.activeState === "landed" ? "Done" : "Speech ready",lamp:failed ? "fail" : speech.notSetUp ? "ask" : undefined},
      {key:"to",text:destination},
      ...(journalError ? [{key:"journal",text:"Recent words not read",lamp:"fail" as const}] : []),
      ...(receipt && (!failed || receiptKind === "copy") ? [{key:"receipt",text:receipt,priority:90,lamp:receipt.startsWith("Not copied") ? "fail" as const : undefined}] : []),
    ]} />
  </PreferencePane>;
}

/** The list declaration also supplies the capture bar; the kit owns fit and menus. */
function SpeakVerbs({verbs,selected}:{verbs:ListVerb[];selected:ObjectListRow|null}) {
  const {ref,fits} = useStripFit<HTMLSpanElement>(true, verbs.map(verb=>verb.label).join("|"), true);
  const anchor = useRef<HTMLButtonElement>(null);
  const [open,setOpen] = useState(false);
  const rect = open ? anchor.current?.getBoundingClientRect() : null;
  return <span ref={ref} className="surface-pane-actions">
    {fits ? verbs.map(verb=><SpeakVerb key={verb.id} verb={verb} selected={selected} />) : <Button dense variant="secondary" ref={anchor} aria-haspopup="menu" aria-expanded={open} onClick={()=>setOpen(!open)}>Actions ▾</Button>}
    {rect ? <WorkMenu label="Speak actions" x={rect.left} y={rect.bottom} opener={anchor.current} autoFocus returnFocus={()=>anchor.current?.focus()} onClose={()=>setOpen(false)} entries={listVerbEntries(verbs,selected)} /> : null}
  </span>;
}

function SpeakVerb({verb,selected}:{verb:ListVerb;selected:ObjectListRow|null}) {
  return <Button dense variant="secondary" disabled={!(verb.enabled?.(selected) ?? Boolean(selected))} onClick={()=>verb.run(selected)}>{verb.label}</Button>;
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
