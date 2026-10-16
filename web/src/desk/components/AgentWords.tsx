/** Phase 16 — AgentWords: the ONE renderer of text an agent wrote.
 *
 *  Canvas: docs/internal/philo/phase-16/02-canvas/agent-words.html.
 *
 *  Full reading shares Material's installed Markdown grammar and React-only
 *  renderer: semantic headings, nested lists, tables, code and explicit links.
 *  HTML stays text; images never fetch. Compact rows have no press targets.
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
import { ReadingDocument, parseReading, readingChildren, readingContent, readingSegments } from "../surface/ReadingDocument";
import type { SyntaxNode } from "@lezer/common";

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

/** Compact adapters use the same installed Markdown grammar as full reading. */
export function parseAgentWords(source: string): Block[] {
  const text = String(source ?? "").replace(/\r\n?/g, "\n");
  const out: Block[] = [];
  const visit = (node: SyntaxNode) => {
    if (node.name === "Paragraph") out.push({ kind: "p", lines: text.slice(node.from, node.to).split("\n") });
    else if (/^(ATX|Setext)Heading[1-6]$/.test(node.name)) out.push({ kind: "h", text: readingContent(node, text) });
    else if (node.name === "FencedCode" || node.name === "CodeBlock") {
      const code = readingChildren(node).filter((child) => child.name === "CodeText");
      const info = node.getChild("CodeInfo");
      out.push({ kind: "code", lang: info ? text.slice(info.from, info.to) : "", text: code.length ? text.slice(code[0].from, code.at(-1)!.to) : "" });
    } else if (node.name === "BulletList" || node.name === "OrderedList") {
      const items: ListItem[] = [];
      for (const item of readingChildren(node).filter((child) => child.name === "ListItem")) {
        const parts = readingChildren(item).filter((child) => child.name === "Paragraph" || child.name === "Task");
        const entry: ListItem = { text: parts.map((part) => text.slice(part.from, part.to)).join("\n") };
        const nested: string[] = [];
        const gather = (child: SyntaxNode) => {
          if (child.name === "Paragraph" || child.name === "Task") nested.push(text.slice(child.from, child.to));
          else readingChildren(child).forEach(gather);
        };
        readingChildren(item).filter((child) => child.name === "BulletList" || child.name === "OrderedList").forEach(gather);
        if (nested.length) entry.children = { ordered: false, items: nested };
        items.push(entry);
      }
      out.push({ kind: "list", ordered: node.name === "OrderedList", start: Number(text.slice(node.from, node.to).match(/^\d+/)?.[0] ?? 1), items });
    } else if (node.name === "TableCell") out.push({ kind: "p", lines: [text.slice(node.from, node.to)] });
    else if (node.name !== "HorizontalRule") readingChildren(node).forEach(visit);
  };
  visit(parseReading(text));
  return out;
}

/** Compact marks keep plain link destinations and no press targets. */
export function parseInline(source: string): Inline[] {
  // A flattened task marker stays text when its body is parsed outside a list.
  if (/^\[[ xX]\](?=[ \t])/.test(source)) source = `\\${source}`;
  const content = parseReading(source).firstChild;
  if (!content) return [];
  const convert = (node: SyntaxNode): Inline[] => {
    if (node.name === "InlineCode") return [{ t: "code", v: readingContent(node, source) }];
    if (node.name === "Escape") return [{ t: "text", v: source.slice(node.from + 1, node.to) }];
    if (node.name === "Autolink") return [{ t: "url", v: source.slice(node.from + 1, node.to - 1) }];
    if (node.name === "Image") return [{ t: "text", v: `[${readingContent(node, source) || "image"}]` }];
    const parts = readingSegments(node, source).flatMap((part): Inline[] => typeof part === "string" ? [{ t: "text", v: part }] : convert(part));
    if (node.name === "StrongEmphasis" || node.name === "Emphasis") return [{ t: node.name === "StrongEmphasis" ? "strong" : "em", c: parts }];
    if (node.name === "Link") {
      const url = node.getChild("URL");
      const href = url ? source.slice(url.from, url.to) : "";
      if (inlinePlain(parts) === href) return [{ t: "url", v: href }];
      return href ? [...parts, { t: "text", v: " " }, { t: "url", v: href }] : parts;
    }
    if (!node.firstChild) return [{ t: "text", v: source.slice(node.from, node.to) }];
    return parts;
  };
  return convert(content);
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
    else {
      // One token with no space (Astra r1 on #1026): cut after / _ - . when
      // the token has one; else at the limit itself.
      const head = flat.slice(0, end);
      const mark = Math.max(head.lastIndexOf("/"), head.lastIndexOf("_"), head.lastIndexOf("-"), head.lastIndexOf("."));
      if (mark > 0) end = mark + 1;
    }
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

/* ── the compact render ───────────────────────────────────────────── */

type Mark = "strong" | "em" | "code" | "url" | "sep";
const LONG_TOKEN = 16;

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
  // 0: not even the first unit fits; the caller cuts that token at the width.
  return n;
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
  const [, setTick] = useState(0);
  const { words, cut } = compactWords(text, 600, ask);

  useLayoutEffect(() => {
    if (limit !== null) return;
    const el = ref.current;
    if (!el || !el.clientWidth) return; // no layout (a test DOM): no cut
    const box = el.getBoundingClientRect();
    const right = box.left + el.clientWidth;
    const bottom = box.top + el.clientHeight;
    const spans = Array.from(el.querySelectorAll<HTMLElement>("[data-aw-w]"));
    // A unit fits only when ALL its boxes do: an overflowing token's wide box
    // is not its last one (Astra r1 on #1026), so read the farthest edges.
    const rects = spans.map((s) => {
      const all = Array.from(s.getClientRects());
      const list = all.length ? all : [s.getBoundingClientRect()];
      return { right: Math.max(...list.map((r) => r.right)), bottom: Math.max(...list.map((r) => r.bottom)) };
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
      // Any new width measures again, also the first one after a mount with
      // no width (a drawer that opens): the tick re-renders even when the
      // limit is already null (Astra r1 on #1026).
      if (seen.current !== w) {
        seen.current = w;
        setLimit(null);
        setTick((t) => t + 1);
      }
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
      {limit === 0 && units.length ? (
        // Not even one unit fits (one unbreakable token wider than the box):
        // the token itself is cut at the width, its ellipsis drawn in the
        // line (Astra r1 on #1026).
        <span className="aw-clip" data-aw-w="">
          {units[0].word.map((piece, j) => wrapMarks(piece.v, piece.marks, `c.${j}`))}
        </span>
      ) : (
        <>
          {shown.map((word, i) => (
            <span key={i} data-aw-w="">
              {word.map((piece, j) => wrapMarks(piece.v, piece.marks, `${i}.${j}`))}
              {/* Chromium breaks at <wbr> even in nowrap: one line has none. */}
              {kept[i].joined && lines > 1 ? <wbr /> : null}
            </span>
          ))}
          {ended ? <span className="aw-ell">{shown.length ? " …" : "…"}</span> : null}
        </>
      )}
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
  return <ReadingDocument className={`agent-words${className ? ` ${className}` : ""}`} data-testid={testId}>{source}</ReadingDocument>;
}
