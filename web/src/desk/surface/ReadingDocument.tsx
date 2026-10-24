/** Shared Markdown reading species. Lezer owns the grammar; React owns the DOM.
 * HTML stays text and images stay alt text. No content is fetched on render. */
import { createElement, useMemo, useRef, type ReactNode } from "react";
import { markdownLanguage } from "@codemirror/lang-markdown";
import type { SyntaxNode } from "@lezer/common";
import { Button } from "../../components/signal/Signal";
import { refOpener } from "../openObject";
import { ScrollHint } from "./Surface";
import { FoldGadget } from "./gadgets";
import "./reading-document.css";

export function parseReading(source: string): SyntaxNode {
  return markdownLanguage.parser.parse(source).topNode;
}

export function readingChildren(node: SyntaxNode): SyntaxNode[] {
  const children: SyntaxNode[] = [];
  for (let child = node.firstChild; child; child = child.nextSibling) children.push(child);
  return children;
}

const MARKS = new Set(["HeaderMark", "EmphasisMark", "CodeMark", "CodeInfo", "ListMark", "QuoteMark", "LinkMark", "URL", "LinkTitle", "TableDelimiter", "StrikethroughMark"]);

/** Source between syntax children, excluding only the parser's delimiters. */
export function readingSegments(node: SyntaxNode, source: string): Array<string | SyntaxNode> {
  const parts: Array<string | SyntaxNode> = [];
  let at = node.from;
  for (const child of readingChildren(node)) {
    if (child.from > at) parts.push(source.slice(at, child.from));
    if (!MARKS.has(child.name)) parts.push(child);
    at = child.to;
  }
  if (at < node.to) parts.push(source.slice(at, node.to));
  return parts;
}

export function readingContent(node: SyntaxNode, source: string): string {
  return readingSegments(node, source).map((part) => typeof part === "string" ? part : source.slice(part.from, part.to)).join("").trim();
}

/** Accessible plain label from the same parsed segments used by contents(). */
function readingPlainText(node: SyntaxNode, source: string): string {
  if (node.name === "Escape") return source.slice(node.from + 1, node.to);
  return readingSegments(node, source).map((part) => typeof part === "string" ? part : readingPlainText(part, source)).join("");
}

function ReadingOverflow({ children, label }: { children: ReactNode; label: string }) {
  const scrollRef = useRef<HTMLDivElement>(null);
  return <ScrollHint axis="x" scrollRef={scrollRef} className="reading-scroll-hint">
    <div ref={scrollRef} className="reading-scroll" role="region" aria-label={label} tabIndex={0}>{children}</div>
  </ScrollHint>;
}

type NoteDoors = Record<string, () => void>;
type Context = { source: string; noteDoors: NoteDoors };

/** Only real Markdown links to objects the Desk can open. Code, images and
 * HTML are words in the editable Note, never implicit navigation. */
export function readingObjectLinks(source: string): Array<{ ref: string; node: SyntaxNode }> {
  const links: Array<{ ref: string; node: SyntaxNode }> = [];
  const seen = new Set<string>();
  const visit = (node: SyntaxNode) => {
    if (["Image", "InlineCode", "FencedCode", "CodeBlock", "HTMLBlock", "HTMLTag"].includes(node.name)) return;
    if (node.name === "Link") {
      const url = node.getChild("URL");
      const ref = url ? source.slice(url.from, url.to) : "";
      if (/^[a-z][a-z_]*:\S+$/i.test(ref) && refOpener(ref) && !seen.has(ref)) {
        seen.add(ref);
        links.push({ ref, node });
      }
      return;
    }
    for (const child of readingChildren(node)) visit(child);
  };
  visit(parseReading(source));
  return links;
}

/** A deliberate door beside an editable Note; parsing never opens or fetches. */
export function ReadingObjectLinks({ source, onOpen }: { source: string; onOpen: (ref: string) => void }) {
  const links = useMemo(() => readingObjectLinks(source), [source]);
  if (!links.length) return null;
  return <FoldGadget title="Linked items" className="reading-object-links">
    <div className="reading-object-links-list">
      {links.map((link) => <Button key={link.ref} dense variant="secondary"
        aria-label={readingPlainText(link.node, source).trim() || link.ref}
        onClick={() => onOpen(link.ref)}>
        {contents(link.node, { source, noteDoors: {} })}
      </Button>)}
    </div>
  </FoldGadget>;
}

function plainLines(text: string, key: string): ReactNode {
  return text.split("\n").map((line, i) => <span key={`${key}.${i}`}>{i ? <br /> : null}{line}</span>);
}

function contents(node: SyntaxNode, context: Context): ReactNode[] {
  return readingSegments(node, context.source).map((part, i) => typeof part === "string"
    ? <span key={`${node.from}.${i}`}>{plainLines(part, `${node.from}.${i}`)}</span>
    : renderNode(part, context));
}

function link(node: SyntaxNode, context: Context): ReactNode {
  const { source, noteDoors } = context;
  const urlNode = node.getChild("URL");
  const href = urlNode ? source.slice(urlNode.from, urlNode.to) : "";
  const label = contents(node, context);
  const doorName = href.startsWith("door:") ? href.slice(5) : "";
  const door = Object.prototype.hasOwnProperty.call(noteDoors, doorName) ? noteDoors[doorName] : undefined;
  const open = door ?? refOpener(href);
  if (open) return <Button key={node.from} dense variant="secondary" className="surface-material-door reading-ref" onClick={open}>{label}</Button>;
  if (/^https?:\/\//i.test(href)) return <a key={node.from} href={href} target="_blank" rel="noreferrer noopener">{label.length ? label : href}</a>;
  return <span key={node.from} className="reading-inert"><strong>{label.length ? label : href}</strong>{href && <span className="reading-destination"> {href}</span>}</span>;
}

function renderNode(node: SyntaxNode, context: Context): ReactNode {
  const { source } = context;
  const key = node.from;
  const children = readingChildren(node);
  if (/^(ATX|Setext)Heading[1-6]$/.test(node.name)) {
    const depth = Number(node.name.at(-1));
    return createElement(`h${depth}`, { key, className: `reading-heading reading-heading-${depth} aw-h surface-material-h` }, contents(node, context));
  }
  switch (node.name) {
    case "Document": return children.map((child) => renderNode(child, context));
    case "Paragraph": return <p key={key}>{contents(node, context)}</p>;
    case "Task": return <span key={key}>{contents(node, context)}</span>;
    case "StrongEmphasis": return <strong key={key}>{contents(node, context)}</strong>;
    case "Emphasis": return <em key={key}>{contents(node, context)}</em>;
    case "Strikethrough": return <del key={key}>{contents(node, context)}</del>;
    case "InlineCode": return <code key={key}>{readingContent(node, source)}</code>;
    case "Escape": return source.slice(node.from + 1, node.to);
    case "HardBreak": return <br key={key} />;
    case "Link": return link(node, context);
    case "Autolink": {
      const url = node.getChild("URL");
      const href = url ? source.slice(url.from, url.to) : source.slice(node.from + 1, node.to - 1);
      return /^https?:\/\//i.test(href) ? <a key={key} href={href} target="_blank" rel="noreferrer noopener">{href}</a> : <span key={key}>{href}</span>;
    }
    case "Image": return <span key={key}>[{readingContent(node, source) || "image"}]</span>;
    case "BulletList": return <ul key={key}>{children.map((child) => renderNode(child, context))}</ul>;
    case "OrderedList": {
      const start = Number(source.slice(node.from, node.to).match(/^\d+/)?.[0] ?? 1);
      return <ol key={key} start={start !== 1 ? start : undefined}>{children.map((child) => renderNode(child, context))}</ol>;
    }
    case "ListItem": {
      const paragraphs = children.filter((child) => child.name === "Paragraph");
      return <li key={key}>{children.filter((child) => child.name !== "ListMark").map((child) => child.name === "Paragraph" && paragraphs.length === 1 ? contents(child, context) : renderNode(child, context))}</li>;
    }
    case "Blockquote": return <blockquote key={key}>{children.filter((child) => child.name !== "QuoteMark").map((child) => renderNode(child, context))}</blockquote>;
    case "FencedCode":
    case "CodeBlock": {
      const code = children.filter((child) => child.name === "CodeText");
      const body = code.length ? source.slice(code[0].from, code.at(-1)!.to) : "";
      const info = node.getChild("CodeInfo");
      const lang = info ? source.slice(info.from, info.to) : "";
      return <ReadingOverflow key={key} label="Code"><pre className="reading-code aw-pre">{lang && <span className="reading-language aw-lang">{lang.toUpperCase()}</span>}<code>{body}</code></pre></ReadingOverflow>;
    }
    case "Table": return <ReadingOverflow key={key} label="Table"><table className="reading-table"><thead>{children.filter((child) => child.name === "TableHeader").map((row) => renderNode(row, context))}</thead><tbody>{children.filter((child) => child.name === "TableRow").map((row) => renderNode(row, context))}</tbody></table></ReadingOverflow>;
    case "TableHeader":
    case "TableRow": return <tr key={key}>{children.filter((child) => child.name === "TableCell").map((cell) => createElement(node.name === "TableHeader" ? "th" : "td", { key: cell.from, scope: node.name === "TableHeader" ? "col" : undefined }, contents(cell, context)))}</tr>;
    case "HorizontalRule": return <hr key={key} />;
    // This includes HTMLBlock/HTMLTag: source is shown, never interpreted.
    default: return <span key={key}>{plainLines(source.slice(node.from, node.to), String(key))}</span>;
  }
}

export function ReadingDocument({ children, className, noteDoors = {}, "data-testid": testId }: { children: string; className?: string; noteDoors?: NoteDoors; "data-testid"?: string }) {
  if (!children.trim()) return null;
  return <div className={`reading-document${className ? ` ${className}` : ""}`} data-testid={testId}>{renderNode(parseReading(children), { source: children, noteDoors })}</div>;
}
