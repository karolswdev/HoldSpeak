// The SCAR LAW for typed hub bodies (the test diet, 2026-10-11): a face test
// may type a SUBSET of a hub answer, but every field it types must be a field
// the hub sends, at the same place, of the same JSON type. The hub's answers
// are recorded in ./wire/*.wire.json (tests/integration/test_face_wire_fences.py).
//
// `inventedFields(typed, hub)` lists each field the typed body has and the
// hub's answer does not (or has as another JSON type). A null on either side
// matches any leaf; an empty hub list checks nothing under it.

type Json = unknown;

function kind(value: Json): string {
  if (value === null || value === undefined) return "null";
  if (Array.isArray(value)) return "array";
  return typeof value;
}

export function inventedFields(typed: Json, hub: Json, at = "$"): string[] {
  const t = kind(typed);
  const h = kind(hub);
  // A null on either side (a field the seed left unset) is not a lie.
  if (t === "null" || h === "null") return [];
  if (t !== h) return [`${at}: typed ${t}, hub ${h}`];
  if (t === "array") {
    const rows = hub as Json[];
    if (!rows.length) return [];
    return (typed as Json[]).flatMap((row, i) => inventedFields(row, rows[Math.min(i, rows.length - 1)], `${at}[${i}]`));
  }
  if (t === "object") {
    const live = hub as Record<string, Json>;
    return Object.entries(typed as Record<string, Json>).flatMap(([key, value]) =>
      key in live ? inventedFields(value, live[key], `${at}.${key}`) : [`${at}.${key}: not in the hub's answer`],
    );
  }
  return [];
}

/** A recorded answer's `wire` body. */
export function recorded<T = Record<string, unknown>>(file: { wire: unknown }): T {
  return structuredClone(file.wire) as T;
}
