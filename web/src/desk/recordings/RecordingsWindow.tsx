import { useGuideView } from "../walk/viewState";
/* One selection list; capture still uses the desk's one store. */
import { useEffect, useRef, useState } from "react";
import { readableError } from "../../lib/api";
import type { CoreProps } from "../../pages/cores/core-types";
import { openRef } from "../openObject";
import { CheckGadget, InspectorFacts, InspectorQuestion, ListApp, PaneInspector, PreferenceWell, SegmentedTabs, countWords, type ListVerb, type ObjectListRow } from "../surface";
import { ShowMe } from "../walk/ShowMe";
import { canCapture, isLive, setVoice, stopCapture, useCapture } from "./capture";
import { lengthWords, openRecordingsFolder, parkRecording, posterUrl, retryRecording, shareRecording, sizeWords, unshareRecording, useRecordings, videoUrl } from "./api";
import { pressScreenRecord, useLiveClock } from "./ScreenRecord";
import type { Recording } from "./types";

const whenOf = (row: Recording) => row.title.replace(/^Recording · /, "");
const dateOf = (seconds: number) => new Date(seconds * 1000).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
const keptUntil = (row: Recording, days: number) => days > 0 ? dateOf(row.started_ts + days * 86400) : "";
const value = (text: string) => <span className="surface-preference-value" title={text}>{text}</span>;

function RecordingDetails({ row, keepDays }: { row: Recording; keepDays: number }) {
  const [tab, setTab] = useState("details");
  return <SegmentedTabs label="Recording details" value={tab} onChange={setTab} tabs={[
    { id: "details", label: "Details" },
    ...(row.state === "ready" ? [{ id: "video", label: "Video" }] : []),
    ...(row.state === "ready" && row.shared ? [{ id: "links", label: "Links" }] : []),
  ]}><PreferenceWell>
    {tab === "video" && row.state === "ready" ? <InspectorFacts name={whenOf(row)} rows={[
      { label: "Video", value: <video data-testid="recordings-video" aria-label={whenOf(row)} width={320} height={180} src={videoUrl(row.id)} poster={row.encoder === "mp4" ? posterUrl(row.id) : undefined} controls playsInline preload="metadata" /> },
      ...(row.encoder === "webm" ? [{ label: "Format", value: <span data-testid="recordings-webm">Webm · iPhone video needs ffmpeg</span> }] : []),
    ]} /> : tab === "links" && row.state === "ready" && row.shared ? <InspectorFacts name={whenOf(row)} testId="recordings-links" rows={[
      ...(row.links.tailnet ? [{ label: "On your phone", value: <span data-testid="recordings-link-tailnet" data-feedback-redact="true" className="surface-preference-value" title={row.links.tailnet}>{row.links.tailnet}</span> }] : []),
      ...(row.links.local ? [{ label: "On this Mac", value: <span data-testid="recordings-link-local" data-feedback-redact="true" className="surface-preference-value" title={row.links.local}>{row.links.local}</span> }] : []),
    ]} /> : <InspectorFacts name={whenOf(row)} rows={[
      ...(row.state === "failed" ? [{ label: "Needs you", value: <span data-testid="recordings-wait">{row.error || "Recording failed"}</span> }] : []),
      { label: "Length", value: row.duration_s ? lengthWords(row.duration_s) : "" },
      { label: "Kept until", value: keptUntil(row, keepDays) },
      { label: "Size", value: row.bytes_out ? sizeWords(row.bytes_out) : "" },
    ]} />}
  </PreferenceWell></SegmentedTabs>;
}

export function RecordingsCore(_props: CoreProps) {
  const data = useRecordings();
  const capture = useCapture();
  const clock = useLiveClock(capture);
  const [panel, setPanel] = useState<"capture" | "storage" | "remove" | null>(null);
  const [removeId, setRemoveId] = useState<string | null>(null);
  const [busy, setBusy] = useState("");
  const [notice, setNotice] = useState("");
  const [failed, setFailed] = useState(false);
  useGuideView(() => ({panel,removeId,notice}), saved => {setPanel(saved.panel);setRemoveId(saved.removeId);setNotice(saved.notice);}, undefined, 1);
  const locked = useRef(false);
  const captured = useRef<string | null>(null);
  const rows = data.payload.recordings;
  const shown = data.selected;
  const live = isLive(capture);
  const available = canCapture();
  // Stop leaves the recording made here selected; another selection wins.
  useEffect(() => {
    if (capture.phase === "recording" && !capture.remote && panel === "capture") captured.current = capture.id;
    if (capture.phase === "idle" && captured.current) {
      if (panel === "capture") { data.setPicked(captured.current); setPanel(null); }
      captured.current = null;
    }
  }, [capture.phase, capture.id, capture.remote, panel]);
  const run = async (kind: string, act: () => Promise<void>) => {
    if (locked.current) return;
    locked.current = true; setBusy(kind); setNotice(""); setFailed(false);
    try { await act(); } catch (error) { setNotice(readableError(error)); setFailed(true); }
    finally { locked.current = false; setBusy(""); }
  };
  const selected = (row: ObjectListRow | null) => rows.find((recording) => recording.id === row?.id);
  const copy = (href: string) => void run("copy", async () => { await navigator.clipboard.writeText(href); setNotice("Copied"); });
  const ready = (row: ObjectListRow | null) => !busy && selected(row)?.state === "ready";
  const retry = shown?.state === "failed";
  const verbs: ListVerb[] = [
    { id: "new", label: live ? "Stop" : "New recording", key: "n", testId: live ? "recordings-stop" : "recordings-capture-open",
      enabled: () => !busy && capture.phase !== "asking" && capture.phase !== "stopping",
      run: () => { if (live) stopCapture(); else { setPanel("capture"); setNotice(""); } } },
    { id: "open", label: "Open note", key: "Enter", testId: "recordings-open-note", enabled: (row) => !busy && Boolean(selected(row)?.note_ref), run: (row) => openRef(selected(row)!.note_ref) },
    retry ? { id: "retry", label: "Retry", key: "r", testId: "recordings-retry", enabled: (row) => !busy && selected(row)?.state === "failed" && Boolean(selected(row)?.bytes_in), run: (row) => void run("retry", async () => { data.apply(await retryRecording(row!.id)); }) }
      : { id: "share", label: shown?.shared ? "Stop sharing" : "Share", key: "s", testId: "recordings-share", enabled: ready, run: (row) => void run("share", async () => { const recording = selected(row)!; data.apply(await (recording.shared ? unshareRecording(recording.id) : shareRecording(recording.id))); }) },
    { id: "remove", label: "Remove", key: "Delete", testId: "recordings-park", enabled: (row) => !busy && ["ready", "failed"].includes(selected(row)?.state ?? ""), run: (row) => { setRemoveId(row!.id); setPanel("remove"); setNotice(""); } },
    { enabled: () => true, id: "more", label: "More", items: [
      { id: "phone-link", label: "Copy phone link", testId: "recordings-link-tailnet-copy", enabled: (row) => ready(row) && Boolean(selected(row)?.shared && selected(row)?.links.tailnet), run: (row) => copy(selected(row)!.links.tailnet!) },
      { id: "mac-link", label: "Copy Mac link", testId: "recordings-link-local-copy", enabled: (row) => ready(row) && Boolean(selected(row)?.shared && selected(row)?.links.local), run: (row) => copy(selected(row)!.links.local!) },
      { enabled: () => true, id: "storage", label: "Storage", testId: "recordings-storage", run: () => setPanel("storage") },
      { id: "folder", label: "Open folder", testId: "settings-recordings-open-folder", enabled: () => !busy, run: () => void run("folder", async () => { const answer = await openRecordingsFolder(); if (!answer.opened) throw new Error("The folder did not open"); setNotice("Folder opened"); }) },
    ], run: () => undefined },
  ];
  const needsYou = rows.filter((row) => row.state === "failed").length;
  return <ListApp app={data} label="Recordings"
    ids={{ windowTestId: "recordings-window", listTestId: "recordings-list", paneTestId: "recordings-document", toolbarTestId: "recordings-toolbar", statusTestId: "recordings-status" }}
    words={{ find: "Find a recording", empty: "No recordings yet", noMatch: "No recordings found", select: "Select a recording." }}
    onSelect={() => { setPanel(null); setNotice(""); }}
    row={row => ({ id: row.id, kind: "recording", name: whenOf(row),
      state: row.state === "failed" ? { label: "Failed", tone: "fail" } : undefined,
      cells: { length: row.duration_s ? lengthWords(row.duration_s) : "", kept: keptUntil(row, data.payload.usage.keep_days) } })}
    list={{ columns: [
      { key: "name", word: "Recording", priority: 100, track: "minmax(0, 2fr)", minWidth: 180 },
      { key: "state", word: "State", priority: 40, track: "100px" },
      { key: "length", word: "Length", priority: 30, track: "90px" },
      { key: "kept", word: "Kept until", priority: 10, track: "130px" },
    ], verbs, defaultVerb: "open", rowProps: row => ({ "data-testid": "recordings-row", "data-recording": row.id, "data-state": rows.find(recording => recording.id === row.id)?.state }) }}
    status={[
      rows.length ? { text: countWords(rows.length, "recording") } : null,
      needsYou ? { text: `${needsYou} ${needsYou === 1 ? "needs" : "need"} you`, lamp: "ask" } : null,
      live ? { text: capture.remote ? "Recording on another view" : `Recording ${clock || ""}` } : null,
      notice || capture.error ? { text: notice || capture.error, lamp: failed || capture.error ? "fail" : undefined, testId: "recordings-refusal" } : null,
    ]} pane={() =>
      panel === "remove" && removeId && rows.some((row) => row.id === removeId) ? <InspectorQuestion actionId="remove-recording" targetId={removeId} question="Remove recording?" consequence={value(whenOf(rows.find((row) => row.id === removeId)!))} cancel={() => setPanel(null)} verb={{ label: "Remove", testId: "recordings-remove-confirm", busy: busy === "park", disabled: Boolean(busy), run: () => void run("park", async () => {
        const answer = await parkRecording(removeId); if (!answer.parked) throw new Error("The recording was not removed"); data.drop(removeId); data.setPicked((current) => current === removeId ? null : current); setPanel((current) => current === "remove" ? null : current); setNotice("Recording moved to the parked folder");
      }) }} /> : panel === "capture" ? <PaneInspector label={live ? "Recording now" : "New recording"} rows={[
        ...(live ? [{ label: "Length", control: capture.remote ? "Recording on another view" : clock || "" }] : available ? [{ label: "Voice", control: <CheckGadget label="Voice" checked={capture.voice} onChange={setVoice} /> }] : [{ label: "Screen", control: "Record from your computer" }]),
      ]} completion={available && !live ? { cancel: () => setPanel(null), cancelDisabled: capture.phase === "asking", primary: { label: "Record screen", testId: "recordings-record", busy: capture.phase === "asking", run: pressScreenRecord } } : { done: () => setPanel(null) }} />
        : panel === "storage" ? <PaneInspector label="Storage"><InspectorFacts name="Storage" rows={[
          { label: "Keep", value: <span data-testid="settings-recordings-usage">{data.payload.usage.keep_days > 0 ? `${data.payload.usage.keep_days} days` : "For good"}</span> },
          { label: "Used", value: sizeWords(data.payload.usage.bytes) },
          { label: "Folder", value: value(data.payload.folder) },
        ]} /></PaneInspector>
          : shown ? <PaneInspector label={whenOf(shown)}><RecordingDetails key={shown.id} row={shown} keepDays={data.payload.usage.keep_days} /></PaneInspector> : null}>
    <ShowMe app="open-recordings" />
  </ListApp>;
}

export default RecordingsCore;
