import { createContext, useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch } from "../../../lib/api";
import { useOptionalRuntimeBus } from "../../../runtime/RuntimeBus";
import { useSpeakDeck } from "./useSpeakDeck";
import { refusalLabel } from "./shared";
import { useTalk } from "../../../desk/components/Talk";
import { type MicState } from "../../../desk/surface/controls/MicButton";
import { Mast, ActionNotice, PadGadget, StatusBar, type StatusBarItem, PreferencePane, PreferenceWell, PaneInspector, InspectorForm, InspectorFacts, InspectorBody, PaneActions, ListView, LiveWell, LiveLevel, Lamp, Elapsed, Toolbar, CycleGadget, listVerbEntries, type ListVerb, useListApp, type ObjectListRow } from "../../../desk/surface";
import { plainFailure } from "../../../desk/surface/plainFailure";
import { wireWords } from "../../../desk/surface/words";
import { streamDate, streamTime, presentValue } from "../../../desk/surface/format";
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
  const [sentTo, setSentTo] = useState("");
  const announce = useCallback((text: string) => {
    if (text.startsWith("Sent to ")) { setSentTo(text.slice(8).replace(/ · \d+ ms$/, "")); setReceipt(""); }
    else setReceipt(text);
  }, []);
  const deck = useSpeakDeck(announce);
  const speech = useSpeechSetup();
  const refreshReadiness = deck.refreshReadiness;
  useEffect(() => onReturnToTask(() => { refreshReadiness(); }), [refreshReadiness]);
  const { talkKey, setupRow } = useSpeakTalk(deck, announce, speech);
  const bus = useOptionalRuntimeBus();
  const [journalFailure,setJournalFailure] = useState("");
  const readJournal = useCallback(async () => {
    try {
      const answer = await apiFetch<DictationJournalResponse>("/api/dictation/journal?limit=50");
      setJournalFailure("");
      return { rows: answer.items ?? [], today: Number(answer.today) || 0 };
    } catch (reason) { setJournalFailure(plainFailure("Recent dictations not read",reason)); throw reason; }
  }, []);
  const recent = useListApp({read:readJournal,keyOf:row=>String(row.id)});
  const {rows:journal,picked,setPicked,selected} = recent;
  const today = recent.page?.today ?? 0;
  const refresh = useRef(recent.reload);
  refresh.current = recent.reload;
  useEffect(() => bus?.subscribe("dictation.journal.entry", () => { void refresh.current(); }), [bus]);
  const custody = readHotkeyCustody(deck.readinessData);
  const permissionName = (row: typeof custody.rows[number]) => row.id === "input_monitoring" ? "Input Monitoring" : wireWords(row.label);
  const permissionWords = (row: typeof custody.rows[number]) => `${permissionName(row)} ${row.state === "denied" ? "refused" : "not asked"}`;
  const holdReason = custody.rows.length ? permissionWords(custody.rows[0]) : "Hold key listener did not start";
  const [typing, setTyping] = useState(false);
  const closeInspector = () => setTyping(false);
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
  const word = failed ? "Failed" : listening ? "Listening" : working ? "Thinking" : deck.activeState === "landed" ? "Done" : speech.notSetUp ? "Speech not set up" : "Ready";
  const destination = deck.aim === "agent" ? "To the agent" : "To the app in front";
  const copy = async (text: string) => {
    try { await navigator.clipboard.writeText(text); setReceipt("Copied"); }
    catch { setReceipt("Not copied · Try Copy again"); }
  };
  const rowText = (row: Record<string, unknown>) => String(row.final_text || row.transcript || "");
  const length = (text:string) => { const words=text.trim().split(/\s+/).filter(Boolean).length; return `${words} ${words===1 ? "word" : "words"}`; };
  const at = (row: Record<string,unknown>) => { const date=streamDate(row.created_at || row.timestamp); return date ? `${streamTime(date)}:${String(date.getSeconds()).padStart(2,"0")}` : ""; };
  const target = (row: Record<string,unknown>) => wireWords(presentValue(row.target_profile));
  const rows: ObjectListRow[] = journal.map(row => ({ id: String(row.id), kind: "dictation", name: rowText(row) || "No words",
    when: at(row), leadingLamp:{state:"off",label:"Recorded"}, cells: { to: target(row), length:length(rowText(row)) } }));
  const pickedRow = rows.find(row => row.id === picked) ?? null;
  const settings = () => { rememberTaskFocus(); openSurfaceOr("configure-settings", "/settings", "speak"); };
  const verbs: ListVerb[] = [
    { id: "open", label: "Open", key: "Enter", run: () => setTyping(false) },
    { id: "copy", label: "Copy", enabled: row => Boolean(row) && !listening && !working, run: () => { if (selected) void copy(rowText(selected)); } },
    { id: "put-back", label: "Put back", enabled: row => Boolean(row) && !listening && !working, run: () => { if (selected) void deck.deliver(rowText(selected)); } },
    { id: "type", label: "Type", enabled: () => !listening && !working, run: () => setTyping(true) },
    { id: "settings", label: "Settings", enabled: () => true, run: settings },
  ];
  const retry = () => { if (deck.utterance.trim()) void deck.deliver(deck.utterance); else { deck.setPhase("idle"); deck.setRefusal(""); deck.refreshReadiness(); } };
  const finalText = String(deck.result?.final_text || "");
  const engine = speechEngineName(speech) || (speech.notSetUp ? "Not set up" : "Not read");
  const copyStatus = receipt.startsWith("Not copied") ? "Not copied" : receipt === "Copied" ? "Copied" : "";
  const resultFact = receipt && !failed && !copyStatus && !receipt.startsWith("⚠") ? [{label:"Result",value:receipt}] : [];
  const setupFacts = [
    {label:"Speech",value:engine},
    {label:"Hold key",value:custody.display || "Not read"},
    {label:"To",value:deck.aim === "agent" ? "Agent" : "App in front"},
    ...custody.rows.map(row=>({label:permissionName(row),value:row.state === "denied" ? "Refused" : "Not asked"})),
    ...(sentTo && !failed && !working ? [{label:"Sent",value:sentTo}] : []),
    ...resultFact,
  ];
  return <PreferencePane label="Speak" testId="speak-face" style={{gap:0,overflow:"hidden"}}>
    <Mast kind="dictation" glyph={SYSTEM.dockSpeak} title="Speak" figures={listening && started !== null ? [{value:<Elapsed start={started} />,label:"Listening",tone:"stop"}] : today ? [{value:today,label:"today"}] : undefined} facts={<span data-testid="speak-phase">{word}{custody.display && !custody.show ? ` · Hold ${custody.display}` : ""}</span>} />
    <ShowMe app="surface-dictation" />
    <Toolbar label="Speak" trailingStays trailing={<CycleGadget label="To" roster value={deck.aim === "agent" ? "agent" : "focused"} options={[{value:"focused",label:"App in front"},{value:"agent",label:"Agent"}]} onChange={deck.pickAim} disabled={listening || working} />}>
      {talkKey}<SpeakVerbs verbs={verbs} selected={pickedRow} />
    </Toolbar>
    <div className="surface-pane-actions" style={{flex:"1 1 0",minHeight:0,gap:0,alignItems:"stretch",alignContent:"stretch",overflow:"hidden"}}>
      <div data-feedback-redact="true" className="object-list" style={{gap:12,padding:12,border:0,flex:"2 1 320px",contain:"size",minHeight:failed ? 100 : 0,overflow:"hidden"}}>
        <div className="surface-live-well" data-testid="speak-live" style={{height:"auto",maxHeight:"none",minHeight:140,flex:"0 1 180px",overflow:"auto",gap:12,fontFamily:"var(--font-sans)"}}>
          <PaneActions><Lamp state={failed ? "failed" : listening || working ? "working" : speech.notSetUp ? "waiting" : deck.activeState === "landed" ? "done" : "off"} label={word} /><span>{word === "Speech not set up" ? "Not set up" : word} · <span data-testid="speak-types-into">{destination}</span></span><span style={{marginLeft:"auto",fontSize:24,fontWeight:700}}>{started !== null ? <Elapsed start={started} running={listening} end={listening ? undefined : ended} /> : "0:00"}</span></PaneActions>
          <LiveLevel label="Audio level" level={listening ? deck.level : 0} expanded>
            <LiveWell label="Dictated words" lines={[{id:"utterance",text:listening ? "" : finalText || deck.utterance || (working ? "Thinking" : "Hold Talk, then speak")}]} working={working} data-feedback-redact="true" />
          </LiveLevel>
        </div>
        {setupRow}
        {custody.show ? <div data-testid="speak-hotkey" title={custody.rows.map(permissionWords).join(" · ") || holdReason}><ActionNotice tone="warn" action={{label:"Fix hold key",onClick:settings}}>{holdReason}</ActionNotice></div> : null}
        {failed ? <ActionNotice tone="danger" action={deck.micState === "failed" ? undefined : {label:"Retry",onClick:retry}}>{failureWords} · Nothing was typed</ActionNotice> : null}
        {recent.error ? <ActionNotice tone="danger" action={{label:"Try again",onClick:()=>void recent.reload()}}>{journalFailure} · Nothing changed</ActionNotice> : <ListView label="Recent dictations" data-feedback-redact="true" rows={rows} ordered wholeRows columns={[{key:"name",word:"Recent dictations",track:"4fr",minWidth:180},{key:"when",word:"At",track:".9fr",minWidth:82,priority:3},{key:"to",word:"To",track:"1fr",minWidth:90},{key:"length",word:"Length",track:".9fr",minWidth:80,priority:1}]}
          selectedId={picked} onSelect={id=>{setPicked(id);setTyping(false);}} onOpen={id=>{setPicked(id);setTyping(false);}}
          verbs={verbs} externalToolbar empty={recent.loading ? "Reading dictations" : "No recent dictations"} />}
      </div>
      <div className="surface-inspector-body" style={{flex:"1 1 160px",contain:"size",minHeight:0,overflow:"hidden"}}>
        {typing ? <PaneInspector label="Type words" testId="speak-editor"><InspectorForm
          rows={[{label:"Dictation",control:<PadGadget inputProps={{"data-feedback-redact":"true"} as import("react").TextareaHTMLAttributes<HTMLTextAreaElement>} label="Dictation" mic={false} value={deck.utterance} onChange={deck.setUtterance} rows={3} placeholder="Type your words" onKeyDown={event=>{if((event.metaKey || event.ctrlKey) && event.key === "Enter" && !event.nativeEvent.isComposing){event.preventDefault();void deck.deliver(deck.utterance);}}} />}]}
          notice={finalText && finalText !== deck.utterance ? <LiveWell label="Sent words" lines={[{id:"sent",text:finalText}]} data-feedback-redact="true" /> : undefined}
          facts={sentTo && !failed && !working && [deck.result?.raw_text,deck.result?.final_text].includes(deck.utterance) ? {name:"Delivery",rows:[{label:"Sent",value:sentTo}]} : undefined}
          completion={{cancel:closeInspector,leading:<Button dense variant="secondary" disabled={!deck.utterance.trim()} onClick={()=>void copy(deck.utterance)}>Copy words</Button>,primary:{label:"Put words back",run:()=>void deck.deliver(deck.utterance),disabled:!deck.utterance.trim() || listening,busy:deck.busy},state:destination}} />
        </PaneInspector> : selected ? <PaneInspector label={rowText(selected).split(/\s+/).slice(0,6).join(" ")} object={<img src={SYSTEM.dockSpeak} alt="" width={32} height={32} />} subtitle={`Dictation · ${at(selected)}`} testId="speak-inspector"><InspectorBody>
          <PreferenceWell><InspectorFacts header={false} name="Dictation" rows={[{label:"Words",value:rowText(selected)},...(target(selected) ? [{label:"To",value:target(selected)}] : []),{label:"Length",value:length(rowText(selected))},{label:"Speech now",value:engine},...(selected.source === "hotkey" && custody.display ? [{label:"Hold key",value:custody.display}] : []),...(sentTo && !failed && !working && [deck.result?.raw_text,deck.result?.final_text].includes(rowText(selected)) ? [{label:"Sent",value:sentTo}] : []),...resultFact]} data-feedback-redact="true" /></PreferenceWell>
          <PaneActions>{verbs.filter(verb=>verb.id === "copy" || verb.id === "put-back").map(verb=><SpeakVerb key={verb.id} verb={verb} selected={pickedRow} />)}</PaneActions>
        </InspectorBody></PaneInspector> : <PaneInspector label="Speech setup" object={<img src={SYSTEM.dockSpeak} alt="" width={32} height={32} />} testId="speak-setup-facts"><InspectorFacts header={false} name="Speech setup" data-feedback-redact="true" rows={setupFacts} /></PaneInspector>}
      </div>
    </div>
    <StatusBar data-testid="speak-footer" items={[
      {key:"speech",text:copyStatus || (failed ? "Failed" : speech.notSetUp ? "Speech not set up" : listening ? "Listening" : working ? "Thinking" : deck.activeState === "landed" ? "Done" : "Ready"),lamp:copyStatus === "Not copied" ? "fail" : failed ? "fail" : speech.notSetUp ? "ask" : listening || working ? "info" : "ok"},
      {key:"to",text:destination},
      ...(today ? [{key:"today",priority:99,text:`${today} ${today===1 ? "dictation" : "dictations"} today`}] : []),

    ]} />
  </PreferencePane>;
}

/** One declaration supplies the bar, context menu and app menu. Pane verbs
 * always stay in Actions; row verbs join it when the shared measured strip folds. */
function SpeakVerbs({verbs,selected}:{verbs:ListVerb[];selected:ObjectListRow|null}) {
  const {ref,fits} = useStripFit<HTMLSpanElement>(true,verbs.map(verb=>verb.label).join("|"),true);
  const anchor = useRef<HTMLButtonElement>(null);
  const [open,setOpen] = useState(false);
  const rect = open ? anchor.current?.getBoundingClientRect() : null;
  const rowVerbs=verbs.filter(verb=>["open","copy","put-back"].includes(verb.id));
  const menuVerbs=fits ? verbs.filter(verb=>!rowVerbs.includes(verb)) : verbs;
  return <span ref={ref} className="surface-pane-actions">
    {fits ? rowVerbs.map(verb=><SpeakVerb key={verb.id} verb={verb} selected={selected} />) : null}
    <Button dense variant="secondary" ref={anchor} aria-haspopup="menu" aria-expanded={open} onClick={()=>setOpen(!open)}>Actions ▾</Button>
    {rect ? <WorkMenu label="Speak actions" x={rect.left} y={rect.bottom} opener={anchor.current} autoFocus returnFocus={()=>anchor.current?.focus()} onClose={()=>setOpen(false)} entries={listVerbEntries(menuVerbs,selected).map(entry=>entry.type === "item" ? {...entry,onSelect:()=>{anchor.current?.focus();entry.onSelect();}} : entry)} /> : null}
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
    { speech, testId: "speak-speech-setup", primary: true, appearance: "verb", onReady: deck.refreshReadiness },
  );
}
