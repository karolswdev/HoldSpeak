/* W2-LIVE (2026-10-27; canvas betterment/canvases/live-direction-2026-10-27.html,
 * direction A) — the live transcript as a document, not a counted stream.
 *
 * The hub's `segment` frame is `TranscriptSegment.to_dict()`
 * (holdspeak/meeting_session/models.py: text, speaker, start_time, end_time,
 * is_bookmarked). The old stream read `timestamp`/`start`, keys the wire never
 * sends, so every line had an empty time mark and no speaker. Here a line has
 * its time mark (m:ss from `start_time`) in the margin, the speaker's name
 * heads a run of lines when the speaker changes, a bookmarked line wears the
 * ember mark, and the newest line arrives at the foot. While the window sits
 * at the foot it follows the new lines; scrolled up, it stays where he reads. */
import { useLayoutEffect, useMemo, useRef } from "react";

type Segment = Record<string, unknown>;

/** Seconds since the meeting started → `m:ss` (`h:mm:ss` past the hour). A
 *  preformatted string (an older frame's `timestamp`) passes through. */
export function transcriptMark(segment: Segment): string {
  const raw = segment.start_time ?? segment.start ?? segment.timestamp ?? segment.time;
  if (typeof raw === "string" && raw.trim() && !Number.isFinite(Number(raw))) return raw.trim();
  const secs = typeof raw === "number" ? raw : typeof raw === "string" && raw.trim() ? Number(raw) : NaN;
  if (!Number.isFinite(secs) || secs < 0) return "";
  const whole = Math.floor(secs);
  const h = Math.floor(whole / 3600);
  const m = Math.floor((whole % 3600) / 60);
  const s = String(whole % 60).padStart(2, "0");
  return h ? `${h}:${String(m).padStart(2, "0")}:${s}` : `${m}:${s}`;
}

function scrollParent(node: HTMLElement | null): HTMLElement | null {
  let at = node?.parentElement ?? null;
  while (at) {
    const overflow = getComputedStyle(at).overflowY;
    if ((overflow === "auto" || overflow === "scroll") && at.scrollHeight > at.clientHeight) return at;
    at = at.parentElement;
  }
  return null;
}

export function LiveTranscript({
  segments,
  listening,
}: {
  segments: Segment[];
  listening: boolean;
}) {
  const lines = useMemo(
    () =>
      segments.map((segment, index) => {
        const speaker = String(segment.speaker ?? "").trim();
        const previous = index ? String(segments[index - 1].speaker ?? "").trim() : "";
        return {
          key: String(segment.id ?? segment.segment_id ?? `${segment.start_time ?? ""}-${index}`),
          mark: transcriptMark(segment),
          speaker: speaker && speaker !== previous ? speaker : "",
          text: String(segment.text ?? segment.transcript ?? ""),
          flagged: segment.is_bookmarked === true,
        };
      }),
    [segments],
  );
  const foot = useRef<HTMLDivElement | null>(null);
  const pinned = useRef(true);
  // Before the new line paints: was he at the foot? Then follow it.
  useLayoutEffect(() => {
    const scroller = scrollParent(foot.current);
    if (!scroller) return;
    const onScroll = () => {
      pinned.current = scroller.scrollHeight - scroller.scrollTop - scroller.clientHeight < 48;
    };
    scroller.addEventListener("scroll", onScroll, { passive: true });
    return () => scroller.removeEventListener("scroll", onScroll);
  }, [lines.length > 0]);
  useLayoutEffect(() => {
    if (!pinned.current) return;
    const scroller = scrollParent(foot.current);
    if (scroller) scroller.scrollTop = scroller.scrollHeight;
  }, [lines.length]);

  return (
    <div className="live-doc" role="log" aria-label="Transcript" aria-live="polite" data-testid="live-transcript">
      {lines.map((line) => (
        <div
          key={line.key}
          className="live-doc-line"
          data-flagged={line.flagged || undefined}
          data-testid="live-transcript-line"
        >
          <span className="live-doc-when">{line.mark}</span>
          <div className="live-doc-body">
            {line.speaker ? <div className="live-doc-who">{line.speaker}</div> : null}
            <p className="live-doc-said">{line.text}</p>
          </div>
        </div>
      ))}
      <div className="live-doc-line live-doc-listening" ref={foot}>
        <span className="live-doc-when" />
        {listening ? (
          <span className="live-doc-listen" data-testid="live-listening">
            <span className="live-doc-caret" aria-hidden="true" />
            Listening
          </span>
        ) : null}
      </div>
    </div>
  );
}
