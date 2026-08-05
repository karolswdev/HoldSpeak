/** Safe field extractors for the wire → typed-primitive boundary (HS-117-01).
 *
 * Every `fromWire*` mapper uses these instead of bare property access on `any`.
 * Each helper checks shape before reading, returns a typed fallback on miss,
 * and never silently coerces (a number field that arrives as a string stays
 * the fallback, not a cast). Extra fields on the wire object are ignored. */

function isRecord(wire: unknown): wire is Record<string, unknown> {
  return typeof wire === "object" && wire !== null;
}

export function wireString(wire: unknown, key: string, fallback = ""): string {
  if (!isRecord(wire) || !(key in wire)) return fallback;
  const v = wire[key];
  return typeof v === "string" ? v : fallback;
}

export function wireNumber(wire: unknown, key: string, fallback = 0): number {
  if (!isRecord(wire) || !(key in wire)) return fallback;
  const v = wire[key];
  return typeof v === "number" && Number.isFinite(v) ? v : fallback;
}

export function wireBool(wire: unknown, key: string, fallback = false): boolean {
  if (!isRecord(wire) || !(key in wire)) return fallback;
  const v = wire[key];
  return typeof v === "boolean" ? v : fallback;
}

export function wireArray(wire: unknown, key: string): unknown[] {
  if (!isRecord(wire) || !(key in wire)) return [];
  const v = wire[key];
  return Array.isArray(v) ? v : [];
}

export function wireStringOrNull(wire: unknown, key: string): string | null {
  if (!isRecord(wire) || !(key in wire)) return null;
  const v = wire[key];
  return typeof v === "string" ? v : null;
}

export function wireRaw(wire: unknown, key: string): unknown {
  if (!isRecord(wire) || !(key in wire)) return undefined;
  return wire[key];
}

/** Log a contextual warning when a required identity field is absent. */
export function warnMissingId(kind: string, wire: unknown, key: string): void {
  if (!isRecord(wire) || !(key in wire) || wire[key] === "" || wire[key] == null) {
    console.warn(`[wireGuard] ${kind}: missing required field "${key}"`, wire);
  }
}
