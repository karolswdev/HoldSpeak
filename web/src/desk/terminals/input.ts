import type { TerminalKey } from "./types";

export type TerminalInputOperation =
  | { kind: "text"; text: string; paste?: boolean }
  | { kind: "keys"; keys: TerminalKey[] };

export interface DecodedTerminalInput {
  operations: TerminalInputOperation[];
  /** The unsupported sequence is named and shown to the caller; it is never
   * sent as a literal Escape-prefixed payload. */
  rejected: string | null;
}

const NAMED = new Set([
  "Enter", "Escape", "Tab", "BTab", "Space", "BSpace", "Up", "Down",
  "Left", "Right", "Home", "End", "PageUp", "PageDown", "IC", "DC",
  "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12",
]);
const MODIFIER = /^(?:C|M|S)(?:-(?:C|M|S))*-[A-Za-z0-9\\]$/;

export function isAllowedTerminalKey(value: string): boolean {
  return NAMED.has(value) || MODIFIER.test(value);
}

/** Matches holdspeak.tmux_transport.plain_text: literal text may carry only
 * tab and LF controls. Other C0/C1 bytes and DEL are transport refusals, not
 * text to smuggle through the keys endpoint. */
export function isAllowedLiteralText(value: string): boolean {
  for (const character of value) {
    const code = character.charCodeAt(0);
    if ((code < 0x20 && character !== "\t" && character !== "\n") || (code >= 0x7f && code <= 0x9f)) return false;
  }
  return true;
}

export function normalizeTerminalKeys(items: unknown[]):
  | { keys: TerminalKey[]; rejected: null }
  | { keys: []; rejected: string } {
  const keys: TerminalKey[] = [];
  for (const item of items) {
    if (typeof item === "string") {
      if (!isAllowedTerminalKey(item)) return { keys: [], rejected: item };
      keys.push(item);
      continue;
    }
    if (item && typeof item === "object" && "literal" in item) {
      const literal = (item as { literal?: unknown }).literal;
      if (typeof literal !== "string") return { keys: [], rejected: String(literal) };
      if (!isAllowedLiteralText(literal)) return { keys: [], rejected: `literal contains terminal control: ${JSON.stringify(literal)}` };
      keys.push({ literal });
      continue;
    }
    return { keys: [], rejected: String(item) };
  }
  return { keys, rejected: null };
}

function controlName(code: number): string | null {
  if (code >= 1 && code <= 26) return `C-${String.fromCharCode(96 + code)}`;
  return null;
}

function csiName(sequence: string): string | null {
  const match = /^\x1b\[([0-9;?]*)([~A-Za-z])$/.exec(sequence);
  if (!match) return null;
  const params = match[1];
  const final = match[2];
  if (!params && final === "A") return "Up";
  if (!params && final === "B") return "Down";
  if (!params && final === "C") return "Right";
  if (!params && final === "D") return "Left";
  if (!params && final === "H") return "Home";
  if (!params && final === "F") return "End";
  if (final !== "~") return null;
  return ({ "1": "Home", "2": "IC", "3": "DC", "4": "End", "5": "PageUp", "6": "PageDown" } as Record<string, string>)[params] || null;
}

function escapeName(sequence: string): string | null {
  return ({ "\x1bOP": "F1", "\x1bOQ": "F2", "\x1bOR": "F3", "\x1bOS": "F4" } as Record<string, string>)[sequence] || null;
}

function pushText(operations: TerminalInputOperation[], text: string, paste = false) {
  if (!text) return;
  const previous = operations.at(-1);
  if (previous?.kind === "text" && Boolean(previous.paste) === paste) previous.text += text;
  else operations.push({ kind: "text", text, ...(paste ? { paste: true } : {}) });
}

function pushKey(operations: TerminalInputOperation[], key: TerminalKey) {
  const previous = operations.at(-1);
  if (previous?.kind === "keys") previous.keys.push(key);
  else operations.push({ kind: "keys", keys: [key] });
}

/** Decode xterm's ordered onData stream without dropping or reordering input.
 * Text (including bracketed paste) remains a non-submitting text operation;
 * named controls use the existing hub allow-list. */
export function decodeTerminalInput(data: string): DecodedTerminalInput {
  const operations: TerminalInputOperation[] = [];
  let rejected: string | null = null;
  let index = 0;

  while (index < data.length) {
    const rest = data.slice(index);
    // Bracketed paste.  The wrappers are terminal protocol, not user text.
    if (rest.startsWith("\x1b[200~")) {
      const end = rest.indexOf("\x1b[201~", 6);
      if (end < 0) {
        rejected = rest;
        break;
      }
      const pasted = rest.slice(6, end);
      if (!isAllowedLiteralText(pasted)) {
        rejected = pasted;
        break;
      }
      pushText(operations, pasted, true);
      index += end + 6;
      continue;
    }

    const character = data[index];
    const code = character.charCodeAt(0);
    if (character !== "\x1b" && character !== "\r" && character !== "\n" && character !== "\t" && character !== "\b" && character !== "\x7f" && !(code >= 0x80 && code <= 0x9f) && code >= 0x20) {
      let end = index + 1;
      while (end < data.length) {
        const next = data[end];
        const nextCode = next.charCodeAt(0);
        if (next === "\x1b" || next === "\r" || next === "\n" || next === "\t" || next === "\b" || next === "\x7f" || nextCode < 0x20 || (nextCode >= 0x80 && nextCode <= 0x9f)) break;
        end += 1;
      }
      pushText(operations, data.slice(index, end));
      index = end;
      continue;
    }

    if (character === "\r") {
      pushKey(operations, "Enter");
      index += data[index + 1] === "\n" ? 2 : 1;
      continue;
    }
    if (character === "\n") {
      pushText(operations, "\n");
      index += 1;
      continue;
    }
    if (character === "\t") {
      pushKey(operations, "Tab");
      index += 1;
      continue;
    }
    if (character === "\b" || character === "\x7f") {
      pushKey(operations, "BSpace");
      index += 1;
      continue;
    }
    if (character === "\x1b") {
      let end = index + 1;
      if (data[end] === "[") {
        end += 1;
        while (end < data.length && !/[A-Za-z~]/.test(data[end])) end += 1;
        if (end < data.length) end += 1;
      } else if (data[end] === "O" && end + 1 < data.length) {
        end += 2;
      } else if (end < data.length) {
        // Alt/SS3 and other named escape sequences must be rejected as a
        // whole. Never downgrade an unsupported sequence to bare Escape plus
        // text, which would type something the owner did not request.
        end += 1;
      }
      const sequence = data.slice(index, end);
      const named = sequence === "\x1b" ? "Escape" : csiName(sequence) || escapeName(sequence);
      if (!named) {
        rejected = sequence;
        break;
      }
      pushKey(operations, named);
      index = end;
      continue;
    }

    const named = controlName(code);
    if (named && isAllowedTerminalKey(named)) pushKey(operations, named);
    else {
      rejected = character;
      break;
    }
    index += 1;
  }
  return { operations: rejected ? [] : operations, rejected };
}

/** A small convenience for key-palette callers and tests. */
export function decodeTerminalKeys(data: string): TerminalKey[] {
  const result = decodeTerminalInput(data);
  if (result.rejected) return [];
  return result.operations.flatMap((operation) => operation.kind === "keys" ? operation.keys : [{ literal: operation.text }]);
}

export const decodeInput = decodeTerminalInput;
