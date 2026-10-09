/** Phase 16 — AgentWords: the ONE renderer of text an agent wrote.
 *
 *  Canvas: docs/internal/philo/phase-16/02-canvas/agent-words.html.
 *
 *  The input is UNTRUSTED. The output is React nodes only: no HTML string
 *  is ever set on the DOM (a tag in the text is shown as text, React
 *  escapes it). The subset: paragraphs and line breaks,
 *  `**bold**`, `*italic*` / `_italic_`, `` `code` ``, fenced code blocks
 *  (a language token when given), numbered and bulleted lists (one level
 *  nested), `# headings` as a bold line, `[text](url)` as the text and then
 *  the URL as plain text (never an anchor: an agent's link is never a press
 *  target), `![alt](src)` as `[alt]`. Long tokens break after `/ _ - .`.
 *
 *  `compact`: for rows, lamps and titles. Inline marks kept, blocks joined
 *  into one line with ` · `; when a paragraph ends with `?` the line is the
 *  last such paragraph (THE ASK, ruling 2026-10-08); cut with `…` at the
 *  surface's width and never
 *  inside a word (`lines` lets a row keep two lines). `agentWordsPlain`
 *  is the same words as plain text, for an attribute (a `title`).
 */
import { useLayoutEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";
import "./agent-words.css";

/* ── the model ────────────────────────────────────────────────────── */

export type Inline =
  | { t: "text"; v: string }
  | { t: "code"; v: string }
  | { t: "url"; v: string }
  | { t: "strong"; c: Inline[] }
  | { t: "em"; c: Inline[] };

export interface ListItem {
  text: string;
  children?: { ordered: boolean; items: string[] };
}

export type Block =
  | { kind: "p"; lines: string[] }
  | { kind: "h"; text: string }
  | { kind: "list"; ordered: boolean; start: number; items: ListItem[] }
  | { kind: "code"; lang: string; text: string };

const FENCE_RE = /^\s*(```+|~~~+)\s*([\w+#.-]*)\s*$/;
const HEADING_RE = /^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$/;
const ITEM_RE = /^(\s*)([-*+•]|(\d{1,4})[.)])\s+(.*)$/;
const RULE_RE = /^\s{0,3}([-*_])(\s*\1){2,}\s*$/;

/** The blocks of an agent's text. */
export function parseAgentWords(source: string): Block[] {
  const out: Block[] = [];
  const lines = String(source ?? "").replace(/\r\n?/g, "\n").split("\n");
  let para: string[] = [];
  const flush = () => {
    if (para.length) out.push({ kind: "p", lines: para });
    para = [];
  };
  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i];
    const fence = raw.match(FENCE_RE);
    if (fence) {
      flush();
      const close = fence[1];
      const body: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith(close)) body.push(lines[i++]);
      out.push({ kind: "code", lang: fence[2] || "", text: body.join("\n") });
      continue;
    }
    if (!raw.trim()) {
      flush();
      continue;
    }
    if (RULE_RE.test(raw)) {
      flush();
      continue;
    }
    const h = raw.match(HEADING_RE);
    if (h) {
      flush();
      out.push({ kind: "h", text: h[1] });
      continue;
    }
    const item = raw.match(ITEM_RE);
    if (item) {
      const nested = item[1].replace(/\t/g, "  ").length >= 2;
      const ordered = item[3] !== undefined;
      const prev = out.at(-1);
      if (nested && !para.length && prev?.kind === "list" && prev.items.length) {
        const parent = prev.items[prev.items.length - 1];
        if (!parent.children) parent.children = { ordered, items: [] };
        parent.children.items.push(item[4]);
        continue;
      }
      flush();
      if (prev?.kind === "list" && prev.ordered === ordered && out.at(-1) === prev) prev.items.push({ text: item[4] });
      else out.push({ kind: "list", ordered, start: ordered ? Number(item[3]) || 1 : 1, items: [{ text: item[4] }] });
      continue;
    }
    // A line under a list item, indented: it goes on with that item.
    const prev = out.at(-1);
    if (!para.length && prev?.kind === "list" && /^\s{2,}\S/.test(raw)) {
      const last = prev.items[prev.items.length - 1];
      if (last.children?.items.length) last.children.items[last.children.items.length - 1] += ` ${raw.trim()}`;
      else last.text += ` ${raw.trim()}`;
      continue;
    }
    para.push(raw.replace(/^\s{0,3}>\s?/, "").trim());
  }
  flush();
  return out;
}

/** The index of the closing `delim` from `from`, skipping code spans. */
function findClose(s: string, from: number, delim: string): number {
  let i = from;
  while (i < s.length) {
    if (s[i] === "\\") {
      i += 2;
      continue;
    }
    if (s[i] === "`") {
      const run = s.slice(i).match(/^`+/)![0];
      const end = s.indexOf(run, i + run.length);
      if (end > 0) {
        i = end + run.length;
        continue;
      }
    }
    if (s.startsWith(delim, i)) {
      // `**` never closes a single `*`, and the reverse.
      if (delim.length === 1 && s[i + 1] === delim) {
        i += 2;
        continue;
      }
      return i;
    }
    i++;
  }
  return -1;
}

const WORD_CHAR = /[A-Za-z0-9]/;

/** The inline marks of one line. */
export function parseInline(s: string): Inline[] {
  const out: Inline[] = [];
  let text = "";
  const push = (node: Inline) => {
    if (text) out.push({ t: "text", v: text });
    text = "";
    out.push(node);
  };
  let i = 0;
  while (i < s.length) {
    const ch = s[i];
    if (ch === "\\" && i + 1 < s.length && /[\\`*_[\]()#!<>~.-]/.test(s[i + 1])) {
      text += s[i + 1];
      i += 2;
      continue;
    }
    if (ch === "`") {
      const run = s.slice(i).match(/^`+/)![0];
      const end = s.indexOf(run, i + run.length);
      if (end > 0) {
        push({ t: "code", v: s.slice(i + run.length, end).trim() || s.slice(i + run.length, end) });
        i = end + run.length;
        continue;
      }
      text += run;
      i += run.length;
      continue;
    }
    if (ch === "!" && s[i + 1] === "[") {
      const m = s.slice(i).match(/^!\[([^\]]*)\]\(([^)\s]*)(?:\s+"[^"]*")?\)/);
      if (m) {
        text += `[${m[1] || "image"}]`;
        i += m[0].length;
        continue;
      }
    }
    if (ch === "[") {
      const m = s.slice(i).match(/^\[([^\]]+)\]\(([^)\s]+)(?:\s+"[^"]*")?\)/);
      if (m) {
        const label = parseInline(m[1]);
        if (m[1].trim() === m[2].trim()) push({ t: "url", v: m[2] });
        else {
          if (text) out.push({ t: "text", v: text });
          text = "";
          out.push(...label, { t: "text", v: " " }, { t: "url", v: m[2] });
        }
        i += m[0].length;
        continue;
      }
    }
    if (ch === "<") {
      const m = s.slice(i).match(/^<((?:https?|mailto):[^>\s]+)>/);
      if (m) {
        push({ t: "url", v: m[1] });
        i += m[0].length;
        continue;
      }
    }
    if ((ch === "*" || ch === "_") && s[i + 1] === ch) {
      const delim = ch + ch;
      const leftOk = ch === "*" || !WORD_CHAR.test(s[i - 1] ?? "");
      const end = leftOk && s[i + 2] && s[i + 2] !== " " ? findClose(s, i + 2, delim) : -1;
      if (end > i + 2 && (ch === "*" || !WORD_CHAR.test(s[end + 2] ?? ""))) {
        push({ t: "strong", c: parseInline(s.slice(i + 2, end)) });
        i = end + 2;
        continue;
      }
      text += delim;
      i += 2;
      continue;
    }
    if (ch === "*" || ch === "_") {
      const leftOk = ch === "*" || !WORD_CHAR.test(s[i - 1] ?? "");
      const end = leftOk && s[i + 1] && s[i + 1] !== " " ? findClose(s, i + 1, ch) : -1;
      if (end > i + 1 && s[end - 1] !== " " && (ch === "*" || !WORD_CHAR.test(s[end + 1] ?? ""))) {
        push({ t: "em", c: parseInline(s.slice(i + 1, end)) });
        i = end + 1;
        continue;
      }
    }
    text += ch;
    i++;
  }
  if (text) out.push({ t: "text", v: text });
  return out;
}

/* ── plain text ───────────────────────────────────────────────────── */

function inlinePlain(nodes: Inline[]): string {
  return nodes.map((n) => ("c" in n ? inlinePlain(n.c) : n.v)).join("");
}

/** The line pieces of the blocks, in order (the compact join). */
function blockLines(blocks: Block[]): string[] {
  const out: string[] = [];
  for (const b of blocks) {
    if (b.kind === "p") out.push(...b.lines.filter(Boolean));
    else if (b.kind === "h") out.push(b.text);
    else if (b.kind === "code") {
      const flat = b.text.split("\n").map((l) => l.trim()).filter(Boolean).join(" ");
      if (flat) out.push(`\`${flat.replace(/`/g, "'")}\``);
    } else
      for (const item of b.items) {
        out.push(item.text);
        for (const child of item.children?.items ?? []) out.push(child);
      }
  }
  return out;
}

/** Cut `text` to at most `max` characters at a whole word, with `…`. */
export function cutAtWord(text: string, max: number): string {
  const flat = text.replace(/\s+/g, " ").trim();
  if (flat.length <= max) return flat;
  // Room for ` …`; the cut falls on the space at or before it.
  let end = Math.max(1, max - 2);
  if (flat[end] !== " ") {
    const space = flat.lastIndexOf(" ", end);
    if (space > 0) end = space;
  }
  const kept = flat.slice(0, end).replace(/[\s·]+$/, "");
  return `${kept} …`;
}

/* ── the ask ──────────────────────────────────────────────────────── */

const ENDS_ASKING = /\?["'`*_)\]\s]*$/;

/** Ruling 2026-10-08 (Muad'Dib, Phase 16): a compact line shows THE ASK.
 *  The last paragraph (or list item, or heading) of the agent's words that
 *  ends with `?`, as its own markdown; null when no part asks. */
export function askOf(text: string): string | null {
  let ask: string | null = null;
  for (const b of parseAgentWords(text)) {
    const parts =
      b.kind === "p" ? [b.lines.join("\n")]
        : b.kind === "h" ? [b.text]
          : b.kind === "list" ? b.items.flatMap((i) => [i.text, ...(i.children?.items ?? [])])
            : [];
    for (const part of parts) if (ENDS_ASKING.test(part.trim())) ask = part;
  }
  return ask;
}

/** The words a compact line or an attribute shows: the ask, else all. */
function compactSource(text: string, ask: boolean): string {
  return (ask && askOf(text)) || text;
}

/** The agent's words as plain text, marks removed, blocks joined with
 *  ` · `, cut at a whole word: for an attribute (a `title`). The ask
 *  leads: with a paragraph that ends with `?`, that paragraph alone. */
export function agentWordsPlain(text: string, max = 400, ask = true): string {
  const lines = blockLines(parseAgentWords(compactSource(text, ask))).map((l) => inlinePlain(parseInline(l)).trim()).filter(Boolean);
  return cutAtWord(lines.join(" · "), max);
}

/* ── long tokens ──────────────────────────────────────────────────── */

const LONG_TOKEN = 16;

/** A text with a break chance after `/ _ - .` inside a long token. */
function breakable(text: string, key: string): ReactNode {
  if (text.length <= LONG_TOKEN) return text;
  const parts = text.split(/(\s+)/);
  if (!parts.some((p) => p.length > LONG_TOKEN)) return text;
  const out: ReactNode[] = [];
  let n = 0;
  for (const part of parts) {
    if (part.length <= LONG_TOKEN || /^\s+$/.test(part)) {
      out.push(part);
      continue;
    }
    const bits = part.split(/(?<=[/_\-.])(?=.)/);
    bits.forEach((bit, i) => {
      out.push(bit);
      if (i < bits.length - 1) out.push(<wbr key={`${key}-w${n++}`} />);
    });
  }
  return out;
}

/* ── the full render ──────────────────────────────────────────────── */

function renderInline(nodes: Inline[], key: string): ReactNode[] {
  return nodes.map((n, i) => {
    const k = `${key}.${i}`;
    switch (n.t) {
      case "text":
        return <span key={k}>{breakable(n.v, k)}</span>;
      case "code":
        return <code key={k}>{breakable(n.v, k)}</code>;
      case "url":
        return (
          <span key={k} className="aw-url">
            {breakable(n.v, k)}
          </span>
        );
      case "strong":
        return <strong key={k}>{renderInline(n.c, k)}</strong>;
      case "em":
        return <em key={k}>{renderInline(n.c, k)}</em>;
    }
  });
}

function renderLine(text: string, key: string): ReactNode[] {
  return renderInline(parseInline(text), key);
}

function renderBlock(b: Block, i: number): ReactNode {
  const k = `b${i}`;
  if (b.kind === "h") {
    return (
      <strong key={k} className="aw-h">
        {renderLine(b.text, k)}
      </strong>
    );
  }
  if (b.kind === "code") {
    return (
      <pre key={k} className="aw-pre">
        {b.lang ? <span className="aw-lang">{b.lang.toUpperCase()}</span> : null}
        <code>{b.text}</code>
      </pre>
    );
  }
  if (b.kind === "list") {
    const items = b.items.map((item, j) => (
      <li key={j}>
        {renderLine(item.text, `${k}.${j}`)}
        {item.children ? (
          item.children.ordered ? (
            <ol>{item.children.items.map((c, m) => <li key={m}>{renderLine(c, `${k}.${j}.${m}`)}</li>)}</ol>
          ) : (
            <ul>{item.children.items.map((c, m) => <li key={m}>{renderLine(c, `${k}.${j}.${m}`)}</li>)}</ul>
          )
        ) : null}
      </li>
    ));
    return b.ordered ? (
      <ol key={k} start={b.start !== 1 ? b.start : undefined}>
        {items}
      </ol>
    ) : (
      <ul key={k}>{items}</ul>
    );
  }
  return (
    <p key={k}>
      {b.lines.map((line, j) => (
        <span key={j}>
          {j ? <br /> : null}
          {renderLine(line, `${k}.${j}`)}
        </span>
      ))}
    </p>
  );
}

/* ── the compact render ───────────────────────────────────────────── */

type Mark = "strong" | "em" | "code" | "url" | "sep";

/** One word of the compact line: its pieces with their marks; the space
 *  after it is part of the word. */
export type Word = Array<{ v: string; marks: Mark[] }>;

function runs(nodes: Inline[], marks: Mark[], out: Array<{ v: string; marks: Mark[] }>) {
  for (const n of nodes) {
    if (n.t === "strong" || n.t === "em") runs(n.c, [...marks, n.t], out);
    else if (n.t === "text") out.push({ v: n.v, marks });
    else out.push({ v: n.v, marks: [...marks, n.t] });
  }
}

/** The compact words of the text: every block on one line, ` · ` between. */
export function compactWords(text: string, maxChars = 600, ask = true): { words: Word[]; cut: boolean } {
  const lines = blockLines(parseAgentWords(compactSource(text, ask)));
  const all: Array<{ v: string; marks: Mark[] }> = [];
  lines.forEach((line, i) => {
    if (i) all.push({ v: " · ", marks: ["sep"] });
    runs(parseInline(line.trim()), [], all);
  });
  const words: Word[] = [];
  let current: Word = [];
  let chars = 0;
  let cut = false;
  for (const run of all) {
    for (const bit of run.v.replace(/\s+/g, " ").split(/(?<= )/)) {
      if (!bit) continue;
      if (bit === " " && !current.length) {
        const last = words.at(-1);
        if (last) last[last.length - 1].v += " ";
        continue;
      }
      current.push({ v: bit, marks: run.marks });
      if (bit.endsWith(" ")) {
        words.push(current);
        chars += current.reduce((n, p) => n + p.v.length, 0);
        current = [];
        if (chars > maxChars) {
          cut = true;
          break;
        }
      }
    }
    if (cut) break;
  }
  if (!cut && current.length) words.push(current);
  return { words: trimEnd(words), cut };
}

/** A cut line never ends on the ` · ` mark or a bare space. */
function trimEnd(words: Word[]): Word[] {
  const out = [...words];
  while (out.length && out[out.length - 1].every((p) => p.marks.includes("sep") || !p.v.trim())) out.pop();
  return out;
}

/** A long token (a branch, an id) is many parts in a compact line: each
 *  part after `/ _ - .` is its own unit, so the cut can keep
 *  `hs/project_item-` and drop the rest; the cut never falls inside a part.
 *  A unit with no space after it carries a break chance (`wbr`). */
export function compactUnits(words: Word[]): Array<{ word: Word; joined: boolean }> {
  const out: Array<{ word: Word; joined: boolean }> = [];
  for (const word of words) {
    const length = word.reduce((n, p) => n + p.v.trim().length, 0);
    if (length <= LONG_TOKEN) {
      out.push({ word, joined: false });
      continue;
    }
    const parts: Word = [];
    for (const piece of word) {
      for (const bit of piece.v.split(/(?<=[/_\-.])(?=[^\s])/)) {
        // A bare space stays with the part before it.
        if (!bit.trim() && parts.length) parts[parts.length - 1] = { ...parts[parts.length - 1], v: parts[parts.length - 1].v + bit };
        else parts.push({ v: bit, marks: piece.marks });
      }
    }
    parts.forEach((part, i) => out.push({ word: [part], joined: i < parts.length - 1 && !part.v.endsWith(" ") }));
  }
  return out;
}

/** How many words fit in the box with room for the `…` after the last:
 *  null when all fit. A pure read of the word boxes (the fence tests it). */
export function fitCount(
  words: ReadonlyArray<{ right: number; bottom: number }>,
  box: { right: number; bottom: number },
  ellipsis: number,
): number | null {
  const fits = (w: { right: number; bottom: number }) => w.bottom <= box.bottom + 0.5 && w.right <= box.right + 0.5;
  const first = words.findIndex((w) => !fits(w));
  if (first < 0) return null;
  let n = first;
  while (n > 0 && words[n - 1].right + ellipsis > box.right + 0.5) n--;
  return Math.max(1, n);
}

function wrapMarks(v: ReactNode, marks: Mark[], key: string): ReactNode {
  let node = v;
  for (const m of [...marks].reverse()) {
    if (m === "strong") node = <strong key={key}>{node}</strong>;
    else if (m === "em") node = <em key={key}>{node}</em>;
    else if (m === "code") node = <code key={key}>{node}</code>;
    else if (m === "url") node = <span key={key} className="aw-url">{node}</span>;
    else if (m === "sep") node = <span key={key} className="aw-sep">{node}</span>;
  }
  return node;
}

function CompactWords({ text, lines, ask, className, testId }: { text: string; lines: number; ask: boolean; className?: string; testId?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const [limit, setLimit] = useState<number | null>(null);
  const { words, cut } = compactWords(text, 600, ask);

  useLayoutEffect(() => {
    if (limit !== null) return;
    const el = ref.current;
    if (!el || !el.clientWidth) return; // no layout (a test DOM): no cut
    const box = el.getBoundingClientRect();
    const right = box.left + el.clientWidth;
    const bottom = box.top + el.clientHeight;
    const spans = Array.from(el.querySelectorAll<HTMLElement>("[data-aw-w]"));
    const rects = spans.map((s) => {
      const all = s.getClientRects();
      const r = all[all.length - 1] ?? s.getBoundingClientRect();
      return { right: r.right, bottom: r.bottom };
    });
    const probe = document.createElement("span");
    probe.textContent = " …";
    el.appendChild(probe);
    const ell = probe.getBoundingClientRect().width;
    el.removeChild(probe);
    const n = fitCount(rects, { right, bottom }, ell);
    if (n !== null) setLimit(n);
  });

  // A new width measures again (the window was resized).
  const seen = useRef(0);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(() => {
      const w = el.clientWidth;
      if (seen.current && seen.current !== w) setLimit(null);
      seen.current = w;
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const units = compactUnits(words);
  const kept = limit === null ? units : units.slice(0, limit);
  // A cut line never ends on the ` · ` mark or a bare space.
  while (limit !== null && kept.length && kept[kept.length - 1].word.every((p) => p.marks.includes("sep") || !p.v.trim())) kept.pop();
  const shown = kept.map((u) => u.word);
  const ended = cut || limit !== null;
  if (ended && shown.length) {
    // The last word shown loses its trailing space before the `…`.
    const last = shown[shown.length - 1];
    shown[shown.length - 1] = [...last.slice(0, -1), { ...last[last.length - 1], v: last[last.length - 1].v.trimEnd() }];
  }
  return (
    <span
      ref={ref}
      className={`agent-words is-compact${className ? ` ${className}` : ""}`}
      data-lines={lines > 1 ? String(lines) : undefined}
      style={lines > 1 ? ({ "--aw-lines": lines } as CSSProperties) : undefined}
      title={agentWordsPlain(text, 400, false)}
      data-testid={testId}
    >
      {shown.map((word, i) => (
        <span key={i} data-aw-w="">
          {word.map((piece, j) => wrapMarks(piece.v, piece.marks, `${i}.${j}`))}
          {/* Chromium breaks at <wbr> even in nowrap: one line has none. */}
          {kept[i].joined && lines > 1 ? <wbr /> : null}
        </span>
      ))}
      {ended ? <span className="aw-ell">{shown.length ? " …" : "…"}</span> : null}
    </span>
  );
}

/* ── the component ────────────────────────────────────────────────── */

export interface AgentWordsProps {
  /** The agent's text, as it wrote it (untrusted). */
  text: string;
  /** One line (or `lines`) for rows, lamps and titles. */
  compact?: boolean;
  /** Compact only: the lines the row keeps (default 1). */
  lines?: number;
  /** Compact only: show the ask (the last paragraph that ends with `?`)
   *  when there is one (default). False for words that are not an agent's
   *  turn (the SENT line: what was typed into the agent). */
  ask?: boolean;
  className?: string;
  "data-testid"?: string;
}

export function AgentWords({ text, compact, lines = 1, ask = true, className, "data-testid": testId }: AgentWordsProps) {
  const source = String(text ?? "");
  if (!source.trim()) return null;
  if (compact) return <CompactWords key={source} text={source} lines={lines} ask={ask} className={className} testId={testId} />;
  const blocks = parseAgentWords(source);
  return (
    <div className={`agent-words${className ? ` ${className}` : ""}`} data-testid={testId}>
      {blocks.map(renderBlock)}
    </div>
  );
}
