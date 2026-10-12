// The SCAR LAW for typed hub bodies (the test diet, 2026-10-11): a face test
// may type a SUBSET of a hub answer, but every field it types must be a field
// the hub sends, at the same place, of the same JSON type. The hub's answers
// are recorded in ./wire/*.wire.json (tests/integration/test_face_wire_fences.py).
//
// `inventedFields(typed, ...recorded)` lists each place where the typed body
// says more than the recordings show:
// - a key no recording has at that place;
// - another JSON type than the recording's;
// - an object or a list where every recording has null (Astra r1 on #1107:
//   a null recording proves nothing about the subtree typed under it);
// - rows where every recording's list is empty (record a state with rows).
// Several recordings of one answer may be given: a key is proven when one of
// them carries it non-null. A typed row is compared with the recorded row it
// fits best. A typed null, or a typed leaf against a recorded null, is no lie.

type Json = unknown;
type Obj = Record<string, Json>;

function kind(value: Json): string {
  if (value === null || value === undefined) return "null";
  if (Array.isArray(value)) return "array";
  return typeof value;
}

function diff(typed: Json, hubs: Json[], at: string): string[] {
  const t = kind(typed);
  if (t === "null") return [];
  const live = hubs.filter((h) => kind(h) !== "null");
  if (!live.length) {
    return t === "object" || t === "array" ? [`${at}: typed ${t}, the recordings hold only null`] : [];
  }
  const same = live.filter((h) => kind(h) === t);
  if (!same.length) return [`${at}: typed ${t}, hub ${kind(live[0])}`];
  if (t === "array") {
    const rows = same.flatMap((h) => h as Json[]);
    const typedRows = typed as Json[];
    if (!rows.length) {
      return typedRows.length ? [`${at}: typed rows, the recorded list is empty (record a state with rows)`] : [];
    }
    return typedRows.flatMap((row, i) => bestRow(row, rows, `${at}[${i}]`));
  }
  if (t === "object") {
    return Object.entries(typed as Obj).flatMap(([key, value]) => {
      const holders = (same as Obj[]).filter((h) => key in h);
      if (!holders.length) return [`${at}.${key}: not in the hub's answer`];
      return diff(value, holders.map((h) => h[key]), `${at}.${key}`);
    });
  }
  return [];
}

function bestRow(row: Json, rows: Json[], at: string): string[] {
  let best: string[] | null = null;
  for (const candidate of rows) {
    const found = diff(row, [candidate], at);
    if (!found.length) return [];
    if (!best || found.length < best.length) best = found;
  }
  return best ?? [];
}

export function inventedFields(typed: Json, ...recorded: Json[]): string[] {
  return diff(typed, recorded, "$");
}

/** A recorded answer's `wire` body. */
export function recorded<T = Record<string, unknown>>(file: { wire: unknown }): T {
  return structuredClone(file.wire) as T;
}
