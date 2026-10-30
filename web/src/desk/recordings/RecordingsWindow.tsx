/* Recordings (RECORDINGS-DESIGN-2026-10-28 §2.6; canvas
 * docs/internal/betterment/canvases/recordings-2026-10-28.html): the
 * Recordings window, Go ▸ Work ▸ Recordings (and the dock tile's right
 * button).
 *
 * Window grammar: title bar → Toolbar (Record screen, the primary that makes
 * the object; Stop while one runs; the Voice switch) → the body → a 24 px
 * StatusBar with a dot and a word. Idle, the recordings are a dense list; a
 * press opens one: the video in a well, its two links with Copy, and the
 * row's verbs in the toolbar (Open note, Stop sharing, Park; Retry when the
 * encode failed). A `recording_state` frame replaces the row it names. No
 * host chip on a row (UX-CANON A.9): the links show where he opens them. */
import { useMemo, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import type { CoreProps } from "../../pages/cores/core-types";
import { openRef } from "../openObject";
import { useWindowInterior } from "../surface/interior";
import { CheckGadget } from "../surface/gadgets";
import { DotWord, StatusBar, ToolGlyph, Toolbar, countWords, type StatusBarItem } from "../surface/kit";
import { stateWords } from "../surface/words";
import { ObjectList, type ObjectListRow, type ObjectListSort, type ObjectListTone } from "../surface/objects/ObjectList";
import { SurfaceState } from "../surface/Surface";
import { SPRITE_BASE } from "../sprites";
import { isLive, setVoice, stopCapture, useCapture } from "./capture";
import {
  lengthWords, parkRecording, posterUrl, retryRecording, shareRecording, sizeWords,
  unshareRecording, useRecordings, videoUrl,
} from "./api";
import { pressScreenRecord, useLiveClock } from "./ScreenRecord";
import type { Recording } from "./types";
import "./recordings.css";

/** A recording's state as a dot and a word. */
export function stateOf(row: Recording): { word: string; tone: ObjectListTone; live?: boolean } {
  switch (row.state) {
    case "recording":
      return { word: "Recording", tone: "fail", live: true };
    case "encoding":
      return { word: `Encoding ${Math.max(0, Math.min(99, row.progress || 0))} %`, tone: "info", live: true };
    case "failed":
      return { word: "Failed", tone: "fail" };
    default:
      return row.encoder === "webm" ? { word: "Ready · webm", tone: "warn" } : { word: "Ready", tone: "ok" };
  }
}

/** `Tue 28 Oct 17:40` from the title (`Recording · Tue 28 Oct 17:40`). */
function whenOf(row: Recording): string {
  return row.title.replace(/^Recording · /, "");
}

function copy(text: string): Promise<boolean> {
  try {
    return navigator.clipboard.writeText(text).then(() => true, () => false);
  } catch {
    return Promise.resolve(false);
  }
}

function LinkRow({ label, href, testId }: { label: string; href: string; testId: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <div className="recordings-link" data-testid={testId}>
      <span className="recordings-link-label">{label}</span>
      <a className="recordings-link-url" href={href} target="_blank" rel="noreferrer" title={href}>{href}</a>
      <Button
        variant="secondary"
        dense
        onClick={() => void copy(href).then(setCopied)}
        data-testid={`${testId}-copy`}
      >
        <ToolGlyph kind="copy" />
        {copied ? "Copied" : "Copy"}
      </Button>
    </div>
  );
}

/** One recording as a document: the video, its two links, its facts. */
function RecordingDocument({ row }: { row: Recording }) {
  const ready = row.state === "ready";
  return (
    <div className="recordings-doc" data-testid="recordings-document" data-recording={row.id} data-state={row.state}>
      {ready ? (
        <div className="recordings-well">
          <video
            className="recordings-video"
            data-testid="recordings-video"
            src={videoUrl(row.id)}
            poster={row.encoder === "mp4" ? posterUrl(row.id) : undefined}
            controls
            playsInline
            preload="metadata"
          />
        </div>
      ) : (
        <div className="recordings-well recordings-well-wait" data-testid="recordings-wait">
          <DotWord tone={stateOf(row).tone === "fail" ? "fail" : "info"}>
            {row.state === "failed" ? (row.error || "The encode failed") : stateOf(row).word}
          </DotWord>
          {row.state === "encoding" ? (
            <span className="recordings-meter" aria-hidden="true">
              <span style={{ width: `${Math.max(2, row.progress || 0)}%` }} />
            </span>
          ) : null}
        </div>
      )}
      {ready && row.shared ? (
        <section className="recordings-links" aria-label="Links" data-testid="recordings-links">
          {row.links.tailnet ? <LinkRow label="On your phone" href={row.links.tailnet} testId="recordings-link-tailnet" /> : null}
          {row.links.local ? <LinkRow label="On this Mac" href={row.links.local} testId="recordings-link-local" /> : null}
        </section>
      ) : null}
      {ready && row.encoder === "webm" ? (
        <p className="recordings-fact" data-testid="recordings-webm">
          <DotWord tone="warn">Kept as webm · brew install ffmpeg for an iPhone video</DotWord>
        </p>
      ) : null}
    </div>
  );
}

export function RecordingsCore(_props: CoreProps) {
  const data = useRecordings();
  const capture = useCapture();
  const clock = useLiveClock(capture);
  const [openId, setOpenId] = useState<string | null>(null);
  const [busy, setBusy] = useState("");
  const [refusal, setRefusal] = useState("");
  const [sort, setSort] = useState<ObjectListSort>({ key: "when", dir: "desc" });
  useWindowInterior("list");

  const rows = data.payload.recordings;
  const shown = openId ? rows.find((row) => row.id === openId) ?? null : null;
  const live = isLive(capture);

  const run = async (kind: string, act: () => Promise<void>) => {
    setBusy(kind);
    setRefusal("");
    try { await act(); } catch (error) { setRefusal(error instanceof Error ? error.message : "Request failed"); } finally { setBusy(""); }
  };
  const retry = (row: Recording) => run("retry", async () => { data.apply(await retryRecording(row.id)); });
  const toggleShare = (row: Recording) => run("share", async () => {
    data.apply(await (row.shared ? unshareRecording(row.id) : shareRecording(row.id)));
  });
  const park = (row: Recording) => run("park", async () => {
    await parkRecording(row.id);
    data.drop(row.id);
    setOpenId(null);
  });

  const listRows: ObjectListRow[] = useMemo(() => rows.map((row) => {
    const state = stateOf(row);
    return {
      id: row.id,
      kind: "recording",
      kindWord: "Recording",
      name: whenOf(row),
      sprite: `${SPRITE_BASE}system/dock-screen-record.png`,
      when: whenOf(row),
      whenSort: row.started_ts * 1000,
      state: { label: state.word, tone: state.tone, live: state.live, testId: "recordings-state" },
      cells: {
        length: row.duration_s > 0 ? lengthWords(row.duration_s) : "",
        size: row.state === "ready" ? sizeWords(row.bytes_out) : row.bytes_in ? sizeWords(row.bytes_in) : "",
      },
      sortValues: { length: row.duration_s, size: row.bytes_out || row.bytes_in },
    };
  }), [rows]);

  const usage = data.payload.usage;
  const items: Array<StatusBarItem | null> = refusal ? [
    { key: "refusal", lamp: "warn", text: refusal, testId: "recordings-refusal" },
  ] : capture.error ? [
    { key: "capture", lamp: "warn", text: capture.error, testId: "recordings-capture-error" },
  ] : live ? [
    { key: "live", lamp: "fail", live: true, text: stateWords(capture.remote ? "Recording on another view" : "Recording"), testId: "recordings-status-live" },
    clock ? { key: "clock", text: <span className="recordings-clock">{clock}</span> } : null,
  ] : shown ? [
    { key: "state", lamp: stateOf(shown).tone === "idle" ? undefined : (stateOf(shown).tone as StatusBarItem["lamp"]), text: stateOf(shown).word, testId: "recordings-status-row" },
    shown.duration_s ? { key: "length", text: <b>{lengthWords(shown.duration_s)}</b> } : null,
    shown.state === "ready" ? { key: "size", text: sizeWords(shown.bytes_out) } : null,
  ] : [
    rows.length ? { key: "count", text: countWords(rows.length, "recording") } : null,
    usage.bytes ? { key: "usage", text: `${sizeWords(usage.bytes)} used`, testId: "recordings-usage" } : null,
    data.payload.encoder === "none" ? { key: "ffmpeg", lamp: "warn", text: "No ffmpeg · videos stay webm", testId: "recordings-no-ffmpeg" } : null,
  ];

  let body: ReactNode;
  const phase = data.loading || data.error ? "read" : shown ? `rec-${shown.id}` : rows.length ? "list" : "empty";
  if (data.loading || data.error) {
    body = <SurfaceState loading={data.loading} error={data.error} onRetry={() => void data.reload()} />;
  } else if (shown) {
    body = <RecordingDocument row={shown} />;
  } else if (!rows.length) {
    body = (
      <SurfaceState
        empty
        emptyKind="recording"
        emptyImage={`${SPRITE_BASE}system/48/dock-screen-record.png`}
        emptyLabel="No recordings yet"
        emptyHint="Record screen films this desk; the video plays on your phone."
        actionLabel="Record screen"
        onAction={pressScreenRecord}
      />
    );
  } else {
    body = (
      <div className="recordings-list" data-testid="recordings-list">
        <ObjectList
          label="Recordings"
          density="dense"
          rows={listRows}
          columns={[
            { key: "name", word: "Recorded" },
            { key: "length", word: "Length", track: "72px" },
            { key: "size", word: "Size", track: "80px" },
            { key: "state", word: "State", track: "132px" },
          ]}
          sort={sort}
          onSort={(key: string) => setSort((now) => ({ key, dir: now.key === key && now.dir === "desc" ? "asc" : "desc" }))}
          onOpen={setOpenId}
          rowProps={(row) => ({ "data-testid": "recordings-row", "data-recording": row.id })}
        />
      </div>
    );
  }

  return (
    <div className="recordings-window" data-testid="recordings-window" data-state={live ? "live" : shown ? "recording" : "list"}>
      <Toolbar
        label="Recordings"
        data-testid="recordings-toolbar"
        trailing={shown ? null : (
          <CheckGadget variant="token" label="Voice" checked={capture.voice} onChange={setVoice} />
        )}
        trailingStays
      >
        {live ? (
          <Button variant="danger" dense onClick={stopCapture} disabled={capture.phase === "stopping"} data-testid="recordings-stop">
            <ToolGlyph kind="record" />
            Stop
          </Button>
        ) : !shown ? (
          <Button
            variant="primary"
            dense
            loading={capture.phase === "asking"}
            onClick={pressScreenRecord}
            title="Films this desk (⌃⇧R)"
            data-testid="recordings-record"
          >
            <ToolGlyph kind="record" />
            Record screen
          </Button>
        ) : null}
        {shown ? (
          <>
            <Button variant="secondary" dense onClick={() => setOpenId(null)} data-testid="recordings-back">All recordings</Button>
            {shown.note_ref ? (
              <Button variant="secondary" dense onClick={() => openRef(shown.note_ref)} data-testid="recordings-open-note">
                <ToolGlyph kind="note" />
                Open note
              </Button>
            ) : null}
            {shown.state === "failed" && shown.bytes_in > 0 ? (
              <Button variant="secondary" dense loading={busy === "retry"} onClick={() => void retry(shown)} data-testid="recordings-retry">
                <ToolGlyph kind="retry" />
                Retry
              </Button>
            ) : null}
            {shown.state === "ready" ? (
              <Button variant="secondary" dense loading={busy === "share"} onClick={() => void toggleShare(shown)} data-testid="recordings-share">
                {shown.shared ? "Stop sharing" : "Share"}
              </Button>
            ) : null}
            {shown.state === "ready" || shown.state === "failed" ? (
              <Button variant="secondary" dense loading={busy === "park"} onClick={() => void park(shown)} data-testid="recordings-park">
                Park
              </Button>
            ) : null}
          </>
        ) : null}
      </Toolbar>
      <div className="recordings-body" key={phase} data-phase={phase}>{body}</div>
      <StatusBar data-testid="recordings-status" items={items} />
    </div>
  );
}

export default RecordingsCore;
