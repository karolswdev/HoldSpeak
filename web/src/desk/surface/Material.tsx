// HS-101 round 8 — written material (a note's body, an artifact, an
// agent's instructions) presents as a DOCUMENT on the window material,
// never as markdown source in a box. A deliberately small renderer:
// headings, lists, paragraphs, bold/italic/code/links — built as React
// nodes (no innerHTML), unknown syntax falls back to plain text.
import type { ReactNode } from "react";

const INLINE_RE =
  /(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|_[^_\s][^_]*_|`[^`]+`|\[[^\]]+\]\([^)\s]+\))/g;

function inline(text: string): ReactNode[] {
  const out: ReactNode[] = [];
  let last = 0;
  let key = 0;
  for (const m of text.matchAll(INLINE_RE)) {
    const at = m.index ?? 0;
    if (at > last) out.push(text.slice(last, at));
    const tok = m[0];
    if (tok.startsWith("**"))
      out.push(<strong key={key++}>{tok.slice(2, -2)}</strong>);
    else if (tok.startsWith("`"))
      out.push(<code key={key++}>{tok.slice(1, -1)}</code>);
    else if (tok.startsWith("[")) {
      const text_ = tok.slice(1, tok.indexOf("]"));
      const href = tok.slice(tok.indexOf("(") + 1, -1);
      out.push(
        /^https?:\/\//.test(href) ? (
          <a key={key++} href={href} target="_blank" rel="noreferrer">
            {text_}
          </a>
        ) : (
          <strong key={key++}>{text_}</strong>
        ),
      );
    } else out.push(<em key={key++}>{tok.slice(1, -1)}</em>);
    last = at + tok.length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

type Block =
  | { kind: "h"; text: string }
  | { kind: "ul" | "ol"; items: string[] }
  | { kind: "p"; text: string };

function blocks(source: string): Block[] {
  const out: Block[] = [];
  let para: string[] = [];
  const flush = () => {
    if (para.length) out.push({ kind: "p", text: para.join(" ") });
    para = [];
  };
  for (const raw of source.split("\n")) {
    const line = raw.trim();
    if (!line) {
      flush();
      continue;
    }
    const h = line.match(/^#{1,4}\s+(.*)$/);
    if (h) {
      flush();
      out.push({ kind: "h", text: h[1] });
      continue;
    }
    const li = line.match(/^[-*·]\s+(.*)$/);
    const oli = line.match(/^\d+[.)]\s+(.*)$/);
    if (li || oli) {
      flush();
      const kind = li ? "ul" : "ol";
      const prev = out.at(-1);
      if (prev && prev.kind === kind) prev.items.push((li || oli)![1]);
      else out.push({ kind, items: [(li || oli)![1]] });
      continue;
    }
    para.push(line);
  }
  flush();
  return out;
}

export function Material({
  children,
  className,
}: {
  children: string;
  className?: string;
}) {
  const parsed = blocks(children);
  if (!parsed.length) return null;
  return (
    <div
      className={className ? `surface-material ${className}` : "surface-material"}
    >
      {parsed.map((b, i) => {
        if (b.kind === "h")
          return (
            <strong key={i} className="surface-material-h">
              {inline(b.text)}
            </strong>
          );
        if (b.kind === "p") return <p key={i}>{inline(b.text)}</p>;
        const items = b.items.map((item, j) => <li key={j}>{inline(item)}</li>);
        return b.kind === "ul" ? (
          <ul key={i}>{items}</ul>
        ) : (
          <ol key={i}>{items}</ol>
        );
      })}
    </div>
  );
}
