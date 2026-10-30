/** LAMPS-WORDS (2026-10-30): every lamp says its word in sentence case. The
 *  lamp species (LampGadget: the menu-bar Live / mic / Record / runtime lamps,
 *  the row and info lamps) sends its label through `stateWords`, and its CSS
 *  draws the word as it is: no caps transform, no wide tracking, the sans
 *  face (a state is a dot and a word; mono is for code and ids). Acronyms
 *  and names keep their case. */
import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { LampGadget } from "../gadgets";
import gadgetsCss from "../gadgets.css?raw";
import recordingsCss from "../../recordings/recordings.css?raw";
import deskChromeSrc from "../../components/DeskChrome.tsx?raw";

const lampRule = /\n\.gadget-lamp \{([^}]*)\}/.exec(gadgetsCss)?.[1] ?? "";

describe("the lamp species draws sentence case", () => {
  it.each([
    ["SENDS OUT", "Sends out"],
    ["RECONNECTING", "Reconnecting"],
    ["OFFLINE", "Offline"],
    ["LISTENING", "Listening"],
    ["ON DEVICE", "On device"],
    ["PR OPEN", "PR open"],
    ["CLAUDE CODE ASKS", "Claude Code asks"],
    ["CODEX · MCP ON LAN", "Codex · MCP on LAN"],
    ["TELNYX CALL", "Telnyx call"],
    ["TAILSCALE OFF", "Tailscale off"],
    ["Recording on another view", "Recording on another view"],
    ["No engine", "No engine"],
  ])("%s → %s", (label, words) => {
    const { container } = render(<LampGadget label={label} on tone="ok" />);
    const lamp = container.querySelector(".gadget-lamp");
    expect(lamp?.textContent).toBe(words);
    expect(lamp?.getAttribute("title")).toBe(words);
  });

  it("the species CSS has no caps transform, no wide tracking and no mono face", () => {
    expect(lampRule).not.toBe("");
    expect(lampRule).not.toMatch(/text-transform:\s*uppercase/);
    expect(lampRule).toMatch(/letter-spacing:\s*0;/);
    expect(lampRule).toMatch(/var\(--font-sans\)/);
    expect(lampRule).not.toMatch(/--font-mono/);
  });

  it("no per-lamp override lifts the caps: the species does it once", () => {
    expect(recordingsCss).not.toMatch(/\.gadget-lamp\s*\{/);
  });

  it("the menu bar's runtime lamps pass words, never caps literals", () => {
    expect(deskChromeSrc).toContain('label="Reconnecting"');
    expect(deskChromeSrc).toContain('label="Offline"');
    expect(deskChromeSrc).not.toMatch(/<LampGadget label="[A-Z][A-Z ]+"/);
    expect(deskChromeSrc).toMatch(/role="status">Ready</);
  });
});
