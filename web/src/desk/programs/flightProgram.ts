/* Programs (2026-10-28): the hub's `flight.program`, decoded. Pure: no imports. */
export interface FlightProgram {
  id: string;
  title: string;
  stepId: string | null;
  stepOrdinal: number | null;
}

/** The hub's `flight.program` (`{id, title, step_id, step_ordinal}`). */
export function flightProgramOf(raw: unknown): FlightProgram | null {
  const body = raw as { id?: unknown; title?: unknown; step_id?: unknown; step_ordinal?: unknown } | null | undefined;
  if (!body || typeof body !== "object" || !body.id) return null;
  const ordinal = Number(body.step_ordinal);
  return {
    id: String(body.id),
    title: String(body.title ?? ""),
    stepId: body.step_id ? String(body.step_id) : null,
    stepOrdinal: Number.isFinite(ordinal) && ordinal > 0 ? ordinal : null,
  };
}
