import { describe, expect, it } from "vitest";
import {
  decodeTerminalInput,
  isAllowedTerminalKey,
  normalizeTerminalKeys,
} from "../input";

describe("terminal input decoder", () => {
  it("keeps text and keys ordered, with CRLF represented by one Enter", () => {
    const decoded = decodeTerminalInput("echo hi\r\n\t\x7f");
    expect(decoded.rejected).toBeNull();
    expect(decoded.operations).toEqual([
      { kind: "text", text: "echo hi" },
      { kind: "keys", keys: ["Enter", "Tab", "BSpace"] },
    ]);
  });

  it("maps xterm navigation and control sequences to the hub allow-list", () => {
    const decoded = decodeTerminalInput("\x1b[A\x1b[1~\x1b[4~\x03\x1b");
    expect(decoded.rejected).toBeNull();
    expect(decoded.operations).toEqual([
      { kind: "keys", keys: ["Up", "Home", "End", "C-c", "Escape"] },
    ]);
  });

  it("keeps bracketed multiline paste as non-submitting text", () => {
    const decoded = decodeTerminalInput("\x1b[200~one\ntwo\x1b[201~");
    expect(decoded.rejected).toBeNull();
    expect(decoded.operations).toEqual([{ kind: "text", text: "one\ntwo", paste: true }]);
  });

  it("does not type an unsupported escape sequence", () => {
    const decoded = decodeTerminalInput("\x1b[999~");
    expect(decoded.operations).toEqual([]);
    expect(decoded.rejected).toBe("\x1b[999~");
  });

  it("preserves Unicode but visibly refuses transport-forbidden controls", () => {
    const decoded = decodeTerminalInput("λ🙂\x00");
    expect(decoded.operations).toEqual([]);
    expect(decoded.rejected).toBe("\x00");
    // Refusal is atomic: the safe text before the NUL is not partially sent.
    expect(decodeTerminalInput("safe\x00after").operations).toEqual([]);
    expect(decodeTerminalInput("tab\tline\n").rejected).toBeNull();
  });

  it("normalizes only the same named/literal contract as the hub", () => {
    expect(isAllowedTerminalKey("C-c")).toBe(true);
    expect(isAllowedTerminalKey("ArrowUp")).toBe(false);
    expect(normalizeTerminalKeys(["C-c", { literal: "λ" }, "Enter"])).toEqual({
      keys: ["C-c", { literal: "λ" }, "Enter"],
      rejected: null,
    });
    expect(normalizeTerminalKeys(["not-a-tmux-key"])).toEqual({
      keys: [],
      rejected: "not-a-tmux-key",
    });
    expect(normalizeTerminalKeys([{ literal: "nul\x00" }])).toEqual({
      keys: [],
      rejected: 'literal contains terminal control: "nul\\u0000"',
    });
  });
});
