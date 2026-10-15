// One native form control, one library popup. The SELECT stays visible,
// labelled, focusable and responsible for values, validation and events.
import {
  useEffect, useId, useLayoutEffect, useRef, useState,
  type ComponentPropsWithRef, type CSSProperties, type KeyboardEvent,
} from "react";
import { createPortal } from "react-dom";
import { Button } from "./Button";
import "./WorkbenchSelect.css";

type Choice = { index: number; value: string; label: string; disabled: boolean };
type Popup = { choices: Choice[]; selected: number; active: number; label: string; style: CSSProperties };

function nativeChoices(select: HTMLSelectElement): Choice[] {
  return Array.from(select.options, (option, index) => ({
    index, value: option.value, label: option.label,
    disabled: option.disabled || (option.parentElement instanceof HTMLOptGroupElement && option.parentElement.disabled),
  }));
}

/** Shared by CycleGadget and the surviving Signal Select boundary. */
export function WorkbenchSelect({
  children, disabled, multiple, size, ref: forwardedRef,
  onPointerDown, onMouseDown, onClick, onKeyDown, onBlur, onChange,
  ...props
}: ComponentPropsWithRef<"select">) {
  const ownerRef = useRef<HTMLSelectElement | null>(null);
  const listRef = useRef<HTMLDivElement | null>(null);
  const [popup, setPopup] = useState<Popup | null>(null);
  const search = useRef({ text: "", at: 0 });
  const id = `${useId()}-choices`;
  const dropdown = !multiple && (size ?? 1) <= 1;

  function open(): Popup | null {
    const owner = ownerRef.current;
    if (!owner || !dropdown || owner.matches(":disabled")) return null;
    const choices = nativeChoices(owner);
    if (!choices.length) return null;
    const bounds = owner.getBoundingClientRect();
    const viewport = window.visualViewport;
    const vw = viewport?.width ?? window.innerWidth;
    const vh = viewport?.height ?? window.innerHeight;
    const vx = viewport?.offsetLeft ?? 0;
    const vy = viewport?.offsetTop ?? 0;
    const gap = 4, margin = 8;
    const below = Math.max(0, vy + vh - bounds.bottom - gap - margin);
    const above = Math.max(0, bounds.top - vy - gap - margin);
    const downward = below >= Math.min(160, choices.length * 32 + 8) || below >= above;
    const width = Math.min(Math.max(bounds.width, 200), vw - margin * 2);
    const style: CSSProperties = {
      width, left: Math.max(vx + margin, Math.min(bounds.left, vx + vw - width - margin)),
      maxHeight: Math.min(320, downward ? below : above),
      ...(downward ? { top: Math.max(vy + margin, bounds.bottom + gap) }
        : { bottom: Math.max(margin, window.innerHeight - bounds.top + gap) }),
    };
    // Portal out of window clipping while keeping the owning surface's theme.
    const computed = getComputedStyle(owner);
    for (let index = 0; index < computed.length; index++) {
      const name = computed.item(index);
      if (name.startsWith("--")) (style as Record<string, string | number>)[name] = computed.getPropertyValue(name);
    }
    const selected = owner.selectedIndex;
    const next = {
      choices, selected, active: selected >= 0 && !choices[selected]?.disabled ? selected : choices.findIndex((choice) => !choice.disabled),
      label: owner.getAttribute("aria-label") || Array.from(owner.labels ?? [], (label) => label.textContent?.trim()).filter(Boolean).join(" ") || owner.title,
      style,
    };
    search.current = { text: "", at: 0 };
    setPopup(next);
    return next;
  }

  function commit(index: number) {
    const owner = ownerRef.current;
    // Re-read native options: a live provider may have become unavailable.
    const choice = owner && nativeChoices(owner)[index];
    if (!owner || owner.matches(":disabled") || !choice || choice.disabled || choice.value !== popup?.choices[index]?.value) return;
    setPopup(null);
    owner.focus({ preventScroll: true });
    if (owner.selectedIndex === index) return;
    owner.selectedIndex = index;
    owner.dispatchEvent(new Event("input", { bubbles: true }));
    owner.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function keyDown(event: KeyboardEvent<HTMLSelectElement>) {
    onKeyDown?.(event);
    if (event.defaultPrevented || !dropdown || event.currentTarget.matches(":disabled")) return;
    const { key } = event;
    if (key === "Escape" && popup) {
      event.preventDefault(); event.stopPropagation(); setPopup(null); return;
    }
    if (key === "Tab") { setPopup(null); return; }
    if (event.metaKey || event.ctrlKey || (event.altKey && key !== "ArrowDown" && key !== "ArrowUp")) return;
    const movement = ["ArrowDown", "ArrowUp", "Home", "End"].includes(key);
    const confirm = key === "Enter" || key === " ";
    const typing = key.length === 1 && key.trim() !== "" && !event.altKey;
    if (!movement && !confirm && !typing) return;
    event.preventDefault(); event.stopPropagation();
    const current = popup ?? open();
    if (!current) return;
    if (confirm) { if (popup) commit(popup.active); return; }
    const enabled = current.choices.filter((choice) => !choice.disabled);
    if (!enabled.length) return;
    let active = current.active;
    if (key === "Home") active = enabled[0].index;
    else if (key === "End") active = enabled[enabled.length - 1].index;
    else if (movement && popup) {
      const at = enabled.findIndex((choice) => choice.index === active);
      const step = key === "ArrowDown" ? 1 : -1;
      active = enabled[(at + step + enabled.length) % enabled.length].index;
    } else if (typing) {
      const now = Date.now(), letter = key.toLocaleLowerCase();
      const previous = now - search.current.at < 700 ? search.current.text : "";
      const text = previous && [...previous].every((char) => char === letter) ? letter : previous + letter;
      search.current = { text, at: now };
      const at = enabled.findIndex((choice) => choice.index === active);
      for (let step = text.length > 1 ? 0 : 1; step <= enabled.length; step++) {
        const choice = enabled[(Math.max(0, at) + step) % enabled.length];
        if (choice.label.trim().toLocaleLowerCase().startsWith(text)) { active = choice.index; break; }
      }
    }
    setPopup({ ...current, active });
  }

  useEffect(() => {
    if (!popup) return;
    const owner = ownerRef.current;
    if (!owner) return;
    const choices = nativeChoices(owner);
    // Polls and window raises can recreate React children without changing
    // the choices. Close only when the actual native snapshot changed.
    if (owner.matches(":disabled") || !dropdown || owner.selectedIndex !== popup.selected
      || choices.length !== popup.choices.length
      || choices.some((choice, index) => {
        const before = popup.choices[index];
        return choice.value !== before.value || choice.label !== before.label || choice.disabled !== before.disabled;
      })) setPopup(null);
  });

  useEffect(() => {
    if (!popup) return;
    const outside = (event: PointerEvent) => {
      const target = event.target as Node;
      if (!ownerRef.current?.contains(target) && !listRef.current?.contains(target)) setPopup(null);
    };
    const scroll = (event: Event) => {
      if (!(event.target instanceof Node) || !listRef.current?.contains(event.target)) setPopup(null);
    };
    const close = () => setPopup(null);
    document.addEventListener("pointerdown", outside, true);
    window.addEventListener("scroll", scroll, true);
    window.addEventListener("resize", close);
    window.visualViewport?.addEventListener("resize", close);
    window.visualViewport?.addEventListener("scroll", close);
    return () => {
      document.removeEventListener("pointerdown", outside, true);
      window.removeEventListener("scroll", scroll, true);
      window.removeEventListener("resize", close);
      window.visualViewport?.removeEventListener("resize", close);
      window.visualViewport?.removeEventListener("scroll", close);
    };
  }, [Boolean(popup)]);

  useLayoutEffect(() => {
    if (popup) listRef.current?.querySelector<HTMLElement>(`[data-index="${popup.active}"]`)?.scrollIntoView?.({ block: "nearest" });
  }, [popup?.active]);

  return <>
    <select {...props} disabled={disabled} multiple={multiple} size={size}
      ref={(node) => {
        ownerRef.current = node;
        if (typeof forwardedRef === "function") return forwardedRef(node);
        if (forwardedRef) forwardedRef.current = node;
      }}
      className={`workbench-select ${props.className ?? ""}`.trim()}
      aria-haspopup={dropdown ? "listbox" : undefined}
      aria-expanded={dropdown ? Boolean(popup) : undefined}
      aria-controls={popup ? id : undefined}
      aria-activedescendant={popup && popup.active >= 0 ? `${id}-${popup.active}` : undefined}
      onPointerDown={(event) => {
        onPointerDown?.(event);
        if (event.defaultPrevented || !dropdown || event.button > 0 || event.currentTarget.matches(":disabled")) return;
        event.preventDefault();
        event.currentTarget.focus({ preventScroll: true });
        if (popup) setPopup(null); else open();
      }}
      onMouseDown={(event) => { onMouseDown?.(event); if (dropdown) event.preventDefault(); }}
      onClick={(event) => {
        onClick?.(event);
        if (event.defaultPrevented || !dropdown || event.currentTarget.matches(":disabled")) return;
        event.preventDefault();
        // Pointer opens on down. Assistive activation supplies a click only.
        if (event.detail === 0) { event.currentTarget.focus({ preventScroll: true }); if (popup) setPopup(null); else open(); }
      }}
      onKeyDown={keyDown}
      onBlur={(event) => { setPopup(null); onBlur?.(event); }}
      onChange={(event) => { setPopup(null); onChange?.(event); }}
    >{children}</select>
    {popup ? createPortal(<div ref={listRef} id={id} role="listbox"
      className="workbench-picker" style={popup.style}
      aria-label={popup.label || undefined} aria-labelledby={props["aria-labelledby"]}
      onPointerDown={(event) => { event.preventDefault(); event.stopPropagation(); }}>
      {popup.choices.map((choice) => <Button key={choice.index} variant="chrome"
        id={`${id}-${choice.index}`} role="option" tabIndex={-1}
        aria-selected={choice.index === popup.selected} disabled={choice.disabled}
        className="workbench-picker-row" data-active={choice.index === popup.active || undefined}
        data-index={choice.index}
        onPointerMove={() => { if (!choice.disabled && popup.active !== choice.index) setPopup({ ...popup, active: choice.index }); }}
        onClick={(event) => { event.stopPropagation(); commit(choice.index); }}>
        <span className="workbench-picker-check" aria-hidden="true">{choice.index === popup.selected ? "✓" : ""}</span>
        <span>{choice.label}</span>
      </Button>)}
    </div>, document.body) : null}
  </>;
}
