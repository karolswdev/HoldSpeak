import { useEffect, useId, useRef, useState } from "react";
import { useDesk } from "../store";

export type DeskCreateKind = "note" | "zone" | "kb" | "recipe" | "workflow";

export const DESK_CREATE_CHOICES: ReadonlyArray<{
  kind: DeskCreateKind;
  label: string;
  description: string;
}> = [
  { kind: "note", label: "Note", description: "Write or dictate text." },
  { kind: "zone", label: "Zone", description: "Place related Desk items." },
  {
    kind: "kb",
    label: "Knowledge",
    description: "Gather reusable context.",
  },
  {
    kind: "recipe",
    label: "Agent",
    description: "Save reusable behavior.",
  },
  {
    kind: "workflow",
    label: "Workflow",
    description: "Build repeatable steps.",
  },
];

export function DeskCreateMenu({ className = "" }: { className?: string }) {
  const [open, setOpen] = useState(false);
  const id = useId();
  const rootRef = useRef<HTMLDivElement | null>(null);
  const buttonRef = useRef<HTMLButtonElement | null>(null);
  const menuRef = useRef<HTMLDivElement | null>(null);
  const createPrimitive = useDesk((state) => state.createPrimitive);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      setOpen(false);
      buttonRef.current?.focus();
    };
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  useEffect(() => {
    if (open)
      menuRef.current?.querySelector<HTMLButtonElement>("button")?.focus();
  }, [open]);

  const moveFocus = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) return;
    const items = Array.from(
      event.currentTarget.querySelectorAll<HTMLButtonElement>("button"),
    );
    if (!items.length) return;
    event.preventDefault();
    const current = items.indexOf(document.activeElement as HTMLButtonElement);
    const next =
      event.key === "Home"
        ? 0
        : event.key === "End"
          ? items.length - 1
          : event.key === "ArrowDown"
            ? (current + 1 + items.length) % items.length
            : (current - 1 + items.length) % items.length;
    items[next]?.focus();
  };

  return (
    <div ref={rootRef} className={`desk-create ${className}`.trim()}>
      <button
        ref={buttonRef}
        type="button"
        className="desk-chip desk-create-button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={id}
        onClick={() => setOpen((value) => !value)}
      >
        <span aria-hidden="true">＋</span> Create
      </button>
      {open ? (
        <div
          ref={menuRef}
          id={id}
          className="desk-create-menu"
          role="menu"
          aria-label="Create a Desk item"
          onKeyDown={moveFocus}
        >
          {DESK_CREATE_CHOICES.map((choice) => (
            <button
              key={choice.kind}
              type="button"
              role="menuitem"
              aria-label={`Create ${choice.label}`}
              onClick={() => {
                setOpen(false);
                void createPrimitive(choice.kind);
              }}
            >
              <strong>{choice.label}</strong>
              <span>{choice.description}</span>
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
