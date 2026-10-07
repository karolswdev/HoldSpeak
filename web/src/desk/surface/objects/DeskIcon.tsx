/** PHILO-14 B1 — DeskIcon and IconLamp: the object on the glass.
 *
 *  Ratified board: A Workbench (docs/internal/philo/phase-14/canvas, A-1,
 *  A-2). The sprite over its name; no plate at rest. Selected = the
 *  sprite's `_sel` image and the name inverted (ink on paper). The icon is
 *  the library Button (`variant="chrome"`: the strip owns the material).
 *
 *  Keyboard: a press or Space SELECTS; Enter or a double press OPENS.
 */
import type { CSSProperties, DragEvent, KeyboardEvent } from "react";
import { Button } from "../../../components/signal/Signal";
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
        {badge ? <img className="desk-icon-badge" src={badge} alt="" draggable={false} /> : null}
        {lamp ? (
          <IconLamp tone={lamp.tone} count={lamp.count} />
        ) : count && count > 0 ? (
          <span className="desk-icon-count" aria-hidden="true">
            {count}
          </span>
        ) : null}
      </span>
      <span className="desk-icon-name">{name}</span>
    </Button>
  );
}
