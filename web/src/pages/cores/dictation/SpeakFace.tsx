import { createContext, useCallback, useEffect, useMemo, useRef, useState, type ReactNode, type CSSProperties } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch } from "../../../lib/api";
import { useOptionalRuntimeBus } from "../../../runtime/RuntimeBus";
import { useSpeakDeck } from "./useSpeakDeck";
import { refusalLabel } from "./shared";
import { useTalk } from "../../../desk/components/Talk";
import { type MicState } from "../../../desk/surface/controls/MicButton";
import { Mast, ActionNotice, PadGadget, StatusBar, type StatusBarItem, ListPane, PreferencePane, PreferenceWell, PaneInspector, InspectorForm, InspectorFacts, InspectorBody, PaneActions, ListView, LiveWell, LiveLevel, Lamp, Elapsed, Toolbar, ToolbarFold, CycleGadget, type ListVerb, useListApp, type ObjectListRow } from "../../../desk/surface";
import { plainFailure } from "../../../desk/surface/plainFailure";
import { wireWords } from "../../../desk/surface/words";
import { streamDate, clockOf, isSameStreamDay, wireDayClock, presentValue } from "../../../desk/surface/format";
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
import { useCompactViewport } from "../../../desk/useCompactViewport";

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

function rowText(row: Record<string,unknown>) { return String(row.final_text || row.transcript || ""); }
function at(row: Record<string,unknown>, seconds = false) {
  const date=streamDate(row.created_at || row.timestamp);
  return !date ? "" : isSameStreamDay(date, new Date()) ? clockOf(date, seconds) : wireDayClock(date).split(",")[0];
}

export function SpeakFace() {
  const compact=useCompactViewport();
  const [inspecting,setInspecting]=useState(false);
  const selectedRetry=useRef<string | null>(null);
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
  const closeInspector = () => {setTyping(false);setInspecting(false);};
  const [ended, setEnded] = useState<number | undefined>(undefined);
  const [started, setStarted] = useState<number | null>(null);
  const listening = deck.activeState === "listening";
  const working = deck.activeState === "busy" || deck.busy;
  const compactCapture = compact && Boolean(selected) && !listening && deck.micState !== "busy";
  const failed = deck.activeState === "refused" || Boolean(deck.error);
  const failureCode = deck.refusal || deck.failure || "unknown";
  const failureWords = Object.prototype.hasOwnProperty.call(DICTATION_FAILURES, failureCode)
    ? DICTATION_FAILURES[failureCode as keyof typeof DICTATION_FAILURES].message.split(". ")[0].replace(/\.$/, "")
    : refusalLabel(failureCode);
  useEffect(() => { if (listening) { selectedRetry.current=null; setReceipt(""); setSentTo(""); setStarted(Date.now()); setEnded(undefined); } else setEnded(Date.now()); }, [listening]);
  const word = failed ? "Failed" : listening ? "Listening" : working ? "Thinking" : deck.activeState === "landed" ? "Done" : speech.notSetUp ? "Speech not set up" : "Ready";
  const destination = deck.aim === "agent" ? "To the agent" : "To the app in front";
  const copy = async (text: string) => {
    try { await navigator.clipboard.writeText(text); setReceipt("Copied"); }
    catch { setReceipt("Not copied · Try Copy again"); }
  };
  const length = (text:string) => { const words=text.trim().split(/\s+/).filter(Boolean).length; return `${words} ${words===1 ? "word" : "words"}`; };
  // Identical words in one displayed second keep their stored entry identity.
  const timeById=useMemo(()=>{
    const minutes=new Map<string,number>();
    for (const row of journal) {
      const date=streamDate(row.created_at || row.timestamp);
      if (date && isSameStreamDay(date, new Date())) { const minute=clockOf(date); minutes.set(minute,(minutes.get(minute) ?? 0)+1); }
    }
    const stamps=journal.map(row=>({id:String(row.id),clock:at(row,(minutes.get(at(row)) ?? 0)>1),words:rowText(row)}));
    const repeats=new Map<string,number>();
    for(const stamp of stamps) {const key=`${stamp.words}|${stamp.clock}`;repeats.set(key,(repeats.get(key) ?? 0)+1);}
    return new Map(stamps.map(stamp=>[stamp.id,(repeats.get(`${stamp.words}|${stamp.clock}`) ?? 0)>1 ? `${stamp.clock} · #${stamp.id}` : stamp.clock]));
  },[journal]);
  const recordTime = (row: Record<string,unknown>) => timeById.get(String(row.id)) ?? at(row);
  const repeatedTime=[...timeById.values()].some(time=>time.includes(" · #"));
  const target = (row: Record<string,unknown>) => wireWords(presentValue(row.target_profile));
  const rows: ObjectListRow[] = journal.map(row => ({ id: String(row.id), kind: "dictation", name: rowText(row) || "No words",
    when: recordTime(row), leadingLamp:{state:"off",label:"Delivery not reported"}, cells: { to: target(row), length:length(rowText(row)) } }));
  const pickedRow = rows.find(row => row.id === picked) ?? null;
  const settings = () => { rememberTaskFocus(); openSurfaceOr("configure-settings", "/settings", "speak"); };
  const verbs: ListVerb[] = [
    { id: "open", label: "Open", key: "Enter", run: () => {setTyping(false);setInspecting(true);} },
    { id: "copy", label: "Copy", enabled: row => Boolean(row) && !listening && !working, run: () => { if (selected) void copy(rowText(selected)); } },
    { id: "put-back", label: "Put back", enabled: row => Boolean(row) && !listening && !working, run: () => { if (selected) {selectedRetry.current=rowText(selected);void deck.deliver(selectedRetry.current);} } },
    { id: "type", label: "Type", toolbar:false, enabled: () => !listening && !working, run: () => {setTyping(true);setInspecting(true);} },
    { id: "settings", label: "Settings", toolbar:false, enabled: () => true, run: settings },
  ];
  const sendTyped = () => {selectedRetry.current=null;return deck.deliver(deck.utterance);};
  const retry = () => { const words=selectedRetry.current ?? deck.utterance; if (words.trim()) void deck.deliver(words); else { deck.setPhase("idle"); deck.setRefusal(""); deck.refreshReadiness(); } };
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
  const master=<div data-feedback-redact="true" className="object-list" style={{gap:compactCapture ? 8 : 12,padding:compactCapture ? 8 : 12,border:0,flex:compactCapture ? "1 1 0" : "2 1 320px",contain:"size",minHeight:failed ? 100 : 0,overflow:"hidden"}}>
        <div className="surface-live-well" data-testid="speak-live" data-compact={compactCapture || undefined} style={{height:compactCapture ? 44 : "auto",maxHeight:"none",minHeight:compactCapture ? 44 : 140,flex:compactCapture ? "none" : "0 1 180px",overflow:"auto",gap:12,fontFamily:"var(--font-sans)"}}>
          <PaneActions style={{flexWrap:"nowrap"}}><Lamp state={failed ? "failed" : listening || working ? "working" : speech.notSetUp ? "waiting" : deck.activeState === "landed" ? "done" : "off"} label={word} /><span data-testid="speak-well-words">{compactCapture ? "Hold Talk, then speak" : <>{word === "Speech not set up" ? "Not set up" : word} · <span data-testid="speak-types-into">{destination}</span></>}</span><span style={{marginLeft:"auto",fontSize:24,fontWeight:700}}>{started !== null ? <Elapsed start={started} running={listening} end={listening ? undefined : ended} /> : "0:00"}</span></PaneActions>
          {!compactCapture ? <LiveLevel label="Audio level" level={listening ? deck.level : 0} expanded>
            <LiveWell label="Dictated words" lines={[{id:"utterance",text:listening ? "" : ((failed || working) && selectedRetry.current) || finalText || deck.utterance || (working ? "Thinking" : "Hold Talk, then speak")}]} working={working} data-feedback-redact="true" />
          </LiveLevel> : null}
        </div>
        {setupRow}
        {custody.show ? <div data-testid="speak-hotkey" title={custody.rows.map(permissionWords).join(" · ") || holdReason}><ActionNotice tone="warn" action={{label:"Fix hold key",onClick:settings}}><span className="surface-pane-actions"><Lamp state="waiting" label={holdReason} />{holdReason}</span></ActionNotice></div> : null}
        {failed ? <ActionNotice tone="danger" action={deck.micState === "failed" ? undefined : {label:"Retry",onClick:retry}}>{failureWords} · Nothing was typed</ActionNotice> : null}
        {recent.error ? <ActionNotice tone="danger" action={{label:"Try again",onClick:()=>void recent.reload()}}>{journalFailure} · Nothing changed</ActionNotice> : <ListView label="Recent dictations" data-feedback-redact="true" rows={rows} ordered wholeRows columns={[{key:"when",word:"At",track:repeatedTime ? "132px" : "82px",priority:3},{key:"name",word:"Recent dictations",track:"1fr",minWidth:180},...(rows.some(row=>row.cells?.to) ? [{key:"to",word:"To",track:"90px"}] : []),{key:"length",word:"Length",track:"80px",priority:1}]}
          selectedId={picked} onSelect={id=>{setPicked(id);setTyping(false);}} onOpen={id=>{setPicked(id);setTyping(false);setInspecting(true);}}
          verbs={verbs} externalToolbar empty={recent.loading ? "Reading dictations" : "No recent dictations"} />}
      </div>;
  const detail=<div data-feedback-redact="true" className="surface-inspector-body" style={{display:compactCapture ? "contents" : undefined,flex:compactCapture ? "none" : "1 1 160px",contain:compactCapture ? undefined : "size",minHeight:0,overflow:"hidden",...(!typing && selected ? {"--surface-hover":"var(--hs-plate)"} : {})} as CSSProperties}>
        {typing ? <PaneInspector label="Type words" testId="speak-editor"><InspectorForm fit="rows"
          rows={[{label:"Dictation",control:<PadGadget inputProps={{"data-feedback-redact":"true"} as import("react").TextareaHTMLAttributes<HTMLTextAreaElement>} label="Dictation" mic={false} value={deck.utterance} onChange={deck.setUtterance} rows={3} placeholder="Type your words" onKeyDown={event=>{if((event.metaKey || event.ctrlKey) && event.key === "Enter" && !event.nativeEvent.isComposing){event.preventDefault();void sendTyped();}}} />}]}
          notice={finalText && finalText !== deck.utterance ? <LiveWell label="Sent words" lines={[{id:"sent",text:finalText}]} data-feedback-redact="true" /> : undefined}
          facts={sentTo && !failed && !working && [deck.result?.raw_text,deck.result?.final_text].includes(deck.utterance) ? {name:"Delivery",rows:[{label:"Sent",value:sentTo}]} : undefined}
          completion={{cancel:closeInspector,leading:<Button dense variant="secondary" disabled={!deck.utterance.trim()} onClick={()=>void copy(deck.utterance)}>Copy words</Button>,primary:{label:"Put words back",run:()=>void sendTyped(),disabled:!deck.utterance.trim() || listening,busy:deck.busy},state:destination}} />
        </PaneInspector> : selected ? <PaneInspector label={rowText(selected)} object={<img src={SYSTEM.dockSpeak} alt="" width={32} height={32} />} subtitle={`Dictation · ${recordTime(selected)}`} testId="speak-inspector"><InspectorBody>
          <SelectedFacts compact={compactCapture}><InspectorFacts header={false} name="Dictation" rows={[{label:"Words",value:rowText(selected)},...(target(selected) ? [{label:"To",value:target(selected)}] : []),{label:"Length",value:length(rowText(selected))},{label:"Speech now",value:engine},...(selected.source === "hotkey" && custody.display ? [{label:"Hold key now",value:custody.display}] : []),...(sentTo && !failed && !working && [deck.result?.raw_text,deck.result?.final_text].includes(rowText(selected)) ? [{label:"Sent",value:sentTo}] : []),...resultFact]} data-feedback-redact="true" /></SelectedFacts>
        </InspectorBody></PaneInspector> : <PaneInspector label="Speech setup" object={<img src={SYSTEM.dockSpeak} alt="" width={32} height={32} />} testId="speak-setup-facts"><InspectorFacts header={false} name="Speech setup" data-feedback-redact="true" rows={setupFacts} /></PaneInspector>}
      </div>;
  return <PreferencePane label="Speak" testId="speak-face" style={{gap:0,overflow:"hidden"}}>
    <Mast kind="dictation" glyph={SYSTEM.dockSpeak} title="Speak" figures={listening && started !== null ? [{value:<Elapsed start={started} />,label:"Listening",tone:"stop"}] : today ? [{value:today,label:"today"}] : undefined} facts={<span data-testid="speak-phase">{word}{custody.display && !custody.show ? ` · Hold ${custody.display}` : ""}</span>} />
    <ShowMe app="surface-dictation" />
    <Toolbar label="Speak" trailingStays trailing={<CycleGadget label="To" roster value={deck.aim === "agent" ? "agent" : "focused"} options={[{value:"focused",label:"App in front"},{value:"agent",label:"Agent"}]} onChange={deck.pickAim} disabled={listening || working} />}>
      {talkKey}<ToolbarFold verbs={verbs.map(verb=>({key:verb.id,label:verb.label,menuOnly:verb.toolbar === false,disabled:!(verb.enabled?.(pickedRow) ?? Boolean(pickedRow)),onSelect:()=>verb.run(pickedRow)}))} />
    </Toolbar>
    {compact ? <div className="surface-pane-actions" style={{display:compactCapture ? "grid" : undefined,gridTemplateRows:compactCapture ? "minmax(0,1fr) auto" : undefined,flex:"1 1 0",minHeight:0,gap:0,flexDirection:"column",flexWrap:"nowrap",alignItems:"stretch",overflow:"hidden"}}>{master}{detail}</div>
      : <ListPane deck listShare={2/3} open={inspecting} onBack={()=>setInspecting(false)} label="Speak inspector" list={master}>{detail}</ListPane>}
    <StatusBar data-testid="speak-footer" parts={[
      {key:"speech",text:copyStatus || (failed ? "Failed" : speech.notSetUp ? "Speech not set up" : listening ? "Listening" : working ? "Thinking" : deck.activeState === "landed" ? "Done" : "Ready"),lamp:copyStatus === "Not copied" ? "fail" : failed ? "fail" : speech.notSetUp ? "ask" : listening || working ? "info" : "ok"},
      {key:"to",text:destination},
      ...(today ? [{key:"today",priority:99,text:`${today} ${today===1 ? "dictation" : "dictations"} today`}] : []),

    ]} />
  </PreferencePane>;
}

/** A compact selection reads its facts in place; a live/wide seat scrolls them. */
function SelectedFacts({compact,children}:{compact:boolean;children:ReactNode}) {
  return compact ? <>{children}</> : <PreferenceWell fit="reading">{children}</PreferenceWell>;
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
