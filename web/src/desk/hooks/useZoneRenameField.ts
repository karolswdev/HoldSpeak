/** PHILO-8-01 — the ONE zone rename behaviour, composed by the one row
 * component `ZoneRenameRow` (the spatial Floor's overlay and the list's zone
 * row; the owner ratified the canvas 2026-09-26). The name opens selected, so
 * typing replaces it; Enter writes, blur out of the row writes, Escape keeps
 * the name; a name of spaces only writes nothing. A refused name keeps the
 * field open with focus and its chip (`zoneRenameError` for this zone). */
import { useRef, useState, type FocusEvent, type KeyboardEvent } from "react";
import { useDesk } from "../store";

export function useZoneRenameField(zoneId: string, title: string) {
  const [name, setName] = useState(title);
  const inputRef = useRef<HTMLInputElement>(null);
  const error = useDesk((s) => (s.zoneRenameError?.zoneId === zoneId ? s.zoneRenameError : null));

  const commit = async () => {
    const { renameZone, clearZoneRenameError } = useDesk.getState();
    clearZoneRenameError();
    const clean = name.trim();
    if (clean && clean !== title) {
      await renameZone(zoneId, clean);
      if (useDesk.getState().zoneRenameError?.zoneId === zoneId) {
        inputRef.current?.focus();
        return;
      }
    }
    // Close only this zone's field: another rename may have opened meanwhile.
    if (useDesk.getState().renamingZoneId === zoneId) useDesk.getState().setRenamingZone(null);
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
      onFocus: (e: FocusEvent<HTMLInputElement>) => e.currentTarget.select(),
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
