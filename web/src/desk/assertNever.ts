/** Exhaustive-switch helper (HS-117-14): a `default` branch that passes
 * the discriminant here turns a missing `case` into a compile error.
 * At runtime it throws — but the compiler should prevent reaching it. */
export function assertNever(x: never): never {
  throw new Error(`Unhandled kind: ${x}`);
}
