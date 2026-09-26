/** PHILO-8-01 — the ONE zone name field (the owner ratified the canvas,
 * 2026-09-26: "Ratify as drawn", "Chip on the list and the Floor"). The
 * spatial Floor draws it over the zone (`is-overlay`); the list draws it in
 * the zone's Name cell (`is-inrow`). A refusal is the library StateChip
 * `failure` on its own line under the field: `NAME TAKEN` or `NOT SAVED`. */
import type { CSSProperties } from "react";
import { MicButton } from "./MicButton";
import { StateChip } from "../surface";
import { useZoneRenameField } from "../hooks/useZoneRenameField";

export function ZoneRenameRow({
  zoneId,
  title,
  placement,
  style,
}: {
  zoneId: string;
  title: string;
  placement: "overlay" | "inrow";
  style?: CSSProperties;
}) {
  const field = useZoneRenameField(zoneId, title);
  return (
    <span
      className={`desk-zone-rename-row is-${placement}`}
      style={style}
      // The field keeps its pointer, clicks and keys: the Floor must not start
      // a drag, and the list row must not dive or open on them.
      onPointerDown={(e) => e.stopPropagation()}
      onClick={(e) => e.stopPropagation()}
      onKeyDown={(e) => e.stopPropagation()}
      {...field.rowProps}
    >
      <input className="desk-zone-rename" aria-label="Zone name" {...field.inputProps} />
      <MicButton draftScope={`zone-rename:${zoneId}`} onText={(t) => field.setName(t)} />
      {field.error ? (
        <span className="desk-zone-rename-refusal" data-code={field.error.code} title={field.error.detail}>
          <StateChip state="failure" label={field.error.label} data-testid="zone-name-refused" />
        </span>
      ) : null}
    </span>
  );
}
