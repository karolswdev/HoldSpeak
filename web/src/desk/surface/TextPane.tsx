/* TextPane (PG-LANG §9.1, §11): the kit's second text well after PadGadget,
 * a line editor with a gutter of line lamps.
 *
 * One row per line: the gutter (the line number, the line lamp: a `kit-dot`
 * in the tone of the thing the line belongs to, the change mark `~ + − !`),
 * the line, and its lamp words at the line end. A lamp is the run, not the
 * text: it is never in the line's value and never edited. A read-only line
 * (a lamp line, a `?` question) is drawn and not edited; every other line is
 * a one-line textarea that wraps (so the pane scrolls vertically only).
 *
 * Words: keywords (a token list) in ink, ids (`R3`, `R+`) in the kind tint,
 * a `>` line in the body face (his words read as words), the rest mono.
 * The colours are a painted copy of the line under a transparent textarea
 * (one font per line, so the copy and the textarea wrap the same way).
 *
 * Keys: Return splits the line (the indent and a `> ` carry over),
 * Backspace at the start joins it to the line above, Delete at the end
 * joins the next, ↑ / ↓ go to the next line that can be edited, and a paste
 * of several lines makes several lines. The mic (the voice law) puts the
 * spoken words at the caret of the last line he was in. */
import { useLayoutEffect, useRef, type ClipboardEvent, type KeyboardEvent, type ReactNode } from "react";
import { MicButton } from "./controls/MicButton";
import type { ObjectTone } from "./objects/kinds";
import "./text-pane.css";

/** A line's change mark: changed, added, removed above it, refused. */
export type TextPaneMark = "~" | "+" | "-" | "!";

export type TextPaneLine = {
  /** The line as he edits it (no lamp). */
  text: string;
  /** The run's words at the line end (`Merged #1585 · 41 min`): drawn, never edited. */
  lamp?: string;
  /** The gutter lamp's tone; none draws no dot. */
  tone?: ObjectTone | "idle";
  /** Drawn, not edited (a lamp line, a `?` question). */
  readOnly?: boolean;
  /** The change mark in the gutter. */
  mark?: TextPaneMark;
  /** The hover title of the line (a refusal's reason). */
  title?: string;
};

const MARK_WORDS: Record<TextPaneMark, string> = { "~": "Changed", "+": "Added", "-": "Removed above", "!": "Refused" };
const MARK_GLYPH: Record<TextPaneMark, string> = { "~": "~", "+": "+", "-": "−", "!": "!" };

/** Words lines (`> …`) in the body face. */
export function isWordsLine(text: string): boolean {
  return /^\s*>( |$)/.test(text);
}

const ID = /(R\d+|R\+)(?=[\s:]|$)/g;

function paintIds(text: string, key: string): ReactNode[] {
  const out: ReactNode[] = [];
  let at = 0;
  for (const match of text.matchAll(ID)) {
    const start = match.index ?? 0;
    if (start > 0 && /\w/.test(text[start - 1])) continue;
    if (start > at) out.push(text.slice(at, start));
    out.push(<span key={`${key}-id-${start}`} className="kit-textpane-id">{match[0]}</span>);
    at = start + match[0].length;
  }
  if (at < text.length) out.push(text.slice(at));
  return out;
}

/** The painted copy of one line: the same characters, in spans. */
export function paintLine(text: string, keywords: readonly string[]): ReactNode[] {
  const indent = /^\s*/.exec(text)?.[0] ?? "";
  if (isWordsLine(text)) {
    const marker = /^\s*>\s?/.exec(text)?.[0] ?? indent;
    return [marker ? <span key="m" className="kit-textpane-quote">{marker}</span> : null, text.slice(marker.length)];
  }
  // A keyword starts the line (after the indent) or a `·` part of it.
  const starts = [indent.length];
  for (const match of text.matchAll(/· /g)) starts.push((match.index ?? 0) + 2);
  const sorted = [...keywords].sort((a, b) => b.length - a.length);
  const spans: { from: number; to: number }[] = [];
  for (const start of starts) {
    const hit = sorted.find((word) => text.startsWith(word, start) && /^($|[\s:])/.test(text.slice(start + word.length, start + word.length + 1)));
    if (hit) spans.push({ from: start, to: start + hit.length });
  }
  if (text.startsWith("+ ", indent.length)) spans.unshift({ from: indent.length, to: indent.length + 1 });
  const out: ReactNode[] = [];
  let at = 0;
  for (const span of spans.sort((a, b) => a.from - b.from)) {
    if (span.from < at) continue;
    out.push(...paintIds(text.slice(at, span.from), `t${at}`));
    out.push(<span key={`k${span.from}`} className="kit-textpane-keyword">{text.slice(span.from, span.to)}</span>);
    at = span.to;
  }
  out.push(...paintIds(text.slice(at), `t${at}`));
  return out;
}

/** The gutter marks of `now` against `base` (a line diff): `~` for a
 *  changed line, `+` for an added one, `-` on the line under a removal. */
export function lineMarks(base: readonly string[], now: readonly string[]): (TextPaneMark | undefined)[] {
  const n = base.length;
  const m = now.length;
  if (n * m > 4_000_000) return now.map((line, index) => (line === base[index] ? undefined : "~"));
  // The longest common subsequence, from the end.
  const width = m + 1;
  const table = new Uint16Array((n + 1) * width);
  for (let i = n - 1; i >= 0; i -= 1) {
    for (let j = m - 1; j >= 0; j -= 1) {
      table[i * width + j] = base[i] === now[j]
        ? table[(i + 1) * width + j + 1] + 1
        : Math.max(table[(i + 1) * width + j], table[i * width + j + 1]);
    }
  }
  const marks: (TextPaneMark | undefined)[] = new Array(m).fill(undefined);
  let i = 0;
  let j = 0;
  let removed = 0;
  let added: number[] = [];
  const flush = () => {
    // A removal and an addition side by side are a change.
    added.forEach((index, k) => { marks[index] = k < removed ? "~" : "+"; });
    if (removed > added.length && j < m && !marks[j]) marks[j] = "-";
    removed = 0;
    added = [];
  };
  while (i < n || j < m) {
    if (i < n && j < m && base[i] === now[j]) {
      flush();
      i += 1;
      j += 1;
    } else if (j < m && (i >= n || table[i * width + j + 1] >= table[(i + 1) * width + j])) {
      added.push(j);
      j += 1;
    } else {
      removed += 1;
      i += 1;
    }
  }
  flush();
  return marks;
}

export function TextPane({
  label,
  lines,
  onChange,
  keywords = [],
  scrollTo,
  disabled,
  className,
  "data-testid": testId,
}: {
  /** The pane's accessible name (`Program text`); each line is `<label>, line n`. */
  label: string;
  lines: readonly TextPaneLine[];
  /** The lines after an edit; a split or a join carries each line's lamp with it. */
  onChange(next: TextPaneLine[]): void;
  /** The words drawn in ink at the start of a line or of a `·` part. */
  keywords?: readonly string[];
  /** Scroll this line (0-based) into view when it changes. */
  scrollTo?: number | null;
  disabled?: boolean;
  className?: string;
  "data-testid"?: string;
}) {
  const inputs = useRef<(HTMLTextAreaElement | null)[]>([]);
  const rows = useRef<(HTMLDivElement | null)[]>([]);
  const pending = useRef<{ index: number; caret: number } | null>(null);
  const last = useRef<{ index: number; caret: number } | null>(null);
  // A capture can finish after an edit: the mic writes into the newest lines.
  const latest = useRef({ lines, onChange });
  latest.current = { lines, onChange };

  useLayoutEffect(() => {
    const want = pending.current;
    if (!want) return;
    pending.current = null;
    const input = inputs.current[want.index];
    if (!input) return;
    input.focus();
    input.setSelectionRange(want.caret, want.caret);
  });
  useLayoutEffect(() => {
    if (scrollTo == null) return;
    rows.current[scrollTo]?.scrollIntoView?.({ block: "nearest" });
  }, [scrollTo]);

  const editable = (index: number) => index >= 0 && index < lines.length && !lines[index].readOnly;
  const nearest = (from: number, step: 1 | -1) => {
    for (let index = from + step; index >= 0 && index < lines.length; index += step) if (editable(index)) return index;
    return -1;
  };
  const write = (next: TextPaneLine[], focus?: { index: number; caret: number }) => {
    if (focus) pending.current = focus;
    onChange(next);
  };
  const setText = (index: number, text: string) => {
    const next = [...lines];
    next[index] = { ...next[index], text };
    write(next);
  };
  const insertLines = (index: number, caretFrom: number, caretTo: number, pasted: string[]) => {
    const line = lines[index];
    const before = line.text.slice(0, caretFrom);
    const after = line.text.slice(caretTo);
    const made = pasted.map((text) => ({ text }));
    made[0] = { ...line, text: before + pasted[0] };
    const end = made.length - 1;
    const caret = made[end].text.length;
    made[end] = { ...made[end], text: made[end].text + after };
    write([...lines.slice(0, index), ...made, ...lines.slice(index + 1)], { index: index + end, caret });
  };

  const onKeyDown = (index: number, event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.nativeEvent.isComposing) return;
    const input = event.currentTarget;
    const from = input.selectionStart ?? 0;
    const to = input.selectionEnd ?? from;
    const text = lines[index].text;
    if (event.key === "Enter" && !event.shiftKey && !event.metaKey && !event.ctrlKey && !event.altKey) {
      event.preventDefault();
      // The indent carries over, and a line of his words goes on as words.
      const carry = /^\s*(> )?/.exec(text)?.[0] ?? "";
      const keep = from >= carry.length ? carry : /^\s*/.exec(text)?.[0] ?? "";
      insertLines(index, from, to, ["", keep]);
      return;
    }
    if (event.key === "Backspace" && from === 0 && to === 0 && editable(index - 1)) {
      event.preventDefault();
      const above = lines[index - 1];
      const next = [...lines];
      next.splice(index - 1, 2, { ...above, text: above.text + text });
      write(next, { index: index - 1, caret: above.text.length });
      return;
    }
    if (event.key === "Delete" && from === text.length && to === text.length && editable(index + 1)) {
      event.preventDefault();
      const next = [...lines];
      next.splice(index, 2, { ...lines[index], text: text + lines[index + 1].text });
      write(next, { index, caret: from });
      return;
    }
    if ((event.key === "ArrowUp" || event.key === "ArrowDown") && !event.shiftKey && !event.altKey && !event.metaKey && !event.ctrlKey) {
      const target = nearest(index, event.key === "ArrowUp" ? -1 : 1);
      if (target < 0) return;
      event.preventDefault();
      const input2 = inputs.current[target];
      if (!input2) return;
      const caret = Math.min(from, lines[target].text.length);
      input2.focus();
      input2.setSelectionRange(caret, caret);
    }
  };
  const onPaste = (index: number, event: ClipboardEvent<HTMLTextAreaElement>) => {
    const pasted = event.clipboardData?.getData("text/plain") ?? "";
    if (!pasted.includes("\n")) return;
    event.preventDefault();
    const input = event.currentTarget;
    insertLines(index, input.selectionStart ?? 0, input.selectionEnd ?? 0, pasted.replace(/\r\n?/g, "\n").split("\n"));
  };

  return (
    <div className={className ? `kit-textpane ${className}` : "kit-textpane"} role="group" aria-label={label}
      data-disabled={disabled ? "" : undefined} data-testid={testId}>
      <span className="kit-textpane-mic">
        <MicButton
          label={`Speak into ${label.toLowerCase()}`}
          disabled={disabled}
          onText={(spoken) => {
            const { lines: now, onChange: change } = latest.current;
            const at = last.current && now[last.current.index] && !now[last.current.index].readOnly ? last.current : null;
            if (!at) {
              change([...now, { text: spoken }]);
              return;
            }
            const text = now[at.index].text;
            const head = text.slice(0, at.caret);
            const glue = head && !/\s$/.test(head) ? " " : "";
            const next = [...now];
            next[at.index] = { ...next[at.index], text: head + glue + spoken + text.slice(at.caret) };
            last.current = { index: at.index, caret: at.caret + glue.length + spoken.length };
            change(next);
          }}
        />
      </span>
      {lines.map((line, index) => {
        const words = isWordsLine(line.text);
        return (
          <div key={index} ref={(element) => { rows.current[index] = element; }} className="kit-textpane-row"
            data-mark={line.mark} data-readonly={line.readOnly ? "" : undefined} data-words={words ? "" : undefined}
            title={line.title} data-testid="kit-textpane-line" data-line={index + 1}>
            <span className="kit-textpane-gutter" aria-hidden="true">
              <span className="kit-textpane-n">{index + 1}</span>
              <span className="kit-textpane-lampdot">{line.tone ? <span className="kit-dot" data-tone={line.tone} /> : null}</span>
              <span className="kit-textpane-mark" title={line.mark ? MARK_WORDS[line.mark] : undefined}>{line.mark ? MARK_GLYPH[line.mark] : ""}</span>
            </span>
            <span className="kit-textpane-cell">
              <span className="kit-textpane-paint" aria-hidden={line.readOnly ? undefined : true}
                data-entry-copy={line.readOnly ? undefined : ""}>
                {paintLine(line.text, keywords)}{"​"}
              </span>
              {line.readOnly ? null : (
                <textarea
                  ref={(element) => { inputs.current[index] = element; }}
                  className="kit-textpane-input"
                  aria-label={`${label}, line ${index + 1}`}
                  rows={1}
                  spellCheck={words}
                  value={line.text}
                  disabled={disabled}
                  onChange={(event) => setText(index, event.target.value.replace(/\r?\n/g, " "))}
                  onKeyDown={(event) => onKeyDown(index, event)}
                  onPaste={(event) => onPaste(index, event)}
                  onSelect={(event) => { last.current = { index, caret: event.currentTarget.selectionStart }; }}
                  onFocus={(event) => { last.current = { index, caret: event.currentTarget.selectionStart }; }}
                />
              )}
            </span>
            {line.lamp ? (
              <span className="kit-textpane-lamp" title={line.lamp} data-tone={line.tone}>{line.lamp}</span>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
