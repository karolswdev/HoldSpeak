/** EGRESS-CHIP-WORDS (2026-10-30): the chip species says its word in
 *  sentence case. EgressChip and SecretRow send their words through
 *  `stateWords`; `.gadget-chip` has no caps rule and draws the quiet sans; a
 *  chip that carries a host shows it as typed, as a code token (mono). */
import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { EgressChip, SecretRow, chipCarriesHost } from "../gadgets";
import gadgetsCss from "../gadgets.css?raw";

const chipRule = /\n\.gadget-chip \{([^}]*)\}/.exec(gadgetsCss)?.[1] ?? "";

describe("the egress chip says its word in sentence case", () => {
  it.each([
    ["THIS DEVICE", "cloud", "This device"],
    ["SENDS OUT", "cloud", "Sends out"],
    ["SENDS NOTHING", "cloud", "Sends nothing"],
    ["REMOTE · 10.0.0.2", "remote", "Remote · 10.0.0.2"],
    ["192.168.1.43 · LAN", "local", "192.168.1.43 · LAN"],
    ["github.com", "cloud", "github.com"],
    ["api.anthropic.com", "cloud", "api.anthropic.com"],
    ["ICLOUD", "cloud", "iCloud"],
    ["Egress", "cloud", "Egress"],
  ] as const)("%s → %s", (label, scope, words) => {
    const { container } = render(<EgressChip label={label} scope={scope} />);
    const chip = container.querySelector(".gadget-chip-egress");
    expect(chip?.textContent).toBe(words);
    expect(chip?.getAttribute("title")).toBe(words);
  });

  it("a host is a code token: exact text, mono", () => {
    const { container } = render(<EgressChip label="karolsaneapple.atlassian.net" scope="cloud" />);
    const chip = container.querySelector(".gadget-chip-egress");
    expect(chip?.textContent).toBe("karolsaneapple.atlassian.net");
    expect(chip?.hasAttribute("data-literal")).toBe(true);
  });

  it("a word is not a code token", () => {
    const { container } = render(<EgressChip label="SENDS OUT" scope="cloud" />);
    expect(container.querySelector(".gadget-chip-egress")?.hasAttribute("data-literal")).toBe(false);
  });

  it("Not set and a passive same-device chip draw nothing, in any case", () => {
    for (const label of ["NOT SET", "Not set"]) {
      const { container } = render(<EgressChip label={label} scope="cloud" />);
      expect(container.querySelector(".gadget-chip-egress")).toBeNull();
    }
    const { container } = render(<EgressChip label="This device" scope="local" />);
    expect(container.querySelector(".gadget-chip-egress")).toBeNull();
  });

  it("knows a host from a word", () => {
    expect(chipCarriesHost("github.com")).toBe(true);
    expect(chipCarriesHost("192.168.1.43 · LAN")).toBe(true);
    expect(chipCarriesHost("api.example.com:443")).toBe(true);
    expect(chipCarriesHost("Sends out")).toBe(false);
    expect(chipCarriesHost("LAN")).toBe(false);
  });
});

describe("the SecretRow chip says Set or Not set", () => {
  it.each([
    [true, "Set"],
    [false, "Not set"],
  ])("configured %s → %s", (configured, word) => {
    const { container } = render(<SecretRow label="Token" configured={configured} onReplace={() => {}} />);
    expect(container.querySelector(".gadget-secret .gadget-chip")?.textContent).toBe(word);
  });
});

describe("the chip CSS draws the word as it is", () => {
  it("no caps transform, no wide tracking, the sans face", () => {
    expect(chipRule).not.toMatch(/text-transform/);
    expect(chipRule).toMatch(/letter-spacing:\s*0;/);
    expect(chipRule).toMatch(/var\(--font-sans\)/);
    expect(gadgetsCss).toMatch(/\.gadget-chip\[data-literal\] \{\s*font-family: var\(--font-mono\);/);
  });
});
