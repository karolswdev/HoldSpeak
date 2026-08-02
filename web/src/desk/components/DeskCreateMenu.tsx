// HS-111-07 — the Create menu derives from the registry's desk.new-*
// verbs (its private DESK_CREATE_CHOICES list was parallel list #3 and
// had already drifted: it knew Workflow, the registry did not). Rows
// are the ONE menu species: 28px mono labels, no description prose.
import { useEffect, useId, useRef, useState } from "react";
import { verbsFor, type VerbContext } from "../verbRegistry";
import { DeskMenuItem, DeskMenuList } from "./DeskMenu";

const CTX: VerbContext = { selectedRef: null };

export function DeskCreateMenu({ className = "" }: { className?: string }) {
  const [open, setOpen] = useState(false);
  const id = useId();
  const rootRef = useRef<HTMLDivElement | null>(null);
  const buttonRef = useRef<HTMLButtonElement | null>(null);

  // The desk dismissal rule: outside pointer-down or Escape closes.
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

  const creates = verbsFor("floor").filter((v) => v.group === "new");

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
        <DeskMenuList
          className="desk-create-menu"
          label="Create a Desk item"
          anchor="below"
          style={{ position: "absolute", top: "100%", right: 0 }}
          onClose={() => setOpen(false)}
          returnFocus={() => buttonRef.current?.focus()}
          onMouseLeave={() => setOpen(false)}
        >
          {creates.map((v) => {
            // "New Note" → the bare kind word for the Create face.
            const word =
              typeof v.label === "string"
                ? v.label.replace(/^New /, "")
                : v.label(CTX);
            return (
              <DeskMenuItem
                key={v.id}
                ariaLabel={`Create ${word}`}
                onSelect={() => {
                  setOpen(false);
                  v.run(CTX);
                }}
              >
                {word}
              </DeskMenuItem>
            );
          })}
        </DeskMenuList>
      ) : null}
    </div>
  );
}
