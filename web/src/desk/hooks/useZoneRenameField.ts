/** PHILO-8-01 — the ONE zone rename behaviour. The spatial Floor's overlay
 * composes it today; the list's in-row field composes it after the owner
 * ratifies its canvas (UX-CANON §A.2). Enter commits, blur out of the row
 * commits, Escape cancels; a refused name (the hub's named 409) keeps the
 * field open with focus and shows the error. */
import { useRef, useState, type FocusEvent, type KeyboardEvent } from "react";
import { useDesk } from "../store";

export function useZoneRenameField(zoneId: string, title: string) {
  const [name, setName] = useState(title);
  const inputRef = useRef<HTMLInputElement>(null);
  const error = useDesk((s) => s.zoneRenameError);

  const commit = async () => {
    const { renameZone, setRenamingZone, clearZoneRenameError } = useDesk.getState();
    clearZoneRenameError();
    const clean = name.trim();
    if (clean && clean !== title) {
      await renameZone(zoneId, clean);
      if (useDesk.getState().zoneRenameError) {
        inputRef.current?.focus();
        return;
      }
    }
    setRenamingZone(null);
  };

  const cancel = () => {
    const { setRenamingZone, clearZoneRenameError } = useDesk.getState();
    setRenamingZone(null);
    clearZoneRenameError();
  };

  return {
    name,
    setName,
    inputRef,
    error,
    commit,
    cancel,
    /** For the row that holds the input and its mic. HS-111-10: commit only
     * when focus LEAVES the row — the speak-to-fill mic must not
     * commit-and-unmount mid-press. */
    rowProps: {
      onBlur: (e: FocusEvent<HTMLElement>) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node | null)) void commit();
      },
    },
    inputProps: {
      ref: inputRef,
      value: name,
      autoFocus: true,
      onChange: (e: { target: { value: string } }) => {
        setName(e.target.value);
        if (useDesk.getState().zoneRenameError) useDesk.getState().clearZoneRenameError();
      },
      onKeyDown: (e: KeyboardEvent<HTMLInputElement>) => {
        if (e.key === "Enter") void commit();
        if (e.key === "Escape") cancel();
      },
    },
  };
}
