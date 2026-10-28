/* The "Also called" field: the other names for the owner, as chips, then
 * one input. A comma or Enter adds; Backspace on an empty input removes the
 * last chip. One component, two faces: the first-run You card and
 * Settings › People › You (PHILO-15 B57). */
import { useEffect, useRef } from "react";
import { StringGadget } from "../surface";
import type { useOwnerName } from "./ownerName";
import "./firstrun.css";
import { Token } from "../surface/Token";

export function OwnerAliasField({
  owner,
  onDraftChange,
  mic = true,
}: {
  owner: ReturnType<typeof useOwnerName>;
  onDraftChange?: (dirty: boolean) => void;
  mic?: boolean;
}) {
  const alias = owner.aliasDraft;
  const composing = useRef(false);
  const endingComposition = useRef(false);
  const compositionCycle = useRef(0);
  const awaitingFinalChange = useRef(false);
  const composedValue = useRef("");
  const reportedDirty = useRef(false);
  const reportDirty = (dirty: boolean) => {
    if (reportedDirty.current === dirty) return;
    reportedDirty.current = dirty;
    onDraftChange?.(dirty);
  };
  useEffect(() => {
    const dirty = Boolean(alias.trim());
    if (reportedDirty.current === dirty) return;
    reportedDirty.current = dirty;
    onDraftChange?.(dirty);
  }, [alias, onDraftChange]);
  const setDraft = (next: string) => {
    owner.setAliasDraft(next);
    reportDirty(Boolean(next.trim()));
  };
  const commit = () => {
    if (composing.current) return;
    if (!alias.trim()) return;
    owner.commitAliasDraft();
    reportDirty(false);
  };
  return (
    <span className="firstrun-alias-row">
      {owner.aliases.map((name) => (
        <Token key={name} className="surface-token" data-chip>
          {name}
        </Token>
      ))}
      <StringGadget
        label="Also called"
        value={alias}
        mic={mic}
        onChange={(next) => {
          if (awaitingFinalChange.current && next === composedValue.current) {
            awaitingFinalChange.current = false;
            setDraft(next);
            return;
          }
          awaitingFinalChange.current = false;
          // A spoken or pasted list arrives whole: commas split it.
          if (!composing.current && next.includes(",")) {
            owner.addAliases(next);
            setDraft("");
          } else setDraft(next);
        }}
        placeholder="Add"
        onKeyDown={(event) => {
          if (composing.current || endingComposition.current || event.nativeEvent.isComposing || event.keyCode === 229) return;
          if (event.key === "Enter") {
            event.preventDefault();
            commit();
          } else if (event.key === "Backspace" && !alias) owner.removeLastAlias();
        }}
        inputProps={{
          onBlur: commit,
          onCompositionStart: () => {
            compositionCycle.current += 1;
            composing.current = true;
            endingComposition.current = false;
            awaitingFinalChange.current = false;
          },
          onCompositionEnd: (event) => {
            composing.current = false;
            endingComposition.current = true;
            const cycle = compositionCycle.current;
            queueMicrotask(() => {
              if (compositionCycle.current === cycle) endingComposition.current = false;
            });
            awaitingFinalChange.current = true;
            composedValue.current = event.currentTarget.value;
            setDraft(event.currentTarget.value);
          },
        }}
      />
    </span>
  );
}
