/* Parked: the rail and capture card were replaced by the kit selection list. */
/* One recording beside its rail. Capture uses the desk's one store. */
import { useRef, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { readableError } from "../../../lib/api";
import type { CoreProps } from "../../../pages/cores/core-types";
import { openRef } from "../../openObject";
import { Rail, Mast, Spine, ConfirmVerb, Disclosure, CheckGadget, DotWord, StatusBar, SurfaceState, countWords, type SpineTone } from "../../surface";
import { useWindowInterior } from "../../surface/interior";
import { ShowMe } from "../../walk/ShowMe";
import { SPRITE_BASE } from "../../sprites";
import { canCapture, isLive, setVoice, stopCapture, useCapture } from "../capture";
import { lengthWords, parkRecording, posterUrl, retryRecording, shareRecording, sizeWords, unshareRecording, useRecordings, videoUrl } from "../api";
import { RecordingsSettings } from "../RecordingsSettings";
import { pressScreenRecord, useLiveClock } from "../ScreenRecord";
import type { Recording } from "../types";
import "./recordings_20261110.css";

export function stateOf(row: Recording): { word: string; tone: "fail" | "info" | "warn" | "ok"; spine: SpineTone; live?: boolean } {
  switch (row.state) {
    case "recording": return { word: "Recording", tone: "info", spine: "steel", live: true };
    case "encoding": return { word: `Encoding ${Math.max(0, Math.min(99, row.progress || 0))} %`, tone: "info", spine: "steel", live: true };
    case "failed": return { word: "Failed", tone: "fail", spine: "coral" };
    default: return row.encoder === "webm" ? { word: "Ready · webm", tone: "warn", spine: "brass" } : { word: "Ready", tone: "ok", spine: "moss" };
  }
}
const whenOf = (row: Recording) => row.title.replace(/^Recording · /, "");

function CopyLink({ href, label = "Copy", testId }: { href: string; label?: string; testId: string }) {
  const [receipt, setReceipt] = useState("");
  const copy = async () => {
    try { await navigator.clipboard.writeText(href); setReceipt("Copied"); }
    catch { setReceipt("Copy failed"); }
  };
  return <Button dense onClick={() => void copy()} title={href} data-testid={testId}>{receipt || label}</Button>;
}
function ShareUrlRow({ label, href, testId, copy = true }: { label: string; href: string; testId: string; copy?: boolean }) {
  return <div className="recordings-link" data-testid={testId}>
    <span>{label}</span><span className="recordings-link-url" title={href}>{href}</span>
    {copy ? <CopyLink key={href} href={href} testId={`${testId}-copy`} /> : null}
  </div>;
}

export function RecordingsCore(_props: CoreProps) {
  useWindowInterior("list");
  const data = useRecordings();
  const capture = useCapture();
  const clock = useLiveClock(capture);
  const [picked, setPicked] = useState<string | null>(null);
  const [paneOpen, setPaneOpen] = useState(false);
  const [busy, setBusy] = useState("");
  const [refusal, setRefusal] = useState("");
  const [receipt, setReceipt] = useState("");
  const locked = useRef(false);
  const rows = data.payload.recordings;
  const shown = rows.find((row) => row.id === picked) ?? rows[0];
  const live = isLive(capture);
  const available = canCapture();
  const run = async (kind: string, act: () => Promise<void>) => {
    if (locked.current) return;
    locked.current = true; setBusy(kind); setRefusal(""); setReceipt("");
    try { await act(); } catch (error) { setRefusal(readableError(error)); }
    finally { locked.current = false; setBusy(""); }
  };
  const state = shown ? stateOf(shown) : null;
  const notice = refusal || capture.error || receipt;
  return <div className="recordings-window" data-testid="recordings-window">
    <div className="recordings-body surface-rail-layout">
      <Rail label="Recordings" data-testid="recordings-rail" picked={shown?.id ?? null}
        paneOpen={paneOpen} onBack={() => setPaneOpen(false)} onPick={(id) => { setPicked(id); setPaneOpen(true); setRefusal(""); }}
        head={<Button dense variant="primary" onClick={() => { setPaneOpen(true); }} data-testid="recordings-capture-open">{live ? "Recording now" : available ? "New recording" : "Storage"}</Button>}
        items={rows.map((row) => { const s = stateOf(row); return { id: row.id, label: whenOf(row),
          facts: [row.duration_s ? lengthWords(row.duration_s) : "", row.state === "ready" ? sizeWords(row.bytes_out) : ""].filter(Boolean).join(" · "),
          state: <span data-tone={s.spine} data-testid="recordings-state">{s.word}</span>, spine: { tone: s.spine },
          rowData: { "data-testid": "recordings-row", "data-recording": row.id } }; })}>
        {data.loading || data.error ? <SurfaceState loading={data.loading} error={data.error} onRetry={() => void data.reload()} />
          : !rows.length ? <SurfaceState empty emptyLabel="No recordings yet" emptyKind="recording" emptyImage={`${SPRITE_BASE}system/48/dock-screen-record.png`} /> : undefined}
      </Rail>
      <article className="recordings-object" data-testid="recordings-document" data-recording={shown?.id} data-state={shown?.state}>
        <Mast kind="recording" glyph={`${SPRITE_BASE}system/dock-screen-record.png`} title={shown ? whenOf(shown) : "Record this desk"}
          facts={shown ? [state?.word, shown.duration_s ? lengthWords(shown.duration_s) : ""].filter(Boolean).join(" · ") : undefined} data-testid="recordings-mast">
          {shown?.note_ref ? <Button dense onClick={() => openRef(shown.note_ref)} data-testid="recordings-open-note">Open note</Button> : null}
          {shown?.state === "ready" ? <Button dense loading={busy === "share"} disabled={Boolean(busy)} data-testid="recordings-share"
            onClick={() => void run("share", async () => { data.apply(await (shown.shared ? unshareRecording(shown.id) : shareRecording(shown.id))); })}>{shown.shared ? "Stop sharing" : "Share"}</Button> : null}
          {shown && ["ready", "failed"].includes(shown.state) ? <ConfirmVerb key={shown.id} label="Remove" confirmLabel="Remove recording?"
            data-testid="recordings-park" busy={busy === "park"} disabled={Boolean(busy)} onConfirm={() => void run("park", async () => {
              const answer = await parkRecording(shown.id);
              if (!answer.parked) throw new Error("The recording was not removed");
              data.drop(shown.id); setPicked((current) => current === shown.id ? null : current); setReceipt("Recording moved to the parked folder");
            })} /> : null}
          {shown?.state === "ready" && shown.shared && shown.links.tailnet ? <CopyLink key={shown.links.tailnet} href={shown.links.tailnet}
            label="Copy phone link" testId="recordings-link-tailnet-copy" /> : null}
          <ShowMe app="open-recordings" />
        </Mast>
        <Spine tone={state?.spine ?? "idle"} />
        <section className="recordings-plate" data-testid="recordings-plate">
          <span className="recordings-caption">{live ? "Recording now" : "Screen and voice"}</span>
          <h3>{live ? (capture.remote ? "Recording on another view" : clock || "Recording") : "Your next recording"}</h3>
          {live ? <Button dense variant="danger" onClick={stopCapture} disabled={capture.phase === "stopping"} data-testid="recordings-stop">Stop</Button>
            : !available ? <DotWord tone="info">Record from your computer</DotWord> : <div className="recordings-capture-verbs"><Button dense variant="primary" loading={capture.phase === "asking"} onClick={pressScreenRecord} data-testid="recordings-record">Record screen</Button>
              <CheckGadget variant="token" label="Voice" checked={capture.voice} onChange={setVoice} /></div>}
        </section>
        {shown?.state === "ready" ? <>
          {shown.shared ? <section className="recordings-links" aria-label="Links" data-testid="recordings-links">
            {shown.links.tailnet ? <ShareUrlRow key={shown.links.tailnet} copy={false} label="On your phone" href={shown.links.tailnet} testId="recordings-link-tailnet" /> : null}
            {shown.links.local ? <ShareUrlRow key={shown.links.local} label="On this Mac" href={shown.links.local} testId="recordings-link-local" /> : null}
          </section> : null}
          <video className="recordings-video" data-testid="recordings-video" src={videoUrl(shown.id)}
            poster={shown.encoder === "mp4" ? posterUrl(shown.id) : undefined} controls playsInline preload="metadata" />
          {shown.encoder === "webm" ? <DotWord tone="warn" data-testid="recordings-webm">Webm · iPhone video needs ffmpeg</DotWord> : null}
        </> : shown ? <section className="recordings-wait" data-testid="recordings-wait">
          <DotWord tone={state?.tone} live={state?.live}>{shown.error || state?.word}</DotWord>
          {shown.state === "failed" && shown.bytes_in > 0 ? <Button dense loading={busy === "retry"} data-testid="recordings-retry"
            onClick={() => void run("retry", async () => { data.apply(await retryRecording(shown.id)); })}>Retry</Button> : null}
        </section> : null}
        <div data-testid="recordings-storage"><Disclosure label="Storage"><RecordingsSettings payload={data.payload} /></Disclosure></div>
      </article>
    </div>
    <StatusBar data-testid="recordings-status" items={[
      notice ? { text: notice, lamp: refusal || capture.error ? "warn" : undefined, testId: "recordings-refusal" } : null,
      rows.length ? { text: countWords(rows.length, "recording") } : null,
      data.payload.usage.bytes ? { text: `${sizeWords(data.payload.usage.bytes)} used` } : null,
    ]} />
  </div>;
}
export default RecordingsCore;
