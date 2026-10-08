/** PHILO-14 B1 — DeskIcon and IconLamp: the object on the glass.
 *
 *  Ratified board: A Workbench (docs/internal/philo/phase-14/canvas, A-1,
 *  A-2). The sprite over its name; no plate at rest. Selected = the
 *  sprite's `_sel` image and the name inverted (ink on paper). The icon is
 *  the library Button (`variant="chrome"`: the strip owns the material).
 *
 *  Keyboard: a press or Space SELECTS; Enter or a double press OPENS.
 */
import { Fragment, useLayoutEffect, useRef, useState, type CSSProperties, type DragEvent, type KeyboardEvent, type ReactNode } from "react";
import { fitName } from "./fitName";
import { Button } from "../../../components/signal/Signal";
import { listSprite } from "../../sprites";
import { objectKindWord, objectSprite, type ObjectTone } from "./kinds";
import "./objects.css";

export interface IconLampProps {
  tone: ObjectTone;
  /** The notch count (the drawers' `3`, `6`). Zero or less draws no notch. */
  count?: number;
}

/** The one lamp on an icon: a 12 px square LED, raised, at the sprite's top
 *  right, with an optional count notch at its top left. aria-hidden: the
 *  word lives in the icon's accessible name. */
export function IconLamp({ tone, count }: IconLampProps) {
  return (
    <>
      <span className="desk-icon-lamp" data-tone={tone} aria-hidden="true" />
      {count && count > 0 ? (
        <span className="desk-icon-count" aria-hidden="true">
          {count}
        </span>
      ) : null}
    </>
  );
}

export interface DeskIconProps {
  /** The object's id (the sprite variant hash; stamped as data-object-id). */
  id: string;
  kind: string;
  name: string;
  /** The KIND word in the accessible name; default from `kind`. */
  kindWord?: string;
  /** A sprite URL in place of the mold's (lane A0's new mold). */
  sprite?: string;
  /** The selected sprite URL, when `sprite` is given. */
  spriteSelected?: string;
  selected?: boolean;
  /** The lamp, with the word it stands for (the accessible name says it). */
  lamp?: IconLampProps & { label?: string };
  /** The count notch alone, with no lamp (a drawer whose things run and
   *  ask nothing: the Conductor while its agents work). PHILO-14 A1. Ignored
   *  when `lamp` is given (the lamp carries its own count). */
  count?: number;
  /** A small badge sprite at the bottom right (the Conductor's automaton). */
  badge?: string;
  /** DropTarget state: the icon is lit as the target of a drag. */
  drop?: boolean;
  /** Ghost state: the object being dragged, or parked (dimmed). */
  ghost?: boolean;
  onSelect?(): void;
  onOpen?(): void;
  /** Extra words for the accessible name (e.g. `3 need you`). */
  ariaExtra?: string;
  className?: string;
  style?: CSSProperties;
  draggable?: boolean;
  onDragStart?(event: DragEvent<HTMLButtonElement>): void;
  /** The drag ended (dropped anywhere, or let go): the source's cleanup. */
  onDragEnd?(event: DragEvent<HTMLButtonElement>): void;
  /** PHILO-14 C3: the icon as a drop target. `onDragOver` must call
   *  `preventDefault()` for the drop to land; `onDrop` takes it. */
  onDragOver?(event: DragEvent<HTMLButtonElement>): void;
  onDragLeave?(event: DragEvent<HTMLButtonElement>): void;
  onDrop?(event: DragEvent<HTMLButtonElement>): void;
}

export function DeskIcon({
  id,
  kind,
  name,
  kindWord,
  sprite,
  spriteSelected,
  selected,
  lamp,
  count,
  badge,
  drop,
  ghost,
  onSelect,
  onOpen,
  ariaExtra,
  className,
  style,
  draggable,
  onDragStart,
  onDragEnd,
  onDragOver,
  onDragLeave,
  onDrop,
}: DeskIconProps) {
  const lit = Boolean(selected || drop);
  const src = sprite
    ? lit && spriteSelected
      ? spriteSelected
      : sprite
    : objectSprite(kind, id, lit ? "sel" : "rest");
  const label = [name, kindWord ?? objectKindWord(kind), lamp?.label, ariaExtra]
    .filter(Boolean)
    .join(", ");
  // Enter OPENS: handled on keydown, whose default (the native click) is
  // prevented, so it never also selects. Every other activation — a pointer
  // press, Space (the native click on keyup), element.click(), an assistive
  // "press" — arrives as ONE click and SELECTS.
  const onKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    if (event.key === "Enter") {
      event.preventDefault();
      onOpen?.();
    }
  };
  const onClick = () => onSelect?.();
  return (
    <Button
      variant="chrome"
      className={`desk-icon${className ? ` ${className}` : ""}`}
      aria-label={label}
      aria-pressed={selected ? "true" : "false"}
      data-object-id={id}
      data-kind={kind}
      data-selected={selected ? "true" : undefined}
      data-drop={drop ? "true" : undefined}
      data-ghost={ghost ? "true" : undefined}
      style={style}
      onClick={onClick}
      onDoubleClick={onOpen ? () => onOpen() : undefined}
      onKeyDown={onKeyDown}
      draggable={draggable}
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      <span className="desk-icon-art">
        <img src={src} alt="" draggable={false} />
        {badge ? <img className="desk-icon-badge" src={listSprite(badge)} alt="" draggable={false} /> : null}
        {lamp ? (
          <IconLamp tone={lamp.tone} count={lamp.count} />
        ) : count && count > 0 ? (
          <span className="desk-icon-count" aria-hidden="true">
            {count}
          </span>
        ) : null}
      </span>
      <IconName name={name} />
    </Button>
  );
}

/** PHILO-15 lane 12 (B30, Astra r1): the label. A clamped label (the desk,
 *  two lines) is set by `fitName` from its measured width: spaces break
 *  first, a too-long word breaks at its joins, an overlong name is cut in
 *  the middle so its end stays. A drawer's label is clamped to one line
 *  (PHILO-15 B40). An unclamped label is set by CSS from `nameBreaks`. The
 *  full name is the title either way. */
function IconName({ name }: { name: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const [lines, setLines] = useState<string[] | null>(null);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el || typeof getComputedStyle !== "function") return;
    const st = getComputedStyle(el);
    const clamp = parseInt(st.getPropertyValue("-webkit-line-clamp"), 10);
    const ch = charWidth(st);
    if (!Number.isFinite(clamp) || !ch) {
      setLines(null);
      return;
    }
    const max = parseFloat(st.maxWidth);
    const room = el.parentElement?.clientWidth || max;
    const box = Math.min(Number.isFinite(max) ? max : room, room || max);
    const inner = box - parseFloat(st.paddingLeft || "0") - parseFloat(st.paddingRight || "0");
    setLines(fitName(name, Math.floor((inner - 1) / ch), clamp));
  }, [name]);
  return (
    <span ref={ref} className="desk-icon-name" title={name} data-fitted={lines ? "" : undefined}>
      {lines ? lines.join("\n") : nameBreaks(name)}
    </span>
  );
}

const widths = new Map<string, number>();
/** One character's width in the label's (monospaced) font; 0 when there is
 *  no canvas to measure with (jsdom). */
function charWidth(st: CSSStyleDeclaration): number {
  const font = `${st.fontWeight} ${st.fontSize} ${st.fontFamily}`;
  const known = widths.get(font);
  if (known !== undefined) return known;
  let w = 0;
  try {
    const ctx = document.createElement("canvas").getContext("2d");
    if (ctx) {
      ctx.font = font;
      w = ctx.measureText("MMMMMMMMMM").width / 10;
    }
  } catch {
    w = 0;
  }
  widths.set(font, w);
  return w;
}

/** PHILO-15 lane 12 (B30): the CSS form of the break priority. Each word is
 *  an inline-block (`.name-word`), so a line breaks between words first; a
 *  word wider than the line breaks inside itself only after a join
 *  (`<wbr>` after `_ - . /`), never inside a run of letters. */
export function nameBreaks(name: string): ReactNode {
  const words = name.split(/(\s+)/);
  return words.map((word, i) => {
    if (!word) return null;
    if (/^\s+$/.test(word)) return " ";
    const parts = word.split(/(?<=[_\-./])(?=\S)/);
    return (
      <span key={i} className="name-word">
        {parts.map((part, j) => (
          <Fragment key={j}>
            {j > 0 ? <wbr /> : null}
            {part}
          </Fragment>
        ))}
      </span>
    );
  });
}
